import json
import os
import time
from typing import Dict, Optional
from backtest_engine.live.trading212.client import Trading212Client
from backtest_engine.live.connection import get_db_connection, get_redis_client
from backtest_engine.live.ingestion.base import BasePriceIngestor
from backtest_engine.live.utils import T212_STATIC_MAPPING


class Trading212PriceIngestor(BasePriceIngestor):
    """Tâche d'ingestion de prix pour récupérer les cotations via positions."""

    def __init__(self, client: Trading212Client, cache_path: Optional[str] = None):
        self.client = client
        self.cache_path = cache_path or os.getenv("T212_PRICE_CACHE_PATH") or "/tmp/t212_prices.json"
        self._init_db()


    def _init_db(self) -> None:
        """Creates the prices table if DATABASE_URL is set."""
        try:
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS live_prices (
                                ticker VARCHAR(50) PRIMARY KEY,
                                price NUMERIC(15, 6) NOT NULL,
                                source VARCHAR(50) NOT NULL DEFAULT 'trading212',
                                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                            );
                        """)
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS live_candles_1m (
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
        TICKER_TRANSLATION = {v: k for k, v in T212_STATIC_MAPPING.items()}
            
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
        # Read previous prices from cache first (before overwriting) (N-11)
        prev_prices = self.read_cache()

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
                from datetime import datetime, timezone
                pipe = redis_client.pipeline()
                now_str = datetime.now(timezone.utc).isoformat()
                for ticker, price in prices.items():
                    price_payload = json.dumps({
                        "price": str(price),
                        "timestamp": now_str
                    })
                    pipe.set(f"price:{ticker.lower()}", price_payload, ex=180)
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
                            normalized_ticker = ticker.lower()
                            cur.execute("""
                                INSERT INTO live_prices (ticker, price, source, updated_at)
                                VALUES (%s, %s, 'trading212', CURRENT_TIMESTAMP)
                                ON CONFLICT (ticker)
                                DO UPDATE SET price = EXCLUDED.price, source = 'trading212', updated_at = CURRENT_TIMESTAMP;
                            """, (normalized_ticker, price))
                            
                            # UPSERT for 1m continuous pseudo-candles (N-11)
                            prev_price = prev_prices.get(ticker, price)
                            open_val = prev_price
                            close_val = price
                            high_val = max(open_val, close_val)
                            low_val = min(open_val, close_val)
                            
                            cur.execute("""
                                INSERT INTO live_candles_1m (ticker, timestamp_minute, open, high, low, close)
                                VALUES (%s, date_trunc('minute', CURRENT_TIMESTAMP), %s, %s, %s, %s)
                                ON CONFLICT (ticker, timestamp_minute)
                                DO UPDATE SET 
                                    high = GREATEST(live_candles_1m.high, EXCLUDED.high),
                                    low = LEAST(live_candles_1m.low, EXCLUDED.low),
                                    close = EXCLUDED.close;
                            """, (normalized_ticker, open_val, high_val, low_val, close_val))
                            
                        # Auto-cleanup: keep only last 7 days
                        cur.execute("DELETE FROM live_candles_1m WHERE timestamp_minute < NOW() - INTERVAL '7 days'")
                        
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
