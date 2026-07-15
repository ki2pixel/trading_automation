import os
import random
import string
import psycopg2
import pytest
from psycopg2.extras import RealDictCursor
from unittest.mock import patch

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_random_schema_name():
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_schema_{random_str}"

@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL not set")
class TestDBSetupMigration:
    @pytest.fixture(autouse=True)
    def setup_connection(self):
        self.db_url = os.getenv("DATABASE_URL")
        # Save old pool and reset it to force re-initialization with the schema option
        import backtest_engine.live.connection as conn_module
        self.conn_module = conn_module
        self.old_pool = conn_module._db_pool
        conn_module._db_pool = None

        # Connect to master schema to create/drop test schemas
        self.conn = psycopg2.connect(self.db_url)
        self.conn.autocommit = True
        
        yield
        
        # Close test pool if one was created
        if self.conn_module._db_pool is not None:
            try:
                self.conn_module._db_pool.closeall()
            except Exception:
                pass
        
        # Restore old pool
        self.conn_module._db_pool = self.old_pool
        self.conn.close()

    def get_test_db_url(self, schema_name):
        if "?" in self.db_url:
            return f"{self.db_url}&options=-csearch_path%3D{schema_name}"
        else:
            return f"{self.db_url}?options=-csearch_path%3D{schema_name}"

    def test_virgin_database_initialization(self):
        # Given: A virgin/fresh schema
        schema_name = get_random_schema_name()
        with self.conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA {schema_name}")

        try:
            # When: Running init_db with the schema set via search_path options in DATABASE_URL env
            test_db_url = self.get_test_db_url(schema_name)
            
            with patch.dict(os.environ, {"DATABASE_URL": test_db_url}):
                with patch("backtest_engine.live.paper_trading.db_setup.DATABASE_URL", test_db_url):
                    from backtest_engine.live.paper_trading.db_setup import init_db
                    init_db()

            # Then: Verify all tables and constraints were created successfully
            with psycopg2.connect(test_db_url) as conn:
                with conn.cursor() as cur:
                    # Verify tables exist
                    cur.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = %s
                    """, (schema_name,))
                    tables = {row[0] for row in cur.fetchall()}
                    expected_tables = {
                        'paper_portfolio_balance', 'paper_strategy_configs', 
                        'paper_positions', 'paper_transactions',
                        'paper_position_timeframe_reviews', 'live_prices',
                        'live_candles_1m', 'paper_evaluations'
                    }
                    assert expected_tables.issubset(tables)

                    # Verify constraints on paper_positions
                    cur.execute("""
                        SELECT conname, pg_get_constraintdef(oid) 
                        FROM pg_constraint 
                        WHERE conrelid = (quote_ident(%s) || '.paper_positions')::regclass
                    """, (schema_name,))
                    constraints = {row[0]: row[1] for row in cur.fetchall()}
                    
                    # Should NOT have the old unique constraint
                    assert 'paper_positions_asset_strategy_key' not in constraints
                    # Should have the new unique constraint with timeframe
                    assert 'paper_positions_asset_strategy_tf_key' in constraints
                    assert 'UNIQUE (asset, strategy_name, timeframe)' in constraints['paper_positions_asset_strategy_tf_key']

        finally:
            with self.conn.cursor() as cur:
                cur.execute(f"DROP SCHEMA {schema_name} CASCADE")

    def test_database_migration_and_backfill(self):
        # Given: An existing schema with the old layout (no timeframe on positions, old unique constraint)
        schema_name = get_random_schema_name()
        with self.conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA {schema_name}")

        test_db_url = self.get_test_db_url(schema_name)
        
        try:
            # 1. Setup the old schema layout manually
            with psycopg2.connect(test_db_url) as conn:
                with conn.cursor() as cur:
                    # Create the old paper_positions table layout
                    cur.execute("""
                        CREATE TABLE paper_positions (
                            id SERIAL PRIMARY KEY,
                            asset VARCHAR(50) NOT NULL,
                            strategy_name VARCHAR(100) NOT NULL,
                            qty NUMERIC NOT NULL CHECK (qty > 0),
                            entry_price NUMERIC NOT NULL CHECK (entry_price > 0),
                            current_price NUMERIC NOT NULL CHECK (current_price >= 0),
                            pnl NUMERIC NOT NULL DEFAULT 0,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            CONSTRAINT paper_positions_asset_strategy_key UNIQUE (asset, strategy_name)
                        )
                    """)
                    
                    # Insert historical positions to test backfill:
                    # AAPL: Only 1 config exists in SEED_CONFIGS (15m timeframe for ZEAL.CO/AAPL config)
                    # MSFT: Multiple configs will exist in our test strategy config table
                    # TSLA: No configs exist (should fallback to default '1m')
                    cur.execute("""
                        INSERT INTO paper_positions (asset, strategy_name, qty, entry_price, current_price) VALUES
                        ('AAPL', 'momentum_based_zigzag', 10, 150.0, 150.0),
                        ('MSFT', 'test_dual_tf', 5, 300.0, 300.0),
                        ('TSLA', 'unknown_strategy', 20, 200.0, 200.0)
                    """)

            # 2. When: Running init_db to migrate and backfill
            # We patch SEED_CONFIGS to contain the test configs so they are present during init_db backfill!
            test_configs = [
                {'strategy': 'momentum_based_zigzag', 'asset': 'AAPL', 'timeframe': '15m', 'kelly_weight': 0.1},
                {'strategy': 'test_dual_tf', 'asset': 'MSFT', 'timeframe': '5m', 'kelly_weight': 0.1},
                {'strategy': 'test_dual_tf', 'asset': 'MSFT', 'timeframe': '1h', 'kelly_weight': 0.1},
            ]
            
            with patch("backtest_engine.live.paper_trading.db_setup.SEED_CONFIGS", test_configs):
                with patch.dict(os.environ, {"DATABASE_URL": test_db_url}):
                    with patch("backtest_engine.live.paper_trading.db_setup.DATABASE_URL", test_db_url):
                        from backtest_engine.live.paper_trading.db_setup import init_db
                        init_db()

            # Verify the backfilled results from the first migration run
            with psycopg2.connect(test_db_url) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT asset, timeframe FROM paper_positions ORDER BY asset")
                    positions = {row['asset']: row['timeframe'] for row in cur.fetchall()}
                    
                    # AAPL had 1 config ('15m') -> Should match '15m'
                    assert positions['AAPL'] == '15m'
                    
                    # MSFT had 2 configs ('5m', '1h') -> Should be quarantined as 'AMBIGUOUS'
                    assert positions['MSFT'] == 'AMBIGUOUS'
                    
                    # TSLA had 0 configs -> Should keep default '1m'
                    assert positions['TSLA'] == '1m'

            # 3. Simulate post-migration operation:
            # We insert a new legitimate 1m position for MSFT (a strategy with multiple configurations)
            # This is created post-migration, so it has timeframe = '1m'.
            with psycopg2.connect(test_db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO paper_positions (asset, strategy_name, qty, entry_price, current_price, timeframe) 
                        VALUES ('MSFT', 'test_dual_tf', 10, 310.0, 310.0, '1m')
                    """)

            # Force re-initialization of pool for the reboot run
            self.conn_module._db_pool = None

            # 4. When: Running init_db again (simulating a system reboot)
            with patch("backtest_engine.live.paper_trading.db_setup.SEED_CONFIGS", test_configs):
                with patch.dict(os.environ, {"DATABASE_URL": test_db_url}):
                    with patch("backtest_engine.live.paper_trading.db_setup.DATABASE_URL", test_db_url):
                        from backtest_engine.live.paper_trading.db_setup import init_db
                        init_db()

            # Then: Verify that the legitimate post-migration 1m position was NOT modified to 'AMBIGUOUS'
            with psycopg2.connect(test_db_url) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Check the positions in the database
                    cur.execute("SELECT asset, timeframe, qty FROM paper_positions WHERE asset = 'MSFT' ORDER BY qty")
                    msft_positions = cur.fetchall()
                    assert len(msft_positions) == 2
                    
                    # First position (historical, qty=5) should still be 'AMBIGUOUS'
                    assert msft_positions[0]['qty'] == 5
                    assert msft_positions[0]['timeframe'] == 'AMBIGUOUS'
                    
                    # Second position (post-migration legitimate, qty=10) should still be '1m'
                    assert msft_positions[1]['qty'] == 10
                    assert msft_positions[1]['timeframe'] == '1m'

                    # Verify constraints on paper_positions table after migration
                    cur.execute("""
                        SELECT conname 
                        FROM pg_constraint 
                        WHERE conrelid = (quote_ident(%s) || '.paper_positions')::regclass
                    """, (schema_name,))
                    constraint_names = {row['conname'] for row in cur.fetchall()}
                    
                    # The old UNIQUE constraint MUST be dropped
                    assert 'paper_positions_asset_strategy_key' not in constraint_names
                    # The new UNIQUE constraint MUST be present
                    assert 'paper_positions_asset_strategy_tf_key' in constraint_names

        finally:
            with self.conn.cursor() as cur:
                cur.execute(f"DROP SCHEMA {schema_name} CASCADE")

    def test_database_migration_repair(self):
        # Given: An existing schema that ran the OLD migration (already has timeframe column,
        # but does NOT have Version 2 in schema_version table, and contains corrupted timeframes)
        schema_name = get_random_schema_name()
        with self.conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA {schema_name}")

        test_db_url = self.get_test_db_url(schema_name)
        
        try:
            # 1. Setup the old schema layout WITH timeframe column (simulating old migration run)
            with psycopg2.connect(test_db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE paper_positions (
                            id SERIAL PRIMARY KEY,
                            asset VARCHAR(50) NOT NULL,
                            strategy_name VARCHAR(100) NOT NULL,
                            qty NUMERIC NOT NULL CHECK (qty > 0),
                            entry_price NUMERIC NOT NULL CHECK (entry_price > 0),
                            current_price NUMERIC NOT NULL CHECK (current_price >= 0),
                            pnl NUMERIC NOT NULL DEFAULT 0,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            timeframe VARCHAR(10) NOT NULL DEFAULT '1m',
                            CONSTRAINT paper_positions_asset_strategy_key UNIQUE (asset, strategy_name)
                        )
                    """)
                    
                    # Insert positions that were migrated incorrectly by the old migration:
                    # AAPL: Should have been backfilled to '15m' but was left as '1m' or wrong.
                    # MSFT: Had multiple configs ('5m', '1h'), but old migration arbitrarily set it to '1h' via LIMIT 1.
                    # TSLA: No configs, should remain '1m'.
                    cur.execute("""
                        INSERT INTO paper_positions (asset, strategy_name, qty, entry_price, current_price, timeframe) VALUES
                        ('AAPL', 'momentum_based_zigzag', 10, 150.0, 150.0, '1m'),
                        ('MSFT', 'test_dual_tf', 5, 300.0, 300.0, '1h'),
                        ('TSLA', 'unknown_strategy', 20, 200.0, 200.0, '1m')
                    """)

            # 2. When: Running init_db (versioned repair migration)
            test_configs = [
                {'strategy': 'momentum_based_zigzag', 'asset': 'AAPL', 'timeframe': '15m', 'kelly_weight': 0.1},
                {'strategy': 'test_dual_tf', 'asset': 'MSFT', 'timeframe': '5m', 'kelly_weight': 0.1},
                {'strategy': 'test_dual_tf', 'asset': 'MSFT', 'timeframe': '1h', 'kelly_weight': 0.1},
            ]
            
            with patch("backtest_engine.live.paper_trading.db_setup.SEED_CONFIGS", test_configs):
                with patch.dict(os.environ, {"DATABASE_URL": test_db_url}):
                    with patch("backtest_engine.live.paper_trading.db_setup.DATABASE_URL", test_db_url):
                        from backtest_engine.live.paper_trading.db_setup import init_db
                        init_db()

            # Then: Verify that the corrupted databases were correctly audited and repaired
            with psycopg2.connect(test_db_url) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # Check the positions in the database
                    cur.execute("SELECT asset, timeframe FROM paper_positions ORDER BY asset")
                    positions = {row['asset']: row['timeframe'] for row in cur.fetchall()}
                    
                    # AAPL is repaired to '15m'
                    assert positions['AAPL'] == '15m'
                    
                    assert positions['MSFT'] == '1h'
                    assert positions['TSLA'] == '1m'

                    cur.execute("""
                        SELECT original_timeframe, candidate_timeframes, review_status
                        FROM paper_position_timeframe_reviews
                        WHERE position_id = (
                            SELECT id FROM paper_positions
                            WHERE asset = 'MSFT' AND strategy_name = 'test_dual_tf'
                        )
                          AND migration_version = 2
                    """)
                    review_row = cur.fetchone()
                    assert review_row is not None
                    assert review_row['original_timeframe'] == '1h'
                    assert review_row['candidate_timeframes'] == ['1h', '5m']
                    assert review_row['review_status'] == 'PENDING'

                    cur.execute("SELECT version, description FROM schema_version WHERE version = 2")
                    version_row = cur.fetchone()
                    assert version_row is not None
                    assert version_row['version'] == 2

            self.conn_module._db_pool = None
            with patch("backtest_engine.live.paper_trading.db_setup.SEED_CONFIGS", test_configs):
                with patch.dict(os.environ, {"DATABASE_URL": test_db_url}):
                    with patch("backtest_engine.live.paper_trading.db_setup.DATABASE_URL", test_db_url):
                        init_db()

            with psycopg2.connect(test_db_url) as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT timeframe FROM paper_positions
                        WHERE asset = 'MSFT' AND strategy_name = 'test_dual_tf'
                    """)
                    assert cur.fetchone()['timeframe'] == '1h'
                    cur.execute("""
                        SELECT COUNT(*) AS count
                        FROM paper_position_timeframe_reviews
                        WHERE migration_version = 2
                    """)
                    assert cur.fetchone()['count'] == 1

        finally:
            with self.conn.cursor() as cur:
                cur.execute(f"DROP SCHEMA {schema_name} CASCADE")
