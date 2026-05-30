"""
Bjorgum-Double-Tap.py

Python conversion of "Bjorgum Double Tap" / "Bj Double Tap" Pine Script strategy.

Main entry points:
    add_bjorgum_double_tap_features(df, config)
    run_bjorgum_double_tap_strategy(df, config)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple

import math
import numpy as np
import pandas as pd
import numba

from backtest_engine.broker import BrokerConfig, BrokerSimulator, Order


@numba.njit(cache=False)
def _compute_bjorgum_signals_numba(
    n: int,
    is_hbar: np.ndarray,
    is_lbar: np.ndarray,
    piv_highs: np.ndarray,
    piv_lows: np.ndarray,
    closes: np.ndarray,
    dLong: bool,
    dShort: bool,
    tol: float,
    fib: float,
    stopPer: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    long_signal = np.zeros(n, dtype=np.bool_)
    short_signal = np.zeros(n, dtype=np.bool_)
    pattern_tp = np.full(n, np.nan, dtype=np.float64)
    pattern_sl = np.full(n, np.nan, dtype=np.float64)

    logs_idx = np.zeros(5, dtype=np.int64)
    logs_val = np.zeros(5, dtype=np.float64)
    logs_traded = np.zeros(5, dtype=np.int64)
    num_logs = 0
    dir_val = 1

    for i in range(n):
        hbar_i = is_hbar[i]
        lbar_i = is_lbar[i]
        
        dir_prev = dir_val
        if hbar_i:
            dir_val = 1
        elif lbar_i:
            dir_val = 0
            
        dirUp = (dir_val != dir_prev) and (dir_val == 1)
        dirDn = (dir_val != dir_prev) and (dir_val == 0)
        
        setUp = hbar_i and (dir_val == 1)
        setDn = lbar_i and (dir_val == 0)
        
        # Append logic
        if dirUp:
            if num_logs < 5:
                logs_idx[num_logs] = i
                logs_val[num_logs] = piv_highs[i]
                logs_traded[num_logs] = 0
                num_logs += 1
            else:
                for k in range(4):
                    logs_idx[k] = logs_idx[k+1]
                    logs_val[k] = logs_val[k+1]
                    logs_traded[k] = logs_traded[k+1]
                logs_idx[4] = i
                logs_val[4] = piv_highs[i]
                logs_traded[4] = 0
        elif dirDn:
            if num_logs < 5:
                logs_idx[num_logs] = i
                logs_val[num_logs] = piv_lows[i]
                logs_traded[num_logs] = 0
                num_logs += 1
            else:
                for k in range(4):
                    logs_idx[k] = logs_idx[k+1]
                    logs_val[k] = logs_val[k+1]
                    logs_traded[k] = logs_traded[k+1]
                logs_idx[4] = i
                logs_val[4] = piv_lows[i]
                logs_traded[4] = 0

        if setUp and num_logs > 0:
            if logs_val[num_logs - 1] < piv_highs[i]:
                logs_idx[num_logs - 1] = i
                logs_val[num_logs - 1] = piv_highs[i]
                
        if setDn and num_logs > 0:
            if logs_val[num_logs - 1] > piv_lows[i]:
                logs_idx[num_logs - 1] = i
                logs_val[num_logs - 1] = piv_lows[i]
                
        # Evaluate patterns
        if num_logs >= 5:
            x1 = logs_idx[0]
            y1 = logs_val[0]
            
            x2 = logs_idx[1]
            y2 = logs_val[1]
            
            x3 = logs_idx[2]
            y3 = logs_val[2]
            
            x4 = logs_idx[3]
            y4 = logs_val[3]
            traded4 = logs_traded[3]
            
            traded = (traded4 == 1)
            height = (y2 + y4) / 2.0 - y3
            
            _high = y2 + height * (tol / 100.0)
            _low = y2 - height * (tol / 100.0)
            
            close_i = closes[i]
            close_prev = closes[i-1] if i > 0 else closes[0]
            
            # Double Top (m=1)
            if dShort and not traded:
                if y1 < y3 and y4 <= _high and y4 >= _low and close_i < y3 and close_prev >= y3:
                    short_signal[i] = True
                    logs_traded[3] = 1
                    pattern_tp[i] = y3 - height * (fib / 100.0)
                    y6 = max(y2, y4)
                    pattern_sl[i] = y6 - height * (stopPer / 100.0)
                    
            # Double Bottom (m=-1)
            if dLong and not traded and not short_signal[i]:
                if y1 > y3 and y4 >= _high and y4 <= _low and close_i > y3 and close_prev <= y3:
                    long_signal[i] = True
                    logs_traded[3] = 1
                    pattern_tp[i] = y3 - height * (fib / 100.0)
                    y6 = min(y2, y4)
                    pattern_sl[i] = y6 - height * (stopPer / 100.0)

    return long_signal, short_signal, pattern_tp, pattern_sl


_FEATURE_CACHE: dict = {}
_CACHE_MAX_SIZE: int = 512

def _make_feature_cache_key(
    df: pd.DataFrame,
    length: int,
    lookback: int,
    atr_length: int,
) -> tuple:
    src = df['close'].to_numpy(dtype=float, copy=False)
    n = len(src)
    boundary = src[:4].tobytes() + src[max(0, n - 4):].tobytes()
    return (id(src), n, hash(boundary), length, lookback, atr_length)

def clear_feature_cache() -> None:
    _FEATURE_CACHE.clear()

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
class BjorgumDoubleTapConfig:
    # Detection and Trade Parameters
    dLong: bool = True
    dShort: bool = True
    FLIP: bool = True
    tol: float = 15.0
    length: int = 50
    fib: float = 100.0
    stopPer: float = 0.0
    offset: int = 30
    
    # Trailing Stop Parameters
    atrStop: bool = False
    atrLength: int = 14
    atrMult: float = 1.0
    lookback: int = 5
    
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

    apply_estimated_costs_to_realized_pnl: bool = True
    allow_fractional_quantity: bool = True
    quantity_precision: Optional[int] = None

    # Currency and FX provider overrides
    asset_currency: Optional[str] = None
    account_currency: Optional[str] = None
    fx_rate_provider: Optional[object] = None


def bucket_clamp(value: float, bucket_max: float) -> float:
    if pd.isna(value):
        value = 0.0
    return max(min(float(value), float(bucket_max)), 0.0)

def qty_from_bucket(bucket: float, price: float) -> float:
    if pd.isna(price) or price <= 0:
        return 0.0
    return float(bucket) / float(price)

def _normalize_qty(qty: float, config: BjorgumDoubleTapConfig) -> float:
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

def _costs_for_side(side: int, config: BjorgumDoubleTapConfig) -> Tuple[float, float]:
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

def _round_trip_costs_for_side(side: int, qty: float, config: BjorgumDoubleTapConfig) -> float:
    if qty <= 0 or side == 0:
        return 0.0
    commission_per_order, slippage_per_side = _costs_for_side(side, config)
    return commission_per_order * 2.0 + slippage_per_side * 2.0


# Shared indicator references (populated by backtest_engine multiprocessing workers)
_SHARED_BJ_ATR_GRID: np.ndarray | None = None
_SHARED_BJ_ATR_KEYS: dict[int, int] | None = None
_SHARED_BJ_PIV_HIGH_GRID: np.ndarray | None = None
_SHARED_BJ_PIV_HIGH_KEYS: dict[int, int] | None = None
_SHARED_BJ_PIV_LOW_GRID: np.ndarray | None = None
_SHARED_BJ_PIV_LOW_KEYS: dict[int, int] | None = None
_SHARED_BJ_ROLL_MIN_GRID: np.ndarray | None = None
_SHARED_BJ_ROLL_MIN_KEYS: dict[int, int] | None = None
_SHARED_BJ_ROLL_MAX_GRID: np.ndarray | None = None
_SHARED_BJ_ROLL_MAX_KEYS: dict[int, int] | None = None


def add_bjorgum_double_tap_features(
    df: pd.DataFrame,
    config: Optional[BjorgumDoubleTapConfig] = None,
    *,
    use_cache: bool = True,
    compute_full_metrics: bool = True,
) -> pd.DataFrame:
    config = config or BjorgumDoubleTapConfig()

    required = {"high", "low", "close"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    if use_cache:
        key = _make_feature_cache_key(df, config.length, config.lookback, config.atrLength)
        cached = _FEATURE_CACHE.get(key)
        if cached is not None:
            return cached

    out = df.copy()
    n = len(out)
    
    highs = out["high"].to_numpy(dtype=float)
    lows = out["low"].to_numpy(dtype=float)
    closes = out["close"].to_numpy(dtype=float)

    global _SHARED_BJ_ATR_GRID, _SHARED_BJ_ATR_KEYS
    global _SHARED_BJ_PIV_HIGH_GRID, _SHARED_BJ_PIV_HIGH_KEYS
    global _SHARED_BJ_PIV_LOW_GRID, _SHARED_BJ_PIV_LOW_KEYS
    global _SHARED_BJ_ROLL_MIN_GRID, _SHARED_BJ_ROLL_MIN_KEYS
    global _SHARED_BJ_ROLL_MAX_GRID, _SHARED_BJ_ROLL_MAX_KEYS

    use_shared = False
    if (
        _SHARED_BJ_ATR_GRID is not None and _SHARED_BJ_ATR_KEYS is not None and
        _SHARED_BJ_PIV_HIGH_GRID is not None and _SHARED_BJ_PIV_HIGH_KEYS is not None and
        _SHARED_BJ_PIV_LOW_GRID is not None and _SHARED_BJ_PIV_LOW_KEYS is not None and
        _SHARED_BJ_ROLL_MIN_GRID is not None and _SHARED_BJ_ROLL_MIN_KEYS is not None and
        _SHARED_BJ_ROLL_MAX_GRID is not None and _SHARED_BJ_ROLL_MAX_KEYS is not None
    ):
        length_int = int(config.length)
        atr_length_int = int(config.atrLength)
        lookback_int = int(config.lookback)

        if (
            atr_length_int in _SHARED_BJ_ATR_KEYS and
            length_int in _SHARED_BJ_PIV_HIGH_KEYS and
            length_int in _SHARED_BJ_PIV_LOW_KEYS and
            lookback_int in _SHARED_BJ_ROLL_MIN_KEYS and
            lookback_int in _SHARED_BJ_ROLL_MAX_KEYS
        ):
            atr_idx = _SHARED_BJ_ATR_KEYS[atr_length_int]
            piv_high_idx = _SHARED_BJ_PIV_HIGH_KEYS[length_int]
            piv_low_idx = _SHARED_BJ_PIV_LOW_KEYS[length_int]
            roll_min_idx = _SHARED_BJ_ROLL_MIN_KEYS[lookback_int]
            roll_max_idx = _SHARED_BJ_ROLL_MAX_KEYS[lookback_int]

            atr = _SHARED_BJ_ATR_GRID[atr_idx]
            piv_highs = _SHARED_BJ_PIV_HIGH_GRID[piv_high_idx]
            piv_lows = _SHARED_BJ_PIV_LOW_GRID[piv_low_idx]
            s_low = _SHARED_BJ_ROLL_MIN_GRID[roll_min_idx] - (atr * config.atrMult)
            s_high = _SHARED_BJ_ROLL_MAX_GRID[roll_max_idx] + (atr * config.atrMult)
            use_shared = True

    if not use_shared:
        # ATR Calculation
        prev_closes = np.roll(closes, 1)
        prev_closes[0] = closes[0]
        
        tr1 = highs - lows
        tr2 = np.abs(highs - prev_closes)
        tr3 = np.abs(lows - prev_closes)
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        
        tr_series = pd.Series(tr)
        atr = tr_series.ewm(alpha=1.0 / config.atrLength, adjust=False).mean().to_numpy()
        
        # sLow and sHigh (trailing stops)
        lows_series = pd.Series(lows)
        highs_series = pd.Series(highs)
        
        s_low = lows_series.rolling(config.lookback, min_periods=1).min().to_numpy() - (atr * config.atrMult)
        s_high = highs_series.rolling(config.lookback, min_periods=1).max().to_numpy() + (atr * config.atrMult)
        
        piv_highs = highs_series.rolling(config.length, min_periods=1).max().to_numpy()
        piv_lows = lows_series.rolling(config.length, min_periods=1).min().to_numpy()

    is_hbar = (highs == piv_highs)
    is_lbar = (lows == piv_lows)

    long_signal, short_signal, pattern_tp, pattern_sl = _compute_bjorgum_signals_numba(
        n,
        is_hbar,
        is_lbar,
        piv_highs,
        piv_lows,
        closes,
        bool(config.dLong),
        bool(config.dShort),
        float(config.tol),
        float(config.fib),
        float(config.stopPer),
    )

    if compute_full_metrics:
        out["sLow"] = s_low
        out["sHigh"] = s_high
        out["atr"] = atr
        out["long_signal"] = long_signal
        out["short_signal"] = short_signal
        out["pattern_tp"] = pattern_tp
        out["pattern_sl"] = pattern_sl
    else:
        # Optimization mode: keep only columns required by backtester loop setup
        cols_to_keep = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
        out = df[cols_to_keep].copy()
        out["sLow"] = s_low
        out["sHigh"] = s_high
        out["long_signal"] = long_signal
        out["short_signal"] = short_signal
        out["pattern_tp"] = pattern_tp
        out["pattern_sl"] = pattern_sl

    if use_cache:
        if len(_FEATURE_CACHE) >= _CACHE_MAX_SIZE:
            _FEATURE_CACHE.pop(next(iter(_FEATURE_CACHE)))
        _FEATURE_CACHE[key] = out

    return out


def run_bjorgum_double_tap_strategy(
    df: pd.DataFrame,
    config: Optional[BjorgumDoubleTapConfig] = None,
    early_stop_drawdown_pct: Optional[float] = None,
    compute_full_metrics: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    config = config or BjorgumDoubleTapConfig()

    required = {"high", "low", "close"}
    if config.execute_on_next_bar:
        required.add(config.next_bar_execution_price_col)

    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    import inspect
    sig = inspect.signature(add_bjorgum_double_tap_features)
    if "compute_full_metrics" in sig.parameters:
        out = add_bjorgum_double_tap_features(df, config, compute_full_metrics=compute_full_metrics)
    else:
        out = add_bjorgum_double_tap_features(df, config)


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
    
    peak_equity = broker.cash
    withdrawn_profit = 0.0

    side = 0
    qty = 0.0
    entry_price = np.nan
    entry_index: Any = None
    entry_bar_number: Optional[int] = None

    pending_order: Optional[Dict[str, Any]] = None
    trades: List[Dict[str, Any]] = []
    
    from collections import defaultdict
    records: Dict[str, List[Any]] = defaultdict(list)
    
    # Intrabar trade active tracking state
    trade_sl = np.nan
    trade_tp = np.nan
    trailing_active = False

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
        nonlocal trade_sl, trade_tp, trailing_active

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
        trade_sl = np.nan
        trade_tp = np.nan
        trailing_active = False

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
        signal_tp: float,
        signal_sl: float,
    ) -> Dict[str, Any]:
        nonlocal side, qty, entry_price, entry_index, entry_bar_number
        nonlocal trade_sl, trade_tp, trailing_active

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
        
        trade_sl = signal_sl
        trade_tp = signal_tp
        trailing_active = False

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
        signal_tp = order.get("tp", np.nan)
        signal_sl = order.get("sl", np.nan)

        if kind == "close":
            return close_position(fill_price, fill_index, fill_bar_number, comment)

        if kind == "enter":
            return open_position(target_side, order_qty, fill_price, fill_index, fill_bar_number, comment, signal_tp, signal_sl)

        if kind == "reverse":
            old_close = close_position(fill_price, fill_index, fill_bar_number, comment)
            new_open = open_position(target_side, order_qty, fill_price, fill_index, fill_bar_number, comment, signal_tp, signal_sl)
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

    def make_entry_order(new_side: int, order_qty: float, comment: str, tp: float, sl: float) -> Dict[str, Any]:
        return {"kind": "enter", "side": new_side, "qty": order_qty, "comment": comment, "tp": tp, "sl": sl}

    def make_reverse_order(new_side: int, order_qty: float, comment: str, tp: float, sl: float) -> Dict[str, Any]:
        return {"kind": "reverse", "side": new_side, "qty": order_qty, "comment": comment, "tp": tp, "sl": sl}

    n = len(out)
    index = out.index
    open_arr = out["open"].to_numpy(dtype=float)
    high_arr = out["high"].to_numpy(dtype=float)
    low_arr = out["low"].to_numpy(dtype=float)
    close_arr = out["close"].to_numpy(dtype=float)
    
    if config.execute_on_next_bar:
        fill_price_arr = out[config.next_bar_execution_price_col].to_numpy(dtype=float)
    else:
        fill_price_arr = close_arr
        
    long_signal_arr = out["long_signal"].to_numpy(dtype=bool)
    short_signal_arr = out["short_signal"].to_numpy(dtype=bool)
    pattern_tp_arr = out["pattern_tp"].to_numpy(dtype=float)
    pattern_sl_arr = out["pattern_sl"].to_numpy(dtype=float)
    s_low_arr = out["sLow"].to_numpy(dtype=float)
    s_high_arr = out["sHigh"].to_numpy(dtype=float)

    for bar_number in range(n):
        idx = index[bar_number]
        fill_info = {
            "filled_order": None,
            "filled_comment": None,
            "realized_gross_pnl_on_fill": 0.0,
            "realized_costs_on_fill": 0.0,
            "realized_net_pnl_on_fill": 0.0,
        }

        # 1. Fill order generated on the prior bar
        if pending_order is not None:
            fill_price = float(fill_price_arr[bar_number])
            fill_info = execute_order(pending_order, fill_price, idx, bar_number)
            pending_order = None

        close_price = float(close_arr[bar_number])
        high_price = float(high_arr[bar_number])
        low_price = float(low_arr[bar_number])
        open_price = float(open_arr[bar_number])

        # Early Stopping
        current_equity = broker.mark_to_market_equity(close_price, idx)
        if current_equity > peak_equity:
            peak_equity = current_equity
        
        if early_stop_drawdown_pct is not None and early_stop_drawdown_pct > 0 and peak_equity > 0:
            drawdown_pct = (peak_equity - current_equity) / peak_equity * 100.0
            if drawdown_pct >= early_stop_drawdown_pct:
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

        # 2. Intrabar Stop/Limit hit checking
        intrabar_exit_triggered = False
        
        if in_long:
            if config.atrStop:
                if not trailing_active and high_price >= trade_tp:
                    trailing_active = True
                    trade_sl = s_low_arr[bar_number]
                if trailing_active:
                    trade_sl = max(trade_sl, s_low_arr[bar_number])
            
            hit_sl = low_price <= trade_sl
            hit_tp = False if config.atrStop else (high_price >= trade_tp)
            
            if hit_sl or hit_tp:
                intrabar_exit_triggered = True
                if hit_sl and hit_tp:
                    fill_p = trade_sl
                    comment = "L Exit (SL+TP)"
                elif hit_sl:
                    fill_p = min(trade_sl, open_price)
                    comment = "L Exit (SL)"
                else:
                    fill_p = max(trade_tp, open_price)
                    comment = "L Exit (TP)"
                generated_order = make_close_order(comment)
                same_bar_fill = execute_order(generated_order, fill_p, idx, bar_number)
                if fill_info["filled_order"] is None:
                    fill_info = same_bar_fill
                in_long = False
                flat = True
                
        elif in_short:
            if config.atrStop:
                if not trailing_active and low_price <= trade_tp:
                    trailing_active = True
                    trade_sl = s_high_arr[bar_number]
                if trailing_active:
                    trade_sl = min(trade_sl, s_high_arr[bar_number])
                    
            hit_sl = high_price >= trade_sl
            hit_tp = False if config.atrStop else (low_price <= trade_tp)
            
            if hit_sl or hit_tp:
                intrabar_exit_triggered = True
                if hit_sl and hit_tp:
                    fill_p = trade_sl
                    comment = "S Exit (SL+TP)"
                elif hit_sl:
                    fill_p = max(trade_sl, open_price)
                    comment = "S Exit (SL)"
                else:
                    fill_p = min(trade_tp, open_price)
                    comment = "S Exit (TP)"
                generated_order = make_close_order(comment)
                same_bar_fill = execute_order(generated_order, fill_p, idx, bar_number)
                if fill_info["filled_order"] is None:
                    fill_info = same_bar_fill
                in_short = False
                flat = True

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
        pat_tp = pattern_tp_arr[bar_number]
        pat_sl = pattern_sl_arr[bar_number]

        generated_order: Optional[Dict[str, Any]] = None

        if safety_stop_triggered and in_long:
            generated_order = make_close_order("Safety Stop Long")
        elif safety_stop_triggered and in_short:
            generated_order = make_close_order("Safety Stop Short")
        elif in_long and hit_net_take_profit:
            generated_order = make_close_order("Net TP Long")
        elif in_long and hit_net_stop_loss:
            generated_order = make_close_order("Net SL Long")
        elif in_short and hit_net_take_profit:
            generated_order = make_close_order("Net TP Short")
        elif in_short and hit_net_stop_loss:
            generated_order = make_close_order("Net SL Short")
        else:
            if flat and entry_allowed_by_cap and flat_entry_qty > 0:
                if long_signal and allow_long:
                    generated_order = make_entry_order(1, flat_entry_qty, "Long", pat_tp, pat_sl)
                elif short_signal and allow_short:
                    generated_order = make_entry_order(-1, flat_entry_qty, "Short", pat_tp, pat_sl)

            if generated_order is None and in_long and config.FLIP and short_signal:
                if disable_fee_filter:
                    if close_price <= config.max_entry_price and reverse_entry_qty > 0:
                        if allow_short:
                            generated_order = make_reverse_order(-1, reverse_entry_qty, "Short REV", pat_tp, pat_sl)
                        else:
                            generated_order = make_close_order("Exit Long")
                    else:
                        generated_order = make_close_order("Exit Long")
                elif exit_only_no_reverse or not allow_short:
                    generated_order = make_close_order("Exit Long")
                elif hold_until_profitable and reversal_net_filter_passed:
                    if close_price <= config.max_entry_price and reverse_entry_qty > 0:
                        if allow_short:
                            generated_order = make_reverse_order(-1, reverse_entry_qty, "Short REV", pat_tp, pat_sl)
                        else:
                            generated_order = make_close_order("Exit Long")
                    else:
                        generated_order = make_close_order("Exit Long")

            if generated_order is None and in_short and config.FLIP and long_signal:
                if disable_fee_filter:
                    if close_price <= config.max_entry_price and reverse_entry_qty > 0:
                        if allow_long:
                            generated_order = make_reverse_order(1, reverse_entry_qty, "Long REV", pat_tp, pat_sl)
                        else:
                            generated_order = make_close_order("Exit Short")
                    else:
                        generated_order = make_close_order("Exit Short")
                elif exit_only_no_reverse or not allow_long:
                    generated_order = make_close_order("Exit Short")
                elif hold_until_profitable and reversal_net_filter_passed:
                    if close_price <= config.max_entry_price and reverse_entry_qty > 0:
                        if allow_long:
                            generated_order = make_reverse_order(1, reverse_entry_qty, "Long REV", pat_tp, pat_sl)
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
                if fill_info["filled_order"] is None:
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
    result_df = pd.concat([out, state_df], axis=1)
    trades_df = pd.DataFrame(trades)

    return result_df, trades_df
