import os
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
import redis
from typing import Generator, Optional

# Load env variables if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# PostgreSQL Pool
_db_pool: Optional[pool.ThreadedConnectionPool] = None

def get_db_pool() -> Optional[pool.ThreadedConnectionPool]:
    global _db_pool
    if _db_pool is None:
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            try:
                min_conn = int(os.getenv("DB_POOL_MIN", "2"))
                max_conn = int(os.getenv("DB_POOL_MAX", "20"))
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
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)

# Redis Client
_redis_client: Optional[redis.Redis] = None

def _is_upstash_quota_exhausted(redis_url: str, api_key: str, email: str) -> bool:
    """Queries the Upstash Developer API to check if the database limit is reached."""
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
    def __init__(self, failover_client, *args, **kwargs):
        self._failover_client = failover_client
        self._args = args
        self._kwargs = kwargs
        self._active_pipeline = self._failover_client._active_client.pipeline(*args, **kwargs)
        self._commands = []

    def __enter__(self):
        self._active_pipeline.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._active_pipeline.__exit__(exc_type, exc_val, exc_tb)

    def __getattr__(self, name):
        attr = getattr(self._active_pipeline, name)
        if name == "execute":
            def wrapper(*args, **kwargs):
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
            def command_recorder(*args, **kwargs):
                self._commands.append((name, args, kwargs))
                return attr(*args, **kwargs)
            return command_recorder

        return attr


class FailoverRedisClient:
    """Wrapper that proxies calls to active Redis database and transparently fails over to secondary client."""
    def __init__(self, primary_url: str, secondary_url: Optional[str] = None):
        self._primary_url = primary_url
        self._secondary_url = secondary_url
        
        self._primary_client = redis.Redis.from_url(primary_url, decode_responses=True)
        self._secondary_client = None
        if secondary_url:
            self._secondary_client = redis.Redis.from_url(secondary_url, decode_responses=True)
            
        self._active_client = self._primary_client
        self._is_failed_over = False

    def _failover(self, error: Exception):
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

    def pipeline(self, *args, **kwargs):
        return FailoverPipeline(self, *args, **kwargs)

    def __getattr__(self, name):
        attr = getattr(self._active_client, name)
        if callable(attr):
            def wrapper(*args, **kwargs):
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


def get_redis_client() -> Optional[redis.Redis]:
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL")
        redis_url_2 = os.getenv("REDIS_URL_2")

        if not redis_url:
            return None

        if redis_url_2:
            # Load Upstash credentials
            redis_api = os.getenv("REDIS_API")
            redis_2_api = os.getenv("REDIS_2_API")
            upstash_email = os.getenv("UPSTASH_EMAIL", "ki2pixel@gmail.com")
            upstash_2_email = os.getenv("UPSTASH_2_EMAIL", "ki2pixel@gmail.com")

            # Default route
            use_secondary = False

            if redis_api:
                print("[ConnectionManager] Checking primary Redis database quota via Upstash API...")
                if _is_upstash_quota_exhausted(redis_url, redis_api, upstash_email):
                    print("[ConnectionManager] Primary Redis database quota exhausted or suspended. Routing directly to secondary.")
                    use_secondary = True
                else:
                    print("[ConnectionManager] Primary Redis database quota is OK.")

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
                _redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
                _redis_client.ping()
                print("[ConnectionManager] Redis client connected successfully.")
            except Exception as e:
                print(f"[ConnectionManager] Failed to connect to Redis: {e}")
                _redis_client = None
    return _redis_client
