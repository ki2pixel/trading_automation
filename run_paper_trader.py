import os
import sys
import asyncio
import time
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
from contextlib import asynccontextmanager

# Import API router and engine
from backtest_engine.live.paper_trading.api import router as paper_trading_router
from backtest_engine.live.paper_trading.engine import PaperTradingEngine
from backtest_engine.live.paper_trading.db_setup import init_db

engine = None
background_task = None
keepalive_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global background_task, keepalive_task, engine
    
    # Run DB schema check/seed
    print("[PaperTrader] Initializing database...")
    await asyncio.to_thread(init_db)

    # Initialize engine if not already initialized
    if engine is None:
        engine = PaperTradingEngine()

    polling_interval = int(os.getenv("PAPER_TRADER_POLLING_INTERVAL", "60"))
    if engine is not None:
        background_task = asyncio.create_task(
            engine.start_loop_async(interval_seconds=polling_interval)
        )
        print("[PaperTrader] Started background async engine task.")
    
    # Start database keep-alive heartbeat task
    from backtest_engine.live.connection import run_postgres_keep_alive_task
    keepalive_task = asyncio.create_task(
        run_postgres_keep_alive_task()
    )
    print("[PaperTrader] Started background async PostgreSQL keep-alive task.")
    
    yield
    
    if engine is not None:
        engine.stop()
    if keepalive_task is not None:
        keepalive_task.cancel()
        try:
            await keepalive_task
        except asyncio.CancelledError:
            pass
        print("[PaperTrader] Stopped background async PostgreSQL keep-alive task.")
    if background_task is not None:
        try:
            await background_task
        except asyncio.CancelledError:
            pass
    print("[PaperTrader] Stopped background async engine task.")


# Initialize app
app = FastAPI(title="Paper Trading Dashboard API", lifespan=lifespan)

# Include API endpoints
app.include_router(paper_trading_router)

@app.get("/health")
@app.head("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/keep-alive")
@app.head("/keep-alive")
def keep_alive():
    return {"status": "alive", "timestamp": time.time()}

@app.get("/status")
def status():
    global engine
    if engine is None:
        return {"status": "error", "message": "Engine not initialized"}
    return {
        "status": "online",
        "t212_client_active": engine.t212_client is not None,
        "t212_init_error": getattr(engine, "t212_init_error", None),
        "database_url_configured": bool(engine.db_url),
    }

# Mount static files for the frontend dashboard
static_dir = os.path.join(os.path.dirname(__file__), "backtest_engine/live/paper_trading/static")
# Create static directory dynamically if not exists (should be created by now)
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

def main():
    global engine
    engine = PaperTradingEngine()
    
    port = int(os.getenv("PORT", "8081")) # Different default port to not clash if run locally with ingestor
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"[PaperTrader] Starting Paper Trading Web Server on {host}:{port}...")
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()
