import re

with open('/home/kidpixel/trading_automation_v2/backtest_engine/strategies/pmax_explorer.py', 'r') as f:
    content = f.read()

old_block = """    periods_specs = next((s for s in parameter_specs if s.name == "periods"), None)
    multiplier_specs = next((s for s in parameter_specs if s.name == "multiplier"), None)
    length_specs = next((s for s in parameter_specs if s.name == "length"), None)

    if not all([periods_specs, multiplier_specs, length_specs]):
        _write_prescan_report(output_dir, "skipped", None, {})
        return parameter_specs
    if not all([s.values for s in [periods_specs, multiplier_specs, length_specs]]):
        _write_prescan_report(output_dir, "skipped", None, {})
        return parameter_specs"""

new_block = """    periods_specs = next((s for s in parameter_specs if s.name == "periods"), None)
    multiplier_specs = next((s for s in parameter_specs if s.name == "multiplier"), None)
    length_specs = next((s for s in parameter_specs if s.name == "length"), None)

    periods_vals = list(periods_specs.values) if (periods_specs and periods_specs.values) else [strategy_config.get("periods", 10)]
    multiplier_vals = list(multiplier_specs.values) if (multiplier_specs and multiplier_specs.values) else [strategy_config.get("multiplier", 3.0)]
    length_vals = list(length_specs.values) if (length_specs and length_specs.values) else [strategy_config.get("length", 10)]

    if len(periods_vals) * len(multiplier_vals) * len(length_vals) <= 1:
        _write_prescan_report(output_dir, "skipped", None, {})
        return parameter_specs"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('/home/kidpixel/trading_automation_v2/backtest_engine/strategies/pmax_explorer.py', 'w') as f:
        f.write(content)
    print("pmax_explorer.py prescan fixed.")
else:
    print("Could not find old block in pmax_explorer.py")
