"""Unit tests for Bjorgum Double Tap strategy lean mode parity and correctness."""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from backtest_engine.strategies.bjorgum_double_tap import (
    BjorgumDoubleTapConfigOverrides,
    run_bjorgum_double_tap,
)


def test_bjorgum_double_tap_lean_mode_parity() -> None:
    # 1. Generate mock OHLCV data
    idx = pd.date_range("2026-01-01", periods=500, freq="5min")
    np.random.seed(42)
    close_prices = 100.0 + np.random.randn(500).cumsum()
    data = pd.DataFrame(
        {
            "open": close_prices - np.random.rand(500),
            "high": close_prices + np.random.rand(500) + 0.5,
            "low": close_prices - np.random.rand(500) - 0.5,
            "close": close_prices,
            "volume": np.random.rand(500) * 1000.0,
        },
        index=idx,
    )

    overrides = BjorgumDoubleTapConfigOverrides(
        length=10,
        lookback=5,
        atrLength=14,
        atrMult=1.0,
        initial_capital_bucket=1000.0,
        max_capital_bucket=1000.0,
    )

    # 2. Run standard/full backtest
    full_result = run_bjorgum_double_tap(
        data=data,
        symbol="MOCK",
        overrides=overrides,
        initial_capital=1000.0,
        timeframe_minutes=5,
        compute_full_metrics=True,
    )

    # 3. Run lean backtest
    lean_result = run_bjorgum_double_tap(
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

    # Full mode should have all diagnostic columns
    assert "capital_bucket" in full_cols
    assert "withdrawn_profit" in full_cols
    assert "signal_comment" in full_cols
    assert "atr" in full_cols

    # Lean mode should NOT have diagnostic columns to save memory
    assert "capital_bucket" not in lean_cols
    assert "withdrawn_profit" not in lean_cols
    assert "signal_comment" not in lean_cols
    assert "atr" not in lean_cols

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
        full_result.state["long_signal"],
        lean_result.state["long_signal"],
    )
    pd.testing.assert_series_equal(
        full_result.state["short_signal"],
        lean_result.state["short_signal"],
    )
    pd.testing.assert_series_equal(
        full_result.state["sLow"],
        lean_result.state["sLow"],
    )
    pd.testing.assert_series_equal(
        full_result.state["sHigh"],
        lean_result.state["sHigh"],
    )

    # Trades must match exactly
    assert len(full_result.trades) == len(lean_result.trades)
    if len(full_result.trades) > 0:
        pd.testing.assert_frame_equal(
            full_result.trades,
            lean_result.trades,
        )
