import os
import sys
import asyncio
import time
import logging
import secrets
import uuid
import traceback
from fastapi import FastAPI, HTTPException as FastAPIHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from contextlib import asynccontextmanager
import hmac
import hashlib
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel

# Import API router and engine
from backtest_engine.live.paper_trading.api import router as paper_trading_router
from backtest_engine.live.paper_trading.engine import PaperTradingEngine
from backtest_engine.live.paper_trading.db_setup import init_db

logger = logging.getLogger("papertrader")


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "filename": record.filename,
            "lineno": record.lineno,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def setup_siem_logging():
    audit_logger = logging.getLogger("trading_audit")
    audit_logger.setLevel(logging.INFO)
    
    if audit_logger.handlers:
        return audit_logger
        
    log_path = os.getenv("TRADING_AUDIT_LOG_PATH", "/var/log/trading_audit.log")
    
    try:
        # Test write access to directory
        dir_name = os.path.dirname(log_path) or "."
        os.makedirs(dir_name, exist_ok=True)
        handler = logging.FileHandler(log_path, encoding="utf-8")
    except (PermissionError, FileNotFoundError):
        fallback_path = "./trading_audit.log"
        print(f"[SECURITY] Permission denied or directory missing for {log_path}. Falling back to: {fallback_path}")
        handler = logging.FileHandler(fallback_path, encoding="utf-8")
        
    handler.setFormatter(JSONFormatter())
    audit_logger.addHandler(handler)
    return audit_logger


# Initialize SIEM audit logger
setup_siem_logging()
import json


def load_infisical_secrets() -> None:
    """
    Connect to Infisical Secrets Manager using Machine Identity.
    If configured, injects secrets into os.environ dynamically.
    """
    client_id = os.getenv("INFISICAL_CLIENT_ID")
    client_secret = os.getenv("INFISICAL_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        return

    try:
        from infisical_client import InfisicalClient, ClientSettings, AuthenticationOptions
        
        url = os.getenv("INFISICAL_URL", "https://app.infisical.com")
        project_id = os.getenv("INFISICAL_PROJECT_ID")
        env_slug = os.getenv("INFISICAL_ENV", "dev")
        
        client = InfisicalClient(
            ClientSettings(
                auth=AuthenticationOptions(
                    client_id=client_id,
                    client_secret=client_secret
                ),
                site_url=url
            )
        )
        
        # Load all secrets
        secrets_list = client.list_secrets(
            project_id=project_id,
            environment=env_slug
        )
        
        for secret in secrets_list:
            key = getattr(secret, "secret_key", None) or getattr(secret, "secretKey", None)
            val = getattr(secret, "secret_value", None) or getattr(secret, "secretValue", None)
            # Try dictionary access if attributes not found
            if not key and isinstance(secret, dict):
                key = secret.get("secretKey") or secret.get("secret_key")
                val = secret.get("secretValue") or secret.get("secret_value")
            
            if key and val:
                os.environ[key] = val
                
        print(f"[Infisical] Successfully loaded and injected {len(secrets_list)} secrets in process memory.")
    except Exception as e:
        print(f"[Infisical] Fallback warning: Failed to load secrets from Infisical: {e}")


# Load secrets from Infisical before verifying configuration
load_infisical_secrets()


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

# HMAC Secret for session token signing (separate from user password)
HMAC_SECRET = os.getenv("HMAC_SECRET")
if not HMAC_SECRET and not is_testing:
    if is_production:
        raise ValueError(
            "Configuration Error: HMAC_SECRET environment variable is missing! "
            "This is required in production. Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    else:
        HMAC_SECRET = secrets.token_hex(32)
        logger.warning("[CONFIG] HMAC_SECRET not set — auto-generated for dev. Set HMAC_SECRET in production.")

# Fallback for testing environment
if is_testing and not HMAC_SECRET:
    HMAC_SECRET = secrets.token_hex(32)

def create_session_token(username: str, expires: int, secret: str) -> str:
    message = f"{username}:{expires}".encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return f"{username}:{expires}:{sig}"

def verify_session_token(token: str, secret: str) -> bool:
    try:
        username, expires_str, sig = token.split(":", 2)
        expires = int(expires_str)
        if expires < time.time():
            return False
        message = f"{username}:{expires_str}".encode("utf-8")
        expected_sig = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
        return hmac.compare_digest(sig, expected_sig)
    except Exception:
        return False

class CookieSessionAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if len(path) > 1 and path.endswith("/"):
            path = path.rstrip("/")

        # Exclude public monitoring endpoints, styles, and login page/endpoint
        if path in ("/health", "/keep-alive", "/login.html", "/style.css", "/api/login"):
            return await call_next(request)

        session_token = request.cookies.get("paper_trader_session")

        authenticated = False
        if session_token and HMAC_SECRET:
            authenticated = verify_session_token(session_token, HMAC_SECRET)

        if not authenticated:
            # For API requests, return JSON 401
            if path.startswith("/api/"):
                return Response(
                    content='{"detail":"Unauthorized"}',
                    status_code=401,
                    media_type="application/json"
                )
            # For pages, redirect to login
            return RedirectResponse(url="/login.html", status_code=307)

        return await call_next(request)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Double Submit Cookie pattern for CSRF protection.

    Sets a `csrftoken` cookie (HttpOnly=True so JS cannot read it directly).
    Verifies that mutating requests (POST/PUT/DELETE/PATCH) carry a
    matching X-CSRFToken header. Login, logout and csrf-token endpoints are exempt.
    """
    EXEMPT_PATHS = frozenset({"/api/login", "/api/logout", "/api/csrf-token"})
    MUTATING_METHODS = frozenset({"POST", "PUT", "DELETE", "PATCH"})

    async def dispatch(self, request: Request, call_next):
        # Skip CSRF for safe methods — just ensure cookie is set
        if request.method not in self.MUTATING_METHODS:
            response = await call_next(request)
            self._ensure_csrf_cookie(request, response)
            return response

        path = request.url.path
        if len(path) > 1 and path.endswith("/"):
            path = path.rstrip("/")

        # Skip CSRF for exempt paths
        if path in self.EXEMPT_PATHS:
            response = await call_next(request)
            self._ensure_csrf_cookie(request, response)
            return response

        # Security hardening: reject mutating request if Content-Type is not application/json
        # (prevents CORS bypass via Blob, FormData, or text/plain POSTs)
        content_type = request.headers.get("Content-Type", "")
        client_ip = request.client.host if request.client else "unknown"
        if path.startswith("/api/") and not content_type.startswith("application/json"):
            logging.getLogger("trading_audit").error(
                f"Content-Type violation: IP={client_ip}, path={path}, content_type={content_type}"
            )
            return JSONResponse(
                content={"detail": "Content-Type must be application/json for mutating requests"},
                status_code=415
            )

        # Validate CSRF token: cookie must match header
        cookie_token = request.cookies.get("csrftoken")
        header_token = request.headers.get("X-CSRFToken")

        if not cookie_token or not header_token or not hmac.compare_digest(cookie_token, header_token):
            logging.getLogger("trading_audit").error(
                f"CSRF token failure: IP={client_ip}, path={path}"
            )
            return JSONResponse(
                content={"detail": "CSRF token missing or invalid"},
                status_code=403
            )

        response = await call_next(request)
        return response

    def _ensure_csrf_cookie(self, request: Request, response: Response):
        """Set CSRF cookie if not already present on the request."""
        if not request.cookies.get("csrftoken"):
            is_prod = os.getenv("ENVIRONMENT", "").lower() == "production" or os.getenv("RENDER") is not None
            csrf_token = secrets.token_hex(32)
            response.set_cookie(
                key="csrftoken",
                value=csrf_token,
                max_age=30 * 24 * 3600,
                path="/",
                httponly=True,  # JS cannot read this cookie directly
                secure=is_prod,
                samesite="lax"
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to every response."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'"
        )
        is_prod = os.getenv("ENVIRONMENT", "").lower() == "production" or os.getenv("RENDER") is not None
        if is_prod:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class RedisRateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Token Bucket / Counter rate limiter middleware using Redis.
    Limits request rates to prevent DoS attacks.
    """
    def __init__(self, app, rate_limit: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.rate_limit = rate_limit
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not path.startswith("/api/"):
            return await call_next(request)

        # Exclude rate limiting for auth/csrf initialization
        if path in ("/api/csrf-token", "/api/login"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}:{path}"

        from backtest_engine.live.connection import get_redis_client
        redis_client = get_redis_client()
        
        if redis_client:
            try:
                current_requests = redis_client.incr(key)
                if current_requests == 1:
                    redis_client.expire(key, self.window_seconds)
                
                if current_requests > self.rate_limit:
                    logging.getLogger("trading_audit").warning(
                        f"Rate limit exceeded: IP={client_ip}, path={path}, requests={current_requests}, limit={self.rate_limit}"
                    )
                    return JSONResponse(
                        content={"detail": "Too many requests. Please try again later."},
                        status_code=429
                    )
            except Exception as e:
                # Fail open to prevent complete outage if Redis is down
                logger.warning(f"[RateLimiter] Redis error: {e}")
                
        return await call_next(request)


engine = None
background_task = None
keepalive_task = None
kill_switch_listener = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global background_task, keepalive_task, engine, kill_switch_listener
    
    # Run DB schema check/seed
    print("[PaperTrader] Initializing database...")
    await asyncio.to_thread(init_db)

    # Initialize asyncpg pool for async API endpoints
    from backtest_engine.live.connection import init_async_pool, close_async_pool
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        await init_async_pool(db_url)
    else:
        print("[PaperTrader] WARNING: DATABASE_URL not set, asyncpg pool not initialized.")

    # Initialize engine if not already initialized
    if engine is None:
        engine = PaperTradingEngine()

    # Start Kill Switch listener (ESMA RTS 6 compliance)
    from backtest_engine.live.kill_switch import KillSwitchListener
    kill_switch_listener = KillSwitchListener(engine)
    await kill_switch_listener.start()

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
    
    # Shutdown: close asyncpg pool first (API endpoints stop using it)
    await close_async_pool()

    if kill_switch_listener is not None:
        await kill_switch_listener.stop()

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

# Middlewares in Starlette LIFO order (last added = first executed):
# Execution order: CORS → SecurityHeaders → Auth → CSRF
app.add_middleware(CSRFMiddleware)               # 1st added → last executed
app.add_middleware(CookieSessionAuthMiddleware)  # 2nd added → 3rd executed
app.add_middleware(SecurityHeadersMiddleware)     # 3rd added → 2nd executed
app.add_middleware(RedisRateLimiterMiddleware)    # 4th added


# CORS must execute first — added last (LIFO)
_allowed_origins: list[str] = []
if is_production:
    _render_url = os.getenv("RENDER_EXTERNAL_URL", "")
    if _render_url:
        _allowed_origins.append(_render_url)
else:
    _allowed_origins = ["http://localhost:8081", "http://127.0.0.1:8081"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["X-CSRFToken", "Content-Type"],
)

# Include API endpoints
app.include_router(paper_trading_router)

def safe_error_response(exc: Exception, request: Request) -> JSONResponse:
    correlation_id = str(uuid.uuid4())
    logger.exception(f"Unhandled exception occurred. Reference: {correlation_id} | Path: {request.url.path}")
    
    is_prod = os.getenv("ENVIRONMENT", "").lower() == "production" or os.getenv("RENDER") is not None
    is_debug = os.getenv("DEBUG", "false").lower() == "true"
    
    if is_prod and not is_debug:
        return JSONResponse(
            status_code=500,
            content={"error": f"An internal error occurred. Reference: {correlation_id}"}
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "error": str(exc),
                "traceback": traceback.format_exc(),
                "correlation_id": correlation_id
            }
        )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, (FastAPIHTTPException, StarletteHTTPException)):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    return safe_error_response(exc, request)
@app.get("/api/csrf-token")
def get_csrf_token(request: Request, response: Response):
    token = request.cookies.get("csrftoken")
    if not token:
        token = secrets.token_hex(32)
        is_prod = os.getenv("ENVIRONMENT", "").lower() == "production" or os.getenv("RENDER") is not None
        response.set_cookie(
            key="csrftoken",
            value=token,
            max_age=30 * 24 * 3600,
            path="/",
            httponly=True,
            secure=is_prod,
            samesite="lax"
        )
    return {"csrf_token": token}

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/login")
async def login(request: Request):
    content_type = request.headers.get("content-type", "")
    username = None
    password = None
    is_form = False

    if "application/x-www-form-urlencoded" in content_type:
        is_form = True
        import urllib.parse
        body_bytes = await request.body()
        body_str = body_bytes.decode("utf-8")
        form_data = urllib.parse.parse_qs(body_str)
        username = form_data.get("username", [None])[0]
        password = form_data.get("password", [None])[0]
    else:
        try:
            payload = await request.json()
            username = payload.get("username")
            password = payload.get("password")
        except Exception:
            return JSONResponse(
                content={"status": "error", "message": "Invalid request body"},
                status_code=400
            )

    expected_user = os.getenv("PAPER_TRADER_USER", "admin")
    expected_password = os.getenv("PAPER_TRADER_PASSWORD") or PAPER_TRADER_PASSWORD

    if username != expected_user or password != expected_password:
        if is_form:
            return RedirectResponse(url="/login.html?error=true", status_code=303)
        return JSONResponse(
            content={"status": "error", "message": "Invalid username or password"},
            status_code=401
        )

    expires = int(time.time()) + 30 * 24 * 3600
    token = create_session_token(username, expires, HMAC_SECRET)

    is_prod = os.getenv("ENVIRONMENT", "").lower() == "production" or os.getenv("RENDER") is not None

    if is_form:
        response = RedirectResponse(url="/", status_code=303)
    else:
        response = JSONResponse(content={"status": "success", "message": "Logged in successfully"})

    response.set_cookie(
        key="paper_trader_session",
        value=token,
        max_age=30 * 24 * 3600,
        expires=expires,
        path="/",
        domain=None,
        secure=is_prod,
        httponly=True,
        samesite="lax"
    )
    return response

@app.post("/api/logout")
@app.get("/api/logout")
def logout():
    response = RedirectResponse(url="/login.html", status_code=307)
    response.delete_cookie(key="paper_trader_session", path="/")
    return response

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
