import os
import ssl
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
import redis
import threading
from typing import Generator, Optional, Any, Union
from urllib.parse import urlparse, parse_qs

__all__ = [
    "init_async_pool",
    "get_async_pool",
    "close_async_pool",
    "get_db_pool",
    "get_db_connection",
    "get_sync_connection",
    "get_redis_client",
    "run_postgres_keep_alive_task",
    "FailoverRedisClient",
    "FailoverPipeline",
]

# Load env variables if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# PostgreSQL Pool (Synchronous — psycopg2)
_db_pool: Optional[pool.ThreadedConnectionPool] = None

# PostgreSQL Pool (Asynchronous — asyncpg, FastAPI only)
_async_pool: Optional[Any] = None  # Optional[asyncpg.Pool], lazy-imported


def _build_asyncpg_ssl(dsn: str) -> Union[ssl.SSLContext, bool]:
    """Parse sslmode from DSN and return an ssl.SSLContext if required."""
    parsed = urlparse(dsn)
    qs = parse_qs(parsed.query)
    sslmode = qs.get("sslmode", ["prefer"])[0]

    # mTLS environment support
    ssl_cert = os.getenv("DB_SSL_CERT")
    ssl_key = os.getenv("DB_SSL_KEY")
    ssl_ca = os.getenv("DB_SSL_CA")

    if ssl_cert and ssl_key:
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.load_cert_chain(certfile=ssl_cert, keyfile=ssl_key)
        if ssl_ca:
            ctx.load_verify_locations(cafile=ssl_ca)
            ctx.verify_mode = ssl.CERT_REQUIRED
        else:
            ctx.verify_mode = ssl.CERT_NONE
        ctx.check_hostname = False
        return ctx

    if sslmode in ("require", "verify-ca", "verify-full"):
        ctx = ssl.create_default_context()
        if sslmode == "require":
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        elif sslmode in ("verify-ca", "verify-full"):
            if ssl_ca:
                ctx.load_verify_locations(cafile=ssl_ca)
            ctx.verify_mode = ssl.CERT_REQUIRED
            if sslmode == "verify-ca":
                ctx.check_hostname = False
        return ctx
    return False  # asyncpg interprets False as "no SSL"


async def init_async_pool(dsn: str, min_size: int = 2, max_size: int = 10) -> Any:
    """
    Initialize the asyncpg connection pool for FastAPI async endpoints.

    Must be called once during application startup (lifespan).
    The existing psycopg2 pool is NOT affected.
    """
    import asyncpg

    global _async_pool
    if _async_pool is not None:
        return _async_pool

    ssl_ctx = _build_asyncpg_ssl(dsn)

    min_sz = int(os.getenv("ASYNC_DB_POOL_MIN", str(min_size)))
    max_sz = int(os.getenv("ASYNC_DB_POOL_MAX", str(max_size)))

    _async_pool = await asyncpg.create_pool(
        dsn,
        min_size=min_sz,
        max_size=max_sz,
        ssl=ssl_ctx,
        command_timeout=30,
    )
    print(f"[ConnectionManager] asyncpg Pool initialized (min={min_sz}, max={max_sz}, ssl={ssl_ctx is not False})")
    return _async_pool


async def get_async_pool() -> Any:
    """Return the asyncpg pool. Raises RuntimeError if not initialized."""
    if _async_pool is None:
        raise RuntimeError(
            "asyncpg pool not initialized. Call init_async_pool() during app startup."
        )
    return _async_pool


async def close_async_pool() -> None:
    """Gracefully close the asyncpg pool during application shutdown."""
    global _async_pool
    if _async_pool is not None:
        await _async_pool.close()
        _async_pool = None
        print("[ConnectionManager] asyncpg Pool closed.")

_db_pool_lock = threading.Lock()

def get_db_pool() -> Optional[pool.ThreadedConnectionPool]:
    global _db_pool
    if _db_pool is None:
        with _db_pool_lock:
            if _db_pool is None:
                db_url = os.getenv("DATABASE_URL")
                if db_url:
                    try:
                        min_conn = int(os.getenv("DB_POOL_MIN", "2"))
                        max_conn = int(os.getenv("DB_POOL_MAX", "5"))
                        _db_pool = pool.ThreadedConnectionPool(min_conn, max_conn, db_url)
                        print(f"[ConnectionManager] PostgreSQL ThreadedConnectionPool initialized (min={min_conn}, max={max_conn})")
                    except Exception as e:
                        print(f"[ConnectionManager] Failed to initialize PostgreSQL pool: {e}")
    return _db_pool

@contextmanager
def get_db_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """Context manager for obtaining a database connection from the pool."""
    pool = get_db_pool()
    if not pool:
        # Fallback to direct connection if pool init failed but URL is set
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise RuntimeError("DATABASE_URL not configured")
        conn = psycopg2.connect(db_url)
        try:
            yield conn
        finally:
            conn.close()
        return

    conn = pool.getconn()
    if conn.closed:
        try:
            pool.putconn(conn, close=True)
        except Exception:
            pass
        conn = pool.getconn()

    is_operational_error = False
    try:
        yield conn
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        is_operational_error = True
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            if is_operational_error or conn.closed:
                pool.putconn(conn, close=True)
            else:
                pool.putconn(conn)
        except Exception:
            try:
                conn.close()
            except Exception:
                pass

async def run_postgres_keep_alive_task(interval_seconds: int = 14400) -> None:
    """Heartbeat task to keep PostgreSQL alive on Aiven (preventing 24h idle spindown)."""
    import asyncio
    print(f"[KeepAlive] Starting PostgreSQL keep-alive loop (interval: {interval_seconds}s)...")
    while True:
        try:
            db_url = os.getenv("DATABASE_URL")
            if db_url:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT 1;")
                        cur.fetchone()
                print("[KeepAlive] PostgreSQL heartbeat (SELECT 1;) executed successfully.")
            else:
                print("[KeepAlive] DATABASE_URL not set, skipping heartbeat.")
        except Exception as e:
            print(f"[KeepAlive] PostgreSQL heartbeat failed: {e}")
        
        await asyncio.sleep(interval_seconds)

# Redis Client
_redis_client: Optional[redis.Redis] = None

def _is_upstash_quota_exhausted(redis_url: str, api_key: str, email: str) -> bool:
    """Queries the Upstash Developer API to check if the database limit is reached."""
    if "upstash" not in redis_url.lower():
        return False

    if not email or not api_key:
        print("[UpstashAPI] Missing email or API key, skipping Upstash API check.")
        return False

    import urllib.request
    import urllib.parse
    import json
    import base64

    try:
        parsed_url = urllib.parse.urlparse(redis_url)
        host = parsed_url.hostname
        if not host:
            return False

        # Get database list
        auth_str = base64.b64encode(f"{email}:{api_key}".encode()).decode()
        req_db = urllib.request.Request("https://api.upstash.com/v2/redis/databases")
        req_db.add_header("Authorization", f"Basic {auth_str}")

        with urllib.request.urlopen(req_db, timeout=5) as response:
            databases = json.loads(response.read())

        db_id = None
        db_limit = 0
        for db in databases:
            db_endpoint = db.get("endpoint", "")
            if db_endpoint in host or host in db_endpoint:
                db_id = db.get("database_id")
                db_limit = db.get("db_request_limit", 0)
                db_state = db.get("state", "active")
                if db_state == "suspended":
                    print(f"[UpstashAPI] Database {db_endpoint} is suspended.")
                    return True
                break

        if not db_id:
            print(f"[UpstashAPI] Could not find database matching host {host} in Upstash account.")
            return False

        if db_limit <= 0:
            return False

        # Get database stats
        req_stats = urllib.request.Request(f"https://api.upstash.com/v2/redis/stats/{db_id}")
        req_stats.add_header("Authorization", f"Basic {auth_str}")

        with urllib.request.urlopen(req_stats, timeout=5) as response:
            stats = json.loads(response.read())

        monthly_requests = stats.get("total_monthly_requests", 0)
        print(f"[UpstashAPI] Database host {host} usage: {monthly_requests}/{db_limit} requests.")
        return monthly_requests >= db_limit

    except Exception as e:
        print(f"[UpstashAPI] Error querying Upstash API for {redis_url}: {e}")
        return False


class FailoverPipeline:
    """Proxy pipeline that records commands and replays them on failover if execution fails."""
    def __init__(self, failover_client: "FailoverRedisClient", *args: Any, **kwargs: Any) -> None:
        self._failover_client = failover_client
        self._args = args
        self._kwargs = kwargs
        self._active_pipeline = self._failover_client._active_client.pipeline(*args, **kwargs)
        self._commands: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def __enter__(self) -> "FailoverPipeline":
        self._active_pipeline.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Any:
        return self._active_pipeline.__exit__(exc_type, exc_val, exc_tb)

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._active_pipeline, name)
        if name == "execute":
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return attr(*args, **kwargs)
                except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
                    if not self._failover_client._is_failed_over and self._failover_client._secondary_client:
                        self._failover_client._failover(e)
                        self._active_pipeline = self._failover_client._active_client.pipeline(*self._args, **self._kwargs)
                        for cmd_name, cmd_args, cmd_kwargs in self._commands:
                            getattr(self._active_pipeline, cmd_name)(*cmd_args, **cmd_kwargs)
                        return self._active_pipeline.execute(*args, **kwargs)
                    raise
                except redis.exceptions.ResponseError as e:
                    err_msg = str(e).lower()
                    is_quota_error = any(keyword in err_msg for keyword in ("quota", "limit", "max"))
                    if is_quota_error and not self._failover_client._is_failed_over and self._failover_client._secondary_client:
                        self._failover_client._failover(e)
                        self._active_pipeline = self._failover_client._active_client.pipeline(*self._args, **self._kwargs)
                        for cmd_name, cmd_args, cmd_kwargs in self._commands:
                            getattr(self._active_pipeline, cmd_name)(*cmd_args, **cmd_kwargs)
                        return self._active_pipeline.execute(*args, **kwargs)
                    raise
            return wrapper

        if callable(attr):
            def command_recorder(*args: Any, **kwargs: Any) -> Any:
                self._commands.append((name, args, kwargs))
                return attr(*args, **kwargs)
            return command_recorder

        return attr


class FailoverRedisClient:
    """Wrapper that proxies calls to active Redis database and transparently fails over to secondary client."""
    def __init__(self, primary_url: str, secondary_url: Optional[str] = None) -> None:
        self._primary_url = primary_url
        self._secondary_url = secondary_url
        
        pool_max = int(os.getenv("REDIS_POOL_MAX", "40"))
        redis_user = os.getenv("REDIS_USER")
        redis_password = os.getenv("REDIS_PASSWORD")
        redis_user_2 = os.getenv("REDIS_USER_2")
        redis_password_2 = os.getenv("REDIS_PASSWORD_2")
        
        # mTLS support
        redis_ssl_cert = os.getenv("REDIS_SSL_CERT")
        redis_ssl_key = os.getenv("REDIS_SSL_KEY")
        redis_ssl_ca = os.getenv("REDIS_SSL_CA")
        
        primary_kwargs = {
            "decode_responses": True,
            "max_connections": pool_max,
            "socket_timeout": 5,
            "socket_connect_timeout": 5,
            "retry_on_timeout": True
        }
        if redis_user:
            primary_kwargs["username"] = redis_user
        if redis_password:
            primary_kwargs["password"] = redis_password
            
        if primary_url.startswith("rediss://"):
            if redis_ssl_cert and redis_ssl_key:
                primary_kwargs["ssl_certfile"] = redis_ssl_cert
                primary_kwargs["ssl_keyfile"] = redis_ssl_key
            if redis_ssl_ca:
                primary_kwargs["ssl_ca_certs"] = redis_ssl_ca
                primary_kwargs["ssl_cert_reqs"] = "required"
            
        self._primary_client = redis.Redis.from_url(
            primary_url,
            **primary_kwargs
        )
        self._secondary_client = None
        if secondary_url:
            secondary_kwargs = {
                "decode_responses": True,
                "max_connections": pool_max,
                "socket_timeout": 5,
                "socket_connect_timeout": 5,
                "retry_on_timeout": True
            }
            if redis_user_2:
                secondary_kwargs["username"] = redis_user_2
            elif redis_user:
                secondary_kwargs["username"] = redis_user
                
            if redis_password_2:
                secondary_kwargs["password"] = redis_password_2
            elif redis_password:
                secondary_kwargs["password"] = redis_password
                
            if secondary_url.startswith("rediss://"):
                # Use secondary certs if provided, else fallback to primary
                redis_ssl_cert_2 = os.getenv("REDIS_SSL_CERT_2") or redis_ssl_cert
                redis_ssl_key_2 = os.getenv("REDIS_SSL_KEY_2") or redis_ssl_key
                redis_ssl_ca_2 = os.getenv("REDIS_SSL_CA_2") or redis_ssl_ca
                
                if redis_ssl_cert_2 and redis_ssl_key_2:
                    secondary_kwargs["ssl_certfile"] = redis_ssl_cert_2
                    secondary_kwargs["ssl_keyfile"] = redis_ssl_key_2
                if redis_ssl_ca_2:
                    secondary_kwargs["ssl_ca_certs"] = redis_ssl_ca_2
                    secondary_kwargs["ssl_cert_reqs"] = "required"
                
            self._secondary_client = redis.Redis.from_url(
                secondary_url,
                **secondary_kwargs
            )
            
        self._active_client = self._primary_client
        self._is_failed_over = False

    def _failover(self, error: Exception) -> None:
        if self._secondary_client is None:
            raise error
            
        if self._is_failed_over:
            raise error
            
        print(f"[FailoverRedisClient] Primary Redis client encountered error: {error}. Failing over to secondary client.")
        self._active_client = self._secondary_client
        self._is_failed_over = True
        
        try:
            self._secondary_client.ping()
            print("[FailoverRedisClient] Secondary Redis client connected successfully.")
        except Exception as ping_err:
            print(f"[FailoverRedisClient] Secondary Redis client ping failed: {ping_err}")
            raise ping_err

    def pipeline(self, *args: Any, **kwargs: Any) -> FailoverPipeline:
        return FailoverPipeline(self, *args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._active_client, name)
        if callable(attr):
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return attr(*args, **kwargs)
                except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
                    if not self._is_failed_over and self._secondary_client:
                        self._failover(e)
                        new_attr = getattr(self._active_client, name)
                        return new_attr(*args, **kwargs)
                    raise
                except redis.exceptions.ResponseError as e:
                    err_msg = str(e).lower()
                    is_quota_error = any(keyword in err_msg for keyword in ("quota", "limit", "max"))
                    if is_quota_error and not self._is_failed_over and self._secondary_client:
                        self._failover(e)
                        new_attr = getattr(self._active_client, name)
                        return new_attr(*args, **kwargs)
                    raise
            return wrapper
        return attr


_redis_client_lock = threading.Lock()

def get_redis_client() -> Optional[Union[redis.Redis, FailoverRedisClient]]:
    global _redis_client
    if _redis_client is None:
        with _redis_client_lock:
            if _redis_client is None:
                redis_url = os.getenv("REDIS_URL")
                redis_url_2 = os.getenv("REDIS_URL_2")

                if not redis_url:
                    return None

                if redis_url_2:
                    # Load Upstash credentials
                    redis_api = os.getenv("REDIS_API")
                    redis_2_api = os.getenv("REDIS_2_API")
                    upstash_email = os.getenv("UPSTASH_EMAIL")
                    upstash_2_email = os.getenv("UPSTASH_2_EMAIL")

                    # Default route
                    use_secondary = False

                    if redis_api and upstash_email:
                        print("[ConnectionManager] Checking primary Redis database quota via Upstash API...")
                        if _is_upstash_quota_exhausted(redis_url, redis_api, upstash_email):
                            print("[ConnectionManager] Primary Redis database quota exhausted or suspended. Routing directly to secondary.")
                            use_secondary = True
                        else:
                            print("[ConnectionManager] Primary Redis database quota is OK.")
                    else:
                        if redis_api:
                            print("[ConnectionManager] Warning: REDIS_API is defined but UPSTASH_EMAIL is missing. Skipping quota check.")

                    try:
                        client = FailoverRedisClient(redis_url, redis_url_2)
                        if use_secondary:
                            # Force failover immediately without checking primary
                            client._active_client = client._secondary_client
                            client._is_failed_over = True
                            client.ping()
                        else:
                            # Try pinging primary
                            try:
                                client.ping()
                                print("[ConnectionManager] Primary Redis client connected successfully.")
                            except Exception as e:
                                print(f"[ConnectionManager] Primary Redis client ping failed: {e}. Failing over to secondary.")
                                client._failover(e)
                        _redis_client = client
                    except Exception as e:
                        print(f"[ConnectionManager] Failed to initialize FailoverRedisClient: {e}")
                        _redis_client = None
                else:
                    try:
                        pool_max = int(os.getenv("REDIS_POOL_MAX", "40"))
                        redis_user = os.getenv("REDIS_USER")
                        redis_password = os.getenv("REDIS_PASSWORD")
                        
                        # mTLS support
                        redis_ssl_cert = os.getenv("REDIS_SSL_CERT")
                        redis_ssl_key = os.getenv("REDIS_SSL_KEY")
                        redis_ssl_ca = os.getenv("REDIS_SSL_CA")
                        
                        redis_kwargs = {
                            "decode_responses": True,
                            "max_connections": pool_max,
                            "socket_timeout": 5,
                            "socket_connect_timeout": 5,
                            "retry_on_timeout": True
                        }
                        if redis_user:
                            redis_kwargs["username"] = redis_user
                        if redis_password:
                            redis_kwargs["password"] = redis_password
                            
                        if redis_url.startswith("rediss://"):
                            if redis_ssl_cert and redis_ssl_key:
                                redis_kwargs["ssl_certfile"] = redis_ssl_cert
                                redis_kwargs["ssl_keyfile"] = redis_ssl_key
                            if redis_ssl_ca:
                                redis_kwargs["ssl_ca_certs"] = redis_ssl_ca
                                redis_kwargs["ssl_cert_reqs"] = "required"
                            
                        _redis_client = redis.Redis.from_url(
                            redis_url,
                            **redis_kwargs
                        )
                        _redis_client.ping()
                        print("[ConnectionManager] Redis client connected successfully.")
                    except Exception as e:
                        print(f"[ConnectionManager] Failed to connect to Redis: {e}")
                        _redis_client = None
    return _redis_client

get_sync_connection = get_db_connection

