import os
import json
import numpy as np
import pandas as pd
import sys
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, Any, List

# Ajouter le chemin racine au path pour importer backtest_engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest_engine.screening import extract_statistical_signature, get_mahalanobis_distance

DATA_DIR = "/home/kidpixel/trading_automation_v2/storage/processed"
BASELINES_FILE = "/home/kidpixel/trading_automation_v2/configs/baselines_signatures.json"

TIMEFRAMES = {
    "10min": "10min",
    "15min": "15min",
    "30min": "30min",
    "45min": "45min",
    "60min": "60min"
}

def resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    df_temp = df.copy()
    if 'timestamp' in df_temp.columns:
        df_temp = df_temp.set_index('timestamp')
    if not isinstance(df_temp.index, pd.DatetimeIndex):
        df_temp.index = pd.to_datetime(df_temp.index)

    resampler = df_temp.resample(rule)
    resampled = pd.DataFrame({
        'open': resampler['open'].first(),
        'high': resampler['high'].max(),
        'low': resampler['low'].min(),
        'close': resampler['close'].last(),
        'volume': resampler['volume'].sum(),
        'symbol': resampler['symbol'].first()
    }).dropna(subset=['close'])
    return resampled

def process_single_candidate(symbol: str, path: str, timeframes: List[str], baselines_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Traite un unique symbole candidat pour tous les timeframes spécifiés.
    Calcule les distances de Mahalanobis pour toutes les stratégies.
    """
    try:
        df = pd.read_parquet(path)
        if len(df) < 100:
            return []
    except Exception as e:
        print(f"Erreur de chargement pour {symbol} : {e}")
        return []

    results = []
    cov_matrix = np.array(baselines_data["global_covariance"])
    signatures = baselines_data["signatures"]

    # Regrouper les signatures historiques de la baseline par stratégie pour calculer le vecteur moyen
    strategies_baseline = {}
    for sig_name, sig_val in signatures.items():
        strat = sig_val["strategy"]
        if strat not in strategies_baseline:
            strategies_baseline[strat] = []

        # Vecteur de caractéristiques de l'actif de référence
        features = [
            sig_val["hurst"],
            sig_val["adf_stat"],
            sig_val["half_life"] if np.isfinite(sig_val["half_life"]) else 1000.0,
            sig_val["volatility_daily"],
            sig_val["rho_1"],
            sig_val["rho_5"]
        ]
        strategies_baseline[strat].append(features)

    # Calculer le vecteur moyen pour chaque stratégie
    strat_centroids = {}
    for strat, feat_list in strategies_baseline.items():
        strat_centroids[strat] = np.mean(feat_list, axis=0)

    for tf in timeframes:
        try:
            df_resampled = resample_ohlcv(df, tf)
            if len(df_resampled) < 50:
                continue

            is_crypto = symbol.endswith("usdt")
            sig = extract_statistical_signature(df_resampled, is_crypto=is_crypto)

            # Construire le vecteur de caractéristiques du candidat
            cand_features = np.array([
                sig["hurst"],
                sig["adf_stat"],
                sig["half_life"] if np.isfinite(sig["half_life"]) else 1000.0,
                sig["volatility_daily"],
                sig["rho_1"],
                sig["rho_5"]
            ])

            # Si des descripteurs sont invalides, ignorer
            if np.isnan(cand_features).any():
                continue

            # Évaluer la similarité avec chaque stratégie
            for strat, centroid in strat_centroids.items():
                distance = get_mahalanobis_distance(cand_features, centroid, cov_matrix)

                # Critères opérationnels de base
                # ADV minimum de 1M € et historique minimal de 1 an
                is_liquid = sig["adv"] >= 1_000_000.0
                has_history = sig["history_years"] >= 1.0

                results.append({
                    "symbol": symbol,
                    "timeframe": tf,
                    "strategy": strat,
                    "distance": distance,
                    "hurst": sig["hurst"],
                    "adf_stat": sig["adf_stat"],
                    "half_life": sig["half_life"],
                    "volatility_daily": sig["volatility_daily"],
                    "adv": sig["adv"],
                    "history_years": sig["history_years"],
                    "is_liquid": is_liquid,
                    "has_history": has_history
                })
        except Exception as e:
            print(f"Erreur lors du traitement de {symbol} sur {tf} : {e}")

    return results

def main():
    parser = argparse.ArgumentParser(description="Moteur de Screening Statistique Multicritère")
    parser.add_argument("--max-workers", type=int, default=8, help="Nombre max de workers en parallèle (max 15)")
    parser.add_argument("--threshold", type=float, default=2.5, help="Seuil de distance de Mahalanobis maximale")
    parser.add_argument("--output-report", type=str, default="reports/screening_report.md", help="Fichier de rapport de sortie")
    parser.add_argument("--exclude", type=str, default="", help="Liste des symboles à exclure, séparés par des virgules")
    parser.add_argument("--crypto-only", action="store_true", help="Screen uniquement les cryptomonnaies (symboles finissant par usdt)")
    args = parser.parse_args()

    baselines_file = "/home/kidpixel/trading_automation_v2/configs/baselines_signatures_crypto.json" if args.crypto_only else BASELINES_FILE

    if not os.path.exists(baselines_file):
        print(f"Erreur: Le fichier de baselines {baselines_file} n'existe pas. Veuillez d'abord exécuter generate_baselines.py ou generate_baselines_crypto.py.")
        sys.exit(1)

    with open(baselines_file, "r") as f:
        baselines_data = json.load(f)

    print("Identification des fichiers candidats...")
    m1_dir = os.path.join(DATA_DIR, "market_data_1m")
    m5_dir = os.path.join(DATA_DIR, "market_data_5m")

    # S'assurer que les répertoires existent (éviter des plantages si market_data_5m n'a pas de cryptos)
    m1_files = {}
    if os.path.exists(m1_dir):
        m1_files = {f.replace(".parquet", ""): os.path.join(m1_dir, f) for f in os.listdir(m1_dir) if f.endswith(".parquet")}
    m5_files = {}
    if os.path.exists(m5_dir):
        m5_files = {f.replace(".parquet", ""): os.path.join(m5_dir, f) for f in os.listdir(m5_dir) if f.endswith(".parquet")}

    # Résolution des répertoires conformément aux exigences :
    # Si le symbole a des données 1m, on l'utilise.
    # Si le symbole n'existe qu'en 5m (ex: EVD.DE, FPE.DE), on l'utilise de 5m.
    # Tout doublon resamplé en 5m est ignoré.
    exclude_symbols = set([s.strip() for s in args.exclude.split(",") if s.strip()])

    candidates = {}

    # Ajouter tous les fichiers 1m
    for sym, path in m1_files.items():
        if sym in exclude_symbols:
            continue
        candidates[sym] = {"path": path, "src": "1m"}

    # Ajouter les fichiers 5m uniquement s'ils n'existent pas en 1m
    for sym, path in m5_files.items():
        if sym in exclude_symbols:
            continue
        if sym not in candidates:
            candidates[sym] = {"path": path, "src": "5m"}
            print(f"Symbole uniquement disponible en 5m détecté : {sym}")

    # Filtrer pour ne garder que les cryptos si --crypto-only est actif
    if args.crypto_only:
        candidates = {sym: info for sym, info in candidates.items() if sym.endswith("usdt")}

    print(f"Total de candidats à screener : {len(candidates)}")

    all_results = []

    # Exécution parallèle avec ProcessPoolExecutor
    print(f"Démarrage du screening en parallèle (Workers: {args.max_workers})...")
    with ProcessPoolExecutor(max_workers=args.max_workers) as executor:
        futures = {}
        for sym, info in candidates.items():
            futures[executor.submit(
                process_single_candidate,
                sym,
                info["path"],
                list(TIMEFRAMES.keys()),
                baselines_data
            )] = sym

        total_candidates = len(candidates)
        completed = 0
        for fut in as_completed(futures):
            completed += 1
            sym = futures[fut]
            try:
                res = fut.result()
                if res:
                    all_results.extend(res)
            except Exception as e:
                print(f"Le worker pour {sym} a échoué avec l'erreur : {e}")

            if completed % 10 == 0 or completed == total_candidates:
                print(f"Progression : {completed}/{total_candidates} symboles traités ({(completed/total_candidates)*100:.1f}%)")

    # Génération du rapport
    print(f"Analyse des résultats et génération du rapport...")
    df_res = pd.DataFrame(all_results)

    if df_res.empty:
        print("Aucun candidat qualifiable trouvé.")
        sys.exit(0)

    # Filtrer par éligibilité
    df_res["eligible"] = (df_res["distance"] <= args.threshold) & df_res["is_liquid"] & df_res["has_history"]

    # Trier par distance croissante
    df_eligible = df_res[df_res["eligible"]].sort_values(by="distance")

    # Création du répertoire de rapport
    os.makedirs(os.path.dirname(args.output_report), exist_ok=True)

    with open(args.output_report, "w") as f:
        f.write("# Rapport de Screening et Qualification Statistique des Actifs\n\n")
        f.write(f"Ce rapport consigne l'éligibilité des nouveaux actifs candidats par rapport à la baseline des 9 actifs de référence du portefeuille.\n\n")
        f.write(f"*   **Seuil de distance de Mahalanobis maximum** : {args.threshold}\n")
        f.write(f"*   **ADV minimum** : 1 000 000 €\n")
        f.write(f"*   **Historique minimum** : 1 an\n\n")

        f.write("## 1. Candidats Qualifiés (Classés par distance croissante)\n\n")
        if df_eligible.empty:
            f.write("*Aucun nouveau candidat ne respecte l'intégralité des critères statistiques et opérationnels.*\n\n")
        else:
            f.write("| Symbole | Timeframe | Stratégie Cible | Distance $D_M$ | Hurst $H$ | ADF (stat) | Demi-Vie (bougies) | ADV (M€) | Années Hist. |\n")
            f.write("| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: |\n")
            for _, row in df_eligible.iterrows():
                hl_str = f"{row['half_life']:.1f}" if np.isfinite(row['half_life']) else "N/A"
                f.write(f"| **{row['symbol']}** | {row['timeframe']} | `{row['strategy']}` | **{row['distance']:.2f}** | {row['hurst']:.2f} | {row['adf_stat']:.2f} | {hl_str} | {row['adv']/1e6:.2f} M€ | {row['history_years']:.1f} ans |\n")
            f.write("\n")

        f.write("## 2. Synthèse Détaillée de l'Univers Screené\n\n")
        f.write("| Symbole | Timeframe | Stratégie | Distance $D_M$ | Hurst $H$ | Liquidité | Historique | Statut |\n")
        f.write("| :--- | :--- | :--- | ---: | ---: | :---: | :---: | :---: |\n")
        for _, row in df_res.sort_values(by=["symbol", "timeframe", "distance"]).iterrows():
            liq_status = "✅" if row["is_liquid"] else "❌"
            hist_status = "✅" if row["has_history"] else "❌"
            status = "✅ Éligible" if row["eligible"] else "❌ Exclu"
            f.write(f"| {row['symbol']} | {row['timeframe']} | `{row['strategy']}` | {row['distance']:.2f} | {row['hurst']:.2f} | {liq_status} | {hist_status} | {status} |\n")

    print(f"Rapport de screening généré avec succès dans {args.output_report} !")

if __name__ == "__main__":
    main()
