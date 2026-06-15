import pandas as pd
import glob
import os
import json

base = 'reports/local_optimizer/hmm_regime_filter/NVO'
best_per_tf = {}

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
    
    # Filter on constraints
    df_filtered = df[(df['max_drawdown_pct'] >= -25.0) & 
                     (df['max_drawdown_pct'] <= -20.0) & 
                     (df['profit_factor'] >= 1.25)]
    
    if not df_filtered.empty:
        # Sort by best return_vs_buy_hold_pct_points
        df_filtered = df_filtered.sort_values(by='return_vs_buy_hold_pct_points', ascending=False)
        best_row = df_filtered.iloc[0]
        
        # Check if we already have a better one for this TF
        if tf not in best_per_tf or best_row['return_vs_buy_hold_pct_points'] > best_per_tf[tf]['score']:
            best_per_tf[tf] = {
                'score': best_row['return_vs_buy_hold_pct_points'],
                'obs_len': best_row['param_obs_len'],
                'stat_len': best_row['param_stat_len'],
                'mu_k': best_row['param_mu_k'],
                'stick': best_row['param_stick'],
                'max_dd_pct': best_row['max_drawdown_pct'],
                'profit_factor': best_row['profit_factor']
            }

for tf, data in best_per_tf.items():
    print(f"TF {tf}m: Score {data['score']:.4f}")
    print(f"  Params: obs_len={data['obs_len']}, stat_len={data['stat_len']}, mu_k={data['mu_k']}, stick={data['stick']}")
    print(f"  Metrics: Max DD={data['max_dd_pct']:.2f}%, PF={data['profit_factor']:.2f}")

