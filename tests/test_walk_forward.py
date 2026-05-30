import numpy as np
import pandas as pd
import pytest

from backtest_engine.walk_forward import (
    generate_rolling_windows,
    PHASE3_BASELINE_PARAMS,
)


class TestGenerateRollingWindows:
    def test_basic_3y1y(self):
        windows = generate_rolling_windows("2018-01-01", "2022-01-01", is_years=3, oos_years=1)
        assert len(windows) == 1
        assert windows[0] == ("2018-01-01", "2021-01-01", "2021-01-01", "2022-01-01")

    def test_multiple_folds(self):
        windows = generate_rolling_windows("2018-01-01", "2024-01-01", is_years=2, oos_years=1)
        assert len(windows) == 4
        assert windows[0][0] == "2018-01-01"
        assert windows[-1][-1] == "2024-01-01"

    def test_no_window_if_too_short(self):
        windows = generate_rolling_windows("2020-01-01", "2021-01-01", is_years=3, oos_years=1)
        assert windows == []

    def test_phase3_baseline_params_structure(self):
        required = {
            "lookback_days", "volatility_multiplier_enter", "volatility_multiplier_exit",
            "target_daily_volatility", "exit_mode", "stoploss_ladder_step0",
            "stoploss_ladder_step1", "stoploss_ladder_ratio0", "takeprofit_ladder_step0",
        }
        assert required.issubset(set(PHASE3_BASELINE_PARAMS.keys()))


class TestWFAStrategyAgnostic:
    """Verify walk-forward functions accept the strategy parameter and route via the registry."""

    def test_run_single_backtest_accepts_strategy_param(self):
        """Verify _run_single_backtest signature accepts and defaults strategy."""
        import inspect
        from backtest_engine.walk_forward import _run_single_backtest
        sig = inspect.signature(_run_single_backtest)
        assert "strategy" in sig.parameters
        assert sig.parameters["strategy"].default == "noise_boundary_intraday"

    def test_run_wfa_fold_accepts_strategy_param(self):
        """Verify run_wfa_fold signature accepts and defaults strategy."""
        import inspect
        from backtest_engine.walk_forward import run_wfa_fold
        sig = inspect.signature(run_wfa_fold)
        assert "strategy" in sig.parameters
        assert sig.parameters["strategy"].default == "noise_boundary_intraday"

    def test_run_wfa_full_accepts_strategy_param(self):
        """Verify run_wfa_full signature accepts and defaults strategy."""
        import inspect
        from backtest_engine.walk_forward import run_wfa_full
        sig = inspect.signature(run_wfa_full)
        assert "strategy" in sig.parameters
        assert sig.parameters["strategy"].default == "noise_boundary_intraday"

    def test_run_single_backtest_hma_crossover(self):
        """Run _run_single_backtest with hma_crossover to prove strategy dispatch works."""
        from backtest_engine.walk_forward import _run_single_backtest
        from backtest_engine.strategy_registry import StrategyRegistry

        # Build minimal OHLCV data
        idx = pd.date_range("2023-01-01", periods=500, freq="5min")
        np.random.seed(42)
        close = 100 + np.cumsum(np.random.randn(500) * 0.1)
        data = pd.DataFrame({
            "open": close + np.random.randn(500) * 0.05,
            "high": close + abs(np.random.randn(500) * 0.1),
            "low": close - abs(np.random.randn(500) * 0.1),
            "close": close,
            "volume": np.random.randint(100, 1000, 500).astype(float),
        }, index=idx)

        # Default HMA params
        params = {}
        result = _run_single_backtest(
            data=data,
            symbol="TEST",
            params=params,
            initial_capital=1000.0,
            timeframe_minutes=5,
            strategy="hma_crossover",
        )
        assert result is not None
        assert hasattr(result, "metrics")
        assert hasattr(result, "trades")
