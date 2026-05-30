# Documentation : Stratégie Noise Boundary Intraday

## TL;DR

**TL;DR** : La stratégie Noise Boundary utilise l'ouverture quotidienne et la fermeture précédente comme points d'ancrage, en construisant des bandes de volatilité pour filtrer le bruit du marché. Elle associe cela à un `vectorbt_prescan` fulgurant pour restreindre l'espace des paramètres avant une optimisation bayésienne coûteuse.

## Le Goulot d'Étranglement de l'Optimisation

Vous avez conçu une stratégie de retour à la moyenne (mean-reversion) intraday. Elle utilise la volatilité historique pour définir les supports et les résistances. Vous souhaitez optimiser le paramètre `lookback_days` ainsi que le `volatility_multiplier_enter`. Vous soumettez alors une gigantesque grille de paramètres à Optuna. 

Optuna commence à échantillonner à l'aveugle. Il teste des multiplicateurs de `0.1` (ce qui provoque des transactions chaque minute et ruine le capital en frais) et de `5.0` (ce qui ne déclenche aucun trade). Ainsi, 80 % de votre budget d'optimisation est gaspillé sur des combinaisons de paramètres mathématiquement vouées à l'échec.

## La Solution du Pré-Scan VectorBT

Avant même qu'Optuna ne démarre sa recherche TPE (Tree-structured Parzen Estimator), la stratégie implémente une méthode `vectorbt_prescan`.

### ❌ L'Optimisation "Parzen à l'Aveugle"

```python
# Optuna explore un espace massif et non contraint
study.optimize(objective, n_trials=5000)
```

### ✅ L'Optimisation "Pré-Scannée"

```python
# 1. VectorBT évalue 20 000 combinaisons de paramètres en 5 secondes
# 2. Il restreint les limites des paramètres aux seules plages rentables
# 3. Optuna explore l'espace concentré à haute probabilité
restricted_specs = vectorbt_prescan(data, parameter_specs)
study.optimize(objective, parameter_specs=restricted_specs)
```

En tirant parti de la simulation de portefeuille vectorisée et hautement optimisée de `vectorbt` (`vbt.Portfolio.from_signals`), nous testons des dizaines de milliers de combinaisons de seuils (en utilisant des données de 5 minutes sous-échantillonnées) en quelques secondes. Le résultat restreint l'espace de recherche d'Optuna, garantissant que l'optimiseur bayésien consacre son budget à affiner de bonnes stratégies plutôt qu'à découvrir des échecs évidents.

## Logique de Signal : Volatilité Ancrée

La stratégie évite les moyennes mobiles standard, qui ont du retard sur l'action des prix intraday. Au lieu de cela, elle ancre ses limites à **l'Ouverture Quotidienne** (Daily Open) et à la **Fermeture du Jour Précédent** (pour prendre en compte les gaps de la nuit).

```python
anchor_up = max(daily_open, prev_day_close)
anchor_down = min(daily_open, prev_day_close)

upper_enter = anchor_up * (1 + multiplier_enter * mapped_vol)
lower_enter = anchor_down * (1 - multiplier_enter * mapped_vol)
```

Où `mapped_vol` correspond à la moyenne glissante de la volatilité pour cette heure précise de la journée lors des jours précédents.

## Tableau des Compromis : VectorBT vs Backtester Personnalisé

| Outil | Vitesse | Logique d'Exécution | Empreinte Mémoire |
| ----- | ------- | ------------------- | ----------------- |
| VectorBT | ✅ Instantané | ❌ Basique (MOC/Signal) | ❌ Massive (Expansion de matrices) |
| Noyau Numba | ❌ Itératif | ✅ Complexe (Stops en cascade, VWAP) | ✅ Faible (État itératif) |

## La Règle d'Or : Pré-Scanner Largement, Optimiser Précisément

**La Règle d'Or : Utilisez les mathématiques matricielles vectorisées pour éliminer le bruit, et les noyaux orientés événements pour simuler la réalité.**

VectorBT est trop rigide pour les sorties complexes en cascade (ladders) et les orchestrations basées sur le temps, mais il est mathématiquement sans pareil pour la validation large des signaux. Utilisez-le comme un filtre grossier pour guider votre optimiseur précis.
