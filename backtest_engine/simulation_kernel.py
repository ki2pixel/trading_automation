"""
backtest_engine/simulation_kernel.py

Numba JIT-compiled broker simulation kernel.
Provides a strict event-driven path-dependent execution loop at native machine speed.
"""

from __future__ import annotations

import numpy as np
from numba import njit

# Definition of the structured datatype representing the C-aligned active position layout.
# This structure enables direct memory offset arithmetic inside the LLVM generated code.
position_dtype = np.dtype(
    [
        ("is_active", np.bool_),
        ("strategy_id", np.int32),
        ("qty", np.float64),
        ("entry_price", np.float64),
        ("entry_bar", np.int32),
        ("trailing_high", np.float64),
        ("stop_loss", np.float64),
        ("take_profit", np.float64),
    ],
    align=True,
)


@njit(cache=True, fastmath=True)
def run_broker_simulation_kernel(
    open_prices: np.ndarray,
    high_prices: np.ndarray,
    low_prices: np.ndarray,
    close_prices: np.ndarray,
    raw_signals: np.ndarray,
    strategy_ids: np.ndarray,
    initial_cash: float,
    capped_bucket_limit: float,
    stop_loss_pct: float,
    trailing_stop_pct: float,
    take_profit_pct: float,
) -> np.ndarray:
    """
    Sequential broker simulator compiled in strict nopython mode.
    Manages multi-strategy portfolios under dynamic shared capital constraints (capped bucket model).

    Parameters
    ----------
    open_prices, high_prices, low_prices, close_prices : 1D float64 arrays
        Market OHLC prices.
    raw_signals : 2D int8 array of shape (n_strategies, n_bars)
        Binary entries/exits (1: long signal, -1: short/exit, 0: flat).
    strategy_ids : 1D int32 array
        Unique identifiers for each of the optimized strategies.
    initial_cash : float
        Starting account capital.
    capped_bucket_limit : float
        The maximum allocated capital allowed globally across all strategies combined.
    stop_loss_pct, trailing_stop_pct, take_profit_pct : float
        Hyperparameter levels configured by the optimizer.
    """
    n_bars = len(close_prices)
    cash = initial_cash
    allocated_capital = 0.0

    n_strategies = len(strategy_ids)
    positions = np.zeros(n_strategies, dtype=position_dtype)
    for s in range(n_strategies):
        positions[s]["is_active"] = False
        positions[s]["strategy_id"] = strategy_ids[s]

    equity_curve = np.empty(n_bars, dtype=np.float64)

    for i in range(n_bars):
        curr_open = open_prices[i]
        curr_high = high_prices[i]
        curr_low = low_prices[i]
        curr_close = close_prices[i]

        # 1. Evaluate protection exits & trailing stops
        for s in range(n_strategies):
            pos = positions[s]
            if pos["is_active"]:
                # Update peak price for trailing stop calculations
                if curr_high > pos["trailing_high"]:
                    pos["trailing_high"] = curr_high
                    pos["stop_loss"] = curr_high * (1.0 - trailing_stop_pct)

                # Stop Loss or Trailing Stop execution
                if curr_low <= pos["stop_loss"]:
                    exit_price = min(pos["stop_loss"], curr_open)  # Account for overnight or bar opening gaps
                    pnl = (exit_price - pos["entry_price"]) * pos["qty"]
                    execution_value = (pos["entry_price"] * pos["qty"]) + pnl
                    cash += execution_value
                    allocated_capital -= (pos["entry_price"] * pos["qty"])
                    pos["is_active"] = False

                # Take Profit execution (Bracket Exit)
                elif curr_high >= pos["take_profit"]:
                    exit_price = max(pos["take_profit"], curr_open)
                    pnl = (exit_price - pos["entry_price"]) * pos["qty"]
                    execution_value = (pos["entry_price"] * pos["qty"]) + pnl
                    cash += execution_value
                    allocated_capital -= (pos["entry_price"] * pos["qty"])
                    pos["is_active"] = False

        # 2. Evaluate entry signals
        for s in range(n_strategies):
            pos = positions[s]
            signal = raw_signals[s, i]

            if not pos["is_active"] and signal != 0:
                # Capped Bucket allocation check
                available_to_allocate = min(cash, capped_bucket_limit - allocated_capital)

                if available_to_allocate > 0.0:
                    pos["is_active"] = True
                    pos["entry_price"] = curr_close
                    pos["qty"] = available_to_allocate / curr_close
                    pos["trailing_high"] = curr_close
                    pos["stop_loss"] = curr_close * (1.0 - stop_loss_pct)
                    pos["take_profit"] = curr_close * (1.0 + take_profit_pct)
                    pos["entry_bar"] = i

                    cash -= available_to_allocate
                    allocated_capital += available_to_allocate

        # 3. Compute Portfolio Net Asset Value (Equity Curve)
        current_equity = cash
        for s in range(n_strategies):
            if positions[s]["is_active"]:
                current_equity += curr_close * positions[s]["qty"]
        equity_curve[i] = current_equity

    return equity_curve
