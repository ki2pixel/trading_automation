import numpy as np
import pandas as pd
import vectorbt as vbt

def apply_msl(
    high: pd.DataFrame,
    low: pd.DataFrame,
    close: pd.DataFrame,
    length: int = 70,
    mult: float = 1.2
) -> np.ndarray:
    """
    MSL Friendly Trend
    Translated to VectorBT using vectorized operations.
    
    Returns:
    - 1.0 : Bullish
    - -1.0 : Bearish
    - 0.0 : Mixed / Initialization
    """
    # 1. Zero-Lag EMA (ZLEMA)
    lag = (length - 1) // 2
    
    # Calculate src: close + (close - close.shift(lag))
    src = close + (close - close.shift(lag))
    zlema = src.ewm(span=length, adjust=False).mean()

    # 2. Volatility Band (Wilder's ATR = RMA of TR)
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = np.maximum(tr1, np.maximum(tr2, tr3))
    
    atr = tr.ewm(alpha=1/length, adjust=False).mean()
    volatility = atr.rolling(window=length * 3).max() * mult

    # 3. Trend State Logic
    upper_band = zlema + volatility
    lower_band = zlema - volatility
    
    # Using np.where to build the state array: 1.0 for bull cross, -1.0 for bear cross, NaN otherwise.
    state_arr = np.where(close > upper_band, 1.0, np.where(close < lower_band, -1.0, np.nan))
    
    # Forward fill to persist the state, and fill initial NaNs with 0.0
    state_df = pd.DataFrame(state_arr, index=close.index, columns=close.columns)
    state_filled = state_df.ffill().fillna(0.0)
        
    return np.asarray(state_filled, dtype=np.float64)

MSLTrend = vbt.IndicatorFactory(
    class_name="MSLTrend",
    short_name="MSL",
    input_names=["high", "low", "close"],
    param_names=["length", "mult"],
    output_names=["state"]
).from_apply_func(
    apply_msl,
    length=70,
    mult=1.2,
    keep_pd=True
)
