import numpy as np
import pandas as pd
from typing import Any, Dict, Literal, Tuple
from pydantic import BaseModel, Field

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from backtest_engine.indicators.pivot_retest import PivotRetest

class PivotRetestStrategyConfig(BaseModel):
    # Strategy parameters
    pivot_timeframe: str = "D"
    retest_bars: int = 5
    
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

def run_pivot_retest_strategy(df: pd.DataFrame, config: PivotRetestStrategyConfig) -> Tuple[pd.DataFrame, pd.DataFrame]:
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Compute vectorized signals using our IndicatorFactory
    pr = PivotRetest.run(
        high, low, close,
        pivot_timeframe=config.pivot_timeframe,
        retest_bars=config.retest_bars
    )
    
    # Convert vectors to arrays
    bullish_signal = pr.bullish_signal.to_numpy()
    bearish_signal = pr.bearish_signal.to_numpy()
    
    # Generate entry and exit signals
    # As discussed, we close long positions on short entry, and vice-versa.
    long_entry = bullish_signal
    short_entry = bearish_signal
    
    long_exit = short_entry.copy()
    short_exit = long_entry.copy()
    
    df['long_entry'] = long_entry
    df['short_entry'] = short_entry
    df['long_exit'] = long_exit
    df['short_exit'] = short_exit
    
    return pd.DataFrame(index=df.index), pd.DataFrame()
