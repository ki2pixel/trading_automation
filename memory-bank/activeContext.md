# Contexte Actif

## Focus Actuel
- Passage en production des 4 phases de remédiation du backend Paper Trading (audit 2026-07-17).

## Prochaines Étapes
- Déploiement incrémental des phases sur staging Render, puis production.
- Exécution du plan de vérification manuel (smoke tests 30min/1h par phase).

## Bloquants / Problems Actuels
- Aucun bloquant.

## Résolutions Récentes
- [2026-07-17] - Exécution des 4 phases de remédiation du backend Paper Trading (39 anomalies, audit 2026-07-17) :
  **Phase 1 (Critiques)** : Kill Switch zombie (C1 — return au lieu de break), double entrée intra-cycle SignalExecutor (P1 — RETURNING id + injection active_positions), idempotence spot_router (J1 — TTL reconciliation attempts, J2 — SUBMITTED après API call), race condition accumulator (H1 — CTE atomique), rate limiting FastAPI (Q6 — slowapi), détection production (Q3 — _is_production() centralisé), N+1 Redis (P2 — batch mget).
  **Phase 2 (Connexions)** : Timeouts Redis async (A2 — socket_timeout/keepalive/health_check), timeout pool DB (A4 — Semaphore + DB_POOL_ACQUIRE_TIMEOUT), alerte cancel failures Kill Switch (C2 — liste + CRITICAL log), lock_timeout panic_close_all (Q2 — SET LOCAL 5s).
  **Phase 3 (Concurrence)** : TTL margin_simulator (I1 — 300s auto-unlock), lock T212 15s→5s + existence check (K1), fcntl cache resolver (L1 — LOCK_SH/LOCK_EX + atomic rename), cohérence multi-sources ingestors (G1/N1 — PG-first, Redis pipeline, local best-effort), seuils PTC depuis env (B2 — PTC_MAX_TRADE_PCT_NAV etc.).
  **Phase 4 (Robustesse)** : Anti-dérive scheduler (O2 — time.monotonic + remaining sleep), lazy warmup brokers (O3 — _warmup_clients()), compteur skipped cycles (O1 — alerte après 3 skips), audit DB conversions bloquées (J4 — INSERT conversion_audit_log BLOCKED), documentation threading.Lock async Redis (A3), vérification A1 (false positive).
- **Tests** : 575 passed, 1 skipped, 0 regressions sur l'ensemble des phases.
- **Fichiers modifiés** : 14 source + 3 test + 1 dependency + 1 .env.template.
- [2026-07-16 19:04:00] - Unification et rédaction du Rapport d'Audit Global du Frontend Paper Trading (`docs/audit/audit_paper_trading_frontend_global_2026-07-16.md`), consolidant les analyses, la cartographie du code réel, le catalogue complet de 32 anomalies qualifiées (SEC, FIN, PERF, ACC, DT), les protocoles de validation et la feuille de route priorisée (P1, P2, P3).
- [2026-07-15 18:44:30] - Stabilisation du Kill Switch distribué du Paper Trader : état Redis JSON canonique et namespacé par environnement, compatibilité fail-closed avec `trading:suspended`, commandes Pub/Sub `KILL`/`SUSPEND`/`RESUME`, contrôle distribué dans `SignalExecutor`, endpoints de statut et de reprise sécurisée, et interface dashboard de reprise avec confirmation de réconciliation. Validation : 10 tests ciblés passés, compilation Python, vérification syntaxique JavaScript, diagnostics IDE et `git diff --check` sans erreur. Aucune tâche active.
- [2026-07-15 18:05:00] - Clôture définitive de la Phase 3, versioning et audit non destructif des migrations PostgreSQL (VV-07, VV-08, VV-10, VV-13, VV-14) :
  1. Correction VV-07 (Isolation Timeframe) : Retrait de la réintroduction de la clé unique historique `UNIQUE (asset, strategy_name)` sur `paper_positions` pour garantir l'isolation par timeframe.
  2. Correction VV-08 (Init Database Vierge) : Déplacement du backfill de `timeframe` après la création et le seeding de la table `paper_strategy_configs`.
  3. Correction VV-10 (One-Shot & Reboot-Resistant Backfill) : Le backfill n'est exécuté que si la colonne `timeframe` vient d'être créée (one-shot), préservant les positions légitimes `1m` créées post-migration lors des redémarrages.
  4. Correction VV-13 & VV-14 (Audit non destructif et Table de Revue) : Introduction d'une table `schema_version` (Version 2) et d'une table `paper_position_timeframe_reviews` pour auditer sans modifier les positions multi-timeframes suspectes. Celles-ci conservent leur timeframe d'origine mais déclenchent une revue `PENDING` listant les timeframes candidats.
  5. Sécurité multi-schémas : Ajout de `table_schema = current_schema()` aux contrôles `information_schema` pour fiabiliser les installations dans les schémas non publics (tests).
  6. Tests d'intégration : Enrichissement de `tests/test_db_setup.py` pour valider l'initialisation vierge, le backfill, la résistance au redémarrage, la non-mutation des positions et la création d'entrées de revue dans la table d'audit.
  7. Suite de tests verte à 100% (606 succès, 1 ignoré).
- [2026-07-13 10:01:00] - Résolution de la régression OOM en production (Render OOM > 512MB) :
  1. Optimisation et mise en cache Redis d'actifs avec 0 transaction dans `/api/performance/metrics`.
  2. Résolution du Case Mismatch de suppression de cache dans `signal_executor.py`.
  3. Réduction de la limite de bougies chargées en SQL par lot (de 10 000 à 5 000).
  4. Ajout d'un cache temporaire de 20s pour l'endpoint `/api/candles`.
  5. Ajout de tests unitaires et validation complète sans régression.
- [2026-07-12 09:37:00] - Clôture des remédiations de l'audit Paper Trading (Phase 2 à Phase 4) :
  1. Validation de l'idempotence et des pre-trade controls de la Phase 2 (34/34 tests verts).
  2. Optimisation asynchrone non-bloquante FIFO/drawdown de l'API /performance/metrics avec cache-through Redis (Phase 3).
  3. Implémentation du reset de suspension /api/control/resume et compatibilité USDC crypto (Phase 3).
  4. Optimisations d'infrastructure (Phase 4) : insertions groupées SQL, cache de BrokerSimulator, DRY de source, résolutions d'imports circulaires et nettoyage debug.
  5. Rerun et correction des 61 tests unitaires et d'intégration du moteur Paper Trading et de sécurité du Job Store (`test_paper_trading_engine.py` et `test_job_store_security.py`) au vert à 100%.
- [2026-07-12 09:14:00] - Correction des tests de l'agrégateur de bougies et de la résolution de prix unitaire :
  1. Correction du filtrage de query mock dans mock_fetchall pour identifier "live_candles_1m" et récupérer les bougies avec la nouvelle structure.
  2. Restauration de mock_fetchone pour la requête de prix en direct unitaire exécutée dans evaluate_and_execute_strategies.
  3. Rerun complet de la suite de tests de remédiation (76/76 tests verts, 100% passés).
- [2026-07-12 01:40:00] - Alignement et complétion de la Phase 3 (Validation & Tests) du plan de remédiation :
  1. Alignement des mocks de base de données (configs, positions, candles) dans tests/test_signal_executor.py et tests/test_paper_trading_engine.py pour refléter les requêtes par lots.
  2. Correction de la structure des tuples de retour des requêtes de prix en direct dans les tests pour inclure updated_at et éviter les IndexErrors.
  3. Isolation de BybitConfig et Trading212Config vis-à-vis du fichier .env local via mocking dans Bybit et Trading 212 tests.
  4. Installation et exécution complète du framework Playwright pour les tests d'intégration frontend (3/3 tests verts).
  5. Réussite de 100% de la suite de tests (77/77 tests verts sur le périmètre de remédiation).
- [2026-07-11 12:00:00] - Remédiation de l'audit frontend (FT-01 à FT-10) et couverture de test Playwright complétée :
  1. Intégrité financière (FT-01 Bybit Spot USDT, FT-02 alignement tables).
  2. Sécurisation anti-XSS via DOM node building (FT-05) et sérialisation du polling avec verrou (FT-06).
  3. Gestion temporelle (FT-03 invalidation cache graphique, FT-04 rafraîchissement config).
  4. Accessibilité (FT-09 focus-trapping modales / touche Escape, FT-07 sidebar responsive).
  5. Validation automatique réussie des tests d'intégration Playwright (3/3 tests verts).
- [2026-07-11 00:40:00] - Remédiation complète de l'audit backend (C-01 à C-05, H-01 à H-05) :
  1. Implémentation de la persistance de statut PENDING pré-POST, récupération d'état en cas de crash, et arrêt de vidage d'accumulateur en dry-run.
  2. Intégration de verrous FOR UPDATE SQL pour le BUY/SELL et panic close, et vérification stricte de suppression.
  3. Validation SHA256 obligatoire des clés API en production.
  4. Stockage JSON des prix Redis (180s TTL) et contrôle de fraîcheur de 3 minutes (Redis + SQL).
  5. Capping max_capital_bucket, vérification available_balance dans le margin simulator, retrait des defaults de prix PTC, suppression N+1 des positions, TIMESTAMPTZ, rate limit login et masquage traceback.
  6. Réalisation de tests unitaires et d'intégration étendus (37/37 tests au vert).
- [2026-07-09 19:11:00] - Harmonisation de la documentation du Paper Trading et Ingesteur Live :
  1. Mise à jour complète du README unifié avec les concepts de sécurité API (CSRF Content-Type, rate limiter Redis, CSP hors-ligne) et de protection/auto-cicatrisation des micro-positions.
  2. Intégration dans le guide de déploiement Render des variables T212_INGESTOR_ENV et T212_PAPER_ROUTING_ENABLED pour découpler les environnements.
- [2026-07-09 17:38:00] - Protection et auto-cicatrisation des micro-positions Trading 212 :
  1. Implémentation de la vente partielle préventive (Solution A) dans `SignalExecutor` pour protéger la micro-position de tracking lors de l'envoi d'ordres de vente réels.
  2. Implémentation du bootstrap d'auto-cicatrisation instantané (Solution B) post-EXIT dans le cycle de vie du robot de paper trading.
  3. Ajout et réussite d'un test d'intégration complet (40/40 tests verts).
- [2026-07-09 11:58:00] - Réconciliation et nettoyage de Trading212 Demo :
  1. Résolution du bug de précision d'arrondi dans le bootstrapper Trading212 (arrondi par excès de la valeur absolue) permettant de placer avec succès les micro-positions de Novo Nordisk (NVO / NOVCd_EQ) et Amadeus IT (AMS.MC / AMSe_EQ).
  2. Nettoyage de la watchlist de [test_multi_tickers.py](file:///home/kidpixel/trading_automation_v2/ressources/trading212/trading212-api-extended-main/test_multi_tickers.py) pour retirer les tickers extra non configurés (Logitech, Zealand Pharma, Siemens Healthineers) afin d'éviter toute future divergence.
- [2026-07-09 09:00:00] - Découplage de la configuration Trading 212 : Ajout de la variable d'environnement T212_INGESTOR_ENV pour forcer l'ingesteur de prix et le bootstrapper en mode démo (demo) tout en permettant au moteur de trading d'utiliser le compte réel (live). Passage réussi des tests unitaires (29/29).
- [2026-07-07 13:33:00] - Résolution de l'anomalie de chargement des ressources frontend (Option A locale et Offline-first) : téléchargement et copie locale de la version correcte stable v4.1.3 de Lightweight Charts (évitant le crash TypeError sur `addCandlestickSeries` lié à v5.x) dans un dossier vendor dédié, suppression des inclusions Google Fonts et remplacement par un jeu de polices système de haute qualité dans index.html et login.html (dont l'inline script a été extrait dans /js/login.js pour respecter la CSP) et style.css. Ajout d'un favicon.ico local et des balises associées pour éliminer le 404 GET.
- [2026-07-07 01:29:00] - Correction du suivi du solde de trésorerie Trading 212 en Paper Trading : extraction des liquidités disponibles réelles (`availableToTrade` dans la structure `cash`) de l'API get_account_summary() au lieu de la valeur nette globale du compte (`totalValue`), évitant l'écrasement erroné de la trésorerie locale et résolvant le double comptage du NAV.
- [2026-07-06 11:58:00] - Correction des anomalies d'exécution et de validation du client Trading 212 en Paper Trading : résolution des rejets HTTP 400 de précision de quantité en interceptant l'erreur pour arrondir dynamiquement à la précision autorisée par le courtier ; résolution de l'erreur SQL sur `paper_positions` et de l'accès imbriqué au ticker T212 ; validation par bridage automatique (capping) sur les ordres de vente.
- [2026-07-06 10:20:00] - Audit et alignement de l'intégralité des fiches de compétences (.agents/skills/) : mise à jour des 7 fiches de compétences critiques (execution-order-routing, trading212-api, paper-trading, risk-money-management, market-data-ingestion, local-parquet-storage, backtesting-engine) pour correspondre à l'état réel de la plateforme (idempotence UUID v4 36-char, devise unique T212, sécurité SHA256, keepalive Redis, allocations mémoire POSIX).
- [2026-07-06 10:10:00] - Alignement et mise à jour des standards de développement (.agents/rules/codingstandards.md) : intégration des contraintes d'idempotence (UUID v4 36 caractères, interrogation post-timeout), robustesse Redis Pub/Sub (TCP keepalive, health check), logging discret des déconnexions d'inactivité, et respect de la devise unique Trading 212.
- [2026-07-06 10:01:00] - Correction du mapping du ticker Novartis (NVS) pour Trading 212 : passage du ticker CHF (NOVNs_EQ) au ticker EUR (NOTd1_EQ sur Xetra) dans map_tickers.py, t212_assets_mapping.json et t212_assets_mapping.csv pour respecter la contrainte de devise unique du compte.
- [2026-07-06 09:30:00] - Résolution de l'erreur d'importation de VectorBT (ModuleNotFoundError: No module named 'vectorbt') dans l'environnement Paper Trading live. Ajout de `vectorbt>=1.0,<2` à `requirements-live.txt` pour s'assurer que toutes les stratégies (zigzag, hmm, trend_type) peuvent être instanciées en production.
- [2026-07-05 12:30:00] - Stabilisation du KillSwitchListener par l'ajout du health check et du keepalive TCP sur la connexion Redis Pub/Sub, et masquage (niveau INFO) des stacktraces lors des déconnexions d'inactivité prévisibles (idle timeout).
- [2026-07-05 02:56:00] - Résolution de l'erreur d'importation Numba (No module named 'numba') lors de l'exécution de la stratégie cybernetic_hilbert pour les paires crypto (ltcusdc et dotusdc) dans le Paper Trader en direct. Ajout de numba>=0.61.2,<0.62 dans requirements-base.txt pour garantir la compatibilité avec numpy>=2.2, validation de l'import et de la suite de tests unitaires (216/216 passés).
- [2026-07-04 20:35:00] - Sécurisation des appels d'API signés Bybit dans le Paper Trader (s'exécutent uniquement si des clés de configuration Bybit sont explicitement présentes, évitant ainsi les erreurs 401 en mode public-only).
- [2026-07-04 20:17:00] - Phase 3 (Priorité Moyenne/Basse) de durcissement de la sécurité complétée : Intégration de Tenacity retries avec exponential backoff et jitter sur Bybit et Trading 212 (avec régénération dynamique des signatures Bybit à chaque tentative), Validation stricte du Content-Type application/json dans CSRFMiddleware, Support mTLS PostgreSQL (asyncpg/psycopg2) et Redis, Intégration du logger JSON structuré SIEM dans 'trading_audit'. Passage réussi des tests unitaires de la Phase 3 (5/5 tests verts).
- [2026-07-04 20:12:00] - Phase 2 (Priorité Haute) du plan de remédiation de sécurité complétée : Prise en charge des Redis ACLs (REDIS_USER, REDIS_PASSWORD) dans `connection.py`, Implémentation du Kill Switch asynchrone indépendant (canal Redis `URGENCY`) avec annulation globale Bybit et Trading 212, Conception et intégration des Pre-Trade Controls (PTC volumétrique, notionnel et price collars dans `controls.py`), et Rate limiting FastAPI anti-DoS (Token Bucket via Redis). La configuration est désormais gérée de manière exclusive et standard via les variables d'environnement (Secrets Manager Client Infisical retiré). Passage réussi des tests unitaires de la Phase 2 (3/3 tests verts).
- [2026-07-04 20:06:00] - Phase 1 (Priorité Critique) du plan de remédiation de sécurité complétée : Idempotence Bybit (UUID 36 char), Verrou Redis SETNX et réconciliation avant rejeu sur Trading 212, Chiffrement SQLCipher (AES-256) et signatures cryptographiques HMAC-SHA256 contre l'altération des jobs SQLite, Failsafe d'environnement (Fail-Fast) au démarrage. Passage réussi des tests unitaires de sécurité (4/4) et correction de l'exception handler FastAPI (567/567 tests verts).
- [2026-07-04 09:30:00] - Audit, synchronisation et mise à jour des fiches de compétences (.agents/skills/) : mise à jour d'execution-order-routing et market-data-ingestion, création de la fiche paper-trading pour verrouiller l'architecture double pile SQL et la robustesse réseau, et passage réussi des tests (567/567).
- [2026-07-04 09:21:00] - Optimisation de la taille de codingstandards.md (condensé à ~7 000 caractères, en dessous de la limite de 12 000 caractères de l'IDE, avec note de garde).
