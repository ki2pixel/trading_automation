# Vérification complémentaire — Remédiation Phase 3

**Date** : 2026-07-15  
**Périmètre** : vérification des corrections annoncées pour PT-14, PT-15, PT-16 et VR-01 à VR-06 après la seconde série de modifications.

## Verdict

**Échec de validation.** Les corrections SQL et Redis sont partiellement présentes, mais la déclaration `604 / 604 tests réussis` est contredite par les exécutions reproduites.

## Résultats d’exécution

| Commande | Résultat |
| :---- | :---- |
| `PYTHONPATH=. pytest -q tests/test_api_caching.py tests/test_job_store_security.py tests/test_pre_trade_controls_extended.py tests/test_paper_trading_auth.py` | **2 échecs, 20 succès**. |
| `PYTHONPATH=. pytest -q tests/test_api_caching.py tests/test_job_store_security.py tests/test_pre_trade_controls_extended.py tests/test_paper_trading_auth.py tests/test_lorentzian_classification.py` | **Segmentation fault** dans `test_no_future_data_in_knn`. |
| `PYTHONPATH=. pytest --collect-only -q tests/` | **604 tests collectés**. |

La suite complète ne peut pas être déclarée réussie tant que ces deux échecs et ce crash natif sont reproductibles.

## Corrections confirmées

### PT-14 / VR-01 — Écritures Redis async corrigées

Les écritures cache sont désormais attendues et bornées :

- `./backtest_engine/live/paper_trading/api.py:404`
- `./backtest_engine/live/paper_trading/api.py:762`

Les lectures restent asynchrones avec `asyncio.wait_for`. Les avertissements précédents de coroutines Redis non attendues ne réapparaissent pas dans la sélection de tests exécutée.

### VR-02 — Renommage du ledger appliqué à l’API

Les endpoints portfolio et panic utilisent désormais `paper_cash_balance` :

- `./backtest_engine/live/paper_trading/api.py:147`
- `./backtest_engine/live/paper_trading/api.py:581`

La correction élimine la référence obsolète à `cash_balance` dans ces deux flux.

### VR-03 — Domaine SQL des actions élargi

Le schéma neuf accepte désormais les actions insensibles à la casse avec :

```sql
CHECK (UPPER(action) IN ('BUY', 'SELL'))
```

La migration remplace aussi les contraintes existantes de même nom :

- `./backtest_engine/live/paper_trading/db_setup.py:514`
- `./backtest_engine/live/paper_trading/db_setup.py:582`

### PT-16 / VR-04 — Conflits de chandeliers enregistrés

La migration journalise maintenant les conflits `live_candles_1m` dans `migration_usdt_conflicts` avant la suppression :

- `./scripts/migrate_usdt_to_usdc.py:130`

## Anomalies confirmées

| Identifiant Anomalie | Catégorie de Risque | Conséquence en Production | Sévérité (Critique/Haute/Moyenne) |
| :---- | :---- | :---- | :---- |
| VF-01 | Stabilité native | Le correctif de contiguïté NumPy ne supprime pas le segmentation fault Numba. | Critique |
| VF-02 | Isolation des tests / failsafe | Deux tests de sécurité Trading 212 restent incompatibles avec leur environnement et leur assertion. | Moyenne |
| VF-03 | Migration de données | La sauvegarde JSON reste incomplète pour les chandeliers et la suppression conflictuelle repose sur une comparaison de timestamp fragile. | Haute |

### VF-01 — Segmentation fault Numba toujours présent

`np.ascontiguousarray` est appliqué aux séries OHLC dans `./backtest_engine/indicators/lorentzian_classification.py:751`, mais le test ciblé continue de faire tomber l’interpréteur :

```text
Fatal Python error: Segmentation fault
.../backtest_engine/indicators/lorentzian_classification.py:856
.../tests/test_lorentzian_classification.py:234 in test_no_future_data_in_knn
```

Le changement ne valide donc pas la stabilité de Numba 0.61.2. Une suite qui peut terminer le processus Python ne fournit aucune garantie de réussite globale.

### VF-02 — Tests Trading 212 failsafe toujours en échec

Les échecs reproduits sont :

1. `test_environment_failsafe` attend le texte `Demo environment`, tandis que l’implémentation retourne `Demo/Testnet environment`.
2. `test_trading212_idempotency_and_reconciliation` échoue avant le test métier : la clé chargée ne correspond pas à `EXPECTED_T212_DEMO_KEY_HASH`.

Le second échec révèle une isolation incomplète de l’environnement de test. Le fixture global dans `./tests/conftest.py` injecte des hashes, mais ne neutralise pas les variables `T212_DEMO_API_SECRET` ou les valeurs héritées de l’environnement local, que `Trading212Config` préfère aux variables génériques.

Le failsafe lui-même rejette correctement la configuration ; la suite de test n’est cependant pas reproductible dans l’environnement courant.

### VF-03 — Migration chandeliers : conservation persistante, export JSON incomplet

Les conflits de chandeliers sont maintenant conservés dans `migration_usdt_conflicts`, ce qui évite leur perte silencieuse dans PostgreSQL. Le script n’exporte néanmoins toujours en JSON que `live_prices` et `paper_strategy_configs` :

- `./scripts/migrate_usdt_to_usdc.py:20`
- `./scripts/migrate_usdt_to_usdc.py:28`

Les chandeliers conflictuels ne bénéficient donc pas de l’export JSON annoncé avant altération.

Le `DELETE` des chandeliers joint ensuite :

```sql
c_usdt.timestamp_minute::text = logged.ts
```

alors que `logged.ts` est extrait de `row_to_json(...)->>'timestamp_minute'`. Les représentations PostgreSQL `timestamp::text` et JSON peuvent différer, notamment par l’usage d’un espace contre `T` comme séparateur. Une divergence empêche le `DELETE`, puis l’`UPDATE` du ticker peut violer la clé primaire `(ticker, timestamp_minute)`.

La suppression doit être reliée aux colonnes natives `ticker` et `timestamp_minute` transportées dans le CTE, sans sérialisation JSON puis comparaison textuelle.

## Conditions restantes avant validation

1. Éliminer le segmentation fault de `test_no_future_data_in_knn` et démontrer sa stabilité sur exécutions répétées.
2. Isoler explicitement les variables de credentials Trading 212 dans les tests, notamment les variables demo prioritaires.
3. Aligner les assertions de message sur le contrat réel ou, de préférence, tester un code d’erreur stable plutôt qu’un texte complet.
4. Exporter les conflits `live_candles_1m` en JSON avant modification si cette garantie fait partie du contrat de migration.
5. Réécrire la suppression des chandeliers à partir des colonnes timestamp natives, sans comparaison textuelle issue de JSON.
6. Exécuter `PYTHONPATH=. pytest -q tests/` jusqu’à une fin normale avec 604 succès et sans crash de processus.

## Conclusion

Les corrections PT-14, VR-02, VR-03 et l’enregistrement des conflits de chandeliers corrigent une partie des défauts précédents. La remédiation globale reste non validée : la suite ne passe pas, le crash Numba demeure et la migration de chandeliers possède un chemin de suppression fragile.
