import os
import sys
import time
from fastapi import FastAPI
import uvicorn

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from backtest_engine.live.trading212.config import Trading212Config
from backtest_engine.live.trading212.client import Trading212Client
from backtest_engine.live.trading212.resolver import Trading212TickerResolver
from backtest_engine.live.trading212.bootstrapper import Trading212Bootstrapper
from backtest_engine.live.trading212.ingestor import Trading212PriceIngestor

from backtest_engine.live.bybit.config import BybitConfig
from backtest_engine.live.bybit.client import BybitClient
from backtest_engine.live.bybit.ingestor import BybitPriceIngestor

from backtest_engine.live.connection import get_db_connection, get_redis_client, run_postgres_keep_alive_task

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    global background_tasks, t212_ingestor, bybit_ingestor
    import asyncio

    # 1. Initialize Trading 212 Client and Ingestor dynamically if not initialized (Uvicorn worker re-import)
    if t212_ingestor is None:
        t212_env = os.getenv("T212_INGESTOR_ENV", "demo").lower()
        t212_config = Trading212Config(env=t212_env)
        try:
            t212_config.validate()
            t212_client = Trading212Client(t212_config)
            t212_ingestor = Trading212PriceIngestor(t212_client)
            print(f"[Runner] Trading 212 client and ingestor initialized dynamically in lifespan (env={t212_env}).")
        except Exception as e:
            print(f"[Runner] Trading 212 not configured (env={t212_env}): {e}. Skipping.")
            t212_ingestor = None

    # 2. Initialize Bybit Client and Ingestor dynamically if not initialized (Uvicorn worker re-import)
    if bybit_ingestor is None:
        bybit_config = BybitConfig()
        try:
            bybit_config.validate()
            bybit_client = BybitClient(bybit_config)
            bybit_ingestor = BybitPriceIngestor(bybit_client)
            print("[Runner] Bybit client and ingestor initialized dynamically in lifespan.")
        except Exception as e:
            print(f"[Runner] Bybit not configured: {e}. Skipping.")
            bybit_ingestor = None

    polling_interval = int(os.getenv("T212_POLLING_INTERVAL", "60"))

    if t212_ingestor is not None:
        background_tasks.append(
            asyncio.create_task(
                t212_ingestor.start_loop_async(interval_seconds=polling_interval)
            )
        )
        print("[Runner] Started background async Trading 212 polling task.")

    if bybit_ingestor is not None:
        background_tasks.append(
            asyncio.create_task(
                bybit_ingestor.start_loop_async(interval_seconds=polling_interval)
            )
        )
        print("[Runner] Started background async Bybit polling task.")

    # Start database keep-alive heartbeat task
    background_tasks.append(
        asyncio.create_task(
            run_postgres_keep_alive_task()
        )
    )
    print("[Runner] Started background async PostgreSQL keep-alive task.")

    yield

    if t212_ingestor is not None:
        t212_ingestor._running = False
    if bybit_ingestor is not None:
        bybit_ingestor._running = False

    # Cancel all background tasks to ensure clean exit
    for task in background_tasks:
        task.cancel()

    for task in background_tasks:
        try:
            await task
        except asyncio.CancelledError:
            pass
    print("[Runner] Stopped background async polling tasks.")

app = FastAPI(title="Trading 212 & Bybit Price Ingestor API", lifespan=lifespan)
t212_ingestor = None
bybit_ingestor = None
background_tasks = []

@app.get("/health")
@app.head("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/keep-alive")
@app.head("/keep-alive")
def keep_alive():
    # Keep-Alive for Redis/Valkey (Aiven idle shutdown mitigation)
    redis_client = get_redis_client()
    if redis_client:
        try:
            redis_client.set("ping:keepalive", str(time.time()))
        except Exception as e:
            print(f"[KeepAlive] Failed to write keep-alive to Redis: {e}")
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
                    cur.execute("SELECT ticker, price FROM live_prices")
                    rows = cur.fetchall()
                    for ticker, price in rows:
                        prices[ticker] = float(price)
            return prices
        except Exception as e:
            print(f"[Runner] Failed to fetch prices from PostgreSQL: {e}")

    # 3. Fallback to local JSON caches
    prices = {}
    if t212_ingestor is not None:
        prices.update(t212_ingestor.read_cache())
    if bybit_ingestor is not None:
        prices.update(bybit_ingestor.read_cache())
    return prices

def main():
    global t212_ingestor, bybit_ingestor

    # 1. Initialize Trading 212 Client and Ingestor
    t212_env = os.getenv("T212_INGESTOR_ENV", "demo").lower()
    t212_config = Trading212Config(env=t212_env)
    try:
        t212_config.validate()
        t212_client = Trading212Client(t212_config)
        t212_ingestor = Trading212PriceIngestor(t212_client)
        print(f"[Runner] Trading 212 client and ingestor initialized successfully (env={t212_env}).")
    except Exception as e:
        print(f"[Runner] Trading 212 not configured (env={t212_env}): {e}. Skipping.")
        t212_ingestor = None

    # 2. Initialize Bybit Client and Ingestor
    bybit_config = BybitConfig()
    try:
        bybit_config.validate()
        bybit_client = BybitClient(bybit_config)
        bybit_ingestor = BybitPriceIngestor(bybit_client)
        print("[Runner] Bybit client and ingestor initialized successfully.")
    except Exception as e:
        print(f"[Runner] Bybit not configured: {e}. Skipping.")
        bybit_ingestor = None

    if t212_ingestor is None and bybit_ingestor is None:
        print("[Runner] ERROR: Neither Trading 212 nor Bybit are configured. Exiting.", file=sys.stderr)
        sys.exit(1)

    # 3. Bootstrapping (optional for T212)
    bootstrap_env = os.getenv("T212_BOOTSTRAP", "false").lower()
    if bootstrap_env in ("true", "1", "yes") and t212_ingestor is not None:
        print("[Runner] Running bootstrap procedure...")
        try:
            resolver = Trading212TickerResolver(t212_client)
            bootstrapper = Trading212Bootstrapper(t212_client, resolver)
            bootstrapper.bootstrap()
        except Exception as e:
            print(f"[Runner] Bootstrap failed: {e}", file=sys.stderr)

    # 4. Mode routing
    mode = os.getenv("T212_INGESTOR_MODE", "worker").lower()
    polling_interval = int(os.getenv("T212_POLLING_INTERVAL", "60"))

    if mode == "web":
        port = int(os.getenv("PORT", "8080"))
        host = os.getenv("HOST", "0.0.0.0")
        print(f"[Runner] Starting ingestor in WEB mode on {host}:{port}...")
        uvicorn.run("run_ingestor:app", host=host, port=port, log_level="info", reload=False)
    else:
        print(f"[Runner] Starting ingestor in WORKER mode (async)...")
        import asyncio
        async def run_loops():
            tasks = []
            if t212_ingestor is not None:
                tasks.append(t212_ingestor.start_loop_async(interval_seconds=polling_interval))
            if bybit_ingestor is not None:
                tasks.append(bybit_ingestor.start_loop_async(interval_seconds=polling_interval))
            await asyncio.gather(*tasks)
        try:
            asyncio.run(run_loops())
        except KeyboardInterrupt:
            print("[Runner] Ingestor stopped by keyboard interrupt.")

if __name__ == "__main__":
    main()
