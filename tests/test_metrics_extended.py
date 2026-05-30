import unittest
import pandas as pd
import numpy as np
from backtest_engine.metrics import _max_drawdown_duration_bars, compute_metrics, MetricsInput

class TestMetricsExtended(unittest.TestCase):
    def test_max_drawdown_duration_bars_basic(self):
        # No drawdown
        equity = pd.Series([100, 110, 120, 130])
        peak = equity.cummax()
        df = pd.DataFrame({"equity": equity, "peak_equity": peak})
        df["drawdown"] = df["equity"] - df["peak_equity"]
        self.assertEqual(_max_drawdown_duration_bars(df), 0)

        # Single drawdown: [100, 90, 95, 110]
        # Drawdown: [0, -10, -5, 0]
        # bars below peak: 2
        equity = pd.Series([100, 90, 95, 110])
        peak = equity.cummax()
        df = pd.DataFrame({"equity": equity, "peak_equity": peak})
        df["drawdown"] = df["equity"] - df["peak_equity"]
        self.assertEqual(_max_drawdown_duration_bars(df), 2)

        # Multiple drawdowns: [100, 90, 110, 105, 100, 115]
        # Drawdown: [0, -10, 0, -5, -10, 0]
        # Groups: [0, 1, 0, 2, 2, 0] -> Max duration is 2
        equity = pd.Series([100, 90, 110, 105, 100, 115])
        peak = equity.cummax()
        df = pd.DataFrame({"equity": equity, "peak_equity": peak})
        df["drawdown"] = df["equity"] - df["peak_equity"]
        self.assertEqual(_max_drawdown_duration_bars(df), 2)

    def test_compute_metrics_mdd_period(self):
        # Create a mock backtest result
        dates = pd.date_range("2023-01-01", periods=10, freq="D")
        bars = pd.DataFrame({
            "open": [100]*10, "high": [105]*10, "low": [95]*10, "close": [100]*10
        }, index=dates)
        
        # State with a specific realized PnL to create drawdown
        # Initial 1000. Realized: 0, -100, 0, 100, 0, ...
        # Equity: 1000, 900, 900, 1000, 1000, ...
        # Drawdown: 0, -100, -100, 0, 0, ...
        # Duration: 2 bars
        state = pd.DataFrame({
            "realized_net_pnl_on_fill": [0, -100, 0, 100, 0, 0, 0, 0, 0, 0],
            "estimated_net_if_closed_now": [0]*10
        }, index=dates)
        
        trades = pd.DataFrame(columns=["net_pnl", "bars_held"])
        
        payload = MetricsInput(
            symbol="TEST",
            strategy="TEST",
            initial_capital=1000.0,
            bars=bars,
            state=state,
            trades=trades,
            timeframe_minutes=1440
        )
        
        metrics, _ = compute_metrics(payload)
        
        self.assertEqual(metrics["max_drawdown_period_bars"], 2)
        # 10 days total. 2 bars in drawdown out of 10.
        # Elapsed days = 9.0 (from 1st to 10th)
        # Result: (2 / 10) * 9.0 = 1.8 days
        self.assertAlmostEqual(metrics["max_drawdown_period_days"], 1.8)

if __name__ == "__main__":
    unittest.main()
