# Audit Backend — Paper Trading (`backtest_engine/live/`)

- **Date** : 2026-07-26
- **Périmètre** : `backtest_engine/live/` (27 fichiers Python, ~7 300 lignes) — focus `paper_trading/`, avec vérifications croisées dans `run_paper_trader.py` (montage API/middlewares) et `tests/`.
- **Méthode** : lecture intégrale du périmètre, vérification de chaque anomalie contre le code réel (numéros de ligne exacts), référentiel d'invariants `AGENTS.md` §2 (standards) et §3 (protocole d'audit).
- **Statut** : **REQUEST CHANGES** — 1 anomalie critique (latente), 4 hautes, 11 moyennes, 10 basses.

---

## 1. Synthèse

L'architecture globale est saine : séparation sync/async (psycopg2/asyncpg), middlewares de sécurité complets (auth session HMAC, CSRF double-submit, rate limiting Redis, headers, masquage d'erreurs avec UUID de corrélation), failsafe SHA256 des clés API sur les deux brokers, Kill Switch fail-closed avec keepalive Redis conforme, verrous `FOR UPDATE` et gardes `DELETE ... RETURNING` sur les mutations financières, et usage quasi systématique de `Decimal` dans les chemins financiers.

Les risques majeurs identifiés sont :

1. Un **bug de type dans la récupération d'ordres de conversion** (`dry_run` passé à un dataclass qui ne l'accepte pas) qui rend toute récupération impossible et ouvre la voie à une double conversion si le pipeline est activé.
2. Une **incompatibilité de casse des tickers** entre le warm-up MarketFlow et le moteur de stratégies, rendant le warm-up inopérant pour 8 des 21 actifs.
3. Une **fuite potentielle de credentials Redis** dans les logs via l'URL Upstash.
4. Un **défaut de séquençage Redis/PostgreSQL** dans l'ingestor Bybit contredisant le correctif G1-FIX qu'il prétend implémenter.
5. Un **pipeline de conversion USDC→EUR fonctionnellement mort** : `AccumulatorBuffer.deposit()` n'est jamais appelé en production.

## 2. Tableau des anomalies

| Identifiant | Catégorie de Risque | Conséquence en Production | Sévérité |
| :---- | :---- | :---- | :---- |
| PT-01 | Logique / Idempotence | Récupération d'ordre de conversion impossible (TypeError masqué) → double conversion USDC→EUR si le pipeline est activé. | Critique (latente) |
| PT-02 | Cohérence données | Warm-up inopérant pour 8/21 actifs ; stratégies bloquées en `WAITING_DATA` ; doublons de bougies `ZEAL.CO`/`zeal.co`. | Haute |
| PT-03 | Sécurité | Credentials Redis (URL avec basic auth) exposés en clair dans les logs sur erreur API Upstash. | Haute |
| PT-04 | Cohérence données | Redis reçoit des prix dont l'écriture PostgreSQL a échoué ; le moteur (Redis prioritaire) valorise la NAV sur des prix fantômes. | Haute |
| PT-05 | Logique | `continue` manquant après ajustement des frais → INSERT violant `CHECK (qty > 0)` → erreur DB + rollback du cycle d'achat. | Moyenne |
| PT-06 | Erreurs | Exception non-`RequestException` d'un broker (JSON malformé, `InvalidOperation`) → rollback global de la MAJ NAV, y compris la mise à jour cash de l'autre broker. | Moyenne |
| PT-07 | Logique / Feature | `deposit()` jamais appelé → buffer de conversion toujours à 0 → profits `secured_balance` jamais convertis en EUR. | Moyenne |
| PT-08 | Risk Management | Price collar PTC inopérant : `reference_price == price` sur tous les chemins d'appel → déviation toujours 0 %. | Moyenne |
| PT-09 | Logique / Observabilité | Flux SSE `/logs/stream` cesse définitivement d'émettre après saturation du buffer (1 000 entrées). | Moyenne |
| PT-10 | BDD / Cohérence | Panic close : requête de prix par position (N+1) ; divergence comptable — profits Bybit non versés en `secured_balance` contrairement au SELL standard. | Moyenne |
| PT-11 | Idempotence | `client_order_id` non transmis au broker T212 ; réconciliation par quantités avec tolérance float `1e-7` — faux positif « FILLED » possible si 2 stratégies tradent le même ticker. | Moyenne |
| PT-12 | Erreurs | `except Exception: pass` silencieux (parse prix Redis, `is_market_open`, caches API) — violation AGENTS.md §2.3, masque la corruption de données de prix. | Moyenne |
| PT-13 | Précision financière | Décisions de sortie live (SL/TP/trailing) calculées en `float` via `BrokerSimulator` — violation AGENTS.md §2.2. | Moyenne |
| PT-14 | Concurrence | Keep-alive PostgreSQL (psycopg2 bloquant) exécuté dans la boucle asyncio FastAPI sans `to_thread`. | Moyenne |
| PT-15 | Logique | Branche morte dangereuse `len(row) == 5` : attribution de toutes les bougies au ticker du premier config. | Moyenne |
| PT-16 | Sécurité | mTLS sans CA (`DB_SSL_CERT`/`DB_SSL_KEY` sans `DB_SSL_CA`) → `CERT_NONE` + `check_hostname=False` (surface MITM). | Basse |
| PT-17 | Logique | `reconciliation_attempts` reconstruit à 0 à chaque cycle (non persisté) → compteur J1-FIX mort ; `LIMIT 1` sans `ORDER BY`. | Basse |
| PT-18 | Logique | `UTAMarginSimulator` réinstancié à chaque cycle → verrou `_conversion_locked` (TTL 5 min) jamais persistant. | Basse |
| PT-19 | Risk Management | NAV par défaut 100 000 / 10 000 si lignes de balance absentes → sizing Kelly sur base fictive. | Basse |
| PT-20 | Logging | `print()` au lieu de `logger` dans `connection.py`, ingestors, clients, configs → logs non structurés, hors JSON d'audit. | Basse |
| PT-21 | Logging | `logger.exception()` (traceback) sur erreurs réseau transitoires (Redis mget, API publiques FX) — violation §2.3. | Basse |
| PT-22 | Performance BDD | Index manquants : `paper_transactions(timestamp)`, lookups `LOWER(ticker)` sur `live_prices`/`live_candles_1m`. | Basse |
| PT-23 | Concurrence | `_last_call_times` du throttle T212 partagé sans verrou (thread moteur + thread kill switch). | Basse |
| PT-24 | Logique | Lookup PTC `pos_key` en 2-uplet contre clés 3-uplets → toujours vide (sans impact actuel : branche `has_position=False`). | Basse |
| PT-25 | Logique | Conversion : `client_order_id` « blocked-… » à la seconde (collisions uniques) ; `drain()` draine aussi les dépôts postérieurs à la soumission. | Basse |
| PT-26 | Résilience | `_clients_warmed_up=True` même en échec d'init broker → aucune tentative de reconnexion ultérieure. | Basse |

---

## 3. Détail et corrections des anomalies majeures

### PT-01 — Critique : `TypeError` dans la récupération des ordres de conversion (double-spend latent)

**Fichier** : `backtest_engine/live/bybit/conversion/spot_router.py:64-78` ; `backtest_engine/live/bybit/conversion/order_types.py:30-63`

Le Step 0 de `try_convert()` reconstruit un `ConversionOrder` depuis `conversion_audit_log` en passant `dry_run=row[8]` :

```python
unfinished_order = ConversionOrder(
    client_order_id=row[0],
    ...
    dry_run=row[8],          # ← le dataclass n'a PAS de champ dry_run
    submitted_at=row[9] if row[9] else datetime.now(timezone.utc),
)
```

Le dataclass `ConversionOrder` ne déclare aucun champ `dry_run` → `TypeError: __init__() got an unexpected keyword argument 'dry_run'`. Ce `TypeError` est capturé par le `except Exception` englobant (ligne 96), loggé comme simple erreur, puis l'exécution **poursuit vers le Step 1** : si le buffer dépasse le seuil, un **nouvel ordre avec un nouvel `orderLinkId`** est soumis alors qu'un ordre antérieur non résolu existe — double conversion. Le même défaut existe dans la branche forced-FAILED (`dry_run=unfinished_order.dry_run`, ligne 88).

Note : l'anomalie est **latente** aujourd'hui car le buffer n'est jamais alimenté (cf. PT-07), mais elle devient active dès que `deposit()` est câblé, avec `BYBIT_CONVERSION_ENABLED=true` et `DRY_RUN=false`.

**Correction** : persister `dry_run` comme propriété hors dataclass, ou l'ajouter au dataclass :

```python
# order_types.py — ajouter le champ au dataclass
@dataclass
class ConversionOrder:
    ...
    dry_run: bool = False
    ...
```

et ne jamais laisser un `TypeError` de reconstruction être absorbé par le même `except` que les erreurs réseau :

```python
# spot_router.py — Step 0 : séparer les fautes de programmation des fautes transitoires
        except (psycopg2.Error, redis.exceptions.RedisError, OSError) as e:
            logger.error("[SpotRouter] Failed to check/recover unfinished orders: %s", e)
            return None  # fail-closed : ne jamais soumettre un nouvel ordre
```

*Justification* : toute impossibilité de lire l'état d'un ordre non résolu doit interdire la soumission d'un nouvel ordre (anti-double-spend, §2.8).

---

### PT-02 — Haute : Warm-up MarketFlow invisible pour le moteur (casse des tickers)

**Fichiers** : `backtest_engine/live/paper_trading/marketflow_warmup.py:95` (INSERT) ; `backtest_engine/live/paper_trading/signal_executor.py:407,420` (SELECT)

`run_warmup()` itère sur `TICKER_MAPPING` dont 8 clés sont en casse mixte (`ZEAL.CO`, `NVO`, `EVD.DE`, `GMAB`, `FPE.DE`, `SAP`, `NVS`, `AMS.MC`) et insère les bougies avec ce ticker **tel quel** :

```python
records.append((t212_ticker, dt_val, open_val, high_val, low_val, close_val))
```

Le moteur interroge `live_candles_1m` avec des tickers **systématiquement minuscules** (`active_assets.add(asset.lower())` → `WHERE ticker = ANY(...)`), et l'ingestor T212 écrit aussi en minuscules. L'égalité PostgreSQL étant sensible à la casse, les ~1 440 bougies de warm-up de ces 8 actifs sont **invisibles** pour le moteur : stratégies bloquées en `WAITING_DATA` jusqu'à accumulation organique, et lignes dupliquées (`ZEAL.CO` ≠ `zeal.co`) dans la table. Le dashboard (`LOWER(ticker) = LOWER($1)`) les voit, ce qui masque le défaut visuellement.

**Correction** :

```python
# marketflow_warmup.py — parse_and_insert
records.append((t212_ticker.lower(), dt_val, open_val, high_val, low_val, close_val))
```

Plus une passe de reprise unique : `UPDATE live_candles_1m SET ticker = LOWER(ticker) WHERE ticker <> LOWER(ticker);` (avec gestion des collisions de PK via `ON CONFLICT` manuel ou suppression préalable des doublons).

*Justification* : la clé de corrélation inter-modules (ticker) doit avoir une forme canonique unique — minuscules, comme déjà pratiqué par les deux ingestors et le moteur.

---

### PT-03 — Haute : Credentials Redis exposés dans les logs (Upstash)

**Fichier** : `backtest_engine/live/connection.py:266`

```python
print(f"[UpstashAPI] Error querying Upstash API for {redis_url}: {e}")
```

`redis_url` est de la forme `rediss://<user>:<password>@<host>:<port>` — les credentials sont écrits en clair dans les logs (et ces logs sont streamés vers le dashboard authentifié via `/api/logs/stream`). Le même motif existe à la ligne ~230 (`print` du statut suspendu sans URL — celui-là est inoffensif).

**Correction** :

```python
host = urllib.parse.urlparse(redis_url).hostname or "unknown"
print(f"[UpstashAPI] Error querying Upstash API for host {host}: {type(e).__name__}: {e}")
```

*Justification* : §2.2 — « Secrets masqués via variables d'environnement », jamais en log. Ne journaliser que le host.

---

### PT-04 — Haute : Ingestor Bybit — Redis reçoit des prix non commités en BDD

**Fichier** : `backtest_engine/live/bybit/ingestor.py:138-150, 158-196`

Le pipeline Redis est **alimenté avant** la transaction PostgreSQL de chaque symbole :

```python
if redis_pipeline:
    redis_pipeline.set(f"price:{symbol_lower}", price_payload, ex=180)   # staging AVANT PG

try:
    with get_db_connection() as conn:
        ...  # INSERT live_prices + candles
except Exception:
    prices.pop(symbol_lower, None)   # ← ne retire PAS la commande déjà stagée
    continue
...
if redis_pipeline and prices:
    redis_pipeline.execute()         # ← publie aussi les symboles dont PG a échoué
```

Le commentaire « G1-FIX » affirme que Redis ne reçoit que des données commitées ; en réalité `prices.pop()` ne défait pas le staging. Comme le moteur donne la **priorité à Redis** sur SQL pour la valorisation (`update_portfolio_nav`, ligne 317), un prix dont la persistance a échoué devient la source de vérité.

**Correction** : ne stager qu'après succès PG — par exemple en accumulant les payloads validés dans une liste pendant la boucle, puis en construisant le pipeline à la fin :

```python
staged: list[tuple[str, str]] = []
...
    # après conn.commit() réussi pour ce symbole :
    staged.append((f"price:{symbol_lower}", price_payload))
...
if redis_client and staged:
    pipe = redis_client.pipeline()
    for key, payload in staged:
        pipe.set(key, payload, ex=180)
    pipe.execute()
```

*Justification* : ordre de consistance documenté (PG d'abord, Redis ensuite) — le staging doit suivre le commit, pas le précéder.

---

### PT-05 — Moyenne : `continue` manquant après rejet pour quantité nulle (BUY)

**Fichier** : `backtest_engine/live/paper_trading/signal_executor.py:717-735`

Après ajustement des frais, si `qty <= 0`, une évaluation `REJECTED` est loggée mais l'exécution **poursuit** vers les Pre-Trade Controls (qui laissent passer une quantité nulle) puis vers l'`INSERT INTO paper_positions` — qui viole le `CHECK (qty > 0)` → `psycopg2.IntegrityError` → rollback + évaluation `ERROR` contradictoire avec le `REJECTED` déjà écrit.

```python
                if qty <= 0:
                    self.log_evaluation(
                        conn, strategy_name, asset, timeframe,
                        price=current_price, signal_type='ENTRY',
                        signal_triggered=True, status='REJECTED',
                        fail_reason='Kelly size or cash availability results in zero qty after fee adjustment',
                        details={...}
                    )
                    continue          # ← manquant
```

*Justification* : un rejet métier doit court-circuiter le chemin d'exécution ; l'état actuel produit une erreur DB évitable et un double logging incohérent.

---

### PT-06 — Moyenne : `update_portfolio_nav` — une erreur broker fait tout échouer

**Fichier** : `backtest_engine/live/paper_trading/signal_executor.py:203-204, 222-223, 348-355`

Les blocs de récupération du cash broker ne captent que `requests.exceptions.RequestException`. Or `Decimal(str(...))` sur une réponse malformée lève `decimal.InvalidOperation`, et `response.json()` lève `json.JSONDecodeError` — aucune n'est une `RequestException`. Elles remontent au `except Exception` global → `conn.rollback()` → `PortfolioUpdateError`. La mise à jour cash T212 (déjà exécutée dans la même transaction) est **annulée** par la faute Bybit, et la NAV n'est pas recalculée du tout ce cycle.

**Correction** : capturer par broker `(requests.exceptions.RequestException, ValueError, KeyError, TypeError)` (`InvalidOperation` et `JSONDecodeError` héritent de `ValueError`) pour qu'une défaillance d'un broker n'invalide ni l'autre ni le calcul de NAV.

*Justification* : §2.3 — exceptions typées ; isolation des défaillances de transport par connecteur.

---

### PT-07 — Moyenne : Pipeline de conversion mort — `deposit()` jamais appelé

**Fichiers** : `backtest_engine/live/bybit/conversion/accumulator.py:41` ; `backtest_engine/live/paper_trading/signal_executor.py:1091-1102`

Recherche exhaustive : `AccumulatorBuffer.deposit()` n'est appelé que dans `tests/`. Le SELL profitable Bybit crédite `secured_balance` (EUR) mais n'alimente jamais `conversion_accumulator` → `should_trigger()` retourne toujours `False` → aucune conversion USDC→EUR n'est jamais déclenchée (`BYBIT_CONVERSION_ENABLED` inclus). La fonctionnalité documentée « extraction des profits » est inopérante de bout en bout — et c'est ce qui masque PT-01.

**Correction** : lors du SELL Bybit profitable, enregistrer le profit dans le buffer dans la même transaction :

```python
if pnl > 0 and source == 'bybit':
    ...
    accumulator = AccumulatorBuffer()  # seuil depuis env, comme run_conversion_pipeline
    accumulator.deposit(conn, pnl, trade_ref=f"paper-sell-{pos_id}")
```

*Justification* : la chaîne fonctionnelle définie par le système (profit → buffer → seuil → conversion) doit être câblée, sinon supprimer le code mort (§3.2 — pas de code temporaire permanent).

---

### PT-08 — Moyenne : Price collar PTC structurellement inopérant

**Fichiers** : `backtest_engine/live/controls.py:74-88` ; `signal_executor.py:741-748, 973-980` ; `trading212/client.py:~282` ; `bybit/conversion/spot_router.py:~215`

Sur **tous** les chemins d'appel, `reference_price` reçoit la même valeur que `price` (`current_price`/`price`) → `price_deviation` vaut toujours `0` → le contrôle « collar » (ESMA RTS 6) ne peut jamais se déclencher. Seuls les contrôles volumétrique et notionnel fonctionnent.

**Correction** : passer une référence indépendante — p. ex. la clôture de la dernière barre (`last_closed_bar["close"]` côté exécuteur) ou le prix `live_prices` en BDD côté client T212, au lieu du prix d'exécution lui-même.

*Justification* : un garde-fou de conformité déclaré doit être alimenté par une source de référence réellement indépendante.

---

### PT-09 — Moyenne : `/api/logs/stream` se fige après 1 000 logs

**Fichier** : `backtest_engine/live/paper_trading/api.py:695-725`

Le suivi d'index est basé sur `len(log_buffer)`, borné à `maxlen=1000`. Une fois le deque plein, `current_len` reste égal à `1000` et `last_sent_idx` vaut `1000` : la condition `current_len > last_sent_idx` n'est plus jamais vraie → plus aucun log n'est émis jusqu'à reconnexion du client.

**Correction** : suivre un curseur monotone indépendant de la taille du buffer — p. ex. mémoriser l'objet du dernier log émis et comparer par identité/timestamp, ou utiliser un compteur global incrémenté à chaque `emit` stocké dans l'entrée (`entry["seq"]`), puis filtrer `seq > last_sent_seq`.

*Justification* : l'observabilité du dashboard ne doit pas dépendre d'un invariant (taille croissante) que `maxlen` invalide par construction.

---

### PT-10 — Moyenne : Panic close — N+1 et divergence comptable

**Fichier** : `backtest_engine/live/paper_trading/api.py:565-623`

1. **N+1** : une requête `SELECT price FROM live_prices` par position dans la boucle (ligne 579). Violation §2.4 — requêter en une fois : `SELECT ticker, price FROM live_prices WHERE LOWER(ticker) = ANY($1)` avec la liste des assets des positions.
2. **Divergence comptable** : le SELL standard de `signal_executor` verse les profits Bybit en `secured_balance` (EUR sécurisé) ; le panic close crédite systématiquement `net_revenue` en cash, sans sécurisation. Deux chemins de clôture → deux comptabilités différentes pour le même événement économique.

**Correction** : factoriser le calcul de clôture (revenu net, PnL, ventilation `secured_balance`) dans une fonction partagée utilisée par les deux chemins.

---

### PT-11 — Moyenne : Idempotence T212 — `client_order_id` local seulement

**Fichier** : `backtest_engine/live/trading212/client.py:183-336`

Le payload de l'ordre ne contient que `ticker` et `quantity` — le `client_order_id` (UUID v4) n'est pas transmis au broker (l'API T212 market orders ne l'accepte pas). L'idempotence repose sur : (a) un verrou Redis SETNX de 5 s, (b) une réconciliation par quantité de position (`abs(current_qty - expected_qty) < 1e-7`). Si deux stratégies tradent le même ticker (le suivi se fait par ticker, pas par stratégie), la somme des quantités peut coïncider avec `expected_qty` → retour prématuré « FILLED » alors que l'ordre n'a jamais été exécuté → divergence paper/réel.

**Correction** : interroger `get_pending_orders()` + l'historique d'ordres par fenêtre temporelle avant tout rejeu (§2.8 — « toute tentative de rejeu doit être précédée d'une interrogation de statut d'ordre »), et conserver le `client_order_id` en BDD (`paper_transactions`) pour la réconciliation, au lieu de la seule comparaison de quantités en float.

---

### PT-12 — Moyenne : Captures silencieuses `except Exception: pass`

**Localisations** : `signal_executor.py:90-91` (`datetime.now`), `signal_executor.py:456-457` (parse prix Redis — corruption de prix masquée), `api.py:406-407, 417-418, 444-445, 657, 659, 734-735, 743-744, 815-816` (caches best-effort), `trading212/resolver.py:80-81`.

Violation directe de §2.3 (« Interdiction de capturer `Exception` de manière générique et silencieuse »). Le cas le plus dommageable est le parse Redis : un payload de prix corrompu est ignoré sans trace, et le moteur bascule silencieusement sur SQL.

**Correction** : au minimum `logger.warning("...: %s", e)` avec contexte (ticker, payload tronqué) ; les chemins best-effort peuvent rester non bloquants mais doivent être visibles.

---

### PT-13 — Moyenne : Décisions de sortie live calculées en `float`

**Fichier** : `backtest_engine/live/paper_trading/signal_executor.py:887-961`

Les règles de sortie live (brackets SL/TP, trailing, safety stop) sont évaluées via `BrokerSimulator` alimenté en `float` (`broker.cash = float(qty * entry_price)`, `BrokerPosition(signed_quantity=float(qty), average_price=float(entry_price))`, `live_bar_dict["close"] = float(current_price)`). §2.2 impose `Decimal` pour toute la logique financière live. Les seuils de stop peuvent basculer sur des erreurs de représentation binaire (ex. `0.1 + 0.2`), déclenchant ou manquant une sortie.

**Correction** : soit porter les entrées des règles de sortie en `Decimal` dans le module broker (chemin live), soit encapsuler la conversion avec quantification explicite (`Decimal.quantize`) avant comparaison aux seuils.

---

### PT-14 — Moyenne : Keep-alive PostgreSQL bloquant dans la boucle asyncio

**Fichiers** : `backtest_engine/live/connection.py:182-200` ; `run_paper_trader.py:331-334`

`run_postgres_keep_alive_task` est une coroutine planifiée sur la boucle FastAPI qui exécute `get_db_connection()` (psycopg2 **bloquant**) directement, sans `asyncio.to_thread`. Pendant le round-trip BDD (toutes les 4 h), la boucle d'événements — y compris les endpoints API et le Kill Switch — est gelée.

**Correction** :

```python
await asyncio.to_thread(_heartbeat_once)  # envelopper le bloc psycopg2
```

---

### PT-15 — Moyenne : Branche morte d'attribution de ticker erronée

**Fichier** : `backtest_engine/live/paper_trading/signal_executor.py:427-432`

```python
if len(row) == 5:
    ticker = configs[0][2].lower() if configs else "unknown"
    timestamp, o, h, l, c = row
```

La requête retourne toujours 6 colonnes ; cette branche est morte. Si le `SELECT` est un jour modifié, **toutes** les bougies seront attribuées au ticker du premier config — corruption croisée des historiques de tous les actifs. Code mort dangereux à supprimer (§3.2).

---

## 4. Anomalies basses (détails condensés)

- **PT-16** (`connection.py:60-69`) : avec `DB_SSL_CERT`/`DB_SSL_KEY` mais sans `DB_SSL_CA`, le contexte mTLS passe en `CERT_NONE` + `check_hostname=False` — le serveur n'est plus authentifié. Exiger `DB_SSL_CA` ou échouer à l'init.
- **PT-17** (`spot_router.py:70-95`) : `reconciliation_attempts` n'étant pas persisté en BDD, l'objet reconstruit repart à 0 à chaque cycle — le garde-fou « max 10 tentatives » ne peut jamais se déclencher (le TTL 15 min de `_recover_order_state` reste le backstop effectif). Ajouter une colonne `reconciliation_attempts` + `ORDER BY created_at` sur le `LIMIT 1`.
- **PT-18** (`signal_executor.py:1192`) : `UTAMarginSimulator` recréé à chaque cycle → `_conversion_locked` (TTL 5 min) jamais persistant ; le verrou est un no-op. Instancier une fois dans le moteur.
- **PT-19** (`signal_executor.py:231-232`) : NAV par défaut 100 000/10 000 si la ligne de balance est absente → sizing Kelly fictif. Préférer `PortfolioUpdateError` (fail-closed).
- **PT-20** (transversal) : `print()` au lieu de `logger` dans `connection.py`, `bybit/ingestor.py`, `trading212/ingestor.py`, `bybit/client.py`, `trading212/client.py`, `resolver.py`, `bootstrapper.py`, `db_setup.py` — logs non structurés, invisibles du pipeline JSON (§2.2).
- **PT-21** (`signal_executor.py:293-294, 458-459` ; `utils.py:212-213`) : tracebacks `logger.exception()` sur erreurs réseau transitoires (Redis mget, API FX publiques) — §2.3 impose info/warning sans traceback quand la reconnexion gère le cas.
- **PT-22** (`db_setup.py`) : index absents sur `paper_transactions(timestamp)` (tri `ORDER BY timestamp DESC` paginé) et pour les lookups `LOWER(ticker)` sur `live_prices`/`live_candles_1m` (panic close, warm-up, API candles) — scans séquentiels croissants.
- **PT-23** (`trading212/client.py:33-46`) : `_last_call_times` muté sans verrou ; le client est appelé depuis la thread moteur et la thread kill switch (`asyncio.to_thread`). Verrou `threading.Lock` autour du throttle.
- **PT-24** (`signal_executor.py:739-740`) : `pos_key = (asset.lower(), strategy_name)` (2-uplet) contre clés `(asset, strategy, timeframe)` → lookup toujours vide. Sans impact actuel (branche `has_position=False` ⇒ quantité 0 correcte) — corriger ou supprimer pour éviter un faux sentiment de protection.
- **PT-25** (`spot_router.py:472-491` ; `accumulator.py:101-121`) : `client_order_id` « blocked-YYYYMMDDHHMMSS » → collision d'unicité si 2 blocages dans la même seconde (ajouter un suffixe UUID) ; `drain()` marque aussi les dépôts postérieurs à la soumission de l'ordre (borner par `created_at <= submitted_at`).
- **PT-26** (`engine.py:49-100`) : `_clients_warmed_up = True` même si l'init des deux brokers a échoué → aucun retry ultérieur ; une indisponibilité transitoire fige le mode « local-only » jusqu'au redémarrage. Réessayer périodiquement (p. ex. toutes les N cycles).

---

## 5. Points conformes (revus et validés)

- **Sécurité API** : middlewares dans `run_paper_trader.py` — auth par cookie de session HMAC (`compare_digest`), CSRF double-submit + contrainte `Content-Type: application/json`, rate limiting Redis (dont 5/5 min sur `/api/login`, 3/min sur panic/resume), security headers + HSTS, CORS restreint, `safe_error_response` avec UUID de corrélation en production.
- **Failsafe clés API** : validation SHA256 des clés Bybit et T212 dans les deux sens (démo↔live), fail-closed — conforme §2.2.
- **Kill Switch** : fail-closed sur indisponibilité Redis, `socket_keepalive=True` + `health_check_interval=30`, persistance avant notification, ordre des transitions correct (§2.8).
- **Concurrence BDD** : `FOR UPDATE` sur les lignes de balance, `DELETE ... RETURNING` contre les doubles clôtures, `lock_timeout` dans le panic close, sémaphore + timeout d'acquisition du pool psycopg2.
- **Anti-N+1** : NAV et évaluation des stratégies batchés (Redis `mget`, `ANY()`, `executemany`) — conforme §2.4 (hors panic close, cf. PT-10).
- **Réseau** : `NETWORK_TIMEOUT_DEFAULT = 10` appliqué aux clients brokers et au warm-up ; retries tenacity avec backoff exponentiel + 429/5xx ; heartbeat PostgreSQL.
- **Précision financière** : `Decimal` quasi systématique dans l'exécuteur et le pipeline de conversion (exceptions : PT-13, floats du throttling/réconciliation T212).
- **BDD** : contraintes `CHECK` d'intégrité financière (qty > 0, balances ≥ 0), unicités métier, migrations idempotentes versionnées (`schema_version`).

## 6. Recommandations priorisées

1. **PT-01** : ajouter `dry_run` au dataclass `ConversionOrder` et rendre le Step 0 fail-closed — avant toute activation de la conversion.
2. **PT-02** : normaliser la casse des tickers au warm-up + reprise des données historiques.
3. **PT-03** : purger l'URL Redis des logs (host seulement).
4. **PT-04** : restager le pipeline Redis après commit PG dans l'ingestor Bybit.
5. **PT-07** : câbler `deposit()` sur le SELL profitable (ou retirer le pipeline mort).
6. **PT-05, PT-06, PT-08, PT-09, PT-12** : corrections ciblées court terme.
7. Mettre en place un test de non-régression par anomalie corrigée (table de perspectives §5 : cas nominaux + bornes `qty=0`, `NAV=0`, prix stale, Redis down, PG down, double soumission).

---

*Rapport généré par audit manuel assisté — chaque anomalie citée a été vérifiée contre le code source avec numéros de ligne au 2026-07-26.*
