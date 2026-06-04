# Moteur de Métriques (Metrics Engine)

**TL;DR** : Si vous devez évaluer des millions de combinaisons de paramètres, ne calculez pas le ratio de Sharpe avec Pandas. Utilisez une fonction de score rapide vectorisée via NumPy pour la boucle d'optimisation ; ne calculez les métriques complètes que pour les meilleurs candidats.

Vous exécutez un optimiseur bayésien. Il teste des milliers de configurations par minute. Vous remarquez que le processeur est constamment à 100%, mais seule une fraction des combinaisons est réellement évaluée. En profilant le code, vous réalisez que le calcul des métriques standards comme le Max Drawdown et le Ratio de Sharpe prend plus de temps que le backtest lui-même.

C'est le piège de la surcharge des métriques. Lorsque vous devez évaluer une stratégie, la précision exacte d'une métrique annualisée importe souvent peu pendant la phase de recherche. Vous avez simplement besoin d'un score relatif pour comparer deux ensembles de paramètres.

### ❌ La Boucle de "Métriques Complètes"

Calculer l'ensemble des métriques à chaque itération :

```python
def evaluate_params(params):
    equity = run_backtest(params)
    # Lent : calcule drawdown, sharpe, sortino, calmar...
    metrics = compute_metrics(equity)
    return metrics['sharpe_ratio']
```

### ✅ La Boucle de "Score Rapide"

Utiliser un score proxy vectorisé pour la recherche, puis les métriques complètes pour les rapports :

```python
def evaluate_params(params):
    equity = run_backtest(params)
    # Rapide : calcul purement vectorisé (NumPy)
    return compute_fast_score(equity)
```

## Système de Métriques à Deux Niveaux

Le module `metrics.py` sépare le calcul des métriques en deux chemins distincts :

1. **`compute_fast_score`** : Utilisé à l'intérieur de la boucle d'optimisation. Il s'appuie uniquement sur des tableaux `numpy`, évitant ainsi la surcharge des `pandas.DataFrame` et des calculs arithmétiques complexes sur les dates. Il fournit un proxy robuste de la qualité de la stratégie.
2. **`compute_metrics`** : Utilisé une fois l'optimisation terminée. Il calcule la suite complète des métriques : Ratio de Sharpe Déflaté (DSR), Ratio de Calmar, Ratio de Sortino, et Taux de Réussite (Win Rate).

### Compromis

| Fonction | Vitesse | Précision | Phase d'Utilisation |
| -------- | ------- | --------- | ------------------- |
| `compute_fast_score` | ✅ Haute | ❌ Proxy | Boucle d'Optimisation |
| `compute_metrics` | ❌ Basse | ✅ Exacte | Rapports Finaux |

## La Règle d'Or : Optimiser pour la Recherche, Rapporter pour les Humains

Lors d'une recherche de paramètres, l'optimiseur ne se soucie que du classement relatif. Réservez les métriques coûteuses et humainement lisibles pour le rapport final.
