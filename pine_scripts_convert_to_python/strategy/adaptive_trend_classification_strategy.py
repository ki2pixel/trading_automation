import numpy as np
import pandas as pd
from typing import Any, Dict, Literal, Tuple
from pydantic import BaseModel, Field

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from backtest_engine.indicators.adaptive_trend_classification import AdaptiveTrend

class AdaptiveTrendClassificationStrategyConfig(BaseModel):
    # Strategy parameters
    La: float = 0.02
    De: float = 0.03
    cutout: int = 0
    robustness: Literal["Narrow", "Medium", "Wide"] = "Medium"
    Long_threshold: float = 0.1
    Short_threshold: float = -0.1
    
    ema_len: int = 28
    ema_w: float = 1.0
    hull_len: int = 28
    hma_w: float = 1.0
    wma_len: int = 28
    wma_w: float = 1.0
    dema_len: int = 28
    dema_w: float = 1.0
    lsma_len: int = 28
    lsma_w: float = 1.0
    kama_len: int = 28
    kama_w: float = 1.0
    
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

def run_adaptive_trend_classification_strategy(df: pd.DataFrame, config: AdaptiveTrendClassificationStrategyConfig) -> Tuple[pd.DataFrame, pd.DataFrame]:
    close = df['close']
    
    # Compute vectorized signals using our IndicatorFactory
    atc = AdaptiveTrend.run(
        close,
        La=config.La, De=config.De, cutout=config.cutout, robustness=config.robustness,
        Long_threshold=config.Long_threshold, Short_threshold=config.Short_threshold,
        ema_len=config.ema_len, ema_w=config.ema_w, hull_len=config.hull_len, hma_w=config.hma_w,
        wma_len=config.wma_len, wma_w=config.wma_w, dema_len=config.dema_len, dema_w=config.dema_w,
        lsma_len=config.lsma_len, lsma_w=config.lsma_w, kama_len=config.kama_len, kama_w=config.kama_w
    )
    
    # Convert vectors to arrays
    direction = atc.direction.to_numpy()
    
    # Generate entry and exit signals
    # direction == 1 -> Long
    # direction == -1 -> Short
    direction_shifted = np.roll(direction, 1)
    direction_shifted[0] = 0
    
    long_entry = (direction == 1) & (direction_shifted != 1)
    short_entry = (direction == -1) & (direction_shifted != -1)
    
    long_exit = short_entry.copy()
    short_exit = long_entry.copy()
    
    df['long_entry'] = long_entry
    df['short_entry'] = short_entry
    df['long_exit'] = long_exit
    df['short_exit'] = short_exit
    
    return pd.DataFrame(index=df.index), pd.DataFrame()
