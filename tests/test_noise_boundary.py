import unittest
import pandas as pd
import numpy as np
from backtest_engine.strategies.noise_boundary_intraday import compute_noise_boundary

class TestNoiseBoundary(unittest.TestCase):
    def test_compute_noise_boundary_logic(self):
        # Create mock intraday data for 15 days
        dates = pd.date_range("2023-01-01", periods=15, freq="D")
        intraday_indices = []
        for d in dates:
            for h in range(9, 16):
                intraday_indices.append(d + pd.Timedelta(hours=h))
        
        df = pd.DataFrame(index=intraday_indices)
        df["close"] = 100 * np.power(1.01, (df.index.day - 1))
        df["open"] = df["close"] * 0.99 # Mock open
        
        # Lookback 5 days
        lookback = 5
        multiplier_enter = 2.0
        multiplier_exit = 1.0
        
        results = compute_noise_boundary(df, lookback, multiplier_enter, multiplier_exit)
        
        # Check that results has same index
        self.assertEqual(len(results), len(df))
        self.assertTrue(results.index.equals(df.index))
        
        # Check that we have NaN for the first few days (lookback_days - 1 + 1 for shift)
        # Since we use sigma_open with min_periods = lookback_days - 1 (4), and shift by 1,
        # the first 4 days are NaN.
        # 7 bars per day. First 4 days = 28 bars should have NaNs in daily_volatility
        nan_bars = 4 * 7
        self.assertTrue(results["daily_volatility"].iloc[:nan_bars].isna().all())
        
        # Check that daily_open is correct (anchored to first bar of day)
        sample_day = dates[10].date()
        day_results = results[results.index.date == sample_day]
        self.assertEqual(len(day_results["daily_open"].unique()), 1)
        self.assertEqual(day_results["daily_open"].iloc[0], df[df.index.date == sample_day]["open"].iloc[0])
        
        # Check bands calculation
        vol = day_results["daily_volatility"].iloc[0]
        opened = day_results["daily_open"].iloc[0]
        prev_close = day_results["prev_day_close"].iloc[0]
        prev_close_filled = prev_close if not np.isnan(prev_close) else opened
        anchor_up = max(opened, prev_close_filled)
        anchor_down = min(opened, prev_close_filled)
        if not np.isnan(vol):
            self.assertAlmostEqual(day_results["upper_enter"].iloc[0], anchor_up * (1 + multiplier_enter * vol))
            self.assertAlmostEqual(day_results["lower_enter"].iloc[0], anchor_down * (1 - multiplier_enter * vol))

    def test_sigma_open_curve(self):
        # Create a mock dataset with 10 days of 10 bars each
        # Intraday price trends up every day: close_t goes from 100 to 109
        # So move_open_t increases intraday!
        dates = pd.date_range("2026-05-01", periods=10, freq="D")
        indices = []
        for d in dates:
            for m in range(10):
                indices.append(d + pd.Timedelta(minutes=m))
        df = pd.DataFrame(index=indices)
        df["open"] = 100.0
        df["close"] = 100.0 + np.tile(np.arange(10), 10)
        
        results = compute_noise_boundary(df, lookback_days=3, multiplier_enter=2.0, multiplier_exit=1.0)
        
        # Take a day that is fully calculated (e.g. Day 6)
        day_results = results[results.index.date == dates[5].date()]
        vols = day_results["daily_volatility"]
        
        # Verify vols is strictly increasing during the day
        self.assertTrue((vols.diff().dropna() > 0).all())
        # First minute volatility should be 0 because close_0 == open_0
        self.assertAlmostEqual(vols.iloc[0], 0.0)
        # Last minute volatility should be greater than first minute
        self.assertGreater(vols.iloc[-1], vols.iloc[0])

    def test_overnight_gap_anchor(self):
        # Day 1: Close = 100
        # Day 2: Open = 110 (Gap haussier of +10)
        # Verify that UB is anchored to 110 and LB is anchored to 100
        indices = []
        dates = pd.date_range("2026-05-01", periods=5, freq="D")
        for d in dates:
            for m in range(2):
                indices.append(d + pd.Timedelta(minutes=m))
        df = pd.DataFrame(index=indices)
        df["open"] = 100.0
        df["close"] = 100.0
        
        # Set Day 4 to have an open of 110
        day4_indices = df.index.date == dates[3].date()
        df.loc[day4_indices, "open"] = 110.0
        df.loc[day4_indices, "close"] = 110.0
        
        results = compute_noise_boundary(df, lookback_days=2, multiplier_enter=1.0, multiplier_exit=0.5)
        
        # Check Day 4 results
        day4_results = results[results.index.date == dates[3].date()]
        # prev_day_close should be 100.0 (Day 3 close)
        self.assertEqual(day4_results["prev_day_close"].iloc[0], 100.0)
        # UB should be max(110, 100) * (1 + vol) = 110 * (1 + vol)
        # LB should be min(110, 100) * (1 - vol) = 100 * (1 - vol)
        vol = day4_results["daily_volatility"].iloc[0]
        if not np.isnan(vol):
            self.assertAlmostEqual(day4_results["upper_enter"].iloc[0], 110.0 * (1 + vol))
            self.assertAlmostEqual(day4_results["lower_enter"].iloc[0], 100.0 * (1 - vol))

    def test_vwap_entry_filter(self):
        from backtest_engine.strategies.noise_boundary_intraday import run_noise_boundary_intraday, NoiseBoundaryConfigOverrides
        
        # Create a 10 day dataset to have valid volatilities
        dates = pd.date_range("2026-05-01", periods=10, freq="D")
        indices = []
        for d in dates:
            for m in range(5):
                indices.append(d + pd.Timedelta(minutes=m))
        df = pd.DataFrame(index=indices)
        df["open"] = 100.0
        df["high"] = 100.1
        df["low"] = 99.9
        df["close"] = 100.0
        df["volume"] = 1000.0
        
        # On the last day:
        # Bar 0 (09:30): open=110, high=110, low=110, close=110, volume=1000000
        # Bar 1 (09:31): open=100, high=105, low=100, close=105, volume=1
        last_day_indices = df.index.date == dates[-1].date()
        last_day_locs = np.where(last_day_indices)[0]
        
        df.iloc[last_day_locs[0], df.columns.get_loc("open")] = 110.0
        df.iloc[last_day_locs[0], df.columns.get_loc("high")] = 110.0
        df.iloc[last_day_locs[0], df.columns.get_loc("low")] = 110.0
        df.iloc[last_day_locs[0], df.columns.get_loc("close")] = 110.0
        df.iloc[last_day_locs[0], df.columns.get_loc("volume")] = 1000000.0
        
        df.iloc[last_day_locs[1], df.columns.get_loc("open")] = 100.0
        df.iloc[last_day_locs[1], df.columns.get_loc("high")] = 105.0
        df.iloc[last_day_locs[1], df.columns.get_loc("low")] = 100.0
        df.iloc[last_day_locs[1], df.columns.get_loc("close")] = 105.0
        df.iloc[last_day_locs[1], df.columns.get_loc("volume")] = 1.0
        
        overrides = NoiseBoundaryConfigOverrides(
            lookback_days=5,
            target_daily_volatility=0.01,
            volatility_multiplier_enter=0.01,  # enter easily
            start_trade_after_open_minutes=0,
            exit_trades_before_close_minutes=0,
        )
        
        res = run_noise_boundary_intraday(df, "MOCK", overrides, initial_capital=1000.0)
        # Price (105) is above upper_enter (around 100), but below VWAP (around 110)
        # So no long order should be entered!
        self.assertTrue(res.trades.empty)

    def test_leverage_cap_not_reject(self):
        from backtest_engine.broker import BrokerSimulator, BrokerConfig
        config = BrokerConfig(
            initial_capital=1000.0,
            sizing_mode="target_volatility",
            target_daily_volatility=0.1,  # huge target volatility
            max_leverage=2.0
        )
        broker = BrokerSimulator(config)
        # Implied leverage: 0.1 / 0.01 = 10.0x.
        # Should cap size to 2.0x instead of returning 0.0.
        size = broker.calculate_position_size(price=100.0, equity=1000.0, realized_volatility=0.01)
        self.assertGreater(size, 0.0)
        # Notional should be equity * max_leverage = 1000 * 2.0 = 2000
        # Size = 2000 / 100 = 20.0
        self.assertAlmostEqual(size, 20.0)

if __name__ == "__main__":
    unittest.main()
