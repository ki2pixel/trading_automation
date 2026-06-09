import numpy as np
import pandas as pd
from typing import Any, Dict, Literal, Tuple
from pydantic import BaseModel, Field

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from backtest_engine.indicators.msl_trend import MSLTrend

class MSLTrendStrategyConfig(BaseModel):
    # Strategy parameters
    length: int = 70
    mult: float = 1.2
    
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

def run_msl_trend_strategy(df: pd.DataFrame, config: MSLTrendStrategyConfig) -> Tuple[pd.DataFrame, pd.DataFrame]:
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Compute vectorized states using our IndicatorFactory
    msl = MSLTrend.run(
        high, low, close,
        length=config.length,
        mult=config.mult
    )
    
    state_arr = msl.state.to_numpy()
    
    n = len(df)
    long_entry = np.zeros(n, dtype=bool)
    short_entry = np.zeros(n, dtype=bool)
    long_exit = np.zeros(n, dtype=bool)
    short_exit = np.zeros(n, dtype=bool)
    
    # Vectorized signal logic
    # State mapping: 1.0 (Bullish), -1.0 (Bearish), 0.0 (Mixed)
    long_entry[1:] = (state_arr[1:] == 1.0) & (state_arr[:-1] != 1.0)
    long_exit[1:] = (state_arr[1:] != 1.0) & (state_arr[:-1] == 1.0)
    
    short_entry[1:] = (state_arr[1:] == -1.0) & (state_arr[:-1] != -1.0)
    short_exit[1:] = (state_arr[1:] != -1.0) & (state_arr[:-1] == -1.0)
    
    df['long_entry'] = long_entry
    df['short_entry'] = short_entry
    df['long_exit'] = long_exit
    df['short_exit'] = short_exit
    
    return pd.DataFrame(index=df.index), pd.DataFrame()
