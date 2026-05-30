import sys
import numpy as np
import pandas as pd
from pathlib import Path
import multiprocessing
from backtest_engine.bayesian_optimizer import share_dataframe, rebuild_dataframe, _init_worker_bayesian, _evaluate_worker_bayesian
from backtest_engine.strategies.hma_crossover import HMAConfigOverrides

def worker_run(shm_metadata):
    try:
        print("Worker starting in child process...")
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
        print("Worker initialized.")
        res = _evaluate_worker_bayesian((1, {"fast_len": 5, "slow_len": 15}))
        print("Worker evaluation result:", res)
    except Exception as e:
        import traceback
        print("Worker failed with exception:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    multiprocessing.set_start_method("spawn", force=True)
    
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

    try:
        print("Spawning child process...")
        p = multiprocessing.Process(target=worker_run, args=(shm_metadata,))
        p.start()
        p.join()
        print("Child process exit code:", p.exitcode)
    finally:
        print("Cleaning up shm...")
        for obj in shm_objects:
            obj.unlink()
