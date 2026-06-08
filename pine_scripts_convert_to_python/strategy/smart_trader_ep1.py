import numpy as np
import pandas as pd
from numba import njit
from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, Field
import math

class SmartTraderEP1Config(BaseModel):
    calc_method: Literal["Geometry (Source File)", "Intrabar (Precise)"] = "Geometry (Source File)"
    universal_len: int = 20
    long_power_min: float = 50.0
    short_power_max: float = 30.0
    opp_dom_threshold: float = 0.0
    max_decay_angle: float = 60.0
    
    enable_stop_loss: bool = False
    stop_loss_pct: float = 0.0
    enable_take_profit: bool = False
    take_profit_pct: float = 0.0
    
    sl_buffer_pct: float = 0.15
    tp_buffer_pct: float = 0.05
    allow_long: bool = True
    allow_short: bool = True

@njit
def compute_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    n = len(close)
    atr = np.zeros(n, dtype=np.float64)
    tr = np.zeros(n, dtype=np.float64)
    tr[0] = high[0] - low[0]
    for i in range(1, n):
        tr1 = high[i] - low[i]
        tr2 = abs(high[i] - close[i-1])
        tr3 = abs(low[i] - close[i-1])
        tr[i] = max(tr1, tr2, tr3)
    atr[0] = tr[0]
    for i in range(1, n):
        atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
    return atr

@njit
def _compute_ep1_signals(
    open_p, high, low, close, vol, vol_up, vol_down, atr,
    is_intrabar_mode, universal_len,
    long_power_min, short_power_max, opp_dom_threshold, max_decay_angle
):
    n = len(close)
    signals = np.zeros(n, dtype=np.int8) # 1: LONG, -1: SHORT, 0: NO_TRADE
    strat_hb_price = np.full(n, np.nan)
    strat_hs_price = np.full(n, np.nan)
    
    vol_b = np.zeros(n, dtype=np.float64)
    vol_s = np.zeros(n, dtype=np.float64)
    
    for i in range(n):
        if is_intrabar_mode and not np.isnan(vol_up[i]):
            vol_b[i] = vol_up[i]
            vol_s[i] = vol_down[i]
        else:
            r = high[i] - low[i]
            if r == 0:
                vol_b[i] = vol[i] * 0.5
                vol_s[i] = vol[i] * 0.5
            else:
                vol_b[i] = vol[i] * ((close[i] - low[i]) / r)
                vol_s[i] = vol[i] * ((high[i] - close[i]) / r)

    for i in range(n):
        if i < universal_len:
            continue
            
        start_idx = i - universal_len + 1
        
        hb_val = -1.0; hb_idx = -1
        hs_val = -1.0; hs_idx = -1
        lb_val = 1e18; lb_idx = -1
        ls_val = 1e18; ls_idx = -1
        
        for j in range(i, start_idx - 1, -1):
            vb = vol_b[j]
            vs = vol_s[j]
            if vb > hb_val: hb_val = vb; hb_idx = j
            if vs > hs_val: hs_val = vs; hs_idx = j
            if vb > 0 and vb < lb_val: lb_val = vb; lb_idx = j
            if vs > 0 and vs < ls_val: ls_val = vs; ls_idx = j

        hb_price = high[hb_idx] if hb_idx != -1 else np.nan
        sh_hb = i - hb_idx if hb_idx != -1 else 9999
        remaining_pct = np.nan
        decay_angle = 0.0
        cum_delta = 0.0
        
        if hb_idx != -1:
            cum_b = 0.0; cum_s = 0.0
            for k in range(hb_idx + 1, i + 1):
                cum_b += vol_b[k]
                cum_s += vol_s[k]
            y_val = cum_s
            z_val = hb_val - y_val
            progress = (y_val / hb_val) * 100.0 if hb_val > 0 else 0.0
            remaining_pct = (z_val / hb_val) * 100.0 if hb_val > 0 else np.nan
            age = i - hb_idx
            avgRate = progress / age if age > 0 else 0.0
            decay_angle = -math.atan(avgRate / 5.0) * 180.0 / math.pi
            cum_delta = cum_b - cum_s

        hs_price = low[hs_idx] if hs_idx != -1 else np.nan
        sh_hs = i - hs_idx if hs_idx != -1 else 9999
        
        strat_hb_price[i] = hb_price
        strat_hs_price[i] = hs_price
        
        sh_lb = i - lb_idx if lb_idx != -1 else 9999
        sh_ls = i - ls_idx if ls_idx != -1 else 9999
        
        sh_hb100 = 9999; sh_hb200 = 9999
        if hb_idx != -1 and hb_val > 0:
            n1 = hb_val * 1.0; n2 = hb_val * 2.0
            cum = 0.0
            for k in range(hb_idx + 1, i + 1):
                cum += vol_s[k]
                ba = i - k
                if cum >= n1 and sh_hb100 == 9999: sh_hb100 = ba
                if cum >= n2 and sh_hb200 == 9999: sh_hb200 = ba

        sh_hs100 = 9999; sh_hs200 = 9999
        if hs_idx != -1 and hs_val > 0:
            n1 = hs_val * 1.0; n2 = hs_val * 2.0
            cum = 0.0
            for k in range(hs_idx + 1, i + 1):
                cum += vol_b[k]
                ba = i - k
                if cum >= n1 and sh_hs100 == 9999: sh_hs100 = ba
                if cum >= n2 and sh_hs200 == 9999: sh_hs200 = ba
                
        nearest_type = 0
        nearest_shift = 9999
        nearest_name = 0
        
        if sh_hb < nearest_shift: nearest_shift = sh_hb; nearest_name = 1; nearest_type = 1
        if sh_hs < nearest_shift: nearest_shift = sh_hs; nearest_name = 2; nearest_type = -1
        if sh_lb < nearest_shift: nearest_shift = sh_lb; nearest_name = 3; nearest_type = 1
        if sh_ls < nearest_shift: nearest_shift = sh_ls; nearest_name = 4; nearest_type = -1
        if sh_hb100 < nearest_shift: nearest_shift = sh_hb100; nearest_name = 5; nearest_type = -1
        if sh_hb200 < nearest_shift: nearest_shift = sh_hb200; nearest_name = 6; nearest_type = -1
        if sh_hs100 < nearest_shift: nearest_shift = sh_hs100; nearest_name = 7; nearest_type = 1
        if sh_hs200 < nearest_shift: nearest_shift = sh_hs200; nearest_name = 8; nearest_type = 1
        
        post_bullish = 0; post_bearish = 0
        if nearest_shift > 0 and nearest_shift < 9999:
            nn_idx = i - nearest_shift
            limit = min(i + 1, nn_idx + 1 + 5)
            for k in range(nn_idx + 1, limit):
                op_k = close[k-1] if k > 0 else (high[k]+low[k])/2.0
                cl_k = close[k]
                if cl_k > op_k: post_bullish += 1
                elif cl_k < op_k: post_bearish += 1
                
        post_momentum = 0
        if post_bullish > post_bearish: post_momentum = 1
        elif post_bearish > post_bullish: post_momentum = -1
        
        seg_len_base = max(1, universal_len // 5)
        sxh=0.0; syh=0.0; sxyh=0.0; sx2h=0.0; nh=0
        sxl=0.0; syl=0.0; sxyl=0.0; sx2l=0.0; nl=0
        for k in range(5):
            seg_start = start_idx + k * seg_len_base
            rem = (i + 1) - seg_start
            if rem <= 0: break
            slen = min(seg_len_base, rem) if k < 4 else rem
            
            m_hi = -1e18; ba_hi = -1
            m_lo = 1e18; ba_lo = -1
            for j in range(slen):
                sh = seg_start + j
                if high[sh] > m_hi: m_hi = high[sh]; ba_hi = sh
                if low[sh] < m_lo: m_lo = low[sh]; ba_lo = sh
                
            if ba_hi != -1:
                sxh += ba_hi; syh += m_hi; sxyh += ba_hi*m_hi; sx2h += ba_hi*ba_hi; nh += 1
            if ba_lo != -1:
                sxl += ba_lo; syl += m_lo; sxyl += ba_lo*m_lo; sx2l += ba_lo*ba_lo; nl += 1
                
        slope_hi = 0.0; intercept_hi = np.nan
        if nh >= 2:
            den = nh * sx2h - sxh * sxh
            if den != 0: slope_hi = (nh * sxyh - sxh * syh) / den
            if nh != 0: intercept_hi = (syh - slope_hi * sxh) / nh
            
        slope_lo = 0.0; intercept_lo = np.nan
        if nl >= 2:
            den = nl * sx2l - sxl * sxl
            if den != 0: slope_lo = (nl * sxyl - sxl * syl) / den
            if nl != 0: intercept_lo = (syl - slope_lo * sxl) / nl
            
        th = atr[i] * 0.001
        trend_dir = 0
        if slope_hi > th and slope_lo > th: trend_dir = 1
        elif slope_hi < -th and slope_lo < -th: trend_dir = -1
        
        zone = 0
        if not np.isnan(hb_price) and not np.isnan(intercept_hi) and not np.isnan(intercept_lo) and hb_idx != -1:
            hi_hb = slope_hi * hb_idx + intercept_hi
            lo_hb = slope_lo * hb_idx + intercept_lo
            r_ch = hi_hb - lo_hb
            pos_pct = ((hb_price - lo_hb) / r_ch) * 100.0 if r_ch > 0 else 50.0
            if pos_pct >= 100: zone = 2
            elif pos_pct >= 75: zone = 1
            elif pos_pct >= 25: zone = 0
            elif pos_pct > 0: zone = -1
            else: zone = -2
            
        price_above_hb = close[i] > hb_price if not np.isnan(hb_price) else True
        price_above_hs = close[i] > hs_price if not np.isnan(hs_price) else True
        
        sig = 0
        if not np.isnan(remaining_pct):
            is_opp_dom = remaining_pct < opp_dom_threshold
            power_strong = remaining_pct >= long_power_min
            power_weak = remaining_pct <= short_power_max
            delta_pos = cum_delta > 0
            delta_neg = cum_delta < 0
            post_bullish_mom = post_momentum == 1
            post_bearish_mom = post_momentum == -1
            
            recent_event = nearest_shift <= 2
            
            if recent_event and nearest_type == -1 and post_bullish_mom:
                if post_bullish >= 3: sig = 1
                else: sig = 0
            elif recent_event and nearest_type == -1 and post_bearish_mom:
                sig = -1
            elif recent_event and nearest_type == 1 and post_bullish_mom:
                sig = 1
            elif recent_event and nearest_type == 1 and post_bearish_mom:
                if post_bearish >= 3: sig = -1
                else: sig = 0
            else:
                if trend_dir == 1:
                    if delta_pos and (power_strong or post_bullish_mom): sig = 1
                    elif is_opp_dom and delta_neg and post_bearish_mom: sig = -1
                    elif delta_pos: sig = 1
                elif trend_dir == -1:
                    if delta_neg and (is_opp_dom or post_bearish_mom): sig = -1
                    elif delta_pos and power_strong and post_bullish_mom: sig = 1
                    elif delta_neg: sig = -1
                else:
                    if delta_pos and post_bullish_mom: sig = 1
                    elif delta_neg and post_bearish_mom: sig = -1
            
            if sig == 1 and not price_above_hb and not price_above_hs: sig = 0
            if sig == -1 and price_above_hb and price_above_hs: sig = 0
            
        signals[i] = sig
        
    return signals, strat_hb_price, strat_hs_price

def add_smart_trader_ep1_features(df: pd.DataFrame, config: SmartTraderEP1Config) -> pd.DataFrame:
    open_p = df['open'].values.astype(np.float64)
    high = df['high'].values.astype(np.float64)
    low = df['low'].values.astype(np.float64)
    close = df['close'].values.astype(np.float64)
    vol = df['volume'].values.astype(np.float64)
    
    vol_up = df['up_volume'].values.astype(np.float64) if 'up_volume' in df.columns else np.full(len(df), np.nan)
    vol_down = df['down_volume'].values.astype(np.float64) if 'down_volume' in df.columns else np.full(len(df), np.nan)
    
    atr = compute_atr(high, low, close)
    is_intrabar = config.calc_method == "Intrabar (Precise)"
    
    signals, hb_price, hs_price = _compute_ep1_signals(
        open_p, high, low, close, vol, vol_up, vol_down, atr,
        is_intrabar, config.universal_len, config.long_power_min,
        config.short_power_max, config.opp_dom_threshold, config.max_decay_angle
    )
    
    df['long_entry'] = (signals == 1) & config.allow_long
    df['short_entry'] = (signals == -1) & config.allow_short
    df['long_exit'] = (signals == -1)
    df['short_exit'] = (signals == 1)
    
    df['strat_hb_price'] = hb_price
    df['strat_hs_price'] = hs_price
    
    return df

def run_smart_trader_ep1_strategy(df: pd.DataFrame, config: SmartTraderEP1Config) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df = add_smart_trader_ep1_features(df, config)
    n = len(df)
    records = []
    trades = []
    
    in_position = False
    side = 0
    entry_price = 0.0
    qty = 0.0
    
    long_entries = df['long_entry'].values
    short_entries = df['short_entry'].values
    long_exits = df['long_exit'].values
    short_exits = df['short_exit'].values
    hb_price = df['strat_hb_price'].values
    hs_price = df['strat_hs_price'].values
    close = df['close'].values
    
    for i in range(n):
        mark_price = close[i]
        
        if in_position:
            exit_triggered = False
            if side == 1:
                sl_price = hs_price[i] - mark_price * (config.sl_buffer_pct / 100.0) if not np.isnan(hs_price[i]) else -1e18
                tp_price = hb_price[i] - mark_price * (config.tp_buffer_pct / 100.0) if not np.isnan(hb_price[i]) else 1e18
                if mark_price <= sl_price or mark_price >= tp_price or long_exits[i]:
                    exit_triggered = True
            elif side == -1:
                sl_price = hb_price[i] + mark_price * (config.sl_buffer_pct / 100.0) if not np.isnan(hb_price[i]) else 1e18
                tp_price = hs_price[i] + mark_price * (config.tp_buffer_pct / 100.0) if not np.isnan(hs_price[i]) else -1e18
                if mark_price >= sl_price or mark_price <= tp_price or short_exits[i]:
                    exit_triggered = True
                    
            if exit_triggered:
                pnl = (mark_price - entry_price)*qty if side == 1 else (entry_price - mark_price)*qty
                trades.append({"side": side, "entry_price": entry_price, "exit_price": mark_price, "pnl": pnl})
                in_position = False
                side = 0
        
        if not in_position:
            if long_entries[i]:
                in_position = True
                side = 1
                entry_price = mark_price
                qty = 1.0
            elif short_entries[i]:
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
