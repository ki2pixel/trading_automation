import re

with open('/home/kidpixel/trading_automation_v2/backtest_engine/strategies/pmax_explorer.py', 'r') as f:
    content = f.read()

# Fix the bounds check
old_bounds = """        min_periods = max(int(periods_specs.values[0]), min_periods - margin_periods)
        max_periods = min(int(periods_specs.values[-1]), max_periods + margin_periods)
        min_mult = max(float(multiplier_specs.values[0]), min_mult - margin_mult)
        max_mult = min(float(multiplier_specs.values[-1]), max_mult + margin_mult)
        min_len = max(int(length_specs.values[0]), min_len - margin_len)
        max_len = min(int(length_specs.values[-1]), max_len + margin_len)"""

new_bounds = """        min_periods = max(int(periods_vals[0]), min_periods - margin_periods)
        max_periods = min(int(periods_vals[-1]), max_periods + margin_periods)
        min_mult = max(float(multiplier_vals[0]), min_mult - margin_mult)
        max_mult = min(float(multiplier_vals[-1]), max_mult + margin_mult)
        min_len = max(int(length_vals[0]), min_len - margin_len)
        max_len = min(int(length_vals[-1]), max_len + margin_len)"""

if old_bounds in content:
    content = content.replace(old_bounds, new_bounds)
    print("Replaced bounds.")
else:
    print("Could not find old_bounds")

# Fix the report crash
old_report = """                "periods": {
                    "original_bounds": [int(periods_specs.values[0]), int(periods_specs.values[-1])],
                    "new_bounds": [int(periods_filtered[0]), int(periods_filtered[-1])],
                    "filtered_values": list(periods_filtered),
                },
                "multiplier": {
                    "original_bounds": [float(multiplier_specs.values[0]), float(multiplier_specs.values[-1])],
                    "new_bounds": [float(mult_filtered[0]), float(mult_filtered[-1])],
                    "filtered_values": list(mult_filtered),
                },
                "length": {
                    "original_bounds": [int(length_specs.values[0]), int(length_specs.values[-1])],
                    "new_bounds": [int(len_filtered[0]), int(len_filtered[-1])],
                    "filtered_values": list(len_filtered),
                },"""

new_report = """                "periods": {
                    "original_bounds": [int(periods_vals[0]), int(periods_vals[-1])],
                    "new_bounds": [int((periods_filtered or periods_vals)[0]), int((periods_filtered or periods_vals)[-1])],
                    "filtered_values": list(periods_filtered or periods_vals),
                },
                "multiplier": {
                    "original_bounds": [float(multiplier_vals[0]), float(multiplier_vals[-1])],
                    "new_bounds": [float((mult_filtered or multiplier_vals)[0]), float((mult_filtered or multiplier_vals)[-1])],
                    "filtered_values": list(mult_filtered or multiplier_vals),
                },
                "length": {
                    "original_bounds": [int(length_vals[0]), int(length_vals[-1])],
                    "new_bounds": [int((len_filtered or length_vals)[0]), int((len_filtered or length_vals)[-1])],
                    "filtered_values": list(len_filtered or length_vals),
                },"""

if old_report in content:
    content = content.replace(old_report, new_report)
    print("Replaced report.")
else:
    print("Could not find old_report")

# Fix missing return in except Exception
old_except = """    except Exception as e:
        _write_prescan_report(output_dir, "error", None, {})
        logger.warning(f"Erreur Pre-Scan VectorBT: {e}. Optuna utilisera les bornes globales.")

    _write_prescan_report(output_dir, "skipped", None, {})
    return parameter_specs"""

new_except = """    except Exception as e:
        _write_prescan_report(output_dir, "error", None, {})
        logger.warning(f"Erreur Pre-Scan VectorBT: {e}. Optuna utilisera les bornes globales.")
        return parameter_specs

    _write_prescan_report(output_dir, "skipped", None, {})
    return parameter_specs"""

if old_except in content:
    content = content.replace(old_except, new_except)
    print("Replaced except return.")
else:
    print("Could not find old_except")


with open('/home/kidpixel/trading_automation_v2/backtest_engine/strategies/pmax_explorer.py', 'w') as f:
    f.write(content)

