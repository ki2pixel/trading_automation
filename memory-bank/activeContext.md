# Contexte Actif

*Note: Les entrées antérieures sont archivées dans [activeContext_archive_202608.md](file:///home/kidpixel/trading_automation_v2/memory-bank/archives/activeContext_archive_202608.md)*

## Focus Actuel
- [2026-08-27 13:15:00] - **Fix VectorBT / Plotly 7 Incompatibilité `scattermapbox` (`momentum_based_zigzag`)** :
  - **Cause racine** : Sur Render, `requirements-live.txt` ne verrouillait pas `plotly`. Pip a résolu `plotly==7.0.0` (nouvelle release majeure) qui a supprimé les traces Mapbox (`scattermapbox`) au profit de Maplibre (`scattermap`). À l'import de `vectorbt` (déclenché par `momentum_based_zigzag`), `settings.register_templates()` chargeait `templates/dark.json` contenant `"scattermapbox"`, levant `Invalid property specified for object of type plotly.graph_objs.layout.template.Data: 'scattermapbox'`.
  - **Pinning Dépendances** : Verrouillage explicite `plotly>=6.0,<7` dans `requirements-live.txt` (aligné sur `requirements-backtest.txt`).
  - **Patch de Compatibilité Runtime** : Création de `backtest_engine/compatibility.py` (importé dans `backtest_engine/__init__.py`) interceptant `pkgutil.get_data` pour migrer dynamiquement les clés obsolètes Mapbox (`scattermapbox` -> `scattermap`, etc.) de vectorbt afin de garantir l'absence de crash même si Plotly 7 est présent.
  - **Tests** : 28/28 tests verts (`tests/test_vectorbt_plotly_compat.py`, `tests/test_transactions_api.py`, `tests/test_paper_trading_engine.py`, etc.).
- [2026-08-26 20:00:00] - **Fix Bug 422 `cursor_id`, TypeError `txData` & Faux Positif Métriques (Frontend Chart)** :
  - **Alignement d'Arité** : Correction de l'appel `getTransactions(5000, 0, null, null, normalizedTicker)` dans `chart.js` (l'actif était erronément passé en 4ᵉ position au lieu de la 5ᵉ, alimentant `cursor_id` avec un ticker alphabétique).
  - **Défense en Profondeur** : Assainissement de `cursorId` via `Number.isInteger(Number(cursorId))` dans `api.js` pour empêcher toute 422 FastAPI en amont.
  - **Cache Étanche par Actif** : Remplacement de `cachedTransactions` (scalaire global) par `const cachedTransactionsByAsset = new Map()`, invalidé proprement lors de `invalidateChartCache()`.
  - **Résilience & Isolation d'Erreurs** : Encapsulation `try/catch` de `getTransactions` avec validation `Array.isArray(rawTx)` et fallback `[]` pour éviter `TypeError: txData is not iterable` et garantir le rendu graphique même si les transactions échouent.
  - **Élimination du Faux Positif UI** : Suivi de l'étape (`loadStage`) dans `loadChart` pour dissocier les erreurs de bougies des erreurs de métriques financières.
  - **Tests & Validation** : 28/28 tests verts (`tests/test_transactions_api.py`, `tests/test_paper_trading_engine.py`, `tests/test_paper_trading_auth.py`, `tests/test_api_caching.py`).
- [2026-08-03 16:40:00] - **Fix T212 SELL 400 "must have opened position at least 1.00" (NVO/NOVCd_EQ)** : Cause racine — l'API T212 interprète une quantité négative comme la quantité **totale** de position à vendre et exige une position restante ≥ 1.00. Le code vendait `real_qty - micro_qty` (micro ≈ 0.0001), laissant une position résiduelle < 1.00 → 400. Correctif : `max_sellable = real_qty - max(1.00, micro_qty)` dans `signal_executor.py`, cap SELL `initial_qty - 1.00` avec skip si < 1.00 dans `trading212/client.py`. Tests mis à jour (`-9.0001` / skip), + fix du test flaky `test_stale_redis_price_resolution` (copie `list(args)` du spy `executemany`). 27/27 tests verts. Prochaine étape : suivi production SELL NVO sur compte demo.
- [2026-07-28 09:59:00] - **Optimisation du Cycle d'Évaluation PaperTrader (88.6s → <60s)** : Optimisation complète en 6 phases de `evaluate_and_execute_strategies()` :
  - **Phase 1 — SQL Index & Timestamp Range Scan** : Index descendant `idx_live_candles_1m_ticker_ts_desc` sur `live_candles_1m(ticker, timestamp_minute DESC)` dans `db_setup.py`. Remplacement de `ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY timestamp_minute DESC)` par un filtrage direct indexé `WHERE timestamp_minute >= NOW() - interval` dans `signal_executor.py`.
  - **Phase 2 — Cache de Resampling (ticker, timeframe)** : Cache per-cycle `_resampling_cache` évitant la reconstruction de DataFrames et le ré-échantillonnage Pandas redondants pour les stratégies partageant actif + timeframe (ex: 3 configs sur 45m).
  - **Phase 3 — Batch Updates Statuts** : Remplacement des commits SQL individuels par un accumulateur `_status_updates` et un unique `executemany()` + `conn.commit()` en fin de cycle.
  - **Phase 4 — Évaluation Parallèle des Stratégies** : Exécution concurrente de `run_function()` via `ThreadPoolExecutor(max_workers=2)` (dimensionné pour le quota Render 0.5 CPU). Post-traitement et exécution des ordres conservés en séquentiel pour la sécurité des transactions.
  - **Phase 5 — Micro-optimisations** : Remplacement des appels redondants à `is_market_open()` par des recherches O(1) dans le dictionnaire pré-calculé `market_open_status`.
  - **Phase 6 — Instrumentation Monotonique** : Ajout du logger `[EvalCycle]` mesurant les phases `Prefetch`, `SQL candles`, `Redis prices`, `Preprocess`, `Strategy eval (parallel)`, `Trade exec+DB`.
  - **Fichiers** : `signal_executor.py`, `db_setup.py`, `test_paper_trading_engine.py`, `test_signal_executor.py`. **Tests** : 40/41 verts (1 échec pré-existant sur `test_stale_redis_price_resolution`).
- [2026-07-27 03:00:00] - **Garde-Fous d'Exécution SignalExecutor intégrés** : Max Entry Price dynamique, ATR Gate (P25 Wilder), MHP (3 bougies, signaux inverses uniquement). Module `execution_guards.py`, migration `opened_at` V3, SQL cap 10000, tests 20+11 verts, doc §3 mise à jour. Prochaine étape : validation comportement réel en Phase 2 (logs `paper_evaluations`).
- [2026-07-27 18:44:00] - **Fix Warmup Progress (SQL Goulot + Métriques + Frontend)** : Résolution du blocage structurel `rn <= 2000` qui étranglait le resampling 45m (49 bougies max au lieu de 50).
  - **Fix 1 — SQL Dynamique** : Extraction des helpers `_parse_timeframe_minutes()` et `_compute_min_bars_needed()` dans `SignalExecutor`. Calcul de `max_rn = max(2000, min_bars_needed * tf_minutes)` avant la requête batch pour adapter dynamiquement la fenêtre de lecture des bougies 1m.
  - **Fix 2 — Métriques Warmup** : Nouvelle colonne `warmup_progress JSONB` dans `paper_strategy_configs` avec migration `ADD COLUMN IF NOT EXISTS`. Persistance de `{current_bars, required_bars, progress_pct, timeframe_minutes}` dans les deux chemins WAITING_DATA. Nettoyage à NULL lors du passage à `active` ou `error`. Exposition via `GET /api/configs`.
  - **Fix 3 — Frontend** : Remplacement du badge statique "Waiting" par une barre de progression `████░░ 49/50 (98.0%)` avec fallback sur l'ancien badge. CSS `.warmup-progress`, `.warmup-bar`, `.warmup-fill`, `.warmup-text`.
  - **Fichiers** : `signal_executor.py`, `db_setup.py`, `api.py`, `configs.js`, `style.css`. Tests : 10/11 + 13/14 passent (2 échecs pré-existants, zéro régression).

## Prochaines Étapes
- Monitoring et observation de l'exécution live / Paper Trading.
- Aucun bloquant.

## Bloquants / Problèmes Actuels
- Aucun bloquant.

## Résolutions Récentes
- [2026-07-12 09:37:00] - Clôture des remédiations de l'audit Paper Trading (Phase 2 à Phase 4) :
  1. Validation de l'idempotence et des pre-trade controls de la Phase 2 (34/34 tests verts).
  2. Optimisation asynchrone non-bloquante FIFO/drawdown de l'API /performance/metrics avec cache-through Redis (Phase 3).
  3. Implémentation du reset de suspension /api/control/resume et compatibilité USDC crypto (Phase 3).
  4. Optimisations d'infrastructure (Phase 4) : insertions groupées SQL, cache de BrokerSimulator, DRY de source, résolutions d'imports circulaires et nettoyage debug.
  5. Rerun et correction des 61 tests unitaires et d'intégration du moteur Paper Trading et de sécurité du Job Store (`test_paper_trading_engine.py` et `test_job_store_security.py`) au vert à 100%.

## Historique Archivé
- [activeContext_archive_202608.md](file:///home/kidpixel/trading_automation_v2/memory-bank/archives/activeContext_archive_202608.md)
- [activeContext_history.md](file:///home/kidpixel/trading_automation_v2/memory-bank/archives/activeContext_history.md)
