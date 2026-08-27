# Suivi de Progression

*Note: Les entrées antérieures sont archivées dans [progress_archive_202608.md](file:///home/kidpixel/trading_automation_v2/memory-bank/archives/progress_archive_202608.md)*

## Tâches Terminées

- [x] [2026-08-27 13:15:00] - **Fix VectorBT / Plotly 7 Incompatibilité `scattermapbox` (`momentum_based_zigzag`)** :
  - **`requirements-live.txt`** : Pinning `plotly>=6.0,<7` pour aligner les dépendances de production sur `requirements-backtest.txt` et empêcher pip d'installer Plotly 7.0+ sur Render.
  - **`backtest_engine/compatibility.py` & `__init__.py`** : Patch automatique runtime interceptant `pkgutil.get_data` pour transformer les traces obsolètes Mapbox (`scattermapbox` etc.) en Maplibre (`scattermap`) dans les thèmes vectorbt.
  - **`tests/test_vectorbt_plotly_compat.py`** : Tests unitaires de non-régression validant le chargement des templates vectorbt et l'exécution sans erreur de `momentum_based_zigzag`.
  - **Tests** : 28/28 tests verts.

- [x] [2026-08-26 20:00:00] - **Fix Bug 422 `cursor_id`, TypeError `txData` & Faux Positif Métriques (Frontend Chart)** :
  - **`chart.js`** : Réalignement des arguments `getTransactions(5000, 0, null, null, normalizedTicker)`. Migration de `cachedTransactions` vers `const cachedTransactionsByAsset = new Map()` étanche par ticker normalisé. Encapsulation `try/catch` de la récupération des transactions avec validation `Array.isArray()` et fallback `[]` prévenant `TypeError: txData is not iterable`. Suivi d'état `loadStage` pour éliminer le faux positif `Failed to load financial metrics`.
  - **`api.js`** : Validation stricte `Number.isInteger(Number(cursorId))` empêchant toute transmission d'une valeur non numérique comme `cursor_id` vers FastAPI. Normalisation `asset.toLowerCase()`.
  - **`tests/test_transactions_api.py`** : Création de la suite de tests unitaires et d'intégration validant le comportement nominal (200), les cas limites, les rejets de validation (422) et la non-régression de la pagination logs.
  - **Tests** : 28/28 tests verts (100% de succès sur `test_transactions_api.py`, `test_paper_trading_engine.py`, `test_paper_trading_auth.py`, `test_api_caching.py`). Syntax checks `node --check` validés.

- [x] [2026-08-03 16:40:00] - **Fix T212 SELL 400 "must have opened position at least 1.00" (NVO/NOVCd_EQ)** : Cause racine identifiée — l'API T212 interprète une quantité négative comme la quantité **totale** de position à vendre et exige une position restante ≥ 1.00. Le code vendait `real_qty - micro_qty` (micro ≈ 0.0001), laissant une position résiduelle < 1.00 → rejet 400.
  - **`signal_executor.py`** : `max_sellable = real_qty - max(1.00, micro_qty)` au lieu de `real_qty - micro_qty`.
  - **`trading212/client.py`** : Cap SELL `max_sellable = initial_qty - 1.00`, skip silencieux si `initial_qty < 1.00` (au lieu de vendre la position entière).
  - **Tests mis à jour** : `test_signal_executor.py` (`-9.0001` au lieu de `-10.0`), `test_robustness.py` (skip au lieu de `-0.1`).
  - **Fix du test flaky `test_stale_redis_price_resolution`** : le spy `executemany` copie maintenant `list(args)` au moment de la capture (le buffer `_eval_buffer` était vidé par `_flush_evaluations()` avant l'assertion).
  - **Tests** : 27/27 verts sur `test_robustness.py` + `test_signal_executor.py`. Fichiers modifiés : `signal_executor.py`, `trading212/client.py`, `tests/test_robustness.py`, `tests/test_signal_executor.py`.

- [x] [2026-07-28 09:59:00] - **Optimisation du Cycle d'Évaluation PaperTrader (88.6s → <60s)** : Optimisation complète en 6 phases de `evaluate_and_execute_strategies()` :
  - **Phase 1 — SQL Index & Timestamp Range Scan** : Index descendant `idx_live_candles_1m_ticker_ts_desc` sur `live_candles_1m(ticker, timestamp_minute DESC)` (`db_setup.py`). Requête SQL modifiée pour un filtre direct indexé `WHERE timestamp_minute >= NOW() - make_interval(mins => %s)`.
  - **Phase 2 — Cache de Resampling `(ticker, timeframe)`** : Cache per-cycle `_resampling_cache` évitant la régénération répétée des DataFrames Pandas et du resampling 45m/30m/60m pour les configurations partageant la même paire/timeframe.
  - **Phase 3 — Batch Updates Statuts** : Accumulation des transitions d'état dans `_status_updates` et flush en un seul `executemany()` + `conn.commit()`.
  - **Phase 4 — Évaluation Parallèle des Stratégies** : Exécution concurrente des calculs d'indicateurs via `ThreadPoolExecutor(max_workers=2)` (limite 0.5 CPU Render). Boucle d'exécution d'ordres séquentielle inchangée pour la sécurité financière.
  - **Phase 5 — Micro-optimisations** : Remplacement des ré-évaluations `is_market_open()` par le dictionnaire `market_open_status`.
  - **Phase 6 — Instrumentation Log** : Logger `[EvalCycle]` mesurant les durées par étape.
  - **Fichiers** : `signal_executor.py`, `db_setup.py`, `tests/test_paper_trading_engine.py`, `tests/test_signal_executor.py`. **Tests** : 40/41 verts (1 échec pré-existant `test_stale_redis_price_resolution`).

- [x] [2026-07-27 18:44:00] - **Fix Warmup Progress (SQL Goulot + Métriques + Frontend)** — 3 fixes pour le statut WAITING_DATA :
  - **Fix 1 — SQL Dynamique** : Extraction `_parse_timeframe_minutes(tf_str)` et `_compute_min_bars_needed(indicator_params)` comme `@staticmethod` dans `SignalExecutor`. Clause SQL `rn <= max(2000, min_bars * tf_minutes)` calculée avant le batch fetch → débloque `cybernetic_hilbert` ZEAL.CO 45m (49→50 bougies).
  - **Fix 2 — Métriques Warmup** : Colonne `warmup_progress JSONB DEFAULT NULL` ajoutée à `paper_strategy_configs`. Persistance `{current_bars, required_bars, progress_pct, timeframe_minutes}` dans les 2 chemins WAITING_DATA. Nettoyage à NULL sur transition `active`/`error`. Exposition dans `GET /api/configs`.
  - **Fix 3 — Frontend** : Badge "Waiting" remplacé par barre de progression `warmup-progress` (fill CSS gradient + fraction `49/50 (98.0%)`). Fallback badge si métriques absentes.
  - **Fichiers** : `signal_executor.py`, `db_setup.py`, `api.py`, `configs.js`, `style.css`. **Tests** : 10/11 `test_signal_executor.py`, 13/14 `test_paper_trading_engine.py` (2 échecs pré-existants, zéro régression).

- [x] [2026-07-27 12:00:00] - **Refactorisation de la boucle principale Paper Trader** : Élimination du dépassement de cycle 122.2s → cible < 60s.
  - **Phase 1 (Critique)** : A-01 parallélisation `ThreadPoolExecutor` T212+Bybit, A-02 accumulateur `_eval_buffer` + `executemany` batch.
  - **Phase 2 (Haute)** : A-03/A-04 cache `_strategy_result_cache` par `(asset, tf, bar_ts)`, A-08 cache intraday `compute_previous_day_close`.
  - **Phase 3 (Structurelle)** : Découplage `start_loop_async` en deux boucles `asyncio.gather` (NAV 30s + évaluation 60s), A-05 réutilisation `BrokerSimulator` + `exit_rules` pré-instanciés, A-06 fetch bougies 10K→2K.
  - **Phase 4 (Micro)** : A-07 pré-calcul `market_open_status` par asset.
  - **Tests** : 26/27 passent. 1 échec préexistant (`test_bybit_secured_profit_routing`).

- [x] [2026-07-27 03:00:00] - **Garde-Fous d'Exécution SignalExecutor (Feuille de Route §3)**
  - Module `execution_guards.py` créé (fonctions pures, typage Decimal/float selon charte §2.2).
  - **Max Entry Price dynamique** : cap = close_veille × (1+buffer), buffer +30 % défaut, repli statique BDD.
  - **ATR Gate** : ATR Wilder P25, lookback 100 bougies, fail-open < 20 bougies fermées.
  - **MHP** : 3 bougies min pour signaux inverses uniquement (SL/TP/trailing prioritaires). Migration `opened_at` V3 sur `paper_positions` avec backfill best-effort.
  - **SQL** : cap `rn <= 5000` → `rn <= 10000` (compatibilité ATR lookback 100+).
  - **API Pydantic** : 7 nouvelles clés typées dans `IndicatorParamsModel` (`extra='allow'`).
  - **Tests** : 20/20 `test_execution_guards.py`, 11/11 `test_signal_executor.py`. Régression : 630/636 (6 échecs pré-existants).

- [x] [2026-07-27 09:18:00] - Résolution des blocages "Postgres price is stale" et "Waiting Data" pour ZEAL.CO et NVO en 45m (`cybernetic_hilbert` et `momentum_based_zigzag`) :
  - **Script de backfill (`scripts/backfill_candles.py`)** : Ingestion de 3 000 bougies 1m historiques via l'API MarketFlow (`live_candles_1m`).
  - **Gestion de marché fermé & tolérance `signal_executor.py`** : Prise en compte du calendrier boursier (`configs/market_hours.json`), statut `MARKET_CLOSED` hors-heures, correction du dead code sur les checks de position, et transmission de l'âge exact du prix en secondes dans `WAITING_DATA`.

- [x] [2026-07-27 01:35:00] - Élaboration du plan d'implémentation et validation finale de la remédiation globale Paper Trading (`docs/audit/paper-trading-frontend-2026-07-26.md` / `implementation_plan.md`) :
  **Phase 1 (Sécurité & Intégrité)** : F-01 (Pagination curseur composite `(timestamp, id)`), F-02 (Extraction IP cliente réelle `X-Forwarded-For` et `forwarded_allow_ips`).
  **Phase 2 (Robustesse UI & Transport)** : F-03 (Déduplication SSE `seq`), F-04 (Révocation de session `jti` + liste noire Redis), F-05 (Protection XSS `textContent` chart), F-06 (Validation Pydantic server-side `ConfigUpdate`), F-07 (Gestion centralisée HTTP 429 & UX login).
  **Phase 3 (Conformité & Cosmétique)** : F-08 (Harmonisation `lang="en"` & UI), F-09 (Logout HTTP 303), F-10 (Sélecteur actif dynamique), F-11 (Deduplication promesse CSRF), F-12 (CSP & `defer`), F-13 (Evaluations composite cursor), F-14 (Accessibilité ARIA), F-15 (Favicon & nettoyages).

- [x] [2026-07-27 01:14:19] - Audit frontend complet du Paper Trading (`backtest_engine/live/paper_trading/static/`, ~3 900 lignes + contrat API/middlewares) : vérification de l'audit frontend du 2026-07-17 (22/23 anomalies confirmées corrigées, A-08 partielle) ; 15 nouvelles anomalies consignées F-01 à F-15 (2 hautes : pagination curseur perdant des transactions aux timestamps identiques du panic close, rate limit par IP mutualisé derrière le LB Render ; 5 moyennes : doublons SSE, session 30 jours non révocable, innerHTML ticker, validation serveur ConfigUpdate absente, 429 non géré ; 8 basses). Statut : REQUEST CHANGES. Rapport : `docs/audit/paper-trading-frontend-2026-07-26.md`.

- [x] [2026-07-26 22:40:00] - Exécution et validation finale de la remédiation backend Paper Trading (`docs/audit/paper-trading-backend-2026-07-26.md` / `implementation_plan.md`) :
  **Phase 1 (Critiques/Hautes)** : PT-01 (`dry_run` dans `ConversionOrder` + Step 0 fail-closed `spot_router.py`), PT-02 ( normalisation `.lower()` tickers warm-up), PT-03 (masquage hostname credentials Redis URL), PT-04 (staging Redis post-commit PG ingestor Bybit).
  **Phase 2 (Hautes/Moyennes)** : PT-05 (`continue` post-rejet `qty <= 0`), PT-06 (isolation exceptions par broker dans `update_portfolio_nav`), PT-07 (`deposit()` câblé sur SELL Bybit profitable), PT-08 (prix de référence indépendant pour PTC price collar), PT-09 (curseur `seq` monotone flux SSE logs), PT-10 (batch SQL `ANY()` + alignement `secured_balance` Panic Close).
  **Phase 3 (Moyennes/Basses)** : PT-11 (idempotence T212 via `get_pending_orders()`), PT-12 (logging contextuel exceptions), PT-13 (`Decimal` calculs de sortie `BrokerSimulator`), PT-14 (keep-alive PG `asyncio.to_thread`), PT-15 (suppression branche morte `len(row) == 5`), PT-16 à PT-26 (mTLS CA strict, persistance reconciliation, locks throttle, index DDL, auto-reconnexion brokers).
  **Phase 4 (Validation & Tests)** : 92/92 tests unitaires et d'intégration validés, 0 régression.

- [x] [2026-07-25 19:25:00] - Analyse quantitative, financière et comportementale approfondie des transactions de Paper Trading (30/06/2026 au 24/07/2026) :
  **Journal de Trading** : Reconstitution FIFO de 178 transactions (87 trades complets clôturés, 4 positions ouvertes).
  **Métriques Globale** : Win Rate 36.78%, PnL Brut/Net T212 +71.52 € (+23.84%), PnL Net Bybit +21.91 € (Friction com. 49.61 €), Payoff Ratio 2.72, Profit Factor 1.58, Expectancy +0.82 €/trade (+0.35%), Max Drawdown -38.76 €.
  **Diagnostic Anomalies** : Identification du whipsawing sur timeframes ultra-courts 10m/15m (36.8% de trades < 2h causant des pertes d'érosion), stop-loss fixes à 0.5% trop serrés (`AMS.MC` 0% win rate), dépendance à un outlier SAP (+91.76 €).
  **Plan d'Ajustement** : Rehaussement timeframes 10m→30m/45m, Stop-Loss dynamiques ATR (2.0x ATR / min 2.5%), activation du Trailing Stop, filtrage de volatilité ATR et période minimale de rétention.
  **Rapport** : Rédaction du rapport complet dans `paper_trading_analysis_report.md`.

## Tâches en Cours
- Aucune tâche active.

## Tâches Futures

- [ ] Suivi production : vérifier sur le compte T212 demo que le SELL NVO (NOVCd_EQ) passe sans 400 après déploiement du fix 1.00 (position résiduelle ≥ 1.00).

### [2026-07-15 14:50:00] - Validation finale de la Phase 3 (Audit)
- **VV-01 à VV-05** entièrement résolus et vérifiés.
- Régression `Trading212Client` dans `test_paper_trading_engine.py` fixée via un patch `autouse` de classe.
- Régression `test_evaluate_and_execute_strategies_buy_order` fixée par index d'assertion et modification de requête mockée (`timeframe`).
- Régression `is_trading_suspended()` (Kill Switch persistant) fixée par l'ajout d'un fixture global `autouse=True` (`reset_kill_switch_global`) dans `test_signal_executor.py`.
- **Statut final** : La commande `pytest -q tests/` s'est exécutée avec un taux de réussite de **100% (603 passed, 1 skipped)** sans crash (0 segfault Numba). 
- Le Moteur de Paper Trading est prêt pour le déploiement. Un rapport de validation finale a été produit.

## Historique Archivé
- [progress_archive_202608.md](file:///home/kidpixel/trading_automation_v2/memory-bank/archives/progress_archive_202608.md)
- [progress_history.md](file:///home/kidpixel/trading_automation_v2/memory-bank/archives/progress_history.md)