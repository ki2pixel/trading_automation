# Audit backend — Paper Trading

**Date** : 2026-07-15  
**Périmètre** : `backtest_engine/live/`, avec les points d’entrée `run_paper_trader.py`, les schémas paper trading et les tests associés.  
**Méthode** : revue statique ciblée des flux d’exécution, de persistance, des contrôles pré-trade, de la clôture d’urgence et des intégrations Trading 212 / Bybit. Aucun ordre broker ni modification de données n’a été exécuté.

## Statut

**Non conforme pour un paper trading fiable, et non autorisable pour le routage broker réel.**

Les défauts majeurs affectent directement l’intégrité du capital simulé, l’idempotence du routage réel optionnel, la propagation du kill switch et la cohérence des métriques. Le comportement actuel peut afficher une NAV, une exposition et des résultats de performance qui ne correspondent pas aux transactions paper exécutées.

## Note de goût

**2/10** — des abstractions de sécurité existent, mais leurs invariants ne sont pas reliés au modèle de données ni au flux transactionnel. La présence de contrôles sans source de vérité indépendante crée une sécurité cosmétique.

## Diagnostic de structure de données

Une même table de solde sert simultanément de ledger paper, de cache de solde broker et de base de sizing, sans séparation d’état ni invariant SQL de conservation du capital.

## Analyse d’impact sur la compatibilité

Les corrections proposées nécessitent une migration des tables paper et des contrats internes de routage. Elles ne doivent pas modifier rétroactivement les APIs publiques ; une phase de compatibilité est requise pour les données existantes et les tableaux de bord.

## Éléments contrôlés

- Boucle du moteur, calcul NAV, génération de signaux, sizing et écriture des transactions.
- Schéma PostgreSQL et migrations exécutées au démarrage.
- API FastAPI paper trading, contrôles de configuration et performance.
- Kill switch local, Redis Pub/Sub et annulation d’ordres broker.
- Client Trading 212, conversion Bybit et contrôles pré-trade.
- Tests unitaires présents dans `tests/`.

## Constats

| Identifiant Anomalie | Catégorie de Risque | Conséquence en Production | Sévérité (Critique/Haute/Moyenne) |
| :---- | :---- | :---- | :---- |
| PT-01 | Intégrité financière | Le cash paper dépensé est remplacé par le solde broker ; la NAV et le sizing utilisent des fonds virtuels non disponibles. | Critique |
| PT-02 | Concurrence / double dépense | Des stratégies ou workers peuvent consommer le même cash et rendre le solde négatif. | Critique |
| PT-03 | Idempotence du routage Trading 212 | Un crash entre l’appel broker et le commit peut produire un second ordre réel. | Critique |
| PT-04 | Kill switch distribué | L’API panic confirme un arrêt alors que d’autres workers et les ordres broker peuvent rester actifs. | Critique |
| PT-05 | Contrôle pré-trade | Le price collar est systématiquement neutralisé et ne bloque aucune cotation anormale. | Haute |
| PT-06 | Validation d’entrée | Des montants, prix ou paramètres non finis et incohérents peuvent être persistés. | Haute |
| PT-07 | Réconciliation broker | Un solde Bybit réel à zéro laisse un solde paper obsolète positif exploitable pour le sizing. | Haute |
| PT-08 | Pipeline de conversion | Les profits paper ne créditent jamais l’accumulateur ; le pipeline ne peut pas démarrer depuis les gains. | Haute |
| PT-09 | Disponibilité / reprise | Un ordre Bybit `SUBMITTED` introuvable reste bloquant et empêche les conversions ultérieures. | Haute |
| PT-10 | Performance / verrouillage | La clôture d’urgence exécute une requête de prix par position pendant qu’elle détient les verrous de portefeuille. | Haute |
| PT-11 | Invariants de persistance | Le schéma accepte soldes, quantités et prix invalides ; il ne borne pas les actions de transaction. | Haute |
| PT-12 | Isolation des stratégies | Deux timeframes d’une même stratégie et d’un même actif partagent une position ou violent l’unicité. | Haute |
| PT-13 | Exactitude du reporting | Les frais de buy sont exclus de certains PnL et métriques, surestimant la performance Bybit. | Haute |
| PT-14 | Disponibilité API | Des appels Redis synchrones sont exécutés dans des endpoints asynchrones et peuvent bloquer l’event loop. | Moyenne |
| PT-15 | Isolation des secrets | Le failsafe de hash ne valide pas strictement les clés démo / testnet. | Moyenne |
| PT-16 | Migration de données | Une migration de démarrage efface des données USDT en présence d’une ligne USDC sans sauvegarde ni journal de conflit. | Moyenne |

### PT-01 — Mélange du ledger paper et des soldes broker

**Invariant architectural violé** : le capital paper doit être indépendant du solde réel, sauf opération explicite de synchronisation et réconciliation documentée.

`SignalExecutor.update_portfolio_nav()` écrase `paper_portfolio_balance.cash_balance` avec `availableToTrade` Trading 212 ou `walletBalance` Bybit. Cette même colonne est débitée lors des achats paper et sert ensuite au sizing. Quand un client broker est initialisé mais que le routage réel est désactivé, le prochain cycle rétablit le cash dépensé dans la simulation.

**Défaillance** : une stratégie peut ouvrir des positions paper successives avec un capital qui a déjà été engagé. La NAV, les tailles Kelly et les limites d’exposition deviennent non fiables.

**Correction obligatoire** : séparer le ledger paper (`paper_cash_balance`, transactions, positions) du cache de réconciliation broker (`broker_available_cash`, timestamp, provenance). Interdire toute mise à jour de cash paper par polling broker.

### PT-02 — Sizing basé sur un snapshot de cash périmé

**Invariant architectural violé** : le sizing d’un achat doit être établi à partir du solde verrouillé et débité dans une même transaction atomique.

Les balances sont lues avant la boucle de configurations. Au moment de l’achat, la ligne est verrouillée mais le cash verrouillé n’est pas relu pour recalculer la quantité. Le schéma ne contient aucun `CHECK (cash_balance >= 0)`.

**Défaillance** : deux configurations ou deux processus peuvent chacun dimensionner sur le même solde initial. Le dernier débit rend le cash négatif.

**Correction obligatoire** : utiliser une transaction sérialisable ou un `SELECT ... FOR UPDATE` suivi d’un rechargement de la balance, calculer la quantité sous verrou, puis écrire position, transaction et balance dans le même commit. Ajouter des contraintes SQL positives et une contrainte de non-négativité du cash.

### PT-03 — Routage Trading 212 sans idempotence durable

**Invariant architectural violé** : tout ordre broker doit posséder un identifiant stable, durablement journalisé avant l’I/O réseau et récupérable après redémarrage.

Le `client_order_id` est généré au moment du routage, n’est ni persisté dans `paper_transactions` ni envoyé dans le payload Trading 212. Le verrou Redis est donc associé à un UUID éphémère. Après un crash entre l’acceptation de l’ordre par Trading 212 et le commit PostgreSQL, le cycle suivant génère une nouvelle clé et peut soumettre un doublon.

**Défaillance** : double achat ou double vente réel, sans piste d’audit permettant une récupération déterministe.

**Correction obligatoire** : introduire un journal d’ordres durable avec état (`PENDING`, `SUBMITTED`, `ACKNOWLEDGED`, `FILLED`, `FAILED`), un identifiant client stable, la réponse broker et un mécanisme de récupération Trading 212 avant tout rejeu. Ne marquer une transaction paper comme exécutée qu’après la réconciliation du journal.

### PT-04 — Endpoint panic incomplet et non distribué

**Invariant architectural violé** : l’arrêt d’urgence doit être distribué, durable et annuler les ordres réels avant de confirmer le succès.

`POST /api/control/panic` définit uniquement le flag mémoire puis clôture les positions paper. Il n’écrit pas `trading:suspended` dans Redis et n’appelle pas `KillSwitchListener.trigger_kill()`, lequel propage le flag et annule les ordres Bybit et Trading 212.

**Défaillance** : dans un déploiement multi-worker, un worker continue d’évaluer des signaux. Quand le routage broker est actif, les ordres ouverts ne sont pas annulés malgré une réponse API de succès.

**Correction obligatoire** : centraliser panic et listener sur une commande idempotente unique : persistance du statut, publication Redis, attente bornée des annulations broker et résultat détaillé par broker. Réserver le succès HTTP aux états confirmés ou signaler explicitement les annulations incomplètes.

### PT-05 — Price collar sans référence indépendante

**Invariant architectural violé** : le prix de l’ordre et le prix de référence doivent venir de sources ou d’instants indépendants.

Trading 212 et la conversion Bybit appellent `PreTradeController.check_limits()` avec `price` et `reference_price` égaux. L’écart calculé est donc toujours nul.

**Défaillance** : le contrôle de 3 % n’interdit ni un prix stale, ni une cotation erronée, ni un mouvement violent.

**Correction obligatoire** : fournir un prix de référence horodaté et indépendant (dernier prix validé, NBBO ou médiane de sources), imposer une fraîcheur maximale et refuser l’ordre si la référence n’existe pas.

### PT-06 — Configurations sans bornes financières

**Invariant architectural violé** : les entrées financières doivent être finies, positives et cohérentes avant leur persistance.

Le modèle `ConfigUpdate` accepte des `float` sans validation explicite des valeurs négatives, `NaN`, infinies ou des relations entre `initial_capital_bucket`, `max_capital_bucket` et `max_entry_price`.

**Défaillance** : une configuration invalide peut annuler les protections de sizing, provoquer des opérations incohérentes ou contaminer la base.

**Correction obligatoire** : remplacer les valeurs financières API par `Decimal`, exiger des bornes strictement positives et valider `initial_capital_bucket <= max_capital_bucket`, ainsi que les plafonds dépendants de la stratégie.

### PT-07 — Réconciliation Bybit à zéro ignorée

**Invariant architectural violé** : zéro est une valeur broker valide et doit remplacer tout solde précédent.

Le cash Bybit n’est mis à jour que si `bybit_balance > 0`.

**Défaillance** : un compte broker vidé conserve un cash local positif et les contrôles pré-trade autorisent des tailles sans financement réel.

**Correction obligatoire** : remplacer le test par une validation de présence et de finitude de la réponse broker, puis persister aussi la valeur zéro avec son timestamp de réconciliation.

### PT-08 — Accumulateur de conversion jamais crédité par les profits paper

**Invariant architectural violé** : les événements de profit réalisés doivent alimenter transactionnellement les mécanismes qui en dépendent.

Aucun flux de clôture de position ne déclenche `AccumulatorBuffer.deposit()`. Le routeur Bybit lit donc un accumulateur qui reste à zéro.

**Défaillance** : la conversion des profits paper vers EUR ne peut pas être déclenchée automatiquement.

**Correction obligatoire** : déposer le profit net éligible dans l’accumulateur dans la même transaction que la vente et la mise à jour de `secured_balance`, avec une référence unique à la transaction de vente.

### PT-09 — Récupération d’ordre de conversion bloquante

**Invariant architectural violé** : un ordre non retrouvé doit finir dans un état terminal ou expirer sous délai, jamais bloquer le pipeline indéfiniment.

Un ordre `SUBMITTED` absent de `/v5/order/realtime` et `/v5/order/history` reste `SUBMITTED`, sauf cas où son état antérieur est `PENDING`. Au cycle suivant, ce même ordre est repris avant toute nouvelle conversion.

**Défaillance** : une réponse API incohérente ou une rétention broker rend le pipeline définitivement indisponible.

**Correction obligatoire** : ajouter un délai de récupération, une transition contrôlée vers `UNKNOWN` ou `FAILED_RECONCILIATION`, une alerte opérateur et une procédure manuelle de résolution. Les nouveaux ordres restent suspendus seulement pendant cette fenêtre bornée.

### PT-10 — N+1 dans la clôture d’urgence

**Invariant architectural violé** : un chemin d’urgence ne doit pas exécuter de lecture par position sous verrous de portefeuille.

`panic_close_all()` verrouille les balances et positions, puis interroge `live_prices` individuellement pour chaque position.

**Défaillance** : la durée de la transaction et des verrous croît linéairement avec le portefeuille. Des signaux concurrentiels sont bloqués pendant une phase d’urgence déjà fragile.

**Correction obligatoire** : charger tous les prix requis en une requête avec `LOWER(ticker) = ANY($1)`, construire une map locale puis fermer les positions en batch. Définir une politique explicite quand aucun prix frais n’est disponible.

### PT-11 — Schéma sans invariants financiers

**Invariant architectural violé** : PostgreSQL doit empêcher les états financiers invalides indépendamment du code applicatif.

`paper_portfolio_balance`, `paper_positions`, `paper_transactions`, `conversion_accumulator` et `conversion_audit_log` n’imposent pas les bornes critiques. Les actions de transaction ne sont pas limitées à un ensemble fermé. Après ajustement de quantité pour les frais, le flux journalise une quantité `<= 0` mais ne s’arrête pas avant les opérations suivantes.

**Défaillance** : un bug applicatif ou une entrée API incohérente peut persister du cash négatif, une quantité nulle ou négative, un prix invalide ou une action non reconnue.

**Correction obligatoire** : ajouter des contraintes `CHECK` sur les montants, prix, quantités, statuts et actions ; rejeter immédiatement une quantité non positive après tout arrondi ou ajustement ; ajouter des tests d’intégration PostgreSQL qui tentent ces insertions.

### PT-12 — Clé de position incompatible avec les configurations multi-timeframes

**Invariant architectural violé** : l’identité d’une position doit couvrir toutes les dimensions qui différencient les stratégies autorisées.

`paper_strategy_configs` autorise `(strategy_name, asset, timeframe)` alors que `paper_positions` impose seulement `(asset, strategy_name)`. L’exécuteur construit aussi ses positions actives sans timeframe.

**Défaillance** : les configurations `15m` et `1h` partagent une même position ou déclenchent une violation de contrainte lors de l’entrée.

**Correction obligatoire** : ajouter `timeframe` à la position, à son index unique et aux requêtes d’exécution. Migrer les positions existantes par jointure sur la configuration réellement active ou les placer en état de revue manuelle si l’association est ambiguë.

### PT-13 — Frais incohérents dans les PnL et métriques

**Invariant architectural violé** : toutes les projections de PnL doivent utiliser le même coût complet d’exécution que le ledger.

La mise à jour de `paper_positions.pnl` ne retire pas les frais. Les métriques API reconstruisent les coûts d’entrée avec `qty * price`, alors que les achats Bybit enregistrent les frais dans `paper_transactions.total_value`. Les calculs convertissent aussi les valeurs en `float`.

**Défaillance** : les KPI Bybit, le profit factor et les courbes affichées surestiment le PnL et peuvent produire des écarts de précision.

**Correction obligatoire** : stocker explicitement les frais et la devise dans les transactions, calculer le coût complet à partir du ledger et garder `Decimal` jusqu’à la sérialisation API. Créer des cas de test avec buy/sell, frais, ventes partielles et arrondis.

### PT-14 — I/O Redis bloquante dans FastAPI

**Invariant architectural violé** : les endpoints async ne doivent pas appeler un client réseau synchrone sur l’event loop.

Les endpoints de cache et le middleware de rate limiting utilisent `get_redis_client()` et des appels synchrones. Certains échecs sont supprimés par `except Exception: pass`.

**Défaillance** : une indisponibilité Redis peut immobiliser l’event loop jusqu’au timeout socket et masquer l’origine de la dégradation.

**Correction obligatoire** : utiliser un client Redis async dans les routes et middleware FastAPI, avec timeout explicite et comportement de repli journalisé. Ne pas supprimer les exceptions de transport.

### PT-15 — Failsafe incomplet des clés broker démo/test

**Invariant architectural violé** : le hash attendu doit être obligatoire et validé dans chaque environnement authentifié.

Les validations Bybit et Trading 212 contrôlent le hash live, mais l’environnement non-live ne requiert ni ne compare systématiquement un hash démo/testnet.

**Défaillance** : une clé erronée peut être chargée en test, et le contrôle de séparation d’environnements est incomplet.

**Correction obligatoire** : exiger un hash attendu distinct pour chaque mode authentifié, refuser une configuration incomplète et tester les couples clé/environnement acceptés et rejetés.

### PT-16 — Migration USDT vers USDC destructive au démarrage

**Invariant architectural violé** : une migration de données ne doit supprimer aucune donnée métier sans sauvegarde, journal d’arbitrage et validation opérateur.

La migration exécutée par `init_db()` supprime des lignes USDT dès qu’une ligne USDC correspondante existe, notamment pour les prix, chandeliers et configurations. Elle n’est pas versionnée et s’exécute à chaque démarrage.

**Défaillance** : perte silencieuse de séries historiques ou de configurations, sans possibilité d’audit ni de restauration.

**Correction obligatoire** : retirer la suppression du chemin de démarrage ; créer une migration versionnée, transactionnelle, avec table de conflits et export de sauvegarde. Exiger une validation explicite avant purge.

## Contrôles existants valides mais insuffisants

- L’application principale applique un cookie de session signé HMAC, un middleware CSRF et des en-têtes de sécurité.
- Les requêtes SQL observées sont paramétrées.
- Le listener Redis du kill switch est configuré avec keepalive et health check.
- Le routeur de conversion Bybit persiste un ordre avant son appel réseau et utilise un identifiant stable pour Bybit.

Ces protections ne corrigent pas les défauts de cohérence du ledger, de reprise Trading 212 et de panic HTTP. L’API du module paper trading dépend en outre des middlewares installés par `run_paper_trader.py` ; elle ne garantit pas seule l’authentification ni le CSRF.

## Couverture de tests et lacunes

Les tests inspectés sont principalement des tests unitaires avec mocks. Ils ne démontrent pas l’intégrité transactionnelle PostgreSQL ni la récupération réelle des brokers.

| Case ID | Input / Precondition | Perspective (Equivalence / Boundary) | Expected Result | Notes |
|--------|----------------------|---------------------------------------|-----------------|-------|
| TC-C-01 | Deux achats concurrents, même source et cash insuffisant | Limite — concurrence / solde à 0 | Un seul achat est validé ; cash final non négatif | Test d’intégration PostgreSQL multi-connexions |
| TC-C-02 | Crash après acceptation Trading 212, avant commit local | Erreur — reprise | Aucun second POST ; ordre existant réconcilié | Journal d’ordres persistant requis |
| TC-C-03 | Panic depuis un worker dans un déploiement à deux workers | Équivalence — distribué | Redis suspend les deux workers et les ordres broker sont annulés | Vérifier la réponse partielle en cas d’échec broker |
| TC-C-04 | Prix ordre à +3.01 % de la référence fraîche | Limite — +1 | Rejet du contrôle price collar | Référence indépendante obligatoire |
| TC-C-05 | `NaN`, `inf`, montant négatif, zéro, bucket inversés | Limite — NULL / 0 / ±1 | Validation API rejetée sans persistance | Autant de cas d’erreur que de cas nominaux |
| TC-C-06 | Solde Bybit broker égal à 0 | Limite — 0 | Cache broker mis à 0 ; aucun sizing financé par ancien solde | Ne modifie pas le ledger paper |
| TC-C-07 | Profit Bybit net positif puis seuil atteint | Équivalence — workflow | Dépôt unique dans accumulateur et conversion déclenchable | Référence transaction unique |
| TC-C-08 | Conversion `SUBMITTED` absente des deux endpoints après TTL | Limite — timeout | État terminal / alerte ; pipeline ne reste pas bloqué indéfiniment | Vérifier idempotence de la transition |
| TC-C-09 | Panic avec 0, 1 et N positions | Limite — vide / minimum / maximum | Une seule lecture groupée des prix ; transaction bornée | Mesurer le nombre de requêtes |
| TC-C-10 | Position même actif / stratégie sur 15m et 1h | Équivalence — identité composée | Deux positions isolées et deux sorties indépendantes | Migration de clé unique |
| TC-C-11 | Buy Bybit, sell partiel puis sell final avec frais | Équivalence / limite | PnL et métriques égaux au ledger Decimal | Aucun `float` avant la réponse HTTP |
| TC-C-12 | Conflit USDT et USDC en migration | Erreur — conflit | Aucune suppression automatique ; conflit journalisé | Migration hors démarrage |

## Plan de remédiation priorisé

### Bloquant avant tout routage réel

1. Séparer définitivement ledger paper et cache de réconciliation broker ; corriger PT-01, PT-02 et PT-07 ensemble.
2. Ajouter le journal d’ordres Trading 212 et la récupération après crash ; corriger PT-03.
3. Centraliser le kill switch HTTP/PubSub/broker ; corriger PT-04.
4. Introduire les contraintes SQL et les validations API ; corriger PT-06 et PT-11.
5. Mettre en place les tests d’intégration des cas TC-C-01 à TC-C-06.

### Haute priorité avant confiance dans les résultats paper

1. Rendre la référence du price collar réellement indépendante.
2. Corriger l’identité des positions avec le timeframe.
3. Unifier le ledger de frais et les métriques de performance.
4. Connecter transactionnellement les profits au pipeline de conversion et borner sa récupération.
5. Supprimer le N+1 de panic close.

### Dette à traiter avant le prochain déploiement

1. Remplacer Redis synchrone par le client async dans FastAPI et journaliser les erreurs de cache.
2. Compléter la validation des hashes de clés non-live.
3. Extraire la migration USDT/USDC dans un mécanisme versionné et non destructif.

## Commandes de vérification

Les commandes ci-dessous doivent être exécutées après l’implémentation des corrections :

```bash
PYTHONPATH=. pytest -q tests/test_signal_executor.py tests/test_paper_trading_engine.py tests/test_paper_trading_auth.py tests/test_api_caching.py tests/test_pre_trade_controls_extended.py tests/test_conversion_pipeline.py
PYTHONPATH=. pytest -q tests/
```

**Résultat de l’audit** : la première commande ciblée a été exécutée avec succès : **52 tests passés**. Elle ne couvre pas les scénarios d’intégration critiques listés dans ce rapport.

Les nouveaux tests d’intégration PostgreSQL doivent être exécutés contre une base dédiée, isolée et jetable. La couverture de branche des flux de capital, de reprise d’ordre et de kill switch doit être mesurée avec :

```bash
PYTHONPATH=. pytest --cov=backtest_engine.live.paper_trading --cov=backtest_engine.live.trading212 --cov=backtest_engine.live.bybit.conversion --cov-branch tests/
```

## Conclusion

Le système possède des briques de sécurité, mais son modèle d’état ne protège pas les invariants financiers fondamentaux. Le correctif ne consiste pas à ajouter des conditions autour du code existant : il faut restaurer une source de vérité transactionnelle, des identifiants d’ordres persistants et un arrêt d’urgence unique. Tant que PT-01 à PT-04 ne sont pas corrigés et couverts par des tests d’intégration, le routage réel doit rester désactivé.
