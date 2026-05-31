import pandas as pd
from backtest_engine.strategies.pmax_explorer import vectorbt_prescan
from backtest_engine.optimizer import ParameterGridSpec
import numpy as np
import traceback
import logging

df = pd.DataFrame({
    "open": np.random.randn(2000),
    "high": np.random.randn(2000),
    "low": np.random.randn(2000),
    "close": np.random.randn(2000),
    "volume": np.random.randn(2000)
}, index=pd.date_range("2020-01-01", periods=2000, freq="1min"))

specs = [
    ParameterGridSpec(name="multiplier", kind="choice", values=[3.0]),
    ParameterGridSpec(name="length", kind="numeric", values=list(range(5, 51))),
]

import os
os.makedirs("/tmp/pmax_test", exist_ok=True)

# Patch the except block in pmax_explorer.py for debug
with open('/home/kidpixel/trading_automation_v2/backtest_engine/strategies/pmax_explorer.py', 'r') as f:
    content = f.read()
if "logger.warning(f\"Erreur Pre-Scan VectorBT: {e}." in content:
    content = content.replace("logger.warning(f\"Erreur Pre-Scan VectorBT: {e}.", "import traceback; logger.warning(f\"Erreur Pre-Scan VectorBT: {e}\\n{traceback.format_exc()}\"); logger.warning(f\"Erreur Pre-Scan VectorBT: {e}.")
    with open('/home/kidpixel/trading_automation_v2/backtest_engine/strategies/pmax_explorer.py', 'w') as f:
        f.write(content)

res = vectorbt_prescan(df, specs, 1, "/tmp/pmax_test")
print("Prescan returned", len(res), "specs")
