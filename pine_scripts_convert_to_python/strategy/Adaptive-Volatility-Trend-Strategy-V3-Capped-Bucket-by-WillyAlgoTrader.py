"""
Adaptive Volatility Trend Strategy V3.2 (Capped Bucket) - Python conversion.

Converted from TradingView Pine Script:
"Adaptive Volatility Trend Strategy V3.2 (Capped Bucket)" by WillyAlgoTrader.

Expected input:
    pandas.DataFrame with columns:
        open, high, low, close
    optional:
        volume

Main outputs:
    add_avt_features(df, config) -> DataFrame
        Adds indicator/ML-ready columns, signals, scores, bands and filters.

    backtest_avt_strategy(df, config) -> (DataFrame, trades DataFrame)
        Adds the strategy/bucket/order simulation columns and a trade ledger.

Notes:
    - This is a clean pandas/numpy conversion. It does not depend on TA-Lib.
    - Currency conversion functions from Pine (`strategy.convert_to_account/symbol`) are
      treated as 1:1. Use `point_value` for futures/CFDs where one point is not one unit.
    - TradingView strategies with `process_orders_on_close=false` usually fill market
      orders at the next bar's open. The default `execution="next_open"` mirrors that.
      Set `execution="close"` for simpler same-bar-close fills.
    - The script did not define native TradingView commissions. Therefore the capped
      bucket is updated from realized gross strategy P&L by default, while the user
      supplied fee/slippage estimates are used for filters, TP/SL and safety logic,
      as in the Pine code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
import numba

from backtest_engine.broker import BrokerConfig, BrokerSimulator, Order


@numba.njit(cache=False)
def _compute_adaptive_ma_numba(safe_src_arr: np.ndarray, sc_arr: np.ndarray) -> np.ndarray:
    n = len(safe_src_arr)
    adaptive_arr = np.empty(n, dtype=np.float64)
    prev = np.nan
    for i in range(n):
        value = safe_src_arr[i]
        if np.isnan(prev):
            current = value
        else:
            current = prev + sc_arr[i] * (value - prev)
        adaptive_arr[i] = current
        prev = current
    return adaptive_arr


@numba.njit(cache=False)
def _compute_trend_dir_numba(line_delta_arr: np.ndarray, threshold_arr: np.ndarray) -> np.ndarray:
    n = len(line_delta_arr)
    trend_dir_arr = np.zeros(n, dtype=np.int64)
    prev_trend = 0
    for i in range(n):
        if line_delta_arr[i] > threshold_arr[i]:
            prev_trend = 1
        elif line_delta_arr[i] < -threshold_arr[i]:
            prev_trend = -1
        trend_dir_arr[i] = prev_trend
    return trend_dir_arr



Preset = Literal["Conservative", "Default", "Aggressive", "Scalping"]
DirectionMode = Literal["Long & Short", "Long only", "Short only"]
FeeMode = Literal[
    "Parametric: hold until net covers fees",
    "Parametric: exit only, no forced reversal",
    "Disabled: always reverse/close on opposite signal",
]
SafetyAppliesTo = Literal["Both", "Long only", "Short only"]
SafetyStopMode = Literal[
    "Net loss only",
    "Max bars only",
    "Net loss OR max bars",
    "Net loss AND max bars",
]
SafetyMaxNetLossMode = Literal["Cash amount", "% of entry value"]
ExecutionMode = Literal["next_open", "close"]


@dataclass(slots=True)
class AVTConfig:
    # Main settings
    source: str = "close"
    length: int = 21
    atr_len: int = 14
    atr_mult: float = 2.0
    preset: Preset = "Default"

    # Currency overrides
    asset_currency: str | None = None
    account_currency: str | None = None
    fx_rate_provider: object | None = None

    # Filters
    use_rsi_filter: bool = True
    rsi_len: int = 14
    rsi_overbought: int = 70
    rsi_oversold: int = 30
    use_volume_filter: bool = True
    volume_mult: float = 1.2

    # Advanced
    efficiency_smoothing: int = 5
    min_signal_score: int = 40

    # V3 capped bucket model
    max_entry_price: float = 300.0
    max_capital_bucket: float = 300.0
    initial_capital_bucket: float = 300.0

    # Direction
    trade_direction_mode: DirectionMode = "Long & Short"

    # Fee/reversal filter
    fee_mode: FeeMode = "Parametric: hold until net covers fees"
    estimated_commission_per_order_long: float = 0.0
    estimated_commission_per_order_short: float = 3.0
    estimated_slippage_per_side_long: float = 0.0
    estimated_slippage_per_side_short: float = 0.0
    min_net_profit_after_costs: float = 0.0

    # Explicit net exits
    use_net_bracket_exits: bool = False
    take_profit_net_percent: float = 10.0
    stop_loss_net_percent: float = 10.0

    # Safety stop
    use_safety_stop: bool = True
    safety_stop_applies_to: SafetyAppliesTo = "Short only"
    safety_stop_mode: SafetyStopMode = "Net loss only"
    safety_max_net_loss_mode: SafetyMaxNetLossMode = "Cash amount"
    safety_max_net_loss_cash: float = 50.0
    safety_max_net_loss_percent: float = 0.0
    safety_max_bars_in_trade: int = 0

    # Python/backtest assumptions
    point_value: float = 1.0
    execution: ExecutionMode = "next_open"
    apply_estimated_costs_to_realized_pnl: bool = True
    allow_fractional_quantity: bool = True
    quantity_precision: int | None = 6


def _require_ohlc(df: pd.DataFrame) -> None:
    missing = {"open", "high", "low", "close"} - set(df.columns)
    if missing:
        raise ValueError(f"Input DataFrame is missing required columns: {sorted(missing)}")


def _as_float_series(df: pd.DataFrame, column: str, fallback: float = np.nan) -> pd.Series:
    if column in df.columns:
        return pd.to_numeric(df[column], errors="coerce").astype(float)
    return pd.Series(fallback, index=df.index, dtype="float64")


def _price_source(df: pd.DataFrame, source: str) -> pd.Series:
    source = source.lower()
    if source == "close":
        return _as_float_series(df, "close")
    if source == "open":
        return _as_float_series(df, "open")
    if source == "high":
        return _as_float_series(df, "high")
    if source == "low":
        return _as_float_series(df, "low")
    if source == "hl2":
        return (_as_float_series(df, "high") + _as_float_series(df, "low")) / 2.0
    if source == "hlc3":
        return (
            _as_float_series(df, "high")
            + _as_float_series(df, "low")
            + _as_float_series(df, "close")
        ) / 3.0
    if source == "ohlc4":
        return (
            _as_float_series(df, "open")
            + _as_float_series(df, "high")
            + _as_float_series(df, "low")
            + _as_float_series(df, "close")
        ) / 4.0
    if source in df.columns:
        return _as_float_series(df, source)
    raise ValueError(
        f"Unknown source={source!r}. Use one of close/open/high/low/hl2/hlc3/ohlc4 "
        "or pass the name of an existing numeric DataFrame column."
    )


def _sma(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(length, min_periods=length).mean()


def _ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False, min_periods=1).mean()


def _rma(series: pd.Series, length: int) -> pd.Series:
    """TradingView-style Wilder RMA approximation."""
    return series.ewm(alpha=1.0 / length, adjust=False, min_periods=1).mean()


def _true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev_close = close.shift(1)
    return pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int) -> pd.Series:
    return _rma(_true_range(high, low, close), length)


def _rsi(series: pd.Series, length: int) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0.0).fillna(0.0)
    loss = (-delta.clip(upper=0.0)).fillna(0.0)

    avg_gain = _rma(gain, length)
    avg_loss = _rma(loss, length)

    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))

    both_zero = (avg_gain == 0.0) & (avg_loss == 0.0)
    only_gain = (avg_gain > 0.0) & (avg_loss == 0.0)
    only_loss = (avg_gain == 0.0) & (avg_loss > 0.0)

    rsi = rsi.mask(both_zero, 50.0)
    rsi = rsi.mask(only_gain, 100.0)
    rsi = rsi.mask(only_loss, 0.0)
    return rsi.fillna(50.0)


def _safe_div(num: pd.Series, den: pd.Series, fallback: float = 0.0) -> pd.Series:
    out = num / den.replace(0.0, np.nan)
    return out.replace([np.inf, -np.inf], np.nan).fillna(fallback)


def _efficiency_ratio(source: pd.Series, length: int) -> pd.Series:
    # Pine:
    # direction  = abs(nz(src, 0) - nz(src[len], src))
    # volatility = sum(abs(nz(src, 0) - nz(src[1], src)), len)
    safe_src = source.fillna(0.0)
    shifted_len = source.shift(length).fillna(source)
    direction = (safe_src - shifted_len).abs()

    shifted_1 = source.shift(1).fillna(source)
    step_change = (safe_src - shifted_1).abs()
    volatility = step_change.rolling(length, min_periods=1).sum()

    return _safe_div(direction, volatility, 0.0)


def _adaptive_ma(source: pd.Series, close: pd.Series, length: int, smooth: int) -> tuple[pd.Series, pd.Series]:
    er = _efficiency_ratio(source, length)
    er_smoothed = _ema(er, smooth).fillna(0.5)

    fast_sc = 2.0 / (2.0 + 1.0)
    slow_sc = 2.0 / (30.0 + 1.0)
    sc = (er_smoothed * (fast_sc - slow_sc) + slow_sc) ** 2.0

    safe_src = source.where(source.notna(), close)
    safe_src_arr = safe_src.to_numpy(dtype=float)
    sc_arr = sc.to_numpy(dtype=float)
    adaptive_arr = _compute_adaptive_ma_numba(safe_src_arr, sc_arr)

    adaptive = pd.Series(adaptive_arr, index=source.index, dtype="float64")
    return adaptive, er_smoothed



def _signal_score(
    is_bull: pd.Series,
    er: pd.Series,
    rsi_value: pd.Series,
    vol_ratio: pd.Series,
    has_volume: pd.Series,
) -> pd.Series:
    trend_score = np.minimum(er.fillna(0.0) * 60.0, 40.0)

    bull_rsi_dist = np.maximum(rsi_value - 50.0, 0.0)
    bear_rsi_dist = np.maximum(50.0 - rsi_value, 0.0)
    rsi_dist = pd.Series(np.where(is_bull, bull_rsi_dist, bear_rsi_dist), index=er.index)
    momentum_score = np.minimum(rsi_dist, 30.0)

    with_volume = np.minimum(np.maximum(vol_ratio - 1.0, 0.0) * 30.0, 30.0)
    volume_score = pd.Series(np.where(has_volume, with_volume, 15.0), index=er.index)

    total = np.minimum(trend_score + momentum_score + volume_score, 100.0)
    return np.floor(total + 0.5).astype(int)


def _bucket_clamp(value: float, bucket_max: float) -> float:
    if pd.isna(value):
        return 0.0
    return float(max(min(value, bucket_max), 0.0))


def _qty_from_bucket(bucket: float, price: float) -> float:
    return float(bucket / price) if price and price > 0 else 0.0


def _effective_parameters(config: AVTConfig) -> tuple[int, int, float]:
    if config.preset == "Conservative":
        return 30, 20, 2.5
    if config.preset == "Aggressive":
        return 12, 10, 1.5
    if config.preset == "Scalping":
        return 8, 7, 1.2
    return config.length, config.atr_len, config.atr_mult


# Shared indicator references (populated by backtest_engine multiprocessing workers)
_SHARED_AVT_AMA_GRID: np.ndarray | None = None
_SHARED_AVT_AMA_KEYS: dict[tuple[str, int, int], int] | None = None
_SHARED_AVT_ATR_GRID: np.ndarray | None = None
_SHARED_AVT_ATR_KEYS: dict[int, int] | None = None
_SHARED_AVT_RSI_GRID: np.ndarray | None = None
_SHARED_AVT_RSI_KEYS: dict[tuple[str, int], int] | None = None


def add_avt_features(df: pd.DataFrame, config: AVTConfig | None = None, compute_full_metrics: bool = True) -> pd.DataFrame:
    """
    Add AVT indicator, filter, score and signal columns to an OHLCV DataFrame.

    The output is ML-friendly: no chart/table/alert fields are included, only numeric
    and boolean columns derived from the Pine calculations.
    """
    config = config or AVTConfig()
    _require_ohlc(df)

    out = df.copy()
    close = _as_float_series(out, "close")
    high = _as_float_series(out, "high")
    low = _as_float_series(out, "low")
    volume = _as_float_series(out, "volume", fallback=0.0)

    effective_length, effective_atr_len, effective_mult = _effective_parameters(config)
    source = _price_source(out, config.source)

    global _SHARED_AVT_AMA_GRID, _SHARED_AVT_AMA_KEYS
    global _SHARED_AVT_ATR_GRID, _SHARED_AVT_ATR_KEYS
    global _SHARED_AVT_RSI_GRID, _SHARED_AVT_RSI_KEYS

    # 1. AMA Grid Lookup
    ama_loaded = False
    if _SHARED_AVT_AMA_GRID is not None and _SHARED_AVT_AMA_KEYS is not None:
        ama_key = (str(config.source), int(effective_length), int(config.efficiency_smoothing))
        if ama_key in _SHARED_AVT_AMA_KEYS:
            idx = _SHARED_AVT_AMA_KEYS[ama_key]
            adaptive_line = pd.Series(_SHARED_AVT_AMA_GRID[idx, 0], index=out.index, dtype="float64")
            efficiency_ratio = pd.Series(_SHARED_AVT_AMA_GRID[idx, 1], index=out.index, dtype="float64")
            ama_loaded = True

    if not ama_loaded:
        adaptive_line, efficiency_ratio = _adaptive_ma(
            source=source,
            close=close,
            length=effective_length,
            smooth=config.efficiency_smoothing,
        )
    safe_line = adaptive_line.fillna(close)

    # 2. ATR Grid Lookup
    atr_loaded = False
    if _SHARED_AVT_ATR_GRID is not None and _SHARED_AVT_ATR_KEYS is not None:
        atr_key = int(effective_atr_len)
        if atr_key in _SHARED_AVT_ATR_KEYS:
            idx = _SHARED_AVT_ATR_KEYS[atr_key]
            atr_raw = pd.Series(_SHARED_AVT_ATR_GRID[idx], index=out.index, dtype="float64")
            atr_loaded = True

    if not atr_loaded:
        atr_raw = _atr(high, low, close, effective_atr_len).fillna(0.0)

    line_delta = safe_line - safe_line.shift(1).fillna(safe_line)
    threshold = atr_raw * 0.05

    line_delta_arr = line_delta.to_numpy(dtype=float)
    threshold_arr = threshold.to_numpy(dtype=float)
    trend_dir_arr = _compute_trend_dir_numba(line_delta_arr, threshold_arr)
    trend_dir = pd.Series(trend_dir_arr, index=out.index, dtype="int64")

    is_bull_trend = trend_dir == 1
    is_bear_trend = trend_dir == -1

    # 3. RSI Grid Lookup
    rsi_loaded = False
    if _SHARED_AVT_RSI_GRID is not None and _SHARED_AVT_RSI_KEYS is not None:
        rsi_key = (str(config.source), int(config.rsi_len))
        if rsi_key in _SHARED_AVT_RSI_KEYS:
            idx = _SHARED_AVT_RSI_KEYS[rsi_key]
            rsi_value = pd.Series(_SHARED_AVT_RSI_GRID[idx], index=out.index, dtype="float64")
            rsi_loaded = True

    if not rsi_loaded:
        rsi_value = _rsi(source, config.rsi_len).fillna(50.0)

    has_volume = volume.fillna(0.0) > 0.0
    vol_sma_raw = _sma(volume, 20)
    vol_sma = pd.Series(np.where(has_volume, vol_sma_raw.fillna(volume), 0.0), index=out.index)
    vol_ratio = pd.Series(
        np.where(has_volume & (vol_sma > 0.0), volume / vol_sma.replace(0.0, np.nan), 1.0),
        index=out.index,
    ).replace([np.inf, -np.inf], np.nan).fillna(1.0)

    vol_confirm = (
        (~pd.Series(config.use_volume_filter, index=out.index))
        | (~has_volume)
        | (vol_ratio >= config.volume_mult)
    )
    rsi_buy_ok = (~pd.Series(config.use_rsi_filter, index=out.index)) | (rsi_value < config.rsi_overbought)
    rsi_sell_ok = (~pd.Series(config.use_rsi_filter, index=out.index)) | (rsi_value > config.rsi_oversold)

    prev_bull = is_bull_trend.shift(1, fill_value=False)
    prev_bear = is_bear_trend.shift(1, fill_value=False)
    trend_flip_bull = is_bull_trend & (~prev_bull)
    trend_flip_bear = is_bear_trend & (~prev_bear)

    price_above = source > safe_line
    price_below = source < safe_line

    buy_condition = trend_flip_bull & price_above & rsi_buy_ok & vol_confirm
    sell_condition = trend_flip_bear & price_below & rsi_sell_ok & vol_confirm

    buy_score_raw = _signal_score(
        pd.Series(True, index=out.index),
        efficiency_ratio.fillna(0.0),
        rsi_value,
        vol_ratio,
        has_volume,
    )
    sell_score_raw = _signal_score(
        pd.Series(False, index=out.index),
        efficiency_ratio.fillna(0.0),
        rsi_value,
        vol_ratio,
        has_volume,
    )

    buy_score = pd.Series(np.where(buy_condition, buy_score_raw, 0), index=out.index).astype(int)
    sell_score = pd.Series(np.where(sell_condition, sell_score_raw, 0), index=out.index).astype(int)

    bar_number = pd.Series(np.arange(len(out)), index=out.index)
    warmup_bars = max(effective_length * 2, 50)
    is_warmed_up = bar_number >= warmup_bars

    confirmed_buy = buy_condition & is_warmed_up & (buy_score >= config.min_signal_score)
    confirmed_sell = sell_condition & is_warmed_up & (sell_score >= config.min_signal_score)

    if compute_full_metrics:
        er_factor = 1.0 - efficiency_ratio.fillna(0.5) * 0.4
        band_width = atr_raw * effective_mult * er_factor
        upper_band = safe_line + band_width
        lower_band = safe_line - band_width

        out["avt_source"] = source
        out["avt_effective_length"] = effective_length
        out["avt_effective_atr_len"] = effective_atr_len
        out["avt_effective_mult"] = effective_mult
        out["avt_warmup_bars"] = warmup_bars
        out["avt_is_warmed_up"] = is_warmed_up

        out["avt_adaptive_trend"] = safe_line
        out["avt_efficiency_ratio"] = efficiency_ratio
        out["avt_atr"] = atr_raw
        out["avt_er_factor"] = er_factor
        out["avt_band_width"] = band_width
        out["avt_upper_band"] = upper_band
        out["avt_lower_band"] = lower_band
        out["avt_trend_dir"] = trend_dir
        out["avt_is_bull_trend"] = is_bull_trend
        out["avt_is_bear_trend"] = is_bear_trend

        out["avt_rsi"] = rsi_value
        out["avt_has_volume"] = has_volume
        out["avt_volume_sma"] = vol_sma
        out["avt_volume_ratio"] = vol_ratio
        out["avt_volume_confirm"] = vol_confirm
        out["avt_rsi_buy_ok"] = rsi_buy_ok
        out["avt_rsi_sell_ok"] = rsi_sell_ok

        out["avt_trend_flip_bull"] = trend_flip_bull
        out["avt_trend_flip_bear"] = trend_flip_bear
        out["avt_price_above_trend"] = price_above
        out["avt_price_below_trend"] = price_below
        out["avt_buy_condition"] = buy_condition
        out["avt_sell_condition"] = sell_condition
        out["avt_buy_score"] = buy_score
        out["avt_sell_score"] = sell_score
        out["avt_confirmed_buy"] = confirmed_buy
        out["avt_confirmed_sell"] = confirmed_sell

        # Same as Pine aliases.
        out["avt_long_signal"] = confirmed_buy
        out["avt_short_signal"] = confirmed_sell

        # Last signal/score columns, useful for dashboards and ML labels.
        last_signal = []
        last_score = []
        sig = "—"
        score = 0
        for buy, sell, bscore, sscore in zip(confirmed_buy, confirmed_sell, buy_score, sell_score):
            if buy:
                sig = "BUY"
                score = int(bscore)
            if sell:
                sig = "SELL"
                score = int(sscore)
            last_signal.append(sig)
            last_score.append(score)

        out["avt_last_signal"] = last_signal
        out["avt_last_score"] = last_score
    else:
        # Avoid creating 35+ high-volume pandas columns when doing lightweight/optimization trials
        cols_to_keep = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
        out = df[cols_to_keep].copy()
        out["avt_long_signal"] = confirmed_buy
        out["avt_short_signal"] = confirmed_sell

    return out



def _position_gross_pnl(
    position_size: float,
    position_avg_price: float,
    mark_price: float,
    point_value: float,
    fx_rate: float = 1.0,
) -> float:
    if position_size == 0 or pd.isna(position_avg_price) or pd.isna(mark_price):
        return 0.0
    mark_price_account = mark_price * fx_rate
    if position_size > 0:
        return (mark_price_account - position_avg_price) * abs(position_size) * point_value
    if position_size < 0:
        return (position_avg_price - mark_price_account) * abs(position_size) * point_value
    return 0.0


def _apply_target_position(
    *,
    target_size: float,
    fill_price: float,
    bar_index: int,
    position_size: float,
    position_avg_price: float,
    entry_bar_index: int | None,
    point_value: float,
) -> tuple[float, float, int | None, float, bool]:
    """
    Apply a TradingView-like market entry/close target.

    Returns:
        position_size, position_avg_price, entry_bar_index, realized_gross_pnl, opened_or_reversed
    """
    realized = 0.0
    opened_or_reversed = False

    # Flat -> open.
    if position_size == 0:
        if target_size != 0:
            return target_size, fill_price, bar_index, 0.0, True
        return 0.0, np.nan, None, 0.0, False

    # Close.
    if target_size == 0:
        realized = _position_gross_pnl(position_size, position_avg_price, fill_price, point_value)
        return 0.0, np.nan, None, realized, False

    # Same direction. Pyramiding is disabled in the Pine strategy, so replace target
    # only if the caller explicitly asks for a same-side target.
    if np.sign(position_size) == np.sign(target_size):
        return target_size, position_avg_price, entry_bar_index, 0.0, False

    # Reversal: close the old side and open the new side at the same fill price.
    realized = _position_gross_pnl(position_size, position_avg_price, fill_price, point_value)
    return target_size, fill_price, bar_index, realized, True


def backtest_avt_strategy(
    df: pd.DataFrame,
    config: AVTConfig | None = None,
    early_stop_drawdown_pct: float | None = None,
    compute_full_metrics: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Simulate the Pine strategy logic on an OHLCV DataFrame.

    Returns:
        enriched_df:
            Original OHLCV + AVT feature columns + strategy state columns.
        trades:
            One row per filled close/reversal/open event.

    This is intentionally explicit and loop-based because the capped bucket and
    reversal filters are stateful.
    """
    config = config or AVTConfig()
    import inspect
    sig = inspect.signature(add_avt_features)
    if "compute_full_metrics" in sig.parameters:
        enriched = add_avt_features(df, config, compute_full_metrics)
    else:
        enriched = add_avt_features(df, config)
    broker = BrokerSimulator(
        BrokerConfig(
            initial_capital=float(config.initial_capital_bucket),
            execute_on_next_bar=config.execution == "next_open",
            execution_price_col="open" if config.execution == "next_open" else "close",
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

    open_ = _as_float_series(enriched, "open")
    close = _as_float_series(enriched, "close")

    allow_long = config.trade_direction_mode != "Short only"
    allow_short = config.trade_direction_mode != "Long only"

    hold_until_profitable = config.fee_mode == "Parametric: hold until net covers fees"
    exit_only_no_reverse = config.fee_mode == "Parametric: exit only, no forced reversal"
    disable_fee_filter = config.fee_mode == "Disabled: always reverse/close on opposite signal"

    capital_bucket = _bucket_clamp(config.initial_capital_bucket, config.max_capital_bucket)
    withdrawn_profit = 0.0
    strategy_netprofit = 0.0
    processed_netprofit = 0.0
    peak_equity = float(broker.cash)

    position_size = 0.0
    position_avg_price = np.nan
    entry_bar_index: int | None = None

    pending_target_size: float | None = None
    pending_comment: str | None = None
    pending_created_at = None

    rows: list[dict] = []
    trades: list[dict] = []

    index = enriched.index
    open_arr = open_.to_numpy(dtype=float)
    close_arr = close.to_numpy(dtype=float)
    long_signal_arr = enriched["avt_long_signal"].to_numpy(dtype=bool)
    short_signal_arr = enriched["avt_short_signal"].to_numpy(dtype=bool)

    def execute_target_position(
        *,
        target_size: float,
        fill_price: float,
        bar_index: int,
        comment: str,
    ) -> tuple[float, float, float, float, float, bool]:
        nonlocal position_size, position_avg_price, entry_bar_index

        old_size = position_size
        old_avg = position_avg_price
        old_side = 1 if old_size > 0 else -1 if old_size < 0 else 0
        target_side = 1 if target_size > 0 else -1 if target_size < 0 else 0
        target_qty = broker.normalize_quantity(abs(target_size))
        if target_qty <= 0:
            target_side = 0

        realized_gross = 0.0
        realized_costs = 0.0
        realized_net = 0.0
        closed_trade_count = len(broker.closed_trades)

        if old_side != 0 and (target_side == 0 or target_side != old_side):
            broker.fill_order(
                Order(
                    id=f"close-{bar_index}-{len(broker.fills)}",
                    side="sell" if old_side > 0 else "buy",
                    quantity=abs(old_size),
                    comment=comment,
                    cost_side="long" if old_side > 0 else "short",
                ),
                index[bar_index],
                fill_price,
            )
            if len(broker.closed_trades) > closed_trade_count:
                broker_trade = broker.closed_trades[-1]
                realized_gross = float(broker_trade.gross_pnl)
                realized_costs = float(broker_trade.commission)
                realized_net = float(broker_trade.net_pnl)

        opened_or_reversed = False
        if target_side != 0 and target_qty > 0 and old_side != target_side:
            fill = broker.fill_order(
                Order(
                    id=f"entry-{bar_index}-{len(broker.fills)}",
                    side="buy" if target_side > 0 else "sell",
                    quantity=target_qty,
                    comment=comment,
                    cost_side="long" if target_side > 0 else "short",
                ),
                index[bar_index],
                fill_price,
            )
            opened_or_reversed = fill is not None
            if fill is not None:
                entry_bar_index = bar_index

        position_size = float(broker.position.signed_quantity)
        position_avg_price = float(broker.position.average_price) if not broker.position.is_flat else np.nan
        if broker.position.is_flat:
            entry_bar_index = None

        return old_size, old_avg, realized_gross, realized_costs, realized_net, opened_or_reversed

    for bar_num, idx in enumerate(index):
        bar_realized_net = 0.0

        # Fill any order created on the prior bar. This mirrors
        # process_orders_on_close=false for market orders.
        if pending_target_size is not None and config.execution == "next_open":
            fill_price = open_arr[bar_num]
            if pd.isna(fill_price):
                fill_price = close_arr[bar_num]

            old_size, old_avg, realized, realized_costs, realized_net, opened_or_reversed = execute_target_position(
                target_size=pending_target_size,
                fill_price=float(fill_price),
                bar_index=bar_num,
                comment=str(pending_comment or ""),
            )
            if realized_net != 0.0:
                strategy_netprofit += realized_net
                bar_realized_net += realized_net

            raw_bucket = capital_bucket + (strategy_netprofit - processed_netprofit)
            if raw_bucket > config.max_capital_bucket:
                withdrawn_profit += raw_bucket - config.max_capital_bucket
            capital_bucket = _bucket_clamp(raw_bucket, config.max_capital_bucket)
            processed_netprofit = strategy_netprofit

            trades.append(
                {
                    "created_at": pending_created_at,
                    "filled_at": idx,
                    "comment": pending_comment,
                    "fill_price": float(fill_price),
                    "old_position_size": old_size,
                    "old_position_avg_price": old_avg,
                    "new_position_size": position_size,
                    "new_position_avg_price": position_avg_price,
                    "realized_gross_pnl": realized,
                    "estimated_costs": realized_costs,
                    "realized_net_pnl": realized_net,
                    "strategy_netprofit": strategy_netprofit,
                    "capital_bucket": capital_bucket,
                    "withdrawn_profit": withdrawn_profit,
                    "opened_or_reversed": opened_or_reversed,
                }
            )

            pending_target_size = None
            pending_comment = None
            pending_created_at = None

        # Phase 2: Early Stopping (Ruin-based pruning)
        mark_price = float(close_arr[bar_num])
        current_equity = broker.mark_to_market_equity(mark_price, enriched.index[bar_num])
        if current_equity > peak_equity:
            peak_equity = current_equity

        if early_stop_drawdown_pct is not None and early_stop_drawdown_pct > 0 and peak_equity > 0:
            drawdown_pct = (peak_equity - current_equity) / peak_equity * 100.0
            if drawdown_pct >= early_stop_drawdown_pct:
                strategy_state = pd.DataFrame(rows, index=enriched.index[:len(rows)])
                enriched = pd.concat([enriched.iloc[:len(rows)], strategy_state], axis=1)
                return enriched, broker.closed_trades_frame()

        in_long = position_size > 0.0
        in_short = position_size < 0.0
        flat = position_size == 0.0
        abs_pos_size = abs(position_size)
        entry_price = position_avg_price if abs_pos_size > 0 else np.nan

        bars_in_trade = bar_num - entry_bar_index if entry_bar_index is not None else 0
        gross_pnl_estimate_account = _position_gross_pnl(
            position_size,
            position_avg_price,
            mark_price,
            config.point_value,
            fx_rate=broker.fx_rate(enriched.index[bar_num]),
        )

        current_commission = (
            config.estimated_commission_per_order_long
            if in_long
            else config.estimated_commission_per_order_short
            if in_short
            else 0.0
        )
        current_slippage = (
            config.estimated_slippage_per_side_long
            if in_long
            else config.estimated_slippage_per_side_short
            if in_short
            else 0.0
        )
        estimated_round_trip_costs_account = (
            current_commission * 2.0 + current_slippage * 2.0 if abs_pos_size > 0.0 else 0.0
        )
        estimated_net_if_closed_now_account = (
            gross_pnl_estimate_account - estimated_round_trip_costs_account
        )
        reversal_net_filter_passed = (
            estimated_net_if_closed_now_account >= config.min_net_profit_after_costs
        )
        estimated_bucket_after_close = _bucket_clamp(
            capital_bucket + estimated_net_if_closed_now_account,
            config.max_capital_bucket,
        )

        quantity_point_value = abs_pos_size * config.point_value
        entry_position_value_account = (
            entry_price * abs_pos_size * config.point_value if abs_pos_size > 0.0 else 0.0
        )
        take_profit_net_threshold_account = (
            entry_position_value_account * config.take_profit_net_percent / 100.0
        )
        stop_loss_net_threshold_account = (
            entry_position_value_account * config.stop_loss_net_percent / 100.0
        )
        if config.safety_max_net_loss_mode == "Cash amount":
            safety_max_net_loss_threshold_account = config.safety_max_net_loss_cash
        else:
            safety_max_net_loss_threshold_account = (
                entry_position_value_account * config.safety_max_net_loss_percent / 100.0
            )

        safety_direction_allowed = (
            config.safety_stop_applies_to == "Both"
            or (config.safety_stop_applies_to == "Long only" and in_long)
            or (config.safety_stop_applies_to == "Short only" and in_short)
        )
        safety_loss_triggered = (
            safety_max_net_loss_threshold_account > 0.0
            and estimated_net_if_closed_now_account <= -safety_max_net_loss_threshold_account
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
            and abs_pos_size > 0.0
            and estimated_net_if_closed_now_account >= take_profit_net_threshold_account
        )
        hit_net_stop_loss = (
            config.use_net_bracket_exits
            and abs_pos_size > 0.0
            and estimated_net_if_closed_now_account <= -stop_loss_net_threshold_account
        )

        # Price levels used for diagnostics/data-window parity.
        if in_long and quantity_point_value > 0.0:
            long_take_profit_price = entry_price + (
                take_profit_net_threshold_account + estimated_round_trip_costs_account
            ) / quantity_point_value
            long_stop_loss_price = entry_price + (
                estimated_round_trip_costs_account - stop_loss_net_threshold_account
            ) / quantity_point_value
        else:
            long_take_profit_price = np.nan
            long_stop_loss_price = np.nan

        if in_short and quantity_point_value > 0.0:
            short_take_profit_price = entry_price - (
                take_profit_net_threshold_account + estimated_round_trip_costs_account
            ) / quantity_point_value
            short_stop_loss_price = entry_price + (
                stop_loss_net_threshold_account - estimated_round_trip_costs_account
            ) / quantity_point_value
        else:
            short_take_profit_price = np.nan
            short_stop_loss_price = np.nan

        entry_allowed_by_cap = mark_price <= config.max_entry_price and capital_bucket > 0.0
        flat_entry_qty = _qty_from_bucket(capital_bucket, mark_price)
        reverse_entry_qty = _qty_from_bucket(estimated_bucket_after_close, mark_price)

        long_signal = bool(long_signal_arr[bar_num])
        short_signal = bool(short_signal_arr[bar_num])

        order_target_size: float | None = None
        order_comment = ""

        if safety_stop_triggered and in_long:
            order_target_size = 0.0
            order_comment = "Safety Stop Long"
        elif safety_stop_triggered and in_short:
            order_target_size = 0.0
            order_comment = "Safety Stop Short"
        elif in_long and hit_net_take_profit:
            order_target_size = 0.0
            order_comment = "Net TP Long"
        elif in_long and hit_net_stop_loss:
            order_target_size = 0.0
            order_comment = "Net SL Long"
        elif in_short and hit_net_take_profit:
            order_target_size = 0.0
            order_comment = "Net TP Short"
        elif in_short and hit_net_stop_loss:
            order_target_size = 0.0
            order_comment = "Net SL Short"
        else:
            if flat and entry_allowed_by_cap and flat_entry_qty > 0.0:
                if long_signal and allow_long:
                    order_target_size = flat_entry_qty
                    order_comment = "BUY"
                elif short_signal and allow_short:
                    order_target_size = -flat_entry_qty
                    order_comment = "SELL"

            if in_long and short_signal:
                if disable_fee_filter:
                    if mark_price <= config.max_entry_price and reverse_entry_qty > 0.0:
                        if allow_short:
                            order_target_size = -reverse_entry_qty
                            order_comment = "SELL REV"
                        else:
                            order_target_size = 0.0
                            order_comment = "Exit Long"
                    else:
                        order_target_size = 0.0
                        order_comment = "Exit Long"
                elif exit_only_no_reverse or not allow_short:
                    order_target_size = 0.0
                    order_comment = "Exit Long"
                elif hold_until_profitable and reversal_net_filter_passed:
                    if mark_price <= config.max_entry_price and reverse_entry_qty > 0.0:
                        if allow_short:
                            order_target_size = -reverse_entry_qty
                            order_comment = "SELL REV"
                        else:
                            order_target_size = 0.0
                            order_comment = "Exit Long"
                    else:
                        order_target_size = 0.0
                        order_comment = "Exit Long"

            if in_short and long_signal:
                if disable_fee_filter:
                    if mark_price <= config.max_entry_price and reverse_entry_qty > 0.0:
                        if allow_long:
                            order_target_size = reverse_entry_qty
                            order_comment = "BUY REV"
                        else:
                            order_target_size = 0.0
                            order_comment = "Exit Short"
                    else:
                        order_target_size = 0.0
                        order_comment = "Exit Short"
                elif exit_only_no_reverse or not allow_long:
                    order_target_size = 0.0
                    order_comment = "Exit Short"
                elif hold_until_profitable and reversal_net_filter_passed:
                    if mark_price <= config.max_entry_price and reverse_entry_qty > 0.0:
                        if allow_long:
                            order_target_size = reverse_entry_qty
                            order_comment = "BUY REV"
                        else:
                            order_target_size = 0.0
                            order_comment = "Exit Short"
                    else:
                        order_target_size = 0.0
                        order_comment = "Exit Short"

        # Same-bar close mode, useful for research/backtests that do not want a
        # one-bar execution delay.
        if order_target_size is not None and config.execution == "close":
            old_size, old_avg, realized, realized_costs, realized_net, opened_or_reversed = execute_target_position(
                target_size=order_target_size,
                fill_price=mark_price,
                bar_index=bar_num,
                comment=order_comment,
            )
            if realized_net != 0.0:
                strategy_netprofit += realized_net
                bar_realized_net += realized_net

            raw_bucket = capital_bucket + (strategy_netprofit - processed_netprofit)
            if raw_bucket > config.max_capital_bucket:
                withdrawn_profit += raw_bucket - config.max_capital_bucket
            capital_bucket = _bucket_clamp(raw_bucket, config.max_capital_bucket)
            processed_netprofit = strategy_netprofit

            trades.append(
                {
                    "created_at": idx,
                    "filled_at": idx,
                    "comment": order_comment,
                    "fill_price": mark_price,
                    "old_position_size": old_size,
                    "old_position_avg_price": old_avg,
                    "new_position_size": position_size,
                    "new_position_avg_price": position_avg_price,
                    "realized_gross_pnl": realized,
                    "estimated_costs": realized_costs,
                    "realized_net_pnl": realized_net,
                    "strategy_netprofit": strategy_netprofit,
                    "capital_bucket": capital_bucket,
                    "withdrawn_profit": withdrawn_profit,
                    "opened_or_reversed": opened_or_reversed,
                }
            )
        elif order_target_size is not None:
            pending_target_size = order_target_size
            pending_comment = order_comment
            pending_created_at = idx

        # Re-check early stop after same-bar fills
        if early_stop_drawdown_pct is not None and early_stop_drawdown_pct > 0 and peak_equity > 0:
            current_equity = broker.mark_to_market_equity(mark_price, idx)
            if current_equity > peak_equity:
                peak_equity = current_equity
            drawdown_pct = (peak_equity - current_equity) / peak_equity * 100.0
            if drawdown_pct >= early_stop_drawdown_pct:
                strategy_state = pd.DataFrame(rows, index=enriched.index[:len(rows)])
                enriched = pd.concat([enriched.iloc[:len(rows)], strategy_state], axis=1)
                return enriched, broker.closed_trades_frame()

        if compute_full_metrics:
            rows.append(
                {
                    # Standard columns expected by backtest_engine metrics
                    "realized_net_pnl_on_fill": bar_realized_net,
                    "estimated_net_if_closed_now": estimated_net_if_closed_now_account,
                    "position_size": position_size,
                    "position_avg_price": position_avg_price,
                    # AVT-specific columns
                    "avt_position_size": position_size,
                    "avt_position_avg_price": position_avg_price,
                    "avt_in_long": position_size > 0.0,
                    "avt_in_short": position_size < 0.0,
                    "avt_flat": position_size == 0.0,
                    "avt_bars_in_trade": (
                        bar_num - entry_bar_index if entry_bar_index is not None else 0
                    ),
                    "avt_strategy_netprofit": strategy_netprofit,
                    "avt_capital_bucket": capital_bucket,
                    "avt_withdrawn_profit": withdrawn_profit,
                    "avt_gross_pnl_estimate_account": gross_pnl_estimate_account,
                    "avt_estimated_round_trip_costs_account": estimated_round_trip_costs_account,
                    "avt_estimated_net_if_closed_now_account": estimated_net_if_closed_now_account,
                    "avt_reversal_net_filter_passed": reversal_net_filter_passed,
                    "avt_estimated_bucket_after_close": estimated_bucket_after_close,
                    "avt_entry_position_value_account": entry_position_value_account,
                    "avt_take_profit_net_threshold_account": take_profit_net_threshold_account,
                    "avt_stop_loss_net_threshold_account": stop_loss_net_threshold_account,
                    "avt_safety_max_net_loss_threshold_account": safety_max_net_loss_threshold_account,
                    "avt_safety_loss_triggered": safety_loss_triggered,
                    "avt_safety_bars_triggered": safety_bars_triggered,
                    "avt_safety_stop_triggered": safety_stop_triggered,
                    "avt_hit_net_take_profit": hit_net_take_profit,
                    "avt_hit_net_stop_loss": hit_net_stop_loss,
                    "avt_long_take_profit_price": long_take_profit_price,
                    "avt_long_stop_loss_price": long_stop_loss_price,
                    "avt_short_take_profit_price": short_take_profit_price,
                    "avt_short_stop_loss_price": short_stop_loss_price,
                    "avt_entry_allowed_by_cap": entry_allowed_by_cap,
                    "avt_flat_entry_qty": flat_entry_qty,
                    "avt_reverse_entry_qty": reverse_entry_qty,
                    "avt_order_comment": order_comment if order_target_size is not None else "",
                    "avt_order_target_size": order_target_size,
                    "avt_pending_target_size": pending_target_size,
                    "avt_pending_comment": pending_comment,
                }
            )
        else:
            rows.append(
                {
                    "realized_net_pnl_on_fill": bar_realized_net,
                    "estimated_net_if_closed_now": estimated_net_if_closed_now_account,
                    "position_size": position_size,
                    "position_avg_price": position_avg_price,
                }
            )

    strategy_state = pd.DataFrame(rows, index=enriched.index)
    enriched = pd.concat([enriched, strategy_state], axis=1)

    return enriched, broker.closed_trades_frame()


# Example usage:
#
# import pandas as pd
# from adaptive_volatility_trend_strategy import AVTConfig, add_avt_features, backtest_avt_strategy
#
# df = pd.read_csv("your_ohlcv.csv", parse_dates=["date"]).set_index("date")
# config = AVTConfig(source="close", preset="Default", execution="next_open")
#
# features = add_avt_features(df, config)
# results, trades = backtest_avt_strategy(df, config)
#
# ml_columns = [
#     "avt_adaptive_trend",
#     "avt_upper_band",
#     "avt_lower_band",
#     "avt_trend_dir",
#     "avt_efficiency_ratio",
#     "avt_rsi",
#     "avt_volume_ratio",
#     "avt_confirmed_buy",
#     "avt_confirmed_sell",
#     "avt_last_score",
#     "avt_capital_bucket",
#     "avt_position_size",
# ]
# dataset_for_ml = results[ml_columns].copy()
