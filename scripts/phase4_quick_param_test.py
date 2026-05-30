#!/usr/bin/env python3
"""
Phase 4 — Quick manual parameter sweep on OOS hold-out folds.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

_repo = Path(__file__).resolve().parent.parent
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))

from backtest_engine.data import load_canonical_market_data
from backtest_engine.walk_forward import _run_single_backtest

# Folds from WFA hold-out (last fold OOS for each ticker)
TICKER_FOLDS = {
    "SAP":  {"oos_start": "2023-04-16", "oos_end": "2024-04-16", "currency": "EUR"},
    "LOGI": {"oos_start": "2023-06-17", "oos_end": "2024-06-17", "currency": "CHF"},
    "GMAB": {"oos_start": "2023-01-02", "oos_end": "2024-01-02", "currency": "USD"},
    "NVO":  {"oos_start": "2023-11-08", "oos_end": "2024-11-08", "currency": "DKK"},
    "AMS.MC": {"oos_start": "2023-11-14", "oos_end": "2024-11-14", "currency": "EUR"},
    "NVS":  {"oos_start": "2023-06-16", "oos_end": "2024-06-16", "currency": "CHF"},
    "SHL.DE": {"oos_start": "2023-04-20", "oos_end": "2024-04-20", "currency": "EUR"},
    "ZEAL.CO": {"oos_start": "2024-01-02", "oos_end": "2025-01-02", "currency": "DKK"},
}

BASELINE = {
    "lookback_days": 17,
    "volatility_multiplier_enter": 0.5,
    "volatility_multiplier_exit": 0.1,
    "target_daily_volatility": 0.018,
    "exit_mode": "combined",
    "stoploss_ladder_step0": -0.018,
    "stoploss_ladder_step1": -0.020,
    "stoploss_ladder_ratio0": 0.8,
    "takeprofit_ladder_step0": 0.028,
}

# Parameter variations to test
VARIANTS = {
    "baseline": BASELINE,
    "narrower_bands": {**BASELINE, "volatility_multiplier_enter": 0.3, "volatility_multiplier_exit": 0.05},
    "wider_bands": {**BASELINE, "volatility_multiplier_enter": 0.8, "volatility_multiplier_exit": 0.15},
    "shorter_lookback": {**BASELINE, "lookback_days": 10},
    "longer_lookback": {**BASELINE, "lookback_days": 25},
    "lower_vol_target": {**BASELINE, "target_daily_volatility": 0.01},
    "higher_vol_target": {**BASELINE, "target_daily_volatility": 0.025},
    "conservative_low_vol": {
        "lookback_days": 17,
        "volatility_multiplier_enter": 0.25,
        "volatility_multiplier_exit": 0.08,
        "target_daily_volatility": 0.012,
        "exit_mode": "combined",
        "stoploss_ladder_step0": -0.015,
        "stoploss_ladder_step1": -0.020,
        "stoploss_ladder_ratio0": 0.8,
        "takeprofit_ladder_step0": 0.020,
    },
}


def main() -> None:
    repo_root = Path("/home/kidpixel/trading_automation_v2")
    results = []

    for symbol, fold_info in TICKER_FOLDS.items():
        print(f"\n=== {symbol} ({fold_info['currency']}) OOS {fold_info['oos_start']} -> {fold_info['oos_end']} ===")
        data = load_canonical_market_data(
            symbol=symbol,
            repo_root=repo_root,
            processed_dir="storage/processed",
            start_date=fold_info["oos_start"],
            end_date=fold_info["oos_end"],
            timeframe_minutes=1,
        )
        if data.empty:
            print(f"  No data, skipping")
            continue

        for variant_name, params in VARIANTS.items():
            result = _run_single_backtest(
                data=data,
                symbol=symbol,
                params=params,
                initial_capital=1000.0,
                timeframe_minutes=1,
                repo_root=repo_root,
                strategy="noise_boundary_intraday",
            )
            m = result.metrics
            sharpe = m.get("sharpe_ratio")
            cagr = m.get("cagr_pct")
            mdd = m.get("max_drawdown_pct")
            trades = m.get("closed_trades")

            # Fallback for None values in formatting
            sharpe_val = sharpe if sharpe is not None else 0.0
            cagr_val = cagr if cagr is not None else 0.0
            mdd_val = mdd if mdd is not None else 0.0
            trades_val = trades if trades is not None else 0

            row = {
                "symbol": symbol,
                "currency": fold_info["currency"],
                "variant": variant_name,
                "sharpe": sharpe,
                "cagr": cagr,
                "mdd": mdd,
                "trades": trades,
                "win_rate": m.get("win_rate_pct"),
            }
            results.append(row)
            print(f"  {variant_name:20s} | Sharpe={sharpe_val:7.3f} | CAGR={cagr_val:8.1f}% | MDD={mdd_val:7.1f}% | Trades={trades_val:4d}")

    # Save results
    out_path = repo_root / "reports/noise_boundary_intraday/phase4_wfa_holdout_1m/param_sweep_results.json"
    out_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    print(f"\nResults saved to {out_path}")

    # Print best per ticker
    df = pd.DataFrame(results)
    print("\n=== Best variant per ticker (by Sharpe OOS) ===")
    for symbol in df["symbol"].unique():
        sub = df[df["symbol"] == symbol].copy()
        sub["sharpe"] = sub["sharpe"].fillna(-999.0).astype(float)
        best_idx = sub["sharpe"].idxmax()
        best = sub.loc[best_idx]
        sharpe_val = best["sharpe"] if best["sharpe"] != -999.0 else 0.0
        print(f"{symbol}: {best['variant']} (Sharpe={sharpe_val:.3f}, Trades={int(best['trades'])})")


if __name__ == "__main__":
    main()
