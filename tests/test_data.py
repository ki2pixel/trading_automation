import pandas as pd
import pytest
from backtest_engine.data import split_wfo_windows

def test_split_wfo_windows():
    data = pd.DataFrame({"value": range(100)})
    
    # Test 1 window
    windows = split_wfo_windows(data, windows=1, train_ratio=0.8)
    assert len(windows) == 1
    train, test = windows[0]
    assert len(train) == 80
    assert len(test) == 20
    assert train.iloc[0]["value"] == 0
    assert train.iloc[-1]["value"] == 79
    assert test.iloc[0]["value"] == 80
    assert test.iloc[-1]["value"] == 99

    # Test 2 windows
    windows = split_wfo_windows(data, windows=2, train_ratio=0.7)
    assert len(windows) == 2
    
    # Window 1: 0 to 49
    train1, test1 = windows[0]
    assert len(train1) == int(50 * 0.7)  # 35
    assert len(test1) == 50 - 35         # 15
    assert train1.iloc[0]["value"] == 0
    assert train1.iloc[-1]["value"] == 34
    assert test1.iloc[0]["value"] == 35
    assert test1.iloc[-1]["value"] == 49
    
    # Window 2: 50 to 99
    train2, test2 = windows[1]
    assert len(train2) == int(50 * 0.7)  # 35
    assert len(test2) == 50 - 35         # 15
    assert train2.iloc[0]["value"] == 50
    assert train2.iloc[-1]["value"] == 84
    assert test2.iloc[0]["value"] == 85
    assert test2.iloc[-1]["value"] == 99

    # Test uneven division
    data_uneven = pd.DataFrame({"value": range(105)})
    windows = split_wfo_windows(data_uneven, windows=2, train_ratio=0.8)
    assert len(windows) == 2
    
    # window_size = 105 // 2 = 52
    train1, test1 = windows[0]
    assert len(train1) + len(test1) == 52
    assert len(train1) == int(52 * 0.8)  # 41
    
    train2, test2 = windows[1]
    # second window takes the remainder: 105 - 52 = 53
    assert len(train2) + len(test2) == 53
    assert len(train2) == int(53 * 0.8)  # 42

def test_split_wfo_windows_edge_cases():
    data = pd.DataFrame({"value": range(10)})
    
    with pytest.raises(ValueError, match="strictly positive"):
        split_wfo_windows(data, windows=0, train_ratio=0.8)
        
    with pytest.raises(ValueError, match="train_ratio"):
        split_wfo_windows(data, windows=2, train_ratio=1.0)
        
    with pytest.raises(ValueError, match="Not enough data"):
        split_wfo_windows(data, windows=20, train_ratio=0.8)

    # Empty data
    assert split_wfo_windows(pd.DataFrame(), windows=2, train_ratio=0.8) == []


def test_build_fx_rate_provider():
    from pathlib import Path
    from backtest_engine.data import build_fx_rate_provider

    repo_root = Path(__file__).parent.parent
    # GMAB is USD-denominated, account is EUR
    provider = build_fx_rate_provider(repo_root, "GMAB", account_currency="EUR", timeframe_minutes=1)
    assert provider is not None

    # Test with a timestamp known to be in the EURUSD dataset
    rate = provider("USD", pd.Timestamp("2020-01-02 09:30:00"))
    assert rate > 0
    assert rate < 2.0  # 1 USD should be < 2 EUR historically

    # EUR asset vs EUR account -> no conversion needed
    provider_eur = build_fx_rate_provider(repo_root, "SAP", account_currency="EUR", timeframe_minutes=1)
    assert provider_eur is None


def test_filter_time_window():
    from backtest_engine.data import filter_time_window
    import pandas as pd
    import pytest

    idx = pd.date_range("2023-01-01", periods=10, freq="D")
    df = pd.DataFrame({"value": range(10)}, index=idx)

    # 1. No bounds
    res = filter_time_window(df)
    assert len(res) == 10
    assert (res["value"] == range(10)).all()

    # 2. Start date
    res = filter_time_window(df, start_date="2023-01-03")
    assert len(res) == 8
    assert res.index[0] == pd.Timestamp("2023-01-03")

    # 3. End date
    res = filter_time_window(df, end_date="2023-01-05")
    assert len(res) == 5
    assert res.index[-1] == pd.Timestamp("2023-01-05")

    # 4. Both bounds
    res = filter_time_window(df, start_date="2023-01-03", end_date="2023-01-05")
    assert len(res) == 3
    assert list(res["value"]) == [2, 3, 4]

    # 5. Invalid parameters
    with pytest.raises(ValueError, match="start_date must be <= end_date"):
        filter_time_window(df, start_date="2023-01-05", end_date="2023-01-03")

    # 6. Non-DatetimeIndex
    df_no_dt = pd.DataFrame({"value": range(10)})
    with pytest.raises(ValueError, match="Cannot filter a time window without a DatetimeIndex"):
        filter_time_window(df_no_dt, start_date="2023-01-03")


def test_new_timeframe_validations():
    from backtest_engine.data import validate_timeframe_minutes, SUPPORTED_TIMEFRAMES_MINUTES
    for minutes in [1, 5, 10, 15, 20, 30, 45, 60, 120, 240]:
        assert minutes in SUPPORTED_TIMEFRAMES_MINUTES
        assert validate_timeframe_minutes(minutes) == minutes


def test_resample_canonical_market_data_from_1m():
    from backtest_engine.data import resample_canonical_market_data
    import pandas as pd
    import numpy as np

    # Create 1-minute OHLCV data
    idx = pd.date_range("2023-01-01 09:30:00", periods=20, freq="1min")
    df = pd.DataFrame({
        "open": np.linspace(100, 101, 20),
        "high": np.linspace(100.5, 101.5, 20),
        "low": np.linspace(99.5, 100.5, 20),
        "close": np.linspace(100.1, 101.1, 20),
        "volume": [10.0] * 20,
    }, index=idx)

    # Resample to 5 minutes
    res_5 = resample_canonical_market_data(df, timeframe_minutes=5, base_minutes=1)
    assert len(res_5) == 4
    assert res_5.iloc[0]["open"] == df.iloc[0]["open"]
    assert res_5.iloc[0]["close"] == df.iloc[4]["close"]
    assert res_5.iloc[0]["high"] == df.iloc[:5]["high"].max()
    assert res_5.iloc[0]["low"] == df.iloc[:5]["low"].min()
    assert res_5.iloc[0]["volume"] == 50.0

    # Resample to 10 minutes
    res_10 = resample_canonical_market_data(df, timeframe_minutes=10, base_minutes=1)
    assert len(res_10) == 2


def test_filter_market_hours():
    from backtest_engine.data import filter_market_hours
    from pathlib import Path

    repo_root = Path(__file__).parent.parent

    # Create synthetic 1-minute data spanning two days with UTC timestamps
    idx = pd.date_range("2023-01-02 00:00:00", periods=1440, freq="1min")  # 24h
    idx = idx.append(pd.date_range("2023-01-03 00:00:00", periods=1440, freq="1min"))
    df = pd.DataFrame({"value": range(len(idx))}, index=idx)

    # 1. XETRA symbol (CET UTC+1) -> market hours 09:00-17:30 local = 08:00-16:30 UTC
    filtered = filter_market_hours(df, symbol="SAP", repo_root=repo_root)
    # First retained bar should be 08:00 UTC on Jan 2
    assert filtered.index[0] == pd.Timestamp("2023-01-02 08:00:00")
    # Last retained bar should be 16:30 UTC on Jan 3
    assert filtered.index[-1] == pd.Timestamp("2023-01-03 16:30:00")
    # Each day: 09:00 to 17:30 inclusive at 1min -> (510 - 0) + 1 = 511 bars per day
    assert len(filtered) == 511 * 2

    # 2. NASDAQ symbol (EST UTC-5) -> market hours 09:30-16:00 local = 14:30-21:00 UTC
    filtered_nq = filter_market_hours(df, symbol="GMAB", repo_root=repo_root)
    # First retained: 14:30 UTC
    assert filtered_nq.index[0] == pd.Timestamp("2023-01-02 14:30:00")
    # Last retained: 21:00 UTC
    assert filtered_nq.index[-1] == pd.Timestamp("2023-01-03 21:00:00")
    # Each day: 09:30 to 16:00 inclusive at 1min -> (390 - 0) + 1 = 391 bars per day
    assert len(filtered_nq) == 391 * 2

    # 3. Unknown symbol -> unchanged
    filtered_unk = filter_market_hours(df, symbol="UNKNOWN", repo_root=repo_root)
    assert len(filtered_unk) == len(df)

    # 4. Non-DatetimeIndex raises
    with pytest.raises(ValueError, match="Cannot filter market hours without a DatetimeIndex"):
        filter_market_hours(pd.DataFrame({"value": [1]}), symbol="SAP", repo_root=repo_root)


def test_list_canonical_symbols(tmp_path):
    from backtest_engine.optimizer import list_canonical_symbols
    from pathlib import Path
    
    # Setup temporary directory structure
    processed_dir = tmp_path / "processed"
    (processed_dir / "market_data_1m").mkdir(parents=True)
    (processed_dir / "market_data_5m").mkdir(parents=True)
    (processed_dir / "market_data_10m").mkdir(parents=True)
    
    # Create mock parquet/csv files
    # market_data_1m has 'BTCUSD', 'ETHUSD'
    (processed_dir / "market_data_1m" / "BTCUSD.parquet").touch()
    (processed_dir / "market_data_1m" / "ETHUSD.csv.gz").touch()
    
    # market_data_5m has 'BTCUSD', 'EURUSD'
    (processed_dir / "market_data_5m" / "BTCUSD.parquet").touch()
    (processed_dir / "market_data_5m" / "EURUSD.parquet").touch()
    
    # market_data_10m has 'AAPL'
    (processed_dir / "market_data_10m" / "AAPL.parquet").touch()
    
    # Test minutes == 1: should return only 1m symbols -> ['BTCUSD', 'ETHUSD']
    symbols_1m = list_canonical_symbols(Path("/"), processed_dir=processed_dir, timeframe_minutes=1)
    assert symbols_1m == ['BTCUSD', 'ETHUSD']
    
    # Test minutes == 10: should return union of 10m, 1m, and 5m symbols -> ['AAPL', 'BTCUSD', 'ETHUSD', 'EURUSD']
    symbols_10m = list_canonical_symbols(Path("/"), processed_dir=processed_dir, timeframe_minutes=10)
    assert symbols_10m == ['AAPL', 'BTCUSD', 'ETHUSD', 'EURUSD']

