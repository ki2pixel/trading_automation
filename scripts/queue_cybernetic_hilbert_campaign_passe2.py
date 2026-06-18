#!/usr/bin/env python3
import sys
import os
import time
from uuid import uuid4
from pathlib import Path
from typing import Dict, Any

# Add root directory to python path for backtest_engine imports
repo_root = Path(__file__).resolve().parents[1]
sys.path.append(str(repo_root))

from backtest_engine.job_store import OptimizerJob, OptimizerJobStore
from backtest_engine.optimizer import estimate_iterations, validate_parameter_grid, build_parameter_spec

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

def main() -> None:
    # Cibles qualifiées depuis la Passe 1 (Mode Tendance)
    # Les paramètres de base sont désormais figés. On active 'phase_mode_enabled'
    # et on optimise 'require_cycling_bars' (1 à 5).
    targets = {
        "lxsdeeur": {
            "timeframe": "60min",
            "hilbert_smooth_period": 14,
            "take_profit_net_percent": 20.0,
            "stop_loss_net_percent": 1.0
        },
        "mrkdeeur": {
            "timeframe": "45min",
            "hilbert_smooth_period": 12,
            "take_profit_net_percent": 9.0,
            "stop_loss_net_percent": 1.0
        }
    }

    # Ouvrir la base de données de jobs
    store = OptimizerJobStore()
    print(f"Connexion à la base de données SQLite : {store.storage_path}")

    # Enregistrer les jobs
    print("Enregistrement des jobs de Passe 2 dans la file d'attente...")
    queued_count = 0
    
    for symbol, params in targets.items():
        tf_str = str(params["timeframe"])
        tf_min = timeframe_to_minutes(tf_str)
        
        # Grille de paramètres dynamique par actif (Passe 2)
        parameters_payload = [
            {"name": "hilbert_smooth_period", "kind": "choice", "values": [params["hilbert_smooth_period"]]},
            {"name": "phase_mode_enabled", "kind": "choice", "values": [True]},
            {"name": "use_net_bracket_exits", "kind": "choice", "values": [True]},
            {"name": "use_safety_stop", "kind": "choice", "values": [False]},
            {"name": "take_profit_net_percent", "kind": "choice", "values": [params["take_profit_net_percent"]]},
            {"name": "stop_loss_net_percent", "kind": "choice", "values": [params["stop_loss_net_percent"]]},
            {"name": "require_cycling_bars", "kind": "numeric", "start": 1, "end": 5, "step": 1}
        ]

        # Calculer l'espace des itérations
        specs = [build_parameter_spec(p["name"], p, strategy="cybernetic_hilbert") for p in parameters_payload]
        raw_iterations = estimate_iterations(specs)
        grid_validation = validate_parameter_grid(
            specs,
            fixed_overrides=None,
            strategy="cybernetic_hilbert",
            optimization_mode="grid"
        )
        canonical_iterations = grid_validation["canonical_iterations"]
        
        # Fidélité aux archives de la Passe 2 : n_trials = 1000 même pour une petite grille
        bayesian_max_iterations = 1000 
        
        request_payload = {
            "strategy": "cybernetic_hilbert",
            "symbol": symbol,
            "timeframe_minutes": tf_min,
            "timeframe": tf_str,
            "optimization_mode": "bayesian",
            "max_iterations": bayesian_max_iterations,
            "early_stop_drawdown_pct": 0,
            "enable_convergence_stop": True,
            "convergence_patience": 1000,
            "circuit_breaker_ratio": 1.0,
            "use_vectorbt_prescan": True,
            "run_post_validation": True,
            "workers": 15,
            "min_closed_trades": 50,
            "max_drawdown_pct": -25.0,
            "min_exposure_pct": 3.0,
            "min_profit_factor": 1.25,
            "max_rows": None,
            "write_best_run": True,
            "score_metric": "return_vs_buy_hold_pct_points",
            "score_direction": "max",
            "parameters": parameters_payload,
            "fixed_overrides": {}
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
        print(f"File d'attente -> {symbol} {tf_str} (Grid Size: {canonical_iterations})")

    print(f"Succès ! {queued_count} jobs de Passe 2 ajoutés à SQLite.")
    print("Démarrez le worker avec : ./start_backtest_engine.sh start (ou via l'UI) pour lancer l'exécution.")

if __name__ == "__main__":
    main()
