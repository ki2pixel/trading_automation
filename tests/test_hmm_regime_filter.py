import pytest
import numpy as np
import pandas as pd
from backtest_engine.indicators.hmm_regime_filter import HMMRegimeFilter, gpdf, _hmm_regime_filter_1d_nb, _hmm_regime_filter_2d_nb
from pine_scripts_convert_to_python.strategy.hmm_regime_filter_strategy import run_hmm_regime_filter_strategy, HMMRegimeFilterStrategyConfig

def test_gpdf():
    # Test gaussian pdf function
    val = gpdf(0.0, 0.0, 1.0)
    assert np.isclose(val, 1.0)
    
    val2 = gpdf(1.0, 0.0, 1.0)
    assert np.isclose(val2, np.exp(-0.5))

def test_hmm_1d():
    obs = np.array([0.0, 1.5, 3.0, -1.5, -3.0])
    sigma = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
    
    official_state, p_up, p_range, p_down = _hmm_regime_filter_1d_nb(
        obs, sigma, obs_len=14, stat_len=28, mu_k=1.5, stick=0.9, confirm_bars=2, dom_thresh=0.5
    )
    
    assert len(official_state) == 5
    assert np.all((official_state >= 0) & (official_state <= 2))
    assert np.allclose(p_up + p_range + p_down, 1.0)

def test_hmm_vectorbt_indicator():
    # 2D case
    dates = pd.date_range("2020-01-01", periods=100)
    np.random.seed(42)
    high = pd.DataFrame(np.random.randn(100, 2) + 100, index=dates, columns=['A', 'B'])
    low = pd.DataFrame(np.random.randn(100, 2) + 98, index=dates, columns=['A', 'B'])
    close = pd.DataFrame(np.random.randn(100, 2) + 99, index=dates, columns=['A', 'B'])
    
    res = HMMRegimeFilter.run(high, low, close)
    assert res.official_state.shape == (100, 2)
    assert res.prob_up.shape == (100, 2)
    
def test_hmm_strategy_signals():
    dates = pd.date_range("2020-01-01", periods=200)
    np.random.seed(42)
    # create a strong upward trend to force official_state = 0
    close = np.linspace(100, 200, 200) + np.random.randn(200)
    high = close + 2
    low = close - 2
    
    df = pd.DataFrame({'high': high, 'low': low, 'close': close}, index=dates)
    config = HMMRegimeFilterStrategyConfig()
    
    long_entry, short_entry, long_exit, short_exit, indicators = run_hmm_regime_filter_strategy(df, config)
    
    assert len(long_entry) == 200
    assert 'official_state' in indicators
    # Test lookahead: no state change on bar 0 based on future bars
    assert indicators['official_state'].iloc[0] == 1 # initial state
