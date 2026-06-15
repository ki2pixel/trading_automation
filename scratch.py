import pandas as pd
import json

run_dir = '/home/kidpixel/trading_automation_v2/reports/local_optimizer/hmm_regime_filter/NVO/20260615T110744Z-0e438189f27340c4919f2d4c58ede0ca'

with open(f"{run_dir}/recommendations.json") as f:
    rec = json.load(f)
    best = rec.get("best", {})
    
df = pd.read_parquet(f"{run_dir}/results.parquet")
df_best = df[df['return_vs_buy_hold_pct_points'] > best['score'] - 0.01].iloc[0]

print(f"Score: {best['score']}")
print(f"Params: {best['parameters']}")
print(f"PF: {best['metrics']['profit_factor']}")
print(f"Max DD %: {df_best['max_drawdown_pct']}")

