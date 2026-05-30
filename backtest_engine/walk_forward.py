"""
Walk-Forward Analysis (WFA) module for Phase 4 — Validation and Generalisation.

Supports rolling IS/OOS windows, baseline fixed-parameter evaluation,
Bayesian re-optimisation on IS, and overfitting metrics (PBO / DSR).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .data import load_canonical_market_data
from .reports import BacktestRunResult
from .strategy_registry import StrategyRegistry
from .optimizer import ParameterGridSpec
from .overfitting_analysis import compute_dsr, compute_pbo_cscv

logger = logging.getLogger(__name__)

# Best params from Phase 3 (LOGI 2022-2023, combined mode, Sharpe 3.13)
PHASE3_BASELINE_PARAMS: dict[str, Any] = {
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

DEFAULT_NOISE_BOUNDARY_SPECS: list[ParameterGridSpec] = [
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


@dataclass
class WFAFoldResult:
    symbol: str
    fold_idx: int
    is_start: str
    is_end: str
    oos_start: str
    oos_end: str

    # Baseline (fixed Phase-3 params)
    baseline_is_sharpe: float | None = None
    baseline_is_cagr: float | None = None
    baseline_is_mdd: float | None = None
    baseline_is_trades: int | None = None
    baseline_oos_sharpe: float | None = None
    baseline_oos_cagr: float | None = None
    baseline_oos_mdd: float | None = None
    baseline_oos_trades: int | None = None

    # Re-optimised (best params found on IS, validated on OOS)
    reopt_params: dict | None = None
    reopt_is_sharpe: float | None = None
    reopt_is_cagr: float | None = None
    reopt_is_mdd: float | None = None
    reopt_is_trades: int | None = None
    reopt_oos_sharpe: float | None = None
    reopt_oos_cagr: float | None = None
    reopt_oos_mdd: float | None = None
    reopt_oos_trades: int | None = None

    # Overfitting diagnostics
    pbo: float | None = None
    dsr: float | None = None


def generate_rolling_windows(
    start_date: str | pd.Timestamp,
    end_date: str | pd.Timestamp,
    is_years: int = 3,
    oos_years: int = 1,
) -> list[tuple[str, str, str, str]]:
    """Generate rolling IS/OOS date windows advancing by ``oos_years``.

    Returns
    -------
    list[tuple[is_start, is_end, oos_start, oos_end]]
    """
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    windows: list[tuple[str, str, str, str]] = []
    current = start

    while True:
        is_end = current + pd.DateOffset(years=is_years)
        oos_start = is_end
        oos_end = oos_start + pd.DateOffset(years=oos_years)
        if oos_end > end:
            break
        windows.append(
            (
                current.strftime("%Y-%m-%d"),
                is_end.strftime("%Y-%m-%d"),
                oos_start.strftime("%Y-%m-%d"),
                oos_end.strftime("%Y-%m-%d"),
            )
        )
        current = current + pd.DateOffset(years=oos_years)

    return windows


def _run_single_backtest(
    data: pd.DataFrame,
    symbol: str,
    params: dict[str, Any],
    initial_capital: float,
    timeframe_minutes: int,
    repo_root: Path | None = None,
    strategy: str = "noise_boundary_intraday",
    compute_full_metrics: bool = True,
    fast_score_metric: str | None = None,
) -> BacktestRunResult:
    """Run a strategy with the given parameter dict, resolved via the registry."""
    info = StrategyRegistry.get(strategy)
    overrides = info.overrides_from_mapping_function(params)
    kwargs: dict[str, Any] = dict(
        data=data,
        symbol=symbol,
        overrides=overrides,
        initial_capital=initial_capital,
        timeframe_minutes=timeframe_minutes,
        compute_full_metrics=compute_full_metrics,
    )
    if not compute_full_metrics and fast_score_metric:
        kwargs["fast_score_metric"] = fast_score_metric
    # Some runners accept repo_root (e.g. noise_boundary_intraday)
    import inspect
    sig = inspect.signature(info.run_function)
    if "repo_root" in sig.parameters:
        kwargs["repo_root"] = repo_root
    return info.run_function(**kwargs)


def _extract_metrics(result: BacktestRunResult) -> dict[str, float | int | None]:
    m = result.metrics
    return {
        "sharpe_ratio": m.get("sharpe_ratio"),
        "cagr_pct": m.get("cagr_pct"),
        "max_drawdown_pct": m.get("max_drawdown_pct"),
        "return_pct": m.get("return_pct"),
        "closed_trades": m.get("closed_trades"),
        "win_rate_pct": m.get("win_rate_pct"),
        "profit_factor": m.get("profit_factor"),
    }


def run_wfa_fold(
    *,
    symbol: str,
    is_data: pd.DataFrame,
    oos_data: pd.DataFrame,
    fold_idx: int,
    is_start: str,
    is_end: str,
    oos_start: str,
    oos_end: str,
    baseline_params: dict[str, Any] | None = None,
    parameter_specs: list[ParameterGridSpec] | None = None,
    reoptimize: bool = True,
    reopt_trials: int = 50,
    reopt_max_trials_for_pbo: int = 30,
    initial_capital: float = 1000.0,
    timeframe_minutes: int = 5,
    output_root: Path | None = None,
    repo_root: Path | None = None,
    strategy: str = "noise_boundary_intraday",
) -> WFAFoldResult:
    """Execute one WFA fold with baseline + optional IS re-optimisation."""

    baseline_params = baseline_params or PHASE3_BASELINE_PARAMS.copy()
    result = WFAFoldResult(
        symbol=symbol,
        fold_idx=fold_idx,
        is_start=is_start,
        is_end=is_end,
        oos_start=oos_start,
        oos_end=oos_end,
    )

    # ── Branch A: baseline fixed params ───────────────────────────────
    baseline_is = _run_single_backtest(
        is_data, symbol, baseline_params, initial_capital, timeframe_minutes, repo_root, strategy=strategy
    )
    b_is = _extract_metrics(baseline_is)
    result.baseline_is_sharpe = b_is["sharpe_ratio"]
    result.baseline_is_cagr = b_is["cagr_pct"]
    result.baseline_is_mdd = b_is["max_drawdown_pct"]
    result.baseline_is_trades = b_is["closed_trades"]

    baseline_oos = _run_single_backtest(
        oos_data, symbol, baseline_params, initial_capital, timeframe_minutes, repo_root, strategy=strategy
    )
    b_oos = _extract_metrics(baseline_oos)
    result.baseline_oos_sharpe = b_oos["sharpe_ratio"]
    result.baseline_oos_cagr = b_oos["cagr_pct"]
    result.baseline_oos_mdd = b_oos["max_drawdown_pct"]
    result.baseline_oos_trades = b_oos["closed_trades"]

    # ── Branch B: re-optimise on IS ──────────────────────────────────
    if reoptimize:
        specs = parameter_specs or DEFAULT_NOISE_BOUNDARY_SPECS
        opt_out = (output_root or Path("reports/noise_boundary_intraday/phase4_wfa/reopt")) / f"{symbol}_fold{fold_idx}"

        try:
            from .bayesian_optimizer import run_bayesian_optimization

            opt_summary = run_bayesian_optimization(
                data=is_data,
                symbol=symbol,
                parameter_specs=specs,
                fixed_overrides=None,
                initial_capital=initial_capital,
                output_root=opt_out,
                timeframe_minutes=timeframe_minutes,
                strategy=strategy,
                score_metric="sharpe_ratio",
                score_direction="max",
                n_trials=reopt_trials,
                workers=1,
                write_best_run=False,
                enable_convergence_stop=True,
                convergence_patience=max(20, reopt_trials // 3),
                convergence_window_size=15,
            )

            best = opt_summary.best_row
            if best and best.get("parameters"):
                reopt_params = best["parameters"]
                result.reopt_params = reopt_params

                # IS validation of reopt params
                r_is = _run_single_backtest(
                    is_data, symbol, reopt_params, initial_capital, timeframe_minutes, repo_root, strategy=strategy
                )
                r_is_m = _extract_metrics(r_is)
                result.reopt_is_sharpe = r_is_m["sharpe_ratio"]
                result.reopt_is_cagr = r_is_m["cagr_pct"]
                result.reopt_is_mdd = r_is_m["max_drawdown_pct"]
                result.reopt_is_trades = r_is_m["closed_trades"]

                # OOS validation of reopt params
                r_oos = _run_single_backtest(
                    oos_data, symbol, reopt_params, initial_capital, timeframe_minutes, repo_root, strategy=strategy
                )
                r_oos_m = _extract_metrics(r_oos)
                result.reopt_oos_sharpe = r_oos_m["sharpe_ratio"]
                result.reopt_oos_cagr = r_oos_m["cagr_pct"]
                result.reopt_oos_mdd = r_oos_m["max_drawdown_pct"]
                result.reopt_oos_trades = r_oos_m["closed_trades"]

                # ── PBO (CSCV) ────────────────────────────────────────
                # Re-run top trials on IS to build daily-returns matrix
                completed = [
                    r for r in opt_summary.results
                    if r.get("status") == "COMPLETED" and r.get("parameters")
                ]
                # Sort by Sharpe descending and keep top N for PBO speed
                completed.sort(
                    key=lambda x: x.get("metrics", {}).get("sharpe_ratio", -np.inf),
                    reverse=True,
                )
                top_trials = completed[:reopt_max_trials_for_pbo]

                daily_returns_matrix: list[np.ndarray] = []
                for trial in top_trials:
                    try:
                        tr = _run_single_backtest(
                            is_data, symbol, trial["parameters"],
                            initial_capital, timeframe_minutes, repo_root, strategy=strategy,
                        )
                        if not tr.equity_curve.empty and "equity" in tr.equity_curve.columns:
                            equity = tr.equity_curve["equity"].resample("D").last().dropna()
                            daily = equity.pct_change().dropna().values
                            if len(daily) > 1:
                                daily_returns_matrix.append(daily)
                    except Exception:
                        continue

                if len(daily_returns_matrix) >= 4:
                    # Align lengths (pad shortest with zeros or truncate to min)
                    min_len = min(len(d) for d in daily_returns_matrix)
                    mat = np.array([d[:min_len] for d in daily_returns_matrix])
                    result.pbo = compute_pbo_cscv(mat, n_splits=16)

                # ── DSR ───────────────────────────────────────────────
                if (
                    not r_oos.equity_curve.empty
                    and "equity" in r_oos.equity_curve.columns
                ):
                    equity = r_oos.equity_curve["equity"].resample("D").last().dropna()
                    daily = equity.pct_change().dropna().values
                    if len(daily) > 1 and result.reopt_oos_sharpe is not None:
                        result.dsr = compute_dsr(
                            returns=daily,
                            sharpe_observed=result.reopt_oos_sharpe,
                            n_trials=reopt_trials,
                        )

        except Exception as exc:
            logger.warning("Re-optimisation failed for %s fold %d: %s", symbol, fold_idx, exc)

    return result


def run_wfa_full(
    *,
    symbol: str,
    repo_root: Path,
    start_date: str,
    end_date: str,
    is_years: int = 3,
    oos_years: int = 1,
    processed_dir: str = "storage/processed",
    baseline_params: dict[str, Any] | None = None,
    parameter_specs: list[ParameterGridSpec] | None = None,
    reoptimize: bool = True,
    reopt_trials: int = 50,
    initial_capital: float = 1000.0,
    timeframe_minutes: int = 5,
    output_root: Path | None = None,
    strategy: str = "noise_boundary_intraday",
) -> list[WFAFoldResult]:
    """Run complete WFA for a single symbol."""

    data = load_canonical_market_data(
        symbol=symbol,
        repo_root=repo_root,
        processed_dir=processed_dir,
        start_date=start_date,
        end_date=end_date,
        timeframe_minutes=timeframe_minutes,
    )
    if data.empty:
        raise ValueError(f"No data for {symbol} between {start_date} and {end_date}")

    windows = generate_rolling_windows(start_date, end_date, is_years, oos_years)
    if not windows:
        raise ValueError(
            f"No WFA windows for {symbol} (IS={is_years}y, OOS={oos_years}y)"
        )

    results: list[WFAFoldResult] = []
    for fold_idx, (is_s, is_e, oos_s, oos_e) in enumerate(windows):
        is_data = data.loc[is_s:is_e]
        oos_data = data.loc[oos_s:oos_e]
        if is_data.empty or oos_data.empty:
            logger.warning("Empty slice for %s fold %d — skipping", symbol, fold_idx)
            continue

        fold = run_wfa_fold(
            symbol=symbol,
            is_data=is_data,
            oos_data=oos_data,
            fold_idx=fold_idx,
            is_start=is_s,
            is_end=is_e,
            oos_start=oos_s,
            oos_end=oos_e,
            baseline_params=baseline_params,
            parameter_specs=parameter_specs,
            reoptimize=reoptimize,
            reopt_trials=reopt_trials,
            initial_capital=initial_capital,
            timeframe_minutes=timeframe_minutes,
            output_root=output_root,
            repo_root=repo_root,
            strategy=strategy,
        )
        results.append(fold)

    return results
