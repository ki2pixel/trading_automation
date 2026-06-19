# Automatiser les campagnes d'optimisation en masse

**TL;DR** : Pour optimiser des dizaines d'actifs sur plusieurs passes successives, n'utilisez pas la ligne de commande manuelle. **Enfilez programmatiquement des tâches (jobs) dans la base SQLite via des scripts de campagne dédiés**, puis laissez tourner le worker en tâche de fond pour une exécution robuste et résiliente.

Vous venez de qualifier 20 nouveaux actifs lors de la phase de screening. Vous devez à présent exécuter deux passes d'optimisation pour la stratégie Momentum-based ZigZag sur chacun d'eux : une première passe pour identifier le sweet spot du signal, puis une seconde passe pour tester les brackets de gestion du risque (Stop Loss et Take Profit fixes).

Cliquer 40 fois dans l'interface graphique pour configurer ces lancements est fastidieux ; écrire un script bash avec une boucle de commandes CLI successives est fragile. Si l'un des calculs subit un dépassement de mémoire (OOM Kill), votre boucle crashe en cours de route, vous laissant sans progression sauvegardée et avec un processeur surchargé.

Pour éviter cela, le moteur propose un modèle d'orchestration par file de tâches.

---

## Deux philosophies d'exécution

### ❌ Le script de boucle CLI séquentiel
Ce modèle exécute directement les commandes d'optimisation les unes après les autres.

```bash
# Une approche fragile et non supervisée
for symbol in belgbeeur daideeur cafreur; do
  python3 -m backtest_engine optimize --strategy momentum_based_zigzag --symbol $symbol --timeframe 15 ...
done
```

- **Absence de résilience** : Si le processus plante au milieu de la nuit, toute la file s'arrête.
- **Aucune visibilité** : Impossible de suivre la progression sans scruter la sortie brute du terminal.
- **Monopolisation des ressources** : Difficile de limiter la charge CPU ou de répartir les tâches sur d'autres workers.

### ✅ L'orchestration programmatique par SQLite
Ce modèle sépare la définition de la campagne de son calcul réel.

```python
# scripts/queue_zigzag_campaign.py
from backtest_engine.job_store import OptimizerJob, OptimizerJobStore

store = OptimizerJobStore()
for symbol, timeframe in targets:
    job = OptimizerJob(id=uuid4().hex, request=request_payload, ...)
    store.add(job)
```

- **Exécution asynchrone** : Les tâches sont stockées de façon persistante dans `jobs.sqlite3`.
- **Surveillance en temps réel** : La progression est visible dans l'UI ou via les tables SQLite.
- **Workers découplés** : Vous pouvez lancer plusieurs workers en parallèle pour consommer la file d'attente.

---

## Comparatif des approches

| Critère | Boucle CLI Manuelle | Tâches enfilées SQLite |
| :--- | :--- | :--- |
| **Persistance au crash** | ❌ Perdue si le script parent s'arrête | ✅ Reprend là où elle s'est arrêtée |
| **Parallélisation** | ❌ Complexe à gérer en bash | ✅ Native (plusieurs workers sur la même DB) |
| **Modification à chaud** | ❌ Impossible sans tuer la boucle | ✅ Possibilité d'annuler ou réordonner les jobs |
| **Visibilité UI** | ❌ Aucune | ✅ Progression visible barre par barre |

---

## La structure d'un script de campagne programmatique

Tous les scripts de campagne stockés dans le dossier `scripts/` (ex: `queue_zigzag_campaign.py`, `queue_hmm_campaign.py`) suivent le même patron de conception en quatre étapes :

### 1. Filtrage et sélection des cibles
Le script parse le fichier de screening le plus récent pour extraire automatiquement les candidats éligibles tout en appliquant les filtres d'exclusion définis par la recherche.

```python
def parse_eligible_targets(report_path: Path) -> list[tuple[str, str]]:
    targets = []
    # Lecture du rapport et parsing de la table Markdown
    # Exclusion des actifs historiques ou non éligibles
    return targets
```

### 2. Calcul des dimensions de recherche
Le script calcule la taille brute de l'espace de recherche (la combinatoire) et détermine le nombre d'itérations bayésiennes optimal pour l'intensité demandée (ex: ~2.6% de la grille canonique pour une intensité "deep").

```python
specs = [build_parameter_spec(p["name"], p, strategy="strategy_name") for p in parameters]
grid_validation = validate_parameter_grid(specs, optimization_mode="bayesian")
canonical_iterations = grid_validation["canonical_iterations"]
bayesian_max_iterations = calculate_bayesian_iterations(canonical_iterations)
```

### 3. Construction des payloads et verrouillage des passes
Pour les pipelines multi-passes, le script verrouille les configurations validées dans les étapes précédentes via le dictionnaire `fixed_overrides` :
- **Passe 1 (Signal Brut)** : On bloque tous les paramètres de Stop Loss, Take Profit et Trailing Stop à `False`.
- **Passe 2 (Gestion du Risque)** : On verrouille les paramètres de signal optimaux découverts en Passe 1 (ex: `rsi_period`, `qqe_factor`) et on déclare la plage de recherche sur les pourcentages de SL/TP fixes.

```python
# Exemple de verrouillage pour la Passe 2
fixed_overrides = {
    "use_safety_stop": False,
    "enable_trailing_stop": False,
    "rsi_period": 22,
    "qqe_factor": 5.0,
    "rsi_smoothing": 15,
    "ob": 90.0,
    "os": 24.0,
    "signal_mode": "Live"
}
```

### 4. Injection dans l'OptimizerJobStore
Chaque job est instancié avec un identifiant unique (UUID) et son statut initialisé à `PENDING` avant d'être sauvegardé dans la base.

```python
store = OptimizerJobStore()
job = OptimizerJob(
    id=uuid4().hex,
    created_at=time.time(),
    request=request_payload,
    progress={"currentIteration": 0, "totalIterations": bayesian_max_iterations}
)
store.add(job)
```

---

## Le cas d'étude du Profit Factor Infini

Lors de l'évaluation des filtres et des contraintes d'optimisation (tels que la contrainte `--min-profit-factor`), un problème classique d'optimisation mathématique se pose.

**La singularité du Profit Factor** : Si une stratégie génère des gains robustes sur plusieurs trades mais n'enregistre absolument aucune perte sur la période testée (un cas de "stratégie parfaite" ou de tendance pure), le calcul mathématique classique du Profit Factor divise par zéro ($PnL_{Gains} / 0$), ce qui renvoie une valeur indéfinie (`None`).

Dans les premières versions de l'optimizer, ce cas particulier provoquait une violation systématique de la contrainte de Profit Factor minimum, rejetant à tort des configurations d'une efficience absolue.

Le système intègre désormais un mécanisme de contournement de cette anomalie dans `backtest_engine/optimizer.py` :

```python
winning_trades = _score_value(metrics, "winning_trades") or 0
losing_trades = _score_value(metrics, "losing_trades") or 0
is_infinite_pf = (profit_factor is None) and (winning_trades > 0) and (losing_trades == 0)

if not is_infinite_pf:
    if profit_factor is None or profit_factor < constraints.min_profit_factor:
        violations.append(f"profit_factor {profit_factor} < min_profit_factor {constraints.min_profit_factor}")
```

Si le ratio de perte est nul sur un échantillon de trades actifs, la contrainte de Profit Factor est automatiquement validée, protégeant ainsi l'Alpha brut des configurations exceptionnelles lors des campagnes d'optimisation automatiques.

---

## Lancer et surveiller une campagne

Une fois les jobs injectés dans la file d'attente SQLite :

1. Lancer le worker pour démarrer les calculs :
   ```bash
   ./start_backtest_engine.sh start
   # ou directement via python3 :
   python3 -m backtest_engine worker --output-dir reports/local_optimizer
   ```
2. Inspecter les états en interrogeant le Job Store :
   ```bash
   python3 -m backtest_engine list-jobs
   ```

---

## La règle d'or

> **La règle d'or** : Programmez l'enfilement pour garantir la reproductibilité ; déléguez l'exécution au Job Store pour sécuriser la résilience.

<!-- Guidé par documentation/SKILL.md — sections: Technical Article Structure, Technical Writing Voice, Punctuation Guidelines, Avoiding AI-Generated Feel -->

