import numpy as np
import pandas as pd
from dataclasses import dataclass

try:
    import numba
    from numba import njit
except ImportError:
    def njit(cache=True):
        def decorator(func):
            return func
        return decorator

@dataclass
class DualRsiDcaLongConfig:
    base_order_size: float = 90.0
    use_limit_base: bool = False
    ao_count: int = 5
    ao_size: float = 110.0
    ao_step: float = 1.3
    ao_step_mult: float = 1.3
    ao_size_mult: float = 1.25
    
    entry_rsi_len: int = 14
    entry_rsi_level: float = 31.0
    
    exit_rsi_len: int = 14
    exit_rsi_level: float = 69.0
    min_profit_pct: float = 2.4
    
    process_orders_on_close: bool = True

def _rma(x: pd.Series, n: int) -> pd.Series:
    """Rolling Moving Average (RMA) équivalent à ta.rma en Pine Script"""
    alpha = 1.0 / n
    return x.ewm(alpha=alpha, adjust=False).mean()

def _rsi(close: pd.Series, length: int) -> pd.Series:
    """Calcul du RSI équivalent à ta.rsi"""
    delta = close.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    
    rma_up = _rma(up, length)
    rma_down = _rma(down, length)
    
    rs = rma_up / rma_down
    rsi = np.where(rma_down == 0, 100.0, 100.0 - (100.0 / (1.0 + rs)))
    return pd.Series(rsi, index=close.index)

def add_dual_rsi_dca_long_features(df: pd.DataFrame, config: DualRsiDcaLongConfig) -> pd.DataFrame:
    """Ajoute les indicateurs RSI et signaux de croisement nécessaires."""
    df_out = df.copy()
    
    # Calcul RSI
    df_out['entry_rsi'] = _rsi(df_out['close'], config.entry_rsi_len)
    df_out['exit_rsi'] = _rsi(df_out['close'], config.exit_rsi_len)
    
    # Signaux Cross Up / Down
    df_out['entry_rsi_prev'] = df_out['entry_rsi'].shift(1)
    df_out['exit_rsi_prev'] = df_out['exit_rsi'].shift(1)
    
    df_out['entry_cross_up'] = (df_out['entry_rsi_prev'] < config.entry_rsi_level) & (df_out['entry_rsi'] >= config.entry_rsi_level)
    df_out['exit_cross_down'] = (df_out['exit_rsi_prev'] > config.exit_rsi_level) & (df_out['exit_rsi'] <= config.exit_rsi_level)
    
    return df_out


@njit(cache=True)
def _compute_dca_numba(
    close_arr: np.ndarray,
    entry_cross_up: np.ndarray,
    exit_cross_down: np.ndarray,
    time_indices: np.ndarray,
    base_order_size: float,
    ao_count: int,
    ao_sizes: np.ndarray,
    ao_thresholds: np.ndarray,
    min_profit_pct: float
):
    n_bars = len(close_arr)
    
    in_position = False
    base_entry = np.nan
    ao_filled = 0
    position_size = 0.0
    position_avg_price = 0.0
    realized_pnl = 0.0
    
    max_trades = n_bars
    trades_out = np.empty((max_trades, 6), dtype=np.float64)
    trade_count = 0
    
    for i in range(n_bars):
        close_price = close_arr[i]
        time_idx = time_indices[i]
        
        # 3. EXIT CHECK
        if in_position:
            avg_px = position_avg_price
            min_tp_price = avg_px * (1.0 + min_profit_pct / 100.0)
            profit_armed = close_price >= min_tp_price
            
            if profit_armed and exit_cross_down[i]:
                exit_price = close_price
                pnl = (exit_price - position_avg_price) * position_size
                realized_pnl += pnl
                
                trades_out[trade_count, 0] = time_idx
                trades_out[trade_count, 1] = 2.0  # close
                trades_out[trade_count, 2] = exit_price
                trades_out[trade_count, 3] = position_size
                trades_out[trade_count, 4] = pnl
                trades_out[trade_count, 5] = -1.0 # RSI_TP
                trade_count += 1
                
                in_position = False
                base_entry = np.nan
                ao_filled = 0
                position_size = 0.0
                position_avg_price = 0.0
                continue
                
        # 1. ENTRY CHECK (Base Order)
        open_base = not in_position and entry_cross_up[i]
        if open_base:
            qty = base_order_size / close_price
            position_size += qty
            position_avg_price = close_price
            base_entry = close_price
            ao_filled = 0
            in_position = True
            
            trades_out[trade_count, 0] = time_idx
            trades_out[trade_count, 1] = 1.0  # entry
            trades_out[trade_count, 2] = close_price
            trades_out[trade_count, 3] = qty
            trades_out[trade_count, 4] = 0.0
            trades_out[trade_count, 5] = 0.0 # Long_Base
            trade_count += 1
            
        # 2. AVERAGING ORDERS CHECK
        elif in_position and ao_filled < ao_count and not np.isnan(base_entry):
            next_idx = ao_filled + 1
            threshold = ao_thresholds[next_idx]
            trigger_px = base_entry * (1.0 - threshold / 100.0)
            
            if close_price <= trigger_px:
                ao_qty_usdt = ao_sizes[next_idx]
                qty = ao_qty_usdt / close_price
                
                # Update position
                total_cost = (position_size * position_avg_price) + (qty * close_price)
                position_size += qty
                position_avg_price = total_cost / position_size
                
                ao_filled = next_idx
                
                trades_out[trade_count, 0] = time_idx
                trades_out[trade_count, 1] = 1.0  # entry
                trades_out[trade_count, 2] = close_price
                trades_out[trade_count, 3] = qty
                trades_out[trade_count, 4] = 0.0
                trades_out[trade_count, 5] = float(next_idx) # Long_AO_{next_idx}
                trade_count += 1

    return realized_pnl, trades_out[:trade_count]

def run_dual_rsi_dca_long_strategy(df: pd.DataFrame, config: DualRsiDcaLongConfig, compute_full_metrics: bool = True) -> dict:
    """Run the backtest loop and return metrics using Numba JIT compilation."""
    df_eval = add_dual_rsi_dca_long_features(df, config)
    
    # Pre-calculate geometric parameters for AO
    ao_thresholds = np.zeros(config.ao_count + 1)
    ao_sizes = np.zeros(config.ao_count + 1)
    
    dev = 0.0
    step = config.ao_step
    for i in range(1, config.ao_count + 1):
        if i == 1:
            dev = step
        else:
            step = step * config.ao_step_mult
            dev += step
        ao_thresholds[i] = dev
        ao_sizes[i] = config.ao_size * (config.ao_size_mult ** (i - 1))
        
    close_arr = df_eval['close'].to_numpy(dtype=np.float64)
    entry_arr = df_eval['entry_cross_up'].fillna(False).to_numpy(dtype=np.bool_)
    exit_arr = df_eval['exit_cross_down'].fillna(False).to_numpy(dtype=np.bool_)
    time_indices = np.arange(len(df_eval), dtype=np.float64)
    
    realized_pnl, trades_raw = _compute_dca_numba(
        close_arr,
        entry_arr,
        exit_arr,
        time_indices,
        float(config.base_order_size),
        int(config.ao_count),
        ao_sizes,
        ao_thresholds,
        float(config.min_profit_pct)
    )
    
    # Reconstruct trades dict format
    trades = []
    ts_index = df_eval.index
    for t in trades_raw:
        idx = int(t[0])
        type_code = int(t[1])
        price = t[2]
        qty = t[3]
        pnl = t[4]
        comment_code = int(t[5])
        
        t_type = 'close' if type_code == 2 else 'entry'
        if comment_code == -1:
            comment = 'RSI_TP'
        elif comment_code == 0:
            comment = 'Long_Base'
        else:
            comment = f'Long_AO_{comment_code}'
            
        trades.append({
            'type': t_type,
            'time': ts_index[idx] if hasattr(ts_index, '__getitem__') else idx,
            'price': price,
            'qty': qty,
            'pnl': pnl if type_code == 2 else 0.0,
            'comment': comment
        })
        
    metrics = {
        'total_trades': len([t for t in trades if t['type'] == 'close']),
        'realized_pnl': realized_pnl,
        'trades': trades
    }
    
    return metrics
