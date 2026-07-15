import os
import sys
import psycopg2
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DATABASE_URL = os.getenv("DATABASE_URL")

def test_insert():
    if not DATABASE_URL:
        print("[Test] ERROR: DATABASE_URL not set.")
        sys.exit(1)

    print("[Test] Connecting to database...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print(f"[Test] Connection failed: {e}")
        sys.exit(1)

    try:
        with conn.cursor() as cur:
            print("[Test] Inserting dummy transaction into paper_transactions...")
            # We omit the 'id' column to let the SERIAL sequence generate it
            cur.execute("""
                INSERT INTO paper_transactions (asset, strategy_name, action, qty, price, total_value)
                VALUES ('TEST_ASSET', 'test_strategy', 'BUY', 1.0, 100.0, 100.0)
                RETURNING id;
            """)
            inserted_id = cur.fetchone()[0]
            print(f"[Test] Successfully inserted transaction. Generated ID: {inserted_id}")

            # Clean up the dummy transaction
            cur.execute("DELETE FROM paper_transactions WHERE id = %s;", (inserted_id,))
            conn.commit()
            print("[Test] Dummy transaction cleaned up successfully.")
    except Exception as e:
        conn.rollback()
        print(f"[Test] Insertion failed: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    test_insert()
