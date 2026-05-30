import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import pandas as pd
import optuna

from backtest_engine.bayesian_optimizer import run_bayesian_optimization
from backtest_engine.optimizer import ParameterGridSpec
from backtest_engine.strategies.hma_crossover import HMAConfigOverrides


class TestBayesianSamplerSelection(unittest.TestCase):
    def setUp(self) -> None:
        index = pd.date_range("2024-01-01 09:30:00", periods=10, freq="5min")
        self.bars = pd.DataFrame(
            {
                "open": [100.0] * 10,
                "high": [100.5] * 10,
                "low": [99.5] * 10,
                "close": [100.0] * 10,
                "volume": [1000] * 10,
            },
            index=index,
        )

    @patch("optuna.create_study")
    def test_qmc_sampler_selection_pure_numeric_over_1000_trials(self, mock_create_study) -> None:
        mock_study = MagicMock()
        mock_create_study.return_value = mock_study
        
        # Pure numeric parameter specs
        parameter_specs = [
            ParameterGridSpec("fast_len", "numeric", (3, 4, 5)),
            ParameterGridSpec("slow_len", "numeric", (10, 11, 12)),
        ]
        
        try:
            run_bayesian_optimization(
                data=self.bars,
                symbol="TEST",
                parameter_specs=parameter_specs,
                fixed_overrides=HMAConfigOverrides(),
                output_root=Path("/tmp"),
                n_trials=1005,
                min_closed_trades=0,
                write_best_run=False,
                enable_convergence_stop=False,
                seed=42,
            )
        except Exception:
            # We don't care if the optimizer loops fail or exit because we only want to assert
            # the sampler passed to optuna.create_study.
            pass

        self.assertTrue(mock_create_study.called)
        kwargs = mock_create_study.call_args[1]
        sampler = kwargs.get("sampler")
        self.assertIsInstance(sampler, optuna.samplers.QMCSampler)

    @patch("optuna.create_study")
    def test_tpe_sampler_selection_pure_numeric_under_1000_trials(self, mock_create_study) -> None:
        mock_study = MagicMock()
        mock_create_study.return_value = mock_study
        
        # Pure numeric parameter specs
        parameter_specs = [
            ParameterGridSpec("fast_len", "numeric", (3, 4, 5)),
        ]
        
        try:
            run_bayesian_optimization(
                data=self.bars,
                symbol="TEST",
                parameter_specs=parameter_specs,
                fixed_overrides=HMAConfigOverrides(),
                output_root=Path("/tmp"),
                n_trials=500,
                min_closed_trades=0,
                write_best_run=False,
                enable_convergence_stop=False,
                seed=42,
            )
        except Exception:
            pass

        self.assertTrue(mock_create_study.called)
        kwargs = mock_create_study.call_args[1]
        sampler = kwargs.get("sampler")
        self.assertIsInstance(sampler, optuna.samplers.TPESampler)
        self.assertTrue(sampler._multivariate)

    @patch("optuna.create_study")
    def test_tpe_sampler_selection_with_categorical_over_1000_trials(self, mock_create_study) -> None:
        mock_study = MagicMock()
        mock_create_study.return_value = mock_study
        
        # Parameter specs containing a categorical variable
        parameter_specs = [
            ParameterGridSpec("fast_len", "numeric", (3, 4, 5)),
            ParameterGridSpec("trade_direction_mode", "choice", ("Long Only", "Short Only", "Long & Short")),
        ]
        
        try:
            run_bayesian_optimization(
                data=self.bars,
                symbol="TEST",
                parameter_specs=parameter_specs,
                fixed_overrides=HMAConfigOverrides(),
                output_root=Path("/tmp"),
                n_trials=1005,
                min_closed_trades=0,
                write_best_run=False,
                enable_convergence_stop=False,
                seed=42,
            )
        except Exception:
            pass

        self.assertTrue(mock_create_study.called)
        kwargs = mock_create_study.call_args[1]
        sampler = kwargs.get("sampler")
        self.assertIsInstance(sampler, optuna.samplers.TPESampler)
        self.assertTrue(sampler._multivariate)

    @patch("optuna.create_study")
    def test_tpe_sampler_selection_with_categorical_under_1000_trials(self, mock_create_study) -> None:
        mock_study = MagicMock()
        mock_create_study.return_value = mock_study
        
        # Parameter specs containing a categorical variable
        parameter_specs = [
            ParameterGridSpec("fast_len", "numeric", (3, 4, 5)),
            ParameterGridSpec("trade_direction_mode", "choice", ("Long Only", "Short Only")),
        ]
        
        try:
            run_bayesian_optimization(
                data=self.bars,
                symbol="TEST",
                parameter_specs=parameter_specs,
                fixed_overrides=HMAConfigOverrides(),
                output_root=Path("/tmp"),
                n_trials=500,
                min_closed_trades=0,
                write_best_run=False,
                enable_convergence_stop=False,
                seed=42,
            )
        except Exception:
            pass

        self.assertTrue(mock_create_study.called)
        kwargs = mock_create_study.call_args[1]
        sampler = kwargs.get("sampler")
        self.assertIsInstance(sampler, optuna.samplers.TPESampler)
        self.assertTrue(sampler._multivariate)


if __name__ == "__main__":
    unittest.main()
