#!/usr/bin/env python3
"""Validate the newly resampled 5m Parquet files using load_canonical_market_data."""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Set up repository root
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from backtest_engine.data import load_canonical_market_data

SYMBOLS = ["AMS.MC", "LOGI", "NVS", "NVO", "SAP", "SHL.DE"]

def main():
    print("Starting validation of resampled 5m Parquet files...")
    all_ok = True
    
    for symbol in SYMBOLS:
        print(f"\nValidating 5m data for {symbol}...")
        try:
            # 1. Load the canonical 5m data
            df = load_canonical_market_data(
                symbol=symbol,
                repo_root=REPO_ROOT,
                processed_dir="storage/processed",
                timeframe_minutes=5,
                apply_market_hours=False  # Do not filter market hours for this structural test
            )
            
            errors = []
            
            # 2. Check DatetimeIndex
            if not isinstance(df.index, pd.DatetimeIndex):
                errors.append("Index is not a DatetimeIndex.")
            elif df.index.isna().any():
                errors.append("DatetimeIndex contains NaN values.")
            elif not df.index.is_monotonic_increasing:
                errors.append("DatetimeIndex is not chronologically sorted.")
                
            # 3. Check columns presence
            required = ["open", "high", "low", "close", "volume"]
            missing = [c for c in required if c not in df.columns]
            if missing:
                errors.append(f"Missing required columns: {missing}")
                
            # 4. Check for NaNs in OHLC
            for col in ["open", "high", "low", "close"]:
                if col in df.columns and df[col].isna().any():
                    errors.append(f"Column '{col}' contains NaN values.")
                    
            # 5. Check for invalid OHLC rows
            if all(c in df.columns for c in ["open", "high", "low", "close"]):
                o = df["open"]
                h = df["high"]
                l = df["low"]
                c = df["close"]
                valid_ohlc = (l <= np.minimum(o, c)) & (h >= np.maximum(o, c)) & (l <= h)
                invalid_count = (~valid_ohlc).sum()
                if invalid_count > 0:
                    errors.append(f"Contains {invalid_count} invalid OHLC rows.")
                    
            # 6. Check volume presence and type
            if "volume" not in df.columns:
                errors.append("Volume column is missing.")
            else:
                if not np.issubdtype(df["volume"].dtype, np.integer):
                    errors.append(f"Volume column has type {df['volume'].dtype}, expected integer.")
                non_zero_vol = (df["volume"] > 0).sum()
                if non_zero_vol == 0:
                    errors.append("All volume values are 0 (unexpected after resampling).")
                else:
                    print(f"  [INFO] Volume has {non_zero_vol:,} non-zero values out of {len(df):,} rows.")
            
            # Print status
            if errors:
                print(f"  [FAIL] {symbol} (5m) failed validation with {len(errors)} error(s):")
                for err in errors:
                    print(f"    - {err}")
                all_ok = False
            else:
                print(f"  [OK] {symbol} (5m) passed all compatibility checks.")
                print(f"       Rows: {len(df):,}")
                print(f"       Start: {df.index.min()}")
                print(f"       End:   {df.index.max()}")
                
        except Exception as e:
            print(f"  [CRITICAL ERROR] Failed to load/validate {symbol} (5m): {e}")
            all_ok = False
            
    print("\n" + "="*50)
    if all_ok:
        print("ALL 5m SYMBOLS VALIDATED SUCCESSFULLY AND ARE COMPATIBLE!")
        sys.exit(0)
    else:
        print("SOME 5m VALIDATIONS FAILED. SEE DETAILS ABOVE.")
        sys.exit(1)

if __name__ == "__main__":
    main()
