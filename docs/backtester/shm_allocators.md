# Allocateurs de Mémoire Partagée

**TL;DR** : Si vous voulez exécuter des backtests en parallèle rapidement, ne passez pas de tableaux massifs à chaque processus. Utilisez `/dev/shm` pour allouer les données spécifiques à la stratégie une seule fois ; laissez les workers y lire directement.

Vous construisez un optimiseur. Vous avez 10 ans de données à la minute. Vous décidez de lancer 16 processus de travail (workers) pour tester différents paramètres. Soudain, votre machine gèle. Votre RAM est saturée. Vous venez de copier le même jeu de données de 2 Go 16 fois.

C'est le piège de la duplication de mémoire. En Python, `multiprocessing` peut sérialiser et dupliquer les arguments envoyés aux workers. Lorsqu'on manipule des données financières haute fréquence ou des indicateurs pré-calculés, cette approche s'effondre sous son propre poids.

Pour résoudre ce problème, nous avons extrait toute l'allocation mémoire dans `shm_allocators.py`.

### ❌ L'Approche par Duplication

Passer les données directement aux workers copie la mémoire en arrière-plan :

```python
def worker(data, params):
    # 'data' est copié pour chaque worker
    return run_backtest(data, params)

with Pool(16) as p:
    p.starmap(worker, [(huge_data, p) for p in params])
```

### ✅ L'Approche par Mémoire Partagée

Nous allouons les données une seule fois dans `/dev/shm` et ne passons que la référence :

```python
def worker(shm_name, shape, params):
    # Les workers s'attachent exactement au même bloc mémoire
    shm = SharedMemory(name=shm_name)
    data = np.ndarray(shape, buffer=shm.buf)
    return run_backtest(data, params)

shm = create_shared_memory(huge_data)
with Pool(16) as p:
    p.starmap(worker, [(shm.name, huge_data.shape, p) for p in params])
```

## Allocation Spécifique à la Stratégie

Toutes les stratégies n'ont pas besoin des mêmes données. Une stratégie de moyenne mobile a besoin des prix de clôture ; une stratégie de profil de volume a besoin de données au tick.

Le module `shm_allocators.py` expose des fonctions d'allocation dédiées pour chaque stratégie, comme `_allocate_hma_crossover` ou `_allocate_pmax_explorer`. Cela garantit que nous ne chargeons en RAM que ce qui est strictement nécessaire, tout en extrayant cette complexité de la boucle principale de l'optimiseur.

## Le Cycle de Vie Non-lié (Unlinked Lifecycle)

Lorsqu'on manipule `/dev/shm`, si un worker plante ou que l'utilisateur appuie sur `Ctrl+C`, le segment de mémoire partagée peut devenir orphelin. Cela crée une fuite de mémoire persistante qui survit jusqu'au prochain redémarrage de la machine.

Pour prévenir cela, les allocateurs implémentent un cycle de vie "non-lié" (unlinked) : les volumes sont immédiatement dissociés après l'attachement, ou libérés de manière fiable dans un bloc `finally`. Le système d'exploitation sait ainsi qu'il doit libérer la mémoire dès que le dernier worker ferme son accès.

### Compromis

| Approche | Efficacité Mémoire | Complexité d'Implémentation | Résilience aux Crashs |
| -------- | ------------------ | --------------------------- | --------------------- |
| Passage Direct | ❌ Médiocre | ✅ Faible | ✅ Haute |
| Mémoire Partagée | ✅ Excellente | ❌ Haute | ❌ Faible (Requiert un nettoyage strict) |

## La Règle d'Or : Calculer Une Fois, Partager Partout

Ne calculez jamais le même indicateur deux fois. Si un indicateur ne dépend pas des paramètres de l'optimiseur, calculez-le avant la boucle d'optimisation et placez-le en mémoire partagée.
