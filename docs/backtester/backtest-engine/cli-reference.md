# Guide de référence de la CLI

**TL;DR** : L'ensemble du moteur de backtest est pilotable depuis une commande unique : `python3 -m backtest_engine <sous-commande>`. Découvre comment interagir avec tes données et tes simulations directement depuis ton terminal.

Tu aimes scripter des tâches récurrentes, automatiser des optimisations complexes à distance (par exemple sur un serveur dédié) ou simplement aller plus vite qu'en cliquant sur une interface Web ? 

La ligne de commande (CLI) est ta meilleure amie. Elle te donne un accès complet et non bridé à toutes les fonctionnalités du moteur : du scan des fichiers de données jusqu'au nettoyage de la base de données après un crash.

Voici les outils à ta disposition et comment les utiliser.

---

## Les sous-commandes en un coup d'œil

| Ce que tu veux faire | Sous-commande à utiliser |
|---|---|
| Vérifier la qualité de tes fichiers CSV bruts de collecte | **`scan`** |
| Nettoyer les données brutes et générer des fichiers Parquet | **`build-canonical`** |
| Lancer une simulation de trading unitaire | **`run`** |
| Chercher automatiquement les meilleurs paramètres d'indicateurs | **`optimize`** |
| Extraire des recommandations et des "sweet spots" après une optimisation | **`interpret-optimization`** |
| Démarrer le serveur API Web local | **`serve`** |
| Lancer un worker pour traiter les tâches d'optimisation en arrière-plan | **`worker`** |
| Nettoyer la base de données après un crash brutal de worker | **`mark-crashed`** |

> [!NOTE]
> Toutes les commandes partagent un argument racine global optionnel : `--repo-root PATH`. Il permet de spécifier le dossier de ton projet si tu lances tes commandes depuis un autre répertoire (par défaut, le moteur se repère tout seul par rapport au chemin du code).

---

## 1. Préparer et valider tes données

### `scan` : Inspecter tes CSV bruts
Avant de confier ton argent à une stratégie, vérifie que les données de ton tableur de collecte ne contiennent pas d'incohérences physiques (comme un prix OHLC absurde).

```bash
python3 -m backtest_engine scan --symbol GMAB --price-repair auto
```

**Options clés :**
- `--symbol` (requis) : Le nom du ticket d'action à inspecter.
- `--price-repair none|auto` (défaut : `none`) : Tente de réparer les décalages de décimales (ex: division heuristique par 10 ou 100 si la virgule est manquante).
- `--market-divisor` (défaut : 1.0) : Divise tous les prix par un coefficient fixe si tes fichiers bruts ont été multipliés lors de l'export.

---

### `build-canonical` : Transformer les CSV en Parquet propre
Cette commande est indispensable après chaque collecte. Elle lit tes CSV bruts, applique les corrections de splits d'actions, réaligne les prix et génère des fichiers Parquet compacts et ultra-rapides à lire dans `storage/processed/`.

```bash
python3 -m backtest_engine build-canonical --format parquet --divisor-overrides-file configs/canonical_divisor_overrides.json
```

**Options clés :**
- `--format csv|parquet` (défaut : `csv`) : Choisis `parquet` pour des performances optimales.
- `--output-dir` (défaut : `storage/processed`) : Le dossier où stocker tes fichiers nettoyés.
- `--divisor-overrides-file` : Chemin vers le fichier JSON spécifiant les divisions à appliquer à la volée pour certains symboles historiques corrompus.

---

## 2. Simuler et Optimiser

### `run` : Exécuter un backtest unique
C'est le couteau suisse pour valider une intuition sur une stratégie précise.

```bash
python3 -m backtest_engine run --strategy hma_crossover --symbol GMAB --config configs/strategies/hma_crossover.default.json
```

**Options clés :**
- `--strategy` : La stratégie à exécuter parmi les 7 proposées (`hma_crossover`, `range_filter`, `3commas_bot`, `pmax_explorer`, `bjorgum_double_tap`, `noise_boundary_intraday`, `adaptive_volatility_trend`).
- `--symbol` (requis) : L'action ou la paire à simuler.
- `--config` : Le fichier de configuration de référence contenant les variables de l'indicateur.
- `--timeframe` (défaut : 5) : Temps d'agrégation des barres en minutes (multiple de 5).
- `--start-date` / `--end-date` : Borne tes calculs dans le temps (format `YYYY-MM-DD`).
- `--whole-shares` : Force l'achat d'actions entières (pas de fractions).

---

### `optimize` : Chercher les meilleurs paramètres
Ne passe pas des heures à modifier manuellement tes indicateurs. Laisse le moteur explorer des milliers de combinaisons, soit de manière exhaustive (Grid), soit intelligemment (Bayésien via l'algorithme TPE d'Optuna).

```bash
python3 -m backtest_engine optimize --strategy hma_crossover --symbol GMAB --optimization-mode bayesian --max-iterations 300 --param fast_len=5:60:1 --param slow_len=20:120:1
```

**Options clés :**
- `--optimization-mode grid|bayesian` (défaut : `grid`).
- `--param` (requis, cumulable) : Définit l'espace à explorer pour chaque variable.
  - Plage numérique : `nom=min:max:step` (ex: `fast_len=5:30:5`).
  - Choix textuels : `nom=optionA|optionB` (ex: `trade_direction_mode=Long only|Long & Short`).
- `--max-iterations` (défaut : 10000) : Nombre maximum d'essais pour l'optimisation bayésienne.
- `--score` (défaut : `sharpe_ratio`) : La métrique de tri que tu veux maximiser (ex: `total_net_pnl`, `profit_factor`, `win_rate_pct`).
- `--workers` : Le nombre de processus CPU en parallèle à utiliser.

---

### `interpret-optimization` : Analyser les sweet spots
Une fois qu'une optimisation est terminée, cette commande t'aide à repérer les zones de paramètres stables (les "sweet spots") pour éviter de choisir une valeur isolée et trop ajustée au passé.

```bash
python3 -m backtest_engine interpret-optimization --job-dir reports/local_optimizer/hma_crossover/GMAB/T_2026-05-23_10-00-00
```

**Options clés :**
- `--job-dir` (requis) : Le répertoire où sont stockés les fichiers de résultats de ton run d'optimisation.
- `--top-quantile` (défaut : `0.95`, ou lu depuis `optimization_config.json`) : Le pourcentage des meilleures itérations à conserver pour définir la zone de robustesse.
- `--score-tolerance-pct` (défaut : `0.10`, ou lu depuis `optimization_config.json`) : La tolérance relative du score par rapport à la meilleure itération pour définir la zone de robustesse.

> [!TIP]
> Si `--top-quantile` ou `--score-tolerance-pct` ne sont pas passés en ligne de commande, le moteur essaiera d'abord de les lire directement dans le fichier `optimization_config.json` du répertoire du job. C'est idéal pour tuner l'interprétation par job.

---

## 3. Orchestration & Production locale

### `serve` : Lancer l'API FastAPI
Cette commande démarre le serveur web local qui expose l'interface de visualisation graphique et reçoit les requêtes du tableau de bord.

```bash
python3 -m backtest_engine serve --host 127.0.0.1 --port 8765
```

---

### `worker` : Lancer la file de tâches en arrière-plan
Le worker écoute la file d'attente stockée dans notre base de données SQLite locale. Dès que tu lances une optimisation depuis l'interface web, le worker s'en empare et l'exécute sur tes cœurs de processeur.

```bash
python3 -m backtest_engine worker --poll-interval 1.0
```

---

### `mark-crashed` : Nettoyer après un plantage
Si ton ordinateur s'est éteint brusquement ou si un processus d'optimisation a été tué par le système (par exemple pour manque de mémoire OOM), la base de données peut croire que la tâche est toujours "en cours". Cette commande débloque la situation.

```bash
python3 -m backtest_engine mark-crashed --worker-id worker-node-01 --exit-code 137
```
