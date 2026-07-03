import os
import json
import time
from datetime import datetime
import logging
import threading
from decimal import Decimal
from backtest_engine.live.utils import is_crypto_asset, is_market_open

logger = logging.getLogger("papertrader")


def get_eurusd_rate(conn=None):
    """
    Retrieve the EUR/USD exchange rate (1 EUR = X USD).
    Queries the live_prices table first. If unavailable, falls back to a public API
    with a strict timeout, and finally to a static fallback (1.08).
    """
    import urllib.request
    import urllib.error
    import json
    import psycopg2

    # 1. Query the database first
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT price FROM live_prices WHERE ticker = 'eurusd'")
                row = cur.fetchone()
                if row and row[0] is not None:
                    return Decimal(str(row[0]))
        except (psycopg2.Error, Exception) as e:
            logger.exception("[PaperTrader] DB query for eurusd failed")
            
    # 2. Query public API with strict timeout
    urls = [
        "https://open.er-api.com/v6/latest/EUR",
        "https://api.exchangerate-api.com/v4/latest/EUR"
    ]
    for url in urls:
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'AntigravityPaperTrader/1.0'}
            )
            with urllib.request.urlopen(req, timeout=1.5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    rates = data.get("rates", {})
                    usd_rate = rates.get("USD")
                    if usd_rate is not None:
                        return Decimal(str(usd_rate))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ConnectionError, json.JSONDecodeError, UnicodeDecodeError, ValueError, Exception) as api_err:
            logger.exception(f"[PaperTrader] Public API call to {url} failed")
            
    # 3. Static fallback
    logger.info("[PaperTrader] Using static fallback (1.08) for EUR/USD rate.")
    return Decimal("1.08")


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
            logger.info("[PaperTrader] Trading 212 API client successfully initialized.")
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





