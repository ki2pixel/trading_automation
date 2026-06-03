from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from .canonical import build_canonical_dataset
from .data import load_canonical_market_data, load_market_data, scan_market_data, validate_timeframe_minutes
from .optimizer import allowed_score_metrics, estimate_iterations, load_data_and_optimize, parse_cli_parameter, validate_iteration_limits, validate_parameter_grid, validate_score_metric
from .report_interpreter import write_optimization_recommendations
from .reports import write_backtest_outputs
from .strategy_registry import StrategyRegistry
from .web import run_optimizer_worker, serve_optimizer_app
from .paths import get_reports_dir


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def cmd_scan(args: argparse.Namespace) -> int:
    report = scan_market_data(
        symbol=args.symbol,
        repo_root=Path(args.repo_root),
        price_repair=args.price_repair,
        market_divisor=args.market_divisor,
        max_files=args.max_files,
        max_rows=args.max_rows,
    )
    payload = report.to_dict()
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if report.error_count == 0 else 2


def cmd_run(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root)
    info = StrategyRegistry.get(args.strategy)
    config_overrides = info.config_override_class()
    load_overrides_fn = info.load_overrides_function
    run_fn = info.run_function
    config_backtest: dict[str, object] = {}
    if args.config:
        config_overrides, config_backtest = load_overrides_fn(args.config)
    if args.data_source == "canonical":
        data = load_canonical_market_data(
            symbol=args.symbol,
            repo_root=repo_root,
            processed_dir=args.processed_dir,
            max_rows=args.max_rows,
            timeframe_minutes=args.timeframe,
            start_date=args.start_date,
            end_date=args.end_date,
        )
    else:
        data = load_market_data(
            symbol=args.symbol,
            repo_root=repo_root,
            price_repair=args.price_repair,
            market_divisor=args.market_divisor,
            max_files=args.max_files,
            max_rows=args.max_rows,
            start_date=args.start_date,
            end_date=args.end_date,
        )

    import inspect
    overrides = _strategy_overrides_from_args(args, base=config_overrides)
    initial_capital = args.initial_capital if args.initial_capital is not None else float(config_backtest.get("initial_capital", 1000.0))
    
    run_kwargs = {
        "data": data,
        "symbol": args.symbol,
        "overrides": overrides,
        "initial_capital": initial_capital,
        "timeframe_minutes": args.timeframe,
        "repo_root": repo_root,
    }
    
    sig = inspect.signature(run_fn)
    if "early_stop_drawdown_pct" in sig.parameters:
        run_kwargs["early_stop_drawdown_pct"] = args.early_stop_drawdown_pct
        
    result = run_fn(**run_kwargs)
    output_dir_path = Path(args.output_dir)
    if not output_dir_path.is_absolute():
        output_dir_path = (repo_root / output_dir_path).resolve()
    output_dir = write_backtest_outputs(result, output_dir_path)
    print(f"Backtest written to: {output_dir}")
    print(json.dumps(result.metrics, indent=2, ensure_ascii=False, default=str))
    return 0


def _split_csv_arg(value: str | None) -> list[str] | None:
    if value is None or value.strip() == "":
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def _parse_divisor_overrides(value: str | None) -> dict[str, float]:
    if not value:
        return {}
    overrides: dict[str, float] = {}
    for item in value.split(","):
        if not item.strip():
            continue
        if "=" not in item:
            raise ValueError(f"Invalid divisor override {item!r}; expected SYMBOL=DIVISOR")
        symbol, divisor = item.split("=", 1)
        overrides[symbol.strip()] = float(divisor.strip())
    return overrides


def _load_divisor_overrides_file(path: str | None) -> dict[str, float]:
    if not path:
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Divisor overrides file must contain a JSON object {symbol: divisor}")
    return {str(symbol): float(divisor) for symbol, divisor in payload.items()}


def cmd_build_canonical(args: argparse.Namespace) -> int:
    overrides = _load_divisor_overrides_file(args.divisor_overrides_file)
    overrides.update(_parse_divisor_overrides(args.divisor_overrides))
    repo_root = Path(args.repo_root).resolve()
    output_dir_path = Path(args.output_dir)
    if not output_dir_path.is_absolute():
        output_dir_path = (repo_root / output_dir_path).resolve()
    summary = build_canonical_dataset(
        repo_root=repo_root,
        output_dir=output_dir_path,
        symbols=_split_csv_arg(args.symbols),
        fx_pairs=_split_csv_arg(args.fx_pairs),
        include_market=not args.no_market,
        include_fx=not args.no_fx,
        include_splits=not args.no_splits,
        price_repair=args.price_repair,
        market_divisor=args.market_divisor,
        divisor_overrides=overrides,
        output_format=args.format,
        max_files=args.max_files,
        max_rows=args.max_rows,
        verbose=not args.quiet,
    )
    print(json.dumps(summary.to_dict(), indent=2, ensure_ascii=False))
    return 0


def _strategy_overrides_from_args(args: argparse.Namespace, base: Any | None = None) -> Any:
    if base is not None:
        override_cls = type(base)
    else:
        override_cls = StrategyRegistry.get(args.strategy).config_override_class
    payload = asdict(base or override_cls())
    for field_name in override_cls.__dataclass_fields__:
        arg_name = field_name
        if not hasattr(args, arg_name):
            continue
        value = getattr(args, arg_name)
        if value is not None:
            payload[field_name] = value
    if getattr(args, "whole_shares", False):
        payload["allow_fractional_quantity"] = False
    elif base is None:
        payload["allow_fractional_quantity"] = True
    return override_cls(**payload)

def _hma_overrides_from_args(args: argparse.Namespace, base: Any | None = None) -> Any:
    return _strategy_overrides_from_args(args, base=base)


def cmd_optimize(args: argparse.Namespace) -> int:
    info = StrategyRegistry.get(args.strategy)
    config_overrides = info.config_override_class()
    load_overrides_fn = info.load_overrides_function
    config_backtest: dict[str, object] = {}
    if args.config:
        config_overrides, config_backtest = load_overrides_fn(args.config)
    fixed_overrides = _strategy_overrides_from_args(args, base=config_overrides)
    initial_capital = args.initial_capital if args.initial_capital is not None else float(config_backtest.get("initial_capital", 1000.0))
    score_metric = validate_score_metric(args.score, strategy=args.strategy)
    parameter_specs = [parse_cli_parameter(value, strategy=args.strategy) for value in args.param]
    total_iterations = estimate_iterations(parameter_specs)
    grid_validation = validate_parameter_grid(parameter_specs, fixed_overrides=fixed_overrides, strategy=args.strategy)
    max_raw_iterations = args.max_raw_iterations if args.max_raw_iterations is not None else args.max_iterations
    max_canonical_iterations = args.max_canonical_iterations if args.max_canonical_iterations is not None else args.max_iterations

    # Grid-size limits only apply in grid mode
    if args.optimization_mode == "grid":
        validate_iteration_limits(
            raw_iterations=total_iterations,
            canonical_iterations=grid_validation["canonical_iterations"],
            max_raw_iterations=max_raw_iterations,
            max_canonical_iterations=max_canonical_iterations,
        )
    payload = {
        "strategy": args.strategy,
        "symbol": args.symbol,
        "timeframe_minutes": validate_timeframe_minutes(args.timeframe),
        "start_date": args.start_date,
        "end_date": args.end_date,
        "score_metric": score_metric,
        "score_direction": args.score_direction,
        "total_iterations": total_iterations,
        "canonical_iterations": grid_validation["canonical_iterations"],
        "valid_iterations": grid_validation["valid_iterations"],
        "skipped_iterations": grid_validation["skipped_iterations"],
        "deduplicated_inactive_iterations": grid_validation["deduplicated_inactive_iterations"],
        "skipped_examples": grid_validation["skipped_examples"],
        "max_raw_iterations": max_raw_iterations,
        "max_canonical_iterations": max_canonical_iterations,
        "min_closed_trades": args.min_closed_trades,
        "workers": args.workers,
        "parameters": [asdict(spec) for spec in parameter_specs],
    }
    if args.dry_run:
        print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        return 0

    def print_progress(progress) -> None:
        print(
            f"{progress.current_iteration}/{progress.total_iterations} "
            f"best {score_metric}={progress.best_score} params={progress.best_parameters}",
            flush=True,
        )

    repo_root = Path(args.repo_root).resolve()
    output_dir_path = Path(args.output_dir)
    if not output_dir_path.is_absolute():
        output_dir_path = (repo_root / output_dir_path).resolve()

    summary = load_data_and_optimize(
        repo_root=repo_root,
        symbol=args.symbol,
        processed_dir=args.processed_dir,
        timeframe_minutes=args.timeframe,
        start_date=args.start_date,
        end_date=args.end_date,
        parameter_specs=parameter_specs,
        fixed_overrides=fixed_overrides,
        initial_capital=initial_capital,
        output_root=output_dir_path,
        strategy=args.strategy,
        score_metric=score_metric,
        score_direction=args.score_direction,
        secondary_score_metric=args.secondary_score,
        secondary_score_direction=args.secondary_score_direction,
        max_rows=args.max_rows,
        max_iterations=args.max_iterations,
        max_raw_iterations=max_raw_iterations,
        max_canonical_iterations=max_canonical_iterations,
        min_closed_trades=args.min_closed_trades,
        workers=args.workers,
        write_best_run=not args.no_best_run,
        progress_callback=print_progress,
        optimization_mode=args.optimization_mode,
        early_stop_drawdown_pct=args.early_stop_drawdown_pct,
        enable_convergence_stop=args.enable_convergence_stop,
        convergence_patience=args.convergence_patience,
        convergence_min_improvement=args.convergence_min_improvement,
        convergence_window_size=args.convergence_window_size,
        convergence_window_count=args.convergence_window_count,
        circuit_breaker_ratio=args.circuit_breaker_ratio,
        wfo_windows=args.wfo_windows,
    )
    print(f"Optimization written to: {summary.output_dir}")
    print(json.dumps({k: v for k, v in asdict(summary).items() if k != "results"}, indent=2, ensure_ascii=False, default=str))
    if summary.status == "FAILED":
        return 1
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    output_dir_path = Path(args.output_dir)
    if not output_dir_path.is_absolute():
        output_dir_path = (repo_root / output_dir_path).resolve()
    serve_optimizer_app(
        repo_root=repo_root,
        host=args.host,
        port=args.port,
        processed_dir=args.processed_dir,
        output_dir=str(output_dir_path),
    )
    return 0


def cmd_worker(args: argparse.Namespace) -> int:
    import signal
    import sys
    import logging
    import traceback
    from datetime import datetime
    
    logger = logging.getLogger("backtest_engine.worker_main")
    
    def signal_handler(signum, frame):
        logger.info(f"Signal {signum} reçu. Arrêt propre du worker...")
        for handler in logging.root.handlers[:]:
            try:
                handler.flush()
            except Exception:  # NOSONAR
                pass
        sys.exit(0)
        
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    repo_root = Path(args.repo_root).resolve()
    output_dir_path = Path(args.output_dir)
    if not output_dir_path.is_absolute():
        output_dir_path = (repo_root / output_dir_path).resolve()
        
    try:
        return run_optimizer_worker(
            repo_root=repo_root,
            processed_dir=args.processed_dir,
            output_dir=str(output_dir_path),
            poll_interval=args.poll_interval,
            once=args.once,
            worker_id=args.worker_id,
        )
    except Exception as e:
        output_dir_path.mkdir(parents=True, exist_ok=True)
        error_log = output_dir_path / "worker_error.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tb = traceback.format_exc()
        
        with open(error_log, "a", encoding="utf-8") as f:
            f.write(f"\n========================================\n")
            f.write(f"TIMESTAMP: {timestamp}\n")
            f.write(f"EXCEPTION: {type(e).__name__}: {e}\n")
            f.write(f"TRACEBACK:\n{tb}")
            f.write(f"========================================\n")
            
        logger.error(f"Worker crashed with exception: {e}. Traceback logged to {error_log}")
        return 1


def cmd_mark_crashed(args: argparse.Namespace) -> int:
    from .job_store import OptimizerJobStore
    repo_root = Path(args.repo_root).resolve()
    output_dir_path = Path(args.output_dir)
    if not output_dir_path.is_absolute():
        output_dir_path = (repo_root / output_dir_path).resolve()
    job_store_path = output_dir_path / "jobs.sqlite3"
    
    store = OptimizerJobStore(storage_path=job_store_path)
    exit_code = args.exit_code
    
    if exit_code == 137:
        reason = "Worker crashed (respawned by supervisor, exit code 137: OOM / SIGKILL)"
    elif exit_code == 139:
        reason = "Worker crashed (respawned by supervisor, exit code 139: Segfault / SIGSEGV)"
    else:
        reason = f"Worker crashed (respawned by supervisor, exit code {exit_code})"
        
    count = store.mark_worker_crashed(worker_id=args.worker_id, error_message=reason)
    print(f"Successfully marked {count} in-progress jobs as FAILED for worker {args.worker_id}")
    return 0



def cmd_interpret_optimization(args: argparse.Namespace) -> int:
    report = write_optimization_recommendations(
        Path(args.job_dir),
        top_quantile=args.top_quantile,
        score_tolerance_pct=args.score_tolerance_pct,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m backtest_engine",
        description="Local backtesting POC for converted Pine/TradingView strategies.",
    )
    parser.add_argument("--repo-root", default=str(_repo_root()), help="Repository root path")

    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Scan SheetsFinance market CSVs for data-quality issues")
    scan.add_argument("--symbol", required=True)
    scan.add_argument("--price-repair", choices=["none", "auto"], default="none")
    scan.add_argument("--market-divisor", type=float, default=1.0)
    scan.add_argument("--max-files", type=int, default=None)
    scan.add_argument("--max-rows", type=int, default=None)
    scan.add_argument("--output", default=None)
    scan.set_defaults(func=cmd_scan)

    run = sub.add_parser("run", help="Run the HMA crossover POC backtest")
    run.add_argument("--symbol", required=True)
    run.add_argument("--strategy", choices=["hma_crossover", "adaptive_volatility_trend", "range_filter", "3commas_bot", "pmax_explorer", "bjorgum_double_tap", "noise_boundary_intraday"], default="hma_crossover")
    run.add_argument(
        "--data-source",
        choices=["canonical", "raw"],
        default="canonical",
        help="Use cleaned canonical data from storage/processed by default, or raw SheetsFinance CSVs for diagnostics",
    )
    run.add_argument("--processed-dir", default="storage/processed", help="Canonical dataset root for --data-source canonical")
    run.add_argument("--timeframe", type=int, default=5, help="Backtest timeframe in minutes; must be a multiple of 5")
    run.add_argument("--start-date", default=None, help="Inclusive backtest window start, e.g. 2024-01-01")
    run.add_argument("--end-date", default=None, help="Inclusive backtest window end, e.g. 2025-01-01")
    run.add_argument("--price-repair", choices=["none", "auto"], default="none")
    run.add_argument("--market-divisor", type=float, default=1.0)
    run.add_argument("--max-files", type=int, default=None)
    run.add_argument("--max-rows", type=int, default=None)
    run.add_argument("--output-dir", default=str(get_reports_dir() / "local"))
    run.add_argument("--config", default=None, help="Fichier JSON de configuration stratégie/backtest")
    run.add_argument("--initial-capital", type=float, default=None)
    run.add_argument("--fast-len", type=int, default=None)
    run.add_argument("--slow-len", type=int, default=None)
    run.add_argument("--max-entry-price", type=float, default=None)
    run.add_argument("--max-capital-bucket", type=float, default=None)
    run.add_argument("--initial-capital-bucket", type=float, default=None)
    run.add_argument(
        "--trade-direction-mode",
        choices=["Long & Short", "Long only", "Short only"],
        default=None,
    )
    run.add_argument("--fee-mode", choices=["Parametric: hold until net covers fees", "Parametric: exit only, no forced reversal", "Disabled: always reverse/close on opposite signal"], default=None)
    run.add_argument("--estimated-commission-per-order-long", type=float, default=None)
    run.add_argument("--estimated-commission-per-order-short", type=float, default=None)
    run.add_argument("--estimated-slippage-per-side-long", type=float, default=None)
    run.add_argument("--estimated-slippage-per-side-short", type=float, default=None)
    run.add_argument("--min-net-profit-after-costs", type=float, default=None)
    run.add_argument("--use-net-bracket-exits", action="store_true", default=None)
    run.add_argument("--take-profit-net-percent", type=float, default=None)
    run.add_argument("--stop-loss-net-percent", type=float, default=None)
    run.add_argument("--use-safety-stop", action="store_true", default=None)
    run.add_argument("--safety-stop-applies-to", choices=["Both", "Long only", "Short only"], default=None)
    run.add_argument("--safety-stop-mode", choices=["Net loss only", "Max bars only", "Net loss OR max bars", "Net loss AND max bars"], default=None)
    run.add_argument("--safety-max-net-loss-mode", choices=["Cash amount", "% of entry value"], default=None)
    run.add_argument("--safety-max-net-loss-cash", type=float, default=None)
    run.add_argument("--safety-max-net-loss-percent", type=float, default=None)
    run.add_argument("--safety-max-bars-in-trade", type=int, default=None)
    run.add_argument("--whole-shares", action="store_true", help="Disable fractional share sizing")
    run.add_argument("--quantity-precision", type=int, default=6)
    run.add_argument("--early-stop-drawdown-pct", type=float, default=None, help="Early stop backtest if drawdown exceeds this percentage (0-100)")
    run.set_defaults(func=cmd_run)

    optimize = sub.add_parser("optimize", help="Run a local grid optimizer on canonical datasets")
    optimize.add_argument("--symbol", required=True)
    optimize.add_argument("--strategy", choices=["hma_crossover", "adaptive_volatility_trend", "range_filter", "3commas_bot", "pmax_explorer", "bjorgum_double_tap", "noise_boundary_intraday"], default="hma_crossover")
    optimize.add_argument("--processed-dir", default="storage/processed", help="Canonical dataset root")
    optimize.add_argument("--timeframe", type=int, default=5, help="Optimization timeframe in minutes; must be a multiple of 5")
    optimize.add_argument("--start-date", default=None, help="Inclusive optimization data window start, e.g. 2024-01-01")
    optimize.add_argument("--end-date", default=None, help="Inclusive optimization data window end, e.g. 2025-01-01")
    optimize.add_argument(
        "--param",
        action="append",
        required=True,
        help="Optimization parameter, e.g. fast_len=5:30:5 or trade_direction_mode=Long only|Long & Short",
    )
    optimize.add_argument("--dry-run", action="store_true", help="Only validate and print the iteration count")
    optimize.add_argument("--output-dir", default=str(get_reports_dir() / "local_optimizer"))
    optimize.add_argument("--config", default=None, help="Fichier JSON de configuration stratégie/backtest pour les overrides fixes")
    optimize.add_argument("--initial-capital", type=float, default=None)
    optimize.add_argument("--max-rows", type=int, default=None)
    optimize.add_argument("--score", choices=allowed_score_metrics(), default="sharpe_ratio", help="Metric used to rank configurations")
    optimize.add_argument("--score-direction", choices=["max", "min"], default="max")
    optimize.add_argument("--secondary-score", choices=allowed_score_metrics(), default=None, help="Secondary metric for multi-objective optimization (Pareto Front)")
    optimize.add_argument("--secondary-score-direction", choices=["max", "min"], default="max")
    optimize.add_argument("--wfo-windows", type=int, default=1, help="Number of rolling windows for Walk-Forward Optimization (Bayesian only)")
    optimize.add_argument(
        "--max-iterations",
        type=int,
        default=10000,
        help="Backward-compatible default limit applied to raw and canonical grids unless a specific limit is provided",
    )
    optimize.add_argument(
        "--max-raw-iterations",
        type=int,
        default=None,
        help="Maximum number of raw grid combinations before inactive-parameter deduplication",
    )
    optimize.add_argument(
        "--max-canonical-iterations",
        type=int,
        default=None,
        help="Maximum number of effective canonical combinations after inactive-parameter deduplication",
    )
    optimize.add_argument("--workers", type=int, default=1, help="Number of local worker processes for optimization")
    optimize.add_argument(
        "--min-closed-trades",
        type=int,
        default=1,
        help="Minimum closed trades required for a combination to be eligible for best ranking (default: 1)",
    )
    optimize.add_argument("--no-best-run", action="store_true", help="Do not write full backtest outputs when a new best is found")
    optimize.add_argument(
        "--optimization-mode",
        choices=["grid", "bayesian"],
        default="grid",
        dest="optimization_mode",
        help="'grid' for exhaustive grid search (default), 'bayesian' for Optuna TPE smart search",
    )
    optimize.add_argument("--fast-len", type=int, default=None, help="Fixed value unless optimized by --param")
    optimize.add_argument("--slow-len", type=int, default=None, help="Fixed value unless optimized by --param")
    optimize.add_argument("--lookback-days", type=int, default=None)
    optimize.add_argument("--volatility-multiplier-enter", type=float, default=None)
    optimize.add_argument("--volatility-multiplier-exit", type=float, default=None)
    optimize.add_argument("--target-daily-volatility", type=float, default=None)
    optimize.add_argument("--start-trade-after-open-minutes", type=int, default=None)
    optimize.add_argument("--trade-frequency-minutes", type=int, default=None)
    optimize.add_argument("--exit-trades-before-close-minutes", type=int, default=None)
    optimize.add_argument("--max-entry-price", type=float, default=None)
    optimize.add_argument("--max-capital-bucket", type=float, default=None)
    optimize.add_argument("--initial-capital-bucket", type=float, default=None)
    optimize.add_argument(
        "--trade-direction-mode",
        choices=["Long & Short", "Long only", "Short only"],
        default=None,
    )
    optimize.add_argument("--fee-mode", choices=["Parametric: hold until net covers fees", "Parametric: exit only, no forced reversal", "Disabled: always reverse/close on opposite signal"], default=None)
    optimize.add_argument("--estimated-commission-per-order-long", type=float, default=None)
    optimize.add_argument("--estimated-commission-per-order-short", type=float, default=None)
    optimize.add_argument("--estimated-slippage-per-side-long", type=float, default=None)
    optimize.add_argument("--estimated-slippage-per-side-short", type=float, default=None)
    optimize.add_argument("--min-net-profit-after-costs", type=float, default=None)
    optimize.add_argument("--take-profit-net-percent", type=float, default=None)
    optimize.add_argument("--stop-loss-net-percent", type=float, default=None)
    optimize.add_argument("--safety-stop-applies-to", choices=["Both", "Long only", "Short only"], default=None)
    optimize.add_argument("--safety-stop-mode", choices=["Net loss only", "Max bars only", "Net loss OR max bars", "Net loss AND max bars"], default=None)
    optimize.add_argument("--safety-max-net-loss-mode", choices=["Cash amount", "% of entry value"], default=None)
    optimize.add_argument("--safety-max-net-loss-cash", type=float, default=None)
    optimize.add_argument("--safety-max-net-loss-percent", type=float, default=None)
    optimize.add_argument("--safety-max-bars-in-trade", type=int, default=None)
    optimize.add_argument("--whole-shares", action="store_true", help="Disable fractional share sizing")
    optimize.add_argument("--quantity-precision", type=int, default=6)
    optimize.add_argument("--early-stop-drawdown-pct", type=float, default=None, help="Early stop iteration if drawdown exceeds this percentage (0-100)")
    optimize.add_argument("--enable-convergence-stop", action="store_true", default=True, help="Enable early stopping on convergence (Bayesian mode)")
    optimize.add_argument("--convergence-patience", type=int, default=100, help="Stop if no improvement for N consecutive iterations (Bayesian mode)")
    optimize.add_argument("--convergence-min-improvement", type=float, default=0.01, help="Minimum relative improvement to consider significant (Bayesian mode)")
    optimize.add_argument("--convergence-window-size", type=int, default=50, help="Size of each convergence window (Bayesian mode)")
    optimize.add_argument("--convergence-window-count", type=int, default=3, help="Stop after N consecutive windows without improvement (Bayesian mode)")
    optimize.add_argument("--circuit-breaker-ratio", type=float, default=0.2, help="Ratio of n_trials without improvement to trigger circuit breaker (Bayesian mode)")
    optimize.set_defaults(func=cmd_optimize)

    serve = sub.add_parser("serve", help="Serve the local optimizer web UI")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)
    serve.add_argument("--processed-dir", default="storage/processed")
    serve.add_argument("--output-dir", default=str(get_reports_dir() / "local_optimizer"))
    serve.set_defaults(func=cmd_serve)

    worker = sub.add_parser("worker", help="Run a persistent optimizer worker consuming the SQLite job queue")
    worker.add_argument("--repo-root", default=str(_repo_root()), help="Repository root path; accepted here for convenience after the subcommand")
    worker.add_argument("--processed-dir", default="storage/processed")
    worker.add_argument("--output-dir", default=str(get_reports_dir() / "local_optimizer"))
    worker.add_argument("--poll-interval", type=float, default=1.0, help="Seconds to wait between queue polls when idle")
    worker.add_argument("--once", action="store_true", help="Process at most one queued job then exit")
    worker.add_argument("--worker-id", default=None, help="Optional stable worker identifier stored with claimed jobs")
    worker.set_defaults(func=cmd_worker)

    mark_crashed = sub.add_parser("mark-crashed", help="Mark all IN_PROGRESS jobs for a given worker as FAILED after a crash")
    mark_crashed.add_argument("--worker-id", required=True, help="ID of the worker that crashed")
    mark_crashed.add_argument("--exit-code", type=int, default=1, help="Exit code of the crashed worker")
    mark_crashed.add_argument("--output-dir", default=str(get_reports_dir() / "local_optimizer"))
    mark_crashed.set_defaults(func=cmd_mark_crashed)


    interpret = sub.add_parser("interpret-optimization", help="Generate sweet-spot recommendations for a completed optimizer job")
    interpret.add_argument("--job-dir", required=True, help="Optimizer output directory containing results.json and optimization_config.json")
    interpret.add_argument("--top-quantile", type=float, default=None, help="Score quantile used to define high-performing candidates")
    interpret.add_argument("--score-tolerance-pct", type=float, default=None, help="Relative score tolerance from the best score for candidate selection")
    interpret.set_defaults(func=cmd_interpret_optimization)

    build = sub.add_parser("build-canonical", help="Rebuild clean canonical datasets from raw SheetsFinance exports")
    build.add_argument("--output-dir", default="storage/processed")
    build.add_argument("--symbols", default=None, help="Comma-separated market symbols; default: all")
    build.add_argument("--fx-pairs", default=None, help="Comma-separated FX pairs; default: all")
    build.add_argument("--no-market", action="store_true")
    build.add_argument("--no-fx", action="store_true")
    build.add_argument("--no-splits", action="store_true")
    build.add_argument("--price-repair", choices=["none", "auto"], default="auto")
    build.add_argument(
        "--market-divisor",
        default="auto",
        help="Global market price divisor, or 'auto'. Use overrides for per-symbol control.",
    )
    build.add_argument(
        "--divisor-overrides",
        default=None,
        help="Comma-separated per-symbol overrides, e.g. GMAB=10,LOGI=100",
    )
    build.add_argument(
        "--divisor-overrides-file",
        default=None,
        help="Path to a JSON file containing {symbol: divisor} overrides",
    )
    build.add_argument("--format", choices=["csv", "parquet"], default="csv")
    build.add_argument("--max-files", type=int, default=None)
    build.add_argument("--max-rows", type=int, default=None)
    build.add_argument("--quiet", action="store_true", help="Do not print per-symbol progress to stderr")
    build.set_defaults(func=cmd_build_canonical)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
