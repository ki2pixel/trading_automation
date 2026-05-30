import numpy as np
import pandas as pd
import time

def wma_pandas(series: pd.Series, length: int) -> pd.Series:
    weights = np.arange(1, length + 1, dtype=float)
    weight_sum = weights.sum()
    return series.rolling(length, min_periods=length).apply(
        lambda values: float(np.dot(values, weights) / weight_sum),
        raw=True,
    )

def wma_fast(series: pd.Series, length: int) -> pd.Series:
    weights = np.arange(1, length + 1, dtype=float)
    weight_sum = weights.sum()
    
    res = np.convolve(series.to_numpy(), weights[::-1], mode='full')[:len(series)] / weight_sum
    res[:length-1] = np.nan
    return pd.Series(res, index=series.index)

data = np.random.rand(1000000)
s = pd.Series(data)

t0 = time.time()
res_pd = wma_pandas(s, 50)
t1 = time.time()

t2 = time.time()
res_fast = wma_fast(s, 50)
t3 = time.time()

print(f"Pandas WMA took {t1-t0:.4f}s")
print(f"Fast WMA took {t3-t2:.4f}s")
print("Are they close?", np.allclose(res_pd.dropna(), res_fast.dropna()))
