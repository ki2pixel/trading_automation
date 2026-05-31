import re

with open('/home/kidpixel/trading_automation_v2/backtest_engine/strategies/hma_crossover.py', 'r') as f:
    content = f.read()

old_start = """    fast_specs = next((s for s in parameter_specs if s.name == "fast_len"), None)
    slow_specs = next((s for s in parameter_specs if s.name == "slow_len"), None)

    if fast_specs and slow_specs and fast_specs.values and slow_specs.values:
        try:"""

new_start = """    fast_specs = next((s for s in parameter_specs if s.name == "fast_len"), None)
    slow_specs = next((s for s in parameter_specs if s.name == "slow_len"), None)

    fast_vals = list(fast_specs.values) if (fast_specs and fast_specs.values) else [20]
    slow_vals = list(slow_specs.values) if (slow_specs and slow_specs.values) else [50]

    if len(fast_vals) * len(slow_vals) <= 1:
        _write_prescan_report(output_dir, "skipped", None, {})
        return parameter_specs

    try:"""

content = content.replace(old_start, new_start)

# Fix indentation since we removed the `if` block above `try:`
# Actually wait, `try:` was indented under `if`. If we replace `if ... try:` with `try:` without changing the indentation of the entire block, we'll get an IndentationError.
# We must de-indent the entire try-except block. Or we can just keep the `if True:` so we don't have to touch indentation!
