import os
import psycopg2
import json

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
    }
]

def init_db():
    if not DATABASE_URL:
        print("[DB Setup] DATABASE_URL not set. Skipping setup.")
        return

    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                # 1. Create Portfolio Balance table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS paper_portfolio_balance (
                        id SERIAL PRIMARY KEY,
                        cash_balance NUMERIC NOT NULL DEFAULT 100000,
                        allocated_balance NUMERIC NOT NULL DEFAULT 0,
                        total_nav NUMERIC NOT NULL DEFAULT 100000,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert default balance if empty
                cur.execute("SELECT count(*) FROM paper_portfolio_balance")
                if cur.fetchone()[0] == 0:
                    cur.execute("INSERT INTO paper_portfolio_balance (cash_balance, total_nav) VALUES (100000, 100000)")

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
                
                # 5. Create Evaluations table
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
                    cur.execute("""
                        INSERT INTO paper_strategy_configs (strategy_name, asset, timeframe, kelly_weight, indicator_params)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (strategy_name, asset, timeframe) 
                        DO UPDATE SET kelly_weight = EXCLUDED.kelly_weight, indicator_params = EXCLUDED.indicator_params
                    """, (config['strategy'], config['asset'], config['timeframe'], config['kelly_weight'], params_json))

            conn.commit()
            print("[DB Setup] Paper trading database schema initialized and seeded.")
    except Exception as e:
        print(f"[DB Setup] Database setup failed: {e}")

if __name__ == "__main__":
    init_db()
