import numpy as np
import pandas as pd
from pathlib import Path
from backtest_engine.bayesian_optimizer import share_dataframe, rebuild_dataframe, _init_worker_bayesian, _evaluate_worker_bayesian
from backtest_engine.optimizer import ParameterGridSpec
from backtest_engine.strategies.hma_crossover import HMAConfigOverrides

# Create dummy dataframe
index = pd.date_range("2024-01-01 09:30:00", periods=50, freq="5min")
data = pd.DataFrame(
    {
        "open": np.linspace(100.0, 105.0, 50),
        "high": np.linspace(100.5, 105.5, 50),
        "low": np.linspace(99.5, 104.5, 50),
        "close": np.linspace(100.0, 105.0, 50),
        "volume": np.ones(50) * 1000,
    },
    index=index,
)

print("Sharing dataframe...")
shm_metadata, shm_objects = share_dataframe(data)
print("Metadata:", shm_metadata)

try:
    print("Rebuilding dataframe in same process...")
    rebuilt = rebuild_dataframe(shm_metadata)
    print("Rebuilt head:\n", rebuilt.head())
    
    print("Initializing worker context...")
    _init_worker_bayesian(
        shm_metadata=shm_metadata,
        symbol="TEST",
        fixed_overrides=HMAConfigOverrides(),
        initial_capital=1000.0,
        strategy="hma_crossover",
        score_metric="sharpe_ratio",
        min_closed_trades=0,
        timeframe_minutes=5,
    )
    print("Worker context initialized successfully.")
    
    print("Evaluating worker task...")
    res = _evaluate_worker_bayesian((1, {"fast_len": 5, "slow_len": 15}))
    print("Result:", res)
finally:
    print("Cleaning up shm...")
    for obj in shm_objects:
        obj.unlink()
