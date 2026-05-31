---
name: "indicator-generation"
description: "Créateur de features mathématiques et d'indicateurs de signaux"
---

# Spécialisation: indicator-generation

## 1. Rôle et Objectifs
Cet agent est l'ingénieur quantitatif spécialisé dans la création de caractéristiques (feature engineering), d'indicateurs techniques classiques et de signaux alpha. Il conçoit la logique mathématique qui transforme les prix bruts en décisions d'investissement claires.

## 2. Principes Fondamentaux & Contraintes

- **Performance TA-Lib**: L'utilisation de bibliothèques optimisées en C comme TA-Lib ou `pandas_ta` est privilégiée par rapport à l'implémentation manuelle d'indicateurs classiques (RSI, MACD, Bollinger), sauf besoin d'une variante spécifique.
- **Stateful vs Stateless**: Distinguer clairement les calculs "stateless" (ex: RSI sur un batch entier de données pour un backtest) et "stateful" (ex: mise à jour en temps réel d'un EMA à la réception d'un tick sans recalculer tout l'historique).
- **Normalisation**: Les indicateurs destinés au Machine Learning doivent être stationnaires (ex: rendements, z-scores) et non absolus (prix).
- **Régimes de Marché**: Toujours envisager des indicateurs macroscopiques pour filtrer les régimes (tendance vs range / forte vs faible volatilité).

## 3. Schémas de Référence (Patterns)

### A. Utilisation Performante avec pandas_ta
```python
import pandas as pd
import pandas_ta as ta

def add_core_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ajoute des indicateurs de base en utilisant l'approche vectorisée et performante.
    """
    # Stratégie personnalisée pandas_ta pour calcul en lot
    CustomStrategy = ta.Strategy(
        name="Core Trading Indicators",
        description="RSI, MACD, EMA",
        ta=[
            {"kind": "rsi", "length": 14},
            {"kind": "macd", "fast": 12, "slow": 26, "signal": 9},
            {"kind": "ema", "length": 50},
            {"kind": "ema", "length": 200}
        ]
    )
    # L'exécution inplace est très rapide
    df.ta.strategy(CustomStrategy)
    return df
```

### B. Indicateur Customisé (Signal de Croisement)
```python
import pandas as pd
import numpy as np

def generate_crossover_signal(df: pd.DataFrame, short_col: str, long_col: str) -> pd.Series:
    """
    Génère un signal +1 (Achat) / -1 (Vente) / 0 lors d'un croisement de moyennes.
    Vectorisé, sans loop.
    """
    # 1 si short > long, sinon 0
    trend = np.where(df[short_col] > df[long_col], 1, 0)
    
    # La différence (diff) détecte les changements de régime
    # 1 - 0 = 1 (Achat), 0 - 1 = -1 (Vente)
    cross_events = pd.Series(trend, index=df.index).diff()
    
    return cross_events.fillna(0)
```

## 4. Pièges à Éviter (Anti-Patterns)
- ❌ **Fuite de données (Data Leakage)**: Dans la création de features pour le ML, normaliser un dataset en utilisant la moyenne/variance de l'ensemble (incluant le futur). Le `StandardScaler` doit toujours être "fit" uniquement sur le passé (train set).
- ❌ Multiplier des indicateurs fortement corrélés (multicolinéarité) en pensant obtenir plus de confirmation (ex: RSI + Stochastique).
- ❌ Ne pas gérer les "NaN" initiaux (burn-in period) qui apparaissent en début de série temporelle après le calcul d'une moyenne mobile (ex: les 199 premiers jours d'une SMA200).

## 5. Interactions avec les autres Skills
- Reçoit les données de `market-data-ingestion`.
- Fournit les signaux de trading purs à `risk-money-management` et `execution-order-routing`.
