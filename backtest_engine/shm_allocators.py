"""
backtest_engine/shm_allocators.py

Délégation de l'allocation des mémoires partagées POSIX (SharedIndicatorVolume)
pour chaque stratégie. L'objectif est de réduire la complexité cognitive du 
Bayesian Optimizer principal.
"""

import logging
import numpy as np
import pandas as pd
from typing import Any

from .shared_memory import SharedIndicatorVolume

logger = logging.getLogger(__name__)

def _get_fixed_val(fixed_overrides, name, default):
    if fixed_overrides and hasattr(fixed_overrides, name):
        val = getattr(fixed_overrides, name)
        if val is not None:
            return val
    return default

def _get_dynamic_memory_limit() -> int:
    from .bayesian_optimizer import _get_dynamic_memory_limit as get_mem
    return get_mem()

def _allocate_hma_crossover(data, parameter_specs, fixed_overrides, workers, shm_objects):
    hma_shm_metadata = None
    fast_specs = next((s for s in parameter_specs if s.name == "fast_len"), None)
    slow_specs = next((s for s in parameter_specs if s.name == "slow_len"), None)
    fast_vals = list(fast_specs.values) if (fast_specs and fast_specs.values) else [_get_fixed_val(fixed_overrides, "fast_len", 20)]
    slow_vals = list(slow_specs.values) if (slow_specs and slow_specs.values) else [_get_fixed_val(fixed_overrides, "slow_len", 50)]
    
    if fast_vals and slow_vals:
        from .strategies.hma_crossover import _load_strategy_module
        strategy_mod = _load_strategy_module()
        hma_func = strategy_mod.hma
        import gc as _gc
        
        unique_lengths = sorted(list(set(fast_vals) | set(slow_vals)))
        length_to_idx = {int(length): i for i, length in enumerate(unique_lengths)}

        estimated_bytes = len(unique_lengths) * len(data) * 8
        max_memory_limit = _get_dynamic_memory_limit()
        if estimated_bytes > max_memory_limit:
            logger.warning(
                f"Shared memory grid for HMA Crossover is too large "
                f"({estimated_bytes / (1024**2):.1f} MB, "
                f"limit: {max_memory_limit / (1024**2):.1f} MB). "
                f"Skipping precalculation and falling back to on-the-fly "
                f"calculation to protect system memory."
            )
        else:
            close_series = data["close"]
            hma_grid_arr = np.zeros((len(unique_lengths), len(data)), dtype=np.float64)
            for i, length in enumerate(unique_lengths):
                hma_grid_arr[i] = hma_func(close_series, length).values

            hma_shm = SharedIndicatorVolume(array_to_share=hma_grid_arr)
            shm_objects.append(hma_shm)

            hma_shm_metadata = {
                "shm_name": hma_shm.shm_name,
                "shape": hma_shm.shape,
                "dtype": str(hma_shm.dtype),
                "length_to_idx": length_to_idx
            }

            try:
                if workers > 1:
                    strategy_mod._SHARED_HMA_GRID = hma_shm.get_view()
                    strategy_mod._SHARED_HMA_LENGTH_TO_IDX = length_to_idx
                    del hma_grid_arr
                    _gc.collect()
                else:
                    strategy_mod._SHARED_HMA_GRID = hma_grid_arr
                    strategy_mod._SHARED_HMA_LENGTH_TO_IDX = length_to_idx
            except Exception as e:
                logger.debug(f"Failed to mount local parent HMA grid: {e}")
                
    return hma_shm_metadata

def _allocate_pmax_explorer(data, parameter_specs, fixed_overrides, workers, shm_objects):
    pmax_shm_metadata = None
    periods_specs = next((s for s in parameter_specs if s.name == "periods"), None)
    length_specs = next((s for s in parameter_specs if s.name == "length"), None)
    mav_specs = next((s for s in parameter_specs if s.name == "mav"), None)
    change_atr_specs = next((s for s in parameter_specs if s.name == "change_atr"), None)

    periods_vals = list(periods_specs.values) if (periods_specs and periods_specs.values) else [_get_fixed_val(fixed_overrides, "periods", 10)]
    length_vals = list(length_specs.values) if (length_specs and length_specs.values) else [_get_fixed_val(fixed_overrides, "length", 10)]
    mav_vals = list(mav_specs.values) if (mav_specs and mav_specs.values) else [_get_fixed_val(fixed_overrides, "mav", "EMA")]
    change_atr_vals = list(change_atr_specs.values) if (change_atr_specs and change_atr_specs.values) else [_get_fixed_val(fixed_overrides, "change_atr", True)]

    from .strategies.pmax_explorer import _load_strategy_module
    strategy_mod = _load_strategy_module()
    
    source_col = fixed_overrides.source_col if (fixed_overrides and hasattr(fixed_overrides, "source_col") and fixed_overrides.source_col) else "hl2"
    if source_col == "hl2" and "hl2" not in data.columns:
        hl2_series = (data["high"] + data["low"]) / 2.0
    else:
        hl2_series = data[source_col] if source_col in data.columns else data["close"]
    
    src_arr = hl2_series.to_numpy(dtype=float)
    high_arr = data["high"].to_numpy(dtype=float)
    low_arr = data["low"].to_numpy(dtype=float)
    close_arr = data["close"].to_numpy(dtype=float)

    mavg_combos = []
    for mav in mav_vals:
        for length in length_vals:
            mavg_combos.append((str(mav), int(length)))
    mavg_keys = {combo: i for i, combo in enumerate(mavg_combos)}

    atr_combos = []
    for periods in periods_vals:
        for change_atr in change_atr_vals:
            atr_combos.append((int(periods), bool(change_atr)))
    atr_keys = {combo: i for i, combo in enumerate(atr_combos)}

    estimated_bytes = (len(mavg_combos) + len(atr_combos)) * len(data) * 8
    max_memory_limit = _get_dynamic_memory_limit()
    if estimated_bytes > max_memory_limit:
        logger.warning(
            f"Shared memory grids for PMax Explorer are too large ({estimated_bytes / (1024**2):.1f} MB). "
            f"Skipping precalculation to protect system memory."
        )
    else:
        mavg_grid_arr = np.zeros((len(mavg_combos), len(data)), dtype=np.float64)
        for combo, idx in mavg_keys.items():
            mav_type, length = combo
            if mav_type == "SMA":
                mavg_grid_arr[idx] = strategy_mod.pine_sma(src_arr, length)
            elif mav_type == "EMA":
                mavg_grid_arr[idx] = strategy_mod.pine_ema(src_arr, length)
            elif mav_type == "WMA":
                mavg_grid_arr[idx] = strategy_mod.pine_wma(src_arr, length)
            elif mav_type == "TMA":
                mavg_grid_arr[idx] = strategy_mod.pine_tma(src_arr, length)
            elif mav_type == "VAR":
                mavg_grid_arr[idx] = strategy_mod.pine_var(src_arr, length)
            elif mav_type == "WWMA":
                mavg_grid_arr[idx] = strategy_mod.pine_wwma(src_arr, length)
            elif mav_type == "ZLEMA":
                mavg_grid_arr[idx] = strategy_mod.pine_zlema(src_arr, length)
            elif mav_type == "TSF":
                mavg_grid_arr[idx] = strategy_mod.pine_tsf(src_arr, length)
            else:
                mavg_grid_arr[idx] = strategy_mod.pine_ema(src_arr, length)

        atr_grid_arr = np.zeros((len(atr_combos), len(data)), dtype=np.float64)
        for combo, idx in atr_keys.items():
            periods, change_atr = combo
            atr_grid_arr[idx] = strategy_mod.compute_atr(high_arr, low_arr, close_arr, periods, change_atr)

        mavg_shm = SharedIndicatorVolume(array_to_share=mavg_grid_arr)
        shm_objects.append(mavg_shm)

        atr_shm = SharedIndicatorVolume(array_to_share=atr_grid_arr)
        shm_objects.append(atr_shm)

        pmax_shm_metadata = {
            "mavg_shm_name": mavg_shm.shm_name,
            "mavg_shape": mavg_shm.shape,
            "mavg_dtype": str(mavg_shm.dtype),
            "mavg_keys": mavg_keys,
            "atr_shm_name": atr_shm.shm_name,
            "atr_shape": atr_shm.shape,
            "atr_dtype": str(atr_shm.dtype),
            "atr_keys": atr_keys,
        }

        try:
            strategy_mod._SHARED_PMAX_MAVG_GRID = mavg_grid_arr
            strategy_mod._SHARED_PMAX_MAVG_KEYS = mavg_keys
            strategy_mod._SHARED_PMAX_ATR_GRID = atr_grid_arr
            strategy_mod._SHARED_PMAX_ATR_KEYS = atr_keys
        except Exception as e:
            logger.debug(f"Failed to mount local parent PMax grid: {e}")
            
    return pmax_shm_metadata

def _allocate_range_filter(data, parameter_specs, fixed_overrides, workers, shm_objects):
    rf_shm_metadata = None
    period_specs = next((s for s in parameter_specs if s.name == "sampling_period"), None)
    mult_specs = next((s for s in parameter_specs if s.name == "range_multiplier"), None)

    period_vals = list(period_specs.values) if (period_specs and period_specs.values) else [100]
    mult_vals = list(mult_specs.values) if (mult_specs and mult_specs.values) else [3.0]

    from .strategies.range_filter import _load_strategy_module
    strategy_mod = _load_strategy_module()
    
    source_col = fixed_overrides.source_col if (fixed_overrides and hasattr(fixed_overrides, "source_col") and fixed_overrides.source_col) else "close"
    src_series = data[source_col] if source_col in data.columns else data["close"]
    
    combos = []
    for period in period_vals:
        for mult in mult_vals:
            combos.append((int(period), float(mult)))
    rf_keys = {combo: i for i, combo in enumerate(combos)}

    estimated_bytes = len(combos) * len(data) * 8 * 2
    max_memory_limit = _get_dynamic_memory_limit()
    if estimated_bytes > max_memory_limit:
        logger.warning(
            f"Shared memory grid for Range Filter is too large ({estimated_bytes / (1024**2):.1f} MB). "
            f"Skipping precalculation to protect system memory."
        )
    else:
        smrng_grid_arr = np.zeros((len(combos), len(data)), dtype=np.float64)
        filt_grid_arr = np.zeros((len(combos), len(data)), dtype=np.float64)

        for combo, idx in rf_keys.items():
            period, mult = combo
            smrng_series = strategy_mod._smooth_range(src_series, period, mult)
            filt_series = strategy_mod._range_filter(src_series, smrng_series)
            
            smrng_grid_arr[idx] = smrng_series.to_numpy(dtype=float)
            filt_grid_arr[idx] = filt_series.to_numpy(dtype=float)

        smrng_shm = SharedIndicatorVolume(array_to_share=smrng_grid_arr)
        shm_objects.append(smrng_shm)

        filt_shm = SharedIndicatorVolume(array_to_share=filt_grid_arr)
        shm_objects.append(filt_shm)

        rf_shm_metadata = {
            "smrng_shm_name": smrng_shm.shm_name,
            "smrng_shape": smrng_shm.shape,
            "smrng_dtype": str(smrng_shm.dtype),
            "filt_shm_name": filt_shm.shm_name,
            "filt_shape": filt_shm.shape,
            "filt_dtype": str(filt_shm.dtype),
            "rf_keys": rf_keys,
        }

        try:
            strategy_mod._SHARED_RF_SMRNG_GRID = smrng_grid_arr
            strategy_mod._SHARED_RF_GRID = filt_grid_arr
            strategy_mod._SHARED_RF_KEYS = rf_keys
        except Exception as e:
            logger.debug(f"Failed to mount local parent Range Filter grid: {e}")
            
    return rf_shm_metadata

def _allocate_bjorgum_double_tap(data, parameter_specs, fixed_overrides, workers, shm_objects):
    bjorgum_shm_metadata = None
    length_specs = next((s for s in parameter_specs if s.name == "length"), None)
    atr_length_specs = next((s for s in parameter_specs if s.name == "atrLength"), None)
    lookback_specs = next((s for s in parameter_specs if s.name == "lookback"), None)

    length_vals = list(length_specs.values) if (length_specs and length_specs.values) else [_get_fixed_val(fixed_overrides, "length", 50)]
    atr_length_vals = list(atr_length_specs.values) if (atr_length_specs and atr_length_specs.values) else [_get_fixed_val(fixed_overrides, "atrLength", 14)]
    lookback_vals = list(lookback_specs.values) if (lookback_specs and lookback_specs.values) else [_get_fixed_val(fixed_overrides, "lookback", 5)]

    estimated_bytes = (2 * len(length_vals) + 2 * len(lookback_vals) + len(atr_length_vals)) * len(data) * 8
    max_memory_limit = _get_dynamic_memory_limit()
    if estimated_bytes > max_memory_limit:
        logger.warning(
            f"Shared memory grid for Bjorgum Double Tap is too large ({estimated_bytes / (1024**2):.1f} MB). "
            f"Skipping precalculation to protect system memory."
        )
    else:
        from .strategies.bjorgum_double_tap import _load_strategy_module
        strategy_mod = _load_strategy_module()

        high_series = data["high"]
        low_series = data["low"]
        close_series = data["close"]

        piv_high_grid_arr = np.zeros((len(length_vals), len(data)), dtype=np.float64)
        piv_low_grid_arr = np.zeros((len(length_vals), len(data)), dtype=np.float64)
        for idx, length in enumerate(length_vals):
            piv_high_grid_arr[idx] = high_series.rolling(int(length), min_periods=1).max().to_numpy()
            piv_low_grid_arr[idx] = low_series.rolling(int(length), min_periods=1).min().to_numpy()

        roll_min_grid_arr = np.zeros((len(lookback_vals), len(data)), dtype=np.float64)
        roll_max_grid_arr = np.zeros((len(lookback_vals), len(data)), dtype=np.float64)
        for idx, lookback in enumerate(lookback_vals):
            roll_min_grid_arr[idx] = low_series.rolling(int(lookback), min_periods=1).min().to_numpy()
            roll_max_grid_arr[idx] = high_series.rolling(int(lookback), min_periods=1).max().to_numpy()

        atr_grid_arr = np.zeros((len(atr_length_vals), len(data)), dtype=np.float64)
        
        closes = close_series.to_numpy(dtype=float)
        prev_closes = np.roll(closes, 1)
        prev_closes[0] = closes[0]
        
        tr1 = high_series.to_numpy(dtype=float) - low_series.to_numpy(dtype=float)
        tr2 = np.abs(high_series.to_numpy(dtype=float) - prev_closes)
        tr3 = np.abs(low_series.to_numpy(dtype=float) - prev_closes)
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        tr_series = pd.Series(tr)
        
        for idx, atr_length in enumerate(atr_length_vals):
            atr_grid_arr[idx] = tr_series.ewm(alpha=1.0 / int(atr_length), adjust=False).mean().to_numpy()

        atr_shm = SharedIndicatorVolume(array_to_share=atr_grid_arr)
        shm_objects.append(atr_shm)

        piv_high_shm = SharedIndicatorVolume(array_to_share=piv_high_grid_arr)
        shm_objects.append(piv_high_shm)

        piv_low_shm = SharedIndicatorVolume(array_to_share=piv_low_grid_arr)
        shm_objects.append(piv_low_shm)

        roll_min_shm = SharedIndicatorVolume(array_to_share=roll_min_grid_arr)
        shm_objects.append(roll_min_shm)

        roll_max_shm = SharedIndicatorVolume(array_to_share=roll_max_grid_arr)
        shm_objects.append(roll_max_shm)

        bjorgum_shm_metadata = {
            "atr_shm_name": atr_shm.shm_name,
            "atr_shape": atr_shm.shape,
            "atr_dtype": str(atr_shm.dtype),
            "atr_keys": {int(v): i for i, v in enumerate(atr_length_vals)},
            
            "piv_high_shm_name": piv_high_shm.shm_name,
            "piv_high_shape": piv_high_shm.shape,
            "piv_high_dtype": str(piv_high_shm.dtype),
            "piv_high_keys": {int(v): i for i, v in enumerate(length_vals)},

            "piv_low_shm_name": piv_low_shm.shm_name,
            "piv_low_shape": piv_low_shm.shape,
            "piv_low_dtype": str(piv_low_shm.dtype),
            "piv_low_keys": {int(v): i for i, v in enumerate(length_vals)},

            "roll_min_shm_name": roll_min_shm.shm_name,
            "roll_min_shape": roll_min_shm.shape,
            "roll_min_dtype": str(roll_min_shm.dtype),
            "roll_min_keys": {int(v): i for i, v in enumerate(lookback_vals)},

            "roll_max_shm_name": roll_max_shm.shm_name,
            "roll_max_shape": roll_max_shm.shape,
            "roll_max_dtype": str(roll_max_shm.dtype),
            "roll_max_keys": {int(v): i for i, v in enumerate(lookback_vals)},
        }

        try:
            if workers > 1:
                import gc as _gc
                strategy_mod._SHARED_BJ_ATR_GRID = atr_shm.get_view()
                strategy_mod._SHARED_BJ_ATR_KEYS = bjorgum_shm_metadata["atr_keys"]
                strategy_mod._SHARED_BJ_PIV_HIGH_GRID = piv_high_shm.get_view()
                strategy_mod._SHARED_BJ_PIV_HIGH_KEYS = bjorgum_shm_metadata["piv_high_keys"]
                strategy_mod._SHARED_BJ_PIV_LOW_GRID = piv_low_shm.get_view()
                strategy_mod._SHARED_BJ_PIV_LOW_KEYS = bjorgum_shm_metadata["piv_low_keys"]
                strategy_mod._SHARED_BJ_ROLL_MIN_GRID = roll_min_shm.get_view()
                strategy_mod._SHARED_BJ_ROLL_MIN_KEYS = bjorgum_shm_metadata["roll_min_keys"]
                strategy_mod._SHARED_BJ_ROLL_MAX_GRID = roll_max_shm.get_view()
                strategy_mod._SHARED_BJ_ROLL_MAX_KEYS = bjorgum_shm_metadata["roll_max_keys"]
                
                del piv_high_grid_arr
                del piv_low_grid_arr
                del roll_min_grid_arr
                del roll_max_grid_arr
                del atr_grid_arr
                _gc.collect()
            else:
                strategy_mod._SHARED_BJ_ATR_GRID = atr_grid_arr
                strategy_mod._SHARED_BJ_ATR_KEYS = bjorgum_shm_metadata["atr_keys"]
                strategy_mod._SHARED_BJ_PIV_HIGH_GRID = piv_high_grid_arr
                strategy_mod._SHARED_BJ_PIV_HIGH_KEYS = bjorgum_shm_metadata["piv_high_keys"]
                strategy_mod._SHARED_BJ_PIV_LOW_GRID = piv_low_grid_arr
                strategy_mod._SHARED_BJ_PIV_LOW_KEYS = bjorgum_shm_metadata["piv_low_keys"]
                strategy_mod._SHARED_BJ_ROLL_MIN_GRID = roll_min_grid_arr
                strategy_mod._SHARED_BJ_ROLL_MIN_KEYS = bjorgum_shm_metadata["roll_min_keys"]
                strategy_mod._SHARED_BJ_ROLL_MAX_GRID = roll_max_grid_arr
                strategy_mod._SHARED_BJ_ROLL_MAX_KEYS = bjorgum_shm_metadata["roll_max_keys"]
        except Exception as e:
            logger.debug(f"Failed to mount local parent Bjorgum Double Tap grid: {e}")
            
    return bjorgum_shm_metadata

def _allocate_adaptive_volatility_trend(data, parameter_specs, fixed_overrides, workers, shm_objects):
    avt_shm_metadata = None
    source_specs = next((s for s in parameter_specs if s.name == "source"), None)
    length_specs = next((s for s in parameter_specs if s.name == "length"), None)
    smoothing_specs = next((s for s in parameter_specs if s.name == "efficiency_smoothing"), None)
    atr_len_specs = next((s for s in parameter_specs if s.name == "atr_len"), None)
    rsi_len_specs = next((s for s in parameter_specs if s.name == "rsi_len"), None)

    source_vals = list(source_specs.values) if (source_specs and source_specs.values) else [_get_fixed_val(fixed_overrides, "source", "close")]
    length_vals = list(length_specs.values) if (length_specs and length_specs.values) else [_get_fixed_val(fixed_overrides, "length", 21)]
    smoothing_vals = list(smoothing_specs.values) if (smoothing_specs and smoothing_specs.values) else [_get_fixed_val(fixed_overrides, "efficiency_smoothing", 5)]
    atr_len_vals = list(atr_len_specs.values) if (atr_len_specs and atr_len_specs.values) else [_get_fixed_val(fixed_overrides, "atr_len", 14)]
    rsi_len_vals = list(rsi_len_specs.values) if (rsi_len_specs and rsi_len_specs.values) else [_get_fixed_val(fixed_overrides, "rsi_len", 14)]

    from .strategies.adaptive_volatility_trend import _load_strategy_module
    strategy_mod = _load_strategy_module()

    ama_combos = []
    for src in source_vals:
        for l in length_vals:
            for s in smoothing_vals:
                ama_combos.append((str(src), int(l), int(s)))
    ama_keys = {combo: i for i, combo in enumerate(ama_combos)}

    rsi_combos = []
    for src in source_vals:
        for rl in rsi_len_vals:
            rsi_combos.append((str(src), int(rl)))
    rsi_keys = {combo: i for i, combo in enumerate(rsi_combos)}

    estimated_bytes = (len(ama_combos) * 2 + len(atr_len_vals) + len(rsi_combos)) * len(data) * 8
    max_memory_limit = _get_dynamic_memory_limit()
    if estimated_bytes > max_memory_limit:
        logger.warning(
            f"Shared memory grids for Adaptive Volatility Trend are too large ({estimated_bytes / (1024**2):.1f} MB). "
            f"Skipping precalculation to protect system memory."
        )
    else:
        ama_grid_arr = np.zeros((len(ama_combos), 2, len(data)), dtype=np.float64)
        for combo, idx in ama_keys.items():
            src, l, s = combo
            source_series = strategy_mod._price_source(data, src)
            close_series = data["close"]
            adaptive_line, efficiency_ratio = strategy_mod._adaptive_ma(source_series, close_series, l, s)
            ama_grid_arr[idx, 0] = adaptive_line.to_numpy(dtype=float)
            ama_grid_arr[idx, 1] = efficiency_ratio.to_numpy(dtype=float)

        high_series = data["high"]
        low_series = data["low"]
        close_series = data["close"]
        
        atr_grid_arr = np.zeros((len(atr_len_vals), len(data)), dtype=np.float64)
        atr_keys = {int(v): i for i, v in enumerate(atr_len_vals)}
        for atr_len, idx in atr_keys.items():
            atr_series = strategy_mod._atr(high_series, low_series, close_series, atr_len)
            atr_grid_arr[idx] = atr_series.to_numpy(dtype=float)

        rsi_grid_arr = np.zeros((len(rsi_combos), len(data)), dtype=np.float64)
        for combo, idx in rsi_keys.items():
            src, rl = combo
            source_series = strategy_mod._price_source(data, src)
            rsi_series = strategy_mod._rsi(source_series, rl)
            rsi_grid_arr[idx] = rsi_series.to_numpy(dtype=float)

        ama_shm = SharedIndicatorVolume(array_to_share=ama_grid_arr)
        shm_objects.append(ama_shm)

        atr_shm = SharedIndicatorVolume(array_to_share=atr_grid_arr)
        shm_objects.append(atr_shm)

        rsi_shm = SharedIndicatorVolume(array_to_share=rsi_grid_arr)
        shm_objects.append(rsi_shm)

        avt_shm_metadata = {
            "ama_shm_name": ama_shm.shm_name,
            "ama_shape": ama_shm.shape,
            "ama_dtype": str(ama_shm.dtype),
            "ama_keys": ama_keys,

            "atr_shm_name": atr_shm.shm_name,
            "atr_shape": atr_shm.shape,
            "atr_dtype": str(atr_shm.dtype),
            "atr_keys": atr_keys,

            "rsi_shm_name": rsi_shm.shm_name,
            "rsi_shape": rsi_shm.shape,
            "rsi_dtype": str(rsi_shm.dtype),
            "rsi_keys": rsi_keys,
        }

        try:
            strategy_mod._SHARED_AVT_AMA_GRID = ama_grid_arr
            strategy_mod._SHARED_AVT_AMA_KEYS = ama_keys
            strategy_mod._SHARED_AVT_ATR_GRID = atr_grid_arr
            strategy_mod._SHARED_AVT_ATR_KEYS = atr_keys
            strategy_mod._SHARED_AVT_RSI_GRID = rsi_grid_arr
            strategy_mod._SHARED_AVT_RSI_KEYS = rsi_keys
        except Exception as e:
            logger.debug(f"Failed to mount local parent Adaptive Volatility Trend grid: {e}")

    return avt_shm_metadata

def _allocate_3commas_bot(data, parameter_specs, fixed_overrides, workers, shm_objects):
    commas_bot_shm_metadata = None
    ma_type1_specs = next((s for s in parameter_specs if s.name == "ma_type1"), None)
    ma_type2_specs = next((s for s in parameter_specs if s.name == "ma_type2"), None)
    ma_length1_specs = next((s for s in parameter_specs if s.name == "ma_length1"), None)
    ma_length2_specs = next((s for s in parameter_specs if s.name == "ma_length2"), None)
    atr_len_specs = next((s for s in parameter_specs if s.name == "atr_len"), None)
    swing_lookback_specs = next((s for s in parameter_specs if s.name == "swing_lookback"), None)

    ma_type1_vals = list(ma_type1_specs.values) if (ma_type1_specs and ma_type1_specs.values) else [_get_fixed_val(fixed_overrides, "ma_type1", "EMA")]
    ma_type2_vals = list(ma_type2_specs.values) if (ma_type2_specs and ma_type2_specs.values) else [_get_fixed_val(fixed_overrides, "ma_type2", "EMA")]
    ma_length1_vals = list(ma_length1_specs.values) if (ma_length1_specs and ma_length1_specs.values) else [_get_fixed_val(fixed_overrides, "ma_length1", 21)]
    ma_length2_vals = list(ma_length2_specs.values) if (ma_length2_specs and ma_length2_specs.values) else [_get_fixed_val(fixed_overrides, "ma_length2", 50)]
    atr_len_vals = list(atr_len_specs.values) if (atr_len_specs and atr_len_specs.values) else [_get_fixed_val(fixed_overrides, "atr_len", 14)]
    swing_lookback_vals = list(swing_lookback_specs.values) if (swing_lookback_specs and swing_lookback_specs.values) else [_get_fixed_val(fixed_overrides, "swing_lookback", 5)]

    from .strategies.commas_bot import _load_strategy_module
    strategy_mod = _load_strategy_module()

    unique_ma_combos = set()
    for t1 in ma_type1_vals:
        for l1 in ma_length1_vals:
            unique_ma_combos.add((str(t1), int(l1)))
    for t2 in ma_type2_vals:
        for l2 in ma_length2_vals:
            unique_ma_combos.add((str(t2), int(l2)))

    ma_combos = sorted(list(unique_ma_combos))
    ma_keys = {combo: i for i, combo in enumerate(ma_combos)}

    estimated_bytes = (len(ma_combos) + len(atr_len_vals) + len(swing_lookback_vals) * 2) * len(data) * 8
    max_memory_limit = _get_dynamic_memory_limit()
    if estimated_bytes > max_memory_limit:
        logger.warning(
            f"Shared memory grids for 3Commas Bot are too large ({estimated_bytes / (1024**2):.1f} MB). "
            f"Skipping precalculation to protect system memory."
        )
    else:
        ma_grid_arr = np.zeros((len(ma_combos), len(data)), dtype=np.float64)
        close_series = data["close"]
        for combo, idx in ma_keys.items():
            ma_type, length = combo
            ma_series = strategy_mod.get_ma(close_series, ma_type, length, df=data)
            ma_grid_arr[idx] = ma_series.to_numpy(dtype=float)

        atr_grid_arr = np.zeros((len(atr_len_vals), len(data)), dtype=np.float64)
        atr_keys = {int(v): i for i, v in enumerate(atr_len_vals)}
        for atr_len, idx in atr_keys.items():
            atr_series = strategy_mod.atr(data, atr_len)
            atr_grid_arr[idx] = atr_series.to_numpy(dtype=float)

        swing_grid_arr = np.zeros((len(swing_lookback_vals), 2, len(data)), dtype=np.float64)
        swing_keys = {int(v): i for i, v in enumerate(swing_lookback_vals)}
        for swing_lookback, idx in swing_keys.items():
            low_series = data["low"]
            high_series = data["high"]
            low_lowest = strategy_mod.lowest(low_series, swing_lookback)
            high_highest = strategy_mod.highest(high_series, swing_lookback)
            swing_grid_arr[idx, 0] = low_lowest.to_numpy(dtype=float)
            swing_grid_arr[idx, 1] = high_highest.to_numpy(dtype=float)

        ma_shm = SharedIndicatorVolume(array_to_share=ma_grid_arr)
        shm_objects.append(ma_shm)

        atr_shm = SharedIndicatorVolume(array_to_share=atr_grid_arr)
        shm_objects.append(atr_shm)

        swing_shm = SharedIndicatorVolume(array_to_share=swing_grid_arr)
        shm_objects.append(swing_shm)

        commas_bot_shm_metadata = {
            "ma_shm_name": ma_shm.shm_name,
            "ma_shape": ma_shm.shape,
            "ma_dtype": str(ma_shm.dtype),
            "ma_keys": ma_keys,

            "atr_shm_name": atr_shm.shm_name,
            "atr_shape": atr_shm.shape,
            "atr_dtype": str(atr_shm.dtype),
            "atr_keys": atr_keys,

            "swing_shm_name": swing_shm.shm_name,
            "swing_shape": swing_shm.shape,
            "swing_dtype": str(swing_shm.dtype),
            "swing_keys": swing_keys,
        }

        try:
            strategy_mod._SHARED_CB_MA_GRID = ma_grid_arr
            strategy_mod._SHARED_CB_MA_KEYS = ma_keys
            strategy_mod._SHARED_CB_ATR_GRID = atr_grid_arr
            strategy_mod._SHARED_CB_ATR_KEYS = atr_keys
            strategy_mod._SHARED_CB_SWING_GRID = swing_grid_arr
            strategy_mod._SHARED_CB_SWING_KEYS = swing_keys
        except Exception as e:
            logger.debug(f"Failed to mount local parent 3Commas Bot grid: {e}")

    return commas_bot_shm_metadata

def _allocate_noise_boundary_intraday(data, parameter_specs, fixed_overrides, workers, shm_objects):
    noise_boundary_shm_metadata = None
    lookback_specs = next((s for s in parameter_specs if s.name == "lookback_days"), None)
    lookback_vals = list(lookback_specs.values) if (lookback_specs and lookback_specs.values) else [_get_fixed_val(fixed_overrides, "lookback_days", 20)]

    import backtest_engine.strategies.noise_boundary_intraday as nb_mod

    vol_grid_arr = np.zeros((len(lookback_vals), 2, len(data)), dtype=np.float64)
    vol_keys = {int(v): i for i, v in enumerate(lookback_vals)}

    normalized_index = data.index.normalize()
    daily_open = data.groupby(normalized_index)["open"].transform("first")
    move_open = (data["close"] / daily_open - 1).abs()
    pivoted_df = pd.DataFrame({"move_open": move_open}, index=data.index)
    pivoted_df["date"] = normalized_index
    pivoted_df["time"] = data.index.time
    pivoted_matrix = pivoted_df.pivot(index="date", columns="time", values="move_open")
    multi_index = pd.MultiIndex.from_arrays([normalized_index, data.index.time], names=["date", "time"])

    daily_close = data["close"].resample("D").last().dropna()
    daily_returns = daily_close.pct_change()

    for lookback, idx in vol_keys.items():
        rolling_matrix = pivoted_matrix.rolling(window=lookback, min_periods=lookback - 1).mean().shift(1)
        stacked = rolling_matrix.stack(dropna=False)
        mapped_vol = stacked.reindex(multi_index).values
        vol_grid_arr[idx, 0] = mapped_vol

        daily_dvol_series = daily_returns.rolling(window=lookback, min_periods=lookback - 1).std().shift(1)
        spy_dvol = daily_dvol_series.reindex(normalized_index).values
        spy_dvol_filled = np.where(np.isnan(spy_dvol), 0.0, spy_dvol)
        vol_grid_arr[idx, 1] = spy_dvol_filled

    vol_shm = SharedIndicatorVolume(array_to_share=vol_grid_arr)
    shm_objects.append(vol_shm)

    noise_boundary_shm_metadata = {
        "vol_shm_name": vol_shm.shm_name,
        "vol_shape": vol_shm.shape,
        "vol_dtype": str(vol_shm.dtype),
        "vol_keys": vol_keys,
    }

    try:
        nb_mod._SHARED_NB_VOL_GRID = vol_grid_arr
        nb_mod._SHARED_NB_VOL_KEYS = vol_keys
    except Exception as e:
        logger.debug(f"Failed to mount local parent Noise Boundary grid: {e}")

    return noise_boundary_shm_metadata

def allocate_shared_memory_for_strategy(strategy: str, data: pd.DataFrame, parameter_specs: list, fixed_overrides: Any, workers: int, shm_objects: list) -> dict:
    """
    Alloue la mémoire partagée POSIX et précalcule les grilles selon la stratégie.
    Retourne un dictionnaire contenant les métadonnées pour chaque grille.
    """
    metadata_dict = {
        "hma_shm_metadata": None,
        "pmax_shm_metadata": None,
        "rf_shm_metadata": None,
        "bjorgum_shm_metadata": None,
        "avt_shm_metadata": None,
        "commas_bot_shm_metadata": None,
        "noise_boundary_shm_metadata": None
    }
    
    if strategy == "hma_crossover":
        metadata_dict["hma_shm_metadata"] = _allocate_hma_crossover(data, parameter_specs, fixed_overrides, workers, shm_objects)
    elif strategy == "pmax_explorer":
        metadata_dict["pmax_shm_metadata"] = _allocate_pmax_explorer(data, parameter_specs, fixed_overrides, workers, shm_objects)
    elif strategy == "range_filter":
        metadata_dict["rf_shm_metadata"] = _allocate_range_filter(data, parameter_specs, fixed_overrides, workers, shm_objects)
    elif strategy == "bjorgum_double_tap":
        metadata_dict["bjorgum_shm_metadata"] = _allocate_bjorgum_double_tap(data, parameter_specs, fixed_overrides, workers, shm_objects)
    elif strategy == "adaptive_volatility_trend":
        metadata_dict["avt_shm_metadata"] = _allocate_adaptive_volatility_trend(data, parameter_specs, fixed_overrides, workers, shm_objects)
    elif strategy == "3commas_bot":
        metadata_dict["commas_bot_shm_metadata"] = _allocate_3commas_bot(data, parameter_specs, fixed_overrides, workers, shm_objects)
    elif strategy == "noise_boundary_intraday":
        metadata_dict["noise_boundary_shm_metadata"] = _allocate_noise_boundary_intraday(data, parameter_specs, fixed_overrides, workers, shm_objects)
        
    return metadata_dict

def reset_shared_memory_for_strategy(strategy: str) -> None:
    """
    Réinitialise les références globales du parent local pour éviter 
    les fuites de références sur les objets mémoire.
    """
    if strategy == "hma_crossover":
        from .strategies.hma_crossover import _load_strategy_module
        try:
            strategy_mod = _load_strategy_module()
            strategy_mod._SHARED_HMA_GRID = None
            strategy_mod._SHARED_HMA_LENGTH_TO_IDX = None
        except Exception:  # NOSONAR
            pass
    elif strategy == "pmax_explorer":
        from .strategies.pmax_explorer import _load_strategy_module
        try:
            strategy_mod = _load_strategy_module()
            strategy_mod._SHARED_PMAX_MAVG_GRID = None
            strategy_mod._SHARED_PMAX_MAVG_KEYS = None
            strategy_mod._SHARED_PMAX_ATR_GRID = None
            strategy_mod._SHARED_PMAX_ATR_KEYS = None
        except Exception:  # NOSONAR
            pass
    elif strategy == "range_filter":
        from .strategies.range_filter import _load_strategy_module
        try:
            strategy_mod = _load_strategy_module()
            strategy_mod._SHARED_RF_SMRNG_GRID = None
            strategy_mod._SHARED_RF_GRID = None
            strategy_mod._SHARED_RF_KEYS = None
        except Exception:  # NOSONAR
            pass
    elif strategy == "bjorgum_double_tap":
        from .strategies.bjorgum_double_tap import _load_strategy_module
        try:
            strategy_mod = _load_strategy_module()
            strategy_mod._SHARED_BJ_ATR_GRID = None
            strategy_mod._SHARED_BJ_ATR_KEYS = None
            strategy_mod._SHARED_BJ_PIV_HIGH_GRID = None
            strategy_mod._SHARED_BJ_PIV_HIGH_KEYS = None
            strategy_mod._SHARED_BJ_PIV_LOW_GRID = None
            strategy_mod._SHARED_BJ_PIV_LOW_KEYS = None
            strategy_mod._SHARED_BJ_ROLL_MIN_GRID = None
            strategy_mod._SHARED_BJ_ROLL_MIN_KEYS = None
            strategy_mod._SHARED_BJ_ROLL_MAX_GRID = None
            strategy_mod._SHARED_BJ_ROLL_MAX_KEYS = None
        except Exception:  # NOSONAR
            pass
    elif strategy == "adaptive_volatility_trend":
        from .strategies.adaptive_volatility_trend import _load_strategy_module
        try:
            strategy_mod = _load_strategy_module()
            strategy_mod._SHARED_AVT_AMA_GRID = None
            strategy_mod._SHARED_AVT_AMA_KEYS = None
            strategy_mod._SHARED_AVT_ATR_GRID = None
            strategy_mod._SHARED_AVT_ATR_KEYS = None
            strategy_mod._SHARED_AVT_RSI_GRID = None
            strategy_mod._SHARED_AVT_RSI_KEYS = None
        except Exception:  # NOSONAR
            pass
    elif strategy == "3commas_bot":
        from .strategies.commas_bot import _load_strategy_module
        try:
            strategy_mod = _load_strategy_module()
            strategy_mod._SHARED_CB_MA_GRID = None
            strategy_mod._SHARED_CB_MA_KEYS = None
            strategy_mod._SHARED_CB_ATR_GRID = None
            strategy_mod._SHARED_CB_ATR_KEYS = None
            strategy_mod._SHARED_CB_SWING_GRID = None
            strategy_mod._SHARED_CB_SWING_KEYS = None
        except Exception:  # NOSONAR
            pass
    elif strategy == "noise_boundary_intraday":
        import backtest_engine.strategies.noise_boundary_intraday as nb_mod
        try:
            nb_mod._SHARED_NB_VOL_GRID = None
            nb_mod._SHARED_NB_VOL_KEYS = None
        except Exception:  # NOSONAR
            pass
