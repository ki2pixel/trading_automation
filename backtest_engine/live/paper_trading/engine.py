import os
import json
import time
import psycopg2
from datetime import datetime
import pytz

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
        if asset not in self.market_hours:
            return False
            
        config = self.market_hours[asset]
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
        if local_time.weekday() >= 5:
            return False
            
        current_time_str = local_time.strftime("%H:%M")
        
        # Lexicographical comparison works for HH:MM format
        return config["open"] <= current_time_str <= config["close"]

    def _update_portfolio_nav(self, conn):
        """
        Update the total NAV of the portfolio based on current prices of positions
        and the cash balance.
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
                                "UPDATE paper_portfolio_balance SET cash_balance = %s, last_updated = CURRENT_TIMESTAMP",
                                (api_cash,)
                            )
                    except Exception as api_err:
                        print(f"[PaperTrader] Failed to fetch account summary from Trading 212 API: {api_err}")

                # Get current cash balance
                cur.execute("SELECT cash_balance FROM paper_portfolio_balance LIMIT 1")
                row = cur.fetchone()
                if not row:
                    return
                cash_balance = Decimal(str(row[0]))

                # Update positions with current prices and calculate total value
                cur.execute("SELECT id, asset, qty, entry_price FROM paper_positions")
                positions = cur.fetchall()
                
                total_nav = cash_balance
                
                for pos_id, asset, qty, entry_price in positions:
                    qty = Decimal(str(qty))
                    entry_price = Decimal(str(entry_price))
                    
                    if not self.is_market_open(asset):
                        # Keep previous current_price if closed
                        cur.execute("SELECT current_price FROM paper_positions WHERE id = %s", (pos_id,))
                        last_price_row = cur.fetchone()
                        if last_price_row and last_price_row[0] is not None:
                            total_nav += (Decimal(str(last_price_row[0])) * qty)
                        continue 
                    
                    # 1. Try reading from Redis first
                    current_price = None
                    if redis_client:
                        try:
                            redis_val = redis_client.get(f"price:{asset}")
                            if redis_val is not None:
                                current_price = Decimal(str(redis_val))
                        except Exception as re:
                            print(f"[PaperTrader] Redis read error for {asset}: {re}")

                    # 2. Fallback to SQL DB
                    if current_price is None:
                        cur.execute("SELECT price, updated_at FROM trading212_prices WHERE ticker = %s", (asset,))
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
                                    print(f"[PaperTrader] WARNING: price for {asset} is stale (age: {age.total_seconds()}s). Using it anyway.")
                    
                    # 3. Fallback to last known position price
                    if current_price is not None:
                        pnl = (current_price - entry_price) * qty
                        cur.execute("""
                            UPDATE paper_positions 
                            SET current_price = %s, pnl = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (current_price, pnl, pos_id))
                        total_nav += (current_price * qty)
                    else:
                        cur.execute("SELECT current_price FROM paper_positions WHERE id = %s", (pos_id,))
                        last_price_row = cur.fetchone()
                        if last_price_row and last_price_row[0] is not None:
                            last_price = Decimal(str(last_price_row[0]))
                            total_nav += (last_price * qty)
                        
                cur.execute("UPDATE paper_portfolio_balance SET total_nav = %s, last_updated = CURRENT_TIMESTAMP", (total_nav,))
                conn.commit()
        except Exception as e:
            print(f"[PaperTrader] Error updating NAV: {e}")
            conn.rollback()

    def run_cycle(self):
        """Single execution cycle for the paper trader."""
        from backtest_engine.live.connection import get_db_connection
        
        try:
            with get_db_connection() as conn:
                self._update_portfolio_nav(conn)
        except Exception as e:
            print(f"[PaperTrader] Error in run_cycle: {e}")

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


