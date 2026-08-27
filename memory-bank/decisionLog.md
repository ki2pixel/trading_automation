# Journal des Décisions

*Note: Les entrées antérieures sont archivées dans [decisionLog_archive_202608.md](file:///home/kidpixel/trading_automation_v2/memory-bank/archives/decisionLog_archive_202608.md)*

## [2026-08-27 13:15:00] - Résolution de l'Incompatibilité VectorBT / Plotly 7 (`scattermapbox`)
- **Décision** :
  1. **Pinning Dépendances Live** : Ajouter `plotly>=6.0,<7` dans `requirements-live.txt` pour aligner les dépendances de production sur `requirements-backtest.txt` et interdire à pip d'installer Plotly 7.0.0+ sur Render.
  2. **Patch de Compatibilité Automatique (`backtest_engine/compatibility.py`)** : Intercepter `pkgutil.get_data` au chargement de `backtest_engine` (`__init__.py`) pour remplacer au vol les traces Mapbox obsolètes (`scattermapbox`, `densitymapbox`, `choroplethmapbox`) par les équivalents Maplibre (`scattermap`, `densitymap`, `choroplethmap`) dans les templates vectorbt (`dark.json`, `light.json`).
- **Justification** : Plotly 7.0.0 a formellement supprimé `scattermapbox`. VectorBT 1.0.0 intégrant ces clés en dur dans ses fichiers JSON de thème, l'import de `vectorbt` (provoqué par `momentum_based_zigzag`) levait une exception `ValueError` immédiate qui plantait l'évaluation des stratégies sur le Paper Trader.
- **Alternatives rejetées** :
  - Modifier les fichiers internes de vectorbt dans le virtualenv : Non reproductible lors des builds Docker ou sur les environnements CI/CD.
  - Supprimer vectorbt de `momentum_based_zigzag` : N'aurait pas protégé les autres indicateurs qui l'utilisent (`msl_trend`, `pivot_retest`, `lorentzian_classification`, etc.).

## [2026-08-26 20:00:00] - Résolution du Bug 422 `cursor_id`, Erreur d'Itérabilité `TypeError: txData` et Faux Positifs Frontend
- **Décision** :
  1. **Alignement d'Arité & Contrat** : Passer `cursorId = null` et `asset = normalizedTicker` dans `chart.js` (`getTransactions(5000, 0, null, null, normalizedTicker)`). Maintien strict de la rétrocompatibilité pour `modules/logs.js`.
  2. **Défense en Profondeur** : Validation `Number.isInteger(Number(cursorId))` dans `api.js` pour éliminer tout risque d'injection textuelle accidentelle dans la query `/transactions` FastAPI.
  3. **Cache Associatif par Actif** : Remplacement de `cachedTransactions` par `const cachedTransactionsByAsset = new Map()`, indexé par ticker en minuscules, réinitialisé par `invalidateChartCache()`.
  4. **Tolérance aux Pannes & Parsing Défensif** : Encapsulation `try/catch` de `getTransactions` dans `loadChart` avec validation `Array.isArray()` et fallback `[]`. Les erreurs de transactions visuelles ne bloquent plus l'affichage des chandeliers ni des courbes de NAV.
  5. **Granularité des Messages d'Erreur** : Suivi d'état `loadStage` pour différencier les erreurs de bougies (`Failed to load candle data`) des erreurs financières (`Failed to load financial metrics`).
- **Justification** : Résolution définitive de la cascade d'erreurs (422 FastAPI -> TypeError frontend -> alerte trompeuse métriques) et isolation étanche de l'état du cache entre actifs.
- **Alternatives rejetées** :
  - Modifier l'ordre des paramètres dans `getTransactions` de `api.js` : Rejeté par respect du principe de non-régression de l'userspace (aurait cassé `modules/logs.js`).
  - Masquer l'erreur 422 côté backend FastAPI en acceptant `cursor_id: str` : Rejeté car cela corrompt le contrat de typage fort du backend et la cohérence de l'API.

## [2026-07-27 18:44:00] - Fix Warmup Progress : SQL Dynamique + Métriques JSONB + Frontend Progress Bar
- **Décision** : Implémentation en 3 fixes du goulot d'étranglement WAITING_DATA identifié sur `ZEAL.CO` (45m) :
  1. **SQL Dynamique** : Remplacer le hardcode `rn <= 2000` par un calcul `max(2000, min_bars_needed * tf_minutes)` avant le batch fetch. Extraction des helpers `_parse_timeframe_minutes()` (string → int) et `_compute_min_bars_needed()` (lookback indicator_params) en `@staticmethod` dans `SignalExecutor` pour éviter la duplication entre pré-SQL et per-config.
  2. **Métriques Warmup (JSONB)** : Nouvelle colonne `warmup_progress JSONB DEFAULT NULL` dans `paper_strategy_configs` plutôt qu'une table séparée (simplicité, pas de JOIN). Persistance dans les deux chemins WAITING_DATA (raw candles < 10 et aggregated < min_bars). Nettoyage à NULL sur transitions `active` et `error`. Exposition via `GET /api/configs` (pas de nouvel endpoint).
  3. **Frontend Progress Bar** : Barre CSS avec gradient linéaire (#f59e0b → #eab308) + fraction texte. Éléments DOM créés via `createElement` (pas d'innerHTML pour le contenu dynamique). Fallback badge `"Waiting"` quand `warmup_progress` est absent pour rétrocompatibilité avec les configs créées avant migration.
- **Justification** : Éliminer le blocage structurel où le plafond SQL de 2000 minutes ne permettait pas d'atteindre les 50 bougies 45m requises (besoin réel : 2250 minutes). Fournir une transparence complète à l'utilisateur sur l'avancement du warmup sans nécessiter de logs ou d'inspection BDD. Approche JSONB choisie pour la flexibilité du schéma futur (ajout possible de `estimated_activation_utc`, `remaining_market_minutes`, etc.).
- **Alternatives rejetées** : (a) Relever `rn <= 2000` à 5000 statique — trop rigide, ne s'adapte pas aux stratégies futures avec lookback > 100. (b) Table `paper_warmup_status` séparée — sur-ingénierie pour un champ transitoire. (c) Endpoint REST dédié `/api/warmup-progress` — la charge de polling supplémentaire n'est pas justifiée, les métriques sont incluses dans le flux existant `/api/configs`.

## [2026-07-27 01:40:00] - Audit et Alignement des Règles de Développement (`AGENTS.md` & `codingstandards.md`)
- **Décision** : Mise à jour et harmonisation des règles de développement globales dans `AGENTS.md` (section 2) et `.agents/rules/codingstandards.md` pour refléter l'état réel de la base de code après la remédiation backend Paper Trading (PT-01 à PT-26) :
  1. **Clés d'API & Sécurité** : Formalisation du mode fallback sans clés (warning et init réussie pour ingestion publique) vs levée de `ValueError` contrôlée lors des requêtes signées. Failsafe SHA256 des hashes des clés API au démarrage.
  2. **Isolation des Exceptions** : Règle d'isolation des erreurs broker `(requests.exceptions.RequestException, ValueError, KeyError, TypeError)` par connecteur dans les opérations multi-courtiers (calcul NAV). Interdiction de masquer les fautes de programmation (`TypeError` / desérialisation) sous des `except Exception` de transport.
  3. **Persistance & Async** : Séquençage strict imposant l'exécution du staging pipeline Redis (prix live) STRICTEMENT APRÈS le commit de la transaction PostgreSQL. Obligation d'envelopper les appels `psycopg2` bloquants dans `asyncio.to_thread()` au sein des coroutines asyncio.
  4. **Logique Financière & Métier** : Dépôt systématique des PnL net des SELL Bybit profitables dans `AccumulatorBuffer` (`deposit()`) au sein de la même transaction SQL.
  5. **Normalisation Canonique** : Imposition de la casse minuscule canonique (`ticker.lower()`) pour tous les symboles d'actifs inter-modules (warm-up, DB, Redis, exécuteur).
- **Justification** : Prévenir la dérive entre la documentation/spécification d'ingénierie et le code de production, et pérenniser les invariants de robustesse, sécurité et précision financière établis lors des audits.

## [2026-07-13 10:01:00] - Optimisation de la performance (Render OOM > 512MB) sur l'ouverture de marché
- **Décision** :
  1. Activer le cache Redis sur `/api/performance/metrics` même pour les actifs ayant 0 trade (qui causent sinon un calcul lourd et répété de 5000 bougies à chaque intervalle de polling).
  2. Corriger le bug de casse (case mismatch) sur la suppression de clé Redis de cache (`perf_metrics:{asset.lower()}`) dans `signal_executor.py` lors des ordres BUY/SELL.
  3. Réduire la limite de chargement des bougies 1m de 10 000 à 5 000 en SQL dans le moteur d'exécution (SignalExecutor) afin de soulager la RAM psycopg2/Pandas.
  4. Ajouter une mise en cache temporaire de 20 secondes sur l'endpoint `/api/candles` pour réduire les requêtes en base de données répétées.
- **Justification** : Le polling du dashboard toutes les 10 secondes couplé à l'absence de transactions fermées (trades == 0) forçait le recalcul constant de courbes à chaque requête de l'utilisateur, ce qui saturait la CPU et provoquait des fuites de mémoire/OOM (crashs répétés toutes les 4-5 minutes).

## [2026-07-04 00:38:00] - Phase 5 Hygiène & Dette Technique Backend validée (Dépendances, Docker, Nettoyage)
- **Décision** : Partitionnement des dépendances Python du projet en 3 fichiers (`requirements-base.txt`, `requirements-backtest.txt`, `requirements-live.txt`), suppression de `requirements-backtest-engine.txt`, et build Docker de production allégé en copiant et installant uniquement le live. Nettoyage de la dette technique via la suppression automatisée de 332 imports inutilisés, l'audit du nommage (snake_case), et l'enrichissement des annotations de types statiques sur `connection.py` et `signal_executor.py` (API publique déclarée via `__all__`).
- **Justification** : Réduire le poids de l'image Docker de production sur Render, clarifier la structure des dépendances par environnement pour les développeurs, accélérer les phases de build/CI, améliorer la maintenabilité du code par le typage statique strict et éliminer le code mort (imports inutilisés).

## [2026-07-04 00:15:00] - Phase 4 Robustesse Backend validée (Paper Trading & Optimizer)
- **Décision** : Sécurisation du backend de trading automation via 3 piliers :
  1. **Exceptions Ciblées** : Remplacement des captures d'exceptions génériques (`except Exception`) par des captures typées spécifiques aux couches (DB : `psycopg2.Error`/`asyncpg.PostgresError`, Réseau : `urllib.error`/`requests.exceptions.RequestException`, Validation : `ValueError`/`KeyError`). Utilisation systématique de `logger.exception` pour conserver les stack traces. Création d'exceptions custom `SignalExecutionError` et `PortfolioUpdateError` pour les échecs d'affaires.
  2. **Shielding en Production** : Implémentation du helper `safe_error_response` et configuration de gestionnaires d'exception globaux FastAPI. En production, les erreurs non gérées retournent un message générique masquant les détails techniques et fournissant un UUID de corrélation unique. La trace complète est logguée côté serveur associée à cet UUID. Les détails détaillés restent visibles en mode développement/DEBUG.
  3. **Timeouts Explicites** : Centralisation de `NETWORK_TIMEOUT_DEFAULT = 10.0` dans `utils.py` et application stricte sur tous les appels réseau (Bybit, Trading 212, warm-up) pour prévenir les pannes et blocages silencieux.
- **Justification** : Éliminer la fuite d'informations système et de structure de base de données en production, structurer la gestion d'erreurs pour une meilleure maintenabilité, et interdire les timeouts infinis par défaut sur les requêtes réseau externes.

## [2026-07-03 22:50:00] - Phase 1 Sécurité Critique validée (Paper Trading Backend)
- **Décision** : Implémentation des 4 mesures de sécurité critiques de l'audit pour le backend Paper Trading FastAPI :
  1. **Séparation HMAC** : Utilisation d'une variable d'environnement `HMAC_SECRET` dédiée pour la signature de session (séparée du mot de passe utilisateur, auto-générée en dev/test, requise en prod).
  2. **Protection CSRF** : Implémentation du middleware `CSRFMiddleware` (Double Submit Cookie) vérifiant le header `X-CSRFToken` par rapport au cookie `csrftoken` non HttpOnly sur les requêtes mutantes. Intégration côté client via un intercepteur fetch dans `app.js`.
  3. **Validation Pydantic** : Modèle `IndicatorParamsModel` validant `indicator_params` via `model_validator` pour rejeter les injections (structures imbriquées de type listes/dict) tout en autorisant les clés dynamiques via `extra='allow'`.
  4. **En-têtes CORS/CSP** : Configuration des en-têtes de sécurité de production via `CORSMiddleware` (whitelist stricte, `X-CSRFToken` et `Content-Type` autorisés) et `SecurityHeadersMiddleware` (CSP, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Strict-Transport-Security`).
- **Justification** : Éliminer les risques critiques d'invalidation de mot de passe comme clé HMAC, d'attaques CSRF sur les endpoints mutants d'administration du Paper Trading, de contournement ou d'injections malveillantes via les paramètres de stratégies, et d'expositions inter-origines non sécurisées.

## [2026-07-02 23:15:00] - Conception de la Passerelle de Conversion Réelle Crypto-Fiat (Bybit Live)
- **Décision** : Analyse des vecteurs de conversion et des risques associés à la transition en environnement réel Bybit (UTA, MiCA) suite au rapport `Analyse-Conversion-API-Bybit-EUR.md` :
  1. **Choix du Routage** : Option A (API Spot `EURUSDT` avec `marketUnit="quoteCoin"`) retenue au lieu de l'Option B (Convert API OTC) pour les faibles montants, en raison de frais explicites inférieurs (0,10% - 0,20% Taker vs 0,15% - 0,40% spread OTC) et d'une exécution déterministe.
  2. **Buffer de Rétention** : Utilisation d'un patron d'accumulateur (Buffer de Rétention) avec un seuil de déclenchement à 15 USDT pour respecter le seuil minimal de commande Spot de Bybit (1-5 USDT) et éviter les rejets.
  3. **Contrôle de Marge UTA (Haircut Loss)** : Mise en place obligatoire d'un simulateur de marge pré-trade interrogeant `GET /v5/account/info` avant conversion, afin de s'assurer que le retrait de collatéral (l'EUR ayant un ratio de collatéral de 0%) ne pousse pas le taux de marge de maintien (MMR) au-dessus de 100% (seuil de liquidation).
  4. **Routage MiCA (Juridiction EEE)** : Migration recommandée des stratégies vers une devise de base USDC (stablecoin conforme MiCA avec ratio collatéral de 100% dans l'UTA) pour éliminer le besoin de "Double-Hop Routing" (USDT -> USDC -> EUR) et réduire les frais cumulés.
- **Justification** : Prévenir les rejets d'ordres par le moteur de matching de Bybit, prémunir le compte UTA contre les liquidations accidentelles induites par la perte de collatéral marge, et respecter le cadre réglementaire européen MiCA tout en minimisant les frais de transaction.

## [2026-07-02 22:15:00] - Enrichissement et Stabilisation du Dashboard Paper Trading
- **Décision** : Enrichissement de l'interface de monitoring Paper Trading avec de nouvelles fonctionnalités et correction de la résilience de l'ingesteur :
  1. Intégration de `Lightweight Charts` v4.1.3 avec une échelle double Y (NAV sur l'axe gauche, prix des bougies sur l'axe droit) pour superposer la courbe de stratégie vs Buy & Hold sans distorsion.
  2. Stream en temps réel des logs du moteur de Paper Trading via FastAPI SSE (Server-Sent Events) en redirigeant dynamiquement les sorties standard (prints) vers un logger Python circulaire.
  3. Ajout de contrôles interactifs : interrupteurs d'activation/désactivation de stratégie et bouton de panique (Close All) avec double confirmation modale.
  4. Déplacement de l'initialisation des ingesteurs de prix de `run_ingestor.py` directement dans le context manager `lifespan` de FastAPI pour s'assurer que les workers d'Uvicorn démarrent toujours les tâches d'ingestion asynchrones en arrière-plan.
- **Justification** : Offrir un monitoring temps réel robuste des métriques d'exécution et de performance (calculées en FIFO) et assurer la continuité du flux de données de marché en environnement de production (Render).

## [2026-07-02 20:21:00] - Alignement et Mise à jour des Standards de Code (Trading Automation)
- **Décision** : Mise à jour de `.agents/rules/codingstandards.md` pour refléter la réalité technique de la base de code :
  1. Ingesteur de prix Bybit en mode public-only sur Render (sans clés d'API requises).
  2. Simulation des frais de transaction Bybit Spot à 0.1000% (non-VIP) et Trading 212 à 0.0000% de frais dans le Paper Trading.
  3. Rôle de `shm_allocators.py` dans l'allocation POSIX SHM pour réduire la complexité d'Optuna.
  4. Correction de la confusion sur les métriques : NVO, NVS et AMS.MC sont des actifs/tickers de référence WFA, tandis que PBO et DSR sont les véritables métriques de robustesse.
  5. Organisation plate des données Parquet dans `storage/processed/market_data_{timeframe}m/{symbol}.parquet`.
- **Justification** : Aligner précisément la documentation d'architecture de référence avec le codebase pour éviter la dérive de documentation et guider correctement les futurs développements.

## [2026-07-02 15:00:00] - Architecture Dual-Portefeuille et Intégration Binance API
- **Décision** : Séparation stricte des portefeuilles et de la gestion de balance entre les actions (gérées via Trading212 en EUR) et les crypto-actifs (gérées via Binance en USDT) au sein du moteur de Paper Trading. Migration des tables SQL `trading212_prices` $\rightarrow$ `live_prices` et `trading212_candles_1m` $\rightarrow$ `live_candles_1m` pour unifier les données de marché. Intégration d'un routeur dynamique dans le moteur de paper trading basé sur le suffixe des actifs (ex: `*.usdt` redirigé vers l'écosystème Binance).
- **Justification** : Trading212 interdit le trading algorithmique sur crypto-actifs et n'offre pas de vente à d'API Spot ouverte pour les cryptos. Binance fournit une API Spot Testnet idéale et un écosystème 24/7 complet. La séparation évite d'avoir une surcharge arbitraire de Kelly weight pour les cryptos, préserve la logique financière spécifique à chaque écosystème, et permet une modélisation propre sans pollution mutuelle.

## Historique Archivé
- [decisionLog_archive_202608.md](file:///home/kidpixel/trading_automation_v2/memory-bank/archives/decisionLog_archive_202608.md)
- [decisionLog_history.md](file:///home/kidpixel/trading_automation_v2/memory-bank/archives/decisionLog_history.md)

