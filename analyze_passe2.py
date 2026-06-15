import pandas as pd
import glob
import os
import json

base = 'reports/local_optimizer/hmm_regime_filter/NVO'
best_per_tf = {}

for pq in glob.glob(os.path.join(base, '*', 'results.parquet')):
    run_dir = os.path.dirname(pq)
    
    # We want to identify if this run is Passe 2. Usually Passe 2 runs are newer or have confirm_bars and dom_thresh varying in optimization_config
    config_path = os.path.join(run_dir, 'optimization_config.json')
    tf = 'Unknown'
    is_passe_2 = False
    if os.path.exists(config_path):
        with open(config_path) as f:
            c = json.load(f)
            if 'timeframe_minutes' in c:
                tf = c['timeframe_minutes']
            elif 'timeframes' in c:
                tf = ','.join(c['timeframes'])
            
            # check if confirm_bars or dom_thresh are in parameter_specs
            specs = c.get('parameter_specs', {})
            if 'confirm_bars' in specs and isinstance(specs['confirm_bars'], dict):
                is_passe_2 = True
            if 'dom_thresh' in specs and isinstance(specs['dom_thresh'], dict):
                is_passe_2 = True

    if not is_passe_2:
        continue

    df = pd.read_parquet(pq)
    
    # Sort by best return_vs_buy_hold_pct_points
    # We might have the same constraints as Passe 1 (Max DD -20 to -25%, PF >= 1.25)
    # Actually, we usually just take the absolute best that meets constraints if we want, or just the absolute best since it's refining Passe 1.
    df_filtered = df[(df['max_drawdown_pct'] >= -25.0) & (df['profit_factor'] >= 1.25)]
    
    if not df_filtered.empty:
        df_filtered = df_filtered.sort_values(by='return_vs_buy_hold_pct_points', ascending=False)
        best_row = df_filtered.iloc[0]
        
        if tf not in best_per_tf or best_row['return_vs_buy_hold_pct_points'] > best_per_tf[tf]['score']:
            best_per_tf[tf] = {
                'score': best_row['return_vs_buy_hold_pct_points'],
                'obs_len': best_row.get('param_obs_len'),
                'stat_len': best_row.get('param_stat_len'),
                'mu_k': best_row.get('param_mu_k'),
                'stick': best_row.get('param_stick'),
                'confirm_bars': best_row.get('param_confirm_bars'),
                'dom_thresh': best_row.get('param_dom_thresh'),
                'max_dd_pct': best_row['max_drawdown_pct'],
                'profit_factor': best_row['profit_factor']
            }

for tf, data in sorted(best_per_tf.items(), key=lambda x: str(x[0])):
    print(f"TF {tf}m: Score {data['score']:.4f}")
    print(f"  Params: obs_len={data['obs_len']}, stat_len={data['stat_len']}, mu_k={data['mu_k']}, stick={data['stick']}, confirm_bars={data['confirm_bars']}, dom_thresh={data['dom_thresh']}")
    print(f"  Metrics: Max DD={data['max_dd_pct']:.2f}%, PF={data['profit_factor']:.2f}")

