import os
import sys
import threading
import time
from fastapi import FastAPI
import uvicorn

from backtest_engine.live.trading212.config import Trading212Config
from backtest_engine.live.trading212.client import Trading212Client
from backtest_engine.live.trading212.resolver import Trading212TickerResolver
from backtest_engine.live.trading212.bootstrapper import Trading212Bootstrapper
from backtest_engine.live.trading212.ingestor import Trading212PriceIngestor
from backtest_engine.live.connection import get_db_connection, get_redis_client

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    global background_task
    polling_interval = int(os.getenv("T212_POLLING_INTERVAL", "60"))
    if ingestor is not None:
        import asyncio
        background_task = asyncio.create_task(
            ingestor.start_loop_async(interval_seconds=polling_interval)
        )
        print("[Runner] Started background async polling task.")
    yield
    if ingestor is not None:
        ingestor._running = False
    if background_task is not None:
        try:
            await background_task
        except asyncio.CancelledError:
            pass
    print("[Runner] Stopped background async polling task.")

app = FastAPI(title="Trading 212 Price Ingestor API", lifespan=lifespan)
ingestor = None
background_task = None

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/keep-alive")
def keep_alive():
    return {"status": "alive", "timestamp": time.time()}

@app.get("/prices")
def get_prices():
    # 1. Try fetching from Redis (Upstash)
    redis_client = get_redis_client()
    if redis_client:
        try:
            keys = redis_client.keys("price:*")
            if keys:
                prices = {}
                for key in keys:
                    ticker = key.split("price:")[1]
                    price_val = redis_client.get(key)
                    if price_val is not None:
                        prices[ticker] = float(price_val)
                return prices
        except Exception as e:
            print(f"[Runner] Failed to fetch prices from Redis: {e}")

    # 2. Fallback to PostgreSQL via Connection Pool
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        try:
            prices = {}
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT ticker, price FROM trading212_prices")
                    rows = cur.fetchall()
                    for ticker, price in rows:
                        prices[ticker] = float(price)
            return prices
        except Exception as e:
            print(f"[Runner] Failed to fetch prices from PostgreSQL: {e}")
            # Fallback to local JSON cache below
            
    if ingestor is None:
        return {}
    return ingestor.read_cache()

def run_polling_loop(ingestor_instance, interval):
    try:
        ingestor_instance.start_loop(interval_seconds=interval)
    except Exception as e:
        print(f"[Runner] Background polling thread failed: {e}")

def main():
    global ingestor
    
    # 1. Config loading and validation
    config = Trading212Config()
    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
        
    client = Trading212Client(config)
    
    # 2. Bootstrapping (optional)
    bootstrap_env = os.getenv("T212_BOOTSTRAP", "false").lower()
    if bootstrap_env in ("true", "1", "yes"):
        print("[Runner] Running bootstrap procedure...")
        try:
            resolver = Trading212TickerResolver(client)
            bootstrapper = Trading212Bootstrapper(client, resolver)
            bootstrapper.bootstrap()
        except Exception as e:
            print(f"[Runner] Bootstrap failed: {e}", file=sys.stderr)
            # Do not crash the process if bootstrap fails, to ensure resilience
            
    # 3. Create ingestor
    ingestor = Trading212PriceIngestor(client)
    
    # 4. Mode routing
    mode = os.getenv("T212_INGESTOR_MODE", "worker").lower()
    polling_interval = int(os.getenv("T212_POLLING_INTERVAL", "60"))
    
    if mode == "web":
        port = int(os.getenv("PORT", "8080"))
        host = os.getenv("HOST", "0.0.0.0")
        print(f"[Runner] Starting ingestor in WEB mode on {host}:{port}...")
        uvicorn.run(app, host=host, port=port, log_level="info")
    else:
        print(f"[Runner] Starting ingestor in WORKER mode (async)...")
        import asyncio
        try:
            asyncio.run(ingestor.start_loop_async(interval_seconds=polling_interval))
        except KeyboardInterrupt:
            print("[Runner] Ingestor stopped by keyboard interrupt.")

if __name__ == "__main__":
    main()
