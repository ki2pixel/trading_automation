from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib.util
from pathlib import Path
import sys
import threading
from types import ModuleType
from typing import Any

import pandas as pd

from ..metrics import MetricsInput, compute_metrics
from ..reports import BacktestRunResult
from ..configuration import coerce_strategy_parameters, load_strategy_config

STRATEGY_FILE = (
    Path(__file__).resolve().parents[2]
    / "pine_scripts_convert_to_python"
    / "strategy"
    / "Dual-RSI-DCA-Long-Strategy.py"
)
_MODULE_NAME = "converted_dual_rsi_dca_long"
_MODULE: ModuleType | None = None
_MODULE_LOCK = threading.Lock()

@dataclass
class DualRsiDcaLongConfigOverrides:
    base_order_size: float | None = None
    use_limit_base: bool | None = None
    ao_count: int | None = None
    ao_size: float | None = None
    ao_step: float | None = None
    ao_step_mult: float | None = None
    ao_size_mult: float | None = None
    entry_rsi_len: int | None = None
    entry_rsi_level: float | None = None
    exit_rsi_len: int | None = None
    exit_rsi_level: float | None = None
    min_profit_pct: float | None = None
    process_orders_on_close: bool | None = None

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

    # Common parameters mapped implicitly (used by metrics/costs, etc.)
    account_currency: str | None = None
    asset_currency: str | None = None
    fx_rate_provider: object | None = None
    early_stop_drawdown_pct: float | None = None

def dual_rsi_dca_long_overrides_from_mapping(values: dict[str, object] | None, *, ignore_unknown: bool = True) -> DualRsiDcaLongConfigOverrides:
    if not values:
        return DualRsiDcaLongConfigOverrides()
    coerced = coerce_strategy_parameters("dual_rsi_dca_long", values, ignore_unknown=ignore_unknown)
    allowed = set(DualRsiDcaLongConfigOverrides.__dataclass_fields__.keys())
    return DualRsiDcaLongConfigOverrides(**{key: value for key, value in coerced.items() if key in allowed})

def load_dual_rsi_dca_long_overrides_from_config(path: str | Path) -> tuple[DualRsiDcaLongConfigOverrides, dict[str, object]]:
    runtime_config = load_strategy_config(path, strategy="dual_rsi_dca_long")
    return dual_rsi_dca_long_overrides_from_mapping(runtime_config.parameters), runtime_config.backtest

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
        except Exception as exc:
            sys.modules.pop(spec.name, None)
            raise
        _MODULE = module
        return _MODULE

def _to_strategy_ohlcv(data: pd.DataFrame) -> pd.DataFrame:
    out = data.copy()
    for col in ["open", "high", "low", "close", "volume"]:
        if col not in out.columns:
            raise ValueError(f"Missing required column: {col}")
    return out[["open", "high", "low", "close", "volume"]].copy()

def _apply_overrides(config: Any, overrides: DualRsiDcaLongConfigOverrides) -> Any:
    for key, value in asdict(overrides).items():
        if value is not None and hasattr(config, key):
            setattr(config, key, value)
    return config

def run_dual_rsi_dca_long(
    data: pd.DataFrame,
    symbol: str,
    overrides: DualRsiDcaLongConfigOverrides | None = None,
    initial_capital: float = 10000.0,
    timeframe_minutes: int | str = 3,
    compute_full_metrics: bool = True,
    fast_score_metric: str | None = None,
    repo_root: Path | None = None,
) -> BacktestRunResult:
    from ._currency_utils import setup_currency_and_fx_provider

    overrides = overrides or DualRsiDcaLongConfigOverrides()
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
    config = module.DualRsiDcaLongConfig()
    config = _apply_overrides(config, overrides)

    bars = _to_strategy_ohlcv(data)
    metrics_result = module.run_dual_rsi_dca_long_strategy(
        bars, 
        config,
        compute_full_metrics=compute_full_metrics,
    )
    
    trades_raw = metrics_result.get('trades', [])
    closed_trades = [t for t in trades_raw if t.get('type') == 'close']
    trades = pd.DataFrame(closed_trades)
    
    if not trades.empty:
        if 'pnl' in trades.columns:
            trades.rename(columns={'pnl': 'net_pnl'}, inplace=True)
        else:
            trades['net_pnl'] = 0.0
        trades['side'] = 'long'
    else:
        trades = pd.DataFrame(columns=['net_pnl', 'side'])
        
    state = pd.DataFrame() # The state isn't exported directly but not strictly required for compute_metrics 
               # unless we have early_stop which this strategy currently delegates to custom logic

    if compute_full_metrics:
        metrics, equity_curve = compute_metrics(
            MetricsInput(
                symbol=symbol,
                strategy="dual_rsi_dca_long",
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
        strategy="dual_rsi_dca_long",
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
    import json
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


_worker_close = None
_worker_rsi_arr = None
_worker_rsi_lengths = None
_worker_time_indices = None
_worker_base_order_size = None
_worker_ao_count = None
_worker_ao_sizes = None
_worker_ao_thresholds = None
_worker_min_profit_pct = None


def _init_prescan_worker(close, rsi_arr, rsi_lengths, time_indices, base_size, ao_c, ao_s, ao_t, min_p):
    global _worker_close, _worker_rsi_arr, _worker_rsi_lengths, _worker_time_indices
    global _worker_base_order_size, _worker_ao_count, _worker_ao_sizes, _worker_ao_thresholds, _worker_min_profit_pct
    _worker_close = close
    _worker_rsi_arr = rsi_arr
    _worker_rsi_lengths = rsi_lengths
    _worker_time_indices = time_indices
    _worker_base_order_size = base_size
    _worker_ao_count = ao_c
    _worker_ao_sizes = ao_s
    _worker_ao_thresholds = ao_t
    _worker_min_profit_pct = min_p


def _process_prescan_batch(batch_combos):
    global _worker_close, _worker_rsi_arr, _worker_rsi_lengths, _worker_time_indices
    global _worker_base_order_size, _worker_ao_count, _worker_ao_sizes, _worker_ao_thresholds, _worker_min_profit_pct
    import pandas as pd
    import numpy as np

    mod = _load_strategy_module()
    _compute_dca_numba = mod._compute_dca_numba

    returns_batches = []
    rsi_len_to_idx = {l: i for i, l in enumerate(_worker_rsi_lengths)}

    for en_len, en_lvl, ex_len, ex_lvl in batch_combos:
        en_rsi = _worker_rsi_arr[:, rsi_len_to_idx[en_len]]
        ex_rsi = _worker_rsi_arr[:, rsi_len_to_idx[ex_len]]

        en_rsi_prev = np.empty_like(en_rsi)
        en_rsi_prev[0] = en_rsi[0]
        en_rsi_prev[1:] = en_rsi[:-1]

        ex_rsi_prev = np.empty_like(ex_rsi)
        ex_rsi_prev[0] = ex_rsi[0]
        ex_rsi_prev[1:] = ex_rsi[:-1]

        en_cross_up = (en_rsi_prev < en_lvl) & (en_rsi >= en_lvl)
        ex_cross_down = (ex_rsi_prev > ex_lvl) & (ex_rsi <= ex_lvl)

        realized_pnl, _ = _compute_dca_numba(
            _worker_close,
            en_cross_up,
            ex_cross_down,
            _worker_time_indices,
            _worker_base_order_size,
            _worker_ao_count,
            _worker_ao_sizes,
            _worker_ao_thresholds,
            _worker_min_profit_pct
        )

        returns_batches.append(((en_len, en_lvl, ex_len, ex_lvl), realized_pnl))

    return returns_batches


def vectorbt_prescan(
    data: pd.DataFrame,
    parameter_specs: list[Any],
    timeframe_minutes: int | str,
    output_dir: Path | None = None,
    stop_requested: Callable[[], bool] | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
    workers: int = 1,
) -> list[Any]:
    import logging
    import numpy as np
    from ..optimizer import ParameterGridSpec

    logger = logging.getLogger(__name__)

    if stop_requested is not None and stop_requested():
        _write_prescan_report(output_dir, "cancelled", None, {})
        return parameter_specs

    en_len_specs = next((s for s in parameter_specs if s.name == "entry_rsi_len"), None)
    en_lvl_specs = next((s for s in parameter_specs if s.name == "entry_rsi_level"), None)
    ex_len_specs = next((s for s in parameter_specs if s.name == "exit_rsi_len"), None)
    ex_lvl_specs = next((s for s in parameter_specs if s.name == "exit_rsi_level"), None)

    en_len_vals = list(en_len_specs.values) if (en_len_specs and en_len_specs.values) else [14]
    en_lvl_vals = list(en_lvl_specs.values) if (en_lvl_specs and en_lvl_specs.values) else [31.0]
    ex_len_vals = list(ex_len_specs.values) if (ex_len_specs and ex_len_specs.values) else [14]
    ex_lvl_vals = list(ex_lvl_specs.values) if (ex_lvl_specs and ex_lvl_specs.values) else [69.0]

    combos = [(en_l, en_v, ex_l, ex_v) for en_l in en_len_vals for en_v in en_lvl_vals for ex_l in ex_len_vals for ex_v in ex_lvl_vals]
    if len(combos) <= 1:
        _write_prescan_report(output_dir, "skipped", None, {})
        return parameter_specs

    try:
        import vectorbt as vbt
        import gc

        if len(data) > 150000:
            data = data.iloc[-150000:]

        close = data["close"].to_numpy(dtype=float)
        time_indices = np.arange(len(data), dtype=np.float64)

        all_rsi_lengths = sorted(list(set(en_len_vals + ex_len_vals)))
        all_rsi = vbt.RSI.run(data["close"], window=all_rsi_lengths)
        rsi_np = all_rsi.rsi.to_numpy(dtype=float)
        if rsi_np.ndim == 1:
            rsi_np = rsi_np.reshape(-1, 1)

        # DCA Parameters fixed for prescan based on standard defaults or parameter_specs if constant
        base_size = 90.0
        ao_count = 5
        ao_size = 110.0
        ao_step = 1.3
        ao_step_mult = 1.3
        ao_size_mult = 1.25
        min_profit_pct = 2.4
        
        # Check if specs have these fixed
        for s in parameter_specs:
            if s.name == "base_order_size" and s.values and len(s.values) == 1: base_size = float(s.values[0])
            if s.name == "ao_count" and s.values and len(s.values) == 1: ao_count = int(s.values[0])
            if s.name == "min_profit_pct" and s.values and len(s.values) == 1: min_profit_pct = float(s.values[0])

        ao_thresholds = np.zeros(ao_count + 1)
        ao_sizes = np.zeros(ao_count + 1)
        dev = 0.0
        step = ao_step
        for i in range(1, ao_count + 1):
            if i == 1: dev = step
            else:
                step = step * ao_step_mult
                dev += step
            ao_thresholds[i] = dev
            ao_sizes[i] = ao_size * (ao_size_mult ** (i - 1))

        BATCH_SIZE = max(1, 400 if workers == 1 else 100)
        total_batches = (len(combos) + BATCH_SIZE - 1) // BATCH_SIZE
        results = []

        if workers > 1:
            import multiprocessing
            try: ctx = multiprocessing.get_context("fork")
            except ValueError: ctx = multiprocessing.get_context()

            batches = [combos[i * BATCH_SIZE:(i + 1) * BATCH_SIZE] for i in range(total_batches)]
            
            import concurrent.futures
            with concurrent.futures.ProcessPoolExecutor(
                max_workers=workers,
                mp_context=ctx,
                initializer=_init_prescan_worker,
                initargs=(close, rsi_np, all_rsi_lengths, time_indices, base_size, ao_count, ao_sizes, ao_thresholds, min_profit_pct)
            ) as executor:
                completed = 0
                futures = {executor.submit(_process_prescan_batch, b): b for b in batches}
                while futures:
                    if stop_requested is not None and stop_requested():
                        for f in futures: f.cancel()
                        executor.shutdown(wait=False)
                        _write_prescan_report(output_dir, "cancelled", None, {})
                        return parameter_specs

                    done, _ = concurrent.futures.wait(futures.keys(), timeout=1.0, return_when=concurrent.futures.FIRST_COMPLETED)
                    for future in done:
                        try:
                            results.extend(future.result())
                        except Exception as e:
                            for f in futures: f.cancel()
                            executor.shutdown(wait=False)
                            raise RuntimeError(f"Pre-scan echoue: {e}") from e
                        del futures[future]
                        completed += 1
                        if progress_callback is not None:
                            try: progress_callback(completed, total_batches)
                            except Exception: pass
        else:
            _init_prescan_worker(close, rsi_np, all_rsi_lengths, time_indices, base_size, ao_count, ao_sizes, ao_thresholds, min_profit_pct)
            for batch_idx in range(total_batches):
                if stop_requested is not None and stop_requested():
                    _write_prescan_report(output_dir, "cancelled", None, {})
                    return parameter_specs
                start_i = batch_idx * BATCH_SIZE
                batch = combos[start_i:start_i + BATCH_SIZE]
                results.extend(_process_prescan_batch(batch))
                if progress_callback is not None:
                    try: progress_callback(batch_idx + 1, total_batches)
                    except Exception: pass

    except Exception as e:
        logger.warning(f"VectorBT Pre-scan err: {e}. Fallback to global bounds.")
        _write_prescan_report(output_dir, "error", None, {})
        return parameter_specs

    import pandas as pd
    df_res = pd.DataFrame(results, columns=["combo", "pnl"])
    df_res = df_res.sort_values(by="pnl", ascending=False)
    
    top_n = max(1, int(len(df_res) * 0.05))
    top_combos = df_res.head(top_n)["combo"].tolist()

    if not top_combos:
        _write_prescan_report(output_dir, "no_candidates", top_n, {})
        return parameter_specs

    min_en_l = min(c[0] for c in top_combos); max_en_l = max(c[0] for c in top_combos)
    min_en_v = min(c[1] for c in top_combos); max_en_v = max(c[1] for c in top_combos)
    min_ex_l = min(c[2] for c in top_combos); max_ex_l = max(c[2] for c in top_combos)
    min_ex_v = min(c[3] for c in top_combos); max_ex_v = max(c[3] for c in top_combos)

    def restrict(s_vals, mn, mx, is_float):
        v = sorted([float(x) for x in s_vals]) if is_float else sorted([int(x) for x in s_vals])
        margin = max(1.0 if is_float else 1, (mx - mn) * 0.1)
        return tuple(x for x in s_vals if (mn - margin) <= (float(x) if is_float else int(x)) <= (mx + margin))

    new_specs = []
    filtered_res = {}
    for s in parameter_specs:
        if s.name == "entry_rsi_len":
            nv = restrict(s.values, min_en_l, max_en_l, False) or s.values
            filtered_res["entry_rsi_len"] = list(nv)
            new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=nv))
        elif s.name == "entry_rsi_level":
            nv = restrict(s.values, min_en_v, max_en_v, True) or s.values
            filtered_res["entry_rsi_level"] = list(nv)
            new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=nv))
        elif s.name == "exit_rsi_len":
            nv = restrict(s.values, min_ex_l, max_ex_l, False) or s.values
            filtered_res["exit_rsi_len"] = list(nv)
            new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=nv))
        elif s.name == "exit_rsi_level":
            nv = restrict(s.values, min_ex_v, max_ex_v, True) or s.values
            filtered_res["exit_rsi_level"] = list(nv)
            new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=nv))
        else:
            new_specs.append(s)

    _write_prescan_report(output_dir, "success", top_n, filtered_res)
    return new_specs
