import numpy as np
import pandas as pd
from numba import njit
import vectorbt as vbt
import threading

_MA_CACHE = {}
_MA_CACHE_LOCK = threading.Lock()

@njit(cache=True)
def calc_ema(arr, length):
    out = np.full_like(arr, np.nan)
    if length > len(arr): return out
    alpha = 2.0 / (length + 1)
    out[length-1] = np.mean(arr[:length])
    for i in range(length, len(arr)):
        out[i] = arr[i] * alpha + out[i-1] * (1 - alpha)
    return out

@njit(cache=True)
def calc_sma(arr, length):
    out = np.full_like(arr, np.nan)
    if length > len(arr): return out
    sum_val = np.sum(arr[:length])
    out[length-1] = sum_val / length
    for i in range(length, len(arr)):
        sum_val = sum_val + arr[i] - arr[i-length]
        out[i] = sum_val / length
    return out

@njit(cache=True)
def calc_wma(arr, length):
    out = np.full_like(arr, np.nan)
    if length > len(arr): return out
    norm = length * (length + 1) / 2.0
    for i in range(length-1, len(arr)):
        sum_val = 0.0
        for j in range(length):
            sum_val += arr[i - j] * (length - j)
        out[i] = sum_val / norm
    return out

@njit(cache=True)
def calc_dema(arr, length):
    ema1 = calc_ema(arr, length)
    out = np.full_like(arr, np.nan)
    if length * 2 - 1 > len(arr): return out
    alpha = 2.0 / (length + 1)
    ema2 = np.full_like(arr, np.nan)
    start_idx = length - 1
    ema2[start_idx + length - 1] = np.mean(ema1[start_idx : start_idx + length])
    for i in range(start_idx + length, len(arr)):
        ema2[i] = ema1[i] * alpha + ema2[i-1] * (1 - alpha)
    for i in range(len(arr)):
        if not np.isnan(ema2[i]):
            out[i] = 2 * ema1[i] - ema2[i]
    return out

@njit(cache=True)
def calc_lsma(arr, length):
    out = np.full_like(arr, np.nan)
    if length > len(arr): return out
    sum_x = length * (length - 1) / 2.0
    sum_x2 = length * (length - 1) * (2 * length - 1) / 6.0
    divisor = length * sum_x2 - sum_x * sum_x
    for i in range(length-1, len(arr)):
        sum_y = 0.0
        sum_xy = 0.0
        for j in range(length):
            y = arr[i - length + 1 + j]
            sum_y += y
            sum_xy += j * y
        slope = (length * sum_xy - sum_x * sum_y) / divisor
        intercept = (sum_y - slope * sum_x) / length
        out[i] = intercept + slope * (length - 1)
    return out

@njit(cache=True)
def calc_kama(arr, length, fast_len=2, slow_len=30):
    out = np.full_like(arr, np.nan)
    if length > len(arr): return out
    fast_alpha = 2.0 / (fast_len + 1)
    slow_alpha = 2.0 / (slow_len + 1)
    out[length-1] = arr[length-1]
    for i in range(length, len(arr)):
        change = abs(arr[i] - arr[i - length])
        volatility = 0.0
        for j in range(length):
            volatility += abs(arr[i - j] - arr[i - j - 1])
        er = change / volatility if volatility != 0 else 0.0
        sc = (er * (fast_alpha - slow_alpha) + slow_alpha) ** 2
        out[i] = out[i-1] + sc * (arr[i] - out[i-1])
    return out

@njit(cache=True)
def _adaptive_trend_nb(close, mas_3d, La, De, cutout, Long_threshold, Short_threshold, weights):
    rows, cols = close.shape
    direction = np.zeros((rows, cols), dtype=np.int64)
    average_signal = np.zeros((rows, cols), dtype=np.float64)
    
    for c in range(cols):
        sig = np.zeros(54, dtype=np.int64)
        equity = np.ones(54, dtype=np.float64)
        
        equity_type = np.zeros(6, dtype=np.float64)
        for j in range(6):
            equity_type[j] = weights[j]
            
        ma_signal_prev = np.zeros(6, dtype=np.float64)
        dir_val = 0
        
        for r in range(1, rows):
            c_r = close[r, c]
            c_prev = close[r-1, c]
            
            R_r = (c_r - c_prev) / c_prev if c_prev != 0 else 0.0
            e_La = np.exp(La * (r - cutout)) if r >= cutout else 1.0
            r_adjust = R_r * e_La
            d = 1.0 - De
            
            sum_equity_type = 0.0
            sum_weighted_cut = 0.0
            
            for j in range(6):
                a_j = 0.0
                if ma_signal_prev[j] > 0:
                    a_j = r_adjust
                elif ma_signal_prev[j] < 0:
                    a_j = -r_adjust
                
                equity_type[j] = max(0.25, equity_type[j] * d * (1.0 + a_j))
                
                sum_sig_eq = 0.0
                sum_eq = 0.0
                
                for i in range(9):
                    k = 9 * j + i
                    ma_val_r = mas_3d[r, c, k]
                    
                    sig_prev = sig[k]
                    a = 0.0
                    if sig_prev > 0:
                        a = r_adjust
                    elif sig_prev < 0:
                        a = -r_adjust
                        
                    equity[k] = max(0.25, equity[k] * d * (1.0 + a))
                    
                    if not np.isnan(ma_val_r):
                        if c_r > ma_val_r:
                            sig[k] = 1
                        elif c_r < ma_val_r:
                            sig[k] = -1
                            
                    sum_sig_eq += sig[k] * equity[k]
                    sum_eq += equity[k]
                
                ma_sig = 0.0
                if sum_eq > 0:
                    ma_sig = np.round(sum_sig_eq / sum_eq, 2)
                
                ma_signal_prev[j] = ma_sig
                
                cut_val = 0.0
                if ma_sig > 0.49:
                    cut_val = 1.0
                elif ma_sig < -0.49:
                    cut_val = -1.0
                
                sum_weighted_cut += cut_val * equity_type[j]
                sum_equity_type += equity_type[j]
                
            avg_sig = 0.0
            if sum_equity_type > 0:
                avg_sig = sum_weighted_cut / sum_equity_type
                
            average_signal[r, c] = avg_sig
            
            if avg_sig > Long_threshold:
                dir_val = 1
            elif avg_sig < Short_threshold:
                dir_val = -1
                
            direction[r, c] = dir_val

    return average_signal, direction

def apply_adaptive_trend(close, La, De, cutout, robustness, Long_threshold, Short_threshold,
                        ema_len, ema_w, hull_len, hma_w, wma_len, wma_w,
                        dema_len, dema_w, lsma_len, lsma_w, kama_len, kama_w):
    
    close_np = np.asarray(close)
    if close_np.ndim == 1:
        close_np = close_np.reshape(-1, 1)
        
    rows, cols = close_np.shape
    mas_3d = np.full((rows, cols, 54), np.nan, dtype=np.float64)
    
    rob = robustness.item() if isinstance(robustness, np.ndarray) else robustness
    
    def get_lengths(L, rob_val):
        L_val = int(L.item() if isinstance(L, np.ndarray) else L)
        if rob_val == "Narrow":
            offsets = [-4, -3, -2, -1, 0, 1, 2, 3, 4]
        elif rob_val == "Wide":
            offsets = [-7, -5, -3, -1, 0, 1, 3, 5, 7]
        else:
            offsets = [-6, -4, -2, -1, 0, 1, 2, 4, 6]
        return [max(2, L_val + off) for off in offsets]
        
    lengths = [
        get_lengths(ema_len, rob),
        get_lengths(hull_len, rob),
        get_lengths(wma_len, rob),
        get_lengths(dema_len, rob),
        get_lengths(lsma_len, rob),
        get_lengths(kama_len, rob)
    ]
    
    global _MA_CACHE

    ema_len_val = int(ema_len.item() if isinstance(ema_len, np.ndarray) else ema_len)
    hull_len_val = int(hull_len.item() if isinstance(hull_len, np.ndarray) else hull_len)
    wma_len_val = int(wma_len.item() if isinstance(wma_len, np.ndarray) else wma_len)
    dema_len_val = int(dema_len.item() if isinstance(dema_len, np.ndarray) else dema_len)
    lsma_len_val = int(lsma_len.item() if isinstance(lsma_len, np.ndarray) else lsma_len)
    kama_len_val = int(kama_len.item() if isinstance(kama_len, np.ndarray) else kama_len)

    for c in range(cols):
        c_arr = close_np[:, c].astype(np.float64)
        
        # Build a cache key for this column
        check_vals = (c_arr[0], c_arr[rows // 2], c_arr[-1]) if rows > 0 else (0.0, 0.0, 0.0)
        cache_key = (
            rows,
            check_vals,
            rob,
            ema_len_val,
            hull_len_val,
            wma_len_val,
            dema_len_val,
            lsma_len_val,
            kama_len_val
        )
        
        cached_mas = None
        with _MA_CACHE_LOCK:
            if cache_key in _MA_CACHE:
                cached_mas = _MA_CACHE[cache_key]
                
        if cached_mas is not None:
            mas_3d[:, c, :] = cached_mas
        else:
            col_mas = np.full((rows, 54), np.nan, dtype=np.float64)
            for i, l in enumerate(lengths[0]):
                col_mas[:, i] = calc_ema(c_arr, l)
            for i, l in enumerate(lengths[1]):
                col_mas[:, 9 + i] = calc_sma(c_arr, l)
            for i, l in enumerate(lengths[2]):
                col_mas[:, 18 + i] = calc_wma(c_arr, l)
            for i, l in enumerate(lengths[3]):
                col_mas[:, 27 + i] = calc_dema(c_arr, l)
            for i, l in enumerate(lengths[4]):
                col_mas[:, 36 + i] = calc_lsma(c_arr, l)
            for i, l in enumerate(lengths[5]):
                col_mas[:, 45 + i] = calc_kama(c_arr, l)
                
            with _MA_CACHE_LOCK:
                if len(_MA_CACHE) >= 32:
                    _MA_CACHE.clear()
                _MA_CACHE[cache_key] = col_mas
                
            mas_3d[:, c, :] = col_mas
            
    def get_val(param):
        return param.item() if isinstance(param, np.ndarray) else param

    ema_w_val = float(get_val(ema_w))
    hma_w_val = float(get_val(hma_w))
    wma_w_val = float(get_val(wma_w))
    dema_w_val = float(get_val(dema_w))
    lsma_w_val = float(get_val(lsma_w))
    kama_w_val = float(get_val(kama_w))
            
    weights = np.array([ema_w_val, hma_w_val, wma_w_val, dema_w_val, lsma_w_val, kama_w_val], dtype=np.float64)
    
    avg_sig, direction = _adaptive_trend_nb(
        close_np, mas_3d, 
        float(get_val(La)) / 1000.0, float(get_val(De)) / 100.0, int(get_val(cutout)), 
        float(get_val(Long_threshold)), float(get_val(Short_threshold)), weights
    )
    
    if len(np.asarray(close).shape) == 1:
        avg_sig = avg_sig[:, 0]
        direction = direction[:, 0]
        
    return avg_sig, direction
    
AdaptiveTrend = vbt.IndicatorFactory(
    class_name='AdaptiveTrend',
    short_name='atc',
    input_names=['close'],
    param_names=['La', 'De', 'cutout', 'robustness', 'Long_threshold', 'Short_threshold',
                 'ema_len', 'ema_w', 'hull_len', 'hma_w', 'wma_len', 'wma_w',
                 'dema_len', 'dema_w', 'lsma_len', 'lsma_w', 'kama_len', 'kama_w'],
    output_names=['average_signal', 'direction']
).from_apply_func(
    apply_adaptive_trend,
    La=0.02, De=0.03, cutout=0, robustness="Medium", Long_threshold=0.1, Short_threshold=-0.1,
    ema_len=28, ema_w=1.0, hull_len=28, hma_w=1.0, wma_len=28, wma_w=1.0,
    dema_len=28, dema_w=1.0, lsma_len=28, lsma_w=1.0, kama_len=28, kama_w=1.0,
    keep_pd=True
)
