import os
import psycopg2
import json
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
                        IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'trading212_prices') AND 
                           NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'live_prices') THEN
                            ALTER TABLE trading212_prices RENAME TO live_prices;
                        END IF;
                        
                        IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'trading212_candles_1m') AND 
                           NOT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'live_candles_1m') THEN
                            ALTER TABLE trading212_candles_1m RENAME TO live_candles_1m;
                        END IF;
                    END $$;
                """)

                # 0.1 Migration: Migrate USDT assets/tickers to USDC for Bybit safely (idempotent)
                cur.execute("""
                    DO $$
                    BEGIN
                        -- live_prices migration
                        IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'live_prices') THEN
                            DELETE FROM live_prices 
                            WHERE ticker LIKE '%usdt' 
                              AND REPLACE(ticker, 'usdt', 'usdc') IN (SELECT ticker FROM live_prices);
                            
                            UPDATE live_prices SET ticker = REPLACE(ticker, 'usdt', 'usdc') 
                            WHERE ticker LIKE '%usdt' AND source = 'bybit';
                        END IF;
                        
                        -- live_candles_1m migration
                        IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'live_candles_1m') THEN
                            DELETE FROM live_candles_1m c_usdt
                            WHERE c_usdt.ticker LIKE '%usdt'
                              AND EXISTS (
                                  SELECT 1 FROM live_candles_1m c_usdc
                                  WHERE c_usdc.ticker = REPLACE(c_usdt.ticker, 'usdt', 'usdc')
                                    AND c_usdc.timestamp_minute = c_usdt.timestamp_minute
                              );
                            
                            UPDATE live_candles_1m SET ticker = REPLACE(ticker, 'usdt', 'usdc') 
                            WHERE ticker LIKE '%usdt';
                        END IF;
                        
                        -- paper_strategy_configs migration
                        IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'paper_strategy_configs') THEN
                            DELETE FROM paper_strategy_configs cfg_usdt
                            WHERE cfg_usdt.asset LIKE '%usdt'
                              AND EXISTS (
                                  SELECT 1 FROM paper_strategy_configs cfg_usdc
                                  WHERE cfg_usdc.strategy_name = cfg_usdt.strategy_name
                                    AND cfg_usdc.asset = REPLACE(cfg_usdt.asset, 'usdt', 'usdc')
                                    AND cfg_usdc.timeframe = cfg_usdt.timeframe
                              );
                            
                            UPDATE paper_strategy_configs SET asset = REPLACE(asset, 'usdt', 'usdc') 
                            WHERE asset LIKE '%usdt';
                        END IF;
                    END $$;
                """)

                # 1. Create Portfolio Balance table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS paper_portfolio_balance (
                        id SERIAL PRIMARY KEY,
                        source VARCHAR(50) NOT NULL DEFAULT 'trading212' UNIQUE,
                        cash_balance NUMERIC NOT NULL DEFAULT 100000,
                        allocated_balance NUMERIC NOT NULL DEFAULT 0,
                        total_nav NUMERIC NOT NULL DEFAULT 100000,
                        secured_balance NUMERIC NOT NULL DEFAULT 0,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Migrate paper_portfolio_balance to add source and secured_balance if they don't exist
                cur.execute("""
                    ALTER TABLE paper_portfolio_balance ADD COLUMN IF NOT EXISTS source VARCHAR(50) NOT NULL DEFAULT 'trading212';
                    ALTER TABLE paper_portfolio_balance ADD COLUMN IF NOT EXISTS secured_balance NUMERIC NOT NULL DEFAULT 0;
                    -- Ensure UNIQUE constraint on source column
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.table_constraints 
                            WHERE table_name='paper_portfolio_balance' AND constraint_type='UNIQUE'
                        ) THEN
                            ALTER TABLE paper_portfolio_balance ADD CONSTRAINT paper_portfolio_balance_source_key UNIQUE (source);
                        END IF;
                    END $$;
                """)

                # Seed the double portfolio balances
                cur.execute("""
                    INSERT INTO paper_portfolio_balance (source, cash_balance, total_nav)
                    VALUES ('trading212', 100000, 100000)
                    ON CONFLICT (source) DO NOTHING;
                """)
                cur.execute("""
                    INSERT INTO paper_portfolio_balance (source, cash_balance, total_nav)
                    VALUES ('bybit', 10000, 10000)
                    ON CONFLICT (source) DO NOTHING;
                """)

                # 2. Create Positions table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS paper_positions (
                        id SERIAL PRIMARY KEY,
                        asset VARCHAR(50) NOT NULL,
                        strategy_name VARCHAR(100) NOT NULL,
                        qty NUMERIC NOT NULL,
                        entry_price NUMERIC NOT NULL,
                        current_price NUMERIC NOT NULL,
                        pnl NUMERIC NOT NULL DEFAULT 0,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # 3. Create Transactions table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS paper_transactions (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        asset VARCHAR(50) NOT NULL,
                        strategy_name VARCHAR(100) NOT NULL,
                        action VARCHAR(20) NOT NULL,
                        qty NUMERIC NOT NULL,
                        price NUMERIC NOT NULL,
                        total_value NUMERIC NOT NULL
                    )
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

                # 6. Create Evaluations table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS paper_evaluations (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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

                # Seed the strategy configs
                for config in SEED_CONFIGS:
                    params_json = json.dumps(config.get('indicator_params', {}))
                    # Uniform Kelly weight (e.g. 0.1) for stocks, but keep original for crypto
                    is_crypto = is_crypto_asset(config['asset'])
                    kelly_weight = config.get('kelly_weight', 0.1) if is_crypto else 0.1
                    cur.execute("""
                        INSERT INTO paper_strategy_configs (strategy_name, asset, timeframe, kelly_weight, indicator_params)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (strategy_name, asset, timeframe) 
                        DO NOTHING
                    """, (config['strategy'], config['asset'], config['timeframe'], kelly_weight, params_json))

            conn.commit()
            print("[DB Setup] Paper trading database schema initialized and seeded.")
    except Exception as e:
        print(f"[DB Setup] Database setup failed: {e}")

if __name__ == "__main__":
    init_db()
