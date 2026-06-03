"""
3Commas-Bot.py

Python conversion of:
"3Commas Bot" Pine Script strategy (TradingView v5)

Main entry points:
    add_3commas_bot_features(df, config)
        Adds MA, ATR, swing, signal, and filter columns only.

    run_3commas_bot_strategy(df, config)
        Adds features plus a stateful backtest approximation of the
        TradingView strategy, including ATR-based stops, R:R targets,
        optional ATR trailing stop, time/date filters, and max drawdown
        protection.

Conversion notes:
    - TradingView's strategy uses cash sizing (default_qty_type=strategy.cash).
      This conversion mirrors that via config.cash_per_trade / price.
    - process_orders_on_close=false means entries are generated on one bar and
      filled on the next bar open by default (config.execute_on_next_bar=True).
    - Stop/limit exits are checked intrabar using the current bar's high/low
      and filled at the stop/limit price when hit.
    - Intrabar trailing-stop updates use the bar's close/open[1] or current
      swing low/high depending on trail_source.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple

import math
import numpy as np
import pandas as pd

from backtest_engine.broker import BrokerConfig, BrokerSimulator, Order


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

MAType = Literal["EMA", "HEMA", "SMA", "HMA", "WMA", "DEMA", "VWMA", "VWAP", "T3"]
TrailSource = Literal["High/Low", "Close", "Open"]

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


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@dataclass
class CommasBotConfig:
    # ---- Trade variables ----
    long_trades: bool = True
    short_trades: bool = True
    use_limit: bool = True
    trail_stop: bool = False
    flip: bool = False
    set_max_drawdown: bool = False

    # ---- Risk Management ----
    rnr: float = 1.0
    risk_m: float = 1.0
    swing_lookback: int = 5
    max_perc_dd: float = 20.0
    atr_len: int = 14

    # ---- Trailing Stop ----
    trail_stop_size: float = 1.0
    trail_source: TrailSource = "High/Low"
    rr_exit: float = 0.0

    # ---- MA Type ----
    ma_type1: MAType = "EMA"
    ma_type2: MAType = "EMA"

    # ---- MA Settings ----
    ma_length1: int = 21
    ma_length2: int = 50

    # ---- Filters ----
    use_time_filter: bool = False
    time_session: str = "0000-0300"
    start_time: Optional[Any] = None
    end_time: Optional[Any] = None

    # ---- Capped Bucket ----
    initial_capital_bucket: float = 300.0
    max_capital_bucket: float = 300.0
    max_entry_price: float = 300.0

    # ---- Trade direction ----
    trade_direction_mode: TradeDirectionMode = "Long & Short"

    # ---- Fee / reversal filter ----
    fee_mode: FeeMode = "Parametric: hold until net covers fees"
    estimated_commission_per_order_long: float = 0.0
    estimated_commission_per_order_short: float = 3.0
    estimated_slippage_per_side_long: float = 0.0
    estimated_slippage_per_side_short: float = 0.0
    min_net_profit_after_costs: float = 0.0

    # ---- Explicit net exits ----
    use_net_bracket_exits: bool = False
    take_profit_net_percent: float = 10.0
    stop_loss_net_percent: float = 10.0

    # ---- Safety stop ----
    use_safety_stop: bool = True
    safety_stop_applies_to: SafetyStopAppliesTo = "Short only"
    safety_stop_mode: SafetyStopMode = "Net loss only"
    safety_max_net_loss_mode: SafetyMaxNetLossMode = "Cash amount"
    safety_max_net_loss_cash: float = 50.0
    safety_max_net_loss_percent: float = 0.0
    safety_max_bars_in_trade: int = 0

    # ---- Execution ----
    execute_on_next_bar: bool = True
    next_bar_execution_price_col: str = "open"
    point_value: float = 1.0
    allow_fractional_quantity: bool = True
    quantity_precision: Optional[int] = None
    apply_estimated_costs_to_realized_pnl: bool = True

    # Currency and FX provider overrides
    asset_currency: Optional[str] = None
    account_currency: Optional[str] = None
    fx_rate_provider: Optional[object] = None


# ---------------------------------------------------------------------------
# Indicator helpers
# ---------------------------------------------------------------------------

def _wma(series: pd.Series, length: int) -> pd.Series:
    length = int(length)
    if length < 1:
        raise ValueError("WMA length must be >= 1")
    weights = np.arange(1, length + 1, dtype=float)
    weight_sum = weights.sum()
    
    values = series.to_numpy(dtype=float)
    if len(values) < length:
        return pd.Series(np.nan, index=series.index)
        
    w = weights[::-1] / weight_sum
    conv = np.convolve(values, w, mode='valid')
    
    pad = np.full(length - 1, np.nan)
    result = np.concatenate((pad, conv))
    
    return pd.Series(result, index=series.index)


def _hma(series: pd.Series, length: int) -> pd.Series:
    length = int(length)
    if length < 1:
        raise ValueError("HMA length must be >= 1")
    half_len = max(1, int(length / 2))
    sqrt_len = max(1, int(math.sqrt(length)))
    fast_wma = _wma(series, half_len)
    slow_wma = _wma(series, length)
    raw_hma = 2.0 * fast_wma - slow_wma
    return _wma(raw_hma, sqrt_len)


def _ha_open(df: pd.DataFrame) -> pd.Series:
    if len(df) == 0:
        return pd.Series(dtype=float, index=df.index)
        
    open_vals = df["open"].to_numpy(dtype=float)
    close_vals = df["close"].to_numpy(dtype=float)
    high_vals = df["high"].to_numpy(dtype=float)
    low_vals = df["low"].to_numpy(dtype=float)
    
    ha_close_vals = (open_vals + high_vals + low_vals + close_vals) / 4.0
    ha_open_vals = np.empty(len(df), dtype=float)
    
    ha_open_vals[0] = (open_vals[0] + close_vals[0]) / 2.0
    
    for i in range(1, len(df)):
        ha_open_vals[i] = (ha_open_vals[i - 1] + ha_close_vals[i - 1]) / 2.0
        
    return pd.Series(ha_open_vals, index=df.index)


def get_ma(
    series: pd.Series,
    ma_type: MAType,
    length: int,
    df: pd.DataFrame | None = None,
) -> pd.Series:
    length = int(length)
    if length < 1:
        raise ValueError("MA length must be >= 1")

    if ma_type == "EMA":
        return series.ewm(span=length, adjust=False).mean()
    if ma_type == "SMA":
        return series.rolling(length, min_periods=length).mean()
    if ma_type == "HMA":
        return _hma(series, length)
    if ma_type == "WMA":
        return _wma(series, length)
    if ma_type == "VWMA":
        if df is None or "volume" not in df.columns:
            raise ValueError("df with 'volume' column required for VWMA")
        return (
            (series * df["volume"]).rolling(length, min_periods=length).sum()
            / df["volume"].rolling(length, min_periods=length).sum()
        )
    if ma_type == "VWAP":
        if df is None or "volume" not in df.columns:
            raise ValueError("df with 'volume' column required for VWAP")
        tp = (df["high"] + df["low"] + df["close"]) / 3.0
        return (tp * df["volume"]).cumsum() / df["volume"].cumsum()
    if ma_type == "DEMA":
        e1 = series.ewm(span=length, adjust=False).mean()
        e2 = e1.ewm(span=length, adjust=False).mean()
        return 2.0 * e1 - e2
    if ma_type == "T3":
        axe1 = series.ewm(span=length, adjust=False).mean()
        axe2 = axe1.ewm(span=length, adjust=False).mean()
        axe3 = axe2.ewm(span=length, adjust=False).mean()
        axe4 = axe3.ewm(span=length, adjust=False).mean()
        axe5 = axe4.ewm(span=length, adjust=False).mean()
        axe6 = axe5.ewm(span=length, adjust=False).mean()
        ab = 0.7
        ac1 = -ab * ab * ab
        ac2 = 3 * ab * ab + 3 * ab * ab * ab
        ac3 = -6 * ab * ab - 3 * ab - 3 * ab * ab * ab
        ac4 = 1 + 3 * ab + ab * ab * ab + 3 * ab * ab
        return ac1 * axe6 + ac2 * axe5 + ac3 * axe4 + ac4 * axe3
    if ma_type == "HEMA":
        if df is None:
            raise ValueError("df required for HEMA")
        ha_open = _ha_open(df)
        return ha_open.ewm(span=length, adjust=False).mean()
    raise ValueError(f"Unknown MA type: {ma_type}")


def crossover(a: pd.Series, b: pd.Series) -> pd.Series:
    return (a > b) & (a.shift(1) <= b.shift(1))


def crossunder(a: pd.Series, b: pd.Series) -> pd.Series:
    return (a < b) & (a.shift(1) >= b.shift(1))


def atr(df: pd.DataFrame, length: int) -> pd.Series:
    tr1 = df["high"] - df["low"]
    tr2 = (df["high"] - df["close"].shift(1)).abs()
    tr3 = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / length, min_periods=length, adjust=False).mean()


def lowest(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(length, min_periods=length).min()


def highest(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(length, min_periods=length).max()


def _parse_session(session_str: str) -> Tuple[int, int]:
    parts = session_str.split("-")
    start_h = int(parts[0][:2])
    start_m = int(parts[0][2:])
    end_h = int(parts[1][:2])
    end_m = int(parts[1][2:])
    return start_h * 60 + start_m, end_h * 60 + end_m


def _is_in_session(index: pd.DatetimeIndex, session_str: str) -> pd.Series:
    start_min, end_min = _parse_session(session_str)
    minutes = index.hour * 60 + index.minute
    if start_min <= end_min:
        in_sess = (minutes >= start_min) & (minutes <= end_min)
    else:
        in_sess = (minutes >= start_min) | (minutes <= end_min)
    return pd.Series(in_sess, index=index)


def _normalize_qty(qty: float, config: CommasBotConfig) -> float:
    if pd.isna(qty) or qty <= 0:
        return 0.0
    qty = float(qty)
    if not config.allow_fractional_quantity:
        qty = math.floor(qty)
    if config.quantity_precision is not None:
        qty = round(qty, config.quantity_precision)
    return max(qty, 0.0)


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


def _side_name(side: int) -> str:
    if side > 0:
        return "long"
    if side < 0:
        return "short"
    return "flat"


def _costs_for_side(side: int, config: CommasBotConfig) -> Tuple[float, float]:
    """
    Returns (commission_per_order, slippage_per_side) in account/symbol currency.
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


def _round_trip_costs_for_side(side: int, qty: float, config: CommasBotConfig) -> float:
    if qty <= 0 or side == 0:
        return 0.0
    commission_per_order, slippage_per_side = _costs_for_side(side, config)
    return commission_per_order * 2.0 + slippage_per_side * 2.0


# Shared indicator references (populated by backtest_engine multiprocessing workers)
_SHARED_CB_MA_GRID: np.ndarray | None = None
_SHARED_CB_MA_KEYS: dict[tuple[str, int], int] | None = None
_SHARED_CB_ATR_GRID: np.ndarray | None = None
_SHARED_CB_ATR_KEYS: dict[int, int] | None = None
_SHARED_CB_SWING_GRID: np.ndarray | None = None
_SHARED_CB_SWING_KEYS: dict[int, int] | None = None


# ---------------------------------------------------------------------------
# Feature-only function
# ---------------------------------------------------------------------------

def add_3commas_bot_features(
    df: pd.DataFrame,
    config: Optional[CommasBotConfig] = None,
) -> pd.DataFrame:
    config = config or CommasBotConfig()

    out = df.copy()

    global _SHARED_CB_MA_GRID, _SHARED_CB_MA_KEYS
    global _SHARED_CB_ATR_GRID, _SHARED_CB_ATR_KEYS
    global _SHARED_CB_SWING_GRID, _SHARED_CB_SWING_KEYS

    # MAs
    ma_key1 = (str(config.ma_type1), int(config.ma_length1))
    if _SHARED_CB_MA_GRID is not None and _SHARED_CB_MA_KEYS is not None and ma_key1 in _SHARED_CB_MA_KEYS:
        idx1 = _SHARED_CB_MA_KEYS[ma_key1]
        out["ma1"] = pd.Series(_SHARED_CB_MA_GRID[idx1], index=out.index, dtype="float64")
    else:
        out["ma1"] = get_ma(out["close"], config.ma_type1, config.ma_length1, df=out)

    ma_key2 = (str(config.ma_type2), int(config.ma_length2))
    if _SHARED_CB_MA_GRID is not None and _SHARED_CB_MA_KEYS is not None and ma_key2 in _SHARED_CB_MA_KEYS:
        idx2 = _SHARED_CB_MA_KEYS[ma_key2]
        out["ma2"] = pd.Series(_SHARED_CB_MA_GRID[idx2], index=out.index, dtype="float64")
    else:
        out["ma2"] = get_ma(out["close"], config.ma_type2, config.ma_length2, df=out)

    # ATR
    atr_key = int(config.atr_len)
    if _SHARED_CB_ATR_GRID is not None and _SHARED_CB_ATR_KEYS is not None and atr_key in _SHARED_CB_ATR_KEYS:
        idx_atr = _SHARED_CB_ATR_KEYS[atr_key]
        out["atr"] = pd.Series(_SHARED_CB_ATR_GRID[idx_atr], index=out.index, dtype="float64")
    else:
        out["atr"] = atr(out, config.atr_len)

    # Swing high/low
    swing_key = int(config.swing_lookback)
    if _SHARED_CB_SWING_GRID is not None and _SHARED_CB_SWING_KEYS is not None and swing_key in _SHARED_CB_SWING_KEYS:
        idx_swing = _SHARED_CB_SWING_KEYS[swing_key]
        out["lowest_low"] = pd.Series(_SHARED_CB_SWING_GRID[idx_swing, 0], index=out.index, dtype="float64")
        out["highest_high"] = pd.Series(_SHARED_CB_SWING_GRID[idx_swing, 1], index=out.index, dtype="float64")
    else:
        out["lowest_low"] = lowest(out["low"], config.swing_lookback)
        out["highest_high"] = highest(out["high"], config.swing_lookback)

    # Cross conditions
    out["ma1_cross_up2"] = crossover(out["ma1"], out["ma2"])
    out["ma1_cross_dn2"] = crossunder(out["ma1"], out["ma2"])

    # Valid entries (raw signal + ATR available)
    out["valid_long_entry"] = out["ma1_cross_up2"] & out["atr"].notna()
    out["valid_short_entry"] = out["ma1_cross_dn2"] & out["atr"].notna()

    # Time filter: True when trading is ALLOWED
    if config.use_time_filter:
        in_session = _is_in_session(out.index, config.time_session)
        time_filter = ~in_session
    else:
        time_filter = pd.Series(True, index=out.index)

    # Date filter
    date_filter = pd.Series(True, index=out.index)
    if config.start_time is not None:
        date_filter &= out.index >= pd.Timestamp(config.start_time)
    if config.end_time is not None:
        date_filter &= out.index <= pd.Timestamp(config.end_time)

    out["within_time"] = time_filter & date_filter

    return out


# ---------------------------------------------------------------------------
# Strategy backtest
# ---------------------------------------------------------------------------

class _CommasBotBacktestSession:
    def __init__(
        self,
        config: CommasBotConfig,
        compute_full_metrics: bool,
        broker: BrokerSimulator,
        out: pd.DataFrame,
    ):
        self.config = config
        self.compute_full_metrics = compute_full_metrics
        self.broker = broker
        
        self.n = len(out)
        self.index = out.index
        self.open_arr = out["open"].to_numpy(dtype=float)
        self.high_arr = out["high"].to_numpy(dtype=float)
        self.low_arr = out["low"].to_numpy(dtype=float)
        self.close_arr = out["close"].to_numpy(dtype=float)
        self.fill_price_arr = out[config.next_bar_execution_price_col].to_numpy(dtype=float)
        
        self.valid_long_arr = out["valid_long_entry"].to_numpy(dtype=bool)
        self.valid_short_arr = out["valid_short_entry"].to_numpy(dtype=bool)
        self.within_time_arr = out["within_time"].to_numpy(dtype=bool)
        self.atr_arr = out["atr"].to_numpy(dtype=float)
        self.lowest_low_arr = out["lowest_low"].to_numpy(dtype=float)
        self.highest_high_arr = out["highest_high"].to_numpy(dtype=float)
        
        # State
        self.side = 0
        self.qty = 0.0
        self.entry_price = np.nan
        self.entry_index: Any = None
        self.entry_bar_number: Optional[int] = None
        
        self.look_for_exit = False
        self.trade_stop_price = 0.0
        self.trade_target_price = np.nan
        self.trailing_stop = 0.0
        self.trade_exit_trigger_price = 0.0
        
        self.pending_order: Optional[Dict[str, Any]] = None
        self.trades: List[Dict[str, Any]] = []
        
        from collections import defaultdict
        self.records = defaultdict(list)
        
        self.capital_bucket = bucket_clamp(config.initial_capital_bucket, config.max_capital_bucket)
        self.withdrawn_profit = 0.0
        self.peak_equity = float(broker.cash)
        self.max_dd_stopped = False

    def _update_bucket_with_trade_pnl(self, net_pnl: float) -> None:
        raw_bucket = self.capital_bucket + float(net_pnl)
        if raw_bucket > self.config.max_capital_bucket:
            self.withdrawn_profit += raw_bucket - self.config.max_capital_bucket
        self.capital_bucket = bucket_clamp(raw_bucket, self.config.max_capital_bucket)

    def _current_gross_pnl(self, mark_price: float, timestamp: Any) -> float:
        if self.side == 0 or self.qty <= 0 or pd.isna(self.entry_price) or pd.isna(mark_price):
            return 0.0
        fx_rate = self.broker.fx_rate(timestamp)
        mark_price_account = mark_price * fx_rate
        if self.side > 0:
            return (mark_price_account - self.entry_price) * self.qty * self.config.point_value
        return (self.entry_price - mark_price_account) * self.qty * self.config.point_value

    def _close_position(self, exit_price: float, exit_index: Any, exit_bar_number: int, comment: str) -> Dict[str, Any]:
        if self.side == 0 or self.qty <= 0:
            return {"filled_order": None, "filled_comment": None, "realized_gross_pnl_on_fill": 0.0, "realized_costs_on_fill": 0.0, "realized_net_pnl_on_fill": 0.0}

        closed_side = self.side
        closed_qty = self.qty
        closed_entry_price = self.entry_price

        close_order = Order(
            id=f"close-{exit_bar_number}-{len(self.trades)}",
            side="sell" if closed_side > 0 else "buy",
            quantity=closed_qty,
            comment=comment,
            cost_side="long" if closed_side > 0 else "short",
        )
        self.broker.fill_order(close_order, exit_index, exit_price)
        broker_trade = self.broker.closed_trades[-1] if self.broker.closed_trades else None

        gross = float(broker_trade.gross_pnl) if broker_trade is not None else 0.0
        costs = float(broker_trade.commission) if broker_trade is not None else 0.0
        net = gross - costs

        self.trades.append({
            "entry_index": self.entry_index,
            "exit_index": exit_index,
            "entry_bar": self.entry_bar_number,
            "exit_bar": exit_bar_number,
            "side": _side_name(closed_side),
            "qty": closed_qty,
            "entry_price": closed_entry_price,
            "exit_price": exit_price,
            "gross_pnl": gross,
            "estimated_costs": costs,
            "net_pnl": net,
            "exit_comment": comment,
            "bars_held": (exit_bar_number - self.entry_bar_number if self.entry_bar_number is not None else np.nan),
        })

        self._update_bucket_with_trade_pnl(net)

        self.side = 0
        self.qty = 0.0
        self.entry_price = np.nan
        self.entry_index = None
        self.entry_bar_number = None
        self.look_for_exit = False
        self.trade_stop_price = 0.0
        self.trade_target_price = np.nan
        self.trailing_stop = 0.0
        self.trade_exit_trigger_price = 0.0

        return {"filled_order": "close", "filled_comment": comment, "realized_gross_pnl_on_fill": gross, "realized_costs_on_fill": costs, "realized_net_pnl_on_fill": net}

    def _open_position(self, new_side: int, fill_price: float, fill_index: Any, fill_bar_number: int, comment: str) -> Dict[str, Any]:
        if new_side == 0 or pd.isna(fill_price) or fill_price <= 0:
            return {"filled_order": None, "filled_comment": None, "realized_gross_pnl_on_fill": 0.0, "realized_costs_on_fill": 0.0, "realized_net_pnl_on_fill": 0.0}

        entry_bucket_qty = _normalize_qty(qty_from_bucket(self.capital_bucket, fill_price), self.config)
        if entry_bucket_qty <= 0:
            return {"filled_order": None, "filled_comment": None, "realized_gross_pnl_on_fill": 0.0, "realized_costs_on_fill": 0.0, "realized_net_pnl_on_fill": 0.0}

        self.side = int(np.sign(new_side))
        open_order = Order(
            id=f"entry-{fill_bar_number}-{len(self.trades)}",
            side="buy" if self.side > 0 else "sell",
            quantity=entry_bucket_qty,
            comment=comment,
            cost_side="long" if self.side > 0 else "short",
        )
        fill = self.broker.fill_order(open_order, fill_index, fill_price)
        self.qty = float(fill.quantity) if fill is not None else entry_bucket_qty
        self.entry_price = float(fill.price) if fill is not None else float(fill_price)
        self.entry_index = fill_index
        self.entry_bar_number = fill_bar_number

        atr_val = float(self.atr_arr[fill_bar_number])
        ll = float(self.lowest_low_arr[fill_bar_number])
        hh = float(self.highest_high_arr[fill_bar_number])

        if self.side > 0:
            long_stop = ll - (atr_val * self.config.risk_m)
            long_risk = fill_price - long_stop
            long_limit = fill_price + (self.config.rnr * long_risk)
            long_limit_dist = fill_price - long_limit

            self.trade_stop_price = long_stop
            self.trade_target_price = long_limit if self.config.use_limit else np.nan
            self.trade_exit_trigger_price = fill_price - (long_limit_dist * self.config.rr_exit)
            self.trailing_stop = self.trade_stop_price
            self.look_for_exit = False
        else:
            short_stop = hh + (atr_val * self.config.risk_m)
            short_risk = short_stop - fill_price
            short_limit = fill_price - (self.config.rnr * short_risk)
            short_limit_dist = short_limit - fill_price

            self.trade_stop_price = short_stop
            self.trade_target_price = short_limit if self.config.use_limit else np.nan
            self.trade_exit_trigger_price = fill_price + (short_limit_dist * self.config.rr_exit)
            self.trailing_stop = self.trade_stop_price
            self.look_for_exit = False

        return {"filled_order": "entry", "filled_comment": comment, "realized_gross_pnl_on_fill": 0.0, "realized_costs_on_fill": 0.0, "realized_net_pnl_on_fill": 0.0}

    def _execute_order(self, order: Dict[str, Any], fill_price: float, fill_index: Any, fill_bar_number: int) -> Dict[str, Any]:
        if order is None:
            return {"filled_order": None, "filled_comment": None, "realized_gross_pnl_on_fill": 0.0, "realized_costs_on_fill": 0.0, "realized_net_pnl_on_fill": 0.0}

        kind = order["kind"]
        if kind == "close":
            return self._close_position(fill_price, fill_index, fill_bar_number, order["comment"])
        if kind == "enter":
            return self._open_position(order["side"], fill_price, fill_index, fill_bar_number, order["comment"])
        if kind == "reverse":
            old_close = self._close_position(fill_price, fill_index, fill_bar_number, order["comment"])
            new_open = self._open_position(order["side"], fill_price, fill_index, fill_bar_number, order["comment"])
            return {
                "filled_order": "reverse",
                "filled_comment": order["comment"],
                "realized_gross_pnl_on_fill": old_close["realized_gross_pnl_on_fill"],
                "realized_costs_on_fill": old_close["realized_costs_on_fill"],
                "realized_net_pnl_on_fill": old_close["realized_net_pnl_on_fill"],
                "opened_after_reverse": new_open["filled_order"] == "entry",
            }
        raise ValueError(f"Unsupported order kind: {kind}")

    def _make_close_order(self, comment: str) -> Dict[str, Any]:
        return {"kind": "close", "side": 0, "qty": 0.0, "comment": comment}

    def _make_entry_order(self, new_side: int, comment: str) -> Dict[str, Any]:
        return {"kind": "enter", "side": new_side, "comment": comment}

    def _make_reverse_order(self, new_side: int, comment: str) -> Dict[str, Any]:
        return {"kind": "reverse", "side": new_side, "comment": comment}

    def _process_bar(self, bar_number: int) -> None:
        idx = self.index[bar_number]
        fill_info = {
            "filled_order": None,
            "filled_comment": None,
            "realized_gross_pnl_on_fill": 0.0,
            "realized_costs_on_fill": 0.0,
            "realized_net_pnl_on_fill": 0.0,
        }

        # 1) Fill pending order from prior bar
        if self.pending_order is not None:
            fill_price = float(self.fill_price_arr[bar_number])
            fill_info = self._execute_order(self.pending_order, fill_price, idx, bar_number)
            self.pending_order = None

        close_price = float(self.close_arr[bar_number])
        high_price = float(self.high_arr[bar_number])
        low_price = float(self.low_arr[bar_number])
        open_price = float(self.open_arr[bar_number])

        in_long = self.side > 0
        in_short = self.side < 0
        flat = self.side == 0

        # --- Common state calculations ---
        bars_in_trade = (bar_number - self.entry_bar_number if self.entry_bar_number is not None else 0)

        gross_pnl_estimate = self._current_gross_pnl(close_price, idx)
        estimated_round_trip_costs = _round_trip_costs_for_side(self.side, self.qty, self.config)
        estimated_net_if_closed_now = gross_pnl_estimate - estimated_round_trip_costs
        reversal_net_filter_passed = (estimated_net_if_closed_now >= self.config.min_net_profit_after_costs)

        entry_position_value = (self.entry_price * self.qty * self.config.point_value if self.qty > 0 and not pd.isna(self.entry_price) else 0.0)
        take_profit_net_threshold = (entry_position_value * self.config.take_profit_net_percent / 100.0)
        stop_loss_net_threshold = (entry_position_value * self.config.stop_loss_net_percent / 100.0)

        if self.config.safety_max_net_loss_mode == "Cash amount":
            safety_max_net_loss_threshold = float(self.config.safety_max_net_loss_cash)
        else:
            safety_max_net_loss_threshold = (entry_position_value * self.config.safety_max_net_loss_percent / 100.0)

        safety_direction_allowed = (
            self.config.safety_stop_applies_to == "Both"
            or (self.config.safety_stop_applies_to == "Long only" and in_long)
            or (self.config.safety_stop_applies_to == "Short only" and in_short)
        )
        safety_loss_triggered = (safety_max_net_loss_threshold > 0 and estimated_net_if_closed_now <= -safety_max_net_loss_threshold)
        safety_bars_triggered = (self.config.safety_max_bars_in_trade > 0 and bars_in_trade >= self.config.safety_max_bars_in_trade)

        if self.config.safety_stop_mode == "Net loss only":
            safety_condition = safety_loss_triggered
        elif self.config.safety_stop_mode == "Max bars only":
            safety_condition = safety_bars_triggered
        elif self.config.safety_stop_mode == "Net loss OR max bars":
            safety_condition = safety_loss_triggered or safety_bars_triggered
        else:
            safety_condition = safety_loss_triggered and safety_bars_triggered

        safety_stop_triggered = (self.config.use_safety_stop and safety_direction_allowed and safety_condition)

        hit_net_take_profit = (self.config.use_net_bracket_exits and self.qty > 0 and estimated_net_if_closed_now >= take_profit_net_threshold)
        hit_net_stop_loss = (self.config.use_net_bracket_exits and self.qty > 0 and estimated_net_if_closed_now <= -stop_loss_net_threshold)

        # 2) Update trailing stop
        if in_long and self.config.trail_stop and self.look_for_exit:
            if self.config.trail_source == "Close":
                trail_src = self.close_arr[bar_number - 1] if bar_number > 0 else close_price
            elif self.config.trail_source == "Open":
                trail_src = self.open_arr[bar_number - 1] if bar_number > 0 else open_price
            else:
                trail_src = float(self.lowest_low_arr[bar_number])
            trail = trail_src - (float(self.atr_arr[bar_number]) * self.config.trail_stop_size)
            if trail > self.trailing_stop:
                self.trailing_stop = trail

        if in_short and self.config.trail_stop and self.look_for_exit:
            if self.config.trail_source == "Close":
                trail_src = self.close_arr[bar_number - 1] if bar_number > 0 else close_price
            elif self.config.trail_source == "Open":
                trail_src = self.open_arr[bar_number - 1] if bar_number > 0 else open_price
            else:
                trail_src = float(self.highest_high_arr[bar_number])
            trail = trail_src + (float(self.atr_arr[bar_number]) * self.config.trail_stop_size)
            if trail < self.trailing_stop:
                self.trailing_stop = trail

        # 3) Priority order generation
        generated_order = None
        hit_stop = False
        hit_limit = False
        exit_comment = ""

        # 3a) Safety stop (highest priority)
        if safety_stop_triggered and in_long:
            generated_order = self._make_close_order("Safety Stop Long")
        elif safety_stop_triggered and in_short:
            generated_order = self._make_close_order("Safety Stop Short")
        # 3b) Optional explicit net TP/SL exits
        elif in_long and hit_net_take_profit:
            generated_order = self._make_close_order("Net TP Long")
        elif in_long and hit_net_stop_loss:
            generated_order = self._make_close_order("Net SL Long")
        elif in_short and hit_net_take_profit:
            generated_order = self._make_close_order("Net TP Short")
        elif in_short and hit_net_stop_loss:
            generated_order = self._make_close_order("Net SL Short")
        # 3c) Native stop / limit exits
        else:
            if in_long:
                effective_stop = self.trailing_stop if (self.config.trail_stop and self.look_for_exit) else self.trade_stop_price
                if low_price <= effective_stop:
                    hit_stop = True
                    exit_comment = "Stop Long"
                if self.config.use_limit and not pd.isna(self.trade_target_price):
                    if high_price >= self.trade_target_price:
                        hit_limit = True
                        if hit_stop:
                            exit_comment = "Stop Long"
                        else:
                            exit_comment = "Limit Long"
                if not self.look_for_exit and self.config.trail_stop:
                    if np.isclose(self.config.rr_exit, 0.0, atol=1e-9):
                        self.look_for_exit = True
                    elif high_price >= self.trade_exit_trigger_price:
                        self.look_for_exit = True

            if in_short:
                effective_stop = self.trailing_stop if (self.config.trail_stop and self.look_for_exit) else self.trade_stop_price
                if high_price >= effective_stop:
                    hit_stop = True
                    exit_comment = "Stop Short"
                if self.config.use_limit and not pd.isna(self.trade_target_price):
                    if low_price <= self.trade_target_price:
                        hit_limit = True
                        if hit_stop:
                            exit_comment = "Stop Short"
                        else:
                            exit_comment = "Limit Short"
                if not self.look_for_exit and self.config.trail_stop:
                    if np.isclose(self.config.rr_exit, 0.0, atol=1e-9):
                        self.look_for_exit = True
                    elif low_price <= self.trade_exit_trigger_price:
                        self.look_for_exit = True

            if hit_stop or hit_limit:
                generated_order = self._make_close_order(exit_comment)

        # 4) Max drawdown check
        if generated_order is None and self.config.set_max_drawdown and not self.max_dd_stopped:
            current_equity = self.broker.mark_to_market_equity(close_price, idx)
            if current_equity > self.peak_equity:
                self.peak_equity = current_equity
            if self.peak_equity > 0:
                dd_pct = (self.peak_equity - current_equity) / self.peak_equity
                if dd_pct >= self.config.max_perc_dd / 100.0:
                    self.max_dd_stopped = True
                    if self.side != 0:
                        close_info = self._close_position(close_price, idx, bar_number, "Max Drawdown")
                        fill_info = close_info

        in_long = self.side > 0
        in_short = self.side < 0
        flat = self.side == 0

        # 5) Entry signals
        valid_long = bool(self.valid_long_arr[bar_number])
        valid_short = bool(self.valid_short_arr[bar_number])
        within_time = bool(self.within_time_arr[bar_number])

        allow_long = self.config.trade_direction_mode != "Short only"
        allow_short = self.config.trade_direction_mode != "Long only"

        entry_allowed_by_cap = close_price <= self.config.max_entry_price and self.capital_bucket > 0
        flat_entry_qty = _normalize_qty(qty_from_bucket(self.capital_bucket, close_price), self.config)
        reverse_entry_qty = flat_entry_qty

        hold_until_profitable = (self.config.fee_mode == "Parametric: hold until net covers fees")
        exit_only_no_reverse = (self.config.fee_mode == "Parametric: exit only, no forced reversal")
        disable_fee_filter = (self.config.fee_mode == "Disabled: always reverse/close on opposite signal")

        if generated_order is None and not self.max_dd_stopped and entry_allowed_by_cap:
            if flat and flat_entry_qty > 0:
                if valid_short and within_time and allow_short and self.config.short_trades:
                    generated_order = self._make_entry_order(-1, "Short")
                elif valid_long and within_time and allow_long and self.config.long_trades:
                    generated_order = self._make_entry_order(1, "Long")

            if generated_order is None and in_long and valid_short and within_time and allow_short and self.config.short_trades and self.config.flip:
                if disable_fee_filter:
                    if close_price <= self.config.max_entry_price and reverse_entry_qty > 0:
                        generated_order = self._make_reverse_order(-1, "Short Rev")
                    else:
                        generated_order = self._make_close_order("Exit Long")
                elif exit_only_no_reverse:
                    generated_order = self._make_close_order("Exit Long")
                elif hold_until_profitable and reversal_net_filter_passed:
                    if close_price <= self.config.max_entry_price and reverse_entry_qty > 0:
                        generated_order = self._make_reverse_order(-1, "Short Rev")
                    else:
                        generated_order = self._make_close_order("Exit Long")

            if generated_order is None and in_short and valid_long and within_time and allow_long and self.config.long_trades and self.config.flip:
                if disable_fee_filter:
                    if close_price <= self.config.max_entry_price and reverse_entry_qty > 0:
                        generated_order = self._make_reverse_order(1, "Long Rev")
                    else:
                        generated_order = self._make_close_order("Exit Short")
                elif exit_only_no_reverse:
                    generated_order = self._make_close_order("Exit Short")
                elif hold_until_profitable and reversal_net_filter_passed:
                    if close_price <= self.config.max_entry_price and reverse_entry_qty > 0:
                        generated_order = self._make_reverse_order(1, "Long Rev")
                    else:
                        generated_order = self._make_close_order("Exit Short")

        signal_order = None
        signal_comment = None
        signal_side = 0

        if generated_order is not None:
            signal_order = generated_order["kind"]
            signal_comment = generated_order["comment"]
            signal_side = generated_order.get("side", 0)

            if self.config.execute_on_next_bar:
                if signal_order == "close":
                    fill_info = self._execute_order(generated_order, close_price, idx, bar_number)
                else:
                    self.pending_order = generated_order
            else:
                fill_info = self._execute_order(generated_order, close_price, idx, bar_number)

        effective_stop = 0.0
        if in_long:
            effective_stop = self.trailing_stop if (self.config.trail_stop and self.look_for_exit) else self.trade_stop_price
        elif in_short:
            effective_stop = self.trailing_stop if (self.config.trail_stop and self.look_for_exit) else self.trade_stop_price

        if self.compute_full_metrics:
            self.records["position_side"].append(self.side)
            self.records["position_label"].append(_side_name(self.side))
            self.records["position_size"].append(self.side * self.qty)
            self.records["position_avg_price"].append(self.entry_price)
            self.records["in_long"].append(in_long)
            self.records["in_short"].append(in_short)
            self.records["flat"].append(flat)
            self.records["look_for_exit"].append(self.look_for_exit)
            self.records["trade_stop_price"].append(self.trade_stop_price)
            self.records["trade_target_price"].append(self.trade_target_price)
            self.records["trailing_stop"].append(self.trailing_stop)
            self.records["effective_stop"].append(effective_stop)
            self.records["trade_exit_trigger_price"].append(self.trade_exit_trigger_price)
            self.records["hit_stop"].append(hit_stop)
            self.records["hit_limit"].append(hit_limit)
            self.records["signal_order"].append(signal_order)
            self.records["signal_comment"].append(signal_comment)
            self.records["signal_side"].append(signal_side)
            self.records["max_dd_stopped"].append(self.max_dd_stopped)
            self.records["capital_bucket"].append(self.capital_bucket)
            self.records["withdrawn_profit"].append(self.withdrawn_profit)
            self.records["entry_allowed_by_cap"].append(entry_allowed_by_cap)
            self.records["flat_entry_qty"].append(flat_entry_qty)
            self.records["reverse_entry_qty"].append(reverse_entry_qty)
            self.records["bars_in_trade"].append(bars_in_trade)
            self.records["gross_pnl_estimate"].append(gross_pnl_estimate)
            self.records["estimated_round_trip_costs"].append(estimated_round_trip_costs)
            self.records["estimated_net_if_closed_now"].append(estimated_net_if_closed_now)
            self.records["reversal_net_filter_passed"].append(reversal_net_filter_passed)
            self.records["safety_max_net_loss_threshold"].append(safety_max_net_loss_threshold)
            self.records["safety_loss_triggered"].append(safety_loss_triggered)
            self.records["safety_bars_triggered"].append(safety_bars_triggered)
            self.records["safety_stop_triggered"].append(safety_stop_triggered)
            self.records["hit_net_take_profit"].append(hit_net_take_profit)
            self.records["hit_net_stop_loss"].append(hit_net_stop_loss)
            self.records["filled_order"].append(fill_info.get("filled_order"))
            self.records["filled_comment"].append(fill_info.get("filled_comment"))
            self.records["realized_gross_pnl_on_fill"].append(fill_info.get("realized_gross_pnl_on_fill", 0.0))
            self.records["realized_costs_on_fill"].append(fill_info.get("realized_costs_on_fill", 0.0))
            self.records["realized_net_pnl_on_fill"].append(fill_info.get("realized_net_pnl_on_fill", 0.0))
        else:
            self.records["position_size"].append(self.side * self.qty)
            self.records["position_avg_price"].append(self.entry_price)
            self.records["estimated_net_if_closed_now"].append(estimated_net_if_closed_now)
            self.records["realized_net_pnl_on_fill"].append(fill_info.get("realized_net_pnl_on_fill", 0.0))

    def run(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        for bar_number in range(self.n):
            self._process_bar(bar_number)
            
        state_df = pd.DataFrame(self.records, index=self.index)
        trades_df = pd.DataFrame(self.trades)
        return state_df, trades_df


def run_3commas_bot_strategy(
    df: pd.DataFrame,
    config: Optional[CommasBotConfig] = None,
    compute_full_metrics: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    config = config or CommasBotConfig()

    required = {"open", "high", "low", "close"}
    if config.execute_on_next_bar:
        required.add(config.next_bar_execution_price_col)
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    out = add_3commas_bot_features(df, config)

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

    session = _CommasBotBacktestSession(config, compute_full_metrics, broker, out)
    state_df, trades_df = session.run()

    if compute_full_metrics:
        result_df = pd.concat([out, state_df], axis=1)
    else:
        result_df = state_df

    return result_df, trades_df
