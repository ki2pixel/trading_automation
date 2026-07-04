#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'automatisation de file d'attente de jobs d'optimisation pour la stratégie
Momentum-based ZigZag (avec QQE - Passe 1) sur les nouveaux actifs cryptos qualifiés.
"""

import sys
import re
import time
from uuid import uuid4
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Résolution et ajout du chemin racine du dépôt au python path
repo_root = Path(__file__).resolve().parents[1]
sys.path.append(str(repo_root))

from backtest_engine.job_store import OptimizerJob, OptimizerJobStore
from backtest_engine.optimizer import estimate_iterations, validate_parameter_grid, build_parameter_spec


def parse_eligible_targets(report_path: Path) -> List[Tuple[str, str]]:
    """
    Parcourt le rapport de screening crypto et extrait les couples (symbole, timeframe)
    éligibles associés à la stratégie 'momentum_based_zigzag'.
    
    Args:
        report_path: Chemin absolu vers le rapport de screening.
        
    Returns:
        Une liste de tuples (symbole, timeframe).
    """
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    section_title = "### 2. Timeframes & Stratégies Éligibles (Toutes les configurations qualifiées pour le Top 10)"
    if section_title not in content:
        raise ValueError(f"Section '{section_title}' introuvable dans le rapport {report_path}.")

    start_idx = content.find(section_title) + len(section_title)
    end_idx = len(content)

    # Recherche du début de la section suivante (titre de niveau 2)
    next_section_matches = [m.start() for m in re.finditer(r"\n##", content[start_idx:])]
    if next_section_matches:
        end_idx = start_idx + next_section_matches[0]

    section_content = content[start_idx:end_idx]

    targets: List[Tuple[str, str]] = []
    seen = set()

    for line in section_content.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue

        parts = [p.strip() for p in line.split("|")[1:-1]]
        if not parts or parts[0].startswith("---") or parts[0].startswith(":-") or "Symbole" in parts[0]:
            continue

        # Extraction du symbole (première colonne)
        symbol = parts[0].replace("**", "").replace("`", "").strip().lower()
        if not symbol:
            continue

        # Analyse des colonnes 2 (Timeframe Optimal) et 3 (Autres Timeframes Qualifiés)
        for col_idx in [1, 2]:
            if col_idx >= len(parts):
                continue
            col_content = parts[col_idx]

            # Regex robuste
            matches = re.findall(r"(\d+min|\d+h|\d+d|\d+m)\s*\(([^)]+)\)", col_content)
            for tf, strats_in_parentheses in matches:
                # Nettoyage des stratégies associées
                strats = [s.strip().replace("`", "") for s in strats_in_parentheses.split(",")]
                if "momentum_based_zigzag" in strats:
                    tf_clean = tf.strip()
                    pair = (symbol, tf_clean)
                    if pair not in seen:
                        seen.add(pair)
                        targets.append(pair)

    return targets


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


def calculate_bayesian_iterations(canonical_iterations: int) -> int:
    """
    Calcule le nombre d'itérations maximales pour l'optimisation bayésienne
    avec un coefficient multiplicateur de 0.0256 clampé entre 1000 et 24000.
    
    Args:
        canonical_iterations: Le nombre de combinaisons de la grille.
        
    Returns:
        Le nombre de runs alloués.
    """
    multiplier = 0.0256
    calculated = round(canonical_iterations * multiplier)
    clamped = max(1000, min(calculated, 24000))
    return clamped


def main() -> None:
    # Chemin vers le rapport de screening source
    report_path = repo_root / "reports" / "screening_report_crypto.md"
    if not report_path.exists():
        print(f"Erreur : Le rapport de screening {report_path} est introuvable.")
        sys.exit(1)

    print("Lecture et filtrage des candidats depuis le rapport de screening crypto...")
    try:
        targets = parse_eligible_targets(report_path)
    except Exception as e:
        print(f"Erreur lors du parsing du rapport : {e}")
        sys.exit(1)

    print(f"Trouvé {len(targets)} couples (symbole, timeframe) valides pour momentum_based_zigzag :")
    for symbol, tf in targets:
        print(f"  - {symbol} ({tf})")

    if not targets:
        print("Aucun candidat trouvé. Arrêt.")
        sys.exit(0)

    # Définition des paramètres à optimiser (Passe 1 - Cœur QQE & Oscillateur)
    parameters_payload: List[Dict[str, Any]] = [
        {"name": "rsi_period", "kind": "numeric", "start": 7, "end": 30, "step": 1},
        {"name": "qqe_factor", "kind": "numeric", "start": 1.5, "end": 6.0, "step": 0.1},
        {"name": "rsi_smoothing", "kind": "numeric", "start": 2, "end": 15, "step": 1},
        {"name": "ob", "kind": "numeric", "start": 65.0, "end": 90.0, "step": 1.0},
        {"name": "os", "kind": "numeric", "start": 10.0, "end": 35.0, "step": 1.0},
        {"name": "signal_mode", "kind": "choice", "values": ["Close", "Live"]}
    ]

    # Overrides fixes (Paramètres bloqués de la Passe 1)
    fixed_overrides: Dict[str, Any] = {
        "use_safety_stop": False,
        "enable_stop_loss": False,
        "enable_take_profit": False,
        "enable_trailing_stop": False
    }

    print("\nValidation de la grille de paramètres et estimation des itérations...")
    try:
        # Calcul de la dimension brute et de l'espace canonique valide
        specs = [build_parameter_spec(p["name"], p, strategy="momentum_based_zigzag") for p in parameters_payload]
        raw_iterations = estimate_iterations(specs)
        grid_validation = validate_parameter_grid(
            specs,
            fixed_overrides=None,
            strategy="momentum_based_zigzag",
            optimization_mode="bayesian"
        )
        canonical_iterations = grid_validation["canonical_iterations"]
    except Exception as e:
        print(f"Erreur de validation de la grille de paramètres : {e}")
        sys.exit(1)

    # Calcul de l'intensité bayésienne
    bayesian_max_iterations = calculate_bayesian_iterations(canonical_iterations)

    print(f"Espace de recherche : {raw_iterations} combinaisons brutes.")
    print(f"Espace canonique valide : {canonical_iterations} combinaisons.")
    print(f"Intensité Bayésienne (~2.56%): {bayesian_max_iterations} essais (trials) par job.")

    # Connexion à la base de données de jobs SQLite
    try:
        store = OptimizerJobStore()
        print(f"\nConnexion à la base de données SQLite : {store.storage_path}")
    except Exception as e:
        print(f"Erreur lors de la connexion à SQLite : {e}")
        sys.exit(1)

    # Enregistrement des jobs dans SQLite
    print("Enregistrement des jobs dans la file d'attente...")
    queued_count = 0
    for symbol, tf_str in targets:
        try:
            tf_min = timeframe_to_minutes(tf_str)
            
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
                "convergence_patience": 300,
                "circuit_breaker_ratio": 0.2,
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

            # Instanciation de l'objet job
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
            
            # Ajout en BDD (le statut par défaut sera 'queued')
            store.add(job)
            queued_count += 1
            print(f"  [Enregistré] Job pour {symbol} ({tf_str})")
        except Exception as e:
            print(f"  [Erreur] Impossible d'enregistrer le job pour {symbol} ({tf_str}) : {e}")

    print(f"\nSuccès ! {queued_count} jobs d'optimisation ont été ajoutés à la base de données SQLite.")
    print("Démarrez le worker avec : ./start_backtest_engine.sh start (ou via l'UI) pour lancer l'exécution.")


if __name__ == "__main__":
    main()
