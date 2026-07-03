import os
import sys
import asyncio
import time
import base64
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
from contextlib import asynccontextmanager
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Import API router and engine
from backtest_engine.live.paper_trading.api import router as paper_trading_router
from backtest_engine.live.paper_trading.engine import PaperTradingEngine
from backtest_engine.live.paper_trading.db_setup import init_db

logger = logging.getLogger("papertrader")

# Check Basic Auth Configuration
PAPER_TRADER_USER = os.getenv("PAPER_TRADER_USER", "admin")
PAPER_TRADER_PASSWORD = os.getenv("PAPER_TRADER_PASSWORD")

is_testing = "pytest" in sys.modules or "unittest" in sys.modules or os.getenv("PYTEST_CURRENT_TEST") is not None
is_production = os.getenv("ENVIRONMENT", "").lower() == "production" or os.getenv("RENDER") is not None

if not PAPER_TRADER_PASSWORD and not is_testing:
    msg = "PAPER_TRADER_PASSWORD environment variable is missing!"
    if is_production:
        logger.critical(f"[CONFIG ERROR] {msg}")
        raise ValueError(f"Configuration Error: {msg} This is required in production.")
    else:
        logger.critical(f"[CONFIG ERROR] {msg}")
        raise ValueError(f"Configuration Error: {msg} Please set it in your environment or .env file.")

# Fallback for testing environment
if is_testing and not PAPER_TRADER_PASSWORD:
    PAPER_TRADER_PASSWORD = "test_password"

class BasicAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Normalize path to strip trailing slashes (except root '/')
        path = request.url.path
        if len(path) > 1 and path.endswith("/"):
            path = path.rstrip("/")

        # Exclude public monitoring endpoints
        if path in ("/health", "/keep-alive"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return Response(
                content="Unauthorized: Missing credentials",
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="Paper Trading Access"'}
            )

        try:
            auth_type, credentials = auth_header.split(" ", 1)
            if auth_type.lower() != "basic":
                return Response(
                    content="Unauthorized: Invalid authentication scheme",
                    status_code=401,
                    headers={"WWW-Authenticate": 'Basic realm="Paper Trading Access"'}
                )

            decoded = base64.b64decode(credentials).decode("utf-8")
            username, password = decoded.split(":", 1)
        except Exception:
            return Response(
                content="Unauthorized: Invalid credentials format",
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="Paper Trading Access"'}
            )

        expected_user = os.getenv("PAPER_TRADER_USER", "admin")
        expected_password = os.getenv("PAPER_TRADER_PASSWORD") or PAPER_TRADER_PASSWORD

        if username != expected_user or password != expected_password:
            return Response(
                content="Unauthorized: Invalid username or password",
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="Paper Trading Access"'}
            )

        return await call_next(request)

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

# Add Basic Auth Middleware to protect dashboard and API endpoints
app.add_middleware(BasicAuthMiddleware)

# Include API endpoints
app.include_router(paper_trading_router)

@app.get("/health")
@app.head("/health")
@app.get("/health/")
@app.head("/health/")
def health_check():
    return {"status": "healthy"}

@app.get("/keep-alive")
@app.head("/keep-alive")
@app.get("/keep-alive/")
@app.head("/keep-alive/")
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
