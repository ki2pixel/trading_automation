import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, "/home/kidpixel/trading_automation-main")
load_dotenv()

from backtest_engine.live.connection import get_db_connection, get_redis_client
from backtest_engine.live.paper_trading.db_setup import SEED_CONFIGS

def clean_database():
    print("Starting database cleanup...")
    
    # 0. Get authorized tickers from db_setup
    authorized_tickers = list(set(config["asset"] for config in SEED_CONFIGS))
    print(f"Authorized tickers (total {len(authorized_tickers)}): {sorted(authorized_tickers)}")
    
    # 1. PostgreSQL Cleanup
    tickers_to_clean = []
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Find tickers in database
                cur.execute("SELECT DISTINCT ticker FROM trading212_prices;")
                db_tickers = [row[0] for row in cur.fetchall()]
                
                cur.execute("SELECT DISTINCT ticker FROM trading212_candles_1m;")
                candle_tickers = [row[0] for row in cur.fetchall()]
                
                all_db_tickers = list(set(db_tickers + candle_tickers))
                print(f"Tickers currently in PostgreSQL: {all_db_tickers}")
                
                tickers_to_clean = [t for t in all_db_tickers if t not in authorized_tickers]
                print(f"Obsolete tickers to clean in PostgreSQL: {tickers_to_clean}")
                
                if tickers_to_clean:
                    # Delete from trading212_prices
                    cur.execute(
                        "DELETE FROM trading212_prices WHERE ticker = ANY(%s);",
                        (tickers_to_clean,)
                    )
                    prices_deleted = cur.rowcount
                    
                    # Delete from trading212_candles_1m
                    cur.execute(
                        "DELETE FROM trading212_candles_1m WHERE ticker = ANY(%s);",
                        (tickers_to_clean,)
                    )
                    candles_deleted = cur.rowcount
                    
                    conn.commit()
                    print(f"[PostgreSQL] Successfully deleted {prices_deleted} rows from trading212_prices.")
                    print(f"[PostgreSQL] Successfully deleted {candles_deleted} rows from trading212_candles_1m.")
                else:
                    print("[PostgreSQL] No obsolete tickers found to clean.")
    except Exception as e:
        print(f"[PostgreSQL] Error during deletion: {e}")
        return False

    # 2. Redis Cleanup
    try:
        redis_client = get_redis_client()
        if redis_client:
            # Fetch all price keys
            redis_keys = redis_client.keys("price:*")
            print(f"Price keys currently in Redis: {redis_keys}")
            
            deleted_keys_count = 0
            for k in redis_keys:
                k_str = k.decode("utf-8") if isinstance(k, bytes) else k
                ticker = k_str.split("price:")[1]
                if ticker not in authorized_tickers:
                    if redis_client.delete(k):
                        deleted_keys_count += 1
                        print(f"Deleted Redis key: {k_str}")
            print(f"[Redis] Successfully deleted {deleted_keys_count} keys from Redis.")
        else:
            print("[Redis] Client not configured or unable to connect. Skipping Redis cleanup.")
    except Exception as e:
        print(f"[Redis] Error during deletion: {e}")

    # 3. Verification
    print("\nVerifying final state...")
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT ticker FROM trading212_prices ORDER BY ticker;")
                remaining_prices = [row[0] for row in cur.fetchall()]
                
                cur.execute("SELECT DISTINCT ticker FROM trading212_candles_1m ORDER BY ticker;")
                remaining_candles = [row[0] for row in cur.fetchall()]
                
                print(f"Remaining tickers in trading212_prices (total {len(remaining_prices)}): {remaining_prices}")
                print(f"Remaining tickers in trading212_candles_1m (total {len(remaining_candles)}): {remaining_candles}")
                
                # Check for any remaining unauthorized tickers
                unauthorized_remaining = [t for t in (remaining_prices + remaining_candles) if t not in authorized_tickers]
                if not unauthorized_remaining:
                    print("Verification SUCCESS: All obsolete tickers cleared!")
                    return True
                else:
                    print(f"Verification WARNING: Obsolete tickers still remain in database: {unauthorized_remaining}")
                    return False
    except Exception as e:
        print(f"Error during verification: {e}")
        return False

if __name__ == "__main__":
    clean_database()
