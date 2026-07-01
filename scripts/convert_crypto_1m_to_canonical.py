#!/usr/bin/env python3
"""Convert crypto CSV and spot Parquet datasets to canonical snappy-compressed Parquet files.

Fuses deep historical CSVs with recent spot Parquet data for BTC and ETH,
and filters other spot Parquet assets based on history length (>= 3 years).
"""

import sys
import argparse
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from concurrent.futures import ProcessPoolExecutor

import pandas as pd
import numpy as np

# Set up repository root
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def check_parquet_history_years(file_path: Path) -> float:
    """Read first and last timestamp from a parquet file to evaluate history length."""
    try:
        df_time = pd.read_parquet(file_path, columns=["d"])
        if df_time.empty:
            return 0.0
        first_ts = df_time["d"].iloc[0]
        last_ts = df_time["d"].iloc[-1]
        
        # Convert to tz-naive if tz-aware
        if hasattr(first_ts, "tzinfo") and first_ts.tzinfo is not None:
            first_ts = first_ts.tz_localize(None)
            last_ts = last_ts.tz_localize(None)
            
        days = (last_ts - first_ts).days
        return days / 365.25
    except Exception as e:
        print(f"Error reading timestamps for {file_path.name}: {e}")
        return 0.0


def normalize_and_save_dataframe(df: pd.DataFrame, symbol: str, output_path: Path) -> int:
    """Clean, normalize and serialize a DataFrame to Parquet format."""
    # Ensure canonical columns exist
    df = df.dropna(subset=["timestamp", "open", "high", "low", "close"])
    
    # 1. Price validation
    df["high"] = df[["open", "high", "low", "close"]].max(axis=1)
    df["low"] = df[["open", "high", "low", "close"]].min(axis=1)
    
    # 2. Keep volume as float
    df["volume"] = df["volume"].astype(float).fillna(0.0)
    
    # 3. Add symbol column
    df["symbol"] = symbol
    
    # 4. Remove duplicate timestamps (keep the last one)
    df = df.drop_duplicates(subset=["timestamp"], keep="last")
    
    # 5. Sort by timestamp ascending
    df = df.sort_values(by="timestamp").reset_index(drop=True)
    
    # 6. Reorder columns to match canonical schema:
    # timestamp, open, high, low, close, volume, symbol
    df = df[["timestamp", "open", "high", "low", "close", "volume", "symbol"]]
    
    # 7. Write to Parquet using pyarrow engine and snappy compression
    df.to_parquet(output_path, engine="pyarrow", compression="snappy", index=False)
    
    return len(df)


def process_altcoin_file(args: Tuple[Path, Path, str]) -> Dict[str, Any]:
    """Process a single altcoin Parquet file from spot directory."""
    input_path, output_dir, symbol = args
    output_path = output_dir / f"{symbol}.parquet"
    
    try:
        # Load parquet
        df = pd.read_parquet(input_path)
        
        # Rename columns: d -> timestamp, o/h/l/c/v -> open/high/low/close/volume
        df = df.rename(columns={
            "d": "timestamp",
            "o": "open",
            "h": "high",
            "l": "low",
            "c": "close",
            "v": "volume"
        })
        
        # Convert timestamp to UTC-naive
        if df["timestamp"].dt.tz is not None:
            df["timestamp"] = df["timestamp"].dt.tz_localize(None)
            
        final_len = normalize_and_save_dataframe(df, symbol, output_path)
        
        return {
            "symbol": symbol,
            "status": "success",
            "rows": final_len,
            "error": None
        }
    except Exception as e:
        return {
            "symbol": symbol,
            "status": "error",
            "rows": 0,
            "error": str(e)
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert and fuse crypto market data.")
    parser.add_argument(
        "--input-dir",
        type=str,
        default="financial_datasets/market_data_1m",
        help="Path to directory containing crypto CSVs and spot folder"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="storage/processed/market_data_1m",
        help="Path where Parquet files will be saved"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Max number of multiprocessing workers to spawn"
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir).resolve()
    spot_dir = input_dir / "spot"
    output_dir = Path(args.output_dir).resolve()

    if not input_dir.exists():
        print(f"Error: Input directory {input_dir} does not exist.")
        sys.exit(1)

    print(f"Creating output directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- PART 1: Priority Assets (BTC & ETH) ---
    priority_assets = [
        {
            "symbol": "btcusdt",
            "csv_name": "btcusd_bitstamp_1min_2012-2025.csv",
            "spot_name": "BTCUSDT.parquet"
        },
        {
            "symbol": "ethusdt",
            "csv_name": "ethusd_1min_ohlc.csv",
            "spot_name": "ETHUSDT.parquet"
        }
    ]

    for asset in priority_assets:
        symbol = asset["symbol"]
        csv_path = input_dir / asset["csv_name"]
        spot_path = spot_dir / asset["spot_name"]
        output_path = output_dir / f"{symbol}.parquet"

        print(f"\nProcessing priority asset: {symbol.upper()}...")
        
        # Load CSV if exists
        csv_df = pd.DataFrame()
        if csv_path.exists():
            print(f"  Loading CSV dataset: {csv_path.name}...")
            csv_df = pd.read_csv(csv_path)
            # CSV timestamps are UNIX seconds
            csv_df["timestamp"] = pd.to_datetime(csv_df["timestamp"], unit="s")
        else:
            print(f"  WARNING: CSV dataset {csv_path.name} not found.")

        # Load Spot Parquet if exists
        spot_df = pd.DataFrame()
        if spot_path.exists():
            print(f"  Loading Spot Parquet: {spot_path.name}...")
            spot_df = pd.read_parquet(spot_path)
            spot_df = spot_df.rename(columns={
                "d": "timestamp",
                "o": "open",
                "h": "high",
                "l": "low",
                "c": "close",
                "v": "volume"
            })
            if spot_df["timestamp"].dt.tz is not None:
                spot_df["timestamp"] = spot_df["timestamp"].dt.tz_localize(None)
        else:
            print(f"  WARNING: Spot Parquet {spot_path.name} not found.")

        if csv_df.empty and spot_df.empty:
            print(f"  ERROR: No data found for priority asset {symbol}.")
            continue

        # Fusion
        print(f"  Fusing datasets...")
        fused_df = pd.concat([csv_df, spot_df], ignore_index=True)
        
        # Normalize and Save
        total_rows = normalize_and_save_dataframe(fused_df, symbol, output_path)
        print(f"  Saved {total_rows:,} rows to {output_path}.")

    # --- PART 2: Other Spot Altcoins (>= 3 years history) ---
    print("\nScanning other spot altcoins in spot/ directory...")
    if not spot_dir.exists():
        print(f"Error: spot/ directory {spot_dir} does not exist.")
        sys.exit(1)

    all_spot_files = list(spot_dir.glob("*.parquet"))
    altcoin_tasks: List[Tuple[Path, Path, str]] = []

    for file_path in all_spot_files:
        stem_upper = file_path.stem.upper()
        # Skip already processed priority assets
        if stem_upper in ["BTCUSDT", "ETHUSDT"]:
            continue
            
        history_years = check_parquet_history_years(file_path)
        symbol = stem_upper.lower()
        
        if history_years >= 3.0:
            print(f"  [KEEP] {stem_upper} - History: {history_years:.2f} years (>= 3 years)")
            altcoin_tasks.append((file_path, output_dir, symbol))
        else:
            # Skip asset
            pass

    print(f"\nFound {len(altcoin_tasks)} altcoins qualifying for canonical ingestion.")
    if altcoin_tasks:
        print(f"Starting conversion using up to {args.workers} workers...")
        start_time = time.time()
        
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            results = list(executor.map(process_altcoin_file, altcoin_tasks))
            
        elapsed = time.time() - start_time
        print(f"Conversion of altcoins completed in {elapsed:.2f} seconds.")
        
        # Print summary
        success_count = sum(1 for r in results if r["status"] == "success")
        error_count = sum(1 for r in results if r["status"] == "error")
        total_rows_altcoins = sum(r["rows"] for r in results if r["status"] == "success")
        
        print(f"Successfully processed: {success_count} assets ({total_rows_altcoins:,} rows)")
        if error_count > 0:
            print(f"Failed assets: {error_count}")
            for r in results:
                if r["status"] == "error":
                    print(f"  - {r['symbol'].upper()}: {r['error']}")
    else:
        print("No other spot altcoins qualified.")

    print("\nAll operations completed successfully!")


if __name__ == "__main__":
    main()
