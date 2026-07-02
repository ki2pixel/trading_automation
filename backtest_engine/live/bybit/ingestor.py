import os
import time
import json
import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List, Optional
from backtest_engine.live.ingestion.base import BasePriceIngestor
from backtest_engine.live.bybit.client import BybitClient
from backtest_engine.live.connection import get_db_connection, get_redis_client

class BybitPriceIngestor(BasePriceIngestor):
    """Bybit price and candle ingestor."""

    def __init__(
        self,
        client: BybitClient,
        symbols: Optional[List[str]] = None,
        cache_path: Optional[str] = None
    ):
        self.client = client
        self.symbols = symbols or self._resolve_symbols()
        self.cache_path = cache_path or os.getenv("BYBIT_PRICE_CACHE_PATH") or "/tmp/bybit_prices.json"
        self._running = False
        self._init_db()

    def _resolve_symbols(self) -> List[str]:
        base = self.client.config.base_currency
        raw_assets = os.getenv("BYBIT_ASSETS", "LTC,DOT").split(",")
        return [f"{asset.strip().upper()}{base}" for asset in raw_assets]

    def _init_db(self) -> None:
        """Creates the live prices and candles tables if DATABASE_URL is set."""
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
                        ALTER TABLE live_prices ADD COLUMN IF NOT EXISTS source VARCHAR(50) NOT NULL DEFAULT 'trading212';
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
                print("[BybitIngestor] PostgreSQL tables initialized.")
        except Exception as e:
            print(f"[BybitIngestor] Failed to initialize PostgreSQL tables: {e}")

    def bootstrap_historical_candles(self, limit: int = 1000) -> None:
        """Fetches and inserts historical klines on startup to prevent strategy warmup delay."""
        print(f"[BybitIngestor] Bootstrapping up to {limit} historical 1m candles for {self.symbols}...")
        for symbol in self.symbols:
            try:
                res = self.client.get_klines(symbol, interval="1", limit=limit)
                klines_data = res.get("result", {}).get("list", [])
                if not klines_data:
                    print(f"[BybitIngestor] No historical candles returned for {symbol}")
                    continue
                
                # Bybit returns klines in descending order (newest first).
                # We reverse the list to insert from oldest to newest.
                klines_data = list(reversed(klines_data))
                
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        for k in klines_data:
                            # k[0] is start time in milliseconds string
                            dt = datetime.fromtimestamp(int(k[0]) / 1000.0, tz=timezone.utc)
                            o = Decimal(k[1])
                            h = Decimal(k[2])
                            l = Decimal(k[3])
                            c = Decimal(k[4])
                            
                            cur.execute("""
                                INSERT INTO live_candles_1m (ticker, timestamp_minute, open, high, low, close)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                ON CONFLICT (ticker, timestamp_minute)
                                DO UPDATE SET
                                    open = EXCLUDED.open,
                                    high = EXCLUDED.high,
                                    low = EXCLUDED.low,
                                    close = EXCLUDED.close;
                            """, (symbol.lower(), dt, o, h, l, c))
                        conn.commit()
                print(f"[BybitIngestor] Successfully bootstrapped {len(klines_data)} candles for {symbol.lower()}")
            except Exception as e:
                print(f"[BybitIngestor] Error bootstrapping klines for {symbol}: {e}")

    def poll_and_cache(self) -> Dict[str, float]:
        """Polls current ticker price and recent 1m candles from Bybit and saves them to caches."""
        prices: Dict[str, float] = {}
        for symbol in self.symbols:
            try:
                # 1. Fetch current price
                ticker_data = self.client.get_ticker_price(symbol.upper())
                tickers_list = ticker_data.get("result", {}).get("list", [])
                if not tickers_list:
                    continue
                
                price_val = Decimal(tickers_list[0].get("lastPrice", "0"))
                symbol_lower = symbol.lower()
                prices[symbol_lower] = float(price_val)

                # 2. Fetch last 5 candles to keep live_candles_1m up-to-date
                res = self.client.get_klines(symbol, interval="1", limit=5)
                klines_data = res.get("result", {}).get("list", [])
                
                # 3. Write current price to Redis, PostgreSQL and local cache
                redis_client = get_redis_client()
                if redis_client:
                    try:
                        redis_client.set(f"price:{symbol_lower}", str(price_val))
                    except Exception as re:
                        print(f"[BybitIngestor] Redis error for {symbol_lower}: {re}")

                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        # Write price to live_prices
                        cur.execute("""
                            INSERT INTO live_prices (ticker, price, source, updated_at)
                            VALUES (%s, %s, 'bybit', CURRENT_TIMESTAMP)
                            ON CONFLICT (ticker)
                            DO UPDATE SET price = EXCLUDED.price, source = 'bybit', updated_at = CURRENT_TIMESTAMP;
                        """, (symbol_lower, price_val))

                        # Write klines to live_candles_1m
                        for k in klines_data:
                            dt = datetime.fromtimestamp(int(k[0]) / 1000.0, tz=timezone.utc)
                            o = Decimal(k[1])
                            h = Decimal(k[2])
                            l = Decimal(k[3])
                            c = Decimal(k[4])
                            
                            cur.execute("""
                                INSERT INTO live_candles_1m (ticker, timestamp_minute, open, high, low, close)
                                VALUES (%s, %s, %s, %s, %s, %s)
                                ON CONFLICT (ticker, timestamp_minute)
                                DO UPDATE SET
                                    open = EXCLUDED.open,
                                    high = EXCLUDED.high,
                                    low = EXCLUDED.low,
                                    close = EXCLUDED.close;
                            """, (symbol_lower, dt, o, h, l, c))
                        
                        # Auto-cleanup: keep only last 7 days
                        cur.execute("DELETE FROM live_candles_1m WHERE ticker = %s AND timestamp_minute < NOW() - INTERVAL '7 days'", (symbol_lower,))
                        conn.commit()

            except Exception as e:
                print(f"[BybitIngestor] Error polling {symbol}: {e}")

        if prices:
            self._write_local_cache(prices)
            
        return prices

    def _write_local_cache(self, prices: Dict[str, float]) -> None:
        """Writes current price dictionary to local JSON cache."""
        try:
            temp_path = f"{self.cache_path}.tmp"
            os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
            with open(temp_path, "w") as f:
                json.dump(prices, f)
            os.replace(temp_path, self.cache_path)
        except Exception as e:
            print(f"[BybitIngestor] Failed to write local cache: {e}")

    def read_cache(self) -> Dict[str, float]:
        """Reads cached prices from the JSON file."""
        if not os.path.exists(self.cache_path):
            return {}
        try:
            with open(self.cache_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[BybitIngestor] Failed to read local cache: {e}")
            return {}

    def start_loop(self, interval_seconds: int = 60) -> None:
        """Starts a blocking loop that polls prices at the specified interval."""
        print(f"[BybitIngestor] Starting blocking loop. Interval: {interval_seconds}s")
        import signal
        self._running = True

        def handle_signal(signum, frame):
            print(f"[BybitIngestor] Stopping loop gracefully...")
            self._running = False

        try:
            signal.signal(signal.SIGTERM, handle_signal)
            signal.signal(signal.SIGINT, handle_signal)
        except ValueError:
            pass

        # Bootstrap on startup
        self.bootstrap_historical_candles()

        while self._running:
            try:
                self.poll_and_cache()
            except Exception as e:
                print(f"[BybitIngestor] Error in loop: {e}")
            
            for _ in range(interval_seconds):
                if not self._running:
                    break
                time.sleep(1)
        print("[BybitIngestor] Polling loop stopped.")

    async def start_loop_async(self, interval_seconds: int = 60) -> None:
        """Starts a non-blocking async loop that polls prices at the specified interval."""
        print(f"[BybitIngestor] Starting async polling loop. Interval: {interval_seconds}s")
        self._running = True

        # Bootstrap in thread pool on startup
        await asyncio.to_thread(self.bootstrap_historical_candles)

        while self._running:
            try:
                await asyncio.to_thread(self.poll_and_cache)
            except Exception as e:
                print(f"[BybitIngestor] Error in async loop: {e}")
            
            for _ in range(interval_seconds):
                if not self._running:
                    break
                await asyncio.sleep(1)
        print("[BybitIngestor] Async polling loop stopped.")
