import pandas as pd
from backtest_engine.strategies.pmax_explorer import vectorbt_prescan
from backtest_engine.optimizer import ParameterGridSpec
import numpy as np
import traceback

df = pd.DataFrame({
    "open": np.random.randn(200),
    "high": np.random.randn(200),
    "low": np.random.randn(200),
    "close": np.random.randn(200),
    "volume": np.random.randn(200)
}, index=pd.date_range("2020-01-01", periods=200, freq="1min"))

specs = [
    ParameterGridSpec(name="multiplier", kind="choice", values=[3.0]),
    ParameterGridSpec(name="length", kind="numeric", values=[10, 11]),
]

import os
os.makedirs("/tmp/pmax_test", exist_ok=True)

try:
    res = vectorbt_prescan(df, specs, 1, "/tmp/pmax_test")
    print("Success")
except Exception as e:
    traceback.print_exc()

