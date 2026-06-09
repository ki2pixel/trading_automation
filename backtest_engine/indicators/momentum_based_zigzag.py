import numpy as np
import pandas as pd
import vectorbt as vbt
from numba import njit
from typing import Tuple

@njit(cache=True)
def calc_rma_numba_2d(src: np.ndarray, length: int) -> np.ndarray:
    rows, cols = src.shape
    alpha = 1.0 / length
    out = np.empty_like(src)
    for c in range(cols):
        out[0, c] = src[0, c]
        for r in range(1, rows):
            if np.isnan(out[r-1, c]):
                out[r, c] = src[r, c]
            else:
                out[r, c] = alpha * src[r, c] + (1 - alpha) * out[r-1, c]
    return out

@njit(cache=True)
def calc_ema_numba_2d(src: np.ndarray, length: int) -> np.ndarray:
    rows, cols = src.shape
    alpha = 2.0 / (length + 1)
    out = np.empty_like(src)
    for c in range(cols):
        out[0, c] = src[0, c]
        for r in range(1, rows):
            if np.isnan(out[r-1, c]):
                out[r, c] = src[r, c]
            else:
                out[r, c] = alpha * src[r, c] + (1 - alpha) * out[r-1, c]
    return out

@njit(cache=True)
def calc_rsi_numba_2d(close: np.ndarray, length: int) -> np.ndarray:
    rows, cols = close.shape
    diff = np.empty_like(close)
    for c in range(cols):
        diff[0, c] = 0.0
        for r in range(1, rows):
            diff[r, c] = close[r, c] - close[r-1, c]
    
    up = np.where(diff > 0, diff, 0.0)
    down = np.where(diff < 0, -diff, 0.0)
    
    rmaup = calc_rma_numba_2d(up, length)
    rmadown = calc_rma_numba_2d(down, length)
    
    rsi = np.empty_like(close)
    for c in range(cols):
        for r in range(rows):
            if rmadown[r, c] == 0:
                rsi[r, c] = 100.0 if rmaup[r, c] != 0 else 0.0
            else:
                rs = rmaup[r, c] / rmadown[r, c]
                rsi[r, c] = 100.0 - (100.0 / (1.0 + rs))
    return rsi

@njit(cache=True)
def momentum_based_zigzag_nb(
    high: np.ndarray, 
    low: np.ndarray, 
    close: np.ndarray, 
    rsi_period: int, 
    qqe_factor: float, 
    rsi_smoothing: int,
    ob: float,
    os: float
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    
    rows, cols = close.shape
    
    rsi_currenttf = calc_rsi_numba_2d(close, rsi_period)
    rsi5 = calc_rsi_numba_2d(close, 5)
    
    RsiMa = calc_ema_numba_2d(rsi_currenttf, rsi_smoothing)
    
    AtrRsi = np.empty_like(RsiMa)
    for c in range(cols):
        AtrRsi[0, c] = 0.0
        for r in range(1, rows):
            AtrRsi[r, c] = abs(RsiMa[r-1, c] - RsiMa[r, c])
            
    wilders_period = rsi_period * 2 - 1
    MaAtrRsi = calc_ema_numba_2d(AtrRsi, wilders_period)
    dar_array = calc_ema_numba_2d(MaAtrRsi, wilders_period) * qqe_factor
    
    go_long = np.zeros((rows, cols), dtype=np.bool_)
    go_short = np.zeros((rows, cols), dtype=np.bool_)
    zigzag_out = np.full((rows, cols), np.nan, dtype=np.float64)
    stoploss_long = np.full((rows, cols), np.nan, dtype=np.float64)
    stoploss_short = np.full((rows, cols), np.nan, dtype=np.float64)
    
    for c in range(cols):
        longband = 0.0
        shortband = 0.0
        trend = 1
        
        qqexlong = 0.0
        qqexshort = 0.0
        
        barssince_qqexlong = 999999
        barssince_qqexshort = 999999
        
        last_qqe_high = np.nan
        last_qqe_low = np.nan
        
        momentum_direction = 0
        
        zz_peak = np.nan
        zz_bottom = np.nan
        
        barssince_momentumup = 999999
        barssince_momentumdown = 999999
        
        barssince_rsi5_ob = 999999
        barssince_rsi5_os = 999999
        
        pl = np.nan
        ph = np.nan

        for r in range(1, rows):
            rsindex = RsiMa[r, c]
            rsindex_prev = RsiMa[r-1, c]
            dar = dar_array[r, c]
            
            newshortband = rsindex + dar
            newlongband = rsindex - dar
            
            longband_prev = longband
            if rsindex_prev > longband_prev and rsindex > longband_prev:
                longband = max(longband_prev, newlongband)
            else:
                longband = newlongband
                
            shortband_prev = shortband
            if rsindex_prev < shortband_prev and rsindex < shortband_prev:
                shortband = min(shortband_prev, newshortband)
            else:
                shortband = newshortband

            if qqexlong == 1:
                barssince_qqexlong = 0
            else:
                barssince_qqexlong += 1
                
            if qqexshort == 1:
                barssince_qqexshort = 0
            else:
                barssince_qqexshort += 1
                
            qqe_goingup = barssince_qqexlong < barssince_qqexshort
            qqe_goingdown = barssince_qqexlong > barssince_qqexshort
            
            qqe_goingup_prev = (barssince_qqexlong - 1 < barssince_qqexshort - 1) if barssince_qqexlong > 0 and barssince_qqexshort > 0 else False
            qqe_goingdown_prev = (barssince_qqexlong - 1 > barssince_qqexshort - 1) if barssince_qqexlong > 0 and barssince_qqexshort > 0 else False
            
            last_qqe_high_prev = last_qqe_high
            if (high[r, c] > last_qqe_high_prev and qqe_goingup) or (qqe_goingdown_prev and qqe_goingup):
                last_qqe_high = high[r, c]
            else:
                last_qqe_high = last_qqe_high_prev if not np.isnan(last_qqe_high_prev) else high[r, c]
                
            last_qqe_low_prev = last_qqe_low
            if (low[r, c] < last_qqe_low_prev and qqe_goingdown) or (qqe_goingup_prev and qqe_goingdown):
                last_qqe_low = low[r, c]
            else:
                last_qqe_low = last_qqe_low_prev if not np.isnan(last_qqe_low_prev) else low[r, c]
                
            cross_rsindex_shortband = (rsindex_prev <= shortband_prev) and (rsindex > shortband_prev)
            cross_high_lqh = (high[r-1, c] <= last_qqe_high_prev) and (high[r, c] > last_qqe_high) if not np.isnan(last_qqe_high_prev) else False
            
            cross_rsindex_longband = (rsindex_prev >= longband_prev) and (rsindex < longband_prev)
            cross_low_lql = (low[r-1, c] >= last_qqe_low_prev) and (low[r, c] < last_qqe_low) if not np.isnan(last_qqe_low_prev) else False
            
            trend_prev = trend
            if cross_rsindex_shortband or cross_high_lqh:
                trend = 1
            elif cross_rsindex_longband or cross_low_lql:
                trend = -1
            else:
                trend = trend_prev
                
            if trend == 1 and trend_prev == -1:
                qqexlong += 1
            else:
                qqexlong = 0
                
            if trend == -1 and trend_prev == 1:
                qqexshort += 1
            else:
                qqexshort = 0
                
            qqe_long = 1 if qqexlong == 1 else 0
            qqe_short = -1 if qqexshort == 1 else 0
            
            qqenew = 1 if qqe_long == 1 else (-1 if qqe_short == -1 else 0)
            
            qqeup = qqenew == 1
            qqedown = qqenew == -1
            
            momentum_direction_prev = momentum_direction
            if qqeup:
                momentum_direction = 1
            elif qqedown:
                momentum_direction = -1
            else:
                momentum_direction = momentum_direction_prev
                
            zz_goingup = momentum_direction == 1
            zz_goingdown = momentum_direction == -1
            zz_goingup_prev = momentum_direction_prev == 1
            zz_goingdown_prev = momentum_direction_prev == -1
            
            zz_peak_prev = zz_peak
            if (high[r, c] > zz_peak_prev and zz_goingup) or (zz_goingdown_prev and zz_goingup) or np.isnan(zz_peak_prev):
                zz_peak = high[r, c]
            else:
                zz_peak = zz_peak_prev
                
            zz_bottom_prev = zz_bottom
            if (low[r, c] < zz_bottom_prev and zz_goingdown) or (zz_goingup_prev and zz_goingdown) or np.isnan(zz_bottom_prev):
                zz_bottom = low[r, c]
            else:
                zz_bottom = zz_bottom_prev
                
            if zz_goingup and zz_goingdown_prev:
                zigzag_out[r, c] = zz_bottom_prev
            elif zz_goingup_prev and zz_goingdown:
                zigzag_out[r, c] = zz_peak_prev
                
            momentumup = momentum_direction == 1 and momentum_direction_prev != 1
            momentumdown = momentum_direction == -1 and momentum_direction_prev != -1
            
            if momentumup:
                barssince_momentumup = 0
                pl = zigzag_out[r, c] if not np.isnan(zigzag_out[r, c]) else zz_bottom_prev
            else:
                barssince_momentumup += 1
                
            if momentumdown:
                barssince_momentumdown = 0
                ph = zigzag_out[r, c] if not np.isnan(zigzag_out[r, c]) else zz_peak_prev
            else:
                barssince_momentumdown += 1
                
            if rsi5[r, c] > ob:
                barssince_rsi5_ob = 0
            else:
                barssince_rsi5_ob += 1
                
            if rsi5[r, c] < os:
                barssince_rsi5_os = 0
            else:
                barssince_rsi5_os += 1
                
            barssince_mup_prev = barssince_momentumup - 1 if momentumup else barssince_momentumup
            barssince_r5ob_prev = barssince_rsi5_ob - 1 if barssince_rsi5_ob > 0 else barssince_rsi5_ob
            mom_down_was_force_up = momentumdown and (barssince_mup_prev >= barssince_r5ob_prev)
            
            barssince_mdown_prev = barssince_momentumdown - 1 if momentumdown else barssince_momentumdown
            barssince_r5os_prev = barssince_rsi5_os - 1 if barssince_rsi5_os > 0 else barssince_rsi5_os
            mom_up_was_force_down = momentumup and (barssince_mdown_prev >= barssince_r5os_prev)
            
            golong = momentumup and not mom_up_was_force_down
            goshort = momentumdown and not mom_down_was_force_up
            
            sl_long = np.nan
            sl_short = np.nan
            
            if golong:
                go_long[r, c] = True
                if not np.isnan(pl):
                    sl_long = low[r, c] if low[r, c] < pl else pl
                    
            if goshort:
                go_short[r, c] = True
                if not np.isnan(ph):
                    sl_short = high[r, c] if high[r, c] > ph else ph
                    
            stoploss_long[r, c] = sl_long
            stoploss_short[r, c] = sl_short
        
    return go_long, go_short, zigzag_out, stoploss_long, stoploss_short

def get_val(param):
    return param.item() if isinstance(param, np.ndarray) else param

def momentum_based_zigzag_apply(high, low, close, rsi_period=14, qqe_factor=4.238, rsi_smoothing=5, ob=80.0, os=20.0):
    high_np = np.asarray(high)
    low_np = np.asarray(low)
    close_np = np.asarray(close)
    
    if close_np.ndim == 1:
        high_np = high_np.reshape(-1, 1)
        low_np = low_np.reshape(-1, 1)
        close_np = close_np.reshape(-1, 1)
        
    gl, gs, zz, sll, sls = momentum_based_zigzag_nb(
        high_np, low_np, close_np,
        int(get_val(rsi_period)), float(get_val(qqe_factor)), 
        int(get_val(rsi_smoothing)), float(get_val(ob)), float(get_val(os))
    )
    
    if len(np.asarray(close).shape) == 1:
        gl = gl[:, 0]
        gs = gs[:, 0]
        zz = zz[:, 0]
        sll = sll[:, 0]
        sls = sls[:, 0]
        
    return gl, gs, zz, sll, sls

MomentumBasedZigZagIndicator = vbt.IndicatorFactory(
    class_name="MomentumBasedZigZag",
    short_name="MBZZ",
    input_names=["high", "low", "close"],
    param_names=["rsi_period", "qqe_factor", "rsi_smoothing", "ob", "os"],
    output_names=["bullish_signal", "bearish_signal", "zigzag", "stoploss_long", "stoploss_short"]
).from_apply_func(
    momentum_based_zigzag_apply,
    rsi_period=14,
    qqe_factor=4.238,
    rsi_smoothing=5,
    ob=80.0,
    os=20.0,
    keep_pd=True
)
