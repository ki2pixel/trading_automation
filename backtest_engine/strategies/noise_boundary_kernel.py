"""
backtest_engine/strategies/noise_boundary_kernel.py

Numba JIT-compiled execution kernel for the Noise Boundary Intraday strategy.
Replaces the pure Python BrokerSimulator for massive latency reduction during optimization.
"""

from __future__ import annotations

import numpy as np
from numba import njit
import math

position_dtype = np.dtype(
    [
        ("is_active", np.bool_),
        ("side", np.int32),  # 1 for long, -1 for short
        ("qty", np.float64),
        ("entry_price", np.float64),
        ("entry_bar", np.int32),
        ("peak_price", np.float64),
        ("lowest_price", np.float64),
        ("ladder_step", np.int32),
        ("remaining_commission", np.float64),
    ],
    align=True,
)

closed_trade_dtype = np.dtype(
    [
        ("entry_bar", np.int32),
        ("exit_bar", np.int32),
        ("side", np.int32),  # 1 for long, -1 for short
        ("quantity", np.float64),
        ("entry_price", np.float64),
        ("exit_price", np.float64),
        ("gross_pnl", np.float64),
        ("commission", np.float64),
        ("net_pnl", np.float64),
        ("exit_type", np.int32),
        ("is_partial", np.bool_),
    ],
    align=True,
)

state_dtype = np.dtype(
    [
        ("cash", np.float64),
        ("position_size", np.float64),
        ("position_abs_size", np.float64),
        ("position_avg_price", np.float64),
        ("equity", np.float64),
        ("realized_net_pnl_on_fill", np.float64),
        ("estimated_net_if_closed_now", np.float64),
    ],
    align=True,
)

@njit(cache=True)
def calculate_position_size(
    price: float, equity: float, config_sizing_mode: int, target_daily_volatility: float, 
    vol_for_sizing: float, max_leverage: float, point_value: float, fx_rate: float, 
    quantity_precision: int, allow_fractional_quantity: bool
) -> float:
    # config_sizing_mode: 0 = fixed, 1 = percent_of_equity, 2 = target_volatility
    if config_sizing_mode == 0:
        size = 1.0
    elif config_sizing_mode == 1:
        size = equity * 0.1 / price
    elif config_sizing_mode == 2:
        if vol_for_sizing > 0:
            size = (equity * target_daily_volatility) / (price * vol_for_sizing)
        else:
            size = 1.0
    else:
        size = 1.0

    if size > 0:
        price_account = price * fx_rate
        denom = price_account * point_value
        if denom > 0 and equity > 0:
            max_size = (equity * max_leverage) / denom
            size = min(size, max_size)
        else:
            size = 0.0

    if size <= 0:
        return 0.0
    
    if not allow_fractional_quantity:
        size = math.floor(size)
        
    if quantity_precision >= 0:
        factor = 10.0 ** quantity_precision
        size = round(size * factor) / factor
        
    return max(size, 0.0)


@njit(cache=True)
def commission_for(
    quantity: float, price_account: float, side: int, 
    point_value: float, commission_fixed: float, commission_rate: float, 
    comm_fixed_long: float, slippage_long: float, comm_min_long: float,
    comm_fixed_short: float, slippage_short: float, comm_min_short: float
) -> float:
    notional = abs(quantity) * price_account * point_value
    fixed = commission_fixed
    rate_comm = notional * commission_rate
    slippage = 0.0
    
    if side == 1:
        fixed = comm_fixed_long if comm_fixed_long >= 0 else fixed
        slippage = slippage_long
        if comm_min_long >= 0:
            rate_comm = max(comm_min_long, rate_comm)
    elif side == -1:
        fixed = comm_fixed_short if comm_fixed_short >= 0 else fixed
        slippage = slippage_short
        if comm_min_short >= 0:
            rate_comm = max(comm_min_short, rate_comm)
            
    return fixed + slippage + rate_comm


@njit(cache=True, fastmath=True)
def _execute_pending_entry(pos, pending_side, pending_qty, exec_p, fx_rate, curr_high, curr_low, cash, point_value, 
                           commission_fixed, commission_rate, comm_fixed_long, slippage_long, comm_min_long, 
                           comm_fixed_short, slippage_short, comm_min_short, i):
    price_acc = exec_p * fx_rate
    comm = commission_for(pending_qty, price_acc, pending_side, point_value, commission_fixed, commission_rate, 
                          comm_fixed_long, slippage_long, comm_min_long, comm_fixed_short, slippage_short, comm_min_short)
    new_cash = cash - ((pending_qty * exec_p * point_value) + comm)
    
    pos["is_active"] = True
    pos["side"] = pending_side
    pos["qty"] = pending_qty
    pos["entry_price"] = exec_p
    pos["entry_bar"] = i
    pos["peak_price"] = curr_high
    pos["lowest_price"] = curr_low
    pos["ladder_step"] = 0
    pos["remaining_commission"] = comm
    
    return new_cash

@njit(cache=True, fastmath=True)
def _evaluate_exits(pos, curr_high, curr_low, curr_close, allow_overnight, minutes_until_close, exit_before_min, 
                    exit_mode_vwap, vwap_val, exit_mode_boundary, up_exit, low_exit, exit_mode_ladder, seq_ladder, 
                    stoploss_step0, takeprofit_step0, takeprofit_ratio0, stoploss_step1, takeprofit_step1):
    
    if curr_high > pos["peak_price"]: pos["peak_price"] = curr_high
    if curr_low < pos["lowest_price"]: pos["lowest_price"] = curr_low
    
    exit_action_qty = 0.0
    exit_action_type = 0
    
    if not allow_overnight and minutes_until_close <= exit_before_min:
        return pos["qty"], 1
        
    if exit_mode_vwap and not np.isnan(vwap_val):
        if pos["side"] == 1 and curr_close < vwap_val:
            return pos["qty"], 3
        elif pos["side"] == -1 and curr_close > vwap_val:
            return pos["qty"], 2
            
    if exit_mode_boundary:
        if pos["side"] == 1 and not np.isnan(low_exit) and curr_close <= low_exit:
            return pos["qty"], 4
        elif pos["side"] == -1 and not np.isnan(up_exit) and curr_close >= up_exit:
            return pos["qty"], 5
            
    if exit_mode_ladder:
        avg_price = pos["entry_price"]
        side_mult = float(pos["side"])
        pct_change = (curr_close - avg_price) / avg_price * side_mult
        
        if seq_ladder:
            step = pos["ladder_step"]
            if step == 0:
                if pct_change <= stoploss_step0:
                    return pos["qty"], 6
                elif pct_change >= takeprofit_step0:
                    pos["ladder_step"] = 1
                    return pos["qty"] * takeprofit_ratio0, 7
            elif step == 1:
                if pct_change <= stoploss_step1:
                    return pos["qty"], 8
                elif not np.isnan(takeprofit_step1) and pct_change >= takeprofit_step1:
                    return pos["qty"], 9
                    
    return exit_action_qty, exit_action_type

@njit(cache=True, fastmath=True)
def _execute_exit(pos, exit_action_qty, exit_action_type, curr_close, fx_rate, point_value, 
                  commission_fixed, commission_rate, comm_fixed_long, slippage_long, comm_min_long, 
                  comm_fixed_short, slippage_short, comm_min_short, trades, trade_idx, max_trades, 
                  cash, running_realized_pnl, i):
                  
    is_partial = (exit_action_qty < pos["qty"] * 0.999)
    exit_price = curr_close
    
    price_acc = exit_price * fx_rate
    comm = commission_for(exit_action_qty, price_acc, pos["side"], point_value, commission_fixed, commission_rate, 
                          comm_fixed_long, slippage_long, comm_min_long, comm_fixed_short, slippage_short, comm_min_short)
    
    side_mult = float(pos["side"])
    gross = (exit_price - pos["entry_price"]) * exit_action_qty * side_mult * point_value
    
    closing_ratio = exit_action_qty / pos["qty"]
    allocated_entry_comm = pos["remaining_commission"] * closing_ratio
    total_comm = allocated_entry_comm + comm
    net_pnl = gross - total_comm
    
    if trade_idx < max_trades:
        t = trades[trade_idx]
        t["entry_bar"] = pos["entry_bar"]
        t["exit_bar"] = i
        t["side"] = pos["side"]
        t["quantity"] = exit_action_qty
        t["entry_price"] = pos["entry_price"]
        t["exit_price"] = exit_price
        t["gross_pnl"] = gross
        t["commission"] = total_comm
        t["net_pnl"] = net_pnl
        t["exit_type"] = exit_action_type
        t["is_partial"] = is_partial
        
    cash += (exit_action_qty * exit_price * point_value) - comm + gross
    running_realized_pnl += net_pnl
    
    if is_partial:
        pos["qty"] -= exit_action_qty
        pos["remaining_commission"] -= allocated_entry_comm
    else:
        pos["is_active"] = False
        
    return cash, running_realized_pnl, trade_idx + 1 if trade_idx < max_trades else max_trades

@njit(cache=True, fastmath=True)
def _evaluate_entries(pos, trade_freq_bars, trade_freq_min, timing_mode_end, bars_since_open, minutes_since_open, 
                      start_min, allow_overnight, minutes_until_close, exit_before_min, curr_close, curr_high, curr_low, 
                      upper, lower, vwap_val, entry_on_high_low, use_vwap_filter, direction_mode, 
                      cash, sizing_mode, target_daily_volatility, vol_for_sizing, max_leverage, point_value, fx_rate, 
                      quantity_precision, allow_fractional_quantity):
                      
    freq_ok = True
    if trade_freq_bars > 0:
        if timing_mode_end:
            freq_ok = ((bars_since_open + 1) % trade_freq_bars == 0)
        else:
            freq_ok = (bars_since_open % trade_freq_bars == 0)
    elif trade_freq_min > 1:
        if timing_mode_end:
            freq_ok = (int(round(minutes_since_open + 1)) % int(trade_freq_min) == 0)
        else:
            freq_ok = (int(round(minutes_since_open)) % int(trade_freq_min) == 0)
            
    entry_time_allowed = True if allow_overnight else (minutes_until_close > exit_before_min)
    
    if minutes_since_open >= start_min and entry_time_allowed and freq_ok:
        long_trig = curr_high if entry_on_high_low else curr_close
        short_trig = curr_low if entry_on_high_low else curr_close
        
        long_vwap_ok = (not use_vwap_filter) or (not np.isnan(vwap_val) and long_trig > vwap_val)
        short_vwap_ok = (not use_vwap_filter) or (not np.isnan(vwap_val) and short_trig < vwap_val)
        
        if not np.isnan(upper) and long_trig > upper and long_vwap_ok and (direction_mode == 1 or direction_mode == 2):
            qty = calculate_position_size(curr_close, cash, sizing_mode, target_daily_volatility, vol_for_sizing, 
                                          max_leverage, point_value, fx_rate, quantity_precision, allow_fractional_quantity)
            if qty > 0:
                return 1, qty
        elif not np.isnan(lower) and short_trig < lower and short_vwap_ok and (direction_mode == 1 or direction_mode == 3):
            qty = calculate_position_size(curr_close, cash, sizing_mode, target_daily_volatility, vol_for_sizing, 
                                          max_leverage, point_value, fx_rate, quantity_precision, allow_fractional_quantity)
            if qty > 0:
                return -1, qty
                
    return 0, 0.0

@njit(cache=True, fastmath=True)
def run_noise_boundary_kernel(
    open_prices: np.ndarray, high_prices: np.ndarray, low_prices: np.ndarray, close_prices: np.ndarray, exec_prices: np.ndarray,
    upper_enter: np.ndarray, lower_enter: np.ndarray, vol_for_sizing_arr: np.ndarray,
    upper_exit: np.ndarray, lower_exit: np.ndarray,
    minutes_since_open_arr: np.ndarray, minutes_until_close_arr: np.ndarray, bars_since_open_arr: np.ndarray, vwap_values: np.ndarray,
    initial_cash: float,
    allow_overnight: bool, exit_before_min: float, start_min: float,
    direction_mode: int,
    trade_freq_bars: float, trade_freq_min: float, timing_mode_end: bool,
    use_vwap_filter: bool, entry_on_high_low: bool,
    exit_mode_vwap: bool, exit_mode_boundary: bool, exit_mode_ladder: bool,
    seq_ladder: bool, stoploss_step0: float, stoploss_step1: float, takeprofit_step0: float, takeprofit_step1: float, takeprofit_ratio0: float,
    sizing_mode: int, target_daily_volatility: float, max_leverage: float, point_value: float, fx_rate: float, 
    quantity_precision: int, allow_fractional_quantity: bool, drawdown_limit: float,
    commission_fixed: float, commission_rate: float, 
    comm_fixed_long: float, slippage_long: float, comm_min_long: float,
    comm_fixed_short: float, slippage_short: float, comm_min_short: float
) -> tuple[np.ndarray, np.ndarray]:
    
    n_bars = len(close_prices)
    cash = initial_cash
    
    pos = np.zeros(1, dtype=position_dtype)[0]
    pos["is_active"] = False
    
    max_trades = 100000
    trades = np.zeros(max_trades, dtype=closed_trade_dtype)
    trade_idx = 0
    
    state_arr = np.zeros(n_bars, dtype=state_dtype)
    
    pending_side = 0
    pending_qty = 0.0
    
    running_realized_pnl = 0.0
    last_realized_pnl = 0.0
    peak_equity = initial_cash
    
    for i in range(n_bars):
        curr_high = high_prices[i]
        curr_low = low_prices[i]
        curr_close = close_prices[i]
        exec_p = exec_prices[i]
        
        minutes_since_open = minutes_since_open_arr[i]
        minutes_until_close = minutes_until_close_arr[i]
        vwap_val = vwap_values[i]
        bars_since_open = bars_since_open_arr[i]
        
        # 1. Execute Pending Entry
        if pending_side != 0:
            cash = _execute_pending_entry(pos, pending_side, pending_qty, exec_p, fx_rate, curr_high, curr_low, cash, point_value, 
                                          commission_fixed, commission_rate, comm_fixed_long, slippage_long, comm_min_long, 
                                          comm_fixed_short, slippage_short, comm_min_short, i)
            pending_side = 0
            pending_qty = 0.0
            
        # 2. Evaluate and Execute Exits
        if pos["is_active"]:
            exit_action_qty, exit_action_type = _evaluate_exits(
                pos, curr_high, curr_low, curr_close, allow_overnight, minutes_until_close, exit_before_min, 
                exit_mode_vwap, vwap_val, exit_mode_boundary, upper_exit[i], lower_exit[i], exit_mode_ladder, seq_ladder, 
                stoploss_step0, takeprofit_step0, takeprofit_ratio0, stoploss_step1, takeprofit_step1
            )
            
            if exit_action_qty > 0:
                cash, running_realized_pnl, trade_idx = _execute_exit(
                    pos, exit_action_qty, exit_action_type, curr_close, fx_rate, point_value, commission_fixed, commission_rate, 
                    comm_fixed_long, slippage_long, comm_min_long, comm_fixed_short, slippage_short, comm_min_short, 
                    trades, trade_idx, max_trades, cash, running_realized_pnl, i
                )
                    
        # 3. State tracking & Drawdown Early Exit
        equity = cash
        open_pnl = 0.0
        pos_size = 0.0
        pos_avg_price = 0.0
        
        if pos["is_active"]:
            price_acc = curr_close * fx_rate
            side_mult = float(pos["side"])
            pos_size = pos["qty"] * side_mult
            pos_avg_price = pos["entry_price"]
            open_pnl = (price_acc - pos_avg_price) * pos["qty"] * side_mult * point_value
            equity = cash + pos["qty"] * price_acc * side_mult * point_value
            
        realized_pnl_delta = running_realized_pnl - last_realized_pnl
        last_realized_pnl = running_realized_pnl
        
        peak_equity = max(peak_equity, equity)
        if not math.isnan(drawdown_limit) and drawdown_limit > 0 and peak_equity > 0:
            drawdown_pct = (peak_equity - equity) / peak_equity * 100.0
            if drawdown_pct > drawdown_limit:
                if pos["is_active"]:
                    cash, running_realized_pnl, trade_idx = _execute_exit(
                        pos, pos["qty"], 10, exec_p, fx_rate, point_value, commission_fixed, commission_rate, 
                        comm_fixed_long, slippage_long, comm_min_long, comm_fixed_short, slippage_short, comm_min_short, 
                        trades, trade_idx, max_trades, cash, running_realized_pnl, i
                    )
                    equity = cash
                    open_pnl = 0.0
                    pos_size = 0.0
                    pos_avg_price = 0.0
                    realized_pnl_delta = running_realized_pnl - last_realized_pnl
                    last_realized_pnl = running_realized_pnl
                
                state_arr[i]["cash"] = cash
                state_arr[i]["position_size"] = pos_size
                state_arr[i]["position_abs_size"] = abs(pos_size)
                state_arr[i]["position_avg_price"] = pos_avg_price
                state_arr[i]["equity"] = equity
                state_arr[i]["realized_net_pnl_on_fill"] = realized_pnl_delta
                state_arr[i]["estimated_net_if_closed_now"] = open_pnl
                
                for j in range(i + 1, n_bars):
                    state_arr[j]["cash"] = cash
                    state_arr[j]["position_size"] = 0.0
                    state_arr[j]["position_abs_size"] = 0.0
                    state_arr[j]["position_avg_price"] = 0.0
                    state_arr[j]["equity"] = cash
                    state_arr[j]["realized_net_pnl_on_fill"] = 0.0
                    state_arr[j]["estimated_net_if_closed_now"] = 0.0
                break
                
        state_arr[i]["cash"] = cash
        state_arr[i]["position_size"] = pos_size
        state_arr[i]["position_abs_size"] = abs(pos_size)
        state_arr[i]["position_avg_price"] = pos_avg_price
        state_arr[i]["equity"] = equity
        state_arr[i]["realized_net_pnl_on_fill"] = realized_pnl_delta
        state_arr[i]["estimated_net_if_closed_now"] = open_pnl

        # 4. Entry Evaluation
        if not pos["is_active"]:
            pending_side, pending_qty = _evaluate_entries(
                pos, trade_freq_bars, trade_freq_min, timing_mode_end, bars_since_open, minutes_since_open, 
                start_min, allow_overnight, minutes_until_close, exit_before_min, curr_close, curr_high, curr_low, 
                upper_enter[i], lower_enter[i], vwap_val, entry_on_high_low, use_vwap_filter, direction_mode, 
                cash, sizing_mode, target_daily_volatility, vol_for_sizing_arr[i], max_leverage, point_value, fx_rate, 
                quantity_precision, allow_fractional_quantity
            )
                        
    return trades[:trade_idx], state_arr
