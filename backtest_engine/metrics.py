from __future__ import annotations

from dataclasses import dataclass

import math

import numpy as np
import pandas as pd


BASE_TIMEFRAME_MINUTES = 5
TRADING_DAYS_PER_YEAR = 252
US_REGULAR_SESSION_MINUTES = 390


@dataclass
class MetricsInput:
    symbol: str
    strategy: str
    initial_capital: float
    bars: pd.DataFrame
    state: pd.DataFrame
    trades: pd.DataFrame
    timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES


def build_equity_curve(state: pd.DataFrame, initial_capital: float) -> pd.DataFrame:
    realized = state.get("realized_net_pnl_on_fill", pd.Series(0.0, index=state.index)).fillna(0.0)
    open_pnl = state.get("estimated_net_if_closed_now", pd.Series(0.0, index=state.index)).fillna(0.0)
    equity = float(initial_capital) + realized.cumsum() + open_pnl
    curve = pd.DataFrame(index=state.index)
    curve["realized_net_pnl_cumulative"] = realized.cumsum()
    curve["open_net_pnl_estimate"] = open_pnl
    curve["equity"] = equity
    curve["peak_equity"] = curve["equity"].cummax()
    curve["drawdown"] = curve["equity"] - curve["peak_equity"]
    curve["drawdown_pct"] = curve["drawdown"] / curve["peak_equity"].replace(0, math.nan)
    return curve


def _safe_pct(value: float, denominator: float) -> float | None:
    if denominator == 0 or math.isnan(denominator):
        return None
    return value / denominator * 100.0


def _profit_factor(profit: float, loss: float) -> float | None:
    return (profit / abs(loss)) if loss else None


def _mean_numeric(frame: pd.DataFrame, column: str) -> float | None:
    if column not in frame or frame.empty:
        return None
    value = pd.to_numeric(frame[column], errors="coerce").mean()
    return float(value) if not math.isnan(value) else None


def _side_trade_metrics(trades: pd.DataFrame, side: str) -> dict:
    subset = trades[trades.get("side", pd.Series(dtype=str)).astype(str).str.lower() == side]
    if subset.empty:
        return {
            f"{side}_closed_trades": 0,
            f"{side}_net_pnl": 0.0,
            f"{side}_gross_profit": 0.0,
            f"{side}_gross_loss": 0.0,
            f"{side}_profit_factor": None,
            f"{side}_win_rate_pct": None,
        }

    pnl = pd.to_numeric(subset["net_pnl"], errors="coerce").fillna(0.0)
    wins = pnl[pnl > 0]
    losses = pnl[pnl < 0]
    gross_profit = float(wins.sum())
    gross_loss = float(losses.sum())
    return {
        f"{side}_closed_trades": int(len(subset)),
        f"{side}_net_pnl": float(pnl.sum()),
        f"{side}_gross_profit": gross_profit,
        f"{side}_gross_loss": gross_loss,
        f"{side}_profit_factor": _profit_factor(gross_profit, gross_loss),
        f"{side}_win_rate_pct": _safe_pct(float(len(wins)), float(len(subset))),
    }


def _trade_excursion_metrics(trades: pd.DataFrame, bars: pd.DataFrame) -> dict:
    if trades.empty or bars.empty or not {"high", "low"}.issubset(bars.columns):
        return {
            "max_trade_runup": None,
            "max_trade_runup_pct": None,
            "max_trade_drawdown": None,
            "max_trade_drawdown_pct": None,
            "average_trade_runup": None,
            "average_trade_drawdown": None,
        }

    required_columns = {"entry_index", "exit_index", "side", "qty", "entry_price"}
    if not required_columns.issubset(trades.columns):
        return {
            "max_trade_runup": None,
            "max_trade_runup_pct": None,
            "max_trade_drawdown": None,
            "max_trade_drawdown_pct": None,
            "average_trade_runup": None,
            "average_trade_drawdown": None,
        }

    bar_positions = pd.Series(np.arange(len(bars), dtype=np.int64), index=bars.index)
    trade_data = pd.DataFrame(
        {
            "entry_pos": trades["entry_index"].map(bar_positions),
            "exit_pos": trades["exit_index"].map(bar_positions),
            "side": trades["side"].astype(str).str.lower(),
            "qty": pd.to_numeric(trades["qty"], errors="coerce"),
            "entry_price": pd.to_numeric(trades["entry_price"], errors="coerce"),
        }
    )
    valid_mask = (
        trade_data["entry_pos"].notna()
        & trade_data["exit_pos"].notna()
        & trade_data["side"].isin(["long", "short"])
        & (trade_data["qty"] > 0)
        & trade_data["entry_price"].notna()
        & (trade_data["entry_price"] != 0)
    )
    trade_data = trade_data.loc[valid_mask].copy()
    if trade_data.empty:
        return {
            "max_trade_runup": None,
            "max_trade_runup_pct": None,
            "max_trade_drawdown": None,
            "max_trade_drawdown_pct": None,
            "average_trade_runup": None,
            "average_trade_drawdown": None,
        }

    entry_pos = trade_data["entry_pos"].to_numpy(dtype=np.int64)
    exit_pos = trade_data["exit_pos"].to_numpy(dtype=np.int64)
    ordered_mask = entry_pos <= exit_pos
    if not ordered_mask.all():
        trade_data = trade_data.iloc[ordered_mask].copy()
        entry_pos = entry_pos[ordered_mask]
        exit_pos = exit_pos[ordered_mask]
    if trade_data.empty:
        return {
            "max_trade_runup": None,
            "max_trade_runup_pct": None,
            "max_trade_drawdown": None,
            "max_trade_drawdown_pct": None,
            "average_trade_runup": None,
            "average_trade_drawdown": None,
        }

    high_values = pd.to_numeric(bars["high"], errors="coerce").to_numpy(dtype=float)
    low_values = pd.to_numeric(bars["low"], errors="coerce").to_numpy(dtype=float)

    def range_extrema(values: np.ndarray, starts: np.ndarray, ends: np.ndarray, *, maximize: bool) -> np.ndarray:
        fill_value = -math.inf if maximize else math.inf
        prepared = np.where(np.isnan(values), fill_value, values)
        levels = [prepared]
        span = 1
        while span * 2 <= len(prepared):
            previous = levels[-1]
            combine = np.maximum if maximize else np.minimum
            levels.append(combine(previous[:-span], previous[span:]))
            span *= 2

        lengths = ends - starts + 1
        powers = np.floor(np.log2(lengths)).astype(np.int64)
        result = np.empty(len(starts), dtype=float)
        combine = np.maximum if maximize else np.minimum
        for power in np.unique(powers):
            mask = powers == power
            window_span = 1 << int(power)
            left = levels[int(power)][starts[mask]]
            right = levels[int(power)][ends[mask] - window_span + 1]
            result[mask] = combine(left, right)

        valid_counts = np.cumsum(np.where(np.isnan(values), 0, 1))
        counts = valid_counts[ends] - np.where(starts > 0, valid_counts[starts - 1], 0)
        result[counts == 0] = math.nan
        return result

    max_high = range_extrema(high_values, entry_pos, exit_pos, maximize=True)
    min_low = range_extrema(low_values, entry_pos, exit_pos, maximize=False)

    side = trade_data["side"].to_numpy(dtype=str)
    qty = trade_data["qty"].to_numpy(dtype=float)
    entry_price = trade_data["entry_price"].to_numpy(dtype=float)
    long_mask = side == "long"

    runup_per_unit = np.where(long_mask, max_high - entry_price, entry_price - min_low)
    drawdown_per_unit = np.where(long_mask, min_low - entry_price, entry_price - max_high)
    runups = np.maximum(runup_per_unit * qty, 0.0)
    drawdowns = np.minimum(drawdown_per_unit * qty, 0.0)
    runup_pcts = runup_per_unit / entry_price * 100.0
    drawdown_pcts = drawdown_per_unit / entry_price * 100.0

    return {
        "max_trade_runup": float(np.max(runups)),
        "max_trade_runup_pct": float(np.max(runup_pcts)),
        "max_trade_drawdown": float(np.min(drawdowns)),
        "max_trade_drawdown_pct": float(np.min(drawdown_pcts)),
        "average_trade_runup": float(np.sum(runups) / len(runups)),
        "average_trade_drawdown": float(np.sum(drawdowns) / len(drawdowns)),
    }


def bars_per_year_for_timeframe(timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES) -> int:
    try:
        minutes = int(timeframe_minutes)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"timeframe_minutes must be an integer, got {timeframe_minutes!r}") from exc
    if minutes <= 0:
        raise ValueError(f"timeframe_minutes must be > 0, got {minutes}")
    bars_per_day = max(1, US_REGULAR_SESSION_MINUTES // minutes)
    return TRADING_DAYS_PER_YEAR * bars_per_day


def _max_drawdown_duration_bars(equity_curve: pd.DataFrame) -> int:
    if equity_curve.empty or "drawdown" not in equity_curve:
        return 0
    drawdown = equity_curve["drawdown"]
    is_drawdown = drawdown < 0
    if not is_drawdown.any():
        return 0
    groups = (is_drawdown != is_drawdown.shift()).cumsum()
    durations = is_drawdown.groupby(groups).sum()
    return int(durations.max())


def _risk_adjusted_metrics(equity_curve: pd.DataFrame, bars_per_year: int) -> dict:
    if equity_curve.empty or "equity" not in equity_curve:
        return {"sharpe_ratio": None, "sortino_ratio": None}
    returns = pd.to_numeric(equity_curve["equity"], errors="coerce").pct_change().replace([math.inf, -math.inf], math.nan).dropna()
    if len(returns) < 2:
        return {"sharpe_ratio": None, "sortino_ratio": None}
    mean_return = float(returns.mean())
    std_return = float(returns.std(ddof=1))
    downside = returns[returns < 0]
    downside_std = float(downside.std(ddof=1)) if len(downside) > 1 else math.nan
    annualization = math.sqrt(float(bars_per_year))
    return {
        "sharpe_ratio": (mean_return / std_return * annualization) if std_return and not math.isnan(std_return) else None,
        "sortino_ratio": (mean_return / downside_std * annualization) if downside_std and not math.isnan(downside_std) else None,
    }


def compute_metrics(payload: MetricsInput) -> tuple[dict, pd.DataFrame]:
    trades = payload.trades.copy()
    equity_curve = build_equity_curve(payload.state, payload.initial_capital)

    if trades.empty:
        net_pnl = gross_profit = gross_loss = 0.0
        winning = losing = breakeven = 0
        average_winning_trade = average_losing_trade = None
        average_bars_held = average_winning_bars_held = average_losing_bars_held = None
        commission_paid = 0.0
    else:
        trades["net_pnl"] = pd.to_numeric(trades["net_pnl"], errors="coerce").fillna(0.0)
        net_pnl = float(trades["net_pnl"].sum())
        wins = trades[trades["net_pnl"] > 0]
        losses = trades[trades["net_pnl"] < 0]
        flats = trades[trades["net_pnl"] == 0]
        gross_profit = float(wins["net_pnl"].sum())
        gross_loss = float(losses["net_pnl"].sum())
        winning, losing, breakeven = len(wins), len(losses), len(flats)
        average_winning_trade = float(wins["net_pnl"].mean()) if winning else None
        average_losing_trade = float(losses["net_pnl"].mean()) if losing else None
        average_bars_held = float(pd.to_numeric(trades.get("bars_held"), errors="coerce").mean()) if "bars_held" in trades else None
        average_winning_bars_held = _mean_numeric(wins, "bars_held")
        average_losing_bars_held = _mean_numeric(losses, "bars_held")
        commission_paid = float(pd.to_numeric(trades.get("estimated_costs", pd.Series(0.0, index=trades.index)), errors="coerce").fillna(0.0).sum())

    closed_trades = int(len(trades))
    max_drawdown = float(equity_curve["drawdown"].min()) if len(equity_curve) else 0.0
    max_drawdown_pct = float(equity_curve["drawdown_pct"].min() * 100.0) if len(equity_curve) else 0.0
    max_drawdown_period_bars = _max_drawdown_duration_bars(equity_curve)
    max_drawdown_period_days = 0.0
    if len(payload.bars) > 0 and len(equity_curve) > 0:
        elapsed_days = max((payload.bars.index[-1] - payload.bars.index[0]).total_seconds() / 86400.0, 0.0)
        max_drawdown_period_days = (max_drawdown_period_bars / len(equity_curve)) * elapsed_days

    final_equity = float(equity_curve["equity"].iloc[-1]) if len(equity_curve) else float(payload.initial_capital)
    open_pnl = float(equity_curve["open_net_pnl_estimate"].iloc[-1]) if len(equity_curve) else 0.0
    total_pnl = final_equity - float(payload.initial_capital)
    total_pnl_pct = _safe_pct(total_pnl, float(payload.initial_capital))
    exposure_bars = 0
    if "position_abs_size" in payload.state:
        exposure_bars = int((pd.to_numeric(payload.state["position_abs_size"], errors="coerce").fillna(0.0) > 0).sum())
    elif "position_size" in payload.state:
        exposure_bars = int((pd.to_numeric(payload.state["position_size"], errors="coerce").fillna(0.0).abs() > 0).sum())

    first_close = float(payload.bars["close"].iloc[0]) if len(payload.bars) else math.nan
    last_close = float(payload.bars["close"].iloc[-1]) if len(payload.bars) else math.nan
    buy_hold_return_pct = _safe_pct(last_close - first_close, first_close) if len(payload.bars) else None
    buy_hold_pnl = (payload.initial_capital * (buy_hold_return_pct / 100.0)) if buy_hold_return_pct is not None else None
    return_pct = _safe_pct(final_equity - payload.initial_capital, payload.initial_capital)
    strategy_outperformance = (total_pnl - buy_hold_pnl) if buy_hold_pnl is not None else None

    position_values = pd.Series(dtype=float)
    if {"position_abs_size", "position_avg_price"}.issubset(payload.state.columns):
        position_values = (
            pd.to_numeric(payload.state["position_abs_size"], errors="coerce").fillna(0.0)
            * pd.to_numeric(payload.state["position_avg_price"], errors="coerce").fillna(0.0)
        )
    max_position_value = float(position_values.max()) if len(position_values) else 0.0
    average_position_value = float(position_values[position_values > 0].mean()) if len(position_values[position_values > 0]) else 0.0
    required_account_size = float(payload.initial_capital) + abs(max_drawdown)
    cagr = None
    if len(payload.bars) > 1 and return_pct is not None:
        elapsed_days = max((payload.bars.index[-1] - payload.bars.index[0]).total_seconds() / 86400.0, 0.0)
        if elapsed_days > 0 and final_equity > 0 and payload.initial_capital > 0:
            cagr = ((final_equity / payload.initial_capital) ** (365.25 / elapsed_days) - 1.0) * 100.0

    side_metrics = {}
    if not trades.empty and "side" in trades:
        side_metrics.update(_side_trade_metrics(trades, "long"))
        side_metrics.update(_side_trade_metrics(trades, "short"))
    else:
        side_metrics.update(_side_trade_metrics(pd.DataFrame(columns=["side", "net_pnl"]), "long"))
        side_metrics.update(_side_trade_metrics(pd.DataFrame(columns=["side", "net_pnl"]), "short"))

    trade_excursions = _trade_excursion_metrics(trades, payload.bars)
    risk_adjusted = _risk_adjusted_metrics(equity_curve, bars_per_year_for_timeframe(payload.timeframe_minutes))

    metrics = {
        "symbol": payload.symbol,
        "strategy": payload.strategy,
        "initial_capital": payload.initial_capital,
        "final_equity": final_equity,
        "open_pnl": open_pnl,
        "total_pnl": total_pnl,
        "total_pnl_pct": total_pnl_pct,
        "total_net_pnl": net_pnl,
        "return_pct": return_pct,
        "closed_trades": closed_trades,
        "winning_trades": int(winning),
        "losing_trades": int(losing),
        "breakeven_trades": int(breakeven),
        "win_rate_pct": _safe_pct(float(winning), float(closed_trades)),
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "profit_factor": _profit_factor(gross_profit, gross_loss),
        "commission_paid": commission_paid,
        "average_trade": (net_pnl / closed_trades) if closed_trades else None,
        "average_winning_trade": average_winning_trade,
        "average_losing_trade": average_losing_trade,
        "average_win_loss_ratio": (average_winning_trade / abs(average_losing_trade)) if average_winning_trade is not None and average_losing_trade not in (None, 0) else None,
        "average_bars_held": average_bars_held,
        "average_winning_bars_held": average_winning_bars_held,
        "average_losing_bars_held": average_losing_bars_held,
        "best_trade": float(trades["net_pnl"].max()) if closed_trades else None,
        "worst_trade": float(trades["net_pnl"].min()) if closed_trades else None,
        "max_drawdown": max_drawdown,
        "max_drawdown_pct": max_drawdown_pct,
        "max_drawdown_period_bars": max_drawdown_period_bars,
        "max_drawdown_period_days": max_drawdown_period_days,
        "buy_hold_pnl": buy_hold_pnl,
        "buy_hold_return_pct": buy_hold_return_pct,
        "return_vs_buy_hold_pct_points": (return_pct - buy_hold_return_pct) if return_pct is not None and buy_hold_return_pct is not None else None,
        "strategy_outperformance_pnl": strategy_outperformance,
        "cagr_pct": cagr,
        "required_account_size": required_account_size,
        "return_on_required_account_pct": _safe_pct(total_pnl, required_account_size),
        "net_profit_to_max_drawdown_pct": _safe_pct(net_pnl, abs(max_drawdown)) if max_drawdown else None,
        "max_position_value": max_position_value,
        "average_position_value": average_position_value,
        "capital_efficiency_pct": _safe_pct(net_pnl, max_position_value) if max_position_value else None,
        "exposure_bars": exposure_bars,
        "exposure_pct": _safe_pct(float(exposure_bars), float(len(payload.state))) if len(payload.state) else None,
        "bars": int(len(payload.bars)),
        "start": str(payload.bars.index[0]) if len(payload.bars) else None,
        "end": str(payload.bars.index[-1]) if len(payload.bars) else None,
    }
    metrics.update(side_metrics)
    metrics.update(trade_excursions)
    metrics.update(risk_adjusted)
    return metrics, equity_curve


def compute_fast_score(trades: pd.DataFrame, score_metric: str, *, state: pd.DataFrame | None = None, initial_capital: float = 1000.0, timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES, bars: pd.DataFrame | None = None) -> float | None:
    """Compute a single score metric as cheaply as possible.

    For trade-based metrics (total_net_pnl, win_rate_pct, etc.) only
    *trades* is required.  For risk-adjusted metrics (sharpe_ratio,
    sortino_ratio) the *state* DataFrame must be supplied so that an
    equity curve can be built without the full ``compute_metrics``
    overhead.
    """
    # ---- risk-adjusted fast path (B8) ----
    if score_metric in ("sharpe_ratio", "sortino_ratio"):
        if state is None or state.empty:
            return None
        realized = state.get("realized_net_pnl_on_fill", pd.Series(0.0, index=state.index)).fillna(0.0)
        open_pnl = state.get("estimated_net_if_closed_now", pd.Series(0.0, index=state.index)).fillna(0.0)
        equity = float(initial_capital) + realized.cumsum() + open_pnl
        returns = equity.pct_change().replace([math.inf, -math.inf], math.nan).dropna()
        if len(returns) < 2:
            return None
        mean_ret = float(returns.mean())
        bars_yr = bars_per_year_for_timeframe(timeframe_minutes)
        ann = math.sqrt(float(bars_yr))
        if score_metric == "sharpe_ratio":
            std_ret = float(returns.std(ddof=1))
            return (mean_ret / std_ret * ann) if std_ret and not math.isnan(std_ret) else None
        else:  # sortino_ratio
            downside = returns[returns < 0]
            ds_std = float(downside.std(ddof=1)) if len(downside) > 1 else math.nan
            return (mean_ret / ds_std * ann) if ds_std and not math.isnan(ds_std) else None

    # ---- return vs buy & hold fast path ----
    if score_metric == "return_vs_buy_hold_pct_points":
        if state is None or state.empty or bars is None or bars.empty:
            return None
        realized = state.get("realized_net_pnl_on_fill", pd.Series(0.0, index=state.index)).fillna(0.0)
        open_pnl = state.get("estimated_net_if_closed_now", pd.Series(0.0, index=state.index)).fillna(0.0)
        final_equity = float(initial_capital) + float(realized.sum()) + float(open_pnl.iloc[-1])
        return_pct = float((final_equity / initial_capital - 1.0) * 100.0) if initial_capital > 0 else 0.0
        
        initial_price = float(bars["close"].iloc[0])
        final_price = float(bars["close"].iloc[-1])
        buy_hold_return_pct = float(((final_price / initial_price) - 1.0) * 100.0) if initial_price and final_price else 0.0
        
        return return_pct - buy_hold_return_pct

    if trades.empty:
        return 0.0 if score_metric in ("total_net_pnl", "total_pnl", "gross_profit", "gross_loss") else None

    if score_metric not in ("total_net_pnl", "total_pnl", "win_rate_pct", "profit_factor", "gross_profit", "gross_loss", "average_trade", "closed_trades"):
        return None

    if score_metric == "closed_trades":
        return float(len(trades))

    pnl = pd.to_numeric(trades["net_pnl"], errors="coerce").fillna(0.0)

    if score_metric in ("total_net_pnl", "total_pnl"):
        return float(pnl.sum())
    elif score_metric == "win_rate_pct":
        wins = (pnl > 0).sum()
        return float(wins) / len(trades) * 100.0 if len(trades) > 0 else None
    elif score_metric == "profit_factor":
        gross_profit = float(pnl[pnl > 0].sum())
        gross_loss = float(pnl[pnl < 0].sum())
        return (gross_profit / abs(gross_loss)) if gross_loss else None
    elif score_metric == "gross_profit":
        return float(pnl[pnl > 0].sum())
    elif score_metric == "gross_loss":
        return float(pnl[pnl < 0].sum())
    elif score_metric == "average_trade":
        return float(pnl.mean())
        
    return None
