from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Callable, Literal
import pandas as pd
import numpy as np

from ..metrics import MetricsInput, compute_metrics
from ..reports import BacktestRunResult
from ..configuration import coerce_strategy_parameters, load_strategy_config
from ..broker import BrokerSimulator, BrokerConfig, Order, ExitOrchestrator, TimeExitRule, VWAPExitRule, LadderExitRule


@dataclass
class NoiseBoundaryConfigOverrides:
    lookback_days: int | None = None
    volatility_multiplier_enter: float | None = None
    volatility_multiplier_exit: float | None = None
    target_daily_volatility: float | None = None
    exit_mode: str | None = None
    stoploss_ladder_step0: float | None = None
    stoploss_ladder_step1: float | None = None
    stoploss_ladder_ratio0: float | None = None
    takeprofit_ladder_step0: float | None = None
    takeprofit_ladder_step1: float | None = None
    entry_on_high_low: bool | None = None
    use_sequential_ladder: bool | None = None
    start_trade_after_open_minutes: int | None = None
    trade_frequency_minutes: int | None = None
    trade_frequency_bars: int | None = None
    allow_overnight: bool | None = None
    use_vwap_filter: bool | None = None
    exit_trades_before_close_minutes: int | None = None
    max_entry_price: float | None = None
    max_capital_bucket: float | None = None
    initial_capital_bucket: float | None = None
    trade_direction_mode: str | None = None
    fee_mode: str | None = None
    estimated_commission_per_order_long: float | None = None
    estimated_commission_per_order_short: float | None = None
    estimated_slippage_per_side_long: float | None = None
    estimated_slippage_per_side_short: float | None = None
    min_net_profit_after_costs: float | None = None
    use_net_bracket_exits: bool | None = None
    take_profit_net_percent: float | None = None
    stop_loss_net_percent: float | None = None
    use_safety_stop: bool | None = None
    safety_stop_applies_to: str | None = None
    safety_stop_mode: str | None = None
    safety_max_net_loss_mode: str | None = None
    safety_max_net_loss_cash: float | None = None
    safety_max_net_loss_percent: float | None = None
    safety_max_bars_in_trade: int | None = None
    point_value: float | None = None
    execute_on_next_bar: bool | None = None
    next_bar_execution_price_col: str | None = None
    apply_estimated_costs_to_realized_pnl: bool | None = None
    allow_fractional_quantity: bool | None = True
    quantity_precision: int | None = 6
    early_stop_drawdown_pct: float | None = None
    asset_currency: str | None = None
    account_currency: str | None = None
    fx_rate_provider: object | None = None
    max_leverage: float | None = None
    sizing_volatility_type: Literal["daily", "intraday"] | None = None
    entry_timing_mode: Literal["evaluate_at_period_start", "evaluate_at_period_end"] | None = None
    commission_min_long: float | None = None
    commission_min_short: float | None = None
    dividends_series: pd.Series | None = None


def noise_boundary_overrides_from_mapping(values: dict[str, object] | None, *, ignore_unknown: bool = True) -> NoiseBoundaryConfigOverrides:
    if not values:
        return NoiseBoundaryConfigOverrides()
    coerced = coerce_strategy_parameters("noise_boundary_intraday", values, ignore_unknown=ignore_unknown)
    allowed = set(NoiseBoundaryConfigOverrides.__dataclass_fields__.keys())
    return NoiseBoundaryConfigOverrides(**{key: value for key, value in coerced.items() if key in allowed})


def load_noise_boundary_overrides_from_config(path: str | Path) -> tuple[NoiseBoundaryConfigOverrides, dict[str, object]]:
    runtime_config = load_strategy_config(path, strategy="noise_boundary_intraday")
    return noise_boundary_overrides_from_mapping(runtime_config.parameters), runtime_config.backtest


def compute_vwap_intraday(bars: pd.DataFrame) -> pd.Series:
    """
    Compute intraday VWAP for each daily session.
    Formula: cum(typical * volume) / cum(volume)
    """
    if bars.empty or "volume" not in bars.columns:
        return pd.Series(index=bars.index, dtype=float)
        
    typical_price = (bars["high"] + bars["low"] + bars["close"]) / 3
    pv = typical_price * bars["volume"]
    
    normalized_index = bars.index.normalize()
    cum_pv = pv.groupby(normalized_index).cumsum()
    cum_vol = bars.groupby(normalized_index)["volume"].cumsum()
    
    return cum_pv / cum_vol


# Shared indicator references (populated by backtest_engine multiprocessing workers)
_SHARED_NB_VOL_GRID: np.ndarray | None = None
_SHARED_NB_VOL_KEYS: dict[int, int] | None = None

_TIME_CACHE = {}

def _get_time_features(data: pd.DataFrame) -> dict:
    key = (id(data), len(data), data.index[0] if len(data) > 0 else 0)
    if key in _TIME_CACHE:
        return _TIME_CACHE[key]
    
    normalized_index = data.index.normalize()
    ts_series = pd.Series(data.index, index=data.index)
    sod_series = ts_series.groupby(normalized_index).transform("first")
    eod_series = ts_series.groupby(normalized_index).transform("last")
    
    minutes_since_open_arr = ((data.index - sod_series).dt.total_seconds() / 60.0).values
    bars_since_open_arr = data.groupby(normalized_index).cumcount().values
    minutes_until_close_arr = ((eod_series - data.index).dt.total_seconds() / 60.0).values
    
    vwap_series = compute_vwap_intraday(data)
    vwap_values = vwap_series.values
    
    res = {
        "minutes_since_open_arr": minutes_since_open_arr,
        "bars_since_open_arr": bars_since_open_arr,
        "minutes_until_close_arr": minutes_until_close_arr,
        "vwap_series": vwap_series,
        "vwap_values": vwap_values,
    }
    _TIME_CACHE.clear()  # Keep only the latest data chunk to save memory
    _TIME_CACHE[key] = res
    return res

_NB_VOL_CACHE: dict = {}

def compute_noise_boundary(
    bars: pd.DataFrame, 
    lookback_days: int, 
    multiplier_enter: float, 
    multiplier_exit: float,
    dividends_series: pd.Series | None = None
) -> pd.DataFrame:
    """
    Compute noise boundary bands based on intraday volatility curve (sigma_open)
    and anchored to daily open and previous day's close.
    
    Formula:
    UB = max(Open, prev_close) * (1 + Multiplier * sigma_open)
    LB = min(Open, prev_close) * (1 - Multiplier * sigma_open)
    
    sigma_open at time t is the simple rolling average over lookback_days of
    abs(close_t / Open_jour - 1) at the same time t of previous days, shifted by 1 day.
    """
    if bars.empty:
        return pd.DataFrame(index=bars.index)

    # 1. Identify Daily Open
    normalized_index = bars.index.normalize()
    daily_open = bars.groupby(normalized_index)["open"].transform("first")
    
    global _SHARED_NB_VOL_GRID, _SHARED_NB_VOL_KEYS
    lookback_key = int(lookback_days)
    
    # Try SHM cache
    if _SHARED_NB_VOL_GRID is not None and _SHARED_NB_VOL_KEYS is not None and lookback_key in _SHARED_NB_VOL_KEYS:
        idx = _SHARED_NB_VOL_KEYS[lookback_key]
        mapped_vol = _SHARED_NB_VOL_GRID[idx, 0]
    else:
        # Try local cache
        cache_key = (id(bars), lookback_key)
        if cache_key in _NB_VOL_CACHE:
            mapped_vol = _NB_VOL_CACHE[cache_key]
        else:
            # 2. Compute move_open for each intraday bar
            move_open = (bars["close"] / daily_open - 1).abs()
            
            # 3. Pivot move_open to align by date and time of day
            pivoted_df = pd.DataFrame({"move_open": move_open}, index=bars.index)
            pivoted_df["date"] = normalized_index
            pivoted_df["time"] = bars.index.time
            
            # Pivot to have Date as Index and Time as Columns
            pivoted_matrix = pivoted_df.pivot(index="date", columns="time", values="move_open")
            
            # Compute rolling mean over lookback_days along the date axis
            # Shift by 1 day to avoid look-ahead bias
            rolling_matrix = pivoted_matrix.rolling(window=lookback_days, min_periods=lookback_days - 1).mean().shift(1)
            
            # Map back to intraday bars index using MultiIndex
            stacked = rolling_matrix.stack(dropna=False)
            multi_index = pd.MultiIndex.from_arrays([normalized_index, bars.index.time], names=["date", "time"])
            mapped_vol = stacked.reindex(multi_index).values
            
            _NB_VOL_CACHE[cache_key] = mapped_vol

    # 4. Get Previous Day's Close (Overnight Gap Anchor)
    daily_close_series = bars["close"].resample("D").last().dropna()
    prev_day_close_series = daily_close_series.shift(1)
    
    # Adjust for dividends if present
    if dividends_series is not None and not dividends_series.empty:
        divs_norm = dividends_series.copy()
        divs_norm.index = pd.to_datetime(divs_norm.index).normalize()
        prev_day_div = divs_norm.reindex(daily_close_series.index).shift(1).fillna(0)
        prev_day_close_series = prev_day_close_series - prev_day_div

    prev_day_close = prev_day_close_series.reindex(normalized_index).values
    
    # Handle first day where prev_close is NaN by falling back to daily_open
    prev_close_filled = np.where(np.isnan(prev_day_close), daily_open, prev_day_close)
    
    anchor_up = np.maximum(daily_open, prev_close_filled)
    anchor_down = np.minimum(daily_open, prev_close_filled)

    # 5. Compute Bands
    results = pd.DataFrame(index=bars.index)
    results["daily_volatility"] = mapped_vol
    results["daily_open"] = daily_open
    results["prev_day_close"] = prev_day_close
    
    results["upper_enter"] = anchor_up * (1 + multiplier_enter * mapped_vol)
    results["lower_enter"] = anchor_down * (1 - multiplier_enter * mapped_vol)
    results["upper_exit"] = anchor_up * (1 + multiplier_exit * mapped_vol)
    results["lower_exit"] = anchor_down * (1 - multiplier_exit * mapped_vol)
    
    return results


def run_noise_boundary_intraday(
    data: pd.DataFrame,
    symbol: str,
    overrides: NoiseBoundaryConfigOverrides | None = None,
    initial_capital: float = 1000.0,
    timeframe_minutes: int | str = 5,
    compute_full_metrics: bool = True,
    fast_score_metric: str | None = None,
    early_stop_drawdown_pct: float | None = None,
    repo_root: Path | None = None,
    dividends_series: pd.Series | None = None,
) -> BacktestRunResult:
    """
    Run the Noise Boundary Intraday strategy POC.
    """
    overrides = overrides or NoiseBoundaryConfigOverrides()
    drawdown_limit = overrides.early_stop_drawdown_pct if overrides.early_stop_drawdown_pct is not None else early_stop_drawdown_pct
    
    # 1. Indicator Calculation
    lookback = overrides.lookback_days if overrides.lookback_days is not None else 20
    m_enter = overrides.volatility_multiplier_enter if overrides.volatility_multiplier_enter is not None else 2.0
    m_exit = overrides.volatility_multiplier_exit if overrides.volatility_multiplier_exit is not None else 1.0
    
    div_series = dividends_series
    if div_series is None:
        div_series = overrides.dividends_series

    bands = compute_noise_boundary(data, lookback, m_enter, m_exit, dividends_series=div_series)
    
    # 2. Simulation Setup
    fx_rate_provider = overrides.fx_rate_provider
    asset_currency = overrides.asset_currency
    account_currency = overrides.account_currency
    if repo_root is not None and fx_rate_provider is None:
        from ..data import build_fx_rate_provider
        from ..canonical import load_symbol_currency_map
        fx_rate_provider = build_fx_rate_provider(
            repo_root, symbol, account_currency="EUR", timeframe_minutes=timeframe_minutes
        )
        if fx_rate_provider is not None and asset_currency is None:
            currency_map = load_symbol_currency_map(repo_root, timeframe_minutes)
            asset_currency = currency_map.get(symbol, "EUR").upper()
    broker_config = BrokerConfig(
        initial_capital=initial_capital,
        execute_on_next_bar=overrides.execute_on_next_bar if overrides.execute_on_next_bar is not None else True,
        execution_price_col=overrides.next_bar_execution_price_col if overrides.next_bar_execution_price_col is not None else "open",
        commission_fixed_long=overrides.estimated_commission_per_order_long,
        commission_fixed_short=overrides.estimated_commission_per_order_short,
        commission_min_long=overrides.commission_min_long,
        commission_min_short=overrides.commission_min_short,
        slippage_per_side_long=overrides.estimated_slippage_per_side_long if overrides.estimated_slippage_per_side_long is not None else 0.0,
        slippage_per_side_short=overrides.estimated_slippage_per_side_short if overrides.estimated_slippage_per_side_short is not None else 0.0,
        point_value=overrides.point_value if overrides.point_value is not None else 1.0,
        allow_fractional_quantity=overrides.allow_fractional_quantity if overrides.allow_fractional_quantity is not None else True,
        quantity_precision=overrides.quantity_precision,
        sizing_mode="target_volatility" if overrides.target_daily_volatility else "percent_of_equity",
        target_daily_volatility=overrides.target_daily_volatility if overrides.target_daily_volatility is not None else 0.01,
        volatility_lookback_days=lookback,
        account_currency=account_currency if account_currency is not None else "EUR",
        asset_currency=asset_currency if asset_currency is not None else "EUR",
        fx_rate_provider=fx_rate_provider,
        max_leverage=overrides.max_leverage if overrides.max_leverage is not None else 3.0,
    )
    broker = BrokerSimulator(broker_config)
    
    # 3. Strategy Parameters & Exits
    start_min = overrides.start_trade_after_open_minutes if overrides.start_trade_after_open_minutes is not None else 15
    exit_before_min = overrides.exit_trades_before_close_minutes if overrides.exit_trades_before_close_minutes is not None else 15
    direction = overrides.trade_direction_mode or "Long & Short"
    exit_mode = overrides.exit_mode or "time_only"
    allow_overnight = overrides.allow_overnight if overrides.allow_overnight is not None else False
    use_vwap_filter = overrides.use_vwap_filter if overrides.use_vwap_filter is not None else True
    
    # Get cached time features (VWAP, minutes_since_open, etc.)
    time_features = _get_time_features(data)
    vwap_values = time_features["vwap_values"]
    minutes_since_open_arr = time_features["minutes_since_open_arr"]
    bars_since_open_arr = time_features["bars_since_open_arr"]
    minutes_until_close_arr = time_features["minutes_until_close_arr"]
    
    from .noise_boundary_kernel import run_noise_boundary_kernel
    
    # Parse Numba config
    direction_mode = 1 if direction == "Long & Short" else (2 if direction == "Long only" else 3)
    exit_mode_vwap = exit_mode in ("vwap", "combined") or "vwap" in exit_mode
    exit_mode_boundary = exit_mode in ("boundary", "boundary_exit", "different_exit", "combined") or "boundary" in exit_mode
    exit_mode_ladder = exit_mode in ("ladder", "combined") or "ladder" in exit_mode
    
    seq_ladder = overrides.use_sequential_ladder if overrides.use_sequential_ladder is not None else True
    stoploss_step0 = overrides.stoploss_ladder_step0 if overrides.stoploss_ladder_step0 is not None else -0.008
    takeprofit_ratio0 = overrides.stoploss_ladder_ratio0 if overrides.stoploss_ladder_ratio0 is not None else 0.5
    stoploss_step1 = overrides.stoploss_ladder_step1 if overrides.stoploss_ladder_step1 is not None else -0.015
    takeprofit_step0 = overrides.takeprofit_ladder_step0 if overrides.takeprofit_ladder_step0 is not None else 0.012
    takeprofit_step1 = overrides.takeprofit_ladder_step1 if overrides.takeprofit_ladder_step1 is not None else np.nan
    
    drawdown_limit = overrides.early_stop_drawdown_pct if overrides.early_stop_drawdown_pct is not None else np.nan
    
    # Sizing config
    sizing_mode_str = broker_config.sizing_mode
    sizing_mode_int = 0 if sizing_mode_str == "fixed" else (1 if sizing_mode_str == "percent_of_equity" else 2)
    target_daily_volatility = broker_config.target_daily_volatility
    max_leverage = broker_config.max_leverage
    point_value = broker_config.point_value
    quantity_precision = broker_config.quantity_precision if broker_config.quantity_precision is not None else -1
    allow_fractional_quantity = broker_config.allow_fractional_quantity
    
    # Commission config
    commission_fixed = broker_config.commission_fixed
    commission_rate = broker_config.commission_rate
    comm_fixed_long = broker_config.commission_fixed_long if broker_config.commission_fixed_long is not None else -1.0
    slippage_long = broker_config.slippage_per_side_long
    comm_min_long = broker_config.commission_min_long if broker_config.commission_min_long is not None else -1.0
    comm_fixed_short = broker_config.commission_fixed_short if broker_config.commission_fixed_short is not None else -1.0
    slippage_short = broker_config.slippage_per_side_short
    comm_min_short = broker_config.commission_min_short if broker_config.commission_min_short is not None else -1.0
    
    # (Exit rules logic handled by kernel)
    
    _DVOL_CACHE: dict = getattr(run_noise_boundary_intraday, "_DVOL_CACHE", {})
    if not hasattr(run_noise_boundary_intraday, "_DVOL_CACHE"):
        run_noise_boundary_intraday._DVOL_CACHE = _DVOL_CACHE

    # Sizing Volatility
    if overrides.sizing_volatility_type == "daily":
        global _SHARED_NB_VOL_GRID, _SHARED_NB_VOL_KEYS
        lookback_key = int(lookback)
        if _SHARED_NB_VOL_GRID is not None and _SHARED_NB_VOL_KEYS is not None and lookback_key in _SHARED_NB_VOL_KEYS:
            idx = _SHARED_NB_VOL_KEYS[lookback_key]
            spy_dvol = _SHARED_NB_VOL_GRID[idx, 1]
        else:
            cache_key = (id(data), lookback_key)
            if cache_key in _DVOL_CACHE:
                spy_dvol = _DVOL_CACHE[cache_key]
            else:
                daily_close = data["close"].resample("D").last().dropna()
                daily_returns = daily_close.pct_change()
                daily_dvol_series = daily_returns.rolling(window=lookback, min_periods=lookback - 1).std().shift(1)
                normalized_index = data.index.normalize()
                spy_dvol = daily_dvol_series.reindex(normalized_index).values
                _DVOL_CACHE[cache_key] = spy_dvol
    else:
        spy_dvol = None

    # State tracking
    state_list = []
    
    # Pre-extract NumPy arrays for direct indexing (avoids to_dict("records") overhead)
    timestamps = data.index
    _open_arr = data["open"].values
    _high_arr = data["high"].values
    _low_arr = data["low"].values
    _close_arr = data["close"].values
    _volume_arr = data["volume"].values if "volume" in data.columns else np.zeros(len(data))
    _exec_col = broker.config.execution_price_col
    _exec_arr = data[_exec_col].values if _exec_col in data.columns else _open_arr
    
    _band_upper_enter = bands["upper_enter"].values
    _band_lower_enter = bands["lower_enter"].values
    _band_upper_exit = bands["upper_exit"].values
    _band_lower_exit = bands["lower_exit"].values
    _band_daily_vol = bands["daily_volatility"].values
    
    # Fallback missing arrays
    if spy_dvol is None:
        spy_dvol = np.full(len(data), _band_daily_vol[0] if len(_band_daily_vol) > 0 else 0.0)
    
    vol_for_sizing_arr = spy_dvol if overrides.sizing_volatility_type == "daily" else _band_daily_vol
    
    trade_freq_bars = float(overrides.trade_frequency_bars if overrides.trade_frequency_bars is not None else -1)
    trade_freq_min = float(overrides.trade_frequency_minutes if overrides.trade_frequency_minutes is not None else -1)
    timing_mode_end = bool((overrides.entry_timing_mode or "evaluate_at_period_start") == "evaluate_at_period_end")
    entry_on_high_low = bool(overrides.entry_on_high_low if overrides.entry_on_high_low is not None else False)
    
    # 4. Core Numba Kernel Execution
    trades_arr, state_arr = run_noise_boundary_kernel(
        # Arrays
        _open_arr, _high_arr, _low_arr, _close_arr, _exec_arr,
        _band_upper_enter, _band_lower_enter, vol_for_sizing_arr,
        _band_upper_exit, _band_lower_exit,
        minutes_since_open_arr, minutes_until_close_arr, bars_since_open_arr, vwap_values,
        # Scalars (Rules & Entry)
        initial_capital,
        allow_overnight, float(exit_before_min), float(start_min),
        direction_mode,
        trade_freq_bars, trade_freq_min, timing_mode_end,
        use_vwap_filter, entry_on_high_low,
        # Scalars (Exits)
        exit_mode_vwap, exit_mode_boundary, exit_mode_ladder,
        seq_ladder, stoploss_step0, stoploss_step1, takeprofit_step0, takeprofit_step1, takeprofit_ratio0,
        # Scalars (Sizing & Account)
        sizing_mode_int, float(target_daily_volatility), float(max_leverage), float(point_value), 1.0, # fx_rate passed as 1.0 for simplicity unless we map a full series
        quantity_precision, allow_fractional_quantity, drawdown_limit,
        # Scalars (Commissions)
        commission_fixed, commission_rate, 
        comm_fixed_long, slippage_long, comm_min_long,
        comm_fixed_short, slippage_short, comm_min_short
    )
    
    # 5. Reconstruct outputs for metric generator
    from ..broker import ClosedTrade
    for i in range(len(trades_arr)):
        t = trades_arr[i]
        
        # map exit type back to string
        comment = ""
        type_id = t["exit_type"]
        if type_id == 1: comment = "Time threshold reached"
        elif type_id == 2: comment = "VWAP Cross Up"
        elif type_id == 3: comment = "VWAP Cross Down"
        elif type_id == 4: comment = "Lower Boundary crossed (SL)"
        elif type_id == 5: comment = "Upper Boundary crossed (SL)"
        elif type_id == 6: comment = "Ladder SL Step 0"
        elif type_id == 7: comment = "Ladder TP Step 0"
        elif type_id == 8: comment = "Ladder SL Step 1"
        elif type_id == 9: comment = "Ladder TP Step 1"
        elif type_id == 10: comment = f"Early Stop Drawdown Capped at limit"
        
        entry_ts = timestamps[t["entry_bar"]]
        exit_ts = timestamps[t["exit_bar"]]
        side_str = "long" if t["side"] == 1 else "short"
        
        trade = ClosedTrade(
            entry_time=entry_ts,
            exit_time=exit_ts,
            side=side_str,
            quantity=t["quantity"],
            entry_price=t["entry_price"],
            exit_price=t["exit_price"],
            gross_pnl=t["gross_pnl"],
            commission=t["commission"],
            net_pnl=t["net_pnl"],
            entry_order_id=f"entry_{side_str}_{entry_ts}",
            exit_order_id=f"exit_{side_str}_{exit_ts}",
            exit_comment=comment,
            is_partial_exit=t["is_partial"]
        )
        broker.closed_trades.append(trade)

    state_list = state_arr.tolist()  # Can convert to DataFrame directly
    state_df = pd.DataFrame(state_arr, index=timestamps)
    # The dataframe uses specific column names that metrics.py relies on
    state_df.index.name = "timestamp"
    
    trades_df = broker.closed_trades_frame()    
    # Calculate bars_held for each trade
    if not trades_df.empty:
        # Map entry_time and exit_time to indices
        bar_indices = pd.Series(range(len(data)), index=data.index)
        trades_df["entry_bar_idx"] = trades_df["entry_time"].map(bar_indices)
        trades_df["exit_bar_idx"] = trades_df["exit_time"].map(bar_indices)
        trades_df["bars_held"] = trades_df["exit_bar_idx"] - trades_df["entry_bar_idx"]
    
    # 5. Metrics & Results
    if compute_full_metrics:
        metrics, equity_curve = compute_metrics(
            MetricsInput(
                symbol=symbol,
                strategy="noise_boundary_intraday",
                initial_capital=initial_capital,
                bars=data,
                state=state_df,
                trades=trades_df,
                timeframe_minutes=timeframe_minutes,
            )
        )
    else:
        from ..metrics import compute_fast_score
        metrics = {"closed_trades": len(trades_df)}
        if fast_score_metric:
            score = compute_fast_score(
                trades_df, 
                fast_score_metric, 
                state=state_df, 
                initial_capital=initial_capital, 
                timeframe_minutes=timeframe_minutes,
                bars=data,
            )
            if score is not None:
                metrics[fast_score_metric] = score
        equity_curve = pd.DataFrame()

    return BacktestRunResult(
        strategy="noise_boundary_intraday",
        symbol=symbol,
        config=asdict(overrides),
        bars=data,
        state=state_df,
        trades=trades_df,
        equity_curve=equity_curve,
        metrics=metrics,
    )


def _write_prescan_report(
    output_dir: Path | None,
    status: str,
    top_n: int | None,
    parameters: dict[str, dict[str, Any]],
) -> None:
    if output_dir is None:
        return
    report = {
        "status": status,
        "top_n_configurations_found": top_n,
        "parameters": parameters,
    }
    try:
        path = output_dir / "vectorbt_prescan_report.json"
        path.write_text(json.dumps(report, indent=4, default=str), encoding="utf-8")
    except Exception:
        pass


# Globals for multiprocessing workers to reference mapped memory directly
_worker_close = None
_worker_anchor_up = None
_worker_anchor_down = None
_worker_mapped_vol_by_lookback = None
_worker_timeframe_minutes = None

def _init_prescan_worker(close, anchor_up, anchor_down, mapped_vol, timeframe_mins):
    global _worker_close, _worker_anchor_up, _worker_anchor_down, _worker_mapped_vol_by_lookback, _worker_timeframe_minutes
    _worker_close = close
    _worker_anchor_up = anchor_up
    _worker_anchor_down = anchor_down
    _worker_mapped_vol_by_lookback = mapped_vol
    _worker_timeframe_minutes = timeframe_mins

def _process_prescan_batch(batch_combos):
    global _worker_close, _worker_anchor_up, _worker_anchor_down, _worker_mapped_vol_by_lookback, _worker_timeframe_minutes
    import pandas as pd
    import numpy as np
    import vectorbt as vbt

    batch_long_entries = {}
    batch_short_entries = {}
    batch_long_exits = {}
    batch_short_exits = {}

    for lookback, mult_enter, mult_exit in batch_combos:
        mapped_vol = _worker_mapped_vol_by_lookback[lookback]
        upper_enter = _worker_anchor_up * (1 + mult_enter * mapped_vol)
        lower_enter = _worker_anchor_down * (1 - mult_enter * mapped_vol)
        upper_exit = _worker_anchor_up * (1 + mult_exit * mapped_vol)
        lower_exit = _worker_anchor_down * (1 - mult_exit * mapped_vol)

        long_entries = _worker_close > upper_enter
        short_entries = _worker_close < lower_enter
        long_exits = _worker_close < lower_exit
        short_exits = _worker_close > upper_exit

        col = (lookback, mult_enter, mult_exit)
        batch_long_entries[col] = long_entries
        batch_short_entries[col] = short_entries
        batch_long_exits[col] = long_exits
        batch_short_exits[col] = short_exits

    columns = pd.MultiIndex.from_tuples(batch_combos, names=["lookback_days", "volatility_multiplier_enter", "volatility_multiplier_exit"])
    long_entries_df = pd.DataFrame(batch_long_entries, index=_worker_close.index, columns=columns)
    short_entries_df = pd.DataFrame(batch_short_entries, index=_worker_close.index, columns=columns)
    long_exits_df = pd.DataFrame(batch_long_exits, index=_worker_close.index, columns=columns)
    short_exits_df = pd.DataFrame(batch_short_exits, index=_worker_close.index, columns=columns)

    pf = vbt.Portfolio.from_signals(
        _worker_close,
        entries=long_entries_df,
        exits=long_exits_df,
        short_entries=short_entries_df,
        short_exits=short_exits_df,
        freq=f"{_worker_timeframe_minutes}min",
    )
    return pf.total_return()


def vectorbt_prescan(
    data: pd.DataFrame,
    parameter_specs: list[Any],
    timeframe_minutes: int | str,
    output_dir: Path | None = None,
    stop_requested: Callable[[], bool] | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
    workers: int = 1,
) -> list[Any]:
    """Préalablement à l'optimisation bayésienne, scanne rapidement les paramètres 
    de bandes (lookback_days, volatility_multiplier_enter, volatility_multiplier_exit) 
    avec VectorBT pour restreindre les bornes d'exploration.
    """
    import logging
    import numpy as np
    from ..optimizer import ParameterGridSpec

    logger = logging.getLogger(__name__)

    if stop_requested is not None and stop_requested():
        logger.warning("Pre-scan Noise Boundary annulé avant démarrage.")
        _write_prescan_report(output_dir, "cancelled", None, {})
        return parameter_specs

    lookback_specs = next((s for s in parameter_specs if s.name == "lookback_days"), None)
    mult_enter_specs = next((s for s in parameter_specs if s.name == "volatility_multiplier_enter"), None)
    mult_exit_specs = next((s for s in parameter_specs if s.name == "volatility_multiplier_exit"), None)

    if not all([lookback_specs, mult_enter_specs, mult_exit_specs]):
        _write_prescan_report(output_dir, "skipped", None, {})
        return parameter_specs
    if not all([s.values for s in [lookback_specs, mult_enter_specs, mult_exit_specs]]):
        _write_prescan_report(output_dir, "skipped", None, {})
        return parameter_specs

    try:
        import vectorbt as vbt
        import gc

        # 1. Temporal Downsampling (Piste C)
        prescan_timeframe = timeframe_minutes
        if int(timeframe_minutes) == 1:
            logger.info("Downsampling 1min bars to 5min bars for fast pre-scan processing.")
            conversion = {
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }
            # Keep any other columns intact (e.g. symbol)
            for col in data.columns:
                if col not in conversion:
                    conversion[col] = 'first'
            data = data.resample("5Min").agg(conversion).dropna()
            prescan_timeframe = 5

        # Slice limit (1.5 years of 5min or 1min bars)
        if len(data) > 150000:
            logger.info(f"Slicing data from {len(data)} to 150000 bars for fast pre-scan processing.")
            data = data.iloc[-150000:]

        lookbacks = sorted({int(v) for v in lookback_specs.values})
        mult_enters = sorted({float(v) for v in mult_enter_specs.values})
        mult_exits = sorted({float(v) for v in mult_exit_specs.values})

        from ..prescan_utils import downsample_parameter_grid
        downsampled = downsample_parameter_grid(
            {
                "lookback_days": lookbacks,
                "volatility_multiplier_enter": mult_enters,
                "volatility_multiplier_exit": mult_exits,
            },
            max_combos=20000,
            strategy_name="NoiseBoundary"
        )
        lookbacks = downsampled["lookback_days"]
        mult_enters = downsampled["volatility_multiplier_enter"]
        mult_exits = downsampled["volatility_multiplier_exit"]

        # Precompute overnight gap anchors anchor_up & anchor_down (constant across all parameters)
        normalized_index = data.index.normalize()
        daily_open = data.groupby(normalized_index)["open"].transform("first")
        
        daily_close_series = data["close"].resample("D").last().dropna()
        prev_day_close_series = daily_close_series.shift(1)
        prev_day_close = prev_day_close_series.reindex(normalized_index).values
        prev_close_filled = np.where(np.isnan(prev_day_close), daily_open, prev_day_close)
        
        anchor_up = np.maximum(daily_open, prev_close_filled).values if hasattr(np.maximum(daily_open, prev_close_filled), "values") else np.maximum(daily_open, prev_close_filled)
        anchor_down = np.minimum(daily_open, prev_close_filled).values if hasattr(np.minimum(daily_open, prev_close_filled), "values") else np.minimum(daily_open, prev_close_filled)

        # Precompute move_open
        move_open = (data["close"] / daily_open - 1).abs()
        pivoted_df = pd.DataFrame({"move_open": move_open}, index=data.index)
        pivoted_df["date"] = normalized_index
        pivoted_df["time"] = data.index.time
        pivoted_matrix = pivoted_df.pivot(index="date", columns="time", values="move_open")

        # Precompute mapped_vol for each unique lookback_days
        mapped_vol_by_lookback = {}
        multi_index = pd.MultiIndex.from_arrays([normalized_index, data.index.time], names=["date", "time"])
        for lookback in lookbacks:
            if stop_requested is not None and stop_requested():
                logger.warning("Pre-scan Noise Boundary annulé pendant le précalcul des indicateurs.")
                _write_prescan_report(output_dir, "cancelled", None, {})
                return parameter_specs
            rolling_matrix = pivoted_matrix.rolling(window=lookback, min_periods=lookback - 1).mean().shift(1)
            stacked = rolling_matrix.stack(dropna=False)
            mapped_vol = stacked.reindex(multi_index).values
            mapped_vol_by_lookback[lookback] = mapped_vol

        # Generate combinations
        combos = [
            (l, me, mx)
            for l in lookbacks
            for me in mult_enters
            for mx in mult_exits
        ]

        # 2. Dynamic Batch Size (Piste B)
        if workers > 1:
            BATCH_SIZE = 50
        else:
            BATCH_SIZE = 100

        total_batches = (len(combos) + BATCH_SIZE - 1) // BATCH_SIZE if combos else 0
        returns_batches: list[pd.Series] = []

        close = data["close"]

        # 3. Multiprocessing Parallelization (Piste A)
        if workers > 1:
            logger.info(f"Lancement du Pre-Scan VectorBT en parallèle avec {workers} processus (Batch Size={BATCH_SIZE})...")
            import multiprocessing
            try:
                ctx = multiprocessing.get_context("fork")
            except ValueError:
                ctx = multiprocessing.get_context()

            # Split combos into list of batches
            batches = []
            for batch_idx in range(total_batches):
                start_i = batch_idx * BATCH_SIZE
                end_i = min(start_i + BATCH_SIZE, len(combos))
                batches.append(combos[start_i:end_i])

            import concurrent.futures
            with concurrent.futures.ProcessPoolExecutor(
                max_workers=workers,
                mp_context=ctx,
                initializer=_init_prescan_worker,
                initargs=(close, anchor_up, anchor_down, mapped_vol_by_lookback, prescan_timeframe)
            ) as executor:
                completed = 0
                futures = {executor.submit(_process_prescan_batch, b): b for b in batches}

                while futures:
                    if stop_requested is not None and stop_requested():
                        logger.warning("Pre-scan Noise Boundary annulé pendant le calcul parallèle.")
                        for f in futures:
                            f.cancel()
                        executor.shutdown(wait=False)
                        _write_prescan_report(output_dir, "cancelled", None, {})
                        return parameter_specs

                    done, _ = concurrent.futures.wait(
                        futures.keys(),
                        timeout=1.0,
                        return_when=concurrent.futures.FIRST_COMPLETED
                    )

                    for future in done:
                        try:
                            res = future.result()
                            returns_batches.append(res)
                        except Exception as e:
                            logger.error(f"Le process worker a crashé ou échoué: {e}")
                            for f in futures:
                                f.cancel()
                            executor.shutdown(wait=False)
                            raise RuntimeError(f"Pre-scan VectorBT échoué: {e}") from e

                        del futures[future]
                        completed += 1
                        if progress_callback is not None:
                            try:
                                progress_callback(completed, total_batches)
                            except Exception as cb_err:
                                logger.warning(f"Error in prescan progress callback: {cb_err}")
        else:
            logger.info(f"Lancement du Pre-Scan VectorBT en séquentiel (Batch Size={BATCH_SIZE})...")
            for batch_idx in range(total_batches):
                if stop_requested is not None and stop_requested():
                    logger.warning("Pre-scan Noise Boundary annulé pendant le calcul des signaux.")
                    _write_prescan_report(output_dir, "cancelled", None, {})
                    return parameter_specs

                start_i = batch_idx * BATCH_SIZE
                end_i = min(start_i + BATCH_SIZE, len(combos))
                batch_combos = combos[start_i:end_i]

                batch_long_entries = {}
                batch_short_entries = {}
                batch_long_exits = {}
                batch_short_exits = {}

                for lookback, mult_enter, mult_exit in batch_combos:
                    mapped_vol = mapped_vol_by_lookback[lookback]

                    upper_enter = anchor_up * (1 + mult_enter * mapped_vol)
                    lower_enter = anchor_down * (1 - mult_enter * mapped_vol)
                    upper_exit = anchor_up * (1 + mult_exit * mapped_vol)
                    lower_exit = anchor_down * (1 - mult_exit * mapped_vol)

                    long_entries = close > upper_enter
                    short_entries = close < lower_enter
                    long_exits = close < lower_exit
                    short_exits = close > upper_exit

                    col = (lookback, mult_enter, mult_exit)
                    batch_long_entries[col] = long_entries
                    batch_short_entries[col] = short_entries
                    batch_long_exits[col] = long_exits
                    batch_short_exits[col] = short_exits

                columns = pd.MultiIndex.from_tuples(batch_combos, names=["lookback_days", "volatility_multiplier_enter", "volatility_multiplier_exit"])
                long_entries_df = pd.DataFrame(batch_long_entries, index=data.index, columns=columns)
                short_entries_df = pd.DataFrame(batch_short_entries, index=data.index, columns=columns)
                long_exits_df = pd.DataFrame(batch_long_exits, index=data.index, columns=columns)
                short_exits_df = pd.DataFrame(batch_short_exits, index=data.index, columns=columns)

                pf = vbt.Portfolio.from_signals(
                    close,
                    entries=long_entries_df,
                    exits=long_exits_df,
                    short_entries=short_entries_df,
                    short_exits=short_exits_df,
                    freq=f"{prescan_timeframe}min",
                )
                returns_batches.append(pf.total_return())

                # Free RAM
                del long_entries_df
                del short_entries_df
                del long_exits_df
                del short_exits_df
                del pf
                del batch_long_entries
                del batch_short_entries
                del batch_long_exits
                del batch_short_exits
                gc.collect()

                if progress_callback is not None:
                    try:
                        progress_callback(batch_idx + 1, total_batches)
                    except Exception as cb_err:
                        logger.warning(f"Error in prescan progress callback: {cb_err}")

        if returns_batches:
            returns = pd.concat(returns_batches)
            returns = returns.sort_index()
        else:
            returns = pd.Series(dtype=float)

        # Récupère le Top 5% des configurations
        top_n = max(1, int(len(returns) * 0.05))
        top_params = returns.nlargest(top_n).index.tolist()

        if top_params:
            min_lookback, max_lookback = min(p[0] for p in top_params), max(p[0] for p in top_params)
            min_mult_enter, max_mult_enter = min(p[1] for p in top_params), max(p[1] for p in top_params)
            min_mult_exit, max_mult_exit = min(p[2] for p in top_params), max(p[2] for p in top_params)

            # Marge de sécurité (+/- 10%)
            margin_lookback = max(1, int((max_lookback - min_lookback) * 0.1))
            margin_mult_enter = max(0.1, (max_mult_enter - min_mult_enter) * 0.1)
            margin_mult_exit = max(0.1, (max_mult_exit - min_mult_exit) * 0.1)

            min_lookback = max(int(lookback_specs.values[0]), min_lookback - margin_lookback)
            max_lookback = min(int(lookback_specs.values[-1]), max_lookback + margin_lookback)

            min_mult_enter = max(float(mult_enter_specs.values[0]), min_mult_enter - margin_mult_enter)
            max_mult_enter = min(float(mult_enter_specs.values[-1]), max_mult_enter + margin_mult_enter)

            min_mult_exit = max(float(mult_exit_specs.values[0]), min_mult_exit - margin_mult_exit)
            max_mult_exit = min(float(mult_exit_specs.values[-1]), max_mult_exit + margin_mult_exit)

            # Remplacement des spécifications pour Optuna
            new_specs = []
            lookback_filtered: tuple = ()
            mult_enter_filtered: tuple = ()
            mult_exit_filtered: tuple = ()

            for s in parameter_specs:
                if s.name == "lookback_days":
                    new_vals = tuple(v for v in s.values if min_lookback <= int(v) <= max_lookback)
                    lookback_filtered = new_vals or s.values
                    new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=lookback_filtered))
                elif s.name == "volatility_multiplier_enter":
                    new_vals = tuple(v for v in s.values if min_mult_enter <= float(v) <= max_mult_enter)
                    mult_enter_filtered = new_vals or s.values
                    new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=mult_enter_filtered))
                elif s.name == "volatility_multiplier_exit":
                    new_vals = tuple(v for v in s.values if min_mult_exit <= float(v) <= max_mult_exit)
                    mult_exit_filtered = new_vals or s.values
                    new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=mult_exit_filtered))
                else:
                    new_specs.append(s)

            _write_prescan_report(
                output_dir,
                "success",
                top_n,
                {
                    "lookback_days": {
                        "original_bounds": [int(lookback_specs.values[0]), int(lookback_specs.values[-1])],
                        "new_bounds": [int(lookback_filtered[0]), int(lookback_filtered[-1])],
                        "filtered_values": list(lookback_filtered),
                    },
                    "volatility_multiplier_enter": {
                        "original_bounds": [float(mult_enter_specs.values[0]), float(mult_enter_specs.values[-1])],
                        "new_bounds": [float(mult_enter_filtered[0]), float(mult_enter_filtered[-1])],
                        "filtered_values": list(mult_enter_filtered),
                    },
                    "volatility_multiplier_exit": {
                        "original_bounds": [float(mult_exit_specs.values[0]), float(mult_exit_specs.values[-1])],
                        "new_bounds": [float(mult_exit_filtered[0]), float(mult_exit_filtered[-1])],
                        "filtered_values": list(mult_exit_filtered),
                    },
                },
            )
            logger.info(
                f"Bornes Optuna réduites via VectorBT: "
                f"lookback_days({min_lookback}-{max_lookback}), "
                f"volatility_multiplier_enter({min_mult_enter:.1f}-{max_mult_enter:.1f}), "
                f"volatility_multiplier_exit({min_mult_exit:.1f}-{max_mult_exit:.1f})"
            )
            return new_specs
        else:
            _write_prescan_report(output_dir, "no_candidates", top_n, {})
            return parameter_specs

    except ImportError:
        _write_prescan_report(output_dir, "skipped", None, {})
        logger.warning("VectorBT n'est pas installé, impossible de lancer le pre-scan.")
    except Exception as e:
        _write_prescan_report(output_dir, "error", None, {})
        logger.warning(f"Erreur Pre-Scan VectorBT: {e}. Optuna utilisera les bornes globales.")

    _write_prescan_report(output_dir, "skipped", None, {})
    return parameter_specs

