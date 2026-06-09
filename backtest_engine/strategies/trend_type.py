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
    / "trend_type_strategy.py"
)
_MODULE_NAME = "converted_trend_type_strategy"
_MODULE: ModuleType | None = None
_MODULE_LOCK = threading.Lock()


@dataclass
class TrendTypeConfigOverrides:
    use_atr: bool | None = None
    atr_len: int | None = None
    atr_ma_len: int | None = None
    use_adx: bool | None = None
    adx_len: int | None = None
    di_len: int | None = None
    adx_lim: float | None = None
    smooth: int | None = None
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


def trend_type_overrides_from_mapping(values: dict[str, object] | None, *, ignore_unknown: bool = True) -> TrendTypeConfigOverrides:
    if not values:
        return TrendTypeConfigOverrides()
    coerced = coerce_strategy_parameters("trend_type", values, ignore_unknown=ignore_unknown)
    allowed = set(TrendTypeConfigOverrides.__dataclass_fields__.keys())
    return TrendTypeConfigOverrides(**{key: value for key, value in coerced.items() if key in allowed})


def load_trend_type_overrides_from_config(path: str | Path) -> tuple[TrendTypeConfigOverrides, dict[str, object]]:
    runtime_config = load_strategy_config(path, strategy="trend_type")
    return trend_type_overrides_from_mapping(runtime_config.parameters), runtime_config.backtest


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


def _apply_overrides(config: Any, overrides: TrendTypeConfigOverrides) -> Any:
    for key, value in asdict(overrides).items():
        if value is not None and hasattr(config, key):
            setattr(config, key, value)
    return config


def run_trend_type(
    data: pd.DataFrame,
    symbol: str,
    overrides: TrendTypeConfigOverrides | None = None,
    initial_capital: float = 1000.0,
    timeframe_minutes: int | str = 5,
    compute_full_metrics: bool = True,
    fast_score_metric: str | None = None,
    repo_root: Path | None = None,
) -> BacktestRunResult:
    from ._currency_utils import setup_currency_and_fx_provider

    overrides = overrides or TrendTypeConfigOverrides()
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
    config = module.TrendTypeStrategyConfig()
    config = _apply_overrides(config, overrides)

    bars = _to_strategy_ohlcv(data)
    
    # Vectorized execution
    raw_state, _ = module.run_trend_type_strategy(bars, config)

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
                strategy="trend_type",
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
        strategy="trend_type",
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
    de Trend Type (atr_len, atr_ma_len, adx_len, di_len, adx_lim, smooth) 
    avec VectorBT pour restreindre les bornes d'exploration.
    """
    import logging
    import numpy as np
    from ..optimizer import ParameterGridSpec

    logger = logging.getLogger(__name__)

    if stop_requested is not None and stop_requested():
        logger.warning("Pre-scan Trend Type annulé avant démarrage.")
        _write_prescan_report(output_dir, "cancelled", None, {})
        return parameter_specs

    atr_specs = next((s for s in parameter_specs if s.name == "atr_len"), None)
    atr_ma_specs = next((s for s in parameter_specs if s.name == "atr_ma_len"), None)
    adx_specs = next((s for s in parameter_specs if s.name == "adx_len"), None)
    di_specs = next((s for s in parameter_specs if s.name == "di_len"), None)
    adx_lim_specs = next((s for s in parameter_specs if s.name == "adx_lim"), None)
    smooth_specs = next((s for s in parameter_specs if s.name == "smooth"), None)

    # Si certains paramètres clés manquent, on ignore le pre-scan
    if not all([atr_specs, atr_ma_specs, adx_specs, di_specs, adx_lim_specs]):
        _write_prescan_report(output_dir, "skipped", None, {})
        return parameter_specs
    if not all([s.values for s in [atr_specs, atr_ma_specs, adx_specs, di_specs, adx_lim_specs]]):
        _write_prescan_report(output_dir, "skipped", None, {})
        return parameter_specs

    try:
        import vectorbt as vbt
        import gc
        from ..indicators.trend_type import TrendType

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

        atr_lens = sorted({int(v) for v in atr_specs.values})
        atr_ma_lens = sorted({int(v) for v in atr_ma_specs.values})
        adx_lens = sorted({int(v) for v in adx_specs.values})
        di_lens = sorted({int(v) for v in di_specs.values})
        adx_lims = sorted({float(v) for v in adx_lim_specs.values})
        smooths = sorted({int(v) for v in smooth_specs.values}) if smooth_specs and smooth_specs.values else [3]

        from ..prescan_utils import downsample_parameter_grid
        downsampled = downsample_parameter_grid(
            {
                "atr_len": atr_lens,
                "atr_ma_len": atr_ma_lens,
                "adx_len": adx_lens,
                "di_len": di_lens,
                "adx_lim": adx_lims,
                "smooth": smooths,
            },
            max_combos=20000,
            strategy_name="TrendType"
        )
        atr_lens = downsampled["atr_len"]
        atr_ma_lens = downsampled["atr_ma_len"]
        adx_lens = downsampled["adx_len"]
        di_lens = downsampled["di_len"]
        adx_lims = downsampled["adx_lim"]
        smooths = downsampled["smooth"]

        # Generate combinations (filtrées pour s'assurer que atr_ma_len >= atr_len)
        combos = [
            (atr_l, atr_ma_l, adx_l, di_l, adx_lim, sm)
            for atr_l in atr_lens
            for atr_ma_l in atr_ma_lens
            if atr_ma_l >= atr_l
            for adx_l in adx_lens
            for di_l in di_lens
            for adx_lim in adx_lims
            for sm in smooths
        ]

        if not combos:
            # Fallback en cas de grille vide suite au filtre
            combos = [
                (atr_l, atr_ma_l, adx_l, di_l, adx_lim, sm)
                for atr_l in atr_lens
                for atr_ma_l in atr_ma_lens
                for adx_l in adx_lens
                for di_l in di_lens
                for adx_lim in adx_lims
                for sm in smooths
            ]

        # Simulation par lots séquentielle (très rapide et mémoire-safe)
        batch_size = 500
        total_batches = (len(combos) + batch_size - 1) // batch_size if combos else 0
        returns_batches: list[pd.Series] = []

        high = data["high"]
        low = data["low"]
        close = data["close"]

        logger.info(f"Lancement du Pre-Scan Trend Type en séquentiel ({len(combos)} combos, {total_batches} lots)...")

        for batch_idx in range(total_batches):
            if stop_requested is not None and stop_requested():
                logger.warning("Pre-scan Trend Type annulé pendant le calcul des signaux.")
                _write_prescan_report(output_dir, "cancelled", None, {})
                return parameter_specs

            start_i = batch_idx * batch_size
            end_i = min(start_i + batch_size, len(combos))
            batch_combos = combos[start_i:end_i]

            batch_atr_len = [c[0] for c in batch_combos]
            batch_atr_ma_len = [c[1] for c in batch_combos]
            batch_adx_len = [c[2] for c in batch_combos]
            batch_di_len = [c[3] for c in batch_combos]
            batch_adx_lim = [c[4] for c in batch_combos]
            batch_smooth = [c[5] for c in batch_combos]

            tt = TrendType.run(
                high, low, close,
                use_atr=True,
                atr_len=batch_atr_len,
                atr_ma_len=batch_atr_ma_len,
                use_adx=True,
                adx_len=batch_adx_len,
                di_len=batch_di_len,
                adx_lim=batch_adx_lim,
                smooth=batch_smooth,
                param_product=False
            )

            state = tt.state
            long_entries = (state == 2.0) & (state.shift(1) != 2.0)
            long_exits = (state != 2.0) & (state.shift(1) == 2.0)
            short_entries = (state == -2.0) & (state.shift(1) != -2.0)
            short_exits = (state != -2.0) & (state.shift(1) == -2.0)

            pf = vbt.Portfolio.from_signals(
                close,
                entries=long_entries,
                exits=long_exits,
                short_entries=short_entries,
                short_exits=short_exits,
                freq=f"{prescan_timeframe}min",
            )
            returns_batches.append(pf.total_return())

            # Libérer la RAM
            del tt
            del state
            del long_entries
            del long_exits
            del short_entries
            del short_exits
            del pf
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
            # Récupérer les valeurs des paramètres via leurs noms préfixés par TT_
            min_atr = min(p[1] for p in top_params)
            max_atr = max(p[1] for p in top_params)
            min_atr_ma = min(p[2] for p in top_params)
            max_atr_ma = max(p[2] for p in top_params)
            min_adx = min(p[4] for p in top_params)
            max_adx = max(p[4] for p in top_params)
            min_di = min(p[5] for p in top_params)
            max_di = max(p[5] for p in top_params)
            min_adx_lim = min(p[6] for p in top_params)
            max_adx_lim = max(p[6] for p in top_params)

            # Marge de sécurité (+/- 10%)
            margin_atr = max(1, int((max_atr - min_atr) * 0.1))
            margin_atr_ma = max(1, int((max_atr_ma - min_atr_ma) * 0.1))
            margin_adx = max(1, int((max_adx - min_adx) * 0.1))
            margin_di = max(1, int((max_di - min_di) * 0.1))
            margin_adx_lim = max(1.0, (max_adx_lim - min_adx_lim) * 0.1)

            min_atr = max(int(atr_specs.values[0]), min_atr - margin_atr)
            max_atr = min(int(atr_specs.values[-1]), max_atr + margin_atr)

            min_atr_ma = max(int(atr_ma_specs.values[0]), min_atr_ma - margin_atr_ma)
            max_atr_ma = min(int(atr_ma_specs.values[-1]), max_atr_ma + margin_atr_ma)

            min_adx = max(int(adx_specs.values[0]), min_adx - margin_adx)
            max_adx = min(int(adx_specs.values[-1]), max_adx + margin_adx)

            min_di = max(int(di_specs.values[0]), min_di - margin_di)
            max_di = min(int(di_specs.values[-1]), max_di + margin_di)

            min_adx_lim = max(float(adx_lim_specs.values[0]), min_adx_lim - margin_adx_lim)
            max_adx_lim = min(float(adx_lim_specs.values[-1]), max_adx_lim + margin_adx_lim)

            # Remplacement des spécifications pour Optuna
            new_specs = []
            atr_filtered = ()
            atr_ma_filtered = ()
            adx_filtered = ()
            di_filtered = ()
            adx_lim_filtered = ()

            for s in parameter_specs:
                if s.name == "atr_len":
                    new_vals = tuple(v for v in s.values if min_atr <= int(v) <= max_atr)
                    atr_filtered = new_vals or s.values
                    new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=atr_filtered))
                elif s.name == "atr_ma_len":
                    new_vals = tuple(v for v in s.values if min_atr_ma <= int(v) <= max_atr_ma)
                    atr_ma_filtered = new_vals or s.values
                    new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=atr_ma_filtered))
                elif s.name == "adx_len":
                    new_vals = tuple(v for v in s.values if min_adx <= int(v) <= max_adx)
                    adx_filtered = new_vals or s.values
                    new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=adx_filtered))
                elif s.name == "di_len":
                    new_vals = tuple(v for v in s.values if min_di <= int(v) <= max_di)
                    di_filtered = new_vals or s.values
                    new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=di_filtered))
                elif s.name == "adx_lim":
                    new_vals = tuple(v for v in s.values if min_adx_lim <= float(v) <= max_adx_lim)
                    adx_lim_filtered = new_vals or s.values
                    new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=adx_lim_filtered))
                else:
                    new_specs.append(s)

            _write_prescan_report(
                output_dir,
                "success",
                top_n,
                {
                    "atr_len": {
                        "original_bounds": [int(atr_specs.values[0]), int(atr_specs.values[-1])],
                        "new_bounds": [int(atr_filtered[0]), int(atr_filtered[-1])],
                        "filtered_values": list(atr_filtered),
                    },
                    "atr_ma_len": {
                        "original_bounds": [int(atr_ma_specs.values[0]), int(atr_ma_specs.values[-1])],
                        "new_bounds": [int(atr_ma_filtered[0]), int(atr_ma_filtered[-1])],
                        "filtered_values": list(atr_ma_filtered),
                    },
                    "adx_len": {
                        "original_bounds": [int(adx_specs.values[0]), int(adx_specs.values[-1])],
                        "new_bounds": [int(adx_filtered[0]), int(adx_filtered[-1])],
                        "filtered_values": list(adx_filtered),
                    },
                    "di_len": {
                        "original_bounds": [int(di_specs.values[0]), int(di_specs.values[-1])],
                        "new_bounds": [int(di_filtered[0]), int(di_filtered[-1])],
                        "filtered_values": list(di_filtered),
                    },
                    "adx_lim": {
                        "original_bounds": [float(adx_lim_specs.values[0]), float(adx_lim_specs.values[-1])],
                        "new_bounds": [float(adx_lim_filtered[0]), float(adx_lim_filtered[-1])],
                        "filtered_values": list(adx_lim_filtered),
                    },
                },
            )
            logger.info(
                f"Bornes Optuna réduites via VectorBT pour Trend Type : "
                f"atr_len({min_atr}-{max_atr}), "
                f"atr_ma_len({min_atr_ma}-{max_atr_ma}), "
                f"adx_len({min_adx}-{max_adx}), "
                f"di_len({min_di}-{max_di}), "
                f"adx_lim({min_adx_lim:.1f}-{max_adx_lim:.1f})"
            )
            return new_specs
        else:
            _write_prescan_report(output_dir, "no_candidates", top_n, {})
            return parameter_specs

    except ImportError:
        _write_prescan_report(output_dir, "skipped", None, {})
        logger.warning("VectorBT n'est pas installé, impossible de lancer le pre-scan.")
    except Exception as e:
        _write_prescan_report(output_dir, "error", None, {})
        logger.warning(f"Erreur Pre-Scan VectorBT Trend Type: {e}. Optuna utilisera les bornes globales.")

    _write_prescan_report(output_dir, "skipped", None, {})
    return parameter_specs

