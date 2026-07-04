#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'automatisation de file d'attente de jobs d'optimisation pour la stratégie
Momentum-based ZigZag (Passe 2 - Gestion du Risque) sur les actifs cryptos qualifiés.
"""

import sys
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
    # 4 configurations cibles cryptos qualifiées en Passe 1 (Cœur QQE & Oscillateur)
    # Les paramètres de la Passe 1 (rsi_period, qqe_factor, rsi_smoothing, ob, os, signal_mode) sont figés.
    # On optimise les seuils de stop_loss_pct (1.0% à 10.0%, pas de 0.5%) et take_profit_pct (2.0% à 25.0%, pas de 1.0%).
    targets: List[Dict[str, Any]] = [
        {
            "symbol": "dotusdt",
            "timeframe": "30min",
            "rsi_period": 21,
            "qqe_factor": 5.7,
            "rsi_smoothing": 12,
            "ob": 65.0,
            "os": 33.0,
            "signal_mode": "Live"
        },
        {
            "symbol": "dotusdt",
            "timeframe": "45min",
            "rsi_period": 30,
            "qqe_factor": 3.0,
            "rsi_smoothing": 4,
            "ob": 85.0,
            "os": 16.0,
            "signal_mode": "Close"
        },
        {
            "symbol": "ltcusdt",
            "timeframe": "30min",
            "rsi_period": 8,
            "qqe_factor": 6.0,
            "rsi_smoothing": 8,
            "ob": 75.0,
            "os": 27.0,
            "signal_mode": "Live"
        },
        {
            "symbol": "ltcusdt",
            "timeframe": "45min",
            "rsi_period": 10,
            "qqe_factor": 3.8,
            "rsi_smoothing": 13,
            "ob": 76.0,
            "os": 29.0,
            "signal_mode": "Live"
        }
    ]

    # Connexion à la base de données de jobs SQLite
    try:
        store = OptimizerJobStore()
        print(f"Connexion à la base de données SQLite : {store.storage_path}")
    except Exception as e:
        print(f"Erreur lors de la connexion à SQLite : {e}")
        sys.exit(1)

    print("Enregistrement des jobs de Passe 2 dans la file d'attente...")
    queued_count = 0

    for target in targets:
        symbol = target["symbol"]
        tf_str = target["timeframe"]
        
        try:
            tf_min = timeframe_to_minutes(tf_str)
            
            # Grille de paramètres dynamique par actif (Passe 2)
            parameters_payload: List[Dict[str, Any]] = [
                {"name": "rsi_period", "kind": "choice", "values": [int(target["rsi_period"])]},
                {"name": "qqe_factor", "kind": "choice", "values": [float(target["qqe_factor"])]},
                {"name": "rsi_smoothing", "kind": "choice", "values": [int(target["rsi_smoothing"])]},
                {"name": "ob", "kind": "choice", "values": [float(target["ob"])]},
                {"name": "os", "kind": "choice", "values": [float(target["os"])]},
                {"name": "signal_mode", "kind": "choice", "values": [str(target["signal_mode"])]},
                {"name": "enable_stop_loss", "kind": "choice", "values": [True]},
                {"name": "enable_take_profit", "kind": "choice", "values": [True]},
                {"name": "stop_loss_pct", "kind": "numeric", "start": 1.0, "end": 10.0, "step": 0.5},
                {"name": "take_profit_pct", "kind": "numeric", "start": 2.0, "end": 25.0, "step": 1.0}
            ]

            # Overrides fixes pour la Passe 2
            fixed_overrides = {
                "use_safety_stop": False,
                "enable_trailing_stop": False
            }

            # Validation de la grille de paramètres et estimation des itérations
            specs = [build_parameter_spec(p["name"], p, strategy="momentum_based_zigzag") for p in parameters_payload]
            raw_iterations = estimate_iterations(specs)
            grid_validation = validate_parameter_grid(
                specs,
                fixed_overrides=None,
                strategy="momentum_based_zigzag",
                optimization_mode="bayesian"
            )
            canonical_iterations = grid_validation["canonical_iterations"]
            
            # Profondeur de recherche bayésienne
            bayesian_max_iterations = 1000

            # Construction du payload de requête
            request_payload = {
                "strategy": "momentum_based_zigzag",
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
                "fixed_overrides": fixed_overrides
            }

            # Instanciation de l'objet de job
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
            
            # Ajout en BDD SQLite (statut 'queued' par défaut)
            store.add(job)
            queued_count += 1
            print(f"  [Enregistré] Job Passe 2 pour {symbol} {tf_str} (Grid Size: {canonical_iterations})")
        except Exception as e:
            print(f"  [Erreur] Impossible d'enregistrer le job Passe 2 pour {symbol} {tf_str} : {e}")

    print(f"\nSuccès ! {queued_count} jobs de Passe 2 ont été ajoutés à la base de données SQLite.")
    print("Démarrez le worker avec : ./start_backtest_engine.sh start (ou via l'UI) pour lancer l'exécution.")


if __name__ == "__main__":
    main()
