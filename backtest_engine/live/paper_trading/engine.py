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
        tz_offset_str = config.get("tz_offset", "+00:00")
        
        # Simple manual tz parsing for "+01:00" format to hours and minutes
        sign = 1 if tz_offset_str[0] == "+" else -1
        hours_offset = int(tz_offset_str[1:3])
        mins_offset = int(tz_offset_str[4:6])
        
        # Current UTC time
        utc_now = datetime.now(pytz.utc)
        
        # Not handling complex timezone transitions here, just a fixed offset for the MVP
        local_time = utc_now.astimezone(pytz.FixedOffset(sign * (hours_offset * 60 + mins_offset)))
        
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
        try:
            with conn.cursor() as cur:
                # Get current cash balance
                cur.execute("SELECT cash_balance FROM paper_portfolio_balance LIMIT 1")
                row = cur.fetchone()
                if not row:
                    return
                cash_balance = row[0]

                # Update positions with current prices and calculate total value
                cur.execute("SELECT id, asset, qty, entry_price FROM paper_positions")
                positions = cur.fetchall()
                
                total_nav = cash_balance
                
                for pos_id, asset, qty, entry_price in positions:
                    if not self.is_market_open(asset):
                        continue # Keep previous current_price if closed
                    
                    cur.execute("SELECT price FROM trading212_prices WHERE ticker = %s", (asset,))
                    price_row = cur.fetchone()
                    if price_row:
                        current_price = price_row[0]
                        pnl = (current_price - entry_price) * qty
                        cur.execute("""
                            UPDATE paper_positions 
                            SET current_price = %s, pnl = %s, updated_at = CURRENT_TIMESTAMP
                            WHERE id = %s
                        """, (current_price, pnl, pos_id))
                        total_nav += (current_price * qty)
                    else:
                        # If no live price, fallback to last known
                        cur.execute("SELECT current_price FROM paper_positions WHERE id = %s", (pos_id,))
                        last_price = cur.fetchone()[0]
                        total_nav += (last_price * qty)
                        
                cur.execute("UPDATE paper_portfolio_balance SET total_nav = %s, last_updated = CURRENT_TIMESTAMP", (total_nav,))
                conn.commit()
        except Exception as e:
            print(f"[PaperTrader] Error updating NAV: {e}")
            conn.rollback()

    def run_cycle(self):
        """Single execution cycle for the paper trader."""
        if not self.db_url:
            print("[PaperTrader] DATABASE_URL not set. Cannot run cycle.")
            return

        try:
            with psycopg2.connect(self.db_url) as conn:
                # 1. Update Portfolio NAV and Position PnLs
                self._update_portfolio_nav(conn)
                
                # 2. Strategy Execution (Placeholder for future when history is available)
                # print("[PaperTrader] Strategy execution is disabled pending historical data support.")
                
        except Exception as e:
            print(f"[PaperTrader] Error in run_cycle: {e}")

    def start_loop(self, interval_seconds=60):
        self._running = True
        print(f"[PaperTrader] Starting paper trading loop (interval: {interval_seconds}s)...")
        while self._running:
            self.run_cycle()
            time.sleep(interval_seconds)

    def stop(self):
        self._running = False
