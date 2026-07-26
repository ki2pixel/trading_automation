# Rapport d'Audit Frontend — Paper Trading Dashboard

**Date** : 2026-07-17  
**Périmètre** : `backtest_engine/live/paper_trading/` + `run_paper_trader.py`  
**Fichiers audités** : 14 (1 API Python, 2 HTML, 1 CSS, 8 JS, 1 vendor, 1 serveur FastAPI)  
**Total anomalies détectées** : 23

---

## 🔴 Critiques (3)

### A-01 — Le SSE `/api/logs/stream` ne peut pas gérer un 401 correctement

| Champ | Détail |
|:---|:---|
| **Fichier** | `api.py` L461-500, `run_paper_trader.py` L123-127 |
| **Catégorie** | Fiabilité / Flux de données |
| **Description** | Le middleware `CookieSessionAuthMiddleware` retourne `application/json` pour tout path commençant par `/api/`. Or `EventSource` ne parse que `text/event-stream`. Quand le cookie de session expire, le navigateur reçoit du JSON au lieu d'un flux SSE. L'événement `onerror` se déclenche en boucle sans jamais rediriger vers la page de login — l'utilisateur voit une console de logs indéfiniment vide sans comprendre pourquoi. |
| **Correction** | Soit exclure `/api/logs/stream` du middleware d'auth (le SSE ne contient que des logs, rien de sensible au-delà de ce que l'auth protège déjà), soit ajouter un mécanisme côté frontend pour détecter un 401 via un endpoint `/api/auth-check` séparé. |

---

### A-02 — `RedisRateLimiterMiddleware` lève une exception non catchée si Redis est down

| Champ | Détail |
|:---|:---|
| **Fichier** | `run_paper_trader.py` L225 |
| **Catégorie** | Disponibilité |
| **Description** | L'appel `get_async_redis_client()` dans `RedisRateLimiterMiddleware.dispatch()` n'est pas wrappé dans un try-catch. Si la connexion Redis est rompue ou refuse la connexion, toutes les requêtes API traversant ce middleware lèvent une exception non gérée → 500 silencieuse. Le traitement `except Exception` à L255 ne couvre que les opérations d'incrémentation, pas l'initialisation du client. |
| **Correction** | Wrapper `get_async_redis_client()` dans un try-catch avec fallback "fail open" : si Redis est indisponible, logger un avertissement et laisser passer la requête sans rate limiting. |

---

### A-03 — Cache Redis `perf_metrics` non invalidé après un panic close

| Champ | Détail |
|:---|:---|
| **Fichier** | `api.py` L465 (setex TTL 300s), L360-395 (panic close) |
| **Catégorie** | Intégrité des données |
| **Description** | Le cache Redis des métriques de performance (`perf_metrics:{ticker}`) a un TTL de 300 secondes. Après une liquidation panic close, les positions sont fermées, les transactions insérées, mais le cache n'est pas invalidé. Le dashboard continue d'afficher des KPIs basés sur les données pré-liquidation pendant jusqu'à 5 minutes — profit factor, drawdown, equity curves fantômes. |
| **Correction** | Ajouter `redis_client.delete(f"perf_metrics:{ticker.lower()}")` dans la boucle de panic close (L393) pour chaque actif liquidé. |

---

## 🟠 Hautes (8)

### A-04 — GET `/api/logout` exposé

| Champ | Détail |
|:---|:---|
| **Fichier** | `api.py` L1072 |
| **Catégorie** | Sécurité |
| **Description** | Le décorateur `@router.get("/logout")` rend la déconnexion accessible via GET. Un attaquant peut forcer la déconnexion d'un utilisateur authentifié via `<img src="https://dashboard.example.com/api/logout">` sur une page tierce. Même avec `SameSite=strict`, une navigation top-level (clic sur un lien malveillant) déclenche la déconnexion. |
| **Correction** | Supprimer le handler GET et ne garder que POST. |

---

### A-05 — Absence de timeout sur les appels `fetch`

| Champ | Détail |
|:---|:---|
| **Fichier** | `api.js` L9-62 (interceptor), L66-168 (fonctions API) |
| **Catégorie** | Fiabilité |
| **Description** | Aucun appel `fetch` n'utilise `AbortController` avec timeout. Si le serveur hang (deadlock BDD, timeout réseau non résolu), la promesse n'est jamais résolue ni rejetée. Le flag `isLoading` dans `app.js` reste bloqué à `true` indéfiniment, paralysant tout le cycle de polling. |
| **Correction** | Ajouter un `AbortController` avec timeout de 15 secondes sur chaque appel fetch dans les fonctions wrapper d'`api.js`. |

---

### A-06 — Token CSRF jamais rafraîchi automatiquement après 403

| Champ | Détail |
|:---|:---|
| **Fichier** | `api.js` L71-72 |
| **Catégorie** | UX / Fiabilité |
| **Description** | Quand le serveur retourne 403 (CSRF token expiré ou invalide), l'interceptor affiche un toast "Please refresh the page" mais ne tente pas de récupérer un nouveau token via `/api/csrf-token`. L'utilisateur doit recharger manuellement la page entière. |
| **Correction** | Dans le handler 403, appeler `cachedCsrfToken = null` puis `ensureCsrfToken()`, puis réessayer la requête originale une fois avant d'afficher l'erreur. |

---

### A-07 — `triggerImmediateRefresh` écrase `isLoading = false`

| Champ | Détail |
|:---|:---|
| **Fichier** | `app.js` L230-233 |
| **Catégorie** | Race condition |
| **Description** | Quand l'utilisateur revient sur l'onglet (`visibilitychange` → visible), `triggerImmediateRefresh()` force `isLoading = false` puis lance `runPollingCycle()`. Si un cycle de polling était déjà en cours (`isLoading=true`), ce reset permet à deux cycles de s'exécuter en parallèle — requêtes concurrentes, potentiellement corruption d'état ou double rendu. |
| **Correction** | Remplacer `isLoading = false` par un check : si `isLoading` est déjà `true`, ne pas lancer de nouveau cycle. |

---

### A-08 — Attribut `lang` incohérent entre les pages

| Champ | Détail |
|:---|:---|
| **Fichiers** | `index.html` L1, `login.html` L1 |
| **Catégorie** | Accessibilité (WCAG 3.1.1) |
| **Description** | `index.html` a `lang="en"` mais contient du texte français ("Évaluations Récentes", "Actif", "Stratégie", "Précédent", "Suivant"). `login.html` a `lang="fr"` mais contient de l'anglais ("Please log in", "Username", "Password", "Log In"). Les lecteurs d'écran appliquent une prononciation incorrecte. |
| **Correction** | Uniformiser : tout passer en `lang="en"` et traduire les chaînes françaises restantes dans `index.html`, ou inversement. La stratégie actuelle de l'application est l'anglais (les logs, les statuts, les messages d'erreur sont en anglais), donc `lang="en"` partout. |

---

### A-09 — Absence de règle `prefers-reduced-motion`

| Champ | Détail |
|:---|:---|
| **Fichier** | `style.css` L2-32 (variables), L520-620 (animations) |
| **Catégorie** | Accessibilité (WCAG 2.3.3) |
| **Description** | Les animations `heartbeat-pulse`, `fadeIn`, `zoomIn`, `blink-error`, `status-pulse`, `status-pulse-offline` et `button-loading-spinner` s'exécutent sans condition. Les utilisateurs ayant activé `prefers-reduced-motion: reduce` au niveau OS subissent ces animations, ce qui peut causer des nausées ou migraines (vestibular disorders). |
| **Correction** | Ajouter une media query : `@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; } }` |

---

### A-10 — Contraste insuffisant sur le bouton Resume

| Champ | Détail |
|:---|:---|
| **Fichier** | `style.css` L648-662 |
| **Catégorie** | Accessibilité (WCAG 1.4.3) |
| **Description** | `.btn-confirm-resume` utilise `color: #052e16` (vert très foncé) sur `background: #10b981` (vert émeraude). Ratio de contraste ≈ 2.1:1, très en dessous du minimum WCAG AA de 4.5:1 pour du texte normal. Le texte est quasi illisible. |
| **Correction** | Remplacer `color: #052e16` par `color: #ffffff`. |

---

### A-11 — Double mécanisme de rate limiting incohérent

| Champ | Détail |
|:---|:---|
| **Fichiers** | `api.py` L28-29 (`slowapi.Limiter`), `run_paper_trader.py` L218-222 (`RedisRateLimiterMiddleware`) |
| **Catégorie** | Maintenabilité |
| **Description** | Deux systèmes de rate limiting coexistent : `slowapi.Limiter` (in-memory, appliqué uniquement sur `/api/control/panic` et `/api/control/resume` + `/api/login`) et `RedisRateLimiterMiddleware` (Redis, appliqué sur tous les `/api/*`). Deux sources de vérité, deux comportements de backoff, debugging complexifié. |
| **Correction** | Supprimer `slowapi` et centraliser tout le rate limiting dans `RedisRateLimiterMiddleware` avec des limites configurables par path. |

---

## 🟡 Moyennes (12)

### A-12 — Pas de debounce sur le changement d'onglet

| Champ | Détail |
|:---|:---|
| **Fichier** | `app.js` L50-65 |
| **Catégorie** | Performance |
| **Description** | Chaque clic sur un onglet de navigation déclenche un fetch immédiat. Un clic rapide sur 3 onglets lance 3 requêtes simultanées, gaspillant des connexions à la base de données. |
| **Correction** | Ajouter un debounce de 200ms sur le handler de clic des `nav-item`. |

---

### A-13 — Filtrage des transactions côté client

| Champ | Détail |
|:---|:---|
| **Fichier** | `chart.js` L168-190 |
| **Catégorie** | Performance |
| **Description** | `getTransactions(5000, 0)` fetch toutes les transactions sans filtre, puis `filter(tx => tx.asset.toLowerCase() === ticker.toLowerCase())` en JS. Pour 10 000+ trades historiques, gaspillage de bande passante et de mémoire côté client. |
| **Correction** | Ajouter un paramètre `asset` optionnel à l'endpoint `/api/transactions` et au wrapper `getTransactions()`. |

---

### A-14 — Message d'erreur trompeur "CDN Offline"

| Champ | Détail |
|:---|:---|
| **Fichier** | `chart.js` L31-37 |
| **Catégorie** | Expérience utilisateur |
| **Description** | Quand `LightweightCharts` est `undefined`, le message affiché dit "Unable to load the charts library from the CDN (unpkg.com)". Or la librairie est servie localement via `/vendor/lightweight-charts.standalone.production.js`. Si le fichier est cassé ou 404 à cause de `StaticFiles`, l'utilisateur reçoit un message parlant de CDN externe — diagnostic incorrect. |
| **Correction** | Remplacer le message par "Chart library failed to load. The local vendor bundle may be missing or corrupted." |

---

### A-15 — Burst de requêtes après panic close

| Champ | Détail |
|:---|:---|
| **Fichier** | `modules/dashboard.js` L355-375 |
| **Catégorie** | Architecture |
| **Description** | Le callback `onPanicSuccess` déclenche simultanément `fetchPortfolio()`, `fetchPositions()`, `fetchTransactions()`, `loadChart()` + `fetchPerformanceMetrics()` (dans loadChart), et `fetchKillSwitchStatus()`. Jusqu'à 6 requêtes concurrentes vers la BDD — contention inutile. |
| **Correction** | Sérialiser les appels ou les grouper via `Promise.all` par priorité (données critiques d'abord : portfolio + positions + kill switch, puis transactions + chart). |

---

### A-16 — SSE continue de traiter les logs quand l'onglet est caché

| Champ | Détail |
|:---|:---|
| **Fichier** | `modules/logs.js` L268-278 |
| **Catégorie** | Performance |
| **Description** | Contrairement au polling (stoppé via `visibilitychange` dans `app.js`), la connexion SSE reste active quand l'utilisateur change d'onglet. Les logs continuent d'être reçus, parsés, et ajoutés au DOM (même avec un cap de 1000 lignes). |
| **Correction** | Écouter `document.addEventListener('visibilitychange', ...)` et fermer/réouvrir l'EventSource selon l'état de visibilité. |

---

### A-17 — Cap DOM utilise `childNodes` au lieu de `children`

| Champ | Détail |
|:---|:---|
| **Fichier** | `modules/logs.js` L296 |
| **Catégorie** | Bug |
| **Description** | La vérification `if (consoleOutput.childNodes.length > 1000)` compte les nœuds texte (espaces, retours à la ligne entre éléments) en plus des éléments `.log-line`. Le nombre réel de lignes de log visibles est donc inférieur à 1000, parfois significativement selon le navigateur. |
| **Correction** | Remplacer `childNodes.length` par `children.length`. |

---

### A-18 — `aria-describedby` manquant sur la modale de panic

| Champ | Détail |
|:---|:---|
| **Fichier** | `index.html` L363-388 |
| **Catégorie** | Accessibilité (WCAG 4.1.2) |
| **Description** | Le texte d'avertissement "This will immediately sell all open positions..." n'est pas lié au `role="dialog"` via `aria-describedby`. Les lecteurs d'écran n'annoncent pas automatiquement ce contenu crucial à l'ouverture de la modale. |
| **Correction** | Ajouter `aria-describedby="panic-modal-desc"` sur le `div[role="dialog"]` et `id="panic-modal-desc"` sur le `<p class="modal-warning-text">`. |

---

### A-19 — Toast disparaît même au survol

| Champ | Détail |
|:---|:---|
| **Fichier** | `ui.js` L60-70 |
| **Catégorie** | UX |
| **Description** | Le `setTimeout` d'auto-suppression (4 secondes) n'est pas annulé au `mouseenter`. Si l'utilisateur lit un message d'erreur long, le toast disparaît avant la fin de la lecture, sans possibilité de le maintenir. |
| **Correction** | Ajouter `toast.addEventListener('mouseenter', () => clearTimeout(autoRemoveTimer))` et relancer le timer au `mouseleave`. |

---

### A-20 — Pas de `prefers-color-scheme: light`

| Champ | Détail |
|:---|:---|
| **Fichier** | `style.css` L2-32 (variables) |
| **Catégorie** | Accessibilité |
| **Description** | Le thème sombre est imposé sans alternative. Certains utilisateurs dyslexiques ou malvoyants préfèrent le mode clair pour un meilleur contraste. Aucune media query `prefers-color-scheme: light` ni toggle de thème. |
| **Correction** | Ajouter un thème clair alternatif via `prefers-color-scheme: light` avec des variables CSS distinctes. |

---

### A-21 — `backdrop-filter: blur()` sans fallback

| Champ | Détail |
|:---|:---|
| **Fichier** | `style.css` L40-55 |
| **Catégorie** | Compatibilité |
| **Description** | Les panneaux `.glass-panel` utilisent `backdrop-filter: blur(16px)` sans `background` opaque en fallback. Sur les navigateurs ne supportant pas `backdrop-filter` (Firefox < 103, navigateurs embarqués anciens), les panneaux deviennent semi-transparents sans flou, rendant le texte illisible sur le fond texturé. |
| **Correction** | Définir un `background: rgba(22, 30, 49, 0.95)` en fallback avant la règle avec `backdrop-filter`. |

---

### A-22 — Pas de `@media print`

| Champ | Détail |
|:---|:---|
| **Fichier** | `style.css` global |
| **Catégorie** | Maintenabilité |
| **Description** | Aucune règle d'impression. L'impression du dashboard (ex: rapport de positions pour un audit, capture des configurations) produit un layout cassé avec le sidebar, les fonds sombres, et les glass panels. |
| **Correction** | Ajouter `@media print { .sidebar, .top-header, .toast-container { display: none; } .main-content { overflow: visible; } ... }` |

---

### A-23 — Timeout Redis systématique de 2 secondes

| Champ | Détail |
|:---|:---|
| **Fichier** | `api.py` L893-900 |
| **Catégorie** | Performance |
| **Description** | Chaque opération Redis (`get`, `setex`) est wrappée dans `asyncio.wait_for(..., timeout=2.0)`. Dans `/api/candles`, il y a jusqu'à 4 opérations Redis (cache get, pool acquire, cache set). En cas de latence Redis, chaque opération bloque jusqu'à 2 secondes — jusqu'à 8 secondes de blocage au total pour une seule requête. |
| **Correction** | Réduire le timeout à 500ms pour les opérations de cache et considérer un circuit breaker : après N échecs consécutifs, bypasser Redis pour une durée T. |

---

## Résumé des actions par priorité

| Priorité | IDs | Effort estimé |
|:---|:---|:---|
| Immédiat | A-01, A-02, A-03 | ~2h |
| Cette semaine | A-04, A-05, A-06, A-07 | ~3h |
| Ce sprint | A-08, A-09, A-10, A-11 | ~2h |
| Backlog | A-12 à A-23 | ~8h |
