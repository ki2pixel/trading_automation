#!/usr/bin/env python3
"""CLI script to compare backtest_engine HMA results with VectorBT re-simulation.

Usage:
    python -m backtest_engine.vectorbt_bridge.compare_hma --symbol AMS.MC

This runs the native HMA crossover strategy, extracts its entry/exit signals,
and re-runs them through ``vectorbt.Portfolio.from_signals`` with the same
commission/slippage assumptions.  The comparison report highlights any
discrepancies in trade count, PnL, drawdown and Sharpe ratio.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


from backtest_engine.data import load_canonical_market_data
from backtest_engine.strategies.hma_crossover import HMAConfigOverrides, run_hma_crossover
from backtest_engine.vectorbt_bridge.strategy_bridge import (
    compare_results,
    run_strategy_via_vectorbt,
    _extract_signals,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare HMA native vs VectorBT")
    parser.add_argument("--symbol", required=True, help="Symbol to test, e.g. AMS.MC")
    parser.add_argument("--repo-root", default=str(Path.cwd()), help="Repository root")
    parser.add_argument("--timeframe", type=int, default=5, help="Timeframe in minutes")
    parser.add_argument("--initial-capital", type=float, default=1000.0)
    parser.add_argument("--fast-len", type=int, default=20)
    parser.add_argument("--slow-len", type=int, default=55)
    parser.add_argument("--max-rows", type=int, default=None)
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    args = parser.parse_args()

    repo_root = Path(args.repo_root)

    # ---- Load data ----
    data = load_canonical_market_data(
        symbol=args.symbol,
        repo_root=repo_root,
        timeframe_minutes=args.timeframe,
        max_rows=args.max_rows,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    print(f"Loaded {len(data)} rows for {args.symbol}")

    # ---- Native run ----
    overrides = HMAConfigOverrides(
        fast_len=args.fast_len,
        slow_len=args.slow_len,
        estimated_commission_per_order_long=0.0,
        estimated_slippage_per_side_long=0.0,
    )

    native_result = run_hma_crossover(
        data=data,
        symbol=args.symbol,
        overrides=overrides,
        initial_capital=args.initial_capital,
        timeframe_minutes=args.timeframe,
        compute_full_metrics=True,
    )

    print(f"Native trades: {len(native_result.trades)}")
    print(f"Native net PnL: {native_result.metrics.get('net_pnl', 'N/A')}")

    # ---- VectorBT re-simulation ----
    pf = run_strategy_via_vectorbt(
        data=data,
        symbol=args.symbol,
        overrides=overrides,
        initial_capital=args.initial_capital,
        timeframe_minutes=args.timeframe,
    )

    print(f"VectorBT trades: {pf.trades.count()}")
    try:
        print(f"VectorBT net PnL: {float(pf.total_profit()):.4f}")
    except Exception:
        print("VectorBT net PnL: N/A")

    # ---- Comparison ----
    comparison = compare_results(native_result, pf, symbol=args.symbol)
    print("\n--- Comparison ---")
    print(json.dumps(comparison, indent=2, default=str))

    # ---- Signal sanity check ----
    entries, exits = _extract_signals(native_result)
    print(f"\nSignals extracted: {entries.sum()} entries, {exits.sum()} exits")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
