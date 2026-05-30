import pandas as pd
import numpy as np
import time

# Create a dummy DataFrame with 1,000,000 bars
N = 1000000
data = pd.DataFrame({
    'close': np.random.randn(N).cumsum() + 100.0
})

lookback = 20

# Original implementation benchmark
start_time = time.time()
for i in range(1000):
    # Slice dataframe
    slice_df = data.iloc[:N - 1000 + i]
    # pct_change on slice
    returns = slice_df['close'].pct_change().dropna()
    realized_volatility = returns.tail(lookback).std()
original_time = time.time() - start_time
print(f"Original implementation time for 1000 iterations: {original_time:.4f} seconds")

# Optimized implementation benchmark
start_time = time.time()
for i in range(1000):
    # Slice only the tail of the dataframe
    slice_df = data.iloc[:N - 1000 + i]
    tail_bars = slice_df['close'].iloc[-(lookback + 2):]
    returns = tail_bars.pct_change().dropna()
    realized_volatility = returns.tail(lookback).std()
optimized_time = time.time() - start_time
print(f"Optimized implementation time for 1000 iterations: {optimized_time:.4f} seconds")
print(f"Speedup: {original_time / optimized_time:.2f}x")
