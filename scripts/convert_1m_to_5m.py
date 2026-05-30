#!/usr/bin/env python3
"""
Pre-convert 1m canonical market data to 5m timeframe for target tickers.
This avoids resampling on the fly in backtests and speeds up optimization.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
import pandas as pd

# Ensure repo root is on path for absolute imports
_repo = Path(__file__).resolve().parent.parent
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))

from backtest_engine.data import load_canonical_market_data, resample_canonical_market_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("convert_1m_to_5m")

TICKERS = ["NVS", "LOGI", "SAP", "AMS.MC", "SHL.DE", "NVO", "GMAB", "ZEAL.CO"]

def main() -> None:
    repo_root = Path("/home/kidpixel/trading_automation_v2")
    processed_dir = repo_root / "storage/processed"
    out_dir = processed_dir / "market_data_5m"
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting 1m to 5m resampling...")
    for symbol in TICKERS:
        logger.info(f"Processing {symbol}...")
        try:
            # Load all available 1m data
            df_1m = load_canonical_market_data(
                symbol=symbol,
                repo_root=repo_root,
                processed_dir=processed_dir,
                timeframe_minutes=1,
            )
            logger.info(f"  Loaded {len(df_1m)} rows of 1m data.")

            # Resample to 5m
            df_5m = resample_canonical_market_data(
                df_1m,
                timeframe_minutes=5,
                base_minutes=1,
            )
            logger.info(f"  Resampled to {len(df_5m)} rows of 5m data.")

            # Save as Parquet
            out_path = out_dir / f"{symbol}.parquet"
            df_5m.to_parquet(out_path)
            logger.info(f"  Saved to {out_path}")

        except Exception as e:
            logger.error(f"  Failed to convert {symbol}: {e}")

    logger.info("All ticker conversions completed successfully!")

if __name__ == "__main__":
    main()
