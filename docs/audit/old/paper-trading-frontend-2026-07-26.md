# Audit Frontend — Paper Trading (`backtest_engine/live/paper_trading/static/`)

- **Date** : 2026-07-26
- **Périmètre** : `backtest_engine/live/paper_trading/static/` (2 HTML, 1 CSS, 8 JS, 1 vendor, ~3 900 lignes hors vendor) — avec vérifications croisées du contrat API dans `backtest_engine/live/paper_trading/api.py` (1 126 lignes) et `run_paper_trader.py` (middlewares, 469 lignes).
- **Méthode** : lecture intégrale du périmètre, vérification de chaque anomalie contre le code réel (numéros de ligne exacts), contre-vérification des 23 anomalies de l'audit frontend du 2026-07-17, référentiel d'invariants `AGENTS.md` §2 (standards) et §3 (protocole d'audit).
- **Statut** : **REQUEST CHANGES** — 0 critique, 2 hautes, 5 moyennes, 8 basses (15 nouvelles anomalies).

---

## 1. Synthèse

La remédiation de l'audit du 2026-07-17 est **quasi exhaustive : 22 anomalies sur 23 corrigées**, dont la totalité des critiques et des hautes (SSE 401, rate limiter fail-open, invalidation cache après panic, logout en GET, timeouts fetch, retry CSRF, race `isLoading`, accessibilité WCAG). Seule A-08 (`lang` incohérent) subsiste partiellement sur `index.html`.

L'état actuel est sain sur les fondamentaux : rendu DOM systématiquement via `textContent`/`createElement` (pas d'injection dans les tableaux), intercepteur `fetch` centralisé avec timeout 15 s, CSRF double-submit avec retry automatique, CSP restrictive (`script-src 'self'`), modales avec focus trap et restauration de focus, polling suspendu quand l'onglet est caché.

Les risques majeurs identifiés sont :

1. Une **perte de transactions en pagination par curseur** : le panic close insère N transactions avec un `CURRENT_TIMESTAMP` identique dans une seule transaction SQL, et le curseur `WHERE timestamp < $1` exclut toutes les lignes partageant le timestamp de rupture de page — l'historique paginé devient incomplet exactement au moment le plus critique (liquidation d'urgence).
2. Un **rate limiting agrégé derrière le proxy** : `request.client.host` vaut l'IP du load balancer Render (X-Forwarded-For ignoré faute de `forwarded_allow_ips`), mutualisant le quota de login (5/5 min) entre tous les visiteurs — verrouillage collectif du login trivial à provoquer.
3. Une **duplication des logs SSE à chaque reconnexion** (le serveur renvoie les 100 dernières entrées, le client ne déduplique pas).
4. Une **session stateless de 30 jours non révocable** : le logout ne supprime que le cookie côté client ; un token HMAC copié reste valide un mois, avec accès au bouton panic.

## 2. Tableau des anomalies (nouvelles)

| Identifiant | Catégorie de Risque | Conséquence en Production | Sévérité |
| :---- | :---- | :---- | :---- |
| F-01 | Intégrité données / Logique | Pagination des transactions incomplète : toutes les lignes au même timestamp que la rupture de page sont sautées (cas systématique du panic close, `CURRENT_TIMESTAMP` unique par transaction SQL). | Haute |
| F-02 | Disponibilité / Sécurité | Rate limit par IP mutualisé derrière le LB Render : 5 échecs de login/5 min pour **tous les utilisateurs confondus** → déni de service du login ; quotas 60 req/min partagés. | Haute |
| F-03 | Observabilité / UX | Jusqu'à 100 lignes de logs dupliquées dans la console à chaque reconnexion SSE (changement d'onglet inclus). | Moyenne |
| F-04 | Sécurité session | Token de session stateless 30 jours, non révocable ; logout purement cosmétique côté serveur ; un token exfiltré donne accès au panic pendant 30 jours. | Moyenne |
| F-05 | Sécurité (XSS) | `innerHTML` interpolé avec `${ticker}` (donnée BDD) dans les placeholders du chart — XSS stockée latente si un ticker malveillant entre en base. | Moyenne |
| F-06 | Contrat API / Validation | `ConfigUpdate` accepte des capitaux ≤ 0 et des buckets incohérents en appel API direct (validation uniquement côté client) → sizing Kelly invalide en BDD. | Moyenne |
| F-07 | UX / Fiabilité | HTTP 429 non géré par l'intercepteur (aucun toast) ; sur login, le rate limit affiche « Invalid username or password » au lieu d'un message de limitation. | Moyenne |
| F-08 | Accessibilité (WCAG 3.1.1) | A-08 résiduelle : `index.html` en `lang="en"` avec contenu français (« Évaluations Récentes », « Précédent/Suivant », en-têtes FR) + incohérence interne EN/FR entre paginations. | Basse |
| F-09 | Logique HTTP | Logout en `307` : le fetch suit en POST vers `/login.html` (StaticFiles → 405) ; ne fonctionne que par le contournement JS. Devrait être `303`. | Basse |
| F-10 | UX / Logique | Sélecteur d'actif peuplé une seule fois (`options.length <= 1`) : les nouvelles configs n'apparaissent jamais sans rechargement complet. | Basse |
| F-11 | Concurrence | `ensureCsrfToken()` sans déduplication de promesse : appels concurrents → cookies multiples, token JS potentiellement désynchronisé → 403 initiaux. | Basse |
| F-12 | Sécurité / Performance | CSP perfectible (`object-src`, `base-uri` absents ; `style-src 'unsafe-inline'` imposé par les styles inline) ; vendor charts chargé en synchrone bloquant dans `<head>`. | Basse |
| F-13 | Cohérence données | Pagination des évaluations par offset : dérive avec les insertions live → doublons/trous entre pages. | Basse |
| F-14 | Accessibilité | `asset-selector` sans `label`/aria-label ; `aria-describedby` absent sur edit-modal et resume-modal. | Basse |
| F-15 | Divers | `/favicon.ico` non exclu du middleware auth (redirect 307) ; `placeholder="admin"` révèle l'identifiant par défaut ; PnL agrégé côté client en `float` (divergence d'arrondi avec les KPIs serveur). | Basse |

---

## 3. Vérification de l'audit précédent (2026-07-17)

| ID | Anomalie (résumé) | Statut | Preuve |
| :---- | :---- | :---- | :---- |
| A-01 | SSE `/api/logs/stream` ne gère pas le 401 | ✅ Corrigée | Auth-check via `/api/status/heartbeat` après 5 échecs SSE, redirect login (`logs.js:313-328`). |
| A-02 | Rate limiter : exception si Redis down | ✅ Corrigée | Fail-open explicite init + opérations (`run_paper_trader.py:263-269, 286-288`). |
| A-03 | Cache `perf_metrics` non invalidé après panic | ✅ Corrigée | Invalidation Redis post-transaction pour tous les actifs liquidés (`api.py:666-682`). |
| A-04 | GET `/api/logout` exposé | ✅ Corrigée | `POST` uniquement (`api.py:1122`) ; client en POST (`app.js:100`). |
| A-05 | Absence de timeout sur les `fetch` | ✅ Corrigée | `AbortController` 15 s, exclusion SSE (`api.js:41, 56-62`). |
| A-06 | Token CSRF jamais rafraîchi après 403 | ✅ Corrigée | Invalidation + refetch + retry unique (`api.js:80-93`). |
| A-07 | `triggerImmediateRefresh` écrase `isLoading` | ✅ Corrigée | Garde `if (isLoading) return;` (`app.js:231-234`). |
| A-08 | Attribut `lang` incohérent | ⚠️ Partielle | `login.html:2` passé en `en` ; `index.html` toujours mixte FR/EN → requalifiée F-08. |
| A-09 | Absence de `prefers-reduced-motion` | ✅ Corrigée | Media query globale (`style.css:248-252`). |
| A-10 | Contraste bouton Resume | ✅ Corrigée | `color: #ffffff` (`style.css:997`). |
| A-11 | Double rate limiting slowapi/Redis | ✅ Corrigée | slowapi supprimé, limites par path centralisées (`run_paper_trader.py:229-232`). |
| A-12 | Pas de debounce sur les onglets | ✅ Corrigée | Debounce 200 ms (`app.js:57-70`). |
| A-13 | Filtrage des transactions côté client | ✅ Corrigée | Param `asset` serveur (`api.py:211`) utilisé par le chart (`chart.js:166`). |
| A-14 | Message « CDN Offline » trompeur | ✅ Corrigée | Message vendor local (`chart.js:27`). |
| A-15 | Burst de requêtes après panic | ✅ Corrigée | Groupage par priorité (`app.js:84-92`). |
| A-16 | SSE actif quand l'onglet est caché | ✅ Corrigée | Fermeture/réouverture sur `visibilitychange` (`logs.js:345-357`). |
| A-17 | Cap DOM via `childNodes` | ✅ Corrigée | `children.length` + `firstElementChild` (`logs.js:297-298`). |
| A-18 | `aria-describedby` manquant (panic) | ✅ Corrigée | Liaison complète (`index.html:371, 378`). |
| A-19 | Toast disparaît au survol | ✅ Corrigée | Pause au `mouseenter` (`ui.js:46-49`). |
| A-20 | Pas de thème clair | ✅ Corrigée | `prefers-color-scheme: light` (`style.css:208-224`). |
| A-21 | `backdrop-filter` sans fallback | ✅ Corrigée | Fond opaque + `@supports` (`style.css:54-67`). |
| A-22 | Pas de `@media print` | ✅ Corrigée | Règles d'impression (`style.css:226-245`). |
| A-23 | Timeout Redis 2 s systématique | ✅ Corrigée | `REDIS_CACHE_TIMEOUT = 0.5` (`api.py:23`). |

**Bilan : 22/23 corrigées (96 %), 1 partielle.**

---

## 4. Détail et corrections des anomalies majeures

### F-01 — Haute : La pagination par curseur perd des transactions aux timestamps partagés

**Fichiers** : `backtest_engine/live/paper_trading/api.py:227-252` ; `backtest_engine/live/paper_trading/static/js/modules/logs.js:111-116` ; insertion panic `api.py:642-646` ; insertions moteur `signal_executor.py:834-837, 1128-1131`

Le client pagine par curseur temporel : le curseur de la page N+1 est le `timestamp` de la dernière ligne de la page N (`logs.js:112`), et le serveur applique `WHERE timestamp < $1 ORDER BY timestamp DESC` (`api.py:237`). Or toutes les transactions insérées dans une même transaction SQL portent un `CURRENT_TIMESTAMP` **strictement identique** (début de transaction PostgreSQL). C'est le cas systématique du panic close : N positions liquidées → N lignes `paper_transactions` au même timestamp (`api.py:564-646`).

Si la rupture de page tombe sur un tel paquet (page de 50 lignes se terminant au milieu d'un panic de 12 positions, par exemple), toutes les lignes restantes du paquet sont **définitivement exclues** de la pagination : le curseur `timestamp < X` saute toutes les lignes à `timestamp = X`. L'historique consultable devient incomplet exactement sur l'événement le plus audité (liquidation d'urgence). Aucun message d'erreur — la perte est silencieuse.

**Correction** : curseur composite `(timestamp, id)` strictement monotone :

```python
# api.py — branche cursor_dt
rows = await conn.fetch(
    "SELECT id, timestamp, asset, strategy_name, action, qty, price, total_value "
    "FROM paper_transactions WHERE (timestamp, id) < ($1, $2) "
    "ORDER BY timestamp DESC, id DESC LIMIT $3",
    cursor_dt, cursor_id, limit,
)
```

```javascript
// logs.js — curseur composite
if (data.length === txLimit) {
    const last = data[data.length - 1];
    cursorStack.push({ timestamp: last.timestamp, id: last.id });
}
```

*Justification* : un curseur de pagination doit être un identifiant de position unique et total (§3.3 — intégrité I/O ; l'historique de trading est une donnée d'audit).

---

### F-02 — Haute : Rate limiting agrégé derrière le proxy (verrouillage collectif du login)

**Fichiers** : `run_paper_trader.py:248` (clé IP), `run_paper_trader.py:458-466` (uvicorn sans `forwarded_allow_ips`) ; `requirements-live.txt` (`uvicorn[standard]>=0.40,<1`)

Le rate limiter clé sur `request.client.host`. uvicorn 0.40 honore `X-Forwarded-For` uniquement si le pair appartient à `forwarded_allow_ips` (défaut : `127.0.0.1`), et `uvicorn.run()` ne le configure pas. Derrière le load balancer Render, `request.client.host` vaut donc l'IP du LB pour **toutes** les connexions : tous les visiteurs partagent les mêmes compteurs.

Conséquences :
- `/api/login` : 5 tentatives / 5 min (`run_paper_trader.py:254-257`) **mutualisées** — 5 échecs depuis n'importe quelle origine verrouillent le login pour tout le monde, y compris l'administrateur légitime. Déni de service trivial et permanent (un script relance toutes les 5 min).
- Tous les autres endpoints `/api/*` partagent le quota 60 req/min par path : un seul visiteur (ou le dashboard lui-même, qui pollue à ~2-5 req/10 s) peut épuiser le quota commun.

**Correction** : faire confiance aux en-têtes du LB de façon bornée et documenter le prérequis :

```python
# run_paper_trader.py — main()
uvicorn.run(
    app, host=host, port=port, log_level="info",
    proxy_headers=True,
    forwarded_allow_ips=os.getenv("FORWARDED_ALLOW_IPS", "*"),  # "*" acceptable uniquement derrière un LB qui réécrit XFF (Render)
)
```

et journaliser l'IP effective retenue dans les logs de rate limit pour vérification post-déploiement.

*Justification* : un contrôle de disponibilité (rate limit) qui ne distingue pas les clients est un faux contrôle — il punit les utilisateurs légitimes et n'arrête pas un attaquant distribué (§2.9 — garde-fous ; RTS 6 : le login ne doit pas être un point de blocage collectif).

---

### F-03 — Moyenne : Duplication des logs SSE à chaque reconnexion

**Fichiers** : `backtest_engine/live/paper_trading/api.py:720-729` ; `backtest_engine/live/paper_trading/static/js/modules/logs.js:270-308, 345-357`

À chaque connexion SSE, le serveur envoie les **100 dernières entrées** du buffer (`api.py:722-729`) pour fournir le contexte immédiat. Le client ajoute chaque message au DOM sans aucune déduplication (`logs.js:294`). Or le client ferme et rouvre l'`EventSource` à **chaque** cycle `visibilitychange` (`logs.js:345-357`) et après chaque série d'erreurs (retry 30 s). Résultat : un utilisateur qui change d'onglet 3 fois voit jusqu'à 300 lignes dupliquées dans la console — exactement le type de bruit qui masque une erreur réelle pendant un incident.

Le champ `seq` monotone (correctif PT-09) est déjà présent dans chaque message : la déduplication est gratuite côté client.

**Correction** :

```javascript
// logs.js — suivre le dernier seq reçu
let lastSeqReceived = 0;

const handleSseMessage = (event) => {
    try {
        const data = JSON.parse(event.data);
        if (typeof data.seq === 'number' && data.seq <= lastSeqReceived) return;
        if (typeof data.seq === 'number') lastSeqReceived = data.seq;
        // ... rendu inchangé
```

*Justification* : le contrat SSE du serveur (replay des 100 derniers) est légitime ; c'est au client d'être idempotent (§2.8 — idempotence).

---

### F-04 — Moyenne : Session stateless de 30 jours, non révocable

**Fichiers** : `backtest_engine/live/paper_trading/api.py:1005-1020` (token HMAC sans `jti`), `api.py:1099-1119` (cookie 30 jours), `api.py:1122-1126` (logout = `delete_cookie` uniquement)

Le token de session est un HMAC stateless `username:expires:sig` valable 30 jours. Le serveur ne conserve aucun état de session : le logout ne fait que demander au navigateur de supprimer le cookie. Un token copié (extension malveillante, accès physique, log proxy) reste utilisable jusqu'à expiration naturelle, même après un « logout » — et donne accès aux endpoints de contrôle (`/api/control/panic`). Le middleware CSRF ne protège pas contre ce scénario : l'attaquant qui possède le cookie de session sur une origine contrôlée obtient aussi un `csrftoken` via `GET /api/csrf-token`.

**Correction** (par ordre de valeur) :
1. Réduire `max_age` à 8–12 h avec renouvellement glissant (ré-émission du cookie si `expires - now < 4 h`).
2. Ajouter un `jti` au token et une liste de révocation Redis (`SETEX session_revoked:{jti}` au logout ; vérification dans `verify_session_token` — coût : 1 GET Redis par requête, déjà dans le budget du rate limiter).
3. Marquer le logout côté audit : `trading_audit.info("logout: user=%s", username)`.

*Justification* : un dashboard avec liquidation d'urgence en un clic ne peut pas reposer sur des sessions d'un mois non révocables (§2.2 — fiabilité absolue ; §2.9 — garde-fous).

---

### F-05 — Moyenne : `innerHTML` interpolé avec `${ticker}` dans les placeholders du chart

**Fichier** : `backtest_engine/live/paper_trading/static/js/chart.js:147-151, 248-252`

Deux placeholders d'erreur construisent leur HTML par interpolation directe du ticker :

```javascript
placeholder.innerHTML = `
    ...
    <p ...>No price candles available for ${ticker}. The feed may be inactive or offline.</p>
`;
```

`ticker` provient du `<select id="asset-selector">`, peuplé depuis `paper_strategy_configs.asset` (donnée BDD, `configs.js:159-165`). Le reste du code est exemplaire (`textContent` partout ailleurs) — ces deux points sont les seuls où une donnée externe atteint `innerHTML`. Le vecteur d'exploitation est étroit (`asset` n'est pas modifiable via l'API — `ConfigUpdate` ne l'expose pas ; il faut une écriture directe en BDD ou un ticker broker malveillant), d'où la sévérité moyenne, mais le pattern est une faille XSS stockée latente dans un contexte authentifié.

**Correction** :

```javascript
// chart.js — construire le message sans innerHTML pour la partie dynamique
placeholder.innerHTML = `<svg ...>...</svg>
    <p style="color: var(--danger); font-weight: bold; margin-top: 10px;">Stale Market Data</p>`;
const detail = document.createElement('p');
detail.style.cssText = 'font-size: 13px; max-width: 400px; text-align: center;';
detail.textContent = `No price candles available for ${ticker}. The feed may be inactive or offline.`;
placeholder.appendChild(detail);
```

*Justification* : donnée externe + `innerHTML` = XSS par construction ; le fait que le vecteur soit aujourd'hui difficile ne change pas la nature du défaut (§3.3 — exposition involontaire).

---

### F-06 — Moyenne : `ConfigUpdate` sans validation métier côté serveur

**Fichier** : `backtest_engine/live/paper_trading/api.py:121-127` ; validation client `configs.js:242-266`

Le client valide `> 0` et `initial_bucket ≤ max_bucket` (`configs.js:247-266`), mais le schéma Pydantic n'impose rien :

```python
class ConfigUpdate(BaseModel):
    initial_capital: float
    initial_capital_bucket: float
    max_capital_bucket: float
    max_entry_price: float
    ...
```

Un appel API direct (token de session valide) persiste des capitaux négatifs ou nuls, un bucket initial supérieur au bucket max, ou un `max_entry_price` négatif — valeurs qui alimentent ensuite le sizing Kelly du moteur. La validation côté client est une commodité UX, jamais une frontière de sécurité (§2.3 — validation aux frontières du système).

**Correction** :

```python
from pydantic import BaseModel, ConfigDict, Field, model_validator

class ConfigUpdate(BaseModel):
    initial_capital: float = Field(gt=0, le=1e9)
    initial_capital_bucket: float = Field(gt=0, le=1e9)
    max_capital_bucket: float = Field(gt=0, le=1e9)
    max_entry_price: float = Field(gt=0, le=1e12)
    is_active: bool
    indicator_params: IndicatorParamsModel | None = None

    @model_validator(mode='after')
    def check_buckets(self):
        if self.initial_capital_bucket > self.max_capital_bucket:
            raise ValueError("initial_capital_bucket cannot exceed max_capital_bucket")
        return self
```

*Justification* : la règle métier (cohérence des buckets) doit vivre à la frontière serveur ; Pydantic la rend déclarative et testée par les 422 existants.

---

### F-07 — Moyenne : HTTP 429 non géré ; message de login trompeur sous rate limit

**Fichiers** : `backtest_engine/live/paper_trading/static/js/api.js:78-114` ; `backtest_engine/live/paper_trading/static/js/login.js:38-42` ; limite login `run_paper_trader.py:254-257`

L'intercepteur traite 401/403/422/500/503 mais pas 429 : en cas de rate limit, aucun toast n'informe l'utilisateur. Pire sur le login : le serveur répond `{"detail": "Too many requests..."}` (FastAPI/`JSONResponse` du middleware), et `login.js:40` lit `data.message` (absent) → affiche le fallback **« Invalid username or password. »** — l'utilisateur légitime, verrouillé par la limite (aggravée par F-02), croit que son mot de passe est erroné et réessaie, prolongeant son propre blocage.

**Correction** :

```javascript
// api.js — après la branche 422
} else if (response.status === 429) {
    showError("Too many requests. Please wait a moment before retrying (429).");
}
```

```javascript
// login.js — distinguer le 429
} else if (response.status === 429) {
    errorAlert.textContent = 'Too many login attempts. Please wait 5 minutes and try again.';
    errorAlert.style.display = 'block';
}
```

*Justification* : un contrôle de sécurité dont le signal utilisateur est erroné dégrade à la fois la sécurité (réessais) et le diagnostic (§2.3 — exceptions explicites).

---

## 5. Anomalies basses (détail bref)

### F-08 — `lang` et incohérences linguistiques résiduelles (A-08 partielle)
`index.html:2` reste `lang="en"` avec des chaînes françaises : boutons « Précédent/Suivant » (`index.html:293-295`), « Évaluations Récentes » (`index.html:304`), en-têtes « Date/Heure », « Actif », « Stratégie », « Statut », « Raison/Détails » (`index.html:309-316`) — alors que la pagination des évaluations est en anglais (« Previous/Next », `index.html:324-326`). Correction : tout passer en anglais (stratégie actuelle de l'application) et harmoniser les deux paginations.

### F-09 — Logout en `307` au lieu de `303`
`api.py:1124` : `RedirectResponse(url="/login.html", status_code=307)`. Le 307 conserve la méthode : le `fetch` suit en **POST** vers `/login.html`, que `StaticFiles` sert en GET/HEAD uniquement (405 sur le suivi). Fonctionne uniquement parce que `app.js:103-106` réécrit ensuite `window.location.href`. Le login utilise correctement 303 (`api.py:1093, 1105`) — aligner : `status_code=303`.

### F-10 — Sélecteur d'actif figé après le premier chargement
`configs.js:157-166` : le `<select>` n'est peuplé que si `options.length <= 1`. Une config ajoutée en BDD après le premier rendu n'apparaît jamais sans rechargement complet de la page, bien que `fetchConfigs(true)` tourne en polling. Correction : repeupler en comparant l'ensemble des actifs à chaque fetch (conserver la sélection courante).

### F-11 — `ensureCsrfToken()` sans déduplication de promesse
`api.js:27-39` : si deux requêtes mutantes partent en parallèle sans token caché, deux `GET /api/csrf-token` concurrents partent ; chacun peut recevoir un `Set-Cookie` différent, et le token caché peut ne plus correspondre au cookie final → 403 initiaux (rattrapés par le retry F-06-existant, mais avec bruit d'audit CSRF côté SIEM). Correction : mémoïser la promesse en vol (`let csrfPromise = null; csrfPromise ??= originalFetch(...)...`).

### F-12 — CSP perfectible et chargement synchrone du vendor
`run_paper_trader.py:208-215` : ajouter `object-src 'none'; base-uri 'none'` à la CSP. Le `style-src 'unsafe-inline'` est imposé par les nombreux styles inline de `index.html` (ex. `:292-295, 358, 361-363`) — les déplacer vers `style.css` permettrait de le retirer. `index.html:10` charge le vendor charts (≈400 Ko) en `<script>` synchrone bloquant : ajouter `defer`.

### F-13 — Pagination des évaluations par offset (dérive en live)
`api.py:269-299` + `logs.js:34-42, 120-122` : pagination `LIMIT/OFFSET` sur une table alimentée en continu → les insertions décalent les fenêtres (doublons entre pages N et N+1). Correction identique à F-01 : curseur `(timestamp, id)`.

### F-14 — Accessibilité : labels et descriptions de modales
`index.html:145` : `<select id="asset-selector">` sans `<label>` ni `aria-label` (WCAG 1.3.1/4.1.2). `edit-modal` (`index.html:334`) et `resume-modal` (`index.html:396`) ont `aria-labelledby` mais pas de `aria-describedby` vers leur texte explicatif — la liaison faite pour panic-modal (A-18) n'a pas été généralisée.

### F-15 — Divers (regroupés)
- `run_paper_trader.py:106` : `/favicon.ico` non exclu du middleware auth → redirect 307 sur requête favicon non authentifiée (cosmétique, pollue les logs).
- `login.html:25` : `placeholder="admin"` révèle l'identifiant par défaut (`PAPER_TRADER_USER` défaut `admin`, `api.py:1023`) — retirer le placeholder.
- `dashboard.js:114-133` : PnL agrégé par somme `float` côté client ; les KPIs « Open PnL » peuvent diverger en arrondi des soldes serveur (`Decimal`). Affichage seulement — à documenter ou à faire servir par l'endpoint `/portfolio`.

---

## 6. Points forts constatés

- **Rendu DOM sain** : toutes les tables (positions, transactions, évaluations, configs) construites via `createElement`/`textContent` ; toasts via `innerText` — surface XSS quasi nulle hors F-05.
- **Intercepteur `fetch` centralisé** : timeout 15 s, gestion 401/403 (retry CSRF unique)/422/500/503, exclusion SSE propre.
- **Sécurité des formulaires** : double confirmation panic + resume, boutons désactivés jusqu'au consentement, rollback du toggle sur échec (`configs.js:181, 185`), validation client complète avec messages explicites.
- **Accessibilité modales** : focus trap, `Escape`, restauration du focus sur l'élément déclencheur, `aria-live` sur toasts et kill switch.
- **Polling économe** : suspension quand l'onglet est caché, rafraîchissement conditionnel piloté par les dirty flags du heartbeat (`dashboard.js:220-232`).
- **SSE robuste côté transport** : compteur d'erreurs plafonné, auth-check avant redirect, retry temporisé 30 s.
- **Middlewares serveur ordonnés correctement** : CORS → RateLimit → SecurityHeaders → Auth → CSRF, headers `nosniff`/`DENY`/CSP/HSTS, masquage d'erreurs avec UUID de corrélation.

---

## 7. Résumé des actions par priorité

| Priorité | IDs | Nature |
| :---- | :---- | :---- |
| Immédiat | F-01, F-02 | Curseur composite `(timestamp, id)` ; `forwarded_allow_ips` + vérification IP effective |
| Cette semaine | F-03, F-04, F-05, F-06, F-07 | Dédup `seq` SSE ; session 8-12 h + `jti`/révocation ; `textContent` chart ; validation Pydantic ; gestion 429 |
| Backlog | F-08 à F-15 | Harmonisation linguistique, 303 logout, sélecteur d'actif dynamique, CSP, accessibilité, cosmétiques |

**Commande de tests suggérée pour la non-régression** : `pytest tests/ -k "paper or api" --cov=backtest_engine/live/paper_trading --cov-report=term-missing` (vérifier notamment les cas 401/403/429 de l'intercepteur et la pagination curseur composite).
