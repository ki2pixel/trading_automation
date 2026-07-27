#!/usr/bin/env python3
"""
Script de backfill ciblé pour ZEAL.CO (GETTEX) et NVO (XETRA).

Charge 3000+ bougies 1m historiques via MarketFlow API dans live_candles_1m
pour permettre un démarrage immédiat des stratégies 45m (cybernetic_hilbert /
momentum_based_zigzag) sans attendre 2,7–4,4 jours d'accumulation live.

Usage:
    python scripts/backfill_candles.py [--ticker ZEAL.CO] [--ticker NVO] [--range 3000]
"""

import os
import sys
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("backfill")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backtest_engine.live.utils import TICKER_MAPPING
from backtest_engine.live.paper_trading.marketflow_warmup import fetch_candles, parse_and_insert
from backtest_engine.live.connection import get_db_connection


TARGET_TICKERS = ["ZEAL.CO", "NVO"]
DEFAULT_RANGE = 3000


def main():
    parser = argparse.ArgumentParser(description="Backfill live_candles_1m from MarketFlow API")
    parser.add_argument(
        "--ticker", action="append", dest="tickers",
        help=f"Asset ticker to backfill (repeatable, default: {' '.join(TARGET_TICKERS)})",
    )
    parser.add_argument(
        "--range", type=int, default=DEFAULT_RANGE,
        help=f"Number of 1m candles to fetch (default: {DEFAULT_RANGE})",
    )
    args = parser.parse_args()

    tickers = args.tickers or TARGET_TICKERS
    range_limit = args.range

    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        logger.error("RAPIDAPI_KEY not set. Cannot proceed.")
        sys.exit(1)

    missing = [t for t in tickers if t not in TICKER_MAPPING]
    if missing:
        logger.error("No MarketFlow symbol mapping for: %s", missing)
        sys.exit(1)

    logger.info("========================================")
    logger.info("Backfill ciblé live_candles_1m")
    logger.info("Tickers: %s", tickers)
    logger.info("Range:   %d bougies 1m (~%.1f jours)", range_limit, range_limit / 1440.0)
    logger.info("========================================")

    with get_db_connection() as conn:
        for ticker in tickers:
            mf_symbol = TICKER_MAPPING[ticker]
            logger.info("Traitement de %s (MarketFlow: %s)...", ticker, mf_symbol)

            candles = fetch_candles(mf_symbol, range_limit=range_limit)
            if candles:
                parse_and_insert(ticker, candles, conn)
            else:
                logger.warning("Aucune bougie récupérée pour %s.", ticker)

    logger.info("[Backfill] Terminé.")


if __name__ == "__main__":
    main()
