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


def clear_bjorgum_double_tap_feature_cache() -> None:
    import sys as _sys
    mod = _sys.modules.get("converted_bjorgum_double_tap")
    if mod is not None and hasattr(mod, "clear_feature_cache"):
        mod.clear_feature_cache()


STRATEGY_FILE = (
    Path(__file__).resolve().parents[2]
    / "pine_scripts_convert_to_python"
    / "strategy"
    / "Bjorgum-Double-Tap.py"
)
_MODULE_NAME = "converted_bjorgum_double_tap"
_MODULE: ModuleType | None = None
_MODULE_LOCK = threading.Lock()


@dataclass
class BjorgumDoubleTapConfigOverrides:
    dLong: bool | None = None
    dShort: bool | None = None
    FLIP: bool | None = None
    tol: float | None = None
    length: int | None = None
    fib: float | None = None
    stopPer: float | None = None
    offset: int | None = None
    atrStop: bool | None = None
    atrLength: int | None = None
    atrMult: float | None = None
    lookback: int | None = None
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
    execute_on_next_bar: bool | None = None
    next_bar_execution_price_col: str | None = None
    apply_estimated_costs_to_realized_pnl: bool | None = None
    allow_fractional_quantity: bool | None = True
    quantity_precision: int | None = 6
    early_stop_drawdown_pct: float | None = None
    asset_currency: str | None = None
    account_currency: str | None = None
    fx_rate_provider: object | None = None


def bjorgum_double_tap_overrides_from_mapping(values: dict[str, object] | None, *, ignore_unknown: bool = True) -> BjorgumDoubleTapConfigOverrides:
    if not values:
        return BjorgumDoubleTapConfigOverrides()
    coerced = coerce_strategy_parameters("bjorgum_double_tap", values, ignore_unknown=ignore_unknown)
    allowed = set(BjorgumDoubleTapConfigOverrides.__dataclass_fields__.keys())
    return BjorgumDoubleTapConfigOverrides(**{key: value for key, value in coerced.items() if key in allowed})


def load_bjorgum_double_tap_overrides_from_config(path: str | Path) -> tuple[BjorgumDoubleTapConfigOverrides, dict[str, object]]:
    runtime_config = load_strategy_config(path, strategy="bjorgum_double_tap")
    return bjorgum_double_tap_overrides_from_mapping(runtime_config.parameters), runtime_config.backtest


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
    for col in ["open", "high", "low", "close"]:
        if col not in out.columns:
            raise ValueError(f"Missing required column: {col}")
    return out


def _apply_overrides(config: Any, overrides: BjorgumDoubleTapConfigOverrides) -> Any:
    for key, value in asdict(overrides).items():
        if value is not None and hasattr(config, key):
            setattr(config, key, value)
    return config


def run_bjorgum_double_tap(
    data: pd.DataFrame,
    symbol: str,
    overrides: BjorgumDoubleTapConfigOverrides | None = None,
    initial_capital: float = 1000.0,
    timeframe_minutes: int | str = 5,
    compute_full_metrics: bool = True,
    fast_score_metric: str | None = None,
    repo_root: Path | None = None,
) -> BacktestRunResult:
    from ._currency_utils import setup_currency_and_fx_provider

    overrides = overrides or BjorgumDoubleTapConfigOverrides()
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
    config = module.BjorgumDoubleTapConfig()
    config = _apply_overrides(config, overrides)

    bars = _to_strategy_ohlcv(data)
    state, trades = module.run_bjorgum_double_tap_strategy(
        bars, 
        config,
        early_stop_drawdown_pct=overrides.early_stop_drawdown_pct if overrides else None,
        compute_full_metrics=compute_full_metrics,
    )
    
    if compute_full_metrics:
        metrics, equity_curve = compute_metrics(
            MetricsInput(
                symbol=symbol,
                strategy="bjorgum_double_tap",
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
        strategy="bjorgum_double_tap",
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
_worker_rolling_high_cache = None
_worker_rolling_low_cache = None
_worker_timeframe_minutes = None

def _init_prescan_worker(close, rolling_high, rolling_low, timeframe_mins):
    global _worker_close, _worker_rolling_high_cache, _worker_rolling_low_cache, _worker_timeframe_minutes
    _worker_close = close
    _worker_rolling_high_cache = rolling_high
    _worker_rolling_low_cache = rolling_low
    _worker_timeframe_minutes = timeframe_mins

def _process_prescan_batch(batch_combos):
    global _worker_close, _worker_rolling_high_cache, _worker_rolling_low_cache, _worker_timeframe_minutes
    import pandas as pd
    import vectorbt as vbt

    batch_long_entries = {}
    batch_short_entries = {}
    batch_long_exits = {}
    batch_short_exits = {}

    close_shift_1 = _worker_close.shift(1).fillna(_worker_close.iloc[0])

    for length, tol in batch_combos:
        rolling_high = _worker_rolling_high_cache[length]
        rolling_low = _worker_rolling_low_cache[length]

        tf = tol / 100.0

        near_low = _worker_close <= rolling_low * (1 + tf)
        near_high = _worker_close >= rolling_high * (1 - tf)

        long_sig = near_low & (_worker_close > close_shift_1)
        short_sig = near_high & (_worker_close < close_shift_1)

        long_sig = long_sig & (~long_sig.shift(1).fillna(0.0).astype(bool))
        short_sig = short_sig & (~short_sig.shift(1).fillna(0.0).astype(bool))

        col = (length, tol)
        batch_long_entries[col] = long_sig
        batch_short_entries[col] = short_sig
        batch_long_exits[col] = short_sig   # sortie long quand signal short
        batch_short_exits[col] = long_sig   # sortie short quand signal long

    long_entries_df = pd.DataFrame(batch_long_entries, index=_worker_close.index)
    short_entries_df = pd.DataFrame(batch_short_entries, index=_worker_close.index)
    long_exits_df = pd.DataFrame(batch_long_exits, index=_worker_close.index)
    short_exits_df = pd.DataFrame(batch_short_exits, index=_worker_close.index)

    pf = vbt.Portfolio.from_signals(
        _worker_close,
        entries=long_entries_df,
        exits=long_exits_df,
        short_entries=short_entries_df,
        short_exits=short_exits_df,
        freq=f"{_worker_timeframe_minutes}min"
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
    """Pre-scan rapide VectorBT pour Bjorgum Double Tap.

    Approxime la detection de figures Double Top/Bottom par retest
    d'extremums recents (length + tol) sans la boucle d'etat complete,
    afin de rester executable en quelques secondes sur ~100k barres.
    """
    import logging
    from ..optimizer import ParameterGridSpec

    logger = logging.getLogger(__name__)

    if stop_requested is not None and stop_requested():
        logger.warning("Pre-scan Bjorgum annule avant demarrage.")
        _write_prescan_report(output_dir, "cancelled", None, {})
        return parameter_specs

    length_specs = next((s for s in parameter_specs if s.name == "length"), None)
    tol_specs = next((s for s in parameter_specs if s.name == "tol"), None)

    if not length_specs or not tol_specs or not length_specs.values or not tol_specs.values:
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

        lengths = sorted({int(v) for v in length_specs.values})
        tols = sorted({float(v) for v in tol_specs.values})

        from ..prescan_utils import downsample_parameter_grid
        downsampled = downsample_parameter_grid(
            {"lengths": lengths, "tols": tols},
            max_combos=20000,
            strategy_name="Bjorgum"
        )
        lengths = downsampled["lengths"]
        tols = downsampled["tols"]

        rolling_high_cache = {}
        rolling_low_cache = {}
        for length in lengths:
            rolling_high_cache[length] = data["high"].rolling(window=length, min_periods=1).max()
            rolling_low_cache[length] = data["low"].rolling(window=length, min_periods=1).min()

        combos = [(length, tol) for length in lengths for tol in tols]

        # 2. Dynamic Batch Size (Piste B)
        if workers > 1:
            batch_size = 50
        else:
            batch_size = 100

        total_batches = (len(combos) + batch_size - 1) // batch_size if combos else 0
        returns_batches: list[pd.Series] = []

        close = data["close"]

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
                initargs=(close, rolling_high_cache, rolling_low_cache, prescan_timeframe)
            ) as executor:
                completed = 0
                futures = {executor.submit(_process_prescan_batch, b): b for b in batches}

                while futures:
                    if stop_requested is not None and stop_requested():
                        logger.warning("Pre-scan Bjorgum annulé pendant le calcul parallèle.")
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
                    logger.warning("Pre-scan Bjorgum annule pendant le calcul des signaux.")
                    _write_prescan_report(output_dir, "cancelled", None, {})
                    return parameter_specs

                start_i = batch_idx * batch_size
                end_i = min(start_i + batch_size, len(combos))
                batch_combos = combos[start_i:end_i]

                batch_long_entries = {}
                batch_short_entries = {}
                batch_long_exits = {}
                batch_short_exits = {}

                for length, tol in batch_combos:
                    rolling_high = rolling_high_cache[length]
                    rolling_low = rolling_low_cache[length]

                    tf = tol / 100.0

                    # Prix proche d'un extremum recent (tolerance tol%)
                    near_low = data["close"] <= rolling_low * (1 + tf)
                    near_high = data["close"] >= rolling_high * (1 - tf)

                    # Retest avec rebond/chute directionnelle
                    long_sig = near_low & (data["close"] > data["close"].shift(1).fillna(data["close"].iloc[0]))
                    short_sig = near_high & (data["close"] < data["close"].shift(1).fillna(data["close"].iloc[0]))

                    # Premier signal consecutif uniquement
                    long_sig = long_sig & (~long_sig.shift(1).fillna(0.0).astype(bool))
                    short_sig = short_sig & (~short_sig.shift(1).fillna(0.0).astype(bool))

                    col = (length, tol)
                    batch_long_entries[col] = long_sig
                    batch_short_entries[col] = short_sig
                    batch_long_exits[col] = short_sig   # sortie long quand signal short
                    batch_short_exits[col] = long_sig   # sortie short quand signal long

                long_entries_df = pd.DataFrame(batch_long_entries, index=data.index)
                short_entries_df = pd.DataFrame(batch_short_entries, index=data.index)
                long_exits_df = pd.DataFrame(batch_long_exits, index=data.index)
                short_exits_df = pd.DataFrame(batch_short_exits, index=data.index)

                pf = vbt.Portfolio.from_signals(
                    data["close"],
                    entries=long_entries_df,
                    exits=long_exits_df,
                    short_entries=short_entries_df,
                    short_exits=short_exits_df,
                    freq=f"{prescan_timeframe}min"
                )
                returns_batches.append(pf.total_return())

                # Free RAM
                del long_entries_df
                del short_entries_df
                del long_exits_df
                del short_exits_df
                del pf
                del batch_long_entries
                del batch_short_entries
                del batch_long_exits
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

        min_len, max_len = min(p[0] for p in top_params), max(p[0] for p in top_params)
        min_tol, max_tol = min(p[1] for p in top_params), max(p[1] for p in top_params)

        # Marge de securite (+/- 10%)
        margin_len = max(1, int((max_len - min_len) * 0.1))
        margin_tol = max(0.5, (max_tol - min_tol) * 0.1)

        min_len = max(int(length_specs.values[0]), min_len - margin_len)
        max_len = min(int(length_specs.values[-1]), max_len + margin_len)
        min_tol = max(float(tol_specs.values[0]), min_tol - margin_tol)
        max_tol = min(float(tol_specs.values[-1]), max_tol + margin_tol)

        # Reconstruire ParameterGridSpec avec les nouvelles bornes
        new_specs = []
        len_filtered: tuple = ()
        tol_filtered: tuple = ()
        for s in parameter_specs:
            if s.name == "length":
                new_vals = tuple(v for v in s.values if min_len <= int(v) <= max_len)
                len_filtered = new_vals or s.values
                new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=len_filtered))
            elif s.name == "tol":
                new_vals = tuple(v for v in s.values if min_tol <= float(v) <= max_tol)
                tol_filtered = new_vals or s.values
                new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=tol_filtered))
            else:
                new_specs.append(s)

        _write_prescan_report(
            output_dir,
            "success",
            top_n,
            {
                "length": {
                    "original_bounds": [int(length_specs.values[0]), int(length_specs.values[-1])],
                    "new_bounds": [int(len_filtered[0]), int(len_filtered[-1])],
                    "filtered_values": list(len_filtered),
                },
                "tol": {
                    "original_bounds": [float(tol_specs.values[0]), float(tol_specs.values[-1])],
                    "new_bounds": [float(tol_filtered[0]), float(tol_filtered[-1])],
                    "filtered_values": list(tol_filtered),
                },
            },
        )
        logger.info(
            f"Bornes Optuna reduites via VectorBT: "
            f"length({min_len}-{max_len}), tol({min_tol:.1f}-{max_tol:.1f})"
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
