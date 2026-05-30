#!/usr/bin/env python3
"""
Phase 4 Hold-out — WFA baseline 1m sur les 8 tickers de remplacement.

Usage:
    python scripts/phase4_wfa_holdout_1m.py
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

# Ensure repo root is on path
_repo = Path(__file__).resolve().parent.parent
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))

from backtest_engine.data import get_canonical_market_data_date_bounds
from backtest_engine.walk_forward import run_wfa_full, WFAFoldResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("phase4_wfa_holdout_1m")

# Ticker-specific overrides for WFA configuration
TICKER_CONFIG: dict[str, dict] = {
    # ZEAL.CO: very short history (2023-01 -> 2025-12); use 1y IS / 1y OOS
    # end_date must allow OOS window to complete (needs at least 2025-01-02)
    "ZEAL.CO": {"is_years": 1, "oos_years": 1, "end_date": "2025-12-31"},
    # GMAB: EURUSD FX data ends 2024-12; cap end-date to avoid missing FX
    "GMAB": {"is_years": 2, "oos_years": 1, "end_date": "2024-12-31"},
    # Default for all others
    "__default__": {"is_years": 2, "oos_years": 1, "end_date": "2025-01-01"},
}

DEFAULT_TICKERS = ["AMS.MC", "GMAB", "LOGI", "NVO", "NVS", "SAP", "SHL.DE", "ZEAL.CO"]


def _safe_float(val: float | None) -> str:
    return f"{val:.3f}" if val is not None else "—"


def _safe_int(val: int | None) -> str:
    return str(val) if val is not None else "—"


def _fmt_cell(val: object) -> str:
    if val is None:
        return "—"
    if isinstance(val, float):
        return f"{val:.3f}"
    return str(val)


def _df_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    cols = list(df.columns)
    header = "| " + " | ".join(cols) + " |"
    separator = "|" + "|".join([" --- " for _ in cols]) + "|"
    lines = [header, separator]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(_fmt_cell(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def _generate_report(
    all_results: dict[str, list[WFAFoldResult]],
    output_dir: Path,
) -> None:
    """Generate the Phase 4 hold-out markdown report."""

    lines: list[str] = [
        "# Phase 4 — Validation Hold-out 1m (8 Tickers EUR/CHF/DKK/USD)",
        "",
        f"**Date d'exécution:** {pd.Timestamp.now(tz='UTC').strftime('%Y-%m-%d %H:%M UTC')}",
        "**Fenêtres:** rolling IS/OOS (2y/1y par défaut, 1y/1y pour ZEAL.CO)",
        "**Ré-optimisation:** Non (baseline fixe uniquement)",
        "",
        "---",
        "",
    ]

    for ticker, folds in all_results.items():
        cfg = TICKER_CONFIG.get(ticker, TICKER_CONFIG["__default__"])
        lines.append(f"## {ticker}")
        lines.append("")
        lines.append(f"*Config: {cfg['is_years']}y IS / {cfg['oos_years']}y OOS, end={cfg['end_date']}*")
        lines.append("")

        rows = []
        for f in folds:
            rows.append({
                "Fold": f.fold_idx,
                "IS": f"{f.is_start} → {f.is_end}",
                "OOS": f"{f.oos_start} → {f.oos_end}",
                "Sharpe IS (base)": f.baseline_is_sharpe,
                "Sharpe OOS (base)": f.baseline_oos_sharpe,
                "CAGR OOS (base)": f.baseline_oos_cagr,
                "MDD OOS (base)": f.baseline_oos_mdd,
                "Trades OOS (base)": f.baseline_oos_trades,
            })

        lines.append(_df_to_markdown(pd.DataFrame(rows)))
        lines.append("")

        base_sharpes = [f.baseline_is_sharpe for f in folds if f.baseline_is_sharpe is not None]
        base_oos_sharpes = [f.baseline_oos_sharpe for f in folds if f.baseline_oos_sharpe is not None]
        if base_sharpes and base_oos_sharpes:
            lines.append(
                f"**Dégradation baseline:** IS Sharpe moyen = {sum(base_sharpes)/len(base_sharpes):.3f}, "
                f"OOS Sharpe moyen = {sum(base_oos_sharpes)/len(base_oos_sharpes):.3f}"
            )
            lines.append("")

        lines.append("---")
        lines.append("")

    # Global summary
    lines.append("## Synthèse Globale")
    lines.append("")

    all_folds = [f for folds in all_results.values() for f in folds]
    if not all_folds:
        lines.append("Aucun fold valide n'a été généré.")
    else:
        base_oos_sharpes = [f.baseline_oos_sharpe for f in all_folds if f.baseline_oos_sharpe is not None]
        if base_oos_sharpes:
            lines.append(
                f"- **Baseline fixe** — Sharpe OOS moyen sur tous les actifs: "
                f"{sum(base_oos_sharpes)/len(base_oos_sharpes):.3f} "
                f"(min={min(base_oos_sharpes):.3f}, max={max(base_oos_sharpes):.3f})"
            )

        # Per-currency summary
        currency_map = {
            "AMS.MC": "EUR", "SAP": "EUR", "SHL.DE": "EUR",
            "LOGI": "CHF", "NVS": "CHF",
            "NVO": "DKK", "ZEAL.CO": "DKK",
            "GMAB": "USD",
        }
        by_currency: dict[str, list[float]] = {}
        for ticker, folds in all_results.items():
            curr = currency_map.get(ticker, "UNK")
            for f in folds:
                if f.baseline_oos_sharpe is not None:
                    by_currency.setdefault(curr, []).append(f.baseline_oos_sharpe)

        lines.append("")
        lines.append("### Par devise")
        lines.append("")
        for curr in sorted(by_currency.keys()):
            vals = by_currency[curr]
            lines.append(
                f"- **{curr}** — Sharpe OOS moyen: {sum(vals)/len(vals):.3f} "
                f"(min={min(vals):.3f}, max={max(vals):.3f}, n={len(vals)} folds)"
            )

        lines.append("")
        lines.append("### Verdict")
        lines.append("")
        if base_oos_sharpes and sum(base_oos_sharpes) / len(base_oos_sharpes) < 0.5:
            lines.append(
                "**NO-GO** — Le Sharpe OOS moyen est inférieur à 0.5, insuffisant pour le live."
            )
        else:
            lines.append(
                "**CONDITIONAL-GO** — Les performances OOS sur granularité 1m sont positives. "
                "Recommandation: (1) ajuster les paramètres pour les devises non-EUR si dégradation, "
                "(2) tester en paper trading avant mise en production."
            )

    report_path = output_dir / "phase4_wfa_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Report written to %s", report_path)


def main() -> None:
    p = argparse.ArgumentParser(description="Phase 4 Hold-out WFA 1m")
    p.add_argument(
        "--tickers",
        default=",".join(DEFAULT_TICKERS),
        help="Comma-separated list of tickers",
    )
    p.add_argument("--start-date", default="2015-01-01", help="Global start date")
    p.add_argument("--output-dir", default="reports/noise_boundary_intraday/phase4_wfa_holdout_1m", help="Output dir")
    p.add_argument("--repo-root", default=".", help="Repo root")
    p.add_argument("--timeframe-minutes", type=int, default=1, help="Timeframe")
    args = p.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(args.repo_root).resolve()

    all_results: dict[str, list[WFAFoldResult]] = {}

    for ticker in tickers:
        cfg = TICKER_CONFIG.get(ticker, TICKER_CONFIG["__default__"].copy())
        logger.info("=" * 60)
        logger.info("Processing %s (config=%s)", ticker, cfg)
        logger.info("=" * 60)

        try:
            actual_start, actual_end = get_canonical_market_data_date_bounds(
                symbol=ticker,
                repo_root=repo_root,
                processed_dir="storage/processed",
                timeframe_minutes=args.timeframe_minutes,
            )
            start = max(args.start_date, actual_start)
            end = min(cfg["end_date"], actual_end)
            logger.info("Data bounds for %s: %s → %s (effective end=%s)", ticker, start, actual_end, end)
        except Exception as exc:
            logger.error("Cannot determine date bounds for %s: %s", ticker, exc)
            continue

        try:
            from backtest_engine.walk_forward import generate_rolling_windows
            from backtest_engine.data import load_canonical_market_data
            from backtest_engine.walk_forward import run_wfa_fold

            data = load_canonical_market_data(
                symbol=ticker,
                repo_root=repo_root,
                processed_dir="storage/processed",
                start_date=start,
                end_date=end,
                timeframe_minutes=args.timeframe_minutes,
            )
            if data.empty:
                logger.warning("No data for %s between %s and %s", ticker, start, end)
                continue

            windows = generate_rolling_windows(start, end, cfg["is_years"], cfg["oos_years"])
            if not windows:
                logger.warning("No WFA windows for %s (IS=%sy, OOS=%sy)", ticker, cfg["is_years"], cfg["oos_years"])
                continue

            # Only use the LAST fold (most recent, most relevant for hold-out)
            is_s, is_e, oos_s, oos_e = windows[-1]
            logger.info("%s: using LAST fold — IS %s → %s | OOS %s → %s", ticker, is_s, is_e, oos_s, oos_e)

            is_data = data.loc[is_s:is_e]
            oos_data = data.loc[oos_s:oos_e]
            if is_data.empty or oos_data.empty:
                logger.warning("Empty slice for %s fold — skipping", ticker)
                continue

            fold = run_wfa_fold(
                symbol=ticker,
                is_data=is_data,
                oos_data=oos_data,
                fold_idx=len(windows) - 1,
                is_start=is_s,
                is_end=is_e,
                oos_start=oos_s,
                oos_end=oos_e,
                reoptimize=False,
                initial_capital=1000.0,
                timeframe_minutes=args.timeframe_minutes,
                repo_root=repo_root,
            )
            all_results[ticker] = [fold]
            logger.info("%s: 1 fold completed", ticker)
        except Exception as exc:
            logger.error("WFA failed for %s: %s", ticker, exc, exc_info=True)
            continue

    # Persist raw JSON
    raw_path = output_dir / "raw_results.json"
    serialisable = {}
    for ticker, folds in all_results.items():
        serialisable[ticker] = [
            {k: v for k, v in f.__dict__.items() if not isinstance(v, pd.DataFrame)}
            for f in folds
        ]
    raw_path.write_text(json.dumps(serialisable, indent=2, default=str), encoding="utf-8")
    logger.info("Raw results written to %s", raw_path)

    # Generate report
    _generate_report(all_results, output_dir)


if __name__ == "__main__":
    main()
