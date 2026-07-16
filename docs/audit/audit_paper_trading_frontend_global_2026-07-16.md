# Rapport d'Audit Global — Frontend Paper Trading

**Date de l'audit :** 16 juillet 2026  
**Auteurs :** Équipe d'Architecture Système & Audit Sécurité  
**Statut :** Concluant (7/10) — Nécessite une consolidation immédiate sur la fiabilité financière et l'authentification.

---

## 1. Résumé Exécutif

Le présent rapport fusionne et unifie de manière exhaustive les deux audits de code statiques menés le 16 juillet 2026 sur l'interface utilisateur et la couche de liaison du module de Paper Trading. 

### 1.1 Appréciation de la Qualité Globale
Le frontend est conçu comme une Application Page Unique (SPA) construite en JavaScript Vanilla structuré en modules ES6, sans dépendance vis-à-vis d'un framework lourd (React/Vue). La structure générale du code est saine et présente plusieurs forces majeures :
- **Hygiène Sécuritaire (XSS) :** Remarquable. La manipulation dynamique du DOM s'effectue exclusivement par le biais de propriétés et méthodes sécurisées (`textContent`, `createTextNode`, `createElement`), éliminant quasiment tout risque d'injection de script inline via des chaînes malicieuses.
- **Robustesse des Actions Destructrices :** Le processus de déclenchement du Kill Switch (liquidation globale) et de reprise sécurisée du trading intègre des garde-fous UX pertinents (double confirmation par case à cocher, blocage du focus clavier, indicateurs visuels d'attente, rollback optimiste en cas de rejet par l'API).
- **Consommation Réseau Rationnalisée :** Un système intelligent de drapeaux d'invalidation (dirty-flags via un heartbeat périodique de 10 s) évite les requêtes de rafraîchissement global systématiques de l'ensemble des composants lorsque l'état de l'application n'a pas bougé.

### 1.2 Points de Vigilance Majeurs
Cependant, l'audit identifie plusieurs anomalies critiques pouvant induire l'opérateur en erreur sur l'état réel du marché et de ses configurations financières, ou affaiblir la sécurité de la plateforme :
1. **Erreur d'Affichage KPI (Profit Factor à « NaN ») :** Un désalignement de contrat entre le backend FastAPI et le client JavaScript concernant le traitement de la valeur de division par zéro (profit factor infini) affiche un résultat invalide dans l'UI.
2. **Condition de Course Graphique (Race Condition) :** L'absence de garde de séquence sur les requêtes asynchrones de données de marché permet l'entrelacement de réponses d'actifs distincts, affichant potentiellement les courbes d'un actif sur le graphique d'un autre.
3. **Absence d'Implémentation de l'Authentification :** Les endpoints critiques d'authentification (`/api/login`, `/api/csrf-token`) appelés par le frontend sont absents du code de l'API backend fourni, laissant supposer un état non fonctionnel ou l'absence de protection CSRF effective en production.

---

## 2. Périmètre & Cartographie du Code

### 2.1 Cartographie du Frontend Réel
L'analyse de production cible exclusivement le répertoire actif servant l'interface utilisateur.

| Fichier | Taille | Rôle / Responsabilité | Statut |
| :--- | :--- | :--- | :--- |
| [`index.html`](file:///home/kidpixel/trading_automation_v2/docs/audit/../../live/paper_trading/static/index.html) | 24,6 KB | Dashboard principal, structure HTML5 de l'application et modales d'action. | Actif (Production) |
| [`login.html`](file:///home/kidpixel/trading_automation_v2/docs/audit/../../live/paper_trading/static/login.html) | 5,9 KB | Page d'authentification initiale (contient un style CSS inline massif à corriger). | Actif (Production) |
| [`style.css`](file:///home/kidpixel/trading_automation_v2/docs/audit/../../live/paper_trading/static/style.css) | 28,0 KB | Charte graphique globale, responsive design, variables CSS et effets glassmorphism. | Actif (Production) |
| [`app.js`](file:///home/kidpixel/trading_automation_v2/docs/audit/../../live/paper_trading/static/app.js) | 46,6 KB | Logique applicative principale, orchestration du polling, gestion des onglets et modales. | Actif (Production) |
| [`js/api.js`](file:///home/kidpixel/trading_automation_v2/docs/audit/../../live/paper_trading/static/js/api.js) | 4,0 KB | Intercepteur HTTP `fetch` centralisé, injection de token CSRF, gestion du statut d'auth. | Actif (Production) |
| [`js/chart.js`](file:///home/kidpixel/trading_automation_v2/docs/audit/../../live/paper_trading/static/js/chart.js) | 8,3 KB | Logique d'affichage et d'interaction avec la bibliothèque graphique Lightweight Charts. | Actif (Production) |
| [`js/ui.js`](file:///home/kidpixel/trading_automation_v2/docs/audit/../../live/paper_trading/static/js/ui.js) | 2,9 KB | Utilitaires de formatage de devises, notifications toast et gestion d'état de bouton. | Actif (Production) |
| [`js/login.js`](file:///home/kidpixel/trading_automation_v2/docs/audit/../../live/paper_trading/static/js/login.js) | 1,8 KB | Intercepteur et gestionnaire de soumission du formulaire d'authentification. | Actif (Production) |
| [`vendor/lightweight-charts.standalone.production.js`](file:///home/kidpixel/trading_automation_v2/docs/audit/../../live/paper_trading/static/vendor/lightweight-charts.standalone.production.js) | 161 KB | Bibliothèque graphique locale tierce (évite l'appel à un CDN externe). | Actif (Production) |

### 2.2 Exclusion Explicite des Fichiers Obsolètes
> [!IMPORTANT]
> Les répertoires et fichiers situés sous `backtest_engine/web_static/` ont été identifiés comme issus d'une branche de développement **obsolète ou divergente**. Ils ne sont **pas servis** par le serveur web de production. Ils sont formellement exclus du présent audit pour éviter toute confusion avec le périmètre réel.

### 2.3 Fichiers Backend Clés Audités (Couche Contrat d'API)
Pour valider les interactions frontend-backend, les scripts suivants ont été audités :
- [`live/paper_trading/api.py`](file:///home/kidpixel/trading_automation_v2/docs/audit/../../live/paper_trading/api.py) (892 lignes) : Définition des routes FastAPI de l'interface de programmation.
- [`live/paper_trading/signal_executor.py`](file:///home/kidpixel/trading_automation_v2/docs/audit/../../live/paper_trading/signal_executor.py) (1178 lignes) : Logique d'exécution transactionnelle.
- [`live/kill_switch.py`](file:///home/kidpixel/trading_automation_v2/docs/audit/../../live/kill_switch.py) (433 lignes) : Structure de contrôle du circuit breaker.
- [`live/connection.py`](file:///home/kidpixel/trading_automation_v2/docs/audit/../../live/connection.py) (557 lignes) : Client de persistance et de messagerie Redis.
- [`live/controls.py`](file:///home/kidpixel/trading_automation_v2/docs/audit/../../live/controls.py) (83 lignes) : Validateur pré-trade.
- [`live/utils.py`](file:///home/kidpixel/trading_automation_v2/docs/audit/../../live/utils.py) (220 lignes) : Outils de calcul décimal et d'évaluation d'horaires.

---

## 3. Catalogue Unifié des Anomalies et Vulnérabilités

Cette section liste l'intégralité des défauts identifiés, classés par catégorie technique et dotés d'un identifiant de suivi.

### 3.1 Sécurité (SEC)

| Identifiant | Catégorie | Description & Impact en Production | Sévérité |
| :--- | :--- | :--- | :--- |
| **SEC-01** | Sécurité | **Endpoints d'authentification non implémentés :** Le frontend tente de requêter `POST /api/login` et `GET /api/csrf-token` mais ces routes n'existent pas dans le fichier `api.py`. Si le système est exposé en production via un reverse proxy sans implémentation effective, la protection CSRF est inexistante pour toutes les requêtes de mutation.<br>*Règle violée : AGENTS.md §6.1* | **Critique** |
| **SEC-02** | Sécurité | **Pas de Rate Limiting sur la route `/api/login` :** Aucune restriction du débit de requêtes (throttling) n'est mise en œuvre au backend ou au frontend (bouton de connexion sans cooldown temporaire après échec).<br>Permet les attaques par brute-force et de type credential stuffing.<br>*Règle violée : AGENTS.md §2.8 et §6.1* | **Critique** |
| **SEC-03** | Sécurité | **Absence de Content-Security-Policy (CSP) :** Aucun en-tête HTTP ni balise meta CSP n'est défini dans `index.html` et `login.html`. Bien que l'architecture par modules ES6 limite l'exploitation de scripts inline non autorisés, l'absence de CSP laisse l'application vulnérable aux injections malveillantes via d'autres vecteurs (images, polices, connexions ws/http non prévues).<br>*Règle violée : AGENTS.md §6.1* | **Critique** |
| **SEC-04** | Sécurité | **Pas de Middleware global d'erreur dans FastAPI :** Les erreurs SQL ou système internes ne sont pas uniformément capturées par un middleware standard retournant un jeton d'erreur unique et anonymisé (UUID de corrélation).<br>Risque d'exposer des détails d'infrastructure ou des stack traces détaillées au client en production.<br>*Règle violée : AGENTS.md §2.3 (Masquage)* | **Moyenne** |
| **SEC-05** | Sécurité | **Gestion d'erreurs HTTP incomplète dans l'intercepteur fetch :** L'intercepteur global dans `api.js` ne gère pas le code HTTP 403 (en cas d'expiration/rotation CSRF) et n'extrait pas la propriété descriptive `detail` des réponses d'erreur 422 renvoyées par FastAPI.<br>Bloque l'expérience utilisateur et affiche des logs système bruts en console.<br>*Règle violée : AGENTS.md §2.3* | **Moyenne** |
| **SEC-06** | Sécurité | **Déconnexion de session via méthode GET :** Le bouton de déconnexion dans `index.html` utilise un lien `href="/api/logout"` (méthode GET), ce qui empêche l'utilisation du token CSRF et expose l'utilisateur à des déconnexions forcées par préchargement automatique (prefetch) du navigateur.<br>*Règle violée : AGENTS.md §6.1* | **Moyenne** |
| **SEC-07** | Sécurité | **Fuite potentielle du jeton CSRF sur les appels tiers :** L'intercepteur JavaScript attache automatiquement le header `X-CSRFToken` à toutes les requêtes `fetch` sans vérifier le domaine de destination.<br>Si un appel réseau vers une API externe est ajouté, le jeton CSRF interne y sera partagé.<br>*Règle violée : AGENTS.md §6.1* | **Basse** |

---

### 3.2 Exactitude Financière (FIN)

| Identifiant | Catégorie | Description & Impact en Production | Sévérité |
| :--- | :--- | :--- | :--- |
| **FIN-01** | Exactitude | **Profit Factor affiché « NaN » en l'absence de pertes :** Si une stratégie n'a généré que des transactions gagnantes, le backend renvoie `profit_factor: null` pour représenter l'infini. Le frontend teste une égalité de chaîne avec la valeur `'Infinity'` au lieu d'intercepter la valeur `null`. `parseFloat(null)` renvoie `NaN`.  | **Haute** |
| **FIN-02** | Exactitude | **Cache persistant bloquant le rafraîchissement des configurations :** Dans `app.js`, la méthode `fetchConfigs` utilise indéfiniment la variable locale `cachedConfigs` sans invalidation temporelle au sein du cycle de polling. Les indicateurs d'ouverture de marché ou l'apparition de statuts d'erreur en cours de fonctionnement ne se mettent jamais à jour spontanément. | **Haute** |
| **FIN-03** | Exactitude | **Non-rafraîchissement automatique du tableau des Transactions :** Le drapeau de modification `changed.transactions` du polling est utilisé uniquement pour nettoyer le cache des graphiques, mais n'actualise pas le tableau de la vue active des Transactions.<br>L'utilisateur doit cliquer manuellement sur un autre onglet pour forcer la mise à jour des transactions exécutées. | **Moyenne** |
| **FIN-04** | Exactitude | **Absence de bougies gérée par une interruption silencieuse :** Si `getCandles` renvoie une liste vide, le script s'arrête silencieusement sans effacer le graphique précédent ni afficher d'état vide explicite.<br>L'opérateur peut croire qu'une stratégie tourne avec des données de prix récentes alors que le flux de marché est interrompu. | **Moyenne** |
| **FIN-05** | Exactitude | **Capture et échec silencieux du chargement des blocs de données clés :** Les blocs `catch` réseau de `fetchPortfolio`, `fetchPositions`, etc. écrivent dans `console.error` sans notifier l'interface.<br>L'opérateur peut surveiller des métriques financières obsolètes (NAV, solde disponible) figées à l'écran sans le savoir. | **Moyenne** |
| **FIN-06** | Exactitude | **Collision de markers BUY/SELL minute :** Les marqueurs d'ordres sur le graphique Lightweight Charts sont stockés et dédupliqués en utilisant le timestamp minute comme clé unique.<br>Si un achat et une vente se produisent dans la même minute, un seul marqueur s'affiche, masquant la réalité opérationnelle. | **Moyenne** |
| **FIN-07** | Exactitude | **Désalignement des plages d'analyse de performance et de prix :** Les séries de prix du graphique (`/api/candles`) sont limitées à 1000 bougies tandis que les courbes de performance associées (`/api/performance/metrics`) calculent sur un historique de 5000 bougies.<br>Crée des comparaisons de courbes faussées et illisibles. | **Moyenne** |
| **FIN-08** | Exactitude | **Affichage des quantités en float natif non arrondi :** Les colonnes de quantité dans les tableaux ne subissent aucun formatage décimal, affichant des anomalies d'arrondi binaire (ex. `0.30000000000000004`). | **Basse** |
| **FIN-09** | Exactitude | **Valeurs d'évaluation à 0 masquées :** L'évaluation d'un actif est affichée sous forme de tiret `-` si le prix calculé est égal à `0` à cause du test de condition falsy JavaScript `evalItem.price ? ... : '-'`. | **Basse** |

---

### 3.3 Performance & Concurrency (PERF)

| Identifiant | Catégorie | Description & Impact en Production | Sévérité |
| :--- | :--- | :--- | :--- |
| **PERF-01** | Performance | **Course critique TOCTOU dans le basculement (failover) de Redis :** Dans `connection.py` à la ligne 400, l'indicateur de bascule `_is_failed_over` est évalué puis modifié sans lock thread-safe.<br>Risque de double exécution de `_failover()`, provoquant des conflits de connexions Redis primaires et des pertes de messages Pub/Sub.<br>*Règle violée : AGENTS.md §2.5* | **Haute** |
| **PERF-02** | Performance | **Variable globale `_trading_suspended` accédée sans barrière mémoire :** Le flag d'état du kill switch est manipulé à travers différents threads sans instruction de synchronisation mémoire globale.<br>Le GIL élimine le risque d'état corrompu mais n'évite pas des délais de synchronisation minimes entre threads.<br>*Règle violée : AGENTS.md §2.5* | **Basse** |
| **PERF-03** | Performance | **Perte silencieuse de la connexion SSE (Server-Sent Events) :** L'application implémente `EventSource` pour streamer les logs système mais ne configure aucun handler d'erreur `onerror`. En cas de crash du flux, aucune notification visuelle n'est poussée à l'écran.<br>L'utilisateur pense lire les événements système en temps réel alors que la connexion est coupée.<br>*Règle violée : AGENTS.md §2.8* | **Haute** |
| **PERF-04** | Performance | **Course conditionnelle asynchrone (Race Condition) lors du changement d'actif :** La méthode `loadChart` met à jour des variables au niveau du module JS. Si un utilisateur sélectionne `BTC` puis immédiatement `ETH`, les requêtes asynchrones en arrière-plan peuvent entrelacer leurs retours, dessinant les données de l'un sur le repère temporel de l'autre. | **Haute** |
| **PERF-05** | Performance | **Requêtes de Token CSRF dupliquées au démarrage :** `ensureCsrfToken` met en cache le jeton mais ne stocke pas la promesse de récupération HTTP.<br>Si deux requêtes POST s'initialisent en même temps au démarrage, deux requêtes réseau d'authentification CSRF distinctes partent en parallèle. | **Basse** |
| **PERF-06** | Performance | **Polling CPU/Réseau maintenu sur les onglets masqués :** Le timer de polling toutes les 10 s s'exécute sans interruption même si le navigateur est minimisé ou si l'onglet est inactif.<br>Consomme inutilement les ressources réseau et CPU des serveurs. | **Basse** |
| **PERF-07** | Performance | **Filtrage des transactions déporté côté client :** La route `/api/transactions` renvoie par défaut 5000 transactions non filtrées par actif. Le client JS effectue le filtrage pour l'asset sélectionné localement.<br>Augmente de façon disproportionnée la charge réseau et mémoire en cours de session active. | **Basse** |

---

### 3.4 Accessibilité (ACC)

| Identifiant | Catégorie | Description & Impact en Production | Sévérité |
| :--- | :--- | :--- | :--- |
| **ACC-01** | Accessibilité | **Boutons de fermeture de modale non focusables :** Les boutons de fermeture dans les pop-ups sont définis par des balises `<span>` non sémantiques. Ils ne sont pas inclus dans l'indexation de tabulation et ne réagissent pas à la touche `Entrée` ou `Espace`. | **Moyenne** |
| **ACC-02** | Accessibilité | **Focus clavier invisible sur les commutateurs de configuration :** Les inputs de formulaires pour activer les stratégies sont masqués pour des raisons visuelles sans qu'aucune règle CSS `:focus-visible` ne reporte le focus visuel sur l'habillage graphique externe. | **Moyenne** |
| **ACC-03** | Accessibilité | **Indicateur de santé des flux Bybit/T212 basé uniquement sur la couleur :** Le statut de connexion est rendu via une puce colorée et une info-bulle `title` non lisible par lecteur d'écran.<br>Exclut les utilisateurs daltoniens ou malvoyants. | **Moyenne** |
| **ACC-04** | Accessibilité | **Absence de support de réduction des animations :** Le panneau utilise des indicateurs clignotants (`blink-error`) et des transitions sans tenir compte de la préférence du système utilisateur.<br>Risque de fatigue visuelle ou de distractions pour les personnes sensibles. | **Basse** |
| **ACC-05** | Accessibilité | **Logique d'annonce vocale des logs trop verbeuse :** La console de logs utilise le rôle sémantique `aria-live="polite"` sur un conteneur hautement actif.<br>Provoque une saturation auditive immédiate si un lecteur d'écran est utilisé. | **Basse** |
| **ACC-06** | Accessibilité | **Attribut `scope="col"` absent sur les en-têtes de colonnes :** Les balises `<th>` des tables de positions, de transactions et de configurations ne précisent pas la portée de la cellule, nuisant à l'analyse sémantique automatique. | **Basse** |
| **ACC-07** | Accessibilité | **Absence d'alternative textuelle pour le graphique dynamique :** Le conteneur du graphique dessiné dans le canvas n'a pas d'alternative textuelle structurée (ex. tableau caché contenant les dernières valeurs de cours). | **Basse** |

---

### 3.5 Dette Technique (DT)

| Identifiant | Catégorie | Description & Impact en Production | Sévérité |
| :--- | :--- | :--- | :--- |
| **DT-01** | Dette Tech | **Gestion des fallbacks Redis par interception globale et silencieuse :** Les requêtes Redis d'authentification ou de sauvegarde temporaire capturent de façon générique l'ensemble des exceptions (`except Exception: pass`).<br>Empêche la détection d'erreurs de syntaxe ou de configuration critiques de la base de données. | **Moyenne** |
| **DT-02** | Dette Tech | **Feuille de style CSS inline volumineuse dans `login.html` :** Plus de 160 lignes de styles CSS résident dans une balise `<style>` au sein de la page de login, dupliquant une partie des variables globales.<br>Empêche le durcissement optimal des politiques CSP et complexifie la maintenance graphique. | **Moyenne** |
| **DT-03** | Dette Tech | **Paramètres de requête d'API non sécurisés et non encodés :** Les requêtes HTTP de récupération de données de marché concatènent directement la variable ticker (`?ticker=${ticker}`) sans passer par un appel `encodeURIComponent`. | **Moyenne** |
| **DT-04** | Dette Tech | **Message d'erreur de bibliothèque graphique ciblant un CDN obsolète :** Le script d'alerte en cas de chargement manquant de Lightweight Charts mentionne explicitement `unpkg.com` alors que la dépendance a été relocalisée en local dans `vendor/`. | **Moyenne** |
| **DT-05** | Dette Tech | **Mélange linguistique et i18n désorganisé :** L'attribut principal de la page indique `lang="en"`, mais les boutons de pagination, les headers de sidebar et les alertes toasts affichent du texte alternatif en français. | **Basse** |
| **DT-06** | Dette Tech | **Règles de localisation et formats régionaux mixtes :** Le format monétaire applique des conventions européennes (`fr-FR`, avec séparateur d'espace et symbole €) alors que les calculs de volumes ou de USDT appliquent des conventions américaines (`en-US`). | **Basse** |
| **DT-07** | Dette Tech | **Risque de dérive de pagination sur le flux des transactions :** La pagination backend repose sur un modèle classique de `LIMIT` et `OFFSET`. Sur un flux de transactions dynamique en temps réel, l'insertion d'une nouvelle ligne décale les index et fait sauter des éléments. | **Basse** |
| **DT-08** | Dette Tech | **Éléments de script importés non référencés :** Le fichier `app.js` et `chart.js` contiennent des importations inutilisées (ex: `formatPercent`, `formatCurrency`), alourdissant le contexte JS. | **Basse** |
| **DT-09** | Dette Tech | **Duplication de la règle métier d'évaluation Crypto :** L'évaluation de type de marché (`is_crypto_asset`) s'exécute côté client via des chaînes en dur (`endsWith('usdt')`), dupliquant inutilement la règle unifiée du backend. | **Basse** |

---

## 4. Plan d'Action et Remédiation Priorisé

Ce plan réorganise et fusionne les priorités des rapports précédents afin de maximiser la cohérence et l'efficacité des chantiers de développement futurs.

### 4.1 Priorité 1 (P1) — Sécurité & Fiabilité immédiate
*Objectif : Rendre le système fonctionnel, stable sur le calcul financier, et étanche face aux attaques de base.*

1. **Implémenter les Endpoints d'Authentification backend manquants (SEC-01) :**
   - Créer `POST /api/login` pour valider les identifiants et générer un cookie de session HttpOnly, Secure, et SameSite=Strict.
   - Créer `GET /api/csrf-token` pour l'initialisation du cookie double-submit pattern.
2. **Corriger le Profit Factor « NaN » (FIN-01) :**
   - Remplacer le traitement JavaScript dans `js/chart.js` :
     ```javascript
     const pf = perfData.profit_factor;
     document.getElementById('analytic-profitfactor').textContent =
         (pf === null || pf === undefined) ? '∞' : Number(pf).toFixed(2);
     ```
3. **Mettre en place la sécurité contre les conditions de course graphique (PERF-04) :**
   - Implémenter un garde de séquence (Sequence Guard) dans `js/chart.js` pour s'assurer que les retours asynchrones hors-délais ne se dessinent pas sur l'actif nouvellement sélectionné :
     ```javascript
     let chartRequestId = 0;
     export async function loadChart(ticker, forceRefresh = false) {
         const requestId = ++chartRequestId;
         // ...
         const candlesData = await getCandles(ticker);
         if (requestId !== chartRequestId) return;
         // Répéter la garde après chaque await asynchrone
     }
     ```
4. **Invalidation du cache des configurations au polling (FIN-02) :**
   - Ajouter un drapeau de forçage `forceRefresh = false` dans `fetchConfigs` et l'appeler avec `true` depuis la boucle de polling récurrente pour contourner la variable statique `cachedConfigs`.
5. **Résoudre la faille TOCTOU sur Redis (PERF-01) :**
   - Encapsuler la condition critique de changement d'état dans `connection.py` sous un verrou d'exclusion mutuelle :
     ```python
     self._failover_lock = threading.Lock()
     # ...
     with self._failover_lock:
         if not self._is_failed_over:
             self._failover()
     ```
6. **Sécuriser la transmission et le stockage du token CSRF (SEC-03, SEC-07) :**
   - Ajouter des en-têtes HTTP `Content-Security-Policy` restrictifs via un middleware FastAPI ou des balises meta.
   - Restreindre l'intercepteur fetch dans `js/api.js` pour s'assurer que le header `X-CSRFToken` est uniquement envoyé sur les requêtes d'origine identique (`same-origin`).
7. **Ajouter le rate limiting d'authentification (SEC-02) :**
   - Configurer une limite globale (ex. 5 tentatives max / 5 minutes par adresse IP) sur l'endpoint `/api/login`.
8. **Sécuriser la reconnexion SSE (PERF-03) :**
   - Ajouter un écouteur `onerror` sur l'objet `EventSource` natif du client pour afficher une notification toast explicite à l'opérateur en cas de perte de connexion réseau prolongée avec le serveur de logs.

---

### 4.2 Priorité 2 (P2) — Accessibilité & Standardisation
*Objectif : Rendre l'interface conforme aux bonnes pratiques d'ergonomie, d'accessibilité sémantique et de structure de données.*

1. **Rendre les modales interactives au clavier (ACC-01, ACC-02) :**
   - Remplacer les balises fermantes `<span>` non interactives par de vrais éléments de bouton : `<button type="button" class="close-modal">`.
   - Ajouter des règles graphiques `:focus-visible` bien visibles sur les commutateurs et sliders.
2. **Ajouter une alternative pour le Heartbeat (ACC-03) :**
   - Remplacer le point de couleur simple par un conteneur doté d'attributs `aria-label` descriptifs ou de texte masqué pour les synthèses vocales.
3. **Uniformiser l'i18n et les devises (DT-05, DT-06) :**
   - Aligner l'attribut `lang` et traduire l'intégralité des chaînes d'interface dans une seule et unique langue de référence (l'anglais technique est préconisé).
   - Unifier l'usage des locales d'affichage monétaires (`fr-FR` ou `en-US` de manière homogène sur tous les indicateurs du tableau de bord).
4. **Implémenter la déconnexion en POST (SEC-06) :**
   - Modifier l'action de déconnexion pour utiliser une requête POST asynchrone protégée contre le CSRF, en remplacement du lien GET brut.
5. **Sécuriser les requêtes HTTP dynamiques (DT-03) :**
   - Systématiser l'appel à `encodeURIComponent` pour l'ensemble des requêtes concaténant des query params (ex: ticker).
6. **Indiquer la péremption des données financières (FIN-05) :**
   - Ajouter un indicateur graphique (ex: réduction de l'opacité du conteneur et ajout d'un texte d'état) sur les blocs de données financières si la requête réseau de polling échoue.

---

### 4.3 Priorité 3 (P3) — Architecture & Dette technique
*Objectif : Simplifier la maintenance du code et optimiser la consommation de ressources.*

1. **Refactoring majeur du module principal `app.js` (DT-08) :**
   - Découper ce fichier monolithique de ~1100 lignes en modules JS spécialisés par composant graphique (ex: `dashboard.js`, `configs.js`, `logs.js`).
   - Supprimer les fonctions et importations mortes.
2. **Optimiser le cycle de vie du Polling (PERF-06) :**
   - Suspendre le timer périodique de 10 s lorsque `document.hidden` est détecté (onglet en arrière-plan) et forcer une mise à jour dès le retour au premier plan.
3. **Mettre en place la pagination sécurisée (DT-07) :**
   - Remplacer le système `LIMIT`/`OFFSET` de l'API de transactions par une pagination basée sur curseur temporel (`cursor_timestamp`), insensible aux nouvelles écritures concurrentes.
4. **Unifier la logique des variables CSS (DT-02) :**
   - Extraire le CSS inline massif de `login.html` pour le réintégrer dans `style.css` afin de supprimer les duplications de variables chromatiques.

---

## 5. Méthodologie et Protocoles de Validation

Toute correction appliquée selon le plan d'action décrit ci-dessus devra faire l'objet d'une validation rigoureuse selon les protocoles d'assurance-qualité suivants.

### 5.1 Protocole 1 : Tests Unitaires et API (Côté Backend)
- **Validation d'Authentification (SEC-01, SEC-02) :**
  - Écrire un scénario de test unitaire sous `pytest` validant que l'accès à une ressource protégée (ex: `/api/positions`) sans cookie de session légitime retourne un code HTTP `401 Unauthorized`.
  - Simuler un brute-force (10 requêtes de connexion rapides) sur `/api/login` et s'assurer que le backend renvoie un code HTTP `429 Too Many Requests` avec l'en-tête `Retry-After`.
- **Validation CSRF (SEC-01) :**
  - Envoyer une requête `POST /api/configs` avec un cookie de session valide mais sans header `X-CSRFToken` ou avec un jeton erroné. Valider la réponse HTTP `403 Forbidden`.

### 5.2 Protocole 2 : Tests de Concurrence et de Résilience (Côté Système)
- **Validation du Basculement Redis (PERF-01) :**
  - Déclencher 20 appels simultanés asynchrones vers le client Redis pour forcer une bascule de secours. Vérifier qu'aucune exception d'état ou double instanciation de client primaire n'est consignée dans les logs.
- **Validation de Résilience SSE (PERF-03) :**
  - Couper brutalement la connexion réseau ou redémarrer le service backend FastAPI pendant que le dashboard est ouvert. 
  - Valider que le client JavaScript déclenche son exception `onerror`, affiche une alerte visuelle claire à l'écran, et rétablit proprement la console lors du redémarrage du backend.

### 5.3 Protocole 3 : Validation Visuelle et Expérience Utilisateur (Côté Frontend)
- **Validation de non-entrelacement Graphique (PERF-04) :**
  - Ouvrir l'outil de limitation réseau du navigateur (Network Throttling réglé sur "Slow 3G").
  - Cliquer successivement et très rapidement sur 5 actifs différents dans le sélecteur.
  - Vérifier que seul le graphique et les indicateurs du dernier actif cliqué finissent par s'afficher à l'écran, sans aucune superposition ou mélange de courbes avec les actifs cliqués précédemment.
- **Validation du Profit Factor (FIN-01) :**
  - Configurer une stratégie de test n'ayant réalisé que des transactions gagnantes.
  - S'assurer que le KPI du Profit Factor affiche le symbole de l'infini `∞` et non la valeur textuelle `NaN`.
- **Validation Accessibilité Clavier (ACC-01, ACC-02) :**
  - Parcourir l'ensemble de l'interface en utilisant uniquement la touche `Tab` et la touche `Espace`/`Entrée`.
  - Vérifier que toutes les fenêtres modales peuvent être ouvertes, configurées, validées et fermées (y compris via la touche `Escape`) sans jamais recourir au pointeur de la souris, et que le focus visuel reste toujours identifiable à chaque étape de navigation.

---
*Fin du rapport d'audit consolidé.*