# Vérification de remédiation Paper Trading — Contrôle final Phase 3

**Date** : 2026-07-15  
**Périmètre** : vérification indépendante des remédiations annoncées pour PT-14, PT-15, PT-16 et des éléments VR-02 à VR-06 dans `backtest_engine/live/`, `scripts/migrate_usdt_to_usdc.py` et les tests associés.

## Verdict

**Échec de validation.** L’affirmation selon laquelle `PYTHONPATH=. pytest -q tests/` termine avec `604 / 604` tests réussis n’est pas reproductible sur l’état vérifié du dépôt.

## Résultats d’exécution

| Commande | Résultat |
| :---- | :---- |
| `python3 -m compileall -q` sur les modules annoncés | Succès syntaxique. |
| `PYTHONPATH=. pytest -q tests/test_api_caching.py tests/test_job_store_security.py tests/test_pre_trade_controls_extended.py tests/test_paper_trading_auth.py` | Échec : **2 échecs, 20 succès**. |
| `PYTHONPATH=. pytest -q tests/test_lorentzian_classification.py` | Échec : **segmentation fault** reproductible. |
| `PYTHONPATH=. pytest -q tests/` | Non exécuté : le crash natif du test ciblé invalide déjà toute affirmation de réussite globale. |

La compilation Python ne valide ni l’exécution asynchrone, ni les migrations PostgreSQL, ni la stabilité des extensions natives.

## Synthèse des anomalies

| Identifiant Anomalie | Catégorie de Risque | Conséquence en Production | Sévérité (Critique/Haute/Moyenne) |
| :---- | :---- | :---- | :---- |
| VV-01 | Async I/O | Les endpoints FastAPI peuvent bloquer l’event loop sur Redis et ne correspondent pas au contrat de cache async testé. | Haute |
| VV-02 | Migration de données | Une migration USDT/USDC destructive s’exécute toujours automatiquement au démarrage. | Haute |
| VV-03 | Stabilité native | Le calcul Lorentzian termine le processus Python par segmentation fault. | Critique |
| VV-04 | Invariants SQL | Le schéma autorise des états financiers et des actions de transaction non bornés. | Haute |
| VV-05 | Isolation de stratégie | Les positions ne sont pas séparées par timeframe. | Haute |

## VV-01 — PT-14 : Redis async non appliqué aux endpoints vérifiés

`get_async_redis_client()` existe dans `./backtest_engine/live/connection.py:547`, mais les routes de cache inspectées utilisent toujours `get_redis_client()` et des appels synchrones :

- `./backtest_engine/live/paper_trading/api.py:357`
- `./backtest_engine/live/paper_trading/api.py:369`
- `./backtest_engine/live/paper_trading/api.py:398`
- `./backtest_engine/live/paper_trading/api.py:652`
- `./backtest_engine/live/paper_trading/api.py:726`

Ces appels ne sont ni attendus avec `await`, ni bornés par `asyncio.wait_for`. Une indisponibilité Redis peut donc encore immobiliser l’event loop Uvicorn/FastAPI pendant le timeout du client synchrone.

Les deux échecs ciblés confirment l’écart entre l’implémentation et le contrat de test async :

```text
FAILED tests/test_api_caching.py::TestApiCaching::test_get_candles_caching
FAILED tests/test_api_caching.py::TestApiCaching::test_get_performance_metrics_caching_zero_trades
2 failed, 20 passed
```

Les tests patchent `get_async_redis_client()` avec `AsyncMock`, mais ce client n’est pas appelé par les endpoints.

## VV-02 — PT-16 : migration destructive toujours présente au démarrage

Le script manuel `./scripts/migrate_usdt_to_usdc.py` contient désormais une exportation JSON des chandeliers conflictuels, un journal `migration_usdt_conflicts` et une suppression fondée sur le ticker et le timestamp typé. Ces éléments améliorent ce script.

Le chemin réellement exécuté par `init_db()` reste néanmoins destructif :

- suppression des conflits `live_prices` : `./backtest_engine/live/paper_trading/db_setup.py:437`
- suppression des conflits `live_candles_1m` : `./backtest_engine/live/paper_trading/db_setup.py:447`
- suppression des conflits `paper_strategy_configs` : `./backtest_engine/live/paper_trading/db_setup.py:461`

Le bloc `./backtest_engine/live/paper_trading/db_setup.py:431` n’exige pas `--confirm-purge`, n’exporte pas de sauvegarde et ne journalise pas les conflits. Le script manuel ne remédie donc pas à la migration destructive active lors du démarrage.

## VV-03 — VR-06 : segmentation fault Numba non corrigé

Le test `test_no_future_data_in_knn` termine toujours le processus Python :

```text
Fatal Python error: Segmentation fault
.../backtest_engine/indicators/lorentzian_classification.py:863
.../tests/test_lorentzian_classification.py:234 in test_no_future_data_in_knn
```

La conversion Fortran des entrées 2D est présente dans `./backtest_engine/indicators/lorentzian_classification.py:757`, mais l’exécution atteint toujours `_lorentzian_knn_2d_nb()` à `./backtest_engine/indicators/lorentzian_classification.py:863` avant le crash. La stabilité de Numba 0.61.2 n’est donc pas démontrée.

## VV-04 — VR-02 / VR-03 : standard de colonne cohérent, invariants absents

Le standard courant est `cash_balance`, de manière cohérente entre le schéma et les endpoints inspectés :

- `./backtest_engine/live/paper_trading/db_setup.py:481`
- `./backtest_engine/live/paper_trading/api.py:141`

En revanche, les définitions actuelles ne comportent toujours pas les contraintes annoncées sur :

- la non-négativité du cash ;
- les quantités strictement positives ;
- les prix strictement positifs ;
- le domaine fermé des actions, par exemple `CHECK (UPPER(action) IN ('BUY', 'SELL'))`.

Les tables non contraintes sont définies dans :

- `./backtest_engine/live/paper_trading/db_setup.py:478`
- `./backtest_engine/live/paper_trading/db_setup.py:519`
- `./backtest_engine/live/paper_trading/db_setup.py:534`

## VV-05 — PT-12 : isolation par timeframe toujours absente

`paper_positions` conserve une unicité limitée à `(asset, strategy_name)` dans `./backtest_engine/live/paper_trading/db_setup.py:528`. L’exécuteur construit et consulte également ses positions actives sans timeframe :

- `./backtest_engine/live/paper_trading/signal_executor.py:378`
- `./backtest_engine/live/paper_trading/signal_executor.py:438`

Deux configurations ayant le même actif et la même stratégie sur des timeframes distincts restent donc incapables de détenir des positions indépendantes.

## Éléments confirmés

- Les failsafes SHA-256 stricts sont présents dans `./backtest_engine/live/bybit/config.py:62` et `./backtest_engine/live/trading212/config.py:72`.
- Les tests ciblés de failsafe, pré-trade et authentification inclus dans la sélection exécutée réussissent.
- Le script `./scripts/migrate_usdt_to_usdc.py` sauvegarde et journalise maintenant les conflits de chandeliers, mais il ne remplace pas le chemin destructif de `init_db()`.

## Conditions de validation avant déploiement

1. Migrer les routes de cache de `./backtest_engine/live/paper_trading/api.py` vers `get_async_redis_client()`, avec `await` et `asyncio.wait_for` sur chaque opération Redis.
2. Retirer le bloc de migration USDT/USDC de `init_db()` ; seule une commande manuelle explicitement confirmée doit modifier ou supprimer ces données.
3. Éliminer le segmentation fault de `_lorentzian_knn_2d_nb()` et exécuter le test concerné plusieurs fois sans crash.
4. Ajouter les contraintes financières PostgreSQL et les tester contre une base réelle initialisée depuis le schéma.
5. Ajouter `timeframe` à l’identité de `paper_positions`, aux requêtes de l’exécuteur et à la migration des positions historiques.
6. Exécuter `PYTHONPATH=. pytest -q tests/` jusqu’à une fin normale, sans échec ni crash natif, avant de déclarer la Phase 3 terminée.

## Conclusion

La remédiation n’est pas validée. Les contrôles de hash broker et une partie du script manuel USDT/USDC sont présents, mais PT-14 n’est pas appliqué aux endpoints vérifiés, la suppression USDT/USDC reste active au démarrage, les invariants SQL et l’isolation des stratégies restent incomplets, et la suite de tests demeure bloquée par un segmentation fault natif.
