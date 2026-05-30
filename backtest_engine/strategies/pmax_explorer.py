from __future__ import annotations

from dataclasses import asdict, dataclass
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


def clear_pmax_explorer_feature_cache() -> None:
    """Proxy to the strategy module's feature cache eviction function."""
    import sys as _sys
    mod = _sys.modules.get("converted_pmax_explorer")
    if mod is not None and hasattr(mod, "clear_pmax_feature_cache"):
        mod.clear_pmax_feature_cache()


STRATEGY_FILE = (
    Path(__file__).resolve().parents[2]
    / "pine_scripts_convert_to_python"
    / "strategy"
    / "PMax-Explorer-STRATEGY-SCREENER.py"
)
_PMAX_MODULE_NAME = "converted_pmax_explorer"
_PMAX_MODULE: ModuleType | None = None
_PMAX_MODULE_LOCK = threading.Lock()


@dataclass
class PMaxExplorerConfigOverrides:
    periods: int | None = None
    multiplier: float | None = None
    mav: str | None = None
    length: int | None = None
    change_atr: bool | None = None
    source_col: str | None = None
    
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


def pmax_overrides_from_mapping(values: dict[str, object] | None, *, ignore_unknown: bool = True) -> PMaxExplorerConfigOverrides:
    if not values:
        return PMaxExplorerConfigOverrides()
    coerced = coerce_strategy_parameters("pmax_explorer", values, ignore_unknown=ignore_unknown)
    allowed = set(PMaxExplorerConfigOverrides.__dataclass_fields__.keys())
    return PMaxExplorerConfigOverrides(**{key: value for key, value in coerced.items() if key in allowed})


def load_pmax_overrides_from_config(path: str | Path) -> tuple[PMaxExplorerConfigOverrides, dict[str, object]]:
    runtime_config = load_strategy_config(path, strategy="pmax_explorer")
    return pmax_overrides_from_mapping(runtime_config.parameters), runtime_config.backtest


def _load_strategy_module() -> ModuleType:
    global _PMAX_MODULE

    if _PMAX_MODULE is not None:
        return _PMAX_MODULE

    with _PMAX_MODULE_LOCK:
        if _PMAX_MODULE is not None:
            return _PMAX_MODULE

        spec = importlib.util.spec_from_file_location(_PMAX_MODULE_NAME, STRATEGY_FILE)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load strategy module: {STRATEGY_FILE}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(spec.name, None)
            raise
        _PMAX_MODULE = module
        return _PMAX_MODULE


def _to_strategy_ohlcv(data: pd.DataFrame) -> pd.DataFrame:
    out = data.copy()
    for col in ["open", "high", "low", "close", "volume"]:
        if col not in out.columns:
            raise ValueError(f"Missing required column: {col}")
    return out[["open", "high", "low", "close", "volume"]].copy()


def _apply_overrides(config: Any, overrides: PMaxExplorerConfigOverrides) -> Any:
    for key, value in asdict(overrides).items():
        if value is not None and hasattr(config, key):
            setattr(config, key, value)
    return config


def run_pmax_explorer(
    data: pd.DataFrame,
    symbol: str,
    overrides: PMaxExplorerConfigOverrides | None = None,
    initial_capital: float = 1000.0,
    timeframe_minutes: int | str = 5,
    compute_full_metrics: bool = True,
    fast_score_metric: str | None = None,
    early_stop_drawdown_pct: float | None = None,
    repo_root: Path | None = None,
) -> BacktestRunResult:
    from ._currency_utils import setup_currency_and_fx_provider

    overrides = overrides or PMaxExplorerConfigOverrides()
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
    config = module.PMaxExplorerConfig()
    config = _apply_overrides(config, overrides)

    bars = _to_strategy_ohlcv(data)
    state, trades = module.run_pmax_explorer_strategy(
        bars, 
        config,
        early_stop_drawdown_pct=overrides.early_stop_drawdown_pct if overrides else None,
        compute_full_metrics=compute_full_metrics,
    )
    
    if compute_full_metrics:
        metrics, equity_curve = compute_metrics(
            MetricsInput(
                symbol=symbol,
                strategy="pmax_explorer",
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
        strategy="pmax_explorer",
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


def _compute_pmax_multi_py(
    mavg: np.ndarray, atr: np.ndarray, multipliers: np.ndarray
) -> np.ndarray:
    """Fallback Python implementation of vectorised PMax."""
    n = len(mavg)
    M = len(multipliers)
    pmax = np.empty((n, M), dtype=float)
    dir_arr = np.empty((n, M), dtype=int)
    longStop = np.empty((n, M), dtype=float)
    shortStop = np.empty((n, M), dtype=float)
    current_dir = np.ones(M, dtype=int)

    for i in range(n):
        if np.isnan(mavg[i]) or np.isnan(atr[i]):
            pmax[i] = np.nan
            dir_arr[i] = current_dir
            longStop[i] = np.nan
            shortStop[i] = np.nan
            continue

        cur_long_stop = mavg[i] - multipliers * atr[i]
        cur_short_stop = mavg[i] + multipliers * atr[i]

        if i == 0:
            prev_long_stop = cur_long_stop
            prev_short_stop = cur_short_stop
        else:
            prev_long_stop = longStop[i - 1]
            prev_short_stop = shortStop[i - 1]

        longStop[i] = np.where(
            mavg[i] > prev_long_stop,
            np.maximum(cur_long_stop, prev_long_stop),
            cur_long_stop,
        )
        shortStop[i] = np.where(
            mavg[i] < prev_short_stop,
            np.minimum(cur_short_stop, prev_short_stop),
            cur_short_stop,
        )

        if i > 0:
            current_dir = dir_arr[i - 1]

        flip_to_long = (current_dir == -1) & (mavg[i] > prev_short_stop)
        flip_to_short = (current_dir == 1) & (mavg[i] < prev_long_stop)
        current_dir = np.where(flip_to_long, 1, np.where(flip_to_short, -1, current_dir))

        dir_arr[i] = current_dir
        pmax[i] = np.where(current_dir == 1, longStop[i], shortStop[i])

    return pmax


try:
    import numba

    @numba.njit(cache=True)
    def _compute_pmax_multi(
        mavg: np.ndarray, atr: np.ndarray, multipliers: np.ndarray
    ) -> np.ndarray:
        """Numba-compiled vectorised PMax for an array of multipliers."""
        n = len(mavg)
        M = len(multipliers)
        pmax = np.empty((n, M), dtype=np.float64)
        dir_arr = np.empty((n, M), dtype=np.int64)
        longStop = np.empty((n, M), dtype=np.float64)
        shortStop = np.empty((n, M), dtype=np.float64)
        current_dir = np.ones(M, dtype=np.int64)

        for i in range(n):
            if np.isnan(mavg[i]) or np.isnan(atr[i]):
                for m in range(M):
                    pmax[i, m] = np.nan
                    dir_arr[i, m] = current_dir[m]
                    longStop[i, m] = np.nan
                    shortStop[i, m] = np.nan
                continue

            for m in range(M):
                cur_long_stop = mavg[i] - multipliers[m] * atr[i]
                cur_short_stop = mavg[i] + multipliers[m] * atr[i]

                if i == 0:
                    prev_long_stop = cur_long_stop
                    prev_short_stop = cur_short_stop
                else:
                    prev_long_stop = longStop[i - 1, m]
                    prev_short_stop = shortStop[i - 1, m]

                if mavg[i] > prev_long_stop:
                    longStop[i, m] = max(cur_long_stop, prev_long_stop)
                else:
                    longStop[i, m] = cur_long_stop

                if mavg[i] < prev_short_stop:
                    shortStop[i, m] = min(cur_short_stop, prev_short_stop)
                else:
                    shortStop[i, m] = cur_short_stop

                if i > 0:
                    current_dir[m] = dir_arr[i - 1, m]

                if current_dir[m] == -1 and mavg[i] > prev_short_stop:
                    current_dir[m] = 1
                elif current_dir[m] == 1 and mavg[i] < prev_long_stop:
                    current_dir[m] = -1

                dir_arr[i, m] = current_dir[m]
                if current_dir[m] == 1:
                    pmax[i, m] = longStop[i, m]
                else:
                    pmax[i, m] = shortStop[i, m]

        return pmax

except ImportError:
    _compute_pmax_multi = _compute_pmax_multi_py  # type: ignore[assignment]


# Globals for multiprocessing workers to reference mapped memory directly
_worker_close = None
_worker_ma_df = None
_worker_atr_df = None
_worker_multiplier_vals = None
_worker_timeframe_minutes = None

def _init_prescan_worker(close, ma_df, atr_df, multiplier_vals, timeframe_mins):
    global _worker_close, _worker_ma_df, _worker_atr_df, _worker_multiplier_vals, _worker_timeframe_minutes
    _worker_close = close
    _worker_ma_df = ma_df
    _worker_atr_df = atr_df
    _worker_multiplier_vals = multiplier_vals
    _worker_timeframe_minutes = timeframe_mins

def _process_prescan_batch(batch_combos):
    global _worker_close, _worker_ma_df, _worker_atr_df, _worker_multiplier_vals, _worker_timeframe_minutes
    import pandas as pd
    import numpy as np
    import vectorbt as vbt
    from .pmax_explorer import _compute_pmax_multi

    returns_batches = []
    mini_batch_size = max(1, 200 // len(batch_combos))

    for m_idx in range(0, len(_worker_multiplier_vals), mini_batch_size):
        mini_mults = _worker_multiplier_vals[m_idx : m_idx + mini_batch_size]
        mults_arr = np.array(mini_mults)

        batch_entries = {}
        batch_exits = {}

        for periods, length in batch_combos:
            mavg = _worker_ma_df[length].to_numpy(dtype=float)
            mavg_shifted = np.empty_like(mavg)
            mavg_shifted[0] = mavg[0]
            mavg_shifted[1:] = mavg[:-1]

            atr = _worker_atr_df[periods].to_numpy(dtype=float)
            pmax_multi = _compute_pmax_multi(mavg, atr, mults_arr)

            entries_multi = (mavg[:, None] > pmax_multi) & (mavg_shifted[:, None] <= pmax_multi)
            exits_multi = (mavg[:, None] < pmax_multi) & (mavg_shifted[:, None] >= pmax_multi)

            for idx, mult in enumerate(mini_mults):
                col = (periods, mult, length)
                batch_entries[col] = entries_multi[:, idx]
                batch_exits[col] = exits_multi[:, idx]

        entries_df = pd.DataFrame(batch_entries, index=_worker_close.index)
        exits_df = pd.DataFrame(batch_exits, index=_worker_close.index)

        pf = vbt.Portfolio.from_signals(
            _worker_close,
            entries=entries_df,
            exits=exits_df,
            freq=f"{_worker_timeframe_minutes}min",
        )
        returns_batches.append(pf.total_return())

    return pd.concat(returns_batches) if returns_batches else pd.Series(dtype=float)


def vectorbt_prescan(
    data: pd.DataFrame,
    parameter_specs: list[Any],
    timeframe_minutes: int | str,
    output_dir: Path | None = None,
    stop_requested: Callable[[], bool] | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
    workers: int = 1,
) -> list[Any]:
    """Pre-scan rapide VectorBT pour PMax Explorer.

    Scanne les combinaisons (periods, multiplier, length) avec mav fixe a EMA
    afin de restreindre les bornes d'exploration avant l'optimisation bayesienne.
    """
    import logging
    import random
    import numpy as np
    from ..optimizer import ParameterGridSpec

    logger = logging.getLogger(__name__)

    if stop_requested is not None and stop_requested():
        logger.warning("Pre-scan PMax annule avant demarrage.")
        _write_prescan_report(output_dir, "cancelled", None, {})
        return parameter_specs

    periods_specs = next((s for s in parameter_specs if s.name == "periods"), None)
    multiplier_specs = next((s for s in parameter_specs if s.name == "multiplier"), None)
    length_specs = next((s for s in parameter_specs if s.name == "length"), None)

    if not all([periods_specs, multiplier_specs, length_specs]):
        _write_prescan_report(output_dir, "skipped", None, {})
        return parameter_specs
    if not all([s.values for s in [periods_specs, multiplier_specs, length_specs]]):
        _write_prescan_report(output_dir, "skipped", None, {})
        return parameter_specs

    try:
        import vectorbt as vbt
        import gc

        from ..prescan_utils import downsample_parameter_grid

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

        periods_vals = sorted({int(v) for v in periods_specs.values})
        multiplier_vals = sorted({float(v) for v in multiplier_specs.values})
        length_vals = sorted({int(v) for v in length_specs.values})

        downsampled = downsample_parameter_grid(
            {"periods": periods_vals, "multiplier": multiplier_vals, "length": length_vals},
            max_combos=2000,
            strategy_name="PMax"
        )
        periods_vals = downsampled["periods"]
        multiplier_vals = downsampled["multiplier"]
        length_vals = downsampled["length"]

        close = data["close"]
        high = data["high"]
        low = data["low"]
        source = (high + low) / 2.0

        # Pre-calculer toutes les EMA (mav fixe = EMA) avec VectorBT
        all_ma = vbt.MA.run(source, window=length_vals)
        # Pre-calculer toutes les ATR avec VectorBT
        all_atr = vbt.ATR.run(high, low, close, window=periods_vals)

        module = _load_strategy_module()

        combos = [(periods, length) for length in length_vals for periods in periods_vals]

        # 2. Dynamic Batch Size (Piste B)
        if workers > 1:
            # We want batches to be smaller in parallel to run cleanly
            max_batch_combos = max(1, 100 // len(multiplier_vals))
        else:
            max_batch_combos = max(1, 400 // len(multiplier_vals))
            
        BATCH_SIZE = max_batch_combos
        total_batches = (len(combos) + BATCH_SIZE - 1) // BATCH_SIZE if combos else 0
        returns_batches: list[pd.Series] = []

        try:
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
                    initargs=(close, all_ma.ma, all_atr.atr, multiplier_vals, prescan_timeframe)
                ) as executor:
                    completed = 0
                    futures = {executor.submit(_process_prescan_batch, b): b for b in batches}

                    while futures:
                        if stop_requested is not None and stop_requested():
                            logger.warning("Pre-scan PMax annulé pendant le calcul parallèle.")
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
                        logger.warning("Pre-scan PMax annule pendant l'evaluation VectorBT.")
                        _write_prescan_report(output_dir, "cancelled", None, {})
                        return parameter_specs

                    start_i = batch_idx * BATCH_SIZE
                    end_i = min(start_i + BATCH_SIZE, len(combos))
                    batch_combos = combos[start_i:end_i]

                    # Mini-batching multiplier_vals
                    mini_batch_size = max(1, 200 // len(batch_combos))

                    for m_idx in range(0, len(multiplier_vals), mini_batch_size):
                        mini_mults = multiplier_vals[m_idx : m_idx + mini_batch_size]
                        mults_arr = np.array(mini_mults)

                        batch_entries = {}
                        batch_exits = {}

                        for periods, length in batch_combos:
                            mavg = all_ma.ma[length].to_numpy(dtype=float)
                            mavg_shifted = np.empty_like(mavg)
                            mavg_shifted[0] = mavg[0]
                            mavg_shifted[1:] = mavg[:-1]

                            atr = all_atr.atr[periods].to_numpy(dtype=float)
                            pmax_multi = _compute_pmax_multi(mavg, atr, mults_arr)

                            entries_multi = (mavg[:, None] > pmax_multi) & (mavg_shifted[:, None] <= pmax_multi)
                            exits_multi = (mavg[:, None] < pmax_multi) & (mavg_shifted[:, None] >= pmax_multi)

                            for idx, mult in enumerate(mini_mults):
                                col = (periods, mult, length)
                                batch_entries[col] = entries_multi[:, idx]
                                batch_exits[col] = exits_multi[:, idx]

                        entries_df = pd.DataFrame(batch_entries, index=data.index)
                        exits_df = pd.DataFrame(batch_exits, index=data.index)

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
                        del batch_entries
                        del batch_exits
                        gc.collect()

                    if progress_callback is not None:
                        try:
                            progress_callback(batch_idx + 1, total_batches)
                        except Exception as cb_err:
                            logger.warning(f"Error in prescan progress callback: {cb_err}")

        except MemoryError as me:
            logger.warning(f"MemoryError during PMax VectorBT pre-scan: {me}. Falling back to unmodified parameter_specs.")
            gc.collect()
            _write_prescan_report(output_dir, "error", None, {})
            return parameter_specs

        returns = pd.concat(returns_batches)
        returns = returns.sort_index()

        # Recupere le Top 5% des combinaisons
        top_n = max(1, int(len(returns) * 0.05))
        top_params = returns.nlargest(top_n).index.tolist()

        if not top_params:
            _write_prescan_report(output_dir, "no_candidates", top_n, {})
            return parameter_specs

        min_periods, max_periods = min(p[0] for p in top_params), max(p[0] for p in top_params)
        min_mult, max_mult = min(p[1] for p in top_params), max(p[1] for p in top_params)
        min_len, max_len = min(p[2] for p in top_params), max(p[2] for p in top_params)

        # Marge de securite (+/- 10%)
        margin_periods = max(1, int((max_periods - min_periods) * 0.1))
        margin_mult = max(0.1, (max_mult - min_mult) * 0.1)
        margin_len = max(1, int((max_len - min_len) * 0.1))

        min_periods = max(int(periods_specs.values[0]), min_periods - margin_periods)
        max_periods = min(int(periods_specs.values[-1]), max_periods + margin_periods)
        min_mult = max(float(multiplier_specs.values[0]), min_mult - margin_mult)
        max_mult = min(float(multiplier_specs.values[-1]), max_mult + margin_mult)
        min_len = max(int(length_specs.values[0]), min_len - margin_len)
        max_len = min(int(length_specs.values[-1]), max_len + margin_len)

        # Reconstruire ParameterGridSpec avec les nouvelles bornes
        new_specs = []
        periods_filtered: tuple = ()
        mult_filtered: tuple = ()
        len_filtered: tuple = ()
        for s in parameter_specs:
            if s.name == "periods":
                new_vals = tuple(v for v in s.values if min_periods <= int(v) <= max_periods)
                periods_filtered = new_vals or s.values
                new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=periods_filtered))
            elif s.name == "multiplier":
                new_vals = tuple(v for v in s.values if min_mult <= float(v) <= max_mult)
                mult_filtered = new_vals or s.values
                new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=mult_filtered))
            elif s.name == "length":
                new_vals = tuple(v for v in s.values if min_len <= int(v) <= max_len)
                len_filtered = new_vals or s.values
                new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=len_filtered))
            else:
                new_specs.append(s)

        _write_prescan_report(
            output_dir,
            "success",
            top_n,
            {
                "periods": {
                    "original_bounds": [int(periods_specs.values[0]), int(periods_specs.values[-1])],
                    "new_bounds": [int(periods_filtered[0]), int(periods_filtered[-1])],
                    "filtered_values": list(periods_filtered),
                },
                "multiplier": {
                    "original_bounds": [float(multiplier_specs.values[0]), float(multiplier_specs.values[-1])],
                    "new_bounds": [float(mult_filtered[0]), float(mult_filtered[-1])],
                    "filtered_values": list(mult_filtered),
                },
                "length": {
                    "original_bounds": [int(length_specs.values[0]), int(length_specs.values[-1])],
                    "new_bounds": [int(len_filtered[0]), int(len_filtered[-1])],
                    "filtered_values": list(len_filtered),
                },
            },
        )
        logger.info(
            f"Bornes Optuna reduites via VectorBT: "
            f"periods({min_periods}-{max_periods}), multiplier({min_mult:.1f}-{max_mult:.1f}), "
            f"length({min_len}-{max_len})"
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
