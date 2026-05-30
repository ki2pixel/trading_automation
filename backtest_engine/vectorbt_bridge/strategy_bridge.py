"""Strategy bridge: run backtest_engine signals through VectorBT portfolio simulation.

The bridge extracts raw entry/exit signals produced by our converted Pine strategies
and feeds them into ``vectorbt.Portfolio.from_signals``, using the same commission,
slippage and sizing assumptions so that results can be compared head-to-head.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backtest_engine.reports import BacktestRunResult
from backtest_engine.strategy_registry import StrategyRegistry

# Lazily import vectorbt so the module can be imported even when vbt is absent.
try:
    import vectorbt as vbt
except ImportError:
    vbt = None  # type: ignore[assignment]


def _extract_signals(result: BacktestRunResult) -> tuple[pd.Series, pd.Series]:
    """Return entry/exit boolean Series from a backtest_engine result.

    The converted HMA strategy writes ``long_signal`` and ``short_signal``
    columns into ``result.state``.  We treat them as VectorBT entry/exit
    signals respectively.
    """
    state = result.state
    entries = state.get("long_signal", pd.Series(False, index=state.index))
    exits = state.get("short_signal", pd.Series(False, index=state.index))

    # Ensure booleans (the Pine conversion may write 0/1 floats)
    entries = entries.fillna(0.0).astype(bool)
    exits = exits.fillna(0.0).astype(bool)

    return entries, exits


def run_strategy_via_vectorbt(
    data: pd.DataFrame,
    symbol: str,
    overrides: Any | None = None,
    initial_capital: float = 1000.0,
    timeframe_minutes: int = 5,
    strategy: str = "hma_crossover",
    repo_root: Path | None = None,
) -> "vbt.Portfolio":
    """Run the selected strategy natively, then re-simulate the extracted signals in VectorBT.

    Parameters
    ----------
    data: OHLCV DataFrame with DatetimeIndex.
    symbol: ticker symbol (for logging only).
    overrides: strategy parameter overrides.
    initial_capital: cash allocated at start.
    timeframe_minutes: bar resolution (used for annualisation of metrics).
    strategy: name of the strategy to run via the registry.
    repo_root: repository root directory Path for FX data dynamic loading.

    Returns
    -------
    A ``vectorbt.Portfolio`` instance built from the same signals.
    """
    if vbt is None:
        raise RuntimeError("vectorbt is not installed")

    info = StrategyRegistry.get(strategy)
    overrides = overrides or info.overrides_class()

    # 1) Run our native engine with lightweight metrics (no full metric compute)
    native_result = info.run_function(
        data=data,
        symbol=symbol,
        overrides=overrides,
        initial_capital=initial_capital,
        timeframe_minutes=timeframe_minutes,
        compute_full_metrics=False,
        repo_root=repo_root,
    )

    # 2) Extract signals
    entries, exits = _extract_signals(native_result)

    # 3) Determine VectorBT-compatible execution assumptions
    cfg = asdict(overrides)
    fees = cfg.get("estimated_commission_per_order_long") or 0.0
    slippage = cfg.get("estimated_slippage_per_side_long") or 0.0

    # VectorBT's from_signals uses close price by default; our engine can execute
    # on next-bar open.  We expose both variants so the caller can compare.
    price = data["close"]  # VectorBT default

    # 4) Build portfolio
    pf = vbt.Portfolio.from_signals(
        close=price,
        entries=entries,
        exits=exits,
        init_cash=initial_capital,
        fees=fees,
        slippage=slippage,
        freq=f"{timeframe_minutes}min",
    )

    return pf


def _native_trade_list(native_result: BacktestRunResult) -> pd.DataFrame:
    """Normalise le DataFrame trades natif pour comparaison."""
    trades = native_result.trades.copy()
    if trades.empty:
        return trades
    # Ensure numeric
    for col in ["net_pnl", "gross_pnl", "entry_price", "exit_price", "qty"]:
        if col in trades.columns:
            trades[col] = pd.to_numeric(trades[col], errors="coerce")
    return trades


def _vectorbt_trade_list(pf: "vbt.Portfolio") -> pd.DataFrame:
    """Extract a trade list from a VectorBT portfolio."""
    if pf.trades.count() == 0:
        return pd.DataFrame()
    # VectorBT returns a Records object; convert to readable DataFrame
    vt = pf.trades.records_readable
    # Rename to our convention
    rename = {
        "Entry Timestamp": "entry_index",
        "Exit Timestamp": "exit_index",
        "Size": "qty",
        "Entry Price": "entry_price",
        "Exit Price": "exit_price",
        "PnL": "net_pnl",
    }
    vt = vt.rename(columns={k: v for k, v in rename.items() if k in vt.columns})
    return vt


def compare_results(
    native_result: BacktestRunResult,
    pf: "vbt.Portfolio",
    symbol: str = "",
) -> dict[str, Any]:
    """Compare native backtest_engine results with VectorBT re-simulation.

    Returns a dictionary with aligned metrics and any discrepancies.
    """
    native_trades = _native_trade_list(native_result)
    vbt_trades = _vectorbt_trade_list(pf)

    # ---- Core metrics ----
    n_native = int(len(native_trades))
    n_vbt = int(len(vbt_trades))

    native_net_pnl = float(native_trades["net_pnl"].sum()) if n_native else 0.0
    vbt_net_pnl = float(vbt_trades["net_pnl"].sum()) if n_vbt else 0.0

    native_equity = native_result.equity_curve["equity"] if not native_result.equity_curve.empty else pd.Series()
    vbt_equity = pf.value()

    native_max_dd = (
        (native_equity / native_equity.cummax() - 1).min() * 100
        if not native_equity.empty
        else None
    )
    vbt_max_dd = pf.drawdown().max() * 100 if hasattr(pf, "drawdown") else None

    # ---- Sharpe (annualised) ----
    try:
        native_sharpe = native_result.metrics.get("sharpe_ratio")
    except Exception:
        native_sharpe = None
    try:
        vbt_sharpe = pf.sharpe_ratio() if hasattr(pf, "sharpe_ratio") else None
    except Exception:
        vbt_sharpe = None

    return {
        "symbol": symbol,
        "native_trades": n_native,
        "vbt_trades": n_vbt,
        "native_net_pnl": round(native_net_pnl, 4),
        "vbt_net_pnl": round(vbt_net_pnl, 4),
        "pnl_delta_pct": round((vbt_net_pnl - native_net_pnl) / abs(native_net_pnl) * 100, 2) if native_net_pnl else None,
        "native_max_drawdown_pct": round(float(native_max_dd), 4) if native_max_dd is not None else None,
        "vbt_max_drawdown_pct": round(float(vbt_max_dd), 4) if vbt_max_dd is not None else None,
        "native_sharpe": native_sharpe,
        "vbt_sharpe": float(vbt_sharpe) if vbt_sharpe is not None else None,
        "trades_delta": n_vbt - n_native,
    }
