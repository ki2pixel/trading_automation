# Vérification VV-13 — Réparation legacy versionnée

**Date** : 2026-07-15  
**Périmètre** : versionnage PostgreSQL, réparation des associations timeframe héritées et test d’intégration de migration.

## Verdict

**Validation partielle, déploiement non autorisable.**

Le mécanisme de version 2 est transactionnel avec le reste de `init_db()` et la réparation est exécutée sur une base PostgreSQL réelle. La suite complète réussit avec **606 succès, 1 test ignoré et 60 avertissements**.

Le mécanisme de réparation est cependant destructif envers les positions légitimes qui existaient déjà dans une base sans enregistrement de version 2. Il met en quarantaine toutes les positions liées à une stratégie ayant plusieurs configurations de timeframe, quel que soit leur timeframe courant. La migration ne peut pas prouver qu’une position donnée provient de l’ancien `LIMIT 1`; elle détruit donc également une association valide `5m`, `15m` ou `1h` en la remplaçant par `AMBIGUOUS`.

## Résultats d’exécution

| Commande | Résultat |
| :---- | :---- |
| `PYTHONPATH=. pytest -v tests/test_db_setup.py` | **3 succès** en 11,90 s. |
| `PYTHONPATH=. pytest -q tests/` | **606 succès, 1 ignoré, 60 avertissements** en 76,31 s. |

Les avertissements proviennent d’API dépréciées Pandas et websockets, ainsi que d’API Optuna expérimentales. Aucun échec et aucun crash natif n’ont été observés.

## Éléments confirmés

### Migration versionnée transactionnelle

`schema_version` est créée puis interrogée avant l’application de la migration :

- création : `./backtest_engine/live/paper_trading/db_setup.py:431` à `./backtest_engine/live/paper_trading/db_setup.py:438` ;
- lecture de la version 2 : `./backtest_engine/live/paper_trading/db_setup.py:440` à `./backtest_engine/live/paper_trading/db_setup.py:442` ;
- enregistrement idempotent de la version : `./backtest_engine/live/paper_trading/db_setup.py:835` à `./backtest_engine/live/paper_trading/db_setup.py:840` ;
- commit final unique : `./backtest_engine/live/paper_trading/db_setup.py:842`.

En cas d’échec avant le commit, les changements de schéma et de données de la transaction sont annulés. L’intention de rendre la réparation one-shot est correctement matérialisée.

### Réparation d’une base héritée explicitement simulée

Le test `./tests/test_db_setup.py:223` construit une base ayant déjà la colonne `timeframe`, sans version 2, puis vérifie :

- réattribution unique de `AAPL` vers `15m` ;
- quarantaine de `MSFT` vers `AMBIGUOUS` ;
- écriture de la version 2.

Cette couverture confirme le scénario précis préparé par le test.

## Anomalie bloquante

| Identifiant Anomalie | Catégorie de Risque | Conséquence en Production | Sévérité (Critique/Haute/Moyenne) |
| :---- | :---- | :---- | :---- |
| VV-14 | Intégrité des positions / migration destructive | Une position valide ayant une stratégie multi-timeframes est retirée de son timeframe effectif sans preuve qu’elle est corrompue. | Critique |
| VV-15 | Auditabilité / couverture de migration | Aucune conservation du timeframe antérieur ni test d’une position multi-timeframe déjà valide. La revue manuelle ne peut pas reconstruire l’association supprimée. | Haute |

### VV-14 — Quarantaine indistincte des positions légitimes et corrompues

La réparation sélectionne toute position associée à plus d’une configuration :

```sql
WHERE (
    SELECT COUNT(DISTINCT c.timeframe)
    FROM paper_strategy_configs c
    WHERE c.asset = p.asset AND c.strategy_name = p.strategy_name
) > 1;
```

`./backtest_engine/live/paper_trading/db_setup.py:797` à `./backtest_engine/live/paper_trading/db_setup.py:818`.

Le prédicat ne teste ni la provenance de la ligne, ni son ancienneté, ni si son `timeframe` actuel correspond déjà exactement à l’une des configurations. Une position valide `MSFT / test_dual_tf / 1h` répond au même prédicat qu’une position corrompue par l’ancien `LIMIT 1` et est remplacée par `AMBIGUOUS`.

Cette mutation casse l’invariant PT-12 : une position valide doit conserver l’identité `(asset, strategy_name, timeframe)` qui permet à son exécuteur de la retrouver. Le résultat est une position orpheline et une exposition potentiellement non réconciliée par la stratégie active.

**Correction obligatoire** : la migration ne doit pas modifier automatiquement les associations multi-timeframes déjà présentes. Elle doit inscrire ces lignes dans une table de revue dédiée, avec l’identifiant de position, le timeframe original, les timeframes candidats, le motif et la date d’audit. Le timeframe de la position doit rester inchangé jusqu’à la décision opérateur. Seules les correspondances prouvées uniques peuvent être réattribuées automatiquement.

### VV-15 — Perte de l’information requise pour la revue manuelle

La réparation effectue :

```sql
UPDATE paper_positions p
SET timeframe = 'AMBIGUOUS'
```

à `./backtest_engine/live/paper_trading/db_setup.py:810` à `./backtest_engine/live/paper_trading/db_setup.py:818`.

Aucune table d’audit, aucune colonne d’ancien timeframe et aucun export ne préservent l’état précédent. Le seul signal est un `print`, non structuré et non durable. Une fois le commit effectué, l’opérateur ne sait plus si la position était auparavant `5m`, `15m` ou `1h`.

Le test `./tests/test_db_setup.py:223` ne crée que des positions volontairement corrompues. Il ne couvre pas le cas nécessaire d’une position existante, déjà valide et associée à une stratégie multi-timeframes.

**Correction obligatoire** : créer et tester une table de quarantaine/audit transactionnelle avant toute mutation, ou ne pas modifier `paper_positions` et exposer les anomalies via cette table. Ajouter un test PostgreSQL où une position `1h` légitime coexiste avec deux configurations et vérifier que sa valeur demeure `1h` après réparation.

## Conclusion

La réussite `606 passed, 1 skipped, 60 warnings` est confirmée. Le versionnage et le chemin de réparation synthétique fonctionnent comme implémentés.

La sécurité financière et l’intégrité de portefeuille exigent de traiter les données ambigües sans détruire leur dernier état connu. VV-14 et VV-15 bloquent donc la validation de déploiement de la réparation automatique actuelle.
