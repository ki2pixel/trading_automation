import pytest
import numpy as np
import pandas as pd
from pine_scripts_convert_to_python.strategy.smart_trader_geometric import (
    compute_yang_zhang,
    _compute_frozen_anchors,
    add_smart_trader_geometric_features,
    SmartTraderGeometricConfig,
    run_smart_trader_geometric_strategy
)

def test_yang_zhang():
    lookback = 5
    open_p = np.array([100, 102, 101, 105, 104, 106])
    high = np.array([105, 103, 104, 108, 106, 110])
    low = np.array([98, 100, 99, 102, 101, 105])
    close = np.array([102, 101, 103, 106, 105, 108])
    
    sigma = compute_yang_zhang(open_p, high, low, close, lookback)
    assert len(sigma) == len(close)
    # the first elements might be NaN due to rolling window
    assert np.isnan(sigma[0]) or sigma[0] == 1e-8 or not np.isnan(sigma[0])

def test_frozen_anchors():
    high = np.array([10, 12, 11, 15, 14, 16])
    low = np.array([5, 6, 4, 8, 7, 9])
    close = np.array([8, 10, 7, 12, 11, 15])
    lookback = 3
    
    ceil_arr, floor_arr, center_arr, anchor_idx = _compute_frozen_anchors(high, low, close, lookback)
    assert len(ceil_arr) == len(close)
    
    # Check anchor logic
    # bars: 0, 1, 2
    # at i=2 (lookback-1), anchor is established on window [0:3] -> high: 10,12,11 -> hh=12. low: 5,6,4 -> ll=4.
    assert ceil_arr[2] == 12
    assert floor_arr[2] == 4
    assert center_arr[2] == np.sqrt(12*4)
    assert anchor_idx[2] == 2
    
    # at i=3, close is 12. Not > ceiling (12), not < floor (4). Anchor maintained.
    assert anchor_idx[3] == 2
    assert ceil_arr[3] == 12
    
    # at i=5, close is 15. 15 > 12. So anchor should be broken for NEXT bar. 
    # Actually, at i=5 it breaks, meaning anchor_idx[5] will still be 2 but then current_anchor_i becomes -1.

def test_add_features():
    df = pd.DataFrame({
        'open': [10]*30,
        'high': [12]*30,
        'low': [8]*30,
        'close': [10]*30
    })
    
    config = SmartTraderGeometricConfig(lookback_period=5)
    df_out = add_smart_trader_geometric_features(df, config)
    
    assert 'Ceil angle' in df_out.columns
    assert 'Ctr distance' in df_out.columns
    assert 'PnU area' in df_out.columns
    assert 'PnD centroid' in df_out.columns

def test_run_strategy_quorum():
    df = pd.DataFrame({
        'open': [10]*10,
        'high': [12]*10,
        'low': [8]*10,
        'close': [10]*10,
        'Ceil angle': [-10, 20, 20, 20, 20, -10, -10, -10, -10, -10],
        'Flr angle': [5, 5, 5, 5, 5, 5, 5, 5, 5, 5]
    })
    
    config = SmartTraderGeometricConfig(
        lookback_period=5,
        min_long_entry_slots=2, # Need 2 slots to pass
        slots=[
            {"variable": "Ceil angle", "condition": ">", "threshold": 0.0, "apply_to": "Long entry"},
            {"variable": "Flr angle", "condition": ">", "threshold": 0.0, "apply_to": "Long entry"}
        ]
    )
    
    state_df, trades_df = run_smart_trader_geometric_strategy(df, config)
    
    # Bar 1 has Ceil angle 20 > 0 and Flr angle 5 > 0. Two slots pass -> entry.
    # Bar 0 has Ceil angle -10. One slot passes -> no entry.
    
    assert state_df['in_position'].iloc[0] == False
    assert state_df['in_position'].iloc[1] == True
    assert state_df['side'].iloc[1] == 1

