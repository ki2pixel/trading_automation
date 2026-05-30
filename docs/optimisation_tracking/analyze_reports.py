#!/usr/bin/env python3
import os
import json
import argparse
import sys

def parse_args():
    parser = argparse.ArgumentParser(description="Analyse les rapports de l'optimiseur local de trading.")
    parser.add_argument(
        "report_dir",
        type=str,
        help="Chemin vers le répertoire de rapports (ex: /mnt/venv_ext4/trading_automation_v2/reports/local_optimizer/noise_boundary_intraday)"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    base_dir = args.report_dir

    if not os.path.exists(base_dir):
        print(f"Erreur : Le répertoire spécifié n'existe pas : {base_dir}")
        sys.exit(1)

    results = {}

    for symbol in os.listdir(base_dir):
        sym_dir = os.path.join(base_dir, symbol)
        if not os.path.isdir(sym_dir): continue
        
        results[symbol] = []
        
        for run in os.listdir(sym_dir):
            run_dir = os.path.join(sym_dir, run)
            if not os.path.isdir(run_dir): continue
            
            summary_path = os.path.join(run_dir, "summary.json")
            config_path = os.path.join(run_dir, "optimization_config.json")
            rec_path = os.path.join(run_dir, "recommendations.json")
            
            eligible = 0
            tf = "Unknown"
            best_score = None
            
            # Read summary for eligible iterations
            if os.path.exists(summary_path):
                try:
                    with open(summary_path, 'r') as f:
                        data = json.load(f)
                        eligible = data.get("eligible_iterations", 0)
                except Exception:
                    pass
                    
            # Read config for timeframe
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        cdata = json.load(f)
                        if "timeframe_minutes" in cdata:
                            tf = f"{cdata['timeframe_minutes']}m"
                        elif "timeframes" in cdata:
                            tf = ",".join(cdata["timeframes"])
                except Exception:
                    pass
                    
            # Read recommendations for best score if eligible > 0
            if eligible > 0 and os.path.exists(rec_path):
                try:
                    with open(rec_path, 'r') as f:
                        rdata = json.load(f)
                        best_info = rdata.get("best", {})
                        if best_info:
                            best_score = best_info.get("score")
                except Exception:
                    pass

            results[symbol].append({
                "run": run,
                "eligible": eligible,
                "tf": tf,
                "best_score": best_score
            })

    # Print nicely formatted summary
    print(f"Analyse des rapports dans : {base_dir}")
    print("\nSymbol     | Timeframe | Eligible Iterations | Best Score")
    print("-" * 65)
    
    total_eligible = 0
    for sym, runs in sorted(results.items()):
        # Sort runs by timeframe string
        for r in sorted(runs, key=lambda x: str(x['tf'])):
            score_str = f"{r['best_score']:.4f}" if r['best_score'] is not None else "N/A"
            print(f"{sym:<10} | {r['tf']:<9} | {r['eligible']:<19} | {score_str}")
            total_eligible += r['eligible']
            
    print("-" * 65)
    print(f"Total des itérations éligibles sur l'ensemble : {total_eligible}")

if __name__ == "__main__":
    main()
