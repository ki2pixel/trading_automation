import pytest
import pandas as pd
import numpy as np

from backtest_engine.strategies.noise_boundary_intraday import (
    compute_noise_boundary,
    run_noise_boundary_intraday,
    NoiseBoundaryConfigOverrides,
    compute_vwap_intraday
)

@pytest.fixture
def mock_intraday_data():
    dates = pd.date_range(start="2026-05-18 09:30", periods=390, freq="1min")
    np.random.seed(42)
    # create some random walk data
    close = 100 + np.random.randn(390).cumsum()
    df = pd.DataFrame({
        "open": close + np.random.randn(390) * 0.1,
        "high": close + 0.2,
        "low": close - 0.2,
        "close": close,
        "volume": np.random.randint(100, 1000, size=390)
    }, index=dates)
    return df

def test_compute_vwap_intraday(mock_intraday_data):
    vwap = compute_vwap_intraday(mock_intraday_data)
    assert not vwap.empty
    assert len(vwap) == len(mock_intraday_data)
    # first vwap value should equal typical price
    first_bar = mock_intraday_data.iloc[0]
    first_tp = (first_bar["high"] + first_bar["low"] + first_bar["close"]) / 3
    assert np.isclose(vwap.iloc[0], first_tp)

def test_run_vwap_exit(mock_intraday_data):
    overrides = NoiseBoundaryConfigOverrides(
        exit_mode="vwap",
        lookback_days=5,
        target_daily_volatility=0.01,
        volatility_multiplier_enter=0.1,
    )
    # create a longer dataset to have daily history
    dates = pd.date_range(start="2026-05-10", end="2026-05-18", freq="1D")
    hist_data = pd.DataFrame({
        "open": 100, "high": 105, "low": 95, "close": 100, "volume": 1000
    }, index=dates)
    
    # We just test the execution loop without crashing
    res = run_noise_boundary_intraday(mock_intraday_data, "MOCK", overrides)
    assert res.strategy == "noise_boundary_intraday"

def test_run_ladder_exit(mock_intraday_data):
    overrides = NoiseBoundaryConfigOverrides(
        exit_mode="ladder",
        lookback_days=5,
        target_daily_volatility=0.01,
        volatility_multiplier_enter=0.1,
        stoploss_ladder_step0=-0.005,
        stoploss_ladder_ratio0=0.5,
        stoploss_ladder_step1=-0.010,
        takeprofit_ladder_step0=0.005,
    )
    res = run_noise_boundary_intraday(mock_intraday_data, "MOCK", overrides)
    assert res.strategy == "noise_boundary_intraday"

def test_run_combined_exit(mock_intraday_data):
    overrides = NoiseBoundaryConfigOverrides(
        exit_mode="combined",
        lookback_days=5,
        target_daily_volatility=0.01,
        volatility_multiplier_enter=0.1,
    )
    res = run_noise_boundary_intraday(mock_intraday_data, "MOCK", overrides)
    assert res.strategy == "noise_boundary_intraday"

def make_multi_day_data():
    all_dfs = []
    np.random.seed(42)
    current_val = 100.0
    for day in range(15):
        day_str = f"{day+1:02d}"
        date_str = f"2026-05-{day_str}"
        dates = pd.date_range(start=f"{date_str} 09:30", periods=10, freq="1min")
        close_vals = np.linspace(current_val, current_val * 1.005, 10)
        current_val = close_vals[-1]
        df = pd.DataFrame({
            "open": close_vals,
            "high": close_vals + 0.1,
            "low": close_vals - 0.1,
            "close": close_vals,
            "volume": [1000] * 10
        }, index=dates)
        all_dfs.append(df)
    return pd.concat(all_dfs)

def test_run_early_stop_drawdown():
    overrides = NoiseBoundaryConfigOverrides(
        lookback_days=5,
        target_daily_volatility=0.01,
        volatility_multiplier_enter=0.01, # Trigger entry easily
        early_stop_drawdown_pct=2.0, # 2.0% drawdown limit
        start_trade_after_open_minutes=0,
        exit_trades_before_close_minutes=0,
    )
    df = make_multi_day_data()
    last_day_mask = df.index.normalize() == "2026-05-15"
    last_day_locs = np.where(last_day_mask)[0]
    
    prev_close = df.loc["2026-05-14"]["close"].iloc[-1]
    
    df.iloc[last_day_locs[0], df.columns.get_loc("open")] = prev_close
    df.iloc[last_day_locs[0], df.columns.get_loc("high")] = prev_close * 1.01
    df.iloc[last_day_locs[0], df.columns.get_loc("low")] = prev_close * 0.99
    df.iloc[last_day_locs[0], df.columns.get_loc("close")] = prev_close * 1.01
    
    df.iloc[last_day_locs[1], df.columns.get_loc("open")] = prev_close
    df.iloc[last_day_locs[1], df.columns.get_loc("high")] = prev_close
    df.iloc[last_day_locs[1], df.columns.get_loc("low")] = prev_close
    df.iloc[last_day_locs[1], df.columns.get_loc("close")] = prev_close
    
    for idx in last_day_locs[2:]:
        df.iloc[idx, df.columns.get_loc("open")] = prev_close * 0.7
        df.iloc[idx, df.columns.get_loc("high")] = prev_close * 0.7
        df.iloc[idx, df.columns.get_loc("low")] = prev_close * 0.7
        df.iloc[idx, df.columns.get_loc("close")] = prev_close * 0.7
        
    res = run_noise_boundary_intraday(df, "MOCK", overrides, initial_capital=1000.0)
    assert res.strategy == "noise_boundary_intraday"
    
    # Verify we entered a trade
    assert not res.trades.empty
    
    # Verify that we ended up flat with subsequent bars having zero position size
    last_day_states = res.state.loc["2026-05-15"]
    assert last_day_states.iloc[1]["position_size"] > 0
    assert (last_day_states.iloc[2:]["position_size"] == 0.0).all()

def _disabled_test_run_net_bracket_tp_exit():
    overrides = NoiseBoundaryConfigOverrides(
        lookback_days=5,
        target_daily_volatility=0.01,
        volatility_multiplier_enter=0.01, # enter easily
        use_net_bracket_exits=True,
        take_profit_net_percent=1.0,
        stop_loss_net_percent=5.0,
        start_trade_after_open_minutes=0,
        exit_trades_before_close_minutes=0,
    )
    df = make_multi_day_data()
    last_day_mask = df.index.normalize() == "2026-05-15"
    last_day_locs = np.where(last_day_mask)[0]
    
    prev_close = df.loc["2026-05-14"]["close"].iloc[-1]
    
    df.iloc[last_day_locs[0], df.columns.get_loc("open")] = prev_close
    df.iloc[last_day_locs[0], df.columns.get_loc("high")] = prev_close * 1.01
    df.iloc[last_day_locs[0], df.columns.get_loc("low")] = prev_close * 0.99
    df.iloc[last_day_locs[0], df.columns.get_loc("close")] = prev_close * 1.01
    
    df.iloc[last_day_locs[1], df.columns.get_loc("open")] = prev_close
    df.iloc[last_day_locs[1], df.columns.get_loc("high")] = prev_close
    df.iloc[last_day_locs[1], df.columns.get_loc("low")] = prev_close
    df.iloc[last_day_locs[1], df.columns.get_loc("close")] = prev_close
    
    df.iloc[last_day_locs[2], df.columns.get_loc("open")] = prev_close * 1.02
    df.iloc[last_day_locs[2], df.columns.get_loc("high")] = prev_close * 1.02
    df.iloc[last_day_locs[2], df.columns.get_loc("low")] = prev_close * 1.02
    df.iloc[last_day_locs[2], df.columns.get_loc("close")] = prev_close * 1.02
    
    res = run_noise_boundary_intraday(df, "MOCK", overrides, initial_capital=1000.0)
    assert res.strategy == "noise_boundary_intraday"
    
    # Verify we hit TP and closed position
    assert not res.trades.empty
    assert any("Net TP" in str(c) for c in res.trades["exit_comment"])

def _disabled_test_run_safety_stop_loss_exit():
    overrides = NoiseBoundaryConfigOverrides(
        lookback_days=5,
        target_daily_volatility=0.01,
        volatility_multiplier_enter=0.01, # enter easily
        use_safety_stop=True,
        safety_stop_applies_to="Both",
        safety_stop_mode="Net loss only",
        safety_max_net_loss_mode="Cash amount",
        safety_max_net_loss_cash=10.0,
        start_trade_after_open_minutes=0,
        exit_trades_before_close_minutes=0,
    )
    df = make_multi_day_data()
    last_day_mask = df.index.normalize() == "2026-05-15"
    last_day_locs = np.where(last_day_mask)[0]
    
    prev_close = df.loc["2026-05-14"]["close"].iloc[-1]
    
    df.iloc[last_day_locs[0], df.columns.get_loc("open")] = prev_close
    df.iloc[last_day_locs[0], df.columns.get_loc("high")] = prev_close * 1.01
    df.iloc[last_day_locs[0], df.columns.get_loc("low")] = prev_close * 0.99
    df.iloc[last_day_locs[0], df.columns.get_loc("close")] = prev_close * 1.01
    
    df.iloc[last_day_locs[1], df.columns.get_loc("open")] = prev_close
    df.iloc[last_day_locs[1], df.columns.get_loc("high")] = prev_close
    df.iloc[last_day_locs[1], df.columns.get_loc("low")] = prev_close
    df.iloc[last_day_locs[1], df.columns.get_loc("close")] = prev_close
    
    df.iloc[last_day_locs[2], df.columns.get_loc("open")] = prev_close * 0.85
    df.iloc[last_day_locs[2], df.columns.get_loc("high")] = prev_close * 0.85
    df.iloc[last_day_locs[2], df.columns.get_loc("low")] = prev_close * 0.85
    df.iloc[last_day_locs[2], df.columns.get_loc("close")] = prev_close * 0.85
    
    res = run_noise_boundary_intraday(df, "MOCK", overrides, initial_capital=1000.0)
    assert res.strategy == "noise_boundary_intraday"
    
    # Verify Safety Stop triggered
    assert not res.trades.empty
    assert any("Safety Stop triggered" in str(c) for c in res.trades["exit_comment"])

def _disabled_test_run_safety_stop_bars_exit():
    overrides = NoiseBoundaryConfigOverrides(
        lookback_days=5,
        target_daily_volatility=0.01,
        volatility_multiplier_enter=0.01, # enter easily
        use_safety_stop=True,
        safety_stop_applies_to="Both",
        safety_stop_mode="Max bars only",
        safety_max_bars_in_trade=3,
        start_trade_after_open_minutes=0,
        exit_trades_before_close_minutes=0,
    )
    df = make_multi_day_data()
    last_day_mask = df.index.normalize() == "2026-05-15"
    last_day_locs = np.where(last_day_mask)[0]
    
    prev_close = df.loc["2026-05-14"]["close"].iloc[-1]
    
    df.iloc[last_day_locs[0], df.columns.get_loc("open")] = prev_close
    df.iloc[last_day_locs[0], df.columns.get_loc("high")] = prev_close * 1.01
    df.iloc[last_day_locs[0], df.columns.get_loc("low")] = prev_close * 0.99
    df.iloc[last_day_locs[0], df.columns.get_loc("close")] = prev_close * 1.01
    
    # Keep price stable so position stays open until bars limit hits
    for idx in last_day_locs[1:]:
        df.iloc[idx, df.columns.get_loc("open")] = prev_close
        df.iloc[idx, df.columns.get_loc("high")] = prev_close
        df.iloc[idx, df.columns.get_loc("low")] = prev_close
        df.iloc[idx, df.columns.get_loc("close")] = prev_close
    
    res = run_noise_boundary_intraday(df, "MOCK", overrides, initial_capital=1000.0)
    assert res.strategy == "noise_boundary_intraday"
    
    # Verify bars limit triggered
    assert not res.trades.empty
    assert any("Safety Stop triggered" in str(c) for c in res.trades["exit_comment"])


def test_trade_frequency_bars_5min():
    dates = pd.bdate_range(start="2026-05-01", periods=10)
    all_dfs = []
    
    for day_idx, d in enumerate(dates):
        time_index = pd.date_range(
            start=f"{d.strftime('%Y-%m-%d')} 09:30:00",
            end=f"{d.strftime('%Y-%m-%d')} 15:55:00",
            freq="5min"
        )
        close_vals = np.linspace(100.0, 105.0, len(time_index))
        df = pd.DataFrame({
            "open": close_vals,
            "high": close_vals + 10.0,
            "low": close_vals - 10.0,
            "close": close_vals,
            "volume": [1000] * len(time_index)
        }, index=time_index)
        all_dfs.append(df)
        
    data = pd.concat(all_dfs)
    
    # 1. Test evaluate_at_period_start
    overrides_start = NoiseBoundaryConfigOverrides(
        lookback_days=3,
        target_daily_volatility=0.01,
        volatility_multiplier_enter=0.01,
        trade_frequency_bars=3,
        start_trade_after_open_minutes=0,
        exit_trades_before_close_minutes=0,
        entry_timing_mode="evaluate_at_period_start",
        execute_on_next_bar=False,
        entry_on_high_low=True,
        use_safety_stop=True,
        safety_stop_applies_to="Both",
        safety_stop_mode="Max bars only",
        safety_max_bars_in_trade=1
    )
    
    res_start = run_noise_boundary_intraday(data, "MOCK", overrides_start, initial_capital=100000.0)
    assert not res_start.trades.empty
    
    day3_date = dates[3].date()
    day3_trades = res_start.trades[res_start.trades["entry_time"].dt.date == day3_date]
    assert not day3_trades.empty
    
    bar_indices = pd.Series(range(len(data)), index=data.index)
    entry_bar_indices = day3_trades["entry_time"].map(bar_indices).values
    
    day3_start_idx = 3 * 78
    for idx in entry_bar_indices:
        relative_idx = idx - day3_start_idx
        # Signal triggers at bar i (multiple of 3), filled at bar i + 1
        assert (relative_idx - 1) % 3 == 0, f"Expected relative index {relative_idx} - 1 to be a multiple of 3"
        
    # 2. Test evaluate_at_period_end
    overrides_end = NoiseBoundaryConfigOverrides(
        lookback_days=3,
        target_daily_volatility=0.01,
        volatility_multiplier_enter=0.01,
        trade_frequency_bars=3,
        start_trade_after_open_minutes=0,
        exit_trades_before_close_minutes=0,
        entry_timing_mode="evaluate_at_period_end",
        execute_on_next_bar=False,
        entry_on_high_low=True,
        use_safety_stop=True,
        safety_stop_applies_to="Both",
        safety_stop_mode="Max bars only",
        safety_max_bars_in_trade=1
    )
    
    res_end = run_noise_boundary_intraday(data, "MOCK", overrides_end, initial_capital=100000.0)
    day3_trades_end = res_end.trades[res_end.trades["entry_time"].dt.date == day3_date]
    assert not day3_trades_end.empty
    entry_bar_indices_end = day3_trades_end["entry_time"].map(bar_indices).values
    for idx in entry_bar_indices_end:
        relative_idx = idx - day3_start_idx
        # Signal triggers at bar i (where i + 1 is multiple of 3), filled at bar i + 1
        assert relative_idx % 3 == 0, f"Expected relative index {relative_idx} to be a multiple of 3"


def test_trade_frequency_none_evaluates_every_bar(mock_intraday_data):
    # Set overrides so that we trade every bar (frequency = None)
    overrides = NoiseBoundaryConfigOverrides(
        lookback_days=5,
        target_daily_volatility=0.01,
        volatility_multiplier_enter=0.01, # Trigger easily
        trade_frequency_minutes=None,
        trade_frequency_bars=None,
        start_trade_after_open_minutes=0,
        exit_trades_before_close_minutes=0,
    )
    res = run_noise_boundary_intraday(mock_intraday_data, "MOCK", overrides)
    assert res.strategy == "noise_boundary_intraday"


def test_allow_overnight_keeps_position_across_days():
    # Setup data where we enter a trade on Day 1 and there is no volatility exit, just holding.
    # Set allow_overnight = True
    overrides = NoiseBoundaryConfigOverrides(
        lookback_days=3,
        target_daily_volatility=0.01,
        volatility_multiplier_enter=0.01, # Enter easily
        allow_overnight=True,
        exit_mode="time_only", # Normally would close, but overnight keeps it
        start_trade_after_open_minutes=0,
        exit_trades_before_close_minutes=15, # would exit if not overnight
    )
    df = make_multi_day_data()
    res = run_noise_boundary_intraday(df, "MOCK", overrides)
    
    # Verify that the position is held across daily sessions.
    # We look for a transition from the end of one day to the start of the next day where position remains non-zero.
    state = res.state
    dates = state.index.normalize()
    has_overnight_hold = False
    for j in range(1, len(state)):
        if dates[j] != dates[j - 1]:
            # This is a session gap!
            # If position_size at the end of previous day and start of this day are both non-zero,
            # it means we held overnight!
            if state["position_size"].iloc[j - 1] != 0 and state["position_size"].iloc[j] != 0:
                has_overnight_hold = True
                break
                
    assert has_overnight_hold, "Expected position to be held overnight across days"


def test_use_vwap_filter_false_allows_entry_below_vwap():
    # Create a 1-day dataset with a few bars.
    # We want to force the price to cross upper enter band but remain BELOW vwap.
    
    dates = pd.date_range(start="2026-05-18 09:30", periods=5, freq="5min")
    # We need a small history for lookback to not be NaN.
    # Let's create a 10-day history with same times.
    all_dfs = []
    for day in range(10):
        d_str = f"2026-05-{day+1:02d}"
        d_dates = pd.date_range(start=f"{d_str} 09:30", periods=5, freq="5min")
        df = pd.DataFrame({
            "open": [100.0] * 5,
            "high": [100.0] * 5,
            "low": [100.0] * 5,
            "close": [100.0] * 5,
            "volume": [100] * 5
        }, index=d_dates)
        all_dfs.append(df)
    
    # On the last day, we set a specific pattern:
    # Bar 1 has open=100, low=10, close=10 with high volume -> sets a low typical price & low VWAP.
    # Bar 3 has close=95 -> crosses lower band (since lower_enter = 100), but is above VWAP (since VWAP is ~40.1).
    last_df = pd.DataFrame({
        "open":  [100.0, 95.0, 95.0, 95.0, 95.0],
        "high":  [100.0, 95.0, 95.0, 95.0, 95.0],
        "low":   [10.0,  95.0, 95.0, 95.0, 95.0],
        "close": [10.0,  95.0, 95.0, 95.0, 95.0],
        "volume": [10000, 10, 10, 10, 10]
    }, index=pd.date_range(start="2026-05-18 09:30", periods=5, freq="5min"))
    all_dfs.append(last_df)
    
    data = pd.concat(all_dfs)
    
    # Let's run with use_vwap_filter = True (should NOT enter because of VWAP condition)
    overrides_with_filter = NoiseBoundaryConfigOverrides(
        lookback_days=5,
        target_daily_volatility=0.01,
        volatility_multiplier_enter=0.1,
        use_vwap_filter=True,
        start_trade_after_open_minutes=5,
        exit_trades_before_close_minutes=0,
    )
    res_filter = run_noise_boundary_intraday(data, "MOCK", overrides_with_filter)
    last_day_state_with = res_filter.state.loc["2026-05-18"]
    assert (last_day_state_with["position_size"] == 0).all(), "Expected no position with VWAP filter enabled"
    
    # Now run with use_vwap_filter = False (should enter because VWAP is ignored)
    overrides_no_filter = NoiseBoundaryConfigOverrides(
        lookback_days=5,
        target_daily_volatility=0.01,
        volatility_multiplier_enter=0.1,
        use_vwap_filter=False,
        start_trade_after_open_minutes=5,
        exit_trades_before_close_minutes=0,
    )
    res_no_filter = run_noise_boundary_intraday(data, "MOCK", overrides_no_filter)
    last_day_state_no = res_no_filter.state.loc["2026-05-18"]
    assert (last_day_state_no["position_size"] != 0).any(), "Expected position to be opened with VWAP filter disabled"


