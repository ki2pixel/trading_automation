#!/usr/bin/env python3
"""Analyze structural, chronological, and mathematical integrity of 1m CSV datasets.

Produces a detailed validation report JSON and outputs a console summary.
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


def read_csv_robust(csv_path: Path) -> Tuple[pd.DataFrame, bool, int]:
    """Read a CSV file, recovering any merged lines on-the-fly.
    
    Returns:
        DataFrame, has_corruption, count of recovered lines.
    """
    cleaned_lines: List[str] = []
    has_corruption: bool = False
    recovered_count: int = 0

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
                has_corruption = True
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
                            recovered_count += 1
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
    df = pd.read_csv(io.StringIO(csv_data))
    return df, has_corruption, recovered_count


def validate_single_file(args: Tuple[Path, Optional[Dict[str, Any]]]) -> Dict[str, Any]:
    """Validate a single CSV file and return the result dictionary."""
    csv_path, meta = args
    file_name: str = csv_path.name
    file_size: int = csv_path.stat().st_size
    errors: List[str] = []
    warnings: List[str] = []
    metrics: Dict[str, Any] = {}

    # Size check: stubs are typically ~37 bytes
    if file_size <= 100:
        return {
            "file_name": file_name,
            "status": "empty",
            "file_size_bytes": file_size,
            "errors": ["File is empty stub (header only)"],
            "warnings": [],
            "metrics": {}
        }

    try:
        df, has_corruption, recovered_count = read_csv_robust(csv_path)
        if has_corruption:
            warnings.append(f"Recovered {recovered_count} merged line(s) due to formatting corruption")
            metrics["recovered_lines_count"] = recovered_count
    except Exception as e:
        return {
            "file_name": file_name,
            "status": "ko",
            "file_size_bytes": file_size,
            "errors": [f"Failed to read CSV (with robust parsing): {e}"],
            "warnings": [],
            "metrics": {}
        }

    # Validate presence of required headers
    required_cols = ["timestamp", "open", "high", "low", "close", "volume"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        return {
            "file_name": file_name,
            "status": "ko",
            "file_size_bytes": file_size,
            "errors": [f"Missing required columns: {missing_cols}"],
            "warnings": [],
            "metrics": {}
        }

    # Check for NaN / missing values
    for col in required_cols:
        nan_count = int(df[col].isnull().sum())
        if nan_count > 0:
            errors.append(f"Column '{col}' has {nan_count} missing (NaN) values")

    df_clean = df.dropna(subset=required_cols)

    if len(df_clean) == 0:
        errors.append("No valid data rows left after removing NaNs")
        return {
            "file_name": file_name,
            "status": "ko",
            "file_size_bytes": file_size,
            "errors": errors,
            "warnings": warnings,
            "metrics": {
                "row_count": len(df),
                "clean_row_count": 0
            }
        }

    # Chronological validation
    if len(df_clean) >= 2:
        # Strictly increasing timestamps
        ts_diffs = df_clean["timestamp"].diff().dropna()
        if (ts_diffs <= 0).any():
            errors.append("Timestamps are not strictly increasing (duplicate or out-of-order timestamps found)")

        # Cadence check: must be multiples of 60,000 ms
        non_60s_multiples = ts_diffs[ts_diffs % 60000 != 0]
        if not non_60s_multiples.empty:
            errors.append(f"Found {len(non_60s_multiples)} timestamp deltas that are not multiples of 60,000 ms")

    # Gap detection and coverage ratio
    min_ts = int(df_clean["timestamp"].min())
    max_ts = int(df_clean["timestamp"].max())
    theoretical_minutes = int((max_ts - min_ts) / 60000) + 1

    if len(df_clean) >= 2:
        ts_diffs = df_clean["timestamp"].diff().dropna()
        gaps = ts_diffs[ts_diffs > 60000]
        gaps_count = len(gaps)
        max_gap_ms = int(gaps.max()) if gaps_count > 0 else 0
        max_gap_minutes = int(max_gap_ms / 60000)
    else:
        gaps_count = 0
        max_gap_minutes = 0

    coverage_ratio = float(len(df_clean) / theoretical_minutes) if theoretical_minutes > 0 else 1.0

    metrics["row_count"] = len(df)
    metrics["clean_row_count"] = len(df_clean)
    metrics["start_timestamp"] = min_ts
    metrics["end_timestamp"] = max_ts
    metrics["gaps_count"] = gaps_count
    metrics["max_gap_minutes"] = max_gap_minutes
    metrics["coverage_ratio"] = round(coverage_ratio, 6)

    # Mathematical coherence OHLCV checks
    # Prices and volumes must be >= 0
    for col in required_cols:
        if (df_clean[col] < 0).any():
            errors.append(f"Negative values detected in column '{col}'")

    # Invariants checks: high >= open, high >= close, low <= open, low <= close
    inv_high_open = df_clean["high"] < df_clean["open"]
    inv_high_close = df_clean["high"] < df_clean["close"]
    inv_low_open = df_clean["low"] > df_clean["open"]
    inv_low_close = df_clean["low"] > df_clean["close"]

    if inv_high_open.any() or inv_high_close.any() or inv_low_open.any() or inv_low_close.any():
        errors.append("OHLC physical invariants violated (high < open/close or low > open/close)")

    # Metadata alignment checks
    if meta is None:
        warnings.append("Symbol metadata config not found in instrument-meta-data.json")
    else:
        # Expected start day alignment
        start_day_str = meta.get("startDayForMinuteCandles")
        if start_day_str:
            try:
                expected_start = pd.to_datetime(start_day_str, utc=True)
                first_candle_time = pd.to_datetime(min_ts, unit="ms", utc=True)
                time_diff = abs(first_candle_time - expected_start)
                diff_hours = time_diff.total_seconds() / 3600.0
                metrics["expected_start_deviation_hours"] = round(diff_hours, 2)
                if diff_hours > 24.0:
                    warnings.append(
                        f"First timestamp deviates from expected start day '{start_day_str}' by {diff_hours:.2f} hours"
                    )
            except Exception as e:
                warnings.append(f"Failed to check startDayForMinuteCandles: {e}")

        # Price precision check against decimalFactor
        decimal_factor = meta.get("decimalFactor")
        if decimal_factor:
            try:
                decimal_factor_float = float(decimal_factor)
                price_cols = ["open", "high", "low", "close"]
                for col in price_cols:
                    scaled = df_clean[col] * decimal_factor_float
                    # Allow a small float epsilon tolerance (1e-4) for precision check
                    mismatch_mask = np.abs(scaled - np.round(scaled)) > 1e-4
                    if mismatch_mask.any():
                        mismatched_rows = df_clean.loc[mismatch_mask]
                        sample_vals = mismatched_rows[col].head(3).tolist()
                        errors.append(
                            f"Price precision mismatch for column '{col}' (decimalFactor: {decimal_factor}). "
                            f"Sample anomalies: {sample_vals}"
                        )
                        break
            except Exception as e:
                errors.append(f"Failed to perform decimalFactor check: {e}")

    status = "ko" if errors else "ok"

    return {
        "file_name": file_name,
        "status": status,
        "file_size_bytes": file_size,
        "errors": errors,
        "warnings": warnings,
        "metrics": metrics
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate raw 1m CSV data files.")
    parser.add_argument(
        "--input-dir",
        type=str,
        default="financial_datasets/market_data_1m",
        help="Path to directory containing raw CSVs"
    )
    parser.add_argument(
        "--metadata-file",
        type=str,
        default="financial_datasets/market_data_1m/instrument-meta-data.json",
        help="Path to instrument-meta-data.json"
    )
    parser.add_argument(
        "--report-file",
        type=str,
        default="financial_datasets/market_data_1m/validation_report.json",
        help="Path where report will be saved"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=15,
        help="Max number of multiprocessing workers to spawn"
    )
    args = parser.parse_args()

    input_path = Path(args.input_dir).resolve()
    metadata_path = Path(args.metadata_file).resolve()
    report_path = Path(args.report_file).resolve()

    if not input_path.exists():
        print(f"Error: Input directory {input_path} does not exist.")
        sys.exit(1)

    # Load metadata
    metadata: Dict[str, Any] = {}
    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            print(f"Loaded metadata config for {len(metadata)} instruments.")
        except Exception as e:
            print(f"Warning: Failed to load metadata file {metadata_path}: {e}")
    else:
        print(f"Warning: Metadata file {metadata_path} not found.")

    csv_files = sorted(input_path.glob("*.csv"))
    if not csv_files:
        print("No CSV files found to validate.")
        sys.exit(0)

    print(f"Starting validation of {len(csv_files)} files using up to {args.workers} workers...")
    start_time = time.time()

    # Prepare inputs for parallel map
    tasks: List[Tuple[Path, Optional[Dict[str, Any]]]] = []
    for csv_file in csv_files:
        symbol_key = csv_file.stem.lower()
        meta_cfg = metadata.get(symbol_key)
        tasks.append((csv_file, meta_cfg))

    results: List[Dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        results = list(executor.map(validate_single_file, tasks))

    elapsed = time.time() - start_time
    print(f"Validation completed in {elapsed:.2f} seconds.")

    # Aggregate counts and results
    ok_count = 0
    ko_count = 0
    empty_count = 0
    report_files: Dict[str, Dict[str, Any]] = {}

    for res in results:
        file_name = res["file_name"]
        status = res["status"]
        if status == "ok":
            ok_count += 1
        elif status == "ko":
            ko_count += 1
        elif status == "empty":
            empty_count += 1

        report_files[file_name] = {
            "status": res["status"],
            "file_size_bytes": res["file_size_bytes"],
            "errors": res["errors"],
            "warnings": res["warnings"],
            "metrics": res["metrics"]
        }

    report_data = {
        "summary": {
            "total_files": len(csv_files),
            "ok_files": ok_count,
            "ko_files": ko_count,
            "empty_files": empty_count,
            "elapsed_seconds": round(elapsed, 2)
        },
        "files": report_files
    }

    # Write report file
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        print(f"Validation report saved successfully to {report_path}")
    except Exception as e:
        print(f"Error: Failed to save validation report: {e}")

    # Output Console Summary
    print("\n" + "=" * 40)
    print(" VALIDATION SUMMARY")
    print("=" * 40)
    print(f"Total Files Checked : {len(csv_files)}")
    print(f"OK Files            : {ok_count}")
    print(f"KO Files (Errors)   : {ko_count}")
    print(f"Empty Files (Stubs) : {empty_count}")
    print("=" * 40)

    if ko_count > 0:
        print("\nSample KO files with errors:")
        sample_ko_printed = 0
        for name, details in report_files.items():
            if details["status"] == "ko":
                print(f"  - {name}:")
                for err in details["errors"]:
                    print(f"      * {err}")
                sample_ko_printed += 1
                if sample_ko_printed >= 5:
                    print("  ... (and others)")
                    break


if __name__ == "__main__":
    main()
