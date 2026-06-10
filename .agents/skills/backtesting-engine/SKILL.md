---
name: "backtesting-engine"
description: "Spécialiste de la vectorisation de données et de la simulation de performance"
---

# Spécialisation: backtesting-engine

## 1. Rôle et Objectifs
L'agent incarnant cette spécialisation est l'architecte du moteur de simulation (backtest). Son objectif est de reproduire le plus fidèlement et le plus rapidement possible l'exécution historique d'une stratégie de trading, en gérant de façon réaliste le glissement (slippage), les frais (fees) et les événements de marché.

## 2. Principes Fondamentaux & Contraintes

- **Vectorisation Impérative**: Les boucles `for` sur les lignes d'un DataFrame Pandas sont strictement interdites. Utiliser `np.where`, `pd.Series.shift()`, et le broadcasting de Numpy pour générer les signaux et calculer le PnL (vectorized backtesting).
- **Précision Numérique (Floats autorisés)**: Contrairement à l'exécution Live où `Decimal` est obligatoire, l'utilisation de types `float` (ex: `np.float64`) est **requise** dans ce moteur pour garantir la performance des calculs vectorisés avec Pandas/Numpy.
- **Shared Memory (shm_allocators.py)**: L'échange de gros DataFrames entre les processus (workers) lors des optimisations Optuna doit obligatoirement passer par la mémoire partagée POSIX. La sérialisation via `pickle` est formellement interdite (risque d'OOM).
- **Queue Pipelining (Optuna)**: L'utilisation de bases SQLite ou de `JournalFileStorage` sur le disque est interdite pour gérer l'historique des essais concurrents Optuna. Utiliser une architecture basée sur des Queues en mémoire.
- **Walk-Forward Analysis (WFA)**: Les stratégies doivent obligatoirement être soumises à une WFA robuste incluant le calcul des métriques NVO (Net Value Optimization), NVS (Net Value Stability) et AMS.MC (Average Monthly Sharpe Monte Carlo) pour valider leur robustesse avant tout passage en Live.
- **Simulation Orientée Événements**: Pour les stratégies nécessitant une granularité extrême (intra-bougie) ou un ordre d'exécution complexe (Event-Driven backtesting), un moteur de file d'attente (Queue) doit être utilisé, au détriment de la vitesse.
- **Réalisme Financier**: Toujours inclure un modèle de commission et de slippage. Un backtest sans friction n'a aucune valeur en production.
- **Thread-Safety**: Lors de l'optimisation de paramètres en parallèle (Multiprocessing), veiller à ce que l'état du moteur ne soit pas corrompu par la concurrence.

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
