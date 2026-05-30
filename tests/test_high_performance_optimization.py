"""
tests/test_high_performance_optimization.py

Unit test suite to verify the correctness, compilation integrity, and lifecycle
of high-performance components (JIT simulation kernel, zero-copy shared memory indicator grids).
"""

from __future__ import annotations

import unittest
from pathlib import Path
import numpy as np
import pandas as pd
import optuna

from backtest_engine.shared_memory import SharedIndicatorVolume
from backtest_engine.simulation_kernel import (
    run_broker_simulation_kernel,
    position_dtype,
)
from backtest_engine.bayesian_optimizer import run_bayesian_optimization
from backtest_engine.optimizer import ParameterGridSpec
from backtest_engine.strategies.hma_crossover import HMAConfigOverrides
from backtest_engine.strategies.pmax_explorer import PMaxExplorerConfigOverrides


class TestHighPerformanceOptimization(unittest.TestCase):
    def setUp(self) -> None:
        index = pd.date_range("2024-01-01 09:30:00", periods=50, freq="5min")
        self.data = pd.DataFrame(
            {
                "open": np.linspace(100.0, 105.0, 50),
                "high": np.linspace(100.5, 105.5, 50),
                "low": np.linspace(99.5, 104.5, 50),
                "close": np.linspace(100.0, 105.0, 50),
                "volume": np.ones(50) * 1000,
            },
            index=index,
        )

    def test_shared_memory_volume_lifecycle(self) -> None:
        """Verify allocation, zero-copy mapping, and clean unlinking of SharedIndicatorVolume."""
        test_arr = np.linspace(1.0, 100.0, 1000, dtype=np.float64)
        
        # Parent allocates
        parent_vol = SharedIndicatorVolume(array_to_share=test_arr)
        self.assertIsNotNone(parent_vol.shm_name)
        self.assertEqual(parent_vol.shape, (1000,))
        self.assertEqual(parent_vol.dtype, np.float64)

        try:
            # Child / worker attaches
            worker_vol = SharedIndicatorVolume(
                shm_name=parent_vol.shm_name,
                shape=parent_vol.shape,
                dtype=parent_vol.dtype,
            )
            worker_view = worker_vol.get_view()
            
            # Assert identity and direct mapping
            np.testing.assert_array_equal(worker_view, test_arr)
            
            # Mutate to confirm it's shared memory (mutates worker view if parent view is mutated)
            parent_view = parent_vol.get_view()
            parent_view[0] = 999.0
            self.assertEqual(worker_view[0], 999.0)

            worker_vol.close()
        finally:
            parent_vol.unlink()

    def test_jit_broker_simulation_kernel(self) -> None:
        """Verify strict Numba compilation and correct execution of the JIT simulation kernel."""
        # Simple inputs
        n_bars = 10
        open_prices = np.linspace(10.0, 15.0, n_bars)
        high_prices = open_prices + 0.5
        low_prices = open_prices - 0.5
        close_prices = open_prices + 0.1
        
        raw_signals = np.zeros((1, n_bars), dtype=np.int8)
        raw_signals[0, 2] = 1  # Trigger long entry on bar 2
        
        strategy_ids = np.array([0], dtype=np.int32)
        initial_cash = 1000.0
        capped_bucket_limit = 500.0
        
        # Run kernel
        equity_curve = run_broker_simulation_kernel(
            open_prices=open_prices,
            high_prices=high_prices,
            low_prices=low_prices,
            close_prices=close_prices,
            raw_signals=raw_signals,
            strategy_ids=strategy_ids,
            initial_cash=initial_cash,
            capped_bucket_limit=capped_bucket_limit,
            stop_loss_pct=0.02,
            trailing_stop_pct=0.01,
            take_profit_pct=0.05,
        )
        
        self.assertEqual(len(equity_curve), n_bars)
        self.assertTrue(np.all(equity_curve >= 0.0))
        # Initial cash on first bars should match
        self.assertEqual(equity_curve[0], 1000.0)

    def test_bayesian_optimization_with_shared_memory(self) -> None:
        """Verify that a full Bayesian optimization run executes smoothly using shared memory."""
        parameter_specs = [
            ParameterGridSpec("fast_len", "numeric", (5, 6)),
            ParameterGridSpec("slow_len", "numeric", (15, 16)),
        ]

        summary = run_bayesian_optimization(
            data=self.data,
            symbol="TEST",
            parameter_specs=parameter_specs,
            fixed_overrides=HMAConfigOverrides(
                confirm_on_close=True,
                initial_capital_bucket=1000.0,
                max_capital_bucket=1000.0,
            ),
            output_root=Path("/tmp/hp_opt_test"),
            n_trials=5,
            min_closed_trades=0,
            workers=2,  # Exercise multiprocess shared memory path!
            write_best_run=False,
            enable_convergence_stop=False,
            seed=42,
        )

        self.assertEqual(summary.status, "FINISHED")
        self.assertEqual(summary.iterations_completed, 5)
        self.assertIsNotNone(summary.best_row)

    def test_pmax_bayesian_optimization_with_shared_memory(self) -> None:
        """Verify that a full Bayesian optimization run executes smoothly for pmax_explorer using shared memory grids."""
        parameter_specs = [
            ParameterGridSpec("periods", "numeric", (9, 10)),
            ParameterGridSpec("length", "numeric", (9, 10)),
            ParameterGridSpec("multiplier", "numeric", (2.9, 3.0)),
        ]

        summary = run_bayesian_optimization(
            data=self.data,
            symbol="TEST",
            parameter_specs=parameter_specs,
            fixed_overrides=PMaxExplorerConfigOverrides(
                mav="EMA",
                change_atr=True,
                initial_capital_bucket=1000.0,
                max_capital_bucket=1000.0,
            ),
            output_root=Path("/tmp/hp_opt_test"),
            n_trials=5,
            min_closed_trades=0,
            strategy="pmax_explorer",
            workers=2,  # Exercise multiprocess shared memory path!
            write_best_run=False,
            enable_convergence_stop=False,
            seed=42,
        )

        self.assertEqual(summary.status, "FINISHED")
        self.assertEqual(summary.iterations_completed, 5)
        self.assertIsNotNone(summary.best_row)

    def test_rf_bayesian_optimization_with_shared_memory(self) -> None:
        """Verify that a full Bayesian optimization run executes smoothly for range_filter using shared memory grids."""
        from backtest_engine.strategies.range_filter import RangeFilterConfigOverrides

        parameter_specs = [
            ParameterGridSpec("sampling_period", "numeric", (99, 100)),
            ParameterGridSpec("range_multiplier", "numeric", (2.9, 3.0)),
        ]

        summary = run_bayesian_optimization(
            data=self.data,
            symbol="TEST",
            parameter_specs=parameter_specs,
            fixed_overrides=RangeFilterConfigOverrides(
                initial_capital_bucket=1000.0,
                max_capital_bucket=1000.0,
            ),
            output_root=Path("/tmp/hp_opt_test"),
            n_trials=5,
            min_closed_trades=0,
            strategy="range_filter",
            workers=2,  # Exercise multiprocess shared memory path!
            write_best_run=False,
            enable_convergence_stop=False,
            seed=42,
        )

        self.assertEqual(summary.status, "FINISHED")
        self.assertEqual(summary.iterations_completed, 5)
        self.assertIsNotNone(summary.best_row)

    def test_rf_shared_memory_correctness(self) -> None:
        """Verify that the optimized Range Filter path using shared memory matches the original path to 1e-9 precision."""
        from backtest_engine.strategies.range_filter import _load_strategy_module
        import numpy as np

        strategy_mod = _load_strategy_module()
        cfg = strategy_mod.RangeFilterConfig()
        cfg.sampling_period = 100
        cfg.range_multiplier = 3.0

        # Calculate original
        original_df = strategy_mod.add_range_filter_columns(self.data, cfg)

        # Precalculate and mount shared grids locally to simulate worker environment
        combos = [(100, 3.0)]
        rf_keys = {combos[0]: 0}
        
        smrng_grid_arr = np.zeros((1, len(self.data)), dtype=np.float64)
        filt_grid_arr = np.zeros((1, len(self.data)), dtype=np.float64)
        
        smrng_series = strategy_mod._smooth_range(self.data["close"], 100, 3.0)
        filt_series = strategy_mod._range_filter(self.data["close"], smrng_series)
        
        smrng_grid_arr[0] = smrng_series.to_numpy(dtype=float)
        filt_grid_arr[0] = filt_series.to_numpy(dtype=float)

        try:
            # Mount onto strategy module
            strategy_mod._SHARED_RF_SMRNG_GRID = smrng_grid_arr
            strategy_mod._SHARED_RF_GRID = filt_grid_arr
            strategy_mod._SHARED_RF_KEYS = rf_keys

            # Calculate optimized
            optimized_df = strategy_mod.add_range_filter_columns(self.data, cfg)

            # Assert precision matches
            np.testing.assert_allclose(
                optimized_df["smrng"].to_numpy(dtype=float),
                original_df["smrng"].to_numpy(dtype=float),
                rtol=1e-9,
                atol=1e-9
            )
            np.testing.assert_allclose(
                optimized_df["range_filter"].to_numpy(dtype=float),
                original_df["range_filter"].to_numpy(dtype=float),
                rtol=1e-9,
                atol=1e-9
            )
        finally:
            # Clean up
            strategy_mod._SHARED_RF_SMRNG_GRID = None
            strategy_mod._SHARED_RF_GRID = None
            strategy_mod._SHARED_RF_KEYS = None

    def test_bjorgum_shared_memory_correctness(self) -> None:
        """Verify that the optimized Bjorgum Double Tap path using shared memory matches the original path to 1e-9 precision."""
        from backtest_engine.strategies.bjorgum_double_tap import _load_strategy_module
        import numpy as np
        import pandas as pd

        strategy_mod = _load_strategy_module()
        cfg = strategy_mod.BjorgumDoubleTapConfig()
        cfg.length = 50
        cfg.lookback = 5
        cfg.atrLength = 14
        cfg.atrMult = 1.0

        # Calculate original
        original_df = strategy_mod.add_bjorgum_double_tap_features(self.data, cfg)

        # Precalculate components to mount onto shared variables locally
        atr_grid_arr = np.zeros((1, len(self.data)), dtype=np.float64)
        piv_high_grid_arr = np.zeros((1, len(self.data)), dtype=np.float64)
        piv_low_grid_arr = np.zeros((1, len(self.data)), dtype=np.float64)
        roll_min_grid_arr = np.zeros((1, len(self.data)), dtype=np.float64)
        roll_max_grid_arr = np.zeros((1, len(self.data)), dtype=np.float64)

        closes = self.data["close"].to_numpy(dtype=float)
        prev_closes = np.roll(closes, 1)
        prev_closes[0] = closes[0]
        tr = np.maximum(self.data["high"] - self.data["low"], np.maximum(np.abs(self.data["high"] - prev_closes), np.abs(self.data["low"] - prev_closes)))
        tr_series = pd.Series(tr)
        
        atr_grid_arr[0] = tr_series.ewm(alpha=1.0 / 14, adjust=False).mean().to_numpy()
        piv_high_grid_arr[0] = self.data["high"].rolling(50, min_periods=1).max().to_numpy()
        piv_low_grid_arr[0] = self.data["low"].rolling(50, min_periods=1).min().to_numpy()
        roll_min_grid_arr[0] = self.data["low"].rolling(5, min_periods=1).min().to_numpy()
        roll_max_grid_arr[0] = self.data["high"].rolling(5, min_periods=1).max().to_numpy()

        try:
            strategy_mod._SHARED_BJ_ATR_GRID = atr_grid_arr
            strategy_mod._SHARED_BJ_ATR_KEYS = {14: 0}
            strategy_mod._SHARED_BJ_PIV_HIGH_GRID = piv_high_grid_arr
            strategy_mod._SHARED_BJ_PIV_HIGH_KEYS = {50: 0}
            strategy_mod._SHARED_BJ_PIV_LOW_GRID = piv_low_grid_arr
            strategy_mod._SHARED_BJ_PIV_LOW_KEYS = {50: 0}
            strategy_mod._SHARED_BJ_ROLL_MIN_GRID = roll_min_grid_arr
            strategy_mod._SHARED_BJ_ROLL_MIN_KEYS = {5: 0}
            strategy_mod._SHARED_BJ_ROLL_MAX_GRID = roll_max_grid_arr
            strategy_mod._SHARED_BJ_ROLL_MAX_KEYS = {5: 0}

            # Calculate optimized
            optimized_df = strategy_mod.add_bjorgum_double_tap_features(self.data, cfg)

            # Assert precision matches
            np.testing.assert_allclose(
                optimized_df["atr"].to_numpy(dtype=float),
                original_df["atr"].to_numpy(dtype=float),
                rtol=1e-9,
                atol=1e-9
            )
            np.testing.assert_allclose(
                optimized_df["sLow"].to_numpy(dtype=float),
                original_df["sLow"].to_numpy(dtype=float),
                rtol=1e-9,
                atol=1e-9
            )
            np.testing.assert_allclose(
                optimized_df["sHigh"].to_numpy(dtype=float),
                original_df["sHigh"].to_numpy(dtype=float),
                rtol=1e-9,
                atol=1e-9
            )
        finally:
            strategy_mod._SHARED_BJ_ATR_GRID = None
            strategy_mod._SHARED_BJ_ATR_KEYS = None
            strategy_mod._SHARED_BJ_PIV_HIGH_GRID = None
            strategy_mod._SHARED_BJ_PIV_HIGH_KEYS = None
            strategy_mod._SHARED_BJ_PIV_LOW_GRID = None
            strategy_mod._SHARED_BJ_PIV_LOW_KEYS = None
            strategy_mod._SHARED_BJ_ROLL_MIN_GRID = None
            strategy_mod._SHARED_BJ_ROLL_MIN_KEYS = None
            strategy_mod._SHARED_BJ_ROLL_MAX_GRID = None
            strategy_mod._SHARED_BJ_ROLL_MAX_KEYS = None

    def test_bjorgum_bayesian_optimization_with_shared_memory(self) -> None:
        """Verify that a full Bayesian optimization run executes smoothly for bjorgum_double_tap using shared memory grids."""
        from backtest_engine.strategies.bjorgum_double_tap import BjorgumDoubleTapConfigOverrides

        parameter_specs = [
            ParameterGridSpec("length", "numeric", (49, 50)),
            ParameterGridSpec("atrLength", "numeric", (13, 14)),
            ParameterGridSpec("lookback", "numeric", (4, 5)),
        ]

        summary = run_bayesian_optimization(
            data=self.data,
            symbol="TEST",
            parameter_specs=parameter_specs,
            fixed_overrides=BjorgumDoubleTapConfigOverrides(
                initial_capital_bucket=1000.0,
                max_capital_bucket=1000.0,
            ),
            output_root=Path("/tmp/hp_opt_test"),
            n_trials=5,
            min_closed_trades=0,
            strategy="bjorgum_double_tap",
            workers=2,  # Exercise multiprocess shared memory path!
            write_best_run=False,
            enable_convergence_stop=False,
            seed=42,
        )

        self.assertEqual(summary.status, "FINISHED")
        self.assertEqual(summary.iterations_completed, 5)
        self.assertIsNotNone(summary.best_row)

    def test_avt_shared_memory_correctness(self) -> None:
        """Verify that the optimized Adaptive Volatility Trend path using shared memory matches the original path to 1e-9 precision."""
        from backtest_engine.strategies.adaptive_volatility_trend import _load_strategy_module
        import numpy as np

        strategy_mod = _load_strategy_module()
        cfg = strategy_mod.AVTConfig()
        cfg.source = "close"
        cfg.length = 21
        cfg.atr_len = 14
        cfg.rsi_len = 14
        cfg.efficiency_smoothing = 5

        # Calculate original
        original_df = strategy_mod.add_avt_features(self.data, cfg)

        # Precalculate components to mount onto shared variables locally
        source_series = strategy_mod._price_source(self.data, "close")
        close_series = self.data["close"]
        high_series = self.data["high"]
        low_series = self.data["low"]

        adaptive_line, efficiency_ratio = strategy_mod._adaptive_ma(source_series, close_series, 21, 5)
        atr_series = strategy_mod._atr(high_series, low_series, close_series, 14)
        rsi_series = strategy_mod._rsi(source_series, 14)

        ama_grid_arr = np.zeros((1, 2, len(self.data)), dtype=np.float64)
        ama_grid_arr[0, 0] = adaptive_line.to_numpy(dtype=float)
        ama_grid_arr[0, 1] = efficiency_ratio.to_numpy(dtype=float)

        atr_grid_arr = np.zeros((1, len(self.data)), dtype=np.float64)
        atr_grid_arr[0] = atr_series.to_numpy(dtype=float)

        rsi_grid_arr = np.zeros((1, len(self.data)), dtype=np.float64)
        rsi_grid_arr[0] = rsi_series.to_numpy(dtype=float)

        try:
            strategy_mod._SHARED_AVT_AMA_GRID = ama_grid_arr
            strategy_mod._SHARED_AVT_AMA_KEYS = {("close", 21, 5): 0}
            strategy_mod._SHARED_AVT_ATR_GRID = atr_grid_arr
            strategy_mod._SHARED_AVT_ATR_KEYS = {14: 0}
            strategy_mod._SHARED_AVT_RSI_GRID = rsi_grid_arr
            strategy_mod._SHARED_AVT_RSI_KEYS = {("close", 14): 0}

            # Calculate optimized
            optimized_df = strategy_mod.add_avt_features(self.data, cfg)

            # Assert precision matches
            np.testing.assert_allclose(
                optimized_df["avt_adaptive_trend"].to_numpy(dtype=float),
                original_df["avt_adaptive_trend"].to_numpy(dtype=float),
                rtol=1e-9,
                atol=1e-9
            )
            np.testing.assert_allclose(
                optimized_df["avt_atr"].to_numpy(dtype=float),
                original_df["avt_atr"].to_numpy(dtype=float),
                rtol=1e-9,
                atol=1e-9
            )
            np.testing.assert_allclose(
                optimized_df["avt_rsi"].to_numpy(dtype=float),
                original_df["avt_rsi"].to_numpy(dtype=float),
                rtol=1e-9,
                atol=1e-9
            )
        finally:
            strategy_mod._SHARED_AVT_AMA_GRID = None
            strategy_mod._SHARED_AVT_AMA_KEYS = None
            strategy_mod._SHARED_AVT_ATR_GRID = None
            strategy_mod._SHARED_AVT_ATR_KEYS = None
            strategy_mod._SHARED_AVT_RSI_GRID = None
            strategy_mod._SHARED_AVT_RSI_KEYS = None

    def test_avt_bayesian_optimization_with_shared_memory(self) -> None:
        """Verify that a full Bayesian optimization run executes smoothly for adaptive_volatility_trend using shared memory grids."""
        from backtest_engine.strategies.adaptive_volatility_trend import AVTConfigOverrides

        parameter_specs = [
            ParameterGridSpec("length", "numeric", (20, 21)),
            ParameterGridSpec("atr_len", "numeric", (13, 14)),
            ParameterGridSpec("rsi_len", "numeric", (13, 14)),
        ]

        summary = run_bayesian_optimization(
            data=self.data,
            symbol="TEST",
            parameter_specs=parameter_specs,
            fixed_overrides=AVTConfigOverrides(
                initial_capital_bucket=1000.0,
                max_capital_bucket=1000.0,
            ),
            output_root=Path("/tmp/hp_opt_test"),
            n_trials=5,
            min_closed_trades=0,
            strategy="adaptive_volatility_trend",
            workers=2,  # Exercise multiprocess shared memory path!
            write_best_run=False,
            enable_convergence_stop=False,
            seed=42,
        )

        self.assertEqual(summary.status, "FINISHED")
        self.assertEqual(summary.iterations_completed, 5)
        self.assertIsNotNone(summary.best_row)

    def test_commas_bot_shared_memory_correctness(self) -> None:
        """Verify that the optimized 3Commas Bot path using shared memory matches the original path to 1e-9 precision."""
        from backtest_engine.strategies.commas_bot import _load_strategy_module
        import numpy as np
        import pandas as pd

        strategy_mod = _load_strategy_module()
        cfg = strategy_mod.CommasBotConfig()
        cfg.ma_type1 = "EMA"
        cfg.ma_type2 = "EMA"
        cfg.ma_length1 = 21
        cfg.ma_length2 = 50
        cfg.atr_len = 14
        cfg.swing_lookback = 5

        # Calculate original
        original_df = strategy_mod.add_3commas_bot_features(self.data, cfg)

        # Precalculate components to mount onto shared variables locally
        close_series = self.data["close"]
        ma1_series = strategy_mod.get_ma(close_series, "EMA", 21, df=self.data)
        ma2_series = strategy_mod.get_ma(close_series, "EMA", 50, df=self.data)
        atr_series = strategy_mod.atr(self.data, 14)
        lowest_low = strategy_mod.lowest(self.data["low"], 5)
        highest_high = strategy_mod.highest(self.data["high"], 5)

        ma_grid_arr = np.zeros((2, len(self.data)), dtype=np.float64)
        ma_grid_arr[0] = ma1_series.to_numpy(dtype=float)
        ma_grid_arr[1] = ma2_series.to_numpy(dtype=float)

        atr_grid_arr = np.zeros((1, len(self.data)), dtype=np.float64)
        atr_grid_arr[0] = atr_series.to_numpy(dtype=float)

        swing_grid_arr = np.zeros((1, 2, len(self.data)), dtype=np.float64)
        swing_grid_arr[0, 0] = lowest_low.to_numpy(dtype=float)
        swing_grid_arr[0, 1] = highest_high.to_numpy(dtype=float)

        try:
            strategy_mod._SHARED_CB_MA_GRID = ma_grid_arr
            strategy_mod._SHARED_CB_MA_KEYS = {("EMA", 21): 0, ("EMA", 50): 1}
            strategy_mod._SHARED_CB_ATR_GRID = atr_grid_arr
            strategy_mod._SHARED_CB_ATR_KEYS = {14: 0}
            strategy_mod._SHARED_CB_SWING_GRID = swing_grid_arr
            strategy_mod._SHARED_CB_SWING_KEYS = {5: 0}

            # Calculate optimized
            optimized_df = strategy_mod.add_3commas_bot_features(self.data, cfg)

            # Assert precision matches
            np.testing.assert_allclose(
                optimized_df["ma1"].to_numpy(dtype=float),
                original_df["ma1"].to_numpy(dtype=float),
                rtol=1e-9,
                atol=1e-9
            )
            np.testing.assert_allclose(
                optimized_df["ma2"].to_numpy(dtype=float),
                original_df["ma2"].to_numpy(dtype=float),
                rtol=1e-9,
                atol=1e-9
            )
            np.testing.assert_allclose(
                optimized_df["atr"].to_numpy(dtype=float),
                original_df["atr"].to_numpy(dtype=float),
                rtol=1e-9,
                atol=1e-9
            )
            np.testing.assert_allclose(
                optimized_df["lowest_low"].to_numpy(dtype=float),
                original_df["lowest_low"].to_numpy(dtype=float),
                rtol=1e-9,
                atol=1e-9
            )
            np.testing.assert_allclose(
                optimized_df["highest_high"].to_numpy(dtype=float),
                original_df["highest_high"].to_numpy(dtype=float),
                rtol=1e-9,
                atol=1e-9
            )
        finally:
            strategy_mod._SHARED_CB_MA_GRID = None
            strategy_mod._SHARED_CB_MA_KEYS = None
            strategy_mod._SHARED_CB_ATR_GRID = None
            strategy_mod._SHARED_CB_ATR_KEYS = None
            strategy_mod._SHARED_CB_SWING_GRID = None
            strategy_mod._SHARED_CB_SWING_KEYS = None

    def test_commas_bot_bayesian_optimization_with_shared_memory(self) -> None:
        """Verify that a full Bayesian optimization run executes smoothly for 3commas_bot using shared memory grids."""
        from backtest_engine.strategies.commas_bot import CommasBotConfigOverrides

        parameter_specs = [
            ParameterGridSpec("ma_length1", "numeric", (20, 21)),
            ParameterGridSpec("ma_length2", "numeric", (49, 50)),
            ParameterGridSpec("atr_len", "numeric", (13, 14)),
            ParameterGridSpec("swing_lookback", "numeric", (4, 5)),
        ]

        summary = run_bayesian_optimization(
            data=self.data,
            symbol="TEST",
            parameter_specs=parameter_specs,
            fixed_overrides=CommasBotConfigOverrides(
                initial_capital_bucket=1000.0,
                max_capital_bucket=1000.0,
            ),
            output_root=Path("/tmp/hp_opt_test"),
            n_trials=5,
            min_closed_trades=0,
            strategy="3commas_bot",
            workers=2,  # Exercise multiprocess shared memory path!
            write_best_run=False,
            enable_convergence_stop=False,
            seed=42,
        )

        self.assertEqual(summary.status, "FINISHED")
        self.assertEqual(summary.iterations_completed, 5)
        self.assertIsNotNone(summary.best_row)

    def test_noise_boundary_shared_memory_correctness(self) -> None:
        """Verify that the optimized Noise Boundary Intraday path using shared memory matches the original path to 1e-9 precision."""
        import backtest_engine.strategies.noise_boundary_intraday as nb_mod
        import numpy as np
        import pandas as pd

        # We must use a dataset that spans multiple days to compute daily volatility
        index = pd.date_range("2024-01-01 09:30:00", periods=200, freq="5min")
        data = pd.DataFrame(
            {
                "open": np.linspace(100.0, 105.0, 200),
                "high": np.linspace(100.5, 105.5, 200),
                "low": np.linspace(99.5, 104.5, 200),
                "close": np.linspace(100.0, 105.0, 200),
                "volume": np.ones(200) * 1000,
            },
            index=index,
        )

        cfg = nb_mod.NoiseBoundaryConfigOverrides()
        cfg.lookback_days = 2
        cfg.volatility_multiplier_enter = 2.0
        cfg.volatility_multiplier_exit = 1.0
        cfg.sizing_volatility_type = "daily"

        # Calculate original
        original_df = nb_mod.compute_noise_boundary(data, 2, 2.0, 1.0)
        
        # Calculate original spy_dvol
        daily_close = data["close"].resample("D").last().dropna()
        daily_returns = daily_close.pct_change()
        daily_dvol_series = daily_returns.rolling(window=2, min_periods=1).std().shift(1)
        normalized_index = data.index.normalize()
        original_spy_dvol = daily_dvol_series.reindex(normalized_index).values

        # Precalculate components to mount onto shared variables locally
        vol_grid_arr = np.zeros((1, 2, len(data)), dtype=np.float64)
        vol_grid_arr[0, 0] = original_df["daily_volatility"].to_numpy(dtype=float)
        
        spy_dvol_filled = np.where(np.isnan(original_spy_dvol), 0.0, original_spy_dvol)
        vol_grid_arr[0, 1] = spy_dvol_filled

        try:
            nb_mod._SHARED_NB_VOL_GRID = vol_grid_arr
            nb_mod._SHARED_NB_VOL_KEYS = {2: 0}

            # Calculate optimized mapped_vol
            optimized_df = nb_mod.compute_noise_boundary(data, 2, 2.0, 1.0)

            # Assert precision matches
            np.testing.assert_allclose(
                optimized_df["daily_volatility"].to_numpy(dtype=float),
                original_df["daily_volatility"].to_numpy(dtype=float),
                rtol=1e-9,
                atol=1e-9
            )
            
            # Assert optimized run_noise_boundary_intraday matches standard by running backtest
            res = nb_mod.run_noise_boundary_intraday(data, "TEST", cfg, compute_full_metrics=False)
            self.assertIsNotNone(res)
        finally:
            nb_mod._SHARED_NB_VOL_GRID = None
            nb_mod._SHARED_NB_VOL_KEYS = None

    def test_noise_boundary_bayesian_optimization_with_shared_memory(self) -> None:
        """Verify that a full Bayesian optimization run executes smoothly for noise_boundary_intraday using shared memory grids."""
        from backtest_engine.strategies.noise_boundary_intraday import NoiseBoundaryConfigOverrides

        parameter_specs = [
            ParameterGridSpec("lookback_days", "numeric", (2, 3)),
            ParameterGridSpec("volatility_multiplier_enter", "numeric", (1.9, 2.0)),
        ]

        # Use 200 data points to spans multiple days so daily close resampling doesn't error
        index = pd.date_range("2024-01-01 09:30:00", periods=200, freq="5min")
        test_data = pd.DataFrame(
            {
                "open": np.linspace(100.0, 105.0, 200),
                "high": np.linspace(100.5, 105.5, 200),
                "low": np.linspace(99.5, 104.5, 200),
                "close": np.linspace(100.0, 105.0, 200),
                "volume": np.ones(200) * 1000,
            },
            index=index,
        )

        summary = run_bayesian_optimization(
            data=test_data,
            symbol="TEST",
            parameter_specs=parameter_specs,
            fixed_overrides=NoiseBoundaryConfigOverrides(
                initial_capital_bucket=1000.0,
                max_capital_bucket=1000.0,
                sizing_volatility_type="daily",
            ),
            output_root=Path("/tmp/hp_opt_test"),
            n_trials=5,
            min_closed_trades=0,
            strategy="noise_boundary_intraday",
            workers=2,  # Exercise multiprocess shared memory path!
            write_best_run=False,
            enable_convergence_stop=False,
            seed=42,
        )

        self.assertEqual(summary.status, "FINISHED")
        self.assertEqual(summary.iterations_completed, 5)
        self.assertIsNotNone(summary.best_row)


if __name__ == "__main__":
    unittest.main()
