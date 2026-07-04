#!/usr/bin/env python3
import sys
import time
from uuid import uuid4
from pathlib import Path
from typing import Any

# Add root directory to python path for backtest_engine imports
repo_root = Path(__file__).resolve().parents[1]
sys.path.append(str(repo_root))

from backtest_engine.job_store import OptimizerJob, OptimizerJobStore
from backtest_engine.optimizer import estimate_iterations, validate_parameter_grid, build_parameter_spec

# Hardcoded targets from Passe 1 validated configurations (extension only, min_closed_trades = 50)
# Format: (symbol, timeframe, rsi_period, qqe_factor, rsi_smoothing, ob, os, signal_mode)
TARGET_CONFIGS: list[tuple[str, str, int, float, int, float, float, str]] = [
    ("belgbeeur", "10m", 22, 5.0, 15, 90.0, 24.0, "Live"),
    ("daideeur", "15m", 17, 4.1, 5, 89.0, 10.0, "Close"),
    ("cpriteur", "10m", 17, 2.3, 7, 66.0, 31.0, "Close"),
    ("cafreur", "15m", 15, 1.5, 10, 82.0, 23.0, "Close"),
    ("vnadeeur", "10m", 16, 1.6, 15, 76.0, 20.0, "Live"),
    ("akzanleur", "30m", 29, 6.0, 12, 90.0, 10.0, "Live"),
    ("randnleur", "10m", 18, 6.0, 2, 73.0, 28.0, "Live"),
    ("vpknleur", "15m", 27, 1.9, 4, 66.0, 34.0, "Close"),
    ("beideeur", "15m", 27, 2.9, 15, 67.0, 18.0, "Live")
]

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
    multiplier = 0.0256
    calculated = round(canonical_iterations * multiplier)
    clamped = max(1000, min(calculated, 24000))
    return clamped

def main() -> None:
    print("Initialisation de la Passe 2 (Gestion du Risque) de momentum_based_zigzag pour les 9 actifs qualifiés...")
    
    # Définition des paramètres à optimiser (Passe 2)
    parameters_payload: list[dict[str, Any]] = [
        {"name": "enable_stop_loss", "kind": "choice", "values": [True]},
        {"name": "enable_take_profit", "kind": "choice", "values": [True]},
        {"name": "stop_loss_pct", "kind": "numeric", "start": 0.5, "end": 5.0, "step": 0.1},
        {"name": "take_profit_pct", "kind": "numeric", "start": 1.0, "end": 15.0, "step": 0.1}
    ]

    # Calculer l'espace des itérations
    specs = [build_parameter_spec(p["name"], p, strategy="momentum_based_zigzag") for p in parameters_payload]
    raw_iterations = estimate_iterations(specs)
    grid_validation = validate_parameter_grid(
        specs,
        fixed_overrides=None,
        strategy="momentum_based_zigzag",
        optimization_mode="bayesian"
    )
    canonical_iterations = grid_validation["canonical_iterations"]

    # Calculer le nombre de runs pour l'intensité bayésienne
    bayesian_max_iterations = calculate_bayesian_iterations(canonical_iterations)

    print(f"Espace de recherche : {raw_iterations} combinatoires brutes.")
    print(f"Espace canonique valide : {canonical_iterations} combinaisons.")
    print(f"Intensité Bayésienne (Approfondi) : {bayesian_max_iterations} essais (trials) par job.")

    # Ouvrir la base de données de jobs
    store = OptimizerJobStore()
    print(f"Connexion à la base de données SQLite : {store.storage_path}")

    # Enregistrer les jobs
    print("Enregistrement des jobs dans la file d'attente...")
    queued_count = 0
    for symbol, tf_str, rsi_period, qqe_factor, rsi_smoothing, ob, os, signal_mode in TARGET_CONFIGS:
        tf_min = timeframe_to_minutes(tf_str)
        
        # Paramètres bloqués de Passe 1 spécifiques à cet actif
        fixed_overrides: dict[str, Any] = {
            "use_safety_stop": False,
            "enable_trailing_stop": False,
            "rsi_period": int(rsi_period),
            "qqe_factor": float(qqe_factor),
            "rsi_smoothing": int(rsi_smoothing),
            "ob": float(ob),
            "os": float(os),
            "signal_mode": str(signal_mode)
        }
        
        # Payload de requête
        request_payload: dict[str, Any] = {
            "strategy": "momentum_based_zigzag",
            "symbol": symbol,
            "timeframe_minutes": tf_min,
            "timeframe": tf_str,
            "optimization_mode": "bayesian",
            "max_iterations": bayesian_max_iterations,
            "early_stop_drawdown_pct": 0,
            "enable_convergence_stop": True,
            "convergence_patience": 300,
            "circuit_breaker_ratio": 0.3,
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
        print(f"  -> Job enfilé pour {symbol} {tf_str} (Core bloqué: rsi_period={rsi_period}, qqe_factor={qqe_factor}, rsi_smoothing={rsi_smoothing}, ob={ob}, os={os}, signal_mode='{signal_mode}')")

    print(f"\nSuccès ! {queued_count} jobs d'optimisation Passe 2 ont été ajoutés à la base de données SQLite.")
    print("Démarrez le worker avec : ./start_backtest_engine.sh start (ou via l'UI) pour lancer l'exécution.")

if __name__ == "__main__":
    main()
