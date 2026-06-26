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

def get_redis_client() -> Optional[redis.Redis]:
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            try:
                _redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
                _redis_client.ping()
                print("[ConnectionManager] Redis client connected successfully.")
            except Exception as e:
                print(f"[ConnectionManager] Failed to connect to Redis: {e}")
                _redis_client = None
    return _redis_client
