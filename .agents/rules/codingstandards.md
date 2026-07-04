# Standards de Code et Règles de Développement (Trading Automation)

## 1. Philosophie Générale
- **Lisibilité**: Code clair et explicite privilégié.
- **Fiabilité absolue**: Application financière. Gestion rigoureuse des erreurs requise.
- **Testabilité**: Conception modulaire facilitant les tests unitaires et d'intégration.

## 2. Standards Python (Backtest Engine & Scripts)
- **Typage Statique**: Annotations de type Python (`typing`) obligatoires partout.
- **Précision Financière (CRITIQUE)**: 
  - **Live & Paper Trading**: Utilisation exclusive de `decimal.Decimal` pour la logique financière, les calculs de PnL, frais et soldes. Commission Bybit Spot fixée à 0.1000%, Trading 212 à 0.0000%.
  - **Backtest Vectorisé (Pandas/Numpy)**: Utilisation de `float` (ex: `np.float64`) obligatoire pour la performance de calcul.
  ```python
  # ✅ Live/Paper (Decimal)
  pnl = Decimal(str(exit_p)) - Decimal(str(entry_p))
  # ✅ Vectorisé (Float)
  df['pnl'] = (df['close'] - df['open']) * df['qty']
  ```
- **PEP 8 & Docstrings**: Respect strict du style PEP 8. Documentez l'objectif, les arguments et retours des fonctions complexes.
- **Audit & Logging**: Logs structurés (format JSON) requis pour le routage d'ordres (`timestamp_utc`, `order_id`, `symbole`, `quantité`, `prix`, `statut`).
- **Secrets & Conf**: Secrets masqués via variables d'environnement. Mode public-only pour l'ingestion Bybit sur Render (sans clé).
- **Timeouts Réseau Centralisés**: Timeout explicite obligatoire sur chaque appel HTTP (Bybit, Trading 212, warm-ups). Constante globale `NETWORK_TIMEOUT_DEFAULT = 10` dans `utils.py`. Maximum standard de 10s (jusqu'à 30s pour téléchargements lourds).

## 3. Gestion des Erreurs et Robustesse
- **Exceptions spécifiques**: Interdiction de capturer `Exception` de manière générique et silencieuse (`except Exception: pass`). Interceptez des exceptions typées.
- **Middleware exception**: Captures globales `except Exception as e` tolérées uniquement au niveau du middleware FastAPI ou de l'orchestrateur global.
- **Logging de tracebacks**: Utilisez obligatoirement `logger.exception()` pour logger les erreurs système et de transport critiques avec leur traceback complet.
- **Exceptions d'Affaires**: Levez des exceptions métier dédiées (ex: `SignalExecutionError`, `PortfolioUpdateError`).
- **Masquage en Production**: API en production masquant les détails internes. Utilisation de `safe_error_response(exc, request)` retournant un message standard et un UUID de corrélation unique. Traces verbeuses affichées uniquement si `DEBUG=true` en dev.

## 4. Base de Données et Persistance
- **Séparation Sync/Async**:
  - **FastAPI (API)**: Utilisation exclusive d'un pool asynchrone `asyncpg` (`asyncpg.create_pool()`). Appels bloquants interdits.
  - **Workers Sync & Backtests**: Utilisation exclusive de `psycopg2` (synchrone/multithread).
- **Anti-N+1**: Interrogation SQL en boucle interdite. Utilisez des requêtes groupées (`ticker IN ($1, $2, ...)`) et des transactions en lot (`executemany` ou requêtes groupées) pour la persistance (ex: mise à jour de la NAV).
- **Bufferisation I/O**: Écritures fréquentes (ex: Optuna trials) tamponnées en mémoire et flushées par lots (ex: N=50). Flush final garanti via `atexit` ou `finally`.

## 5. Concurrence et Thread-Safety
- **États Partagés**: Mutation d'états concurrents (allocations, portefeuilles) protégée par verrous explicites (`Lock`, `asyncio.Lock`).
- **Deadlocks**: Ordre d'acquisition strict et timeouts requis (`timeout` ou `wait_for`).
- **Réconciliation**: Synchronisation et réconciliation périodique obligatoire avec l'état réel du broker.
- **Asynchronisme**: Appels I/O réseau via `asyncio`. Bloquer la boucle principale est interdit.

## 6. Concurrence, Multiprocessing et Mémoire Partagée (Pandas/NumPy/Optuna)
- **Queue Pipelining**: Stockage disque (`JournalFileStorage`) interdit pour Optuna en raison de la RAM/IO. Utilisez `ProcessPoolExecutor` avec Queue Pipelining en RAM.
- **Bypass CPU**: Implémentez un bypass du pré-scan VectorBT pour les calculs lourds (ex: HMM).
- **Vectorisation**: Boucles natives (`iterrows`, `for`) interdites sur les DataFrames de backtest.
- **Shared Memory**: Partage de grilles NumPy via `shm_allocators.py` et `SharedIndicatorVolume` (POSIX Shared Memory, Zero-Copy). Passage exclusif de métadonnées (nom, shape, dtype) aux workers.
  ```python
  # ✅ Utilisation de shared memory via buffer
  shm_grid = np.ndarray(metadata['shape'], dtype=metadata['dtype'], buffer=shm.buf)
  ```
- **Mémoire & Robustesse**: Libération explicite des gros objets et verrous. Gestion proactive des `NaN`/`inf` et correction systématique des `SettingWithCopyWarning`.

## 7. Architecture, Structure et Frameworks
- **Dualité de Traitement**: Séparation stricte. Backtest vectorisé (Pandas, Vectorbt) vs Exécution Live événementielle (Event-Driven / async).
- **Separation of Concerns (SoC)**: Logique de calcul isolée des connecteurs API, BDD et I/O.
- **Validation WFA**: Optimisation hyperparamétrique soumise à une validation Walk-Forward Analysis (WFA), PBO et DSR (CSCV) sur les actifs de référence **NVO**, **NVS**, et **AMS.MC** avant production.
- **Interfaces & Reporting**: API avec FastAPI/Uvicorn. Visualisations Plotly ou Lightweight Charts.
- **Dépendances segmentées**: 
  - `requirements-base.txt` : Socle commun (Pandas, Numpy, loguru).
  - `requirements-backtest.txt` : Simulation & Optimisation (Optuna, VectorBT, Numba).
  - `requirements-live.txt` : FastAPI, asyncpg, psycopg2, Redis.
- **Patron BaseStrategyRunner**: Toute stratégie doit dériver de la classe abstraite `BaseStrategyRunner` (`strategy_base.py`) gérant la normalisation, la reconstruction de l'état, les surcharges et la boucle principale.
- **Cycle de vie des exécuteurs**: Ingestion -> Calcul Signaux -> Validation Pre-Trade -> Routage d'ordres -> Persistance/Réconciliation.

## 8. Résilience Réseau et API (Live Execution)
- **Rate Limiting**: Backoff exponentiel obligatoire face aux limitations des brokers.
- **WebSocket**: Heartbeats (ping/pong) et reconnexion automatique/silencieuse requis.
- **Idempotence**: Vérification systématique d'exécution via un `client_order_id` unique après un timeout d'ordre, avant toute tentative de renvoi.

## 9. Tests, Validation et Mocking
- **Structure**: Tests unitaires via `pytest` au format **Given/When/Then**.
- **Mocking**: Requêtes réseau réelles interdites pendant la CI/CD. Utilisez des mocks ou cassettes (`VCR.py`).
- **Non-Régression**: Validation automatique des métriques financières et de robustesse (PBO/DSR) sur les actifs **NVO**, **NVS**, et **AMS.MC** (comparaison avec `aggregated_metrics.json`).

## 10. Stockage Local (Parquet) et I/O
- **Format**: Stockage au format `.parquet` compressé (`snappy` ou `zstd`). csv.gz toléré en repli.
- **Organisation**: Fichiers plats par symbole stockés dans des dossiers par timeframe (ex: `storage/processed/market_data_{tf}m/{symbol}.parquet`).
- **Schémas stricts**: Versionnage explicite du schéma de données lors des modifications d'indicateurs.

## 11. Risk & Money Management (Garde-fous)
- **Pre-Trade Checks**: Vérification synchrone obligatoire de la marge, de l'exposition max et des conflits d'ordres avant routage.
- **Circuit Breakers**: Arrêt global automatique ("Close-Only") en cas de Max Drawdown journalier atteint ou anomalie de requêtes/sec.

## 12. Bonnes Pratiques Git
- **Commits Atomiques**: Commits ciblés et indépendants.
- **Conventions**: Messages conformes aux standards (ex: `feat:`, `fix:`, `refactor:`, `test:`).

---
> *Note: Veuillez maintenir ce document sous la limite stricte des 12 000 caractères.*