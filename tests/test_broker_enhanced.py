import math
import pytest
import pandas as pd

from backtest_engine.broker import (
    BrokerConfig,
    BrokerSimulator,
    Position,
    Order,
    ExitAction,
    TimeExitRule,
    VWAPExitRule,
    BoundaryExitRule,
    LadderExitRule,
    SequentialLadderExitRule,
    ExitOrchestrator
)

def test_time_exit_rule():
    rule = TimeExitRule(threshold_minutes=15)
    bar1 = {"timestamp": pd.Timestamp("2024-01-01 15:30"), "minutes_until_close": 30}
    bar2 = {"timestamp": pd.Timestamp("2024-01-01 15:50"), "minutes_until_close": 10}
    
    pos = Position(1.0, 100.0)
    
    assert rule.evaluate(bar1, pos) is None
    
    action = rule.evaluate(bar2, pos)
    assert action is not None
    assert action.type == "close"
    assert action.rule_name == "TimeExitRule"

def test_vwap_exit_rule():
    dates = pd.date_range("2024-01-01 09:30", periods=3, freq="5min")
    vwap_series = pd.Series([100.0, 101.0, 102.0], index=dates)
    
    rule = VWAPExitRule(vwap_series)
    pos_long = Position(1.0, 100.0)
    
    # Close price above VWAP -> No exit
    bar1 = {"timestamp": dates[1], "close": 101.5}
    assert rule.evaluate(bar1, pos_long) is None
    
    # Close price below VWAP -> Exit
    bar2 = {"timestamp": dates[2], "close": 101.5}
    action = rule.evaluate(bar2, pos_long)
    assert action is not None
    assert action.type == "close"
    
    pos_short = Position(-1.0, 100.0)
    # Short pos: price above VWAP -> Exit
    action_short = rule.evaluate(bar2, pos_short)
    assert action_short is None # 101.5 < 102.0, no exit for short
    
    bar3 = {"timestamp": dates[1], "close": 101.5} # VWAP is 101.0
    action_short = rule.evaluate(bar3, pos_short)
    assert action_short is not None
    assert action_short.type == "close"

def test_ladder_exit_rule():
    steps = [(0.01, 0.5), (0.02, 1.0)] # 1% profit -> exit 50%, 2% profit -> exit 100%
    rule = LadderExitRule(steps)
    
    pos = Position(100.0, 100.0)
    
    bar1 = {"close": 100.5}
    assert rule.evaluate(bar1, pos) is None
    
    bar2 = {"close": 101.0}
    action1 = rule.evaluate(bar2, pos)
    assert action1 is not None
    assert action1.type == "partial"
    assert action1.quantity == 50.0
    
    # Already executed step 1, shouldn't execute again
    bar3 = {"close": 101.5}
    assert rule.evaluate(bar3, pos) is None
    
    bar4 = {"close": 102.0}
    action2 = rule.evaluate(bar4, pos)
    assert action2 is not None
    assert action2.type == "partial"
    assert action2.quantity == 100.0

def test_boundary_exit_rule():
    dates = pd.date_range("2024-01-01 09:30", periods=2, freq="5min")
    upper = pd.Series([105.0, 105.0], index=dates)
    lower = pd.Series([95.0, 95.0], index=dates)
    
    rule = BoundaryExitRule(upper, lower)
    pos_long = Position(1.0, 100.0)
    
    bar1 = {"timestamp": dates[0], "close": 100.0}
    assert rule.evaluate(bar1, pos_long) is None
    
    bar2 = {"timestamp": dates[1], "close": 94.0}
    action = rule.evaluate(bar2, pos_long)
    assert action is not None
    assert action.type == "close"
    assert action.comment == "Lower Boundary crossed (SL)"
    
    pos_short = Position(-1.0, 100.0)
    bar3 = {"timestamp": dates[1], "close": 106.0}
    action_short = rule.evaluate(bar3, pos_short)
    assert action_short is not None
    assert action_short.type == "close"
    assert action_short.comment == "Upper Boundary crossed (SL)"

def test_sequential_ladder_exit_rule():
    # step0: SL=-1%, TP=+2%
    # step1: SL=0% (breakeven), TP=+5%
    # TP ratio = 50%
    rule = SequentialLadderExitRule(
        stoploss_step0=-0.01,
        stoploss_step1=0.00,
        takeprofit_step0=0.02,
        takeprofit_step1=0.05,
        takeprofit_ratio0=0.5
    )
    
    pos = Position(100.0, 100.0)
    
    # Step 0: price goes to 101.0 -> no trigger
    assert rule.evaluate({"close": 101.0}, pos) is None
    
    # Step 0: price goes to 99.5 -> SL step 0 hit (100 -> 99.5 is -0.5%, wait, SL is -1.0%, so no trigger)
    assert rule.evaluate({"close": 99.5}, pos) is None
    
    # Step 0: price hits SL step 0 (-1.5%) -> triggers full close
    action_sl = rule.evaluate({"close": 98.5}, pos)
    assert action_sl is not None
    assert action_sl.type == "close"
    assert action_sl.comment == "Ladder SL Step 0"
    
    # Reset for next scenario (simulate entering new position)
    rule.current_step = 0
    
    # Step 0: price goes to 102.5 (+2.5%) -> triggers TP Step 0
    action_tp = rule.evaluate({"close": 102.5}, pos)
    assert action_tp is not None
    assert action_tp.type == "partial"
    assert action_tp.quantity == 50.0
    assert rule.current_step == 1
    
    # Update position size after partial close
    pos = Position(50.0, 100.0)
    
    # Step 1: price goes to 103.0 -> no trigger
    assert rule.evaluate({"close": 103.0}, pos) is None
    
    # Step 1: price drops to 99.9 (<= 0.0% breakeven) -> triggers SL Step 1
    action_sl1 = rule.evaluate({"close": 99.9}, pos)
    assert action_sl1 is not None
    assert action_sl1.type == "close"
    assert action_sl1.comment == "Ladder SL Step 1"

def test_exit_orchestrator():
    rule1 = TimeExitRule(threshold_minutes=15)
    rule2 = LadderExitRule([(-0.01, 0.5)]) # 1% stop loss for 50% partial
    
    orch = ExitOrchestrator([rule1, rule2])
    pos = Position(100.0, 100.0)
    
    bar = {"timestamp": pd.Timestamp("2024-01-01 15:50"), "minutes_until_close": 10, "close": 98.0}
    
    action = orch.evaluate(bar, pos)
    assert action is not None
    # Both trigger, but close > partial
    assert action.type == "close"

def test_sizing_target_volatility():
    config = BrokerConfig(sizing_mode="target_volatility", target_daily_volatility=0.01, volatility_lookback_days=20)
    broker = BrokerSimulator(config)
    
    dates = pd.date_range("2024-01-01", periods=21, freq="D")
    closes = [100.0]
    for i in range(20):
        closes.append(closes[-1] * (1.0 + (0.01 if i%2==0 else -0.01)))
    
    df = pd.DataFrame({"close": closes}, index=dates)
    
    size = broker.calculate_position_size(price=100.0, equity=1000.0, bars_for_vol=df)
    assert size > 0
    assert not math.isnan(size)

def test_sizing_target_volatility_precalculated():
    config = BrokerConfig(sizing_mode="target_volatility", target_daily_volatility=0.02, volatility_lookback_days=20)
    broker = BrokerSimulator(config)
    
    # Pass precalculated volatility directly (e.g. 1.5% or 0.015)
    size = broker.calculate_position_size(price=100.0, equity=1000.0, realized_volatility=0.015)
    # Expected size = (1000 * 0.02) / (100 * 0.015) = 20 / 1.5 = 13.333333
    assert size == pytest.approx(13.333333)

def test_apply_fill_partial():
    broker = BrokerSimulator()
    
    # Entry
    order1 = Order("entry", "buy", 10.0)
    broker.fill_order(order1, "2024-01-01", 100.0)
    
    assert broker.position.signed_quantity == 10.0
    assert broker.position.average_price == 100.0
    
    # Partial Exit
    order2 = Order("exit_partial", "sell", 5.0)
    broker.fill_order(order2, "2024-01-02", 110.0)
    
    assert broker.position.signed_quantity == 5.0
    assert broker.position.average_price == 100.0
    
    assert len(broker.closed_trades) == 1
    trade = broker.closed_trades[0]
    assert trade.is_partial_exit is True
    assert trade.parent_entry_order_id == "entry"
    assert trade.quantity == 5.0
    
    # Full Exit
    order3 = Order("exit_full", "sell", 5.0)
    broker.fill_order(order3, "2024-01-03", 120.0)
    
    assert broker.position.signed_quantity == 0.0
    
    assert len(broker.closed_trades) == 2
    trade2 = broker.closed_trades[1]
    assert trade2.is_partial_exit is False

def test_integration_broker_exits():
    steps = [(0.05, 0.5)]
    rule_ladder = LadderExitRule(steps)
    rule_time = TimeExitRule(threshold_minutes=15)
    
    orch = ExitOrchestrator([rule_ladder, rule_time])
    
    broker = BrokerSimulator()
    broker.exit_orchestrator = orch
    
    broker.fill_order(Order("entry", "buy", 10.0), pd.Timestamp("2024-01-01 10:00"), 100.0)
    
    bar1 = {"timestamp": pd.Timestamp("2024-01-01 10:05"), "open": 102.0, "close": 102.0, "minutes_until_close": 300}
    action1 = broker.evaluate_exits(bar1)
    assert action1 is None
    
    bar2 = {"timestamp": pd.Timestamp("2024-01-01 10:10"), "open": 106.0, "close": 106.0, "minutes_until_close": 295}
    action2 = broker.evaluate_exits(bar2)
    assert action2 is not None
    assert action2.type == "partial"
    assert action2.quantity == 5.0
    
    assert broker.position.signed_quantity == 5.0
    
    bar3 = {"timestamp": pd.Timestamp("2024-01-01 15:50"), "open": 105.0, "close": 105.0, "minutes_until_close": 10}
    action3 = broker.evaluate_exits(bar3)
    assert action3 is not None
    assert action3.type == "close"
    
    assert broker.position.is_flat is True

def test_fx_currency_conversion():
    provider = lambda currency, ts: 0.9 if currency == "USD" else 1.0
    config = BrokerConfig(
        account_currency="EUR",
        asset_currency="USD",
        fx_rate_provider=provider,
        initial_capital=1000.0,
    )
    broker = BrokerSimulator(config)
    
    # Buy 1 share at $100 -> converted to 90 EUR
    broker.fill_order(Order("entry", "buy", 1.0), pd.Timestamp("2024-01-01"), 100.0)
    assert broker.cash == pytest.approx(910.0)
    
    # Sell at $110 -> converted to 99 EUR; gross = 99 - 90 = 9 EUR
    broker.fill_order(Order("exit", "sell", 1.0), pd.Timestamp("2024-01-02"), 110.0)
    
    trades = broker.closed_trades_frame()
    assert len(trades) == 1
    assert trades.iloc[0]["gross_pnl"] == pytest.approx(9.0)
    assert trades.iloc[0]["entry_price"] == pytest.approx(90.0)
    assert trades.iloc[0]["exit_price"] == pytest.approx(99.0)

def test_fx_mark_to_market_equity():
    provider = lambda currency, ts: 0.9 if currency == "USD" else 1.0
    config = BrokerConfig(
        account_currency="EUR",
        asset_currency="USD",
        fx_rate_provider=provider,
        initial_capital=1000.0,
    )
    broker = BrokerSimulator(config)
    broker.fill_order(Order("entry", "buy", 1.0), pd.Timestamp("2024-01-01"), 100.0)
    
    # Position value at $110 in EUR: 110 * 0.9 = 99
    # Equity = 910 + 99 = 1009
    equity = broker.mark_to_market_equity(110.0, pd.Timestamp("2024-01-01"))
    assert equity == pytest.approx(1009.0)

def test_same_bar_exit_guard():
    steps = [(0.01, 1.0)] # 1% profit -> close position
    rule = LadderExitRule(steps)
    orch = ExitOrchestrator([rule])
    
    broker = BrokerSimulator()
    broker.exit_orchestrator = orch
    
    # Fill order on timestamp 10:00
    broker.fill_order(Order("entry", "buy", 10.0), pd.Timestamp("2024-01-01 10:00"), 100.0)
    
    # Bar with same timestamp (10:00) showing a profit (102.0 close vs 100.0 average price)
    same_bar = {"timestamp": pd.Timestamp("2024-01-01 10:00"), "open": 100.0, "close": 102.0}
    
    # Guard should prevent exit
    action = broker.evaluate_exits(same_bar)
    assert action is None
    assert broker.position.signed_quantity == 10.0
    
    # Bar with different timestamp (10:05) showing same profit
    next_bar = {"timestamp": pd.Timestamp("2024-01-01 10:05"), "open": 102.0, "close": 102.0}
    action_next = broker.evaluate_exits(next_bar)
    assert action_next is not None
    assert broker.position.is_flat is True
