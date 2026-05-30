#!/usr/bin/env python3
"""Convert Dukascopy 1m CSV datasets to canonical Parquet files with volume.

The script reads CSVs from financial_datasets/market_data_1m/, formats the data
to match the canonical schema, validates basic properties, and writes them to
storage/processed/market_data_1m/.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Set up repository root
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

INPUT_DIR = REPO_ROOT / "financial_datasets" / "market_data_1m"
OUTPUT_DIR = REPO_ROOT / "storage" / "processed" / "market_data_1m"

def main():
    if not INPUT_DIR.exists():
        print(f"Error: Input directory {INPUT_DIR} does not exist.")
        sys.exit(1)
        
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    csv_files = sorted(INPUT_DIR.glob("*.csv"))
    if not csv_files:
        print("No CSV files found in input directory.")
        sys.exit(0)
        
    print(f"Found {len(csv_files)} CSV files to process.")
    
    for csv_path in csv_files:
        symbol = csv_path.stem
        output_path = OUTPUT_DIR / f"{symbol}.parquet"
        print(f"\nProcessing {symbol} ({csv_path.name}) -> {output_path.name}...")
        
        try:
            # 1. Read CSV
            df = pd.read_csv(csv_path)
            initial_len = len(df)
            
            # Verify required columns exist
            required_cols = ["timestamp", "open", "high", "low", "close", "volume"]
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                print(f"  [ERROR] Missing columns {missing} in {csv_path.name}. Skipping.")
                continue
                
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
            # (ensure high is the absolute maximum, and low is the absolute minimum)
            df["high"] = df[["open", "high", "low", "close"]].max(axis=1)
            df["low"] = df[["open", "high", "low", "close"]].min(axis=1)
            
            # 6. Remove duplicate timestamps (keep the last one)
            df = df.drop_duplicates(subset=["timestamp"], keep="last")
            
            # 7. Sort by timestamp ascending
            df = df.sort_values(by="timestamp").reset_index(drop=True)
            
            # Reorder columns to match original canonical format:
            # timestamp, open, high, low, close, volume, symbol
            df = df[["timestamp", "open", "high", "low", "close", "volume", "symbol"]]
            
            # 8. Write to Parquet (overwriting the old one)
            df.to_parquet(output_path, index=False)
            
            final_len = len(df)
            removed = initial_len - final_len
            print(f"  [OK] Successfully converted {symbol}. Rows: {final_len:,} (removed {removed:,} duplicates/NaNs).")
            print(f"       Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            
        except Exception as e:
            print(f"  [ERROR] Failed to convert {symbol}: {e}")
            
    print("\nConversion finished.")

if __name__ == "__main__":
    main()
