import os
import sys
import threading
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
from contextlib import asynccontextmanager

# Import API router and engine
from backtest_engine.live.paper_trading.api import router as paper_trading_router
from backtest_engine.live.paper_trading.engine import PaperTradingEngine
from backtest_engine.live.paper_trading.db_setup import init_db

engine = None
background_thread = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global background_thread
    
    # Run DB schema check/seed
    print("[PaperTrader] Initializing database...")
    init_db()

    polling_interval = int(os.getenv("PAPER_TRADER_POLLING_INTERVAL", "60"))
    background_thread = threading.Thread(
        target=run_engine_loop,
        args=(engine, polling_interval),
        daemon=True
    )
    background_thread.start()
    print("[PaperTrader] Started background engine thread.")
    
    yield
    
    if engine is not None:
        engine.stop()
    if background_thread is not None:
        background_thread.join(timeout=5)
    print("[PaperTrader] Stopped background engine thread.")

def run_engine_loop(engine_instance, interval):
    try:
        engine_instance.start_loop(interval_seconds=interval)
    except Exception as e:
        print(f"[PaperTrader] Background engine thread failed: {e}")

# Initialize app
app = FastAPI(title="Paper Trading Dashboard API", lifespan=lifespan)

# Include API endpoints
app.include_router(paper_trading_router)

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
