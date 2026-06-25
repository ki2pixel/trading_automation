import os
import psycopg2
import json

DATABASE_URL = os.getenv("DATABASE_URL")

SEED_CONFIGS = [
    {"strategy": "cybernetic_hilbert", "asset": "ZEAL.CO", "timeframe": "45m", "kelly_weight": 0.0079},
    {"strategy": "momentum_based_zigzag", "asset": "NVO", "timeframe": "45m", "kelly_weight": 0.0073},
    {"strategy": "3commas_bot", "asset": "EVD.DE", "timeframe": "30m", "kelly_weight": 0.0132},
    {"strategy": "3commas_bot", "asset": "GMAB", "timeframe": "60m", "kelly_weight": 0.0123},
    {"strategy": "3commas_bot", "asset": "FPE.DE", "timeframe": "20m", "kelly_weight": 0.0093},
    {"strategy": "adaptive_volatility_trend", "asset": "dpwdeeur", "timeframe": "45m", "kelly_weight": 0.0322},
    {"strategy": "3commas_bot", "asset": "teniteur", "timeframe": "30m", "kelly_weight": 0.0155},
    {"strategy": "adaptive_volatility_trend", "asset": "akzanleur", "timeframe": "30m", "kelly_weight": 0.0322},
    {"strategy": "momentum_based_zigzag", "asset": "daideeur", "timeframe": "15m", "kelly_weight": 0.0066},
    {"strategy": "momentum_based_zigzag", "asset": "SAP", "timeframe": "30m", "kelly_weight": 0.0154},
    {"strategy": "hmm_regime_filter", "asset": "mrkdeeur", "timeframe": "45m", "kelly_weight": 0.0057},
    {"strategy": "momentum_based_zigzag", "asset": "AMS.MC", "timeframe": "10m", "kelly_weight": 0.0077},
    {"strategy": "momentum_based_zigzag", "asset": "vnadeeur", "timeframe": "10m", "kelly_weight": 0.0056},
    {"strategy": "hmm_regime_filter", "asset": "acfreur", "timeframe": "15m", "kelly_weight": 0.0060},
    {"strategy": "hmm_regime_filter", "asset": "lxsdeeur", "timeframe": "30m", "kelly_weight": 0.0048},
    {"strategy": "momentum_based_zigzag", "asset": "randnleur", "timeframe": "10m", "kelly_weight": 0.0116},
    {"strategy": "hmm_regime_filter", "asset": "rifreur", "timeframe": "10m", "kelly_weight": 0.0052},
    {"strategy": "hmm_regime_filter", "asset": "abibeeur", "timeframe": "15m", "kelly_weight": 0.0048},
    {"strategy": "momentum_based_zigzag", "asset": "belgbeeur", "timeframe": "10m", "kelly_weight": 0.0049},
    {"strategy": "momentum_based_zigzag", "asset": "cafreur", "timeframe": "15m", "kelly_weight": 0.0039},
    {"strategy": "trend_type", "asset": "NVS", "timeframe": "15m", "kelly_weight": 0.0093}
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
                        UNIQUE(strategy_name, asset, timeframe)
                    )
                """)

                # Seed the strategy configs
                for config in SEED_CONFIGS:
                    cur.execute("""
                        INSERT INTO paper_strategy_configs (strategy_name, asset, timeframe, kelly_weight)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (strategy_name, asset, timeframe) DO NOTHING
                    """, (config['strategy'], config['asset'], config['timeframe'], config['kelly_weight']))

            conn.commit()
            print("[DB Setup] Paper trading database schema initialized and seeded.")
    except Exception as e:
        print(f"[DB Setup] Database setup failed: {e}")

if __name__ == "__main__":
    init_db()
