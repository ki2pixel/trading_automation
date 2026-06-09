import numpy as np
import pandas as pd
import vectorbt as vbt
from numba import njit


@njit(cache=True)
def _pivot_retest_nb(close, low, high, pivot, r1, r2, s1, s2, new_session, retest_bars):
    """
    Numba optimized core logic for Pivot Breakout Retest Signals.
    Inputs are 2D numpy arrays of shape (time, columns).
    """
    rows, cols = close.shape
    
    bullish_signal = np.zeros_like(close, dtype=np.bool_)
    bearish_signal = np.zeros_like(close, dtype=np.bool_)
    
    for c in range(cols):
        pivot_break_bull = -1
        r1_break_bull = -1
        r2_break_bull = -1
        
        pivot_break_bear = -1
        s1_break_bear = -1
        s2_break_bear = -1
        
        for r in range(1, rows):
            if new_session[r, c]:
                pivot_break_bull = -1
                r1_break_bull = -1
                r2_break_bull = -1
                
                pivot_break_bear = -1
                s1_break_bear = -1
                s2_break_bear = -1
                
            curr_close = close[r, c]
            prev_close = close[r-1, c]
            curr_low = low[r, c]
            curr_high = high[r, c]
            
            p = pivot[r, c]
            r1_val = r1[r, c]
            r2_val = r2[r, c]
            s1_val = s1[r, c]
            s2_val = s2[r, c]
            
            # Crossovers (bullish break)
            if prev_close <= p and curr_close > p:
                pivot_break_bull = r
            if prev_close <= r1_val and curr_close > r1_val:
                r1_break_bull = r
            if prev_close <= r2_val and curr_close > r2_val:
                r2_break_bull = r
                
            # Crossunders (bearish break)
            if prev_close >= p and curr_close < p:
                pivot_break_bear = r
            if prev_close >= s1_val and curr_close < s1_val:
                s1_break_bear = r
            if prev_close >= s2_val and curr_close < s2_val:
                s2_break_bear = r
                
            # Bullish Retest check
            sig_bull = False
            if pivot_break_bull != -1 and (r - pivot_break_bull <= retest_bars) and curr_low <= p and curr_close > p:
                sig_bull = True
            if r1_break_bull != -1 and (r - r1_break_bull <= retest_bars) and curr_low <= r1_val and curr_close > r1_val:
                sig_bull = True
            if r2_break_bull != -1 and (r - r2_break_bull <= retest_bars) and curr_low <= r2_val and curr_close > r2_val:
                sig_bull = True
                
            if sig_bull:
                bullish_signal[r, c] = True
                pivot_break_bull = -1
                r1_break_bull = -1
                r2_break_bull = -1
                
            # Bearish Retest check
            sig_bear = False
            if pivot_break_bear != -1 and (r - pivot_break_bear <= retest_bars) and curr_high >= p and curr_close < p:
                sig_bear = True
            if s1_break_bear != -1 and (r - s1_break_bear <= retest_bars) and curr_high >= s1_val and curr_close < s1_val:
                sig_bear = True
            if s2_break_bear != -1 and (r - s2_break_bear <= retest_bars) and curr_high >= s2_val and curr_close < s2_val:
                sig_bear = True
                
            if sig_bear:
                bearish_signal[r, c] = True
                pivot_break_bear = -1
                s1_break_bear = -1
                s2_break_bear = -1
                
    return bullish_signal, bearish_signal


def apply_pivot_retest(
    high: pd.DataFrame,
    low: pd.DataFrame,
    close: pd.DataFrame,
    pivot_timeframe: str = "D",
    retest_bars: int = 5
):
    """
    VectorBT apply function to calculate Pivot Breakout Retests.
    """
    # Replace 'M' with 'ME' for newer pandas compatibility while supporting Pine Script 'M'
    resample_tf = "ME" if pivot_timeframe == "M" else pivot_timeframe
    
    # 1. Resample to calculate previous timeframe OHLC safely without lookahead bias
    prev_h = high.resample(resample_tf).max().shift(1)
    prev_l = low.resample(resample_tf).min().shift(1)
    prev_c = close.resample(resample_tf).last().shift(1)
    
    # 2. Calculate classic pivot levels
    pivot = (prev_h + prev_l + prev_c) / 3
    r1 = (2 * pivot) - prev_l
    s1 = (2 * pivot) - prev_h
    r2 = pivot + (prev_h - prev_l)
    s2 = pivot - (prev_h - prev_l)
    
    # 3. Reindex to original resolution
    pivot = pivot.reindex(high.index, method='ffill')
    r1 = r1.reindex(high.index, method='ffill')
    s1 = s1.reindex(high.index, method='ffill')
    r2 = r2.reindex(high.index, method='ffill')
    s2 = s2.reindex(high.index, method='ffill')
    
    # 4. Detect new session starts
    # We create a series of the resampled index dates, broadcast it, and check for changes
    session_starts = pd.Series(prev_h.index, index=prev_h.index)
    aligned_sessions = session_starts.reindex(high.index, method='ffill')
    
    new_session_1d = (aligned_sessions != aligned_sessions.shift(1)).values
    
    # Handle single or multi-column data
    cols_count = high.shape[1] if len(high.shape) > 1 else 1
    if len(high.shape) == 1:
        new_session = new_session_1d[:, None]
        h_val = high.values[:, None]
        l_val = low.values[:, None]
        c_val = close.values[:, None]
        p_val = pivot.values[:, None]
        r1_val = r1.values[:, None]
        r2_val = r2.values[:, None]
        s1_val = s1.values[:, None]
        s2_val = s2.values[:, None]
    else:
        new_session = np.tile(new_session_1d[:, None], (1, cols_count))
        h_val = high.values
        l_val = low.values
        c_val = close.values
        p_val = pivot.values
        r1_val = r1.values
        r2_val = r2.values
        s1_val = s1.values
        s2_val = s2.values
        
    # 5. Call Numba optimized logic
    bullish, bearish = _pivot_retest_nb(
        c_val, l_val, h_val,
        p_val, r1_val, r2_val, s1_val, s2_val,
        new_session, retest_bars
    )
    
    # 6. Format output correctly for 1D or 2D
    if len(high.shape) == 1:
        bullish = bullish[:, 0]
        bearish = bearish[:, 0]
        
    return bullish, bearish

PivotRetest = vbt.IndicatorFactory(
    class_name="PivotRetest",
    short_name="PR",
    input_names=["high", "low", "close"],
    param_names=["pivot_timeframe", "retest_bars"],
    output_names=["bullish_signal", "bearish_signal"]
).from_apply_func(
    apply_pivot_retest,
    pivot_timeframe="D",
    retest_bars=5,
    keep_pd=True
)
