# Vérification de la remédiation audit — Phase 3

**Date** : 2026-07-15  
**Périmètre** : PT-14, PT-15 et PT-16, avec vérification des régressions introduites dans le moteur paper trading, l’API, le schéma PostgreSQL et la suite de tests.

## Verdict

**Échec de validation.** La déclaration selon laquelle `pytest tests/` réussit intégralement avec 593 tests est invalide dans l’état vérifié.

## Résultats d’exécution

| Commande | Résultat |
| :---- | :---- |
| `PYTHONPATH=. pytest -q tests/` | Échec : au moins 13 tests échouent avant un segmentation fault dans `tests/test_lorentzian_classification.py`. |
| `PYTHONPATH=. pytest -q tests/test_api_caching.py tests/test_job_store_security.py tests/test_pre_trade_controls_extended.py tests/test_paper_trading_auth.py` | Échec : 4 tests en échec, 18 succès et 2 avertissements de coroutines Redis non attendues. |
| `PYTHONPATH=. pytest --collect-only -q tests/` | 604 tests collectés. |
| `python3 -m compileall -q` sur les modules modifiés de Phase 3 | Succès syntaxique seulement. |

La compilation Python ne valide pas les appels async, les requêtes SQL ni les invariants transactionnels.

## Synthèse des anomalies

| Identifiant Anomalie | Catégorie de Risque | Conséquence en Production | Sévérité (Critique/Haute/Moyenne) |
| :---- | :---- | :---- | :---- |
| VR-01 | Async I/O / cache | Les écritures Redis ne sont pas attendues ; le cache ne s’écrit pas et des coroutines fuient. | Haute |
| VR-02 | Compatibilité schéma/API | Les endpoints utilisent `cash_balance` après son renommage en `paper_cash_balance`. | Critique |
| VR-03 | Intégrité transactionnelle | La contrainte SQL accepte `buy`/`sell`, alors que les flux insèrent `BUY`/`SELL`. | Critique |
| VR-04 | Migration destructive | La migration manuelle supprime des chandeliers USDT conflictuels sans backup JSON ni journal de conflit. | Haute |
| VR-05 | Validation / tests | Les tests de failsafe et de cache ne sont pas alignés avec l’implémentation. | Moyenne |
| VR-06 | Stabilité CI | La suite complète présente des échecs avant un crash natif Python. | Haute |

## PT-14 — Migration Redis asynchrone

### Éléments conformes

Les lectures Redis passent par `redis.asyncio` et sont bornées par `asyncio.wait_for` :

- `./backtest_engine/live/paper_trading/api.py:375`
- `./backtest_engine/live/paper_trading/api.py:688`
- `./run_paper_trader.py:279`

### Échec confirmé

Les écritures Redis de cache restent invoquées sans `await` ni timeout :

- `./backtest_engine/live/paper_trading/api.py:404`
- `./backtest_engine/live/paper_trading/api.py:762`

Le résultat observé est :

```text
RuntimeWarning: coroutine 'Redis.execute_command' was never awaited
```

Les tests cache mockent encore `get_redis_client()` plutôt que `get_async_redis_client()`. Ils échouent donc et ne valident pas la migration async.

**Conclusion PT-14** : la lecture est partiellement migrée ; l’écriture async est cassée. La remédiation ne peut pas être déclarée terminée.

## PT-15 — Failsafe des clés broker

### Éléments conformes

Les configurations Bybit et Trading 212 exigent maintenant un hash attendu en environnement demo/testnet lorsqu’une clé privée est définie :

- `./backtest_engine/live/bybit/config.py:69`
- `./backtest_engine/live/trading212/config.py:79`

Ce comportement applique correctement un refus par défaut aux clés privées configurées sans hash de référence.

### Échecs de tests

`tests/test_job_store_security.py::test_environment_failsafe` échoue : l’implémentation retourne d’abord une erreur de hash demo non correspondant, tandis que le test attend l’erreur spécifique de clé live détectée dans un environnement demo.

`tests/test_job_store_security.py::test_trading212_idempotency_and_reconciliation` échoue : son environnement de test ne définit pas `EXPECTED_T212_DEMO_KEY_HASH`, désormais requis par le failsafe.

**Conclusion PT-15** : le contrôle est plus strict, mais les tests de régression ne sont pas stabilisés. La réussite intégrale de la suite est donc fausse.

## PT-16 — Migration USDT vers USDC

### Élement conforme

La migration destructive a été retirée du chemin de démarrage :

- `./backtest_engine/live/paper_trading/db_setup.py:431`

Le script dédié exige l’argument `--confirm-purge` avant toute modification.

### Échec confirmé

Le script reste destructif pour les chandeliers conflictuels :

- Il journalise les conflits de `live_prices` et `paper_strategy_configs`.
- Il sauvegarde seulement `live_prices` et `paper_strategy_configs` en JSON.
- Il supprime les conflits de `live_candles_1m` sans les écrire dans `migration_usdt_conflicts` : `./scripts/migrate_usdt_to_usdc.py:130`.
- Il ne génère aucune sauvegarde JSON des chandeliers avant leur suppression.

**Conclusion PT-16** : la suppression n’est plus automatique au démarrage, mais l’outil manuel ne constitue pas une migration non destructive complète.

## Régressions de schéma critiques

### VR-02 — Références obsolètes à `cash_balance`

Le schéma migre `cash_balance` vers `paper_cash_balance` :

- `./backtest_engine/live/paper_trading/db_setup.py:455`

Mais l’API utilise encore `cash_balance` :

- `./backtest_engine/live/paper_trading/api.py:147`
- `./backtest_engine/live/paper_trading/api.py:154`
- `./backtest_engine/live/paper_trading/api.py:581`

Conséquences :

- `GET /api/portfolio` échoue avec une colonne inexistante.
- `POST /api/control/panic` échoue lors du crédit du cash après la suppression d’une position.
- Le chemin d’urgence n’est pas fiable après migration.

### VR-03 — Contrat SQL incompatible avec les transactions

Le schéma neuf impose :

```sql
CHECK (action IN ('buy', 'sell'))
```

dans `./backtest_engine/live/paper_trading/db_setup.py:514`.

Les flux d’exécution insèrent pourtant des actions majuscules :

- `./backtest_engine/live/paper_trading/signal_executor.py:826`
- `./backtest_engine/live/paper_trading/signal_executor.py:1123`
- `./backtest_engine/live/paper_trading/api.py:591`

Un schéma neuf rejette donc les achats, ventes et clôtures d’urgence avec une violation de contrainte. Les tests actuels utilisent des mocks SQL et ne détectent pas ce défaut.

## Conditions de validation avant déploiement

1. Attendre les appels `setex()` Redis asynchrones et appliquer `asyncio.wait_for`.
2. Mettre à jour les tests de cache avec `AsyncMock` et `get_async_redis_client()`.
3. Uniformiser les requêtes sur `paper_cash_balance`.
4. Uniformiser le domaine SQL de `action` avec les valeurs réellement insérées, ou convertir toutes les actions en minuscules.
5. Sauvegarder et journaliser les conflits `live_candles_1m` avant toute suppression dans `./scripts/migrate_usdt_to_usdc.py`.
6. Exécuter une suite complète stable, sans échec ni crash natif, sur les 604 tests actuellement collectés.
7. Ajouter des tests PostgreSQL d’intégration contre un schéma neuf et un schéma existant migré.

## Conclusion

Les changements ne sont pas validés pour déploiement. PT-14 est incomplet, PT-15 possède une couverture de test cassée, PT-16 reste destructif pour une catégorie de données, et les régressions de schéma empêchent le fonctionnement fiable du portfolio, du panic close et des transactions sur une base initialisée ou migrée.
