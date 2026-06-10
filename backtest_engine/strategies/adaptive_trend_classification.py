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
import numpy as np

from ..metrics import MetricsInput, compute_metrics
from ..reports import BacktestRunResult
from ..configuration import coerce_strategy_parameters, load_strategy_config
from ..broker import BrokerSimulator, BrokerConfig, Order


STRATEGY_FILE = (
    Path(__file__).resolve().parents[2]
    / "pine_scripts_convert_to_python"
    / "strategy"
    / "adaptive_trend_classification_strategy.py"
)
_MODULE_NAME = "converted_adaptive_trend_classification_strategy"
_MODULE: ModuleType | None = None
_MODULE_LOCK = threading.Lock()


@dataclass
class AdaptiveTrendClassificationConfigOverrides:
    La: float | None = None
    De: float | None = None
    cutout: int | None = None
    robustness: str | None = None
    Long_threshold: float | None = None
    Short_threshold: float | None = None
    ema_len: int | None = None
    ema_w: float | None = None
    hull_len: int | None = None
    hma_w: float | None = None
    wma_len: int | None = None
    wma_w: float | None = None
    dema_len: int | None = None
    dema_w: float | None = None
    lsma_len: int | None = None
    lsma_w: float | None = None
    kama_len: int | None = None
    kama_w: float | None = None
    signal_mode: str | None = None
    
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


def adaptive_trend_classification_overrides_from_mapping(values: dict[str, object] | None, *, ignore_unknown: bool = True) -> AdaptiveTrendClassificationConfigOverrides:
    if not values:
        return AdaptiveTrendClassificationConfigOverrides()
    coerced = coerce_strategy_parameters("adaptive_trend_classification", values, ignore_unknown=ignore_unknown)
    allowed = set(AdaptiveTrendClassificationConfigOverrides.__dataclass_fields__.keys())
    return AdaptiveTrendClassificationConfigOverrides(**{key: value for key, value in coerced.items() if key in allowed})


def load_adaptive_trend_classification_overrides_from_config(path: str | Path) -> tuple[AdaptiveTrendClassificationConfigOverrides, dict[str, object]]:
    runtime_config = load_strategy_config(path, strategy="adaptive_trend_classification")
    return adaptive_trend_classification_overrides_from_mapping(runtime_config.parameters), runtime_config.backtest


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
        except Exception as exc:  # NOSONAR
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


def _normalize_trades(trades: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame(columns=[
            "entry_index", "exit_index", "side", "qty", "entry_price",
            "exit_price", "gross_pnl", "estimated_costs", "net_pnl",
            "bars_held", "exit_comment",
        ])

    out = trades.copy()
    out = out.rename(columns={
        "entry_time": "entry_index",
        "exit_time": "exit_index",
        "quantity": "qty",
        "commission": "estimated_costs",
    })

    bar_positions = pd.Series(
        np.arange(len(bars), dtype=np.int64), index=bars.index,
    )
    entry_pos = out["entry_index"].map(bar_positions)
    exit_pos = out["exit_index"].map(bar_positions)
    out["bars_held"] = (exit_pos - entry_pos).astype(float)

    for col in [
        "entry_index", "exit_index", "side", "qty", "entry_price",
        "exit_price", "gross_pnl", "estimated_costs", "net_pnl",
        "bars_held", "exit_comment",
    ]:
        if col not in out.columns:
            out[col] = np.nan

    return out[[
        "entry_index", "exit_index", "side", "qty", "entry_price",
        "exit_price", "gross_pnl", "estimated_costs", "net_pnl",
        "bars_held", "exit_comment",
    ]]


def _build_state_from_broker(
    broker: BrokerSimulator,
    bars: pd.DataFrame,
    timestamps: pd.DatetimeIndex,
    close_arr: np.ndarray,
) -> pd.DataFrame:
    n = len(bars)
    realized = np.zeros(n, dtype=np.float64)
    open_pnl = np.zeros(n, dtype=np.float64)
    pos_size = np.zeros(n, dtype=np.float64)
    pos_avg = np.zeros(n, dtype=np.float64)

    bar_positions = pd.Series(np.arange(n, dtype=np.int64), index=timestamps)
    for ct in broker.closed_trades:
        exit_ts = ct.exit_time
        if exit_ts in bar_positions.index:
            idx = bar_positions[exit_ts]
            realized[idx] += ct.net_pnl

    fill_by_bar: dict[object, list] = {}
    for fill in broker.fills:
        fill_by_bar.setdefault(fill.timestamp, []).append(fill)

    cur_qty = 0.0
    cur_avg = 0.0
    last_idx = 0
    pos_qty = np.zeros(n, dtype=np.float64)

    fill_indices = [bar_positions.get(ts, -1) for ts in fill_by_bar.keys()]
    fill_indices = sorted([i for i in fill_indices if i != -1])

    for idx in fill_indices:
        if idx > last_idx:
            pos_qty[last_idx:idx] = cur_qty
            pos_avg[last_idx:idx] = cur_avg
        ts = timestamps[idx]
        for fill in fill_by_bar[ts]:
            delta = fill.signed_quantity
            new_qty = cur_qty + delta
            if cur_qty == 0 or cur_qty * delta > 0:
                total = abs(cur_qty) + abs(delta)
                if total > 0:
                    cur_avg = (abs(cur_qty) * cur_avg + abs(delta) * fill.price) / total
                cur_qty = new_qty
            else:
                if new_qty == 0:
                    cur_qty = 0.0
                    cur_avg = 0.0
                elif cur_qty * new_qty > 0:
                    cur_qty = new_qty
                else:
                    cur_qty = new_qty
                    cur_avg = fill.price
        pos_qty[idx] = cur_qty
        pos_avg[idx] = cur_avg
        last_idx = idx + 1

    if last_idx < n:
        pos_qty[last_idx:n] = cur_qty
        pos_avg[last_idx:n] = cur_avg

    pos_size[:] = np.abs(pos_qty)

    mask = (pos_qty != 0) & (pos_avg > 0)
    if mask.any():
        active_indices = np.where(mask)[0]
        if broker.config.asset_currency == broker.config.account_currency:
            price_account = close_arr[active_indices]
        else:
            fx_arr = np.array([broker.fx_rate(timestamps[idx]) for idx in active_indices])
            price_account = close_arr[active_indices] * fx_arr
        
        side_mult = np.sign(pos_qty[active_indices])
        open_pnl[active_indices] = (price_account - pos_avg[active_indices]) * np.abs(pos_qty[active_indices]) * side_mult * broker.config.point_value

    state = pd.DataFrame(
        {
            "realized_net_pnl_on_fill": realized,
            "estimated_net_if_closed_now": open_pnl,
            "position_abs_size": pos_size,
            "position_avg_price": pos_avg,
        },
        index=timestamps,
    )
    return state


def _apply_overrides(config: Any, overrides: AdaptiveTrendClassificationConfigOverrides) -> Any:
    for key, value in asdict(overrides).items():
        if value is not None and hasattr(config, key):
            setattr(config, key, value)
    return config


def run_adaptive_trend_classification(
    data: pd.DataFrame,
    symbol: str,
    overrides: AdaptiveTrendClassificationConfigOverrides | None = None,
    initial_capital: float = 1000.0,
    timeframe_minutes: int | str = 5,
    compute_full_metrics: bool = True,
    fast_score_metric: str | None = None,
    repo_root: Path | None = None,
) -> BacktestRunResult:
    from ._currency_utils import setup_currency_and_fx_provider

    overrides = overrides or AdaptiveTrendClassificationConfigOverrides()
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
    config = module.AdaptiveTrendClassificationStrategyConfig()
    config = _apply_overrides(config, overrides)

    bars = _to_strategy_ohlcv(data)
    
    # Vectorized execution
    raw_state, _ = module.run_adaptive_trend_classification_strategy(bars, config)

    entries_long = bars['long_entry'].fillna(False).to_numpy()
    entries_short = bars['short_entry'].fillna(False).to_numpy()
    exits_long = bars['long_exit'].fillna(False).to_numpy()
    exits_short = bars['short_exit'].fillna(False).to_numpy()

    direction = overrides.trade_direction_mode or "Long & Short"
    allow_long = direction in ("Long & Short", "Long only")
    allow_short = direction in ("Long & Short", "Short only")

    exec_col = overrides.next_bar_execution_price_col or "open"
    broker_config = BrokerConfig(
        initial_capital=initial_capital,
        execute_on_next_bar=overrides.execute_on_next_bar if overrides.execute_on_next_bar is not None else True,
        execution_price_col=exec_col,
        commission_fixed_long=overrides.estimated_commission_per_order_long,
        commission_fixed_short=overrides.estimated_commission_per_order_short,
        slippage_per_side_long=overrides.estimated_slippage_per_side_long if overrides.estimated_slippage_per_side_long is not None else 0.0,
        slippage_per_side_short=overrides.estimated_slippage_per_side_short if overrides.estimated_slippage_per_side_short is not None else 0.0,
        point_value=overrides.point_value if overrides.point_value is not None else 1.0,
        allow_fractional_quantity=overrides.allow_fractional_quantity if overrides.allow_fractional_quantity is not None else True,
        quantity_precision=overrides.quantity_precision,
        account_currency=account_currency if account_currency is not None else "EUR",
        asset_currency=asset_currency if asset_currency is not None else "EUR",
        fx_rate_provider=fx_rate_provider,
    )
    broker = BrokerSimulator(broker_config)

    # Exit rules
    exit_rules = []
    if overrides.use_net_bracket_exits:
        from ..broker import NetBracketExitRule
        exit_rules.append(NetBracketExitRule(
            broker,
            tp_pct=overrides.take_profit_net_percent,
            sl_pct=overrides.stop_loss_net_percent,
        ))
    if overrides.use_safety_stop if overrides.use_safety_stop is not None else False:
        from ..broker import SafetyStopExitRule
        exit_rules.append(SafetyStopExitRule(
            broker,
            applies_to=overrides.safety_stop_applies_to or "Both",
            mode=overrides.safety_stop_mode or "Net loss only",
            max_loss_mode=overrides.safety_max_net_loss_mode or "Cash amount",
            max_loss_cash=overrides.safety_max_net_loss_cash,
            max_loss_pct=overrides.safety_max_net_loss_percent,
            max_bars=overrides.safety_max_bars_in_trade or 0,
        ))
    if exit_rules:
        from ..broker import ExitOrchestrator
        broker.exit_orchestrator = ExitOrchestrator(exit_rules)

    timestamps = bars.index
    ts_arr = timestamps.to_pydatetime()
    exec_arr = bars[exec_col].to_numpy(dtype=np.float64) if exec_col in bars.columns else bars["open"].to_numpy(dtype=np.float64)
    open_arr = bars["open"].to_numpy(dtype=np.float64)
    high_arr = bars["high"].to_numpy(dtype=np.float64)
    low_arr = bars["low"].to_numpy(dtype=np.float64)
    close_arr = bars["close"].to_numpy(dtype=np.float64)
    n_bars = len(bars)

    drawdown_limit = overrides.early_stop_drawdown_pct
    check_drawdown = drawdown_limit is not None and drawdown_limit > 0
    peak_equity = initial_capital
    order_counter = 0

    if not allow_long:
        entries_long[:] = False
    if not allow_short:
        entries_short[:] = False

    pending_signal: str | None = None

    for i in range(n_bars):
        ts = ts_arr[i]
        exec_price = float(exec_arr[i])

        if pending_signal is not None and broker_config.execute_on_next_bar:
            if pending_signal == "long" and allow_long:
                if broker.position.is_flat or broker.position.signed_quantity < 0:
                    if broker.position.signed_quantity < 0:
                        qty = abs(broker.position.signed_quantity)
                        order_counter += 1
                        broker.fill_order(
                            Order(id=f"exit_short_{order_counter}", side="buy", quantity=qty,
                                  comment="Exit Short", cost_side="short"),
                            ts, exec_price,
                        )
                    qty = broker.calculate_position_size(exec_price, broker.cash, timestamp=ts)
                    qty = broker.normalize_quantity(qty)
                    if qty > 0:
                        order_counter += 1
                        broker.fill_order(
                            Order(id=f"entry_long_{order_counter}", side="buy", quantity=qty,
                                  comment="Entry Long", cost_side="long"),
                            ts, exec_price,
                        )
            elif pending_signal == "short" and allow_short:
                if broker.position.is_flat or broker.position.signed_quantity > 0:
                    if broker.position.signed_quantity > 0:
                        qty = abs(broker.position.signed_quantity)
                        order_counter += 1
                        broker.fill_order(
                            Order(id=f"exit_long_{order_counter}", side="sell", quantity=qty,
                                  comment="Exit Long", cost_side="long"),
                            ts, exec_price,
                        )
                    qty = broker.calculate_position_size(exec_price, broker.cash, timestamp=ts)
                    qty = broker.normalize_quantity(qty)
                    if qty > 0:
                        order_counter += 1
                        broker.fill_order(
                            Order(id=f"entry_short_{order_counter}", side="sell", quantity=qty,
                                  comment="Entry Short", cost_side="short"),
                            ts, exec_price,
                        )
            elif pending_signal == "exit_long":
                if broker.position.signed_quantity > 0:
                    qty = abs(broker.position.signed_quantity)
                    order_counter += 1
                    broker.fill_order(
                        Order(id=f"exit_long_{order_counter}", side="sell", quantity=qty,
                              comment="Exit Long", cost_side="long"),
                        ts, exec_price,
                    )
            elif pending_signal == "exit_short":
                if broker.position.signed_quantity < 0:
                    qty = abs(broker.position.signed_quantity)
                    order_counter += 1
                    broker.fill_order(
                        Order(id=f"exit_short_{order_counter}", side="buy", quantity=qty,
                              comment="Exit Short", cost_side="short"),
                        ts, exec_price,
                    )
            pending_signal = None

        if not broker.position.is_flat and broker.exit_orchestrator is not None:
            bar_dict = {
                "timestamp": ts,
                "open": float(open_arr[i]),
                "high": float(high_arr[i]),
                "low": float(low_arr[i]),
                "close": float(close_arr[i]),
            }
            broker.evaluate_exits(bar_dict)

        if entries_long[i]:
            pending_signal = "long"
        elif entries_short[i]:
            pending_signal = "short"
        elif exits_long[i]:
            pending_signal = "exit_long"
        elif exits_short[i]:
            pending_signal = "exit_short"

        if check_drawdown:
            equity = broker.cash if broker.position.is_flat else broker.mark_to_market_equity(float(close_arr[i]), ts)
            if equity > peak_equity:
                peak_equity = equity
            if peak_equity > 0:
                dd_pct = (peak_equity - equity) / peak_equity * 100.0
                if dd_pct >= drawdown_limit:
                    break

    raw_trades = broker.closed_trades_frame()
    trades = _normalize_trades(raw_trades, bars)
    state = _build_state_from_broker(broker, bars, timestamps, close_arr)

    if compute_full_metrics:
        metrics, equity_curve = compute_metrics(
            MetricsInput(
                symbol=symbol,
                strategy="adaptive_trend_classification",
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
        strategy="adaptive_trend_classification",
        symbol=symbol,
        config=config.model_dump() if hasattr(config, "model_dump") else (config.dict() if hasattr(config, "dict") else asdict(config)),
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


# Globals for multiprocessing workers
_worker_close = None

def _init_prescan_worker(close):
    global _worker_close
    _worker_close = close

def _process_prescan_batch(args):
    global _worker_close
    import pandas as pd
    import numpy as np
    import vectorbt as vbt
    from ..indicators.adaptive_trend_classification import AdaptiveTrend

    batch_combos, keys, rob_val, prescan_timeframe = args

    batch_vals = list(zip(*batch_combos))
    run_kwargs = {keys[i]: list(batch_vals[i]) for i in range(len(keys))}
    run_kwargs["robustness"] = [rob_val] * len(batch_combos)
    run_kwargs["param_product"] = False

    at = AdaptiveTrend.run(_worker_close, **run_kwargs)
    direction = at.direction
    long_entries = (direction == 1.0) & (direction.shift(1) != 1.0)
    short_entries = (direction == -1.0) & (direction.shift(1) != -1.0)
    long_exits = short_entries
    short_exits = long_entries

    pf = vbt.Portfolio.from_signals(
        _worker_close,
        entries=long_entries,
        exits=long_exits,
        short_entries=short_entries,
        short_exits=short_exits,
        freq=f"{prescan_timeframe}min",
    )
    
    ret_series = pf.total_return()
    if not isinstance(ret_series, pd.Series):
        ret_series = pd.Series([ret_series], index=[(rob_val,) + batch_combos[0]])
    else:
        ret_series.index = [(rob_val,) + combo for combo in batch_combos]

    return pd.Series(ret_series.values, index=ret_series.index)


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
    de Adaptive Trend Classification avec VectorBT pour restreindre les bornes d'exploration.
    """
    import logging
    import itertools
    import numpy as np
    from ..optimizer import ParameterGridSpec
    import gc

    logger = logging.getLogger(__name__)

    if stop_requested is not None and stop_requested():
        logger.warning("Pre-scan Adaptive Trend annulé avant démarrage.")
        _write_prescan_report(output_dir, "cancelled", None, {})
        return parameter_specs

    param_defaults = {
        "La": 0.02,
        "De": 0.03,
        "cutout": 0,
        "robustness": "Medium",
        "Long_threshold": 0.1,
        "Short_threshold": -0.1,
        "ema_len": 28,
        "ema_w": 1.0,
        "hull_len": 28,
        "hma_w": 1.0,
        "wma_len": 28,
        "wma_w": 1.0,
        "dema_len": 28,
        "dema_w": 1.0,
        "lsma_len": 28,
        "lsma_w": 1.0,
        "kama_len": 28,
        "kama_w": 1.0,
    }

    # Vérifier s'il y a des paramètres spécifiés
    has_active = False
    for spec in parameter_specs:
        if spec.name in param_defaults and spec.values:
            has_active = True
            break

    if not has_active:
        _write_prescan_report(output_dir, "skipped", None, {})
        return parameter_specs

    try:
        import vectorbt as vbt
        from ..indicators.adaptive_trend_classification import AdaptiveTrend

        # 1. Temporal Downsampling
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

        # Slice limit (150k bars)
        if len(data) > 150000:
            logger.info(f"Slicing data from {len(data)} to 150000 bars for fast pre-scan processing.")
            data = data.iloc[-150000:]

        active_params = {}
        for name, default in param_defaults.items():
            spec = next((s for s in parameter_specs if s.name == name), None)
            if spec and spec.values:
                if isinstance(default, int):
                    active_params[name] = sorted({int(v) for v in spec.values})
                elif isinstance(default, float):
                    active_params[name] = sorted({float(v) for v in spec.values})
                else:
                    active_params[name] = sorted({str(v) for v in spec.values})
            else:
                active_params[name] = [default]

        robs = active_params.pop("robustness")

        from ..prescan_utils import downsample_parameter_grid
        downsampled = downsample_parameter_grid(
            active_params,
            max_combos=10000,
            strategy_name="AdaptiveTrend"
        )
        for name, values in downsampled.items():
            active_params[name] = values

        keys = list(active_params.keys())
        vals_lists = [active_params[k] for k in keys]
        combos_numeric = list(itertools.product(*vals_lists))

        # Simulation par lots
        batch_size = 500
        total_batches = (len(combos_numeric) + batch_size - 1) // batch_size if combos_numeric else 0
        returns_batches: list[pd.Series] = []

        close = data["close"]

        # Multiprocessing Parallelization
        if workers > 1:
            logger.info(f"Lancement du Pre-Scan Adaptive Trend en parallèle avec {workers} processus (Batch Size={batch_size})...")
            import multiprocessing
            import concurrent.futures

            try:
                ctx = multiprocessing.get_context("fork")
            except ValueError:
                ctx = multiprocessing.get_context()

            batches = []
            for rob_val in robs:
                for batch_idx in range(total_batches):
                    start_i = batch_idx * batch_size
                    end_i = min(start_i + batch_size, len(combos_numeric))
                    batch_combos = combos_numeric[start_i:end_i]
                    batches.append((batch_combos, keys, rob_val, prescan_timeframe))

            with concurrent.futures.ProcessPoolExecutor(
                max_workers=workers,
                mp_context=ctx,
                initializer=_init_prescan_worker,
                initargs=(close,)
            ) as executor:
                futures = {executor.submit(_process_prescan_batch, b): b for b in batches}
                completed = 0
                total_runs = len(batches)

                while futures:
                    if stop_requested is not None and stop_requested():
                        logger.warning("Pre-scan Adaptive Trend Classification annulé pendant le calcul parallèle.")
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
                                progress_callback(completed, total_runs)
                            except Exception as cb_err:
                                logger.warning(f"Error in prescan progress callback: {cb_err}")
        else:
            logger.info(f"Lancement du Pre-Scan Adaptive Trend en séquentiel (Batch Size={batch_size})...")
            total_runs = len(robs) * total_batches
            run_count = 0

            for rob_val in robs:
                for batch_idx in range(total_batches):
                    if stop_requested is not None and stop_requested():
                        logger.warning("Pre-scan Adaptive Trend Classification annulé.")
                        _write_prescan_report(output_dir, "cancelled", None, {})
                        return parameter_specs

                    start_i = batch_idx * batch_size
                    end_i = min(start_i + batch_size, len(combos_numeric))
                    batch_combos = combos_numeric[start_i:end_i]

                    batch_vals = list(zip(*batch_combos))
                    run_kwargs = {keys[i]: list(batch_vals[i]) for i in range(len(keys))}
                    run_kwargs["robustness"] = [rob_val] * len(batch_combos)
                    run_kwargs["param_product"] = False

                    at = AdaptiveTrend.run(close, **run_kwargs)
                    direction = at.direction
                    long_entries = (direction == 1.0) & (direction.shift(1) != 1.0)
                    short_entries = (direction == -1.0) & (direction.shift(1) != -1.0)
                    long_exits = short_entries
                    short_exits = long_entries

                    pf = vbt.Portfolio.from_signals(
                        close,
                        entries=long_entries,
                        exits=long_exits,
                        short_entries=short_entries,
                        short_exits=short_exits,
                        freq=f"{prescan_timeframe}min",
                    )
                    
                    ret_series = pf.total_return()
                    if not isinstance(ret_series, pd.Series):
                        ret_series = pd.Series([ret_series], index=[0])
                    else:
                        ret_series.index = list(range(len(ret_series)))

                    ret_series.index = [(rob_val,) + combo for combo in batch_combos]
                    returns_batches.append(pd.Series(ret_series.values, index=ret_series.index))

                    del at
                    del direction
                    del long_entries
                    del short_entries
                    del long_exits
                    del short_exits
                    del pf
                    gc.collect()

                    run_count += 1
                    if progress_callback is not None:
                        try:
                            progress_callback(run_count, total_runs)
                        except Exception as cb_err:
                            logger.warning(f"Error in prescan progress callback: {cb_err}")

        if returns_batches:
            returns = pd.concat(returns_batches)
            returns = returns.sort_index()
        else:
            returns = pd.Series(dtype=float)

        top_n = max(1, int(len(returns) * 0.05))
        top_params = returns.nlargest(top_n).index.tolist()

        if top_params:
            filtered_by_param = {"robustness": set()}
            for k in keys:
                filtered_by_param[k] = set()

            for p in top_params:
                filtered_by_param["robustness"].add(p[0])
                for i, k in enumerate(keys):
                    filtered_by_param[k].add(p[i+1])

            # Apply margins and reconstruct specs
            new_specs = []
            report_params = {}

            # Restauration de robustness dans keys pour reconstruire le rapport
            all_keys_with_rob = ["robustness"] + keys
            for s in parameter_specs:
                if s.name == "robustness":
                    new_vals = tuple(v for v in s.values if v in filtered_by_param["robustness"])
                    tf_filtered = new_vals or s.values
                    new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=tf_filtered))
                    report_params["robustness"] = {
                        "original_values": list(s.values),
                        "filtered_values": list(tf_filtered),
                    }
                elif s.name in keys:
                    vals = sorted(list(filtered_by_param[s.name]))
                    min_v = vals[0]
                    max_v = vals[-1]
                    default_def = param_defaults[s.name]
                    if isinstance(default_def, int):
                        margin = max(1, int((max_v - min_v) * 0.1))
                        min_v = max(int(s.values[0]), int(min_v) - margin)
                        max_v = min(int(s.values[-1]), int(max_v) + margin)
                        new_vals = tuple(v for v in s.values if min_v <= int(v) <= max_v)
                    else:
                        margin = max(0.001, (max_v - min_v) * 0.1)
                        min_v = max(float(s.values[0]), float(min_v) - margin)
                        max_v = min(float(s.values[-1]), float(max_v) + margin)
                        new_vals = tuple(v for v in s.values if min_v <= float(v) <= max_v)
                    
                    filtered_res = new_vals or s.values
                    new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=filtered_res))
                    report_params[s.name] = {
                        "original_bounds": [s.values[0], s.values[-1]],
                        "new_bounds": [filtered_res[0], filtered_res[-1]],
                        "filtered_values": list(filtered_res),
                    }
                else:
                    new_specs.append(s)

            _write_prescan_report(output_dir, "success", top_n, report_params)
            logger.info(f"Bornes Optuna réduites via VectorBT pour Adaptive Trend Classification.")
            return new_specs

    except Exception as e:
        logger.warning(f"Erreur Pre-Scan VectorBT Adaptive Trend: {e}")

    _write_prescan_report(output_dir, "skipped", None, {})
    return parameter_specs
