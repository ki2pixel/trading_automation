#!/usr/bin/env python3
"""CLI script to demonstrate VectorBT Walk-Forward Optimization (WFO).

This script uses a simple chunking approach to split data into In-Sample (IS)
and Out-Of-Sample (OOS) windows to perform WFO. It tests a grid of parameters
in-sample and evaluates the best ones out-of-sample.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

try:
    import vectorbt as vbt
except ImportError:
    vbt = None

from backtest_engine.vectorbt_bridge.data_adapter import SheetsFinanceData


def main() -> int:
    parser = argparse.ArgumentParser(description="VectorBT Walk-Forward Optimization for HMA")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--repo-root", default=str(Path.cwd()))
    parser.add_argument("--timeframe", type=int, default=5)
    parser.add_argument("--fast-range", default="10:40:10")
    parser.add_argument("--slow-range", default="40:100:20")
    parser.add_argument("--n-windows", type=int, default=3)
    args = parser.parse_args()

    if vbt is None:
        print("Error: vectorbt is not installed.")
        return 1

    vbt_data = SheetsFinanceData.fetch_symbol(
        symbol=args.symbol,
        repo_root=Path(args.repo_root),
        timeframe_minutes=args.timeframe,
    )
    price = vbt_data.get("close")
    
    def _parse_range(s: str) -> np.ndarray:
        parts = s.split(":")
        return np.arange(int(parts[0]), int(parts[1]), int(parts[2]))

    fast_windows = _parse_range(args.fast_range)
    slow_windows = _parse_range(args.slow_range)
    
    chunk_size = len(price) // args.n_windows
    if chunk_size == 0:
        print("Error: Not enough data for the requested number of windows.")
        return 1
        
    oos_equity = [1000.0]
    
    for i in range(args.n_windows - 1):
        # In-sample: window i
        is_start = i * chunk_size
        is_end = (i + 1) * chunk_size
        is_price = price.iloc[is_start:is_end]
        
        # Out-of-sample: window i+1
        oos_start = is_end
        oos_end = (i + 2) * chunk_size
        oos_price = price.iloc[oos_start:oos_end]
        
        # Optimize In-Sample
        fast_is, slow_is = vbt.MA.run_combs(is_price, window=fast_windows, r=2)
        entries_is = fast_is.ma_crossed_above(slow_is)
        exits_is = fast_is.ma_crossed_below(slow_is)
        
        pf_is = vbt.Portfolio.from_signals(is_price, entries_is, exits_is, freq=f"{args.timeframe}min")
        is_returns = pf_is.total_return()
        best_params = is_returns.idxmax()
        
        print(f"Window {i} (IS): Best params {best_params} with return {is_returns.max()*100:.2f}%")
        
        # Test Out-Of-Sample
        fast_oos = vbt.MA.run(oos_price, window=[best_params[0]])
        slow_oos = vbt.MA.run(oos_price, window=[best_params[1]])
        
        entries_oos = fast_oos.ma_crossed_above(slow_oos)
        exits_oos = fast_oos.ma_crossed_below(slow_oos)
        
        pf_oos = vbt.Portfolio.from_signals(
            oos_price, 
            entries_oos, 
            exits_oos, 
            init_cash=oos_equity[-1], 
            freq=f"{args.timeframe}min"
        )
        
        final_val = pf_oos.value().iloc[-1] if not pf_oos.value().empty else oos_equity[-1]
        oos_equity.append(final_val)
        
        # Total return of the out-of-sample window over its starting equity
        oos_return = pf_oos.total_return().iloc[0] if hasattr(pf_oos.total_return(), "iloc") else pf_oos.total_return()
        print(f"Window {i+1} (OOS): Return {oos_return * 100:.2f}%")
        
    print(f"\nFinal WFO Equity: {oos_equity[-1]:.2f}")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
