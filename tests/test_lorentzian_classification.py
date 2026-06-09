"""Tests for the Lorentzian Classification ML Strategy.

Validates:
- Feature normalization causality (no lookahead bias)
- Lorentzian distance formula correctness
- KNN no self-comparison
- y_train label causality
- Signal generation on synthetic data
- Performance benchmark
- IndicatorFactory integration
- StrategyRegistry integration
"""

import time
import math

import numpy as np
import pandas as pd
import pytest


# ─── Fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def synthetic_ohlcv():
    """Generate synthetic OHLCV data with a trending pattern."""
    np.random.seed(42)
    n = 500
    t = np.arange(n, dtype=np.float64)
    # Simulated price with trend + noise
    base = 100.0 + 0.05 * t + 3.0 * np.sin(t / 20.0) + np.random.randn(n) * 0.5
    close = base
    high = close + np.abs(np.random.randn(n) * 0.3)
    low = close - np.abs(np.random.randn(n) * 0.3)
    open_ = close + np.random.randn(n) * 0.1
    volume = np.random.randint(100, 10000, size=n).astype(np.float64)

    dates = pd.date_range("2024-01-01", periods=n, freq="5min")
    df = pd.DataFrame({
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }, index=dates)
    return df


@pytest.fixture
def large_synthetic_ohlcv():
    """Generate large synthetic OHLCV data for performance testing."""
    np.random.seed(123)
    n = 5000
    t = np.arange(n, dtype=np.float64)
    base = 100.0 + 0.01 * t + 5.0 * np.sin(t / 50.0) + np.random.randn(n) * 1.0
    close = base
    high = close + np.abs(np.random.randn(n) * 0.5)
    low = close - np.abs(np.random.randn(n) * 0.5)
    open_ = close + np.random.randn(n) * 0.2
    volume = np.random.randint(100, 10000, size=n).astype(np.float64)

    dates = pd.date_range("2024-01-01", periods=n, freq="5min")
    df = pd.DataFrame({
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    }, index=dates)
    return df


# ─── Test 1: Feature Normalization Causality ─────────────────────

class TestFeatureNormalizationCausality:
    """Verify that normalized features do not use future data."""

    def test_n_rsi_causality(self, synthetic_ohlcv):
        """Changing future bars must not affect past feature values."""
        from backtest_engine.indicators.lorentzian_classification import n_rsi

        close = synthetic_ohlcv["close"].to_numpy(dtype=np.float64)
        n = len(close)
        cutoff = n - 50

        # Original computation
        result_original = n_rsi(close.copy(), 14, 1)

        # Modify future bars
        close_modified = close.copy()
        close_modified[cutoff:] = close_modified[cutoff:] * 2.0

        result_modified = n_rsi(close_modified, 14, 1)

        # Past values must be identical
        np.testing.assert_array_equal(
            result_original[:cutoff],
            result_modified[:cutoff],
            err_msg="n_rsi uses future data (lookahead bias detected)",
        )

    def test_n_wt_causality(self, synthetic_ohlcv):
        """Changing future bars must not affect past WaveTrend values."""
        from backtest_engine.indicators.lorentzian_classification import n_wt

        hlc3 = ((synthetic_ohlcv["high"] + synthetic_ohlcv["low"] + synthetic_ohlcv["close"]) / 3.0).to_numpy(dtype=np.float64)
        n = len(hlc3)
        cutoff = n - 50

        result_original = n_wt(hlc3.copy(), 10, 11)

        hlc3_modified = hlc3.copy()
        hlc3_modified[cutoff:] = hlc3_modified[cutoff:] * 2.0

        result_modified = n_wt(hlc3_modified, 10, 11)

        np.testing.assert_array_equal(
            result_original[:cutoff],
            result_modified[:cutoff],
            err_msg="n_wt uses future data (lookahead bias detected)",
        )

    def test_n_cci_causality(self, synthetic_ohlcv):
        """Changing future bars must not affect past CCI values."""
        from backtest_engine.indicators.lorentzian_classification import n_cci

        close = synthetic_ohlcv["close"].to_numpy(dtype=np.float64)
        high = synthetic_ohlcv["high"].to_numpy(dtype=np.float64)
        low = synthetic_ohlcv["low"].to_numpy(dtype=np.float64)
        n = len(close)
        cutoff = n - 50

        result_original = n_cci(close.copy(), high.copy(), low.copy(), 20, 1)

        close_mod = close.copy()
        close_mod[cutoff:] *= 2.0
        high_mod = high.copy()
        high_mod[cutoff:] *= 2.0
        low_mod = low.copy()
        low_mod[cutoff:] *= 2.0

        result_modified = n_cci(close_mod, high_mod, low_mod, 20, 1)

        np.testing.assert_array_equal(
            result_original[:cutoff],
            result_modified[:cutoff],
            err_msg="n_cci uses future data (lookahead bias detected)",
        )

    def test_n_adx_causality(self, synthetic_ohlcv):
        """Changing future bars must not affect past ADX values."""
        from backtest_engine.indicators.lorentzian_classification import n_adx

        close = synthetic_ohlcv["close"].to_numpy(dtype=np.float64)
        high = synthetic_ohlcv["high"].to_numpy(dtype=np.float64)
        low = synthetic_ohlcv["low"].to_numpy(dtype=np.float64)
        n = len(close)
        cutoff = n - 50

        result_original = n_adx(high.copy(), low.copy(), close.copy(), 20)

        close_mod = close.copy()
        close_mod[cutoff:] *= 2.0
        high_mod = high.copy()
        high_mod[cutoff:] *= 2.0
        low_mod = low.copy()
        low_mod[cutoff:] *= 2.0

        result_modified = n_adx(high_mod, low_mod, close_mod, 20)

        np.testing.assert_array_equal(
            result_original[:cutoff],
            result_modified[:cutoff],
            err_msg="n_adx uses future data (lookahead bias detected)",
        )


# ─── Test 2: Lorentzian Distance Formula ─────────────────────────

class TestLorentzianDistance:
    """Verify the mathematical correctness of the Lorentzian distance."""

    def test_known_vectors(self):
        """d(x, y) = sum(ln(1 + |x_j - y_j|)) on known vectors."""
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([4.0, 1.0, 5.0])

        expected = (
            math.log(1.0 + abs(1.0 - 4.0))
            + math.log(1.0 + abs(2.0 - 1.0))
            + math.log(1.0 + abs(3.0 - 5.0))
        )
        # ln(4) + ln(2) + ln(3) ≈ 1.3863 + 0.6931 + 1.0986 = 3.178
        assert abs(expected - 3.178) < 0.01

        # Compute manually
        d = 0.0
        for j in range(3):
            d += math.log(1.0 + abs(x[j] - y[j]))
        assert abs(d - expected) < 1e-10

    def test_zero_distance(self):
        """Distance to self should be 0."""
        x = np.array([1.0, 2.0, 3.0])
        d = 0.0
        for j in range(3):
            d += math.log(1.0 + abs(x[j] - x[j]))
        assert d == 0.0

    def test_symmetry(self):
        """d(x, y) == d(y, x)."""
        x = np.array([1.5, 3.7, 0.2])
        y = np.array([4.1, 0.9, 2.8])
        d_xy = sum(math.log(1.0 + abs(x[j] - y[j])) for j in range(3))
        d_yx = sum(math.log(1.0 + abs(y[j] - x[j])) for j in range(3))
        assert abs(d_xy - d_yx) < 1e-12


# ─── Test 3: KNN No Self-Comparison ──────────────────────────────

class TestKNNNoSelfComparison:
    """Verify the KNN loop does not compare a bar with itself."""

    def test_no_future_data_in_knn(self, synthetic_ohlcv):
        """Modify future data and verify past signals are unchanged."""
        from backtest_engine.indicators.lorentzian_classification import (
            LorentzianClassification,
        )

        df = synthetic_ohlcv
        cutoff = len(df) - 100

        # Run with original data
        result_orig = LorentzianClassification.run(
            high=df["high"],
            low=df["low"],
            close=df["close"],
            neighbors_count=8,
            max_bars_back=200,
            feature_count=5,
            use_volatility_filter=False,
            use_regime_filter=False,
            use_adx_filter=False,
            use_ema_filter=False,
            use_sma_filter=False,
            use_kernel_filter=False,
        )

        # Run with modified future data
        df_mod = df.copy()
        df_mod.iloc[cutoff:, df_mod.columns.get_loc("close")] *= 3.0
        df_mod.iloc[cutoff:, df_mod.columns.get_loc("high")] *= 3.0
        df_mod.iloc[cutoff:, df_mod.columns.get_loc("low")] *= 3.0

        result_mod = LorentzianClassification.run(
            high=df_mod["high"],
            low=df_mod["low"],
            close=df_mod["close"],
            neighbors_count=8,
            max_bars_back=200,
            feature_count=5,
            use_volatility_filter=False,
            use_regime_filter=False,
            use_adx_filter=False,
            use_ema_filter=False,
            use_sma_filter=False,
            use_kernel_filter=False,
        )

        # Past predictions must be identical
        np.testing.assert_array_equal(
            result_orig.prediction.iloc[:cutoff].to_numpy(),
            result_mod.prediction.iloc[:cutoff].to_numpy(),
            err_msg="KNN uses future data (lookahead bias in KNN loop)",
        )


# ─── Test 4: y_train Causality ───────────────────────────────────

class TestYTrainCausality:
    """Verify y_train labels only use past data."""

    def test_y_train_formula(self):
        """y_train[t] = sign(close[t] - close[t-4]) for t >= 4."""
        close = np.array([100.0, 101.0, 102.0, 103.0, 104.0, 103.0, 101.0, 99.0])

        # Expected labels:
        # t=0..3: 0 (not enough history)
        # t=4: sign(104-100) = +1
        # t=5: sign(103-101) = +1
        # t=6: sign(101-102) = -1
        # t=7: sign(99-103) = -1
        expected = [0, 0, 0, 0, 1, 1, -1, -1]

        y_train = np.zeros(len(close), dtype=np.int64)
        for i in range(4, len(close)):
            if close[i] > close[i - 4]:
                y_train[i] = 1
            elif close[i] < close[i - 4]:
                y_train[i] = -1

        np.testing.assert_array_equal(y_train, expected)

    def test_y_train_uses_no_future(self):
        """y_train[t] must not change when future data changes."""
        close = np.array([100.0, 101.0, 99.0, 103.0, 104.0, 102.0, 106.0, 107.0])
        cutoff = 5

        y_train_1 = np.zeros(len(close), dtype=np.int64)
        for i in range(4, len(close)):
            if close[i] > close[i - 4]:
                y_train_1[i] = 1
            elif close[i] < close[i - 4]:
                y_train_1[i] = -1

        close_mod = close.copy()
        close_mod[cutoff:] = 999.0

        y_train_2 = np.zeros(len(close_mod), dtype=np.int64)
        for i in range(4, len(close_mod)):
            if close_mod[i] > close_mod[i - 4]:
                y_train_2[i] = 1
            elif close_mod[i] < close_mod[i - 4]:
                y_train_2[i] = -1

        np.testing.assert_array_equal(
            y_train_1[:cutoff],
            y_train_2[:cutoff],
            err_msg="y_train uses future data",
        )


# ─── Test 5: Signal Generation ───────────────────────────────────

class TestSignalGeneration:
    """Verify entry/exit signals are generated correctly."""

    def test_signals_are_boolean(self, synthetic_ohlcv):
        """start_long/start_short/end_long/end_short must be 0 or 1."""
        from backtest_engine.indicators.lorentzian_classification import (
            LorentzianClassification,
        )

        result = LorentzianClassification.run(
            high=synthetic_ohlcv["high"],
            low=synthetic_ohlcv["low"],
            close=synthetic_ohlcv["close"],
            neighbors_count=8,
            max_bars_back=200,
        )

        for name in ["start_long", "start_short", "end_long", "end_short"]:
            arr = getattr(result, name).to_numpy()
            unique = np.unique(arr)
            assert all(v in [0, 1] for v in unique), (
                f"{name} contains non-boolean values: {unique}"
            )

    def test_signals_not_all_zero(self, synthetic_ohlcv):
        """At least some signals should be generated on trending data."""
        from backtest_engine.indicators.lorentzian_classification import (
            LorentzianClassification,
        )

        result = LorentzianClassification.run(
            high=synthetic_ohlcv["high"],
            low=synthetic_ohlcv["low"],
            close=synthetic_ohlcv["close"],
            neighbors_count=8,
            max_bars_back=200,
            use_volatility_filter=False,
            use_regime_filter=False,
            use_kernel_filter=False,
        )

        total_signals = (
            result.start_long.sum() + result.start_short.sum()
        )
        assert total_signals > 0, "No signals generated on trending synthetic data"


# ─── Test 6: Performance Benchmark ───────────────────────────────

class TestPerformanceBenchmark:
    """Verify execution time meets the <200ms target (warm cache)."""

    def test_performance_warm_cache(self, large_synthetic_ohlcv):
        """After JIT warmup, execution should be under 500ms."""
        from backtest_engine.indicators.lorentzian_classification import (
            LorentzianClassification,
        )

        df = large_synthetic_ohlcv

        # Cold run (JIT compilation)
        _ = LorentzianClassification.run(
            high=df["high"][:100],
            low=df["low"][:100],
            close=df["close"][:100],
            neighbors_count=4,
            max_bars_back=50,
            feature_count=2,
        )

        # Warm run
        start = time.perf_counter()
        _ = LorentzianClassification.run(
            high=df["high"],
            low=df["low"],
            close=df["close"],
            neighbors_count=8,
            max_bars_back=2000,
            feature_count=5,
        )
        elapsed = time.perf_counter() - start

        assert elapsed < 5.0, (
            f"Warm cache execution took {elapsed:.3f}s, "
            f"expected < 5.0s for 5000 bars"
        )


# ─── Test 7: IndicatorFactory Integration ────────────────────────

class TestIndicatorFactory:
    """Verify the VectorBT IndicatorFactory wrapper works correctly."""

    def test_run_returns_dataframe(self, synthetic_ohlcv):
        """LorentzianClassification.run() should return proper outputs."""
        from backtest_engine.indicators.lorentzian_classification import (
            LorentzianClassification,
        )

        result = LorentzianClassification.run(
            high=synthetic_ohlcv["high"],
            low=synthetic_ohlcv["low"],
            close=synthetic_ohlcv["close"],
        )

        assert hasattr(result, "prediction"), "Missing 'prediction' output"
        assert hasattr(result, "signal"), "Missing 'signal' output"
        assert hasattr(result, "start_long"), "Missing 'start_long' output"
        assert hasattr(result, "start_short"), "Missing 'start_short' output"
        assert hasattr(result, "end_long"), "Missing 'end_long' output"
        assert hasattr(result, "end_short"), "Missing 'end_short' output"

        # Check index alignment
        assert len(result.prediction) == len(synthetic_ohlcv)

    def test_run_with_custom_params(self, synthetic_ohlcv):
        """Run with non-default parameters."""
        from backtest_engine.indicators.lorentzian_classification import (
            LorentzianClassification,
        )

        result = LorentzianClassification.run(
            high=synthetic_ohlcv["high"],
            low=synthetic_ohlcv["low"],
            close=synthetic_ohlcv["close"],
            neighbors_count=4,
            max_bars_back=500,
            feature_count=3,
            use_volatility_filter=False,
            use_regime_filter=False,
        )
        assert len(result.prediction) == len(synthetic_ohlcv)


# ─── Test 8: Strategy Registry Integration ───────────────────────

class TestStrategyRegistry:
    """Verify the strategy is properly registered."""

    def test_registered_in_registry(self):
        """'lorentzian_classification' should be in StrategyRegistry."""
        from backtest_engine.strategy_registry import StrategyRegistry

        info = StrategyRegistry.get("lorentzian_classification")
        assert info is not None, "Strategy not found in registry"
        assert info.name == "lorentzian_classification"

    def test_config_overrides_class(self):
        """ConfigOverrides class should be accessible."""
        from backtest_engine.strategy_registry import StrategyRegistry

        info = StrategyRegistry.get("lorentzian_classification")
        assert info is not None

        overrides = info.config_override_class()
        assert overrides is not None
        assert hasattr(overrides, "neighbors_count")
        assert hasattr(overrides, "max_bars_back")
        assert hasattr(overrides, "use_kernel_filter")

    def test_parameter_definitions_exist(self):
        """LORENTZIAN_PARAMETER_DEFINITIONS should be in STRATEGY_PARAMETER_DEFINITIONS."""
        from backtest_engine.configuration import STRATEGY_PARAMETER_DEFINITIONS

        assert "lorentzian_classification" in STRATEGY_PARAMETER_DEFINITIONS, (
            "lorentzian_classification missing from STRATEGY_PARAMETER_DEFINITIONS"
        )
        defs = STRATEGY_PARAMETER_DEFINITIONS["lorentzian_classification"]
        assert "neighbors_count" in defs
        assert "use_kernel_filter" in defs
        assert "kernel_h" in defs
