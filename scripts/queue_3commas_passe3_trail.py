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

def main():
    # Targets validés de la Passe 2 & Passe 2.1
    # Format: (symbol, tf, ma1, len1, ma2, len2, rnr, risk_m, swing_lookback)
    targets = [
        ("GMAB", "60m", "DEMA", 8, "HMA", 10, 0.5, 2.5, 5),
        ("GMAB", "30m", "HMA", 5, "DEMA", 23, 1.1, 0.8, 5),
        ("GMAB", "20m", "EMA", 6, "HMA", 128, 1.5, 0.5, 5),
        ("GMAB", "15m", "HMA", 6, "VWMA", 18, 0.8, 2.6, 5),
        ("FPE.DE", "45m", "HMA", 41, "WMA", 10, 0.6, 2.9, 5),
        ("FPE.DE", "30m", "HMA", 52, "EMA", 10, 0.9, 1.2, 5),
        ("FPE.DE", "20m", "DEMA", 30, "HMA", 32, 1.0, 1.5, 5),
        ("FPE.DE", "5m", "WMA", 36, "HMA", 59, 1.1, 0.9, 5),
        ("LOGI", "120m", "HEMA", 7, "SMA", 13, 1.0, 0.6, 9),  # Swing corrigé en P2.1
        ("LOGI", "45m", "HEMA", 6, "SMA", 13, 1.4, 0.7, 5),
        ("LOGI", "10m", "HEMA", 5, "T3", 15, 1.7, 0.8, 5),
        ("LOGI", "5m", "HEMA", 8, "HMA", 57, 2.5, 2.4, 5),
        ("EVD.DE", "30m", "DEMA", 40, "HMA", 140, 1.2, 0.8, 5),
        ("EVD.DE", "20m", "WMA", 20, "WMA", 71, 1.1, 0.9, 5),
        ("EVD.DE", "5m", "SMA", 49, "VWMA", 57, 5.0, 2.5, 5),
        ("TENITEUR", "30m", "HEMA", 5, "SMA", 38, 0.5, 0.8, 5), # Nouvel actif qualifié en P1
    ]

    print(f"Préparation de la Passe 3 (Trailing Stop) pour {len(targets)} configurations.")

    parameters_payload = [
        {"name": "trail_stop_size", "kind": "numeric", "start": 0.5, "end": 3.0, "step": 0.1},
        {"name": "rr_exit", "kind": "numeric", "start": 0.0, "end": 2.0, "step": 0.1}
    ]

    store = OptimizerJobStore()
    print(f"Connexion à la base de données SQLite : {store.storage_path}")

    queued_count = 0
    for symbol, tf_str, ma_type1, ma_length1, ma_type2, ma_length2, rnr, risk_m, swing in targets:
        tf_min = timeframe_to_minutes(tf_str)

        fixed_overrides = {
            "use_safety_stop": False,
            "ma_type1": ma_type1,
            "ma_length1": ma_length1,
            "ma_type2": ma_type2,
            "ma_length2": ma_length2,
            "rnr": rnr,
            "risk_m": risk_m,
            "swing_lookback": swing,
            "trail_stop": True # On force l'activation du Trailing Stop
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

        request_payload = {
            "strategy": "3commas_bot",
            "symbol": symbol,
            "timeframe_minutes": tf_min,
            "timeframe": tf_str,
            "optimization_mode": "grid", # Grid mode for 1D space
            "max_iterations": canonical_iterations,
            "early_stop_drawdown_pct": 0,
            "enable_convergence_stop": False,
            "use_vectorbt_prescan": True,
            "run_post_validation": True,
            "workers": 15,
            "min_closed_trades": 80 if symbol != "TENITEUR" else 50, # Relax constraint for TENITEUR to avoid rejection
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
                "totalIterations": canonical_iterations,
                "rawIterations": raw_iterations
            }
        )

        store.add(job)
        queued_count += 1

    print(f"Succès ! {queued_count} jobs d'optimisation ont été ajoutés à la base de données SQLite.")
    print(f"Espace de recherche par job : {raw_iterations} itérations brutes (Mode Grid Exhaustif).")
    print("Démarrez le worker avec : ./start_backtest_engine.sh start (ou via l'UI) pour lancer l'exécution.")

if __name__ == "__main__":
    main()
