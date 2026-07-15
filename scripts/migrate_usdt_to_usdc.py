import os
import sys
import csv
import json
from datetime import datetime, timezone

# Add parent directory to path to allow imports from backtest_engine
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backtest_engine.live.connection import get_db_connection

def backup_data(conn, backup_dir="backups"):
    """Exports data that will be modified or deleted."""
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    with conn.cursor() as cur:
        # Backup live_prices
        cur.execute("SELECT * FROM live_prices WHERE ticker LIKE '%usdt'")
        prices_backup = cur.fetchall()
        if prices_backup:
            with open(f"{backup_dir}/live_prices_usdt_{timestamp}.json", "w") as f:
                json.dump([dict(zip([col.name for col in cur.description], row)) for row in prices_backup], f, default=str)

        # Backup strategy configs
        cur.execute("SELECT * FROM paper_strategy_configs WHERE asset LIKE '%usdt'")
        configs_backup = cur.fetchall()
        if configs_backup:
            with open(f"{backup_dir}/paper_strategy_configs_usdt_{timestamp}.json", "w") as f:
                json.dump([dict(zip([col.name for col in cur.description], row)) for row in configs_backup], f, default=str)

        # Backup conflicting live_candles_1m
        cur.execute("""
            SELECT c_usdt.*
            FROM live_candles_1m c_usdt
            JOIN live_candles_1m c_usdc
              ON c_usdc.ticker = REPLACE(c_usdt.ticker, 'usdt', 'usdc')
             AND c_usdc.timestamp_minute = c_usdt.timestamp_minute
            WHERE c_usdt.ticker LIKE '%usdt'
        """)
        candles_backup = cur.fetchall()
        if candles_backup:
            with open(f"{backup_dir}/live_candles_1m_conflicts_usdt_{timestamp}.json", "w") as f:
                json.dump([dict(zip([col.name for col in cur.description], row)) for row in candles_backup], f, default=str)

    print(f"[Backup] Data backed up to {backup_dir}/ at {timestamp}")
    return timestamp

def run_migration(confirm_purge=False):
    """
    Runs the USDT to USDC migration in a transactional and versioned manner.
    """
    if not confirm_purge:
        print("WARNING: This migration modifies the database and purges conflicting USDT data.")
        print("You must pass --confirm-purge to execute the migration.")
        sys.exit(1)

    print("Starting non-destructive USDT -> USDC migration...")

    try:
        with get_db_connection() as conn:
            # 1. Export backup before any operation
            backup_id = backup_data(conn)

            with conn.cursor() as cur:
                # 2. Create conflict tracking table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS migration_usdt_conflicts (
                        id SERIAL PRIMARY KEY,
                        migration_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        backup_id VARCHAR(100),
                        table_name VARCHAR(100),
                        conflict_key VARCHAR(255),
                        usdt_data JSONB,
                        usdc_data JSONB,
                        resolved BOOLEAN DEFAULT FALSE
                    )
                """)

                # 3. Transactional migration
                # -------------------------
                # A. live_prices
                # -------------------------
                print("Migrating live_prices...")
                cur.execute("""
                    WITH conflicting AS (
                        SELECT p_usdt.ticker as usdt_ticker, p_usdt.source,
                               row_to_json(p_usdt) as usdt_json, row_to_json(p_usdc) as usdc_json
                        FROM live_prices p_usdt
                        JOIN live_prices p_usdc ON p_usdc.ticker = REPLACE(p_usdt.ticker, 'usdt', 'usdc')
                        WHERE p_usdt.ticker LIKE '%usdt'
                    ),
                    logged AS (
                        INSERT INTO migration_usdt_conflicts (backup_id, table_name, conflict_key, usdt_data, usdc_data)
                        SELECT %s, 'live_prices', usdt_ticker, usdt_json, usdc_json
                        FROM conflicting
                        RETURNING conflict_key
                    )
                    DELETE FROM live_prices WHERE ticker IN (SELECT conflict_key FROM logged)
                """, (backup_id,))

                cur.execute("""
                    UPDATE live_prices SET ticker = REPLACE(ticker, 'usdt', 'usdc')
                    WHERE ticker LIKE '%usdt' AND source = 'bybit'
                """)

                # -------------------------
                # B. paper_strategy_configs
                # -------------------------
                print("Migrating paper_strategy_configs...")
                cur.execute("""
                    WITH conflicting AS (
                        SELECT c_usdt.asset as usdt_asset, c_usdt.strategy_name, c_usdt.timeframe,
                               row_to_json(c_usdt) as usdt_json, row_to_json(c_usdc) as usdc_json
                        FROM paper_strategy_configs c_usdt
                        JOIN paper_strategy_configs c_usdc
                          ON c_usdc.asset = REPLACE(c_usdt.asset, 'usdt', 'usdc')
                         AND c_usdc.strategy_name = c_usdt.strategy_name
                         AND c_usdc.timeframe = c_usdt.timeframe
                        WHERE c_usdt.asset LIKE '%usdt'
                    ),
                    logged AS (
                        INSERT INTO migration_usdt_conflicts (backup_id, table_name, conflict_key, usdt_data, usdc_data)
                        SELECT %s, 'paper_strategy_configs', usdt_asset || '|' || strategy_name || '|' || COALESCE(timeframe, ''), usdt_json, usdc_json
                        FROM conflicting
                        RETURNING usdt_json->>'id' as id
                    )
                    DELETE FROM paper_strategy_configs WHERE id::text IN (SELECT id FROM logged)
                """, (backup_id,))

                cur.execute("""
                    UPDATE paper_strategy_configs SET asset = REPLACE(asset, 'usdt', 'usdc')
                    WHERE asset LIKE '%usdt'
                """)

                # Note: live_candles_1m is huge, usually handled via TimescaleDB or dropping old partitions.
                # If needed, a similar strategy should be applied. For now, we only update non-conflicting ones
                # and leave conflicting ones to be handled by a dedicated timeseries merge job if needed.
                # Or we can do the basic migration here as it was in db_setup.py.
                print("Migrating live_candles_1m...")
                # Backup conflicting live_candles_1m before deletion
                cur.execute("""
                    WITH conflicting AS (
                        SELECT c_usdt.ticker as usdt_ticker, c_usdt.timestamp_minute,
                               row_to_json(c_usdt) as usdt_json, row_to_json(c_usdc) as usdc_json
                        FROM live_candles_1m c_usdt
                        JOIN live_candles_1m c_usdc
                          ON c_usdc.ticker = REPLACE(c_usdt.ticker, 'usdt', 'usdc')
                         AND c_usdc.timestamp_minute = c_usdt.timestamp_minute
                        WHERE c_usdt.ticker LIKE '%usdt'
                    ),
                    logged AS (
                        INSERT INTO migration_usdt_conflicts (backup_id, table_name, conflict_key, usdt_data, usdc_data)
                        SELECT %s, 'live_candles_1m', usdt_ticker || '|' || extract(epoch from timestamp_minute)::text, usdt_json, usdc_json
                        FROM conflicting
                        RETURNING (usdt_data->>'ticker')::text as ticker, (usdt_data->>'timestamp_minute')::timestamptz as ts
                    )
                    DELETE FROM live_candles_1m c_usdt
                    USING logged
                    WHERE c_usdt.ticker = logged.ticker AND c_usdt.timestamp_minute = logged.ts
                """, (backup_id,))
                cur.execute("""
                    UPDATE live_candles_1m SET ticker = REPLACE(ticker, 'usdt', 'usdc')
                    WHERE ticker LIKE '%usdt'
                """)

            conn.commit()
            print("Migration completed successfully.")

    except Exception as e:
        print(f"Migration failed! Transaction rolled back. Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    confirm = "--confirm-purge" in sys.argv
    run_migration(confirm_purge=confirm)
