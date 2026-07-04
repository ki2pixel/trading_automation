import pandas as pd
import numpy as np
import datetime as dt
from pathlib import Path
from unittest.mock import MagicMock, patch

from backtest_engine.screening import extract_statistical_signature
from backtest_engine.live.paper_trading.engine import PaperTradingEngine
from backtest_engine.data import filter_market_hours

def test_crypto_volatility_annualization():
    """
    Given a series of daily prices representing a crypto asset
    When extracting its statistical signature with is_crypto=True
    Then it should use 365 periods instead of 252 for annualizing realized volatility.
    """
    # Create mock series (10 days of constant return)
    prices = [100.0 * (1.01 ** i) for i in range(20)]
    df = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=20, freq="D"),
        "open": prices,
        "high": prices,
        "low": prices,
        "close": prices,
        "volume": [10.0] * 20,
        "symbol": ["btcusdt"] * 20
    })
    
    # Calculate signature without is_crypto (default 252 days)
    sig_stock = extract_statistical_signature(df, is_crypto=False)
    
    # Calculate signature with is_crypto (365 days)
    sig_crypto = extract_statistical_signature(df, is_crypto=True)
    
    # Realized volatility is calculated as log_returns.std() * sqrt(periods)
    # Ratio should be sqrt(365) / sqrt(252)
    expected_ratio = np.sqrt(365) / np.sqrt(252)
    actual_ratio = sig_crypto["volatility_daily"] / sig_stock["volatility_daily"]
    
    assert np.isclose(actual_ratio, expected_ratio)


@patch("backtest_engine.live.paper_trading.engine.PaperTradingEngine._load_market_hours")
def test_crypto_weekend_is_market_open(mock_load_hours):
    """
    Given a PaperTradingEngine and mock market hours configuration
    When testing is_market_open on a weekend (Saturday/Sunday)
    Then it should return True for crypto assets and False for stock assets.
    """
    mock_load_hours.return_value = {
        "btcusdt": {
            "exchange": "CRYPTO",
            "open": "00:00",
            "close": "23:59",
            "timezone": "UTC",
            "tz_offset": "+00:00",
            "is_crypto": True
        },
        "zeal.co": {
            "exchange": "GETTEX",
            "open": "08:00",
            "close": "22:00",
            "tz_offset": "+01:00",
            "timezone": "Europe/Berlin"
        }
    }
    
    # Initialize engine resiliently
    with patch("backtest_engine.live.trading212.client.Trading212Client", MagicMock()):
        engine = PaperTradingEngine()
        
    # Mock datetime.now to be a Saturday
    # 2026-07-04 is a Saturday
    saturday_utc = dt.datetime(2026, 7, 4, 12, 0, tzinfo=dt.timezone.utc)
    
    with patch("backtest_engine.live.paper_trading.engine.datetime") as mock_datetime:
        mock_datetime.now.return_value = saturday_utc
        # Mock strftime and other behaviors if needed
        # We need mock_datetime to behave like dt.datetime but with now returning saturday_utc
        mock_datetime.side_effect = lambda *args, **kw: dt.datetime(*args, **kw)
        
        # Zeal.co is a stock, closed on weekend
        assert engine.is_market_open("zeal.co") is False
        
        # btcusdt is a crypto, open on weekend
        assert engine.is_market_open("btcusdt") is True


def test_crypto_filter_market_hours():
    """
    Given a dataframe representing a 24/7 crypto series
    When filtering market hours using configs/market_hours.json config for crypto
    Then the dataframe should remain completely unchanged.
    """
    # Mock configs/market_hours.json loader
    mock_config = {
        "btcusdt": {
            "exchange": "CRYPTO",
            "open": "00:00",
            "close": "23:59",
            "timezone": "UTC",
            "tz_offset": "+00:00",
            "is_crypto": True
        }
    }
    
    # Generate 24 hours of data
    timestamps = pd.date_range("2026-07-01 00:00:00", "2026-07-01 23:59:00", freq="min")
    df = pd.DataFrame(index=timestamps)
    
    with patch("backtest_engine.data._load_market_hours_config") as mock_load:
        mock_load.return_value = mock_config
        
        # Filter market hours
        filtered_df = filter_market_hours(df, "btcusdt", repo_root=Path("."))
        
        # Number of rows should remain identical (1440 rows for 24h)
        assert len(filtered_df) == len(df)
        assert filtered_df.index.equals(df.index)

def test_crypto_fx_rate_provider_resolution():
    """
    Given a crypto asset ending in "usdt" (e.g., btcusdt) not present in symbol_currency_map.csv
    When building its FX rate provider
    Then it should automatically map its currency to USD and resolve to the USDEUR.parquet provider.
    """
    from backtest_engine.data import build_fx_rate_provider
    
    provider = build_fx_rate_provider(
        repo_root=Path("."),
        symbol="btcusdt",
        account_currency="EUR",
        timeframe_minutes=5
    )
    
    assert provider is not None
    # Verify the provider can be called and returns a valid rate
    rate = provider("USD", pd.Timestamp("2026-06-30 12:00:00"))
    assert isinstance(rate, float)
    assert rate > 0.0
