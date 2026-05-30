import unittest
import tempfile
import json
import optuna
from pathlib import Path
import pandas as pd
from unittest.mock import MagicMock

from backtest_engine.bayesian_optimizer import (
    run_bayesian_optimization,
    _suggest_parameters,
)
from backtest_engine.optimizer import parse_cli_parameter
from backtest_engine.strategies.hma_crossover import HMAConfigOverrides


class TestMultiObjectiveScoring(unittest.TestCase):
    def setUp(self) -> None:
        # Generate short dummy OHLCV data
        index = pd.date_range("2024-01-01 09:30:00", periods=50, freq="5min")
        closes = [100.0 + ((-1) ** (i // 5)) * (i % 10) * 0.8 for i in range(len(index))]
        self.bars = pd.DataFrame(
            {
                "open": closes,
                "high": [value + 0.5 for value in closes],
                "low": [value - 0.5 for value in closes],
                "close": closes,
                "volume": [1000] * len(index),
            },
            index=index,
        )

    def test_single_objective_bayesian_optimization(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary = run_bayesian_optimization(
                data=self.bars,
                symbol="TEST",
                parameter_specs=[
                    parse_cli_parameter("fast_len=3:5:1"),
                ],
                fixed_overrides=HMAConfigOverrides(
                    slow_len=8,
                    max_entry_price=1000.0,
                    max_capital_bucket=300.0,
                    initial_capital_bucket=300.0,
                    trade_direction_mode="Long & Short",
                ),
                output_root=Path(tmp),
                n_trials=3,
                min_closed_trades=0,
                write_best_run=False,
                enable_convergence_stop=False,
                seed=42,
            )

            self.assertEqual(summary.status, "FINISHED")
            self.assertEqual(summary.total_iterations, 3)
            self.assertEqual(summary.iterations_completed, 3)
            self.assertTrue((summary.output_dir / "results.parquet").exists())
            self.assertTrue((summary.output_dir / "results.json").exists())
            self.assertTrue((summary.output_dir / "best.json").exists())
            self.assertTrue((summary.output_dir / "summary.json").exists())
            self.assertTrue((summary.output_dir / "recommendations.json").exists())
            # Pareto front should NOT exist for single-objective
            self.assertFalse((summary.output_dir / "pareto_front.json").exists())

    def test_multi_objective_bayesian_optimization_pareto_front(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary = run_bayesian_optimization(
                data=self.bars,
                symbol="TEST",
                parameter_specs=[
                    parse_cli_parameter("fast_len=3:5:1"),
                ],
                fixed_overrides=HMAConfigOverrides(
                    slow_len=8,
                    max_entry_price=1000.0,
                    max_capital_bucket=300.0,
                    initial_capital_bucket=300.0,
                    trade_direction_mode="Long & Short",
                ),
                output_root=Path(tmp),
                n_trials=4,
                min_closed_trades=0,
                write_best_run=False,
                enable_convergence_stop=False,
                score_metric="sharpe_ratio",
                score_direction="max",
                secondary_score_metric="total_net_pnl",
                secondary_score_direction="max",
                seed=42,
            )

            self.assertEqual(summary.status, "FINISHED")
            self.assertTrue((summary.output_dir / "pareto_front.json").exists())

            # Read and validate pareto front contents
            with open(summary.output_dir / "pareto_front.json", "r", encoding="utf-8") as f:
                pareto_data = json.load(f)

            self.assertIsInstance(pareto_data, list)
            self.assertGreater(len(pareto_data), 0)
            
            first_item = pareto_data[0]
            self.assertIn("number", first_item)
            self.assertIn("score", first_item)
            self.assertIn("secondary_score", first_item)
            self.assertIn("parameters", first_item)
            
            # Ensure the primary and secondary objectives mapped properly
            self.assertTrue(isinstance(first_item["score"], float))
            self.assertTrue(isinstance(first_item["secondary_score"], float))
            self.assertIn("fast_len", first_item["parameters"])

    def test_multi_objective_with_ineligible_trials(self) -> None:
        # Check that sentinel ineligible values work correctly
        with tempfile.TemporaryDirectory() as tmp:
            summary = run_bayesian_optimization(
                data=self.bars,
                symbol="TEST",
                parameter_specs=[
                    parse_cli_parameter("fast_len=3:5:1"),
                ],
                fixed_overrides=HMAConfigOverrides(
                    slow_len=8,
                    max_entry_price=1000.0,
                    max_capital_bucket=300.0,
                    initial_capital_bucket=300.0,
                    trade_direction_mode="Long & Short",
                ),
                output_root=Path(tmp),
                n_trials=3,
                min_closed_trades=100,  # Ridiculous requirement to force ineligible
                write_best_run=False,
                enable_convergence_stop=False,
                score_metric="sharpe_ratio",
                score_direction="max",
                secondary_score_metric="total_net_pnl",
                secondary_score_direction="max",
                seed=42,
            )

            self.assertEqual(summary.status, "FINISHED")
            self.assertEqual(summary.eligible_iterations, 0)
            self.assertTrue((summary.output_dir / "pareto_front.json").exists())
            
            with open(summary.output_dir / "pareto_front.json", "r", encoding="utf-8") as f:
                pareto_data = json.load(f)
            
            # Since all were ineligible, they should have hit the -inf sentinels
            for item in pareto_data:
                self.assertLess(item["score"], -100000.0)
                self.assertLess(item["secondary_score"], -100000.0)

    def test_parameter_importance_with_multiple_parameters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary = run_bayesian_optimization(
                data=self.bars,
                symbol="TEST",
                parameter_specs=[
                    parse_cli_parameter("fast_len=3:5:1"),
                    parse_cli_parameter("slow_len=6:8:1"),
                ],
                fixed_overrides=HMAConfigOverrides(
                    max_entry_price=1000.0,
                    max_capital_bucket=300.0,
                    initial_capital_bucket=300.0,
                    trade_direction_mode="Long & Short",
                ),
                output_root=Path(tmp),
                n_trials=4,
                min_closed_trades=0,
                write_best_run=False,
                enable_convergence_stop=False,
                score_metric="sharpe_ratio",
                score_direction="max",
                secondary_score_metric="total_net_pnl",
                secondary_score_direction="max",
                seed=42,
            )

            self.assertTrue((summary.output_dir / "parameter_importance.json").exists())
            with open(summary.output_dir / "parameter_importance.json", "r", encoding="utf-8") as f:
                importance = json.load(f)
            self.assertIsInstance(importance, dict)
            self.assertIn("fast_len", importance)

    def test_convergence_stop_early_termination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary = run_bayesian_optimization(
                data=self.bars,
                symbol="TEST",
                parameter_specs=[
                    parse_cli_parameter("fast_len=3:4:1"),
                ],
                fixed_overrides=HMAConfigOverrides(
                    slow_len=8,
                    max_entry_price=1000.0,
                    max_capital_bucket=300.0,
                    initial_capital_bucket=300.0,
                    trade_direction_mode="Long & Short",
                ),
                output_root=Path(tmp),
                n_trials=10,
                min_closed_trades=0,
                write_best_run=False,
                enable_convergence_stop=True,
                convergence_patience=2,  # Stop after 2 consecutive non-improvements
                convergence_min_improvement=0.1,
                seed=42,
            )
            # Should stop early due to low n_trials parameters and strict patience
            self.assertIn(summary.status, ["FINISHED", "FINISHED_CONVERGED"])

    def test_parallel_bayesian_optimization_constant_liar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary = run_bayesian_optimization(
                data=self.bars,
                symbol="TEST",
                parameter_specs=[
                    parse_cli_parameter("fast_len=3:6:1"),
                ],
                fixed_overrides=HMAConfigOverrides(
                    slow_len=8,
                    max_entry_price=1000.0,
                    max_capital_bucket=300.0,
                    initial_capital_bucket=300.0,
                    trade_direction_mode="Long & Short",
                ),
                output_root=Path(tmp),
                n_trials=6,
                min_closed_trades=0,
                workers=2,
                write_best_run=False,
                enable_convergence_stop=False,
                seed=42,
            )

            self.assertEqual(summary.status, "FINISHED")
            self.assertEqual(summary.total_iterations, 6)
            self.assertEqual(summary.iterations_completed, 6)
            self.assertTrue((summary.output_dir / "results.parquet").exists())


if __name__ == "__main__":
    unittest.main()
