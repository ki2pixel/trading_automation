#!/usr/bin/env python3
"""Convert verified 1m CSV datasets to canonical snappy-compressed Parquet files.

Reads validation_report.json to select OK files, cleans and normalizes them, and
saves the results to storage/processed/market_data_1m/{symbol}.parquet.
"""

import io
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from concurrent.futures import ProcessPoolExecutor

import pandas as pd
import numpy as np

# Set up repository root
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def read_csv_robust(csv_path: Path) -> pd.DataFrame:
    """Read a CSV file, recovering any merged lines on-the-fly."""
    cleaned_lines: List[str] = []

    with open(csv_path, "r", encoding="utf-8") as f:
        # First line is the header
        header = f.readline()
        cleaned_lines.append(header)

        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            parts = line_str.split(",")
            if len(parts) == 6:
                cleaned_lines.append(line)
            elif len(parts) > 6:
                i = 0
                while i < len(parts):
                    if i + 5 < len(parts):
                        ts = parts[i]
                        open_val = parts[i+1]
                        high_val = parts[i+2]
                        low_val = parts[i+3]
                        close_val = parts[i+4]
                        next_field = parts[i+5]

                        if i + 6 < len(parts):
                            # Merged field: vol + next_ts (timestamp is 13 digits)
                            vol = next_field[:-13]
                            next_ts = next_field[-13:]
                            cleaned_lines.append(f"{ts},{open_val},{high_val},{low_val},{close_val},{vol}\n")
                            parts[i+5] = next_ts
                            i += 5
                        else:
                            vol = next_field
                            cleaned_lines.append(f"{ts},{open_val},{high_val},{low_val},{close_val},{vol}\n")
                            i += 6
                    else:
                        break
            else:
                # Under-segmented line (too few fields)
                cleaned_lines.append(line)

    csv_data = "".join(cleaned_lines)
    return pd.read_csv(io.StringIO(csv_data))


def convert_single_file(args: Tuple[Path, Path, str]) -> Dict[str, Any]:
    """Clean, normalize and serialize a single CSV file to Parquet format."""
    csv_path, output_dir, symbol = args
    parquet_path = output_dir / f"{symbol}.parquet"
    
    try:
        # 1. Read CSV using the robust line splitter
        df = read_csv_robust(csv_path)
        initial_len = len(df)

        # 2. Add symbol column
        df["symbol"] = symbol

        # 3. Convert timestamp to datetime64[ns] UTC-naive
        # pd.to_datetime with unit='ms' yields naive datetime64[ns] in UTC
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        # Drop rows with NaN timestamps or OHLC values
        df = df.dropna(subset=["timestamp", "open", "high", "low", "close"])

        # 4. Round and cast volume to int64
        df["volume"] = df["volume"].round().fillna(0).astype("int64")

        # 5. Fix potential minor OHLC price inconsistencies
        # Ensure high is the absolute maximum, and low is the absolute minimum
        df["high"] = df[["open", "high", "low", "close"]].max(axis=1)
        df["low"] = df[["open", "high", "low", "close"]].min(axis=1)

        # 6. Remove duplicate timestamps (keep the last one)
        df = df.drop_duplicates(subset=["timestamp"], keep="last")

        # 7. Sort by timestamp ascending
        df = df.sort_values(by="timestamp").reset_index(drop=True)

        # Reorder columns to match canonical schema:
        # timestamp, open, high, low, close, volume, symbol
        df = df[["timestamp", "open", "high", "low", "close", "volume", "symbol"]]

        # 8. Write to Parquet using pyarrow engine and snappy compression
        df.to_parquet(parquet_path, engine="pyarrow", compression="snappy", index=False)

        final_len = len(df)
        parquet_size = parquet_path.stat().st_size
        csv_size = csv_path.stat().st_size

        return {
            "symbol": symbol,
            "status": "success",
            "initial_rows": initial_len,
            "final_rows": final_len,
            "min_time": str(df["timestamp"].min()) if final_len > 0 else "N/A",
            "max_time": str(df["timestamp"].max()) if final_len > 0 else "N/A",
            "csv_size_bytes": csv_size,
            "parquet_size_bytes": parquet_size,
            "error": None
        }

    except Exception as e:
        return {
            "symbol": symbol,
            "status": "error",
            "initial_rows": 0,
            "final_rows": 0,
            "min_time": "N/A",
            "max_time": "N/A",
            "csv_size_bytes": csv_path.stat().st_size if csv_path.exists() else 0,
            "parquet_size_bytes": 0,
            "error": str(e)
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert validated 1m CSV data to Parquet.")
    parser.add_argument(
        "--report-file",
        type=str,
        default="financial_datasets/market_data_1m/validation_report.json",
        help="Path to validation_report.json"
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="financial_datasets/market_data_1m",
        help="Path to directory containing raw CSVs"
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
        default=15,
        help="Max number of multiprocessing workers to spawn"
    )
    args = parser.parse_args()

    report_path = Path(args.report_file).resolve()
    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()

    if not report_path.exists():
        print(f"Error: Validation report file {report_path} does not exist. Please run verify_raw_data_1m.py first.")
        sys.exit(1)

    # Load validation report
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
    except Exception as e:
        print(f"Error: Failed to parse validation report: {e}")
        sys.exit(1)

    file_entries = report_data.get("files", {})
    ok_files: List[Tuple[Path, str]] = []

    for file_name, details in file_entries.items():
        if details.get("status") == "ok":
            csv_file_path = input_dir / file_name
            # symbol is lowercase filename stem
            symbol = csv_file_path.stem.lower()
            ok_files.append((csv_file_path, symbol))

    if not ok_files:
        print("No 'ok' status files found in validation report to convert.")
        sys.exit(0)

    print(f"Found {len(ok_files)} verified CSV files to convert.")
    print(f"Creating output directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting conversion using up to {args.workers} workers...")
    start_time = time.time()

    # Prepare parallel tasks
    tasks: List[Tuple[Path, Path, str]] = []
    for csv_path, symbol in ok_files:
        tasks.append((csv_path, output_dir, symbol))

    results: List[Dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        results = list(executor.map(convert_single_file, tasks))

    elapsed = time.time() - start_time
    print(f"Conversion completed in {elapsed:.2f} seconds.\n")

    # Aggregate statistics
    successful_count = 0
    failed_count = 0
    total_initial_rows = 0
    total_final_rows = 0
    total_csv_bytes = 0
    total_parquet_bytes = 0
    global_min_time: Optional[pd.Timestamp] = None
    global_max_time: Optional[pd.Timestamp] = None

    for res in results:
        total_csv_bytes += res["csv_size_bytes"]
        if res["status"] == "success":
            successful_count += 1
            total_initial_rows += res["initial_rows"]
            total_final_rows += res["final_rows"]
            total_parquet_bytes += res["parquet_size_bytes"]
            
            # Global times calculation
            if res["min_time"] != "N/A":
                min_time = pd.Timestamp(res["min_time"])
                if global_min_time is None or min_time < global_min_time:
                    global_min_time = min_time
            if res["max_time"] != "N/A":
                max_time = pd.Timestamp(res["max_time"])
                if global_max_time is None or max_time > global_max_time:
                    global_max_time = max_time
        else:
            failed_count += 1
            print(f"  [ERROR] Failed to convert {res['symbol']}: {res['error']}")

    # Calculate reduction rates
    space_saved_bytes = total_csv_bytes - total_parquet_bytes
    reduction_percent = (space_saved_bytes / total_csv_bytes * 100) if total_csv_bytes > 0 else 0.0

    print("=" * 50)
    print(" CONVERSION BILLAN FINAL")
    print("=" * 50)
    print(f"Converted files successfully : {successful_count}")
    print(f"Failed conversions           : {failed_count}")
    print(f"Total Rows Ingested          : {total_final_rows:,}")
    print(f"Global Time Range            : {global_min_time} to {global_max_time}")
    print(f"Total Original CSV Size      : {total_csv_bytes / (1024 * 1024):.2f} MB")
    print(f"Total Compressed Parquet Size: {total_parquet_bytes / (1024 * 1024):.2f} MB")
    print(f"Space Saved                  : {space_saved_bytes / (1024 * 1024):.2f} MB ({reduction_percent:.2f}% reduction)")
    print("=" * 50)


if __name__ == "__main__":
    main()
