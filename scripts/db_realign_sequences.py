import os
import sys
import psycopg2
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DATABASE_URL = os.getenv("DATABASE_URL")

TABLES_TO_REALIGN = [
    "paper_portfolio_balance",
    "paper_positions",
    "paper_transactions",
    "paper_strategy_configs",
    "paper_evaluations",
    "conversion_accumulator",
    "conversion_audit_log"
]

def realign_sequences():
    if not DATABASE_URL:
        print("[Realign] ERROR: DATABASE_URL not set in environment or .env file.")
        sys.exit(1)
        
    print("[Realign] Connecting to database...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print(f"[Realign] Connection failed: {e}")
        sys.exit(1)
        
    try:
        with conn.cursor() as cur:
            for table in TABLES_TO_REALIGN:
                print(f"[Realign] Realigning sequence for table: {table}...")
                
                # Check if table exists
                cur.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s
                    );
                """, (table,))
                exists = cur.fetchone()[0]
                if not exists:
                    print(f"[Realign] Table {table} does not exist. Skipping.")
                    continue
                
                # Run setval query
                query = f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table}', 'id'), 
                        COALESCE(MAX(id), 1)
                    ) FROM {table};
                """
                try:
                    cur.execute(query)
                    new_val = cur.fetchone()[0]
                    print(f"[Realign] Sequence for '{table}' successfully set to {new_val}.")
                except Exception as ex:
                    print(f"[Realign] Failed to realign '{table}': {ex}")
                    conn.rollback()
                    continue
            
            conn.commit()
            print("[Realign] Sequence realigning completed successfully!")
    except Exception as e:
        conn.rollback()
        print(f"[Realign] Transaction failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    realign_sequences()
