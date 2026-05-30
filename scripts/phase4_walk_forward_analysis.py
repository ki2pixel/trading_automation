#!/usr/bin/env python3
"""
Phase 4 — Walk-Forward Analysis, Multi-Asset Test, and Overfitting Metrics.

Usage:
    python run_phase4_wfa.py
    python run_phase4_wfa.py --tickers LOGI,NVO --is-years 2 --oos-years 1 --reopt-trials 30
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

# Ensure repo root is on path for absolute imports
_repo = Path(__file__).resolve().parent
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))

from backtest_engine.data import get_canonical_market_data_date_bounds
from backtest_engine.walk_forward import (
    PHASE3_BASELINE_PARAMS,
    run_wfa_full,
    WFAFoldResult,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("phase4_wfa")


DEFAULT_TICKERS = ["LOGI", "NVO", "SAP", "NVS", "GMAB"]


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 4 Walk-Forward Analysis")
    p.add_argument(
        "--tickers",
        default=",".join(DEFAULT_TICKERS),
        help="Comma-separated list of tickers to test",
    )
    p.add_argument(
        "--is-years", type=int, default=3, help="In-sample window length in years"
    )
    p.add_argument(
        "--oos-years", type=int, default=1, help="Out-of-sample window length in years"
    )
    p.add_argument(
        "--start-date",
        default="2018-01-01",
        help="Global start date (YYYY-MM-DD). Actual per-ticker bounds are respected.",
    )
    p.add_argument(
        "--end-date",
        default="2025-01-01",
        help="Global end date (YYYY-MM-DD). Actual per-ticker bounds are respected.",
    )
    p.add_argument(
        "--reopt-trials",
        type=int,
        default=50,
        help="Number of Bayesian trials for IS re-optimisation",
    )
    p.add_argument(
        "--baseline-only",
        action="store_true",
        help="Skip IS re-optimisation; only test baseline params",
    )
    p.add_argument(
        "--output-dir",
        default="reports/noise_boundary_intraday/phase4_wfa",
        help="Directory for raw results and markdown report",
    )
    p.add_argument(
        "--repo-root",
        default=".",
        help="Repository root path",
    )
    p.add_argument(
        "--timeframe-minutes",
        type=int,
        default=5,
        help="Data timeframe in minutes",
    )
    return p.parse_args()


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
    # Build header
    header = "| " + " | ".join(cols) + " |"
    separator = "|" + "|".join([" --- " for _ in cols]) + "|"
    lines = [header, separator]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(_fmt_cell(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def _generate_report(
    all_results: dict[str, list[WFAFoldResult]],
    args: argparse.Namespace,
    output_dir: Path,
) -> None:
    """Generate the Phase 4 markdown report."""

    lines: list[str] = [
        "# Phase 4 — Validation et Généralisation (WFA, Multi-Actifs, PBO/DSR)",
        "",
        f"**Date d'exécution:** {pd.Timestamp.now(tz='UTC').strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Fenêtres:** {args.is_years} ans IS / {args.oos_years} ans OOS",
        f"**Ré-optimisation:** {'Non (baseline fixe uniquement)' if args.baseline_only else f'Oui ({args.reopt_trials} trials Optuna TPE)'}",
        "",
        "---",
        "",
    ]

    # Per-ticker tables
    for ticker, folds in all_results.items():
        lines.append(f"## {ticker}")
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
            if not args.baseline_only:
                rows[-1].update({
                    "Sharpe IS (réopt)": f.reopt_is_sharpe,
                    "Sharpe OOS (réopt)": f.reopt_oos_sharpe,
                    "CAGR OOS (réopt)": f.reopt_oos_cagr,
                    "MDD OOS (réopt)": f.reopt_oos_mdd,
                    "Trades OOS (réopt)": f.reopt_oos_trades,
                    "PBO": f.pbo,
                    "DSR": f.dsr,
                })

        lines.append(_df_to_markdown(pd.DataFrame(rows)))
        lines.append("")

        # Degradation stats
        base_sharpes = [f.baseline_is_sharpe for f in folds if f.baseline_is_sharpe is not None]
        base_oos_sharpes = [f.baseline_oos_sharpe for f in folds if f.baseline_oos_sharpe is not None]
        if base_sharpes and base_oos_sharpes:
            lines.append(
                f"**Dégradation baseline:** IS Sharpe moyen = {sum(base_sharpes)/len(base_sharpes):.3f}, "
                f"OOS Sharpe moyen = {sum(base_oos_sharpes)/len(base_oos_sharpes):.3f}"
            )
            lines.append("")

        if not args.baseline_only:
            reopt_is_sharpes = [f.reopt_is_sharpe for f in folds if f.reopt_is_sharpe is not None]
            reopt_oos_sharpes = [f.reopt_oos_sharpe for f in folds if f.reopt_oos_sharpe is not None]
            pbos = [f.pbo for f in folds if f.pbo is not None]
            dsrs = [f.dsr for f in folds if f.dsr is not None]
            if reopt_is_sharpes and reopt_oos_sharpes:
                lines.append(
                    f"**Dégradation ré-optimisée:** IS Sharpe moyen = {sum(reopt_is_sharpes)/len(reopt_is_sharpes):.3f}, "
                    f"OOS Sharpe moyen = {sum(reopt_oos_sharpes)/len(reopt_oos_sharpes):.3f}"
                )
                lines.append("")
            if pbos:
                lines.append(f"**PBO moyen:** {sum(pbos)/len(pbos):.3f}  (seuil critique: 0.5)")
                lines.append("")
            if dsrs:
                lines.append(f"**DSR moyen:** {sum(dsrs)/len(dsrs):.3f}")
                lines.append("")

        lines.append("---")
        lines.append("")

    # Global summary / verdict
    lines.append("## Synthèse Globale")
    lines.append("")

    all_folds = [f for folds in all_results.values() for f in folds]
    if not all_folds:
        lines.append("Aucun fold valide n'a été généré.")
    else:
        # Baseline aggregation
        base_oos_sharpes = [f.baseline_oos_sharpe for f in all_folds if f.baseline_oos_sharpe is not None]
        if base_oos_sharpes:
            lines.append(
                f"- **Baseline fixe** — Sharpe OOS moyen sur tous les actifs: "
                f"{sum(base_oos_sharpes)/len(base_oos_sharpes):.3f} "
                f"(min={min(base_oos_sharpes):.3f}, max={max(base_oos_sharpes):.3f})"
            )

        if not args.baseline_only:
            reopt_oos_sharpes = [f.reopt_oos_sharpe for f in all_folds if f.reopt_oos_sharpe is not None]
            pbos = [f.pbo for f in all_folds if f.pbo is not None]
            dsrs = [f.dsr for f in all_folds if f.dsr is not None]
            if reopt_oos_sharpes:
                lines.append(
                    f"- **Ré-optimisée** — Sharpe OOS moyen: "
                    f"{sum(reopt_oos_sharpes)/len(reopt_oos_sharpes):.3f} "
                    f"(min={min(reopt_oos_sharpes):.3f}, max={max(reopt_oos_sharpes):.3f})"
                )
            if pbos:
                avg_pbo = sum(pbos) / len(pbos)
                lines.append(
                    f"- **PBO moyen:** {avg_pbo:.3f}  → "
                    f"{'RISQUE ÉLEVÉ de surapprentissage' if avg_pbo > 0.5 else 'Risque modéré' if avg_pbo > 0.3 else 'Risque faible'}"
                )
            if dsrs:
                avg_dsr = sum(dsrs) / len(dsrs)
                lines.append(
                    f"- **DSR moyen:** {avg_dsr:.3f}  → "
                    f"{'Significativité statistique douteuse' if avg_dsr < 1.0 else 'Significativité acceptable'}"
                )

        # Verdict
        lines.append("")
        lines.append("### Verdict")
        lines.append("")

        if not base_oos_sharpes:
            lines.append("**NO-GO** — Pas de données OOS suffisantes pour un verdict.")
        elif not args.baseline_only and pbos and sum(pbos) / len(pbos) > 0.5:
            lines.append(
                "**NO-GO** — Le PBO moyen dépasse 0.5, indiquant un risque élevé de surapprentissage. "
                "La stratégie est probablement sur-ajustée aux données historiques et peu fiable en live."
            )
        elif base_oos_sharpes and sum(base_oos_sharpes) / len(base_oos_sharpes) < 0.5:
            lines.append(
                "**NO-GO** — Le Sharpe OOS moyen est inférieur à 0.5, ce qui est insuffisant "
                "pour justifier le risque opérationnel et les coûts de transaction en live."
            )
        else:
            lines.append(
                "**CONDITIONAL-GO** — Les performances OOS sont positives mais la granularité 5m "
                "limite la confiance. Recommandation: (1) collecter des données 1m, (2) valider sur "
                "une période hold-out indépendante, (3) tester en paper trading avant mise en production."
            )

    report_path = output_dir / "phase4_wfa_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Report written to %s", report_path)


def main() -> None:
    args = _parse_args()
    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_root = Path(args.repo_root).resolve()

    all_results: dict[str, list[WFAFoldResult]] = {}

    for ticker in tickers:
        logger.info("=" * 60)
        logger.info("Processing %s", ticker)
        logger.info("=" * 60)

        try:
            # Respect actual data bounds for this ticker
            actual_start, actual_end = get_canonical_market_data_date_bounds(
                symbol=ticker,
                repo_root=repo_root,
                processed_dir="storage/processed",
                timeframe_minutes=args.timeframe_minutes,
            )
            start = max(args.start_date, actual_start)
            end = min(args.end_date, actual_end)
            logger.info("Data bounds for %s: %s → %s", ticker, start, end)
        except Exception as exc:
            logger.error("Cannot determine date bounds for %s: %s", ticker, exc)
            continue

        try:
            folds = run_wfa_full(
                symbol=ticker,
                repo_root=repo_root,
                start_date=start,
                end_date=end,
                is_years=args.is_years,
                oos_years=args.oos_years,
                reoptimize=not args.baseline_only,
                reopt_trials=args.reopt_trials,
                timeframe_minutes=args.timeframe_minutes,
                output_root=output_dir / "reopt",
            )
            all_results[ticker] = folds
            logger.info("%s: %d fold(s) completed", ticker, len(folds))
        except Exception as exc:
            logger.error("WFA failed for %s: %s", ticker, exc, exc_info=True)
            continue

    # Persist raw JSON
    raw_path = output_dir / "raw_results.json"
    serialisable = {}
    for ticker, folds in all_results.items():
        serialisable[ticker] = [
            {
                k: v for k, v in f.__dict__.items()
                if not isinstance(v, pd.DataFrame)
            }
            for f in folds
        ]
    raw_path.write_text(json.dumps(serialisable, indent=2, default=str), encoding="utf-8")
    logger.info("Raw results written to %s", raw_path)

    # Generate report
    _generate_report(all_results, args, output_dir)


if __name__ == "__main__":
    main()
