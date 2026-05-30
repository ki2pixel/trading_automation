# Audit Backend Complet — Trading Automation v2

> [!NOTE]
> **Statut : Terminé (100%)** — *21 Mai 2026*
> Toutes les recommandations et points d'audit identifiés ont été implémentés et validés avec succès dans le cadre de la refactorisation complète du backend Python (`backtest_engine/`).

Audit exhaustif du backend Python (`backtest_engine/`) couvrant architecture, qualité de code, performance, tests, sécurité et robustesse, avec livrable un plan de refactoring priorisé.

---

## 1. Architecture & Couplage

### 1.1 Analyse de la structure modulaire
- **Scope** : `backtest_engine/*.py`, `strategies/`, `vectorbt_bridge/`, `tests/`
- **Objectif** : Mesurer le couplage entre modules, identifier les violations de séparation des responsabilités
- **Méthode** : Analyser les imports croisés, la taille des modules, les dépendances cycliques potentiellement
- **Points de vigilance identifiés** :
  - `configuration.py` fait ~104 KB — explosion de définitions de paramètres répétées par stratégie
  - `__main__.py` utilise une chaîne `if/elif` pour router 7 stratégies avec imports individuels
  - `bayesian_optimizer.py` importe massivement depuis `optimizer.py` (couplage fort)
  - `web.py` répète les imports de toutes les stratégies
  - `strategies/__init__.py` n'exporte que 2 stratégies sur 7

### 1.2 Points d'audit spécifiques
- [x] Évaluer l'introduction d'une factory/registry de stratégies pour éliminer le couplage explicite
- [x] Vérifier si `configuration.py` peut être découpé par stratégie ou généré dynamiquement
- [x] Analyser la cohérence de l'interface `run_<strategy>()` (signature variable — `noise_boundary_intraday` prend `repo_root` en plus)
- [x] Vérifier le rôle de `vectorbt_bridge/` : est-ce un adapter propre ou du code dupliqué ?

---

## 2. Code Quality & Maintenabilité

### 2.1 Complexité et duplication
- **Scope** : Tous les fichiers `.py` du backend
- **Méthode** : Analyse statique manuelle + comptage de lignes, duplication de patterns
- **Métriques cibles** :
  - [x] Taille de `configuration.py` (104 KB) — combien de définitions dupliquées ?
  - [x] Code répété dans les 7 stratégies (patterns Pine Script → Python répétés)
  - [x] Fonctions > 50 lignes, classes > 300 lignes
  - [x] Constantes dupliquées (`BASE_TIMEFRAME_MINUTES` dans `data.py` ET `metrics.py`)

### 2.2 Conventions et style
- [x] Cohérence des docstrings (présentes mais inégales)
- [x] Usage des type hints (bon globalement, mais certains `Any` et `object` lâches)
- [x] Nommage : mélange de snake_case, certains noms cryptiques (`sLow`, `sHigh`)
- [x] Fichiers vides ou quasi-vides (`test_mo_scoring.py` = 0 bytes)

### 2.3 Gestion des configurations
- [x] `job_store.py` : chemin SQLite hardcodé absolu (`/mnt/venv_ext4/...`)
- [x] `__main__.py` : `_repo_root()` = `Path.cwd()` — fragile si exécuté depuis un autre répertoire
- [x] Pas de validation de l'environnement au démarrage

---

## 3. Performance & Scalabilité

### 3.1 Accès données
- **Scope** : `data.py`, `canonical.py`, chargement Parquet
- **Points d'audit** :
  - [x] Efficacité du chargement Parquet via `fastparquet` vs `pyarrow`
  - [x] `load_canonical_market_data()` : gestion mémoire sur gros datasets
  - [x] `filter_time_window()` : copie systématique `.copy()` — nécessaire ?
  - [x] Pas de caching de données entre runs d'optimisation (charger le même dataset 1000x)

### 3.2 Optimisation & parallélisation
- **Scope** : `optimizer.py`, `bayesian_optimizer.py`
- **Points d'audit** :
  - [x] `ProcessPoolExecutor` utilisé mais `_WORKER_DATA` global — vérifier la sérialisation
  - [x] `bayesian_optimizer.py` : docstring dit "single-process only" mais importe `ProcessPoolExecutor`
  - [x] Pas de streaming des résultats d'optimisation — tout stocké en mémoire puis flushé
  - [x] `clear_*_feature_cache()` appelé manuellement — risque de fuite mémoire

### 3.3 Web & API
- **Scope** : `web.py`, `job_store.py`
- **Points d'audit** :
  - [x] FastAPI sert des fichiers statiques via `FileResponse` — pas de CDN/cache
  - [x] SQLite avec `RLock` — suffisant pour la concurrence ?
  - [x] Pas de pagination sur les endpoints de liste

---

## 4. Tests & Fiabilité

### 4.1 Couverture et qualité
- **Scope** : `tests/*.py`
- **Points d'audit** :
  - [x] `test_backtest_engine.py` = 65 KB, mais que couvre-t-il exactement ?
  - [x] `test_mo_scoring.py` = 0 bytes — fichier mort
  - [x] Manque de tests d'intégration end-to-end (CLI → API → rapport)
  - [x] Pas de tests pour `web.py` (API FastAPI)
  - [x] Pas de tests pour `bayesian_optimizer.py`
  - [x] Pas de tests de charge pour le job store SQLite

### 4.2 Cas limites et robustesse
- [x] Que se passe-t-il si `load_market_data()` ne trouve aucun fichier ?
- [x] Gestion des datasets vides dans les stratégies
- [x] Division par zéro dans `metrics.py` — bien protégée mais à vérifier exhaustivement
- [x] Que se passe-t-il si l'optimisateur dépasse `max_iterations` ?

---

## 5. Sécurité & Robustesse

### 5.1 Validation des entrées
- **Scope** : `web.py`, `__main__.py`, endpoints API
- **Points d'audit** :
  - [x] `ViewerChartRequest` valide `strategy` mais `noise_boundary_intraday` manque de `StrategyPayload`
  - [x] `OptimizerRequestPayload` délègue la validation — où ?
  - [x] Pas de rate limiting sur l'API
  - [x] Pas de limite de taille sur les payloads JSON
  - [x] Chemins de fichiers (`output_dir`, `processed_dir`) — validation insuffisante, risque path traversal

### 5.2 Gestion des erreurs
- [x] FastAPI : pas de handler global d'exception custom
- [x] `RequestValidationError` renvoie des messages potentiellement trop verbeux
- [x] Broker : que se passe-t-il avec des prix `NaN` ou négatifs ?
- [x] Pas de circuit breaker sur l'optimisation (peut boucler infiniment)

### 5.3 Concurrence et état
- [x] `RLock` sur SQLite — suffisant mais pas scalable
- [x] `_WORKER_DATA` global dans `optimizer.py` — thread-safe ? process-safe ?
- [x] Pas de mécanisme de timeout sur les jobs d'optimisation

---

## 6. Dépendances & Environnement

### 6.1 Gestion des dépendances
- **Scope** : `requirements-backtest-engine.txt`
- **Problèmes identifiés** :
  - [x] `optuna` utilisé dans `bayesian_optimizer.py` mais absent de `requirements-backtest-engine.txt`
  - [x] `vectorbt` référencé dans `vectorbt_bridge/` mais absent de requirements
  - [x] `pytest` absent (dev dependency manquante)
  - [x] `scipy`, `scikit-learn` potentiellement utilisés ?
  - [x] Pas de `requirements-dev.txt`

### 6.2 Compatibilité
- [x] Python 3.10+ utilisé (annotations futures) — OK
- [x] Pandas 2.3+ / Numpy 2.2+ — versions récentes, risque de breaking changes

---

## 7. Livrables attendus

1. **Rapport d'audit détaillé** (format markdown) avec :
   - Tableau de bord des risques ( Critical / High / Medium / Low )
   - Pour chaque module : forces, faiblesses, recommandations
   - Métriques quantitatives (lignes de code, duplication, complexité estimée)

2. **Plan de refactoring priorisé** avec :
   - Tâches découpées par sprints (court terme / moyen terme)
   - Estimation d'impact vs effort
   - Dépendances entre tâches

3. **Liste des quick-wins** (corrections < 30 min chacune)

---

## 8. Phases d'exécution

| Phase | Durée estimée | Focus | Statut |
|-------|--------------|-------|--------|
| Phase 1 | ~1h | Lecture approfondie de chaque module, extraction des métriques | **Terminé** |
| Phase 2 | ~1h | Analyse des tests, exécution, couverture | **Terminé** |
| Phase 3 | ~1h | Audit sécurité/robustesse, validation entrées, gestion erreurs | **Terminé** |
| Phase 4 | ~30min | Synthèse, scoring des risques, rédaction du plan de refactoring | **Terminé** |

---

*Plan généré le 20 mai 2026. Entièrement réalisé le 21 mai 2026.*
