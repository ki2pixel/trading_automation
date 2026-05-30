#!/usr/bin/env python3
"""
Phase 4 — Compare 1m vs 5m Timeframe Results.
Loads raw results from both 1m and 5m hold-out runs, formats a comparative markdown table,
and saves the report.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("compare_timeframes")

def main() -> None:
    repo_root = Path("/home/kidpixel/trading_automation_v2")
    
    path_1m = repo_root / "reports/noise_boundary_intraday/phase4_wfa_holdout_1m/raw_results.json"
    path_5m = repo_root / "reports/noise_boundary_intraday/phase4_wfa_holdout_5m/raw_results.json"
    
    if not path_1m.exists():
        logger.error(f"Missing 1m raw results at {path_1m}")
        sys.exit(1)
        
    if not path_5m.exists():
        logger.error(f"Missing 5m raw results at {path_5m}. Run 5m hold-out first.")
        sys.exit(1)
        
    data_1m = json.loads(path_1m.read_text(encoding="utf-8"))
    data_5m = json.loads(path_5m.read_text(encoding="utf-8"))
    
    tickers = sorted(list(set(data_1m.keys()).union(data_5m.keys())))
    
    lines = [
        "# Phase 4 — Comparaison Intraday Hold-Out (1m vs 5m)",
        "",
        "Ce rapport compare la performance OOS de la stratégie baseline `noise_boundary_intraday` "
        "sur les granularités 1 minute et 5 minutes.",
        "",
        "## Table Comparative OOS (Baseline)",
        "",
        "| Ticker | Sharpe OOS (1m) | Sharpe OOS (5m) | MDD OOS (1m) | MDD OOS (5m) | Trades OOS (1m) | Trades OOS (5m) | Verdict Robustesse |",
        "|--------|-----------------|-----------------|--------------|--------------|-----------------|-----------------|--------------------|",
    ]
    
    for t in tickers:
        f_1m = data_1m.get(t, [{}])[0]
        f_5m = data_5m.get(t, [{}])[0]
        
        sh_1m = f_1m.get("baseline_oos_sharpe")
        sh_5m = f_5m.get("baseline_oos_sharpe")
        
        mdd_1m = f_1m.get("baseline_oos_mdd")
        mdd_5m = f_5m.get("baseline_oos_mdd")
        
        tr_1m = f_1m.get("baseline_oos_trades")
        tr_5m = f_5m.get("baseline_oos_trades")
        
        # Helper formatting
        sh_1m_str = f"{sh_1m:.3f}" if sh_1m is not None else "—"
        sh_5m_str = f"{sh_5m:.3f}" if sh_5m is not None else "—"
        
        mdd_1m_str = f"{mdd_1m:.1f}%" if mdd_1m is not None else "—"
        mdd_5m_str = f"{mdd_5m:.1f}%" if mdd_5m is not None else "—"
        
        tr_1m_str = str(tr_1m) if tr_1m is not None else "—"
        tr_5m_str = str(tr_5m) if tr_5m is not None else "—"
        
        # Simple heuristic verdict
        if sh_5m is not None and sh_1m is not None:
            if sh_5m > sh_1m and sh_5m > 0.8:
                verdict = "✅ 5m Supérieur (Robuste)"
            elif sh_5m > 0.5:
                verdict = "⚠️ 5m Acceptable"
            elif sh_5m > sh_1m:
                verdict = "📈 5m Amélioré (mais insuffisant)"
            else:
                verdict = "❌ 1m Supérieur ou les deux mauvais"
        else:
            verdict = "—"
            
        lines.append(
            f"| {t} | {sh_1m_str} | {sh_5m_str} | {mdd_1m_str} | {mdd_5m_str} | {tr_1m_str} | {tr_5m_str} | {verdict} |"
        )
        
    lines.extend([
        "",
        "## Observations Clés",
        "",
        "1. **Stabilité des bandes :** La granularité 5m lisse le bruit haute fréquence, ce qui réduit le nombre de faux signaux d'entrée.",
        "2. **Nombre de trades :** En 5m, le nombre de trades OOS devrait être plus faible qu'en 1m, mais leur pertinence et robustesse sont accrues.",
        "3. **Maximum Drawdown (MDD) :** Vérifier si le passage en 5m permet de réduire le MDD sous la limite opérationnelle de 30%.",
    ])
    
    out_path = repo_root / "reports/noise_boundary_intraday/phase4_wfa_holdout_1m/compare_1m_5m_report.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"Comparison report saved to {out_path}")

if __name__ == "__main__":
    main()
