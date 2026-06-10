# Standards de Code et Règles de Développement (Trading Automation)

## 1. Philosophie Générale
- **Lisibilité avant tout**: Le code est lu plus souvent qu'il n'est écrit. Privilégiez un code clair et explicite.
- **Fiabilité absolue**: Il s'agit d'une application financière. Les erreurs peuvent coûter de l'argent. La robustesse et la gestion rigoureuse des erreurs sont primordiales.
- **Testabilité**: Tout nouveau code doit être conçu pour être facilement testable (tests unitaires, tests d'intégration).

## 2. Standards Python (Backtest Engine & Scripts)
- **Typage Statique**: Utilisez systématiquement les annotations de type Python (`typing`). Chaque fonction, méthode et variable complexe doit être typée pour faciliter l'analyse statique (ex: `mypy`).
- **Précision Financière (CRITIQUE)**: Une distinction stricte s'applique selon le contexte d'exécution :
  - **Exécution Live (Routage/Broker API)** : L'utilisation de `float` natifs pour représenter des montants, des prix ou des tailles de lots est **strictement interdite** en raison des approximations d'arrondis. Utilisez exclusivement `decimal.Decimal` pour toute la logique financière et les calculs de PnL en production.
  - **Simulation de Backtest Vectorisée (Pandas/Numpy)** : L'utilisation de `float` (ex: `np.float64`) est **autorisée et requise** pour les moteurs de simulation (ex: `broker.py`) afin de garantir les performances de calcul vectorisé sur de larges historiques, là où `Decimal` dégraderait drastiquement les performances et la compatibilité avec Pandas/vectorbt.
  ```python
  # ❌ MAUVAIS (Live) : Utilisation de floats pour des montants réels (risques d'arrondis)
  pnl = trade.exit_price - trade.entry_price
  balance += pnl * 0.1

  # ✅ BON (Live) : Utilisation stricte de Decimal en production
  from decimal import Decimal
  pnl = Decimal(str(trade.exit_price)) - Decimal(str(trade.entry_price))
  balance += pnl * Decimal('0.1')

  # ✅ BON (Backtest) : Utilisation de float pour la performance vectorisée
  df['pnl'] = (df['close'] - df['open']) * df['qty']
  ```
- **Style et Formatage (PEP 8)**: Respectez les conventions de style Python.
- **Docstrings**: Documentez toutes les classes, méthodes publiques et modules complexes. Chaque docstring doit expliquer l'objectif de la fonction, les arguments attendus et ce qu'elle retourne.
- **Gestion des Exceptions**: Ne capturez jamais les exceptions de manière générique et silencieuse (`except Exception: pass`). Soyez spécifique dans les types d'exceptions capturées et loggez toujours les erreurs avec le contexte approprié.
- **Logging Transactionnel et Audit**: Pour la logique de routage et d'exécution d'ordres, le logging ne sert pas qu'au debug, il garantit la traçabilité légale. Les exécutions d'ordres doivent générer des logs structurés (format JSON) incluant a minima : `timestamp_utc`, `order_id`, `symbole`, `quantité`, `prix` et `statut`. Différenciez correctement les niveaux de log classiques (`DEBUG`, `INFO`, etc.).
- **Gestion des Secrets**: L'écriture en dur ou la journalisation de clés privées et secrets API est strictement interdite. Utilisez exclusivement le masquage et les variables d'environnement.

## 3. Concurrence et Thread-Safety
- **États Partagés**: L'accès concurrent aux structures critiques (carnets d'ordres, portefeuilles, allocations) crée des risques de fuite financière. Utilisez des verrous explicites (`Lock`, `asyncio.Lock`) lors des mutations d'états partagés.
- **Prévention des Deadlocks**: En environnement multi-threadé/asynchrone, imposez un ordre d'acquisition strict si plusieurs verrous sont nécessaires simultanément, et définissez toujours des timeouts d'acquisition (`timeout` ou `wait_for`).
- **Réconciliation d'État**: N'assumez jamais que l'état local du moteur est parfaitement synchronisé avec le broker de manière asynchrone. Implémentez des réconciliations périodiques avec la source de vérité externe.
- **Asynchronisme**: Utilisez `asyncio` pour la gestion des I/O réseau; les appels bloquants sont interdits dans la boucle d'exécution principale.

## 4. Concurrence, Multiprocessing et Mémoire Partagée (Pandas/NumPy/Optuna)
L'optimisation bayésienne (via Optuna) manipule des volumes massifs de données historiques sur plusieurs processus. Une mauvaise gestion entraîne rapidement des pics de RAM (OOM) et des goulots d'étranglement de sérialisation.
- **Queue Pipelining et ProcessPoolExecutor**: L'utilisation du stockage disque pour Optuna (`JournalFileStorage`) est **strictement interdite** en raison de la lenteur d'I/O. L'architecture doit utiliser le **Queue Pipelining** en RAM via `ProcessPoolExecutor` pour garantir un taux d'utilisation CPU maximal.
- **Early Abandoning & Bypass CPU (Short-circuit)**: Les stratégies complexes (ex: algorithmes de classification, HMM) ont l'obligation d'implémenter un mécanisme de court-circuitage (bypass) du pré-scan VectorBT pour éviter les bottlenecks CPU.
- **Vectorisation**: L'itération native (`iterrows`, boucles `for`) est interdite sur les DataFrames de backtest. Privilégiez les opérations vectorisées.
- **Shared Memory Obligatoire**: Ne transmettez jamais de larges DataFrames ou tableaux Numpy natifs entre les processus (serialization Pickle). Utilisez impérativement `shm_allocators.py` et `SharedIndicatorVolume` (POSIX Shared Memory) pour précalculer et partager les grilles d'indicateurs. Seules les métadonnées de la mémoire partagée (nom, shape, dtype) doivent être transmises aux workers.
  ```python
  # ❌ MAUVAIS : Sérialisation d'un gros DataFrame/Array vers les workers
  def worker_objective(trial, data_df):
      # La copie du DataFrame dans chaque worker fait exploser la RAM
      pass

  # ✅ BON : Allocation en mémoire partagée via shm_allocators.py
  def worker_objective(trial, shm_metadata):
      # Le worker lit le pointeur mémoire partagé sans duplication
      shm_grid = np.ndarray(shm_metadata['shape'], dtype=shm_metadata['dtype'], buffer=shm.buf)
  ```
- **Gestion Mémoire**: Libérez explicitement les gros objets en mémoire entre les passes d'optimisation. Veillez à la destruction des verrous et blocs mémoires (`reset_shared_memory_for_strategy`) en fin de tâche.
- **Robustesse des Données**: Traitez de manière proactive les `NaN` et valeurs infinies (`inf`). Corrigez systématiquement les `SettingWithCopyWarning` en utilisant `.copy()` ou `.loc`.

## 5. Architecture, Structure et Frameworks
- **Dualité de Traitement**: Maintenez une séparation stricte des paradigmes. Le backtest et l'optimisation doivent être **massivement vectorisés** (Pandas, Numpy, Vectorbt). L'exécution live et le routage (`broker.py`) doivent être **Event-Driven** (asynchrone tick-par-tick ou bougie-par-bougie).
- **Séparation des Préoccupations (SoC)**: Maintenez une séparation claire entre la logique de trading/calcul (stratégies, indicateurs), la plomberie (connexions API, BDD) et l'I/O.
- **Architectures Hybrides**: Les stratégies particulièrement lourdes en calcul doivent s'affranchir de la vectorisation totale du pré-scan (bypass/short-circuit) si cela crée un goulot d'étranglement CPU.
- **Optimisation & Validation (WFA)**: L'optimisation hyperparamétrique repose sur **Optuna**. Toute stratégie optimisée doit obligatoirement réussir une phase de **Walk-Forward Analysis (WFA)** pour attester de son immunité au surapprentissage (overfitting) avant son intégration en production. L'évaluation de la robustesse s'appuie désormais sur les métriques clés : **NVO** (Net Value Optimization), **NVS** (Net Value Stability), et **AMS.MC** (Average Monthly Sharpe Monte Carlo).
- **Interfaces & Reporting**: Tout endpoint API ou interface de reporting web (`web.py`) doit être développé avec **FastAPI** et **Uvicorn**. Le rendu visuel privilégie **Plotly** ou Lightweight Charts.
- **Configuration**: Ne codez jamais les paramètres en dur. Utilisez les fichiers de configuration dédiés (dossier `configs/`) ou les variables d'environnement.
- **Dépendances**: Limitez strictement l'introduction de nouvelles dépendances externes. Toute nouvelle librairie doit être justifiée et enregistrée dans `requirements-backtest-engine.txt`.

## 6. Résilience Réseau et API (Live Execution)
Les connexions aux exchanges sont instables par nature.
- **Timeouts**: Fixez des délais d'attente stricts pour chaque requête afin de prévenir le blocage silencieux des processus.
- **Rate Limiting**: Implémentez un mécanisme de backoff exponentiel pour anticiper et gérer les limitations de débit des courtiers.
- **Reconnexion WebSockets**: Tout client WebSocket doit intégrer nativement un mécanisme de Heartbeat (ping/pong) et une logique de reconnexion automatique/silencieuse avec ré-abonnement aux flux de marché en cas de coupure.
- **Ordres "Fantômes" (Idempotence)**: En cas de timeout réseau lors de l'envoi d'un ordre, le statut réel de l'ordre est inconnu. Le système doit automatiquement interroger l'API avec un `client_order_id` unique pour vérifier son exécution avant toute nouvelle tentative.

## 7. Tests, Validation et Mocking
- **Tests (pytest)**: Écrivez systématiquement des tests pour les nouvelles fonctionnalités (dossier `tests/`).
- **Mocking Obligatoire**: L'exécution de requêtes réseau réelles vers des brokers pendant la CI/CD ou les tests locaux est formellement interdite. Utilisez des mocks (`pytest-mock`) ou des cassettes (`VCR.py`).
- **Non-Régression Financière**: Toute modification du moteur de backtest ou des stratégies doit être validée par une exécution de test pour s'assurer qu'il n'y a pas de régression non intentionnelle sur les métriques (ex: `aggregated_metrics.json`). Les rapports d'optimisation et la détection des régressions utilisent systématiquement les métriques d'évaluation **NVO**, **NVS**, et **AMS.MC**.

## 8. Stockage Local (Parquet) et I/O de Données Historiques
- **Format et Compression**: Utilisez exclusivement le format `.parquet` avec compression `snappy` (pour la vitesse) ou `zstd` (pour le stockage froid) pour historiser les données de marché tick-level ou minute.
- **Partitionnement Stratégique**: Partitionnez les gros volumes de données par `symbole` puis par `année/mois` (ex: `symbol=AAPL/year=2023/month=10/`). Cela permet aux requêtes Pandas/Polars de ne charger que le sous-ensemble strict en mémoire.
- **Versionnage des Schémas**: Les types de données (`dtypes`) Parquet doivent être stricts. Toute modification d'indicateurs ou de format de colonnes doit s'accompagner d'un versionnage explicite du schéma (ex: `v2_features`) pour prévenir la corruption du backtest.
- **Efficacité**: Optimisez les lectures/écritures. Préférez les traitements vectorisés aux boucles natives.

## 9. Bonnes Pratiques Git
- **Commits Atomiques**: Rédigez des petits commits clairs et indépendants.
- **Messages Conventionnels**: Suivez la nomenclature standard (ex: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`) pour faciliter la lecture de l'historique.

## 10. Risk & Money Management (Garde-fous)
- **Pre-Trade Checks**: Aucun ordre de marché ne doit être envoyé au courtier sans avoir franchi une barrière de validation synchrone (Vérification de la marge disponible, de l'exposition maximale autorisée sur l'actif, et de l'absence d'ordres en conflit).
- **Circuit Breakers (Kill-switches)**: Implémentez des limites dures au niveau global de l'application (ex: Max Drawdown journalier atteint, pic anormal de requêtes d'ordres par seconde). En cas de franchissement, le système doit rejeter toute nouvelle demande et se placer en mode "Close-Only" (fermeture de positions uniquement).