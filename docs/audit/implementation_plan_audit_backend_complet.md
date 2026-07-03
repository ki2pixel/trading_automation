# Plan d'Action Audit Backend — `trading_automation_v2`

> **Source** : [audit-backend-complet.md](file:///home/kidpixel/trading_automation_v2/docs/audit/audit-backend-complet.md) (137 lignes, 5 axes, 14 items)
> **Date** : 2026-07-03
> **Contexte** : Post-migration Supabase → Aiven, Sprint 1 structurel résolu, ingesteur Bybit/Trading212 opérationnel sur Render.

---

## Tableau Récapitulatif

| Phase | Priorité | Items Audit | Effort | Durée Est. | Statut |
|:------|:---------|:------------|:-------|:-----------|:-------|
| **Phase 1 — Sécurité Critique** | P0 Bloquant | §1.1, §1.2, §1.3, Checklist CORS/CSP | L | 5-7 jours | 🟢 Terminé |
| **Phase 2 — Performance & DB** | P1 Haute | §3.2 (pool async), §3.2 (N+1), §3.2 (buffer I/O) | M | 3-5 jours | 🔴 À faire |
| **Phase 3 — Architecture & DRY** | P2 Moyen | §2.2 (BaseStrategyRunner), §2.2 (connexions DB), §2.2 (engine.py) | XL | 7-10 jours | 🔴 À faire |
| **Phase 4 — Robustesse** | P2 Moyen | §4.2 (exceptions), §4.2 (fuites info), §4.2 (timeouts réseau) | S | 2-3 jours | 🔴 À faire |
| **Phase 5 — Hygiène** | P2 Amélioration | §5.2 (dépendances), dette technique résiduelle | S | 1-2 jours | 🔴 À faire |
| **Total** | | **14 items actifs** | | **18-27 jours** | |

---

## Items Déjà Résolus (Sprint 1 — 2026-07-03)

> [!NOTE]
> Ces items ont été traités lors du Sprint 1 structurel et sont **exclus** du plan d'action ci-dessous. Ils sont conservés ici pour traçabilité.

| Item Audit | Résolution Sprint 1 | Date |
|:-----------|:---------------------|:-----|
| Centralisation config dans `utils.py` | ✅ Configurations et `is_market_open` centralisées | 2026-07-03 12:27 |
| Sécurisation Redis (timeouts) | ✅ Timeouts Redis ajoutés | 2026-07-03 12:27 |
| Bridage `limit` FastAPI | ✅ Paramètre `limit` validé et bridé | 2026-07-03 12:27 |
| Code mort `ingestor.py` | ✅ Overrides de `print` et code mort supprimés | 2026-07-03 12:27 |
| Seeding DB | ✅ Correction du seeding | 2026-07-03 12:27 |

---

## Phase 1 — Sécurité Critique

> **Priorité** : P0 — Bloquant production
> **Objectif** : Éliminer toutes les vulnérabilités critiques identifiées avant tout déploiement en environnement exposé.
> **Effort estimé** : L (5-7 jours-homme)
> **Dépendances** : Aucune — phase initiale.

### Tâche 1.1 — Sécurisation des secrets HMAC (§1.1)

- **Criticité** : ❌ CRITIQUE
- **Fichiers impactés** :
  - [api.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/api.py) (ligne 13)
  - [run_paper_trader.py](file:///home/kidpixel/trading_automation_v2/run_paper_trader.py) (lignes 27-28)
- **Actions** :
  - [x] Générer un secret HMAC aléatoire fort au démarrage (≥32 bytes, `secrets.token_hex(32)`) au lieu d'utiliser le mot de passe utilisateur comme clé de signature
  - [x] Séparer `PAPER_TRADER_PASSWORD` (authentification utilisateur) de `HMAC_SECRET` (signature tokens) dans `.env.template`
  - [x] S'assurer que ni le mot de passe ni le secret HMAC ne sont jamais loggés (audit des `logger.info`/`logger.debug`)
  - [x] Ajouter le secret HMAC aux variables d'environnement Render
- **Effort** : S (0.5-1 jour)

### Tâche 1.2 — Protection CSRF (§1.2)

- **Criticité** : ❌ CRITIQUE
- **Fichiers impactés** :
  - [app.js](file:///home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/static/app.js) (lignes 1-10)
  - [api.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/api.py) (tous les endpoints POST/PUT/DELETE)
- **Actions** :
  - [x] Implémenter un middleware CSRF pour FastAPI (génération de token CSRF côté serveur, inclusion dans les réponses via un cookie `csrftoken`)
  - [x] Ajouter un header personnalisé `X-CSRFToken` à toutes les requêtes mutantes depuis le frontend
  - [x] Vérifier côté serveur la correspondance du token CSRF pour les méthodes `POST`, `PUT`, `DELETE`
  - [x] Vérifier les headers `Origin` et `Referer` comme couche de défense supplémentaire
  - [x] Tester avec un scénario d'attaque CSRF simulé
- **Effort** : M (2-3 jours)

### Tâche 1.3 — Validation Pydantic stricte (§1.3)

- **Criticité** : ⚠ HAUT
- **Fichiers impactés** :
  - [api.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/api.py) (lignes 100-105)
- **Actions** :
  - [x] Créer un modèle Pydantic `IndicatorParamsModel` avec les clés et types explicitement autorisés
  - [x] Configurer `model_config = ConfigDict(extra='forbid')` pour rejeter toute clé inconnue (modifié en `extra='allow'` avec vérification via `model_validator` des types primitifs)
  - [x] Remplacer la désérialisation JSON directe de `indicator_params` par la validation via le modèle Pydantic
  - [x] Ajouter des tests unitaires pour les cas valides et les rejets de clés inconnues (ou invalides)
- **Effort** : S (0.5-1 jour)

### Tâche 1.4 — Headers de sécurité CORS/CSP (Checklist ligne 121)

- **Criticité** : ❌ NON IMPLÉMENTÉ
- **Fichiers impactés** :
  - [api.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/api.py) ou [run_paper_trader.py](file:///home/kidpixel/trading_automation_v2/run_paper_trader.py)
- **Actions** :
  - [x] Ajouter le middleware `CORSMiddleware` de FastAPI avec une whitelist d'origines stricte (pas de `*` en production)
  - [x] Implémenter un middleware CSP (Content-Security-Policy) pour restreindre les sources de scripts, styles, et images
  - [x] Ajouter les headers de sécurité complémentaires : `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`
  - [x] Tester la conformité des headers avec un outil comme `securityheaders.com`
- **Effort** : S (1 jour)

### Critères de Complétion Phase 1

- [x] Aucun secret utilisateur n'est utilisé comme clé de signature HMAC
- [x] Tous les endpoints mutants sont protégés contre le CSRF
- [x] `indicator_params` est validé par un modèle Pydantic strict
- [x] Les headers CORS, CSP, HSTS, X-Content-Type-Options et X-Frame-Options sont présents en production
- [x] Tests de sécurité passés (CSRF simulé, injection de clés Pydantic, vérification headers)
- [x] Aucune régression sur les fonctionnalités existantes du Paper Trading

---

## Phase 2 — Performance & Base de Données

> **Priorité** : P1 — Haute priorité
> **Objectif** : Éliminer les goulots d'étranglement de performance et les risques de blocage en contexte asynchrone.
> **Effort estimé** : M (3-5 jours-homme)
> **Dépendances** : Aucune — indépendante de Phase 1.

### Tâche 2.1 — Migration vers asyncpg (§3.2 — Pool synchrone)

- **Criticité** : ⚠ HAUT
- **Fichiers impactés** :
  - [connection.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/connection.py)
  - [api.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/api.py)
  - [engine.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/engine.py)
- **Actions** :
  - [ ] Installer `asyncpg` et le déclarer dans les requirements
  - [ ] Créer un pool asynchrone avec `asyncpg.create_pool()` dans `connection.py`
  - [ ] Migrer tous les endpoints FastAPI vers des requêtes asynchrones via le pool `asyncpg`
  - [ ] Conserver `psycopg2` pour les workers synchrones (backtest, optimisation) — pas de régression
  - [ ] Tester la concurrence sous charge (10+ requêtes simultanées) pour vérifier l'absence de blocages
- **Effort** : M (2-3 jours)

### Tâche 2.2 — Résolution du pattern N+1 (§3.2 — Requêtes N+1)

- **Criticité** : ⚠ HAUT
- **Fichiers impactés** :
  - [engine.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/engine.py) (`_update_portfolio_nav`)
- **Actions** :
  - [ ] Remplacer la boucle de requêtes individuelles par une requête unique : `SELECT * FROM live_prices WHERE ticker IN ($1, $2, ...)`
  - [ ] Mettre à jour les positions en mémoire à partir du résultat groupé
  - [ ] Effectuer un `UPDATE` groupé (ou `executemany`) pour persister les MAJ de NAV
  - [ ] Mesurer l'amélioration : objectif ≥ 5x pour un portefeuille de 10+ positions
- **Effort** : S (0.5-1 jour)

### Tâche 2.3 — Buffer I/O pour la sérialisation JSON (§3.2 — Surcharge JSON)

- **Criticité** : ⚠ MOYEN
- **Fichiers impactés** :
  - Fichier contenant `_json_dump` (module optimisation)
- **Actions** :
  - [ ] Implémenter un buffer en mémoire (liste Python) pour les "best rows" de l'optimisation
  - [ ] Écrire sur le disque par lots (toutes les N=50 itérations ou à la fin du trial)
  - [ ] Ajouter un flush forcé en cas d'interruption (`atexit` ou `finally`)
  - [ ] Mesurer la réduction des appels I/O
- **Effort** : XS (0.5 jour)

### Critères de Complétion Phase 2

- [ ] Les endpoints FastAPI utilisent un pool de connexions asynchrone (`asyncpg`)
- [ ] La fonction `_update_portfolio_nav` exécute au maximum 2 requêtes SQL (1 SELECT groupé + 1 UPDATE groupé) quel que soit le nombre de positions
- [ ] Les écritures JSON d'optimisation sont bufferisées (pas d'I/O à chaque itération)
- [ ] Tests de charge : aucun deadlock ou blocage sous 10 requêtes concurrentes
- [ ] `psycopg2` reste opérationnel pour les workers synchrones (pas de régression backtest)

---

## Phase 3 — Architecture & DRY

> **Priorité** : P2 — Amélioration
> **Objectif** : Réduire la dette technique, la duplication de code, et améliorer la testabilité du moteur.
> **Effort estimé** : XL (7-10 jours-homme)
> **Dépendances** : Phase 2 (la migration asyncpg dans `connection.py` doit être stabilisée avant de centraliser les connexions DB).

### Tâche 3.1 — Extraction de `BaseStrategyRunner` (§2.2 — Duplication stratégies)

- **Criticité** : ⚠ MOYEN
- **Fichiers impactés** :
  - [hma_crossover.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/strategies/hma_crossover.py)
  - [momentum_based_zigzag.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/strategies/momentum_based_zigzag.py)
  - Toutes les stratégies dans `backtest_engine/strategies/`
  - **Nouveau** : `backtest_engine/strategies/strategy_base.py`
- **Actions** :
  - [ ] Auditer les fonctions dupliquées à travers les stratégies : `_normalize_trades`, `_build_state_from_broker`, `_apply_overrides`, boucle de simulation principale
  - [ ] Créer une classe abstraite `BaseStrategyRunner` dans `strategy_base.py` encapsulant la logique commune
  - [ ] Définir les points d'extension (méthodes abstraites) pour la logique spécifique à chaque stratégie
  - [ ] Migrer chaque stratégie existante pour hériter de `BaseStrategyRunner`
  - [ ] Valider la compatibilité avec le `StrategyRegistry` existant
  - [ ] Objectif : réduction de ≥80% de la duplication mesurée en lignes de code
- **Effort** : L (4-5 jours)

### Tâche 3.2 — Centralisation des connexions DB (§2.2 — Duplication connexion)

- **Criticité** : ⚠ MOYEN
- **Fichiers impactés** :
  - [connection.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/connection.py)
  - [api.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/api.py)
  - [db_setup.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/db_setup.py)
- **Actions** :
  - [ ] Faire de `connection.py` le point d'entrée unique pour toute connexion DB (sync et async)
  - [ ] Supprimer les créations de connexions dupliquées dans `api.py` et `db_setup.py`
  - [ ] Exposer une interface claire : `get_async_pool()` pour FastAPI, `get_sync_connection()` pour les workers
  - [ ] Tester que tous les modules utilisent exclusivement `connection.py`
- **Effort** : S (1 jour)

### Tâche 3.3 — Refactoring de `engine.py` (§2.2 — Complexité engine)

- **Criticité** : ⚠ MOYEN
- **Fichiers impactés** :
  - [engine.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/engine.py) (500+ lignes)
  - **Nouveau** : `backtest_engine/live/paper_trading/signal_executor.py`
- **Actions** :
  - [ ] Identifier les blocs de logique métier dans `engine.py` : évaluation des signaux, exécution des trades, calcul du NAV
  - [ ] Extraire la logique métier dans un module `signal_executor.py`
  - [ ] Garder dans `engine.py` uniquement l'infrastructure : connexions DB, Redis, orchestration des cycles
  - [ ] Améliorer la testabilité : `signal_executor.py` doit être testable sans infrastructure (mock DB/Redis)
  - [ ] Vérifier l'absence de régression sur le Paper Trading
- **Effort** : M (2-3 jours)

### Critères de Complétion Phase 3

- [ ] `BaseStrategyRunner` existe et toutes les stratégies en héritent
- [ ] `connection.py` est le point d'entrée unique pour les connexions DB
- [ ] `engine.py` est réduit à l'orchestration infrastructure (≤250 lignes)
- [ ] `signal_executor.py` est testable indépendamment avec des mocks
- [ ] Le `StrategyRegistry` continue de fonctionner sans modification de l'API publique
- [ ] Tests de non-régression : backtest et Paper Trading passent

---

## Phase 4 — Robustesse

> **Priorité** : P2 — Moyen
> **Objectif** : Renforcer la gestion des erreurs pour éviter les fuites d'information et les pannes silencieuses en production.
> **Effort estimé** : S (2-3 jours-homme)
> **Dépendances** : Phase 3 (le refactoring de `engine.py` facilitera la mise en place des exceptions spécifiques dans `signal_executor.py`).

### Tâche 4.1 — Exceptions spécifiques (§4.2 — Exceptions génériques)

- **Criticité** : ⚠ MOYEN
- **Fichiers impactés** : Tous les modules avec `except Exception as e` — principalement :
  - [engine.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/engine.py)
  - [api.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/api.py)
- **Actions** :
  - [ ] Auditer tous les blocs `except Exception as e` avec `grep -rn "except Exception" backtest_engine/`
  - [ ] Remplacer par des exceptions spécifiques : `ValueError`, `KeyError`, `FileNotFoundError`, `ConnectionError`, `asyncpg.PostgresError`, etc.
  - [ ] Conserver un `except Exception` uniquement au niveau du middleware global FastAPI comme filet de sécurité
  - [ ] Créer des exceptions métier custom si nécessaire : `SignalExecutionError`, `PortfolioUpdateError`
- **Effort** : S (1 jour)

### Tâche 4.2 — Messages d'erreur production (§4.2 — Fuites d'informations)

- **Criticité** : ⚠ MOYEN
- **Fichiers impactés** :
  - [web.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/web.py) (tous les `_api_error(str(exc), ...)`)
  - [api.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/api.py)
- **Actions** :
  - [ ] Créer un helper `safe_error_response(exc, request)` qui :
    - Logge l'erreur complète côté serveur (`logger.exception(...)`)
    - Renvoie un message générique à l'utilisateur : `"An internal error occurred. Reference: {uuid}"`
    - Inclut un UUID de corrélation pour le debugging
  - [ ] Remplacer tous les `_api_error(str(exc))` par le helper sécurisé
  - [ ] Conditionner le mode verbose aux environnements de développement (`DEBUG=true`)
- **Effort** : S (0.5-1 jour)

### Tâche 4.3 — Timeouts réseau explicites (§4.2 — Absence timeouts)

- **Criticité** : ⚠ MOYEN
- **Fichiers impactés** :
  - [engine.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/live/paper_trading/engine.py) (appels `urllib.request.urlopen`)
  - Tout appel HTTP externe dans le projet
- **Actions** :
  - [ ] Auditer tous les appels réseau : `grep -rn "urlopen\|requests\.\|httpx\.\|aiohttp" backtest_engine/`
  - [ ] Ajouter un timeout explicite à chaque appel (recommandation : 10s pour les APIs, 30s pour les téléchargements)
  - [ ] Centraliser les timeouts dans une constante ou la configuration (`utils.py` : `NETWORK_TIMEOUT_DEFAULT = 10`)
  - [ ] Gérer proprement les `TimeoutError` et `ConnectionError`

> [!NOTE]
> Les timeouts Redis ont déjà été traités dans le Sprint 1 (2026-07-03). Cette tâche concerne uniquement les appels HTTP externes.

- **Effort** : XS (0.5 jour)

### Critères de Complétion Phase 4

- [ ] Aucun `except Exception` ne subsiste en dehors du middleware global
- [ ] Aucune trace technique interne n'est exposée dans les réponses API en production
- [ ] Tous les appels réseau ont un timeout explicite
- [ ] Les exceptions métier custom sont définies et utilisées
- [ ] Tests : vérifier qu'une erreur interne produit un message générique + UUID de corrélation

---

## Phase 5 — Hygiène & Dette Technique

> **Priorité** : P2 — Amélioration
> **Objectif** : Optimiser la structure du projet pour les déploiements et le développement futur.
> **Effort estimé** : S (1-2 jours-homme)
> **Dépendances** : Phase 2 (les requirements doivent refléter la séparation sync/async post-migration asyncpg).

### Tâche 5.1 — Séparation des requirements (§5.2 — Dépendances)

- **Criticité** : ⚠ MOYEN
- **Fichiers impactés** :
  - [requirements-backtest-engine.txt](file:///home/kidpixel/trading_automation_v2/requirements-backtest-engine.txt)
  - **Nouveaux** : `requirements-base.txt`, `requirements-backtest.txt`, `requirements-live.txt`
- **Actions** :
  - [ ] Créer `requirements-base.txt` : dépendances communes (pandas, numpy, python-dotenv, loguru)
  - [ ] Créer `requirements-backtest.txt` : dépendances backtest uniquement (optuna, vectorbt, numba)
  - [ ] Créer `requirements-live.txt` : dépendances Paper Trading / Live (fastapi, uvicorn, asyncpg, psycopg2, redis)
  - [ ] Chaque fichier spécialisé inclut `-r requirements-base.txt`
  - [ ] Mettre à jour le Dockerfile/scripts de déploiement Render pour utiliser le bon fichier requirements selon le service
  - [ ] Documenter la structure dans le README
- **Effort** : S (0.5-1 jour)

### Tâche 5.2 — Nettoyage dette technique résiduelle

- **Actions** :
  - [ ] Vérifier et supprimer les imports inutilisés (utiliser `ruff` ou `flake8 --select F401`)
  - [ ] Vérifier la cohérence des conventions de nommage (snake_case partout)
  - [ ] S'assurer que tous les fichiers Python ont un `__all__` pour les modules publics
  - [ ] Vérifier la couverture du typage statique (objectif : ≥ 90% sur les modules critiques)
- **Effort** : XS (0.5 jour)

### Critères de Complétion Phase 5

- [ ] 3 fichiers requirements distincts existent et sont fonctionnels
- [ ] Le déploiement Render utilise `requirements-live.txt` pour l'ingesteur
- [ ] Aucun import inutilisé, conventions de nommage cohérentes
- [ ] README mis à jour avec la structure des requirements

---

## Diagramme des Dépendances Inter-Phases

```mermaid
graph LR
    P1["Phase 1<br/>Sécurité Critique<br/>P0 | 5-7j"]
    P2["Phase 2<br/>Performance & DB<br/>P1 | 3-5j"]
    P3["Phase 3<br/>Architecture & DRY<br/>P2 | 7-10j"]
    P4["Phase 4<br/>Robustesse<br/>P2 | 2-3j"]
    P5["Phase 5<br/>Hygiène<br/>P2 | 1-2j"]

    P2 --> P3
    P3 --> P4
    P2 --> P5

    style P1 fill:#ff4444,color:#fff,stroke:#cc0000
    style P2 fill:#ff8800,color:#fff,stroke:#cc6600
    style P3 fill:#ffcc00,color:#333,stroke:#cc9900
    style P4 fill:#44aaff,color:#fff,stroke:#0077cc
    style P5 fill:#88cc44,color:#fff,stroke:#669933
```

> [!IMPORTANT]
> **Phase 1 et Phase 2 sont indépendantes** et peuvent être exécutées en parallèle si deux développeurs sont disponibles. Sinon, Phase 1 d'abord (sécurité = bloquant prod).

---

## Gantt Prévisionnel

```mermaid
gantt
    title Plan d'Action Audit Backend
    dateFormat  YYYY-MM-DD
    axisFormat  %d/%m

    section Phase 1 — Sécurité
    Secrets HMAC (§1.1)              :p1a, 2026-07-07, 1d
    Protection CSRF (§1.2)           :p1b, after p1a, 3d
    Validation Pydantic (§1.3)       :p1c, after p1b, 1d
    Headers CORS/CSP (Checklist)     :p1d, after p1c, 1d
    Validation Phase 1               :milestone, p1m, after p1d, 0d

    section Phase 2 — Performance
    Migration asyncpg (§3.2)         :p2a, 2026-07-07, 3d
    Résolution N+1 (§3.2)           :p2b, after p2a, 1d
    Buffer I/O JSON (§3.2)          :p2c, after p2b, 1d
    Validation Phase 2               :milestone, p2m, after p2c, 0d

    section Phase 3 — Architecture
    BaseStrategyRunner (§2.2)        :p3a, after p2m, 5d
    Centralisation DB (§2.2)         :p3b, after p3a, 1d
    Refactoring engine.py (§2.2)     :p3c, after p3b, 3d
    Validation Phase 3               :milestone, p3m, after p3c, 0d

    section Phase 4 — Robustesse
    Exceptions spécifiques (§4.2)    :p4a, after p3m, 1d
    Messages erreur prod (§4.2)      :p4b, after p4a, 1d
    Timeouts réseau (§4.2)          :p4c, after p4b, 1d
    Validation Phase 4               :milestone, p4m, after p4c, 0d

    section Phase 5 — Hygiène
    Séparation requirements (§5.2)   :p5a, after p2m, 1d
    Nettoyage dette technique        :p5b, after p5a, 1d
    Validation Phase 5               :milestone, p5m, after p5b, 0d
```

---

## Contraintes et Garde-fous

> [!WARNING]
> - **Ne pas casser le Registry pattern** : Toute extraction de `BaseStrategyRunner` doit maintenir la compatibilité avec `StrategyRegistry`.
> - **Séparation sync/async** : `psycopg2` reste pour les workers backtest/optimisation. `asyncpg` est pour FastAPI uniquement.
> - **Chaque phase est auto-contenue** : déployable indépendamment sans régressions. Tester en staging avant merge.
> - **Respect des coding standards** : Toute modification suit les règles définies dans `codingstandards.md`.
