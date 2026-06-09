import numpy as np
import pandas as pd
from typing import Any, Dict, Literal, Tuple
from pydantic import BaseModel, Field

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from backtest_engine.indicators.momentum_based_zigzag import MomentumBasedZigZagIndicator

class MomentumBasedZigZagStrategyConfig(BaseModel):
    rsi_period: int = 14
    qqe_factor: float = 4.238
    rsi_smoothing: int = 5
    ob: float = 80.0
    os: float = 20.0
    
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

def run_momentum_based_zigzag_strategy(df: pd.DataFrame, config: MomentumBasedZigZagStrategyConfig) -> Tuple[pd.DataFrame, pd.DataFrame]:
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Compute signals using our Numba IndicatorFactory
    mbzz = MomentumBasedZigZagIndicator.run(
        high, low, close,
        rsi_period=config.rsi_period,
        qqe_factor=config.qqe_factor,
        rsi_smoothing=config.rsi_smoothing,
        ob=config.ob,
        os=config.os
    )
    
    # Convert vectors to arrays
    long_entry = mbzz.bullish_signal.to_numpy()
    short_entry = mbzz.bearish_signal.to_numpy()
    
    df['long_entry'] = long_entry
    df['short_entry'] = short_entry
    df['long_exit'] = short_entry.copy()
    df['short_exit'] = long_entry.copy()
    
    # Optional: pass dynamic stoploss arrays back to BrokerSimulator if supported by your framework.
    # For now we only return empty DataFrames as per adaptive_trend_classification template.
    
    return pd.DataFrame(index=df.index), pd.DataFrame()
