import numpy as np
import pandas as pd
import pytest
import time
import vectorbt as vbt
from backtest_engine.indicators.momentum_based_zigzag import MomentumBasedZigZagIndicator

def test_no_lookahead_bias():
    np.random.seed(42)
    n = 1000
    close = np.random.lognormal(0, 0.01, n).cumprod() * 100
    high = close * 1.01
    low = close * 0.99
    
    # Run full
    ind_full = MomentumBasedZigZagIndicator.run(high, low, close)
    
    # Run partial (first 500)
    ind_partial = MomentumBasedZigZagIndicator.run(high[:500], low[:500], close[:500])
    
    # Compare up to 500
    np.testing.assert_array_equal(ind_full.bullish_signal.values[:500], ind_partial.bullish_signal.values)
    np.testing.assert_array_equal(ind_full.bearish_signal.values[:500], ind_partial.bearish_signal.values)
    np.testing.assert_array_equal(
        np.nan_to_num(ind_full.zigzag.values[:500]), 
        np.nan_to_num(ind_partial.zigzag.values)
    )

def test_performance_numba():
    np.random.seed(42)
    n = 10000
    close = np.random.lognormal(0, 0.01, n).cumprod() * 100
    high = close * 1.01
    low = close * 0.99
    
    # Compilation run (warmup)
    _ = MomentumBasedZigZagIndicator.run(high[:100], low[:100], close[:100])
    
    start_time = time.perf_counter()
    _ = MomentumBasedZigZagIndicator.run(high, low, close)
    end_time = time.perf_counter()
    
    execution_time_ms = (end_time - start_time) * 1000
    print(f"\nExecution time for {n} bars: {execution_time_ms:.2f} ms")
    assert execution_time_ms < 150.0, f"Execution too slow: {execution_time_ms:.2f} ms"

def test_multi_column():
    np.random.seed(42)
    n = 100
    close1 = np.random.lognormal(0, 0.01, n).cumprod() * 100
    close2 = np.random.lognormal(0, 0.01, n).cumprod() * 50
    df_close = pd.DataFrame({'AAPL': close1, 'MSFT': close2})
    df_high = df_close * 1.01
    df_low = df_close * 0.99
    
    ind = MomentumBasedZigZagIndicator.run(df_high, df_low, df_close)
    
    assert ind.bullish_signal.shape == (100, 2)
    assert ind.bearish_signal.shape == (100, 2)
    assert ind.zigzag.shape == (100, 2)
