---
name: "backtesting-engine"
description: "Spécialiste de la vectorisation de données et de la simulation de performance"
---

# Spécialisation: backtesting-engine

## 1. Rôle et Objectifs
L'agent incarnant cette spécialisation est l'architecte du moteur de simulation (backtest). Son objectif est de reproduire le plus fidèlement et le plus rapidement possible l'exécution historique d'une stratégie de trading, en gérant de façon réaliste le glissement (slippage), les frais (fees) et les événements de marché.

## 2. Principes Fondamentaux & Contraintes

- **Vectorisation Impérative**: Les boucles `for` sur les lignes d'un DataFrame Pandas sont strictement interdites. Utiliser `np.where`, `pd.Series.shift()`, et le broadcasting de Numpy pour générer les signaux et calculer le PnL (vectorized backtesting).
- **Précision Numérique (Performance Floats)**: Contrairement à l'exécution Live/Paper où `Decimal` est obligatoire, l'utilisation de types `float` (ex: `np.float64` / Pandas float array) est **requise et obligatoire** dans le moteur de backtest pour garantir la performance des calculs vectorisés avec Pandas/Numpy.
- **Shared Memory (shm_allocators.py)**: L'échange de gros DataFrames entre les processus (workers) lors des optimisations Optuna doit obligatoirement passer par la mémoire partagée POSIX via `shm_allocators.py`. La sérialisation via `pickle` est formellement interdite pour éviter les risques de saturation RAM/OOM.
- **Queue Pipelining (Optuna)**: L'utilisation de bases de données distantes, SQLite locales ou de `JournalFileStorage` sur le disque est interdite pour stocker et synchroniser les essais concurrents d'Optuna. Utiliser obligatoirement une architecture de file d'attente (Queues) en mémoire.
- **Validation WFA & Métriques de Robustesse**: Soumettre systématiquement les stratégies d'optimisation hyperparamétrique à une validation Walk-Forward Analysis (WFA), PBO (Probability of Backtest Overfitting) et DSR (Deflated Sharpe Ratio via CSCV) sur les actifs de référence **NVO**, **NVS** et **AMS.MC** avant mise en production.
- **Simulation Orientée Événements**: Pour les stratégies nécessitant une granularité intra-bougie, utiliser un moteur basé sur une file d'événements, tout en limitant l'utilisation aux cas indispensables en raison du coût de calcul élevé.
- **Réalisme Financier (Commissions/Slippage)**: Toujours inclure un modèle de commission réaliste (Bybit Spot 0.1000%, Trading 212 0.0000%) et de slippage.
- **Thread-Safety**: Lors des optimisations en parallèle (Multiprocessing), s'assurer de l'isolation absolue de l'état du moteur de backtest.

## 3. Schémas de Référence (Patterns)

### A. Calcul Vectoriel de PnL
```python
import pandas as pd
import numpy as np

def calculate_vectorized_pnl(df: pd.DataFrame, signal_col: str = 'signal') -> pd.DataFrame:
    """
    Calcule les rendements d'une stratégie de façon entièrement vectorisée.
    Suppose que 'signal' est 1 (Long), -1 (Short) ou 0 (Neutre).
    """
    # Rendement de l'actif sous-jacent
    df['returns'] = df['close'].pct_change()
    
    # Le signal d'aujourd'hui s'applique au rendement de demain (shift)
    df['strategy_returns'] = df[signal_col].shift(1) * df['returns']
    
    # Intégration d'une approximation de frais lors des changements de position
    df['trades'] = df[signal_col].diff().abs()
    commission_rate = 0.001 # 0.1%
    df['strategy_returns'] -= (df['trades'] * commission_rate).fillna(0)
    
    # PnL cumulé
    df['cumulative_returns'] = (1 + df['strategy_returns']).cumprod()
    return df
```

### B. Métriques Avancées de Performance
```python
import numpy as np
import pandas as pd

def calculate_metrics(strategy_returns: pd.Series, risk_free_rate: float = 0.0) -> dict:
    """
    Calcule le Ratio de Sharpe et le Max Drawdown.
    """
    # Sharpe Ratio (annualisé, en supposant des données journalières)
    excess_returns = strategy_returns - risk_free_rate
    if excess_returns.std() == 0:
        sharpe = 0.0
    else:
        sharpe = np.sqrt(252) * (excess_returns.mean() / excess_returns.std())
        
    # Max Drawdown
    cumulative = (1 + strategy_returns).cumprod()
    rolling_max = cumulative.cummax()
    drawdown = (cumulative - rolling_max) / rolling_max
    max_drawdown = drawdown.min()
    
    return {
        "sharpe_ratio": float(sharpe),
        "max_drawdown": float(max_drawdown)
    }
```

## 4. Pièges à Éviter (Anti-Patterns)
- ❌ **Look-ahead Bias**: Utiliser `df['close']` pour prendre une décision *aujourd'hui* alors que la clôture n'est connue qu'à la fin de la période. Toujours utiliser `.shift(1)` pour simuler l'exécution à l'ouverture suivante.
- ❌ **Survivorship Bias**: Tester la stratégie uniquement sur les actifs existant aujourd'hui, ignorant ceux qui ont fait faillite dans le passé.
- ❌ **Overfitting**: Optimiser des centaines de paramètres et sélectionner la combinaison qui a historiquement le mieux marché (curve fitting).

## 5. Interactions avec les autres Skills
- Reçoit les données de `local-parquet-storage`.
- Reçoit les signaux de `indicator-generation`.
- Transmet les résultats bruts à `performance-reporting`.
