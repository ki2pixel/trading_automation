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
    multiplier = 0.05
    calculated = round(canonical_iterations * multiplier)
    clamped = max(500, min(calculated, 3000))
    return clamped

def main():
    # Actifs qualifiés de la Passe 1 de 3commas_bot
    targets = [
        ("GMAB", "60m", "DEMA", 8, "HMA", 10),
        ("GMAB", "30m", "HMA", 5, "DEMA", 23),
        ("GMAB", "20m", "EMA", 6, "HMA", 128),
        ("GMAB", "15m", "HMA", 6, "VWMA", 18),
        ("FPE.DE", "45m", "HMA", 41, "WMA", 10),
        ("FPE.DE", "30m", "HMA", 52, "EMA", 10),
        ("FPE.DE", "20m", "DEMA", 30, "HMA", 32),
        ("FPE.DE", "5m", "WMA", 36, "HMA", 59),
        ("LOGI", "120m", "HEMA", 7, "SMA", 13),
        ("LOGI", "45m", "HEMA", 6, "SMA", 13),
        ("LOGI", "10m", "HEMA", 5, "T3", 15),
        ("LOGI", "5m", "HEMA", 8, "HMA", 57),
        ("EVD.DE", "30m", "DEMA", 40, "HMA", 140),
        ("EVD.DE", "20m", "WMA", 20, "WMA", 71),
        ("EVD.DE", "5m", "SMA", 49, "VWMA", 57),
    ]

    print(f"Préparation de la Passe 2.1 (Risk + Swing Lookback) pour {len(targets)} configurations.")

    parameters_payload = [
        {"name": "rnr", "kind": "numeric", "start": 0.5, "end": 5.0, "step": 0.1},
        {"name": "risk_m", "kind": "numeric", "start": 0.5, "end": 5.0, "step": 0.1},
        {"name": "swing_lookback", "kind": "numeric", "start": 1, "end": 20, "step": 1}
    ]

    store = OptimizerJobStore()
    print(f"Connexion à la base de données SQLite : {store.storage_path}")

    queued_count = 0
    for symbol, tf_str, ma_type1, ma_length1, ma_type2, ma_length2 in targets:
        tf_min = timeframe_to_minutes(tf_str)
        
        fixed_overrides = {
            "trail_stop": False,
            "use_safety_stop": False,
            "ma_type1": ma_type1,
            "ma_length1": ma_length1,
            "ma_type2": ma_type2,
            "ma_length2": ma_length2
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
    print(f"Espace de recherche par job : {raw_iterations} itérations brutes.")
    print(f"Itérations Bayésiennes allouées par job : {bayesian_max_iterations}.")
    print("Démarrez le worker avec : ./start_backtest_engine.sh start (ou via l'UI) pour lancer l'exécution.")

if __name__ == "__main__":
    main()
