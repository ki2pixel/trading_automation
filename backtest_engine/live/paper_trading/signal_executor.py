import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union, Callable, Dict, Tuple
import pandas as pd

import psycopg2
import requests
from backtest_engine.live.utils import is_crypto_asset, is_market_open
from backtest_engine.live.paper_trading.exceptions import PortfolioUpdateError
from backtest_engine.live.paper_trading.execution_guards import (
    resolve_max_entry_price,
    is_entry_blocked_by_atr_gate,
    is_exit_blocked_by_mhp,
    count_bars_since_entry,
)

logger = logging.getLogger("papertrader")


class SignalExecutor:
    """Encapsulates paper trading strategy evaluation, trade execution, and NAV calculations."""

    def __init__(
        self,
        engine: Any = None,
        t212_client: Any = None,
        bybit_client: Any = None,
        market_hours: Optional[Dict[str, Any]] = None,
        is_market_open_func: Optional[Callable[[str], bool]] = None,
    ) -> None:
        self.engine: Any = engine
        self._t212_client: Any = t212_client
        self._bybit_client: Any = bybit_client
        self.market_hours: Dict[str, Any] = market_hours or {}
        self._is_market_open_func: Optional[Callable[[str], bool]] = is_market_open_func
        self._last_eval_timestamps: Dict[int, Any] = {}
        self._broker_simulators: Dict[tuple, Any] = {}
        self._eval_buffer: list[tuple] = []  # A-02: batch evaluation inserts
        self._strategy_result_cache: Dict[tuple, tuple] = {}  # A-03: (asset, tf, bar_ts) -> (bar_ts, run_result)
        self._margin_simulator = None  # PT-18: cached UTAMarginSimulator

    @property
    def t212_client(self) -> Any:
        if self.engine:
            return getattr(self.engine, "t212_client", None)
        return self._t212_client

    @t212_client.setter
    def t212_client(self, value: Any) -> None:
        self._t212_client = value
        self._t212_resolver = None

    @property
    def t212_resolver(self) -> Optional[Any]:
        if not hasattr(self, "_t212_resolver") or self._t212_resolver is None:
            self._t212_resolver = None
            client = self.t212_client
            if client:
                try:
                    from backtest_engine.live.trading212.resolver import Trading212TickerResolver
                    self._t212_resolver = Trading212TickerResolver(client)
                except Exception as e:
                    logger.warning(f"[PaperTrader] Failed to initialize Trading212TickerResolver: {e}")
        return self._t212_resolver

    @property
    def t212_bootstrapper(self) -> Optional[Any]:
        if not hasattr(self, "_t212_bootstrapper") or self._t212_bootstrapper is None:
            self._t212_bootstrapper = None
            client = self.t212_client
            resolver = self.t212_resolver
            if client and resolver:
                try:
                    from backtest_engine.live.trading212.bootstrapper import Trading212Bootstrapper
                    self._t212_bootstrapper = Trading212Bootstrapper(client, resolver)
                except Exception as e:
                    logger.warning(f"[PaperTrader] Failed to initialize Trading212Bootstrapper: {e}")
        return self._t212_bootstrapper

    @property
    def bybit_client(self) -> Any:
        if self.engine:
            return getattr(self.engine, "bybit_client", None)
        return self._bybit_client

    @bybit_client.setter
    def bybit_client(self, value: Any) -> None:
        self._bybit_client = value

    @staticmethod
    def _parse_timeframe_minutes(tf_str: str) -> int:
        """Parse a timeframe string like '45m', '1h', '5' into integer minutes."""
        tf = str(tf_str).strip().lower()
        if tf.endswith("m"):
            return int(tf[:-1])
        if tf.endswith("h"):
            return int(tf[:-1]) * 60
        if tf.endswith("min"):
            return int(tf[:-3])
        return int(tf)

    @staticmethod
    def _compute_min_bars_needed(indicator_params: dict) -> int:
        """Compute dynamic warmup period based on indicator lookback parameters."""
        min_bars_needed = 2
        if indicator_params:
            lookbacks = [50]
            for k, v in indicator_params.items():
                if isinstance(v, (int, float)):
                    k_lower = k.lower()
                    if any(term in k_lower for term in ["length", "period", "len", "lookback", "window", "bars"]):
                        lookbacks.append(int(v))
            min_bars_needed = max(lookbacks)
        return min_bars_needed

    def is_market_open(self, asset: str) -> bool:
        if self._is_market_open_func:
            return self._is_market_open_func(asset)
        import datetime as dt
        current_time = None
        try:
            current_time = datetime.now(dt.timezone.utc)
        except Exception as e:
            logger.warning("[PaperTrader] Failed to get current UTC time: %s", e)
            return False
        return is_market_open(asset, self.market_hours, current_time=current_time)

    def log_evaluation(
        self,
        strategy_name: str,
        asset: str,
        timeframe: str,
        price: Optional[Union[float, Decimal]],
        signal_type: str,
        signal_triggered: bool,
        status: str,
        fail_reason: Optional[str] = None,
        details: Optional[Any] = None,
    ) -> None:
        """Accumulate evaluation log entry for batch flush (A-02 anti-N+1)."""
        def serialize_details(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {k: serialize_details(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_details(i) for i in obj]
            elif isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, (int, float)):
                return obj
            elif hasattr(obj, 'to_dict'):
                try:
                    return serialize_details(obj.to_dict())
                except Exception:
                    return str(obj)
            elif hasattr(obj, 'isoformat'):
                return obj.isoformat()
            try:
                json.dumps(obj)
                return obj
            except TypeError:
                return str(obj)

        details_json = None
        if details is not None:
            try:
                details_json = json.dumps(serialize_details(details))
            except (TypeError, ValueError) as e:
                logger.exception("[PaperTrader] JSON serialization error for details")
                details_json = "{}"

        self._eval_buffer.append((
            strategy_name, asset, timeframe,
            float(price) if price is not None else None,
            signal_type, signal_triggered, status,
            fail_reason, details_json,
        ))

    def _flush_evaluations(self, conn: Any) -> None:
        """Batch-insert all accumulated evaluation log entries (A-02)."""
        if not self._eval_buffer:
            return
        try:
            with conn.cursor() as cur:
                cur.executemany("""
                    INSERT INTO paper_evaluations (
                        strategy_name, asset, timeframe, price, signal_type,
                        signal_triggered, status, fail_reason, details, timestamp
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """, self._eval_buffer)
            conn.commit()
            logger.debug("[PaperTrader] Flushed %d evaluation entries in batch.", len(self._eval_buffer))
            self._eval_buffer.clear()
        except psycopg2.Error as e:
            logger.exception("[PaperTrader] Error batch-flushing evaluations")
            try:
                conn.rollback()
            except psycopg2.Error:
                pass
            self._eval_buffer.clear()

    def reconcile_allocated_balances(self, conn: Any = None) -> None:
        """
        Reconcile paper_portfolio_balance.allocated_balance with open paper_positions.
        """
        from backtest_engine.live.paper_trading.db_setup import reconcile_allocated_balances
        if conn is not None:
            reconcile_allocated_balances(conn)
        else:
            from backtest_engine.live.connection import get_db_connection
            with get_db_connection() as conn_obj:
                reconcile_allocated_balances(conn_obj)
                conn_obj.commit()

    def _fetch_t212_summary(self) -> Optional[Decimal]:
        """Fetch Trading 212 account summary and return available cash balance (or None on failure)."""
        if self.t212_client is None:
            return None
        summary = self.t212_client.get_account_summary()
        if not summary:
            return None
        if "cash" in summary and isinstance(summary["cash"], dict) and "availableToTrade" in summary["cash"]:
            return Decimal(str(summary["cash"]["availableToTrade"]))
        elif "free" in summary:
            return Decimal(str(summary["free"]))
        elif "balance" in summary:
            return Decimal(str(summary["balance"]))
        elif "totalValue" in summary:
            return Decimal(str(summary["totalValue"]))
        return None

    def _fetch_bybit_summary(self) -> Decimal:
        """Fetch Bybit account summary and return wallet balance (or Decimal('0') on failure)."""
        if self.bybit_client is None or not self.bybit_client.config.api_key:
            return Decimal("0")
        base_coin = self.bybit_client.config.base_currency
        summary = self.bybit_client.get_account_summary(coin=base_coin)
        bybit_balance = Decimal("0")
        for acc in summary.get("result", {}).get("list", []):
            for coin_info in acc.get("coin", []):
                if coin_info.get("coin") == base_coin:
                    bybit_balance = Decimal(coin_info.get("walletBalance", "0"))
                    break
        return bybit_balance

    def update_portfolio_nav(self, conn: Any) -> None:
        """
        Update the total NAV of the portfolio based on current prices of positions
        and the cash balance, split by ecosystem (trading212 vs bybit).

        Batched I/O: uses Redis mget() + SQL ANY() + executemany() to avoid N+1 queries.
        Broker API calls (T212, Bybit) are executed in parallel via ThreadPoolExecutor.
        """
        from backtest_engine.live.connection import get_redis_client
        redis_client = get_redis_client()
        
        try:
            # A-01: Fetch broker account summaries in parallel (ThreadPoolExecutor)
            t212_balance: Optional[Decimal] = None
            bybit_balance: Optional[Decimal] = None

            t212_needed = self.t212_client is not None
            bybit_needed = self.bybit_client is not None and self.bybit_client.config.api_key

            if t212_needed or bybit_needed:
                with ThreadPoolExecutor(max_workers=2) as executor:
                    futures: dict = {}
                    if t212_needed:
                        futures[executor.submit(self._fetch_t212_summary)] = "t212"
                    if bybit_needed:
                        futures[executor.submit(self._fetch_bybit_summary)] = "bybit"

                    for future in as_completed(futures):
                        source = futures[future]
                        try:
                            result = future.result()
                            if source == "t212":
                                t212_balance = result
                            else:
                                bybit_balance = result
                        except (requests.exceptions.RequestException, ValueError, KeyError, TypeError) as api_err:
                            logger.warning("[PaperTrader] Failed to fetch account summary from %s API: %s", source.upper(), api_err)

            with conn.cursor() as cur:
                # Apply Trading 212 balance if fetched
                if t212_balance is not None:
                    cur.execute(
                        "UPDATE paper_portfolio_balance SET paper_cash_balance = %s, last_updated = CURRENT_TIMESTAMP WHERE source = 'trading212'",
                        (t212_balance,)
                    )

                # Apply Bybit balance if fetched
                if bybit_balance is not None and bybit_balance > 0:
                    cur.execute(
                        "UPDATE paper_portfolio_balance SET paper_cash_balance = %s, last_updated = CURRENT_TIMESTAMP WHERE source = 'bybit'",
                        (bybit_balance,)
                    )

                # Fetch cash and secured balances for both ecosystems
                cur.execute("SELECT source, paper_cash_balance, secured_balance FROM paper_portfolio_balance")
                rows = cur.fetchall()
                balances = {r[0]: Decimal(str(r[1])) for r in rows}
                secured_balances = {r[0]: Decimal(str(r[2])) for r in rows}
                
                t212_nav = balances.get("trading212")
                bybit_nav = balances.get("bybit")
                if t212_nav is None or bybit_nav is None:
                    raise PortfolioUpdateError("No balance row found in paper_portfolio_balance for one or both sources (trading212/bybit)")
                bybit_secured = secured_balances.get("bybit", Decimal("0"))

                # Get open positions (single query)
                cur.execute("SELECT id, asset, qty, entry_price, current_price FROM paper_positions")
                positions = cur.fetchall()
                
                # Retrieve exchange rate to integrate secured_balance (in EUR) converted to USDC/USDT in Bybit total NAV
                from backtest_engine.live.utils import get_eurusd_rate
                eurusd_rate = get_eurusd_rate(conn)
                bybit_nav += bybit_secured * eurusd_rate

                if not positions:
                    cur.execute("UPDATE paper_portfolio_balance SET total_nav = %s, last_updated = CURRENT_TIMESTAMP WHERE source = 'trading212'", (t212_nav,))
                    cur.execute("UPDATE paper_portfolio_balance SET total_nav = %s, last_updated = CURRENT_TIMESTAMP WHERE source = 'bybit'", (bybit_nav,))
                    conn.commit()
                    return

                # ── Batched price resolution ──────────────────────────────────
                # Classify positions by market open/closed
                open_positions = []   # (pos_id, asset, qty, entry_price, current_price)
                closed_positions = [] # same tuple shape

                for pos_id, asset, qty, entry_price, current_price in positions:
                    if self.is_market_open(asset):
                        open_positions.append((pos_id, asset, Decimal(str(qty)), Decimal(str(entry_price)), current_price))
                    else:
                        closed_positions.append((pos_id, asset, Decimal(str(qty)), Decimal(str(entry_price)), current_price))

                # Handle closed-market positions: use last known current_price (no DB query needed)
                for pos_id, asset, qty, entry_price, current_price in closed_positions:
                    if current_price is not None:
                        val = Decimal(str(current_price)) * qty
                        if is_crypto_asset(asset):
                            bybit_nav += val
                        else:
                            t212_nav += val

                # For open-market positions: batch Redis mget + batch SQL fallback
                if open_positions:
                    tickers = [asset.lower() for _, asset, _, _, _ in open_positions]
                    redis_keys = [f"price:{t}" for t in tickers]

                    # 1. Batch Redis mget (single round-trip)
                    redis_prices = {}
                    now_utc = datetime.now(timezone.utc)
                    if redis_client:
                        try:
                            redis_values = redis_client.mget(redis_keys)
                            for ticker, val in zip(tickers, redis_values):
                                if val is not None:
                                    try:
                                        data = json.loads(val)
                                        price_val = Decimal(data["price"])
                                        ts = datetime.fromisoformat(data["timestamp"])
                                        if now_utc - ts <= timedelta(minutes=3):
                                            redis_prices[ticker] = price_val
                                        else:
                                            logger.warning(f"[PaperTrader] Stale Redis price for {ticker} (age: {(now_utc - ts).total_seconds()}s). Ignoring.")
                                    except Exception as je:
                                        logger.error(f"[PaperTrader] Failed to parse Redis price for {ticker}: {je}")
                        except Exception as redis_err:
                            logger.warning("[PaperTrader] Redis mget error: %s", redis_err)

                    # 2. Batch SQL fallback for tickers not found in Redis (single query)
                    missing_tickers = [t for t in tickers if t not in redis_prices]
                    sql_prices = {}
                    if missing_tickers:
                        cur.execute(
                            "SELECT ticker, price, updated_at FROM live_prices WHERE ticker = ANY(%s)",
                            (missing_tickers,)
                        )
                        for row in cur.fetchall():
                            ticker, price, updated_at = row[0], row[1], row[2]
                            price_val = Decimal(str(price))
                            if updated_at:
                                if updated_at.tzinfo is None:
                                    updated_at = updated_at.replace(tzinfo=timezone.utc)
                                age = now_utc - updated_at
                                if age <= timedelta(minutes=3):
                                    sql_prices[ticker] = price_val
                                else:
                                    logger.error(f"[PaperTrader] Postgres price for {ticker} is stale (age: {age.total_seconds()}s). Ignoring.")

                    # 3. Merge prices: Redis takes priority, then SQL
                    all_prices = {**sql_prices, **redis_prices}

                    # 4. Compute PnL and collect batch updates
                    position_updates = []  # (current_price, pnl, pos_id)
                    for pos_id, asset, qty, entry_price, old_current_price in open_positions:
                        asset_lower = asset.lower()
                        current_price = all_prices.get(asset_lower)

                        if current_price is not None:
                            pnl = (current_price - entry_price) * qty
                            position_updates.append((current_price, pnl, pos_id))
                            val = current_price * qty
                        else:
                            # Fallback to last known position price (already fetched above)
                            val = Decimal(str(old_current_price)) * qty if old_current_price is not None else Decimal("0")

                        if is_crypto_asset(asset):
                            bybit_nav += val
                        else:
                            t212_nav += val

                    # 5. Batch UPDATE positions (single executemany round-trip)
                    if position_updates:
                        cur.executemany(
                            "UPDATE paper_positions SET current_price = %s, pnl = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                            position_updates,
                        )

                cur.execute("UPDATE paper_portfolio_balance SET total_nav = %s, last_updated = CURRENT_TIMESTAMP WHERE source = 'trading212'", (t212_nav,))
                cur.execute("UPDATE paper_portfolio_balance SET total_nav = %s, last_updated = CURRENT_TIMESTAMP WHERE source = 'bybit'", (bybit_nav,))
                conn.commit()
        except psycopg2.Error as e:
            logger.exception("[PaperTrader] Database error updating NAV")
            conn.rollback()
            raise PortfolioUpdateError("Database error updating NAV") from e
        except Exception as e:
            logger.exception("[PaperTrader] Unexpected error updating NAV")
            conn.rollback()
            raise PortfolioUpdateError("Unexpected error updating NAV") from e

    @staticmethod
    def _run_strategy_worker(
        strat_info: Any,
        df_aggregated: pd.DataFrame,
        overrides: Any,
        asset: str,
        initial_capital_bucket: float,
        timeframe: str,
    ) -> Tuple[Any, Optional[Exception]]:
        """Thread-safe wrapper for strategy run_function (stateless computation)."""
        try:
            run_result = strat_info.run_function(
                data=df_aggregated,
                symbol=asset,
                overrides=overrides,
                initial_capital=initial_capital_bucket,
                timeframe_minutes=timeframe,
                compute_full_metrics=False,
            )
            return run_result, None
        except Exception as e:
            return None, e

    def evaluate_and_execute_strategies(self, conn: Any) -> None:
        """
        Evaluate active strategy configurations on recent price history and execute trade signals.

        Performance-optimized (P6 instrumented):
        - SQL: timestamp range scan instead of ROW_NUMBER() window
        - Resampling cache: shared (ticker, timeframe) DataFrames
        - Parallel strategy eval: ThreadPoolExecutor(max_workers=2)
        - Batch status updates: single executemany + commit
        """
        t_cycle_start = time.monotonic()
        from backtest_engine.strategy_registry import StrategyRegistry
        from backtest_engine.live.connection import get_redis_client
        redis_client = get_redis_client()
        
        from backtest_engine.live.kill_switch import get_kill_switch_status

        kill_switch_status = get_kill_switch_status(redis_client)
        if kill_switch_status.suspended:
            logger.warning(
                "[SignalExecutor] Trading is suspended by Kill Switch. source=%s reason=%s",
                kill_switch_status.source,
                kill_switch_status.reason,
            )
            return

        # 1. Fetch active configurations
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, strategy_name, asset, timeframe, kelly_weight, 
                       initial_capital, initial_capital_bucket, max_capital_bucket, max_entry_price, indicator_params
                FROM paper_strategy_configs
                WHERE is_active = TRUE
            """)
            configs = cur.fetchall()
            
             # Fetch all active positions to avoid N+1 queries in the loop
            cur.execute("SELECT id, asset, strategy_name, qty, entry_price, timeframe, opened_at FROM paper_positions")
            positions_rows = cur.fetchall()
            active_positions = {
                (r[1].lower(), r[2], r[5]): (r[0], Decimal(str(r[3])), Decimal(str(r[4])))
                for r in positions_rows
            }
            # Separate dict for opened_at to avoid breaking tuple consumers (PTC, SELL, NAV)
            positions_opened_at: Dict[tuple, Optional[datetime]] = {
                (r[1].lower(), r[2], r[5]): r[6]
                for r in positions_rows
            }
            
            # Fetch balances to avoid N+1 and fetchone shifts in the loop
            cur.execute("SELECT source, paper_cash_balance, total_nav FROM paper_portfolio_balance")
            balance_rows = cur.fetchall()
            balances = {
                r[0]: (Decimal(str(r[1])), Decimal(str(r[2])))
                for r in balance_rows
            }
        t_after_prefetch = time.monotonic()
            
        # N-01: Filter configs and extract unique tickers for batch fetching
        # A-07: Pre-compute is_market_open per asset (avoid duplicate calls in filter + loop)
        active_assets = set()
        market_open_status: Dict[str, bool] = {}
        max_lookback_minutes = 2000
        for config in configs:
            asset = config[2]
            if asset not in market_open_status:
                market_open_status[asset] = self.is_market_open(asset)
            if market_open_status[asset]:
                active_assets.add(asset.lower())
            tf_minutes = self._parse_timeframe_minutes(config[3])
            indicator_params_config = config[9] or {}
            min_bars = self._compute_min_bars_needed(indicator_params_config)
            max_lookback_minutes = max(max_lookback_minutes, min_bars * tf_minutes)

        # Batch fetch all 1m candles for active assets (P1: timestamp range scan)
        candles_by_ticker: Dict[str, list] = {}
        if active_assets:
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT ticker, timestamp_minute, open, high, low, close
                        FROM live_candles_1m
                        WHERE ticker = ANY(%s)
                          AND timestamp_minute >= NOW() - make_interval(mins => %s)
                        ORDER BY ticker, timestamp_minute ASC
                    """, (list(active_assets), max_lookback_minutes))
                    all_candle_rows = cur.fetchall()
                
                for row in all_candle_rows:
                    if len(row) == 6:
                        ticker, timestamp_val, o, h, l, c = row
                    elif len(row) == 5:
                        logger.warning("[PaperTrader] Candle row has 5 columns (ticker missing) — please run tickercase migration (PT-02)")
                        ticker = configs[0][2].lower() if configs else "unknown"
                        timestamp_val, o, h, l, c = row
                    else:
                        logger.error("[PaperTrader] Unexpected candle row length %d, skipping", len(row))
                        continue
                    ticker_lower = ticker.lower()
                    if ticker_lower not in candles_by_ticker:
                        candles_by_ticker[ticker_lower] = []
                    candles_by_ticker[ticker_lower].append((timestamp_val, o, h, l, c))
            except psycopg2.Error as db_err:
                logger.exception("[PaperTrader] Database error batch fetching live_candles_1m")
        t_after_sql = time.monotonic()
            
        # P2-FIX: Batch-fetch all live prices via Redis MGET before the config loop
        # B5-FIX: Use pre-computed market_open_status instead of redundant is_market_open() calls
        live_prices_cache: Dict[str, Optional[Decimal]] = {}
        active_asset_list = list(set(c[2].lower() for c in configs if market_open_status.get(c[2], False)))
        if redis_client and active_asset_list:
            try:
                redis_price_keys = [f"price:{t}" for t in active_asset_list]
                redis_values = redis_client.mget(redis_price_keys)
                now_utc = datetime.now(timezone.utc)
                for ticker, val in zip(active_asset_list, redis_values):
                    if val is not None:
                        try:
                            data = json.loads(val)
                            price_val = Decimal(data["price"])
                            ts = datetime.fromisoformat(data["timestamp"])
                            if now_utc - ts <= timedelta(minutes=3):
                                live_prices_cache[ticker] = price_val
                        except Exception as parse_err:
                            logger.warning("[PaperTrader] Failed to parse Redis price for %s: %s", ticker, parse_err)
            except Exception:
                logger.warning("[PaperTrader] Redis mget error for live prices batch: %s", "timeout or connection issue")

        # P2: Per-cycle resampling cache — keyed by (ticker_lower, timeframe)
        _resampling_cache: Dict[Tuple[str, str], Tuple[pd.DataFrame, pd.DataFrame]] = {}
        # P3: Batch status update accumulator — (run_status, warmup_progress_json, last_error, config_id)
        _status_updates: list[tuple] = []

        # ── P4: Pre-compute strategy evaluations in parallel ──────────────────
        # Build list of configs that need run_function() evaluation
        _parallel_tasks: list[tuple] = []  # (config_id, strat_info, df_aggregated, overrides, asset, initial_capital_bucket, timeframe, last_closed_time)
        _parallel_results: Dict[int, Tuple[Any, Optional[Exception]]] = {}  # config_id -> (run_result, error)
        # Pre-built data for configs that pass all pre-eval checks
        _config_precomputed: Dict[int, Tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp]] = {}  # config_id -> (df_1m, df_aggregated, last_closed_time)

        t_after_redis = time.monotonic()

        for config_id, strategy_name, asset, timeframe, kelly_weight, initial_capital, initial_capital_bucket, max_capital_bucket, max_entry_price, indicator_params in configs:
            indicator_params = indicator_params or {}
            # Determine active position status (O(1) local dict check) — needed for signal_type in logs below
            position_row = active_positions.get((asset.lower(), strategy_name, timeframe))
            has_position = position_row is not None
            
            # Check market hours — log MARKET_CLOSED instead of silently skipping
            # A-07: Use pre-computed market_open_status map
            if not market_open_status.get(asset, False):
                self.log_evaluation(
                    strategy_name, asset, timeframe,
                    price=None, signal_type='EXIT' if has_position else 'ENTRY',
                    signal_triggered=False, status='MARKET_CLOSED',
                    fail_reason='Market is closed'
                )
                continue
                
            source = 'bybit' if is_crypto_asset(asset) else 'trading212'
            
            # Fetch 1m candles for this asset from the pre-fetched dict (N-01)
            candle_rows = candles_by_ticker.get(asset.lower(), [])
                
            if len(candle_rows) < 10:
                # Not enough history (Warmup)
                tf_minutes = self._parse_timeframe_minutes(timeframe)
                min_bars_needed = self._compute_min_bars_needed(indicator_params)
                warmup_progress = {
                    "current_bars": 0,
                    "required_bars": min_bars_needed,
                    "progress_pct": 0.0,
                    "timeframe_minutes": tf_minutes,
                }
                # P3: Defer status update to batch flush
                _status_updates.append(('waiting_data', json.dumps(warmup_progress), None, config_id))
                self.log_evaluation(
                    strategy_name, asset, timeframe, 
                    price=None, signal_type='EXIT' if has_position else 'ENTRY', 
                    signal_triggered=False, status='WAITING_DATA', 
                    fail_reason='Not enough candle history'
                )
                continue

            # P2: Resampling cache — share (df_1m, df_aggregated) across configs with same (ticker, timeframe)
            resample_key = (asset.lower(), timeframe)
            cached_resample = _resampling_cache.get(resample_key)
            if cached_resample is not None:
                df_1m, df_aggregated = cached_resample
            else:
                # Convert to DataFrame
                df_1m = pd.DataFrame(candle_rows, columns=["timestamp_minute", "open", "high", "low", "close"])
                # Convert prices to floats for VectorBT
                for col in ["open", "high", "low", "close"]:
                    df_1m[col] = df_1m[col].astype(float)
                df_1m.set_index("timestamp_minute", inplace=True)
                df_1m.index = pd.to_datetime(df_1m.index)
                if df_1m.index.tzinfo is None:
                    df_1m.index = df_1m.index.tz_localize('UTC')
                else:
                    df_1m.index = df_1m.index.tz_convert('UTC')
                    
                # Resample to strategy's timeframe
                rule = timeframe.replace("m", "min").replace("h", "H")
                df_aggregated = df_1m.resample(rule).agg({
                    "open": "first",
                    "high": "max",
                    "low": "min",
                    "close": "last"
                }).dropna()
                df_aggregated["volume"] = 0.0  # dummy volume
                _resampling_cache[resample_key] = (df_1m, df_aggregated)
            
            # Calculate dynamic warmup period based on indicator parameters
            tf_minutes = self._parse_timeframe_minutes(timeframe)
            min_bars_needed = self._compute_min_bars_needed(indicator_params)

            if len(df_aggregated) < min_bars_needed:
                warmup_progress = {
                    "current_bars": len(df_aggregated),
                    "required_bars": min_bars_needed,
                    "progress_pct": round(min(100.0, len(df_aggregated) / min_bars_needed * 100), 1),
                    "timeframe_minutes": tf_minutes,
                }
                # P3: Defer status update to batch flush
                _status_updates.append(('waiting_data', json.dumps(warmup_progress), None, config_id))
                self.log_evaluation(
                    strategy_name, asset, timeframe, 
                    price=None, signal_type='EXIT' if has_position else 'ENTRY', 
                    signal_triggered=False, status='WAITING_DATA', 
                    fail_reason='Not enough candle history'
                )
                continue
                
            # Get latest closed bar (the one before the very last in-progress bar)
            last_closed_bar = df_aggregated.iloc[-2]
            last_closed_time = df_aggregated.index[-2]
            
            # Skip if this config's last closed bar timestamp has not changed (N-10)
            if self._last_eval_timestamps.get(config_id) == last_closed_time:
                continue
            
            # P4: Queue for parallel strategy evaluation
            try:
                strat_info = StrategyRegistry.get(strategy_name)

                # A-03/A-04: Check cache for previously computed result on same (asset, tf, bar_ts)
                cache_key = (asset.lower(), timeframe, last_closed_time)
                cached = self._strategy_result_cache.get(cache_key)
                if cached is not None and cached[0] == last_closed_time:
                    # Cache hit — store precomputed result directly
                    _parallel_results[config_id] = (cached[1], None)
                    _config_precomputed[config_id] = (df_1m, df_aggregated, last_closed_time)
                    logger.debug("[SignalExecutor] Cache hit for %s/%s @ %s", asset, timeframe, last_closed_time)
                else:
                    # Parse config overrides and queue for parallel execution
                    overrides = strat_info.overrides_from_mapping_function(indicator_params)
                    _parallel_tasks.append((
                        config_id, strat_info, df_aggregated, overrides,
                        asset, float(initial_capital_bucket), timeframe, last_closed_time,
                    ))
                    _config_precomputed[config_id] = (df_1m, df_aggregated, last_closed_time)
            except Exception as strat_err:
                logger.exception(f"[PaperTrader] Error preparing strategy {strategy_name} for {asset}")
                # P3: Defer status update to batch flush
                _status_updates.append(('error', None, str(strat_err), config_id))
                self.log_evaluation(
                    strategy_name, asset, timeframe, 
                    price=None, signal_type='EXIT' if has_position else 'ENTRY', 
                    signal_triggered=False, status='ERROR', 
                    fail_reason=str(strat_err)
                )
                continue

        t_after_preprocess = time.monotonic()

        # ── P4: Execute strategy run_function() calls in parallel ──────────
        if _parallel_tasks:
            max_workers = min(2, len(_parallel_tasks))  # Capped for 0.5 CPU Render
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = {
                    pool.submit(
                        self._run_strategy_worker,
                        task[1],   # strat_info
                        task[2],   # df_aggregated
                        task[3],   # overrides
                        task[4],   # asset
                        task[5],   # initial_capital_bucket
                        task[6],   # timeframe
                    ): task
                    for task in _parallel_tasks
                }
                for future in as_completed(futures):
                    task = futures[future]
                    config_id_f = task[0]
                    last_closed_time_f = task[7]
                    try:
                        run_result, strat_err = future.result()
                        _parallel_results[config_id_f] = (run_result, strat_err)
                        # Update strategy result cache on success
                        if run_result is not None and strat_err is None:
                            asset_f = task[4]
                            timeframe_f = task[6]
                            cache_key_f = (asset_f.lower(), timeframe_f, last_closed_time_f)
                            self._strategy_result_cache[cache_key_f] = (last_closed_time_f, run_result)
                    except Exception as exec_err:
                        _parallel_results[config_id_f] = (None, exec_err)

            # Periodic cache cleanup: evict entries older than 5 minutes
            if len(self._strategy_result_cache) > 50:
                stale = [k for k, v in self._strategy_result_cache.items()
                          if (pd.Timestamp.now(tz='UTC') - v[0]).total_seconds() > 300]
                for k in stale:
                    del self._strategy_result_cache[k]

        t_after_strat_eval = time.monotonic()

        # ── Sequential post-processing: signal extraction + trade execution ──
        for config_id, strategy_name, asset, timeframe, kelly_weight, initial_capital, initial_capital_bucket, max_capital_bucket, max_entry_price, indicator_params in configs:
            indicator_params = indicator_params or {}
            position_row = active_positions.get((asset.lower(), strategy_name, timeframe))
            has_position = position_row is not None

            # Skip configs that were filtered out during pre-processing
            if config_id not in _config_precomputed:
                continue

            df_1m, df_aggregated, last_closed_time = _config_precomputed[config_id]
            last_closed_bar = df_aggregated.loc[last_closed_time]
            source = 'bybit' if is_crypto_asset(asset) else 'trading212'

            # Retrieve parallel evaluation result
            parallel_result = _parallel_results.get(config_id)
            if parallel_result is None:
                continue  # Should not happen, but defensive guard

            run_result, strat_err = parallel_result
            if strat_err is not None:
                logger.exception(f"[PaperTrader] Error running strategy {strategy_name} for {asset}: {strat_err}")
                # P3: Defer status update to batch flush
                _status_updates.append(('error', None, str(strat_err), config_id))
                self.log_evaluation(
                    strategy_name, asset, timeframe, 
                    price=None, signal_type='EXIT' if has_position else 'ENTRY', 
                    signal_triggered=False, status='ERROR', 
                    fail_reason=str(strat_err)
                )
                continue

            try:
                # Check signals on the last closed bar
                result_bars = run_result.bars
                
                # Find the index corresponding to our last closed bar
                last_closed_result = result_bars.loc[last_closed_time]
                
                long_entry_signal = bool(last_closed_result.get('long_entry', False))
                long_exit_signal = bool(last_closed_result.get('long_exit', False))
                
                # P3: Defer status update to batch flush
                _status_updates.append(('active', None, None, config_id))
                
                # Update last evaluated timestamp
                self._last_eval_timestamps[config_id] = last_closed_time
                
            except Exception as strat_err:
                logger.exception(f"[PaperTrader] Error extracting signals for {strategy_name}/{asset}")
                # P3: Defer status update to batch flush
                _status_updates.append(('error', None, str(strat_err), config_id))
                self.log_evaluation(
                    strategy_name, asset, timeframe, 
                    price=None, signal_type='EXIT' if has_position else 'ENTRY', 
                    signal_triggered=False, status='ERROR', 
                    fail_reason=str(strat_err)
                )
                continue
                
            # Fetch current live price (P2-FIX: pre-batched Redis mget cache first, then Postgres)
            current_price = live_prices_cache.get(asset.lower())
            now_utc = datetime.now(timezone.utc)
            price_age_s = None
            if current_price is None:
                with conn.cursor() as cur:
                    cur.execute("SELECT price, updated_at FROM live_prices WHERE ticker = %s", (asset.lower(),))
                    price_row = cur.fetchone()
                    if price_row:
                        price_val = Decimal(str(price_row[0]))
                        updated_at = price_row[1]
                        if updated_at:
                            if updated_at.tzinfo is None:
                                updated_at = updated_at.replace(tzinfo=timezone.utc)
                            age = now_utc - updated_at
                            price_age_s = age.total_seconds()
                            if age <= timedelta(minutes=3):
                                current_price = price_val
                            else:
                                logger.error(f"[PaperTrader] Postgres price for {asset} is stale (age: {price_age_s}s). Ignoring.")
            if current_price is None:
                if price_row is None:
                    fail_reason = 'No price in database'
                else:
                    fail_reason = f'No fresh price available (age: {price_age_s:.0f}s)'
                self.log_evaluation(
                    strategy_name, asset, timeframe,
                    price=None, signal_type='EXIT' if has_position else 'ENTRY',
                    signal_triggered=False, status='WAITING_DATA',
                    fail_reason=fail_reason
                )
                continue
                
            if not has_position:
                # Evaluate Entry (Long Only)
                if long_entry_signal:
                    # Check maximum entry price rule (EX-03: dynamic MEP with static fallback)
                    buffer_pct = float(indicator_params.get("max_entry_price_buffer_pct", 0.30))
                    try:
                        cap, cap_mode = resolve_max_entry_price(
                            df_1m=df_1m,
                            static_max=Decimal(str(max_entry_price)),
                            buffer_pct=buffer_pct,
                            now_utc=now_utc,
                            asset=asset,
                        )
                    except (ValueError, KeyError, TypeError) as guard_err:
                        logger.exception("[PaperTrader] MEP guard error for %s — fallback static", asset)
                        cap, cap_mode = Decimal(str(max_entry_price)), "static_fallback"
                    if current_price > cap:
                        logger.info(
                            "[PaperTrader] Entry rejected for %s: price (%s) exceeds max_entry_price cap=%s (mode=%s, buffer=%.2f%%)",
                            asset, current_price, cap, cap_mode, buffer_pct * 100,
                        )
                        self.log_evaluation(
                            strategy_name, asset, timeframe,
                            price=current_price, signal_type='ENTRY',
                            signal_triggered=True, status='REJECTED',
                            fail_reason=f'Price {current_price} > cap {cap} (mode={cap_mode})',
                            details={
                                "price": float(current_price),
                                "cap": float(cap),
                                "mode": cap_mode,
                                "buffer_pct": buffer_pct,
                            }
                        )
                        continue

                    # EX-04: ATR Gate — block entry when volatility is abnormally low
                    if bool(indicator_params.get("atr_gate_enabled", True)):
                        atr_blocked: Optional[bool] = None
                        try:
                            atr_blocked = is_entry_blocked_by_atr_gate(
                                df_aggregated.iloc[:-1],
                                atr_length=int(indicator_params.get("atr_gate_length", 14)),
                                lookback=int(indicator_params.get("atr_gate_lookback", 100)),
                                percentile=float(indicator_params.get("atr_gate_percentile", 25.0)),
                                min_bars=int(indicator_params.get("atr_gate_min_bars", 20)),
                            )
                        except (ValueError, KeyError, TypeError) as atr_err:
                            logger.exception("[PaperTrader] ATR gate error for %s — fail-open", asset)
                            atr_blocked = None
                        if atr_blocked is True:
                            self.log_evaluation(
                                strategy_name, asset, timeframe,
                                price=current_price, signal_type='ENTRY',
                                signal_triggered=True, status='REJECTED',
                                fail_reason='ATR gate: volatility below percentile threshold',
                                details={
                                    "gate": "atr_gate",
                                    "price": float(current_price),
                                }
                            )
                            continue
                        if atr_blocked is None:
                            logger.info("[PaperTrader] ATR gate fail-open for %s (insufficient data)", asset)
                        
                    # Calculate quantity to buy
                    # Determine source depending on asset type
                    source = 'bybit' if is_crypto_asset(asset) else 'trading212'
                    
                    # First fetch total portfolio NAV and cash balance from loaded balances
                    balance_row = balances.get(source)
                    if not balance_row:
                        continue
                    cash_balance = balance_row[0]
                    total_nav = balance_row[1]
                    
                    # Kelly sizing: notional value = NAV * kelly_weight
                    kelly_size_cash = total_nav * Decimal(str(kelly_weight))
                    
                    # Capital allocated = min(Kelly Size, cash_balance, initial_capital_bucket, max_capital_bucket)
                    allocated_cash = min(
                        kelly_size_cash,
                        cash_balance,
                        Decimal(str(initial_capital_bucket)),
                        Decimal(str(max_capital_bucket))
                    )
                    if allocated_cash <= 0:
                        self.log_evaluation(
                            strategy_name, asset, timeframe,
                            price=current_price, signal_type='ENTRY',
                            signal_triggered=True, status='REJECTED',
                            fail_reason=f'Kelly size ({kelly_size_cash}) or cash availability ({cash_balance}) results in zero qty',
                            details={
                                "kelly_size": float(kelly_size_cash),
                                "cash_balance": float(cash_balance),
                                "initial_capital_bucket": float(initial_capital_bucket)
                            }
                        )
                        continue
                        
                    if current_price is None or current_price <= Decimal("0"):
                        logger.warning(f"[PaperTrader] Invalid current_price for {asset} on {strategy_name}: {current_price}")
                        self.log_evaluation(
                            strategy_name, asset, timeframe,
                            price=current_price, signal_type='ENTRY',
                            signal_triggered=True, status='FAILED',
                            fail_reason=f'Invalid price: {current_price}'
                        )
                        continue

                    qty = allocated_cash / current_price
                    # Handle fractional precision
                    qty_precision = indicator_params.get("quantity_precision", 6)
                    qty = round(qty, qty_precision)
                    if qty <= 0:
                        self.log_evaluation(
                            strategy_name, asset, timeframe,
                            price=current_price, signal_type='ENTRY',
                            signal_triggered=True, status='REJECTED',
                            fail_reason='Kelly size or cash availability results in zero qty after precision rounding',
                            details={
                                "allocated_cash": float(allocated_cash),
                                "qty_before_round": float(allocated_cash / current_price),
                                "qty_precision": qty_precision
                            }
                        )
                        continue
                        
                    fee_rate = Decimal("0.0010") if source == 'bybit' else Decimal("0.0")
                    actual_cost = qty * current_price
                    buy_fee = actual_cost * fee_rate
                    total_buy_cost = actual_cost + buy_fee
                    
                    if total_buy_cost > cash_balance:
                        # Safety adjust considering the fee
                        qty = cash_balance / (current_price * (Decimal("1.0") + fee_rate))
                        qty = round(qty, qty_precision)
                        actual_cost = qty * current_price
                        buy_fee = actual_cost * fee_rate
                        total_buy_cost = actual_cost + buy_fee
                        if qty <= 0:
                            self.log_evaluation(
                                strategy_name, asset, timeframe,
                                price=current_price, signal_type='ENTRY',
                                signal_triggered=True, status='REJECTED',
                                fail_reason='Kelly size or cash availability results in zero qty after fee adjustment',
                                details={
                                    "cash_balance": float(cash_balance),
                                    "qty_precision": qty_precision
                                }
                            )
                            continue
                    # Pre-Trade Controls check
                    try:
                        from backtest_engine.live.controls import PreTradeController
                        ptc = PreTradeController()
                        pos_key = (asset.lower(), strategy_name, timeframe)
                        current_qty = active_positions[pos_key][1] if pos_key in active_positions else Decimal("0.0")
                        ptc.check_limits(
                            ticker=asset,
                            quantity=qty,
                            price=current_price,
                            current_nav=total_nav,
                            current_position_qty=current_qty,
                            reference_price=Decimal(str(last_closed_bar["close"]))
                        )
                    except Exception as ptce:
                        logger.error(f"[PaperTrader] BUY Order REJECTED by Pre-Trade Controls for {asset} on {strategy_name}: {ptce}")
                        self.log_evaluation(
                            strategy_name, asset, timeframe,
                            price=current_price, signal_type='ENTRY',
                            signal_triggered=True, status='REJECTED',
                            fail_reason=f"Pre-Trade Controls Check Failed: {str(ptce)}",
                            details={
                                "qty": float(qty),
                                "price": float(current_price),
                                "current_qty": float(current_qty),
                                "nav": float(total_nav)
                            }
                        )
                        continue

                    # Execute BUY
                    import os
                    import uuid
                    client_order_id = str(uuid.uuid4())
                    if source == 'trading212' and os.getenv("T212_PAPER_ROUTING_ENABLED", "false").lower() == "true":
                        if self.t212_client:
                            try:
                                # Résoudre le ticker Trading 212
                                t212_ticker = self.t212_resolver.resolve(asset)
                                logger.info(f"[PaperTrader] Routing real market BUY order for {asset} (mapped to {t212_ticker}) with client_order_id {client_order_id}: {qty} units")
                                
                                # Placer l'ordre réel (idempotent)
                                order_res = self.t212_client.place_market_order(
                                    ticker=t212_ticker,
                                    quantity=float(qty),
                                    client_order_id=client_order_id
                                )
                                logger.info(f"[PaperTrader] T212 API Order Success: {order_res}")
                            except Exception as e:
                                logger.exception(f"[PaperTrader] T212 API BUY order failed for {asset}")
                                self.log_evaluation(
                                    strategy_name, asset, timeframe,
                                    price=current_price, signal_type='ENTRY',
                                    signal_triggered=True, status='FAILED',
                                    fail_reason=f"T212 API Order Error: {str(e)}"
                                )
                                continue
                        else:
                            logger.error("[PaperTrader] T212 client is missing while T212_PAPER_ROUTING_ENABLED is true")
                            self.log_evaluation(
                                strategy_name, asset, timeframe,
                                price=current_price, signal_type='ENTRY',
                                signal_triggered=True, status='FAILED',
                                fail_reason="T212 client is uninitialized"
                            )
                            continue

                    try:
                        with conn.cursor() as cur:
                            # Lock the balance row first to prevent concurrent balance mutations
                            cur.execute("SELECT paper_cash_balance FROM paper_portfolio_balance WHERE source = %s FOR UPDATE", (source,))
                            
                            # 1. Insert position with RETURNING id for intra-cycle dedup (P1-FIX)
                            cur.execute("""
                                INSERT INTO paper_positions (asset, strategy_name, timeframe, qty, entry_price, current_price, pnl, updated_at, opened_at)
                                VALUES (%s, %s, %s, %s, %s, %s, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                                RETURNING id
                            """, (asset, strategy_name, timeframe, qty, current_price, current_price))
                            new_pos_id = cur.fetchone()[0]
                            
                            # 2. Deduct cash from correct source (deduct total cost with fee, but allocate only actual cost)
                            cur.execute("""
                                UPDATE paper_portfolio_balance 
                                SET paper_cash_balance = paper_cash_balance - %s, 
                                    allocated_balance = allocated_balance + %s,
                                    last_updated = CURRENT_TIMESTAMP
                                WHERE source = %s
                            """, (total_buy_cost, actual_cost, source))
                            
                            # 3. Log transaction
                            cur.execute("""
                                INSERT INTO paper_transactions (asset, strategy_name, action, qty, price, total_value, timestamp)
                                VALUES (%s, %s, 'BUY', %s, %s, %s, CURRENT_TIMESTAMP)
                            """, (asset, strategy_name, qty, current_price, total_buy_cost))
                            
                        conn.commit()
                        # P1-FIX: Inject new position into local state to prevent intra-cycle duplicates
                        active_positions[(asset.lower(), strategy_name, timeframe)] = (new_pos_id, qty, current_price)
                        if redis_client:
                            try:
                                redis_client.delete(f"perf_metrics:{asset.lower()}")
                            except Exception as re_err:
                                logger.warning(f"[PaperTrader] Failed to clear metrics cache for {asset} on BUY: {re_err}")
                        logger.info(f"[PaperTrader] Executed virtual BUY for {asset} ({strategy_name}): {qty} units @ {current_price} € (Cost: {actual_cost} €, Fee: {buy_fee} €, Total: {total_buy_cost} €)")
                        
                        self.log_evaluation(
                            strategy_name, asset, timeframe, 
                            price=current_price, signal_type='ENTRY', 
                            signal_triggered=True, status='EXECUTED', 
                            fail_reason=None,
                            details={
                                "qty": float(qty),
                                "cost": float(actual_cost),
                                "indicator_values": last_closed_result.to_dict() if 'last_closed_result' in locals() else {}
                            }
                        )
                    except psycopg2.Error as db_err:
                        logger.exception("[PaperTrader] Database error executing BUY")
                        conn.rollback()
                        self.log_evaluation(
                            strategy_name, asset, timeframe, 
                            price=current_price, signal_type='ENTRY', 
                            signal_triggered=True, status='ERROR', 
                            fail_reason=f"Database error executing BUY: {db_err}"
                        )
                else:
                    self.log_evaluation(
                        strategy_name, asset, timeframe, 
                        price=current_price, signal_type='ENTRY', 
                        signal_triggered=False, status='NO_SIGNAL', 
                        fail_reason='No long entry signal generated',
                        details={
                            "indicator_values": last_closed_result.to_dict() if 'last_closed_result' in locals() else {}
                        }
                    )
            else:
                # Evaluate Exit
                pos_id, qty, entry_price = position_row
                qty = Decimal(str(qty))
                entry_price = Decimal(str(entry_price))
                
                # Check exit triggers
                trigger_exit = False
                exit_reason = ""
                mhp_block: Optional[dict] = None
                
                # 1. Check strategy's custom long_exit signal (EX-05b: with MHP guard for inverse signals only)
                if long_exit_signal:
                    min_bars = int(indicator_params.get("min_holding_bars", 3))
                    opened_at = positions_opened_at.get((asset.lower(), strategy_name, timeframe))
                    if min_bars > 0 and is_exit_blocked_by_mhp(
                        df_aggregated.index, opened_at, last_closed_time, min_bars,
                    ):
                        bars_since = count_bars_since_entry(df_aggregated.index, opened_at, last_closed_time)
                        mhp_block = {"bars_since": bars_since, "min_bars": min_bars}
                    else:
                        trigger_exit = True
                        exit_reason = "Strategy Exit Signal"
                    
                # 2. Check Broker ExitRules (fixed/net brackets, trailing stops, safety stops)
                if not trigger_exit:
                    from backtest_engine.broker import BrokerSimulator, BrokerConfig, Position as BrokerPosition

                    sim_key = (strategy_name, asset.lower())
                    cached_broker = self._broker_simulators.get(sim_key)

                    # A-05: Reuse broker + exit orchestrator if already cached, only update dynamic fields
                    if cached_broker is None:
                        broker_config = BrokerConfig(
                            account_currency=indicator_params.get("account_currency", "EUR"),
                            asset_currency=indicator_params.get("asset_currency", "EUR"),
                            point_value=indicator_params.get("point_value", 1.0)
                        )
                        broker = BrokerSimulator(broker_config)
                        exit_rules = []

                        use_bracket = indicator_params.get("use_net_bracket_exits", False) or indicator_params.get("enable_stop_loss", False) or indicator_params.get("enable_take_profit", False)
                        if use_bracket:
                            from backtest_engine.broker import NetBracketExitRule
                            tp = indicator_params.get("take_profit_pct") if indicator_params.get("enable_take_profit") else indicator_params.get("take_profit_net_percent")
                            sl = indicator_params.get("stop_loss_pct") if indicator_params.get("enable_stop_loss") else indicator_params.get("stop_loss_net_percent")
                            exit_rules.append(NetBracketExitRule(broker, tp_pct=tp, sl_pct=sl))
                        if indicator_params.get("enable_trailing_stop", False):
                            from backtest_engine.broker import TrailingStopExitRule
                            exit_rules.append(TrailingStopExitRule(
                                broker,
                                trail_profit_pct=indicator_params.get("trail_profit_pct", 0.5),
                                trail_loss_pct=indicator_params.get("trail_loss_pct", 0.5),
                            ))
                        if indicator_params.get("use_safety_stop", False):
                            from backtest_engine.broker import SafetyStopExitRule
                            exit_rules.append(SafetyStopExitRule(
                                broker,
                                applies_to=indicator_params.get("safety_stop_applies_to", "Both"),
                                mode=indicator_params.get("safety_stop_mode", "Net loss only"),
                                max_loss_mode=indicator_params.get("safety_max_net_loss_mode", "Cash amount"),
                                max_loss_cash=indicator_params.get("safety_max_net_loss_cash"),
                                max_loss_pct=indicator_params.get("safety_max_net_loss_percent"),
                                max_bars=indicator_params.get("safety_max_bars_in_trade", 0),
                            ))

                        if exit_rules:
                            from backtest_engine.broker import ExitOrchestrator
                            broker.exit_orchestrator = ExitOrchestrator(exit_rules)
                        else:
                            broker.exit_orchestrator = None
                        self._broker_simulators[sim_key] = (broker, exit_rules)
                    else:
                        broker, exit_rules = cached_broker
                        # Re-apply shared broker reference on cached rules (they hold a ref to the old broker)
                        if exit_rules:
                            for rule in exit_rules:
                                rule.broker = broker
                            broker.exit_orchestrator = broker.exit_orchestrator or broker.__dict__.get('exit_orchestrator')

                    # Update dynamic per-cycle fields on the (shared) broker instance
                    from backtest_engine.broker import _OpenPositionEntry
                    broker.cash = float(qty * entry_price)
                    broker._open_entry = _OpenPositionEntry(
                        timestamp=last_closed_time,
                        order_id="dummy_entry",
                        remaining_commission=0.0
                    )
                    broker.position = BrokerPosition(signed_quantity=float(qty), average_price=float(entry_price))

                    if exit_rules:
                        # A-05: ExitOrchestrator already set from cache (line 1073) or first creation
                        
                        # We evaluate on the last closed bar
                        bar_dict = last_closed_bar.to_dict()
                        bar_dict["timestamp"] = last_closed_time
                        
                        # We also evaluate on the current live price for immediate SL/TP
                        live_bar_dict = bar_dict.copy()
                        live_bar_dict["close"] = float(current_price)
                        live_bar_dict["timestamp"] = datetime.now(timezone.utc)
                        
                        closed_action = broker.exit_orchestrator.evaluate(bar_dict, broker.position)
                        live_action = broker.exit_orchestrator.evaluate(live_bar_dict, broker.position)
                        
                        action = closed_action or live_action
                        if action:
                            trigger_exit = True
                            exit_reason = f"{action.rule_name}: {action.comment}"
                            
                if trigger_exit:
                    # Pre-Trade Controls check
                    try:
                        from backtest_engine.live.controls import PreTradeController
                        ptc = PreTradeController()
                        
                        # Fetch total portfolio NAV for PTC validation from loaded balances
                        balance_row = balances.get(source)
                        total_nav = balance_row[1] if balance_row else Decimal("0.0")
                        
                        ptc.check_limits(
                            ticker=asset,
                            quantity=-qty,  # Negative for sell/exit
                            price=current_price,
                            current_nav=total_nav,
                            current_position_qty=qty,
                            reference_price=Decimal(str(last_closed_bar["close"]))
                        )
                    except Exception as ptce:
                        logger.error(f"[PaperTrader] SELL Order REJECTED by Pre-Trade Controls for {asset} on {strategy_name}: {ptce}")
                        self.log_evaluation(
                            strategy_name, asset, timeframe,
                            price=current_price, signal_type='EXIT',
                            signal_triggered=True, status='REJECTED',
                            fail_reason=f"Pre-Trade Controls Check Failed: {str(ptce)}",
                            details={
                                "qty": float(-qty),
                                "price": float(current_price),
                                "current_qty": float(qty),
                                "nav": float(total_nav)
                            }
                        )
                        continue

                    # Execute SELL
                    import os
                    import uuid
                    client_order_id = str(uuid.uuid4())
                    if source == 'trading212' and os.getenv("T212_PAPER_ROUTING_ENABLED", "false").lower() == "true":
                        if self.t212_client:
                            try:
                                # Résoudre le ticker Trading 212
                                t212_ticker = self.t212_resolver.resolve(asset)
                                
                                # Déterminer la quantité à vendre réellement sans liquider la micro-position de tracking
                                sell_qty = qty
                                bootstrapper = self.t212_bootstrapper
                                if bootstrapper:
                                    try:
                                        real_positions = self.t212_client.get_positions()
                                        real_qty = Decimal("0")
                                        for pos in real_positions:
                                            if pos.get("instrument", {}).get("ticker") == t212_ticker:
                                                real_qty = Decimal(str(pos.get("quantity", "0")))
                                                break
                                        
                                        if real_qty > Decimal("0"):
                                            micro_qty = Decimal(str(bootstrapper.micro_qty))
                                            max_sellable = real_qty - micro_qty
                                            if max_sellable < Decimal("0"):
                                                max_sellable = Decimal("0")
                                            sell_qty = min(qty, max_sellable)
                                    except Exception as e:
                                        logger.warning(f"[PaperTrader] Failed to adjust sell quantity for {asset} to protect micro-position: {e}")
                                
                                if sell_qty > Decimal("0"):
                                    logger.info(f"[PaperTrader] Routing real market SELL order for {asset} (mapped to {t212_ticker}) with client_order_id {client_order_id}: {-sell_qty} units (target paper qty: {-qty})")
                                    # Placer l'ordre réel (négatif pour la vente) (idempotent)
                                    order_res = self.t212_client.place_market_order(
                                        ticker=t212_ticker,
                                        quantity=float(-sell_qty),
                                        client_order_id=client_order_id
                                    )
                                    logger.info(f"[PaperTrader] T212 API Order Success: {order_res}")
                                else:
                                    logger.info(f"[PaperTrader] Skipping real market SELL order for {asset} (only micro-position of tracking remains).")
                            except Exception as e:
                                logger.exception(f"[PaperTrader] T212 API SELL order failed for {asset}")
                                self.log_evaluation(
                                    strategy_name, asset, timeframe,
                                    price=current_price, signal_type='EXIT',
                                    signal_triggered=True, status='FAILED',
                                    fail_reason=f"T212 API Order Error: {str(e)}",
                                    details={
                                        "qty": float(qty),
                                        "entry_price": float(entry_price),
                                        "current_price": float(current_price)
                                    }
                                )
                                continue
                        else:
                            logger.error("[PaperTrader] T212 client is missing while T212_PAPER_ROUTING_ENABLED is true")
                            self.log_evaluation(
                                strategy_name, asset, timeframe,
                                price=current_price, signal_type='EXIT',
                                signal_triggered=True, status='FAILED',
                                fail_reason="T212 client is uninitialized",
                                details={
                                    "qty": float(qty),
                                    "entry_price": float(entry_price),
                                    "current_price": float(current_price)
                                }
                            )
                            continue

                    actual_revenue = qty * current_price
                    fee_rate = Decimal("0.0010") if source == 'bybit' else Decimal("0.0")
                    sell_fee = actual_revenue * fee_rate
                    net_revenue = actual_revenue - sell_fee
                    
                    # Entry cost with fee was: (qty * entry_price) * (1 + fee_rate)
                    total_entry_cost = (qty * entry_price) * (Decimal("1.0") + fee_rate)
                    pnl = net_revenue - total_entry_cost
                    
                    try:
                        with conn.cursor() as cur:
                            # Lock the balance row first
                            cur.execute("SELECT paper_cash_balance FROM paper_portfolio_balance WHERE source = %s FOR UPDATE", (source,))
                            
                            # Remove position using RETURNING to verify it actually existed
                            cur.execute("DELETE FROM paper_positions WHERE id = %s RETURNING id", (pos_id,))
                            deleted_row = cur.fetchone()
                            if not deleted_row:
                                logger.warning(f"[PaperTrader] Position {pos_id} already closed/deleted by concurrent task. Skipping SELL credit.")
                                conn.rollback()
                                continue
                            
                            # 2. Add cash back and remove allocated balance from correct source
                            if pnl > 0 and source == 'bybit':
                                from backtest_engine.live.utils import get_eurusd_rate
                                eurusd_rate = get_eurusd_rate(conn)
                                pnl_eur = pnl / eurusd_rate
                                cur.execute("""
                                    UPDATE paper_portfolio_balance 
                                    SET paper_cash_balance = paper_cash_balance + %s,
                                        secured_balance = secured_balance + %s,
                                        allocated_balance = GREATEST(0, allocated_balance - %s),
                                        last_updated = CURRENT_TIMESTAMP
                                    WHERE source = %s
                                """, (total_entry_cost, pnl_eur, qty * entry_price, source))
                                # PT-07: Feed the conversion accumulator with realized profit
                                from backtest_engine.live.bybit.conversion.accumulator import AccumulatorBuffer
                                import os
                                threshold = Decimal(os.getenv("BYBIT_CONVERSION_THRESHOLD_USDC", "100"))
                                accumulator = AccumulatorBuffer(threshold=threshold)
                                accumulator.deposit(conn, pnl, trade_ref=f"paper-sell-{pos_id}")
                            else:
                                cur.execute("""
                                    UPDATE paper_portfolio_balance 
                                    SET paper_cash_balance = paper_cash_balance + %s,
                                        allocated_balance = GREATEST(0, allocated_balance - %s),
                                        last_updated = CURRENT_TIMESTAMP
                                    WHERE source = %s
                                """, (net_revenue, qty * entry_price, source))
                            
                            # 3. Log transaction (log net revenue received in total_value)
                            cur.execute("""
                                INSERT INTO paper_transactions (asset, strategy_name, action, qty, price, total_value, timestamp)
                                VALUES (%s, %s, 'SELL', %s, %s, %s, CURRENT_TIMESTAMP)
                            """, (asset, strategy_name, qty, current_price, net_revenue))
                            
                        conn.commit()
                        # P1-FIX: Remove position from local state to prevent intra-cycle stale reads
                        active_positions.pop((asset.lower(), strategy_name, timeframe), None)
                        if redis_client:
                            try:
                                redis_client.delete(f"perf_metrics:{asset.lower()}")
                            except Exception as re_err:
                                logger.warning(f"[PaperTrader] Failed to clear metrics cache for {asset} on SELL: {re_err}")
                        logger.info(f"[PaperTrader] Executed virtual SELL for {asset} ({strategy_name}) [Reason: {exit_reason}]: {qty} units @ {current_price} € (PnL: {pnl} €, Fee: {sell_fee} €, Net Revenue: {net_revenue} €)")
                        
                        # Auto-cicatrisation réactive instantanée si la micro-position a quand même disparu
                        if source == 'trading212' and self.t212_bootstrapper:
                            try:
                                logger.info(f"[PaperTrader] Triggering reactive self-healing bootstrap for {asset} after EXIT.")
                                self.t212_bootstrapper.bootstrap()
                            except Exception as e:
                                logger.error(f"[PaperTrader] Failed to run reactive self-healing bootstrap for {asset}: {e}")
                        
                        self.log_evaluation(
                            strategy_name, asset, timeframe,
                            price=current_price, signal_type='EXIT',
                            signal_triggered=True, status='EXECUTED',
                            fail_reason=f"Exit rule matched: {exit_reason}",
                            details={
                                "qty": float(qty),
                                "entry_price": float(entry_price),
                                "revenue": float(net_revenue),
                                "pnl": float(pnl),
                                "exit_reason": exit_reason
                            }
                        )
                    except psycopg2.Error as db_err:
                        logger.exception("[PaperTrader] Database error executing SELL")
                        conn.rollback()
                        self.log_evaluation(
                            strategy_name, asset, timeframe,
                            price=current_price, signal_type='EXIT',
                            signal_triggered=True, status='ERROR',
                            fail_reason=f"Database error executing SELL: {db_err}"
                        )
                else:
                    # If MHP blocked the strategy exit signal, log BLOCKED_MHP; otherwise NO_SIGNAL
                    if mhp_block:
                        self.log_evaluation(
                            strategy_name, asset, timeframe,
                            price=current_price, signal_type='EXIT',
                            signal_triggered=True, status='BLOCKED_MHP',
                            fail_reason=f'Minimum holding period: {mhp_block["bars_since"]} < {mhp_block["min_bars"]} bars',
                            details={
                                "qty": float(qty),
                                "entry_price": float(entry_price),
                                "current_price": float(current_price),
                                "bars_since": mhp_block["bars_since"],
                                "min_bars": mhp_block["min_bars"],
                            }
                        )
                    else:
                        self.log_evaluation(
                            strategy_name, asset, timeframe,
                            price=current_price, signal_type='EXIT',
                            signal_triggered=False, status='NO_SIGNAL',
                            fail_reason='No exit trigger matched',
                            details={
                                "qty": float(qty),
                                "entry_price": float(entry_price),
                                "current_price": float(current_price),
                                "current_pnl": float((current_price - entry_price) * qty)
                            }
                        )

        # A-02: flush accumulated evaluation logs in a single batch
        self._flush_evaluations(conn)

        # P3: Batch flush all deferred paper_strategy_configs status updates
        if _status_updates:
            try:
                with conn.cursor() as cur:
                    cur.executemany("""
                        UPDATE paper_strategy_configs
                        SET run_status = %s, warmup_progress = %s, last_error = %s
                        WHERE id = %s
                    """, _status_updates)
                conn.commit()
            except psycopg2.Error as e:
                logger.exception("[PaperTrader] Error batch-flushing strategy config status updates")
                try:
                    conn.rollback()
                except psycopg2.Error:
                    pass

        # P6: Timing instrumentation
        t_cycle_end = time.monotonic()
        logger.info(
            "[EvalCycle] Prefetch: %.1fs | SQL candles: %.1fs | Redis prices: %.1fs | "
            "Preprocess+resample: %.1fs | Strategy eval (parallel): %.1fs | "
            "Trade exec+DB: %.1fs | Total: %.1fs (configs=%d)",
            t_after_prefetch - t_cycle_start,
            t_after_sql - t_after_prefetch,
            t_after_redis - t_after_sql,
            t_after_preprocess - t_after_redis,
            t_after_strat_eval - t_after_preprocess,
            t_cycle_end - t_after_strat_eval,
            t_cycle_end - t_cycle_start,
            len(configs),
        )

    def run_conversion_pipeline(self, conn: Any) -> None:
        """
        Pipeline de conversion USDC → EUR via Bybit Spot.
        Exécuté uniquement si BYBIT_CONVERSION_ENABLED=true.
        """
        try:
            from backtest_engine.live.bybit.conversion.accumulator import AccumulatorBuffer
            from backtest_engine.live.bybit.conversion.margin_simulator import UTAMarginSimulator
            from backtest_engine.live.bybit.conversion.spot_router import SpotConversionRouter
            from decimal import Decimal
            import os

            if not self.bybit_client or not self.bybit_client.config.api_key:
                return

            threshold_str = os.getenv("BYBIT_CONVERSION_THRESHOLD", "15.00")
            threshold = Decimal(threshold_str)
            dry_run = os.getenv("BYBIT_CONVERSION_DRY_RUN", "true").lower() == "true"

            accumulator = AccumulatorBuffer(threshold=threshold)
            # PT-18: Reuse cached margin simulator to preserve _conversion_locked TTL
            if self._margin_simulator is None:
                self._margin_simulator = UTAMarginSimulator(self.bybit_client)
            margin_sim = self._margin_simulator
            router = SpotConversionRouter(
                self.bybit_client, accumulator, margin_sim, dry_run=dry_run
            )

            result = router.try_convert(conn)
            if result:
                logger.info(f"[PaperTrader] Conversion result: {result.status.value} "
                            f"({result.qty_usdc} USDC)")
        except Exception as e:
            logger.exception("[PaperTrader] Conversion pipeline error")
