import time
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import math

repo = Path('/home/kidpixel/trading_automation_v2')
if str(repo) not in sys.path:
    sys.path.insert(0, str(repo))

# 1. Test fast loading
from backtest_engine.data import load_canonical_market_data

t0 = time.time()
df = load_canonical_market_data('NVS', repo, start_date='2021-06-16', end_date='2023-06-16', timeframe_minutes=1)
print("Standard loading time:", time.time() - t0)

# Vectorized _is_valid_ohlc
def check_vectorized(df):
    o = df["open"]
    h = df["high"]
    l = df["low"]
    c = df["close"]
    has_nan = o.isna() | h.isna() | l.isna() | c.isna()
    min_oc = np.minimum(o, c)
    max_oc = np.maximum(o, c)
    valid_ohlc = (~has_nan) & (l <= min_oc) & (h >= max_oc) & (l <= h)
    return valid_ohlc

t0 = time.time()
valid_fast = check_vectorized(df)
print("Vectorized validation time:", time.time() - t0)

# Standard validation check
from backtest_engine.data import _is_valid_ohlc
t0 = time.time()
valid_slow = df[["open", "high", "low", "close"]].apply(lambda row: _is_valid_ohlc(row.to_dict()), axis=1)
print("Standard apply(axis=1) validation time:", time.time() - t0)

print("Are the validation results identical?", (valid_fast == valid_slow).all())

# 2. Test fast bands calculation
lookback_days = 17
multiplier_enter = 0.25
multiplier_exit = 0.08

from backtest_engine.strategies.noise_boundary_intraday import compute_noise_boundary

t0 = time.time()
bands_slow = compute_noise_boundary(df, lookback_days, multiplier_enter, multiplier_exit)
print("Standard bands calculation time:", time.time() - t0)

def compute_noise_boundary_fast(bars, lookback_days, multiplier_enter, multiplier_exit):
    daily_close = bars["close"].resample("D").last().dropna()
    daily_returns = daily_close.pct_change()
    daily_vol = daily_returns.rolling(window=lookback_days).std()
    daily_vol_for_today = daily_vol.shift(1)
    
    # Fast vectorized reindexing!
    normalized_index = bars.index.normalize()
    mapped_vol = daily_vol_for_today.reindex(normalized_index).values
    
    # Fast grouping!
    daily_open = bars.groupby(normalized_index)["open"].transform("first")
    
    results = pd.DataFrame(index=bars.index)
    results["daily_volatility"] = mapped_vol
    results["daily_open"] = daily_open
    results["upper_enter"] = daily_open * (1 + multiplier_enter * mapped_vol)
    results["lower_enter"] = daily_open * (1 - multiplier_enter * mapped_vol)
    results["upper_exit"] = daily_open * (1 + multiplier_exit * mapped_vol)
    results["lower_exit"] = daily_open * (1 - multiplier_exit * mapped_vol)
    return results

t0 = time.time()
bands_fast = compute_noise_boundary_fast(df, lookback_days, multiplier_enter, multiplier_exit)
print("Fast bands calculation time:", time.time() - t0)

print("Are daily_volatility columns close?", np.allclose(bands_slow["daily_volatility"].fillna(0), bands_fast["daily_volatility"].fillna(0)))
print("Are daily_open columns close?", np.allclose(bands_slow["daily_open"], bands_fast["daily_open"]))
print("Are upper_enter close?", np.allclose(bands_slow["upper_enter"].fillna(0), bands_fast["upper_enter"].fillna(0)))
print("Are lower_enter close?", np.allclose(bands_slow["lower_enter"].fillna(0), bands_fast["lower_enter"].fillna(0)))
