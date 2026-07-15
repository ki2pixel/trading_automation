#!/usr/bin/env python3
import sys
import time
from uuid import uuid4
from pathlib import Path

# Add root directory to python path for backtest_engine imports
repo_root = Path(__file__).resolve().parents[1]
sys.path.append(str(repo_root))

from backtest_engine.job_store import OptimizerJob, OptimizerJobStore
from backtest_engine.optimizer import estimate_iterations, validate_parameter_grid, build_parameter_spec

# Optimal parameters from Passe 1
PASSE1_OPTIMAL_PARAMS = {


    # ABIBEEUR
    ("ABIBEEUR", "10m"): {"obs_len": 22, "stat_len": 79, "mu_k": 2.9, "stick": 0.9},
    ("ABIBEEUR", "15m"): {"obs_len": 28, "stat_len": 89, "mu_k": 2.7, "stick": 0.6},
    ("ABIBEEUR", "45m"): {"obs_len": 11, "stat_len": 35, "mu_k": 2.8, "stick": 0.5},

    # ACFREUR
    ("ACFREUR", "10m"): {"obs_len": 30, "stat_len": 61, "mu_k": 2.7, "stick": 0.7},
    ("ACFREUR", "15m"): {"obs_len": 21, "stat_len": 91, "mu_k": 0.5, "stick": 0.6},

    # DIAITEUR
    ("DIAITEUR", "10m"): {"obs_len": 9, "stat_len": 17, "mu_k": 2.3, "stick": 0.8},
    ("DIAITEUR", "15m"): {"obs_len": 8, "stat_len": 16, "mu_k": 2.0, "stick": 0.7},
    ("DIAITEUR", "30m"): {"obs_len": 20, "stat_len": 25, "mu_k": 2.6, "stick": 0.5},

    # LXSDEEUR
    ("LXSDEEUR", "30m"): {"obs_len": 28, "stat_len": 85, "mu_k": 1.0, "stick": 0.6},

    # MRKDEEUR
    ("MRKDEEUR", "10m"): {"obs_len": 11, "stat_len": 70, "mu_k": 2.6, "stick": 0.9},
    ("MRKDEEUR", "15m"): {"obs_len": 5, "stat_len": 44, "mu_k": 2.1, "stick": 0.9},
    ("MRKDEEUR", "30m"): {"obs_len": 5, "stat_len": 82, "mu_k": 1.8, "stick": 0.6},
    ("MRKDEEUR", "45m"): {"obs_len": 30, "stat_len": 15, "mu_k": 2.0, "stick": 0.9},

    # RIFREUR
    ("RIFREUR", "10m"): {"obs_len": 26, "stat_len": 47, "mu_k": 1.2, "stick": 0.9},
    ("RIFREUR", "15m"): {"obs_len": 16, "stat_len": 26, "mu_k": 1.8, "stick": 0.9},
}

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

def main():
    print(f"Préparation de la file d'attente pour la Passe 2 (Filtrage de Régime & Confirmation)...")

    # Ouvrir la base de données de jobs
    store = OptimizerJobStore()
    print(f"Connexion à la base de données SQLite : {store.storage_path}")

    # Enregistrer les jobs
    print("Enregistrement des jobs dans la file d'attente...")
    queued_count = 0

    for (symbol, tf_str), opt in PASSE1_OPTIMAL_PARAMS.items():
        tf_min = timeframe_to_minutes(tf_str)

        # Vérification dynamique de la casse sur le disque (NVO.parquet vs abibeeur.parquet)
        symbol_cased = symbol.lower()
        p1_lower = repo_root / "storage/processed" / "market_data_1m" / f"{symbol.lower()}.parquet"
        p5_lower = repo_root / "storage/processed" / "market_data_5m" / f"{symbol.lower()}.parquet"
        if not p1_lower.exists() and not p5_lower.exists():
            p1_upper = repo_root / "storage/processed" / "market_data_1m" / f"{symbol.upper()}.parquet"
            p5_upper = repo_root / "storage/processed" / "market_data_5m" / f"{symbol.upper()}.parquet"
            if p1_upper.exists() or p5_upper.exists():
                symbol_cased = symbol.upper()

        # Definition des paramètres à optimiser (confirm_bars de 1 à 5 et dom_thresh de 0.3 à 0.8)
        # Les paramètres HMM issus de la Passe 1 sont bloqués (choice à 1 valeur).
        parameters_payload = [
            {"name": "obs_len", "kind": "choice", "values": [opt["obs_len"]]},
            {"name": "stat_len", "kind": "choice", "values": [opt["stat_len"]]},
            {"name": "mu_k", "kind": "choice", "values": [opt["mu_k"]]},
            {"name": "stick", "kind": "choice", "values": [opt["stick"]]},
            {"name": "confirm_bars", "kind": "numeric", "start": 1, "end": 5, "step": 1},
            {"name": "dom_thresh", "kind": "numeric", "start": 0.3, "end": 0.8, "step": 0.1},
            {"name": "use_safety_stop", "kind": "choice", "values": [False]}
        ]

        # Calculer le nombre total de combinaisons (devrait être exactement 30)
        specs = [build_parameter_spec(p["name"], p, strategy="hmm_regime_filter") for p in parameters_payload]
        raw_iterations = estimate_iterations(specs)
        grid_validation = validate_parameter_grid(
            specs,
            fixed_overrides=None,
            strategy="hmm_regime_filter",
            optimization_mode="grid"
        )
        canonical_iterations = grid_validation["canonical_iterations"]

        # Payload de requête de la Passe 2
        request_payload = {
            "strategy": "hmm_regime_filter",
            "symbol": symbol_cased,
            "timeframe_minutes": tf_min,
            "timeframe": tf_str,
            "optimization_mode": "bayesian",
            "max_iterations": 1000, # n_trials à 1000 (Optuna convergera très vite car espace=30)
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
            "fixed_overrides": None
        }

        # Création de l'objet de job
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

        store.add(job)
        queued_count += 1
        print(f"  -> Job enfilé pour {symbol} {tf_str} ({canonical_iterations} combinaisons réelles)")

    print(f"\nSuccès ! {queued_count} jobs de Passe 2 ajoutés à la base de données.")
    print("Lancez le worker avec : ./start_backtest_engine.sh start (ou via l'UI) pour débuter l'optimisation.")

if __name__ == "__main__":
    main()
