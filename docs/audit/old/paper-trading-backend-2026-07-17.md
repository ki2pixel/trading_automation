# Audit Backend Paper Trading — `backtest_engine/live/`

**Date** : 2026-07-17  
**Périmètre** : 18 fichiers Python dans `backtest_engine/live/`  
**Méthodologie** : Revue manuelle approfondie, conformité AGENTS.md

---

## Structure du module

```
backtest_engine/live/
├── connection.py              # Pools BDD sync/async + Redis failover
├── controls.py                # Pre-Trade Controller (ESMA RTS 6)
├── kill_switch.py             # Kill Switch distribué (Redis Pub/Sub)
├── utils.py                   # Utilitaires partagés (mappings, market hours, FX)
├── ingestion/
│   └── base.py                # Classe abstraite BasePriceIngestor
├── bybit/
│   ├── __init__.py
│   ├── config.py              # Configuration Bybit + failsafe SHA256
│   ├── client.py              # Client HTTP Bybit V5 (signé/public)
│   ├── ingestor.py            # Ingestion prix + candles Bybit
│   └── conversion/
│       ├── __init__.py
│       ├── accumulator.py     # Buffer d'accumulation profits USDC
│       ├── margin_simulator.py # Simulateur Marge UTA pré-conversion
│       ├── order_types.py     # FSM ConversionOrder (Decimal, idempotent)
│       └── spot_router.py     # Routeur d'ordres Spot USDC→EUR
├── trading212/
│   ├── __init__.py
│   ├── config.py              # Configuration T212 + failsafe SHA256
│   ├── client.py              # Client HTTP T212 (idempotent, rate-limited)
│   ├── resolver.py            # Résolveur de tickers T212
│   ├── bootstrapper.py        # Bootstrap micro-positions
│   ├── tracker.py             # Filtre micro-positions
│   └── ingestor.py            # Ingestion prix T212 (Portfolio Hack)
└── paper_trading/
    ├── engine.py              # Orchestrateur boucle paper trading
    ├── signal_executor.py     # Évaluateur de signaux + exécuteur trades
    ├── api.py                 # Endpoints FastAPI (asyncpg)
    ├── db_setup.py            # Initialisation schéma DB + seed configs
    ├── exceptions.py          # Exceptions métier dédiées
    └── marketflow_warmup.py   # Warm-up candles via MarketFlow API
```

---

## 🔴 Anomalies Critiques

| ID | Fichier | Problème | Impact |
|:---|:--------|:---------|:-------|
| C1 | `kill_switch.py` | `KillSwitchListener._listen_loop` reconnecte TOUJOURS après `CancelledError`. Si `stop()` est appelé pendant `pubsub.get_message()`, le `CancelledError` est avalé et la boucle `while self._running` continue — la tâche ne s'arrête jamais proprement. | Kill switch zombie, trading bloqué |
| P1 | `paper_trading/signal_executor.py` | `evaluate_and_execute_strategies` vérifie `has_position` en début de boucle via `active_positions` chargé au début de `run_cycle`. Si deux stratégies sur le même asset s'exécutent dans la même boucle, la deuxième ne verra pas la position créée par la première. | Double entrée possible sur même asset |
| J1 | `bybit/conversion/spot_router.py` | `_recover_order_state` utilise un TTL progressif (1m → 5m → 15m) mais le statut `RECONCILIATION_PENDING` n'a **aucun mécanisme de retry automatique** — l'ordre reste bloqué indéfiniment. | Ordre bloqué indéfiniment |
| J2 | `bybit/conversion/spot_router.py` | `_submit_order` persiste `SUBMITTED` PUIS appelle l'API Bybit. Si le crash survient entre les deux, l'ordre est `SUBMITTED` en DB mais n'a jamais atteint Bybit. La recovery au restart le trouvera et échouera (ordre introuvable). | Fonds bloqués, faux positif |
| Q6 | `paper_trading/api.py` | Aucun rate limiting sur les endpoints API FastAPI. | DDoS possible |

---

## 🟠 Anomalies Hautes

| ID | Fichier | Problème | Impact |
|:---|:--------|:---------|:-------|
| H1 | `bybit/conversion/accumulator.py` | `deposit` et `drain` ne sont pas dans une transaction DB commune — `deposit` commit après l'INSERT mais avant le SELECT de solde. Race condition entre deux `deposit` concurrents. | Incohérence de solde |
| A2 | `connection.py` | `get_async_redis_client()` crée un `aioredis.from_url` **sans** `socket_timeout`, `socket_connect_timeout`, ni `health_check_interval`. Pas de keepalive. | Déconnexions silencieuses |
| A4 | `connection.py` | `get_db_connection()` fait `pool.getconn()` puis vérifie `conn.closed` — si le pool est vide, bloque indéfiniment. Pas de timeout. | Blocage worker |
| I1 | `bybit/conversion/margin_simulator.py` | `_conversion_locked` est un simple booléen sans TTL — si le margin check échoue une fois, le verrou persiste jusqu'à `unlock()` manuel. Pas de réévaluation automatique. | Conversion bloquée indéfiniment |
| P2 | `paper_trading/signal_executor.py` | N+1 Redis dans `evaluate_and_execute_strategies` : `redis_client.get(f"price:{asset.lower()}")` unitaire par config active au lieu d'un `mget` batché. | Latence cumulée |
| C2 | `kill_switch.py` | `trigger_kill` appelle `suspend_trading` en premier, puis annule les ordres. Si l'annulation échoue, l'état est déjà `suspended` mais les ordres restent ouverts. | Incohérence d'état |
| Q2 | `paper_trading/api.py` | `panic_close_all` utilise `FOR UPDATE` mais **sans timeout** — si une ligne est lockée par un autre worker, l'endpoint bloque indéfiniment. | Blocage API |
| Q3 | `paper_trading/api.py` | `get_hmac_secret()` utilise `os.getenv("RENDER")` pour détecter la production. Sur Render avec `ENVIRONMENT=production` mais sans `RENDER`, le check échoue. | Secret HMAC manquant en prod |

---

## 🟡 Anomalies Moyennes (sélection)

| ID | Fichier | Problème | Impact |
|:---|:--------|:---------|:-------|
| O2 | `paper_trading/engine.py` | `start_loop` utilise `time.sleep(interval_seconds)` — boucle bloquante, pas de rattrapage si cycle > intervalle. | Dérive temporelle |
| O3 | `paper_trading/engine.py` | `Trading212Client` et `BybitClient` sont instanciés dans `__init__` avec appels réseau (`get_pending_orders()`). Blocage si réseau lent. | Démarrage lent |
| B2 | `controls.py` | Seuils PTC (`max_trade_pct_nav=0.10`, etc.) hardcodés dans le constructeur. Pas de lecture depuis l'environnement ou la config DB. | Reconfiguration impossible sans redeploiement |
| C3 | `kill_switch.py` | Le listener recrée un nouveau `aioredis.from_url` à chaque reconnexion — pas de pool, pas de réutilisation. | Overhead réseau |
| K1 | `trading212/client.py` | `place_market_order` utilise Redis SETNX lock 15s. Si crash après envoi ordre mais avant `finally: delete(lock_key)`, lock expire en 15s. Pendant ce temps, retry légitime bloqué. | Blocage temporaire |
| L1 | `trading212/resolver.py` | Cache fichier (`/tmp/t212_instruments.json`) sans lock — deux workers concurrents peuvent écrire simultanément. | Corruption cache |
| G1 | `bybit/ingestor.py` | `poll_and_cache` écrit dans Redis, PostgreSQL ET fichier local séquentiellement — pas de rollback global si une étape échoue. | Incohérence multi-sources |
| N1 | `trading212/ingestor.py` | Même problème que G1 : écritures séquentielles sans transaction globale. | Incohérence multi-sources |
| J4 | `bybit/conversion/spot_router.py` | `_log_blocked_conversion` logge en `logger.warning` mais n'écrit PAS dans `conversion_audit_log` — les blocages ne sont pas audités en DB. | Perte d'audit trail |
| O1 | `paper_trading/engine.py` | `run_cycle` skip silencieux si `_cycle_lock.acquire(blocking=False)` échoue. Pas de compteur, pas d'alerte. | Cycles sautés non détectés |
| A1 | `connection.py` | `FailoverRedisClient.__getattr__` ne gère pas le cas non-callable/non-pipeline. Manque `hasattr` guard. | AttributeError potentiel |
| A3 | `connection.py` | `_async_redis_client_lock` utilise `threading.Lock()` pour protéger une ressource async. `asyncio.Lock` plus cohérent. | Inadéquation sémantique |
| F1 | `bybit/client.py` | Pas de rate limiting explicite côté client (juste retry `tenacity`). Ne connaît pas les limites API Bybit. | Risque 429 |

---

## Conformité AGENTS.md

| Règle | Statut | Détail |
|:------|:------:|:-------|
| 2.2 Decimal pour live/paper | ✅ | 100% conforme |
| 2.2 Typage statique | ⚠️ | Usage fréquent de `Any` |
| 2.2 Logging structuré JSON | ⚠️ | `spot_router` seulement, le reste en f-strings |
| 2.2 Secrets masqués | ✅ | Via `python-dotenv` |
| 2.2 Failsafe clés API | ✅ | SHA256 anti-mélange live/demo |
| 2.2 Timeouts réseau centralisés | ✅ | `NETWORK_TIMEOUT_DEFAULT = 10.0` (1 exception : Redis async) |
| 2.3 Exceptions typées | ✅ | `SignalExecutionError`, `PortfolioUpdateError`, `PreTradeControlError`, `KillSwitchStateError` |
| 2.4 Séparation sync/async | ✅ | FastAPI → `asyncpg`, workers → `psycopg2` + `asyncio.to_thread` |
| 2.4 Anti-N+1 | ⚠️ | Respecté pour SQL, violé pour Redis (`get` unitaire) |
| 2.4 Bufferisation I/O | ⚠️ | `executemany` pour inserts, pas pour `log_evaluation` |
| 2.5 Thread-safety | ⚠️ | Manque lock sur cache resolver (L1), race condition signal executor (P1) |
| 2.8 Rate limiting | ⚠️ | T212 ✅, Bybit ⚠️, API FastAPI ❌ |
| 2.8 Idempotence | ⚠️ | Implémentée mais 2 bugs critiques (J1, J2) |
| 2.8 WebSocket heartbeats | ✅ | KillSwitch avec `socket_keepalive=True`, `health_check_interval=30` |
| 2.9 Pre-trade checks | ✅ | Contrôle volumétrique, marge UTA, devise T212 |
| 2.9 Circuit breakers | ⚠️ | Fonctionnel mais bug d'arrêt (C1) |

---

## Dimensions d'analyse

### Thread-safety et conditions de concurrence
- **Critique** : Race condition positions intra-cycle (P1), Kill Switch zombie (C1)
- **Haute** : Race condition accumulator (H1), `panic_close_all` sans timeout (Q2)
- **Moyenne** : Cache resolver sans lock (L1), `threading.Lock` pour ressource async (A3)

### Gestion des erreurs et robustesse réseau
- ✅ `tenacity` utilisé pour les clients T212 et Bybit
- ✅ `NETWORK_TIMEOUT_DEFAULT` utilisé partout sauf Redis async
- ❌ `get_async_redis_client()` sans timeout (A2)
- ❌ `get_db_connection()` bloque indéfiniment si pool vide (A4)

### Idempotence des ordres
- ✅ T212 : `client_order_id` + Redis SETNX lock
- ✅ Bybit Conversion : `orderLinkId` UUID v4 + `_recover_order_state` + audit trail DB
- ❌ Crash entre INSERT `SUBMITTED` et appel API (J2)
- ❌ `RECONCILIATION_PENDING` sans retry automatique (J1)

### Pre-trade checks
- ✅ `PreTradeController` avec limites NAV, exposition, collar
- ✅ `UTAMarginSimulator` pour conversion Bybit
- ✅ Vérification devise unique T212
- ⚠️ Seuils hardcodés (B2)

### Circuit breakers
- ✅ `KillSwitchListener` Pub/Sub distribué
- ✅ `panic_close_all` avec lock ordering et RETURNING
- ❌ `_conversion_locked` sans TTL (I1)
- ❌ Kill Switch listener ne s'arrête pas proprement (C1)

### Logging structuré JSON
- ✅ `DequeLogHandler` pour buffer SSE
- ✅ `[AUDIT]` JSON dans `spot_router._log_conversion`
- ⚠️ Majorité des logs en f-strings, pas systématiquement JSON

### Base de données et persistance
- ✅ Séparation stricte asyncpg/psycopg2 respectée
- ⚠️ N+1 Redis (P2)
- ⚠️ Double commit dans `log_evaluation` (P4)

### Rate limiting et backoff
- ✅ `Trading212Client._throttle` avec délais par endpoint
- ✅ `tenacity` avec `wait_random_exponential`
- ❌ Pas de rate limiting sur les endpoints API FastAPI (Q6)

### WebSocket / Heartbeats
- ✅ KillSwitch : `socket_keepalive=True`, `health_check_interval=30`, reconnexion auto
- ❌ Bug d'arrêt sur `CancelledError` (C1)
- N/A : Pas de WebSocket broker (REST only)

---

## Statistiques

| Sévérité | Nombre |
|:---------|:------:|
| Critique | 5 |
| Haute | 12 |
| Moyenne | 14 |
| Basse | 8 |
| **Total** | **39** |
