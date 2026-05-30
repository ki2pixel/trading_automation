import sys
import numpy as np
import pandas as pd
from pathlib import Path
from backtest_engine.bayesian_optimizer import run_bayesian_optimization
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

print("Running bayesian optimization...")
try:
    summary = run_bayesian_optimization(
        data=data,
        symbol="TEST",
        parameter_specs=[
            ParameterGridSpec("fast_len", "numeric", (5, 6)),
            ParameterGridSpec("slow_len", "numeric", (15, 16)),
        ],
        fixed_overrides=HMAConfigOverrides(
            confirm_on_close=True,
            initial_capital_bucket=1000.0,
            max_capital_bucket=1000.0,
        ),
        output_root=Path("/tmp/hp_opt_test"),
        n_trials=5,
        min_closed_trades=0,
        workers=2,
        write_best_run=False,
        enable_convergence_stop=False,
        seed=42,
    )
    print("Success! iterations_completed =", summary.iterations_completed)
except Exception as e:
    import traceback
    print("Optimization failed with exception:")
    traceback.print_exc()
