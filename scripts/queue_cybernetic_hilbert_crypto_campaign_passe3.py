#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'automatisation de file d'attente de jobs d'optimisation pour la stratégie
Cybernetic Hilbert (Passe 3 - Stops Temporels / Safety Stop) sur les actifs cryptos qualifiés.
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
    # 7 configurations cibles cryptos qualifiées divisées selon les résultats de la Passe 2.
    # Pour le Groupe Phase, on active phase_mode_enabled=True et on fige require_cycling_bars=1.
    # Pour le Groupe Trend, on désactive phase_mode_enabled=False.
    # Pour tous, on active use_safety_stop=True et on optimise safety_max_bars_in_trade de 0 à 50 (pas de 5).
    targets: List[Dict[str, Any]] = [
        # --- Groupe Phase (Qualifiés Passe 2) ---
        {
            "symbol": "aptusdt",
            "timeframe": "10min",
            "hilbert_smooth_period": 12,
            "take_profit_net_percent": 18.0,
            "stop_loss_net_percent": 1.0,
            "phase_mode_enabled": True,
            "require_cycling_bars": 1
        },
        {
            "symbol": "dotusdt",
            "timeframe": "10min",
            "hilbert_smooth_period": 10,
            "take_profit_net_percent": 20.0,
            "stop_loss_net_percent": 1.0,
            "phase_mode_enabled": True,
            "require_cycling_bars": 1
        },
        {
            "symbol": "dotusdt",
            "timeframe": "45min",
            "hilbert_smooth_period": 8,
            "take_profit_net_percent": 19.0,
            "stop_loss_net_percent": 1.0,
            "phase_mode_enabled": True,
            "require_cycling_bars": 1
        },
        {
            "symbol": "ltcusdt",
            "timeframe": "30min",
            "hilbert_smooth_period": 9,
            "take_profit_net_percent": 20.0,
            "stop_loss_net_percent": 1.0,
            "phase_mode_enabled": True,
            "require_cycling_bars": 1
        },
        # --- Groupe Trend (Échoués Passe 2 mais qualifiés Passe 1) ---
        {
            "symbol": "ethusdt",
            "timeframe": "45min",
            "hilbert_smooth_period": 9,
            "take_profit_net_percent": 19.0,
            "stop_loss_net_percent": 1.0,
            "phase_mode_enabled": False,
            "require_cycling_bars": None
        },
        {
            "symbol": "dotusdt",
            "timeframe": "1h",
            "hilbert_smooth_period": 6,
            "take_profit_net_percent": 19.0,
            "stop_loss_net_percent": 1.0,
            "phase_mode_enabled": False,
            "require_cycling_bars": None
        },
        {
            "symbol": "ltcusdt",
            "timeframe": "45min",
            "hilbert_smooth_period": 12,
            "take_profit_net_percent": 20.0,
            "stop_loss_net_percent": 1.0,
            "phase_mode_enabled": False,
            "require_cycling_bars": None
        }
    ]

    # Connexion à la base de données de jobs SQLite
    try:
        store = OptimizerJobStore()
        print(f"Connexion à la base de données SQLite : {store.storage_path}")
    except Exception as e:
        print(f"Erreur lors de la connexion à SQLite : {e}")
        sys.exit(1)

    print("Enregistrement des jobs de Passe 3 dans la file d'attente...")
    queued_count = 0

    for target in targets:
        symbol = target["symbol"]
        tf_str = target["timeframe"]
        
        try:
            tf_min = timeframe_to_minutes(tf_str)
            
            # Grille de paramètres dynamique par actif (Passe 3)
            parameters_payload: List[Dict[str, Any]] = [
                {"name": "hilbert_smooth_period", "kind": "choice", "values": [target["hilbert_smooth_period"]]},
                {"name": "phase_mode_enabled", "kind": "choice", "values": [target["phase_mode_enabled"]]},
                {"name": "use_net_bracket_exits", "kind": "choice", "values": [True]},
                {"name": "use_safety_stop", "kind": "choice", "values": [True]},
                {"name": "take_profit_net_percent", "kind": "choice", "values": [target["take_profit_net_percent"]]},
                {"name": "stop_loss_net_percent", "kind": "choice", "values": [target["stop_loss_net_percent"]]},
                {"name": "safety_max_bars_in_trade", "kind": "numeric", "start": 0, "end": 50, "step": 5}
            ]

            # Si le mode Phase est activé, on fige également le paramètre require_cycling_bars=1
            if target["phase_mode_enabled"]:
                parameters_payload.append(
                    {"name": "require_cycling_bars", "kind": "choice", "values": [target["require_cycling_bars"]]}
                )

            # Validation de la grille de paramètres et estimation des itérations
            specs = [build_parameter_spec(p["name"], p, strategy="cybernetic_hilbert") for p in parameters_payload]
            raw_iterations = estimate_iterations(specs)
            grid_validation = validate_parameter_grid(
                specs,
                fixed_overrides=None,
                strategy="cybernetic_hilbert",
                optimization_mode="grid"
            )
            canonical_iterations = grid_validation["canonical_iterations"]
            
            # Fidélité aux standards de la Passe 3 : 1000 essais
            bayesian_max_iterations = 1000

            # Construction du payload de requête
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
            print(f"  [Enregistré] Job Passe 3 pour {symbol} {tf_str} (Grid Size: {canonical_iterations}, Phase Mode: {target['phase_mode_enabled']})")
        except Exception as e:
            print(f"  [Erreur] Impossible d'enregistrer le job Passe 3 pour {symbol} {tf_str} : {e}")

    print(f"\nSuccès ! {queued_count} jobs de Passe 3 ont été ajoutés à la base de données SQLite.")
    print("Démarrez le worker avec : ./start_backtest_engine.sh start (ou via l'UI) pour lancer l'exécution.")


if __name__ == "__main__":
    main()
