"""
pmax_explorer_capped_bucket.py

Python conversion of:
"PMax Explorer" / "PMax Explorer STRATEGY-SCREENER" by KivancOzbilgic

Input DataFrame requirements:
    - Required columns: open, high, low, close
    - The source column defaults to "hl2" in Pine, but we support any column (e.g. "close", "hl2").
      We will calculate "hl2" on the fly if requested.

Main entry points:
    add_pmax_explorer_features(df, config)
        Adds PMax crossover feature/signal columns only.

    run_pmax_explorer_strategy(df, config)
        Stateful backtest approximation including capped bucket sizing, reversal filters, etc.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Tuple
from collections import defaultdict

import math
import numpy as np
import pandas as pd

from backtest_engine.broker import BrokerConfig, BrokerSimulator, Order

_PMAX_FEATURE_CACHE: dict = {}
_PMAX_CACHE_MAX_SIZE: int = 512

# Shared indicator references (populated by backtest_engine multiprocessing workers)
_SHARED_PMAX_MAVG_GRID: np.ndarray | None = None
_SHARED_PMAX_MAVG_KEYS: dict[tuple[str, int], int] | None = None  # (mav, length) -> idx

_SHARED_PMAX_ATR_GRID: np.ndarray | None = None
_SHARED_PMAX_ATR_KEYS: dict[tuple[int, bool], int] | None = None  # (periods, change_atr) -> idx

def _make_feature_cache_key(
    df: pd.DataFrame,
    periods: int,
    multiplier: float,
    mav: str,
    length: int,
    change_atr: bool,
    source_col: str,
) -> tuple:
    src = df[source_col].to_numpy(dtype=float, copy=False) if source_col in df.columns else df["close"].to_numpy(dtype=float, copy=False)
    n = len(src)
    boundary = src[:4].tobytes() + src[max(0, n - 4):].tobytes()
    return (id(src), n, hash(boundary), periods, multiplier, mav, length, change_atr, source_col)

def clear_pmax_feature_cache() -> None:
    _PMAX_FEATURE_CACHE.clear()

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
MA_Types = Literal["SMA", "EMA", "WMA", "TMA", "VAR", "WWMA", "ZLEMA", "TSF"]

@dataclass
class PMaxExplorerConfig:
    # Indicator inputs
    periods: int = 10
    multiplier: float = 3.0
    mav: MA_Types = "EMA"
    length: int = 10
    change_atr: bool = True
    source_col: str = "hl2"
    
    # Currency overrides
    asset_currency: str | None = None
    account_currency: str | None = None
    fx_rate_provider: object | None = None
    
    # Backtest parameters
    max_entry_price: float = 300.0
    max_capital_bucket: float = 300.0
    initial_capital_bucket: float = 300.0

    trade_direction_mode: TradeDirectionMode = "Long & Short"

    fee_mode: FeeMode = "Parametric: hold until net covers fees"
    estimated_commission_per_order_long: float = 0.0
    estimated_commission_per_order_short: float = 3.0
    estimated_slippage_per_side_long: float = 0.0
    estimated_slippage_per_side_short: float = 0.0
    min_net_profit_after_costs: float = 0.0

    use_net_bracket_exits: bool = False
    take_profit_net_percent: float = 10.0
    stop_loss_net_percent: float = 10.0

    use_safety_stop: bool = True
    safety_stop_applies_to: SafetyStopAppliesTo = "Short only"
    safety_stop_mode: SafetyStopMode = "Net loss only"
    safety_max_net_loss_mode: SafetyMaxNetLossMode = "Cash amount"
    safety_max_net_loss_cash: float = 50.0
    safety_max_net_loss_percent: float = 0.0
    safety_max_bars_in_trade: int = 0

    point_value: float = 1.0
    execute_on_next_bar: bool = True
    next_bar_execution_price_col: str = "open"

    apply_estimated_costs_to_realized_pnl: bool = True

    allow_fractional_quantity: bool = True
    quantity_precision: Optional[int] = None


def bucket_clamp(value: float, bucket_max: float) -> float:
    if pd.isna(value):
        value = 0.0
    return max(min(float(value), float(bucket_max)), 0.0)

def qty_from_bucket(bucket: float, price: float) -> float:
    if pd.isna(price) or price <= 0:
        return 0.0
    return float(bucket) / float(price)

def _normalize_qty(qty: float, config: PMaxExplorerConfig) -> float:
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

def _costs_for_side(side: int, config: PMaxExplorerConfig) -> Tuple[float, float]:
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

def _round_trip_costs_for_side(side: int, qty: float, config: PMaxExplorerConfig) -> float:
    if qty <= 0 or side == 0:
        return 0.0
    commission_per_order, slippage_per_side = _costs_for_side(side, config)
    return commission_per_order * 2.0 + slippage_per_side * 2.0

# --- Pine Script Indicators Math ---

def pine_sma(src: np.ndarray, length: int) -> np.ndarray:
    return pd.Series(src).rolling(length).mean().to_numpy()

def pine_ema(src: np.ndarray, length: int) -> np.ndarray:
    alpha = 2.0 / (length + 1)
    res = np.zeros_like(src)
    res[0] = src[0]
    for i in range(1, len(src)):
        if np.isnan(res[i-1]):
            res[i] = src[i]
        else:
            res[i] = alpha * src[i] + (1 - alpha) * res[i-1]
    return res

def pine_wma(src: np.ndarray, length: int) -> np.ndarray:
    weights = np.arange(1, length + 1, dtype=float)
    weight_sum = weights.sum()
    s = pd.Series(src)
    return s.rolling(length, min_periods=length).apply(
        lambda values: float(np.dot(values, weights) / weight_sum),
        raw=True,
    ).to_numpy()

def pine_tma(src: np.ndarray, length: int) -> np.ndarray:
    # sma(sma(src, ceil(length / 2)), floor(length / 2) + 1)
    half_ceil = int(math.ceil(length / 2.0))
    half_floor_plus = int(math.floor(length / 2.0)) + 1
    sma1 = pine_sma(src, half_ceil)
    return pine_sma(sma1, half_floor_plus)

def pine_var(src: np.ndarray, length: int) -> np.ndarray:
    valpha = 2.0 / (length + 1)
    n = len(src)
    var_arr = np.zeros(n, dtype=float)
    
    # Calculate vud1 and vdd1
    vud1 = np.zeros(n, dtype=float)
    vdd1 = np.zeros(n, dtype=float)
    for i in range(1, n):
        vud1[i] = src[i] - src[i-1] if src[i] > src[i-1] else 0.0
        vdd1[i] = src[i-1] - src[i] if src[i] < src[i-1] else 0.0
        
    vud_sum = pd.Series(vud1).rolling(9, min_periods=9).sum().to_numpy()
    vdd_sum = pd.Series(vdd1).rolling(9, min_periods=9).sum().to_numpy()
    
    for i in range(n):
        if np.isnan(vud_sum[i]) or np.isnan(vdd_sum[i]):
            vcmo = 0.0
        else:
            denom = vud_sum[i] + vdd_sum[i]
            vcmo = (vud_sum[i] - vdd_sum[i]) / denom if denom != 0 else 0.0
        
        abs_vcmo = abs(vcmo)
        prev_var = var_arr[i-1] if i > 0 else 0.0
        if np.isnan(prev_var):
            prev_var = 0.0
        var_arr[i] = (valpha * abs_vcmo * src[i]) + (1.0 - valpha * abs_vcmo) * prev_var
        
    return var_arr

def pine_wwma(src: np.ndarray, length: int) -> np.ndarray:
    wwalpha = 1.0 / length
    n = len(src)
    wwma_arr = np.zeros(n, dtype=float)
    for i in range(n):
        prev = wwma_arr[i-1] if i > 0 else src[0]
        if np.isnan(prev):
            prev = src[0]
        wwma_arr[i] = wwalpha * src[i] + (1 - wwalpha) * prev
    return wwma_arr

def pine_zlema(src: np.ndarray, length: int) -> np.ndarray:
    half_len = length / 2.0
    zxLag = int(half_len) if half_len == round(half_len) else int((length - 1) / 2.0)
    n = len(src)
    zxEMAData = np.zeros(n, dtype=float)
    for i in range(n):
        lag_idx = i - zxLag
        if lag_idx >= 0:
            zxEMAData[i] = src[i] + (src[i] - src[lag_idx])
        else:
            zxEMAData[i] = src[i]
            
    return pine_ema(zxEMAData, length)

def pine_linreg(src: np.ndarray, length: int, offset: int = 0) -> np.ndarray:
    n = len(src)
    res = np.full(n, np.nan)
    x = np.arange(length)
    x_mean = x.mean()
    x_var = ((x - x_mean) ** 2).sum()
    if x_var == 0:
        return res
        
    for i in range(length - 1 + offset, n):
        y = src[i - offset - length + 1 : i - offset + 1]
        y_mean = y.mean()
        b1 = ((x - x_mean) * (y - y_mean)).sum() / x_var
        b0 = y_mean - b1 * x_mean
        res[i] = b0 + b1 * (length - 1)
    return res

def pine_tsf(src: np.ndarray, length: int) -> np.ndarray:
    lrc = pine_linreg(src, length, 0)
    lrc1 = pine_linreg(src, length, 1)
    lrs = lrc - lrc1
    return lrc + lrs

def compute_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, length: int, change_atr: bool) -> np.ndarray:
    n = len(close)
    tr = np.zeros(n, dtype=float)
    tr[0] = high[0] - low[0]
    for i in range(1, n):
        h_l = high[i] - low[i]
        h_pc = abs(high[i] - close[i-1])
        l_pc = abs(low[i] - close[i-1])
        tr[i] = max(h_l, h_pc, l_pc)
        
    if change_atr:
        # Pine's atr() function is rma(tr, length)
        # rma is an ema with alpha = 1 / length
        alpha = 1.0 / length
        rma = np.zeros(n, dtype=float)
        # In Pine, RMA initializes with SMA of the first `length` periods
        initial_sma = np.mean(tr[:length]) if length <= n else np.mean(tr)
        rma[length - 1] = initial_sma
        for i in range(length, n):
            rma[i] = alpha * tr[i] + (1 - alpha) * rma[i-1]
        rma[:length-1] = np.nan
        return rma
    else:
        # atr2 = sma(tr, length)
        return pine_sma(tr, length)

def compute_pmax(mavg: np.ndarray, atr: np.ndarray, multiplier: float) -> Tuple[np.ndarray, np.ndarray]:
    n = len(mavg)
    pmax = np.full(n, np.nan)
    dir_arr = np.ones(n, dtype=int)
    
    longStop = np.full(n, np.nan)
    shortStop = np.full(n, np.nan)
    
    # Initialize direction
    current_dir = 1
    
    for i in range(n):
        if np.isnan(mavg[i]) or np.isnan(atr[i]):
            continue
            
        cur_long_stop = mavg[i] - multiplier * atr[i]
        cur_short_stop = mavg[i] + multiplier * atr[i]
        
        prev_long_stop = longStop[i-1] if i > 0 and not np.isnan(longStop[i-1]) else cur_long_stop
        prev_short_stop = shortStop[i-1] if i > 0 and not np.isnan(shortStop[i-1]) else cur_short_stop
        
        longStop[i] = max(cur_long_stop, prev_long_stop) if mavg[i] > prev_long_stop else cur_long_stop
        shortStop[i] = min(cur_short_stop, prev_short_stop) if mavg[i] < prev_short_stop else cur_short_stop
        
        # dir logic
        if i > 0:
            current_dir = dir_arr[i-1]
            
        if current_dir == -1 and mavg[i] > prev_short_stop:
            current_dir = 1
        elif current_dir == 1 and mavg[i] < prev_long_stop:
            current_dir = -1
            
        dir_arr[i] = current_dir
        pmax[i] = longStop[i] if current_dir == 1 else shortStop[i]
        
    return pmax, dir_arr

# ---------------------------------------------------------------------------

def add_pmax_explorer_features(
    df: pd.DataFrame,
    config: Optional[PMaxExplorerConfig] = None,
    *,
    use_cache: bool = True,
) -> pd.DataFrame:
    config = config or PMaxExplorerConfig()

    # Pre-calculate hl2 if requested but missing
    if config.source_col == "hl2" and "hl2" not in df.columns:
        df = df.copy()
        df["hl2"] = (df["high"] + df["low"]) / 2.0

    if config.source_col not in df.columns:
        raise ValueError(f"Missing source column: {config.source_col!r}")

    # ---- check shared memory grids first ----
    global _SHARED_PMAX_MAVG_GRID, _SHARED_PMAX_MAVG_KEYS
    global _SHARED_PMAX_ATR_GRID, _SHARED_PMAX_ATR_KEYS

    mavg = None
    atr = None

    if _SHARED_PMAX_MAVG_GRID is not None and _SHARED_PMAX_MAVG_KEYS is not None:
        mavg_key = (str(config.mav), int(config.length))
        if mavg_key in _SHARED_PMAX_MAVG_KEYS:
            mavg_idx = _SHARED_PMAX_MAVG_KEYS[mavg_key]
            mavg = _SHARED_PMAX_MAVG_GRID[mavg_idx]

    if _SHARED_PMAX_ATR_GRID is not None and _SHARED_PMAX_ATR_KEYS is not None:
        atr_key = (int(config.periods), bool(config.change_atr))
        if atr_key in _SHARED_PMAX_ATR_KEYS:
            atr_idx = _SHARED_PMAX_ATR_KEYS[atr_key]
            atr = _SHARED_PMAX_ATR_GRID[atr_idx]

    if mavg is not None and atr is not None:
        # Both are available from the shared grids! Direct O(1) computation!
        out = df.copy()
        pmax, pmax_dir = compute_pmax(mavg, atr, config.multiplier)
        
        out["mavg"] = mavg
        out["pmax"] = pmax
        out["pmax_dir"] = pmax_dir

        out["raw_long_signal"] = (out["mavg"] > out["pmax"]) & (out["mavg"].shift(1) <= out["pmax"].shift(1))
        out["raw_short_signal"] = (out["mavg"] < out["pmax"]) & (out["mavg"].shift(1) >= out["pmax"].shift(1))
        
        out["long_signal"] = out["raw_long_signal"]
        out["short_signal"] = out["raw_short_signal"]
        return out

    if use_cache:
        key = _make_feature_cache_key(
            df,
            periods=config.periods,
            multiplier=config.multiplier,
            mav=config.mav,
            length=config.length,
            change_atr=config.change_atr,
            source_col=config.source_col,
        )
        cached = _PMAX_FEATURE_CACHE.get(key)
        if cached is not None:
            return cached

    out = df.copy()
    
    src = out[config.source_col].to_numpy(dtype=float)
    high = out["high"].to_numpy(dtype=float)
    low = out["low"].to_numpy(dtype=float)
    close = out["close"].to_numpy(dtype=float)
    
    # Calculate MAvg
    if config.mav == "SMA":
        mavg = pine_sma(src, config.length)
    elif config.mav == "EMA":
        mavg = pine_ema(src, config.length)
    elif config.mav == "WMA":
        mavg = pine_wma(src, config.length)
    elif config.mav == "TMA":
        mavg = pine_tma(src, config.length)
    elif config.mav == "VAR":
        mavg = pine_var(src, config.length)
    elif config.mav == "WWMA":
        mavg = pine_wwma(src, config.length)
    elif config.mav == "ZLEMA":
        mavg = pine_zlema(src, config.length)
    elif config.mav == "TSF":
        mavg = pine_tsf(src, config.length)
    else:
        mavg = pine_ema(src, config.length) # default fallback

    # Calculate ATR
    atr = compute_atr(high, low, close, config.periods, config.change_atr)
    
    # Calculate PMax
    pmax, pmax_dir = compute_pmax(mavg, atr, config.multiplier)
    
    out["mavg"] = mavg
    out["pmax"] = pmax
    out["pmax_dir"] = pmax_dir

    # Signals
    # crossover(MAvg, PMax) -> buySignalk
    # crossunder(MAvg, PMax) -> sellSignallk
    out["raw_long_signal"] = (out["mavg"] > out["pmax"]) & (out["mavg"].shift(1) <= out["pmax"].shift(1))
    out["raw_short_signal"] = (out["mavg"] < out["pmax"]) & (out["mavg"].shift(1) >= out["pmax"].shift(1))
    
    out["long_signal"] = out["raw_long_signal"]
    out["short_signal"] = out["raw_short_signal"]

    if use_cache:
        if len(_PMAX_FEATURE_CACHE) >= _PMAX_CACHE_MAX_SIZE:
            _PMAX_FEATURE_CACHE.pop(next(iter(_PMAX_FEATURE_CACHE)))
        _PMAX_FEATURE_CACHE[key] = out

    return out


def run_pmax_explorer_strategy(
    df: pd.DataFrame,
    config: Optional[PMaxExplorerConfig] = None,
    early_stop_drawdown_pct: Optional[float] = None,
    compute_full_metrics: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    
    config = config or PMaxExplorerConfig()

    required = {"open", "high", "low", "close"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    out = add_pmax_explorer_features(df, config)

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
    records = defaultdict(list)

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

        if pending_order is not None:
            fill_price = float(fill_price_arr[bar_number])
            fill_info = execute_order(pending_order, fill_price, idx, bar_number)
            pending_order = None

        close_price = float(close_arr[bar_number])

        current_equity = broker.mark_to_market_equity(close_price, idx)
        if current_equity > peak_equity:
            peak_equity = current_equity
        
        if early_stop_drawdown_pct is not None and early_stop_drawdown_pct > 0 and peak_equity > 0:
            drawdown_pct = (peak_equity - current_equity) / peak_equity * 100.0
            if drawdown_pct >= early_stop_drawdown_pct:
                partial_state = pd.DataFrame(records, index=out.index[:bar_number])
                if compute_full_metrics:
                    partial_result = pd.concat([out.iloc[:bar_number], partial_state], axis=1)
                else:
                    partial_result = partial_state
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
                    generated_order = make_entry_order(1, flat_entry_qty, "BUY")
                elif short_signal and allow_short:
                    generated_order = make_entry_order(-1, flat_entry_qty, "SELL")

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
