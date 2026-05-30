from __future__ import annotations

import json
from pathlib import Path
import pandas as pd
from html import escape


def generate_global_analysis(
    repo_root: Path | str,
    strategy: str,
    output_dir: str | Path = "reports/local_optimizer"
) -> dict[str, str]:
    if output_dir == "reports/local_optimizer":
        from .paths import get_reports_dir
        base_path = get_reports_dir(repo_root) / "local_optimizer" / strategy
    else:
        base_path = Path(repo_root) / Path(output_dir) / strategy
    if not base_path.exists() or not base_path.is_dir():
        raise FileNotFoundError(f"Aucun rapport d'optimisation trouvé pour la stratégie : {strategy} dans {base_path}")

    symbol_data = []

    for symbol_dir in base_path.iterdir():
        if not symbol_dir.is_dir():
            continue

        symbol = symbol_dir.name

        run_dirs = [d for d in symbol_dir.iterdir() if d.is_dir() and "T" in d.name]
        if not run_dirs:
            continue

        best_run_overall = None
        best_score_overall = float('-inf')
        best_reco_data = None
        best_timeframe = ""

        # Analyser TOUS les runs pour trouver celui avec le meilleur score
        for run_dir in run_dirs:
            reco_path = run_dir / "recommendations.json"
            config_path = run_dir / "optimization_config.json"

            if not reco_path.exists():
                continue

            try:
                with open(reco_path, "r", encoding="utf-8") as f:
                    reco_data = json.load(f)

                timeframe = ""
                if config_path.exists():
                    with open(config_path, "r", encoding="utf-8") as f:
                        config_data = json.load(f)
                        timeframe = config_data.get("timeframe_minutes", "")

                # On regarde le score du 'best'
                current_best = reco_data.get("best") or {}
                score = current_best.get("score")

                if score is not None:
                    # Gestion du score_direction: si min, on inverse le score pour la comparaison
                    direction = reco_data.get("score_direction", "max")
                    effective_score = float(score) if direction == "max" else -float(score)

                    if effective_score > best_score_overall:
                        best_score_overall = effective_score
                        best_run_overall = run_dir
                        best_reco_data = reco_data
                        best_timeframe = timeframe

            except Exception:
                continue

        # Si aucun run valide n'est trouvé pour le symbole
        if not best_reco_data:
            continue

        best = best_reco_data.get("best") or {}
        recommended = best_reco_data.get("recommended") or {}

        best_metrics = best.get("metrics") or {}
        rec_metrics = recommended.get("metrics") or {}

        best_params = best.get("parameters") or {}
        rec_params = recommended.get("parameters") or {}

        row = {
            "SYMBOL": symbol,
            "TIMEFRAME": best_timeframe,
            "SCORE_METRIC": best_reco_data.get("score_metric", ""),
            "BEST_SCORE": best.get("score", ""),
            "REC_SCORE": recommended.get("score", ""),
            "BEST_TRADES": best_metrics.get("closed_trades", ""),
            "BEST_PNL": best_metrics.get("total_net_pnl", ""),
            "BEST_DD": best_metrics.get("max_drawdown", ""),
            "BEST_SHARPE": best_metrics.get("sharpe_ratio", ""),
            "REC_TRADES": rec_metrics.get("closed_trades", ""),
            "REC_PNL": rec_metrics.get("total_net_pnl", ""),
            "REC_DD": rec_metrics.get("max_drawdown", ""),
            "REC_SHARPE": rec_metrics.get("sharpe_ratio", "")
        }

        param_keys = set(best_params.keys()) | set(rec_params.keys())
        reco_params_block = best_reco_data.get("parameters") or {}

        # Sort param keys to have a deterministic order
        for pk in sorted(param_keys):
            row[f"BEST_{pk.upper()}"] = best_params.get(pk, "")
            row[f"REC_{pk.upper()}"] = rec_params.get(pk, "")

            # Extraction des sweet spots et de la confiance depuis le bloc 'parameters'
            param_reco = reco_params_block.get(pk) or {}
            if isinstance(param_reco, dict):
                sweet_spot = param_reco.get("sweet_spot_range")
                if sweet_spot:
                    row[f"SWEET_SPOT_{pk.upper()}"] = f"[{sweet_spot[0]}, {sweet_spot[1]}]" if isinstance(sweet_spot,
                                                                                                          list) and len(
                        sweet_spot) >= 2 else str(sweet_spot)
                else:
                    row[f"SWEET_SPOT_{pk.upper()}"] = ""
                row[f"CONF_{pk.upper()}"] = param_reco.get("confidence", "")

        symbol_data.append(row)

    if not symbol_data:
        raise ValueError(f"Aucune recommandation valide trouvée pour générer la synthèse de : {strategy}")

    df = pd.DataFrame(symbol_data)

    # Optional sorting: by symbol
    df = df.sort_values("SYMBOL")

    parquet_path = base_path / "global_summary.parquet"
    html_path = base_path / "global_summary.html"

    df.to_parquet(parquet_path, index=False, engine="pyarrow", compression="zstd")

    _write_global_html(html_path, df, strategy)

    return {
        "parquet": f"/api/global-analysis/{strategy}/global_summary.parquet",
        "html": f"/api/global-analysis/{strategy}/global_summary.html"
    }


def _write_global_html(path: Path, df: pd.DataFrame, strategy: str):
    columns = list(df.columns)

    header_html = "".join(f"<th tabindex=\"0\">{escape(col)}</th>" for col in columns)

    rows_html = []
    for _, row in df.iterrows():
        tds = []
        for col in columns:
            val = row[col]
            if pd.isna(val) or val == "":
                tds.append("<td>-</td>")
            else:
                if isinstance(val, float):
                    tds.append(f"<td>{escape(f'{val:.4f}')}</td>")
                else:
                    tds.append(f"<td>{escape(str(val))}</td>")
        rows_html.append(f"<tr>{''.join(tds)}</tr>")

    tbody_html = "\n".join(rows_html)

    html = f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Synthèse Globale - {escape(strategy)}</title>
  <style>
    :root {{ --border:#d9dee8; --muted:#667085; --bg:#f7f9fc; --accent:#2563eb; --best:#ecfdf3; --recommended:#eff6ff; }}
    body {{ margin:0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color:#111827; background:white; }}
    header {{ padding:2rem 2.5rem 1rem; border-bottom:1px solid var(--border); background:linear-gradient(180deg,#fff,var(--bg)); }}
    h1 {{ margin:0 0 .4rem; font-size:1.7rem; }}
    .subtitle {{ margin:0; color:var(--muted); }}
    main {{ padding:1rem 2.5rem 2.5rem; }}
    .toolbar {{ display:flex; gap:.75rem; align-items:center; padding:.75rem 0; }}
    a.button {{ color:white; background:var(--accent); text-decoration:none; padding:.55rem .75rem; border-radius:8px; font-weight:600; font-size:.9rem; }}
    .table-wrap {{ overflow:auto; border:1px solid var(--border); border-radius:12px; margin-top: 1rem; max-height: calc(100vh - 200px); }}
    table {{ border-collapse:separate; border-spacing:0; width:100%; font-size:.88rem; }}
    th,td {{ white-space:nowrap; border-bottom:1px solid var(--border); border-right:1px solid var(--border); padding:.48rem .6rem; text-align:right; }}
    th:first-child,td:first-child {{ text-align:left; position:sticky; left:0; background:inherit; z-index:1; font-weight:bold; }}
    th {{ background:#eef2f7; cursor:pointer; user-select:none; position:sticky; top:0; z-index:2; }}
    th:first-child {{ z-index:3; }}
    tbody tr:nth-child(even) {{ background:#fbfcff; }}
    tbody tr:hover {{ background:#fff7ed; }}
  </style>
</head>
<body>
  <header>
    <h1>Synthèse Globale Optimizer — {escape(strategy)}</h1>
    <p class="subtitle">Analyse consolidée des {len(df)} symboles backtestés pour cette stratégie. Reprend le meilleur run, le run recommandé et les plages "sweet spots" pour la meilleure échelle de temps (Timeframe).</p>
  </header>
  <main>
    <div class="toolbar">
      <a class="button" href="global_summary.parquet" download>Télécharger le Parquet complet</a>
    </div>
    <div class="table-wrap">
      <table id="report-table">
        <thead><tr>{header_html}</tr></thead>
        <tbody>{tbody_html}</tbody>
      </table>
    </div>
  </main>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")