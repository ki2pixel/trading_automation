import os
import json
import time
from datetime import datetime

class PaperTradingEngine:
    def __init__(self, db_url=None):
        self.db_url = db_url or os.getenv("DATABASE_URL")
        self.market_hours_path = os.path.join(
            os.path.dirname(__file__), "../../../configs/market_hours.json"
        )
        self.market_hours = self._load_market_hours()
        self._running = False

        # Initialize Trading 212 Client resiliently
        from backtest_engine.live.trading212.config import Trading212Config
        from backtest_engine.live.trading212.client import Trading212Client
        try:
            config = Trading212Config()
            config.validate()
            self.t212_client = Trading212Client(config)
            print("[PaperTrader] Trading 212 API client successfully initialized.")
            self.t212_init_error = None
        except Exception as e:
            print(f"[PaperTrader] Trading 212 credentials not configured or invalid, running in local-only mode: {e}")
            self.t212_client = None
            self.t212_init_error = str(e)

        # Initialize Bybit Client resiliently
        from backtest_engine.live.bybit.config import BybitConfig
        from backtest_engine.live.bybit.client import BybitClient
        try:
            bybit_config = BybitConfig()
            bybit_config.validate()
            self.bybit_client = BybitClient(bybit_config)
            print("[PaperTrader] Bybit API client successfully initialized.")
            self.bybit_init_error = None
        except Exception as e:
            print(f"[PaperTrader] Bybit credentials not configured or invalid: {e}")
            self.bybit_client = None
            self.bybit_init_error = str(e)

    def _load_market_hours(self):
        try:
            with open(self.market_hours_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[PaperTrader] Error loading market hours: {e}")
            return {}

    def is_market_open(self, asset):
        """
        Check if the market is open for a given asset based on Mon-Fri and defined hours.
        """
        if asset.lower().endswith("usdt"):
            return True
            
        if asset not in self.market_hours:
            return False
            
        config = self.market_hours[asset]
        if config.get("is_crypto", False) or config.get("exchange") == "CRYPTO":
            return True
            
        timezone_name = config.get("timezone")
        
        # Current UTC time
        import datetime as dt
        utc_now = datetime.now(dt.timezone.utc)
        
        local_time = None
        if timezone_name:
            try:
                from zoneinfo import ZoneInfo
                local_time = utc_now.astimezone(ZoneInfo(timezone_name))
            except Exception:
                try:
                    import pytz
                    local_time = utc_now.astimezone(pytz.timezone(timezone_name))
                except Exception as e:
                    print(f"[PaperTrader] Failed to resolve timezone {timezone_name} for {asset}: {e}")
                    
        if local_time is None:
            # Fallback to static offset parsing if timezone resolution failed
            tz_offset_str = config.get("tz_offset", "+00:00")
            sign = 1 if tz_offset_str[0] == "+" else -1
            try:
                hours_offset = int(tz_offset_str[1:3])
                mins_offset = int(tz_offset_str[4:6])
                import pytz
                local_time = utc_now.astimezone(pytz.FixedOffset(sign * (hours_offset * 60 + mins_offset)))
            except Exception as e:
                print(f"[PaperTrader] Failed to parse static offset {tz_offset_str} for {asset}: {e}")
                local_time = utc_now
        
        # Check if it's weekend (Monday = 0, Sunday = 6)
        # Ne pas appliquer l'exclusion du week-end si c'est de la crypto
        if not config.get("is_crypto", False) and config.get("exchange") != "CRYPTO":
            if local_time.weekday() >= 5:
                return False
            
        current_time_str = local_time.strftime("%H:%M")
        
        # Lexicographical comparison works for HH:MM format
        return config["open"] <= current_time_str <= config["close"]

    def _update_portfolio_nav(self, conn):
        """
        Update the total NAV of the portfolio based on current prices of positions
        and the cash balance, split by ecosystem (trading212 vs binance).
        """
        from decimal import Decimal
        from datetime import datetime, timedelta, timezone
        from backtest_engine.live.connection import get_redis_client
        
        redis_client = get_redis_client()
        
        try:
            with conn.cursor() as cur:
                # If Trading 212 Client is active, fetch real-time cash balance and update DB
                if getattr(self, "t212_client", None) is not None:
                    try:
                        summary = self.t212_client.get_account_summary()
                        if summary and "totalValue" in summary:
                            api_cash = Decimal(str(summary["totalValue"]))
                            cur.execute(
                                "UPDATE paper_portfolio_balance SET cash_balance = %s, last_updated = CURRENT_TIMESTAMP WHERE source = 'trading212'",
                                (api_cash,)
                            )
                    except Exception as api_err:
                        print(f"[PaperTrader] Failed to fetch account summary from Trading 212 API: {api_err}")

                # If Bybit Client is active, fetch real-time cash balance (USDT) and update DB
                if getattr(self, "bybit_client", None) is not None:
                    try:
                        summary = self.bybit_client.get_account_summary()
                        usdt_balance = Decimal("0")
                        for acc in summary.get("result", {}).get("list", []):
                            for coin_info in acc.get("coin", []):
                                if coin_info.get("coin") == "USDT":
                                    usdt_balance = Decimal(coin_info.get("walletBalance", "0"))
                                    break
                        if usdt_balance > 0:
                            cur.execute(
                                "UPDATE paper_portfolio_balance SET cash_balance = %s, last_updated = CURRENT_TIMESTAMP WHERE source = 'bybit'",
                                (usdt_balance,)
                            )
                    except Exception as api_err:
                        print(f"[PaperTrader] Failed to fetch account summary from Bybit API: {api_err}")

                # Fetch cash balances for both ecosystems
                cur.execute("SELECT source, cash_balance FROM paper_portfolio_balance")
                balances = {r[0]: Decimal(str(r[1])) for r in cur.fetchall()}
                
                t212_cash = balances.get("trading212", Decimal("100000"))
                bybit_cash = balances.get("bybit", Decimal("10000"))

                # Get open positions
                cur.execute("SELECT id, asset, qty, entry_price FROM paper_positions")
                positions = cur.fetchall()
                
                t212_nav = t212_cash
                bybit_nav = bybit_cash
                
                for pos_id, asset, qty, entry_price in positions:
                    qty = Decimal(str(qty))
                    entry_price = Decimal(str(entry_price))
                    asset_lower = asset.lower()
                    is_crypto = asset_lower.endswith("usdt")
                    
                    if not self.is_market_open(asset):
                        # Keep previous current_price if closed
                        cur.execute("SELECT current_price FROM paper_positions WHERE id = %s", (pos_id,))
                        last_price_row = cur.fetchone()
                        if last_price_row and last_price_row[0] is not None:
                            val = Decimal(str(last_price_row[0])) * qty
                            if is_crypto:
                                bybit_nav += val
                            else:
                                t212_nav += val
                        continue 
                    
                    # 1. Try reading from Redis first
                    current_price = None
                    if redis_client:
                        try:
                            redis_val = redis_client.get(f"price:{asset_lower}")
                            if redis_val is not None:
                                current_price = Decimal(str(redis_val))
                        except Exception as re:
                            print(f"[PaperTrader] Redis read error for {asset_lower}: {re}")

                    # 2. Fallback to SQL DB
                    if current_price is None:
                        cur.execute("SELECT price, updated_at FROM live_prices WHERE ticker = %s", (asset_lower,))
                        price_row = cur.fetchone()
                        if price_row:
                            current_price = Decimal(str(price_row[0]))
                            updated_at = price_row[1]
                            # Check freshness (3 minutes warning)
                            if updated_at:
                                if updated_at.tzinfo is None:
                                    updated_at = updated_at.replace(tzinfo=timezone.utc)
                                age = datetime.now(timezone.utc) - updated_at
                                if age > timedelta(minutes=3):
                                    print(f"[PaperTrader] WARNING: price for {asset_lower} is stale (age: {age.total_seconds()}s). Using it anyway.")
                    
                    # 3. Fallback to last known position price
                    if current_price is not None:
                        pnl = (current_price - entry_price) * qty
                        cur.execute("""
                            UPDATE paper_positions 
                            SET current_price = %s, pnl = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (current_price, pnl, pos_id))
                        val = current_price * qty
                        if is_crypto:
                            bybit_nav += val
                        else:
                            t212_nav += val
                    else:
                        cur.execute("SELECT current_price FROM paper_positions WHERE id = %s", (pos_id,))
                        last_price_row = cur.fetchone()
                        if last_price_row and last_price_row[0] is not None:
                            last_price = Decimal(str(last_price_row[0]))
                            val = last_price * qty
                            if is_crypto:
                                bybit_nav += val
                            else:
                                t212_nav += val
                                
                cur.execute("UPDATE paper_portfolio_balance SET total_nav = %s, last_updated = CURRENT_TIMESTAMP WHERE source = 'trading212'", (t212_nav,))
                cur.execute("UPDATE paper_portfolio_balance SET total_nav = %s, last_updated = CURRENT_TIMESTAMP WHERE source = 'bybit'", (bybit_nav,))
                conn.commit()
        except Exception as e:
            print(f"[PaperTrader] Error updating NAV: {e}")
            conn.rollback()

    def run_cycle(self):
        """Single execution cycle for the paper trader."""
        from backtest_engine.live.connection import get_db_connection
        
        try:
            with get_db_connection() as conn:
                # 1. Update NAV and active position prices
                self._update_portfolio_nav(conn)
                # 2. Evaluate active strategies and execute signals
                self._evaluate_and_execute_strategies(conn)
                # 3. Clean up old evaluations (Anti-Bloat)
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM paper_evaluations WHERE timestamp < NOW() - INTERVAL '48 hours'")
                conn.commit()
        except Exception as e:
            print(f"[PaperTrader] Error in run_cycle: {e}")

    def _log_evaluation(self, conn, strategy_name, asset, timeframe, price, signal_type, signal_triggered, status, fail_reason=None, details=None):
        import json
        from decimal import Decimal

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
                print(f"[PaperTrader] JSON serialization error for details: {e}")
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
            print(f"[PaperTrader] Error logging evaluation: {e}")
            try:
                conn.rollback()
            except Exception:
                pass

    def _evaluate_and_execute_strategies(self, conn):
        """
        Evaluate active strategy configurations on recent price history and execute trade signals.
        """
        from backtest_engine.strategy_registry import StrategyRegistry
        from decimal import Decimal
        from datetime import datetime, timezone
        
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
            # Check market hours
            if not self.is_market_open(asset):
                continue
                
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
                    print(f"[PaperTrader] Error updating run_status for config {config_id}: {e}")
                self._log_evaluation(
                    conn, strategy_name, asset, timeframe, 
                    price=None, signal_type='EXIT' if has_position else 'ENTRY', 
                    signal_triggered=False, status='WAITING_DATA', 
                    fail_reason='Not enough candle history'
                )
                continue
                
            # Convert to DataFrame
            import pandas as pd
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
                    print(f"[PaperTrader] Error updating run_status for config {config_id}: {e}")
                self._log_evaluation(
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
                print(f"[PaperTrader] Error running strategy {strategy_name} for {asset}: {strat_err}")
                try:
                    with conn.cursor() as cur:
                        cur.execute("""
                            UPDATE paper_strategy_configs 
                            SET run_status = 'error', last_error = %s 
                            WHERE id = %s
                        """, (str(strat_err), config_id))
                    conn.commit()
                except Exception as e:
                    print(f"[PaperTrader] Error updating run_status for config {config_id}: {e}")
                self._log_evaluation(
                    conn, strategy_name, asset, timeframe, 
                    price=None, signal_type='EXIT' if has_position else 'ENTRY', 
                    signal_triggered=False, status='ERROR', 
                    fail_reason=str(strat_err)
                )
                continue
                
            # Fetch current live price (Redis first, then Postgres)
            from backtest_engine.live.connection import get_redis_client
            redis_client = get_redis_client()
            current_price = None
            if redis_client:
                try:
                    redis_val = redis_client.get(f"price:{asset.lower()}")
                    if redis_val is not None:
                        current_price = Decimal(str(redis_val))
                except Exception as re:
                    print(f"[PaperTrader] Redis read error: {re}")
            if current_price is None:
                with conn.cursor() as cur:
                    cur.execute("SELECT price FROM live_prices WHERE ticker = %s", (asset.lower(),))
                    price_row = cur.fetchone()
                    if price_row:
                        current_price = Decimal(str(price_row[0]))
            if current_price is None:
                # No price available
                self._log_evaluation(
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
                        print(f"[PaperTrader] Entry rejected for {asset}: price ({current_price}) exceeds max_entry_price ({max_entry_price})")
                        self._log_evaluation(
                            conn, strategy_name, asset, timeframe, 
                            price=current_price, signal_type='ENTRY', 
                            signal_triggered=True, status='REJECTED', 
                            fail_reason=f'Price {current_price} exceeds max_entry_price {max_entry_price}',
                            details={"price": float(current_price), "max_entry_price": float(max_entry_price)}
                        )
                        continue
                        
                    # Calculate quantity to buy
                    # Determine source depending on asset type
                    source = 'bybit' if asset.lower().endswith("usdt") else 'trading212'
                    
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
                        self._log_evaluation(
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
                        
                    qty = allocated_cash / current_price
                    # Handle fractional precision
                    qty_precision = indicator_params.get("quantity_precision", 6)
                    qty = round(qty, qty_precision)
                    if qty <= 0:
                        self._log_evaluation(
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
                        
                    actual_cost = qty * current_price
                    if actual_cost > cash_balance:
                        # Safety adjust
                        qty = cash_balance / current_price
                        qty = round(qty, qty_precision)
                        actual_cost = qty * current_price
                        if qty <= 0:
                            self._log_evaluation(
                                conn, strategy_name, asset, timeframe,
                                price=current_price, signal_type='ENTRY',
                                signal_triggered=True, status='REJECTED',
                                fail_reason='Kelly size or cash availability results in zero qty',
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
                            
                            # 2. Deduct cash from correct source
                            cur.execute("""
                                UPDATE paper_portfolio_balance 
                                SET cash_balance = cash_balance - %s, 
                                    allocated_balance = allocated_balance + %s,
                                    last_updated = CURRENT_TIMESTAMP
                                WHERE source = %s
                            """, (actual_cost, actual_cost, source))
                            
                            # 3. Log transaction
                            cur.execute("""
                                INSERT INTO paper_transactions (asset, strategy_name, action, qty, price, total_value, timestamp)
                                VALUES (%s, %s, 'BUY', %s, %s, %s, CURRENT_TIMESTAMP)
                            """, (asset, strategy_name, qty, current_price, actual_cost))
                            
                        conn.commit()
                        print(f"[PaperTrader] Executed virtual BUY for {asset} ({strategy_name}): {qty} units @ {current_price} € (Cost: {actual_cost} €)")
                        
                        self._log_evaluation(
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
                        print(f"[PaperTrader] Database error executing BUY: {db_err}")
                        conn.rollback()
                        self._log_evaluation(
                            conn, strategy_name, asset, timeframe, 
                            price=current_price, signal_type='ENTRY', 
                            signal_triggered=True, status='ERROR', 
                            fail_reason=f"Database error executing BUY: {db_err}"
                        )
                else:
                    self._log_evaluation(
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
                    pnl = actual_revenue - (qty * entry_price)
                    
                    try:
                        with conn.cursor() as cur:
                            # 1. Remove position
                            cur.execute("DELETE FROM paper_positions WHERE id = %s", (pos_id,))
                            
                            # 2. Add cash back and remove allocated balance from correct source
                            cur.execute("""
                                UPDATE paper_portfolio_balance 
                                SET cash_balance = cash_balance + %s,
                                    allocated_balance = GREATEST(0, allocated_balance - %s),
                                    last_updated = CURRENT_TIMESTAMP
                                WHERE source = %s
                            """, (actual_revenue, qty * entry_price, source))
                            
                            # 3. Log transaction
                            cur.execute("""
                                INSERT INTO paper_transactions (asset, strategy_name, action, qty, price, total_value, timestamp)
                                VALUES (%s, %s, 'SELL', %s, %s, %s, CURRENT_TIMESTAMP)
                            """, (asset, strategy_name, qty, current_price, actual_revenue))
                            
                        conn.commit()
                        print(f"[PaperTrader] Executed virtual SELL for {asset} ({strategy_name}) [Reason: {exit_reason}]: {qty} units @ {current_price} € (PnL: {pnl} €)")
                        
                        self._log_evaluation(
                            conn, strategy_name, asset, timeframe,
                            price=current_price, signal_type='EXIT',
                            signal_triggered=True, status='EXECUTED',
                            fail_reason=f"Exit rule matched: {exit_reason}",
                            details={
                                "qty": float(qty),
                                "entry_price": float(entry_price),
                                "revenue": float(actual_revenue),
                                "pnl": float(pnl),
                                "exit_reason": exit_reason
                            }
                        )
                    except Exception as db_err:
                        print(f"[PaperTrader] Database error executing SELL: {db_err}")
                        conn.rollback()
                        self._log_evaluation(
                            conn, strategy_name, asset, timeframe,
                            price=current_price, signal_type='EXIT',
                            signal_triggered=True, status='ERROR',
                            fail_reason=f"Database error executing SELL: {db_err}"
                        )
                else:
                    self._log_evaluation(
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

    def start_loop(self, interval_seconds=60):
        self._running = True
        print(f"[PaperTrader] Starting paper trading loop (interval: {interval_seconds}s)...")
        while self._running:
            self.run_cycle()
            time.sleep(interval_seconds)

    async def start_loop_async(self, interval_seconds=60):
        print(f"[PaperTrader] Starting async paper trading loop (interval: {interval_seconds}s)...")
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


