from __future__ import annotations

import unittest
from pathlib import Path
import numpy as np
import pandas as pd

from backtest_engine.bayesian_optimizer import run_bayesian_optimization
from backtest_engine.optimizer import ParameterGridSpec, OptimizationProgress
from backtest_engine.strategies.hma_crossover import HMAConfigOverrides


class TestConvergenceStatus(unittest.TestCase):
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

    def test_convergence_status_propagation(self) -> None:
        """Verify that OptimizationProgress correctly includes and propagates convergence_status."""
        parameter_specs = [
            ParameterGridSpec("fast_len", "numeric", (5, 6)),
            ParameterGridSpec("slow_len", "numeric", (15, 16)),
        ]

        received_progresses = []

        def progress_callback(progress: OptimizationProgress) -> None:
            received_progresses.append(progress)

        summary = run_bayesian_optimization(
            data=self.data,
            symbol="TEST",
            parameter_specs=parameter_specs,
            fixed_overrides=HMAConfigOverrides(
                confirm_on_close=True,
                initial_capital_bucket=1000.0,
                max_capital_bucket=1000.0,
            ),
            output_root=Path("/tmp/hp_opt_test_convergence"),
            n_trials=5,
            min_closed_trades=0,
            workers=1,
            write_best_run=False,
            enable_convergence_stop=True,
            convergence_patience=10,
            progress_callback=progress_callback,
            seed=42,
        )

        self.assertGreater(len(received_progresses), 0)
        
        for progress in received_progresses:
            self.assertIsNotNone(progress.convergence_status)
            self.assertIn("iterations_since_improvement", progress.convergence_status)
            self.assertIn("total_iterations_since_improvement", progress.convergence_status)
            self.assertIn("circuit_breaker_threshold", progress.convergence_status)
            self.assertIn("patience", progress.convergence_status)
            self.assertEqual(progress.convergence_status["patience"], 10)
            self.assertIn("best_score", progress.convergence_status)
            self.assertIn("current_window_size", progress.convergence_status)
            
            # Print for confirmation
            print(f"Iteration {progress.current_iteration}: convergenceStatus = {progress.convergence_status}")


class TestConvergenceTrackerCircuitBreaker(unittest.TestCase):
    def test_circuit_breaker_triggers(self) -> None:
        """Verify that the circuit breaker triggers when total iterations without improvement crosses the ratio of the budget."""
        from backtest_engine.bayesian_optimizer import ConvergenceTracker
        tracker = ConvergenceTracker(
            score_direction="max",
            patience=50,
            min_relative_improvement=0.01,
            window_size=10,
            window_count=3,
            n_trials=100,
            circuit_breaker_ratio=0.2, # 20 iterations threshold
        )

        # Iteration 1: initial score
        should_stop, reason = tracker.update(10.0)
        self.assertFalse(should_stop)
        self.assertEqual(reason, "")
        self.assertEqual(tracker.total_iterations_since_improvement, 0)
        self.assertEqual(tracker.iterations_since_improvement, 0)

        # Iterations 2-20: 19 ineligible/failed iterations (represented by None score)
        # Total iterations since last improvement will become 19
        for _ in range(19):
            should_stop, reason = tracker.update(None)
            self.assertFalse(should_stop)
            self.assertEqual(reason, "")

        # Iteration 21: one more None score. Total iterations since improvement becomes 20 (>= threshold 100 * 0.2)
        # Since iterations_since_improvement (0) < patience (50), circuit breaker should trigger!
        should_stop, reason = tracker.update(None)
        self.assertTrue(should_stop)
        self.assertEqual(reason, "circuit_breaker")
        self.assertEqual(tracker.total_iterations_since_improvement, 20)
        self.assertEqual(tracker.iterations_since_improvement, 0)

    def test_circuit_breaker_resets_on_new_best(self) -> None:
        """Verify that total_iterations_since_improvement resets correctly when a new best is found."""
        from backtest_engine.bayesian_optimizer import ConvergenceTracker
        tracker = ConvergenceTracker(
            score_direction="max",
            patience=50,
            min_relative_improvement=0.01,
            window_size=10,
            window_count=3,
            n_trials=100,
            circuit_breaker_ratio=0.2, # 20 iterations threshold
        )

        tracker.update(10.0) # Reset total_iterations_since_improvement to 0

        # 10 ineligible iterations
        for _ in range(10):
            tracker.update(None)
        self.assertEqual(tracker.total_iterations_since_improvement, 10)

        # New best score found!
        should_stop, reason = tracker.update(12.0)
        self.assertFalse(should_stop)
        self.assertEqual(reason, "")
        self.assertEqual(tracker.total_iterations_since_improvement, 0)
        self.assertEqual(tracker.iterations_since_improvement, 0)

    def test_circuit_breaker_does_not_trigger_if_patience_reached(self) -> None:
        """Verify that classic patience stopping takes precedence when iterations_since_improvement >= patience."""
        from backtest_engine.bayesian_optimizer import ConvergenceTracker
        tracker = ConvergenceTracker(
            score_direction="max",
            patience=5,
            min_relative_improvement=0.01,
            window_size=10,
            window_count=3,
            n_trials=100,
            circuit_breaker_ratio=0.2, # 20 iterations threshold
        )

        tracker.update(10.0)

        # 4 iterations without improvement (eligible)
        for _ in range(4):
            should_stop, reason = tracker.update(9.0)
            self.assertFalse(should_stop)

        # 5th iteration without improvement: patience is reached (5 >= patience 5)
        # Even though total_iterations_since_improvement is only 5 (which is < threshold 20),
        # classic patience stopping triggers.
        should_stop, reason = tracker.update(9.0)
        self.assertTrue(should_stop)
        self.assertEqual(reason, "patience")


if __name__ == "__main__":
    unittest.main()
