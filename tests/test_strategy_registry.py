"""Unit tests for the StrategyRegistry factory."""

from __future__ import annotations

import pytest
from dataclasses import dataclass
from typing import Any

from backtest_engine.strategy_registry import StrategyInfo, StrategyRegistry


# ──────────────────────────────────────────────────────────────────────
# Static registration sanity checks
# ──────────────────────────────────────────────────────────────────────

ALL_STRATEGY_NAMES = [
    "hma_crossover",
    "pmax_explorer",
    "adaptive_volatility_trend",
    "range_filter",
    "3commas_bot",
    "bjorgum_double_tap",
    "noise_boundary_intraday",
]


class TestStrategyRegistration:
    """Verify all 7 strategies are registered with the required fields."""

    @pytest.mark.parametrize("name", ALL_STRATEGY_NAMES)
    def test_strategy_is_registered(self, name: str) -> None:
        info = StrategyRegistry.get(name)
        assert info.name == name

    @pytest.mark.parametrize("name", ALL_STRATEGY_NAMES)
    def test_run_function_is_callable(self, name: str) -> None:
        info = StrategyRegistry.get(name)
        assert callable(info.run_function)

    @pytest.mark.parametrize("name", ALL_STRATEGY_NAMES)
    def test_config_override_class_is_dataclass(self, name: str) -> None:
        info = StrategyRegistry.get(name)
        assert hasattr(info.config_override_class, "__dataclass_fields__")

    @pytest.mark.parametrize("name", ALL_STRATEGY_NAMES)
    def test_load_overrides_function_is_callable(self, name: str) -> None:
        info = StrategyRegistry.get(name)
        assert callable(info.load_overrides_function)

    @pytest.mark.parametrize("name", ALL_STRATEGY_NAMES)
    def test_overrides_from_mapping_function_is_callable(self, name: str) -> None:
        info = StrategyRegistry.get(name)
        assert callable(info.overrides_from_mapping_function)

    @pytest.mark.parametrize("name", ALL_STRATEGY_NAMES)
    def test_indicators_is_nonempty_list(self, name: str) -> None:
        info = StrategyRegistry.get(name)
        assert isinstance(info.indicators, list)
        assert len(info.indicators) > 0

    @pytest.mark.parametrize("name", ALL_STRATEGY_NAMES)
    def test_vectorbt_prescan_is_callable_or_none(self, name: str) -> None:
        info = StrategyRegistry.get(name)
        assert info.vectorbt_prescan is None or callable(info.vectorbt_prescan)

    @pytest.mark.parametrize("name", ALL_STRATEGY_NAMES)
    def test_clear_feature_cache_is_callable_or_none(self, name: str) -> None:
        info = StrategyRegistry.get(name)
        assert info.clear_feature_cache is None or callable(info.clear_feature_cache)


class TestRegistryLookup:
    """Verify registry lookup, listing, and error handling."""

    def test_list_strategies_returns_all(self) -> None:
        names = StrategyRegistry.list_strategies()
        for expected in ALL_STRATEGY_NAMES:
            assert expected in names

    def test_all_returns_dict_of_strategy_info(self) -> None:
        all_strats = StrategyRegistry.all()
        assert isinstance(all_strats, dict)
        for name, info in all_strats.items():
            assert isinstance(info, StrategyInfo)
            assert info.name == name

    def test_get_unknown_strategy_raises(self) -> None:
        with pytest.raises(ValueError, match="not registered"):
            StrategyRegistry.get("nonexistent_strategy")


class TestOverridesFromMapping:
    """Verify overrides_from_mapping_function produces valid config objects for each strategy."""

    @pytest.mark.parametrize("name", ALL_STRATEGY_NAMES)
    def test_overrides_from_empty_mapping(self, name: str) -> None:
        info = StrategyRegistry.get(name)
        overrides = info.overrides_from_mapping_function({})
        assert overrides is not None
        # Produced object should be a dataclass instance matching the registered class
        assert isinstance(overrides, info.config_override_class)

    @pytest.mark.parametrize("name", ALL_STRATEGY_NAMES)
    def test_default_config_can_be_instantiated(self, name: str) -> None:
        info = StrategyRegistry.get(name)
        obj = info.config_override_class()
        assert obj is not None


class TestIndicatorsMapping:
    """Verify specific indicator lists for known strategies."""

    def test_hma_crossover_indicators(self) -> None:
        info = StrategyRegistry.get("hma_crossover")
        assert info.indicators == ["hma_fast", "hma_slow"]

    def test_noise_boundary_intraday_indicators(self) -> None:
        info = StrategyRegistry.get("noise_boundary_intraday")
        assert "upper_enter" in info.indicators
        assert "lower_enter" in info.indicators
        assert "daily_open" in info.indicators

    def test_bjorgum_double_tap_indicators(self) -> None:
        info = StrategyRegistry.get("bjorgum_double_tap")
        assert "sLow" in info.indicators
        assert "sHigh" in info.indicators


class TestCacheClearing:
    """Verify strategies that have cache clearing functions registered."""

    STRATEGIES_WITH_CACHE = ["hma_crossover", "pmax_explorer", "range_filter", "bjorgum_double_tap"]
    STRATEGIES_WITHOUT_CACHE = ["adaptive_volatility_trend", "3commas_bot", "noise_boundary_intraday"]

    @pytest.mark.parametrize("name", STRATEGIES_WITH_CACHE)
    def test_cache_clearing_callable(self, name: str) -> None:
        info = StrategyRegistry.get(name)
        assert info.clear_feature_cache is not None
        # Call it — it should not raise
        info.clear_feature_cache()

    @pytest.mark.parametrize("name", STRATEGIES_WITHOUT_CACHE)
    def test_no_cache_clearing(self, name: str) -> None:
        info = StrategyRegistry.get(name)
        assert info.clear_feature_cache is None


class TestPrescan:
    """Verify VectorBT prescan registration."""

    STRATEGIES_WITH_PRESCAN = ["hma_crossover", "pmax_explorer", "adaptive_volatility_trend",
                                "range_filter", "3commas_bot", "bjorgum_double_tap", "noise_boundary_intraday"]
    STRATEGIES_WITHOUT_PRESCAN = []

    @pytest.mark.parametrize("name", STRATEGIES_WITH_PRESCAN)
    def test_prescan_callable(self, name: str) -> None:
        info = StrategyRegistry.get(name)
        assert callable(info.vectorbt_prescan)

    @pytest.mark.parametrize("name", STRATEGIES_WITHOUT_PRESCAN)
    def test_no_prescan(self, name: str) -> None:
        info = StrategyRegistry.get(name)
        assert info.vectorbt_prescan is None


class TestPrescanExecution:
    """Verify that vectorbt_prescan executes and handles batching & callbacks correctly."""

    @pytest.mark.parametrize("name", TestPrescan.STRATEGIES_WITH_PRESCAN)
    def test_prescan_runs_and_calls_callback(self, name: str, tmp_path: Any) -> None:
        import pandas as pd
        import numpy as np
        from backtest_engine.optimizer import ParameterGridSpec

        # Generate mock OHLCV data
        idx = pd.date_range("2026-01-01", periods=100, freq="5min")
        data = pd.DataFrame({
            "open": np.linspace(100, 110, 100),
            "high": np.linspace(101, 111, 100),
            "low": np.linspace(99, 109, 100),
            "close": np.linspace(100, 110, 100),
            "volume": np.ones(100) * 1000
        }, index=idx)

        info = StrategyRegistry.get(name)
        assert info.vectorbt_prescan is not None

        # Build appropriate parameters for each strategy
        if name == "hma_crossover":
            specs = [
                ParameterGridSpec(name="fast_len", kind="numeric", values=(5, 6, 7)),
                ParameterGridSpec(name="slow_len", kind="numeric", values=(10, 11, 12)),
            ]
        elif name == "pmax_explorer":
            specs = [
                ParameterGridSpec(name="periods", kind="numeric", values=(5, 6)),
                ParameterGridSpec(name="multiplier", kind="numeric", values=(1.5, 2.0)),
                ParameterGridSpec(name="length", kind="numeric", values=(5, 6)),
            ]
        elif name == "adaptive_volatility_trend":
            specs = [
                ParameterGridSpec(name="length", kind="numeric", values=(5, 6)),
                ParameterGridSpec(name="atr_len", kind="numeric", values=(5, 6)),
                ParameterGridSpec(name="atr_mult", kind="numeric", values=(1.5, 2.0)),
            ]
        elif name == "range_filter":
            specs = [
                ParameterGridSpec(name="sampling_period", kind="numeric", values=(5, 6)),
                ParameterGridSpec(name="range_multiplier", kind="numeric", values=(1.5, 2.0)),
            ]
        elif name == "3commas_bot":
            specs = [
                ParameterGridSpec(name="ma_length1", kind="numeric", values=(5, 6)),
                ParameterGridSpec(name="ma_length2", kind="numeric", values=(10, 11)),
            ]
        elif name == "bjorgum_double_tap":
            specs = [
                ParameterGridSpec(name="length", kind="numeric", values=(5, 6)),
                ParameterGridSpec(name="tol", kind="numeric", values=(1.5, 2.0)),
            ]
        elif name == "noise_boundary_intraday":
            specs = [
                ParameterGridSpec(name="lookback_days", kind="numeric", values=(5, 6)),
                ParameterGridSpec(name="volatility_multiplier_enter", kind="numeric", values=(1.5, 2.0)),
                ParameterGridSpec(name="volatility_multiplier_exit", kind="numeric", values=(1.0, 1.2)),
            ]
        else:
            pytest.fail(f"Unknown strategy with pre-scan: {name}")

        callback_calls = []
        def progress_cb(current: int, total: int) -> None:
            callback_calls.append((current, total))

        # Run pre-scan
        result_specs = info.vectorbt_prescan(
            data=data,
            parameter_specs=specs,
            timeframe_minutes=5,
            output_dir=tmp_path,
            progress_callback=progress_cb
        )

        assert isinstance(result_specs, list)
        assert len(result_specs) == len(specs)
        # Verify the callback was executed
        assert len(callback_calls) > 0
        assert callback_calls[-1][0] == callback_calls[-1][1]


class TestPMaxPreScanMemoryScaling:
    """Verify memory scaling, dynamic batching, and error fallback in PMax pre-scan."""

    def test_pmax_prescan_handles_large_multiplier_list_and_batching(self, tmp_path) -> None:
        import pandas as pd
        import numpy as np
        from backtest_engine.optimizer import ParameterGridSpec

        # Generate mock OHLCV data
        idx = pd.date_range("2026-01-01", periods=50, freq="5min")
        data = pd.DataFrame({
            "open": np.linspace(100, 110, 50),
            "high": np.linspace(101, 111, 50),
            "low": np.linspace(99, 109, 50),
            "close": np.linspace(100, 110, 50),
            "volume": np.ones(50) * 1000
        }, index=idx)

        info = StrategyRegistry.get("pmax_explorer")
        assert info.vectorbt_prescan is not None

        # Build extreme parameter space (46 multiplier values)
        specs = [
            ParameterGridSpec(name="periods", kind="numeric", values=tuple(range(5, 10))),
            ParameterGridSpec(name="multiplier", kind="numeric", values=tuple(np.round(np.arange(1.0, 10.0, 0.2), 2))),
            ParameterGridSpec(name="length", kind="numeric", values=tuple(range(5, 10))),
        ]

        # Run pre-scan — should complete without errors and handle the ~46 multipliers and combos
        result_specs = info.vectorbt_prescan(
            data=data,
            parameter_specs=specs,
            timeframe_minutes=5,
            output_dir=tmp_path
        )

        assert isinstance(result_specs, list)
        assert len(result_specs) == len(specs)

    def test_pmax_prescan_handles_memory_error_gracefully(self, tmp_path, monkeypatch) -> None:
        import pandas as pd
        import numpy as np
        from backtest_engine.optimizer import ParameterGridSpec

        # Generate mock OHLCV data
        idx = pd.date_range("2026-01-01", periods=50, freq="5min")
        data = pd.DataFrame({
            "open": np.linspace(100, 110, 50),
            "high": np.linspace(101, 111, 50),
            "low": np.linspace(99, 109, 50),
            "close": np.linspace(100, 110, 50),
            "volume": np.ones(50) * 1000
        }, index=idx)

        info = StrategyRegistry.get("pmax_explorer")
        assert info.vectorbt_prescan is not None

        specs = [
            ParameterGridSpec(name="periods", kind="numeric", values=(5, 6)),
            ParameterGridSpec(name="multiplier", kind="numeric", values=(1.5, 2.0)),
            ParameterGridSpec(name="length", kind="numeric", values=(5, 6)),
        ]

        # Monkeypatch vectorbt Portfolio from_signals to raise MemoryError
        import vectorbt as vbt
        def mock_from_signals(*args, **kwargs):
            raise MemoryError("Simulated allocation failure")
        monkeypatch.setattr(vbt.Portfolio, "from_signals", mock_from_signals)

        # Run pre-scan — should fall back to unmodified specs instead of crashing
        result_specs = info.vectorbt_prescan(
            data=data,
            parameter_specs=specs,
            timeframe_minutes=5,
            output_dir=tmp_path
        )

        assert result_specs == specs


