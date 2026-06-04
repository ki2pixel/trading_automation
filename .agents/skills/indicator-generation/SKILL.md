---
name: "indicator-generation"
description: "Créateur de features mathématiques et d'indicateurs de signaux"
---

# Spécialisation: indicator-generation

## 1. Rôle et Objectifs
Cet agent est l'ingénieur quantitatif spécialisé dans la création de caractéristiques (feature engineering), d'indicateurs techniques classiques et de signaux alpha. Il conçoit la logique mathématique qui transforme les prix bruts en décisions d'investissement claires.

## 2. Principes Fondamentaux & Contraintes

- **Performance vectorbt** : L'utilisation de bibliothèques optimisées et vectorisées comme `vectorbt` (vbt) est obligatoire pour les calculs d'indicateurs (Moyennes mobiles, RSI, etc.). Éviter de recalculer manuellement ces indicateurs ou d'utiliser des boucles Python.
- **Stateful vs Stateless**: Distinguer clairement les calculs "stateless" (ex: RSI sur un batch entier de données pour un backtest) et "stateful" (ex: mise à jour en temps réel d'un EMA à la réception d'un tick sans recalculer tout l'historique).
- **Normalisation**: Les indicateurs destinés au Machine Learning doivent être stationnaires (ex: rendements, z-scores) et non absolus (prix).
- **Régimes de Marché**: Toujours envisager des indicateurs macroscopiques pour filtrer les régimes (tendance vs range / forte vs faible volatilité).

## 3. Schémas de Référence (Patterns)

### A. Utilisation Performante avec vectorbt
```python
import pandas as pd
import vectorbt as vbt

def add_core_indicators(close_series: pd.Series) -> dict[str, pd.Series]:
    """
    Calcule des indicateurs de base de façon hautement vectorisée avec VectorBT.
    """
    rsi = vbt.RSI.run(close_series, window=14).rsi
    fast_ma = vbt.MA.run(close_series, window=12).ma
    slow_ma = vbt.MA.run(close_series, window=26).ma
    
    return {
        "rsi": rsi,
        "fast_ma": fast_ma,
        "slow_ma": slow_ma
    }
```

### B. Indicateur Customisé (Signal de Croisement)
```python
import pandas as pd
import vectorbt as vbt

def generate_vbt_signals(close_series: pd.Series, fast_window: int = 12, slow_window: int = 26) -> tuple[pd.Series, pd.Series]:
    """
    Génère des signaux d'entrée et de sortie basés sur le croisement de moyennes mobiles avec VectorBT.
    """
    fast_ma = vbt.MA.run(close_series, window=fast_window)
    slow_ma = vbt.MA.run(close_series, window=slow_window)
    
    # Signaux de croisement
    entries = fast_ma.ma_crossed_above(slow_ma)
    exits = fast_ma.ma_crossed_below(slow_ma)
    
    return entries, exits
```

## 4. Pièges à Éviter (Anti-Patterns)
- ❌ **Fuite de données (Data Leakage)**: Dans la création de features pour le ML, normaliser un dataset en utilisant la moyenne/variance de l'ensemble (incluant le futur). Le `StandardScaler` doit toujours être "fit" uniquement sur le passé (train set).
- ❌ Multiplier des indicateurs fortement corrélés (multicolinéarité) en pensant obtenir plus de confirmation (ex: RSI + Stochastique).
- ❌ Ne pas gérer les "NaN" initiaux (burn-in period) qui apparaissent en début de série temporelle après le calcul d'une moyenne mobile (ex: les 199 premiers jours d'une SMA200).

## 5. Interactions avec les autres Skills
- Reçoit les données de `market-data-ingestion`.
- Fournit les signaux de trading purs à `risk-money-management` et `execution-order-routing`.
