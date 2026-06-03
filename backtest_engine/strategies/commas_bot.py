from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib.util
import json
from pathlib import Path
import sys
import threading
from types import ModuleType
from typing import Any, Callable

import pandas as pd

from ..metrics import MetricsInput, compute_metrics
from ..reports import BacktestRunResult
from ..configuration import coerce_strategy_parameters, load_strategy_config


STRATEGY_FILE = (
    Path(__file__).resolve().parents[2]
    / "pine_scripts_convert_to_python"
    / "strategy"
    / "3Commas-Bot.py"
)
_MODULE_NAME = "converted_3commas_bot"
_MODULE: ModuleType | None = None
_MODULE_LOCK = threading.Lock()


@dataclass
class CommasBotConfigOverrides:
    # ---- Trade variables ----
    long_trades: bool | None = None
    short_trades: bool | None = None
    use_limit: bool | None = None
    trail_stop: bool | None = None
    flip: bool | None = None
    set_max_drawdown: bool | None = None

    # ---- Risk Management ----
    rnr: float | None = None
    risk_m: float | None = None
    swing_lookback: int | None = None
    max_perc_dd: float | None = None
    atr_len: int | None = None

    # ---- Trailing Stop ----
    trail_stop_size: float | None = None
    rr_exit: float | None = None

    # ---- MA Type ----
    ma_type1: str | None = None
    ma_type2: str | None = None

    # ---- MA Settings ----
    ma_length1: int | None = None
    ma_length2: int | None = None

    # ---- Filters ----
    use_time_filter: bool | None = None
    time_session: str | None = None

    # ---- Capped Bucket ----
    initial_capital_bucket: float | None = None
    max_capital_bucket: float | None = None
    max_entry_price: float | None = None

    # ---- Trade direction ----
    trade_direction_mode: str | None = None

    # ---- Fee / reversal filter ----
    fee_mode: str | None = None
    estimated_commission_per_order_long: float | None = None
    estimated_commission_per_order_short: float | None = None
    estimated_slippage_per_side_long: float | None = None
    estimated_slippage_per_side_short: float | None = None
    min_net_profit_after_costs: float | None = None

    # ---- Explicit net exits ----
    use_net_bracket_exits: bool | None = None
    take_profit_net_percent: float | None = None
    stop_loss_net_percent: float | None = None

    # ---- Safety stop ----
    use_safety_stop: bool | None = None
    safety_stop_applies_to: str | None = None
    safety_stop_mode: str | None = None
    safety_max_net_loss_mode: str | None = None
    safety_max_net_loss_cash: float | None = None
    safety_max_net_loss_percent: float | None = None
    safety_max_bars_in_trade: int | None = None

    # ---- Execution ----
    point_value: float | None = None
    execute_on_next_bar: bool | None = None
    next_bar_execution_price_col: str | None = None
    allow_fractional_quantity: bool | None = True
    quantity_precision: int | None = 6
    apply_estimated_costs_to_realized_pnl: bool | None = None
    early_stop_drawdown_pct: float | None = None
    asset_currency: str | None = None
    account_currency: str | None = None
    fx_rate_provider: object | None = None


def commas_bot_overrides_from_mapping(values: dict[str, object] | None, *, ignore_unknown: bool = True) -> CommasBotConfigOverrides:
    if not values:
        return CommasBotConfigOverrides()
    coerced = coerce_strategy_parameters("3commas_bot", values, ignore_unknown=ignore_unknown)
    allowed = set(CommasBotConfigOverrides.__dataclass_fields__.keys())
    return CommasBotConfigOverrides(**{key: value for key, value in coerced.items() if key in allowed})


def load_commas_bot_overrides_from_config(path: str | Path) -> tuple[CommasBotConfigOverrides, dict[str, object]]:
    runtime_config = load_strategy_config(path, strategy="3commas_bot")
    return commas_bot_overrides_from_mapping(runtime_config.parameters), runtime_config.backtest


def _load_strategy_module() -> ModuleType:
    global _MODULE

    if _MODULE is not None:
        return _MODULE

    with _MODULE_LOCK:
        if _MODULE is not None:
            return _MODULE

        spec = importlib.util.spec_from_file_location(_MODULE_NAME, STRATEGY_FILE)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load strategy module: {STRATEGY_FILE}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(spec.name, None)
            raise
        _MODULE = module
        return _MODULE


def _to_strategy_ohlcv(data: pd.DataFrame) -> pd.DataFrame:
    out = data.copy()
    required = ["open", "high", "low", "close"]
    for col in required:
        if col not in out.columns:
            raise ValueError(f"Missing required column: {col}")
    if "volume" not in out.columns:
        out["volume"] = 1.0
    return out[["open", "high", "low", "close", "volume"]].copy()


def _apply_overrides(config: Any, overrides: CommasBotConfigOverrides) -> Any:
    for key, value in asdict(overrides).items():
        if value is not None and hasattr(config, key):
            setattr(config, key, value)
    return config


def run_3commas_bot(
    data: pd.DataFrame,
    symbol: str,
    overrides: CommasBotConfigOverrides | None = None,
    initial_capital: float = 1000.0,
    timeframe_minutes: int | str = 5,
    compute_full_metrics: bool = True,
    fast_score_metric: str | None = None,
    repo_root: Path | None = None,
) -> BacktestRunResult:
    from ._currency_utils import setup_currency_and_fx_provider

    overrides = overrides or CommasBotConfigOverrides()
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
    config = module.CommasBotConfig()
    config = _apply_overrides(config, overrides)

    bars = _to_strategy_ohlcv(data)
    state, trades = module.run_3commas_bot_strategy(
        bars, 
        config,
        compute_full_metrics=compute_full_metrics,
    )

    if compute_full_metrics:
        metrics, equity_curve = compute_metrics(
            MetricsInput(
                symbol=symbol,
                strategy="3commas_bot",
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
        strategy="3commas_bot",
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
_worker_close = None
_worker_ma_df = None
_worker_timeframe_minutes = None

def _init_prescan_worker(close, ma_df, timeframe_mins):
    global _worker_close, _worker_ma_df, _worker_timeframe_minutes
    _worker_close = close
    _worker_ma_df = ma_df
    _worker_timeframe_minutes = timeframe_mins

def _process_prescan_batch(batch_combos):
    global _worker_close, _worker_ma_df, _worker_timeframe_minutes
    import pandas as pd
    import vectorbt as vbt

    batch_entries = {}
    batch_exits = {}
    batch_short_entries = {}
    batch_short_exits = {}

    for l1, l2 in batch_combos:
        ma1 = _worker_ma_df[l1]
        ma1_prev = ma1.shift(1)
        ma2 = _worker_ma_df[l2]
        ma2_prev = ma2.shift(1)

        col = (l1, l2)
        # Crossover(ma1, ma2) -> entree long, sortie short
        batch_entries[col] = (ma1 > ma2) & (ma1_prev <= ma2_prev)
        # Crossunder(ma1, ma2) -> sortie long, entree short
        crossunder = (ma1 < ma2) & (ma1_prev >= ma2_prev)
        batch_exits[col] = crossunder
        batch_short_entries[col] = crossunder
        batch_short_exits[col] = batch_entries[col]

    entries_df = pd.DataFrame(batch_entries, index=_worker_close.index)
    exits_df = pd.DataFrame(batch_exits, index=_worker_close.index)
    short_entries_df = pd.DataFrame(batch_short_entries, index=_worker_close.index)
    short_exits_df = pd.DataFrame(batch_short_exits, index=_worker_close.index)

    pf = vbt.Portfolio.from_signals(
        _worker_close,
        entries=entries_df,
        exits=exits_df,
        short_entries=short_entries_df,
        short_exits=short_exits_df,
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
    """Pre-scan rapide VectorBT pour 3Commas-Bot.

    Scanne les combinaisons de longueurs de moyennes mobiles
    (ma_length1, ma_length2) pour restreindre les bornes d'exploration
    avant l'optimisation bayesienne.
    """
    import logging
    from ..optimizer import ParameterGridSpec

    logger = logging.getLogger(__name__)

    if stop_requested is not None and stop_requested():
        logger.warning("Pre-scan 3Commas annule avant demarrage.")
        _write_prescan_report(output_dir, "cancelled", None, {})
        return parameter_specs

    length1_specs = next((s for s in parameter_specs if s.name == "ma_length1"), None)
    length2_specs = next((s for s in parameter_specs if s.name == "ma_length2"), None)

    if not length1_specs or not length2_specs or not length1_specs.values or not length2_specs.values:
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

        length1_values = sorted({int(v) for v in length1_specs.values})
        length2_values = sorted({int(v) for v in length2_specs.values})

        from ..prescan_utils import downsample_parameter_grid
        downsampled = downsample_parameter_grid(
            {"l1": length1_values, "l2": length2_values},
            max_combos=20000,
            strategy_name="3Commas"
        )
        length1_values = downsampled["l1"]
        length2_values = downsampled["l2"]

        # Pre-calculer toutes les MAs pour eviter les recalculs
        all_values = sorted(set(length1_values + length2_values))
        all_ma = vbt.MA.run(data["close"], window=all_values)

        combos = [(l1, l2) for l1 in length1_values for l2 in length2_values]

        # 2. Dynamic Batch Size (Piste B)
        if workers > 1:
            batch_size = 50
        else:
            batch_size = 100

        total_batches = (len(combos) + batch_size - 1) // batch_size if combos else 0
        returns_batches: list[pd.Series] = []

        close = data["close"]
        ma_df = all_ma.ma

        # 3. Multiprocessing Parallelization (Piste A)
        if workers > 1:
            logger.info(f"Lancement du Pre-Scan VectorBT en parallèle avec {workers} processus (Batch Size={batch_size})...")
            import multiprocessing
            try:
                ctx = multiprocessing.get_context("fork")
            except ValueError:
                ctx = multiprocessing.get_context()

            batches = []
            for batch_idx in range(total_batches):
                start_i = batch_idx * batch_size
                end_i = min(start_i + batch_size, len(combos))
                batches.append(combos[start_i:end_i])

            import concurrent.futures
            with concurrent.futures.ProcessPoolExecutor(
                max_workers=workers,
                mp_context=ctx,
                initializer=_init_prescan_worker,
                initargs=(close, ma_df, prescan_timeframe)
            ) as executor:
                completed = 0
                futures = {executor.submit(_process_prescan_batch, b): b for b in batches}

                while futures:
                    if stop_requested is not None and stop_requested():
                        logger.warning("Pre-scan 3Commas annulé pendant le calcul parallèle.")
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
            logger.info(f"Lancement du Pre-Scan VectorBT en séquentiel (Batch Size={batch_size})...")
            for batch_idx in range(total_batches):
                if stop_requested is not None and stop_requested():
                    logger.warning("Pre-scan 3Commas annule pendant le calcul des signaux.")
                    _write_prescan_report(output_dir, "cancelled", None, {})
                    return parameter_specs

                start_i = batch_idx * batch_size
                end_i = min(start_i + batch_size, len(combos))
                batch_combos = combos[start_i:end_i]

                batch_entries = {}
                batch_exits = {}
                batch_short_entries = {}
                batch_short_exits = {}

                for l1, l2 in batch_combos:
                    ma1 = all_ma.ma[l1]
                    ma1_prev = ma1.shift(1)
                    ma2 = all_ma.ma[l2]
                    ma2_prev = ma2.shift(1)

                    col = (l1, l2)
                    # Crossover(ma1, ma2) -> entree long, sortie short
                    batch_entries[col] = (ma1 > ma2) & (ma1_prev <= ma2_prev)
                    # Crossunder(ma1, ma2) -> sortie long, entree short
                    crossunder = (ma1 < ma2) & (ma1_prev >= ma2_prev)
                    batch_exits[col] = crossunder
                    batch_short_entries[col] = crossunder
                    batch_short_exits[col] = batch_entries[col]

                entries_df = pd.DataFrame(batch_entries, index=data.index)
                exits_df = pd.DataFrame(batch_exits, index=data.index)
                short_entries_df = pd.DataFrame(batch_short_entries, index=data.index)
                short_exits_df = pd.DataFrame(batch_short_exits, index=data.index)

                pf = vbt.Portfolio.from_signals(
                    close,
                    entries=entries_df,
                    exits=exits_df,
                    short_entries=short_entries_df,
                    short_exits=short_exits_df,
                    freq=f"{prescan_timeframe}min",
                )
                returns_batches.append(pf.total_return())

                # Free RAM
                del entries_df
                del exits_df
                del short_entries_df
                del short_exits_df
                del pf
                del batch_entries
                del batch_exits
                del batch_short_entries
                del batch_short_exits
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

        min_l1, max_l1 = min(p[0] for p in top_params), max(p[0] for p in top_params)
        min_l2, max_l2 = min(p[1] for p in top_params), max(p[1] for p in top_params)

        # Marge de securite (+/- 10%)
        margin_l1 = max(1, int((max_l1 - min_l1) * 0.1))
        margin_l2 = max(1, int((max_l2 - min_l2) * 0.1))

        min_l1 = max(int(length1_specs.values[0]), min_l1 - margin_l1)
        max_l1 = min(int(length1_specs.values[-1]), max_l1 + margin_l1)
        min_l2 = max(int(length2_specs.values[0]), min_l2 - margin_l2)
        max_l2 = min(int(length2_specs.values[-1]), max_l2 + margin_l2)

        # Reconstruire ParameterGridSpec avec les nouvelles bornes
        new_specs = []
        l1_filtered: tuple = ()
        l2_filtered: tuple = ()
        for s in parameter_specs:
            if s.name == "ma_length1":
                new_vals = tuple(v for v in s.values if min_l1 <= int(v) <= max_l1)
                l1_filtered = new_vals or s.values
                new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=l1_filtered))
            elif s.name == "ma_length2":
                new_vals = tuple(v for v in s.values if min_l2 <= int(v) <= max_l2)
                l2_filtered = new_vals or s.values
                new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=l2_filtered))
            else:
                new_specs.append(s)

        _write_prescan_report(
            output_dir,
            "success",
            top_n,
            {
                "ma_length1": {
                    "original_bounds": [int(length1_specs.values[0]), int(length1_specs.values[-1])],
                    "new_bounds": [int(l1_filtered[0]), int(l1_filtered[-1])],
                    "filtered_values": list(l1_filtered),
                },
                "ma_length2": {
                    "original_bounds": [int(length2_specs.values[0]), int(length2_specs.values[-1])],
                    "new_bounds": [int(l2_filtered[0]), int(l2_filtered[-1])],
                    "filtered_values": list(l2_filtered),
                },
            },
        )
        logger.info(
            f"Bornes Optuna reduites via VectorBT: "
            f"ma_length1({min_l1}-{max_l1}), ma_length2({min_l2}-{max_l2})"
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
