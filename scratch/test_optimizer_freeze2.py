import pandas as pd
import numpy as np
from pathlib import Path
from backtest_engine.bayesian_optimizer import run_bayesian_optimization
from backtest_engine.optimizer import ParameterGridSpec
from backtest_engine.strategies.pmax_explorer import PMaxExplorerConfigOverrides

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

import os
os.makedirs("/tmp/pmax_opt_test", exist_ok=True)

import logging
logging.basicConfig(level=logging.INFO)

run_bayesian_optimization(
    data=df,
    symbol="AMS.MC",
    parameter_specs=specs,
    fixed_overrides=PMaxExplorerConfigOverrides(),
    strategy="pmax_explorer",
    output_root=Path("/tmp/pmax_opt_test"),
    n_trials=10,
    use_vectorbt_prescan=True,
    workers=1
)

print("Optimizer finished successfully")
