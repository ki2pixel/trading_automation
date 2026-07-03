import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

# Old Supabase URL (from Git history / backup)
OLD_DB_URL = "postgresql://postgres.fqlwtzwxyriawjlgxgxs:sgEq%257RJKN438ZPW@aws-0-eu-west-3.pooler.supabase.com:5432/postgres"

# New Aiven URL (from environment or .env)
# Load dotenv if available to read from the updated .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

NEW_DB_URL = os.getenv("DATABASE_URL")

TABLES_TO_MIGRATE = [
    {
        "table": "paper_portfolio_balance",
        "conflict_clause": "ON CONFLICT (source) DO UPDATE SET cash_balance = EXCLUDED.cash_balance, allocated_balance = EXCLUDED.allocated_balance, total_nav = EXCLUDED.total_nav, secured_balance = EXCLUDED.secured_balance, last_updated = EXCLUDED.last_updated"
    },
    {
        "table": "paper_strategy_configs",
        "conflict_clause": "ON CONFLICT (strategy_name, asset, timeframe) DO UPDATE SET kelly_weight = EXCLUDED.kelly_weight, initial_capital = EXCLUDED.initial_capital, initial_capital_bucket = EXCLUDED.initial_capital_bucket, max_capital_bucket = EXCLUDED.max_capital_bucket, max_entry_price = EXCLUDED.max_entry_price, is_active = EXCLUDED.is_active, indicator_params = EXCLUDED.indicator_params, run_status = EXCLUDED.run_status, last_error = EXCLUDED.last_error"
    },
    {
        "table": "paper_positions",
        "truncate": True
    },
    {
        "table": "paper_transactions",
        "truncate": True
    },
    {
        "table": "paper_evaluations",
        "truncate": True
    },
    {
        "table": "conversion_accumulator",
        "truncate": True
    },
    {
        "table": "conversion_audit_log",
        "truncate": True
    },
    {
        "table": "live_prices",
        "conflict_clause": "ON CONFLICT (ticker) DO UPDATE SET price = EXCLUDED.price, source = EXCLUDED.source, updated_at = EXCLUDED.updated_at"
    },
    {
        "table": "live_candles_1m",
        "conflict_clause": "ON CONFLICT (ticker, timestamp_minute) DO UPDATE SET open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low, close = EXCLUDED.close"
    }
]

def migrate_data():
    if not NEW_DB_URL:
        print("[Migrate] ERROR: DATABASE_URL not set in environment or .env file.")
        sys.exit(1)
        
    print("[Migrate] Starting database migration from Supabase to Aiven...")
    print(f"[Migrate] Source DB (Supabase): {OLD_DB_URL.split('@')[1]}")
    print(f"[Migrate] Target DB (Aiven): {NEW_DB_URL.split('@')[1]}")
    
    try:
        # Connect to source and target databases
        src_conn = psycopg2.connect(OLD_DB_URL)
        tgt_conn = psycopg2.connect(NEW_DB_URL)
    except Exception as e:
        print(f"[Migrate] Connection failed: {e}")
        print("[Migrate] Make sure both databases are running and accessible.")
        sys.exit(1)
        
    try:
        for t_info in TABLES_TO_MIGRATE:
            table_name = t_info["table"]
            print(f"\n[Migrate] Migrating table: {table_name}...")
            
            # Fetch data from source
            with src_conn.cursor(cursor_factory=RealDictCursor) as src_cur:
                try:
                    src_cur.execute(f"SELECT * FROM {table_name};")
                    rows = src_cur.fetchall()
                except Exception as e:
                    print(f"[Migrate] Skipping {table_name}: table does not exist or failed to read: {e}")
                    src_conn.rollback()
                    continue
                    
            if not rows:
                print(f"[Migrate] No records found in source for {table_name}. Skipping.")
                continue
                
            print(f"[Migrate] Found {len(rows)} records in source.")
            
            # Write to target
            columns = rows[0].keys()
            col_list = ", ".join(columns)
            val_placeholder = ", ".join(["%s"] * len(columns))
            
            with tgt_conn.cursor() as tgt_cur:
                # 1. Truncate if specified
                if t_info.get("truncate"):
                    print(f"[Migrate] Truncating target table {table_name} before copy...")
                    tgt_cur.execute(f"TRUNCATE TABLE {table_name} CASCADE;")
                    
                # 2. Insert records using fast batch execution (execute_values)
                from psycopg2.extras import execute_values
                query = f"INSERT INTO {table_name} ({col_list}) VALUES %s"
                if "conflict_clause" in t_info:
                    query = f"{query} {t_info['conflict_clause']}"
                    
                # Serialize dicts to JSON string (e.g. indicator_params jsonb column)
                import json
                values_to_insert = []
                for row in rows:
                    row_vals = []
                    for col in columns:
                        val = row[col]
                        if isinstance(val, dict):
                            val = json.dumps(val)
                        row_vals.append(val)
                    values_to_insert.append(tuple(row_vals))
                
                execute_values(tgt_cur, query, values_to_insert)
                
                # 3. Automatically realign primary key sequence if 'id' column exists
                if "id" in columns:
                    try:
                        tgt_cur.execute(f"SELECT pg_get_serial_sequence('{table_name}', 'id');")
                        seq_name = tgt_cur.fetchone()[0]
                        if seq_name:
                            tgt_cur.execute(f"SELECT setval('{seq_name}', COALESCE(MAX(id), 1)) FROM {table_name};")
                            new_val = tgt_cur.fetchone()[0]
                            print(f"[Migrate] Automatically set sequence '{seq_name}' to {new_val}.")
                        else:
                            print(f"[Migrate] No sequence associated with 'id' in table {table_name}.")
                    except Exception as seq_err:
                        print(f"[Migrate] Warning: Could not realign sequence for {table_name}: {seq_err}")
                
                tgt_conn.commit()
                print(f"[Migrate] Successfully inserted/updated {len(rows)} rows in target.")
                
        print("\n[Migrate] Migration completed successfully!")
    except Exception as e:
        tgt_conn.rollback()
        print(f"\n[Migrate] Migration failed: {e}")
    finally:
        src_conn.close()
        tgt_conn.close()

if __name__ == "__main__":
    migrate_data()
