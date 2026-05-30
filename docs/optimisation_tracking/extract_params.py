import os
import json

base_dir = "/mnt/venv_ext4/trading_automation_v2/reports/local_optimizer/noise_boundary_intraday"

# On va chercher les meilleurs scores globaux par symbole/timeframe
best_by_sym_tf = {}

for symbol in os.listdir(base_dir):
    sym_dir = os.path.join(base_dir, symbol)
    if not os.path.isdir(sym_dir): continue
    
    for run in os.listdir(sym_dir):
        run_dir = os.path.join(sym_dir, run)
        if not os.path.isdir(run_dir): continue
        
        summary_path = os.path.join(run_dir, "summary.json")
        config_path = os.path.join(run_dir, "optimization_config.json")
        rec_path = os.path.join(run_dir, "recommendations.json")
        
        eligible = 0
        tf = "Unknown"
        best_score = None
        params = {}
        
        if os.path.exists(summary_path):
            try:
                with open(summary_path, 'r') as f:
                    data = json.load(f)
                    eligible = data.get("eligible_iterations", 0)
            except: pass
                
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    cdata = json.load(f)
                    if "timeframe_minutes" in cdata:
                        tf = f"{cdata['timeframe_minutes']}m"
            except: pass
                
        if eligible > 0 and os.path.exists(rec_path):
            try:
                with open(rec_path, 'r') as f:
                    rdata = json.load(f)
                    best_info = rdata.get("best", {})
                    if best_info:
                        best_score = best_info.get("score")
                        params = best_info.get("parameters", {})
            except: pass

        if best_score is not None:
            key = (symbol, tf)
            if key not in best_by_sym_tf or best_score > best_by_sym_tf[key]['score']:
                best_by_sym_tf[key] = {
                    'score': best_score,
                    'params': params,
                    'eligible': eligible
                }

# Symbols on veut analyser
targets = ["AMS.MC", "FPE.DE", "GMAB", "NVO", "NVS", "SHL.DE"]

print("Paramètres 'Sweet Spots' de la Passe 1 :")
print("-" * 80)
for (sym, tf), data in sorted(best_by_sym_tf.items()):
    if sym in targets and data['eligible'] > 0:
        # On va afficher seulement ceux qui ont des scores corrects ou les top TF
        p = data['params']
        lb = p.get('lookback_days')
        v_in = p.get('volatility_multiplier_enter')
        v_out = p.get('volatility_multiplier_exit')
        
        print(f"[{sym} - {tf}] (Score: {data['score']:.2f} | Éligibles: {data['eligible']})")
        print(f"  -> lookback_days : {lb}")
        print(f"  -> volatility_multiplier_enter : {v_in}")
        print(f"  -> volatility_multiplier_exit : {v_out}")
        print()
