import os
import json
import time
from datetime import datetime
import logging
import threading
from decimal import Decimal
from backtest_engine.live.utils import is_market_open

logger = logging.getLogger("papertrader")


from backtest_engine.live.utils import get_eurusd_rate


class PaperTradingEngine:
    def __init__(self, db_url=None):
        self.db_url = db_url or os.getenv("DATABASE_URL")
        self.market_hours_path = os.path.join(
            os.path.dirname(__file__), "../../../configs/market_hours.json"
        )
        self.market_hours = self._load_market_hours()
        self._running = False
        self._cycle_lock = threading.Lock()
        self._skipped_cycles = 0  # O1-FIX
        self._clients_warmed_up = False  # O3-FIX

        # O3-FIX: Defer broker client init to _warmup_clients()
        self.t212_client = None
        self.t212_init_error = None
        self.bybit_client = None
        self.bybit_init_error = None

        # Initialize Signal Executor (pass lambda for dynamic mocking of is_market_open)
        from backtest_engine.live.paper_trading.signal_executor import SignalExecutor
        self.executor = SignalExecutor(
            engine=self,
            t212_client=self.t212_client,
            bybit_client=self.bybit_client,
            market_hours=self.market_hours,
            is_market_open_func=lambda asset: self.is_market_open(asset)
        )

    def _warmup_clients(self) -> None:
        """O3-FIX: Lazy initialization of broker clients on first cycle.
        PT-26: Only mark as warmed up if at least one client succeeded.
        On full failure, clients are retried periodically (every N cycles)."""
        if self._clients_warmed_up:
            return

        t212_ok = False
        bybit_ok = False

        from backtest_engine.live.trading212.config import Trading212Config
        from backtest_engine.live.trading212.client import Trading212Client
        try:
            config = Trading212Config()
            config.validate()
            self.t212_client = Trading212Client(config)
            self.t212_client.get_pending_orders()
            self.executor.t212_client = self.t212_client
            logger.info("[PaperTrader] Trading 212 API client successfully initialized and pending orders recovered.")
            self.t212_init_error = None
            t212_ok = True
        except ValueError as e:
            logger.info("[PaperTrader] Trading 212 credentials not configured or invalid, running in local-only mode: %s", e)
            self.t212_client = None
            self.t212_init_error = str(e)
        except Exception as e:
            logger.exception("[PaperTrader] Unexpected error initializing Trading 212 Client")
            self.t212_client = None
            self.t212_init_error = str(e)

        from backtest_engine.live.bybit.config import BybitConfig
        from backtest_engine.live.bybit.client import BybitClient
        try:
            bybit_config = BybitConfig()
            bybit_config.validate()
            self.bybit_client = BybitClient(bybit_config)
            self.executor.bybit_client = self.bybit_client
            logger.info("[PaperTrader] Bybit API client successfully initialized.")
            self.bybit_init_error = None
            bybit_ok = True
        except ValueError as e:
            logger.info("[PaperTrader] Bybit credentials not configured or invalid: %s", e)
            self.bybit_client = None
            self.bybit_init_error = str(e)
        except Exception as e:
            logger.exception("[PaperTrader] Unexpected error initializing Bybit Client")
            self.bybit_client = None
            self.bybit_init_error = str(e)

        # PT-26: Only mark warmed up if at least one client initialized.
        # If both failed, _warmup_clients() will retry on every cycle.
        self._clients_warmed_up = t212_ok or bybit_ok
        if not self._clients_warmed_up:
            logger.warning(
                "[PaperTrader] Both broker clients failed to initialize. "
                "Retrying on next cycle (errors: T212=%s, Bybit=%s).",
                self.t212_init_error, self.bybit_init_error,
            )

    def _load_market_hours(self):
        try:
            with open(self.market_hours_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, PermissionError, json.JSONDecodeError) as e:
            logger.exception("[PaperTrader] Error loading market hours")
            return {}

    def is_market_open(self, asset):
        """
        Check if the market is open for a given asset based on Mon-Fri and defined hours.
        """
        import datetime as dt
        current_time = None
        try:
            current_time = datetime.now(dt.timezone.utc)
        except (ValueError, TypeError, OSError) as e:
            logger.exception("[PaperTrader] Error getting current time")
        return is_market_open(asset, self.market_hours, current_time=current_time)

    def run_cycle(self):
        """Single execution cycle for the paper trader."""
        # O3-FIX: Deferred broker client initialization on first cycle
        if not self._clients_warmed_up:
            self._warmup_clients()

        if not self._cycle_lock.acquire(blocking=False):
            self._skipped_cycles += 1
            logger.warning(
                "[PaperTrader] Cycle already in progress, skipping (total skipped: %d).",
                self._skipped_cycles,
            )
            if self._skipped_cycles >= 3:
                logger.error(
                    "[PaperTrader] ALERT: %d consecutive cycles skipped. "
                    "Possible deadlock or slow cycle.",
                    self._skipped_cycles,
                )
            return

        try:
            from backtest_engine.live.connection import get_db_connection

            try:
                with get_db_connection() as conn:
                    # 1. Update NAV and active position prices
                    self.executor.update_portfolio_nav(conn)
                    # 2. Evaluate active strategies and execute signals
                    self.executor.evaluate_and_execute_strategies(conn)
                    # 3. Clean up old evaluations (Anti-Bloat)
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM paper_evaluations WHERE timestamp < NOW() - INTERVAL '48 hours'")
                    conn.commit()
                    # 4. Run conversion pipeline (Live mode only)
                    if os.getenv("BYBIT_CONVERSION_ENABLED", "false").lower() == "true":
                        self.executor.run_conversion_pipeline(conn)
            except Exception as e:
                logger.exception("[PaperTrader] Error in run_cycle database operations")
        finally:
            self._skipped_cycles = 0  # O1-FIX: reset on successful lock acquisition
            self._cycle_lock.release()

    def start_loop(self, interval_seconds=60):
        self._running = True
        logger.info("[PaperTrader] Starting paper trading loop (interval: %ds)...", interval_seconds)
        while self._running:
            cycle_start = time.monotonic()
            self.run_cycle()
            elapsed = time.monotonic() - cycle_start
            remaining = max(0, interval_seconds - elapsed)
            if remaining == 0:
                logger.warning(
                    "[PaperTrader] Cycle took %.1fs (> %ds interval). No sleep.",
                    elapsed, interval_seconds,
                )
            else:
                time.sleep(remaining)

    async def start_loop_async(self, fast_interval=30, eval_interval=60, interval_seconds=None):
        """Phase 3: Decoupled dual-loop execution.
        - Fast loop (30s): update_portfolio_nav + cleanup only
        - Eval loop (60s): evaluate_and_execute_strategies + conversion pipeline

        This guarantees NAV updates are never blocked by a slow evaluation cycle.
        Pass interval_seconds= as a backward-compatible shorthand (sets eval_interval).
        """
        import asyncio
        from backtest_engine.live.connection import get_db_connection
        if interval_seconds is not None:
            eval_interval = interval_seconds
        logger.info("[PaperTrader] Starting decoupled async loops (fast: %ds, eval: %ds)...",
                     fast_interval, eval_interval)
        self._running = True

        async def _fast_loop():
            while self._running:
                cycle_start = time.monotonic()
                try:
                    await asyncio.to_thread(self._run_fast_cycle)
                except Exception:
                    logger.exception("[PaperTrader] Fast cycle error")
                elapsed = time.monotonic() - cycle_start
                if elapsed > fast_interval:
                    logger.warning("[PaperTrader] Fast cycle took %.1fs (> %ds interval).", elapsed, fast_interval)
                await asyncio.sleep(fast_interval)

        async def _eval_loop():
            while self._running:
                cycle_start = time.monotonic()
                try:
                    await asyncio.to_thread(self._run_evaluation_cycle)
                except Exception:
                    logger.exception("[PaperTrader] Evaluation cycle error")
                elapsed = time.monotonic() - cycle_start
                remaining = max(0, eval_interval - elapsed)
                if remaining == 0:
                    logger.warning("[PaperTrader] Eval cycle took %.1fs (> %ds interval).", elapsed, eval_interval)
                await asyncio.sleep(remaining)

        await asyncio.gather(_fast_loop(), _eval_loop())

    def _run_fast_cycle(self) -> None:
        """Phase 3: Fast NAV-only cycle (no strategy evaluation)."""
        if not self._clients_warmed_up:
            self._warmup_clients()
        from backtest_engine.live.connection import get_db_connection
        with get_db_connection() as conn:
            self.executor.update_portfolio_nav(conn)
            with conn.cursor() as cur:
                cur.execute("DELETE FROM paper_evaluations WHERE timestamp < NOW() - INTERVAL '48 hours'")
            conn.commit()
        logger.debug("[PaperTrader] Fast cycle (NAV) completed.")

    def _run_evaluation_cycle(self) -> None:
        """Phase 3: Strategy evaluation cycle (no NAV update)."""
        if not self._clients_warmed_up:
            self._warmup_clients()
        from backtest_engine.live.connection import get_db_connection
        with get_db_connection() as conn:
            self.executor.evaluate_and_execute_strategies(conn)
            if os.getenv("BYBIT_CONVERSION_ENABLED", "false").lower() == "true":
                self.executor.run_conversion_pipeline(conn)
        logger.debug("[PaperTrader] Eval cycle completed.")

    def stop(self):
        self._running = False

    # ── Backward Compatibility Delegations ───────────────────────
    def _update_portfolio_nav(self, conn):
        return self.executor.update_portfolio_nav(conn)

    def _evaluate_and_execute_strategies(self, conn):
        return self.executor.evaluate_and_execute_strategies(conn)

    def _log_evaluation(self, *args, **kwargs):
        # A-02: Strip legacy 'conn' first positional arg for backward compat
        if args and hasattr(args[0], 'cursor'):
            args = args[1:]
        return self.executor.log_evaluation(*args, **kwargs)

    def _run_conversion_pipeline(self, conn):
        return self.executor.run_conversion_pipeline(conn)





