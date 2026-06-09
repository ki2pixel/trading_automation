"""Lorentzian Classification Strategy Logic.

Thin strategy wrapper with Pydantic configuration model that calls the
LorentzianClassification VectorBT indicator and produces entry/exit signals.
"""

import pandas as pd
import numpy as np
from pydantic import BaseModel, Field
from typing import Dict, Any, Tuple

from backtest_engine.indicators.lorentzian_classification import LorentzianClassification


class LorentzianClassificationStrategyConfig(BaseModel):
    """Configuration for the Lorentzian Classification ML strategy.

    Default values match the original Pine Script by @jdehorty.
    """

    # KNN General Settings
    neighbors_count: int = Field(default=8, description="Number of nearest neighbors (k)")
    max_bars_back: int = Field(default=2000, description="Maximum historical bars for KNN search")
    feature_count: int = Field(default=5, description="Number of features (2-5)")

    # Feature 1: RSI
    f1_param_a: int = Field(default=14, description="Feature 1 (RSI) primary parameter")
    f1_param_b: int = Field(default=1, description="Feature 1 (RSI) EMA smoothing")

    # Feature 2: WaveTrend
    f2_param_a: int = Field(default=10, description="Feature 2 (WT) channel length")
    f2_param_b: int = Field(default=11, description="Feature 2 (WT) average length")

    # Feature 3: CCI
    f3_param_a: int = Field(default=20, description="Feature 3 (CCI) primary parameter")
    f3_param_b: int = Field(default=1, description="Feature 3 (CCI) EMA smoothing")

    # Feature 4: ADX
    f4_param_a: int = Field(default=20, description="Feature 4 (ADX) primary parameter")
    f4_param_b: int = Field(default=2, description="Feature 4 (ADX) secondary parameter")

    # Feature 5: RSI (second instance)
    f5_param_a: int = Field(default=9, description="Feature 5 (RSI2) primary parameter")
    f5_param_b: int = Field(default=1, description="Feature 5 (RSI2) EMA smoothing")

    # Filters
    use_volatility_filter: bool = Field(default=True, description="Enable volatility filter")
    use_regime_filter: bool = Field(default=True, description="Enable regime filter")
    regime_threshold: float = Field(default=-0.1, description="Regime filter threshold")
    use_adx_filter: bool = Field(default=False, description="Enable ADX filter")
    adx_threshold: int = Field(default=20, description="ADX filter threshold")
    use_ema_filter: bool = Field(default=False, description="Enable EMA trend filter")
    ema_period: int = Field(default=200, description="EMA period for trend filter")
    use_sma_filter: bool = Field(default=False, description="Enable SMA trend filter")
    sma_period: int = Field(default=200, description="SMA period for trend filter")

    # Kernel Settings
    use_kernel_filter: bool = Field(default=True, description="Trade with kernel regression")
    kernel_h: int = Field(default=8, description="Kernel lookback window")
    kernel_r: float = Field(default=8.0, description="Kernel relative weighting")
    kernel_x: int = Field(default=25, description="Kernel regression level")
    kernel_lag: int = Field(default=2, description="Kernel lag for crossover detection")
    use_kernel_smoothing: bool = Field(default=False, description="Enhance kernel smoothing")

    # Exit Settings
    use_dynamic_exits: bool = Field(default=False, description="Use dynamic kernel-based exits")


def run_lorentzian_classification_strategy(
    df: pd.DataFrame,
    config: LorentzianClassificationStrategyConfig,
) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, Dict[str, Any]]:
    """Execute the Lorentzian Classification strategy.

    Args:
        df: DataFrame with OHLCV columns.
        config: Strategy configuration.

    Returns:
        Tuple of (long_entry, short_entry, long_exit, short_exit, indicators).
    """
    indicator = LorentzianClassification.run(
        high=df["high"],
        low=df["low"],
        close=df["close"],
        neighbors_count=config.neighbors_count,
        max_bars_back=config.max_bars_back,
        feature_count=config.feature_count,
        f1_param_a=config.f1_param_a,
        f1_param_b=config.f1_param_b,
        f2_param_a=config.f2_param_a,
        f2_param_b=config.f2_param_b,
        f3_param_a=config.f3_param_a,
        f3_param_b=config.f3_param_b,
        f4_param_a=config.f4_param_a,
        f4_param_b=config.f4_param_b,
        f5_param_a=config.f5_param_a,
        f5_param_b=config.f5_param_b,
        use_volatility_filter=config.use_volatility_filter,
        use_regime_filter=config.use_regime_filter,
        regime_threshold=config.regime_threshold,
        use_adx_filter=config.use_adx_filter,
        adx_threshold=config.adx_threshold,
        use_ema_filter=config.use_ema_filter,
        ema_period=config.ema_period,
        use_sma_filter=config.use_sma_filter,
        sma_period=config.sma_period,
        use_kernel_filter=config.use_kernel_filter,
        kernel_h=config.kernel_h,
        kernel_r=config.kernel_r,
        kernel_x=config.kernel_x,
        kernel_lag=config.kernel_lag,
        use_kernel_smoothing=config.use_kernel_smoothing,
        use_dynamic_exits=config.use_dynamic_exits,
    )

    # Extract signals directly from indicator outputs
    start_long = indicator.start_long.astype(bool)
    start_short = indicator.start_short.astype(bool)
    end_long = indicator.end_long.astype(bool)
    end_short = indicator.end_short.astype(bool)

    indicators = {
        "prediction": indicator.prediction,
        "signal": indicator.signal,
        "start_long": indicator.start_long,
        "start_short": indicator.start_short,
        "end_long": indicator.end_long,
        "end_short": indicator.end_short,
    }

    return start_long, start_short, end_long, end_short, indicators
