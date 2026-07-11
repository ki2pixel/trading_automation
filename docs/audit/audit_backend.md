**Note de “Goût” (Taste Score)** : 2/10

**Diagnostic de structure de données** : les états d’ordres, de positions et de conversion ne possèdent pas d’identité durable ni de verrou transactionnel commun.

**Analyse d’impact sur la compatibilité** : aucune rupture API nécessaire ; les corrections doivent durcir les invariants côté base et routage.

**Statut : REQUEST CHANGES — ne pas activer le routage réel.**

| Identifiant Anomalie | Catégorie de Risque | Conséquence en Production | Sévérité |
| :---- | :---- | :---- | :---- |
| C-01 | Idempotence Bybit inexistante | Double conversion ou registre financier faux après timeout/crash. | Critique |
| C-02 | Race condition portefeuille / panic close | Double vente, double mouvement de cash, coupe-circuit contournable. | Critique |
| C-03 | Contrôle pré-trade fail-open | Ordre Trading 212 envoyé avec une valorisation fictive à `1.0`. | Critique |
| C-04 | Prix Redis sans fraîcheur | Ordres exécutés sur un cours périmé après panne d’ingestion. | Critique |
| C-05 | Failsafe de clés optionnel | Un mauvais environnement peut router vers un compte live. | Critique |
| H-01 | Conversion dry-run destructive / marge incomplète | Profits marqués convertis sans conversion effective ; contrôle de marge contournable. | Haute |
| H-02 | Authentification et erreurs | Brute force non limité ; traceback exposé hors `DEBUG=true`. | Haute |
| H-03 | N+1 et I/O bloquant dans l’API async | Dégradation ou indisponibilité lors d’un panic close ou de plusieurs stratégies. | Haute |
| H-04 | Limites de capital non appliquées | `max_capital_bucket` donne une fausse garantie de risque. | Haute |
| H-05 | Horodatage et démarrage non fiables | Rapports décalés UTC/DST et démarrage sur schéma potentiellement invalide. | Haute |

Détails critiques :

- C-01 — [spot_router.py](/home/kidpixel/trading_automation_v2/backtest_engine/live/bybit/conversion/spot_router.py:160) marque l’ordre `FILLED` dès `retCode == 0`, puis draine l’accumulateur. Or Bybit précise que l’accusé de réception est asynchrone et qu’il faut confirmer l’état de l’ordre avant de le considérer exécuté. [Documentation Bybit](https://bybit-exchange.github.io/docs/v5/order/create)  
  L’ordre n’est persisté qu’après l’appel externe, dans [spot_router.py](/home/kidpixel/trading_automation_v2/backtest_engine/live/bybit/conversion/spot_router.py:276). Un crash entre le POST et ce log génère un nouvel UUID au redémarrage : aucune récupération n’est possible.

- C-02 — [db_setup.py](/home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/db_setup.py:519) ne garantit pas l’unicité `(asset, strategy_name)`. L’exécuteur lit sans verrou puis insère dans [signal_executor.py](/home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/signal_executor.py:371) et [signal_executor.py](/home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/signal_executor.py:677). En parallèle, le panic close supprime et recrédite le portefeuille dans [api.py](/home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/api.py:469).  
  Le flag kill switch n’est testé qu’avant la boucle : un ordre peut passer entre ce test et l’appel broker.

- C-03 — [client.py](/home/kidpixel/trading_automation_v2/backtest_engine/live/trading212/client.py:142) initialise une NAV et un prix de secours ; si le prix est indisponible, il poursuit avec `1.0` à la ligne 175. Le collar compare ce même prix à lui-même à la ligne 185 : contrôle nul. [controls.py](/home/kidpixel/trading_automation_v2/backtest_engine/live/controls.py:40) remplace également une NAV invalide par `100000`. Le routage réel peut donc suivre avec des données non vérifiées.

- C-04 — Les ingesteurs écrivent `price:*` sans expiration, par exemple [trading212/ingestor.py](/home/kidpixel/trading_automation_v2/backtest_engine/live/trading212/ingestor.py:111). L’exécuteur privilégie cette valeur sans timestamp ni TTL dans [signal_executor.py](/home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/signal_executor.py:516). Une panne d’ingestion laisse un prix ancien autoriser une entrée ou une sortie.

- C-05 — Les hashes de clés attendus restent facultatifs dans [trading212/config.py](/home/kidpixel/trading_automation_v2/backtest_engine/live/trading212/config.py:68) et [bybit/config.py](/home/kidpixel/trading_automation_v2/backtest_engine/live/bybit/config.py:58). Avec `T212_ENV=live`, l’absence des variables de hash ne bloque rien. Le modèle active en plus le routage réel par défaut dans [.env.template](/home/kidpixel/trading_automation_v2/.env.template:51).

Corrections obligatoires :

```sql
ALTER TABLE paper_positions
    ADD CONSTRAINT paper_positions_asset_strategy_key
    UNIQUE (asset, strategy_name);
```

```python
# Ne jamais inventer de valeur financière pour laisser passer un ordre.
if current_nav <= Decimal("0") or price <= Decimal("0"):
    raise PreTradeControlError("Fresh positive NAV and reference price are required")

if reference_price is None or reference_price <= Decimal("0"):
    raise PreTradeControlError("Fresh independent reference price is required")
```

```python
# Conversion : persister avant POST, puis seulement confirmer.
persist_order(conn, order, status=ConversionOrderStatus.PENDING)

response = self.client._request(...)
if response.json().get("retCode") == 0:
    order.status = ConversionOrderStatus.SUBMITTED
    persist_order(conn, order, status=order.status)
    return order

# Le drain est réservé au résultat broker explicitement `Filled`.
if reconciled_order.status is ConversionOrderStatus.FILLED:
    accumulator.drain(conn, reconciled_order.client_order_id)
```

Les autres corrections requises sont :

- verrouiller la position et la ligne de balance (`FOR UPDATE`), utiliser `DELETE ... RETURNING`, puis contrôler `rowcount` avant tout mouvement de cash ;
- rendre le kill switch une barrière atomique vérifiée juste avant chaque ordre broker ;
- stocker les prix Redis avec TTL et timestamp ; refuser tout prix au-delà du seuil de fraîcheur ;
- refuser le routage broker si les hashes attendus sont absents ou si le mode n’est pas explicitement `demo` ;
- ne pas drainer l’accumulateur en dry-run ; vérifier `available_balance` même quand `totalMaintenanceMargin == 0` ;
- ne pas exclure `/api/login` du rate limiting ; n’exposer traceback et message interne que si `DEBUG=true` ;
- remplacer les requêtes par stratégie par des lectures groupées ; supprimer le client Redis synchrone de [api.py](/home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/api.py:487) ;
- appliquer réellement `max_capital_bucket`, actuellement chargé mais absent du calcul d’allocation dans [signal_executor.py](/home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/signal_executor.py:574) ;
- migrer les timestamps financiers vers `TIMESTAMPTZ` et faire échouer le démarrage si [init_db](/home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/db_setup.py:667) échoue.

Contrôle effectué : `PYTHONPATH=. pytest -q tests/test_conversion_pipeline.py` → **12 passed**. Cette suite valide toutefois le comportement incorrect de dry-run qui draine l’accumulateur ; elle ne constitue pas une validation de sûreté.

Tests à ajouter avant toute activation : crash après POST broker, confirmation Bybit différée, double exécution engine/panic close, prix Redis expiré, absence de NAV/prix, hash de clé absent, et vérification que `max_capital_bucket` borne réellement l’ordre.