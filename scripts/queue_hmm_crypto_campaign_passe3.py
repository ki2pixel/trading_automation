#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'automatisation de file d'attente de jobs d'optimisation pour la stratégie
HMM Regime Filter (Passe 3 - Sorties & Brackets TP/SL Nettes) sur l'actif crypto qualifié BNBUSDT.
"""

import sys
import os
import time
from uuid import uuid4
from pathlib import Path
from typing import List, Dict, Any

# Résolution et ajout du chemin racine du dépôt au python path
repo_root = Path(__file__).resolve().parents[1]
sys.path.append(str(repo_root))

from backtest_engine.job_store import OptimizerJob, OptimizerJobStore
from backtest_engine.optimizer import estimate_iterations, validate_parameter_grid, build_parameter_spec


def timeframe_to_minutes(tf_str: str) -> int:
    """
    Convertit un timeframe textuel (ex: '15min', '1h') en nombre de minutes.
    
    Args:
        tf_str: Chaîne de caractères représentant le timeframe.
        
    Returns:
        La valeur équivalente en minutes.
    """
    tf_str = tf_str.lower().strip()
    if tf_str.endswith("min"):
        return int(tf_str[:-3])
    if tf_str.endswith("m"):
        return int(tf_str[:-1])
    if tf_str.endswith("h"):
        return int(tf_str[:-1]) * 60
    if tf_str.endswith("d"):
        return int(tf_str[:-1]) * 1440
    raise ValueError(f"Timeframe inconnu : {tf_str}")


def main() -> None:
    print("Préparation de la file d'attente pour la Passe 3 HMM Crypto (Sorties & Brackets TP/SL)...")

    # Actif validé en Passe 2 et ses paramètres optimaux
    symbol = "bnbusdt"
    tf_str = "60min"
    tf_min = timeframe_to_minutes(tf_str)
    
    opt_p2 = {
        "obs_len": 23,
        "stat_len": 77,
        "mu_k": 2.1,
        "stick": 0.9,
        "confirm_bars": 3,
        "dom_thresh": 0.6
    }

    # Définition des paramètres de la Passe 3
    # - Paramètres HMM & confirmation figés.
    # - Optimisation sur use_safety_stop (True, False), use_net_bracket_exits (True)
    # - take_profit_net_percent (1.0 à 20.0, step 1.0)
    # - stop_loss_net_percent (1.0 à 20.0, step 1.0)
    parameters_payload: List[Dict[str, Any]] = [
        {"name": "obs_len", "kind": "choice", "values": [opt_p2["obs_len"]]},
        {"name": "stat_len", "kind": "choice", "values": [opt_p2["stat_len"]]},
        {"name": "mu_k", "kind": "choice", "values": [opt_p2["mu_k"]]},
        {"name": "stick", "kind": "choice", "values": [opt_p2["stick"]]},
        {"name": "confirm_bars", "kind": "choice", "values": [opt_p2["confirm_bars"]]},
        {"name": "dom_thresh", "kind": "choice", "values": [opt_p2["dom_thresh"]]},
        {"name": "use_safety_stop", "kind": "choice", "values": [True, False]},
        {"name": "use_net_bracket_exits", "kind": "choice", "values": [True]},
        {"name": "take_profit_net_percent", "kind": "numeric", "start": 1.0, "end": 20.0, "step": 1.0},
        {"name": "stop_loss_net_percent", "kind": "numeric", "start": 1.0, "end": 20.0, "step": 1.0}
    ]

    print("Validation de la grille de paramètres et estimation des itérations...")
    try:
        specs = [build_parameter_spec(p["name"], p, strategy="hmm_regime_filter") for p in parameters_payload]
        raw_iterations = estimate_iterations(specs)
        grid_validation = validate_parameter_grid(
            specs,
            fixed_overrides=None,
            strategy="hmm_regime_filter",
            optimization_mode="grid"
        )
        canonical_iterations = grid_validation["canonical_iterations"]
    except Exception as e:
        print(f"Erreur de validation de la grille de paramètres : {e}")
        sys.exit(1)

    print(f"Espace de recherche : {raw_iterations} combinaisons brutes.")
    print(f"Espace canonique valide : {canonical_iterations} combinaisons réelles (use_safety_stop x TP [1-20] x SL [1-20]).")

    # Connexion à la base de données de jobs SQLite
    try:
        store = OptimizerJobStore()
        print(f"Connexion à la base de données SQLite : {store.storage_path}")
    except Exception as e:
        print(f"Erreur lors de la connexion à SQLite : {e}")
        sys.exit(1)

    print("Enregistrement du job de Passe 3 dans la file d'attente...")
    try:
        # Construction du payload de requête
        request_payload = {
            "strategy": "hmm_regime_filter",
            "symbol": symbol,
            "timeframe_minutes": tf_min,
            "timeframe": tf_str,
            "optimization_mode": "bayesian",
            "max_iterations": 1000,
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
            "fixed_overrides": None
        }

        # Instanciation de l'objet job
        job = OptimizerJob(
            id=uuid4().hex,
            created_at=time.time(),
            request=request_payload,
            progress={
                "currentIteration": 0,
                "totalIterations": 1000,
                "rawIterations": raw_iterations
            }
        )
        
        # Ajout en BDD
        store.add(job)
        print(f"Succès ! Le job de Passe 3 pour {symbol} ({tf_str}) a été ajouté à la base de données SQLite.")
        print("Démarrez le worker avec : ./start_backtest_engine.sh start pour lancer l'exécution.")
    except Exception as e:
        print(f"Erreur lors de l'enregistrement du job Passe 3 : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
