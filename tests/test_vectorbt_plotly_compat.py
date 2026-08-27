import pytest
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from backtest_engine.strategy_registry import StrategyRegistry

class TestVectorbtPlotlyCompatibility:

    def test_tc_vbt_01_vectorbt_template_patch(self):
        # Given: backtest_engine compatibility patch is active
        import backtest_engine.compatibility
        import vectorbt as vbt

        # When: Inspecting templates registered in vectorbt settings
        themes = vbt.settings["plotting"]["themes"]

        # Then: Ensure templates can be parsed by plotly go.layout.Template without error
        for theme_name, theme_cfg in themes.items():
            tpl = go.layout.Template(theme_cfg["template"])
            assert tpl is not None

    def test_tc_vbt_02_momentum_based_zigzag_evaluation_success(self):
        # Given: Sample OHLCV dataframe matching paper trading bar format
        dates = pd.date_range("2026-08-01", periods=100, freq="45min")
        np.random.seed(42)
        prices = 100.0 + np.cumsum(np.random.randn(100) * 0.5)
        df = pd.DataFrame({
            "open": prices,
            "high": prices + 0.5,
            "low": prices - 0.5,
            "close": prices + 0.1,
            "volume": np.ones(100) * 1000.0,
        }, index=dates)

        # When: Running momentum_based_zigzag via StrategyRegistry
        strat_info = StrategyRegistry.get("momentum_based_zigzag")
        params = {
            "rsi_period": 8,
            "qqe_factor": 2.0,
            "rsi_smoothing": 4,
            "ob": 82.0,
            "os": 10.0,
            "signal_mode": "Close",
            "enable_stop_loss": True,
            "stop_loss_pct": 0.5,
            "enable_take_profit": True,
            "take_profit_pct": 11.9,
            "enable_trailing_stop": False
        }
        overrides = strat_info.overrides_from_mapping_function(params)
        res = strat_info.run_function(
            data=df,
            symbol="NVO",
            overrides=overrides,
            initial_capital=10000.0,
            timeframe_minutes="45m",
            compute_full_metrics=False,
        )

        # Then: Result is returned with bars, signals, and no Plotly template exceptions
        assert res is not None
        assert "long_entry" in res.bars.columns
        assert "short_entry" in res.bars.columns
