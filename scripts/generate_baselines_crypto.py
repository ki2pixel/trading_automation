import os
import json
import numpy as np
import pandas as pd
import sys

# Ajouter le chemin racine au path pour importer backtest_engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backtest_engine.screening import extract_statistical_signature

# 12 configurations représentatives pour l'univers des crypto-monnaies
REFERENCES = [
    {"symbol": "btcusdt", "timeframe": "30min", "strategy": "cybernetic_hilbert"},
    {"symbol": "btcusdt", "timeframe": "60min", "strategy": "adaptive_volatility_trend"},
    {"symbol": "ethusdt", "timeframe": "30min", "strategy": "cybernetic_hilbert"},
    {"symbol": "ethusdt", "timeframe": "60min", "strategy": "adaptive_volatility_trend"},
    {"symbol": "ltcusdt", "timeframe": "30min", "strategy": "momentum_based_zigzag"},
    {"symbol": "ltcusdt", "timeframe": "60min", "strategy": "3commas_bot"},
    {"symbol": "dogeusdt", "timeframe": "30min", "strategy": "momentum_based_zigzag"},
    {"symbol": "dogeusdt", "timeframe": "60min", "strategy": "3commas_bot"},
    {"symbol": "adausdt", "timeframe": "30min", "strategy": "hmm_regime_filter"},
    {"symbol": "adausdt", "timeframe": "60min", "strategy": "cybernetic_hilbert"},
    {"symbol": "linkusdt", "timeframe": "30min", "strategy": "adaptive_volatility_trend"},
    {"symbol": "linkusdt", "timeframe": "60min", "strategy": "hmm_regime_filter"}
]

DATA_DIR = "/home/kidpixel/trading_automation_v2/storage/processed/market_data_1m"
OUTPUT_FILE = "/home/kidpixel/trading_automation_v2/configs/baselines_signatures_crypto.json"

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
    print("Début du calcul des baselines statistiques pour les cryptomonnaies...")
    signatures = {}
    feature_list = []

    # Extraire les signatures pour chaque configuration
    for ref in REFERENCES:
        symbol = ref["symbol"]
        tf = ref["timeframe"]
        strat = ref["strategy"]

        path = os.path.join(DATA_DIR, f"{symbol}.parquet")
        if not os.path.exists(path):
            print(f"Erreur: Fichier introuvable pour {symbol} : {path}")
            continue

        print(f"Chargement et rééchantillonnage de {symbol} en {tf}...")
        df = pd.read_parquet(path)
        df_resampled = resample_ohlcv(df, tf)

        print(f"Calcul des descripteurs pour {symbol} (is_crypto=True)...")
        sig = extract_statistical_signature(df_resampled, is_crypto=True)
        sig["symbol"] = symbol
        sig["timeframe"] = tf
        sig["strategy"] = strat

        signatures[f"{symbol}_{tf}"] = sig

        # Stocker les caractéristiques pour le calcul de la covariance globale
        features = [
            sig["hurst"],
            sig["adf_stat"],
            sig["half_life"] if np.isfinite(sig["half_life"]) else 1000.0,
            sig["volatility_daily"],
            sig["rho_1"],
            sig["rho_5"]
        ]
        feature_list.append(features)

    if not feature_list:
        print("Erreur: Aucune baseline n'a pu être générée car aucun fichier n'a été trouvé.")
        sys.exit(1)

    # Convertir en tableau numpy
    feature_matrix = np.array(feature_list)

    # Calculer la matrice de covariance globale crypto
    print("Calcul de la matrice de covariance globale crypto...")
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

    print(f"Baselines crypto sauvegardées avec succès dans {OUTPUT_FILE} !")

if __name__ == "__main__":
    main()
