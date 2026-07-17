# Audit Frontend — Paper Trading (`backtest_engine/live/paper_trading/static`)

**Date de l'audit :** 17 juillet 2026
**Type :** audit statique de code (revue manuelle approfondie)
**Périmètre :** interface web du moteur de paper trading — `index.html`, `login.html`, `style.css`, `app.js`, `js/api.js`, `js/chart.js`, `js/login.js`, `js/ui.js`.
**Contexte lu en support :** `live/paper_trading/api.py` (contrat d'API), `live/kill_switch.py` (contrat d'état), `live/utils.py` (règle `is_crypto_asset`).

> **Limite de périmètre importante :** l'application FastAPI principale (qui monte les fichiers statiques et implémente `/api/login`, `/api/logout`, `/api/csrf-token`, `/vendor/*`, `/favicon.ico`) n'est **pas présente** dans le code fourni. Les constats liés à ces endpoints sont donc formulés comme des **points à vérifier** (section 2.6), pas comme des failles avérées.

---

## 1. Résumé exécutif

Le frontend est une **SPA vanilla JS en modules ES** (sans framework), bien organisée en 4 modules (`api`, `ui`, `chart`, `app`), servie par une API FastAPI/asyncpg. La qualité générale est **bonne pour un outil interne** : l'hygiène XSS est exemplaire (DOM construit exclusivement via `textContent`/`createTextNode`), l'intercepteur `fetch` centralise CSRF + gestion de session, les actions destructrices (liquidation, reprise) sont protégées par doubles confirmations, focus trap et états de chargement, et le polling est intelligent (dirty-flags via heartbeat plutôt que refetch systématique).

Trois défauts de fiabilité méritent toutefois une correction rapide, car ils affectent **l'exactitude des informations financières affichées** : un Profit Factor affiché « NaN », une course conditionnelle pouvant afficher les données d'un actif sur le graphique d'un autre, et un cache qui neutralise le rafraîchissement automatique des statuts de stratégies.

| Sévérité | Nombre | Thèmes dominants |
|---|---|---|
| 🔴 Élevée | 3 | Exactitude des données affichées (NaN, race condition, cache) |
| 🟠 Moyenne | 9 | Rafraîchissement, gestion d'erreurs, cohérence des plages de données |
| 🟡 Faible | 11 | i18n FR/EN, formatage, dette technique |
| ♿ Accessibilité | 7 | Clavier, lecteur d'écran, animations |
| ⚡ Performance | 2 | Polling onglet masqué, filtrage côté client |
| 🔎 À vérifier | 2 | Auth/CSP (hors périmètre), opportunités d'API |

**Appréciation globale : 7/10** — socle sain et sécuritaire côté XSS ; à consolider sur la fiabilité du rafraîchissement et l'accessibilité avant un usage quotidien intensif.

---

## 2. Constatations détaillées

### 2.1 🔴 Sévérité élevée

---

#### E-1 — Profit Factor affiché « NaN » quand la stratégie n'a aucune perte

**Fichiers :** `js/chart.js` (fonction `loadChart`) ↔ `api.py` (`_compute_performance_metrics_sync`)

Le backend sérialise le Profit Factor infini en `null` JSON :

```python
pf_val = None if profit_factor == float('inf') or profit_factor is None else profit_factor
```

Mais le frontend teste une chaîne qui n'arrive jamais :

```javascript
document.getElementById('analytic-profitfactor').textContent =
    perfData.profit_factor === 'Infinity' ? '∞' : parseFloat(perfData.profit_factor).toFixed(2);
```

Avec `profit_factor: null` → `parseFloat(null)` → `NaN` → affichage **« NaN »** dans le KPI. Cas déclencheur : toute stratégie avec uniquement des trades gagnants (fréquent en début de vie d'une config).

**Correctif recommandé :**

```javascript
const pf = perfData.profit_factor;
document.getElementById('analytic-profitfactor').textContent =
    (pf === null || pf === undefined) ? '∞' : Number(pf).toFixed(2);
```

---

#### E-2 — Course conditionnelle dans `loadChart` : données d'un actif affichées sur le graphique d'un autre

**Fichier :** `js/chart.js`

`loadChart` est `async` et partage un état au niveau module (`currentChart`, `candleSeries`, `equitySeries`, `bhSeries`, `currentAsset`). Deux appels concurrents peuvent s'entrelacer :

1. L'utilisateur sélectionne `BTCUSDT` → création du graphique, `currentAsset = 'BTCUSDT'`, requêtes lancées.
2. Il sélectionne vite `ETHUSDT` → graphique détruit puis recréé (les références module pointent vers le **nouveau** graphique), `currentAsset = 'ETHUSDT'`.
3. Les requêtes BTC aboutissent → `candleSeries.setData(bougies BTC)` s'applique au graphique ETH, avec markers et KPIs BTC.

Le même scénario existe entre le `change` manuel du sélecteur et le `loadChart` du polling toutes les 10 s (le verrou `isLoading` protège le polling entre ses propres cycles, mais pas contre un `change` utilisateur en vol). Symptôme utilisateur : bougies, courbes de NAV et métriques mélangées entre deux actifs — particulièrement trompeur sur un outil de trading.

**Correctif recommandé :** un jeton de requête (sequence guard) minimal :

```javascript
let chartRequestId = 0;

export async function loadChart(ticker, forceRefresh = false) {
    const requestId = ++chartRequestId;
    // ...
    const candlesData = await getCandles(ticker);
    if (requestId !== chartRequestId) return; // une requête plus récente a pris le relais
    // idem après chaque await (transactions, metrics)
}
```

(Un `AbortController` par requête est une variante acceptable.)

---

#### E-3 — Le cache des configurations neutralise le rafraîchissement périodique des statuts

**Fichier :** `app.js` (`fetchConfigs`, `setInterval`)

```javascript
const fetchConfigs = async () => {
    let data;
    if (cachedConfigs) {
        data = cachedConfigs;          // ← le polling retombe ici
    } else {
        data = await getConfigs();
        cachedConfigs = data;
    }
```

Le `setInterval` appelle bien `fetchConfigs()` toutes les 10 s quand l'onglet Configurations est actif — mais tant que `cachedConfigs` n'a pas été invalidé (toggle, édition, panic), **le rendu utilise le cache**. Conséquences à l'écran :

- le point « marché ouvert/fermé » (`market_open`) ne change jamais pendant la session ;
- un passage de statut `waiting_data` → `active`, ou l'apparition d'un statut `error` + `last_error` (tooltip), n'est **jamais visible spontanément** — exactement l'information qu'un opérateur surveille.

**Correctif recommandé :** ajouter un paramètre `forceRefresh = false` à `fetchConfigs` et l'appeler avec `true` depuis le polling (le cache ne sert alors plus que pour les interactions locales), ou supprimer ce cache au profit du dirty-flag heartbeat.

---

### 2.2 🟠 Sévérité moyenne

---

#### M-1 — Le tableau des Transactions n'est jamais auto-rafraîchi

**Fichier :** `app.js` (`setInterval`)

`changed.evaluations` déclenche `fetchEvaluations()`, mais `changed.transactions` ne sert qu'à invalider le cache du graphique. Sur l'onglet Transactions, une nouvelle exécution n'apparaît qu'après une action manuelle (changement d'onglet ou de page). Incohérent avec le dirty-flag disponible et avec le comportement de l'onglet Évaluations.

**Correctif :** dans le polling, `if (changed.transactions && onglet transactions actif) await fetchTransactions();`

---

#### M-2 — Aucune bougie disponible → retour silencieux, anciennes données laissées à l'écran

**Fichier :** `js/chart.js`

```javascript
if (candlesData.length === 0) {
    console.warn("No candle data fetched for active asset", ticker);
    return;
}
```

L'utilisateur voit le graphique précédent (ou vide) et d'anciens KPIs sans aucun message. Devrait afficher un état vide explicite (« Aucune donnée de marché pour cet actif ») et réinitialiser/masquer la grille d'analytics.

---

#### M-3 — Paramètres de requête non encodés

**Fichier :** `js/api.js` (`getPerformanceMetrics`, `getCandles`, `getTransactions`, `getEvaluations`)

```javascript
const res = await fetch(`/api/candles?ticker=${ticker}`);
```

Sans `encodeURIComponent(ticker)`. Les tickers actuels sont sûrs, mais un ticker contenant `&`, `+` ou `#` casserait la requête silencieusement.

---

#### M-4 — Gestion d'erreurs HTTP incomplète dans l'intercepteur

**Fichier :** `js/api.js`

- **403 non géré** : en cas d'échec CSRF (token expiré/rotation), aucune régénération du token ni retry — l'utilisateur reçoit juste « impossible de mettre à jour ».
- **404/422 non gérés** : les réponses d'erreur FastAPI contiennent un `detail` explicite (ex. règle de validation `indicator_params`) qui n'est jamais remonté ; l'UI n'affiche que `Status code: 422` dans la console technique.
- Les getters (`getPortfolio`, `getPositions`, …) font `res.json()` sans vérifier `res.ok` : un corps d'erreur JSON est ensuite traité comme des données (attrapé en amont par des `try/catch` qui se contentent de `console.error`, cf. M-5).

**Correctif :** ajouter un helper `parseApiError(res)` qui extrait `detail` et gérer le 403 en invalidant `cachedCsrfToken` + retry unique.

---

#### M-5 — Échecs de chargement silencieux sur des données financières

**Fichier :** `app.js` (`fetchPortfolio`, `fetchPositions`, `fetchConfigs`, `fetchTransactions`, `fetchEvaluations`)

Chaque `catch` se limite à `console.error(...)`. Sur un dashboard de trading, des KPIs de NAV/PnL **périmés sont visuellement indiscernables de valeurs fraîches**. Le heartbeat global signale l'état du moteur, pas l'échec d'une requête métier isolée (ex. `/api/positions` en 500 intermittent). Recommandé : toast d'erreur + marqueur visuel de péremption (ex. opacité réduite + horodatage « mis à jour à HH:MM:SS » sur chaque bloc).

---

#### M-6 — Collision de markers BUY/SELL sur la même minute

**Fichier :** `js/chart.js`

Les markers sont dédupliqués par timestamp minute (`seenTimes`) : un BUY et un SELL exécutés dans la même minute → **un seul marker conservé, silencieusement**. Sur des stratégies rapides (scalping 1m), le graphique peut omettre des exécutions. Alternative : autoriser plusieurs markers par minute en les empilant (lightweight-charts supporte plusieurs markers par barre) ou agréger en « BUY×n / SELL×n ».

---

#### M-7 — Plages de données incohérentes entre prix et courbes de performance

**Fichiers :** `js/api.js` ↔ `api.py`

- Bougies affichées : `GET /api/candles` → `limit` par défaut **1000** minutes (~16,6 h).
- Courbes NAV/B&H : `GET /api/performance/metrics` → calcul sur **5000** bougies (~3,5 j).

La courbe de performance s'étend donc ~5× plus loin dans le passé que la série de prix affichée sur le même graphique, avec deux échelles de prix superposées. La comparaison visuelle stratégie vs buy & hold s'en trouve biaisée. Recommandé : aligner les deux fenêtres (paramètre `limit` explicite commun, ex. 5000 pour les deux).

---

#### M-8 — Déconnexion par requête GET

**Fichier :** `index.html` (`<a href="/api/logout">`)

Une action à effet de bord (invalidation de session) en GET : rejouable par prefetch navigateur, non protégée par le jeton CSRF. Recommandé : POST `/api/logout` via bouton + passage du jeton CSRF (l'intercepteur le ferait automatiquement).

---

#### M-9 — Message d'erreur « CDN unpkg.com » obsolète

**Fichiers :** `js/chart.js` ↔ `index.html`

Le message d'erreur affiché quand `LightweightCharts` est indéfini parle du **CDN unpkg.com**, alors que la librairie est vendorée localement (`/vendor/lightweight-charts.standalone.production.js`). En cas d'échec réel (404 du vendor, montage statique absent), ce message oriente le diagnostic vers une fausse piste. À reformuler (« bibliothèque de graphiques introuvable — vérifier le déploiement du fichier vendor »).

---

### 2.3 🟡 Sévérité faible

| # | Constat | Fichier(s) | Détail / recommandation |
|---|---|---|---|
| F-1 | **i18n incohérent FR/EN** | `index.html`, `app.js`, `chart.js` | `lang="en"` sur la page alors que nav, toasts, pagination et tooltips mélangent FR et EN (« Évaluations », « Déconnexion », « Précédent/Suivant » vs « Engine Online », « Edit », « Save Changes »). Tooltips heartbeat en EN, toasts en FR. Choisir une langue unique (ou extraire un dictionnaire i18n) et aligner `lang`. |
| F-2 | **Locales de formatage mixtes** | `js/ui.js` | `formatCurrency` → `fr-FR`/EUR, `formatUSDT`/`formatCrypto` → `en-US`. Même écran, deux conventions de séparateurs (« 1 234,56 € » vs « 1,234.56 USDT »). |
| F-3 | **Quantités affichées en float brut** | `app.js` (positions, transactions) | `pos.qty` / `tx.qty` injectés sans formatage → artefacts binaires possibles (`0.30000000000000004`) et précision variable. Appliquer un `toLocaleString` avec `maximumFractionDigits` adapté (idéalement piloté par `quantity_precision`, déjà présent dans `indicator_params`). |
| F-4 | **Dérive de pagination** | `app.js`, `api.py` | Pagination `OFFSET/LIMIT` sur flux vivant trié DESC : une insertion entre deux pages décale les résultats (doublons/sauts). Pagination par curseur (`timestamp < cursor`) si le volume le justifie. |
| F-5 | **Doublons de logs à la reconnexion SSE** | `app.js` ↔ `api.py` | `/api/logs/stream` rejoue les 100 derniers logs à chaque connexion ; `EventSource` reconnecte automatiquement → lignes dupliquées dans la console. Dédupliquer côté client (clé timestamp+message) ou envoyer un marqueur de backlog. |
| F-6 | **Pas d'indicateur d'état du flux SSE** | `app.js` (`initLogsSSE`) | `onerror` ne fait que logguer ; l'utilisateur ne sait pas si la console est à jour. Un point d'état « flux connecté/reconnexion… » serait utile. |
| F-7 | **Prix `0` masqué** | `app.js` (`fetchEvaluations`) | `evalItem.price ? … : '-'` — un prix de 0 (edge case) s'affiche « - ». Préférer `!= null`. |
| F-8 | **Imports morts** | `app.js` (`formatPercent`), `js/chart.js` (`formatCurrency`, `formatUSDT`) | À retirer (hygiène). |
| F-9 | **Règle « crypto » dupliquée** | `app.js`, `js/ui.js` | `endsWith('usdt'/'usdc')` implémenté deux fois côté client alors que le backend centralise dans `utils.is_crypto_asset`. Si la règle évolue (ex. suffixe `EUR` perp), le frontend divergera. Exposer un champ `market`/`source` dans `/api/positions` plutôt que deviner côté client. |
| F-10 | **Token CSRF : course au démarrage, pas d'invalidation** | `js/api.js` | `ensureCsrfToken` sans déduplication de promesse → double `GET /api/csrf-token` si deux mutations partent simultanément au chargement ; pas de TTL ni d'invalidation sur 403 (cf. M-4). Mettre en cache la **promesse**. |
| F-11 | **Fuite potentielle du jeton CSRF** | `js/api.js` | L'intercepteur attache `X-CSRFToken` à **toute** URL passée à `fetch`. Aujourd'hui tout est same-origin, mais un futur appel tiers fuirait le jeton. Restreindre aux URLs same-origin (`new URL(url, location.origin).origin === location.origin`). |
| F-12 | **CSS login contradictoire** | `login.html` | `.alert { display:none }` vs `.alert-error { display:block }` — l'alerte serait visible par défaut sans le style inline qui la sauve. Nettoyer la cascade. |
| F-13 | **Duplication des variables CSS** | `login.html` vs `style.css` | Palette recopiée inline dans `login.html` → deux sources de vérité pour le thème. |

---

### 2.4 ♿ Accessibilité

Le socle est au-dessus de la moyenne (roles ARIA sur tables/modales/toasts/logs, `aria-label` dynamiques sur toggles et boutons d'édition, focus trap + restauration du focus dans les modales, `aria-live` sur kill switch et toasts). Points à corriger :

| # | Constat | Gravité | Recommandation |
|---|---|---|---|
| A-1 | **Fermetures de modales = `<span class="close-modal">`** : non focusables, non activables au clavier. Le JS leur ajoute un `aria-label`, ce qui ne suffit pas sur un élément non interactif. | Moyenne | Remplacer par `<button type="button" class="close-modal">`. |
| A-2 | **Focus clavier invisible sur les switchs** : l'input est masqué (`opacity:0; width:0; height:0`) et aucun style `:focus-visible` n'existe sur `.slider`. | Moyenne | `.switch input:focus-visible + .slider { outline: 2px solid var(--accent-primary); }` |
| A-3 | **Heartbeats T212/Bybit : information couleur + `title` uniquement** — inaccessible au clavier et aux lecteurs d'écran ; la couleur seule ne distingue pas `fresh`/`stale`/`offline` pour un daltonien. | Moyenne | Ajouter un texte/aria-label explicite (ex. « Flux Bybit : à jour, il y a 3 s ») en plus du point coloré. |
| A-4 | **Animations sans `prefers-reduced-motion`** : `blink-error` en boucle infinie, pulses, fadeIn. | Faible | Media query `@media (prefers-reduced-motion: reduce) { * { animation: none; } }` ciblée. |
| A-5 | **Console de logs en `role="log"` + `aria-live="polite"`** : en flux dense, un lecteur d'écran annonce en continu. | Faible | `aria-live="off"` par défaut, ou annoncer seulement les lignes `error`. |
| A-6 | **`scope="col"` manquant** sur les `<th>` des 4 tableaux. | Faible | Ajout trivial. |
| A-7 | **Pas d'alternative aux graphiques** (canvas Lightweight Charts) : aucun récapitulatif textuel/tabulaire des séries pour les non-voyants. | Faible | `aria-describedby` pointant vers la grille de KPIs + tableau repliable des points. |

**Autres constats rapides :** contraste de `--text-muted: #64748b` sur fond sombre limite pour les petits textes (≈ 4,0:1 sur `--bg-panel`) ; les badges `status-no-signal`/`status-waiting` (texte gris/jaune pâle sur fond translucide) sont sous les seuils WCAG AA — à vérifier avec un outil de contraste.

---

### 2.5 ⚡ Performance

| # | Constat | Recommandation |
|---|---|---|
| P-1 | **Polling 10 s maintenu onglet masqué** : chaque tick peut déclencher heartbeat + kill switch + configs + portfolio + positions + evaluations + candles(1000) + metrics(5000 bougies recalculées ou lues en cache) + transactions(5000). | Suspendre le polling quand `document.hidden`, reprendre + refresh immédiat au retour. |
| P-2 | **Filtrage client des transactions pour les markers** : `/api/transactions` n'a pas de filtre `asset` (alors que `/api/evaluations` en a un) → 5000 lignes téléchargées puis filtrées localement à chaque invalidation. | Ajouter un paramètre `asset` à l'endpoint et ne récupérer que l'actif affiché. |

**À noter (contrat) :** le cache Redis des metrics a un TTL de **300 s** côté backend alors que l'UI rafraîchit toutes les 10 s — l'utilisateur peut voir des KPIs figés jusqu'à 5 minutes sans indication de fraîcheur. Afficher l'horodatage de calcul ou réduire le TTL.

---

### 2.6 🔎 Contrat d'API & points à vérifier (hors périmètre du code fourni)

1. **Endpoints d'authentification absents du repomix** (`/api/login`, `/api/logout`, `/api/csrf-token`) ainsi que le montage statique (`/vendor/*`, `/favicon.ico`). Le frontend suppose : session par cookie, jeton CSRF en header `X-CSRFToken`, redirection 401. **À vérifier côté serveur :** cookie `HttpOnly; Secure; SameSite=Lax/Strict`, rotation du jeton à la connexion, rate limiting sur `/api/login`, en-têtes `Content-Security-Policy` (attention : `login.html` embarque du CSS inline → prévoir `style-src 'unsafe-inline'` ou déplacer le CSS), `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, et authentification effective de **toutes** les routes `/api/*` — y compris `/api/logs/stream` (EventSource n'envoie pas de headers custom, l'auth doit reposer sur le cookie).
2. **Opportunités d'API non exploitées par l'UI :** filtres `status`/`asset` de `/api/evaluations` (ajouter des filtres dans la vue), `kelly_weight` retourné par `/api/configs` mais jamais affiché, `last_updated` du portfolio non affiché (indicateur de fraîcheur des NAV), `updated_at` des positions inutilisé.

---

## 3. Points forts (à conserver)

- **Hygiène XSS exemplaire** : tout le contenu dynamique passe par `textContent`/`createTextNode`/`createElement` ; `innerHTML` uniquement pour du contenu statique (placeholder du graphique). Aucun `eval`, aucune interpolation HTML.
- **Intercepteur `fetch` centralisé** : injection CSRF automatique, redirection 401 → login, toasts génériques 500/503 avec détails techniques en console uniquement (pas de fuite d'erreurs internes vers l'UI).
- **Parcours des actions destructrices soigné** : double confirmation (liquidation), confirmation simple (reprise), focus trap + `Escape` + restauration du focus, états de chargement avec spinner, **rollback optimiste** du toggle en cas d'échec.
- **Polling économe** : dirty-flags (`last_transaction_time` / `last_evaluation_time` / `last_price_time`) plutôt que refetch systématique ; verrou anti-chevauchement `isLoading`.
- **Résilience** : librairie de graphiques vendorée localement (fonctionne sans CDN), gestion explicite de son absence, états vides des tableaux, buffer de logs DOM borné à 1000 lignes.
- **Backend aligné** : requêtes SQL paramétrées (pas d'injection), validation pydantic des configs (refus des structures imbriquées dans `indicator_params`), bornes `limit`/`offset`, calcul de metrics déporté hors event-loop (`asyncio.to_thread`), cache Redis avec timeouts, transaction SQL + verrous `FOR UPDATE` sur la liquidation.
- **Accessibilité de base présente** : roles `dialog`/`table`/`status`/`log`, `aria-modal`, `aria-live`, labels dynamiques — rare sur un outil interne.

---

## 4. Plan d'action priorisé

### P0 — Correctifs immédiats (< 1 j)
1. **E-1** Profit Factor : tester `null` au lieu de `'Infinity'`.
2. **E-3** `fetchConfigs(true)` depuis le polling (paramètre `forceRefresh`).
3. **E-2** Jeton de requête dans `loadChart` (anti-entrelacement).

### P1 — Fiabilité du rafraîchissement et des erreurs (1–2 j)
4. **M-1** Auto-rafraîchir le tableau Transactions via `changed.transactions`.
5. **M-5** Toasts + indicateur de péremption sur échec de chargement des blocs financiers.
6. **M-4** Gestion 403 (régénération CSRF + retry) et remontée des `detail` FastAPI (422).
7. **M-2** État vide explicite quand aucune bougie.
8. **M-3** `encodeURIComponent` sur les query params.
9. **M-9** Corriger le message « CDN unpkg ».
10. **M-7** Aligner les fenêtres candles/metrics (limit commun).

### P2 — Accessibilité & cohérence (2–3 j)
11. **A-1** `.close-modal` → `<button>`. **A-2** `:focus-visible` sur les switchs. **A-3** alternative textuelle aux heartbeats.
12. **F-1/F-2** Unification i18n (une langue, une locale de formatage par devise, `lang` cohérent).
13. **M-8** Logout en POST.
14. **F-3** Formatage des quantités. **F-5** Déduplication des logs SSE + indicateur de connexion.

### P3 — Confort & dette technique (au fil de l'eau)
15. **A-4** `prefers-reduced-motion`. **A-5** aria-live de la console. **A-6** `scope="col"`.
16. **P-1** Polling suspendu onglet masqué. **P-2** filtre `asset` sur `/api/transactions`.
17. Filtres status/asset dans la vue Évaluations ; affichage `kelly_weight` et horodatages de fraîcheur.
18. Refactorer `app.js` (~1100 lignes dans un seul `DOMContentLoaded`) en modules par vue (`dashboard.js`, `configs.js`, `logs.js`) pour testabilité ; supprimer les imports morts ; dédupliquer la règle crypto via un champ `source` de l'API.

---

*Fin du rapport.*