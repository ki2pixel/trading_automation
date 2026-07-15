import os
import json
import numpy as np
import pandas as pd
import sys

# Ajouter le chemin racine au path pour importer backtest_engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest_engine.screening import extract_statistical_signature

REFERENCES = [
    {"symbol": "ZEAL.CO", "timeframe": "45min", "strategy": "cybernetic_hilbert", "src_dir": "market_data_1m"},
    {"symbol": "NVO", "timeframe": "30min", "strategy": "hmm_regime_filter", "src_dir": "market_data_1m"},
    {"symbol": "EVD.DE", "timeframe": "30min", "strategy": "3commas_bot", "src_dir": "market_data_5m"},
    {"symbol": "GMAB", "timeframe": "60min", "strategy": "3commas_bot", "src_dir": "market_data_1m"},
    {"symbol": "FPE.DE", "timeframe": "45min", "strategy": "3commas_bot", "src_dir": "market_data_5m"},
    {"symbol": "NVS", "timeframe": "15min", "strategy": "adaptive_volatility_trend", "src_dir": "market_data_1m"},
    {"symbol": "SAP", "timeframe": "30min", "strategy": "momentum_based_zigzag", "src_dir": "market_data_1m"},
    {"symbol": "SHL.DE", "timeframe": "45min", "strategy": "momentum_based_zigzag", "src_dir": "market_data_1m"},
    {"symbol": "AMS.MC", "timeframe": "10min", "strategy": "momentum_based_zigzag", "src_dir": "market_data_1m"}
]

DATA_DIR = "/home/kidpixel/trading_automation_v2/storage/processed"
OUTPUT_FILE = "/home/kidpixel/trading_automation_v2/configs/baselines_signatures.json"

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

def main():
    print("Début du calcul des baselines statistiques pour les 9 actifs phares...")
    signatures = {}
    feature_list = []

    # 1. Extraire les signatures pour chaque configuration
    for ref in REFERENCES:
        symbol = ref["symbol"]
        tf = ref["timeframe"]
        strat = ref["strategy"]
        src = ref["src_dir"]

        path = os.path.join(DATA_DIR, src, f"{symbol}.parquet")
        if not os.path.exists(path):
            print(f"Erreur: Fichier introuvable pour {symbol} : {path}")
            continue

        print(f"Chargement et rééchantillonnage de {symbol} en {tf}...")
        df = pd.read_parquet(path)
        df_resampled = resample_ohlcv(df, tf)

        print(f"Calcul des descripteurs pour {symbol}...")
        sig = extract_statistical_signature(df_resampled)
        sig["symbol"] = symbol
        sig["timeframe"] = tf
        sig["strategy"] = strat

        signatures[f"{symbol}_{tf}"] = sig

        # Stocker les caractéristiques pour le calcul de la covariance globale
        features = [
            sig["hurst"],
            sig["adf_stat"],
            sig["half_life"] if np.isfinite(sig["half_life"]) else 1000.0, # Remplacer inf par une valeur élevée
            sig["volatility_daily"],
            sig["rho_1"],
            sig["rho_5"]
        ]
        feature_list.append(features)

    # Convertir en tableau numpy
    feature_matrix = np.array(feature_list)

    # 2. Calculer la matrice de covariance globale
    # Elle servira pour la distance de Mahalanobis car nous n'avons pas assez
    # de données par stratégie individuelle pour estimer des covariances séparées.
    print("Calcul de la matrice de covariance globale...")
    cov_matrix = np.cov(feature_matrix, rowvar=False)

    # Sérialiser les signatures
    output_data = {
        "signatures": signatures,
        "global_covariance": cov_matrix.tolist(),
        "feature_names": ["hurst", "adf_stat", "half_life", "volatility_daily", "rho_1", "rho_5"]
    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output_data, f, indent=4)

    print(f"Baselines sauvegardées avec succès dans {OUTPUT_FILE} !")

if __name__ == "__main__":
    main()
