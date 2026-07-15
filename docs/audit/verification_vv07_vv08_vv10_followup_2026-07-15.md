# Vérification de suivi — VV-07, VV-08 et VV-10

**Date** : 2026-07-15  
**Périmètre** : migration PostgreSQL de `paper_positions`, ordre d’initialisation et couverture d’intégration associée.

## Verdict

**Validation partielle, déploiement non autorisable.**

Les défauts structuraux VV-07 et VV-08 sont corrigés dans `./backtest_engine/live/paper_trading/db_setup.py` et les tests d’intégration PostgreSQL ajoutés s’exécutent. La suite complète réussit avec **605 succès, 1 test ignoré et 60 avertissements**.

VV-10 reste invalide. Le nouveau backfill est relancé à chaque démarrage et traite toute position dont le timeframe est `1m` comme une position historique non migrée. Une position `1m` légitime, créée après la migration pour une stratégie possédant plusieurs configurations, est donc réécrite en `AMBIGUOUS` au démarrage suivant. Les nouveaux tests ne reproduisent pas le flux réel : ils ajoutent les configurations ambiguës après `init_db()` puis exécutent manuellement une copie de la requête de backfill.

## Résultats d’exécution

| Commande | Résultat |
| :---- | :---- |
| `PYTHONPATH=. pytest -q tests/test_db_setup.py` | **2 succès** en 6,72 s. |
| `PYTHONPATH=. pytest -q tests/` | **605 succès, 1 ignoré, 60 avertissements** en 71,40 s. |

Aucune commande de lint ou de vérification statique de types n’est définie dans les fichiers de configuration présents dans le dépôt.

## Correctifs confirmés

### VV-07 — Suppression de la contrainte historique

La migration supprime maintenant `paper_positions_asset_strategy_key` et ne la recrée plus ultérieurement :

- suppression : `./backtest_engine/live/paper_trading/db_setup.py:530` à `./backtest_engine/live/paper_trading/db_setup.py:538` ;
- clé d’identité finale : `./backtest_engine/live/paper_trading/db_setup.py:540` à `./backtest_engine/live/paper_trading/db_setup.py:548`.

La clé finale est bien :

```sql
UNIQUE (asset, strategy_name, timeframe)
```

L’isolation des positions par timeframe n’est plus neutralisée par une seconde contrainte à deux colonnes.

### VV-08 — Création de la table avant le backfill

`paper_strategy_configs` est maintenant créée avant toute lecture destinée au backfill :

- création : `./backtest_engine/live/paper_trading/db_setup.py:552` à `./backtest_engine/live/paper_trading/db_setup.py:569` ;
- backfill : `./backtest_engine/live/paper_trading/db_setup.py:714` à `./backtest_engine/live/paper_trading/db_setup.py:756`.

Le test de schéma vierge s’exécute sur un schéma PostgreSQL isolé et réussit. Le défaut de relation inexistante est corrigé.

### Isolation de schéma

Les recherches dans `information_schema` utilisent `table_schema = current_schema()` pour la colonne de solde et les contraintes inspectées :

- `./backtest_engine/live/paper_trading/db_setup.py:456` à `./backtest_engine/live/paper_trading/db_setup.py:460` ;
- `./backtest_engine/live/paper_trading/db_setup.py:531` à `./backtest_engine/live/paper_trading/db_setup.py:545`.

Cette correction évite les faux positifs entre schémas PostgreSQL et est validée par les tests utilisant un `search_path` dédié.

## Anomalie bloquante

| Identifiant Anomalie | Catégorie de Risque | Conséquence en Production | Sévérité (Critique/Haute/Moyenne) |
| :---- | :---- | :---- | :---- |
| VV-11 | Migration non idempotente / intégrité des positions | Un redémarrage transforme des positions `1m` légitimes en positions `AMBIGUOUS`, les rendant indisponibles pour leur stratégie. | Haute |
| VV-12 | Couverture de test de migration | La suite d’intégration ne vérifie pas que `init_db()` applique réellement la quarantaine lorsque les configurations ambiguës existent au moment de la migration. | Haute |

### VV-11 — Le backfill ne distingue pas les données historiques des positions `1m` légitimes

Le backfill s’exécute dès qu’au moins une ligne a `timeframe = '1m'` :

```sql
SELECT COUNT(*) FROM paper_positions WHERE timeframe = '1m'
```

`./backtest_engine/live/paper_trading/db_setup.py:716`.

Il change ensuite toute ligne `1m` ayant plusieurs configurations correspondantes :

```sql
UPDATE paper_positions p
SET timeframe = 'AMBIGUOUS'
WHERE p.timeframe = '1m'
  AND (... COUNT(DISTINCT c.timeframe) ...) > 1;
```

`./backtest_engine/live/paper_trading/db_setup.py:748` à `./backtest_engine/live/paper_trading/db_setup.py:756`.

`1m` est à la fois la valeur par défaut du nouveau schéma et une valeur métier valide. Le schéma ne possède aucun marqueur de migration permettant de savoir si une ligne `1m` vient de l’ancienne structure ou d’une position créée par la version actuelle. Toute exécution ultérieure de `init_db()` réapplique donc cette migration sur des données déjà migrées.

**Correction obligatoire** : rendre la migration one-shot et durable. Ajouter un état explicite de migration, par exemple une table de version de schéma ou une colonne transitoire nullable. N’appliquer le backfill et la quarantaine qu’aux lignes antérieures à la migration, puis enregistrer la version de migration dans la même transaction. Ne jamais utiliser une valeur métier valide comme indicateur de migration.

### VV-12 — Le test ne valide pas le chemin d’initialisation réel pour l’ambiguïté

Dans `./tests/test_db_setup.py`, le test appelle `init_db()` à la ligne 145. Les deux configurations contradictoires pour `MSFT` sont insérées seulement après cet appel, aux lignes 150 à 159. La quarantaine est ensuite simulée par deux requêtes SQL copiées dans le test, aux lignes 163 à 186.

Ce test confirme que la requête copiée produit le résultat attendu. Il ne confirme pas que `init_db()` exécute cette requête lorsque les configurations ambiguës existent déjà, et il ne couvre pas le redémarrage qui déclenche VV-11.

**Correction obligatoire** : préparer la table `paper_strategy_configs` avec une paire multi-timeframes avant l’appel à `init_db()`, exécuter `init_db()` une seconde fois, puis vérifier simultanément :

1. qu’une position historique non renseignée est mise en quarantaine ;
2. qu’une position `1m` créée après migration reste `1m` après le redémarrage ;
3. que le journal de version interdit un second backfill.

## Conclusion

La revendication de réussite des tests est confirmée : `605 passed, 1 skipped, 60 warnings`. VV-07 et VV-08 sont corrigés et disposent d’une exécution PostgreSQL réelle.

La correction de VV-10 n’est pas fiable : le mécanisme confond une donnée métier valide avec un état de migration et le test ne couvre pas le flux que le code de production exécute. Le déploiement reste bloqué jusqu’à l’ajout d’un état de migration durable et d’un test de redémarrage qui protège les positions `1m` légitimes.
