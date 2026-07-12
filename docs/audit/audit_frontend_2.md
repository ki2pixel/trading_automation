# Audit Backend & Frontend — Paper Trading (`backtest_engine/live/`)

**Note de Gout (Taste Score)**: 6.5/10 — Architecture solide avec de bonnes pratiques (Decimal, batched I/O, kill switch, CSRF), mais plusieurs défauts critiques de concurrence, de sécurité et de cohérence frontend/backend.

**Diagnostic de structure de données**: Le schéma dual-portfolio (trading212/bybit) est correct, mais le traitement asymétrique des PnL bybit gagnants (séquestration en `secured_balance` EUR) introduit une complexité de conversion qui n'est pas nécessairement justifiée.

**Analyse d'impact sur la compatibilité**: Aucun changement cassant détecté. Les problèmes identifiés sont des bugs runtime et des risques de concurrence, pas des incompatibilités d'API.

---

## Anomalies Critiques

| Identifiant | Catégorie de Risque | Conséquence en Production | Sévérité |
|:----|:----|:----|:----|
| ANM-01 | Concurrence (Deadlock) | Panic close + signal executor en parallèle → deadlock Postgres, blocage total | **Critique** |
| ANM-02 | Sécurité (Timing Attack) | Comparaison de mot de passe non-constant-time → fuite d'informations | **Critique** |
| ANM-03 | Sécurité (CSRF Bypass) | Panic button frontend omet `Content-Type: application/json` → rejet 415, liquidation d'urgence impossible | **Critique** |
| ANM-04 | Risque Financier (Ordres Réels) | `T212_PAPER_ROUTING_ENABLED=true` envoie des ordres réels sans idempotence (`client_order_id`) | **Haute** |
| ANM-05 | Cohérence Frontend/Backend | Détection crypto `endsWith("usdt")` côté frontend mais backend utilise `usdc` → USDC affiché comme actions EUR | **Haute** |
| ANM-06 | Risk Management (PTC non intégré) | `PreTradeController` défini mais jamais appelé dans `signal_executor.py` | **Haute** |
| ANM-07 | Performance (CPU sur event loop) | `get_performance_metrics` fait du FIFO matching + reconstruction de courbes sur 5000 bougies synchroniquement dans l'event loop async | **Haute** |
| ANM-08 | Concurrence (Lock ordering) | Lock ordering inconsistent entre panic_close (positions→balance) et signal_executor (balance→position) | **Haute** |

## Anomalies Moyennes

| Identifiant | Catégorie de Risque | Conséquence en Production | Sévérité |
|:----|:----|:----|:----|
| ANM-09 | Performance (N+1 I/O) | `marketflow_warmup.py` insère les bougies row-by-row au lieu de `executemany` | **Moyenne** |
| ANM-10 | Memory (Objet éphémère) | `BrokerSimulator` recréé pour chaque position à chaque cycle d'évaluation | **Moyenne** |
| ANM-11 | DRY | Calcul `source` redondant (ligne 426 + 626) dans `signal_executor.py` | **Moyenne** |
| ANM-12 | Import circulaire | `signal_executor.py:226` importe `get_eurusd_rate` depuis `engine.py` qui importe `signal_executor.py` | **Moyenne** |
| ANM-13 | Kill Switch (pas de reset) | Aucun endpoint pour désactiver le kill switch (`set_trading_suspended(False)` jamais exposé) | **Moyenne** |
| ANM-14 | Connexion non gérée | `connection.py:148` fallback `psycopg2.connect()` bypass le pool → connexions non gérées | **Moyenne** |
| ANM-15 | Cache inutile | `app.js:963` invalide `cachedConfigs = null` à chaque tick de polling → cache toujours vide | **Moyenne** |
| ANM-16 | Debug en production | `login.js:9,12,16` — `console.log` laissés en production | **Basse** |

---

## Détails et Corrections

### ANM-01 & ANM-08: Deadlock par lock ordering inconsistent

**Règle violée**: AGENTS.md §2.5 — "Deadlocks: Ordre d'acquisition strict et timeouts requis"

`./backtest_engine/live/paper_trading/api.py:472` (panic_close_all) acquiert les locks dans l'ordre **positions → balance**, tandis que `./backtest_engine/live/paper_trading/signal_executor.py:971` (SELL path) acquiert dans l'ordre **balance → position**. C'est un schéma de deadlock classique.

```python
# api.py:472 — Panic close: positions FIRST, then balance
positions = await conn.fetch(
    "SELECT id, asset, strategy_name, qty, entry_price, current_price FROM paper_positions FOR UPDATE"
)
# ... then per position:
await conn.execute("SELECT cash_balance FROM paper_portfolio_balance WHERE source = $1 FOR UPDATE", source)

# signal_executor.py:971 — SELL: balance FIRST, then position
cur.execute("SELECT cash_balance FROM paper_portfolio_balance WHERE source = %s FOR UPDATE", (source,))
cur.execute("DELETE FROM paper_positions WHERE id = %s RETURNING id", (pos_id,))
```

**Correction**: Standardiser l'ordre des locks sur **balance → position** partout. Dans `panic_close_all`, acquérir les locks balance avant de parcourir les positions:

```python
# api.py — Correction: lock balances first, then positions
async with conn.transaction():
    # 1. Lock all balance rows first (consistent with signal_executor)
    await conn.execute("SELECT 1 FROM paper_portfolio_balance WHERE source = 'trading212' FOR UPDATE")
    await conn.execute("SELECT 1 FROM paper_portfolio_balance WHERE source = 'bybit' FOR UPDATE")
    # 2. Then lock positions
    positions = await conn.fetch(
        "SELECT id, asset, strategy_name, qty, entry_price, current_price FROM paper_positions FOR UPDATE"
    )
```

### ANM-02: Timing attack sur la comparaison de mot de passe

**Règle violée**: Sécurité authentication — `hmac.compare_digest` utilisé pour les tokens mais pas pour les passwords.

`./run_paper_trader.py:476`:
```python
# VULNÉRABLE — comparaison non-constant-time
if username != expected_user or password != expected_password:
```

**Correction**:
```python
user_ok = hmac.compare_digest(username or "", expected_user)
pass_ok = hmac.compare_digest(password or "", expected_password)
if not (user_ok and pass_ok):
```

### ANM-03: Panic button cassé par CSRF middleware

`./backtest_engine/live/paper_trading/static/js/api.js:103`:
```javascript
export async function executePanic() {
    return await fetch('/api/control/panic', { method: 'POST' });
    // Aucun Content-Type: application/json → rejet 415 par CSRFMiddleware
}
```

`./run_paper_trader.py:190`:
```python
if path.startswith("/api/") and not content_type.startswith("application/json"):
    return JSONResponse(status_code=415, ...)
```

**Correction**:
```javascript
export async function executePanic() {
    return await fetch('/api/control/panic', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    });
}
```

### ANM-04: Ordres réels T212 sans idempotence

**Règle violée**: AGENTS.md §2.8 — "Idempotence: Vérification systématique d'exécution via un `client_order_id` unique"

`./backtest_engine/live/paper_trading/signal_executor.py:725`:
```python
order_res = self.t212_client.place_market_order(ticker=t212_ticker, quantity=float(qty))
# Pas de client_order_id → double-exécution possible après timeout réseau
```

Le routeur de conversion Bybit (`./backtest_engine/live/bybit/conversion/spot_router.py`) implémente correctement l'idempotence avec `client_order_id` et `_recover_order_state()`, mais le routing T212 paper trading ne le fait pas.

### ANM-05: Frontend détecte USDT mais le backend utilise USDC

**Règle violée**: AGENTS.md §2.9 — mapping USDT→USDC effectué en backend (`db_setup.py:431-473`), mais le frontend n'a pas suivi.

Trois fichiers concernés:

`./backtest_engine/live/paper_trading/static/app.js:176`:
```javascript
const isCrypto = pos.asset.toLowerCase().endsWith("usdt"); // MANQUE "usdc"
```

`./backtest_engine/live/paper_trading/static/js/ui.js:7`:
```javascript
asset?.toLowerCase().endsWith('usdt') // MANQUE "usdc"
```

`./backtest_engine/live/paper_trading/static/js/chart.js:156`:
```javascript
const isCrypto = ticker.toLowerCase().endsWith('usdt'); // MANQUE "usdc"
```

**Correction** (identique pour les 3 fichiers):
```javascript
const isCrypto = ticker.toLowerCase().endsWith("usdt") || ticker.toLowerCase().endsWith("usdc");
```

Ou mieux, aligner sur la logique backend de `./backtest_engine/live/utils.py:14`:
```javascript
const isCrypto = asset?.toLowerCase().endsWith("usdt") || asset?.toLowerCase().endsWith("usdc");
```

### ANM-06: PreTradeController jamais intégré

**Règle violée**: AGENTS.md §2.9 — "Pre-Trade Checks: Vérification synchrone obligatoire de la marge, de l'exposition max et des conflits d'ordres"

`./backtest_engine/live/controls.py` définit `PreTradeController` avec checks volumétriques, notionnels et price collars, mais `signal_executor.py` n'importe jamais ni n'appelle cette classe. Les checks ad hoc dans le signal executor (max_entry_price, cash balance) ne couvrent pas l'exposition cumulée ni le price collar.

### ANM-07: Calcul de métriques bloquant l'event loop

`./backtest_engine/live/paper_trading/api.py:619-778` — L'endpoint `get_performance_metrics` effectue:
- FIFO trade matching sur toutes les transactions
- Reconstruction de courbes de_NAV sur 5000 bougies
- Calcul de drawdown

Tout cela de manière **synchronique** dans une coroutine async. Pendant ce calcul, l'event loop est bloquée, empêchant le traitement des autres requêtes API.

**Correction**: Déléguer à un thread pool ou pré-calculer périodiquement:
```python
result = await asyncio.to_thread(_compute_performance_metrics, ticker, pool)
```

### ANM-09: marketflow_warmup — INSERT row-by-row

**Règle violée**: AGENTS.md §2.4 — "Utilisez des transactions en lot (`executemany`)"

`./backtest_engine/live/paper_trading/marketflow_warmup.py:98-107`:
```python
for candle in candles:
    cur.execute("""INSERT INTO live_candles_1m ...""", (...))  # N round-trips
```

**Correction**: Collecter les tuples et utiliser `executemany`:
```python
records = []
for candle in candles:
    # ... validation/parsing ...
    records.append((t212_ticker, dt_val, open_val, high_val, low_val, close_val))
if records:
    cur.executemany("""INSERT INTO live_candles_1m ... ON CONFLICT ... DO UPDATE ...""", records)
```

### ANM-10: BrokerSimulator recréé par cycle

`./backtest_engine/live/paper_trading/signal_executor.py:822-837` — Un nouveau `BrokerSimulator` est instancié pour chaque position à chaque cycle d'évaluation (60s). L'objet est créé avec des données factices (`order_id="dummy_entry"`) juste pour évaluer les exit rules.

**Correction**: Mettre en cache le broker par (strategy_name, asset) ou réutiliser une instance unique configurée à la volée.

### ANM-12: Import circulaire

`./backtest_engine/live/paper_trading/signal_executor.py:226`:
```python
from backtest_engine.live.paper_trading.engine import get_eurusd_rate
```

`engine.py` importe `SignalExecutor` depuis `signal_executor.py` au niveau module. `signal_executor.py` importe `get_eurusd_rate` depuis `engine.py` au niveau fonction. Cela fonctionne (lazy import) mais crée une dépendance circulaire fragile.

**Correction**: Importer directement depuis `./backtest_engine/live/utils.py` où `get_eurusd_rate` est défini:
```python
from backtest_engine.live.utils import get_eurusd_rate
```

### ANM-13: Kill Switch sans reset

`./backtest_engine/live/kill_switch.py:17` — `set_trading_suspended(True)` est exposé via `panic_close_all` (api.py:465), mais il n'existe **aucun endpoint** pour appeler `set_trading_suspended(False)`. Une fois le kill switch activé, le trading reste suspendu jusqu'au redémarrage du processus (le flag Redis `trading:suspended` persiste même après redémarrage).

**Correction**: Ajouter un endpoint de réactivation:
```python
@router.post("/control/resume")
async def resume_trading():
    from backtest_engine.live.kill_switch import set_trading_suspended
    set_trading_suspended(False)
    # Also clear Redis flag
    pool = await _get_pool()
    async with pool.acquire() as conn:
        await conn.execute("SELECT 1")  # Just to get a connection
    from backtest_engine.live.connection import get_redis_client
    redis_client = get_redis_client()
    if redis_client:
        redis_client.delete("trading:suspended")
    return {"status": "success", "message": "Trading resumed"}
```

### ANM-14: Fallback connexion non gérée

`./backtest_engine/live/connection.py:148`:
```python
conn = psycopg2.connect(db_url)  # Bypass le pool, connexion orpheline
```

Si le pool échoue à s'initialiser mais que `DATABASE_URL` est set, chaque appel à `get_db_connection` crée une nouvelle connexion non gérée. En cas de charge, cela peut épuiser les connexions PostgreSQL.

### ANM-15: Cache configs toujours invalidé

`./backtest_engine/live/paper_trading/static/app.js:963`:
```javascript
cachedConfigs = null; // À chaque tick de polling (10s)
```

Puis `fetchConfigs` (ligne 231):
```javascript
if (cachedConfigs) {
    data = cachedConfigs;
} else {
    data = await getConfigs(); // Toujours re-fetch car cache toujours null
```

Le cache `cachedConfigs` n'a aucun effet — il est invalidé à chaque cycle de polling.

---

## Points Positifs

Le codebase présente plusieurs bonnes pratiques dignes de mention:

- **Batched I/O**: `update_portfolio_nav` utilise Redis `mget()` + SQL `ANY()` + `executemany()` — évite le N+1
- **Decimal partout**: Conformité avec AGENTS.md §2.2 pour la précision financière
- **Cycle lock non-bloquant**: `engine.py:94` — `acquire(blocking=False)` évite les cycles empilés
- **Stale price detection**: Seuil de 3 minutes pour Redis et Postgres prices
- **RETURNING clause**: Vérification de suppression de position (`DELETE ... RETURNING id`)
- **Failover Redis**: `FailoverRedisClient` avec basculement transparent et replay pipeline
- **Kill switch pub/sub**: `health_check_interval=30` + `socket_keepalive=True` — conforme AGENTS.md §2.8
- **Sécurité**: CSRF double-submit, HMAC session tokens, security headers, rate limiter, `safe_error_response`
- **Idempotence conversion Bybit**: `spot_router.py` implémente correctement `client_order_id` + `_recover_order_state()`

---

## Résumé par priorité d'action

1. **Critique — Corriger immédiatement**: ANM-01 (deadlock), ANM-02 (timing attack), ANM-03 (panic button cassé)
2. **Haute — Planifier un fix**: ANM-04 (idempotence T212), ANM-05 (frontend USDC), ANM-06 (intégrer PTC), ANM-07 (offload métriques)
3. **Moyenne — Améliorer progressivement**: ANM-09 (executemany warmup), ANM-10 (cache broker), ANM-12 (import circulaire), ANM-13 (reset kill switch)
4. **Basse — Nettoyage**: ANM-15 (cache frontend), ANM-16 (console.log)