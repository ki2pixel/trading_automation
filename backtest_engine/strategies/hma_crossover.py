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


def clear_hma_feature_cache() -> None:
    """Proxy to the strategy module's feature cache eviction function.

    Calling this invalidates cached HMA indicator arrays. It is safe to call
    before loading a new dataset so workers never serve stale indicator data.
    The underlying cache lives in the strategy module and is populated lazily
    on the first call to add_hma_crossover_features().
    """
    # Avoid importing the heavy module at import-time; only touch it if it has
    # already been loaded (otherwise there is nothing to clear).
    import sys as _sys
    mod = _sys.modules.get("converted_hma_crossover")
    if mod is not None and hasattr(mod, "clear_hma_feature_cache"):
        mod.clear_hma_feature_cache()


STRATEGY_FILE = (
    Path(__file__).resolve().parents[2]
    / "pine_scripts_convert_to_python"
    / "strategy"
    / "BuySell-Hull-Crossover-Strategy-V3-Capped-Bucket-by-VibeAlgos.py"
)
_HMA_MODULE_NAME = "converted_hma_crossover"
_HMA_MODULE: ModuleType | None = None
_HMA_MODULE_LOCK = threading.Lock()


@dataclass
class HMAConfigOverrides:
    fast_len: int | None = None
    slow_len: int | None = None
    source_col: str | None = None
    confirm_on_close: bool | None = None
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


def hma_overrides_from_mapping(values: dict[str, object] | None, *, ignore_unknown: bool = True) -> HMAConfigOverrides:
    if not values:
        return HMAConfigOverrides()
    coerced = coerce_strategy_parameters("hma_crossover", values, ignore_unknown=ignore_unknown)
    allowed = set(HMAConfigOverrides.__dataclass_fields__.keys())
    return HMAConfigOverrides(**{key: value for key, value in coerced.items() if key in allowed})


def load_hma_overrides_from_config(path: str | Path) -> tuple[HMAConfigOverrides, dict[str, object]]:
    runtime_config = load_strategy_config(path, strategy="hma_crossover")
    return hma_overrides_from_mapping(runtime_config.parameters), runtime_config.backtest


def _load_strategy_module() -> ModuleType:
    global _HMA_MODULE

    if _HMA_MODULE is not None:
        return _HMA_MODULE

    with _HMA_MODULE_LOCK:
        if _HMA_MODULE is not None:
            return _HMA_MODULE

        spec = importlib.util.spec_from_file_location(_HMA_MODULE_NAME, STRATEGY_FILE)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load strategy module: {STRATEGY_FILE}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(spec.name, None)
            raise
        _HMA_MODULE = module
        return _HMA_MODULE


def _to_strategy_ohlcv(data: pd.DataFrame) -> pd.DataFrame:
    out = data.copy()
    # Converted strategies expect lowercase OHLCV columns and a DateTimeIndex.
    for col in ["open", "high", "low", "close", "volume"]:
        if col not in out.columns:
            raise ValueError(f"Missing required column: {col}")
    return out[["open", "high", "low", "close", "volume"]].copy()


def _apply_overrides(config: Any, overrides: HMAConfigOverrides) -> Any:
    for key, value in asdict(overrides).items():
        if value is not None and hasattr(config, key):
            setattr(config, key, value)
    return config


def run_hma_crossover(
    data: pd.DataFrame,
    symbol: str,
    overrides: HMAConfigOverrides | None = None,
    initial_capital: float = 1000.0,
    timeframe_minutes: int | str = 5,
    compute_full_metrics: bool = True,
    fast_score_metric: str | None = None,
    repo_root: Path | None = None,
) -> BacktestRunResult:
    from ._currency_utils import setup_currency_and_fx_provider

    overrides = overrides or HMAConfigOverrides()
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
    config = module.HMACrossoverConfig()
    config = _apply_overrides(config, overrides)

    bars = _to_strategy_ohlcv(data)
    state, trades = module.run_hma_crossover_strategy(
        bars, 
        config,
        early_stop_drawdown_pct=overrides.early_stop_drawdown_pct,
        compute_full_metrics=compute_full_metrics,
    )
    
    if compute_full_metrics:
        metrics, equity_curve = compute_metrics(
            MetricsInput(
                symbol=symbol,
                strategy="hma_crossover",
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
        strategy="hma_crossover",
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
_worker_ma_np = None
_worker_window_to_idx = None
_worker_timeframe_minutes = None

def _init_prescan_worker(close, ma_np, window_to_idx, timeframe_mins):
    global _worker_close, _worker_ma_np, _worker_window_to_idx, _worker_timeframe_minutes
    _worker_close = close
    _worker_ma_np = ma_np
    _worker_window_to_idx = window_to_idx
    _worker_timeframe_minutes = timeframe_mins

def _process_prescan_batch(batch_combos):
    global _worker_close, _worker_ma_np, _worker_window_to_idx, _worker_timeframe_minutes
    import pandas as pd
    import numpy as np
    import vectorbt as vbt

    fast_indices = [_worker_window_to_idx[f_w] for f_w, s_w in batch_combos]
    slow_indices = [_worker_window_to_idx[s_w] for f_w, s_w in batch_combos]

    fast_ma_batch = _worker_ma_np[:, fast_indices]
    slow_ma_batch = _worker_ma_np[:, slow_indices]

    fast_prev = np.empty_like(fast_ma_batch)
    fast_prev[0] = np.nan
    fast_prev[1:] = fast_ma_batch[:-1]

    slow_prev = np.empty_like(slow_ma_batch)
    slow_prev[0] = np.nan
    slow_prev[1:] = slow_ma_batch[:-1]

    # Crossed above: fast_ma_batch > slow_ma_batch, fast_prev <= slow_prev
    entries_batch = (fast_ma_batch > slow_ma_batch) & (fast_prev <= slow_prev)
    # Crossed below: fast_ma_batch < slow_ma_batch, fast_prev >= slow_prev
    exits_batch = (fast_ma_batch < slow_ma_batch) & (fast_prev >= slow_prev)

    columns = pd.MultiIndex.from_tuples(batch_combos, names=["fast_len", "slow_len"])
    entries_df = pd.DataFrame(entries_batch, index=_worker_close.index, columns=columns)
    exits_df = pd.DataFrame(exits_batch, index=_worker_close.index, columns=columns)

    pf = vbt.Portfolio.from_signals(
        _worker_close,
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
    """Préalablement à l'optimisation bayésienne, scanne rapidement les longueurs 
    de moyennes mobiles avec VectorBT pour restreindre les bornes d'exploration.
    """
    import logging
    import numpy as np
    from ..optimizer import ParameterGridSpec

    logger = logging.getLogger(__name__)

    if stop_requested is not None and stop_requested():
        logger.warning("Pre-scan HMA annule avant demarrage.")
        _write_prescan_report(output_dir, "cancelled", None, {})
        return parameter_specs

    fast_specs = next((s for s in parameter_specs if s.name == "fast_len"), None)
    slow_specs = next((s for s in parameter_specs if s.name == "slow_len"), None)

    if fast_specs and slow_specs and fast_specs.values and slow_specs.values:
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

            fast_windows_list = sorted({int(v) for v in fast_specs.values})
            slow_windows_list = sorted({int(v) for v in slow_specs.values})

            from ..prescan_utils import downsample_parameter_grid
            downsampled = downsample_parameter_grid(
                {"fast": fast_windows_list, "slow": slow_windows_list},
                max_combos=20000,
                strategy_name="HMA"
            )
            
            fast_windows = np.array(downsampled["fast"])
            slow_windows = np.array(downsampled["slow"])

            # Pre-calculer toutes les MAs pour eviter les recalculs
            all_ma = vbt.MA.run(data["close"], window=fast_windows)
            ma_np = all_ma.ma.to_numpy(dtype=float)
            if ma_np.ndim == 1:
                ma_np = ma_np.reshape(-1, 1)
            
            # Creer une table de correspondance window -> index
            window_to_idx = {w: idx for idx, w in enumerate(fast_windows)}
            
            # Generer toutes les combinaisons de deux fenetres (fast < slow)
            combos = [(fast_windows[i], fast_windows[j]) for i in range(len(fast_windows)) for j in range(i + 1, len(fast_windows))]

            # 2. Dynamic Batch Size (Piste B)
            if workers > 1:
                BATCH_SIZE = 50
            else:
                BATCH_SIZE = 100

            total_batches = (len(combos) + BATCH_SIZE - 1) // BATCH_SIZE if combos else 0
            returns_batches: list[pd.Series] = []

            close = data["close"]

            # 3. Multiprocessing Parallelization (Piste A)
            if workers > 1:
                logger.info(f"Lancement du Pre-Scan VectorBT en parallèle avec {workers} processus (Batch Size={BATCH_SIZE})...")
                import multiprocessing
                try:
                    ctx = multiprocessing.get_context("fork")
                except ValueError:
                    ctx = multiprocessing.get_context()

                batches = []
                for batch_idx in range(total_batches):
                    start_i = batch_idx * BATCH_SIZE
                    end_i = min(start_i + BATCH_SIZE, len(combos))
                    batches.append(combos[start_i:end_i])

                import concurrent.futures
                with concurrent.futures.ProcessPoolExecutor(
                    max_workers=workers,
                    mp_context=ctx,
                    initializer=_init_prescan_worker,
                    initargs=(close, ma_np, window_to_idx, prescan_timeframe)
                ) as executor:
                    completed = 0
                    futures = {executor.submit(_process_prescan_batch, b): b for b in batches}

                    while futures:
                        if stop_requested is not None and stop_requested():
                            logger.warning("Pre-scan HMA annulé pendant le calcul parallèle.")
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
                        logger.warning("Pre-scan HMA annule pendant l'evaluation VectorBT.")
                        _write_prescan_report(output_dir, "cancelled", None, {})
                        return parameter_specs

                    start_i = batch_idx * BATCH_SIZE
                    end_i = min(start_i + BATCH_SIZE, len(combos))
                    batch_combos = combos[start_i:end_i]

                    fast_indices = [window_to_idx[f_w] for f_w, s_w in batch_combos]
                    slow_indices = [window_to_idx[s_w] for f_w, s_w in batch_combos]

                    fast_ma_batch = ma_np[:, fast_indices]
                    slow_ma_batch = ma_np[:, slow_indices]

                    fast_prev = np.empty_like(fast_ma_batch)
                    fast_prev[0] = np.nan
                    fast_prev[1:] = fast_ma_batch[:-1]

                    slow_prev = np.empty_like(slow_ma_batch)
                    slow_prev[0] = np.nan
                    slow_prev[1:] = slow_ma_batch[:-1]

                    # Crossed above: fast_ma_batch > slow_ma_batch, fast_prev <= slow_prev
                    entries_batch = (fast_ma_batch > slow_ma_batch) & (fast_prev <= slow_prev)
                    # Crossed below: fast_ma_batch < slow_ma_batch, fast_prev >= slow_prev
                    exits_batch = (fast_ma_batch < slow_ma_batch) & (fast_prev >= slow_prev)

                    columns = pd.MultiIndex.from_tuples(batch_combos, names=["fast_len", "slow_len"])
                    entries_df = pd.DataFrame(entries_batch, index=data.index, columns=columns)
                    exits_df = pd.DataFrame(exits_batch, index=data.index, columns=columns)

                    pf = vbt.Portfolio.from_signals(
                        close,
                        entries=entries_df,
                        exits=exits_df,
                        freq=f"{prescan_timeframe}min",
                    )
                    returns_batches.append(pf.total_return())

                    # Free RAM
                    del entries_df
                    del exits_df
                    del pf
                    del fast_ma_batch
                    del slow_ma_batch
                    del entries_batch
                    del exits_batch
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

            # Récupère le Top 5% des configurations
            top_n = max(1, int(len(returns) * 0.05))
            top_params = returns.nlargest(top_n).index.tolist()

            if top_params:
                min_fast, max_fast = min(p[0] for p in top_params), max(p[0] for p in top_params)
                min_slow, max_slow = min(p[1] for p in top_params), max(p[1] for p in top_params)

                # Marge de sécurité (+/- 10%)
                margin_fast = max(1, int((max_fast - min_fast) * 0.1))
                margin_slow = max(1, int((max_slow - min_slow) * 0.1))

                min_fast = max(int(fast_specs.values[0]), min_fast - margin_fast)
                max_fast = min(int(fast_specs.values[-1]), max_fast + margin_fast)
                min_slow = max(int(slow_specs.values[0]), min_slow - margin_slow)
                max_slow = min(int(slow_specs.values[-1]), max_slow + margin_slow)

                # Remplacement des spécifications pour Optuna
                new_specs = []
                fast_filtered: tuple = ()
                slow_filtered: tuple = ()
                for s in parameter_specs:
                    if s.name == "fast_len":
                        new_vals = tuple(v for v in s.values if min_fast <= int(v) <= max_fast)
                        fast_filtered = new_vals or s.values
                        new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=fast_filtered))
                    elif s.name == "slow_len":
                        new_vals = tuple(v for v in s.values if min_slow <= int(v) <= max_slow)
                        slow_filtered = new_vals or s.values
                        new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=slow_filtered))
                    else:
                        new_specs.append(s)

                _write_prescan_report(
                    output_dir,
                    "success",
                    top_n,
                    {
                        "fast_len": {
                            "original_bounds": [int(fast_specs.values[0]), int(fast_specs.values[-1])],
                            "new_bounds": [int(fast_filtered[0]), int(fast_filtered[-1])],
                            "filtered_values": list(fast_filtered),
                        },
                        "slow_len": {
                            "original_bounds": [int(slow_specs.values[0]), int(slow_specs.values[-1])],
                            "new_bounds": [int(slow_filtered[0]), int(slow_filtered[-1])],
                            "filtered_values": list(slow_filtered),
                        },
                    },
                )
                logger.info(f"Bornes Optuna réduites via VectorBT: fast_len({min_fast}-{max_fast}), slow_len({min_slow}-{max_slow})")
                return new_specs
            else:
                _write_prescan_report(output_dir, "no_candidates", top_n, {})
                return parameter_specs
        except ImportError:
            _write_prescan_report(output_dir, "skipped", None, {})
            logger.warning("VectorBT n'est pas installé, impossible de lancer le pre-scan.")
        except Exception as e:
            _write_prescan_report(output_dir, "error", None, {})
            logger.warning(f"Erreur Pre-Scan VectorBT: {e}. Optuna utilisera les bornes globales.")

    _write_prescan_report(output_dir, "skipped", None, {})
    return parameter_specs
