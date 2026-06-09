import numpy as np
import pandas as pd
import vectorbt as vbt

def apply_trend_type(
    high: pd.DataFrame,
    low: pd.DataFrame,
    close: pd.DataFrame,
    use_atr: bool = True,
    atr_len: int = 14,
    atr_ma_len: int = 20,
    use_adx: bool = True,
    adx_len: int = 14,
    di_len: int = 14,
    adx_lim: float = 25.0,
    smooth: int = 3
) -> np.ndarray:
    """
    Trend Type Indicator by BobRivera990
    Translated to VectorBT natively to avoid missing external libraries like talib.
    """
    # 1. Native ATR calculations
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = np.maximum(tr1, np.maximum(tr2, tr3))
    
    atr = tr.ewm(alpha=1/atr_len, adjust=False).mean()
    atr_ma = atr.rolling(window=atr_ma_len).mean()

    # 2. Native ADX / DI calculations
    up = high - high.shift(1)
    down = low.shift(1) - low
    
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)
    
    # Convert numpy arrays back to DataFrame for ewm
    plus_dm_df = pd.DataFrame(plus_dm, index=high.index, columns=high.columns)
    minus_dm_df = pd.DataFrame(minus_dm, index=high.index, columns=high.columns)
    
    trur = tr.ewm(alpha=1/di_len, adjust=False).mean()
    plus_di = 100 * plus_dm_df.ewm(alpha=1/di_len, adjust=False).mean() / trur
    minus_di = 100 * minus_dm_df.ewm(alpha=1/di_len, adjust=False).mean() / trur
    
    sum_di = plus_di + minus_di
    dx = 100 * (plus_di - minus_di).abs() / np.where(sum_di == 0, 1.0, sum_di)
    adx = dx.ewm(alpha=1/adx_len, adjust=False).mean()

    # 3. Conditions
    cnd_sideways_1 = use_atr & (atr <= atr_ma)
    cnd_sideways_2 = use_adx & (adx <= adx_lim)
    cnd_sideways = cnd_sideways_1 | cnd_sideways_2

    cnd_up = plus_di > minus_di
    cnd_down = minus_di >= plus_di

    # 4. State allocation using np.select
    trend_type = np.select(
        [cnd_sideways, cnd_up, cnd_down],
        [0.0, 2.0, -2.0],
        default=np.nan
    )
    
    # 5. Smoothing
    trend_df = pd.DataFrame(trend_type, index=close.index, columns=close.columns)
    if smooth > 1:
        smoothed = trend_df.rolling(window=smooth).mean()
        trend_type = np.round(smoothed / 2.0) * 2.0
    
    return np.asarray(trend_type, dtype=np.float64)

TrendType = vbt.IndicatorFactory(
    class_name="TrendType",
    short_name="TT",
    input_names=["high", "low", "close"],
    param_names=["use_atr", "atr_len", "atr_ma_len", "use_adx", "adx_len", "di_len", "adx_lim", "smooth"],
    output_names=["state"]
).from_apply_func(
    apply_trend_type,
    use_atr=True,
    atr_len=14,
    atr_ma_len=20,
    use_adx=True,
    adx_len=14,
    di_len=14,
    adx_lim=25.0,
    smooth=3,
    keep_pd=True
)
