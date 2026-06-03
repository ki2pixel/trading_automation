"""
Python conversion of TradingView Pine Script:
"Range Filter Buy and Sell 5min Strategy V3.2 (Capped Bucket)"

This module computes the Range Filter signal columns and can optionally run a
lightweight strategy/backtest approximation of the Pine `strategy()` logic.

Expected input DataFrame:
    - Required: close
    - Recommended for backtest with fill_model="next_open": open
    - Optional: high, low, volume, timestamp/index

Important assumptions:
    - Account currency and symbol currency conversion are treated as 1:1.
    - syminfo.pointvalue defaults to 1.0 and is configurable.
    - Estimated commissions/slippage are used for filters/risk logic, matching
      the Pine script. They are not deducted from realized `strategy_netprofit`
      unless you modify `execute_target_position()`.
    - TradingView market-order fills can differ by broker/symbol/settings.
      fill_model="next_open" is closest to historical Pine strategies with
      process_orders_on_close=false. fill_model="close" is useful for ML labels
      and fast research.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np
import pandas as pd

from backtest_engine.broker import BrokerConfig, BrokerSimulator, Order


TradeDirectionMode = Literal["Long & Short", "Long only", "Short only"]
FeeMode = Literal[
    "Parametric: hold until net covers fees",
    "Parametric: exit only, no forced reversal",
    "Disabled: always reverse/close on opposite signal",
]
SafetyStopAppliesTo = Literal["Both", "Long only", "Short only"]
SafetyStopMode = Literal[
    "Net loss only",
    "Max bars only",
    "Net loss OR max bars",
    "Net loss AND max bars",
]
SafetyMaxNetLossMode = Literal["Cash amount", "% of entry value"]
FillModel = Literal["next_open", "close"]


@dataclass
class RangeFilterConfig:
    # Core indicator inputs
    source_col: str = "close"
    sampling_period: int = 100
    range_multiplier: float = 3.0

    # Currency overrides
    asset_currency: str | None = None
    account_currency: str | None = None
    fx_rate_provider: object | None = None

    # V3 capped bucket model
    max_entry_price: float = 300.0
    max_capital_bucket: float = 300.0
    initial_capital_bucket: float = 300.0

    # Trade direction
    trade_direction_mode: TradeDirectionMode = "Long & Short"

    # Fee / reversal filter
    fee_mode: FeeMode = "Parametric: hold until net covers fees"
    estimated_commission_per_order_long: float = 0.0
    estimated_commission_per_order_short: float = 3.0
    estimated_slippage_per_side_long: float = 0.0
    estimated_slippage_per_side_short: float = 0.0
    min_net_profit_after_costs: float = 0.0

    # Explicit net exits
    use_net_bracket_exits: bool = False
    take_profit_net_percent: float = 10.0
    stop_loss_net_percent: float = 10.0

    # Safety stop
    use_safety_stop: bool = True
    safety_stop_applies_to: SafetyStopAppliesTo = "Short only"
    safety_stop_mode: SafetyStopMode = "Net loss only"
    safety_max_net_loss_mode: SafetyMaxNetLossMode = "Cash amount"
    safety_max_net_loss_cash: float = 50.0
    safety_max_net_loss_percent: float = 0.0
    safety_max_bars_in_trade: int = 0

    # Python/backtest assumptions
    point_value: float = 1.0
    fill_model: FillModel = "next_open"
    apply_estimated_costs_to_realized_pnl: bool = True
    allow_fractional_quantity: bool = True
    quantity_precision: int | None = 6
    early_stop_drawdown_pct: float | None = None


def _validate_input(df: pd.DataFrame, cfg: RangeFilterConfig, backtest: bool = False) -> None:
    if cfg.source_col not in df.columns:
        raise ValueError(f"Input DataFrame must contain source column: {cfg.source_col!r}")
    if "close" not in df.columns:
        raise ValueError("Input DataFrame must contain a 'close' column.")
    if backtest and cfg.fill_model == "next_open" and "open" not in df.columns:
        raise ValueError('Backtest with fill_model="next_open" requires an "open" column.')
    if cfg.sampling_period < 1:
        raise ValueError("sampling_period must be >= 1.")
    if cfg.range_multiplier < 0.1:
        raise ValueError("range_multiplier must be >= 0.1.")


import numba

@numba.njit(cache=False)
def _pine_ema_numba(arr: np.ndarray, length: int) -> np.ndarray:
    out = np.full(len(arr), np.nan, dtype=np.float64)
    alpha = 2.0 / (length + 1.0)
    prev = np.nan

    for i in range(len(arr)):
        value = arr[i]
        if np.isnan(value):
            out[i] = np.nan
            continue

        if np.isnan(prev):
            prev = value
        else:
            prev = alpha * value + (1.0 - alpha) * prev

        out[i] = prev
    return out

def _pine_ema(values: pd.Series, length: int) -> pd.Series:
    """
    Pine-like EMA:
    - skips NaN until first valid source value
    - seeds EMA with first valid source value
    """
    arr = values.astype(float).to_numpy()
    out = _pine_ema_numba(arr, length)
    return pd.Series(out, index=values.index, name=f"ema_{length}")


def _bucket_clamp(value: float, bucket_max: float) -> float:
    return max(min(float(value), float(bucket_max)), 0.0)


def _qty_from_bucket(bucket: float, price: float) -> float:
    return float(bucket) / float(price) if price and price > 0 else 0.0


def _smooth_range(source: pd.Series, period: int, multiplier: float) -> pd.Series:
    weighted_period = period * 2 - 1
    average_range = _pine_ema(source.diff().abs(), period)
    return _pine_ema(average_range, weighted_period) * multiplier


@numba.njit(cache=False)
def _range_filter_numba(x: np.ndarray, r: np.ndarray) -> np.ndarray:
    out = np.full(len(x), np.nan, dtype=np.float64)
    
    for i in range(len(x)):
        xi = x[i]
        ri = r[i]

        if np.isnan(xi) or np.isnan(ri):
            out[i] = np.nan
            continue

        prev = out[i - 1] if i > 0 and not np.isnan(out[i - 1]) else 0.0

        if xi > prev:
            candidate = xi - ri
            out[i] = prev if candidate < prev else candidate
        else:
            candidate = xi + ri
            out[i] = prev if candidate > prev else candidate
    return out

def _range_filter(source: pd.Series, smooth_range: pd.Series) -> pd.Series:
    """
    Recursive conversion of Pine's rngfilt() function:

        rangeFilter := x > nz(rangeFilter[1]) ?
            (x - r < nz(rangeFilter[1]) ? nz(rangeFilter[1]) : x - r) :
            (x + r > nz(rangeFilter[1]) ? nz(rangeFilter[1]) : x + r)
    """
    x = source.astype(float).to_numpy()
    r = smooth_range.astype(float).to_numpy()
    out = _range_filter_numba(x, r)
    return pd.Series(out, index=source.index, name="range_filter")


# Shared indicator references (populated by backtest_engine multiprocessing workers)
_SHARED_RF_SMRNG_GRID: np.ndarray | None = None
_SHARED_RF_GRID: np.ndarray | None = None
_SHARED_RF_KEYS: dict[tuple[int, float], int] | None = None


@numba.njit(cache=False)
def _compute_up_down(filt: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = len(filt)
    upward = np.zeros(n, dtype=np.float64)
    downward = np.zeros(n, dtype=np.float64)
    for i in range(n):
        prev_up = upward[i - 1] if i > 0 else 0.0
        prev_down = downward[i - 1] if i > 0 else 0.0
        if i == 0 or np.isnan(filt[i]) or np.isnan(filt[i - 1]):
            upward[i] = prev_up
            downward[i] = prev_down
        elif filt[i] > filt[i - 1]:
            upward[i] = prev_up + 1.0
            downward[i] = 0.0
        elif filt[i] < filt[i - 1]:
            upward[i] = 0.0
            downward[i] = prev_down + 1.0
        else:
            upward[i] = prev_up
            downward[i] = prev_down
    return upward, downward


@numba.njit(cache=False)
def _compute_signals(long_cond: np.ndarray, short_cond: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    n = len(long_cond)
    cond_state = np.full(n, np.nan, dtype=np.float64)
    long_signal = np.zeros(n, dtype=np.bool_)
    short_signal = np.zeros(n, dtype=np.bool_)
    
    for i in range(n):
        prev_state_raw = cond_state[i - 1] if i > 0 else np.nan
        prev_state_for_signal = 0.0 if np.isnan(prev_state_raw) else prev_state_raw

        if long_cond[i]:
            cond_state[i] = 1.0
        elif short_cond[i]:
            cond_state[i] = -1.0
        else:
            cond_state[i] = prev_state_raw

        long_signal[i] = bool(long_cond[i] and np.isclose(prev_state_for_signal, -1.0, atol=1e-9))
        short_signal[i] = bool(short_cond[i] and np.isclose(prev_state_for_signal, 1.0, atol=1e-9))
    return cond_state, long_signal, short_signal


def add_range_filter_columns(
    df: pd.DataFrame,
    cfg: Optional[RangeFilterConfig] = None,
) -> pd.DataFrame:
    """
    Add indicator/signal columns equivalent to the Pine script's core calculations.

    Columns added:
        smrng, range_filter, upward, downward, hband, lband,
        long_cond, short_cond, cond_state, long_signal, short_signal,
        allow_long, allow_short
    """
    cfg = cfg or RangeFilterConfig()
    _validate_input(df, cfg, backtest=False)

    global _SHARED_RF_SMRNG_GRID, _SHARED_RF_GRID, _SHARED_RF_KEYS

    out = df.copy()
    src = out[cfg.source_col].astype(float)

    use_shared = False
    if _SHARED_RF_SMRNG_GRID is not None and _SHARED_RF_GRID is not None and _SHARED_RF_KEYS is not None:
        period_key = (int(cfg.sampling_period), float(cfg.range_multiplier))
        if period_key in _SHARED_RF_KEYS:
            idx = _SHARED_RF_KEYS[period_key]
            out["smrng"] = _SHARED_RF_SMRNG_GRID[idx]
            out["range_filter"] = _SHARED_RF_GRID[idx]
            use_shared = True

    if not use_shared:
        out["smrng"] = _smooth_range(src, cfg.sampling_period, cfg.range_multiplier)
        out["range_filter"] = _range_filter(src, out["smrng"])

    filt = out["range_filter"].to_numpy(dtype=float)

    upward, downward = _compute_up_down(filt)

    out["upward"] = upward
    out["downward"] = downward
    out["hband"] = out["range_filter"] + out["smrng"]
    out["lband"] = out["range_filter"] - out["smrng"]

    prev_src = src.shift(1)
    out["long_cond"] = (
        ((src > out["range_filter"]) & (src > prev_src) & (out["upward"] > 0))
        | ((src > out["range_filter"]) & (src < prev_src) & (out["upward"] > 0))
    ).fillna(0.0).astype(bool)

    out["short_cond"] = (
        ((src < out["range_filter"]) & (src < prev_src) & (out["downward"] > 0))
        | ((src < out["range_filter"]) & (src > prev_src) & (out["downward"] > 0))
    ).fillna(0.0).astype(bool)

    cond_state, long_signal, short_signal = _compute_signals(
        out["long_cond"].to_numpy(dtype=bool),
        out["short_cond"].to_numpy(dtype=bool)
    )

    out["cond_state"] = cond_state
    out["long_signal"] = long_signal
    out["short_signal"] = short_signal
    out["allow_long"] = cfg.trade_direction_mode != "Short only"
    out["allow_short"] = cfg.trade_direction_mode != "Long only"

    return out


def _estimate_position_metrics(
    *,
    close: float,
    position_size: float,
    entry_price: float,
    entry_bar_index: Optional[int],
    bar_index: int,
    capital_bucket: float,
    cfg: RangeFilterConfig,
    fx_rate: float = 1.0,
) -> dict[str, float | bool]:
    in_long = position_size > 0
    in_short = position_size < 0
    flat = position_size == 0
    abs_pos_size = abs(position_size)
    avg_price = entry_price if abs_pos_size > 0 else np.nan

    bars_in_trade = (bar_index - entry_bar_index) if entry_bar_index is not None else 0

    close_account = close * fx_rate
    if in_long:
        gross_pnl = (close_account - avg_price) * abs_pos_size * cfg.point_value
    elif in_short:
        gross_pnl = (avg_price - close_account) * abs_pos_size * cfg.point_value
    else:
        gross_pnl = 0.0

    current_commission = (
        cfg.estimated_commission_per_order_long
        if in_long
        else cfg.estimated_commission_per_order_short
        if in_short
        else 0.0
    )
    current_slippage = (
        cfg.estimated_slippage_per_side_long
        if in_long
        else cfg.estimated_slippage_per_side_short
        if in_short
        else 0.0
    )

    estimated_round_trip_costs = (
        current_commission * 2.0 + current_slippage * 2.0 if abs_pos_size > 0 else 0.0
    )
    estimated_net_if_closed_now = gross_pnl - estimated_round_trip_costs
    reversal_net_filter_passed = estimated_net_if_closed_now >= cfg.min_net_profit_after_costs
    estimated_bucket_after_close = _bucket_clamp(
        capital_bucket + estimated_net_if_closed_now,
        cfg.max_capital_bucket,
    )

    quantity_point_value = abs_pos_size * cfg.point_value
    entry_position_value = (
        avg_price * abs_pos_size * cfg.point_value if abs_pos_size > 0 else 0.0
    )
    take_profit_net_threshold = entry_position_value * cfg.take_profit_net_percent / 100.0
    stop_loss_net_threshold = entry_position_value * cfg.stop_loss_net_percent / 100.0
    safety_max_net_loss_threshold = (
        cfg.safety_max_net_loss_cash
        if cfg.safety_max_net_loss_mode == "Cash amount"
        else entry_position_value * cfg.safety_max_net_loss_percent / 100.0
    )

    safety_direction_allowed = (
        cfg.safety_stop_applies_to == "Both"
        or (cfg.safety_stop_applies_to == "Long only" and in_long)
        or (cfg.safety_stop_applies_to == "Short only" and in_short)
    )
    safety_loss_triggered = (
        safety_max_net_loss_threshold > 0
        and estimated_net_if_closed_now <= -safety_max_net_loss_threshold
    )
    safety_bars_triggered = (
        cfg.safety_max_bars_in_trade > 0
        and bars_in_trade >= cfg.safety_max_bars_in_trade
    )

    if cfg.safety_stop_mode == "Net loss only":
        safety_mode_triggered = safety_loss_triggered
    elif cfg.safety_stop_mode == "Max bars only":
        safety_mode_triggered = safety_bars_triggered
    elif cfg.safety_stop_mode == "Net loss OR max bars":
        safety_mode_triggered = safety_loss_triggered or safety_bars_triggered
    else:
        safety_mode_triggered = safety_loss_triggered and safety_bars_triggered

    safety_stop_triggered = (
        cfg.use_safety_stop and safety_direction_allowed and safety_mode_triggered
    )

    hit_net_take_profit = (
        cfg.use_net_bracket_exits
        and abs_pos_size > 0
        and estimated_net_if_closed_now >= take_profit_net_threshold
    )
    hit_net_stop_loss = (
        cfg.use_net_bracket_exits
        and abs_pos_size > 0
        and estimated_net_if_closed_now <= -stop_loss_net_threshold
    )

    if in_long and quantity_point_value > 0:
        long_take_profit_price = avg_price + (
            take_profit_net_threshold + estimated_round_trip_costs
        ) / quantity_point_value
        long_stop_loss_price = avg_price + (
            estimated_round_trip_costs - stop_loss_net_threshold
        ) / quantity_point_value
    else:
        long_take_profit_price = np.nan
        long_stop_loss_price = np.nan

    if in_short and quantity_point_value > 0:
        short_take_profit_price = avg_price - (
            take_profit_net_threshold + estimated_round_trip_costs
        ) / quantity_point_value
        short_stop_loss_price = avg_price + (
            stop_loss_net_threshold - estimated_round_trip_costs
        ) / quantity_point_value
    else:
        short_take_profit_price = np.nan
        short_stop_loss_price = np.nan

    return {
        "in_long": in_long,
        "in_short": in_short,
        "flat": flat,
        "abs_pos_size": abs_pos_size,
        "bars_in_trade": bars_in_trade,
        "gross_pnl_estimate": gross_pnl,
        "estimated_round_trip_costs": estimated_round_trip_costs,
        "estimated_net_if_closed_now": estimated_net_if_closed_now,
        "reversal_net_filter_passed": reversal_net_filter_passed,
        "estimated_bucket_after_close": estimated_bucket_after_close,
        "entry_position_value": entry_position_value,
        "take_profit_net_threshold": take_profit_net_threshold,
        "stop_loss_net_threshold": stop_loss_net_threshold,
        "safety_max_net_loss_threshold": safety_max_net_loss_threshold,
        "safety_loss_triggered": safety_loss_triggered,
        "safety_bars_triggered": safety_bars_triggered,
        "safety_stop_triggered": safety_stop_triggered,
        "hit_net_take_profit": hit_net_take_profit,
        "hit_net_stop_loss": hit_net_stop_loss,
        "long_take_profit_price": long_take_profit_price,
        "long_stop_loss_price": long_stop_loss_price,
        "short_take_profit_price": short_take_profit_price,
        "short_stop_loss_price": short_stop_loss_price,
    }


class _RangeFilterBacktestSession:
    def __init__(
        self,
        config: RangeFilterConfig,
        compute_full_metrics: bool,
        early_stop_drawdown_pct: Optional[float],
        broker: BrokerSimulator,
        result: pd.DataFrame,
    ):
        self.config = config
        self.compute_full_metrics = compute_full_metrics
        self.early_stop_drawdown_pct = early_stop_drawdown_pct
        self.broker = broker
        self.result = result
        
        self.n = len(result)
        self.index = result.index
        self.close_arr = result["close"].to_numpy(dtype=float)
        self.open_arr = result["open"].to_numpy(dtype=float) if "open" in result.columns else self.close_arr
        self.allow_long_arr = result["allow_long"].to_numpy(dtype=bool)
        self.allow_short_arr = result["allow_short"].to_numpy(dtype=bool)
        self.long_signal_arr = result["long_signal"].to_numpy(dtype=bool)
        self.short_signal_arr = result["short_signal"].to_numpy(dtype=bool)

        self.capital_bucket = _bucket_clamp(self.config.initial_capital_bucket, self.config.max_capital_bucket)
        self.withdrawn_profit = 0.0
        self.strategy_netprofit = 0.0
        self.processed_netprofit = 0.0
        self.peak_equity = float(self.broker.cash)

        self.position_size = 0.0
        self.entry_price = np.nan
        self.entry_bar_index: Optional[int] = None
        self.entry_time = None

        self.pending_order: Optional[dict] = None

        if self.compute_full_metrics:
            self.records = {
                "position_size": [],
                "position_side": [],
                "position_avg_price": [],
                "capital_bucket": [],
                "withdrawn_profit": [],
                "strategy_netprofit": [],
                "realized_net_pnl_on_fill": [],
                "bars_in_trade": [],
                "gross_pnl_estimate": [],
                "estimated_round_trip_costs": [],
                "estimated_net_if_closed_now": [],
                "reversal_net_filter_passed": [],
                "estimated_bucket_after_close": [],
                "entry_position_value": [],
                "take_profit_net_threshold": [],
                "stop_loss_net_threshold": [],
                "safety_max_net_loss_threshold": [],
                "safety_loss_triggered": [],
                "safety_bars_triggered": [],
                "safety_stop_triggered": [],
                "hit_net_take_profit": [],
                "hit_net_stop_loss": [],
                "long_take_profit_price": [],
                "long_stop_loss_price": [],
                "short_take_profit_price": [],
                "short_stop_loss_price": [],
                "flat_entry_qty": [],
                "reverse_entry_qty": [],
                "entry_allowed_by_cap": [],
                "order_action": [],
                "fill_action": [],
                "fill_price": [],
            }
        else:
            self.records = {
                "position_size": [],
                "position_avg_price": [],
                "realized_net_pnl_on_fill": [],
                "estimated_net_if_closed_now": [],
            }

    def _update_bucket_after_closed_profit(self) -> None:
        if self.strategy_netprofit != self.processed_netprofit:
            delta_closed_net = self.strategy_netprofit - self.processed_netprofit
            raw_bucket = self.capital_bucket + delta_closed_net
            if raw_bucket > self.config.max_capital_bucket:
                self.withdrawn_profit += raw_bucket - self.config.max_capital_bucket
            self.capital_bucket = _bucket_clamp(raw_bucket, self.config.max_capital_bucket)
            self.processed_netprofit = self.strategy_netprofit

    def _execute_target_position(
        self,
        target_side: int,
        target_qty: float,
        fill_price: float,
        bar_i: int,
        reason: str,
    ) -> float:
        realized_net = 0.0
        old_size = self.position_size
        old_side = 1 if old_size > 0 else -1 if old_size < 0 else 0
        old_abs = abs(old_size)
        normalized_target_qty = self.broker.normalize_quantity(max(float(target_qty), 0.0))
        target_side = int(np.sign(target_side)) if normalized_target_qty > 0 else 0
        closed_trade_count = len(self.broker.closed_trades)

        if old_side != 0 and (target_side == 0 or target_side != old_side):
            self.broker.fill_order(
                Order(
                    id=f"close-{bar_i}-{closed_trade_count}",
                    side="sell" if old_side > 0 else "buy",
                    quantity=old_abs,
                    comment=reason,
                    cost_side="long" if old_side > 0 else "short",
                ),
                self.index[bar_i],
                fill_price,
            )
            if len(self.broker.closed_trades) > closed_trade_count:
                broker_trade = self.broker.closed_trades[-1]
                realized_net = float(broker_trade.net_pnl)
                self.strategy_netprofit += realized_net

        if target_side == 0 or normalized_target_qty <= 0:
            self.entry_price = np.nan
            self.entry_bar_index = None
            self.entry_time = None
        elif old_side == target_side and old_side != 0:
            self.entry_price = self.entry_price
        else:
            fill = self.broker.fill_order(
                Order(
                    id=f"entry-{bar_i}-{len(self.broker.fills)}",
                    side="buy" if target_side > 0 else "sell",
                    quantity=normalized_target_qty,
                    comment=reason,
                    cost_side="long" if target_side > 0 else "short",
                ),
                self.index[bar_i],
                fill_price,
            )
            if fill is not None:
                self.entry_price = float(fill.price)
                self.entry_bar_index = bar_i
                self.entry_time = self.index[bar_i]

        self.position_size = float(self.broker.position.signed_quantity)
        self.entry_price = float(self.broker.position.average_price) if not self.broker.position.is_flat else np.nan
        if self.broker.position.is_flat:
            self.entry_bar_index = None
            self.entry_time = None

        return realized_net

    def run(self) -> tuple[pd.DataFrame, pd.DataFrame, bool]:
        for i in range(self.n):
            bar_realized_net = 0.0
            close = float(self.close_arr[i])
            fill_price_for_pending = (
                float(self.open_arr[i]) if self.config.fill_model == "next_open" else close
            )

            current_fill_action = ""
            current_fill_price = np.nan
            current_order_action = ""

            if self.config.fill_model == "next_open" and self.pending_order is not None:
                bar_realized_net += self._execute_target_position(
                    target_side=self.pending_order["target_side"],
                    target_qty=self.pending_order["target_qty"],
                    fill_price=fill_price_for_pending,
                    bar_i=i,
                    reason=self.pending_order["reason"],
                )
                current_fill_action = self.pending_order["reason"]
                current_fill_price = fill_price_for_pending
                self.pending_order = None

            self._update_bucket_after_closed_profit()

            metrics = _estimate_position_metrics(
                close=close,
                position_size=self.position_size,
                entry_price=self.entry_price,
                entry_bar_index=self.entry_bar_index,
                bar_index=i,
                capital_bucket=self.capital_bucket,
                cfg=self.config,
                fx_rate=self.broker.fx_rate(self.index[i]),
            )

            entry_allowed_by_cap = close <= self.config.max_entry_price and self.capital_bucket > 0
            flat_entry_qty = _qty_from_bucket(self.capital_bucket, close)
            reverse_entry_qty = _qty_from_bucket(metrics["estimated_bucket_after_close"], close)

            hold_until_profitable = (
                self.config.fee_mode == "Parametric: hold until net covers fees"
            )
            exit_only_no_reverse = (
                self.config.fee_mode == "Parametric: exit only, no forced reversal"
            )
            disable_fee_filter = (
                self.config.fee_mode == "Disabled: always reverse/close on opposite signal"
            )

            allow_long = bool(self.allow_long_arr[i])
            allow_short = bool(self.allow_short_arr[i])
            long_signal = bool(self.long_signal_arr[i])
            short_signal = bool(self.short_signal_arr[i])

            order: Optional[dict] = None

            def make_order(target_side: int, target_qty: float, reason: str) -> dict:
                return {
                    "target_side": target_side,
                    "target_qty": max(float(target_qty), 0.0),
                    "reason": reason,
                }

            if metrics["safety_stop_triggered"] and metrics["in_long"]:
                order = make_order(0, 0.0, "Safety Stop Long")
            elif metrics["safety_stop_triggered"] and metrics["in_short"]:
                order = make_order(0, 0.0, "Safety Stop Short")
            elif metrics["in_long"] and metrics["hit_net_take_profit"]:
                order = make_order(0, 0.0, "Net TP Long")
            elif metrics["in_long"] and metrics["hit_net_stop_loss"]:
                order = make_order(0, 0.0, "Net SL Long")
            elif metrics["in_short"] and metrics["hit_net_take_profit"]:
                order = make_order(0, 0.0, "Net TP Short")
            elif metrics["in_short"] and metrics["hit_net_stop_loss"]:
                order = make_order(0, 0.0, "Net SL Short")
            else:
                if metrics["flat"] and entry_allowed_by_cap and flat_entry_qty > 0:
                    if long_signal and allow_long:
                        order = make_order(1, flat_entry_qty, "Buy")
                    elif short_signal and allow_short:
                        order = make_order(-1, flat_entry_qty, "Sell")

                if order is None and metrics["in_long"] and short_signal:
                    if disable_fee_filter:
                        if close <= self.config.max_entry_price and reverse_entry_qty > 0:
                            if allow_short:
                                order = make_order(-1, reverse_entry_qty, "Sell Rev")
                            else:
                                order = make_order(0, 0.0, "Exit Long")
                        else:
                            order = make_order(0, 0.0, "Exit Long")
                    elif exit_only_no_reverse or not allow_short:
                        order = make_order(0, 0.0, "Exit Long")
                    elif hold_until_profitable and metrics["reversal_net_filter_passed"]:
                        if close <= self.config.max_entry_price and reverse_entry_qty > 0:
                            if allow_short:
                                order = make_order(-1, reverse_entry_qty, "Sell Rev")
                            else:
                                order = make_order(0, 0.0, "Exit Long")
                        else:
                            order = make_order(0, 0.0, "Exit Long")

                if order is None and metrics["in_short"] and long_signal:
                    if disable_fee_filter:
                        if close <= self.config.max_entry_price and reverse_entry_qty > 0:
                            if allow_long:
                                order = make_order(1, reverse_entry_qty, "Buy Rev")
                            else:
                                order = make_order(0, 0.0, "Exit Short")
                        else:
                            order = make_order(0, 0.0, "Exit Short")
                    elif exit_only_no_reverse or not allow_long:
                        order = make_order(0, 0.0, "Exit Short")
                    elif hold_until_profitable and metrics["reversal_net_filter_passed"]:
                        if close <= self.config.max_entry_price and reverse_entry_qty > 0:
                            if allow_long:
                                order = make_order(1, reverse_entry_qty, "Buy Rev")
                            else:
                                order = make_order(0, 0.0, "Exit Short")
                        else:
                            order = make_order(0, 0.0, "Exit Short")

            if order is not None:
                current_order_action = order["reason"]
                if self.config.fill_model == "close":
                    bar_realized_net += self._execute_target_position(
                        target_side=order["target_side"],
                        target_qty=order["target_qty"],
                        fill_price=close,
                        bar_i=i,
                        reason=order["reason"],
                    )
                    current_fill_action = order["reason"]
                    current_fill_price = close
                else:
                    self.pending_order = order

            if self.early_stop_drawdown_pct is not None and self.early_stop_drawdown_pct > 0:
                current_equity = self.broker.mark_to_market_equity(close, self.index[i])
                if current_equity > self.peak_equity:
                    self.peak_equity = current_equity
                drawdown_pct = (self.peak_equity - current_equity) / self.peak_equity * 100.0 if self.peak_equity > 0 else 0.0
                if drawdown_pct >= self.early_stop_drawdown_pct:
                    return pd.DataFrame(self.records, index=self.index[:len(self.records["position_size"])]), self.broker.closed_trades_frame(), True

            self.records["position_size"].append(self.position_size)
            self.records["position_avg_price"].append(self.entry_price)
            self.records["realized_net_pnl_on_fill"].append(bar_realized_net)
            
            if self.compute_full_metrics:
                self.records["position_side"].append(1 if self.position_size > 0 else -1 if self.position_size < 0 else 0)
                self.records["capital_bucket"].append(self.capital_bucket)
                self.records["withdrawn_profit"].append(self.withdrawn_profit)
                self.records["strategy_netprofit"].append(self.strategy_netprofit)
                self.records["flat_entry_qty"].append(flat_entry_qty)
                self.records["reverse_entry_qty"].append(reverse_entry_qty)
                self.records["entry_allowed_by_cap"].append(entry_allowed_by_cap)
                self.records["order_action"].append(current_order_action)
                self.records["fill_action"].append(current_fill_action)
                self.records["fill_price"].append(current_fill_price)
                
                for key in metrics:
                    if key in self.records:
                        self.records[key].append(metrics[key])
            else:
                self.records["estimated_net_if_closed_now"].append(metrics["estimated_net_if_closed_now"])

        return pd.DataFrame(self.records, index=self.index), self.broker.closed_trades_frame(), False


def run_range_filter_strategy(
    df: pd.DataFrame,
    cfg: Optional[RangeFilterConfig] = None,
    early_stop_drawdown_pct: float | None = None,
    compute_full_metrics: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    cfg = cfg or RangeFilterConfig()
    if early_stop_drawdown_pct is not None:
        cfg.early_stop_drawdown_pct = early_stop_drawdown_pct
    _validate_input(df, cfg, backtest=True)

    result = add_range_filter_columns(df, cfg)

    broker = BrokerSimulator(
        BrokerConfig(
            initial_capital=float(cfg.initial_capital_bucket),
            execute_on_next_bar=cfg.fill_model == "next_open",
            execution_price_col="open" if cfg.fill_model == "next_open" else "close",
            commission_fixed_long=float(cfg.estimated_commission_per_order_long),
            commission_fixed_short=float(cfg.estimated_commission_per_order_short),
            slippage_per_side_long=float(cfg.estimated_slippage_per_side_long),
            slippage_per_side_short=float(cfg.estimated_slippage_per_side_short),
            point_value=float(cfg.point_value),
            allow_fractional_quantity=bool(cfg.allow_fractional_quantity),
            quantity_precision=cfg.quantity_precision,
            account_currency=cfg.account_currency if cfg.account_currency is not None else "EUR",
            asset_currency=cfg.asset_currency if cfg.asset_currency is not None else "EUR",
            fx_rate_provider=cfg.fx_rate_provider,
        )
    )

    session = _RangeFilterBacktestSession(
        config=cfg,
        compute_full_metrics=compute_full_metrics,
        early_stop_drawdown_pct=early_stop_drawdown_pct,
        broker=broker,
        result=result,
    )
    
    records_df, trades_df, _ = session.run()

    if compute_full_metrics:
        for col in records_df.columns:
            result[col] = records_df[col]
        return result, trades_df
    else:
        out_df = pd.DataFrame({
            "position_size": records_df["position_size"],
            "position_avg_price": records_df["position_avg_price"],
            "realized_net_pnl_on_fill": records_df["realized_net_pnl_on_fill"],
            "estimated_net_if_closed_now": records_df["estimated_net_if_closed_now"],
        }, index=result.index)
        return out_df, trades_df

# Example usage:
#
# import pandas as pd
#
# data = pd.read_csv("your_5m_ohlcv.csv", parse_dates=["timestamp"], index_col="timestamp")
# cfg = RangeFilterConfig(
#     sampling_period=100,
#     range_multiplier=3.0,
#     max_entry_price=300.0,
#     max_capital_bucket=300.0,
#     initial_capital_bucket=300.0,
#     fill_model="next_open",
# )
#
# # ML/signal dataset only:
# signals = add_range_filter_columns(data, cfg)
#
# # Strategy/backtest approximation:
# backtest_df, trades = run_range_filter_strategy(data, cfg)
# print(backtest_df.tail())
# print(trades.tail())
