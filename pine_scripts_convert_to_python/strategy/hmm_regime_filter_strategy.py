import pandas as pd
import numpy as np
from pydantic import BaseModel, Field
from typing import Dict, Any, Tuple
import vectorbt as vbt
from backtest_engine.indicators.hmm_regime_filter import HMMRegimeFilter

class HMMRegimeFilterStrategyConfig(BaseModel):
    obs_len: int = Field(default=14, description="Observation Length for EMA")
    stat_len: int = Field(default=28, description="Statistic Length for StdDev")
    mu_k: float = Field(default=1.5, description="Mu Multiplier")
    stick: float = Field(default=0.9, description="Stickiness Probability")
    confirm_bars: int = Field(default=2, description="Confirmation Bars")
    dom_thresh: float = Field(default=0.5, description="Dominance Threshold")

def run_hmm_regime_filter_strategy(
    df: pd.DataFrame, 
    config: HMMRegimeFilterStrategyConfig
) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, Dict[str, Any]]:
    """
    Exécute la stratégie HMM Regime Filter.
    """
    hmm_indicator = HMMRegimeFilter.run(
        high=df['high'],
        low=df['low'],
        close=df['close'],
        obs_len=config.obs_len,
        stat_len=config.stat_len,
        mu_k=config.mu_k,
        stick=config.stick,
        confirm_bars=config.confirm_bars,
        dom_thresh=config.dom_thresh
    )
    
    official_state = hmm_indicator.official_state
    official_state_prev = official_state.shift(1).fillna(1)
    
    # Signaux d'entrée
    long_entry = (official_state == 0) & (official_state_prev != 0)
    short_entry = (official_state == 2) & (official_state_prev != 2)
    
    # Signaux de sortie
    long_exit = (official_state != 0) & (official_state_prev == 0)
    short_exit = (official_state != 2) & (official_state_prev == 2)
    
    indicators = {
        'official_state': official_state,
        'prob_up': hmm_indicator.prob_up,
        'prob_range': hmm_indicator.prob_range,
        'prob_down': hmm_indicator.prob_down
    }
    
    return long_entry, short_entry, long_exit, short_exit, indicators
