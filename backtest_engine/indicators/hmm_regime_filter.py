import numpy as np
import pandas as pd
import vectorbt as vbt
from numba import njit
import math

@njit(cache=True)
def gpdf(x, m, s):
    if s == 0.0:
        return 0.0
    return math.exp(-0.5 * ((x - m) / s)**2) / s

@njit(cache=True)
def _hmm_regime_filter_1d_nb(obs_arr, sigma_arr, obs_len, stat_len, mu_k, stick, confirm_bars, dom_thresh):
    n = obs_arr.shape[0]
    out_prob_up = np.zeros(n, dtype=np.float64)
    out_prob_range = np.zeros(n, dtype=np.float64)
    out_prob_down = np.zeros(n, dtype=np.float64)
    out_official_state = np.full(n, 1, dtype=np.int64)
    
    p0 = 1.0 / 3.0
    p1 = 1.0 / 3.0
    p2 = 1.0 / 3.0
    
    current_state = 1
    pending_state = 1
    state_duration = 0
    
    out_prob_up[0] = p0
    out_prob_range[0] = p1
    out_prob_down[0] = p2
    out_official_state[0] = current_state
    
    off = 1.0 - stick
    
    for i in range(1, n):
        obs = obs_arr[i]
        sigma = sigma_arr[i]
        
        if np.isnan(obs) or np.isnan(sigma):
            out_prob_up[i] = p0
            out_prob_range[i] = p1
            out_prob_down[i] = p2
            out_official_state[i] = current_state
            continue
            
        pr0 = p0 * stick + p1 * (off * 0.5) + p2 * (off * 0.25)
        pr1 = p0 * (off * 0.75) + p1 * stick + p2 * (off * 0.75)
        pr2 = p0 * (off * 0.25) + p1 * (off * 0.5) + p2 * stick
        
        mU = mu_k * sigma
        
        e0 = gpdf(obs, mU, sigma)
        e1 = gpdf(obs, 0.0, sigma * 0.8)
        e2 = gpdf(obs, -mU, sigma)
        
        p0_unnorm = pr0 * e0
        p1_unnorm = pr1 * e1
        p2_unnorm = pr2 * e2
        
        total_p = p0_unnorm + p1_unnorm + p2_unnorm
        if total_p > 0.0:
            p0 = p0_unnorm / total_p
            p1 = p1_unnorm / total_p
            p2 = p2_unnorm / total_p
        else:
            p0 = 1.0 / 3.0
            p1 = 1.0 / 3.0
            p2 = 1.0 / 3.0
            
        out_prob_up[i] = p0
        out_prob_range[i] = p1
        out_prob_down[i] = p2
        
        best_state = 1
        max_p = p1
        
        if p0 > max_p:
            max_p = p0
            best_state = 0
            
        if p2 > max_p:
            max_p = p2
            best_state = 2
            
        if max_p < dom_thresh:
            best_state = 1
            
        if best_state != pending_state:
            pending_state = best_state
            state_duration = 0
            
        state_duration += 1
        
        if state_duration >= confirm_bars and current_state != pending_state:
            current_state = pending_state
            
        out_official_state[i] = current_state
        
    return out_official_state, out_prob_up, out_prob_range, out_prob_down

@njit(cache=True)
def _hmm_regime_filter_2d_nb(obs_arr, sigma_arr, obs_len, stat_len, mu_k, stick, confirm_bars, dom_thresh):
    out_official_state = np.empty_like(obs_arr, dtype=np.int64)
    out_prob_up = np.empty_like(obs_arr, dtype=np.float64)
    out_prob_range = np.empty_like(obs_arr, dtype=np.float64)
    out_prob_down = np.empty_like(obs_arr, dtype=np.float64)
    
    for col in range(obs_arr.shape[1]):
        official, pup, prange, pdown = _hmm_regime_filter_1d_nb(
            obs_arr[:, col], sigma_arr[:, col], obs_len, stat_len, mu_k, stick, confirm_bars, dom_thresh
        )
        out_official_state[:, col] = official
        out_prob_up[:, col] = pup
        out_prob_range[:, col] = prange
        out_prob_down[:, col] = pdown
        
    return out_official_state, out_prob_up, out_prob_range, out_prob_down

def apply_hmm_regime_filter(high, low, close, obs_len=14, stat_len=28, mu_k=1.5, stick=0.9, confirm_bars=2, dom_thresh=0.5):
    high = np.asarray(high)
    low = np.asarray(low)
    close = np.asarray(close)
    
    # Compute ATR
    tr0 = np.abs(high - low)
    tr1 = np.abs(high - np.roll(close, 1, axis=0))
    tr2 = np.abs(low - np.roll(close, 1, axis=0))
    tr = np.maximum(tr0, np.maximum(tr1, tr2))
    tr[0] = 0.0 # First row has no previous close
    
    # Calculate ATR using Wilder's EMA (which is typical for ATR) or simple EMA
    # PineScript ATR(14) uses RMA (Wilder's moving average)
    atr = pd.DataFrame(tr).ewm(alpha=1/14, adjust=False).mean().values
    
    ret = close - np.roll(close, 1, axis=0)
    ret[0] = 0.0
    
    norm_ret = np.zeros_like(ret)
    valid_atr = atr > 0
    norm_ret[valid_atr] = ret[valid_atr] / atr[valid_atr]
    
    # obs = EMA(norm_ret, obs_len)
    obs = pd.DataFrame(norm_ret).ewm(span=obs_len, adjust=False).mean().values
    
    # sigma = StdDev(obs, stat_len)
    sigma = pd.DataFrame(obs).rolling(window=stat_len, min_periods=1).std(ddof=0).values
    # Replace NaN with 0.0 initially for safety
    sigma = np.nan_to_num(sigma, nan=0.0)
    
    if close.ndim == 1:
        return _hmm_regime_filter_1d_nb(obs, sigma, obs_len, stat_len, mu_k, stick, confirm_bars, dom_thresh)
    else:
        return _hmm_regime_filter_2d_nb(obs, sigma, obs_len, stat_len, mu_k, stick, confirm_bars, dom_thresh)

HMMRegimeFilter = vbt.IndicatorFactory(
    class_name="HMMRegimeFilter",
    short_name="HMM",
    input_names=["high", "low", "close"],
    param_names=["obs_len", "stat_len", "mu_k", "stick", "confirm_bars", "dom_thresh"],
    output_names=["official_state", "prob_up", "prob_range", "prob_down"]
).from_apply_func(
    apply_hmm_regime_filter,
    obs_len=14,
    stat_len=28,
    mu_k=1.5,
    stick=0.9,
    confirm_bars=2,
    dom_thresh=0.5,
    keep_pd=True
)
