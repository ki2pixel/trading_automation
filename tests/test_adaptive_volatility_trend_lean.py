"""Unit tests for Adaptive Volatility Trend strategy lean mode and Numba optimization."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from backtest_engine.strategies.adaptive_volatility_trend import (
    AVTConfigOverrides,
    run_adaptive_volatility_trend,
)


def test_avt_lean_mode_parity() -> None:
    # 1. Generate mock OHLCV data
    idx = pd.date_range("2026-01-01", periods=1000, freq="5min")
    np.random.seed(42)
    close_prices = 100.0 + np.random.randn(1000).cumsum()
    data = pd.DataFrame(
        {
            "open": close_prices - np.random.rand(1000),
            "high": close_prices + np.random.rand(1000),
            "low": close_prices - np.random.rand(1000),
            "close": close_prices,
            "volume": np.random.rand(1000) * 1000.0,
        },
        index=idx,
    )

    overrides = AVTConfigOverrides(
        length=21,
        atr_len=14,
        atr_mult=2.0,
        preset="Default",
    )

    # 2. Run standard/full backtest
    full_result = run_adaptive_volatility_trend(
        data=data,
        symbol="MOCK",
        overrides=overrides,
        initial_capital=1000.0,
        timeframe_minutes=5,
        compute_full_metrics=True,
    )

    # 3. Run lean backtest
    lean_result = run_adaptive_volatility_trend(
        data=data,
        symbol="MOCK",
        overrides=overrides,
        initial_capital=1000.0,
        timeframe_minutes=5,
        compute_full_metrics=False,
        fast_score_metric="total_net_pnl",
    )

    # 4. Verify structural differences in state DataFrames
    full_cols = set(full_result.state.columns)
    lean_cols = set(lean_result.state.columns)

    # Full mode should have all diagnostic avt_ columns
    assert "avt_rsi" in full_cols
    assert "avt_upper_band" in full_cols
    assert "avt_trend_dir" in full_cols

    # Lean mode should NOT have diagnostic columns to save memory
    assert "avt_rsi" not in lean_cols
    assert "avt_upper_band" not in lean_cols
    assert "avt_trend_dir" not in lean_cols

    # But lean mode MUST have the 4 essential columns required by compute_metrics
    essential_cols = {
        "realized_net_pnl_on_fill",
        "estimated_net_if_closed_now",
        "position_size",
        "position_avg_price",
    }
    assert essential_cols.issubset(lean_cols)

    # 5. Verify functional parity
    # Signal columns must match exactly
    pd.testing.assert_series_equal(
        full_result.state["avt_long_signal"],
        lean_result.state["avt_long_signal"],
    )
    pd.testing.assert_series_equal(
        full_result.state["avt_short_signal"],
        lean_result.state["avt_short_signal"],
    )

    # Trades must match exactly
    assert len(full_result.trades) == len(lean_result.trades)
    if len(full_result.trades) > 0:
        pd.testing.assert_frame_equal(
            full_result.trades,
            lean_result.trades,
        )
