import numpy as np
import time
from backtest_engine.strategies.pmax_explorer import _load_strategy_module

strategy = _load_strategy_module()

src = np.random.randn(150000)
start = time.time()
strategy.pine_tsf(src, 10)
end = time.time()
print(f"Time for TSF: {end - start:.2f} seconds")
