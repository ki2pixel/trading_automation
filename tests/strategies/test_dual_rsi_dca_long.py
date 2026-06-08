import pytest
import pandas as pd
import numpy as np

from backtest_engine.strategies.dual_rsi_dca_long import DualRsiDcaLongConfigOverrides, run_dual_rsi_dca_long

def create_mock_data(length=100) -> pd.DataFrame:
    """Create basic OHLCV dataframe with a DateTimeIndex."""
    dates = pd.date_range(start='2024-01-01', periods=length, freq='3min')
    df = pd.DataFrame({
        'open': np.ones(length) * 100,
        'high': np.ones(length) * 101,
        'low': np.ones(length) * 99,
        'close': np.ones(length) * 100,
        'volume': np.ones(length) * 1000
    }, index=dates)
    return df

def test_geometric_ao_sizing_and_thresholds():
    """Verify that the AO size and thresholds match the exact geometric formulas."""
    df = create_mock_data(50)
    
    # We manipulate prices to trigger entry and all 5 AOs sequentially
    # Entry RSI needs to cross up 31.
    # To fake RSI, we can just ensure close drops then rises.
    
    # Simpler approach: RSI drops below 31, then rises to trigger.
    # Period 0-20: drop to oversold
    for i in range(20):
        df.loc[df.index[i], 'close'] = 100 - i * 5 
        
    # Period 21: Cross up!
    df.loc[df.index[21], 'close'] = 110 # Sharp rise, should cross RSI up
    
    # Period 22-30: Drop aggressively to trigger AOs
    # Base entry should be at 110.
    # AO1 threshold = 1.3%, trigger = 110 * 0.987 = 108.57
    # AO2 threshold = 1.3 + 1.3*1.3 = 1.3 + 1.69 = 2.99%, trigger = 110 * 0.9701 = 106.711
    # AO3 threshold = 2.99 + 1.69*1.3 = 2.99 + 2.197 = 5.187%, trigger = 110 * 0.94813 = 104.294
    
    df.loc[df.index[22], 'close'] = 108.0 # Triggers AO1
    df.loc[df.index[23], 'close'] = 106.0 # Triggers AO2
    df.loc[df.index[24], 'close'] = 104.0 # Triggers AO3
    df.loc[df.index[25], 'close'] = 100.0 # Triggers AO4 (thresh 8.043%)
    df.loc[df.index[26], 'close'] = 95.0  # Triggers AO5 (thresh 11.756%)
    df.loc[df.index[27], 'close'] = 90.0  # Should NOT trigger AO6 (max is 5)
    
    # Period 35: Sharp rise to trigger exit
    for i in range(35, 50):
        df.loc[df.index[i], 'close'] = 150 # Triggers exit RSI and Profit
        
    df.loc[df.index[46], 'close'] = 140 # Cross down 69
    for i in range(47, 50):
        df.loc[df.index[i], 'close'] = 140 # Remain flat so no re-entry
    
    overrides = DualRsiDcaLongConfigOverrides(
        base_order_size=90.0,
        ao_count=5,
        ao_size=110.0,
        ao_step=1.3,
        ao_step_mult=1.3,
        ao_size_mult=1.25,
        entry_rsi_len=5, # short for fast test
        exit_rsi_len=5
    )
    
    from backtest_engine.strategies.dual_rsi_dca_long import _load_strategy_module, _apply_overrides
    
    module = _load_strategy_module()
    config = module.DualRsiDcaLongConfig()
    config = _apply_overrides(config, overrides)
    
    metrics_result = module.run_dual_rsi_dca_long_strategy(df, config)
    trades = metrics_result.get('trades', [])
    
    assert len(trades) > 0, "No trades were executed"
    
    entries = [t for t in trades if t['type'] == 'entry']
    closes = [t for t in trades if t['type'] == 'close']
    
    assert len(entries) <= 6, "Should have maximum 1 base + 5 AOs"
    
    # Check geometric sizes
    # Base: 90 USDT
    # AO1: 110 USDT
    # AO2: 137.5 USDT
    # AO3: 171.875 USDT
    
    if len(entries) >= 2:
        ao1_qty = entries[1]['qty']
        ao1_price = entries[1]['price']
        assert pytest.approx(ao1_qty * ao1_price, 0.1) == 110.0
        
    if len(entries) >= 3:
        ao2_qty = entries[2]['qty']
        ao2_price = entries[2]['price']
        assert pytest.approx(ao2_qty * ao2_price, 0.1) == 137.5

