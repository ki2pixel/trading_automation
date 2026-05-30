from __future__ import annotations

from dataclasses import asdict, dataclass


def clear_range_filter_feature_cache() -> None:
    """No-op: Range Filter does not use a feature cache."""
    pass

import importlib.util
import json
from pathlib import Path
import sys
import threading
from types import ModuleType
from typing import Any, Callable

import numpy as np
import pandas as pd

from ..metrics import MetricsInput, compute_metrics
from ..reports import BacktestRunResult
from ..configuration import coerce_strategy_parameters, load_strategy_config


STRATEGY_FILE = (
    Path(__file__).resolve().parents[2]
    / "pine_scripts_convert_to_python"
    / "strategy"
    / "Range-Filter-Buy-and-Sell-5min-V3-Capped-Bucket-by-PHVNTOM_TRADER.py"
)
_RF_MODULE_NAME = "converted_range_filter"
_RF_MODULE: ModuleType | None = None
_RF_MODULE_LOCK = threading.Lock()


@dataclass
class RangeFilterConfigOverrides:
    source_col: str | None = None
    sampling_period: int | None = None
    range_multiplier: float | None = None
    max_entry_price: float | None = None
    max_capital_bucket: float | None = None
    initial_capital_bucket: float | None = None
    trade_direction_mode: str | None = None
    fee_mode: str | None = None
    estimated_commission_per_order_long: float | None = None
    estimated_commission_per_order_short: float | None = None
    estimated_slippage_per_side_long: float | None = None
    estimated_slippage_per_side_short: float | None = None
    min_net_profit_after_costs: float | None = None
    use_net_bracket_exits: bool | None = None
    take_profit_net_percent: float | None = None
    stop_loss_net_percent: float | None = None
    use_safety_stop: bool | None = None
    safety_stop_applies_to: str | None = None
    safety_stop_mode: str | None = None
    safety_max_net_loss_mode: str | None = None
    safety_max_net_loss_cash: float | None = None
    safety_max_net_loss_percent: float | None = None
    safety_max_bars_in_trade: int | None = None
    point_value: float | None = None
    fill_model: str | None = None
    apply_estimated_costs_to_realized_pnl: bool | None = None
    allow_fractional_quantity: bool | None = True
    quantity_precision: int | None = 6
    early_stop_drawdown_pct: float | None = None
    asset_currency: str | None = None
    account_currency: str | None = None
    fx_rate_provider: object | None = None


def rf_overrides_from_mapping(values: dict[str, object] | None, *, ignore_unknown: bool = True) -> RangeFilterConfigOverrides:
    if not values:
        return RangeFilterConfigOverrides()
    coerced = coerce_strategy_parameters("range_filter", values, ignore_unknown=ignore_unknown)
    allowed = set(RangeFilterConfigOverrides.__dataclass_fields__.keys())
    return RangeFilterConfigOverrides(**{key: value for key, value in coerced.items() if key in allowed})


def load_rf_overrides_from_config(path: str | Path) -> tuple[RangeFilterConfigOverrides, dict[str, object]]:
    runtime_config = load_strategy_config(path, strategy="range_filter")
    return rf_overrides_from_mapping(runtime_config.parameters), runtime_config.backtest


def _load_strategy_module() -> ModuleType:
    global _RF_MODULE

    if _RF_MODULE is not None:
        return _RF_MODULE

    with _RF_MODULE_LOCK:
        if _RF_MODULE is not None:
            return _RF_MODULE

        spec = importlib.util.spec_from_file_location(_RF_MODULE_NAME, STRATEGY_FILE)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load strategy module: {STRATEGY_FILE}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(spec.name, None)
            raise
        _RF_MODULE = module
        return _RF_MODULE


def _to_strategy_ohlcv(data: pd.DataFrame) -> pd.DataFrame:
    out = data.copy()
    for col in ["open", "high", "low", "close", "volume"]:
        if col not in out.columns:
            raise ValueError(f"Missing required column: {col}")
    return out[["open", "high", "low", "close", "volume"]].copy()


def _apply_overrides(config: Any, overrides: RangeFilterConfigOverrides) -> Any:
    for key, value in asdict(overrides).items():
        if value is not None and hasattr(config, key):
            setattr(config, key, value)
    return config


def _normalize_trades(trades: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    """Adapt broker.closed_trades_frame() to the format expected by compute_metrics."""
    if trades.empty:
        return pd.DataFrame(columns=[
            "entry_index", "exit_index", "side", "qty", "entry_price",
            "exit_price", "gross_pnl", "estimated_costs", "net_pnl", "bars_held", "exit_comment",
        ])

    out = trades.copy()
    out = out.rename(columns={
        "entry_time": "entry_index",
        "exit_time": "exit_index",
        "quantity": "qty",
        "commission": "estimated_costs",
    })

    # Compute bars_held from index positions
    bar_positions = pd.Series(np.arange(len(bars), dtype=np.int64), index=bars.index)
    entry_pos = out["entry_index"].map(bar_positions)
    exit_pos = out["exit_index"].map(bar_positions)
    out["bars_held"] = (exit_pos - entry_pos).astype(float)

    # Ensure all expected columns exist
    for col in ["entry_index", "exit_index", "side", "qty", "entry_price",
                 "exit_price", "gross_pnl", "estimated_costs", "net_pnl", "bars_held", "exit_comment"]:
        if col not in out.columns:
            out[col] = np.nan

    return out[[
        "entry_index", "exit_index", "side", "qty", "entry_price",
        "exit_price", "gross_pnl", "estimated_costs", "net_pnl", "bars_held", "exit_comment",
    ]]


def run_range_filter(
    data: pd.DataFrame,
    symbol: str,
    overrides: RangeFilterConfigOverrides | None = None,
    initial_capital: float = 1000.0,
    timeframe_minutes: int | str = 5,
    compute_full_metrics: bool = True,
    fast_score_metric: str | None = None,
    repo_root: Path | None = None,
) -> BacktestRunResult:
    from ._currency_utils import setup_currency_and_fx_provider

    overrides = overrides or RangeFilterConfigOverrides()
    account_currency, asset_currency, fx_rate_provider = setup_currency_and_fx_provider(
        symbol=symbol,
        timeframe_minutes=timeframe_minutes,
        repo_root=repo_root,
        overrides=overrides,
    )
    overrides.account_currency = account_currency
    overrides.asset_currency = asset_currency
    overrides.fx_rate_provider = fx_rate_provider

    module = _load_strategy_module()
    config = module.RangeFilterConfig()
    config = _apply_overrides(config, overrides)

    bars = _to_strategy_ohlcv(data)
    state, raw_trades = module.run_range_filter_strategy(
        bars, 
        config,
        early_stop_drawdown_pct=overrides.early_stop_drawdown_pct,
        compute_full_metrics=compute_full_metrics,
    )

    trades = _normalize_trades(raw_trades, bars)

    if compute_full_metrics:
        metrics, equity_curve = compute_metrics(
            MetricsInput(
                symbol=symbol,
                strategy="range_filter",
                initial_capital=initial_capital,
                bars=bars,
                state=state,
                trades=trades,
                timeframe_minutes=timeframe_minutes,
            )
        )
    else:
        from ..metrics import compute_fast_score
        metrics = {"closed_trades": len(trades)}
        if fast_score_metric:
            score = compute_fast_score(
                trades, 
                fast_score_metric, 
                state=state, 
                initial_capital=initial_capital, 
                timeframe_minutes=timeframe_minutes,
                bars=bars,
            )
            if score is not None:
                metrics[fast_score_metric] = score
        equity_curve = pd.DataFrame()

    return BacktestRunResult(
        strategy="range_filter",
        symbol=symbol,
        config=asdict(config),
        bars=bars,
        state=state,
        trades=trades,
        equity_curve=equity_curve,
        metrics=metrics,
    )


def _write_prescan_report(
    output_dir: Path | None,
    status: str,
    top_n: int | None,
    parameters: dict[str, dict[str, Any]],
) -> None:
    if output_dir is None:
        return
    report = {
        "status": status,
        "top_n_configurations_found": top_n,
        "parameters": parameters,
    }
    try:
        path = output_dir / "vectorbt_prescan_report.json"
        path.write_text(json.dumps(report, indent=4, default=str), encoding="utf-8")
    except Exception:
        pass


# Globals for multiprocessing workers to reference mapped memory directly
_worker_data = None
_worker_strategy_file = None
_worker_timeframe_minutes = None
_worker_module = None

def _init_prescan_worker(data, strategy_file, timeframe_mins):
    global _worker_data, _worker_strategy_file, _worker_timeframe_minutes, _worker_module
    _worker_data = data
    _worker_strategy_file = strategy_file
    _worker_timeframe_minutes = timeframe_mins

    import importlib.util
    import sys
    spec = importlib.util.spec_from_file_location("strategy_module_rf", strategy_file)
    module = importlib.util.module_from_spec(spec)
    sys.modules["strategy_module_rf"] = module
    spec.loader.exec_module(module)
    _worker_module = module

def _process_prescan_batch(batch_combos):
    global _worker_data, _worker_timeframe_minutes, _worker_module
    import pandas as pd
    import vectorbt as vbt

    batch_entries = {}
    batch_exits = {}

    for period, mult in batch_combos:
        cfg = _worker_module.RangeFilterConfig()
        cfg.sampling_period = period
        cfg.range_multiplier = mult

        out = _worker_module.add_range_filter_columns(_worker_data, cfg)
        col = (period, mult)
        batch_entries[col] = out["long_signal"]
        batch_exits[col] = out["short_signal"]

    entries_df = pd.DataFrame(batch_entries, index=_worker_data.index)
    exits_df = pd.DataFrame(batch_exits, index=_worker_data.index)

    pf = vbt.Portfolio.from_signals(
        _worker_data["close"],
        entries=entries_df,
        exits=exits_df,
        freq=f"{_worker_timeframe_minutes}min",
    )
    return pf.total_return()


def vectorbt_prescan(
    data: pd.DataFrame,
    parameter_specs: list[Any],
    timeframe_minutes: int | str,
    output_dir: Path | None = None,
    stop_requested: Callable[[], bool] | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
    workers: int = 1,
) -> list[Any]:
    """Pre-scan rapide VectorBT pour Range Filter.

    Scanne les combinaisons (sampling_period, range_multiplier)
    afin de restreindre les bornes d'exploration avant l'optimisation bayesienne.
    """
    import logging
    import numpy as np
    from ..optimizer import ParameterGridSpec

    logger = logging.getLogger(__name__)

    if stop_requested is not None and stop_requested():
        logger.warning("Pre-scan Range Filter annule avant demarrage.")
        _write_prescan_report(output_dir, "cancelled", None, {})
        return parameter_specs

    period_specs = next((s for s in parameter_specs if s.name == "sampling_period"), None)
    mult_specs = next((s for s in parameter_specs if s.name == "range_multiplier"), None)

    if not period_specs or not mult_specs:
        _write_prescan_report(output_dir, "skipped", None, {})
        return parameter_specs
    if not period_specs.values or not mult_specs.values:
        _write_prescan_report(output_dir, "skipped", None, {})
        return parameter_specs

    try:
        import vectorbt as vbt
        import gc

        # 1. Temporal Downsampling & Slicing (Piste C)
        prescan_timeframe = timeframe_minutes
        if int(timeframe_minutes) == 1:
            logger.info("Downsampling 1min bars to 5min bars for fast pre-scan processing.")
            conversion = {
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }
            for col in data.columns:
                if col not in conversion:
                    conversion[col] = 'first'
            data = data.resample("5Min").agg(conversion).dropna()
            prescan_timeframe = 5

        if len(data) > 150000:
            logger.info(f"Slicing data from {len(data)} to 150000 bars for fast pre-scan processing.")
            data = data.iloc[-150000:]

        module = _load_strategy_module()

        periods = sorted({int(v) for v in period_specs.values})
        mults = sorted({float(v) for v in mult_specs.values})

        from ..prescan_utils import downsample_parameter_grid
        downsampled = downsample_parameter_grid(
            {"periods": periods, "mults": mults},
            max_combos=20000,
            strategy_name="Range Filter"
        )
        periods = downsampled["periods"]
        mults = downsampled["mults"]

        combos = [(period, mult) for period in periods for mult in mults]

        # 2. Dynamic Batch Size (Piste B)
        if workers > 1:
            BATCH_SIZE = 50
        else:
            BATCH_SIZE = 50

        total_batches = (len(combos) + BATCH_SIZE - 1) // BATCH_SIZE if combos else 0
        returns_batches: list[pd.Series] = []

        # 3. Multiprocessing Parallelization (Piste A)
        if workers > 1:
            logger.info(f"Lancement du Pre-Scan VectorBT en parallèle avec {workers} processus (Batch Size={BATCH_SIZE})...")
            import multiprocessing
            import concurrent.futures
            try:
                ctx = multiprocessing.get_context("fork")
            except ValueError:
                ctx = multiprocessing.get_context()

            batches = []
            for batch_idx in range(total_batches):
                start_i = batch_idx * BATCH_SIZE
                end_i = min(start_i + BATCH_SIZE, len(combos))
                batches.append(combos[start_i:end_i])

            with concurrent.futures.ProcessPoolExecutor(
                max_workers=workers,
                mp_context=ctx,
                initializer=_init_prescan_worker,
                initargs=(data, STRATEGY_FILE, prescan_timeframe)
            ) as executor:
                completed = 0
                futures = {executor.submit(_process_prescan_batch, b): b for b in batches}

                while futures:
                    if stop_requested is not None and stop_requested():
                        logger.warning("Pre-scan Range Filter annulé pendant le calcul parallèle.")
                        for f in futures:
                            f.cancel()
                        executor.shutdown(wait=False)
                        _write_prescan_report(output_dir, "cancelled", None, {})
                        return parameter_specs

                    done, _ = concurrent.futures.wait(
                        futures.keys(),
                        timeout=1.0,
                        return_when=concurrent.futures.FIRST_COMPLETED
                    )

                    for future in done:
                        try:
                            res = future.result()
                            returns_batches.append(res)
                        except Exception as e:
                            logger.error(f"Le process worker a crashé ou échoué: {e}")
                            for f in futures:
                                f.cancel()
                            executor.shutdown(wait=False)
                            raise RuntimeError(f"Pre-scan VectorBT échoué: {e}") from e

                        del futures[future]
                        completed += 1
                        if progress_callback is not None:
                            try:
                                progress_callback(completed, total_batches)
                            except Exception as cb_err:
                                logger.warning(f"Error in prescan progress callback: {cb_err}")
        else:
            logger.info(f"Lancement du Pre-Scan VectorBT en séquentiel (Batch Size={BATCH_SIZE})...")
            for batch_idx in range(total_batches):
                if stop_requested is not None and stop_requested():
                    logger.warning("Pre-scan Range Filter annule pendant le calcul des signaux.")
                    _write_prescan_report(output_dir, "cancelled", None, {})
                    return parameter_specs

                start_i = batch_idx * BATCH_SIZE
                end_i = min(start_i + BATCH_SIZE, len(combos))
                batch_combos = combos[start_i:end_i]

                batch_entries = {}
                batch_exits = {}

                for period, mult in batch_combos:
                    cfg = module.RangeFilterConfig()
                    cfg.sampling_period = period
                    cfg.range_multiplier = mult

                    out = module.add_range_filter_columns(data, cfg)
                    col = (period, mult)
                    batch_entries[col] = out["long_signal"]
                    batch_exits[col] = out["short_signal"]

                entries_df = pd.DataFrame(batch_entries, index=data.index)
                exits_df = pd.DataFrame(batch_exits, index=data.index)

                pf = vbt.Portfolio.from_signals(
                    data["close"],
                    entries=entries_df,
                    exits=exits_df,
                    freq=f"{prescan_timeframe}min",
                )
                returns_batches.append(pf.total_return())

                # Free RAM
                del entries_df
                del exits_df
                del pf
                del batch_entries
                del batch_exits
                gc.collect()

                if progress_callback is not None:
                    try:
                        progress_callback(batch_idx + 1, total_batches)
                    except Exception as cb_err:
                        logger.warning(f"Error in prescan progress callback: {cb_err}")

        if returns_batches:
            returns = pd.concat(returns_batches)
            returns = returns.sort_index()
        else:
            returns = pd.Series(dtype=float)

        # Recupere le Top 5% des combinaisons
        top_n = max(1, int(len(returns) * 0.05))
        top_params = returns.nlargest(top_n).index.tolist()

        if not top_params:
            _write_prescan_report(output_dir, "no_candidates", top_n, {})
            return parameter_specs

        min_period, max_period = min(p[0] for p in top_params), max(p[0] for p in top_params)
        min_mult, max_mult = min(p[1] for p in top_params), max(p[1] for p in top_params)

        # Marge de securite (+/- 10%)
        margin_period = max(1, int((max_period - min_period) * 0.1))
        margin_mult = max(0.1, (max_mult - min_mult) * 0.1)

        min_period = max(int(period_specs.values[0]), min_period - margin_period)
        max_period = min(int(period_specs.values[-1]), max_period + margin_period)
        min_mult = max(float(mult_specs.values[0]), min_mult - margin_mult)
        max_mult = min(float(mult_specs.values[-1]), max_mult + margin_mult)

        # Reconstruire ParameterGridSpec avec les nouvelles bornes
        new_specs = []
        period_filtered: tuple = ()
        mult_filtered: tuple = ()
        for s in parameter_specs:
            if s.name == "sampling_period":
                new_vals = tuple(v for v in s.values if min_period <= int(v) <= max_period)
                period_filtered = new_vals or s.values
                new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=period_filtered))
            elif s.name == "range_multiplier":
                new_vals = tuple(v for v in s.values if min_mult <= float(v) <= max_mult)
                mult_filtered = new_vals or s.values
                new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=mult_filtered))
            else:
                new_specs.append(s)

        _write_prescan_report(
            output_dir,
            "success",
            top_n,
            {
                "sampling_period": {
                    "original_bounds": [int(period_specs.values[0]), int(period_specs.values[-1])],
                    "new_bounds": [int(period_filtered[0]), int(period_filtered[-1])],
                    "filtered_values": list(period_filtered),
                },
                "range_multiplier": {
                    "original_bounds": [float(mult_specs.values[0]), float(mult_specs.values[-1])],
                    "new_bounds": [float(mult_filtered[0]), float(mult_filtered[-1])],
                    "filtered_values": list(mult_filtered),
                },
            },
        )
        logger.info(
            f"Bornes Optuna reduites via VectorBT: "
            f"sampling_period({min_period}-{max_period}), range_multiplier({min_mult:.1f}-{max_mult:.1f})"
        )
        return new_specs

    except ImportError:
        _write_prescan_report(output_dir, "skipped", None, {})
        logger.warning("VectorBT n'est pas installe, impossible de lancer le pre-scan.")
    except Exception as e:
        _write_prescan_report(output_dir, "error", None, {})
        logger.warning(f"Erreur Pre-Scan VectorBT: {e}. Optuna utilisera les bornes globales.")

    _write_prescan_report(output_dir, "skipped", None, {})
    return parameter_specs
