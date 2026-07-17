# Vérification des remédiations VV-01 à VV-05

**Date** : 2026-07-15  
**Périmètre** : contrôle indépendant des corrections Redis, migration USDT/USDC, stabilité Numba, invariants SQL et isolation des positions par timeframe.

## Verdict

**Validation partielle, déploiement non autorisable.** La suite de tests annoncée réussit effectivement, sans crash natif. Les correctifs VV-01, VV-02 et VV-03 sont confirmés par revue et exécution. VV-04 et VV-05 restent invalides pour une base PostgreSQL réelle : la migration de schéma réintroduit la contrainte d’unicité historique incompatible avec les timeframes et échoue sur une initialisation vierge avant la création de `paper_strategy_configs`.

## Résultats d’exécution

| Commande | Résultat |
| :---- | :---- |
| `PYTHONPATH=. pytest -q tests/test_api_caching.py tests/test_signal_executor.py tests/test_paper_trading_engine.py tests/test_robustness.py tests/test_job_store_security.py tests/test_pre_trade_controls_extended.py tests/test_paper_trading_auth.py` | **18 succès**. |
| `PYTHONPATH=. pytest -q tests/test_lorentzian_classification.py` | **60 succès**, sans segmentation fault. |
| `PYTHONPATH=. pytest -q tests/` | **603 succès, 1 ignoré, 60 avertissements** en 65,02 s, sans crash natif. |
| Vérification structurelle du schéma | Détection simultanée de la clé timeframe attendue et de la clé historique à deux colonnes réintroduite. |

Les avertissements observés sont principalement des avertissements de dépréciation Pandas, websockets et Optuna. Ils ne remettent pas en cause le résultat de la suite, mais restent à traiter séparément.

## Synthèse

| Identifiant Anomalie | Catégorie de Risque | Conséquence en Production | Sévérité (Critique/Haute/Moyenne) |
| :---- | :---- | :---- | :---- |
| VV-07 | Migration SQL / isolation stratégie | La contrainte historique `(asset, strategy_name)` est recréée après la migration et bloque les positions multi-timeframes. | Critique |
| VV-08 | Initialisation PostgreSQL | Une base vierge échoue lors du backfill des positions, avant la création de `paper_strategy_configs`. | Critique |
| VV-09 | Invariants SQL existants | Les `CHECK` définis uniquement dans `CREATE TABLE IF NOT EXISTS` ne sont pas ajoutés aux bases déjà déployées. | Haute |
| VV-10 | Migration des données ambiguës | Le backfill choisit arbitrairement un timeframe avec `LIMIT 1` lorsqu’il existe plusieurs configurations admissibles. | Haute |

## Correctifs confirmés

### VV-01 — Redis asynchrone dans les endpoints contrôlés

Les endpoints `/candles` et `/performance/metrics` utilisent maintenant `get_async_redis_client()` et bornent les lectures et écritures Redis par `asyncio.wait_for` :

- `./backtest_engine/live/paper_trading/api.py:357`
- `./backtest_engine/live/paper_trading/api.py:369`
- `./backtest_engine/live/paper_trading/api.py:398`
- `./backtest_engine/live/paper_trading/api.py:642`
- `./backtest_engine/live/paper_trading/api.py:652`
- `./backtest_engine/live/paper_trading/api.py:726`

Les tests de cache ciblés réussissent. La migration Redis de ces endpoints est validée.

### VV-02 — Suppression de la migration destructive au démarrage

Le bloc destructif USDT/USDC a été retiré de `init_db()`. Le code documente maintenant que la migration est exclusivement confiée au script manuel :

- `./backtest_engine/live/paper_trading/db_setup.py:432`

Cette correction retire la suppression automatique au démarrage. Le script `./scripts/migrate_usdt_to_usdc.py` demeure le seul chemin prévu pour une migration explicitement confirmée.

### VV-03 — Stabilité Numba

La boucle KNN n’est plus compilée avec `parallel=True` ni exécutée avec `prange` :

- `./backtest_engine/indicators/lorentzian_classification.py:675`
- `./backtest_engine/indicators/lorentzian_classification.py:698`

Les données et tampons sont maintenant mis en ordre C contigu :

- `./backtest_engine/indicators/lorentzian_classification.py:753`
- `./backtest_engine/indicators/lorentzian_classification.py:790`

Les 60 tests Lorentzian et la suite complète se terminent normalement. Le segmentation fault précédemment reproductible n’est plus observé dans cet environnement.

## Anomalies bloquantes

### VV-07 — La migration recrée la contrainte incompatible avec les timeframes

Le schéma de `paper_positions` définit correctement la clé attendue :

```sql
UNIQUE (asset, strategy_name, timeframe)
```

à `./backtest_engine/live/paper_trading/db_setup.py:491`.

La migration supprime également la clé historique puis crée la nouvelle clé :

- `./backtest_engine/live/paper_trading/db_setup.py:516`
- `./backtest_engine/live/paper_trading/db_setup.py:528`

Mais un bloc postérieur réintroduit systématiquement l’ancienne contrainte si elle est absente :

```sql
ALTER TABLE paper_positions
ADD CONSTRAINT paper_positions_asset_strategy_key
UNIQUE (asset, strategy_name);
```

à `./backtest_engine/live/paper_trading/db_setup.py:643` à `./backtest_engine/live/paper_trading/db_setup.py:653`.

Après une migration réussie, l’ancienne contrainte est nécessairement absente ; cette condition recrée donc une exclusivité `(asset, strategy_name)` en plus de la nouvelle clé à trois colonnes. Une position `1h` et une position `15m` pour le même actif et la même stratégie ne peuvent toujours pas coexister.

**Correction requise** : supprimer entièrement le bloc `./backtest_engine/live/paper_trading/db_setup.py:643` à `./backtest_engine/live/paper_trading/db_setup.py:653`. Il invalide directement VV-05.

### VV-08 — Une initialisation vierge référence une table non créée

Le backfill de timeframe est exécuté à `./backtest_engine/live/paper_trading/db_setup.py:533` avant la création de `paper_strategy_configs`, qui ne commence qu’à `./backtest_engine/live/paper_trading/db_setup.py:543`.

La requête de backfill contient :

```sql
SELECT c.timeframe
FROM paper_strategy_configs c
```

PostgreSQL résout le nom de table lors de l’exécution, même si `paper_positions` est vide. Sur une base vierge, `init_db()` échoue donc avec une erreur de relation inexistante avant de créer les configurations de stratégie.

**Correction requise** : créer `paper_strategy_configs` avant le backfill, ou déplacer le backfill après sa création et l’encadrer par une condition `to_regclass('paper_strategy_configs') IS NOT NULL` destinée aux migrations de bases existantes.

### VV-09 — Les contraintes financières ne migrent pas les bases existantes

Les nouveaux `CHECK` sont présents dans le DDL de création :

- `cash_balance >= 0` et `total_nav >= 0` : `./backtest_engine/live/paper_trading/db_setup.py:443`
- quantité, prix et valeur des transactions : `./backtest_engine/live/paper_trading/db_setup.py:502`
- quantité et prix des positions : `./backtest_engine/live/paper_trading/db_setup.py:486`

`CREATE TABLE IF NOT EXISTS` ne modifie pas une table existante. Aucune instruction `ALTER TABLE ... ADD CONSTRAINT` correspondante n’est présente pour les déploiements déjà initialisés. Les bases en production conservent donc les tables sans ces invariants.

**Correction requise** : ajouter des migrations idempotentes nommées pour chaque contrainte, après validation ou traitement des lignes historiques invalides. Ajouter des tests PostgreSQL d’intégration sur une base préexistante et une base vierge.

### VV-10 — Backfill de timeframe ambigu

Le backfill utilise :

```sql
SELECT c.timeframe
FROM paper_strategy_configs c
WHERE c.asset = p.asset
  AND c.strategy_name = p.strategy_name
LIMIT 1
```

à `./backtest_engine/live/paper_trading/db_setup.py:535` à `./backtest_engine/live/paper_trading/db_setup.py:541`.

Lorsque plusieurs configurations existent pour le même actif et la même stratégie, `LIMIT 1` sélectionne un timeframe arbitraire. Cette règle ne respecte pas la décision de migration sûre : déduction automatique uniquement si l’association est unique ; sinon revue manuelle et quarantaine.

**Correction requise** : ne migrer automatiquement que les positions ayant exactement une configuration correspondante. Placer les cas ambigus dans un état de revue manuelle, sans créer de position identifiée par un timeframe inventé.

## Conclusion

La réussite de la suite de tests est confirmée : `603 passed, 1 skipped, 60 warnings`. Les correctifs Redis async, la suppression de la migration destructive au démarrage et la stabilisation Numba sont validés dans l’environnement vérifié.

Le système reste toutefois non autorisable pour un déploiement Paper Trading fiable tant que VV-07 à VV-10 ne sont pas corrigées et validées sur PostgreSQL réel. Les tests unitaires actuels ne créent pas le schéma à partir d’une base vierge et ne vérifient pas la migration d’une base existante ; ils ne détectent donc ni la recréation de la clé historique, ni l’ordre invalide de création des tables, ni l’absence de migration des contraintes `CHECK`.
