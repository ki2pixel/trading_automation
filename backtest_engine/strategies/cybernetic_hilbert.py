"""
backtest_engine/strategies/cybernetic_hilbert.py

Cybernetic Hilbert Transform trading strategy.

Implements Ehlers' Hilbert Transform-based signal crossover logic:
  * **Buy** when Lead Wave crosses below Sine Wave (bottom detection).
  * **Sell** when Lead Wave crosses above Sine Wave (top detection).
  * **Phase Mode filter** gates trades to the *Cycling* regime only.

Follows the established strategy-module pattern (see ``hma_crossover.py``,
``adaptive_volatility_trend.py``) and plugs into ``BrokerSimulator``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from ..metrics import MetricsInput, compute_metrics
from ..reports import BacktestRunResult
from ..configuration import coerce_strategy_parameters, load_strategy_config
from ..broker import BrokerSimulator, BrokerConfig, Order

# ---------------------------------------------------------------------------
# Shared-memory globals (mounted by shm_allocators / worker init)
# ---------------------------------------------------------------------------
_SHARED_HILBERT_GRID: np.ndarray | None = None
_SHARED_HILBERT_KEYS: dict[int, int] | None = None


# ---------------------------------------------------------------------------
# ConfigOverrides dataclass
# ---------------------------------------------------------------------------

@dataclass
class CyberneticHilbertConfigOverrides:
    # ── Hilbert-specific indicator parameters ──
    hilbert_smooth_period: int | None = None
    phase_mode_enabled: bool | None = None
    require_cycling_bars: int | None = None
    # ── V3 common parameters ──
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


# ---------------------------------------------------------------------------
# Overrides helpers (registry pattern)
# ---------------------------------------------------------------------------

def cybernetic_hilbert_overrides_from_mapping(
    values: dict[str, object] | None,
    *,
    ignore_unknown: bool = True,
) -> CyberneticHilbertConfigOverrides:
    if not values:
        return CyberneticHilbertConfigOverrides()
    coerced = coerce_strategy_parameters(
        "cybernetic_hilbert", values, ignore_unknown=ignore_unknown,
    )
    allowed = set(CyberneticHilbertConfigOverrides.__dataclass_fields__.keys())
    return CyberneticHilbertConfigOverrides(
        **{key: value for key, value in coerced.items() if key in allowed},
    )


def load_cybernetic_hilbert_overrides_from_config(
    path: str | Path,
) -> tuple[CyberneticHilbertConfigOverrides, dict[str, object]]:
    runtime_config = load_strategy_config(path, strategy="cybernetic_hilbert")
    return (
        cybernetic_hilbert_overrides_from_mapping(runtime_config.parameters),
        runtime_config.backtest,
    )


# ---------------------------------------------------------------------------
# Signal generation
# ---------------------------------------------------------------------------

def _get_hilbert_arrays(
    close: np.ndarray,
    hilbert_smooth_period: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return (sine_wave, lead_wave, dominant_cycle, phase_mode).

    Uses the shared-memory grid when available (Optuna workers), otherwise
    computes on the fly via the Numba JIT core.
    """
    global _SHARED_HILBERT_GRID, _SHARED_HILBERT_KEYS

    if _SHARED_HILBERT_GRID is not None and _SHARED_HILBERT_KEYS is not None:
        idx = _SHARED_HILBERT_KEYS.get(int(hilbert_smooth_period))
        if idx is not None:
            grid = _SHARED_HILBERT_GRID
            return grid[idx, 0], grid[idx, 1], grid[idx, 2], grid[idx, 3]

    # Fallback: compute on the fly
    from ..indicators.hilbert_transform import hilbert_transform_ehlers

    result = hilbert_transform_ehlers(close, smooth_period_factor=hilbert_smooth_period)
    return (
        result["sine_wave"],
        result["lead_wave"],
        result["dominant_cycle"],
        result["phase_mode"],
    )


def _generate_signals(
    close: np.ndarray,
    hilbert_smooth_period: int = 7,
    phase_mode_enabled: bool = True,
    require_cycling_bars: int = 1,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Generate entry/exit boolean arrays from Hilbert crossover logic.

    Returns
    -------
    tuple of four np.ndarray (bool)
        ``(entries_long, exits_long, entries_short, exits_short)``
    """
    sine, lead, _, pm = _get_hilbert_arrays(close, hilbert_smooth_period)
    n = len(close)

    # Lead Wave crosses below Sine Wave → buy signal (bottom detection)
    cross_below = (lead[:-1] >= sine[:-1]) & (lead[1:] < sine[1:])
    # Lead Wave crosses above Sine Wave → sell signal (top detection)
    cross_above = (lead[:-1] <= sine[:-1]) & (lead[1:] > sine[1:])

    # Pad to match original length (first element is False)
    cross_below = np.concatenate(([False], cross_below))
    cross_above = np.concatenate(([False], cross_above))

    if phase_mode_enabled:
        if require_cycling_bars <= 1:
            cycling_ok = (pm == 1.0)
        else:
            # Vectorized rolling consecutive check using pandas
            cycling_ok = pd.Series(pm).rolling(require_cycling_bars).sum() == require_cycling_bars
            cycling_ok = cycling_ok.fillna(False).to_numpy()
    else:
        cycling_ok = np.ones(n, dtype=bool)

    entries_long = cross_below & cycling_ok
    exits_short = cross_below & cycling_ok
    entries_short = cross_above & cycling_ok
    exits_long = cross_above & cycling_ok

    return entries_long, exits_long, entries_short, exits_short


# ---------------------------------------------------------------------------
# OHLCV validation
# ---------------------------------------------------------------------------

def _to_strategy_ohlcv(data: pd.DataFrame) -> pd.DataFrame:
    out = data.copy()
    for col in ["open", "high", "low", "close", "volume"]:
        if col not in out.columns:
            raise ValueError(f"Missing required column: {col}")
    return out[["open", "high", "low", "close", "volume"]].copy()


# ---------------------------------------------------------------------------
# Trade normalization (BrokerSimulator → compute_metrics format)
# ---------------------------------------------------------------------------

def _normalize_trades(trades: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    """Adapt broker.closed_trades_frame() to the format expected by compute_metrics."""
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

    # Compute bars_held from index positions
    bar_positions = pd.Series(
        np.arange(len(bars), dtype=np.int64), index=bars.index,
    )
    entry_pos = out["entry_index"].map(bar_positions)
    exit_pos = out["exit_index"].map(bar_positions)
    out["bars_held"] = (exit_pos - entry_pos).astype(float)

    # Ensure all expected columns exist
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


# ---------------------------------------------------------------------------
# State DataFrame builder (BrokerSimulator → compute_metrics format)
# ---------------------------------------------------------------------------

def _build_state_from_broker(
    broker: BrokerSimulator,
    bars: pd.DataFrame,
    timestamps: pd.DatetimeIndex,
    close_arr: np.ndarray,
) -> pd.DataFrame:
    """Build a state DataFrame from the broker's fills and closed trades.

    ``compute_metrics`` requires columns:
      - ``realized_net_pnl_on_fill``: net PnL booked on each bar where a trade closes
      - ``estimated_net_if_closed_now``: unrealized PnL at each bar's close
      - ``position_abs_size``: absolute position size
      - ``position_avg_price``: entry average price
    """
    n = len(bars)
    realized = np.zeros(n, dtype=np.float64)
    open_pnl = np.zeros(n, dtype=np.float64)
    pos_size = np.zeros(n, dtype=np.float64)
    pos_avg = np.zeros(n, dtype=np.float64)

    # Map closed trades to bar indices
    bar_positions = pd.Series(np.arange(n, dtype=np.int64), index=timestamps)
    for ct in broker.closed_trades:
        exit_ts = ct.exit_time
        if exit_ts in bar_positions.index:
            idx = bar_positions[exit_ts]
            realized[idx] += ct.net_pnl

    # Replay fills to track position at each bar
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
                # Same direction → update average
                total = abs(cur_qty) + abs(delta)
                if total > 0:
                    cur_avg = (abs(cur_qty) * cur_avg + abs(delta) * fill.price) / total
                cur_qty = new_qty
            else:
                if new_qty == 0:
                    cur_qty = 0.0
                    cur_avg = 0.0
                elif cur_qty * new_qty > 0:
                    # Partial close, same direction remains
                    cur_qty = new_qty
                else:
                    # Reversal
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


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_cybernetic_hilbert(
    data: pd.DataFrame,
    symbol: str,
    overrides: CyberneticHilbertConfigOverrides | None = None,
    initial_capital: float = 1000.0,
    timeframe_minutes: int | str = 5,
    compute_full_metrics: bool = True,
    fast_score_metric: str | None = None,
    repo_root: Path | None = None,
) -> BacktestRunResult:
    """Run the Cybernetic Hilbert Transform strategy backtest.

    Parameters match the registry contract used by all existing strategies.
    """
    from ._currency_utils import setup_currency_and_fx_provider

    overrides = overrides or CyberneticHilbertConfigOverrides()
    account_currency, asset_currency, fx_rate_provider = setup_currency_and_fx_provider(
        symbol=symbol,
        timeframe_minutes=timeframe_minutes,
        repo_root=repo_root,
        overrides=overrides,
    )
    overrides.account_currency = account_currency
    overrides.asset_currency = asset_currency
    overrides.fx_rate_provider = fx_rate_provider

    bars = _to_strategy_ohlcv(data)
    close = bars["close"].to_numpy(dtype=np.float64)

    # Extract indicator parameters with defaults
    hilbert_smooth_period = overrides.hilbert_smooth_period or 7
    phase_mode_enabled = overrides.phase_mode_enabled if overrides.phase_mode_enabled is not None else True
    require_cycling_bars = overrides.require_cycling_bars or 1

    # Generate signals
    entries_long, exits_long, entries_short, exits_short = _generate_signals(
        close,
        hilbert_smooth_period=hilbert_smooth_period,
        phase_mode_enabled=phase_mode_enabled,
        require_cycling_bars=require_cycling_bars,
    )

    # Determine trade direction filter
    direction = overrides.trade_direction_mode or "Long & Short"
    allow_long = direction in ("Long & Short", "Long only")
    allow_short = direction in ("Long & Short", "Short only")

    # Build BrokerConfig
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

    # Set up exit rules (safety stop, net bracket)
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

    # Pre-extract arrays for fast access
    timestamps = bars.index
    ts_arr = timestamps.to_pydatetime()
    exec_arr = bars[exec_col].to_numpy(dtype=np.float64) if exec_col in bars.columns else bars["open"].to_numpy(dtype=np.float64)
    open_arr = bars["open"].to_numpy(dtype=np.float64)
    high_arr = bars["high"].to_numpy(dtype=np.float64)
    low_arr = bars["low"].to_numpy(dtype=np.float64)
    close_arr = bars["close"].to_numpy(dtype=np.float64)
    n_bars = len(bars)

    # Early-stop drawdown tracking
    drawdown_limit = overrides.early_stop_drawdown_pct
    check_drawdown = drawdown_limit is not None and drawdown_limit > 0
    peak_equity = initial_capital
    order_counter = 0

    # Pre-mask signals
    if not allow_long:
        entries_long[:] = False
    if not allow_short:
        entries_short[:] = False

    # Pending signal for execute_on_next_bar
    pending_signal: str | None = None  # "long", "short", "exit_long", "exit_short"

    for i in range(n_bars):
        ts = ts_arr[i]
        exec_price = float(exec_arr[i])

        # Execute pending signal from previous bar (next-bar execution)
        if pending_signal is not None and broker_config.execute_on_next_bar:
            if pending_signal == "long" and allow_long:
                if broker.position.is_flat or broker.position.signed_quantity < 0:
                    # Close short if open
                    if broker.position.signed_quantity < 0:
                        qty = abs(broker.position.signed_quantity)
                        order_counter += 1
                        broker.fill_order(
                            Order(id=f"exit_short_{order_counter}", side="buy", quantity=qty,
                                  comment="Hilbert cross below (close short)", cost_side="short"),
                            ts, exec_price,
                        )
                    # Open long
                    qty = broker.calculate_position_size(exec_price, broker.cash, timestamp=ts)
                    qty = broker.normalize_quantity(qty)
                    if qty > 0:
                        order_counter += 1
                        broker.fill_order(
                            Order(id=f"entry_long_{order_counter}", side="buy", quantity=qty,
                                  comment="Hilbert cross below (entry long)", cost_side="long"),
                            ts, exec_price,
                        )
            elif pending_signal == "short" and allow_short:
                if broker.position.is_flat or broker.position.signed_quantity > 0:
                    # Close long if open
                    if broker.position.signed_quantity > 0:
                        qty = abs(broker.position.signed_quantity)
                        order_counter += 1
                        broker.fill_order(
                            Order(id=f"exit_long_{order_counter}", side="sell", quantity=qty,
                                  comment="Hilbert cross above (close long)", cost_side="long"),
                            ts, exec_price,
                        )
                    # Open short
                    qty = broker.calculate_position_size(exec_price, broker.cash, timestamp=ts)
                    qty = broker.normalize_quantity(qty)
                    if qty > 0:
                        order_counter += 1
                        broker.fill_order(
                            Order(id=f"entry_short_{order_counter}", side="sell", quantity=qty,
                                  comment="Hilbert cross above (entry short)", cost_side="short"),
                            ts, exec_price,
                        )
            elif pending_signal == "exit_long":
                if broker.position.signed_quantity > 0:
                    qty = abs(broker.position.signed_quantity)
                    order_counter += 1
                    broker.fill_order(
                        Order(id=f"exit_long_{order_counter}", side="sell", quantity=qty,
                              comment="Hilbert exit long", cost_side="long"),
                        ts, exec_price,
                    )
            elif pending_signal == "exit_short":
                if broker.position.signed_quantity < 0:
                    qty = abs(broker.position.signed_quantity)
                    order_counter += 1
                    broker.fill_order(
                        Order(id=f"exit_short_{order_counter}", side="buy", quantity=qty,
                              comment="Hilbert exit short", cost_side="short"),
                        ts, exec_price,
                    )
            pending_signal = None

        # Evaluate exit rules (safety stop, bracket exits)
        if not broker.position.is_flat and broker.exit_orchestrator is not None:
            bar_dict = {
                "timestamp": ts,
                "open": float(open_arr[i]),
                "high": float(high_arr[i]),
                "low": float(low_arr[i]),
                "close": float(close_arr[i]),
            }
            broker.evaluate_exits(bar_dict)

        # Process new signals — queue for next-bar execution
        if entries_long[i]:
            pending_signal = "long"
        elif entries_short[i]:
            pending_signal = "short"
        elif exits_long[i]:
            pending_signal = "exit_long"
        elif exits_short[i]:
            pending_signal = "exit_short"

        # Early-stop drawdown check
        if check_drawdown:
            equity = broker.cash if broker.position.is_flat else broker.mark_to_market_equity(float(close_arr[i]), ts)
            if equity > peak_equity:
                peak_equity = equity
            if peak_equity > 0:
                dd_pct = (peak_equity - equity) / peak_equity * 100.0
                if dd_pct >= drawdown_limit:
                    break

    # Build state DataFrame for metrics (equity curve tracking)
    # compute_metrics expects a DataFrame with 'realized_net_pnl_on_fill' and
    # 'estimated_net_if_closed_now' columns, indexed by bar timestamps.
    raw_trades = broker.closed_trades_frame()
    trades = _normalize_trades(raw_trades, bars)

    state = _build_state_from_broker(broker, bars, timestamps, close_arr)

    if compute_full_metrics:
        metrics, equity_curve = compute_metrics(
            MetricsInput(
                symbol=symbol,
                strategy="cybernetic_hilbert",
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
        strategy="cybernetic_hilbert",
        symbol=symbol,
        config=asdict(overrides),
        bars=bars,
        state=state,
        trades=trades,
        equity_curve=equity_curve,
        metrics=metrics,
    )


# ---------------------------------------------------------------------------
# VectorBT Pre-scan (stub — Hilbert has few indicator combos)
# ---------------------------------------------------------------------------

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
    except Exception:  # NOSONAR — best-effort report write
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
    """Pre-scan stub for Cybernetic Hilbert.

    The Hilbert Transform has very few indicator hyperparameters (smooth_period
    in [4..20]), making a VectorBT exhaustive pre-scan unnecessary.  The
    Bayesian optimizer (especially CMA-ES) handles this small continuous space
    efficiently.  Returns the parameter specs unchanged.
    """
    _write_prescan_report(output_dir, "skipped", None, {})
    return parameter_specs
