import pandas as pd
import glob
import os
import json

base = 'reports/local_optimizer/hmm_regime_filter/NVO'

for pq in glob.glob(os.path.join(base, '*', 'results.parquet')):
    run_dir = os.path.dirname(pq)
    config_path = os.path.join(run_dir, 'optimization_config.json')
    tf = 'Unknown'
    if os.path.exists(config_path):
        with open(config_path) as f:
            c = json.load(f)
            if 'timeframe_minutes' in c:
                tf = c['timeframe_minutes']
            elif 'timeframes' in c:
                tf = ','.join(c['timeframes'])
    
    df = pd.read_parquet(pq)
    best_row = df.sort_values(by='return_vs_buy_hold_pct_points', ascending=False).iloc[0]
    print(f"TF {tf}m: Best Score {best_row['return_vs_buy_hold_pct_points']:.4f}")
    print(f"  Params: obs_len={best_row.get('param_obs_len')}, stat_len={best_row.get('param_stat_len')}, mu_k={best_row.get('param_mu_k')}, stick={best_row.get('param_stick')}")
    print(f"  Metrics: Max DD={best_row['max_drawdown_pct']:.2f}%, PF={best_row['profit_factor']:.2f}")

