from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


SUMMARY_METRICS = [
    "initial_capital",
    "final_equity",
    "open_pnl",
    "total_pnl",
    "total_pnl_pct",
    "total_net_pnl",
    "return_pct",
    "max_drawdown",
    "max_drawdown_pct",
]

PERFORMANCE_METRICS = [
    "gross_profit",
    "gross_loss",
    "profit_factor",
    "commission_paid",
    "sharpe_ratio",
    "sortino_ratio",
]

TRADE_METRICS = [
    "closed_trades",
    "winning_trades",
    "losing_trades",
    "breakeven_trades",
    "win_rate_pct",
    "profit_factor",
    "average_trade",
    "average_winning_trade",
    "average_losing_trade",
    "average_win_loss_ratio",
    "average_bars_held",
    "average_winning_bars_held",
    "average_losing_bars_held",
    "best_trade",
    "worst_trade",
]

SIDE_METRICS = [
    "long_closed_trades",
    "long_net_pnl",
    "long_gross_profit",
    "long_gross_loss",
    "long_profit_factor",
    "long_win_rate_pct",
    "short_closed_trades",
    "short_net_pnl",
    "short_gross_profit",
    "short_gross_loss",
    "short_profit_factor",
    "short_win_rate_pct",
]

BENCHMARK_METRICS = [
    "buy_hold_pnl",
    "buy_hold_return_pct",
    "return_vs_buy_hold_pct_points",
    "strategy_outperformance_pnl",
]

CAPITAL_METRICS = [
    "cagr_pct",
    "required_account_size",
    "return_on_required_account_pct",
    "net_profit_to_max_drawdown_pct",
    "max_position_value",
    "average_position_value",
    "capital_efficiency_pct",
    "exposure_bars",
    "exposure_pct",
    "bars",
    "start",
    "end",
]

RUNUP_DRAWDOWN_METRICS = [
    "max_trade_runup",
    "max_trade_runup_pct",
    "average_trade_runup",
    "max_trade_drawdown",
    "max_trade_drawdown_pct",
    "average_trade_drawdown",
]


OPTIMIZER_REPORT_FILENAMES = {
    "parquet": "optimizer_report.parquet",
    "html": "optimizer_report.html",
}

OPTIMIZER_BASE_COLUMNS = [
    "PARAMETERS",
    "STATUS",
    "SCORE",
    "NETPROFITAMOUNT",
    "NETPROFITPERCENT",
    "MAXDRAWDOWNAMOUNT",
    "MAXDRAWDOWNPERCENT",
    "CLOSEDTRADES",
    "PERCENTPROFITABLE",
    "PROFITFACTOR",
    "AVERAGETRADEAMOUNT",
    "AVERAGETRADEPERCENT",
    "AVGERAGEBARSINTRADES",
    "SHARPERATIO",
    "SORTINORATIO",
    "EXPOSUREPERCENT",
    "RETURNVSBUYHOLDPCTPOINTS",
]

PARAMETER_REPORT_LABELS = {
    "fast_len": "FAST HMA LENGTH",
    "slow_len": "SLOW HMA LENGTH",
}


@dataclass
class BacktestRunResult:
    strategy: str
    symbol: str
    config: dict
    bars: pd.DataFrame
    state: pd.DataFrame
    trades: pd.DataFrame
    equity_curve: pd.DataFrame
    metrics: dict


def write_backtest_outputs(result: BacktestRunResult, output_root: Path) -> Path:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = output_root / result.strategy / result.symbol / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    result.trades.to_parquet(output_dir / "trades.parquet", index=False, engine="pyarrow", compression="zstd")
    result.equity_curve.to_parquet(output_dir / "equity_curve.parquet", engine="pyarrow", compression="zstd")
    result.state.to_parquet(output_dir / "state.parquet", engine="pyarrow", compression="zstd")
    (output_dir / "metrics.json").write_text(
        json.dumps(result.metrics, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    (output_dir / "config.json").write_text(
        json.dumps(result.config, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    write_html_summary(result, output_dir / "report.html")
    return output_dir


def write_html_summary(result: BacktestRunResult, path: Path) -> None:
    def fmt(value: object) -> str:
        if value is None:
            return "—"
        if isinstance(value, float):
            return escape(f"{value:,.4f}")
        return escape(str(value))

    def table(title: str, keys: list[str]) -> str:
        rows = "\n".join(
            f"<tr><th>{escape(str(key))}</th><td>{fmt(result.metrics.get(key))}</td></tr>"
            for key in keys
            if key in result.metrics
        )
        return f"<section><h2>{escape(title)}</h2><table>{rows}</table></section>"

    remaining = [
        key for key in result.metrics
        if key not in set(
            SUMMARY_METRICS
            + PERFORMANCE_METRICS
            + TRADE_METRICS
            + SIDE_METRICS
            + BENCHMARK_METRICS
            + CAPITAL_METRICS
            + RUNUP_DRAWDOWN_METRICS
        )
    ]
    strategy = escape(result.strategy)
    symbol = escape(result.symbol)
    html = f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <title>{strategy} — {symbol}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #202124; }}
    section {{ margin: 1.5rem 0; }}
    table {{ border-collapse: collapse; min-width: 640px; }}
    th, td {{ border: 1px solid #ddd; padding: .45rem .65rem; text-align: right; }}
    th {{ text-align: left; background: #f6f6f6; }}
    code {{ background: #f6f6f6; padding: .1rem .25rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(640px, 1fr)); gap: 1rem; }}
  </style>
</head>
<body>
  <h1>{strategy} — {symbol}</h1>
  <p>Rapport local. Exports détaillés : <code>trades.parquet</code>, <code>equity_curve.parquet</code>, <code>state.parquet</code>, <code>metrics.json</code>, <code>config.json</code>.</p>
  <div class="grid">
    {table("Résumé", SUMMARY_METRICS)}
    {table("Performance", PERFORMANCE_METRICS)}
    {table("Trades", TRADE_METRICS)}
    {table("Long / Short", SIDE_METRICS)}
    {table("Benchmark & exposition", BENCHMARK_METRICS)}
    {table("Efficacité du capital", CAPITAL_METRICS)}
    {table("Run-ups & drawdowns des trades", RUNUP_DRAWDOWN_METRICS)}
    {table("Autres métriques", remaining)}
  </div>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")


def _finite_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _format_number(value: object, *, decimals: int = 2, signed: bool = False, absolute: bool = False, suffix: str = "") -> str:
    number = _finite_float(value)
    if number is None:
        return ""
    if absolute:
        number = abs(number)
    sign = "+" if signed and number > 0 else ""
    return f"{sign}{number:,.{decimals}f}{suffix}"


def _format_compact(value: object) -> str:
    if isinstance(value, bool):
        return str(value)
    number = _finite_float(value)
    if number is None:
        return "" if value is None else str(value)
    if float(number).is_integer():
        return str(int(number))
    return f"{number:.10g}"


def _parameter_label(name: str) -> str:
    return PARAMETER_REPORT_LABELS.get(name, name.replace("_", " ").upper())


def _parameter_names(optimization_config: dict[str, Any], results: list[dict[str, Any]]) -> list[str]:
    ordered: list[str] = []
    for spec in optimization_config.get("parameters") or []:
        if isinstance(spec, dict) and spec.get("name"):
            name = str(spec["name"])
            if name not in ordered:
                ordered.append(name)
    for row in results:
        parameters = row.get("parameters") if isinstance(row.get("parameters"), dict) else {}
        for name in parameters:
            if name not in ordered:
                ordered.append(str(name))
    return ordered


def _parameter_summary(parameters: dict[str, Any], names: list[str]) -> str:
    values = [_format_compact(parameters.get(name)) for name in names if name in parameters]
    if values:
        return ", ".join(values)
    if parameters:
        return ", ".join(f"{name}={_format_compact(value)}" for name, value in sorted(parameters.items()))
    return ""


def _average_trade_pct(metrics: dict[str, Any]) -> float | None:
    value = _finite_float(metrics.get("average_trade_pct"))
    if value is not None:
        return value
    average_trade = _finite_float(metrics.get("average_trade"))
    initial_capital = _finite_float(metrics.get("initial_capital"))
    if average_trade is None or initial_capital in (None, 0.0):
        return None
    return average_trade / initial_capital * 100.0


def build_optimizer_report_rows(results: list[dict[str, Any]], optimization_config: dict[str, Any]) -> tuple[list[dict[str, str]], list[str]]:
    """Build OptiPie-like, human-readable optimizer report rows.

    The existing ``results.csv`` remains the exhaustive machine-oriented export.
    This report intentionally mirrors the compact TradingView Optimizer/OptiPie
    layout while appending the dynamic local optimizer parameter columns.
    """

    parameter_names = _parameter_names(optimization_config, results)
    parameter_columns = [_parameter_label(name) for name in parameter_names]
    columns = [*OPTIMIZER_BASE_COLUMNS, *parameter_columns, "ITERATION", "SKIPREASON"]
    rows: list[dict[str, str]] = []
    for item in results:
        metrics = item.get("metrics") if isinstance(item.get("metrics"), dict) else {}
        parameters = item.get("parameters") if isinstance(item.get("parameters"), dict) else {}
        row = {
            "PARAMETERS": _parameter_summary(parameters, parameter_names),
            "STATUS": str(item.get("status") or ""),
            "SCORE": _format_number(item.get("score"), decimals=4),
            "NETPROFITAMOUNT": _format_number(metrics.get("total_net_pnl", metrics.get("total_pnl")), signed=True),
            "NETPROFITPERCENT": _format_number(metrics.get("total_pnl_pct", metrics.get("return_pct")), signed=True, suffix="%"),
            "MAXDRAWDOWNAMOUNT": _format_number(metrics.get("max_drawdown"), absolute=True),
            "MAXDRAWDOWNPERCENT": _format_number(metrics.get("max_drawdown_pct"), absolute=True, suffix="%"),
            "CLOSEDTRADES": _format_compact(metrics.get("closed_trades")),
            "PERCENTPROFITABLE": _format_number(metrics.get("win_rate_pct"), suffix="%"),
            "PROFITFACTOR": _format_number(metrics.get("profit_factor"), decimals=3),
            "AVERAGETRADEAMOUNT": _format_number(metrics.get("average_trade"), signed=True),
            "AVERAGETRADEPERCENT": _format_number(_average_trade_pct(metrics), signed=True, suffix="%"),
            "AVGERAGEBARSINTRADES": _format_number(metrics.get("average_bars_held"), decimals=2),
            "SHARPERATIO": _format_number(metrics.get("sharpe_ratio"), decimals=3),
            "SORTINORATIO": _format_number(metrics.get("sortino_ratio"), decimals=3),
            "EXPOSUREPERCENT": _format_number(metrics.get("exposure_pct"), suffix="%"),
            "RETURNVSBUYHOLDPCTPOINTS": _format_number(metrics.get("return_vs_buy_hold_pct_points"), signed=True),
            "ITERATION": _format_compact(item.get("iteration")),
            "SKIPREASON": str(item.get("skip_reason") or ""),
        }
        for name, column in zip(parameter_names, parameter_columns):
            row[column] = _format_compact(parameters.get(name)) if name in parameters else ""
        rows.append(row)
    return rows, columns


def _optimizer_context_html(optimization_config: dict[str, Any], results: list[dict[str, Any]], recommendations: dict[str, Any] | None) -> str:
    best = recommendations.get("best") if isinstance(recommendations, dict) else None
    recommended = recommendations.get("recommended") if isinstance(recommendations, dict) else None

    def compact_parameters(payload: Any) -> str:
        if not isinstance(payload, dict):
            return "—"
        parameters = payload.get("parameters") if isinstance(payload.get("parameters"), dict) else payload
        if not isinstance(parameters, dict) or not parameters:
            return "—"
        return ", ".join(f"{escape(str(key))}: <strong>{escape(_format_compact(value))}</strong>" for key, value in parameters.items())

    cards = [
        ("Stratégie", optimization_config.get("strategy")),
        ("Symbole", optimization_config.get("symbol")),
        ("Timeframe", f"{optimization_config.get('timeframe_minutes')} min" if optimization_config.get("timeframe_minutes") else None),
        ("Fenêtre", f"{optimization_config.get('start_date') or 'début'} → {optimization_config.get('end_date') or 'fin'}"),
        ("Score", f"{optimization_config.get('score_metric')} ({optimization_config.get('score_direction', 'max')})"),
        ("Itérations", f"{len(results):,}"),
    ]
    card_html = "\n".join(
        f"<div class=\"card\"><span>{escape(label)}</span><strong>{escape(str(value if value not in (None, '') else '—'))}</strong></div>"
        for label, value in cards
    )
    best_html = compact_parameters(best) if isinstance(best, dict) else "—"
    recommended_html = compact_parameters(recommended) if isinstance(recommended, dict) else "—"
    return f"""
    <div class="cards">{card_html}</div>
    <section class="highlights">
      <div><h2>Best observé</h2><p>{best_html}</p></div>
      <div><h2>Recommandation robuste</h2><p>{recommended_html}</p></div>
    </section>
    """


def write_optimizer_reports(
    output_dir: Path,
    results: list[dict[str, Any]],
    optimization_config: dict[str, Any],
    recommendations: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Write OptiPie-like CSV and standalone HTML reports for an optimizer job."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows, columns = build_optimizer_report_rows(results, optimization_config)
    parquet_path = output_dir / OPTIMIZER_REPORT_FILENAMES["parquet"]
    html_path = output_dir / OPTIMIZER_REPORT_FILENAMES["html"]
    pd.DataFrame(rows, columns=columns).to_parquet(parquet_path, index=False, engine="pyarrow", compression="zstd")
    _write_optimizer_html_report(html_path, rows, columns, optimization_config, results, recommendations)
    return {"parquet": str(parquet_path), "html": str(html_path)}


def _write_optimizer_html_report(
    path: Path,
    rows: list[dict[str, str]],
    columns: list[str],
    optimization_config: dict[str, Any],
    results: list[dict[str, Any]],
    recommendations: dict[str, Any] | None,
) -> None:
    best_iteration = None
    recommended_iteration = None
    if isinstance(recommendations, dict):
        best = recommendations.get("best") if isinstance(recommendations.get("best"), dict) else {}
        recommended = recommendations.get("recommended") if isinstance(recommendations.get("recommended"), dict) else {}
        best_iteration = best.get("iteration")
        recommended_iteration = recommended.get("iteration")
    if best_iteration is None:
        completed = [row for row in results if row.get("status") == "COMPLETED" and _finite_float(row.get("score")) is not None]
        if completed:
            direction = str(optimization_config.get("score_direction") or "max")
            best_item = max(completed, key=lambda item: _finite_float(item.get("score")) or float("-inf")) if direction == "max" else min(completed, key=lambda item: _finite_float(item.get("score")) or float("inf"))
            best_iteration = best_item.get("iteration")

    header_html = "".join(f"<th tabindex=\"0\">{escape(column)}</th>" for column in columns)
    columns_json = json.dumps(columns, ensure_ascii=False).replace("</", "<\\/")
    rows_json = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    best_iteration_json = json.dumps(str(best_iteration) if best_iteration is not None else None, ensure_ascii=False)
    recommended_iteration_json = json.dumps(str(recommended_iteration) if recommended_iteration is not None else None, ensure_ascii=False)
    title = f"Optimizer report — {optimization_config.get('strategy', '')} — {optimization_config.get('symbol', '')}"
    context = _optimizer_context_html(optimization_config, results, recommendations)
    html = f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escape(title)}</title>
  <style>
    :root {{ --border:#d9dee8; --muted:#667085; --bg:#f7f9fc; --accent:#2563eb; --best:#ecfdf3; --recommended:#eff6ff; }}
    body {{ margin:0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color:#111827; background:white; }}
    header {{ padding:2rem 2.5rem 1rem; border-bottom:1px solid var(--border); background:linear-gradient(180deg,#fff,var(--bg)); }}
    h1 {{ margin:0 0 .4rem; font-size:1.7rem; }}
    .subtitle {{ margin:0; color:var(--muted); }}
    .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:.75rem; margin:1.25rem 0; }}
    .card {{ border:1px solid var(--border); border-radius:12px; padding:.75rem .9rem; background:white; }}
    .card span {{ display:block; color:var(--muted); font-size:.8rem; margin-bottom:.25rem; }}
    .card strong {{ font-size:.95rem; }}
    .highlights {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:.75rem; margin-top:.75rem; }}
    .highlights div {{ border:1px solid var(--border); border-radius:12px; padding:.85rem 1rem; background:white; }}
    .highlights h2 {{ margin:0 0 .4rem; font-size:1rem; }}
    .highlights p {{ margin:0; color:#1f2937; }}
    main {{ padding:1rem 2.5rem 2.5rem; }}
    .toolbar {{ position:sticky; top:0; z-index:2; display:flex; flex-wrap:wrap; gap:.75rem; align-items:center; padding:.75rem 0; background:white; }}
    input[type="search"] {{ min-width:280px; padding:.55rem .7rem; border:1px solid var(--border); border-radius:8px; font:inherit; }}
    select {{ padding:.55rem .7rem; border:1px solid var(--border); border-radius:8px; font:inherit; background:white; }}
    button {{ padding:.55rem .75rem; border:1px solid var(--border); border-radius:8px; background:white; color:#111827; font:inherit; font-weight:600; cursor:pointer; }}
    button:disabled {{ color:#9ca3af; cursor:not-allowed; }}
    a.button {{ color:white; background:var(--accent); text-decoration:none; padding:.55rem .75rem; border-radius:8px; font-weight:600; }}
    .count {{ color:var(--muted); margin-left:auto; }}
    .pagination {{ display:flex; flex-wrap:wrap; gap:.5rem; align-items:center; color:var(--muted); }}
    .pagination strong {{ color:#111827; }}
    .table-wrap {{ overflow:auto; border:1px solid var(--border); border-radius:12px; }}
    table {{ border-collapse:separate; border-spacing:0; width:100%; font-size:.88rem; }}
    th,td {{ white-space:nowrap; border-bottom:1px solid var(--border); border-right:1px solid var(--border); padding:.48rem .6rem; text-align:right; }}
    th:first-child,td:first-child {{ text-align:left; position:sticky; left:0; background:inherit; z-index:1; }}
    th {{ background:#eef2f7; cursor:pointer; user-select:none; }}
    th:first-child {{ z-index:2; background:#eef2f7; }}
    tbody tr:nth-child(even) {{ background:#fbfcff; }}
    tbody tr:hover {{ background:#fff7ed; }}
    tr.best-row {{ background:var(--best) !important; }}
    tr.recommended-row {{ background:var(--recommended) !important; }}
    tr.best-row.recommended-row {{ background:linear-gradient(90deg,var(--best),var(--recommended)) !important; }}
    .legend {{ color:var(--muted); font-size:.86rem; }}
  </style>
</head>
<body>
  <header>
    <h1>{escape(title)}</h1>
    <p class="subtitle">Rapport optimizer local inspiré de la structure OptiPie/TradingView Optimizer. Le Parquet brut complet reste disponible via <code>results.parquet</code>.</p>
    {context}
  </header>
  <main>
    <div class="toolbar">
      <input id="search" type="search" placeholder="Rechercher dans le rapport…" />
      <div class="pagination" aria-label="Pagination du rapport">
        <span id="range-status">Showing 0 to 0 of 0 rows</span>
        <label>
          <select id="page-size" aria-label="Rows per page">
            <option value="10" selected>10</option>
            <option value="25">25</option>
            <option value="50">50</option>
            <option value="100">100</option>
          </select>
          rows per page
        </label>
        <button id="prev-page" type="button">Précédent</button>
        <strong id="page-status">Page 1 / 1</strong>
        <button id="next-page" type="button">Suivant</button>
      </div>
      <a class="button" href="optimizer_report.parquet">Télécharger le Parquet rapport</a>
      <a class="button" href="results.parquet">Parquet brut</a>
      <a class="button" href="recommendations.json">Recommandations JSON</a>
      <span class="count"><span id="visible-count">{len(rows):,}</span> / {len(rows):,} lignes</span>
    </div>
    <p class="legend">Clique sur un en-tête pour trier. Les lignes vertes indiquent le meilleur score observé; les lignes bleues indiquent la recommandation robuste quand disponible.</p>
    <div class="table-wrap">
      <table id="report-table">
        <thead><tr>{header_html}</tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </main>
  <script>
    const columns = {columns_json};
    const allRows = {rows_json};
    const bestIteration = {best_iteration_json};
    const recommendedIteration = {recommended_iteration_json};
    const table = document.getElementById('report-table');
    const tbody = table.tBodies[0];
    const search = document.getElementById('search');
    const visibleCount = document.getElementById('visible-count');
    const pageSizeSelect = document.getElementById('page-size');
    const rangeStatus = document.getElementById('range-status');
    const pageStatus = document.getElementById('page-status');
    const prevPage = document.getElementById('prev-page');
    const nextPage = document.getElementById('next-page');
    let filteredRows = allRows.slice();
    let currentPage = 1;
    let sortState = {{ index: null, direction: 'asc' }};
    function numericValue(text) {{
      const cleaned = String(text).replace(/[%+,]/g, '').replace(/[^0-9.\\-]/g, '');
      if (!cleaned || cleaned === '-' || cleaned === '.') return NaN;
      return Number(cleaned);
    }}
    function compareRows(left, right, index, direction) {{
      const column = columns[index];
      const leftText = left[column] ?? '';
      const rightText = right[column] ?? '';
      const leftNum = numericValue(leftText);
      const rightNum = numericValue(rightText);
      let result;
      if (!Number.isNaN(leftNum) && !Number.isNaN(rightNum)) {{
        result = leftNum - rightNum;
      }} else {{
        result = String(leftText).localeCompare(String(rightText), undefined, {{ numeric: true, sensitivity: 'base' }});
      }}
      return direction === 'asc' ? result : -result;
    }}
    function applySort() {{
      if (sortState.index === null) return;
      filteredRows.sort((a, b) => compareRows(a, b, sortState.index, sortState.direction));
    }}
    function renderPage() {{
      const pageSize = Number(pageSizeSelect.value);
      const totalRows = filteredRows.length;
      const totalPages = Math.max(1, Math.ceil(totalRows / pageSize));
      currentPage = Math.min(Math.max(1, currentPage), totalPages);
      const startIndex = totalRows === 0 ? 0 : (currentPage - 1) * pageSize;
      const endIndex = Math.min(startIndex + pageSize, totalRows);
      const fragment = document.createDocumentFragment();
      for (const rowData of filteredRows.slice(startIndex, endIndex)) {{
        const tr = document.createElement('tr');
        const iteration = rowData.ITERATION ? String(rowData.ITERATION) : '';
        if (iteration && iteration === bestIteration) tr.classList.add('best-row');
        if (iteration && iteration === recommendedIteration) tr.classList.add('recommended-row');
        for (const column of columns) {{
          const td = document.createElement('td');
          td.textContent = rowData[column] ?? '';
          tr.appendChild(td);
        }}
        fragment.appendChild(tr);
      }}
      tbody.replaceChildren(fragment);
      const displayStart = totalRows === 0 ? 0 : startIndex + 1;
      rangeStatus.textContent = `Showing ${{displayStart.toLocaleString()}} to ${{endIndex.toLocaleString()}} of ${{totalRows.toLocaleString()}} rows`;
      pageStatus.textContent = `Page ${{currentPage.toLocaleString()}} / ${{totalPages.toLocaleString()}}`;
      visibleCount.textContent = totalRows.toLocaleString();
      prevPage.disabled = currentPage <= 1;
      nextPage.disabled = currentPage >= totalPages;
    }}
    function updateFilter() {{
      const q = search.value.trim().toLowerCase();
      filteredRows = !q ? allRows.slice() : allRows.filter(row => columns.some(column => String(row[column] ?? '').toLowerCase().includes(q)));
      applySort();
      currentPage = 1;
      renderPage();
    }}
    search.addEventListener('input', updateFilter);
    pageSizeSelect.addEventListener('change', () => {{ currentPage = 1; renderPage(); }});
    prevPage.addEventListener('click', () => {{ currentPage -= 1; renderPage(); }});
    nextPage.addEventListener('click', () => {{ currentPage += 1; renderPage(); }});
    table.querySelectorAll('th').forEach((th, index) => {{
      th.addEventListener('click', () => {{
        const direction = sortState.index === index && sortState.direction === 'asc' ? 'desc' : 'asc';
        table.querySelectorAll('th').forEach(item => delete item.dataset.direction);
        th.dataset.direction = direction;
        sortState = {{ index, direction }};
        applySort();
        currentPage = 1;
        renderPage();
      }});
      th.addEventListener('keydown', event => {{ if (event.key === 'Enter') th.click(); }});
    }});
    renderPage();
  </script>
</body>
</html>
"""
    path.write_text(html, encoding="utf-8")
