#!/usr/bin/env python3
"""Validate canonical 1m datasets by loading them via backtest_engine."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backtest_engine.data import load_canonical_market_data

REPO_ROOT = Path(__file__).resolve().parent.parent

SYMBOLS = [
    "EURUSD",
    "TATASTEEL", "ADANIPOWER", "CANBK", "PNB", "TMPV",
    "ETERNAL", "BEL", "SBIN", "MOTHERSON", "BHEL"
]


def main() -> None:
    ok_count = 0
    fail_count = 0
    for sym in SYMBOLS:
        try:
            df = load_canonical_market_data(
                symbol=sym,
                repo_root=REPO_ROOT,
                processed_dir="storage/processed",
                timeframe_minutes=1,
            )
            # Compute gap metrics manually
            diffs = df.index.to_series().diff().dropna()
            max_gap = diffs.max()
            gap_count = int((diffs > pd.Timedelta(minutes=1)).sum())
            print(
                f"OK   {sym:12s}  rows={len(df):>9,}  "
                f"range={str(df.index.min())[:19]} -> {str(df.index.max())[:19]}  "
                f"gaps={gap_count:>6,}  max_gap={max_gap}"
            )
            ok_count += 1
        except Exception as exc:
            print(f"FAIL {sym:12s}  {exc}")
            fail_count += 1
    print(f"\nSummary: {ok_count} OK, {fail_count} FAIL")
    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    import pandas as pd
    main()
