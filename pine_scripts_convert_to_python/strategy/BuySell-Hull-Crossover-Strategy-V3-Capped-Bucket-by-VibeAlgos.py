"""
hma_crossover_v3_capped_bucket.py

Python conversion of:
"HMA Crossover Strategy V3.2 (Capped Bucket)" / "HMA Xover V3.2"

Input DataFrame requirements:
    - A DateTimeIndex is recommended, but not required.
    - Required columns: open, high, low, close
    - The source column defaults to "close".

Main entry points:
    add_hma_crossover_features(df, config)
        Adds HMA crossover feature/signal columns only.

    run_hma_crossover_strategy(df, config)
        Adds features plus a stateful backtest approximation of the TradingView
        strategy, including capped bucket sizing, reversal filters, net TP/SL,
        safety stop, and trade log output.

Important conversion note:
    TradingView strategy orders with process_orders_on_close=false are normally
    generated on one bar and filled on the next available tick. This script
    defaults to next-bar open fills via config.execute_on_next_bar=True.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple

import math
import numpy as np
import pandas as pd

from backtest_engine.broker import BrokerConfig, BrokerSimulator, Order


# ---------------------------------------------------------------------------
# Phase 3: Process-level HMA feature cache
# ---------------------------------------------------------------------------
# Each optimizer worker keeps its own copy of this dict (multiprocessing forks
# after _init_worker, so no cross-process sharing or locking is needed).
# The dict maps (data_fingerprint, fast_len, slow_len, source_col,
# confirm_on_close) -> pd.DataFrame (the output of add_hma_crossover_features).
# We bound the dict to at most _HMA_CACHE_MAX_SIZE entries so memory stays
# manageable even in long sweeps that touch many (fast_len, slow_len) pairs.
_HMA_FEATURE_CACHE: dict = {}
_HMA_CACHE_MAX_SIZE: int = 8


def _make_feature_cache_key(
    df: pd.DataFrame,
    fast_len: int,
    slow_len: int,
    source_col: str,
    confirm_on_close: bool,
) -> tuple:
    """Build a cheap, stable cache key for a (data, indicator-params) pair.

    We fingerprint the DataFrame with:
    - shape (rows, cols)          — catches size changes
    - id of the underlying numpy array of the source column  — cheap same-object check
    - hash of first + last 4 values of the source column     — detects data changes
      when the same slot is reused for a different symbol/period.
    """
    src = df[source_col].to_numpy(dtype=float, copy=False)
    n = len(src)
    # Combine a few boundary values into a single hash; avoid hashing the full
    # array to keep key construction O(1).
    boundary = src[:4].tobytes() + src[max(0, n - 4):].tobytes()
    return (id(src), n, hash(boundary), fast_len, slow_len, source_col, confirm_on_close)


def clear_hma_feature_cache() -> None:
    """Evict all cached HMA features — useful in tests or after symbol changes."""
    _HMA_FEATURE_CACHE.clear()


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


@dataclass
class HMACrossoverConfig:
    # Indicator inputs
    fast_len: int = 20
    slow_len: int = 55
    source_col: str = "close"
    confirm_on_close: bool = True

    # Currency overrides
    asset_currency: str | None = None
    account_currency: str | None = None
    fx_rate_provider: object | None = None

    # V3 - capped bucket model
    max_entry_price: float = 300.0
    max_capital_bucket: float = 300.0
    initial_capital_bucket: float = 300.0

    # V3.3 - trade direction
    trade_direction_mode: TradeDirectionMode = "Long & Short"

    # V3.2 - fee / reversal filter
    fee_mode: FeeMode = "Parametric: hold until net covers fees"
    estimated_commission_per_order_long: float = 0.0
    estimated_commission_per_order_short: float = 3.0
    estimated_slippage_per_side_long: float = 0.0
    estimated_slippage_per_side_short: float = 0.0
    min_net_profit_after_costs: float = 0.0

    # V3.2 - explicit net exits
    use_net_bracket_exits: bool = False
    take_profit_net_percent: float = 10.0
    stop_loss_net_percent: float = 10.0

    # V3.2 - safety stop
    use_safety_stop: bool = True
    safety_stop_applies_to: SafetyStopAppliesTo = "Short only"
    safety_stop_mode: SafetyStopMode = "Net loss only"
    safety_max_net_loss_mode: SafetyMaxNetLossMode = "Cash amount"
    safety_max_net_loss_cash: float = 50.0
    safety_max_net_loss_percent: float = 0.0
    safety_max_bars_in_trade: int = 0

    # Python/backtest assumptions
    point_value: float = 1.0
    execute_on_next_bar: bool = True
    next_bar_execution_price_col: str = "open"

    # Pine uses strategy.netprofit for bucket updates. This Python conversion
    # applies the estimated parametric costs to realized PnL by default so the
    # strategy is self-contained.
    apply_estimated_costs_to_realized_pnl: bool = True

    # Pine supports fractional qty for many symbols. Set False for whole shares.
    allow_fractional_quantity: bool = True
    quantity_precision: Optional[int] = None


def bucket_clamp(value: float, bucket_max: float) -> float:
    """Equivalent to the Pine helper: max(min(value, bucketMax), 0)."""
    if pd.isna(value):
        value = 0.0
    return max(min(float(value), float(bucket_max)), 0.0)


def qty_from_bucket(bucket: float, price: float) -> float:
    """Equivalent to Pine helper: price > 0 ? bucket / price : 0."""
    if pd.isna(price) or price <= 0:
        return 0.0
    return float(bucket) / float(price)


def wma(series: pd.Series, length: int) -> pd.Series:
    """
    TradingView-style weighted moving average.
    Most recent value receives the largest weight.
    """
    length = int(length)
    if length < 1:
        raise ValueError("WMA length must be >= 1")

    weights = np.arange(1, length + 1, dtype=float)
    weight_sum = weights.sum()

    res = np.convolve(series.to_numpy(dtype=float), weights[::-1], mode='full')[:len(series)] / weight_sum
    res[:length-1] = np.nan
    return pd.Series(res, index=series.index)


def hma(series: pd.Series, length: int) -> pd.Series:
    """
    TradingView-style Hull Moving Average approximation:
        HMA(src, n) = WMA(2 * WMA(src, n/2) - WMA(src, n), sqrt(n))
    Pine's integer lengths are approximated with floor conversion.
    """
    length = int(length)
    if length < 1:
        raise ValueError("HMA length must be >= 1")

    half_len = max(1, int(length / 2))
    sqrt_len = max(1, int(math.sqrt(length)))

    fast_wma = wma(series, half_len)
    slow_wma = wma(series, length)
    raw_hma = 2.0 * fast_wma - slow_wma
    return wma(raw_hma, sqrt_len)


def crossover(a: pd.Series, b: pd.Series) -> pd.Series:
    """Equivalent to ta.crossover(a, b)."""
    crossed = (a > b) & (a.shift(1) <= b.shift(1))
    return crossed.fillna(0.0).astype(bool)


def crossunder(a: pd.Series, b: pd.Series) -> pd.Series:
    """Equivalent to ta.crossunder(a, b)."""
    crossed = (a < b) & (a.shift(1) >= b.shift(1))
    return crossed.fillna(0.0).astype(bool)


def _normalize_qty(qty: float, config: HMACrossoverConfig) -> float:
    if pd.isna(qty) or qty <= 0:
        return 0.0

    qty = float(qty)

    if not config.allow_fractional_quantity:
        qty = math.floor(qty)

    if config.quantity_precision is not None:
        qty = round(qty, config.quantity_precision)

    return max(qty, 0.0)


def _side_name(side: int) -> str:
    if side > 0:
        return "long"
    if side < 0:
        return "short"
    return "flat"


def _costs_for_side(side: int, config: HMACrossoverConfig) -> Tuple[float, float]:
    """
    Returns (commission_per_order, slippage_per_side) in account/symbol currency.
    This conversion assumes account currency == symbol currency.
    """
    if side > 0:
        return (
            float(config.estimated_commission_per_order_long),
            float(config.estimated_slippage_per_side_long),
        )
    if side < 0:
        return (
            float(config.estimated_commission_per_order_short),
            float(config.estimated_slippage_per_side_short),
        )
    return 0.0, 0.0


def _round_trip_costs_for_side(side: int, qty: float, config: HMACrossoverConfig) -> float:
    if qty <= 0 or side == 0:
        return 0.0
    commission_per_order, slippage_per_side = _costs_for_side(side, config)
    return commission_per_order * 2.0 + slippage_per_side * 2.0


# Shared indicator references (populated by backtest_engine multiprocessing workers)
_SHARED_HMA_GRID: np.ndarray | None = None
_SHARED_HMA_LENGTH_TO_IDX: dict[int, int] | None = None


def add_hma_crossover_features(
    df: pd.DataFrame,
    config: Optional[HMACrossoverConfig] = None,
    *,
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Adds the non-stateful HMA columns and raw crossover signals.

    Output columns added:
        hma_fast
        hma_slow
        raw_long_signal
        raw_short_signal
        long_signal
        short_signal
        hma_regime

    When *use_cache* is True (the default) the result is memoised per
    (data fingerprint, fast_len, slow_len, source_col, confirm_on_close)
    so that optimizer iterations that share indicator lengths skip the
    expensive rolling WMA computation entirely.
    """
    config = config or HMACrossoverConfig()

    if config.source_col not in df.columns:
        raise ValueError(f"Missing source column: {config.source_col!r}")

    # ---- check shared memory grid first ----
    global _SHARED_HMA_GRID, _SHARED_HMA_LENGTH_TO_IDX
    if _SHARED_HMA_GRID is not None and _SHARED_HMA_LENGTH_TO_IDX is not None:
        fast_len_int = int(config.fast_len)
        slow_len_int = int(config.slow_len)
        if fast_len_int in _SHARED_HMA_LENGTH_TO_IDX and slow_len_int in _SHARED_HMA_LENGTH_TO_IDX:
            out = df.copy()
            fast_idx = _SHARED_HMA_LENGTH_TO_IDX[fast_len_int]
            slow_idx = _SHARED_HMA_LENGTH_TO_IDX[slow_len_int]

            # Direct O(1) assignment from shared memory view
            out["hma_fast"] = _SHARED_HMA_GRID[fast_idx]
            out["hma_slow"] = _SHARED_HMA_GRID[slow_idx]

            out["raw_long_signal"] = crossover(out["hma_fast"], out["hma_slow"])
            out["raw_short_signal"] = crossunder(out["hma_fast"], out["hma_slow"])

            if config.confirm_on_close:
                out["long_signal"] = out["raw_long_signal"]
                out["short_signal"] = out["raw_short_signal"]
            else:
                out["long_signal"] = out["raw_long_signal"]
                out["short_signal"] = out["raw_short_signal"]

            out["hma_regime"] = np.select(
                [
                    out["hma_fast"].isna() | out["hma_slow"].isna(),
                    out["hma_fast"] >= out["hma_slow"],
                    out["hma_fast"] < out["hma_slow"],
                ],
                [np.nan, 1.0, -1.0],
                default=np.nan,
            )
            return out

    # ---- cache look-up ----
    if use_cache:
        key = _make_feature_cache_key(
            df,
            fast_len=config.fast_len,
            slow_len=config.slow_len,
            source_col=config.source_col,
            confirm_on_close=config.confirm_on_close,
        )
        cached = _HMA_FEATURE_CACHE.get(key)
        if cached is not None:
            return cached

    # ---- compute ----
    out = df.copy()
    source = out[config.source_col].astype(float)

    out["hma_fast"] = hma(source, config.fast_len)
    out["hma_slow"] = hma(source, config.slow_len)

    out["raw_long_signal"] = crossover(out["hma_fast"], out["hma_slow"])
    out["raw_short_signal"] = crossunder(out["hma_fast"], out["hma_slow"])

    # On completed historical OHLCV data, every bar is effectively confirmed.
    # The flag is retained for parity with the Pine input.
    if config.confirm_on_close:
        out["long_signal"] = out["raw_long_signal"]
        out["short_signal"] = out["raw_short_signal"]
    else:
        out["long_signal"] = out["raw_long_signal"]
        out["short_signal"] = out["raw_short_signal"]

    out["hma_regime"] = np.select(
        [
            out["hma_fast"].isna() | out["hma_slow"].isna(),
            out["hma_fast"] >= out["hma_slow"],
            out["hma_fast"] < out["hma_slow"],
        ],
        [np.nan, 1.0, -1.0],
        default=np.nan,
    )

    # ---- store in cache (with simple LRU eviction) ----
    if use_cache:
        if len(_HMA_FEATURE_CACHE) >= _HMA_CACHE_MAX_SIZE:
            # Drop the oldest entry (dicts are insertion-ordered in Python 3.7+)
            _HMA_FEATURE_CACHE.pop(next(iter(_HMA_FEATURE_CACHE)))
        _HMA_FEATURE_CACHE[key] = out

    return out


def run_hma_crossover_strategy(
    df: pd.DataFrame,
    config: Optional[HMACrossoverConfig] = None,
    early_stop_drawdown_pct: Optional[float] = None,
    compute_full_metrics: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Stateful conversion of the Pine strategy.

    Returns:
        result_df:
            Original dataset plus HMA signals, position state, bucket metrics,
            estimated net PnL columns, TP/SL levels, safety flags, and generated
            order comments.

        trades_df:
            One row per closed trade.

    Required columns:
        close
        config.source_col
        config.next_bar_execution_price_col when execute_on_next_bar=True

    Notes:
        - Currency conversion functions from Pine are treated as identity
          conversions. Use config.point_value for futures/contracts.
        - Orders default to next-bar open fills to match
          process_orders_on_close=false more closely.
        - Intrabar high/low stop/limit simulation is not used because the Pine
          script exits via strategy.close() when net thresholds are detected.
    """
    config = config or HMACrossoverConfig()

    required = {"close", config.source_col}
    if config.execute_on_next_bar:
        required.add(config.next_bar_execution_price_col)

    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    out = add_hma_crossover_features(df, config)

    broker = BrokerSimulator(
        BrokerConfig(
            initial_capital=float(config.initial_capital_bucket),
            execute_on_next_bar=bool(config.execute_on_next_bar),
            execution_price_col=str(config.next_bar_execution_price_col),
            commission_fixed_long=float(config.estimated_commission_per_order_long),
            commission_fixed_short=float(config.estimated_commission_per_order_short),
            slippage_per_side_long=float(config.estimated_slippage_per_side_long),
            slippage_per_side_short=float(config.estimated_slippage_per_side_short),
            point_value=float(config.point_value),
            allow_fractional_quantity=bool(config.allow_fractional_quantity),
            quantity_precision=config.quantity_precision,
            account_currency=config.account_currency if config.account_currency is not None else "EUR",
            asset_currency=config.asset_currency if config.asset_currency is not None else "EUR",
            fx_rate_provider=config.fx_rate_provider,
        )
    )

    capital_bucket = bucket_clamp(
        config.initial_capital_bucket,
        config.max_capital_bucket,
    )
    
    # Track peak equity for early stopping
    peak_equity = broker.cash
    withdrawn_profit = 0.0

    # Position state. side: 1 = long, -1 = short, 0 = flat.
    side = 0
    qty = 0.0
    entry_price = np.nan
    entry_index: Any = None
    entry_bar_number: Optional[int] = None

    pending_order: Optional[Dict[str, Any]] = None
    trades: List[Dict[str, Any]] = []
    
    from collections import defaultdict
    records: Dict[str, List[Any]] = defaultdict(list)

    def current_gross_pnl(mark_price: float, timestamp: Any) -> float:
        if side == 0 or qty <= 0 or pd.isna(entry_price) or pd.isna(mark_price):
            return 0.0
        fx_rate = broker.fx_rate(timestamp)
        mark_price_account = mark_price * fx_rate
        if side > 0:
            return (mark_price_account - entry_price) * qty * config.point_value
        return (entry_price - mark_price_account) * qty * config.point_value

    def update_bucket_with_trade_pnl(net_pnl: float) -> None:
        nonlocal capital_bucket, withdrawn_profit
        raw_bucket = capital_bucket + float(net_pnl)
        if raw_bucket > config.max_capital_bucket:
            withdrawn_profit += raw_bucket - config.max_capital_bucket
        capital_bucket = bucket_clamp(raw_bucket, config.max_capital_bucket)

    def close_position(
        exit_price: float,
        exit_index: Any,
        exit_bar_number: int,
        comment: str,
    ) -> Dict[str, Any]:
        nonlocal side, qty, entry_price, entry_index, entry_bar_number

        if side == 0 or qty <= 0:
            return {
                "filled_order": None,
                "filled_comment": None,
                "realized_gross_pnl_on_fill": 0.0,
                "realized_costs_on_fill": 0.0,
                "realized_net_pnl_on_fill": 0.0,
            }

        closed_side = side
        closed_qty = qty
        closed_entry_price = entry_price
        close_order = Order(
            id=f"close-{exit_bar_number}-{len(trades)}",
            side="sell" if closed_side > 0 else "buy",
            quantity=closed_qty,
            comment=comment,
            cost_side="long" if closed_side > 0 else "short",
        )
        broker.fill_order(close_order, exit_index, exit_price)
        broker_trade = broker.closed_trades[-1] if broker.closed_trades else None
        gross = float(broker_trade.gross_pnl) if broker_trade is not None else current_gross_pnl(exit_price, exit_index)
        costs = float(broker_trade.commission) if broker_trade is not None else _round_trip_costs_for_side(closed_side, closed_qty, config)
        net = (gross - costs) if config.apply_estimated_costs_to_realized_pnl else gross

        trades.append(
            {
                "entry_index": entry_index,
                "exit_index": exit_index,
                "entry_bar": entry_bar_number,
                "exit_bar": exit_bar_number,
                "side": _side_name(closed_side),
                "qty": closed_qty,
                "entry_price": closed_entry_price,
                "exit_price": exit_price,
                "gross_pnl": gross,
                "estimated_costs": costs,
                "net_pnl": net,
                "exit_comment": comment,
                "bars_held": (
                    exit_bar_number - entry_bar_number
                    if entry_bar_number is not None
                    else np.nan
                ),
            }
        )

        update_bucket_with_trade_pnl(net)

        side = 0
        qty = 0.0
        entry_price = np.nan
        entry_index = None
        entry_bar_number = None

        return {
            "filled_order": "close",
            "filled_comment": comment,
            "realized_gross_pnl_on_fill": gross,
            "realized_costs_on_fill": costs,
            "realized_net_pnl_on_fill": net,
        }

    def open_position(
        new_side: int,
        new_qty: float,
        fill_price: float,
        fill_index: Any,
        fill_bar_number: int,
        comment: str,
    ) -> Dict[str, Any]:
        nonlocal side, qty, entry_price, entry_index, entry_bar_number

        new_qty = _normalize_qty(new_qty, config)
        if new_side == 0 or new_qty <= 0 or pd.isna(fill_price) or fill_price <= 0:
            return {
                "filled_order": None,
                "filled_comment": None,
                "realized_gross_pnl_on_fill": 0.0,
                "realized_costs_on_fill": 0.0,
                "realized_net_pnl_on_fill": 0.0,
            }

        side = int(np.sign(new_side))
        open_order = Order(
            id=f"entry-{fill_bar_number}-{len(trades)}",
            side="buy" if side > 0 else "sell",
            quantity=new_qty,
            comment=comment,
            cost_side="long" if side > 0 else "short",
        )
        fill = broker.fill_order(open_order, fill_index, fill_price)
        qty = float(fill.quantity) if fill is not None else new_qty
        entry_price = float(fill.price) if fill is not None else float(fill_price)
        entry_index = fill_index
        entry_bar_number = fill_bar_number

        return {
            "filled_order": "entry",
            "filled_comment": comment,
            "realized_gross_pnl_on_fill": 0.0,
            "realized_costs_on_fill": 0.0,
            "realized_net_pnl_on_fill": 0.0,
        }

    def execute_order(
        order: Dict[str, Any],
        fill_price: float,
        fill_index: Any,
        fill_bar_number: int,
    ) -> Dict[str, Any]:
        """
        Executes one generated strategy order.
        order["kind"] can be: "enter", "close", or "reverse".
        """
        if order is None:
            return {
                "filled_order": None,
                "filled_comment": None,
                "realized_gross_pnl_on_fill": 0.0,
                "realized_costs_on_fill": 0.0,
                "realized_net_pnl_on_fill": 0.0,
            }

        kind = order["kind"]
        target_side = int(order.get("side", 0))
        order_qty = float(order.get("qty", 0.0))
        comment = str(order.get("comment", ""))

        if kind == "close":
            return close_position(fill_price, fill_index, fill_bar_number, comment)

        if kind == "enter":
            return open_position(target_side, order_qty, fill_price, fill_index, fill_bar_number, comment)

        if kind == "reverse":
            old_close = close_position(fill_price, fill_index, fill_bar_number, comment)
            new_open = open_position(target_side, order_qty, fill_price, fill_index, fill_bar_number, comment)

            return {
                "filled_order": "reverse",
                "filled_comment": comment,
                "realized_gross_pnl_on_fill": old_close["realized_gross_pnl_on_fill"],
                "realized_costs_on_fill": old_close["realized_costs_on_fill"],
                "realized_net_pnl_on_fill": old_close["realized_net_pnl_on_fill"],
                "opened_after_reverse": new_open["filled_order"] == "entry",
            }

        raise ValueError(f"Unsupported order kind: {kind}")

    def make_close_order(comment: str) -> Dict[str, Any]:
        return {"kind": "close", "side": 0, "qty": 0.0, "comment": comment}

    def make_entry_order(new_side: int, order_qty: float, comment: str) -> Dict[str, Any]:
        return {"kind": "enter", "side": new_side, "qty": order_qty, "comment": comment}

    def make_reverse_order(new_side: int, order_qty: float, comment: str) -> Dict[str, Any]:
        return {"kind": "reverse", "side": new_side, "qty": order_qty, "comment": comment}

    n = len(out)
    index = out.index
    close_arr = out["close"].to_numpy(dtype=float)
    fill_price_arr = out[config.next_bar_execution_price_col].to_numpy(dtype=float)
    long_signal_arr = out["long_signal"].to_numpy(dtype=bool)
    short_signal_arr = out["short_signal"].to_numpy(dtype=bool)

    for bar_number in range(n):
        idx = index[bar_number]
        fill_info = {
            "filled_order": None,
            "filled_comment": None,
            "realized_gross_pnl_on_fill": 0.0,
            "realized_costs_on_fill": 0.0,
            "realized_net_pnl_on_fill": 0.0,
        }

        # Fill order generated on the prior bar.
        if pending_order is not None:
            fill_price = float(fill_price_arr[bar_number])
            fill_info = execute_order(pending_order, fill_price, idx, bar_number)
            pending_order = None

        close_price = float(close_arr[bar_number])

        # Phase 2: Early Stopping (Ruin-based pruning)
        current_equity = broker.mark_to_market_equity(close_price, idx)
        if current_equity > peak_equity:
            peak_equity = current_equity
        
        if early_stop_drawdown_pct is not None and early_stop_drawdown_pct > 0 and peak_equity > 0:
            drawdown_pct = (peak_equity - current_equity) / peak_equity * 100.0
            if drawdown_pct >= early_stop_drawdown_pct:
                # Early stop triggered: build partial state and add ruin trade
                partial_state = pd.DataFrame(records, index=out.index[:len(records)])
                partial_result = pd.concat([out.iloc[:len(records)], partial_state], axis=1)
                trades.append({
                    "entry_index": index[0],
                    "exit_index": idx,
                    "entry_bar": 0,
                    "exit_bar": bar_number,
                    "side": "LONG",
                    "qty": 1.0,
                    "entry_price": peak_equity,
                    "exit_price": 0.0,
                    "gross_pnl": -peak_equity,
                    "estimated_costs": 0.0,
                    "net_pnl": -peak_equity,
                    "exit_comment": "RUIN_EARLY_STOP",
                    "bars_held": bar_number,
                })
                return partial_result, pd.DataFrame(trades)

        in_long = side > 0
        in_short = side < 0
        flat = side == 0
        abs_pos_size = abs(qty)

        bars_in_trade = (
            bar_number - entry_bar_number
            if entry_bar_number is not None
            else 0
        )

        gross_pnl_estimate = current_gross_pnl(close_price, idx)
        estimated_round_trip_costs = _round_trip_costs_for_side(side, abs_pos_size, config)
        estimated_net_if_closed_now = gross_pnl_estimate - estimated_round_trip_costs

        reversal_net_filter_passed = (
            estimated_net_if_closed_now >= config.min_net_profit_after_costs
        )

        estimated_bucket_after_close = bucket_clamp(
            capital_bucket + estimated_net_if_closed_now,
            config.max_capital_bucket,
        )

        quantity_point_value = abs_pos_size * config.point_value
        entry_position_value = (
            entry_price * abs_pos_size * config.point_value
            if abs_pos_size > 0 and not pd.isna(entry_price)
            else 0.0
        )

        take_profit_net_threshold = (
            entry_position_value * config.take_profit_net_percent / 100.0
        )
        stop_loss_net_threshold = (
            entry_position_value * config.stop_loss_net_percent / 100.0
        )

        if config.safety_max_net_loss_mode == "Cash amount":
            safety_max_net_loss_threshold = float(config.safety_max_net_loss_cash)
        else:
            safety_max_net_loss_threshold = (
                entry_position_value * config.safety_max_net_loss_percent / 100.0
            )

        safety_direction_allowed = (
            config.safety_stop_applies_to == "Both"
            or (config.safety_stop_applies_to == "Long only" and in_long)
            or (config.safety_stop_applies_to == "Short only" and in_short)
        )
        safety_loss_triggered = (
            safety_max_net_loss_threshold > 0
            and estimated_net_if_closed_now <= -safety_max_net_loss_threshold
        )
        safety_bars_triggered = (
            config.safety_max_bars_in_trade > 0
            and bars_in_trade >= config.safety_max_bars_in_trade
        )

        if config.safety_stop_mode == "Net loss only":
            safety_condition = safety_loss_triggered
        elif config.safety_stop_mode == "Max bars only":
            safety_condition = safety_bars_triggered
        elif config.safety_stop_mode == "Net loss OR max bars":
            safety_condition = safety_loss_triggered or safety_bars_triggered
        else:
            safety_condition = safety_loss_triggered and safety_bars_triggered

        safety_stop_triggered = (
            config.use_safety_stop and safety_direction_allowed and safety_condition
        )

        hit_net_take_profit = (
            config.use_net_bracket_exits
            and abs_pos_size > 0
            and estimated_net_if_closed_now >= take_profit_net_threshold
        )
        hit_net_stop_loss = (
            config.use_net_bracket_exits
            and abs_pos_size > 0
            and estimated_net_if_closed_now <= -stop_loss_net_threshold
        )

        if in_long and quantity_point_value > 0:
            long_take_profit_price = entry_price + (
                take_profit_net_threshold + estimated_round_trip_costs
            ) / quantity_point_value
            long_stop_loss_price = entry_price + (
                estimated_round_trip_costs - stop_loss_net_threshold
            ) / quantity_point_value
        else:
            long_take_profit_price = np.nan
            long_stop_loss_price = np.nan

        if in_short and quantity_point_value > 0:
            short_take_profit_price = entry_price - (
                take_profit_net_threshold + estimated_round_trip_costs
            ) / quantity_point_value
            short_stop_loss_price = entry_price + (
                stop_loss_net_threshold - estimated_round_trip_costs
            ) / quantity_point_value
        else:
            short_take_profit_price = np.nan
            short_stop_loss_price = np.nan

        allow_long = config.trade_direction_mode != "Short only"
        allow_short = config.trade_direction_mode != "Long only"

        entry_allowed_by_cap = close_price <= config.max_entry_price and capital_bucket > 0
        flat_entry_qty = _normalize_qty(qty_from_bucket(capital_bucket, close_price), config)
        reverse_entry_qty = _normalize_qty(
            qty_from_bucket(estimated_bucket_after_close, close_price),
            config,
        )

        hold_until_profitable = (
            config.fee_mode == "Parametric: hold until net covers fees"
        )
        exit_only_no_reverse = (
            config.fee_mode == "Parametric: exit only, no forced reversal"
        )
        disable_fee_filter = (
            config.fee_mode == "Disabled: always reverse/close on opposite signal"
        )

        long_signal = bool(long_signal_arr[bar_number])
        short_signal = bool(short_signal_arr[bar_number])

        generated_order: Optional[Dict[str, Any]] = None

        # 1) Last-resort safety stop has highest priority.
        if safety_stop_triggered and in_long:
            generated_order = make_close_order("Safety Stop Long")
        elif safety_stop_triggered and in_short:
            generated_order = make_close_order("Safety Stop Short")

        # 2) Optional explicit net TP/SL exits.
        elif in_long and hit_net_take_profit:
            generated_order = make_close_order("Net TP Long")
        elif in_long and hit_net_stop_loss:
            generated_order = make_close_order("Net SL Long")
        elif in_short and hit_net_take_profit:
            generated_order = make_close_order("Net TP Short")
        elif in_short and hit_net_stop_loss:
            generated_order = make_close_order("Net SL Short")

        else:
            # 3) Flat entries use the current capped bucket.
            if flat and entry_allowed_by_cap and flat_entry_qty > 0:
                if long_signal and allow_long:
                    generated_order = make_entry_order(1, flat_entry_qty, "BUY")
                elif short_signal and allow_short:
                    generated_order = make_entry_order(-1, flat_entry_qty, "SELL")

            # 4) Opposite signal while long.
            if generated_order is None and in_long and short_signal:
                if disable_fee_filter:
                    if close_price <= config.max_entry_price and reverse_entry_qty > 0:
                        if allow_short:
                            generated_order = make_reverse_order(-1, reverse_entry_qty, "SELL REV")
                        else:
                            generated_order = make_close_order("Exit Long")
                    else:
                        generated_order = make_close_order("Exit Long")

                elif exit_only_no_reverse or not allow_short:
                    generated_order = make_close_order("Exit Long")

                elif hold_until_profitable and reversal_net_filter_passed:
                    if close_price <= config.max_entry_price and reverse_entry_qty > 0:
                        if allow_short:
                            generated_order = make_reverse_order(-1, reverse_entry_qty, "SELL REV")
                        else:
                            generated_order = make_close_order("Exit Long")
                    else:
                        generated_order = make_close_order("Exit Long")

            # 5) Opposite signal while short.
            if generated_order is None and in_short and long_signal:
                if disable_fee_filter:
                    if close_price <= config.max_entry_price and reverse_entry_qty > 0:
                        if allow_long:
                            generated_order = make_reverse_order(1, reverse_entry_qty, "BUY REV")
                        else:
                            generated_order = make_close_order("Exit Short")
                    else:
                        generated_order = make_close_order("Exit Short")

                elif exit_only_no_reverse or not allow_long:
                    generated_order = make_close_order("Exit Short")

                elif hold_until_profitable and reversal_net_filter_passed:
                    if close_price <= config.max_entry_price and reverse_entry_qty > 0:
                        if allow_long:
                            generated_order = make_reverse_order(1, reverse_entry_qty, "BUY REV")
                        else:
                            generated_order = make_close_order("Exit Short")
                    else:
                        generated_order = make_close_order("Exit Short")

        signal_order = None
        signal_comment = None
        signal_qty = np.nan
        signal_side = 0

        if generated_order is not None:
            signal_order = generated_order["kind"]
            signal_comment = generated_order["comment"]
            signal_qty = generated_order.get("qty", np.nan)
            signal_side = generated_order.get("side", 0)

            if config.execute_on_next_bar:
                pending_order = generated_order
            else:
                same_bar_fill = execute_order(generated_order, close_price, idx, bar_number)
                fill_info = same_bar_fill

        if compute_full_metrics:
            records["position_side"].append(side)
            records["position_label"].append(_side_name(side))
            records["position_size"].append(side * qty)
            records["position_abs_size"].append(abs(qty))
            records["position_avg_price"].append(entry_price)
            records["in_long"].append(side > 0)
            records["in_short"].append(side < 0)
            records["flat"].append(side == 0)
            records["capital_bucket"].append(capital_bucket)
            records["withdrawn_profit"].append(withdrawn_profit)
            records["bars_in_trade"].append(bars_in_trade)
            records["gross_pnl_estimate"].append(gross_pnl_estimate)
            records["estimated_round_trip_costs"].append(estimated_round_trip_costs)
            records["estimated_net_if_closed_now"].append(estimated_net_if_closed_now)
            records["reversal_net_filter_passed"].append(reversal_net_filter_passed)
            records["estimated_bucket_after_close"].append(estimated_bucket_after_close)
            records["entry_position_value"].append(entry_position_value)
            records["take_profit_net_threshold"].append(take_profit_net_threshold)
            records["stop_loss_net_threshold"].append(stop_loss_net_threshold)
            records["safety_max_net_loss_threshold"].append(safety_max_net_loss_threshold)
            records["safety_loss_triggered"].append(safety_loss_triggered)
            records["safety_bars_triggered"].append(safety_bars_triggered)
            records["safety_stop_triggered"].append(safety_stop_triggered)
            records["hit_net_take_profit"].append(hit_net_take_profit)
            records["hit_net_stop_loss"].append(hit_net_stop_loss)
            records["long_take_profit_price"].append(long_take_profit_price)
            records["long_stop_loss_price"].append(long_stop_loss_price)
            records["short_take_profit_price"].append(short_take_profit_price)
            records["short_stop_loss_price"].append(short_stop_loss_price)
            records["entry_allowed_by_cap"].append(entry_allowed_by_cap)
            records["flat_entry_qty"].append(flat_entry_qty)
            records["reverse_entry_qty"].append(reverse_entry_qty)
            records["signal_order"].append(signal_order)
            records["signal_comment"].append(signal_comment)
            records["signal_qty"].append(signal_qty)
            records["signal_side"].append(signal_side)
            records["filled_order"].append(fill_info.get("filled_order"))
            records["filled_comment"].append(fill_info.get("filled_comment"))
            records["realized_gross_pnl_on_fill"].append(fill_info.get("realized_gross_pnl_on_fill", 0.0))
            records["realized_costs_on_fill"].append(fill_info.get("realized_costs_on_fill", 0.0))
            records["realized_net_pnl_on_fill"].append(fill_info.get("realized_net_pnl_on_fill", 0.0))
        else:
            records["realized_net_pnl_on_fill"].append(fill_info.get("realized_net_pnl_on_fill", 0.0))
            records["estimated_net_if_closed_now"].append(estimated_net_if_closed_now)
            records["position_size"].append(side * qty)
            records["position_avg_price"].append(entry_price)

    state_df = pd.DataFrame(records, index=out.index)
    if compute_full_metrics:
        result_df = pd.concat([out, state_df], axis=1)
    else:
        result_df = state_df
    trades_df = pd.DataFrame(trades)

    return result_df, trades_df


# Example usage:
#
# config = HMACrossoverConfig()
# result, trades = run_hma_crossover_strategy(ohlcv_df, config)
#
# ML-friendly feature subset:
# feature_cols = [
#     "hma_fast",
#     "hma_slow",
#     "hma_regime",
#     "raw_long_signal",
#     "raw_short_signal",
#     "long_signal",
#     "short_signal",
#     "capital_bucket",
#     "withdrawn_profit",
#     "estimated_net_if_closed_now",
#     "bars_in_trade",
# ]
# model_df = result[feature_cols].copy()
