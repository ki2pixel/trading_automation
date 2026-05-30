#!/usr/bin/env python3
"""Demonstrate VectorBT's core strength: vectorised multi-parameter exploration.

This script runs a simple dual-HMA crossover across a grid of (fast, slow)
lengths *in one shot*, using VectorBT's native indicator factory and
portfolio simulation.  It shows the kind of rapid exploration that would
be impossible with our bar-by-bar Pine engine.

Usage:
    python -m backtest_engine.vectorbt_bridge.vectorized_exploration --symbol AMS.MC
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from backtest_engine.data import load_canonical_market_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Vectorised HMA parameter sweep via VectorBT")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--repo-root", default=str(Path.cwd()))
    parser.add_argument("--timeframe", type=int, default=5)
    parser.add_argument("--max-rows", type=int, default=5000)
    parser.add_argument("--fast-range", default="5:50:5", help="start:stop:step for fast HMA")
    parser.add_argument("--slow-range", default="20:100:10", help="start:stop:step for slow HMA")
    args = parser.parse_args()

    import vectorbt as vbt

    data = load_canonical_market_data(
        symbol=args.symbol,
        repo_root=Path(args.repo_root),
        timeframe_minutes=args.timeframe,
        max_rows=args.max_rows,
    )
    price = data["close"]

    # Parse parameter ranges
    def _parse_range(s: str):
        parts = s.split(":")
        return np.arange(int(parts[0]), int(parts[1]), int(parts[2]))

    fast_windows = _parse_range(args.fast_range)
    slow_windows = _parse_range(args.slow_range)

    print(f"Exploring {len(fast_windows)} fast x {len(slow_windows)} slow = {len(fast_windows)*len(slow_windows)} combinations")

    # ---- VectorBT indicator factory ----
    # Create a custom HMA indicator using IndicatorFactory
    # For simplicity we use rolling_mean as a proxy; real HMA is WMA-based.
    # VectorBT's built-in MA indicator is sufficient for this demo.

    fast_ma, slow_ma = vbt.MA.run_combs(
        price,
        window=fast_windows,
        r=2,
        short_names=["fast", "slow"],
    )

    entries = fast_ma.ma_crossed_above(slow_ma)
    exits = fast_ma.ma_crossed_below(slow_ma)

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
    trades = pf.trades.count()
    max_dd = pf.drawdown().max() * 100

    # Build summary table
    summary = []
    for idx in total_return.index:
        summary.append({
            "fast_window": idx[0],
            "slow_window": idx[1],
            "total_return_pct": round(float(total_return[idx]) * 100, 2),
            "sharpe": round(float(sharpe[idx]), 4) if not pd.isna(sharpe[idx]) else None,
            "trades": int(trades[idx]),
            "max_drawdown_pct": round(float(max_dd[idx]), 4) if not pd.isna(max_dd[idx]) else None,
        })

    # Sort by total return descending
    summary.sort(key=lambda x: x["total_return_pct"], reverse=True)

    print(f"\nTop 10 configurations by total return:")
    for row in summary[:10]:
        print(json.dumps(row, default=str))

    # Save full results
    out_path = Path(args.repo_root) / "reports" / "vectorbt_exploration.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2, default=str))
    print(f"\nFull results written to: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
