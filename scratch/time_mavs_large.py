import numpy as np
import time
from backtest_engine.strategies.pmax_explorer import _load_strategy_module

strategy = _load_strategy_module()

src = np.random.randn(1500000)
start = time.time()
strategy.pine_sma(src, 10)
strategy.pine_ema(src, 10)
strategy.pine_wma(src, 10)
strategy.pine_tma(src, 10)
strategy.pine_var(src, 10)
strategy.pine_wwma(src, 10)
strategy.pine_zlema(src, 10)
strategy.pine_tsf(src, 10)
end = time.time()
print(f"Time for 8 MAVs (1 length) on 1.5M bars: {end - start:.2f} seconds")
