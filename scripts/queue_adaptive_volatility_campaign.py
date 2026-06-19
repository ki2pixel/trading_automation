#!/usr/bin/env python3
import sys
import os
import re
import time
import math
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

def get_excluded_match(symbol: str) -> str | None:
    symbol_clean = symbol.lower().replace("_", "").replace(".", "")
    for ex in EXCLUSIONS_LOWER:
        ex_clean = ex.replace("_", "").replace(".", "")
        if symbol_clean.startswith(ex_clean) or ex_clean in symbol_clean:
            return ex
    return None

def parse_eligible_targets(report_path: Path) -> list[tuple[str, str]]:
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
            
            if strategy == "adaptive_volatility_trend":
                ex_match = get_excluded_match(symbol)
                if not ex_match:
                    targets.append((symbol, timeframe))
    return targets

def timeframe_to_minutes(tf_str: str) -> int:
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

def calculate_bayesian_iterations(canonical_iterations: int) -> int:
    # Logique identique au frontend pour l'intensité "deep" (Approfondi)
    # Multiplier: 0.0256, Min: 1000, Max: 24000
    multiplier = 0.0256
    calculated = round(canonical_iterations * multiplier)
    clamped = max(1000, min(calculated, 24000))
    return clamped

def main() -> None:
    report_path = repo_root / "reports" / "screening_report_new_symbols.md"
    if not report_path.exists():
        print(f"Erreur: Le rapport {report_path} est introuvable.")
        sys.exit(1)

    print("Lecture et filtrage des candidats depuis le rapport de screening...")
    targets = parse_eligible_targets(report_path)
    print(f"Trouvé {len(targets)} candidats valides pour adaptive_volatility_trend.")

    # Définition des paramètres à optimiser alignée sur la Passe 1 :
    # - length (10 à 50, pas de 1)
    # - atr_len (7 à 28, pas de 1)
    # - atr_mult (1.0 à 4.0, pas de 0.1)
    parameters_payload = [
        {"name": "length", "kind": "numeric", "start": 10, "end": 50, "step": 1},
        {"name": "atr_len", "kind": "numeric", "start": 7, "end": 28, "step": 1},
        {"name": "atr_mult", "kind": "numeric", "start": 1.0, "end": 4.0, "step": 0.1}
    ]

    # Paramètres bloqués de la Passe 1
    fixed_overrides = {
        "use_rsi_filter": False,
        "use_volume_filter": False,
        "use_safety_stop": False
    }

    # Calculer l'espace des itérations
    specs = [build_parameter_spec(p["name"], p, strategy="adaptive_volatility_trend") for p in parameters_payload]
    raw_iterations = estimate_iterations(specs)
    grid_validation = validate_parameter_grid(
        specs,
        fixed_overrides=None,
        strategy="adaptive_volatility_trend",
        optimization_mode="bayesian"
    )
    canonical_iterations = grid_validation["canonical_iterations"]

    # Calculer le nombre de runs pour l'intensité bayésienne
    bayesian_max_iterations = calculate_bayesian_iterations(canonical_iterations)

    print(f"Espace de recherche : {raw_iterations} combinatoires brutes.")
    print(f"Espace canonique valide : {canonical_iterations} combinaisons.")
    print(f"Intensité Bayésienne (Approfondi ~2.6%): {bayesian_max_iterations} essais (trials) par job.")

    # Ouvrir la base de données de jobs
    store = OptimizerJobStore()
    print(f"Connexion à la base de données SQLite : {store.storage_path}")

    # Enregistrer les jobs
    print("Enregistrement des jobs dans la file d'attente...")
    queued_count = 0
    for symbol, tf_str in targets:
        tf_min = timeframe_to_minutes(tf_str)
        
        # Payload de requête
        request_payload = {
            "strategy": "adaptive_volatility_trend",
            "symbol": symbol,
            "timeframe_minutes": tf_min,
            "timeframe": tf_str,
            "optimization_mode": "bayesian",
            "max_iterations": bayesian_max_iterations,
            "early_stop_drawdown_pct": 0,
            "enable_convergence_stop": True,
            "convergence_patience": 600,
            "circuit_breaker_ratio": 1.0,
            "use_vectorbt_prescan": True,
            "run_post_validation": True,
            "workers": 15,
            "min_closed_trades": 10,
            "max_drawdown_pct": -25.0,
            "min_exposure_pct": 3.0,
            "min_profit_factor": 1.25,
            "max_rows": None,
            "write_best_run": True,
            "score_metric": "return_vs_buy_hold_pct_points",
            "score_direction": "max",
            "parameters": parameters_payload,
            "fixed_overrides": fixed_overrides
        }

        # Création de l'objet de job
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
