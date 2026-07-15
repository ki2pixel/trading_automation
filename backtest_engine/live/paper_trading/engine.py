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

        # Initialize Trading 212 Client resiliently
        from backtest_engine.live.trading212.config import Trading212Config
        from backtest_engine.live.trading212.client import Trading212Client
        try:
            config = Trading212Config()
            config.validate()
            self.t212_client = Trading212Client(config)
            self.t212_client.get_pending_orders()
            logger.info("[PaperTrader] Trading 212 API client successfully initialized and pending orders recovered.")
            self.t212_init_error = None
        except ValueError as e:
            logger.info(f"[PaperTrader] Trading 212 credentials not configured or invalid, running in local-only mode: {e}")
            self.t212_client = None
            self.t212_init_error = str(e)
        except Exception as e:
            logger.exception("[PaperTrader] Unexpected error initializing Trading 212 Client")
            self.t212_client = None
            self.t212_init_error = str(e)

        # Initialize Bybit Client resiliently
        from backtest_engine.live.bybit.config import BybitConfig
        from backtest_engine.live.bybit.client import BybitClient
        try:
            bybit_config = BybitConfig()
            bybit_config.validate()
            self.bybit_client = BybitClient(bybit_config)
            logger.info("[PaperTrader] Bybit API client successfully initialized.")
            self.bybit_init_error = None
        except ValueError as e:
            logger.info(f"[PaperTrader] Bybit credentials not configured or invalid: {e}")
            self.bybit_client = None
            self.bybit_init_error = str(e)
        except Exception as e:
            logger.exception("[PaperTrader] Unexpected error initializing Bybit Client")
            self.bybit_client = None
            self.bybit_init_error = str(e)

        # Initialize Signal Executor (pass lambda for dynamic mocking of is_market_open)
        from backtest_engine.live.paper_trading.signal_executor import SignalExecutor
        self.executor = SignalExecutor(
            engine=self,
            t212_client=self.t212_client,
            bybit_client=self.bybit_client,
            market_hours=self.market_hours,
            is_market_open_func=lambda asset: self.is_market_open(asset)
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
        if not self._cycle_lock.acquire(blocking=False):
            logger.warning("[PaperTrader] Cycle already in progress, skipping.")
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
            self._cycle_lock.release()

    def start_loop(self, interval_seconds=60):
        self._running = True
        logger.info(f"[PaperTrader] Starting paper trading loop (interval: {interval_seconds}s)...")
        while self._running:
            self.run_cycle()
            time.sleep(interval_seconds)

    async def start_loop_async(self, interval_seconds=60):
        logger.info(f"[PaperTrader] Starting async paper trading loop (interval: {interval_seconds}s)...")
        import asyncio
        self._running = True
        while self._running:
            await asyncio.to_thread(self.run_cycle)
            for _ in range(interval_seconds):
                if not self._running:
                    break
                await asyncio.sleep(1)

    def stop(self):
        self._running = False

    # ── Backward Compatibility Delegations ───────────────────────
    def _update_portfolio_nav(self, conn):
        return self.executor.update_portfolio_nav(conn)

    def _evaluate_and_execute_strategies(self, conn):
        return self.executor.evaluate_and_execute_strategies(conn)

    def _log_evaluation(self, conn, *args, **kwargs):
        return self.executor.log_evaluation(conn, *args, **kwargs)

    def _run_conversion_pipeline(self, conn):
        return self.executor.run_conversion_pipeline(conn)





