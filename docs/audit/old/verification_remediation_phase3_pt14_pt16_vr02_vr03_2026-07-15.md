# Vérification des remédiations PT-14 à PT-16 et VR-02 à VR-03

**Date** : 2026-07-15  
**Périmètre** : contrôle indépendant de Redis async, des failsafes broker, de la migration USDT/USDC, de la standardisation `paper_cash_balance` et des contraintes SQL d’actions.

## Verdict

**Tests validés, déploiement Paper Trading non autorisable.** La suite de tests annoncée réussit effectivement et les remédiations PT-14, PT-15, PT-16, VR-02 et VR-03 sont présentes dans les flux inspectés. Deux défauts de migration PostgreSQL déjà identifiés persistent toutefois : la clé historique de position est recréée et le backfill des timeframes référence une table non encore créée. Ces défauts ne sont pas couverts par les tests unitaires actuels.

## Résultats d’exécution

| Commande | Résultat |
| :---- | :---- |
| `PYTHONPATH=. pytest -q tests/test_api_caching.py tests/test_job_store_security.py tests/test_signal_executor.py tests/test_paper_trading_engine.py tests/test_robustness.py tests/test_pre_trade_controls_extended.py tests/test_paper_trading_auth.py` | **60 succès**. |
| `PYTHONPATH=. pytest -q tests/` | **603 succès, 1 ignoré, 60 avertissements** en 63,90 s. |
| `python3 -m compileall -q` sur les modules de remédiation | Succès syntaxique. |
| Contrôle statique de migration | La clé à deux colonnes est recréée ; le backfill est exécuté avant la création de `paper_strategy_configs`. |

## Éléments confirmés

### PT-14 — Redis async dans les routes FastAPI

Les routes de cache utilisent désormais `get_async_redis_client()` et bornent les opérations réseau par `asyncio.wait_for` :

- cache des chandeliers : `./backtest_engine/live/paper_trading/api.py:357`, `./backtest_engine/live/paper_trading/api.py:369`, `./backtest_engine/live/paper_trading/api.py:398` ;
- cache des métriques : `./backtest_engine/live/paper_trading/api.py:642`, `./backtest_engine/live/paper_trading/api.py:652`, `./backtest_engine/live/paper_trading/api.py:726` ;
- reprise du trading : `./backtest_engine/live/paper_trading/api.py:858`, `./backtest_engine/live/paper_trading/api.py:862`.

Les tests ciblés de cache réussissent avec `AsyncMock` et le patch de `get_async_redis_client()`.

### PT-15 — Failsafes des clés broker

Les tests de sécurité ciblés réussissent. Les configurations broker continuent d’exiger un hash environnemental correspondant avant d’autoriser l’usage de clés privées :

- Bybit : `./backtest_engine/live/bybit/config.py:62` ;
- Trading 212 : `./backtest_engine/live/trading212/config.py:72`.

Le fixture global isole maintenant le client Redis async des tests unitaires : `./tests/conftest.py:27`.

### PT-16 — Migration USDT/USDC hors démarrage

`init_db()` ne contient plus de migration destructive USDT/USDC : `./backtest_engine/live/paper_trading/db_setup.py:432`.

Le script manuel `./scripts/migrate_usdt_to_usdc.py` :

- exige `--confirm-purge` : `./scripts/migrate_usdt_to_usdc.py:55` ;
- exporte les chandeliers conflictuels en JSON : `./scripts/migrate_usdt_to_usdc.py:34` ;
- journalise les conflits avant suppression : `./scripts/migrate_usdt_to_usdc.py:154` ;
- supprime par ticker et timestamp typés, sans comparaison textuelle : `./scripts/migrate_usdt_to_usdc.py:160`.

### VR-02 — Standard `paper_cash_balance`

La migration renomme idempotemment la colonne historique `cash_balance` vers `paper_cash_balance` :

- `./backtest_engine/live/paper_trading/db_setup.py:456` ;
- `./backtest_engine/live/paper_trading/db_setup.py:460`.

Les endpoints API et l’exécuteur utilisent le nouveau nom, tout en conservant la clé JSON publique `cash_balance` :

- portfolio API : `./backtest_engine/live/paper_trading/api.py:141`, `./backtest_engine/live/paper_trading/api.py:148` ;
- panic close : `./backtest_engine/live/paper_trading/api.py:545` ;
- exécuteur : `./backtest_engine/live/paper_trading/signal_executor.py:187`, `./backtest_engine/live/paper_trading/signal_executor.py:789`, `./backtest_engine/live/paper_trading/signal_executor.py:1060`.

Cette standardisation est cohérente. Elle ne corrige pas à elle seule le défaut PT-01 préexistant : `update_portfolio_nav()` continue de remplacer le ledger paper par le solde broker lorsque les clients privés sont actifs.

### VR-03 — Domaine SQL des actions et invariants existants

Les tables neuves imposent maintenant `UPPER(action) IN ('BUY', 'SELL')` : `./backtest_engine/live/paper_trading/db_setup.py:512`.

Les migrations ajoutent également des contraintes nommées et idempotentes pour les tables existantes :

- cash et NAV : `./backtest_engine/live/paper_trading/db_setup.py:658` ;
- positions : `./backtest_engine/live/paper_trading/db_setup.py:666` ;
- actions et transactions : `./backtest_engine/live/paper_trading/db_setup.py:677`.

## Anomalies bloquantes persistantes

| Identifiant Anomalie | Catégorie de Risque | Conséquence en Production | Sévérité (Critique/Haute/Moyenne) |
| :---- | :---- | :---- | :---- |
| VV-07 | Migration SQL / isolation stratégie | La contrainte historique empêche toujours deux positions différenciées uniquement par le timeframe. | Critique |
| VV-08 | Initialisation PostgreSQL | Une base vierge échoue avant la création des configurations de stratégie. | Critique |
| VV-10 | Migration de données | Une position historique ambiguë reçoit un timeframe arbitraire. | Haute |

### VV-07 — Réintroduction de la clé historique des positions

La migration crée bien la clé attendue `(asset, strategy_name, timeframe)` à `./backtest_engine/live/paper_trading/db_setup.py:538`. Mais un bloc ultérieur réintroduit systématiquement la contrainte historique lorsqu’elle est absente :

```sql
ALTER TABLE paper_positions
ADD CONSTRAINT paper_positions_asset_strategy_key
UNIQUE (asset, strategy_name);
```

`./backtest_engine/live/paper_trading/db_setup.py:692` à `./backtest_engine/live/paper_trading/db_setup.py:702`.

La migration supprime d’abord cette même contrainte à `./backtest_engine/live/paper_trading/db_setup.py:526`. Elle est donc absente à l’exécution du bloc final et immédiatement recréée. L’isolation par timeframe reste impossible malgré la nouvelle colonne et la nouvelle clé.

**Correction requise** : supprimer le bloc `./backtest_engine/live/paper_trading/db_setup.py:692` à `./backtest_engine/live/paper_trading/db_setup.py:702`.

### VV-08 — Backfill avant création de `paper_strategy_configs`

Le backfill exécute une sous-requête sur `paper_strategy_configs` :

```sql
SELECT c.timeframe
FROM paper_strategy_configs c
```

à `./backtest_engine/live/paper_trading/db_setup.py:545` à `./backtest_engine/live/paper_trading/db_setup.py:552`.

La table `paper_strategy_configs` est seulement créée à `./backtest_engine/live/paper_trading/db_setup.py:553`. PostgreSQL résout les relations avant l’évaluation des lignes : une base vierge échoue donc même si `paper_positions` est vide.

**Correction requise** : déplacer le backfill après la création de `paper_strategy_configs` et l’exécuter exclusivement pour les tables existantes.

### VV-10 — Déduction de timeframe ambiguë

Le backfill utilise `LIMIT 1` sans ordre ni contrôle du nombre de configurations correspondantes : `./backtest_engine/live/paper_trading/db_setup.py:547` à `./backtest_engine/live/paper_trading/db_setup.py:551`.

Une position existante associée à plusieurs configurations reçoit un timeframe arbitraire. Cette migration ne respecte pas la règle de sûreté définie pour PT-12 : déduction automatique uniquement en cas d’association unique ; revue manuelle pour les cas ambigus.

**Correction requise** : ne renseigner le timeframe que lorsqu’une seule configuration correspond. Quarantainer les positions ambiguës pour revue manuelle.

## Conclusion

La réussite `603 passed, 1 skipped, 60 warnings` est reproductible. Les chemins Redis async, les failsafes testés, le script de migration manuel, la nomenclature `paper_cash_balance` et la contrainte d’action sont confirmés.

La suite ne remplace pas un test d’intégration PostgreSQL sur schéma vierge et schéma migré. VV-07, VV-08 et VV-10 bloquent toujours la validation de déploiement du moteur Paper Trading.
