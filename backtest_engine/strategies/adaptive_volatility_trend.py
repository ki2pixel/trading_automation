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


STRATEGY_FILE = (
    Path(__file__).resolve().parents[2]
    / "pine_scripts_convert_to_python"
    / "strategy"
    / "Adaptive-Volatility-Trend-Strategy-V3-Capped-Bucket-by-WillyAlgoTrader.py"
)
_AVT_MODULE_NAME = "converted_adaptive_volatility_trend"
_AVT_MODULE: ModuleType | None = None
_AVT_MODULE_LOCK = threading.Lock()


@dataclass
class AVTConfigOverrides:
    source: str | None = None
    length: int | None = None
    atr_len: int | None = None
    atr_mult: float | None = None
    preset: str | None = None
    use_rsi_filter: bool | None = None
    rsi_len: int | None = None
    rsi_overbought: int | None = None
    rsi_oversold: int | None = None
    use_volume_filter: bool | None = None
    volume_mult: float | None = None
    efficiency_smoothing: int | None = None
    min_signal_score: int | None = None
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
    execution: str | None = None
    apply_estimated_costs_to_realized_pnl: bool | None = None
    allow_fractional_quantity: bool | None = True
    quantity_precision: int | None = 6
    early_stop_drawdown_pct: float | None = None
    asset_currency: str | None = None
    account_currency: str | None = None
    fx_rate_provider: object | None = None


def avt_overrides_from_mapping(values: dict[str, object] | None, *, ignore_unknown: bool = True) -> AVTConfigOverrides:
    if not values:
        return AVTConfigOverrides()
    coerced = coerce_strategy_parameters("adaptive_volatility_trend", values, ignore_unknown=ignore_unknown)
    allowed = set(AVTConfigOverrides.__dataclass_fields__.keys())
    return AVTConfigOverrides(**{key: value for key, value in coerced.items() if key in allowed})


def load_avt_overrides_from_config(path: str | Path) -> tuple[AVTConfigOverrides, dict[str, object]]:
    runtime_config = load_strategy_config(path, strategy="adaptive_volatility_trend")
    return avt_overrides_from_mapping(runtime_config.parameters), runtime_config.backtest


def _load_strategy_module() -> ModuleType:
    global _AVT_MODULE

    if _AVT_MODULE is not None:
        return _AVT_MODULE

    with _AVT_MODULE_LOCK:
        if _AVT_MODULE is not None:
            return _AVT_MODULE

        spec = importlib.util.spec_from_file_location(_AVT_MODULE_NAME, STRATEGY_FILE)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load strategy module: {STRATEGY_FILE}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(spec.name, None)
            raise
        _AVT_MODULE = module
        return _AVT_MODULE


def _to_strategy_ohlcv(data: pd.DataFrame) -> pd.DataFrame:
    out = data.copy()
    for col in ["open", "high", "low", "close", "volume"]:
        if col not in out.columns:
            raise ValueError(f"Missing required column: {col}")
    return out[["open", "high", "low", "close", "volume"]].copy()


def _apply_overrides(config: Any, overrides: AVTConfigOverrides) -> Any:
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


def run_adaptive_volatility_trend(
    data: pd.DataFrame,
    symbol: str,
    overrides: AVTConfigOverrides | None = None,
    initial_capital: float = 1000.0,
    timeframe_minutes: int | str = 5,
    compute_full_metrics: bool = True,
    fast_score_metric: str | None = None,
    repo_root: Path | None = None,
) -> BacktestRunResult:
    from ._currency_utils import setup_currency_and_fx_provider

    overrides = overrides or AVTConfigOverrides()
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
    config = module.AVTConfig()
    config = _apply_overrides(config, overrides)

    bars = _to_strategy_ohlcv(data)
    state, raw_trades = module.backtest_avt_strategy(
        bars,
        config,
        early_stop_drawdown_pct=overrides.early_stop_drawdown_pct if overrides else None,
        compute_full_metrics=compute_full_metrics,
    )


    trades = _normalize_trades(raw_trades, bars)

    if compute_full_metrics:
        metrics, equity_curve = compute_metrics(
            MetricsInput(
                symbol=symbol,
                strategy="adaptive_volatility_trend",
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
        strategy="adaptive_volatility_trend",
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
_worker_source = None
_worker_adaptive_by_length = None
_worker_atr_by_len = None
_worker_timeframe_minutes = None

def _init_prescan_worker(close, source, adaptive_by_length, atr_by_len, timeframe_mins):
    global _worker_close, _worker_source, _worker_adaptive_by_length, _worker_atr_by_len, _worker_timeframe_minutes
    _worker_close = close
    _worker_source = source
    _worker_adaptive_by_length = adaptive_by_length
    _worker_atr_by_len = atr_by_len
    _worker_timeframe_minutes = timeframe_mins

def _process_prescan_batch(batch_combos):
    global _worker_close, _worker_source, _worker_adaptive_by_length, _worker_atr_by_len, _worker_timeframe_minutes
    import pandas as pd
    import numpy as np
    import vectorbt as vbt

    batch_entries = {}
    batch_exits = {}

    for length, atr_len, atr_mult in batch_combos:
        adaptive, er = _worker_adaptive_by_length[length]
        line_delta = adaptive - adaptive.shift(1).fillna(adaptive)

        atr_raw = _worker_atr_by_len[atr_len]
        threshold = atr_raw * 0.05

        # Trend direction vectorisé (équivalent à la logique Pine)
        trend_dir = pd.Series(np.nan, index=_worker_close.index)
        trend_dir[line_delta > threshold] = 1
        trend_dir[line_delta < -threshold] = -1
        trend_dir = trend_dir.ffill().fillna(0).astype(int)

        is_bull = trend_dir == 1
        is_bear = trend_dir == -1

        prev_bull = is_bull.shift(1, fill_value=False)
        prev_bear = is_bear.shift(1, fill_value=False)

        trend_flip_bull = is_bull & (~prev_bull)
        trend_flip_bear = is_bear & (~prev_bear)

        price_above = _worker_source > adaptive
        price_below = _worker_source < adaptive

        entries = trend_flip_bull & price_above
        exits = trend_flip_bear & price_below

        col = (length, atr_len, atr_mult)
        batch_entries[col] = entries
        batch_exits[col] = exits

    entries_df = pd.DataFrame(batch_entries, index=_worker_close.index)
    exits_df = pd.DataFrame(batch_exits, index=_worker_close.index)

    pf = vbt.Portfolio.from_signals(
        _worker_close, entries_df, exits_df, freq=f"{_worker_timeframe_minutes}min"
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
    """Préalablement à l'optimisation bayésienne, scanne rapidement les paramètres
    AVT (length, atr_len, atr_mult) avec VectorBT pour restreindre les bornes
    d'exploration.

    Implémente la logique cœur de la stratégie (Adaptive MA + bands ATR +
    direction de tendance) sans les filtres optionnels (RSI, volume, score)
    afin de garder le scan rapide tout en conservant l'ADN du signal.
    """
    import logging
    import numpy as np
    from ..optimizer import ParameterGridSpec

    logger = logging.getLogger(__name__)

    if stop_requested is not None and stop_requested():
        logger.warning("Pre-scan AVT annule avant demarrage.")
        _write_prescan_report(output_dir, "cancelled", None, {})
        return parameter_specs

    length_specs = next((s for s in parameter_specs if s.name == "length"), None)
    atr_len_specs = next((s for s in parameter_specs if s.name == "atr_len"), None)
    atr_mult_specs = next((s for s in parameter_specs if s.name == "atr_mult"), None)

    if not all([length_specs, atr_len_specs, atr_mult_specs]):
        _write_prescan_report(output_dir, "skipped", None, {})
        return parameter_specs
    if not all([s.values for s in [length_specs, atr_len_specs, atr_mult_specs]]):
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
        close = module._as_float_series(data, "close")
        high = module._as_float_series(data, "high")
        low = module._as_float_series(data, "low")
        source = module._price_source(data, "close")

        lengths = sorted({int(v) for v in length_specs.values})
        atr_lens = sorted({int(v) for v in atr_len_specs.values})
        atr_mults = sorted({float(v) for v in atr_mult_specs.values})

        from ..prescan_utils import downsample_parameter_grid
        downsampled = downsample_parameter_grid(
            {"lengths": lengths, "atr_lens": atr_lens, "atr_mults": atr_mults},
            max_combos=20000,
            strategy_name="AVT"
        )
        lengths = downsampled["lengths"]
        atr_lens = downsampled["atr_lens"]
        atr_mults = downsampled["atr_mults"]

        # Pré-calculer adaptive_ma et efficiency_ratio pour chaque length
        # (efficiency_smoothing est fixé à sa valeur par défaut = 5)
        adaptive_by_length: dict[int, tuple[pd.Series, pd.Series]] = {}
        for length in lengths:
            if stop_requested is not None and stop_requested():
                logger.warning("Pre-scan AVT annule pendant le pre-calcul des indicateurs.")
                _write_prescan_report(output_dir, "cancelled", None, {})
                return parameter_specs
            adaptive, er = module._adaptive_ma(source, close, length, 5)
            adaptive_by_length[length] = (adaptive.fillna(close), er.fillna(0.5))

        # Pré-calculer ATR pour chaque atr_len
        atr_by_len: dict[int, pd.Series] = {}
        for atr_len in atr_lens:
            if stop_requested is not None and stop_requested():
                logger.warning("Pre-scan AVT annule pendant le pre-calcul des indicateurs.")
                _write_prescan_report(output_dir, "cancelled", None, {})
                return parameter_specs
            atr_by_len[atr_len] = module._atr(high, low, close, atr_len).fillna(0.0)

        combos = [(length, atr_len, atr_mult) for length in lengths for atr_len in atr_lens for atr_mult in atr_mults]

        # 2. Dynamic Batch Size (Piste B)
        if workers > 1:
            batch_size = 50
        else:
            batch_size = 100

        total_batches = (len(combos) + batch_size - 1) // batch_size if combos else 0
        returns_batches: list[pd.Series] = []

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
                initargs=(close, source, adaptive_by_length, atr_by_len, prescan_timeframe)
            ) as executor:
                completed = 0
                futures = {executor.submit(_process_prescan_batch, b): b for b in batches}

                while futures:
                    if stop_requested is not None and stop_requested():
                        logger.warning("Pre-scan AVT annulé pendant le calcul parallèle.")
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
                    logger.warning("Pre-scan AVT annule pendant le calcul des signaux.")
                    _write_prescan_report(output_dir, "cancelled", None, {})
                    return parameter_specs

                start_i = batch_idx * batch_size
                end_i = min(start_i + batch_size, len(combos))
                batch_combos = combos[start_i:end_i]

                batch_entries = {}
                batch_exits = {}

                for length, atr_len, atr_mult in batch_combos:
                    adaptive, er = adaptive_by_length[length]
                    line_delta = adaptive - adaptive.shift(1).fillna(adaptive)

                    atr_raw = atr_by_len[atr_len]
                    threshold = atr_raw * 0.05

                    # Trend direction vectorisé (équivalent à la logique Pine)
                    trend_dir = pd.Series(np.nan, index=data.index)
                    trend_dir[line_delta > threshold] = 1
                    trend_dir[line_delta < -threshold] = -1
                    trend_dir = trend_dir.ffill().fillna(0).astype(int)

                    is_bull = trend_dir == 1
                    is_bear = trend_dir == -1

                    prev_bull = is_bull.shift(1, fill_value=False)
                    prev_bear = is_bear.shift(1, fill_value=False)

                    trend_flip_bull = is_bull & (~prev_bull)
                    trend_flip_bear = is_bear & (~prev_bear)

                    price_above = source > adaptive
                    price_below = source < adaptive

                    entries = trend_flip_bull & price_above
                    exits = trend_flip_bear & price_below

                    col = (length, atr_len, atr_mult)
                    batch_entries[col] = entries
                    batch_exits[col] = exits

                entries_df = pd.DataFrame(batch_entries, index=data.index)
                exits_df = pd.DataFrame(batch_exits, index=data.index)

                pf = vbt.Portfolio.from_signals(
                    close, entries_df, exits_df, freq=f"{prescan_timeframe}min"
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

        # Récupère le Top 5% des combinaisons
        top_n = max(1, int(len(returns) * 0.05))
        top_params = returns.nlargest(top_n).index.tolist()

        if not top_params:
            _write_prescan_report(output_dir, "no_candidates", top_n, {})
            return parameter_specs

        min_len, max_len = min(p[0] for p in top_params), max(p[0] for p in top_params)
        min_atr_len, max_atr_len = min(p[1] for p in top_params), max(p[1] for p in top_params)
        min_atr_mult, max_atr_mult = min(p[2] for p in top_params), max(p[2] for p in top_params)

        # Marge de sécurité (+/- 10%)
        margin_len = max(1, int((max_len - min_len) * 0.1))
        margin_atr_len = max(1, int((max_atr_len - min_atr_len) * 0.1))
        margin_atr_mult = max(0.1, (max_atr_mult - min_atr_mult) * 0.1)

        min_len = max(int(length_specs.values[0]), min_len - margin_len)
        max_len = min(int(length_specs.values[-1]), max_len + margin_len)
        min_atr_len = max(int(atr_len_specs.values[0]), min_atr_len - margin_atr_len)
        max_atr_len = min(int(atr_len_specs.values[-1]), max_atr_len + margin_atr_len)
        min_atr_mult = max(float(atr_mult_specs.values[0]), min_atr_mult - margin_atr_mult)
        max_atr_mult = min(float(atr_mult_specs.values[-1]), max_atr_mult + margin_atr_mult)

        # Reconstruire ParameterGridSpec avec les nouvelles bornes
        new_specs = []
        len_filtered: tuple = ()
        atr_len_filtered: tuple = ()
        atr_mult_filtered: tuple = ()
        for s in parameter_specs:
            if s.name == "length":
                new_vals = tuple(v for v in s.values if min_len <= int(v) <= max_len)
                len_filtered = new_vals or s.values
                new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=len_filtered))
            elif s.name == "atr_len":
                new_vals = tuple(v for v in s.values if min_atr_len <= int(v) <= max_atr_len)
                atr_len_filtered = new_vals or s.values
                new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=atr_len_filtered))
            elif s.name == "atr_mult":
                new_vals = tuple(v for v in s.values if min_atr_mult <= float(v) <= max_atr_mult)
                atr_mult_filtered = new_vals or s.values
                new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=atr_mult_filtered))
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
                "atr_len": {
                    "original_bounds": [int(atr_len_specs.values[0]), int(atr_len_specs.values[-1])],
                    "new_bounds": [int(atr_len_filtered[0]), int(atr_len_filtered[-1])],
                    "filtered_values": list(atr_len_filtered),
                },
                "atr_mult": {
                    "original_bounds": [float(atr_mult_specs.values[0]), float(atr_mult_specs.values[-1])],
                    "new_bounds": [float(atr_mult_filtered[0]), float(atr_mult_filtered[-1])],
                    "filtered_values": list(atr_mult_filtered),
                },
            },
        )
        logger.info(
            f"Bornes Optuna réduites via VectorBT: "
            f"length({min_len}-{max_len}), atr_len({min_atr_len}-{max_atr_len}), "
            f"atr_mult({min_atr_mult:.1f}-{max_atr_mult:.1f})"
        )
        return new_specs

    except ImportError:
        _write_prescan_report(output_dir, "skipped", None, {})
        logger.warning("VectorBT n'est pas installé, impossible de lancer le pre-scan.")
    except Exception as e:
        _write_prescan_report(output_dir, "error", None, {})
        logger.warning(f"Erreur Pre-Scan VectorBT: {e}. Optuna utilisera les bornes globales.")

    _write_prescan_report(output_dir, "skipped", None, {})
    return parameter_specs
