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

# Hardcoded targets from Passe 1 validated configurations (min_closed_trades = 10)
# (symbol, timeframe, length, atr_len, atr_mult)
TARGET_CONFIGS = [
    ("akzanleur", "30m", 25, 12, 3.5),
    ("ergiteur", "30m", 16, 27, 3.5),
    ("beideeur", "10m", 47, 25, 3.6),
    ("telnonok", "15m", 26, 19, 2.6),
    ("dpwdeeur", "45m", 45, 10, 3.9),
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
    print(f"Initialisation de la Passe 2 (Filtres) d'Adaptive Volatility Trend pour les 5 configurations qualifiées...")
    
    # Définition des paramètres de filtres à optimiser (Passe 2)
    parameters_payload = [
        {"name": "use_rsi_filter", "kind": "choice", "values": [True, False]},
        {"name": "use_volume_filter", "kind": "choice", "values": [True, False]},
        {"name": "rsi_len", "kind": "numeric", "start": 7, "end": 21, "step": 1},
        {"name": "rsi_overbought", "kind": "numeric", "start": 60, "end": 80, "step": 1},
        {"name": "rsi_oversold", "kind": "numeric", "start": 20, "end": 40, "step": 1}
    ]

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
    print(f"Intensité Bayésienne (Approfondi): {bayesian_max_iterations} essais (trials) par job.")

    # Ouvrir la base de données de jobs
    store = OptimizerJobStore()
    print(f"Connexion à la base de données SQLite : {store.storage_path}")

    # Enregistrer les jobs
    print("Enregistrement des jobs dans la file d'attente...")
    queued_count = 0
    for symbol, tf_str, length, atr_len, atr_mult in TARGET_CONFIGS:
        tf_min = timeframe_to_minutes(tf_str)
        
        # Paramètres bloqués de Passe 1 spécifiques à cet actif
        fixed_overrides = {
            "use_safety_stop": False,
            "length": int(length),
            "atr_len": int(atr_len),
            "atr_mult": float(atr_mult)
        }
        
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
        print(f"  -> Job enfilé pour {symbol} {tf_str} (Core bloqué: length={length}, atr_len={atr_len}, atr_mult={atr_mult})")

    print(f"\nSuccès ! {queued_count} jobs d'optimisation Passe 2 ont été ajoutés à la base de données SQLite.")
    print("Démarrez le worker avec : ./start_backtest_engine.sh start")

if __name__ == "__main__":
    main()
