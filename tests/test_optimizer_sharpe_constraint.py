import unittest
import pandas as pd
import numpy as np
from backtest_engine.optimizer import _evaluate_hma_parameters, ParameterGridSpec

class TestOptimizerSharpeConstraint(unittest.TestCase):
    def test_noise_boundary_sharpe_constraint_low_sharpe(self) -> None:
        # Create a tiny mock dataset
        dates = pd.date_range("2026-05-01 09:30:00", periods=50, freq="5min")
        data = pd.DataFrame(
            {
                "open": [100.0] * 50,
                "high": [100.5] * 50,
                "low": [99.5] * 50,
                "close": [100.0] * 50,
                "volume": [1000.0] * 50,
            },
            index=dates,
        )
        
        parameters = {
            "lookback_days": 5,
            "volatility_multiplier_enter": 2.0,
            "volatility_multiplier_exit": 1.0,
            "target_daily_volatility": 0.01,
            "exit_mode": "time_only",
        }
        
        row, is_eligible, is_skipped = _evaluate_hma_parameters(
            data=data,
            symbol="TEST",
            parameters=parameters,
            iteration=1,
            fixed_overrides=None,
            initial_capital=1000.0,
            strategy="noise_boundary_intraday",
            score_metric="total_net_pnl",
            min_closed_trades=0,
        )
        
        # Since no trades were closed, Sharpe is None / 0, and it should be marked ineligible with status INELIGIBLE_LOW_SHARPE
        self.assertEqual(row["status"], "INELIGIBLE_LOW_SHARPE")
        self.assertIsNone(row["score"])
        self.assertFalse(is_eligible)
        self.assertTrue(is_skipped)

if __name__ == "__main__":
    unittest.main()
