import os
import json
from typing import Any
from decimal import Decimal
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from backtest_engine.live.utils import is_crypto_asset

DATABASE_URL = os.getenv("DATABASE_URL")

SEED_CONFIGS = [
    {
        "strategy": "cybernetic_hilbert",
        "asset": "ZEAL.CO",
        "timeframe": "45m",
        "kelly_weight": 0.0079,
        "indicator_params": {
            "hilbert_smooth_period": 12,
            "take_profit_net_percent": 12.0,
            "stop_loss_net_percent": 1.0,
            "phase_mode_enabled": False,
            "use_net_bracket_exits": True,
            "use_safety_stop": False
        }
    },
    {
        "strategy": "momentum_based_zigzag",
        "asset": "NVO",
        "timeframe": "45m",
        "kelly_weight": 0.0073,
        "indicator_params": {
            "rsi_period": 8,
            "qqe_factor": 2.0,
            "rsi_smoothing": 4,
            "ob": 82.0,
            "os": 10.0,
            "signal_mode": "Close",
            "enable_stop_loss": True,
            "stop_loss_pct": 0.5,
            "enable_take_profit": True,
            "take_profit_pct": 11.9,
            "enable_trailing_stop": False
        }
    },
    {
        "strategy": "3commas_bot",
        "asset": "EVD.DE",
        "timeframe": "30m",
        "kelly_weight": 0.0132,
        "indicator_params": {
            "ma_type1": "DEMA",
            "ma_length1": 40,
            "ma_type2": "HMA",
            "ma_length2": 140,
            "rnr": 1.2,
            "risk_m": 0.8,
            "swing_lookback": 5,
            "trail_stop": False
        }
    },
    {
        "strategy": "3commas_bot",
        "asset": "GMAB",
        "timeframe": "60m",
        "kelly_weight": 0.0123,
        "indicator_params": {
            "ma_type1": "DEMA",
            "ma_length1": 8,
            "ma_type2": "HMA",
            "ma_length2": 10,
            "rnr": 0.5,
            "risk_m": 2.5,
            "swing_lookback": 5,
            "trail_stop": False
        }
    },
    {
        "strategy": "3commas_bot",
        "asset": "FPE.DE",
        "timeframe": "20m",
        "kelly_weight": 0.0093,
        "indicator_params": {
            "ma_type1": "DEMA",
            "ma_length1": 30,
            "ma_type2": "HMA",
            "ma_length2": 32,
            "rnr": 1.0,
            "risk_m": 1.5,
            "swing_lookback": 5,
            "trail_stop": False
        }
    },
    {
        "strategy": "adaptive_volatility_trend",
        "asset": "dpwdeeur",
        "timeframe": "45m",
        "kelly_weight": 0.0322,
        "indicator_params": {
            "length": 45,
            "atr_len": 10,
            "atr_mult": 3.9,
            "use_rsi": True,
            "rsi_len": 10,
            "rsi_OB": 76.0,
            "rsi_OS": 40.0,
            "use_vol": False
        }
    },
    {
        "strategy": "3commas_bot",
        "asset": "teniteur",
        "timeframe": "30m",
        "kelly_weight": 0.0155,
        "indicator_params": {
            "ma_type1": "HEMA",
            "ma_length1": 5,
            "ma_type2": "SMA",
            "ma_length2": 38,
            "rnr": 0.5,
            "risk_m": 0.8,
            "swing_lookback": 5,
            "trail_stop": False
        }
    },
    {
        "strategy": "adaptive_volatility_trend",
        "asset": "akzanleur",
        "timeframe": "30m",
        "kelly_weight": 0.0322,
        "indicator_params": {
            "length": 25,
            "atr_len": 12,
            "atr_mult": 3.5,
            "use_rsi": True,
            "rsi_len": 7,
            "rsi_OB": 80.0,
            "rsi_OS": 34.0,
            "use_vol": True
        }
    },
    {
        "strategy": "momentum_based_zigzag",
        "asset": "daideeur",
        "timeframe": "15m",
        "kelly_weight": 0.0066,
        "indicator_params": {
            "rsi_period": 17,
            "qqe_factor": 4.1,
            "rsi_smoothing": 5,
            "ob": 89.0,
            "os": 10.0,
            "signal_mode": "Close",
            "enable_stop_loss": True,
            "stop_loss_pct": 0.5,
            "enable_take_profit": True,
            "take_profit_pct": 7.8,
            "enable_trailing_stop": False
        }
    },
    {
        "strategy": "momentum_based_zigzag",
        "asset": "SAP",
        "timeframe": "30m",
        "kelly_weight": 0.0154,
        "indicator_params": {
            "rsi_period": 25,
            "qqe_factor": 5.6,
            "rsi_smoothing": 15,
            "ob": 79.0,
            "os": 18.0,
            "signal_mode": "Live",
            "enable_stop_loss": True,
            "stop_loss_pct": 4.8,
            "enable_take_profit": True,
            "take_profit_pct": 13.4,
            "enable_trailing_stop": False
        }
    },
    {
        "strategy": "hmm_regime_filter",
        "asset": "mrkdeeur",
        "timeframe": "45m",
        "kelly_weight": 0.0057,
        "indicator_params": {
            "obs_len": 30,
            "stat_len": 15,
            "mu_k": 2.0,
            "stick": 0.9,
            "confirm_bars": 2,
            "dom_thresh": 0.3,
            "use_safety_stop": True,
            "take_profit_net_percent": 4.0,
            "stop_loss_net_percent": 1.0
        }
    },
    {
        "strategy": "momentum_based_zigzag",
        "asset": "AMS.MC",
        "timeframe": "10m",
        "kelly_weight": 0.0077,
        "indicator_params": {
            "rsi_period": 14,
            "qqe_factor": 2.5,
            "rsi_smoothing": 3,
            "ob": 66.0,
            "os": 35.0,
            "signal_mode": "Live",
            "enable_stop_loss": True,
            "stop_loss_pct": 0.5,
            "enable_take_profit": True,
            "take_profit_pct": 15.0,
            "enable_trailing_stop": False
        }
    },
    {
        "strategy": "momentum_based_zigzag",
        "asset": "vnadeeur",
        "timeframe": "10m",
        "kelly_weight": 0.0056,
        "indicator_params": {
            "rsi_period": 16,
            "qqe_factor": 1.6,
            "rsi_smoothing": 15,
            "ob": 76.0,
            "os": 20.0,
            "signal_mode": "Live",
            "enable_stop_loss": True,
            "stop_loss_pct": 0.7,
            "enable_take_profit": True,
            "take_profit_pct": 14.7,
            "enable_trailing_stop": False
        }
    },
    {
        "strategy": "hmm_regime_filter",
        "asset": "acfreur",
        "timeframe": "15m",
        "kelly_weight": 0.0060,
        "indicator_params": {
            "obs_len": 21,
            "stat_len": 91,
            "mu_k": 0.5,
            "stick": 0.6,
            "confirm_bars": 2,
            "dom_thresh": 0.5,
            "use_safety_stop": True,
            "take_profit_net_percent": 18.0,
            "stop_loss_net_percent": 1.0
        }
    },
    {
        "strategy": "hmm_regime_filter",
        "asset": "lxsdeeur",
        "timeframe": "30m",
        "kelly_weight": 0.0048,
        "indicator_params": {
            "obs_len": 28,
            "stat_len": 85,
            "mu_k": 1.0,
            "stick": 0.6,
            "confirm_bars": 1,
            "dom_thresh": 0.3,
            "use_safety_stop": True,
            "take_profit_net_percent": 20.0,
            "stop_loss_net_percent": 1.0
        }
    },
    {
        "strategy": "momentum_based_zigzag",
        "asset": "randnleur",
        "timeframe": "10m",
        "kelly_weight": 0.0116,
        "indicator_params": {
            "rsi_period": 18,
            "qqe_factor": 6.0,
            "rsi_smoothing": 2,
            "ob": 73.0,
            "os": 28.0,
            "signal_mode": "Live",
            "enable_stop_loss": True,
            "stop_loss_pct": 5.0,
            "enable_take_profit": True,
            "take_profit_pct": 13.4,
            "enable_trailing_stop": False
        }
    },
    {
        "strategy": "hmm_regime_filter",
        "asset": "rifreur",
        "timeframe": "10m",
        "kelly_weight": 0.0052,
        "indicator_params": {
            "obs_len": 26,
            "stat_len": 47,
            "mu_k": 1.2,
            "stick": 0.9,
            "confirm_bars": 5,
            "dom_thresh": 0.7,
            "use_safety_stop": False,
            "take_profit_net_percent": 20.0,
            "stop_loss_net_percent": 2.0
        }
    },
    {
        "strategy": "hmm_regime_filter",
        "asset": "abibeeur",
        "timeframe": "15m",
        "kelly_weight": 0.0048,
        "indicator_params": {
            "obs_len": 28,
            "stat_len": 89,
            "mu_k": 2.7,
            "stick": 0.6,
            "confirm_bars": 2,
            "dom_thresh": 0.5,
            "use_safety_stop": True,
            "take_profit_net_percent": 20.0,
            "stop_loss_net_percent": 1.0
        }
    },
    {
        "strategy": "momentum_based_zigzag",
        "asset": "belgbeeur",
        "timeframe": "10m",
        "kelly_weight": 0.0049,
        "indicator_params": {
            "rsi_period": 22,
            "qqe_factor": 5.0,
            "rsi_smoothing": 15,
            "ob": 90.0,
            "os": 24.0,
            "signal_mode": "Live",
            "enable_stop_loss": True,
            "stop_loss_pct": 0.5,
            "enable_take_profit": True,
            "take_profit_pct": 4.6,
            "enable_trailing_stop": False
        }
    },
    {
        "strategy": "momentum_based_zigzag",
        "asset": "cafreur",
        "timeframe": "15m",
        "kelly_weight": 0.0039,
        "indicator_params": {
            "rsi_period": 15,
            "qqe_factor": 1.5,
            "rsi_smoothing": 10,
            "ob": 82.0,
            "os": 23.0,
            "signal_mode": "Close",
            "enable_stop_loss": True,
            "stop_loss_pct": 0.9,
            "enable_take_profit": True,
            "take_profit_pct": 8.4,
            "enable_trailing_stop": False
        }
    },
    {
        "strategy": "trend_type",
        "asset": "NVS",
        "timeframe": "15m",
        "kelly_weight": 0.0093,
        "indicator_params": {
            "atr_len": 13,
            "atr_ma_len": 12,
            "adx_len": 20,
            "di_len": 17,
            "adx_lim": 33.0,
            "smooth": 5,
            "signal_mode": "Close"
        }
    },
    {
        "strategy": "cybernetic_hilbert",
        "asset": "ltcusdc",
        "timeframe": "45m",
        "kelly_weight": 0.0054,
        "indicator_params": {
            "phase_mode_enabled": False,
            "use_safety_stop": True,
            "safety_max_bars_in_trade": 20,
            "hilbert_smooth_period": 12,
            "take_profit_net_percent": 20.0,
            "stop_loss_net_percent": 1.0
        }
    },
    {
        "strategy": "cybernetic_hilbert",
        "asset": "dotusdc",
        "timeframe": "60m",
        "kelly_weight": 0.0057,
        "indicator_params": {
            "phase_mode_enabled": False,
            "use_safety_stop": True,
            "safety_max_bars_in_trade": 50,
            "hilbert_smooth_period": 6,
            "take_profit_net_percent": 19.0,
            "stop_loss_net_percent": 1.0
        }
    }
]

def reconcile_allocated_balances(conn: Any) -> None:
    """
    Reconciles paper_portfolio_balance.allocated_balance with the sum of
    committed capital (qty * entry_price) for open positions in paper_positions.
    Uses FOR UPDATE transactional locking to prevent race conditions.
    """
    from backtest_engine.live.utils import is_crypto_asset

    with conn.cursor() as cur:
        # Lock paper_portfolio_balance rows for update and fetch existing sources
        cur.execute("SELECT source FROM paper_portfolio_balance FOR UPDATE")
        balance_rows = cur.fetchall()

        allocated_sums = {r[0]: Decimal("0") for r in balance_rows}
        if "trading212" not in allocated_sums:
            allocated_sums["trading212"] = Decimal("0")
        if "bybit" not in allocated_sums:
            allocated_sums["bybit"] = Decimal("0")

        # Fetch open positions
        cur.execute("SELECT asset, qty, entry_price FROM paper_positions")
        positions = cur.fetchall()

        for row in positions:
            asset = row[0]
            qty = row[1]
            entry_price = row[2]

            if qty is not None and entry_price is not None:
                qty_dec = Decimal(str(qty))
                entry_dec = Decimal(str(entry_price))
                cost = qty_dec * entry_dec
                source = 'bybit' if is_crypto_asset(asset) else 'trading212'
                if source in allocated_sums:
                    allocated_sums[source] += cost
                else:
                    allocated_sums[source] = cost

        for source, allocated_real in allocated_sums.items():
            cur.execute(
                """
                UPDATE paper_portfolio_balance
                SET allocated_balance = %s,
                    last_updated = CURRENT_TIMESTAMP
                WHERE source = %s
                """,
                (allocated_real, source)
            )

def init_db():
    if not DATABASE_URL:
        print("[DB Setup] DATABASE_URL not set. Skipping setup.")
        return

    try:
        from backtest_engine.live.connection import get_sync_connection
        with get_sync_connection() as conn:
            with conn.cursor() as cur:
                # 0. Migration: Check and rename old tables if they exist
                cur.execute("""
                    DO $$
                    BEGIN
                        IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = current_schema() AND table_name = 'trading212_prices') AND 
                           NOT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = current_schema() AND table_name = 'live_prices') THEN
                            ALTER TABLE trading212_prices RENAME TO live_prices;
                        END IF;
                        
                        IF EXISTS (SELECT FROM information_schema.tables WHERE table_schema = current_schema() AND table_name = 'trading212_candles_1m') AND 
                           NOT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = current_schema() AND table_name = 'live_candles_1m') THEN
                            ALTER TABLE trading212_candles_1m RENAME TO live_candles_1m;
                        END IF;
                    END $$;
                """)

                # 0b. Create schema_version table if it doesn't exist
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INT PRIMARY KEY,
                        applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        description VARCHAR(255)
                    )
                """)
                
                # Check if Version 2 has been applied
                cur.execute("SELECT EXISTS (SELECT 1 FROM schema_version WHERE version = 2)")
                v2_applied = cur.fetchone()[0]

                # Check if timeframe column exists in paper_positions
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = current_schema()
                          AND table_name = 'paper_positions'
                    );
                """)
                table_exists = cur.fetchone()[0]
                
                timeframe_column_exists = False
                if table_exists:
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_schema = current_schema()
                              AND table_name = 'paper_positions'
                              AND column_name = 'timeframe'
                        );
                    """)
                    timeframe_column_exists = cur.fetchone()[0]
                
                run_timeframe_backfill = not timeframe_column_exists and not v2_applied
                run_timeframe_repair = timeframe_column_exists and not v2_applied

                # NOTE: USDT→USDC migration is handled exclusively by the manual script
                # scripts/migrate_usdt_to_usdc.py (with --confirm-purge, JSON export, and conflict journaling).
                # No automatic data deletion at startup.



                # 1. Create Portfolio Balance table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS paper_portfolio_balance (
                        id SERIAL PRIMARY KEY,
                        source VARCHAR(50) NOT NULL DEFAULT 'trading212' UNIQUE,
                        paper_cash_balance NUMERIC NOT NULL DEFAULT 100000 CHECK (paper_cash_balance >= 0),
                        allocated_balance NUMERIC NOT NULL DEFAULT 0,
                        total_nav NUMERIC NOT NULL DEFAULT 100000 CHECK (total_nav >= 0),
                        secured_balance NUMERIC NOT NULL DEFAULT 0,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Migrate paper_portfolio_balance to add source and secured_balance if they don't exist
                # Also rename cash_balance to paper_cash_balance if it exists
                cur.execute("""
                    DO $$
                    BEGIN
                        IF EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_schema = current_schema()
                              AND table_name='paper_portfolio_balance' 
                              AND column_name='cash_balance'
                        ) THEN
                            ALTER TABLE paper_portfolio_balance RENAME COLUMN cash_balance TO paper_cash_balance;
                        END IF;
                    END $$;
                    ALTER TABLE paper_portfolio_balance ADD COLUMN IF NOT EXISTS source VARCHAR(50) NOT NULL DEFAULT 'trading212';
                    ALTER TABLE paper_portfolio_balance ADD COLUMN IF NOT EXISTS secured_balance NUMERIC NOT NULL DEFAULT 0;
                    -- Ensure UNIQUE constraint on source column
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.table_constraints 
                            WHERE table_schema = current_schema()
                              AND table_name='paper_portfolio_balance' 
                              AND constraint_type='UNIQUE'
                        ) THEN
                            ALTER TABLE paper_portfolio_balance ADD CONSTRAINT paper_portfolio_balance_source_key UNIQUE (source);
                        END IF;
                    END $$;
                """)

                # Seed the double portfolio balances
                cur.execute("""
                    INSERT INTO paper_portfolio_balance (source, paper_cash_balance, total_nav)
                    VALUES ('trading212', 100000, 100000)
                    ON CONFLICT (source) DO NOTHING;
                """)
                cur.execute("""
                    INSERT INTO paper_portfolio_balance (source, paper_cash_balance, total_nav)
                    VALUES ('bybit', 10000, 10000)
                    ON CONFLICT (source) DO NOTHING;
                """)

                # 2. Create Positions table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS paper_positions (
                        id SERIAL PRIMARY KEY,
                        asset VARCHAR(50) NOT NULL,
                        strategy_name VARCHAR(100) NOT NULL,
                        timeframe VARCHAR(10) NOT NULL DEFAULT '1m',
                        qty NUMERIC NOT NULL CHECK (qty > 0),
                        entry_price NUMERIC NOT NULL CHECK (entry_price > 0),
                        current_price NUMERIC NOT NULL CHECK (current_price >= 0),
                        pnl NUMERIC NOT NULL DEFAULT 0,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT paper_positions_asset_strategy_tf_key UNIQUE (asset, strategy_name, timeframe)
                    )
                """)

                # 3. Create Transactions table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS paper_transactions (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        asset VARCHAR(50) NOT NULL,
                        strategy_name VARCHAR(100) NOT NULL,
                        action VARCHAR(20) NOT NULL CHECK (UPPER(action) IN ('BUY', 'SELL')),
                        qty NUMERIC NOT NULL CHECK (qty > 0),
                        price NUMERIC NOT NULL CHECK (price > 0),
                        total_value NUMERIC NOT NULL CHECK (total_value > 0)
                    )
                """)

                # 3b. Migrate existing paper_positions: add timeframe column if not exists
                cur.execute("""
                    ALTER TABLE paper_positions ADD COLUMN IF NOT EXISTS timeframe VARCHAR(10) NOT NULL DEFAULT '1m';
                """)
                cur.execute("""
                    DO $$
                    BEGIN
                        -- Drop old constraint if it exists
                        IF EXISTS (
                            SELECT 1 FROM information_schema.table_constraints
                            WHERE table_schema = current_schema()
                              AND table_name='paper_positions' 
                              AND constraint_name='paper_positions_asset_strategy_key'
                        ) THEN
                            ALTER TABLE paper_positions DROP CONSTRAINT paper_positions_asset_strategy_key;
                        END IF;
                        -- Add new constraint if it doesn't exist
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.table_constraints
                            WHERE table_schema = current_schema()
                              AND table_name='paper_positions' 
                              AND constraint_name='paper_positions_asset_strategy_tf_key'
                        ) THEN
                            ALTER TABLE paper_positions ADD CONSTRAINT paper_positions_asset_strategy_tf_key
                                UNIQUE (asset, strategy_name, timeframe);
                        END IF;
                    END $$;
                """)

                # 4. Create Strategy Configs table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS paper_strategy_configs (
                        id SERIAL PRIMARY KEY,
                        strategy_name VARCHAR(100) NOT NULL,
                        asset VARCHAR(50) NOT NULL,
                        timeframe VARCHAR(20) NOT NULL,
                        kelly_weight NUMERIC NOT NULL,
                        initial_capital NUMERIC NOT NULL DEFAULT 1000,
                        initial_capital_bucket NUMERIC NOT NULL DEFAULT 1000,
                        max_capital_bucket NUMERIC NOT NULL DEFAULT 5000,
                        max_entry_price NUMERIC NOT NULL DEFAULT 10000,
                        is_active BOOLEAN DEFAULT TRUE,
                        indicator_params JSONB DEFAULT '{}'::jsonb,
                        last_error TEXT DEFAULT NULL,
                        UNIQUE(strategy_name, asset, timeframe)
                    )
                """)
                
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS paper_position_timeframe_reviews (
                        id SERIAL PRIMARY KEY,
                        position_id INTEGER NOT NULL,
                        migration_version INTEGER NOT NULL,
                        original_timeframe VARCHAR(10) NOT NULL,
                        candidate_timeframes JSONB NOT NULL,
                        review_status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        resolved_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
                        CONSTRAINT paper_position_timeframe_reviews_status_check
                            CHECK (review_status IN ('PENDING', 'RESOLVED')),
                        CONSTRAINT paper_position_timeframe_reviews_position_version_key
                            UNIQUE (position_id, migration_version)
                    )
                """)

                # 5. Create Live Prices and Candles tables (if not migrated)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS live_prices (
                        ticker VARCHAR(50) PRIMARY KEY,
                        price NUMERIC(15, 6) NOT NULL,
                        source VARCHAR(50) NOT NULL DEFAULT 'trading212',
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cur.execute("""
                    ALTER TABLE live_prices ADD COLUMN IF NOT EXISTS source VARCHAR(50) NOT NULL DEFAULT 'trading212';
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS live_candles_1m (
                        ticker VARCHAR(50),
                        timestamp_minute TIMESTAMP WITH TIME ZONE,
                        open NUMERIC(15, 6) NOT NULL,
                        high NUMERIC(15, 6) NOT NULL,
                        low NUMERIC(15, 6) NOT NULL,
                        close NUMERIC(15, 6) NOT NULL,
                        PRIMARY KEY (ticker, timestamp_minute)
                    );
                """)
                # Performance index for eval cycle candle fetch (DESC scan)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_live_candles_1m_ticker_ts_desc
                    ON live_candles_1m (ticker, timestamp_minute DESC);
                """)

                # 6. Create Evaluations table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS paper_evaluations (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        strategy_name VARCHAR(100) NOT NULL,
                        asset VARCHAR(50) NOT NULL,
                        timeframe VARCHAR(20) NOT NULL,
                        price NUMERIC,
                        signal_type VARCHAR(20),
                        signal_triggered BOOLEAN,
                        status VARCHAR(50),
                        fail_reason TEXT,
                        details JSONB
                    )
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_paper_eval_timestamp ON paper_evaluations (timestamp DESC)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_paper_eval_strat_asset ON paper_evaluations (strategy_name, asset)")

                # 7. Create Conversion Accumulator table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS conversion_accumulator (
                        id SERIAL PRIMARY KEY,
                        source VARCHAR(50) NOT NULL DEFAULT 'bybit',
                        amount NUMERIC NOT NULL,
                        trade_ref VARCHAR(100) DEFAULT '',
                        drained BOOLEAN NOT NULL DEFAULT FALSE,
                        conversion_id VARCHAR(100) DEFAULT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        drained_at TIMESTAMP WITH TIME ZONE DEFAULT NULL
                    )
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_conv_acc_source_drained ON conversion_accumulator (source, drained)")

                # 8. Create Conversion Audit Log table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS conversion_audit_log (
                        id SERIAL PRIMARY KEY,
                        client_order_id VARCHAR(100) NOT NULL UNIQUE,
                        broker_order_id VARCHAR(100),
                        status VARCHAR(50) NOT NULL,
                        qty_usdc NUMERIC NOT NULL,
                        filled_qty_eur NUMERIC DEFAULT 0,
                        avg_fill_price NUMERIC DEFAULT 0,
                        fee_usdc NUMERIC DEFAULT 0,
                        error_message TEXT,
                        dry_run BOOLEAN NOT NULL DEFAULT TRUE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_conv_audit_status ON conversion_audit_log (status)")
                
                # Migrations: Alter timestamp columns to TIMESTAMP WITH TIME ZONE
                cur.execute("ALTER TABLE paper_positions ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE;")
                cur.execute("ALTER TABLE paper_transactions ALTER COLUMN timestamp TYPE TIMESTAMP WITH TIME ZONE;")
                cur.execute("ALTER TABLE paper_evaluations ALTER COLUMN timestamp TYPE TIMESTAMP WITH TIME ZONE;")
                
                # Migration: Add CHECK constraints to existing tables idempotently
                cur.execute("""
                    DO $$
                    BEGIN
                        -- For paper_portfolio_balance
                        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'paper_portfolio_balance_cash_check') THEN
                            ALTER TABLE paper_portfolio_balance ADD CONSTRAINT paper_portfolio_balance_cash_check CHECK (paper_cash_balance >= 0);
                        END IF;
                        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'paper_portfolio_balance_nav_check') THEN
                            ALTER TABLE paper_portfolio_balance ADD CONSTRAINT paper_portfolio_balance_nav_check CHECK (total_nav >= 0);
                        END IF;

                        -- For paper_positions
                        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'paper_positions_qty_check') THEN
                            ALTER TABLE paper_positions ADD CONSTRAINT paper_positions_qty_check CHECK (qty > 0);
                        END IF;
                        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'paper_positions_entry_price_check') THEN
                            ALTER TABLE paper_positions ADD CONSTRAINT paper_positions_entry_price_check CHECK (entry_price > 0);
                        END IF;
                        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'paper_positions_current_price_check') THEN
                            ALTER TABLE paper_positions ADD CONSTRAINT paper_positions_current_price_check CHECK (current_price >= 0);
                        END IF;

                        -- For paper_transactions
                        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'paper_transactions_action_check') THEN
                            ALTER TABLE paper_transactions ADD CONSTRAINT paper_transactions_action_check CHECK (UPPER(action) IN ('BUY', 'SELL'));
                        END IF;
                        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'paper_transactions_qty_check') THEN
                            ALTER TABLE paper_transactions ADD CONSTRAINT paper_transactions_qty_check CHECK (qty > 0);
                        END IF;
                        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'paper_transactions_price_check') THEN
                            ALTER TABLE paper_transactions ADD CONSTRAINT paper_transactions_price_check CHECK (price > 0);
                        END IF;
                        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'paper_transactions_value_check') THEN
                            ALTER TABLE paper_transactions ADD CONSTRAINT paper_transactions_value_check CHECK (total_value > 0);
                        END IF;
                    END $$;
                """)
                
                # Add run_status column if it doesn't exist
                cur.execute("""
                    ALTER TABLE paper_strategy_configs 
                    ADD COLUMN IF NOT EXISTS run_status VARCHAR(50) DEFAULT 'active'
                """)

                # Add last_error column if it doesn't exist
                cur.execute("""
                    ALTER TABLE paper_strategy_configs 
                    ADD COLUMN IF NOT EXISTS last_error TEXT DEFAULT NULL
                """)

                # Add warmup_progress column if it doesn't exist
                cur.execute("""
                    ALTER TABLE paper_strategy_configs 
                    ADD COLUMN IF NOT EXISTS warmup_progress JSONB DEFAULT NULL
                """)

                # Seed the strategy configs
                for config in SEED_CONFIGS:
                    params_json = json.dumps(config.get('indicator_params', {}))
                    kelly_weight = config.get('kelly_weight', 0.1)
                    cur.execute("""
                        INSERT INTO paper_strategy_configs (strategy_name, asset, timeframe, kelly_weight, indicator_params)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (strategy_name, asset, timeframe) 
                        DO NOTHING
                    """, (config['strategy'], config['asset'], config['timeframe'], kelly_weight, params_json))

                # 8. Backfill/Repair timeframe from strategy configs for existing positions
                if not v2_applied:
                    if run_timeframe_backfill:
                        cur.execute("SELECT COUNT(*) FROM paper_positions WHERE timeframe = '1m'")
                        if cur.fetchone()[0] > 0:
                            # 1. Update positions with unique matching timeframe config
                            cur.execute("""
                                UPDATE paper_positions p
                                SET timeframe = (
                                    SELECT MIN(c.timeframe)
                                    FROM paper_strategy_configs c
                                    WHERE c.asset = p.asset AND c.strategy_name = p.strategy_name
                                )
                                WHERE p.timeframe = '1m'
                                  AND (
                                      SELECT COUNT(DISTINCT c.timeframe)
                                      FROM paper_strategy_configs c
                                      WHERE c.asset = p.asset AND c.strategy_name = p.strategy_name
                                  ) = 1;
                            """)
                            
                            # 2. Quarantine ambiguous positions (multiple matching configs)
                            cur.execute("""
                                SELECT id, asset, strategy_name FROM paper_positions p
                                WHERE p.timeframe = '1m'
                                  AND (
                                      SELECT COUNT(DISTINCT c.timeframe)
                                      FROM paper_strategy_configs c
                                      WHERE c.asset = p.asset AND c.strategy_name = p.strategy_name
                                  ) > 1;
                            """)
                            ambiguous_positions = cur.fetchall()
                            if ambiguous_positions:
                                print(f"[DB Setup] WARNING: Found {len(ambiguous_positions)} ambiguous positions with multiple timeframe configs. Quarantining them to 'AMBIGUOUS'.")
                                cur.execute("""
                                    UPDATE paper_positions p
                                    SET timeframe = 'AMBIGUOUS'
                                    WHERE p.timeframe = '1m'
                                      AND (
                                          SELECT COUNT(DISTINCT c.timeframe)
                                          FROM paper_strategy_configs c
                                          WHERE c.asset = p.asset AND c.strategy_name = p.strategy_name
                                      ) > 1;
                                """)
                    
                    elif run_timeframe_repair:
                        cur.execute("""
                            INSERT INTO paper_position_timeframe_reviews (
                                position_id,
                                migration_version,
                                original_timeframe,
                                candidate_timeframes
                            )
                            SELECT
                                p.id,
                                2,
                                p.timeframe,
                                jsonb_agg(DISTINCT c.timeframe ORDER BY c.timeframe)
                            FROM paper_positions p
                            JOIN paper_strategy_configs c
                              ON c.asset = p.asset
                             AND c.strategy_name = p.strategy_name
                            GROUP BY p.id, p.timeframe
                            HAVING COUNT(DISTINCT c.timeframe) > 1
                            ON CONFLICT (position_id, migration_version) DO NOTHING;
                        """)
                        review_count = cur.rowcount
                        if review_count > 0:
                            print(f"[DB Setup] AUDIT: Recorded {review_count} multi-timeframe positions for manual review.")

                        cur.execute("""
                            UPDATE paper_positions p
                            SET timeframe = (
                                SELECT MIN(c.timeframe)
                                FROM paper_strategy_configs c
                                WHERE c.asset = p.asset AND c.strategy_name = p.strategy_name
                            )
                            WHERE (
                                SELECT COUNT(DISTINCT c.timeframe)
                                FROM paper_strategy_configs c
                                WHERE c.asset = p.asset AND c.strategy_name = p.strategy_name
                            ) = 1;
                        """)
                    
                    # Record Version 2 in schema_version
                    cur.execute("""
                        INSERT INTO schema_version (version, description)
                        VALUES (2, 'Timeframe column added to paper_positions, unique constraints updated, and historical positions backfilled/quarantined.')
                        ON CONFLICT (version) DO NOTHING;
                    """)

                # Check if Version 3 has been applied (opened_at column)
                cur.execute("SELECT EXISTS (SELECT 1 FROM schema_version WHERE version = 3)")
                v3_applied = cur.fetchone()[0]

                if not v3_applied:
                    cur.execute("ALTER TABLE paper_positions ADD COLUMN IF NOT EXISTS opened_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP")
                    # Backfill best-effort from last BUY transaction per (asset, strategy_name)
                    cur.execute("""
                        UPDATE paper_positions p SET opened_at = COALESCE(
                            (SELECT MAX(t.timestamp) FROM paper_transactions t
                             WHERE t.action = 'BUY' AND t.asset = p.asset AND t.strategy_name = p.strategy_name),
                            p.updated_at
                        ) WHERE p.opened_at IS NULL
                    """)
                    cur.execute("""
                        INSERT INTO schema_version (version, description)
                        VALUES (3, 'opened_at ajouté à paper_positions pour le Minimum Holding Period (MHP).')
                        ON CONFLICT (version) DO NOTHING;
                    """)

                # Reconcile allocated balance with actual paper_positions
                reconcile_allocated_balances(conn)

            conn.commit()
            print("[DB Setup] Paper trading database schema initialized and seeded.")
    except Exception as e:
        print(f"[DB Setup] Database setup failed: {e}")
        raise e

if __name__ == "__main__":
    init_db()
