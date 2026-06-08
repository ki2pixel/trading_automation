import pandas as pd
import numpy as np

# Create dummy data
n = 100
df = pd.DataFrame({
    'open': np.random.uniform(100, 110, n),
    'high': np.random.uniform(110, 120, n),
    'low': np.random.uniform(90, 100, n),
    'close': np.random.uniform(100, 110, n),
    'volume': np.random.uniform(1000, 5000, n)
})
df.index = pd.date_range("2024-01-01", periods=n, freq="5min")

from pine_scripts_convert_to_python.strategy.smart_trader_ep1 import (
    SmartTraderEP1Config,
    run_smart_trader_ep1_strategy,
    add_smart_trader_ep1_features
)
from backtest_engine.strategies.smart_trader_ep1 import run_smart_trader_ep1

config = SmartTraderEP1Config(universal_len=20)
print("Running standalone...")
df_feat = add_smart_trader_ep1_features(df.copy(), config)
state, trades = run_smart_trader_ep1_strategy(df_feat.copy(), config)
print(f"Features computed. Long entries: {df_feat['long_entry'].sum()}, Short entries: {df_feat['short_entry'].sum()}")
print(f"Trades standalone: {len(trades)}")

print("Running broker wrapper...")
res = run_smart_trader_ep1(df.copy(), "BTCUSDT", initial_capital=10000.0)
print(f"Trades wrapper: {len(res.trades)}")
print("DONE")
