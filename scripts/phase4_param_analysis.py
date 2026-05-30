#!/usr/bin/env python3
"""
Phase 4 — Analyse rapide de volatilité et recommandation de paramètres
sans backtest complet.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_repo = Path(__file__).resolve().parent.parent
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))

from backtest_engine.data import load_canonical_market_data

TICKER_FOLDS = {
    "SAP":    {"is_start": "2021-04-16", "is_end": "2023-04-16", "currency": "EUR"},
    "LOGI":   {"is_start": "2021-06-17", "is_end": "2023-06-17", "currency": "CHF"},
    "GMAB":   {"is_start": "2021-01-02", "is_end": "2023-01-02", "currency": "USD"},
    "NVO":    {"is_start": "2021-11-08", "is_end": "2023-11-08", "currency": "DKK"},
    "AMS.MC": {"is_start": "2021-11-14", "is_end": "2023-11-14", "currency": "EUR"},
    "NVS":    {"is_start": "2021-06-16", "is_end": "2023-06-16", "currency": "CHF"},
    "SHL.DE": {"is_start": "2021-04-20", "is_end": "2023-04-20", "currency": "EUR"},
    "ZEAL.CO":{"is_start": "2023-01-02", "is_end": "2024-01-02", "currency": "DKK"},
}

BASELINE = {
    "lookback_days": 17,
    "volatility_multiplier_enter": 0.5,
    "volatility_multiplier_exit": 0.1,
}


def compute_daily_vol(bars: pd.DataFrame, lookback: int) -> pd.Series:
    daily_close = bars["close"].resample("D").last().dropna()
    daily_returns = daily_close.pct_change()
    daily_vol = daily_returns.rolling(window=lookback).std()
    return daily_vol.shift(1)  # vol connue à la fin du jour précédent


def count_signals(bars: pd.DataFrame, lookback: int, mult_enter: float) -> dict:
    vol = compute_daily_vol(bars, lookback)
    daily_open = bars.groupby(bars.index.date)["open"].transform("first")
    bar_dates = pd.to_datetime(bars.index.date)
    vol_map = vol.to_dict()
    mapped_vol = pd.Series(bar_dates, index=bars.index).map(lambda d: vol_map.get(pd.Timestamp(d), np.nan))

    upper = daily_open * (1 + mult_enter * mapped_vol)
    lower = daily_open * (1 - mult_enter * mapped_vol)

    long_signals = (bars["close"] > upper).sum()
    short_signals = (bars["close"] < lower).sum()
    valid_bars = (~mapped_vol.isna()).sum()

    return {
        "long_signals": int(long_signals),
        "short_signals": int(short_signals),
        "total_signals": int(long_signals + short_signals),
        "valid_bars": int(valid_bars),
        "mean_daily_vol": float(mapped_vol.mean()),
    }


def main() -> None:
    repo_root = Path("/home/kidpixel/trading_automation_v2")
    all_results = []

    for symbol, fold_info in TICKER_FOLDS.items():
        print(f"\n=== {symbol} ({fold_info['currency']}) IS {fold_info['is_start']} -> {fold_info['is_end']} ===")
        bars = load_canonical_market_data(
            symbol=symbol,
            repo_root=repo_root,
            processed_dir="storage/processed",
            start_date=fold_info["is_start"],
            end_date=fold_info["is_end"],
            timeframe_minutes=1,
        )
        if bars.empty:
            print("  No data")
            continue

        # Baseline signal count
        base_signals = count_signals(bars, BASELINE["lookback_days"], BASELINE["volatility_multiplier_enter"])
        print(f"  Baseline (enter={BASELINE['volatility_multiplier_enter']}, lookback={BASELINE['lookback_days']}): {base_signals}")

        # Try different multipliers
        best_mult = None
        best_score = float('inf')
        target_signals = 300  # ~1 signal per trading day
        for mult in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0, 1.5]:
            signals = count_signals(bars, BASELINE["lookback_days"], mult)
            score = abs(signals["total_signals"] - target_signals)
            if score < best_score:
                best_score = score
                best_mult = mult
            print(f"  enter_mult={mult:.1f}: signals={signals['total_signals']:4d}  (long={signals['long_signals']:4d} short={signals['short_signals']:4d})  mean_vol={signals['mean_daily_vol']:.4f}")

        print(f"  -> Recommended enter_mult: {best_mult} (closest to {target_signals} signals)")

        all_results.append({
            "symbol": symbol,
            "currency": fold_info["currency"],
            "baseline_signals": base_signals,
            "recommended_mult_enter": best_mult,
        })

    out_path = repo_root / "reports/noise_boundary_intraday/phase4_wfa_holdout_1m/param_analysis.json"
    out_path.write_text(json.dumps(all_results, indent=2, default=str), encoding="utf-8")
    print(f"\nAnalysis saved to {out_path}")


if __name__ == "__main__":
    main()
