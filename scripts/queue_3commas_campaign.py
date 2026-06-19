#!/usr/bin/env python3
import sys
import os
import time
from uuid import uuid4
from pathlib import Path

# Add root directory to python path for backtest_engine imports
repo_root = Path(__file__).resolve().parents[1]
sys.path.append(str(repo_root))

from backtest_engine.job_store import OptimizerJob, OptimizerJobStore
from backtest_engine.optimizer import estimate_iterations, validate_parameter_grid, build_parameter_spec

EXCLUSIONS = {
    "NVO", "AMS.MC", "EVD.DE", "FPE.DE", "GMAB", "LOGI", "NVS", "SAP", "SHL.DE", "ZEAL.CO"
}
EXCLUSIONS_LOWER = {s.lower() for s in EXCLUSIONS}

def get_excluded_match(symbol):
    symbol_clean = symbol.lower().replace("_", "").replace(".", "")
    for ex in EXCLUSIONS_LOWER:
        ex_clean = ex.replace("_", "").replace(".", "")
        if symbol_clean.startswith(ex_clean) or ex_clean in symbol_clean:
            return ex
    return None

def parse_eligible_targets(report_path):
    with open(report_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    in_table = False
    targets = []

    for line in lines:
        line = line.strip()
        if line.startswith("## 1. Candidats Qualifiés"):
            in_table = True
            continue
        if in_table and line.startswith("##"):
            break
        if in_table and line.startswith("|"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if not parts or parts[0].startswith("---") or parts[0].startswith(":-") or "Symbole" in parts[0]:
                continue
            
            symbol = parts[0].replace("**", "").strip()
            timeframe = parts[1].replace("**", "").strip()
            strategy = parts[2].replace("`", "").strip()
            
            if strategy == "3commas_bot":
                ex_match = get_excluded_match(symbol)
                if not ex_match:
                    targets.append((symbol, timeframe))
    return targets

def timeframe_to_minutes(tf_str):
    tf_str = tf_str.lower().strip()
    if tf_str.endswith("min"):
        return int(tf_str[:-3])
    if tf_str.endswith("m"):
        return int(tf_str[:-1])
    if tf_str.endswith("h"):
        return int(tf_str[:-1]) * 60
    if tf_str.endswith("d"):
        return int(tf_str[:-1]) * 1440
    raise ValueError(f"Timeframe inconnu: {tf_str}")

def calculate_bayesian_iterations(canonical_iterations):
    multiplier = 0.0256
    calculated = round(canonical_iterations * multiplier)
    clamped = max(1000, min(calculated, 24000))
    return clamped

def main():
    report_path = repo_root / "reports" / "screening_report_new_symbols.md"
    if not report_path.exists():
        print(f"Erreur: Le rapport {report_path} est introuvable.")
        sys.exit(1)

    print("Lecture et filtrage des candidats depuis le rapport de screening...")
    targets = parse_eligible_targets(report_path)
    print(f"Trouvé {len(targets)} candidats valides pour 3commas_bot.")

    ma_types = ["EMA", "HEMA", "SMA", "HMA", "WMA", "DEMA", "VWMA", "VWAP", "T3"]
    parameters_payload = [
        {"name": "ma_type1", "kind": "choice", "options": ma_types},
        {"name": "ma_type2", "kind": "choice", "options": ma_types},
        {"name": "ma_length1", "kind": "numeric", "start": 5, "end": 100, "step": 1},
        {"name": "ma_length2", "kind": "numeric", "start": 10, "end": 200, "step": 1}
    ]

    fixed_overrides = {
        "trail_stop": False,
        "rnr": 1.0,
        "risk_m": 1.0,
        "use_safety_stop": False
    }

    # Calculer l'espace des itérations
    specs = [build_parameter_spec(p["name"], p, strategy="3commas_bot") for p in parameters_payload]
    raw_iterations = estimate_iterations(specs)
    grid_validation = validate_parameter_grid(
        specs,
        fixed_overrides=None,
        strategy="3commas_bot",
        optimization_mode="grid"
    )
    canonical_iterations = grid_validation["canonical_iterations"]

    bayesian_max_iterations = calculate_bayesian_iterations(canonical_iterations)

    print(f"Espace de recherche : {raw_iterations} combinatoires brutes.")
    print(f"Espace canonique valide : {canonical_iterations} combinaisons.")
    print(f"Intensité Bayésienne (Approfondi ~2.6%): {bayesian_max_iterations} essais (trials) par job.")

    store = OptimizerJobStore()
    print(f"Connexion à la base de données SQLite : {store.storage_path}")

    print("Enregistrement des jobs dans la file d'attente...")
    queued_count = 0
    for symbol, tf_str in targets:
        tf_min = timeframe_to_minutes(tf_str)
        
        request_payload = {
            "strategy": "3commas_bot",
            "symbol": symbol,
            "timeframe_minutes": tf_min,
            "timeframe": tf_str,
            "optimization_mode": "bayesian",
            "max_iterations": bayesian_max_iterations,
            "early_stop_drawdown_pct": 0,
            "enable_convergence_stop": True,
            "convergence_patience": 300,
            "circuit_breaker_ratio": 0.2,
            "use_vectorbt_prescan": True,
            "run_post_validation": True,
            "workers": 15,
            "min_closed_trades": 80,
            "max_drawdown_pct": -25.0,
            "min_exposure_pct": 3.0,
            "min_profit_factor": 1.25,
            "max_rows": None,
            "write_best_run": True,
            "score_metric": "sortino_ratio",
            "score_direction": "max",
            "parameters": parameters_payload,
            "fixed_overrides": fixed_overrides
        }

        job = OptimizerJob(
            id=uuid4().hex,
            created_at=time.time(),
            request=request_payload,
            progress={
                "currentIteration": 0,
                "totalIterations": bayesian_max_iterations,
                "rawIterations": raw_iterations
            }
        )
        
        store.add(job)
        queued_count += 1

    print(f"Succès ! {queued_count} jobs d'optimisation ont été ajoutés à la base de données SQLite.")
    print("Démarrez le worker avec : ./start_backtest_engine.sh start (ou via l'UI) pour lancer l'exécution.")

if __name__ == "__main__":
    main()
