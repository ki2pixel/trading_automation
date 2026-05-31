import numpy as np
import time
from numba import njit

@njit(cache=True)
def pine_sma(src: np.ndarray, length: int) -> np.ndarray:
    n = len(src)
    res = np.full(n, np.nan)
    for i in range(length - 1, n):
        s = 0.0
        for j in range(length):
            s += src[i - j]
        res[i] = s / length
    return res

src = np.random.randn(1500000)
# warmup
pine_sma(src, 10)

start = time.time()
pine_sma(src, 10)
end = time.time()
print(f"Time for numba SMA on 1.5M: {end - start:.5f} seconds")
