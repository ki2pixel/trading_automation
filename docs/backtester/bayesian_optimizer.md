# Optimiseur Bayésien

**TL;DR** : Si vous voulez trouver les meilleurs paramètres de trading sans attendre une semaine, n'utilisez pas la recherche par grille (grid search). Nous utilisons Optuna pour une recherche bayésienne intelligente, couplée à un `ConvergenceTracker` d'arrêt prématuré et à des allocateurs de mémoire isolés.

Vous avez conçu une stratégie de trading avec 5 paramètres. Si vous testez 10 valeurs pour chacun, cela représente 100 000 combinaisons. Une recherche par grille brute prend des heures. Vous vous tournez vers Optuna, qui apprend des essais passés pour deviner les meilleurs paramètres.

Cependant, tel quel, l'utilisation d'Optuna sur d'énormes ensembles de données financières crée d'énormes goulots d'étranglement de mémoire et des deadlocks LLVM lors de la mise à l'échelle sur plusieurs cœurs de processeur.

Pour résoudre ce problème, notre Optimiseur Bayésien impose une stricte séparation des responsabilités : il orchestre la stratégie de recherche (Optuna) et le suivi de convergence, mais délègue toute la gestion de la mémoire à des allocateurs dédiés.

### ❌ L'Approche "Tout en un"

Lancer l'optimisation avec un parallélisme naïf et un passage de mémoire direct :

```python
def objective(trial):
    params = suggest_params(trial)
    # Une énorme copie de mémoire se produit implicitement ici
    return run_backtest(huge_data, params)

study.optimize(objective, n_jobs=-1) # Provoque un deadlock avec LLVM/Numba !
```

### ✅ L'Approche Orchestrée

Utiliser un multiprocessing basé sur `spawn`, une allocation mémoire isolée et un arrêt prématuré intelligent :

```python
# 1. La mémoire est allouée UNE SEULE FOIS via shm_allocators.py
shm_info = _allocate_strategy_memory(...)

# 2. Le ConvergenceTracker évite de perdre du temps
tracker = ConvergenceTracker(patience=500)

# 3. Le pool 'spawn' explicite évite les deadlocks Numba
with get_context("spawn").Pool(workers) as pool:
    # Les workers ne reçoivent que des références, pas des données
    run_bayesian_optimization(pool, shm_info, tracker)
```

## Le Traqueur de Convergence (Convergence Tracker)

Exécuter 10 000 essais est un gaspillage de puissance de calcul si l'optimiseur a déjà trouvé le maximum global après 1 000 essais. Le `ConvergenceTracker` surveille la progression de l'optimisation et l'interrompt prématurément selon des critères spécifiques :

1. **Patience** : Aucune amélioration absolue pendant `N` itérations consécutives.
2. **Progression par Fenêtre** : Aucune amélioration *significative* (>1%) pendant `W` fenêtres consécutives de `M` essais.

## Architecture Mémoire Refactorisée

*Note : Dans les versions précédentes, l'Optimiseur Bayésien gérait sa propre mémoire partagée (`/dev/shm`). Cette logique a été extraite.*

Pour réduire la complexité cognitive (Score F abaissé à C), toute l'orchestration de la mémoire partagée et le nettoyage du cycle de vie non-lié sont désormais pris en charge par `shm_allocators.py`. L'Optimiseur Bayésien ne reçoit que des objets de référence légers.

### Compromis

| Approche | Vitesse de Recherche | Utilisation des Ressources | Complexité du Code |
| -------- | -------------------- | -------------------------- | ------------------ |
| Recherche par Grille | ❌ Lente | ❌ Haute (essais gaspillés) | ✅ Faible |
| Bayésien + Traqueur | ✅ Rapide | ✅ Basse (arrêt anticipé) | ❌ Haute |

## La Règle d'Or : Déléguer et Terminer Tôt

Le seul rôle de l'optimiseur est de choisir les meilleurs paramètres suivants et de décider quand s'arrêter. Déléguez tout le reste-spécialement l'allocation mémoire et le calcul des métriques-à des sous-systèmes dédiés.
