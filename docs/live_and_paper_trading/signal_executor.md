# SignalExecutor — Moteur d'Évaluation et d'Exécution

**TL;DR**: `SignalExecutor` est le cœur métier du Paper Trader. Il orchestre l'évaluation des signaux stratégiques, le calcul du NAV, l'exécution des entrées/sorties, les Pre-Trade Controls et la protection des micro-positions Trading 212; le tout avec I/O batchée (Redis MGET, SQL ANY, executemany) pour éviter les requêtes N+1.

Vous avez un moteur de Paper Trading qui tourne en boucle toutes les 60 secondes. À chaque cycle, il doit évaluer 16 stratégies sur plusieurs actifs, calculer le NAV, vérifier les positions ouvertes, exécuter des ordres. Sans une gestion rigoureuse des accès I/O, chaque cycle déclenche des centaines de requêtes SQL individuelles — une catastrophe de performance en production.

`SignalExecutor` a été conçu pour résoudre ce problème en amont.

---

## Architecture et Responsabilités

Le module applique une séparation stricte entre l'orchestration de boucle (`engine.py`) et la logique métier pure. `SignalExecutor` ne connaît rien du scheduler, des connexions Redis/PostgreSQL ou des clients brokers au niveau infrastructure; il reçoit tout par injection.

```
PaperTradingEngine (engine.py)
    │
    ├── Cycle 60s ──► SignalExecutor.evaluate_and_execute_strategies(conn)
    │                      │
    │                      ├── 1. Kill Switch check (Redis)
    │                      ├── 2. Fetch configs + positions + balances (batch SQL)
    │                      ├── 3. Fetch candles 1m (batch SQL, 5000 rows/ticker)
    │                      ├── 4. Resample → strategy timeframe
    │                      ├── 5. Run strategy logic (VectorBT)
    │                      ├── 6. Evaluate Entry/Exit signals
    │                      ├── 7. Pre-Trade Controls validation
    │                      ├── 8. Execute BUY/SELL (DB + optional T212 routing)
    │                      └── 9. Log evaluation (paper_evaluations)
    │
    └── Cycle 60s ──► SignalExecutor.update_portfolio_nav(conn)
                           │
                           ├── 1. Fetch broker balances (T212 API / Bybit API)
                           ├── 2. Fetch position prices (Redis MGET batch)
                           ├── 3. SQL fallback (ANY() batch)
                           ├── 4. Compute PnL (vectorized)
                           └── 5. Batch UPDATE positions (executemany)
```

---

## Pipeline de Mise à Jour du NAV

### ❌ Approche naïve (N+1 queries)

```python
# Pour chaque position, une requête SQL + une requête Redis
for pos in positions:
    price = redis.get(f"price:{pos.asset}")  # N requêtes Redis
    if not price:
        cur.execute("SELECT price FROM live_prices WHERE ticker = %s", (pos.asset,))  # N requêtes SQL
    cur.execute("UPDATE paper_positions SET current_price = %s WHERE id = %s", (price, pos.id))  # N requêtes SQL
```

### ✅ Approche batchée (3 round-trips total)

```python
# 1. Un seul MGET Redis pour tous les tickers
redis_prices = redis_client.mget([f"price:{t}" for t in tickers])

# 2. Une seule requête SQL ANY() pour les tickers manquants
cur.execute("SELECT ticker, price, updated_at FROM live_prices WHERE ticker = ANY(%s)", (missing_tickers,))

# 3. Un seul executemany pour toutes les mises à jour
cur.executemany("UPDATE paper_positions SET current_price = %s, pnl = %s WHERE id = %s", position_updates)
```

**Pipeline de fallback des prix**:

```
Redis (MGET batch, TTL 3min)
    │ échec ou stale
    ▼
PostgreSQL live_prices (ANY() batch, fraîcheur 3min)
    │ échec ou stale
    ▼
Dernier prix connu (paper_positions.current_price)
```

---

## Boucle d'Évaluation des Stratégies

### Flux d'un cycle d'évaluation

1. **Kill Switch**: Vérification Redis du statut de suspension avant toute évaluation.
2. **Batch fetching**: Configurations actives, positions ouvertes, balances et bougies 1m sont chargées en 4 requêtes SQL au lieu de N×M.
3. **Filtrage**: Élimination des configs sur marchés fermés (`is_market_open()`).
4. **Warmup check**: Minimum 10 bougies + lookback paramétrique déduit des `indicator_params`.
5. **Resampling**: Agrégation 1m → timeframe cible (5m, 15m, 30m, 45m, 1h).
6. **Exécution stratégie**: Appel à `StrategyRegistry.get(name).run_function()` avec `compute_full_metrics=False`.
7. **Déduplication temporelle**: Skip si le timestamp de la dernière bougie close n'a pas changé (`self._last_eval_timestamps`).
8. **Évaluation des signaux**: Extraction de `long_entry` / `long_exit` depuis la bougie close.

### Calcul du capital alloué (Kelly Sizing)

```python
kelly_size_cash = total_nav * kelly_weight
allocated_cash = min(
    kelly_size_cash,
    cash_balance,              # Liquidités disponibles
    initial_capital_bucket,    # Capital initial de la stratégie
    max_capital_bucket         # Plafond de capital
)
qty = allocated_cash / current_price
qty = round(qty, qty_precision)  # Précision fractionnaire configurable
```

Si `total_buy_cost + fee > cash_balance`, la quantité est réajustée:
```python
qty = cash_balance / (current_price * (1.0 + fee_rate))
```

---

## Exécution des Ordres

### Entrée (BUY)

```
Signal ENTRY détecté
    │
    ├── Rejet si current_price > max_entry_price
    ├── Calcul Kelly sizing → allocated_cash → qty
    ├── Pre-Trade Controls (PTC): limites volumétriques, notionnelles, price collars
    │   └── REJECTED si échec
    ├── T212 Routing (si T212_PAPER_ROUTING_ENABLED=true):
    │   ├── Résolution ticker (Trading212TickerResolver)
    │   ├── Placement ordre marché (idempotent, UUID v4 36 chars)
    │   └── FAILED si erreur API
    └── Persistance:
        ├── INSERT paper_positions RETURNING id (intra-cycle dedup)
        ├── UPDATE paper_portfolio_balance (cash - coût total)
        ├── INSERT paper_transactions (BUY)
        ├── Injection dans active_positions (cache local)
        └── Invalidation cache Redis perf_metrics:{asset}
```

### Sortie (SELL)

```
Signal EXIT ou ExitRule triggered
    │
    ├── Évaluation BrokerSimulator (brackets, trailing stops, safety stops)
    ├── Pre-Trade Controls (PTC)
    │   └── REJECTED si échec
    ├── Protection micro-position Trading 212:
    │   ├── Calcul max_sellable = real_qty - micro_qty
    │   ├── sell_qty = min(paper_qty, max_sellable)
    │   └── Skip si sell_qty ≤ 0
    ├── T212 Routing (idempotent)
    └── Persistance:
        ├── DELETE paper_positions RETURNING id (vérification existence)
        ├── UPDATE paper_portfolio_balance (cash + net_revenue)
        ├── INSERT paper_transactions (SELL)
        ├── Retrait de active_positions (cache local)
        ├── Auto-cicatrisation: bootstrap() si micro-position disparue
        └── Invalidation cache Redis perf_metrics:{asset}
```

---

## Protection des Micro-Positions (Trading 212)

Le routage d'ordres réels sur compte démo expose un risque critique: liquider la micro-position de tracking (0.0001 actions) indispensable au fonctionnement de l'API Trading 212.

| Mécanisme | Déclencheur | Action |
|---|---|---|
| **Écrêtage préventif** | Avant tout ordre SELL réel | `max_sellable = real_qty - micro_qty` |
| **Auto-cicatrisation** | Post-commit EXIT | `bootstrapper.bootstrap()` si micro-position disparue |

```python
# Le système ne vend jamais la totalité des parts réelles
max_sellable = real_qty - micro_qty   # ex: 10.0001 - 0.0001 = 10.0
sell_qty = min(paper_qty, max_sellable)
```

---

## Intégration Kill Switch

Avant chaque cycle d'évaluation, le statut de suspension est vérifié dans Redis:

```python
kill_switch_status = get_kill_switch_status(redis_client)
if kill_switch_status.suspended:
    logger.warning("Trading is suspended by Kill Switch. source=%s reason=%s", ...)
    return  # Sortie immédiate, aucune évaluation
```

Le Kill Switch est distribué (Redis Pub/Sub + état canonique JSON), namespacé par environnement, et compatible fail-closed avec le flag `trading:suspended`.

---

## Gestion des Erreurs et Traçabilité

### Exceptions Spécifiques

Les exceptions génériques sont proscrites. Le module utilise:
- `psycopg2.Error` pour les erreurs base de données
- `requests.exceptions.RequestException` pour les erreurs API broker
- `PortfolioUpdateError` (exception métier dédiée) pour les échecs de mise à jour NAV

### Journal d'Évaluation (`paper_evaluations`)

Chaque évaluation de signal est tracée avec:
- `strategy_name`, `asset`, `timeframe`, `price`
- `signal_type` (ENTRY/EXIT), `signal_triggered` (bool)
- `status`: WAITING_DATA, NO_SIGNAL, EXECUTED, REJECTED, FAILED, ERROR
- `fail_reason`: raison explicite du rejet ou de l'échec
- `details`: JSON avec indicateurs, quantités, prix

### Rollback Transactionnel

Toute erreur SQL pendant une exécution d'ordre déclenche un `conn.rollback()` explicite, garantissant qu'aucun état intermédiaire corrompu n'est persisté.

---

## Cache Local et Déduplication

### Positions actives (`active_positions`)

Dict local évitant les requêtes N+1 dans la boucle d'évaluation:
```python
active_positions = {
    (asset.lower(), strategy_name, timeframe): (pos_id, qty, entry_price)
}
```

Mis à jour atomiquement après chaque BUY (injection) et SELL (retrait).

### Déduplication intra-cycle

L'INSERT de position utilise `RETURNING id` pour injecter immédiatement le nouvel ID dans le cache local, empêchant les doublons si deux configs de la même stratégie+actif sont évaluées dans le même cycle.

### Déduplication temporelle

`self._last_eval_timestamps[config_id]` stocke le dernier timestamp de bougie close évalué. Si le timestamp n'a pas changé depuis le dernier cycle, l'évaluation est ignorée.

---

## The Golden Rule

> **Règle d'or**: Toute opération I/O dans la boucle d'évaluation doit être batchée. Une seule requête Redis, une seule requête SQL et un seul `executemany` par cycle, quel que soit le nombre de stratégies ou d'actifs.
