import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, "/home/kidpixel/trading_automation-main")
load_dotenv()

from backtest_engine.live.connection import get_db_connection, get_redis_client

tickers_to_clean = [
    "ABI_BE_EQ", "ACp_EQ", "AKZAa_EQ", "AMSe_EQ", "CAp_EQ",
    "DAId_EQ", "DPWd_EQ", "EVDd_EQ", "FPEd_EQ", "GE9d_EQ",
    "LXSd_EQ", "MRKd_EQ", "NOTd1_EQ", "NOVCd_EQ", "PROX_BE_EQ",
    "RANDa_EQ", "RUIp_EQ", "SAPd_EQ", "TIMd_EQ", "TW10d_EQ",
    "VNAd_EQ"
]

def clean_database():
    print("Starting database cleanup...")
    
    # 1. PostgreSQL Cleanup
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
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
    except Exception as e:
        print(f"[PostgreSQL] Error during deletion: {e}")
        return False

    # 2. Redis Cleanup
    try:
        redis_client = get_redis_client()
        if redis_client:
            redis_keys = [f"price:{t}" for t in tickers_to_clean]
            deleted_keys_count = 0
            for k in redis_keys:
                if redis_client.delete(k):
                    deleted_keys_count += 1
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
                cur.execute(
                    "SELECT COUNT(*) FROM trading212_prices WHERE ticker = ANY(%s);",
                    (tickers_to_clean,)
                )
                prices_rem = cur.fetchone()[0]
                
                cur.execute(
                    "SELECT COUNT(*) FROM trading212_candles_1m WHERE ticker = ANY(%s);",
                    (tickers_to_clean,)
                )
                candles_rem = cur.fetchone()[0]
                
                print(f"Remaining rows in trading212_prices: {prices_rem}")
                print(f"Remaining rows in trading212_candles_1m: {candles_rem}")
                if prices_rem == 0 and candles_rem == 0:
                    print("Verification SUCCESS: All obsolete tickers cleared!")
                    return True
                else:
                    print("Verification WARNING: Obsolete tickers still remain in database.")
                    return False
    except Exception as e:
        print(f"Error during verification: {e}")
        return False

if __name__ == "__main__":
    clean_database()
