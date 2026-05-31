import re

with open('/home/kidpixel/trading_automation_v2/backtest_engine/bayesian_optimizer.py', 'r') as f:
    content = f.read()

# Add _get_fixed_val helper
setup_block_start = """        noise_boundary_shm_metadata = None
        if strategy == "hma_crossover":"""

setup_block_new = """        noise_boundary_shm_metadata = None

        def _get_fixed_val(name, default):
            if fixed_overrides and hasattr(fixed_overrides, name):
                val = getattr(fixed_overrides, name)
                if val is not None:
                    return val
            return default

        if strategy == "hma_crossover":"""

if setup_block_start in content:
    content = content.replace(setup_block_start, setup_block_new)

# Fix hma_crossover
old_hma = """            fast_specs = next((s for s in parameter_specs if s.name == "fast_len"), None)
            slow_specs = next((s for s in parameter_specs if s.name == "slow_len"), None)
            if fast_specs and slow_specs and fast_specs.values and slow_specs.values:
                from .strategies.hma_crossover import _load_strategy_module
                strategy_mod = _load_strategy_module()
                hma_func = strategy_mod.hma
                import numpy as np
                import gc as _gc
                unique_lengths = sorted(list(set(fast_specs.values) | set(slow_specs.values)))"""

new_hma = """            fast_specs = next((s for s in parameter_specs if s.name == "fast_len"), None)
            slow_specs = next((s for s in parameter_specs if s.name == "slow_len"), None)
            fast_vals = list(fast_specs.values) if (fast_specs and fast_specs.values) else [_get_fixed_val("fast_len", 20)]
            slow_vals = list(slow_specs.values) if (slow_specs and slow_specs.values) else [_get_fixed_val("slow_len", 50)]
            if fast_vals and slow_vals:
                from .strategies.hma_crossover import _load_strategy_module
                strategy_mod = _load_strategy_module()
                hma_func = strategy_mod.hma
                import numpy as np
                import gc as _gc
                unique_lengths = sorted(list(set(fast_vals) | set(slow_vals)))"""
content = content.replace(old_hma, new_hma)

# Fix pmax_explorer
old_pmax = """            periods_vals = list(periods_specs.values) if (periods_specs and periods_specs.values) else [10]
            length_vals = list(length_specs.values) if (length_specs and length_specs.values) else [10]
            mav_vals = list(mav_specs.values) if (mav_specs and mav_specs.values) else ["EMA"]
            change_atr_vals = list(change_atr_specs.values) if (change_atr_specs and change_atr_specs.values) else [True]"""

new_pmax = """            periods_vals = list(periods_specs.values) if (periods_specs and periods_specs.values) else [_get_fixed_val("periods", 10)]
            length_vals = list(length_specs.values) if (length_specs and length_specs.values) else [_get_fixed_val("length", 10)]
            mav_vals = list(mav_specs.values) if (mav_specs and mav_specs.values) else [_get_fixed_val("mav", "EMA")]
            change_atr_vals = list(change_atr_specs.values) if (change_atr_specs and change_atr_specs.values) else [_get_fixed_val("change_atr", True)]"""
content = content.replace(old_pmax, new_pmax)

# Fix range_filter
old_rf = """            periods_vals = list(periods_specs.values) if (periods_specs and periods_specs.values) else [100]
            multiplier_vals = list(multiplier_specs.values) if (multiplier_specs and multiplier_specs.values) else [3.0]"""

new_rf = """            periods_vals = list(periods_specs.values) if (periods_specs and periods_specs.values) else [_get_fixed_val("periods", 100)]
            multiplier_vals = list(multiplier_specs.values) if (multiplier_specs and multiplier_specs.values) else [_get_fixed_val("multiplier", 3.0)]"""
content = content.replace(old_rf, new_rf)

# Fix bjorgum_double_tap
old_bj = """            length_vals = list(length_specs.values) if (length_specs and length_specs.values) else [50]
            atr_length_vals = list(atr_length_specs.values) if (atr_length_specs and atr_length_specs.values) else [14]
            lookback_vals = list(lookback_specs.values) if (lookback_specs and lookback_specs.values) else [5]"""

new_bj = """            length_vals = list(length_specs.values) if (length_specs and length_specs.values) else [_get_fixed_val("length", 50)]
            atr_length_vals = list(atr_length_specs.values) if (atr_length_specs and atr_length_specs.values) else [_get_fixed_val("atrLength", 14)]
            lookback_vals = list(lookback_specs.values) if (lookback_specs and lookback_specs.values) else [_get_fixed_val("lookback", 5)]"""
content = content.replace(old_bj, new_bj)

# Fix adaptive_volatility_trend
old_avt = """            source_vals = list(source_specs.values) if (source_specs and source_specs.values) else ["close"]
            length_vals = list(length_specs.values) if (length_specs and length_specs.values) else [21]
            smoothing_vals = list(smoothing_specs.values) if (smoothing_specs and smoothing_specs.values) else [5]
            atr_len_vals = list(atr_len_specs.values) if (atr_len_specs and atr_len_specs.values) else [14]
            rsi_len_vals = list(rsi_len_specs.values) if (rsi_len_specs and rsi_len_specs.values) else [14]"""

new_avt = """            source_vals = list(source_specs.values) if (source_specs and source_specs.values) else [_get_fixed_val("source", "close")]
            length_vals = list(length_specs.values) if (length_specs and length_specs.values) else [_get_fixed_val("length", 21)]
            smoothing_vals = list(smoothing_specs.values) if (smoothing_specs and smoothing_specs.values) else [_get_fixed_val("efficiency_smoothing", 5)]
            atr_len_vals = list(atr_len_specs.values) if (atr_len_specs and atr_len_specs.values) else [_get_fixed_val("atr_len", 14)]
            rsi_len_vals = list(rsi_len_specs.values) if (rsi_len_specs and rsi_len_specs.values) else [_get_fixed_val("rsi_len", 14)]"""
content = content.replace(old_avt, new_avt)

# Fix 3commas_bot
old_3cb = """            ma_type1_vals = list(ma_type1_specs.values) if (ma_type1_specs and ma_type1_specs.values) else ["EMA"]
            ma_type2_vals = list(ma_type2_specs.values) if (ma_type2_specs and ma_type2_specs.values) else ["EMA"]
            ma_length1_vals = list(ma_length1_specs.values) if (ma_length1_specs and ma_length1_specs.values) else [21]
            ma_length2_vals = list(ma_length2_specs.values) if (ma_length2_specs and ma_length2_specs.values) else [50]
            atr_len_vals = list(atr_len_specs.values) if (atr_len_specs and atr_len_specs.values) else [14]
            swing_lookback_vals = list(swing_lookback_specs.values) if (swing_lookback_specs and swing_lookback_specs.values) else [5]"""

new_3cb = """            ma_type1_vals = list(ma_type1_specs.values) if (ma_type1_specs and ma_type1_specs.values) else [_get_fixed_val("ma_type1", "EMA")]
            ma_type2_vals = list(ma_type2_specs.values) if (ma_type2_specs and ma_type2_specs.values) else [_get_fixed_val("ma_type2", "EMA")]
            ma_length1_vals = list(ma_length1_specs.values) if (ma_length1_specs and ma_length1_specs.values) else [_get_fixed_val("ma_length1", 21)]
            ma_length2_vals = list(ma_length2_specs.values) if (ma_length2_specs and ma_length2_specs.values) else [_get_fixed_val("ma_length2", 50)]
            atr_len_vals = list(atr_len_specs.values) if (atr_len_specs and atr_len_specs.values) else [_get_fixed_val("atr_len", 14)]
            swing_lookback_vals = list(swing_lookback_specs.values) if (swing_lookback_specs and swing_lookback_specs.values) else [_get_fixed_val("swing_lookback", 5)]"""
content = content.replace(old_3cb, new_3cb)

# Fix noise_boundary_intraday
old_nbi = """            lookback_vals = list(lookback_specs.values) if (lookback_specs and lookback_specs.values) else [20]"""
new_nbi = """            lookback_vals = list(lookback_specs.values) if (lookback_specs and lookback_specs.values) else [_get_fixed_val("lookback_days", 20)]"""
content = content.replace(old_nbi, new_nbi)

with open('/home/kidpixel/trading_automation_v2/backtest_engine/bayesian_optimizer.py', 'w') as f:
    f.write(content)

print("bayesian_optimizer.py fixed.")
