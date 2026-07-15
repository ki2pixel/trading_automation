# Vérification VV-10 — Backfill one-shot et résistance au redémarrage

**Date** : 2026-07-15  
**Périmètre** : migration des timeframes de `paper_positions`, exécution répétée de `init_db()` et tests PostgreSQL associés.

## Verdict

**Validation partielle.** Le correctif empêche désormais qu’un redémarrage réapplique le backfill sur les positions créées après une migration réussie. Les scénarios de schéma vierge, de migration depuis l’ancien schéma et de redémarrage sont exécutés avec PostgreSQL réel et réussissent.

Le correctif n’est pas une réparation complète des bases déjà passées par la version précédente de la migration. La présence de la colonne `timeframe` est utilisée comme unique marqueur de version. Toute base ayant déjà reçu cette colonne et un backfill historique arbitraire est ignorée par la nouvelle migration, sans audit ni quarantaine des associations déjà attribuées par l’ancien `LIMIT 1`.

## Résultats d’exécution

| Commande | Résultat |
| :---- | :---- |
| `PYTHONPATH=. pytest -v tests/test_db_setup.py` | **2 succès** en 9,01 s. |
| `PYTHONPATH=. pytest -q tests/` | **605 succès, 1 ignoré, 60 avertissements** en 71,87 s. |

Les 60 avertissements relèvent des API dépréciées Pandas et websockets ainsi que d’API Optuna expérimentales. Aucun échec ni crash natif n’a été observé.

## Correctif confirmé

### One-shot sur les schémas historiques non migrés

La migration vérifie maintenant l’existence de `paper_positions.timeframe` avant de lancer l’`ALTER TABLE` :

```sql
SELECT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'paper_positions'
      AND column_name = 'timeframe'
);
```

`./backtest_engine/live/paper_trading/db_setup.py:523` à `./backtest_engine/live/paper_trading/db_setup.py:532`.

Le backfill est conditionné par `run_timeframe_backfill`, calculé avant l’ajout de la colonne :

- ajout conditionnel de la colonne : `./backtest_engine/live/paper_trading/db_setup.py:534` ;
- exécution one-shot : `./backtest_engine/live/paper_trading/db_setup.py:724` à `./backtest_engine/live/paper_trading/db_setup.py:767`.

Ainsi, une position `1m` créée après migration n’est pas retraitée à l’appel suivant de `init_db()`.

### Tests PostgreSQL de redémarrage

Le test `./tests/test_db_setup.py:103` prépare un ancien schéma, fournit les configurations au moment de `init_db()`, crée ensuite une position `1m` légitime, puis réexécute `init_db()` :

- configurations disponibles lors du backfill : `./tests/test_db_setup.py:141` à `./tests/test_db_setup.py:153` ;
- insertion post-migration : `./tests/test_db_setup.py:170` à `./tests/test_db_setup.py:178` ;
- simulation de redémarrage : `./tests/test_db_setup.py:183` à `./tests/test_db_setup.py:188` ;
- conservation vérifiée de `1m` : `./tests/test_db_setup.py:190` à `./tests/test_db_setup.py:204`.

Ce chemin valide bien la régression précédemment identifiée : le redémarrage ne remplace plus une position `1m` légitime par `AMBIGUOUS`.

## Anomalie résiduelle de déploiement

| Identifiant Anomalie | Catégorie de Risque | Conséquence en Production | Sévérité (Critique/Haute/Moyenne) |
| :---- | :---- | :---- | :---- |
| VV-13 | Upgrade de données / traçabilité de migration | Les bases ayant déjà exécuté l’ancien backfill arbitraire conservent des timeframes possiblement erronés, sans possibilité de détection automatique. | Haute |

### VV-13 — Une colonne existante n’est pas une version de migration fiable

La version précédente avait déjà ajouté `timeframe` et pouvait renseigner un timeframe arbitraire avec `LIMIT 1`. Après mise à jour vers le mécanisme actuel, cette colonne existe déjà. La condition :

```python
run_timeframe_backfill = not cur.fetchone()[0]
```

`./backtest_engine/live/paper_trading/db_setup.py:532`, vaut alors `False`. La nouvelle logique de déduction unique et de quarantaine n’est jamais appliquée aux enregistrements existants.

Les positions auparavant associées au mauvais timeframe restent indiscernables de positions valides. Le mécanisme one-shot protège la stabilité future, mais il ne répare ni ne signale l’historique potentiellement corrompu.

**Correction requise avant d’affirmer une migration complète des déploiements existants** : ajouter une migration versionnée, distincte du test d’existence de colonne. Cette migration doit identifier les positions créées ou modifiées par la version historique, les marquer pour revue lorsque l’association ne peut pas être prouvée de manière unique, et inscrire sa version dans un registre de migrations transactionnel.

## Conclusion

Le bug de réécriture au redémarrage est corrigé pour les migrations exécutées avec la version actuelle. Les tests PostgreSQL ciblés et la suite complète sont validés.

L’état actuel est acceptable pour une nouvelle installation et pour une migration directe depuis le schéma sans colonne `timeframe`. Il n’est pas suffisant pour certifier l’intégrité des bases déjà migrées par la version antérieure contenant le backfill `LIMIT 1`. VV-13 doit être traité avant d’autoriser une mise à niveau de production sans revue des positions existantes.
