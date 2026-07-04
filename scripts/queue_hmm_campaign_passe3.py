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

# Optimal parameters from Passe 2
PASSE2_OPTIMAL_PARAMS = {
    # NVO (Déjà documenté le 15 Juin 2026 - exclu de la file d'attente par défaut)
    ("NVO", "10m"): {"obs_len": 16, "stat_len": 33, "mu_k": 2.1, "stick": 0.8, "confirm_bars": 2, "dom_thresh": 0.3},
    ("NVO", "15m"): {"obs_len": 5, "stat_len": 67, "mu_k": 1.1, "stick": 0.9, "confirm_bars": 2, "dom_thresh": 0.5},
    ("NVO", "20m"): {"obs_len": 5, "stat_len": 13, "mu_k": 1.2, "stick": 0.5, "confirm_bars": 2, "dom_thresh": 0.5},
    ("NVO", "30m"): {"obs_len": 25, "stat_len": 13, "mu_k": 2.6, "stick": 0.9, "confirm_bars": 2, "dom_thresh": 0.5},
    ("NVO", "45m"): {"obs_len": 24, "stat_len": 96, "mu_k": 0.9, "stick": 0.8, "confirm_bars": 2, "dom_thresh": 0.5},
    ("NVO", "60m"): {"obs_len": 5, "stat_len": 12, "mu_k": 0.7, "stick": 0.9, "confirm_bars": 2, "dom_thresh": 0.5},
    ("NVO", "120m"): {"obs_len": 5, "stat_len": 70, "mu_k": 1.4, "stick": 0.7, "confirm_bars": 2, "dom_thresh": 0.3},

    # ABIBEEUR
    ("ABIBEEUR", "10m"): {"obs_len": 22, "stat_len": 79, "mu_k": 2.9, "stick": 0.9, "confirm_bars": 2, "dom_thresh": 0.5},
    ("ABIBEEUR", "15m"): {"obs_len": 28, "stat_len": 89, "mu_k": 2.7, "stick": 0.6, "confirm_bars": 2, "dom_thresh": 0.5},
    ("ABIBEEUR", "45m"): {"obs_len": 11, "stat_len": 35, "mu_k": 2.8, "stick": 0.5, "confirm_bars": 1, "dom_thresh": 0.3},

    # ACFREUR
    ("ACFREUR", "10m"): {"obs_len": 30, "stat_len": 61, "mu_k": 2.7, "stick": 0.7, "confirm_bars": 2, "dom_thresh": 0.5},
    ("ACFREUR", "15m"): {"obs_len": 21, "stat_len": 91, "mu_k": 0.5, "stick": 0.6, "confirm_bars": 2, "dom_thresh": 0.5},

    # DIAITEUR
    ("DIAITEUR", "10m"): {"obs_len": 9, "stat_len": 17, "mu_k": 2.3, "stick": 0.8, "confirm_bars": 2, "dom_thresh": 0.5},
    ("DIAITEUR", "15m"): {"obs_len": 8, "stat_len": 16, "mu_k": 2.0, "stick": 0.7, "confirm_bars": 2, "dom_thresh": 0.5},
    ("DIAITEUR", "30m"): {"obs_len": 20, "stat_len": 25, "mu_k": 2.6, "stick": 0.5, "confirm_bars": 1, "dom_thresh": 0.3},

    # LXSDEEUR
    ("LXSDEEUR", "30m"): {"obs_len": 28, "stat_len": 85, "mu_k": 1.0, "stick": 0.6, "confirm_bars": 1, "dom_thresh": 0.3},

    # MRKDEEUR
    ("MRKDEEUR", "10m"): {"obs_len": 11, "stat_len": 70, "mu_k": 2.6, "stick": 0.9, "confirm_bars": 2, "dom_thresh": 0.5},
    ("MRKDEEUR", "15m"): {"obs_len": 5, "stat_len": 44, "mu_k": 2.1, "stick": 0.9, "confirm_bars": 2, "dom_thresh": 0.5},
    ("MRKDEEUR", "30m"): {"obs_len": 5, "stat_len": 82, "mu_k": 1.8, "stick": 0.6, "confirm_bars": 2, "dom_thresh": 0.5},
    ("MRKDEEUR", "45m"): {"obs_len": 30, "stat_len": 15, "mu_k": 2.0, "stick": 0.9, "confirm_bars": 2, "dom_thresh": 0.3},

    # RIFREUR
    ("RIFREUR", "10m"): {"obs_len": 26, "stat_len": 47, "mu_k": 1.2, "stick": 0.9, "confirm_bars": 5, "dom_thresh": 0.7},
    ("RIFREUR", "15m"): {"obs_len": 16, "stat_len": 26, "mu_k": 1.8, "stick": 0.9, "confirm_bars": 2, "dom_thresh": 0.5},
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
    print(f"Préparation de la file d'attente pour la Passe 3 (Sorties & Brackets TP/SL)...")

    # Ouvrir la base de données de jobs
    store = OptimizerJobStore()
    print(f"Connexion à la base de données SQLite : {store.storage_path}")

    # Enregistrer les jobs
    print("Enregistrement des jobs dans la file d'attente...")
    queued_count = 0

    for (symbol, tf_str), opt in PASSE2_OPTIMAL_PARAMS.items():
        if symbol.upper() == "NVO":
            print(f"  -> {symbol} {tf_str} ignoré (déjà audité dans la campagne historique du 15 Juin 2026)")
            continue

        tf_min = timeframe_to_minutes(tf_str)

        # Vérification dynamique de la casse sur le disque
        symbol_cased = symbol.lower()
        p1_lower = repo_root / "storage/processed" / "market_data_1m" / f"{symbol.lower()}.parquet"
        p5_lower = repo_root / "storage/processed" / "market_data_5m" / f"{symbol.lower()}.parquet"
        if not p1_lower.exists() and not p5_lower.exists():
            p1_upper = repo_root / "storage/processed" / "market_data_1m" / f"{symbol.upper()}.parquet"
            p5_upper = repo_root / "storage/processed" / "market_data_5m" / f"{symbol.upper()}.parquet"
            if p1_upper.exists() or p5_upper.exists():
                symbol_cased = symbol.upper()

        # Définition des paramètres de la Passe 3
        # - Paramètres HMM & confirmation figés.
        # - Recherche sur use_safety_stop (True, False), use_net_bracket_exits (True)
        # - take_profit_net_percent (1.0 à 20.0, step 1.0)
        # - stop_loss_net_percent (1.0 à 20.0, step 1.0)
        parameters_payload = [
            {"name": "obs_len", "kind": "choice", "values": [opt["obs_len"]]},
            {"name": "stat_len", "kind": "choice", "values": [opt["stat_len"]]},
            {"name": "mu_k", "kind": "choice", "values": [opt["mu_k"]]},
            {"name": "stick", "kind": "choice", "values": [opt["stick"]]},
            {"name": "confirm_bars", "kind": "choice", "values": [opt["confirm_bars"]]},
            {"name": "dom_thresh", "kind": "choice", "values": [opt["dom_thresh"]]},
            {"name": "use_safety_stop", "kind": "choice", "values": [True, False]},
            {"name": "use_net_bracket_exits", "kind": "choice", "values": [True]},
            {"name": "take_profit_net_percent", "kind": "numeric", "start": 1.0, "end": 20.0, "step": 1.0},
            {"name": "stop_loss_net_percent", "kind": "numeric", "start": 1.0, "end": 20.0, "step": 1.0}
        ]

        # Calculer le nombre total de combinaisons (devrait être exactement 800)
        specs = [build_parameter_spec(p["name"], p, strategy="hmm_regime_filter") for p in parameters_payload]
        raw_iterations = estimate_iterations(specs)
        grid_validation = validate_parameter_grid(
            specs,
            fixed_overrides=None,
            strategy="hmm_regime_filter",
            optimization_mode="grid"
        )
        canonical_iterations = grid_validation["canonical_iterations"]

        # Payload de requête de la Passe 3
        request_payload = {
            "strategy": "hmm_regime_filter",
            "symbol": symbol_cased,
            "timeframe_minutes": tf_min,
            "timeframe": tf_str,
            "optimization_mode": "bayesian",
            "max_iterations": 1000,
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

    print(f"\nSuccès ! {queued_count} jobs de Passe 3 ajoutés à la base de données SQLite.")
    print("Lancez le worker avec : ./start_backtest_engine.sh start (ou via l'UI) pour débuter l'optimisation.")

if __name__ == "__main__":
    main()
