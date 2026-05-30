#!/usr/bin/env python3
"""
Phase 4 — Optimisation bayésienne rapide par devise (1m).

Usage:
    python scripts/phase4_optim_by_currency.py --symbol SAP --currency EUR --trials 20
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure repo root is on path
_repo = Path(__file__).resolve().parent.parent
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))

from backtest_engine.optimizer import ParameterGridSpec, load_data_and_optimize

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("phase4_optim_currency")


def main() -> None:
    p = argparse.ArgumentParser(description="Phase 4 — Quick Bayesian Optim by Currency")
    p.add_argument("--symbol", required=True, help="Ticker symbol")
    p.add_argument("--currency", required=True, help="Currency label for output naming")
    p.add_argument("--start-date", default="2021-01-01", help="IS start date")
    p.add_argument("--end-date", default="2023-01-01", help="IS end date")
    p.add_argument("--trials", type=int, default=20, help="Bayesian trials")
    p.add_argument("--timeframe-minutes", type=int, default=1)
    p.add_argument("--repo-root", default=".")
    p.add_argument("--output-dir", default="reports/noise_boundary_intraday/phase4_wfa_holdout_1m/optim")
    args = p.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    specs = [
        ParameterGridSpec("lookback_days", "numeric", (5, 6, 30)),
        ParameterGridSpec("volatility_multiplier_enter", "numeric", (0.5, 0.6, 3.0)),
        ParameterGridSpec("volatility_multiplier_exit", "numeric", (0.1, 0.2, 2.0)),
        ParameterGridSpec("target_daily_volatility", "numeric", (0.005, 0.006, 0.02)),
        ParameterGridSpec("exit_mode", "choice", ("time_only", "vwap", "ladder", "combined")),
        ParameterGridSpec("stoploss_ladder_step0", "numeric", (-0.020, -0.019, -0.002)),
        ParameterGridSpec("stoploss_ladder_step1", "numeric", (-0.030, -0.029, -0.005)),
        ParameterGridSpec("stoploss_ladder_ratio0", "numeric", (0.1, 0.2, 0.9)),
        ParameterGridSpec("takeprofit_ladder_step0", "numeric", (0.005, 0.006, 0.030)),
    ]

    logger.info("Starting optimization for %s (%s) %s -> %s (%d trials, %dm)",
                args.symbol, args.currency, args.start_date, args.end_date, args.trials, args.timeframe_minutes)

    summary = load_data_and_optimize(
        repo_root=repo_root,
        symbol=args.symbol,
        processed_dir="storage/processed",
        output_root=output_dir / f"{args.symbol}_{args.currency}",
        strategy="noise_boundary_intraday",
        score_metric="sharpe_ratio",
        score_direction="max",
        timeframe_minutes=args.timeframe_minutes,
        parameter_specs=specs,
        optimization_mode="bayesian",
        max_iterations=args.trials,
        workers=1,
        enable_convergence_stop=True,
        convergence_patience=max(10, args.trials // 2),
        convergence_window_size=5,
        start_date=args.start_date,
        end_date=args.end_date,
    )

    logger.info("Optimization finished. Output: %s", summary.output_dir)
    if summary.best_row:
        logger.info("Best Sharpe IS: %.3f | Params: %s",
                    summary.best_row.get("score", "N/A"),
                    summary.best_row.get("parameters", {}))

    # Write a small JSON summary
    result = {
        "symbol": args.symbol,
        "currency": args.currency,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "trials": args.trials,
        "timeframe_minutes": args.timeframe_minutes,
        "best_row": summary.best_row,
        "output_dir": str(summary.output_dir),
    }
    out_path = output_dir / f"{args.symbol}_{args.currency}_summary.json"
    out_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    logger.info("Summary written to %s", out_path)


if __name__ == "__main__":
    main()
