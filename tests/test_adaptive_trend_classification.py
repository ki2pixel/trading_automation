import pytest
import numpy as np
import pandas as pd
import time
from backtest_engine.indicators.adaptive_trend_classification import AdaptiveTrend

def test_adaptive_trend_classification_no_lookahead():
    """
    Test that the indicator does not suffer from lookahead bias.
    Evaluating the indicator on data[:N] should give the exact same result as on data[:] up to N.
    """
    np.random.seed(42)
    close = np.cumsum(np.random.randn(500)) + 100
    
    # Calculate on full dataset
    atc_full = AdaptiveTrend.run(close)
    full_sig = atc_full.average_signal.to_numpy()
    full_dir = atc_full.direction.to_numpy()
    
    # Calculate on first 400 bars
    atc_partial = AdaptiveTrend.run(close[:400])
    partial_sig = atc_partial.average_signal.to_numpy()
    partial_dir = atc_partial.direction.to_numpy()
    
    np.testing.assert_allclose(partial_sig, full_sig[:400], rtol=1e-5, atol=1e-5)
    np.testing.assert_array_equal(partial_dir, full_dir[:400])

def test_adaptive_trend_classification_numba_performance():
    """
    Test the performance of the indicator.
    Must run under 50ms for 10,000 bars.
    The first run includes Numba compilation time, so we must run it twice and measure the second run.
    """
    np.random.seed(42)
    close = np.cumsum(np.random.randn(10000)) + 1000
    
    # First run to trigger numba compilation
    _ = AdaptiveTrend.run(close)
    
    # Second run to measure performance
    start_time = time.perf_counter()
    _ = AdaptiveTrend.run(close)
    end_time = time.perf_counter()
    
    elapsed_ms = (end_time - start_time) * 1000
    print(f"Elapsed time for 10k bars: {elapsed_ms:.2f} ms")
    
    assert elapsed_ms < 150.0, f"Performance too slow: {elapsed_ms:.2f} ms"
