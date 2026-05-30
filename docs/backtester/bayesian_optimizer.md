# Documentation : Optimiseur Bayésien

## TL;DR

**TL;DR** : L'optimiseur bayésien utilise une architecture de multiprocessing stricte avec une mémoire partagée POSIX pour éviter les deadlocks du compilateur LLVM et les pics de RAM lors des essais parallèles d'Optuna.

## Le Problème de Deadlock avec LLVM

Lors de la création d'un backtester haute performance, le choix évident pour l'optimisation est de combiner Optuna avec des fonctions compilées par Numba et `joblib` pour l'exécution parallèle.

❌ **Le Parallélisme "Naïf"**

```python
# Ceci va provoquer un deadlock de façon aléatoire
study.optimize(objective_function, n_jobs=-1)
```

Le multithreading par défaut d'Optuna ou le multiprocessing basé sur le forking de `joblib` interagit de façon désastreuse avec Numba (LLVM). Lorsque le processus parent "fork" alors que LLVM est en train de compiler ou de maintenir un verrou interne, le processus enfant hérite d'un verrou bloqué. Toute la suite d'optimisation se bloque indéfiniment, consommant 100% du CPU sur un seul cœur sans rien faire.

Pire encore, copier de larges DataFrames Pandas (données OHLCV + indicateurs) vers 16 ou 32 processus de travail provoque un pic de RAM massif (souvent >32 Go), entraînant l'intervention de l'OOM killer de l'OS qui termine le backtest.

✅ **L'Architecture "Spawn + Mémoire Partagée"**

```python
# Pool explicite (spawn) avec mémoire partagée sans copie (zero-copy)
with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("spawn")) as executor:
    # Les workers s'attachent à la mémoire partagée POSIX pré-allouée
    futures = [executor.submit(_evaluate_worker, ...) for _ in range(n_trials)]
```

En utilisant strictement le contexte `spawn`, nous nous assurons qu'un interpréteur Python vierge est lancé pour chaque worker, éliminant ainsi les deadlocks hérités. Pour résoudre le pic de RAM, nous utilisons la mémoire partagée POSIX (`/dev/shm`).

## Architecture de Grille en Mémoire Partagée POSIX

Au lieu de passer des DataFrames aux workers, le processus parent pré-alloue des grilles de mémoire contiguës.

1. **Pré-calcul** : Le processus parent calcule tous les états possibles des indicateurs (par ex., une grille 3D de MM ou de profils de volatilité) avant de lancer les workers.
2. **Allocation** : Ces grilles sont allouées dans `/dev/shm` via `SharedIndicatorVolume`.
3. **Vues Zero-Copy** : Les workers reçoivent les métadonnées (forme, dtype, nom_shm) et s'attachent à la mémoire en utilisant des vues zero-copy `numpy.ndarray`.

### Tableau des Compromis : Mémoire vs Flexibilité

| Approche | Utilisation Mémoire | Risque de Deadlock | Complexité d'Implémentation |
| -------- | ------------------- | ------------------ | --------------------------- |
| Copie de DataFrames | ❌ Très Haute (Risque OOM) | ❌ Élevé (si forking) | ✅ Faible |
| Mémoire Partagée POSIX | ✅ Extrêmement Faible (1x la taille) | ✅ Aucun (avec spawn) | ❌ Élevée |

## Le Traqueur de Convergence (Convergence Tracker)

Exécuter 10 000 essais est un gaspillage de ressources informatiques si l'optimiseur a déjà trouvé le bassin optimal. Le `ConvergenceTracker` surveille la progression de l'optimisation et s'interrompt prématurément selon trois critères :

1. **Patience** : Aucune amélioration absolue pendant `N` itérations consécutives.
2. **Progression par Fenêtre** : Aucune amélioration *significative* (>1%) pendant `W` fenêtres consécutives de `M` essais.
3. **Coupe-circuit (Circuit Breaker)** : Une sécurité globale qui stoppe l'optimisation si le nombre total d'itérations depuis la dernière amélioration dépasse un certain ratio du budget total.

## Nettoyage de Cycle de Vie Non-lié (Unlinked Lifecycle)

Lorsqu'on manipule `/dev/shm`, si un worker plante ou que l'utilisateur appuie sur `Ctrl+C`, le segment de mémoire partagée devient orphelin, provoquant des fuites de mémoire persistantes.

L'optimiseur bayésien implémente un nettoyage au cycle de vie non-lié (unlinked) : les volumes de mémoire sont désolidarisés immédiatement après l'attachement ou libérés de manière fiable dans un bloc `finally`, garantissant qu'aucune mémoire fantôme ne persiste entre les sessions.

## La Règle d'Or : Calculer Une Fois, Partager Partout

**La Règle d'Or : Ne recalculez jamais ce que vous pouvez partager, et ne partagez jamais ce que vous ne pouvez pas sérialiser.** 

En pré-calculant les grilles d'indicateurs dans le processus parent et en les partageant via la mémoire POSIX, les workers n'exécutent que la boucle de simulation Numba ultra-rapide.
