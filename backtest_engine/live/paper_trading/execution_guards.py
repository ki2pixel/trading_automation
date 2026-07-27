"""
Execution guards for SignalExecutor entry/exit validation.

Pure functions — no database I/O, no mutable state.
- Max Entry Price (MEP): caps entry price to previous-day close × (1 + buffer_pct).
- ATR Gate: blocks entry when current ATR is below a percentile of recent history.
- Minimum Holding Period (MHP): blocks exit signals for N closed bars after entry.

Price limits use Decimal (financial precision per §2.2). ATR computation
uses float for vectorized performance (compatible with Pandas/NumPy).
"""

import logging
from decimal import Decimal
from typing import Optional, Tuple

import pandas as pd

from datetime import datetime, timezone

logger = logging.getLogger("papertrader.execution_guards")


def compute_previous_day_close(
    df_1m: pd.DataFrame,
    now_utc: datetime,
) -> Optional[Decimal]:
    """
    Close of the last completed calendar day strictly before now_utc.

    Uses resample('D').last() on the 1m DataFrame, then picks the row
    where the day is < date(now_utc).  Returns None when no such day exists
    (e.g. only intra-day data for a single day).
    """
    if df_1m.empty:
        return None
    close = df_1m.get("close")
    if close is None or close.empty:
        return None

    daily_close = close.resample("D").last().dropna()
    if daily_close.empty:
        return None

    today_utc = now_utc.date()
    prev_days = daily_close[daily_close.index.date < today_utc]
    if prev_days.empty:
        return None

    return Decimal(str(prev_days.iloc[-1]))


def resolve_max_entry_price(
    *,
    df_1m: pd.DataFrame,
    static_max: Decimal,
    buffer_pct: float,
    now_utc: datetime,
) -> Tuple[Decimal, str]:
    """
    Return (cap, mode):
    - 'dynamic': previous-day close × (1 + buffer_pct)
    - 'static_fallback': static_max from config (fallback D2)

    Raises ValueError on degenerate inputs (e.g. buffer_pct < 0).
    """
    if buffer_pct < 0:
        raise ValueError(f"buffer_pct must be >= 0, got {buffer_pct}")

    prev_close = compute_previous_day_close(df_1m, now_utc)
    if prev_close is None:
        logger.info(
            "[ExecutionGuards] No previous day close — static fallback cap=%.6f",
            float(static_max),
        )
        return static_max, "static_fallback"

    cap = prev_close * Decimal(str(1.0 + buffer_pct))
    logger.info(
        "[ExecutionGuards] Dynamic MEP cap=%.6f (prev_close=%.6f, buffer=%.2f%%)",
        float(cap),
        float(prev_close),
        buffer_pct * 100,
    )
    return cap, "dynamic"


def compute_atr_wilder(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    length: int,
) -> pd.Series:
    """
    ATR using Wilder's smoothing (TradingView RMA, alpha=1/length).

    Returns a pd.Series aligned with the input index (first `length`
    values are warmed by ewm min_periods=1 for early bars).
    """
    if length < 1:
        raise ValueError(f"ATR length must be >= 1, got {length}")

    def _true_range(h: pd.Series, l: pd.Series, c: pd.Series) -> pd.Series:
        prev_c = c.shift(1)
        return pd.concat(
            [
                h - l,
                (h - prev_c).abs(),
                (l - prev_c).abs(),
            ],
            axis=1,
        ).max(axis=1)

    def _rma(series: pd.Series, n: int) -> pd.Series:
        return series.ewm(alpha=1.0 / n, adjust=False, min_periods=1).mean()

    return _rma(_true_range(high, low, close), length)


def is_entry_blocked_by_atr_gate(
    df_closed: pd.DataFrame,
    *,
    atr_length: int = 14,
    lookback: int = 100,
    percentile: float = 25.0,
    min_bars: int = 20,
) -> Optional[bool]:
    """
    True → entry blocked (current ATR < percentile threshold).
    None → insufficient data (< min_bars closed bars) → fail-open (D3).
    False → entry allowed.

    df_closed: DataFrame of CLOSED aggregate bars (index=DatetimeIndex tz-aware)
               with columns 'high', 'low', 'close' (float).
    """
    if len(df_closed) < min_bars:
        logger.info(
            "[ExecutionGuards] ATR gate fail-open: %d closed bars < min_bars=%d",
            len(df_closed), min_bars,
        )
        return None

    if percentile <= 0 or percentile >= 100:
        raise ValueError(f"percentile must be in (0, 100), got {percentile}")

    atr_series = compute_atr_wilder(
        df_closed["high"].astype(float),
        df_closed["low"].astype(float),
        df_closed["close"].astype(float),
        length=atr_length,
    )

    current_atr = atr_series.iloc[-1]
    if pd.isna(current_atr):
        logger.warning("[ExecutionGuards] ATR gate fail-open: current ATR is NaN")
        return None

    window = min(lookback, len(atr_series) - 1)
    if window < 1:
        return None

    recent_atr = atr_series.iloc[-(window + 1):-1]
    threshold = float(recent_atr.quantile(percentile / 100.0))

    blocked = float(current_atr) < threshold
    logger.info(
        "[ExecutionGuards] ATR gate: current=%.6f, thr=%.6f (P%.1f, n=%d) → %s",
        float(current_atr), threshold, percentile, len(recent_atr),
        "BLOCKED" if blocked else "ALLOWED",
    )
    return blocked


def count_bars_since_entry(
    agg_index: pd.DatetimeIndex,
    opened_at: datetime,
    last_closed_time: pd.Timestamp,
) -> int:
    """
    Count closed aggregate bars since entry.

    Bars with index > bar_containing(opened_at) and index <= last_closed_time.
    Robust to market closures — counts actual bars, not calendar time.
    """
    if opened_at is None:
        return 0
    idx = agg_index
    if idx.tz is None and opened_at.tzinfo is None:
        pass
    elif idx.tz is None:
        idx = idx.tz_localize("UTC")
    elif opened_at.tzinfo is not None:
        pass
    else:
        opened_at = opened_at.replace(tzinfo=timezone.utc)

    after_entry = idx[idx > opened_at]
    bars = after_entry[after_entry <= last_closed_time]
    return len(bars)


def is_exit_blocked_by_mhp(
    agg_index: pd.DatetimeIndex,
    opened_at: Optional[datetime],
    last_closed_time: pd.Timestamp,
    min_holding_bars: int = 3,
) -> bool:
    """
    True → exit blocked by MHP (fewer than min_holding_bars closed candles
    since entry).  opened_at=None (legacy position) → fail-open (D3).
    """
    if min_holding_bars <= 0 or opened_at is None:
        return False

    bars_since = count_bars_since_entry(agg_index, opened_at, last_closed_time)
    blocked = bars_since < min_holding_bars

    if blocked:
        logger.info(
            "[ExecutionGuards] MHP blocked: %d bars since entry < min=%d",
            bars_since, min_holding_bars,
        )
    return blocked
