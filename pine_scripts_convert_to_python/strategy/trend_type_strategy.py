import numpy as np
import pandas as pd
from typing import Any, Dict, Literal, Tuple
from pydantic import BaseModel, Field

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from backtest_engine.indicators.trend_type import TrendType

class TrendTypeStrategyConfig(BaseModel):
    # Strategy parameters
    use_atr: bool = True
    atr_len: int = 14
    atr_ma_len: int = 20
    use_adx: bool = True
    adx_len: int = 14
    di_len: int = 14
    adx_lim: float = 25.0
    smooth: int = 3
    
    signal_mode: Literal["Close", "Live"] = "Close"
    
    enable_stop_loss: bool = False
    stop_loss_pct: float = 0.0
    enable_take_profit: bool = False
    take_profit_pct: float = 0.0
    enable_trailing_stop: bool = False
    trail_profit_pct: float = 0.0
    trail_loss_pct: float = 0.0
    
    allocator_config: Dict[str, Any] = Field(default_factory=dict)
    enable_pyramiding: bool = False
    max_pyramid_layers: int = 1

def run_trend_type_strategy(df: pd.DataFrame, config: TrendTypeStrategyConfig) -> Tuple[pd.DataFrame, pd.DataFrame]:
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Compute vectorized states using our IndicatorFactory
    tt = TrendType.run(
        high, low, close,
        use_atr=config.use_atr,
        atr_len=config.atr_len,
        atr_ma_len=config.atr_ma_len,
        use_adx=config.use_adx,
        adx_len=config.adx_len,
        di_len=config.di_len,
        adx_lim=config.adx_lim,
        smooth=config.smooth
    )
    
    state_arr = tt.state.to_numpy()
    
    n = len(df)
    long_entry = np.zeros(n, dtype=bool)
    short_entry = np.zeros(n, dtype=bool)
    long_exit = np.zeros(n, dtype=bool)
    short_exit = np.zeros(n, dtype=bool)
    
    # Vectorized signal logic
    long_entry[1:] = (state_arr[1:] == 2.0) & (state_arr[:-1] != 2.0)
    long_exit[1:] = (state_arr[1:] != 2.0) & (state_arr[:-1] == 2.0)
    
    short_entry[1:] = (state_arr[1:] == -2.0) & (state_arr[:-1] != -2.0)
    short_exit[1:] = (state_arr[1:] != -2.0) & (state_arr[:-1] == -2.0)
    
    df['long_entry'] = long_entry
    df['short_entry'] = short_entry
    df['long_exit'] = long_exit
    df['short_exit'] = short_exit
    
    return pd.DataFrame(index=df.index), pd.DataFrame()
