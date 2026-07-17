# Plan d'Audit — Frontend Paper Trading

## Scope

Audit complet du frontend et des interactions frontend↔backend du module paper trading, ciblé sur les fichiers de `backtest_engine/live/paper_trading/static/` (frontend réel) et `backtest_engine/live/paper_trading/api.py` (backend).

Les fichiers `backtest_engine/web_static/` ont été lus mais sont une version **obsolète/divergente** du frontend — ils ne sont pas servis en production. L'audit se concentre sur le frontend réel dans `live/paper_trading/static/`.

---

## Fichiers audités

### Frontend réel (6 fichiers)
| Fichier | Taille | Statut |
|---|---|---|
| `live/paper_trading/static/index.html` | 24.6 KB | Dashboard principal |
| `live/paper_trading/static/login.html` | 5.9 KB | Page de login (CSS inline) |
| `live/paper_trading/static/style.css` | 28 KB | Styles globaux (responsive, glassmorphism) |
| `live/paper_trading/static/app.js` | 46.6 KB | Logique dashboard (modules ES6) |
| `live/paper_trading/static/js/api.js` | 4 KB | Client API + CSRF interceptor |
| `live/paper_trading/static/js/login.js` | 1.8 KB | Login form handler |
| `live/paper_trading/static/js/chart.js` | 8.3 KB | Lightweight Charts rendering |
| `live/paper_trading/static/js/ui.js` | 2.9 KB | Formatters, toasts, boutons |
| `live/paper_trading/static/vendor/lightweight-charts.standalone.production.js` | 161 KB | Vendor bundle local |

### Backend Paper Trading (7 fichiers)
| Fichier | Taille | Rôle |
|---|---|---|
| `live/paper_trading/api.py` | 892 lignes | Endpoints REST (FastAPI APIRouter) |
| `live/paper_trading/signal_executor.py` | 1178 lignes | Exécution des signaux |
| `live/paper_trading/engine.py` | 157 lignes | Orchestrateur paper trading |
| `live/paper_trading/exceptions.py` | 13 lignes | Exceptions métier |
| `live/kill_switch.py` | 433 lignes | Circuit breaker global |
| `live/connection.py` | 557 lignes | Redis (dont FailoverRedisClient) |
| `live/controls.py` | 83 lignes | PreTradeController |
| `live/utils.py` | 220 lignes | Utilitaires (market hours, Decimal) |

---

## Anomalies identifiées — Classification

### 🔴 CRITIQUE — Backend manquant

#### A1. `/api/login` et `/api/csrf-token` NON IMPLÉMENTÉS
**Fichiers** : `api.js:13`, `login.js:25`, `login.html:178`
**Description** : Le frontend appelle `/api/csrf-token` (pour le token CSRF) et `/api/login` (pour l'authentification). Aucun de ces endpoints n'existe dans `api.py` ni dans aucun autre fichier Python du projet (`backtest_engine/`). Aucun `main.py` n'existe pour monter l'app FastAPI.
**Impact** : Login et protection CSRF entièrement non fonctionnels. Le frontend ne peut pas s'authentifier. Si un autre mécanisme contourne ça (ex: reverse proxy), la chaîne CSRF est brisée — toutes les mutations POST/PUT/DELETE sont sans protection réelle.
**Règle violée** : AGENTS.md §2.9 (garde-fous), §2.3 (exceptions d'affaires), §6.1 (sécurité)
**Correction** : Implémenter les endpoints manquants :
- `POST /api/login` — validation credentials + session cookie sécurisé (`HttpOnly`, `Secure`, `SameSite=Strict`)
- `GET /api/csrf-token` — génération token CSRF couplé à la session
- Configurer le cookie de session avec `SameSite=Strict` pour que le CSRF double-submit cookie pattern fonctionne

#### A2. Pas de rate limiting visible sur `/api/login`
**Fichier** : `login.js:25-44`
**Description** : Aucun throttling, délai progressif, ou CAPTCHA côté frontend ni backend pour `/api/login`. Vulnérable au brute force.
**Impact** : Credential stuffing / brute force possible sans détection.
**Règle violée** : AGENTS.md §2.8 (rate limiting), §6.1 (sécurité)
**Correction** : Ajouter rate limiting côté backend (ex: 5 tentatives / 5 minutes par IP + délai exponentiel), et désactiver le bouton submit avec cooldown progressif côté frontend après échecs répétés.

### 🔴 CRITIQUE — Sécurité Frontend

#### A3. Pas de Content-Security-Policy (CSP)
**Fichiers** : `index.html`, `login.html`
**Description** : Aucun meta tag ou header HTTP `Content-Security-Policy`. Les scripts sont chargés en module ES6 (`<script type="module">`), ce qui limite le risque XSS inline, mais l'absence de CSP laisse la porte ouverte aux injections dans d'autres contextes (styles, images, connect-src).
**Impact** : Surface d'attaque XSS élargie. Pas de protection contre les injections de scripts externes malveillants.
**Règle violée** : AGENTS.md §6.1 (sécurité)
**Correction** : Ajouter une CSP stricte dans `index.html` et `login.html` :
```html
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self';">
```
Note : `'unsafe-inline'` sur `style-src` est nécessaire car `login.html` a du CSS inline et `app.js` manipule du style inline dynamiquement. Alternative : externaliser le CSS de login.html.

### 🟡 HAUTE — Concurrence / Thread-Safety Backend

#### A4. Race condition TOCTOU dans `FailoverRedisClient._is_failed_over`
**Fichier** : `connection.py:400`
**Description** : Le flag `_is_failed_over` (booléen) est lu puis écrit sans lock. Deux threads concurrents pourraient tous les deux entrer dans `_failover()` simultanément (check-then-act).
**Impact** : Double failover → état Redis corrompu, perte de messages Pub/Sub, potentiellement deux clients primaires.
**Règle violée** : AGENTS.md §2.5 (thread-safety)
**Correction** : Protéger la section critique avec `threading.Lock` :
```python
self._failover_lock = threading.Lock()
# ...
with self._failover_lock:
    if not self._is_failed_over:
        self._failover()
```

#### A5. `_trading_suspended` globale sans barrière mémoire explicite
**Fichier** : `kill_switch.py:18`
**Description** : Flag booléen lu/écrit depuis `asyncio.to_thread` et la boucle principale sans lock. Le GIL rend l'accès atomique mais sans barrière mémoire, une écriture peut ne pas être visible immédiatement.
**Impact** : Délai de propagation du kill switch (quelques ms) — tolérable pour un circuit breaker non critique en latence.
**Sévérité réelle** : Faible. Le GIL garantit l'atomicité des lectures/écritures de booléens en Python. Acceptable en l'état pour un kill switch.
**Action** : Pas de correction urgente. Documenter le choix architectural.

### 🟡 HAUTE — Résilience Frontend

#### A6. Pas de reconnexion automatique SSE (EventSource)
**Fichier** : `app.js` (EventSource natif pour les logs SSE)
**Description** : L'API `EventSource` native reconnecte automatiquement avec un délai par défaut (~3s), mais aucun handler `onerror` personnalisé n'est défini. En cas d'échec de reconnexion prolongé, l'utilisateur n'est pas notifié et les logs cessent de s'afficher silencieusement.
**Impact** : Perte silencieuse du flux de logs → l'opérateur ne voit plus les événements temps réel sans s'en rendre compte.
**Règle violée** : AGENTS.md §2.8 (résilience réseau)
**Correction** : Ajouter un handler `onerror` qui :
1. Logge l'erreur dans la console
2. Affiche un toast warning si la reconnexion échoue après N tentatives
3. Réinitialise proprement l'EventSource après un échec critique

### 🟢 MOYENNE — Qualité Backend

#### A7. `except Exception: pass` pour fallbacks Redis
**Fichier** : `api.py` (pattern récurrent)
**Description** : Les fallbacks Redis utilisent `except Exception: pass` pour masquer les erreurs quand Redis est down. C'est acceptable car Redis est un cache non critique, mais `Exception` attrape tout — y compris `KeyboardInterrupt`, `SystemExit`, et des erreurs de configuration qui devraient être visibles.
**Impact** : Erreurs de configuration Redis masquées → débogage difficile.
**Règle violée** : AGENTS.md §2.3 (exceptions spécifiques)
**Correction** : Remplacer par `except (redis.RedisError, OSError, ConnectionError):` pour n'attraper que les erreurs réseau/Redis légitimes.

#### A8. Pas de middleware global d'erreur FastAPI
**Fichier** : `api.py`
**Description** : Les endpoints gèrent `HTTPException` et `asyncpg.PostgresError` individuellement. Pas de handler global `@app.exception_handler(Exception)` conforme à la règle §2.3 (`safe_error_response(exc, request)` avec UUID de corrélation).
**Impact** : En production sans `DEBUG=true`, une exception non gérée expose potentiellement une trace dans la réponse 500 par défaut de FastAPI.
**Règle violée** : AGENTS.md §2.3 (masquage en production)
**Correction** : Ajouter un exception handler global qui logge le traceback complet côté serveur mais retourne un message générique + UUID au client.

### 🟢 MOYENNE — Frontend

#### A9. `login.html` : CSS inline massif (160+ lignes)
**Fichier** : `login.html:9-167`
**Description** : Tout le CSS de la page de login est dans une balise `<style>` inline. Fonctionnel mais viole la séparation des préoccupations. Le CSP devrait autoriser `'unsafe-inline'` pour style-src à cause de ça.
**Impact** : Maintenance plus difficile, CSP moins strict.
**Action** : Externaliser dans `style.css` (les variables CSS sont déjà définies là-bas). Optionnel — pas bloquant.

#### A10. `index.html` : `type="module"` sur `app.js` sans fallback
**Fichier** : `index.html:414`
**Description** : `<script type="module" src="app.js"></script>` sans `nomodule` fallback. Tous les navigateurs modernes supportent les modules ES6 — acceptable.
**Impact** : Aucun en pratique (caniuse: 97%+ support). Pas d'action requise.

---

## Points positifs notables (conformité)

| Point | Fichier | Règle |
|---|---|---|
| **Lightweight Charts en vendor bundle local** (161 KB) — pas de CDN, pas de SRI nécessaire | `static/vendor/` | §6.1 |
| **Architecture modules ES6** (`import`/`export`) — code moderne, bien structuré | `app.js`, `chart.js`, `api.js`, `ui.js` | §2.1 |
| **Polling 10s avec dirty flag** — compare `last_transaction_time`/`last_evaluation_time`/`last_price_time` → rafraîchit seulement ce qui a changé | `app.js` | §2.4 |
| **Kill Switch UI avec double confirmation** — checkbox avant liquidation + checkbox avant resume → safety UX | `index.html` | §2.9 |
| **Accessibilité modale** — `setupModalAccessibility` gère focus trap, Escape, `aria-modal` | `app.js` | Bonne pratique |
| **Fetch interceptor global** — gestion 401→redirect login, 500/503→toast error, network error→message | `api.js` | §2.3 |
| **Formatters multidevises** — EUR (Intl), USDT, Crypto avec détection automatique | `ui.js` | §2.2 |
| **CSRF token caching** — `ensureCsrfToken()` cache le token en mémoire, évite requête par appel | `api.js` | §2.4 |
| **`login.js` gère `?error=true`** — redirect password manager avec message d'erreur | `login.js` | Bonne pratique |
| **Responsive design complet** — media queries pour mobile, sidebar collapsible | `style.css` | Bonne pratique |
| **Glassmorphism cohérent** — variables CSS, thème sombre, effets cohérents | `style.css` | §2.1 |
| **Decimal pour calculs financiers** — `panic_close_all`, `signal_executor` utilisent `Decimal` | `signal_executor.py`, `api.py` | §2.2 |
| **`FOR UPDATE` locks** — transactions avec verrous explicites | `signal_executor.py` | §2.5 |
| **Batched I/O anti-N+1** — `update_portfolio_nav` utilise `mget()` + `ANY()` + `executemany()` | `signal_executor.py` | §2.4 |
| **FailoverRedisClient** — failover transparent avec replay pipeline | `connection.py` | §2.8 |
| **KillSwitchListener** — TCP keepalive + `health_check_interval=30` | `kill_switch.py` | §2.8 |
| **`asyncio.to_thread`** pour calculs bloquants — non-bloquant pour la boucle asyncio | `api.py` | §2.5 |
| **PreTradeController** — vérifications volumétriques, notional, price collar | `controls.py` | §2.9 |
| **`market_hours.json` chargé avec `current_time` paramétrable** — testable | `utils.py` | §2.1 |
| **Timeout réseau centralisé** — `NETWORK_TIMEOUT_DEFAULT = 10` | `utils.py` | §2.2 |

---

## Priorités de correction

### Phase 1 — Bloquant (sécurité)
1. **Implémenter `/api/login` et `/api/csrf-token`** (A1) — le système d'auth est inexistant
2. **Ajouter CSP headers** (A3) — protection XSS baseline
3. **Ajouter rate limiting sur `/api/login`** (A2) — anti brute-force

### Phase 2 — Robustesse
4. **Corriger race condition FailoverRedisClient** (A4) — éviter corruption Redis
5. **Ajouter middleware global d'erreur FastAPI** (A8) — masquage production
6. **Remplacer `except Exception: pass` par exceptions Redis typées** (A7)

### Phase 3 — Résilience
7. **Ajouter handler onerror SSE avec notification utilisateur** (A6)

### Phase 4 — Cosmétique (optionnel)
8. Externaliser le CSS de `login.html` (A9)

---

## Vérification post-correction

- Tests : `pytest` sur les nouveaux endpoints `/api/login` et `/api/csrf-token`
- Vérification CSP : inspecter les headers HTTP dans la réponse
- Vérification rate limiting : simuler 10 tentatives rapides → vérifier blocage
- Vérification race condition : test concurrentiel sur FailoverRedisClient
- Smoke test frontend : login → dashboard → sélection asset → chart → modale panic/resume