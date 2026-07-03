import os
import json
import logging
from decimal import Decimal
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np

from backtest_engine.live.utils import is_crypto_asset, is_market_open

logger = logging.getLogger("papertrader")



class SignalExecutor:
    """Encapsulates paper trading strategy evaluation, trade execution, and NAV calculations."""

    def __init__(self, engine=None, t212_client=None, bybit_client=None, market_hours=None, is_market_open_func=None):
        self.engine = engine
        self._t212_client = t212_client
        self._bybit_client = bybit_client
        self.market_hours = market_hours or {}
        self._is_market_open_func = is_market_open_func

    @property
    def t212_client(self):
        if self.engine:
            return getattr(self.engine, "t212_client", None)
        return self._t212_client

    @t212_client.setter
    def t212_client(self, value):
        self._t212_client = value

    @property
    def bybit_client(self):
        if self.engine:
            return getattr(self.engine, "bybit_client", None)
        return self._bybit_client

    @bybit_client.setter
    def bybit_client(self, value):
        self._bybit_client = value

    def is_market_open(self, asset: str) -> bool:
        if self._is_market_open_func:
            return self._is_market_open_func(asset)
        import datetime as dt
        current_time = None
        try:
            current_time = datetime.now(dt.timezone.utc)
        except Exception:
            pass
        return is_market_open(asset, self.market_hours, current_time=current_time)

    def log_evaluation(self, conn, strategy_name, asset, timeframe, price, signal_type, signal_triggered, status, fail_reason=None, details=None):
        def serialize_details(obj):
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
            except Exception as e:
                logger.error(f"[PaperTrader] JSON serialization error for details: {e}")
                details_json = "{}"

        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO paper_evaluations (
                        strategy_name, asset, timeframe, price, signal_type, 
                        signal_triggered, status, fail_reason, details, timestamp
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """, (
                    strategy_name, asset, timeframe, 
                    float(price) if price is not None else None, 
                    signal_type, signal_triggered, status, 
                    fail_reason, details_json
                ))
            conn.commit()
        except Exception as e:
            logger.error(f"[PaperTrader] Error logging evaluation: {e}")
            try:
                conn.rollback()
            except Exception:
                pass

    def update_portfolio_nav(self, conn):
        """
        Update the total NAV of the portfolio based on current prices of positions
        and the cash balance, split by ecosystem (trading212 vs bybit).

        Batched I/O: uses Redis mget() + SQL ANY() + executemany() to avoid N+1 queries.
        """
        from backtest_engine.live.connection import get_redis_client
        redis_client = get_redis_client()
        
        try:
            with conn.cursor() as cur:
                # If Trading 212 Client is active, fetch real-time cash balance and update DB
                if self.t212_client is not None:
                    try:
                        summary = self.t212_client.get_account_summary()
                        if summary and "totalValue" in summary:
                            api_cash = Decimal(str(summary["totalValue"]))
                            cur.execute(
                                "UPDATE paper_portfolio_balance SET cash_balance = %s, last_updated = CURRENT_TIMESTAMP WHERE source = 'trading212'",
                                (api_cash,)
                            )
                    except Exception as api_err:
                        logger.error(f"[PaperTrader] Failed to fetch account summary from Trading 212 API: {api_err}")

                # If Bybit Client is active, fetch real-time cash balance (USDC/USDT) and update DB
                if self.bybit_client is not None:
                    try:
                        base_coin = self.bybit_client.config.base_currency
                        summary = self.bybit_client.get_account_summary(coin=base_coin)
                        bybit_balance = Decimal("0")
                        for acc in summary.get("result", {}).get("list", []):
                            for coin_info in acc.get("coin", []):
                                if coin_info.get("coin") == base_coin:
                                    bybit_balance = Decimal(coin_info.get("walletBalance", "0"))
                                    break
                        if bybit_balance > 0:
                            cur.execute(
                                "UPDATE paper_portfolio_balance SET cash_balance = %s, last_updated = CURRENT_TIMESTAMP WHERE source = 'bybit'",
                                (bybit_balance,)
                            )
                    except Exception as api_err:
                        logger.error(f"[PaperTrader] Failed to fetch account summary from Bybit API: {api_err}")

                # Fetch cash and secured balances for both ecosystems
                cur.execute("SELECT source, cash_balance, secured_balance FROM paper_portfolio_balance")
                rows = cur.fetchall()
                balances = {r[0]: Decimal(str(r[1])) for r in rows}
                secured_balances = {r[0]: Decimal(str(r[2])) for r in rows}
                
                t212_nav = balances.get("trading212", Decimal("100000"))
                bybit_nav = balances.get("bybit", Decimal("10000"))
                bybit_secured = secured_balances.get("bybit", Decimal("0"))

                # Get open positions (single query)
                cur.execute("SELECT id, asset, qty, entry_price, current_price FROM paper_positions")
                positions = cur.fetchall()
                
                # Retrieve exchange rate to integrate secured_balance (in EUR) converted to USDC/USDT in Bybit total NAV
                from backtest_engine.live.paper_trading.engine import get_eurusd_rate
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
                    if redis_client:
                        try:
                            redis_values = redis_client.mget(redis_keys)
                            for ticker, val in zip(tickers, redis_values):
                                if val is not None:
                                    redis_prices[ticker] = Decimal(str(val))
                        except Exception as redis_err:
                            logger.error(f"[PaperTrader] Redis mget error: {redis_err}")

                    # 2. Batch SQL fallback for tickers not found in Redis (single query)
                    missing_tickers = [t for t in tickers if t not in redis_prices]
                    sql_prices = {}
                    if missing_tickers:
                        cur.execute(
                            "SELECT ticker, price, updated_at FROM live_prices WHERE ticker = ANY(%s)",
                            (missing_tickers,)
                        )
                        now_utc = datetime.now(timezone.utc)
                        for row in cur.fetchall():
                            ticker, price, updated_at = row[0], row[1], row[2]
                            sql_prices[ticker] = Decimal(str(price))
                            # Check freshness (3 minutes warning)
                            if updated_at:
                                if updated_at.tzinfo is None:
                                    updated_at = updated_at.replace(tzinfo=timezone.utc)
                                age = now_utc - updated_at
                                if age > timedelta(minutes=3):
                                    logger.warning(f"[PaperTrader] WARNING: price for {ticker} is stale (age: {age.total_seconds():.0f}s). Using it anyway.")

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
        except Exception as e:
            logger.error(f"[PaperTrader] Error updating NAV: {e}")
            conn.rollback()

    def evaluate_and_execute_strategies(self, conn):
        """
        Evaluate active strategy configurations on recent price history and execute trade signals.
        """
        from backtest_engine.strategy_registry import StrategyRegistry
        from backtest_engine.live.connection import get_redis_client
        redis_client = get_redis_client()
        
        # 1. Fetch active configurations
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, strategy_name, asset, timeframe, kelly_weight, 
                       initial_capital, initial_capital_bucket, max_capital_bucket, max_entry_price, indicator_params
                FROM paper_strategy_configs
                WHERE is_active = TRUE
            """)
            configs = cur.fetchall()
            
        for config_id, strategy_name, asset, timeframe, kelly_weight, initial_capital, initial_capital_bucket, max_capital_bucket, max_entry_price, indicator_params in configs:
            indicator_params = indicator_params or {}
            # Check market hours
            if not self.is_market_open(asset):
                continue
                
            source = 'bybit' if is_crypto_asset(asset) else 'trading212'
                
            # Check if we have an active position for this strategy + asset
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, qty, entry_price FROM paper_positions 
                    WHERE asset = %s AND strategy_name = %s LIMIT 1
                """, (asset, strategy_name))
                position_row = cur.fetchone()
                
            has_position = position_row is not None
            
            # Fetch 1m candles for this asset (up to 7 days = 10080 minutes)
            # Fetch only what's necessary (let's say 10000 bars)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT timestamp_minute, open, high, low, close
                    FROM live_candles_1m
                    WHERE ticker = %s
                    ORDER BY timestamp_minute ASC
                    LIMIT 10000
                """, (asset.lower(),))
                candle_rows = cur.fetchall()
                
            if len(candle_rows) < 10:
                # Not enough history (Warmup)
                try:
                    with conn.cursor() as cur:
                        cur.execute("UPDATE paper_strategy_configs SET run_status = 'waiting_data' WHERE id = %s", (config_id,))
                    conn.commit()
                except Exception as e:
                    logger.error(f"[PaperTrader] Error updating run_status for config {config_id}: {e}")
                self.log_evaluation(
                    conn, strategy_name, asset, timeframe, 
                    price=None, signal_type='EXIT' if has_position else 'ENTRY', 
                    signal_triggered=False, status='WAITING_DATA', 
                    fail_reason='Not enough candle history'
                )
                continue
                
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
            df_aggregated["volume"] = 0.0 # dummy volume
            
            # Calculate dynamic warmup period based on indicator parameters
            min_bars_needed = 2
            if indicator_params:
                lookbacks = [50] # Default safe lookback when config is populated
                for k, v in indicator_params.items():
                    if isinstance(v, (int, float)):
                        k_lower = k.lower()
                        if any(term in k_lower for term in ["length", "period", "len", "lookback", "window", "bars"]):
                            lookbacks.append(int(v))
                min_bars_needed = max(lookbacks)

            if len(df_aggregated) < min_bars_needed:
                try:
                    with conn.cursor() as cur:
                        cur.execute("UPDATE paper_strategy_configs SET run_status = 'waiting_data' WHERE id = %s", (config_id,))
                    conn.commit()
                except Exception as e:
                    logger.error(f"[PaperTrader] Error updating run_status for config {config_id}: {e}")
                self.log_evaluation(
                    conn, strategy_name, asset, timeframe, 
                    price=None, signal_type='EXIT' if has_position else 'ENTRY', 
                    signal_triggered=False, status='WAITING_DATA', 
                    fail_reason='Not enough candle history'
                )
                continue
                
            # Get latest closed bar (the one before the very last in-progress bar)
            last_closed_bar = df_aggregated.iloc[-2]
            last_closed_time = df_aggregated.index[-2]
            
            # Let's run the strategy signals on the aggregated data
            try:
                strat_info = StrategyRegistry.get(strategy_name)
                # Parse config overrides
                overrides = strat_info.overrides_from_mapping_function(indicator_params)
                
                # Run backtest_engine's strategy execution
                # We disable full metrics to be super fast
                run_result = strat_info.run_function(
                    data=df_aggregated,
                    symbol=asset,
                    overrides=overrides,
                    initial_capital=float(initial_capital_bucket),
                    timeframe_minutes=timeframe,
                    compute_full_metrics=False
                )
                
                # Check signals on the last closed bar
                result_bars = run_result.bars
                
                # Find the index corresponding to our last closed bar
                last_closed_result = result_bars.loc[last_closed_time]
                
                long_entry_signal = bool(last_closed_result.get('long_entry', False))
                long_exit_signal = bool(last_closed_result.get('long_exit', False))
                
                # Success - Set status to active and reset last_error
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE paper_strategy_configs 
                        SET run_status = 'active', last_error = NULL 
                        WHERE id = %s
                    """, (config_id,))
                conn.commit()
                
            except Exception as strat_err:
                logger.error(f"[PaperTrader] Error running strategy {strategy_name} for {asset}: {strat_err}")
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE paper_strategy_configs 
                            SET run_status = 'error', last_error = %s 
                            WHERE id = %s
                        """, (str(strat_err), config_id))
                    conn.commit()
                except Exception as e:
                    logger.error(f"[PaperTrader] Error updating run_status for config {config_id}: {e}")
                self.log_evaluation(
                    conn, strategy_name, asset, timeframe, 
                    price=None, signal_type='EXIT' if has_position else 'ENTRY', 
                    signal_triggered=False, status='ERROR', 
                    fail_reason=str(strat_err)
                )
                continue
                
            # Fetch current live price (Redis first, then Postgres)
            current_price = None
            if redis_client:
                try:
                    redis_val = redis_client.get(f"price:{asset.lower()}")
                    if redis_val is not None:
                        current_price = Decimal(str(redis_val))
                except Exception as re:
                    logger.error(f"[PaperTrader] Redis read error: {re}")
            if current_price is None:
                with conn.cursor() as cur:
                    cur.execute("SELECT price FROM live_prices WHERE ticker = %s", (asset.lower(),))
                    price_row = cur.fetchone()
                    if price_row:
                        current_price = Decimal(str(price_row[0]))
            if current_price is None:
                # No price available
                self.log_evaluation(
                    conn, strategy_name, asset, timeframe,
                    price=None, signal_type='EXIT' if has_position else 'ENTRY',
                    signal_triggered=False, status='WAITING_DATA',
                    fail_reason='No price available'
                )
                continue
                
            if not has_position:
                # Evaluate Entry (Long Only)
                if long_entry_signal:
                    # Check maximum entry price rule
                    if current_price > Decimal(str(max_entry_price)):
                        logger.info(f"[PaperTrader] Entry rejected for {asset}: price ({current_price}) exceeds max_entry_price ({max_entry_price})")
                        self.log_evaluation(
                            conn, strategy_name, asset, timeframe, 
                            price=current_price, signal_type='ENTRY', 
                            signal_triggered=True, status='REJECTED', 
                            fail_reason=f'Price {current_price} exceeds max_entry_price {max_entry_price}',
                            details={"price": float(current_price), "max_entry_price": float(max_entry_price)}
                        )
                        continue
                        
                    # Calculate quantity to buy
                    # Determine source depending on asset type
                    source = 'bybit' if asset.lower().endswith(("usdt", "usdc")) else 'trading212'
                    
                    # First fetch total portfolio NAV and cash balance
                    with conn.cursor() as cur:
                        cur.execute("SELECT cash_balance, total_nav FROM paper_portfolio_balance WHERE source = %s", (source,))
                        balance_row = cur.fetchone()
                        
                    if not balance_row:
                        continue
                    cash_balance = Decimal(str(balance_row[0]))
                    total_nav = Decimal(str(balance_row[1]))
                    
                    # Kelly sizing: notional value = NAV * kelly_weight
                    kelly_size_cash = total_nav * Decimal(str(kelly_weight))
                    
                    # Capital allocated = min(Kelly Size, cash_balance, initial_capital_bucket)
                    allocated_cash = min(kelly_size_cash, cash_balance, Decimal(str(initial_capital_bucket)))
                    if allocated_cash <= 0:
                        self.log_evaluation(
                            conn, strategy_name, asset, timeframe,
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
                            conn, strategy_name, asset, timeframe,
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
                            conn, strategy_name, asset, timeframe,
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
                                conn, strategy_name, asset, timeframe,
                                price=current_price, signal_type='ENTRY',
                                signal_triggered=True, status='REJECTED',
                                fail_reason='Kelly size or cash availability results in zero qty after fee adjustment',
                                details={
                                    "cash_balance": float(cash_balance),
                                    "qty_precision": qty_precision
                                }
                            )
                            continue
                            
                    # Execute BUY
                    try:
                        with conn.cursor() as cur:
                            # 1. Insert position
                            cur.execute("""
                                INSERT INTO paper_positions (asset, strategy_name, qty, entry_price, current_price, pnl, updated_at)
                                VALUES (%s, %s, %s, %s, %s, 0, CURRENT_TIMESTAMP)
                            """, (asset, strategy_name, qty, current_price, current_price))
                            
                            # 2. Deduct cash from correct source (deduct total cost with fee, but allocate only actual cost)
                            cur.execute("""
                                UPDATE paper_portfolio_balance 
                                SET cash_balance = cash_balance - %s, 
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
                        logger.info(f"[PaperTrader] Executed virtual BUY for {asset} ({strategy_name}): {qty} units @ {current_price} € (Cost: {actual_cost} €, Fee: {buy_fee} €, Total: {total_buy_cost} €)")
                        
                        self.log_evaluation(
                            conn, strategy_name, asset, timeframe, 
                            price=current_price, signal_type='ENTRY', 
                            signal_triggered=True, status='EXECUTED', 
                            fail_reason=None,
                            details={
                                "qty": float(qty),
                                "cost": float(actual_cost),
                                "indicator_values": last_closed_result.to_dict() if 'last_closed_result' in locals() else {}
                            }
                        )
                    except Exception as db_err:
                        logger.error(f"[PaperTrader] Database error executing BUY: {db_err}")
                        conn.rollback()
                        self.log_evaluation(
                            conn, strategy_name, asset, timeframe, 
                            price=current_price, signal_type='ENTRY', 
                            signal_triggered=True, status='ERROR', 
                            fail_reason=f"Database error executing BUY: {db_err}"
                        )
                else:
                    self.log_evaluation(
                        conn, strategy_name, asset, timeframe, 
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
                
                # 1. Check strategy's custom long_exit signal
                if long_exit_signal:
                    trigger_exit = True
                    exit_reason = "Strategy Exit Signal"
                    
                # 2. Check Broker ExitRules (fixed/net brackets, trailing stops, safety stops)
                if not trigger_exit:
                    from backtest_engine.broker import BrokerSimulator, BrokerConfig, Position as BrokerPosition
                    
                    broker_config = BrokerConfig(
                        account_currency=indicator_params.get("account_currency", "EUR"),
                        asset_currency=indicator_params.get("asset_currency", "EUR"),
                        point_value=indicator_params.get("point_value", 1.0)
                    )
                    broker = BrokerSimulator(broker_config)
                    broker.cash = float(qty * entry_price)
                    from backtest_engine.broker import _OpenPositionEntry
                    broker._open_entry = _OpenPositionEntry(
                        timestamp=last_closed_time, 
                        order_id="dummy_entry", 
                        remaining_commission=0.0
                    )
                    broker.position = BrokerPosition(signed_quantity=float(qty), average_price=float(entry_price))
                    
                    exit_rules = []
                    # Brackets (SL / TP)
                    use_bracket = indicator_params.get("use_net_bracket_exits", False) or indicator_params.get("enable_stop_loss", False) or indicator_params.get("enable_take_profit", False)
                    if use_bracket:
                        from backtest_engine.broker import NetBracketExitRule
                        tp = indicator_params.get("take_profit_pct") if indicator_params.get("enable_take_profit") else indicator_params.get("take_profit_net_percent")
                        sl = indicator_params.get("stop_loss_pct") if indicator_params.get("enable_stop_loss") else indicator_params.get("stop_loss_net_percent")
                        exit_rules.append(NetBracketExitRule(
                            broker,
                            tp_pct=tp,
                            sl_pct=sl,
                        ))
                    # Trailing Stop
                    if indicator_params.get("enable_trailing_stop", False):
                        from backtest_engine.broker import TrailingStopExitRule
                        exit_rules.append(TrailingStopExitRule(
                            broker,
                            trail_profit_pct=indicator_params.get("trail_profit_pct", 0.5),
                            trail_loss_pct=indicator_params.get("trail_loss_pct", 0.5),
                        ))
                    # Safety Stop
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
                    # Execute SELL
                    actual_revenue = qty * current_price
                    fee_rate = Decimal("0.0010") if source == 'bybit' else Decimal("0.0")
                    sell_fee = actual_revenue * fee_rate
                    net_revenue = actual_revenue - sell_fee
                    
                    # Entry cost with fee was: (qty * entry_price) * (1 + fee_rate)
                    total_entry_cost = (qty * entry_price) * (Decimal("1.0") + fee_rate)
                    pnl = net_revenue - total_entry_cost
                    
                    try:
                        with conn.cursor() as cur:
                            # 1. Remove position
                            cur.execute("DELETE FROM paper_positions WHERE id = %s", (pos_id,))
                            
                            # 2. Add cash back and remove allocated balance from correct source
                            if pnl > 0 and source == 'bybit':
                                from backtest_engine.live.paper_trading.engine import get_eurusd_rate
                                eurusd_rate = get_eurusd_rate(conn)
                                pnl_eur = pnl / eurusd_rate
                                cur.execute("""
                                    UPDATE paper_portfolio_balance 
                                    SET cash_balance = cash_balance + %s,
                                        secured_balance = secured_balance + %s,
                                        allocated_balance = GREATEST(0, allocated_balance - %s),
                                        last_updated = CURRENT_TIMESTAMP
                                    WHERE source = %s
                                """, (total_entry_cost, pnl_eur, qty * entry_price, source))
                            else:
                                cur.execute("""
                                    UPDATE paper_portfolio_balance 
                                    SET cash_balance = cash_balance + %s,
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
                        logger.info(f"[PaperTrader] Executed virtual SELL for {asset} ({strategy_name}) [Reason: {exit_reason}]: {qty} units @ {current_price} € (PnL: {pnl} €, Fee: {sell_fee} €, Net Revenue: {net_revenue} €)")
                        
                        self.log_evaluation(
                            conn, strategy_name, asset, timeframe,
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
                    except Exception as db_err:
                        logger.error(f"[PaperTrader] Database error executing SELL: {db_err}")
                        conn.rollback()
                        self.log_evaluation(
                            conn, strategy_name, asset, timeframe,
                            price=current_price, signal_type='EXIT',
                            signal_triggered=True, status='ERROR',
                            fail_reason=f"Database error executing SELL: {db_err}"
                        )
                else:
                    self.log_evaluation(
                        conn, strategy_name, asset, timeframe,
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

    def run_conversion_pipeline(self, conn):
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

            if not self.bybit_client:
                return

            threshold_str = os.getenv("BYBIT_CONVERSION_THRESHOLD", "15.00")
            threshold = Decimal(threshold_str)
            dry_run = os.getenv("BYBIT_CONVERSION_DRY_RUN", "true").lower() == "true"

            accumulator = AccumulatorBuffer(threshold=threshold)
            margin_sim = UTAMarginSimulator(self.bybit_client)
            router = SpotConversionRouter(
                self.bybit_client, accumulator, margin_sim, dry_run=dry_run
            )

            result = router.try_convert(conn)
            if result:
                logger.info(f"[PaperTrader] Conversion result: {result.status.value} "
                            f"({result.qty_usdc} USDC)")
        except Exception as e:
            logger.error(f"[PaperTrader] Conversion pipeline error: {e}")
