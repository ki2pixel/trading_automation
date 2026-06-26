import json
import os
import time
from typing import Dict, Any, Optional
from backtest_engine.live.trading212.client import Trading212Client
from backtest_engine.live.connection import get_db_connection, get_redis_client

class Trading212PriceIngestor:
    """Tâche d'ingestion de prix pour récupérer les cotations via positions."""

    def __init__(self, client: Trading212Client, cache_path: Optional[str] = None):
        self.client = client
        self.cache_path = cache_path or os.getenv("T212_PRICE_CACHE_PATH") or "/tmp/t212_prices.json"
        self._init_db()

    def _get_db_connection(self):
        """Returns a PostgreSQL connection if DATABASE_URL is configured."""
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            return None
        import psycopg2
        return psycopg2.connect(db_url)

    def _init_db(self) -> None:
        """Creates the prices table if DATABASE_URL is set."""
        try:
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS trading212_prices (
                                ticker VARCHAR(50) PRIMARY KEY,
                                price NUMERIC(15, 6) NOT NULL,
                                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                            );
                        """)
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS trading212_candles_1m (
                                ticker VARCHAR(50),
                                timestamp_minute TIMESTAMP WITH TIME ZONE,
                                open NUMERIC(15, 6) NOT NULL,
                                high NUMERIC(15, 6) NOT NULL,
                                low NUMERIC(15, 6) NOT NULL,
                                close NUMERIC(15, 6) NOT NULL,
                                PRIMARY KEY (ticker, timestamp_minute)
                            );
                        """)
                        conn.commit()
                    print("[PriceIngestor] PostgreSQL prices table initialized.")
            except RuntimeError as re:
                if "DATABASE_URL not configured" in str(re):
                    print("[PriceIngestor] PostgreSQL database not configured. Skipping initialization.")
                else:
                    raise
        except Exception as e:
            print(f"[PriceIngestor] Failed to initialize PostgreSQL table: {e}")

    def poll_and_cache(self) -> Dict[str, float]:
        """Polls open positions, extracts current prices, and saves them to the cache file."""
        print("[PriceIngestor] Polling Trading 212 positions for realtime prices...")
        try:
            positions = self.client.get_positions()
        except Exception as e:
            print(f"[PriceIngestor] Error fetching positions: {e}")
            return self.read_cache()
            
        # Translation map: Internal T212 API tickers -> User's frontend/warmup tickers
        TICKER_TRANSLATION = {
            'TIMd_EQ': 'ZEAL.CO',
            'NOVCd_EQ': 'NVO',
            'EVDd_EQ': 'EVD.DE',
            'GE9d_EQ': 'GMAB',
            'FPEd_EQ': 'FPE.DE',
            'SAPd_EQ': 'SAP',
            'NOTd1_EQ': 'NVS',
            'AMSe_EQ': 'AMS.MC',
            'DPWd_EQ': 'dpwdeeur',
            'TW10d_EQ': 'teniteur',
            'AKZAa_EQ': 'akzanleur',
            'DAId_EQ': 'daideeur',
            'MRKd_EQ': 'mrkdeeur',
            'VNAd_EQ': 'vnadeeur',
            'ACp_EQ': 'acfreur',
            'LXSd_EQ': 'lxsdeeur',
            'RANDa_EQ': 'randnleur',
            'RUIp_EQ': 'rifreur',
            'ABI_BE_EQ': 'abibeeur',
            'PROX_BE_EQ': 'belgbeeur',
            'CAp_EQ': 'cafreur'
        }
            
        prices: Dict[str, float] = {}
        for pos in positions:
            raw_ticker = pos.get("instrument", {}).get("ticker")
            if raw_ticker not in TICKER_TRANSLATION:
                print(f"[PriceIngestor] Ignoring unauthorized raw ticker: {raw_ticker}")
                continue
            ticker = TICKER_TRANSLATION[raw_ticker]
            
            # Extract price. API can return currentPrice or price depending on schema.
            # Fallback values from position schema: currentPrice, averagePricePaid, etc.
            price = pos.get("currentPrice")
            if price is None:
                price = pos.get("price")
                
            if price is not None:
                try:
                    prices[ticker] = float(price)
                except (ValueError, TypeError):
                    pass
                    
        if prices:
            self._write_cache(prices)
            print(f"[PriceIngestor] Successfully ingested and cached {len(prices)} prices.")
        else:
            print("[PriceIngestor] No pricing data found in positions.")
            
        return prices

    def _write_cache(self, prices: Dict[str, float]) -> None:
        """Writes price dictionary to the JSON cache file, Redis, and database."""
        # 1. Write to local JSON file
        try:
            temp_path = f"{self.cache_path}.tmp"
            os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
            with open(temp_path, "w") as f:
                json.dump(prices, f)
            os.replace(temp_path, self.cache_path)
        except Exception as e:
            print(f"[PriceIngestor] Failed to write price cache: {e}")

        # 1.5 Write to Redis (Upstash)
        redis_client = get_redis_client()
        if redis_client:
            try:
                pipe = redis_client.pipeline()
                for ticker, price in prices.items():
                    pipe.set(f"price:{ticker}", str(price))
                pipe.execute()
                print(f"[PriceIngestor] Successfully published {len(prices)} prices to Redis.")
            except Exception as e:
                print(f"[PriceIngestor] Failed to write to Redis cache: {e}")

        # 2. Write to PostgreSQL (from connection pool)
        try:
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        for ticker, price in prices.items():
                            cur.execute("""
                                INSERT INTO trading212_prices (ticker, price, updated_at)
                                VALUES (%s, %s, CURRENT_TIMESTAMP)
                                ON CONFLICT (ticker)
                                DO UPDATE SET price = EXCLUDED.price, updated_at = CURRENT_TIMESTAMP;
                            """, (ticker, price))
                            
                            # UPSERT for 1m continuous pseudo-candles
                            cur.execute("""
                                INSERT INTO trading212_candles_1m (ticker, timestamp_minute, open, high, low, close)
                                VALUES (%s, date_trunc('minute', CURRENT_TIMESTAMP), %s, %s, %s, %s)
                                ON CONFLICT (ticker, timestamp_minute)
                                DO UPDATE SET 
                                    high = GREATEST(trading212_candles_1m.high, EXCLUDED.high),
                                    low = LEAST(trading212_candles_1m.low, EXCLUDED.low),
                                    close = EXCLUDED.close;
                            """, (ticker, price, price, price, price))
                            
                        # Auto-cleanup: keep only last 24h
                        cur.execute("DELETE FROM trading212_candles_1m WHERE timestamp_minute < NOW() - INTERVAL '24 hours'")
                        
                        conn.commit()
                    print(f"[PriceIngestor] Successfully updated {len(prices)} prices and 1m candles in PostgreSQL.")
            except RuntimeError as re:
                if "DATABASE_URL not configured" in str(re):
                    # Silently skip if DB is not configured (local cache only)
                    pass
                else:
                    raise
        except Exception as e:
            print(f"[PriceIngestor] Failed to write to PostgreSQL cache: {e}")

    def read_cache(self) -> Dict[str, float]:
        """Reads cached prices from the JSON file."""
        if not os.path.exists(self.cache_path):
            return {}
        try:
            with open(self.cache_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[PriceIngestor] Failed to read price cache: {e}")
            return {}

    def start_loop(self, interval_seconds: int = 60) -> None:
        """Starts a blocking loop that polls prices at the specified interval."""
        print(f"[PriceIngestor] Starting polling loop. Interval: {interval_seconds}s")
        import signal
        self._running = True

        def handle_signal(signum, frame):
            print(f"[PriceIngestor] Received signal {signum}. Stopping loop gracefully...")
            self._running = False

        try:
            signal.signal(signal.SIGTERM, handle_signal)
            signal.signal(signal.SIGINT, handle_signal)
        except ValueError:
            # Fallback if not running in the main thread
            pass

        while self._running:
            try:
                self.poll_and_cache()
            except Exception as e:
                print(f"[PriceIngestor] Unexpected error in polling loop: {e}")
            
            # Sleep in 1-second increments to respond to signals quickly
            for _ in range(interval_seconds):
                if not self._running:
                    break
                time.sleep(1)
        print("[PriceIngestor] Polling loop stopped cleanly.")

    async def start_loop_async(self, interval_seconds: int = 60) -> None:
        """Starts a non-blocking async loop that polls prices at the specified interval."""
        print(f"[PriceIngestor] Starting async polling loop. Interval: {interval_seconds}s")
        import asyncio
        self._running = True

        while self._running:
            try:
                await asyncio.to_thread(self.poll_and_cache)
            except Exception as e:
                print(f"[PriceIngestor] Unexpected error in async polling loop: {e}")
            
            for _ in range(interval_seconds):
                if not self._running:
                    break
                await asyncio.sleep(1)
        print("[PriceIngestor] Async polling loop stopped cleanly.")


if __name__ == "__main__":
    # Executable entry point for manual validation
    from backtest_engine.live.trading212.config import Trading212Config
    
    config = Trading212Config()
    client = Trading212Client(config)
    ingestor = Trading212PriceIngestor(client)
    
    # Run a single poll or start loop based on arguments/default
    ingestor.poll_and_cache()
