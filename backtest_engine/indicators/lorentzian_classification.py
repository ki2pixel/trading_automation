"""Lorentzian Classification KNN Indicator.

Numba-accelerated K-Nearest Neighbors classifier using Lorentzian Distance
for market direction prediction. Converted from the Pine Script by @jdehorty.

Architecture:
    Level 1: Feature computation helpers (@njit)
    Level 2: KNN core + filters + kernel regression (@njit)
    Level 3: VectorBT IndicatorFactory wrapper
"""

import numpy as np
import pandas as pd
import vectorbt as vbt
from numba import njit, prange
import math


# ═══════════════════════════════════════════════════════════════════
# Level 1: Feature Computation Helpers (@njit)
# ═══════════════════════════════════════════════════════════════════

@njit(cache=True)
def calc_ema_nb(arr, length):
    """Exponential Moving Average (EMA) with SMA seed."""
    n = arr.shape[0]
    out = np.full(n, np.nan, dtype=np.float64)
    if length > n or length < 1:
        return out
    alpha = 2.0 / (length + 1)
    seed = 0.0
    for i in range(length):
        seed += arr[i]
    out[length - 1] = seed / length
    for i in range(length, n):
        out[i] = arr[i] * alpha + out[i - 1] * (1.0 - alpha)
    return out


@njit(cache=True)
def calc_rma_nb(arr, length):
    """Wilder's Moving Average (RMA) used in RSI and ATR."""
    n = arr.shape[0]
    out = np.full(n, np.nan, dtype=np.float64)
    if length > n or length < 1:
        return out
    alpha = 1.0 / length
    seed = 0.0
    for i in range(length):
        seed += arr[i]
    out[length - 1] = seed / length
    for i in range(length, n):
        out[i] = arr[i] * alpha + out[i - 1] * (1.0 - alpha)
    return out


@njit(cache=True)
def calc_sma_nb(arr, length):
    """Simple Moving Average."""
    n = arr.shape[0]
    out = np.full(n, np.nan, dtype=np.float64)
    if length > n or length < 1:
        return out
    s = 0.0
    for i in range(length):
        s += arr[i]
    out[length - 1] = s / length
    for i in range(length, n):
        s += arr[i] - arr[i - length]
        out[i] = s / length
    return out


@njit(cache=True)
def calc_rsi_nb(close, length):
    """RSI via Wilder's RMA of gains/losses."""
    n = close.shape[0]
    out = np.full(n, np.nan, dtype=np.float64)
    if length + 1 > n:
        return out

    gains = np.zeros(n, dtype=np.float64)
    losses = np.zeros(n, dtype=np.float64)
    for i in range(1, n):
        delta = close[i] - close[i - 1]
        if delta > 0.0:
            gains[i] = delta
        else:
            losses[i] = -delta

    avg_gain = calc_rma_nb(gains[1:], length)
    avg_loss = calc_rma_nb(losses[1:], length)

    for i in range(avg_gain.shape[0]):
        if not np.isnan(avg_gain[i]) and not np.isnan(avg_loss[i]):
            ag = avg_gain[i]
            al = avg_loss[i]
            if al == 0.0:
                out[i + 1] = 100.0
            else:
                rs = ag / al
                out[i + 1] = 100.0 - 100.0 / (1.0 + rs)
    return out


@njit(cache=True)
def calc_cci_nb(close, high, low, length):
    """Commodity Channel Index."""
    n = close.shape[0]
    out = np.full(n, np.nan, dtype=np.float64)
    if length > n or length < 1:
        return out

    tp = (high + low + close) / 3.0

    sma_tp = calc_sma_nb(tp, length)

    for i in range(length - 1, n):
        mean_val = sma_tp[i]
        if np.isnan(mean_val):
            continue
        mean_dev = 0.0
        for j in range(length):
            mean_dev += abs(tp[i - j] - mean_val)
        mean_dev /= length
        if mean_dev == 0.0:
            out[i] = 0.0
        else:
            out[i] = (tp[i] - mean_val) / (0.015 * mean_dev)
    return out


@njit(cache=True)
def calc_adx_nb(high, low, close, length):
    """Average Directional Index (ADX)."""
    n = close.shape[0]
    out = np.full(n, np.nan, dtype=np.float64)
    if length + 1 > n:
        return out

    plus_dm = np.zeros(n, dtype=np.float64)
    minus_dm = np.zeros(n, dtype=np.float64)
    tr = np.zeros(n, dtype=np.float64)

    for i in range(1, n):
        up_move = high[i] - high[i - 1]
        down_move = low[i - 1] - low[i]
        if up_move > down_move and up_move > 0.0:
            plus_dm[i] = up_move
        if down_move > up_move and down_move > 0.0:
            minus_dm[i] = down_move

        hl = high[i] - low[i]
        hc = abs(high[i] - close[i - 1])
        lc = abs(low[i] - close[i - 1])
        tr[i] = max(hl, max(hc, lc))

    smooth_plus_dm = calc_rma_nb(plus_dm[1:], length)
    smooth_minus_dm = calc_rma_nb(minus_dm[1:], length)
    smooth_tr = calc_rma_nb(tr[1:], length)

    dx = np.zeros(smooth_tr.shape[0], dtype=np.float64)
    for i in range(smooth_tr.shape[0]):
        if np.isnan(smooth_tr[i]) or smooth_tr[i] == 0.0:
            continue
        plus_di = 100.0 * smooth_plus_dm[i] / smooth_tr[i]
        minus_di = 100.0 * smooth_minus_dm[i] / smooth_tr[i]
        di_sum = plus_di + minus_di
        if di_sum == 0.0:
            dx[i] = 0.0
        else:
            dx[i] = 100.0 * abs(plus_di - minus_di) / di_sum

    adx_rma = calc_rma_nb(dx, length)
    for i in range(adx_rma.shape[0]):
        if not np.isnan(adx_rma[i]):
            out[i + 1] = adx_rma[i]
    return out


@njit(cache=True)
def calc_wt_nb(hlc3, len1, len2):
    """WaveTrend oscillator."""
    esa = calc_ema_nb(hlc3, len1)

    n = hlc3.shape[0]
    d_raw = np.zeros(n, dtype=np.float64)
    for i in range(n):
        if not np.isnan(esa[i]):
            d_raw[i] = abs(hlc3[i] - esa[i])
    d = calc_ema_nb(d_raw, len1)

    ci = np.zeros(n, dtype=np.float64)
    for i in range(n):
        if not np.isnan(esa[i]) and not np.isnan(d[i]) and d[i] != 0.0:
            ci[i] = (hlc3[i] - esa[i]) / (0.015 * d[i])
        elif not np.isnan(esa[i]):
            ci[i] = 0.0

    tci = calc_ema_nb(ci, len2)
    return tci


@njit(cache=True)
def get_linear_interpolation(src, old_max, lookback):
    """Min-max normalization over a rolling window (causal).

    Implements the Pine Script ``get_Linear_interpolation`` function:
        minVal = ta.lowest(src, lookback)
        normalized = (src - minVal) / (oldMax - minVal)
    """
    n = src.shape[0]
    out = np.full(n, np.nan, dtype=np.float64)
    for i in range(n):
        start = max(0, i - lookback + 1)
        min_val = src[start]
        for j in range(start + 1, i + 1):
            if src[j] < min_val:
                min_val = src[j]
        denom = old_max - min_val
        if denom == 0.0:
            out[i] = 0.0
        else:
            out[i] = (src[i] - min_val) / denom
    return out


@njit(cache=True)
def n_rsi(close, len1, len2):
    """Normalized RSI: get_linear_interpolation(EMA(RSI(close, len1), len2), 100)."""
    rsi = calc_rsi_nb(close, len1)
    # Replace NaN with 50.0 for EMA seed stability
    for i in range(rsi.shape[0]):
        if np.isnan(rsi[i]):
            rsi[i] = 50.0
    ema_rsi = calc_ema_nb(rsi, len2)
    return get_linear_interpolation(ema_rsi, 100.0, 100)


@njit(cache=True)
def n_wt(hlc3, len1, len2):
    """Normalized WaveTrend: get_linear_interpolation(calc_wt(hlc3, len1, len2), 100)."""
    wt = calc_wt_nb(hlc3, len1, len2)
    for i in range(wt.shape[0]):
        if np.isnan(wt[i]):
            wt[i] = 0.0
    return get_linear_interpolation(wt, 100.0, 100)


@njit(cache=True)
def n_cci(close, high, low, len1, len2):
    """Normalized CCI: get_linear_interpolation(EMA(CCI(close, len1), len2), 300)."""
    cci = calc_cci_nb(close, high, low, len1)
    for i in range(cci.shape[0]):
        if np.isnan(cci[i]):
            cci[i] = 0.0
    ema_cci = calc_ema_nb(cci, len2)
    return get_linear_interpolation(ema_cci, 300.0, 100)


@njit(cache=True)
def n_adx(high, low, close, len1):
    """Normalized ADX: get_linear_interpolation(ADX(len1), 100)."""
    adx = calc_adx_nb(high, low, close, len1)
    for i in range(adx.shape[0]):
        if np.isnan(adx[i]):
            adx[i] = 0.0
    return get_linear_interpolation(adx, 100.0, 100)


# ═══════════════════════════════════════════════════════════════════
# Level 2: KNN Core + Filters + Kernel Regression (@njit)
# ═══════════════════════════════════════════════════════════════════

@njit(cache=True)
def _rational_quadratic_kernel(src, lookback, relative_weight, start_bar):
    """Nadaraya-Watson Rational Quadratic Kernel Regression.

    K(x) = (1 + x^2 / (2 * r * h^2))^(-r)
    """
    n = src.shape[0]
    out = np.full(n, np.nan, dtype=np.float64)
    for t in range(n):
        num = 0.0
        den = 0.0
        for i in range(start_bar):
            if t - i < 0:
                break
            x_val = float(i)
            w = (1.0 + (x_val * x_val) / (2.0 * relative_weight * lookback * lookback))
            w = w ** (-relative_weight)
            num += src[t - i] * w
            den += w
        if den > 0.0:
            out[t] = num / den
    return out


@njit(cache=True)
def _gaussian_kernel(src, lookback, start_bar):
    """Nadaraya-Watson Gaussian Kernel Regression.

    K(x) = exp(-x^2 / (2 * h^2))
    """
    n = src.shape[0]
    out = np.full(n, np.nan, dtype=np.float64)
    h2 = 2.0 * lookback * lookback
    for t in range(n):
        num = 0.0
        den = 0.0
        for i in range(start_bar):
            if t - i < 0:
                break
            x_val = float(i)
            w = math.exp(-(x_val * x_val) / h2)
            num += src[t - i] * w
            den += w
        if den > 0.0:
            out[t] = num / den
    return out


@njit(cache=True)
def _volatility_filter_nb(high, low, close, min_len, max_len):
    """Volatility filter: recent ATR vs historical ATR.

    Pine: ml.filter_volatility(1, 10, useVolatilityFilter)
    Returns True when recent volatility exceeds long-term average.
    """
    n = close.shape[0]
    out = np.ones(n, dtype=np.int64)

    # ATR computation
    tr = np.zeros(n, dtype=np.float64)
    for i in range(1, n):
        hl = high[i] - low[i]
        hc = abs(high[i] - close[i - 1])
        lc = abs(low[i] - close[i - 1])
        tr[i] = max(hl, max(hc, lc))

    recent_atr = calc_rma_nb(tr, min_len)
    hist_atr = calc_rma_nb(tr, max_len)

    for i in range(n):
        if not np.isnan(recent_atr[i]) and not np.isnan(hist_atr[i]):
            out[i] = 1 if recent_atr[i] > hist_atr[i] else 0
    return out


@njit(cache=True)
def _regime_filter_nb(ohlc4, threshold):
    """Regime filter using slope of SMA(ohlc4).

    Pine: ml.regime_filter(ohlc4, threshold, useRegimeFilter)
    Klinger-style: calculates if the market is trending or ranging.
    """
    n = ohlc4.shape[0]
    out = np.ones(n, dtype=np.int64)

    # Use a simple slope-based regime detection
    klinger = calc_sma_nb(ohlc4, 10)

    for i in range(1, n):
        if not np.isnan(klinger[i]) and not np.isnan(klinger[i - 1]):
            slope = (klinger[i] - klinger[i - 1]) / klinger[i - 1] if klinger[i - 1] != 0.0 else 0.0
            out[i] = 1 if slope > threshold else 0
    return out


@njit(cache=True)
def _adx_filter_nb(high, low, close, length, threshold):
    """ADX filter: ADX > threshold means trending."""
    adx = calc_adx_nb(high, low, close, length)
    n = close.shape[0]
    out = np.ones(n, dtype=np.int64)
    for i in range(n):
        if not np.isnan(adx[i]):
            out[i] = 1 if adx[i] > threshold else 0
    return out
@njit(cache=True, parallel=True)
def _compute_knn_predictions_parallel(
    f1, f2, f3, f4, f5, y_train, neighbors_count, max_bars_back
):
    """
    Parallel execution of the KNN ANN logic using Numba prange.
    Computes distances with Early Abandoning (Short-circuit).
    """
    n = f1.shape[0]
    out_prediction = np.zeros(n, dtype=np.float64)
    
    for t in prange(5, n):
        last_distance = -1.0
        buf_size = 0
        dist_buf = np.zeros(neighbors_count + 1, dtype=np.float64)
        pred_buf = np.zeros(neighbors_count + 1, dtype=np.int64)
        
        start_idx = max(0, t - max_bars_back)
        
        for j in range(start_idx, t):
            i = j - start_idx
            
            # Early Abandoning
            if (i % 4) == 0:
                d = (
                    math.log1p(abs(f1[t] - f1[j])) +
                    math.log1p(abs(f2[t] - f2[j])) +
                    math.log1p(abs(f3[t] - f3[j])) +
                    math.log1p(abs(f4[t] - f4[j])) +
                    math.log1p(abs(f5[t] - f5[j]))
                )
            else:
                d = math.log1p(abs(f1[t] - f1[j]))
                if d >= last_distance: continue
                d += math.log1p(abs(f2[t] - f2[j]))
                if d >= last_distance: continue
                d += math.log1p(abs(f3[t] - f3[j]))
                if d >= last_distance: continue
                d += math.log1p(abs(f4[t] - f4[j]))
                if d >= last_distance: continue
                d += math.log1p(abs(f5[t] - f5[j]))
                if d >= last_distance: continue

            last_distance = max(d, last_distance)

            # Insertion sort into buffer
            pos = buf_size
            while pos > 0 and dist_buf[pos - 1] > d:
                dist_buf[pos] = dist_buf[pos - 1]
                pred_buf[pos] = pred_buf[pos - 1]
                pos -= 1
            dist_buf[pos] = d
            pred_buf[pos] = y_train[j]
            buf_size += 1
            
            if buf_size > neighbors_count:
                idx_75 = int(round((neighbors_count + 1) * 0.75)) - 1
                idx_75 = max(0, min(idx_75, buf_size - 1))
                last_distance = dist_buf[idx_75]
                buf_size -= 1

        prediction = 0.0
        for k in range(buf_size):
            prediction += float(pred_buf[k])
            
        out_prediction[t] = prediction

    return out_prediction


@njit(cache=True)
def _lorentzian_knn_1d_nb(
    close, high, low, ohlc4,
    f1, f2, f3, f4, f5,
    feature_count, neighbors_count, max_bars_back,
    # Filter arrays (pre-computed)
    vol_filter, regime_filter, adx_filter,
    use_vol_filter, use_regime_filter, use_adx_filter,
    # EMA/SMA filter
    ema_arr, sma_arr, use_ema_filter, use_sma_filter,
    # Kernel parameters
    yhat1, yhat2,
    use_kernel_filter, use_kernel_smoothing,
    # Exit parameters
    use_dynamic_exits,
):
    """Core KNN Lorentzian Classification loop (1D).

    Implements the Approximate Nearest Neighbors algorithm from the Pine Script
    (lines 383-398) with all filters and signal generation.
    """
    n = close.shape[0]

    out_prediction = np.zeros(n, dtype=np.float64)
    out_signal = np.zeros(n, dtype=np.int64)
    out_start_long = np.zeros(n, dtype=np.int64)
    out_start_short = np.zeros(n, dtype=np.int64)
    out_end_long = np.zeros(n, dtype=np.int64)
    out_end_short = np.zeros(n, dtype=np.int64)

    # y_train: label at bar t = sign(close[t] - close[t-4])
    y_train = np.zeros(n, dtype=np.int64)
    for i in range(4, n):
        if close[i] > close[i - 4]:
            y_train[i] = 1
        elif close[i] < close[i - 4]:
            y_train[i] = -1
        else:
            y_train[i] = 0

    # Run parallel KNN engine
    out_prediction = _compute_knn_predictions_parallel(
        f1, f2, f3, f4, f5, y_train, neighbors_count, max_bars_back
    )

    # State variables
    signal = 0  # 0=neutral, 1=long, -1=short
    bars_held = 0
    prev_signal = 0

    # Track signal history for fractal filters (need signal[t-1], signal[t-2], signal[t-3], signal[t-4])
    signal_hist = np.zeros(5, dtype=np.int64)

    # barssince trackers
    bars_since_long_entry = 99999
    bars_since_short_entry = 99999
    bars_since_bullish_alert = 99999
    bars_since_bearish_alert = 99999

    for t in range(n):
        # ─── Combined filter ───
        filter_all = True
        if use_vol_filter and vol_filter[t] == 0:
            filter_all = False
        if use_regime_filter and regime_filter[t] == 0:
            filter_all = False
        if use_adx_filter and adx_filter[t] == 0:
            filter_all = False

        # ─── EMA/SMA trend filters ───
        is_ema_uptrend = True
        is_ema_downtrend = True
        if use_ema_filter and not np.isnan(ema_arr[t]):
            is_ema_uptrend = close[t] > ema_arr[t]
            is_ema_downtrend = close[t] < ema_arr[t]

        is_sma_uptrend = True
        is_sma_downtrend = True
        if use_sma_filter and not np.isnan(sma_arr[t]):
            is_sma_uptrend = close[t] > sma_arr[t]
            is_sma_downtrend = close[t] < sma_arr[t]

        prediction = out_prediction[t]

        # ─── Signal generation ───
        if prediction > 0.0 and filter_all:
            signal = 1
        elif prediction < 0.0 and filter_all:
            signal = -1
        # else: keep previous signal (nz(signal[1]))

        out_signal[t] = signal

        # ─── Bar count tracking ───
        if signal != prev_signal:
            bars_held = 0
        else:
            bars_held += 1

        is_held_four_bars = bars_held == 4
        is_held_less_than_four = 0 < bars_held < 4
        is_different_signal = signal != prev_signal

        # ─── Kernel-based filters ───
        is_bullish_rate = True
        is_bearish_rate = True
        is_bullish_change = False
        is_bearish_change = False
        is_bullish_smooth = True
        is_bearish_smooth = True
        is_bullish_cross = False
        is_bearish_cross = False

        if t >= 2 and not np.isnan(yhat1[t]) and not np.isnan(yhat1[t - 1]) and not np.isnan(yhat1[t - 2]):
            was_bearish_rate = yhat1[t - 2] > yhat1[t - 1]
            was_bullish_rate = yhat1[t - 2] < yhat1[t - 1]
            is_bearish_rate = yhat1[t - 1] > yhat1[t]
            is_bullish_rate = yhat1[t - 1] < yhat1[t]
            is_bearish_change = is_bearish_rate and was_bullish_rate
            is_bullish_change = is_bullish_rate and was_bearish_rate

        if not np.isnan(yhat1[t]) and not np.isnan(yhat2[t]):
            is_bullish_smooth = yhat2[t] >= yhat1[t]
            is_bearish_smooth = yhat2[t] <= yhat1[t]
            # Crossover detection
            if t >= 1 and not np.isnan(yhat1[t - 1]) and not np.isnan(yhat2[t - 1]):
                is_bullish_cross = yhat2[t] >= yhat1[t] and yhat2[t - 1] < yhat1[t - 1]
                is_bearish_cross = yhat2[t] <= yhat1[t] and yhat2[t - 1] > yhat1[t - 1]

        # Alert variables
        if use_kernel_smoothing:
            alert_bullish = is_bullish_cross
            alert_bearish = is_bearish_cross
        else:
            alert_bullish = is_bullish_change
            alert_bearish = is_bearish_change

        # Kernel direction
        if use_kernel_filter:
            if use_kernel_smoothing:
                is_bullish = is_bullish_smooth
                is_bearish = is_bearish_smooth
            else:
                is_bullish = is_bullish_rate
                is_bearish = is_bearish_rate
        else:
            is_bullish = True
            is_bearish = True

        # ─── Buy/Sell signal conditions ───
        is_buy_signal = signal == 1 and is_ema_uptrend and is_sma_uptrend
        is_sell_signal = signal == -1 and is_ema_downtrend and is_sma_downtrend
        is_new_buy = is_buy_signal and is_different_signal
        is_new_sell = is_sell_signal and is_different_signal

        # ─── Entry conditions ───
        start_long = is_new_buy and is_bullish and is_ema_uptrend and is_sma_uptrend
        start_short = is_new_sell and is_bearish and is_ema_downtrend and is_sma_downtrend

        # ─── Exit conditions ───
        # Dynamic exits (kernel-based)
        is_valid_long_exit = bars_since_bearish_alert > bars_since_long_entry
        is_valid_short_exit = bars_since_bullish_alert > bars_since_short_entry
        end_long_dynamic = is_bearish_change and (is_valid_long_exit if t >= 1 else False)
        end_short_dynamic = is_bullish_change and (is_valid_short_exit if t >= 1 else False)

        # Fixed exits (4 bar hold)
        is_last_buy = signal_hist[4] == 1 if t >= 4 else False
        is_last_sell = signal_hist[4] == -1 if t >= 4 else False

        end_long_strict = False
        end_short_strict = False
        if t >= 4:
            end_long_strict = ((is_held_four_bars and is_last_buy) or
                               (is_held_less_than_four and is_new_sell and is_last_buy))
            end_short_strict = ((is_held_four_bars and is_last_sell) or
                                (is_held_less_than_four and is_new_buy and is_last_sell))

        # Choose exit mode
        is_dynamic_valid = not use_ema_filter and not use_sma_filter and not use_kernel_smoothing
        if use_dynamic_exits and is_dynamic_valid:
            end_long = end_long_dynamic
            end_short = end_short_dynamic
        else:
            end_long = end_long_strict
            end_short = end_short_strict

        out_start_long[t] = 1 if start_long else 0
        out_start_short[t] = 1 if start_short else 0
        out_end_long[t] = 1 if end_long else 0
        out_end_short[t] = 1 if end_short else 0

        # ─── Update trackers ───
        if start_long:
            bars_since_long_entry = 0
        else:
            bars_since_long_entry += 1

        if start_short:
            bars_since_short_entry = 0
        else:
            bars_since_short_entry += 1

        if alert_bullish:
            bars_since_bullish_alert = 0
        else:
            bars_since_bullish_alert += 1

        if alert_bearish:
            bars_since_bearish_alert = 0
        else:
            bars_since_bearish_alert += 1

        # Shift signal history
        for k in range(4, 0, -1):
            signal_hist[k] = signal_hist[k - 1]
        signal_hist[0] = signal

        prev_signal = signal

    return (out_prediction, out_signal,
            out_start_long, out_start_short,
            out_end_long, out_end_short)


@njit(cache=True)
def _lorentzian_knn_2d_nb(
    close, high, low, ohlc4,
    f1, f2, f3, f4, f5,
    feature_count, neighbors_count, max_bars_back,
    vol_filter, regime_filter, adx_filter,
    use_vol_filter, use_regime_filter, use_adx_filter,
    ema_arr, sma_arr, use_ema_filter, use_sma_filter,
    yhat1, yhat2,
    use_kernel_filter, use_kernel_smoothing,
    use_dynamic_exits,
):
    """2D wrapper: iterates over columns for multi-symbol support."""
    n_rows = close.shape[0]
    n_cols = close.shape[1]

    all_prediction = np.empty((n_rows, n_cols), dtype=np.float64)
    all_signal = np.empty((n_rows, n_cols), dtype=np.int64)
    all_start_long = np.empty((n_rows, n_cols), dtype=np.int64)
    all_start_short = np.empty((n_rows, n_cols), dtype=np.int64)
    all_end_long = np.empty((n_rows, n_cols), dtype=np.int64)
    all_end_short = np.empty((n_rows, n_cols), dtype=np.int64)

    for col in range(n_cols):
        pred, sig, sl, ss, el, es = _lorentzian_knn_1d_nb(
            close[:, col], high[:, col], low[:, col], ohlc4[:, col],
            f1[:, col], f2[:, col], f3[:, col], f4[:, col], f5[:, col],
            feature_count, neighbors_count, max_bars_back,
            vol_filter[:, col], regime_filter[:, col], adx_filter[:, col],
            use_vol_filter, use_regime_filter, use_adx_filter,
            ema_arr[:, col], sma_arr[:, col], use_ema_filter, use_sma_filter,
            yhat1[:, col], yhat2[:, col],
            use_kernel_filter, use_kernel_smoothing,
            use_dynamic_exits,
        )
        all_prediction[:, col] = pred
        all_signal[:, col] = sig
        all_start_long[:, col] = sl
        all_start_short[:, col] = ss
        all_end_long[:, col] = el
        all_end_short[:, col] = es

    return (all_prediction, all_signal,
            all_start_long, all_start_short,
            all_end_long, all_end_short)


# ═══════════════════════════════════════════════════════════════════
# Level 3: VectorBT IndicatorFactory Wrapper
# ═══════════════════════════════════════════════════════════════════

def apply_lorentzian_classification(
    high, low, close,
    neighbors_count, max_bars_back, feature_count,
    f1_param_a, f1_param_b, f2_param_a, f2_param_b,
    f3_param_a, f3_param_b, f4_param_a, f4_param_b,
    f5_param_a, f5_param_b,
    use_volatility_filter, use_regime_filter, regime_threshold,
    use_adx_filter, adx_threshold,
    use_ema_filter, ema_period, use_sma_filter, sma_period,
    use_kernel_filter, kernel_h, kernel_r, kernel_x,
    kernel_lag, use_kernel_smoothing, use_dynamic_exits,
):
    """Apply function for VectorBT IndicatorFactory.

    Pre-computes features vectorized, then delegates to the Numba KNN kernel.
    """
    high = np.asarray(high, dtype=np.float64)
    low = np.asarray(low, dtype=np.float64)
    close = np.asarray(close, dtype=np.float64)

    is_1d = close.ndim == 1
    if is_1d:
        high = high.reshape(-1, 1)
        low = low.reshape(-1, 1)
        close = close.reshape(-1, 1)

    n_rows, n_cols = close.shape
    hlc3 = (high + low + close) / 3.0
    ohlc4 = (high + low + close + close) / 4.0  # Approximation: no open available

    # Coerce parameters
    neighbors_count = int(neighbors_count)
    max_bars_back = int(max_bars_back)
    feature_count = int(feature_count)
    f1_pa = int(f1_param_a)
    f1_pb = int(f1_param_b)
    f2_pa = int(f2_param_a)
    f2_pb = int(f2_param_b)
    f3_pa = int(f3_param_a)
    f3_pb = int(f3_param_b)
    f4_pa = int(f4_param_a)
    f4_pb = int(f4_param_b)
    f5_pa = int(f5_param_a)
    f5_pb = int(f5_param_b)
    use_vf = bool(use_volatility_filter)
    use_rf = bool(use_regime_filter)
    use_af = bool(use_adx_filter)
    use_ef = bool(use_ema_filter)
    use_sf = bool(use_sma_filter)
    use_kf = bool(use_kernel_filter)
    use_ks = bool(use_kernel_smoothing)
    use_de = bool(use_dynamic_exits)
    k_h = int(kernel_h)
    k_r = float(kernel_r)
    k_x = int(kernel_x)
    k_lag = int(kernel_lag)

    # Pre-compute features per column
    all_f1 = np.zeros((n_rows, n_cols), dtype=np.float64)
    all_f2 = np.zeros((n_rows, n_cols), dtype=np.float64)
    all_f3 = np.zeros((n_rows, n_cols), dtype=np.float64)
    all_f4 = np.zeros((n_rows, n_cols), dtype=np.float64)
    all_f5 = np.zeros((n_rows, n_cols), dtype=np.float64)

    # Pre-compute filter arrays
    all_vol_filter = np.ones((n_rows, n_cols), dtype=np.int64)
    all_regime_filter = np.ones((n_rows, n_cols), dtype=np.int64)
    all_adx_filter = np.ones((n_rows, n_cols), dtype=np.int64)

    # Pre-compute EMA/SMA
    all_ema = np.full((n_rows, n_cols), np.nan, dtype=np.float64)
    all_sma = np.full((n_rows, n_cols), np.nan, dtype=np.float64)

    # Pre-compute kernel regression
    all_yhat1 = np.full((n_rows, n_cols), np.nan, dtype=np.float64)
    all_yhat2 = np.full((n_rows, n_cols), np.nan, dtype=np.float64)

    for c in range(n_cols):
        c_close = close[:, c]
        c_high = high[:, c]
        c_low = low[:, c]
        c_hlc3 = hlc3[:, c]
        c_ohlc4 = ohlc4[:, c]

        # Feature 1: RSI (default: 14, 1)
        all_f1[:, c] = n_rsi(c_close, f1_pa, f1_pb)
        # Feature 2: WaveTrend (default: 10, 11)
        all_f2[:, c] = n_wt(c_hlc3, f2_pa, f2_pb)
        # Feature 3: CCI (default: 20, 1)
        all_f3[:, c] = n_cci(c_close, c_high, c_low, f3_pa, f3_pb)
        # Feature 4: ADX (default: 20, paramB unused)
        all_f4[:, c] = n_adx(c_high, c_low, c_close, f4_pa)
        # Feature 5: RSI (default: 9, 1)
        all_f5[:, c] = n_rsi(c_close, f5_pa, f5_pb)

        # Filters
        if use_vf:
            all_vol_filter[:, c] = _volatility_filter_nb(c_high, c_low, c_close, 1, 10)
        if use_rf:
            all_regime_filter[:, c] = _regime_filter_nb(c_ohlc4, float(regime_threshold))
        if use_af:
            all_adx_filter[:, c] = _adx_filter_nb(c_high, c_low, c_close, 14, float(adx_threshold))

        # EMA/SMA
        if use_ef:
            all_ema[:, c] = calc_ema_nb(c_close, int(ema_period))
        if use_sf:
            all_sma[:, c] = calc_sma_nb(c_close, int(sma_period))

        # Kernel regression
        all_yhat1[:, c] = _rational_quadratic_kernel(c_close, float(k_h), float(k_r), k_x)
        all_yhat2[:, c] = _gaussian_kernel(c_close, float(k_h - k_lag), k_x)

    # Run KNN
    if n_cols == 1 and is_1d:
        prediction, signal, sl, ss, el, es = _lorentzian_knn_1d_nb(
            close[:, 0], high[:, 0], low[:, 0], ohlc4[:, 0],
            all_f1[:, 0], all_f2[:, 0], all_f3[:, 0], all_f4[:, 0], all_f5[:, 0],
            feature_count, neighbors_count, max_bars_back,
            all_vol_filter[:, 0], all_regime_filter[:, 0], all_adx_filter[:, 0],
            use_vf, use_rf, use_af,
            all_ema[:, 0], all_sma[:, 0], use_ef, use_sf,
            all_yhat1[:, 0], all_yhat2[:, 0],
            use_kf, use_ks,
            use_de,
        )
    else:
        prediction, signal, sl, ss, el, es = _lorentzian_knn_2d_nb(
            close, high, low, ohlc4,
            all_f1, all_f2, all_f3, all_f4, all_f5,
            feature_count, neighbors_count, max_bars_back,
            all_vol_filter, all_regime_filter, all_adx_filter,
            use_vf, use_rf, use_af,
            all_ema, all_sma, use_ef, use_sf,
            all_yhat1, all_yhat2,
            use_kf, use_ks,
            use_de,
        )

    return prediction, signal, sl, ss, el, es


LorentzianClassification = vbt.IndicatorFactory(
    class_name="LorentzianClassification",
    short_name="ldc",
    input_names=["high", "low", "close"],
    param_names=[
        "neighbors_count", "max_bars_back", "feature_count",
        "f1_param_a", "f1_param_b", "f2_param_a", "f2_param_b",
        "f3_param_a", "f3_param_b", "f4_param_a", "f4_param_b",
        "f5_param_a", "f5_param_b",
        "use_volatility_filter", "use_regime_filter", "regime_threshold",
        "use_adx_filter", "adx_threshold",
        "use_ema_filter", "ema_period", "use_sma_filter", "sma_period",
        "use_kernel_filter", "kernel_h", "kernel_r", "kernel_x",
        "kernel_lag", "use_kernel_smoothing", "use_dynamic_exits",
    ],
    output_names=[
        "prediction", "signal",
        "start_long", "start_short",
        "end_long", "end_short",
    ],
).from_apply_func(
    apply_lorentzian_classification,
    neighbors_count=8,
    max_bars_back=2000,
    feature_count=5,
    f1_param_a=14,   # RSI length
    f1_param_b=1,    # RSI EMA smoothing
    f2_param_a=10,   # WT channel length
    f2_param_b=11,   # WT average length
    f3_param_a=20,   # CCI length
    f3_param_b=1,    # CCI EMA smoothing
    f4_param_a=20,   # ADX length
    f4_param_b=2,    # ADX (unused, kept for consistency)
    f5_param_a=9,    # RSI2 length
    f5_param_b=1,    # RSI2 EMA smoothing
    use_volatility_filter=True,
    use_regime_filter=True,
    regime_threshold=-0.1,
    use_adx_filter=False,
    adx_threshold=20,
    use_ema_filter=False,
    ema_period=200,
    use_sma_filter=False,
    sma_period=200,
    use_kernel_filter=True,
    kernel_h=8,
    kernel_r=8.0,
    kernel_x=25,
    kernel_lag=2,
    use_kernel_smoothing=False,
    use_dynamic_exits=False,
    keep_pd=True,
)
