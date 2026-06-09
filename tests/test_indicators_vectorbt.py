import pytest
import numpy as np
import pandas as pd
from backtest_engine.indicators.trend_type import TrendType
from backtest_engine.indicators.msl_trend import MSLTrend

@pytest.fixture
def sample_ohlcv():
    """Create a sample OHLCV DataFrame for testing."""
    dates = pd.date_range("2023-01-01", periods=100, freq="1D")
    # Create some trending data
    close = np.linspace(100, 200, 100) + np.random.normal(0, 2, 100)
    # Add a massive spike at the end to ensure a crossover of ZLEMA + Volatility
    close[-10:] = close[-10:] + 50
    
    high = close + 5
    low = close - 5
    
    df = pd.DataFrame({
        "high": high,
        "low": low,
        "close": close
    }, index=dates)
    
    return df

def test_trend_type_indicator(sample_ohlcv):
    """Test the TrendType indicator outputs and shapes."""
    # Given
    df = sample_ohlcv
    
    # When
    tt = TrendType.run(df['high'], df['low'], df['close'], atr_len=14, atr_ma_len=20)
    state = tt.state
    
    # Then
    assert isinstance(state, pd.Series)
    assert len(state) == len(df)
    
    # The first few values might be NaN due to rolling windows
    assert state.isna().iloc[0]
    
    # After window size, we should have valid states: 0.0, 2.0, or -2.0
    valid_states = state.dropna()
    assert len(valid_states) > 0
    
    # Verify the unique values are within the expected set
    unique_vals = valid_states.unique()
    for val in unique_vals:
        assert val in [0.0, 2.0, -2.0]

def test_msl_friendly_trend(sample_ohlcv):
    """Test the MSLTrend indicator outputs and shapes."""
    # Given
    df = sample_ohlcv
    
    # When
    msl = MSLTrend.run(df['high'], df['low'], df['close'], length=20, mult=1.0)
    state = msl.state
    
    # Then
    assert isinstance(state, pd.Series)
    assert len(state) == len(df)
    
    # Verify the unique values (1.0, -1.0, or 0.0 for initial NaN filling)
    unique_vals = state.unique()
    for val in unique_vals:
        assert val in [0.0, 1.0, -1.0]
    
    # Since our mock data is a strong uptrend, we should eventually see 1.0
    assert 1.0 in unique_vals

def test_indicators_with_2d_dataframe(sample_ohlcv):
    """Test vectorbt behavior when passing 2D dataframes (multiple symbols)."""
    # Given
    df1 = sample_ohlcv.copy()
    df2 = sample_ohlcv.copy() * 1.5
    
    close_df = pd.DataFrame({"SYM1": df1["close"], "SYM2": df2["close"]})
    high_df = pd.DataFrame({"SYM1": df1["high"], "SYM2": df2["high"]})
    low_df = pd.DataFrame({"SYM1": df1["low"], "SYM2": df2["low"]})
    
    # When
    tt = TrendType.run(high_df, low_df, close_df)
    msl = MSLTrend.run(high_df, low_df, close_df)
    
    # Then
    assert isinstance(tt.state, pd.DataFrame)
    assert tt.state.shape == close_df.shape
    
    assert isinstance(msl.state, pd.DataFrame)
    assert msl.state.shape == close_df.shape
