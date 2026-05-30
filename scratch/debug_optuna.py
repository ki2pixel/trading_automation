import sys
import numpy as np
import pandas as pd
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from backtest_engine.bayesian_optimizer import share_dataframe, rebuild_dataframe, _init_worker_bayesian, _evaluate_worker_bayesian
from backtest_engine.strategies.hma_crossover import HMAConfigOverrides

if __name__ == "__main__":
    import multiprocessing
    # Force fork start method
    multiprocessing.set_start_method("fork", force=True)

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
        print("Starting ProcessPoolExecutor...")
        executor = ProcessPoolExecutor(
            max_workers=2,
            initializer=_init_worker_bayesian,
            initargs=(shm_metadata, "TEST", HMAConfigOverrides(), 1000.0, "hma_crossover", "sharpe_ratio", 0, 5, None, 1, None, None, None),
        )
        
        print("Submitting trial...")
        future = executor.submit(_evaluate_worker_bayesian, (1, {"fast_len": 5, "slow_len": 15}))
        print("Waiting for result...")
        res = future.result()
        print("Result:", res)
        
        executor.shutdown()
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        print("Cleaning up shm...")
        for obj in shm_objects:
            obj.unlink()
