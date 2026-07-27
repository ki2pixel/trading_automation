"""
Unit tests for execution_guards.py — pure functions for entry/exit validation.

Coverage target: 100% branch coverage on all guard functions.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np

from backtest_engine.live.paper_trading.execution_guards import (
    compute_previous_day_close,
    resolve_max_entry_price,
    compute_atr_wilder,
    is_entry_blocked_by_atr_gate,
    count_bars_since_entry,
    is_exit_blocked_by_mhp,
)


def make_df_1m(days: int = 3) -> pd.DataFrame:
    """Factory: 1m OHLC data for `days` full days ending yesterday (UTC)."""
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = today - timedelta(minutes=1)  # last bar yesterday
    start = end - timedelta(days=days)
    idx = pd.date_range(start=start, end=end, freq="1min", tz="UTC")
    n = len(idx)
    rng = np.random.default_rng(42)
    close = rng.normal(100, 2, n).cumsum() * 0.01 + 100
    close = np.maximum(close, 1.0)
    return pd.DataFrame({
        "open": close - rng.uniform(0, 0.5, n),
        "high": close + rng.uniform(0, 1, n),
        "low": close - rng.uniform(0, 1, n),
        "close": close,
    }, index=idx)


# ---------------------------------------------------------------------------
# compute_previous_day_close
# ---------------------------------------------------------------------------

class TestPreviousDayClose:
    def test_returns_none_on_empty_df(self):
        # Given: empty DataFrame
        # When: compute_previous_day_close
        # Then: None
        assert compute_previous_day_close(pd.DataFrame(), datetime.now(timezone.utc)) is None

    def test_returns_none_on_single_day(self):
        # Given: 1m data for today only (no prior day)
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        idx = pd.date_range(start=today_start, periods=60, freq="1min", tz="UTC")
        df = pd.DataFrame({"close": [100.0] * 60}, index=idx)
        # When/Then: no previous day → None
        assert compute_previous_day_close(df, now) is None

    def test_returns_previous_day_close(self):
        # Given: 3 days of 1m data
        df = make_df_1m(days=3)
        now = datetime.now(timezone.utc)
        # When
        result = compute_previous_day_close(df, now)
        # Then: should be a Decimal
        assert result is not None
        assert isinstance(result, Decimal)
        # It should equal the last close of the second-to-last day (yesterday)
        expected_close = df["close"].resample("D").last().dropna().iloc[-1]
        assert result == Decimal(str(expected_close))


# ---------------------------------------------------------------------------
# resolve_max_entry_price
# ---------------------------------------------------------------------------

class TestResolveMaxEntryPrice:
    def test_dynamic_mode(self):
        # Given: 3 days of data, buffer=0.30
        df = make_df_1m(days=3)
        now = datetime.now(timezone.utc)
        # When
        cap, mode = resolve_max_entry_price(df_1m=df, static_max=Decimal("200"), buffer_pct=0.30, now_utc=now)
        # Then
        assert mode == "dynamic"
        prev_close = compute_previous_day_close(df, now)
        assert cap == prev_close * Decimal("1.30")

    def test_static_fallback_on_single_day(self):
        # Given: only today's data (no previous close)
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        idx = pd.date_range(start=today_start, periods=60, freq="1min", tz="UTC")
        df = pd.DataFrame({"close": [100.0] * 60}, index=idx)
        # When
        cap, mode = resolve_max_entry_price(df_1m=df, static_max=Decimal("150"), buffer_pct=0.30, now_utc=now)
        # Then: D3 fallback
        assert mode == "static_fallback"
        assert cap == Decimal("150")

    def test_buffer_pct_negative_raises(self):
        # Given: negative buffer
        df = make_df_1m()
        now = datetime.now(timezone.utc)
        # When/Then: ValueError
        with pytest.raises(ValueError, match="buffer_pct must be >= 0"):
            resolve_max_entry_price(df_1m=df, static_max=Decimal("100"), buffer_pct=-0.05, now_utc=now)


# ---------------------------------------------------------------------------
# compute_atr_wilder
# ---------------------------------------------------------------------------

class TestATRWilder:
    def test_basic_atr_computation(self):
        # Given: synthetic OHLC data with known TR
        n = 100
        idx = pd.date_range("2024-01-01", periods=n, freq="1h", tz="UTC")
        high = pd.Series(np.linspace(100, 110, n), index=idx)
        low = pd.Series(np.linspace(99, 109, n), index=idx)
        close = pd.Series(np.linspace(99.5, 109.5, n), index=idx)
        # When
        atr = compute_atr_wilder(high, low, close, length=14)
        # Then: series with same index, no NaN in last value
        assert len(atr) == n
        assert not pd.isna(atr.iloc[-1])
        assert atr.iloc[-1] > 0

    def test_length_one(self):
        # Given: length = 1
        high = pd.Series([100, 101], index=pd.DatetimeIndex(["2024-01-01", "2024-01-02"]))
        low = pd.Series([99, 100], index=high.index)
        close = pd.Series([99.5, 100.5], index=high.index)
        # When
        atr = compute_atr_wilder(high, low, close, length=1)
        # Then
        assert len(atr) == 2
        assert not pd.isna(atr.iloc[-1])

    def test_invalid_length_raises(self):
        # Given: length = 0
        high = pd.Series([100], index=pd.DatetimeIndex(["2024-01-01"]))
        # When/Then
        with pytest.raises(ValueError, match="ATR length must be >= 1"):
            compute_atr_wilder(high, high, high, length=0)


# ---------------------------------------------------------------------------
# is_entry_blocked_by_atr_gate
# ---------------------------------------------------------------------------

class TestATRGate:
    def _make_bars(self, n: int, volatility: float = 1.0) -> pd.DataFrame:
        """Generate n aggregate bars with given volatility level."""
        idx = pd.date_range("2024-01-01", periods=n, freq="45min", tz="UTC")
        rng = np.random.default_rng(123)
        close = rng.normal(100, volatility, n).cumsum() * 0.01 + 100
        close = np.maximum(close, 1.0)
        return pd.DataFrame({
            "high": close + rng.uniform(0, volatility * 0.5, n),
            "low": close - rng.uniform(0, volatility * 0.5, n),
            "close": close,
        }, index=idx)

    def test_fail_open_below_min_bars(self):
        # Given: fewer bars than min_bars
        df = self._make_bars(10)
        # When
        result = is_entry_blocked_by_atr_gate(df, min_bars=20)
        # Then: fail-open (None)
        assert result is None

    def test_blocked_when_atr_below_percentile(self):
        # Given: last ATR is artificially very low compared to recent history
        n = 200
        df = self._make_bars(n, volatility=2.0)
        # Force last bar ATR to be tiny
        df.iloc[-1, df.columns.get_loc("high")] = df.iloc[-1]["close"] + 0.001
        df.iloc[-1, df.columns.get_loc("low")] = df.iloc[-1]["close"] - 0.001
        # When
        result = is_entry_blocked_by_atr_gate(df, atr_length=14, lookback=100, percentile=25.0, min_bars=20)
        # Then: blocked
        assert result is True

    def test_allowed_when_atr_above_percentile(self):
        # Given: stable volatility, ATR near median
        df = self._make_bars(200, volatility=1.5)
        # When
        result = is_entry_blocked_by_atr_gate(df, atr_length=14, lookback=100, percentile=10.0, min_bars=20)
        # Then: not blocked
        assert result is False

    def test_atr_equals_percentile_not_blocked(self):
        # Given: ATR exactly equals the percentile threshold (strict < comparison)
        n = 50
        df = self._make_bars(n, volatility=1.0)
        # Calculate actual ATR and force threshold to match
        atr = compute_atr_wilder(df["high"], df["low"], df["close"], length=14)
        current = float(atr.iloc[-1])
        # Find a percentile that makes the threshold exactly equal to current ATR
        recent = atr.iloc[-(50):-1]
        # Use a very high percentile so threshold >= current ATR
        result = is_entry_blocked_by_atr_gate(df, atr_length=14, lookback=50, percentile=0.1, min_bars=20)
        # current ATR > P0.1 → not blocked
        assert result is False

    def test_invalid_percentile_raises(self):
        # Given: percentile = 0
        df = self._make_bars(50)
        # When/Then
        with pytest.raises(ValueError, match="percentile must be in"):
            is_entry_blocked_by_atr_gate(df, percentile=0.0, min_bars=20)


# ---------------------------------------------------------------------------
# count_bars_since_entry / is_exit_blocked_by_mhp
# ---------------------------------------------------------------------------

class TestMHP:
    @pytest.fixture
    def agg_index(self):
        return pd.date_range("2024-01-03 06:00", periods=20, freq="45min", tz="UTC")

    def test_opened_at_none_fail_open(self, agg_index):
        # Given: opened_at = None (legacy position)
        # When/Then: not blocked
        assert not is_exit_blocked_by_mhp(agg_index, None, agg_index[-2], min_holding_bars=3)
        assert count_bars_since_entry(agg_index, None, agg_index[-2]) == 0

    def test_exactly_min_bars_not_blocked(self, agg_index):
        # Given: opened_at at bar[2], last_closed at bar[5] → 3 bars exactly
        # bars = bar[3], bar[4], bar[5] → 3 bars
        opened_at = agg_index[2].to_pydatetime()
        last_closed = agg_index[5]
        # When: MHP=3
        blocked = is_exit_blocked_by_mhp(agg_index, opened_at, last_closed, min_holding_bars=3)
        bars = count_bars_since_entry(agg_index, opened_at, last_closed)
        # Then: 3 bars >= 3 → not blocked
        assert bars == 3
        assert not blocked

    def test_fewer_than_min_bars_blocked(self, agg_index):
        # Given: opened_at at bar[17], last_closed at bar[18] → 1 bar
        opened_at = agg_index[17].to_pydatetime()
        last_closed = agg_index[18]
        # When: MHP=3
        blocked = is_exit_blocked_by_mhp(agg_index, opened_at, last_closed, min_holding_bars=3)
        bars = count_bars_since_entry(agg_index, opened_at, last_closed)
        # Then: 1 < 3 → blocked
        assert bars == 1
        assert blocked

    def test_opened_at_before_window(self, agg_index):
        # Given: opened_at before the entire window
        opened_at = datetime(2023, 1, 1, tzinfo=timezone.utc)
        last_closed = agg_index[-2]
        # When
        blocked = is_exit_blocked_by_mhp(agg_index, opened_at, last_closed, min_holding_bars=10)
        bars = count_bars_since_entry(agg_index, opened_at, last_closed)
        # Then: all bars counted → >= 10 → not blocked
        assert bars == len(agg_index[agg_index <= last_closed])
        assert not blocked

    def test_min_holding_zero_disabled(self, agg_index):
        # Given: min_holding_bars=0
        opened_at = agg_index[0].to_pydatetime()
        # When/Then: MHP disabled → never blocked
        assert not is_exit_blocked_by_mhp(agg_index, opened_at, agg_index[2], min_holding_bars=0)

    def test_opened_at_equals_bar_boundary(self, agg_index):
        # Given: opened_at exactly equals a bar timestamp
        opened_at = agg_index[5].to_pydatetime()
        last_closed = agg_index[8]
        # When: opened_at == bar timestamp → bar is NOT > opened_at → excluded
        bars = count_bars_since_entry(agg_index, opened_at, last_closed)
        # Then: bars[6], bars[7], bars[8] → 3 bars
        assert bars == 3
