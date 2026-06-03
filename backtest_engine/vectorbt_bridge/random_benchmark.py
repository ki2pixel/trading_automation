#!/usr/bin/env python3
"""CLI script to generate a random signal benchmark using VectorBT.

This script loads the canonical data via SheetsFinanceData and generates
N random strategies using NumPy random choices to establish a baseline distribution
for Sharpe Ratio and Total Return.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import numpy as np

try:
    import vectorbt as vbt
except ImportError:
    vbt = None

from backtest_engine.vectorbt_bridge.data_adapter import SheetsFinanceData


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a random signal benchmark via VectorBT")
    parser.add_argument("--symbol", required=True, help="Symbol to test, e.g. AMS.MC")
    parser.add_argument("--repo-root", default=str(Path.cwd()), help="Repository root")
    parser.add_argument("--timeframe", type=int, default=5, help="Timeframe in minutes")
    parser.add_argument("--n-samples", type=int, default=100, help="Number of random paths to generate")
    parser.add_argument("--prob-enter", type=float, default=0.1, help="Probability to enter per bar")
    parser.add_argument("--prob-exit", type=float, default=0.1, help="Probability to exit per bar")
    args = parser.parse_args()

    if vbt is None:
        print("Error: vectorbt is not installed.")
        return 1

    # Fetch data natively
    vbt_data = SheetsFinanceData.fetch_symbol(
        symbol=args.symbol,
        repo_root=Path(args.repo_root),
        timeframe_minutes=args.timeframe,
    )
    
    price = vbt_data.get("close")
    
    print(f"Generating {args.n_samples} random strategies for {args.symbol}...")
    
    # Generate multiple sets of signals using numpy default_rng
    rng = np.random.default_rng()
    entries_data = rng.choice([True, False], size=(len(price), args.n_samples), p=[args.prob_enter, 1 - args.prob_enter])
    exits_data = rng.choice([True, False], size=(len(price), args.n_samples), p=[args.prob_exit, 1 - args.prob_exit])
    
    entries = pd.DataFrame(entries_data, index=price.index)
    exits = pd.DataFrame(exits_data, index=price.index)
    
    pf = vbt.Portfolio.from_signals(
        price,
        entries,
        exits,
        init_cash=1000,
        fees=0.0,
        slippage=0.0,
        freq=f"{args.timeframe}min",
    )
    
    total_return = pf.total_return()
    sharpe = pf.sharpe_ratio()
    
    # Clean up NaNs from sharpe if any (e.g. no trades or zero variance)
    sharpe = sharpe.dropna()
    
    print("\n--- Benchmark Results ---")
    print(f"Total Return: Mean = {total_return.mean()*100:.2f}%, Median = {total_return.median()*100:.2f}%, Max = {total_return.max()*100:.2f}%")
    if len(sharpe) > 0:
        print(f"Sharpe Ratio: Mean = {sharpe.mean():.4f}, Median = {sharpe.median():.4f}, Max = {sharpe.max():.4f}")
    else:
        print("Sharpe Ratio: Not enough valid paths to compute.")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
