"""Data adapter: convert SheetsFinance canonical data to VectorBT-compatible format.

VectorBT accepts any pandas DataFrame/Series with a DatetimeIndex.  The main
``Portfolio.from_signals`` method needs at minimum a "close" price array.
This module thinly wraps our existing ``load_canonical_market_data`` so that
VectorBT can consume the same parquet/csv files the backtest_engine already
uses.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

try:
    import vectorbt as vbt
    from vectorbt.data.base import Data
except ImportError:
    vbt = None
    Data = object  # type: ignore


def load_sheetsfinance_to_vectorbt(
    symbol: str,
    *,
    repo_root: Path | None = None,
    processed_dir: str | Path = "storage/processed",
    timeframe_minutes: int = 5,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """Load canonical market data and return a VectorBT-compatible DataFrame.

    Parameters
    ----------
    symbol: trading symbol (e.g. ``"AMS.MC"``).
    repo_root: root of the repository; defaults to the parent of
        ``backtest_engine/``.
    processed_dir: relative path under *repo_root* where canonical datasets live.
    timeframe_minutes: aggregation interval (must match canonical files).
    start_date: inclusive ISO date string ``"YYYY-MM-DD"`` or ``None``.
    end_date: inclusive ISO date string ``"YYYY-MM-DD"`` or ``None``.

    Returns
    -------
    DataFrame with DatetimeIndex and columns ``open, high, low, close, volume``.
    """
    # Avoid a hard import-time dependency on backtest_engine.data — lazily
    # import so the bridge can be inspected even when that module is not
    # directly on the path.
    from backtest_engine.data import load_canonical_market_data

    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[3]

    df = load_canonical_market_data(
        symbol=symbol,
        repo_root=repo_root,
        processed_dir=processed_dir,
        timeframe_minutes=timeframe_minutes,
        start_date=start_date,
        end_date=end_date,
    )

    # VectorBT is case-insensitive for column names but we keep our lowercase
    # convention for consistency with the converted Pine strategies.
    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Canonical data missing columns {sorted(missing)} for {symbol}")

    return df[list(required)].copy()


if vbt is not None:
    class SheetsFinanceData(Data):  # type: ignore
        """Native VectorBT Data class for SheetsFinance canonical datasets."""

        @classmethod
        def fetch_symbol(
            cls,
            symbol: str,
            *,
            repo_root: Path | None = None,
            processed_dir: str | Path = "storage/processed",
            timeframe_minutes: int = 5,
            start_date: str | None = None,
            end_date: str | None = None,
            **kwargs: Any
        ) -> "SheetsFinanceData":
            """Fetch canonical data for a single symbol and return a VectorBT Data object."""
            df = load_sheetsfinance_to_vectorbt(
                symbol=symbol,
                repo_root=repo_root,
                processed_dir=processed_dir,
                timeframe_minutes=timeframe_minutes,
                start_date=start_date,
                end_date=end_date,
            )
            # VectorBT Data expects a dict of dataframes for each symbol
            return cls.from_data({symbol: df}, **kwargs)
