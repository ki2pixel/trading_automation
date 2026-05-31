import pandas as pd
import numpy as np
from backtest_engine.bayesian_optimizer import run_bayesian_optimization
from backtest_engine.optimizer import ParameterGridSpec

df = pd.DataFrame({
    "open": np.random.randn(2000),
    "high": np.random.randn(2000),
    "low": np.random.randn(2000),
    "close": np.random.randn(2000),
    "volume": np.random.randn(2000)
}, index=pd.date_range("2020-01-01", periods=2000, freq="1min"))

specs = [
    ParameterGridSpec(name="length", kind="numeric", values=[5, 10]),
    ParameterGridSpec(name="mav", kind="choice", values=["EMA", "SMA"]),
    ParameterGridSpec(name="source_col", kind="choice", values=["close"]),
    ParameterGridSpec(name="multiplier", kind="choice", values=[5.0]),
]

class FixedOverrides:
    pass

import os
os.makedirs("/tmp/pmax_opt_test", exist_ok=True)

import logging
logging.basicConfig(level=logging.INFO)

run_bayesian_optimization(
    df,
    "AMS.MC",
    specs,
    FixedOverrides(),
    "pmax_explorer",
    100000,
    "return_vs_buy_hold_pct_points",
    "max",
    10,  # trials
    15,
    50,
    False,
    {},
    "/tmp/pmax_opt_test",
    None,
    None,
    4,
    1,
    False
)

print("Optimizer finished successfully")
