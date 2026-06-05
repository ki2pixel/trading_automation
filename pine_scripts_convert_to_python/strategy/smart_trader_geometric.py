import numpy as np
import pandas as pd
from numba import njit
from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, Field
import math

class SmartTraderGeometricConfig(BaseModel):
    signal_mode: Literal["Close", "Live"] = "Close"
    lookback_period: int = 23
    
    # Format of a slot:
    # {
    #   "variable": "Ceil angle", # e.g.
    #   "condition": ">", # ">", "<", "between", "cross >", "cross <", "rising", "falling"
    #   "threshold": 0.0,
    #   "upper_bound": 0.0,
    #   "compare_to": None,
    #   "apply_to": "Long entry" # Long entry, Short entry, Long exit, Short exit, Block long entry, Block short entry, etc.
    # }
    slots: List[Dict[str, Any]] = Field(default_factory=list)
    
    min_long_entry_slots: int = 1
    min_short_entry_slots: int = 1
    min_long_exit_slots: int = 1
    min_short_exit_slots: int = 1
    
    enable_stop_loss: bool = False
    stop_loss_pct: float = 0.0
    enable_take_profit: bool = False
    take_profit_pct: float = 0.0
    enable_trailing_stop: bool = False
    trail_profit_pct: float = 0.0
    trail_loss_pct: float = 0.0
    
    # Backtest engine specifics
    allocator_config: Dict[str, Any] = Field(default_factory=dict)
    enable_pyramiding: bool = False
    max_pyramid_layers: int = 1


def compute_yang_zhang(open_p: np.ndarray, high: np.ndarray, low: np.ndarray, close: np.ndarray, lookback: int) -> np.ndarray:
    ln_ho = np.log(high / open_p)
    ln_lo = np.log(low / open_p)
    ln_co = np.log(close / open_p)
    
    ln_oc = np.zeros_like(close)
    ln_oc[1:] = np.log(open_p[1:] / close[:-1])
    
    ln_cc = np.zeros_like(close)
    ln_cc[1:] = np.log(close[1:] / close[:-1])
    
    var_o = pd.Series(ln_oc).rolling(lookback).var(ddof=1).values
    var_c = pd.Series(ln_co).rolling(lookback).var(ddof=1).values
    rs = ln_ho * (ln_ho - ln_co) + ln_lo * (ln_lo - ln_co)
    var_rs = pd.Series(rs).rolling(lookback).mean().values
    
    k = 0.34 / (1.34 + (lookback + 1) / (lookback - 1))
    var_yz = var_o + k * var_c + (1 - k) * var_rs
    sigma = np.sqrt(var_yz)
    
    # Avoid zero sigma
    sigma[sigma == 0] = 1e-8
    return sigma


@njit
def _compute_frozen_anchors(high: np.ndarray, low: np.ndarray, close: np.ndarray, lookback: int):
    n = len(close)
    anchor_ceiling = np.full(n, np.nan)
    anchor_floor = np.full(n, np.nan)
    anchor_center = np.full(n, np.nan)
    anchor_idx = np.full(n, -1, dtype=np.int64)
    
    current_ceiling = np.nan
    current_floor = np.nan
    current_center = np.nan
    current_anchor_i = -1
    
    for i in range(n):
        if current_anchor_i == -1:
            if i >= lookback - 1:
                hh = np.max(high[i-lookback+1:i+1])
                ll = np.min(low[i-lookback+1:i+1])
                current_ceiling = hh
                current_floor = ll
                current_center = np.sqrt(hh * ll)
                current_anchor_i = i
                
        if current_anchor_i != -1:
            anchor_ceiling[i] = current_ceiling
            anchor_floor[i] = current_floor
            anchor_center[i] = current_center
            anchor_idx[i] = current_anchor_i
            
            if close[i] > current_ceiling or close[i] < current_floor:
                current_anchor_i = -1
                
    return anchor_ceiling, anchor_floor, anchor_center, anchor_idx


def compute_triangle_metrics(dy: np.ndarray, dx: np.ndarray, y_A: np.ndarray, y_C: np.ndarray, y_B: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Computes Angle, Distance, Area, Centroid for a triangle.
    If y_B is None, it's a right triangle (Main triangles).
    If y_B is given, it's a pin triangle with 3 arbitrary vertices A, B, C."""
    
    # Distance
    if y_B is None:
        distance = dy
    else:
        # For pin triangles, distance is the length of the wick itself (y_B - y_C)
        distance = y_B - y_C

    # Angle
    with np.errstate(divide='ignore', invalid='ignore'):
        if y_B is None:
            # Right triangle
            angle = np.arctan(dy / np.where(dx == 0, 1e-8, dx)) * 180 / np.pi
        else:
            # Pin triangle
            dx_safe = np.where(dx == 0, 1e-8, dx)
            angle = (np.arctan((y_B - y_A) / dx_safe) - np.arctan((y_C - y_A) / dx_safe)) * 180 / np.pi

    # Angle for dx=0 is exactly 0 or 90
    angle = np.where(np.isnan(angle), 0, angle)
    
    # Area
    area = 0.5 * np.abs(dx) * np.abs(distance)
    
    # Centroid
    if y_B is None:
        centroid = (2 * y_A + y_C) / 3
    else:
        centroid = (y_A + y_B + y_C) / 3
        
    return angle, distance, area, centroid


def add_smart_trader_geometric_features(df: pd.DataFrame, config: SmartTraderGeometricConfig) -> pd.DataFrame:
    open_p = df['open'].values
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    
    lookback = config.lookback_period
    
    # 1. Yang-Zhang Sigma
    sigma = compute_yang_zhang(open_p, high, low, close, lookback)
    
    # 2. Frozen Anchors
    ceil_arr, floor_arr, center_arr, anchor_idx = _compute_frozen_anchors(high, low, close, lookback)
    
    # Helper for ICS transformation
    def to_ics(prices):
        return np.log(prices) / sigma
        
    y_ceil_anchor = to_ics(ceil_arr)
    y_floor_anchor = to_ics(floor_arr)
    y_center_anchor = to_ics(center_arr)
    
    # dx is bars since anchor / lookback
    current_idx = np.arange(len(close))
    dx = (current_idx - anchor_idx) / lookback
    dx = np.where(anchor_idx == -1, np.nan, dx)
    
    # Current bar geometries
    y_high = to_ics(high)
    y_low = to_ics(low)
    y_mid = to_ics(np.sqrt(high * low))
    
    body_top = to_ics(np.maximum(open_p, close))
    body_bottom = to_ics(np.minimum(open_p, close))
    
    # 3. Compute 5 Triangles
    # Ceiling Triangle
    dy_ceil = y_high - y_ceil_anchor
    ceil_angle, ceil_dist, ceil_area, ceil_centroid = compute_triangle_metrics(dy_ceil, dx, y_ceil_anchor, y_high)
    
    # Center Triangle
    dy_center = y_mid - y_center_anchor
    ctr_angle, ctr_dist, ctr_area, ctr_centroid = compute_triangle_metrics(dy_center, dx, y_center_anchor, y_mid)
    
    # Floor Triangle
    dy_floor = y_low - y_floor_anchor
    flr_angle, flr_dist, flr_area, flr_centroid = compute_triangle_metrics(dy_floor, dx, y_floor_anchor, y_low)
    
    # Pin Up Triangle (Anchor=Ceil, B=High, C=Body Top)
    dy_pin_up = y_high - body_top # Not really used for dy arg
    pnu_angle, pnu_dist, pnu_area, pnu_centroid = compute_triangle_metrics(dy_pin_up, dx, y_ceil_anchor, y_C=body_top, y_B=y_high)
    
    # Pin Down Triangle (Anchor=Floor, B=Low, C=Body Bottom)
    dy_pin_down = y_low - body_bottom
    pnd_angle, pnd_dist, pnd_area, pnd_centroid = compute_triangle_metrics(dy_pin_down, dx, y_floor_anchor, y_C=body_bottom, y_B=y_low)
    
    # Fill Dataframe
    df['Ceil angle'] = ceil_angle
    df['Ceil distance'] = ceil_dist
    df['Ceil area'] = ceil_area
    df['Ceil centroid'] = ceil_centroid
    
    df['Ctr angle'] = ctr_angle
    df['Ctr distance'] = ctr_dist
    df['Ctr area'] = ctr_area
    df['Ctr centroid'] = ctr_centroid
    
    df['Flr angle'] = flr_angle
    df['Flr distance'] = flr_dist
    df['Flr area'] = flr_area
    df['Flr centroid'] = flr_centroid
    
    df['PnU angle'] = pnu_angle
    df['PnU distance'] = pnu_dist
    df['PnU area'] = pnu_area
    df['PnU centroid'] = pnu_centroid
    
    df['PnD angle'] = pnd_angle
    df['PnD distance'] = pnd_dist
    df['PnD area'] = pnd_area
    df['PnD centroid'] = pnd_centroid
    
    return df

def run_smart_trader_geometric_strategy(df: pd.DataFrame, config: SmartTraderGeometricConfig) -> Tuple[pd.DataFrame, pd.DataFrame]:
    # Evaluate slots and quorum logic here.
    # Due to complexity of strategy slots (dynamic), we do it vectorially.
    
    n = len(df)
    long_entries = np.zeros(n, dtype=int)
    short_entries = np.zeros(n, dtype=int)
    long_exits = np.zeros(n, dtype=int)
    short_exits = np.zeros(n, dtype=int)
    
    block_long_entries = np.zeros(n, dtype=bool)
    block_short_entries = np.zeros(n, dtype=bool)
    block_long_exits = np.zeros(n, dtype=bool)
    block_short_exits = np.zeros(n, dtype=bool)
    
    for slot in config.slots:
        var = slot.get('variable')
        cond = slot.get('condition')
        threshold = slot.get('threshold', 0.0)
        upper_bound = slot.get('upper_bound', 0.0)
        apply_to = slot.get('apply_to')
        
        if var not in df.columns:
            continue
            
        series = df[var].values
        
        # Evaluate condition
        pass_cond = np.zeros(n, dtype=bool)
        if cond == '>':
            pass_cond = series > threshold
        elif cond == '<':
            pass_cond = series < threshold
        elif cond == 'between':
            pass_cond = (series > threshold) & (series < upper_bound)
        elif cond == 'cross >':
            pass_cond[1:] = (series[1:] > threshold) & (series[:-1] <= threshold)
        elif cond == 'cross <':
            pass_cond[1:] = (series[1:] < threshold) & (series[:-1] >= threshold)
        elif cond == 'rising':
            # e.g. rising over N bars. threshold acts as N.
            # Simplified: strictly greater than previous
            pass_cond[1:] = series[1:] > series[:-1]
        elif cond == 'falling':
            pass_cond[1:] = series[1:] < series[:-1]
            
        # Count passes
        if apply_to == 'Long entry':
            long_entries += pass_cond
        elif apply_to == 'Short entry':
            short_entries += pass_cond
        elif apply_to == 'Long exit':
            long_exits += pass_cond
        elif apply_to == 'Short exit':
            short_exits += pass_cond
        elif apply_to == 'Block long entry':
            block_long_entries |= pass_cond
        elif apply_to == 'Block short entry':
            block_short_entries |= pass_cond
        elif apply_to == 'Block long exit':
            block_long_exits |= pass_cond
        elif apply_to == 'Block short exit':
            block_short_exits |= pass_cond
            
    # Final quorum check
    long_signal = (long_entries >= config.min_long_entry_slots) & (~block_long_entries)
    short_signal = (short_entries >= config.min_short_entry_slots) & (~block_short_entries)
    
    long_exit_signal = (long_exits >= config.min_long_exit_slots) & (~block_long_exits)
    short_exit_signal = (short_exits >= config.min_short_exit_slots) & (~block_short_exits)
    
    # Conflict guard: if both entries fire, block both
    conflict = long_signal & short_signal
    long_signal[conflict] = False
    short_signal[conflict] = False
    
    df['long_entry'] = long_signal
    df['short_entry'] = short_signal
    df['long_exit'] = long_exit_signal
    df['short_exit'] = short_exit_signal
    
    # State tracking and trades execution (similar to other strategies)
    # Very simplified version to return state for tests.
    
    records = []
    trades = []
    
    in_position = False
    side = 0
    entry_price = 0.0
    qty = 0.0
    
    for i in range(n):
        mark_price = df['close'].iloc[i]
        
        # exit logic
        if in_position:
            if side == 1 and (df['long_exit'].iloc[i] or df['short_entry'].iloc[i]):
                # close long
                trades.append({"side": side, "entry_price": entry_price, "exit_price": mark_price, "pnl": (mark_price - entry_price)*qty})
                in_position = False
                side = 0
                
            elif side == -1 and (df['short_exit'].iloc[i] or df['long_entry'].iloc[i]):
                # close short
                trades.append({"side": side, "entry_price": entry_price, "exit_price": mark_price, "pnl": (entry_price - mark_price)*qty})
                in_position = False
                side = 0
        
        # entry logic
        if not in_position:
            if df['long_entry'].iloc[i]:
                in_position = True
                side = 1
                entry_price = mark_price
                qty = 1.0 # default qty
            elif df['short_entry'].iloc[i]:
                in_position = True
                side = -1
                entry_price = mark_price
                qty = 1.0
                
        records.append({
            "in_position": in_position,
            "side": side,
            "entry_price": entry_price if in_position else 0.0,
            "position_qty": qty if in_position else 0.0,
        })
        
    state_df = pd.DataFrame(records, index=df.index)
    trades_df = pd.DataFrame(trades)
    
    return state_df, trades_df
