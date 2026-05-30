#!/usr/bin/env python3
"""Convert Kaggle 1-minute datasets to canonical parquet for backtest_engine."""

import pandas as pd
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
FINANCIAL_DATASETS = REPO_ROOT / "financial_datasets"
OUTPUT_DIR = REPO_ROOT / "storage" / "processed" / "market_data_1m"

# Top 10 most liquid symbols by total volume
MARKET_SYMBOLS = [
    "TATASTEEL", "ADANIPOWER", "CANBK", "PNB", "TMPV",
    "ETERNAL", "BEL", "SBIN", "MOTHERSON", "BHEL"
]


def convert_eurusd() -> None:
    """Convert EURUSD ASCII CSVs to canonical parquet."""
    fx_dir = FINANCIAL_DATASETS / "fx_data" / "eurusd"
    csv_files = sorted(fx_dir.rglob("DAT_ASCII_EURUSD_M1_*.csv"))
    if not csv_files:
        print("No EURUSD CSV files found.")
        return

    chunks = []
    for f in csv_files:
        print(f"Reading {f.name} ...")
        df = pd.read_csv(
            f,
            sep=";",
            header=None,
            names=["timestamp", "open", "high", "low", "close", "volume"],
            dtype={"timestamp": str, "open": str, "high": str, "low": str, "close": str, "volume": str},
        )
        chunks.append(df)

    df = pd.concat(chunks, ignore_index=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y%m%d %H%M%S", errors="coerce")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["timestamp", "open", "high", "low", "close"])
    df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"], keep="last")
    df["symbol"] = "EURUSD"

    out_path = OUTPUT_DIR / "EURUSD.parquet"
    df.to_parquet(out_path, index=False)
    print(f"EURUSD -> {out_path} ({len(df):,} rows, {df['timestamp'].min()} -> {df['timestamp'].max()})")


def convert_market_symbol(symbol: str) -> None:
    """Convert a single market_data CSV to canonical parquet."""
    csv_path = FINANCIAL_DATASETS / "market_data" / f"{symbol}_minute.csv"
    if not csv_path.exists():
        print(f"Missing file for {symbol}: {csv_path}")
        return

    print(f"Reading {csv_path.name} ...")
    df = pd.read_csv(csv_path)
    df = df.rename(columns={"date": "timestamp"})
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["timestamp", "open", "high", "low", "close"])
    df = df.sort_values("timestamp").drop_duplicates(subset=["timestamp"], keep="last")
    df["symbol"] = symbol

    out_path = OUTPUT_DIR / f"{symbol}.parquet"
    df.to_parquet(out_path, index=False)
    print(f"{symbol} -> {out_path} ({len(df):,} rows, {df['timestamp'].min()} -> {df['timestamp'].max()})")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Converting EURUSD")
    print("=" * 60)
    convert_eurusd()

    print()
    print("=" * 60)
    print("Converting market_data symbols")
    print("=" * 60)
    for sym in MARKET_SYMBOLS:
        convert_market_symbol(sym)

    print()
    print("Done.")


if __name__ == "__main__":
    main()
