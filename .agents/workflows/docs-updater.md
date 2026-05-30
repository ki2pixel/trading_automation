---
description: Docs Updater, Standard Tools, Cloc Radon, Quality Context (Trading Automation)
---

# Workflow: Docs Updater — Standardized & Metric-Driven (Trading)

> Ce workflow harmonise la documentation en utilisant l'analyse statique standard (`cloc`, `radon`, `tree`) étendue avec fast-filesystem et ripgrep pour la précision technique et les modèles de référence pour la qualité éditoriale. Couvre l'ensemble du codebase (moteur, stratégies, connecteurs) incluant docs/ et tests/ pour éviter les lacunes de documentation.

## 🚨 Protocoles Critiques
1.  **Outils autorisés** : MCP fast-filesystem (`fast_read_file`, `fast_read_multiple_files`, `fast_list_directory`, `fast_get_directory_tree`, `fast_search_files`, `fast_write_file`), MCP filesystem-agent (`edit_file`, `move_file`, `create_directory`), MCP ripgrep (`search`, `advanced-search`, `count-matches`, `list-files`, `list-file-types`), et `run_command` limité aux audits (`tree`, `cloc`, `radon`, `find`, `ls`).
2.  **Contexte** : Initialiser le contexte en appelant l'outil fast_read_file du serveur memory-bank pour lire UNIQUEMENT activeContext.md. Ne lire les autres fichiers de la Memory Bank que si une divergence majeure est détectée lors du diagnostic.
3.  **Source de Vérité** : Le Code (analysé par outils) > La Documentation existante > La Mémoire.
4.  **Sécurité Memory Bank** : Utilisez les outils fast-filesystem (fast_*) pour accéder aux fichiers memory-bank avec des chemins absolus.

### Migration filesystem → fast-filesystem

| Aspect | Outils filesystem | Outils fast-filesystem | Trade-offs |
|--------|------------------|------------------------|------------|
| **Performance** | Appels individuels | Traitement par lot avec chunking auto | ✅ + Optimisé pour gros volumes |
| **Fiabilité** | Risque d'erreurs manuelles | Vérification intégrée + backup automatique | ✅ + Sécurité renforcée |
| **Fonctionnalités** | Base standard | Fonctionnalités avancées (compression, sync, recherche avancée) | ✅ + Capacités étendues |
| **Maintenance** | Outils génériques | Spécialisés MCP avec verrous | ✅ + Cohérence architecture |

## Étape 1 — Audit Structurel et Métrique
Lancer les commandes suivantes pour ignorer les dossiers de données financières (ex: `financial_datasets`, `logs`) et cibler le cœur applicatif de trading.

1.  **Cartographie (Filtre Bruit)** :
    - `run_command "tree -L 2 -I '__pycache__|venv|node_modules|.git|logs|debug|data|financial_datasets|test*'"`
    - *But* : Visualiser uniquement l'architecture logicielle (`core`, `strategies`, `data`, `execution`, `utils`).

2.  **Cartographie Étendue (Fast-Filesystem)** :
    - `fast_get_directory_tree(path="/home/kidpixel/trading_automation_v2", max_depth=3, include_files=false, exclude_patterns=["__pycache__", "venv", "node_modules", ".git", "logs", "debug", "data", "financial_datasets", ".shrimp_task_manager"])`
    - *But* : Explorer récursivement la structure complète avec focus sur docs/, tests/, et l'implémentation du moteur.

3.  **Scan des Stratégies et Scripts** :
    - `fast_list_directory(path="/home/kidpixel/trading_automation_v2/strategies", pattern="*.py", show_hidden=false)`
    - `fast_list_directory(path="/home/kidpixel/trading_automation_v2/scripts", pattern="*.py|*.sh", show_hidden=false)`
    - *But* : Identifier toutes les stratégies implémentées et les scripts utilitaires.

4.  **Volumétrie (Code Source)** :
    - `run_command "cloc core strategies data execution utils scripts --md"`
    - *But* : Quantifier le code réel (Python) sans scanner les jeux de données CSV/JSON.

5.  **Volumétrie Étendue (Documentation & Tests)** :
    - `run_command "cloc docs tests --md"`
    - *But* : Mesurer la volumétrie des zones documentation et tests pour équilibrer les efforts de mise à jour.

6.  **Complexité Cyclomatique (Python Core)** :
    - `run_command "radon cc core strategies data execution utils -a -nc"`
    - *But* : Repérer les points chauds (Score C/D/F).
    - **Règle** : Si Score > 10 (C), la doc DOIT expliquer la logique interne (ex: calculs d'indicateurs, gestion d'ordres), pas juste les entrées/sorties.

7.  **Analyse Patterns Large (Ripgrep)** :
    - `advanced-search(pattern="class|def|function", path="/home/kidpixel/trading_automation_v2", file_pattern="*.py", context=1, exclude_patterns=[".shrimp_task_manager", "financial_datasets"])`
    - `advanced-search(pattern="TODO|FIXME|HACK|PERF", path="/home/kidpixel/trading_automation_v2", file_pattern="*.py|*.md", context=0, exclude_patterns=[".shrimp_task_manager", "financial_datasets"])`
    - *But* : Détecter les patterns architecturaux et marqueurs de dette technique à travers le codebase élargi.

8.  **Fichiers Récemment Modifiés** :
    - `run_command "find /home/kidpixel/trading_automation_v2 -name '*.py' -o -name '*.md' -mtime -30 -type f | grep -v 'financial_datasets' | head -20"`
    - *But* : Identifier les fichiers modifiés récemment pour prioriser les zones nécessitant des mises à jour documentation.

## Étape 2 — Diagnostic Triangulé
Comparer les sources pour détecter les incohérences :

| Source | Rôle | Outil |
| :--- | :--- | :--- |
| **Intention** | Le "Pourquoi" | `fast_read_file` (via MCP) |
| **Réalité** | Le "Quoi" & "Comment" | `radon` (complexité), `cloc` (volume), `fast_search_files` |
| **Existant** | L'état actuel | `fast_search_files` (sur `docs/`), `fast_read_file` |

**Action** : Identifier les divergences. Ex: "Le module `core/backtest_engine.py` est complexe (Radon C) mais ses mécanismes de synchronisation sont absents de la doc technique."

## Étape 3 — Sélection du Standard de Rédaction
Choisir le modèle approprié au domaine financier :

- **Documentation Moteur (Core & Execution)** (`core/`, `execution/`) :
  - Architecture des classes, gestion d'états, thread-safety.
  - Gestion des erreurs critiques (ex: perte de connexion broker, rejets d'ordres).
  - Métriques de performance et optimisation (Numpy/Pandas).
- **Documentation Stratégies** (`strategies/`) :
  - Logique d'entrée/sortie (signaux).
  - Paramètres configurables (inputs) et indicateurs techniques utilisés.
  - Résultats de backtest attendus ou limites connues.
- **Documentation Données & Connecteurs** (`data/`, `brokers/`) :
  - Format de données attendu (ex: OHLCV, ticks).
  - Spécifications des APIs externes (Supabase, Binance, IBKR, etc.).
  - Mécanismes de résilience et de cache.

## Étape 4 — Proposition de Mise à Jour
Générer un plan de modification avant d'appliquer :

## 📝 Plan de Mise à Jour Documentation
### Audit Métrique
- **Cible** : `core/backtest_engine.py`
- **Métriques** : 450 LOC, Complexité max C (12).

### Modifications Proposées
#### 📄 docs/architecture/.../target.md
- **Type** : [Moteur | Stratégie | Connecteur]
- **Diagnostic** : [Obsolète | Incomplet | Manquant]
- **Correction** :
```markdown
  [Contenu proposé respectant le standard choisi]
```

## Étape 5 — Application et Finalisation
1.  **Exécution** : Après validation, utiliser `edit_file`.
2.  **Mise à jour Memory Bank** :
    - Mettre à jour la Memory Bank en utilisant EXCLUSIVEMENT l'outil edit_file.

### Sous-protocole Rédaction — Application de documentation/SKILL.md

#### 5.1 Point d'Entrée Explicite
- **Mode Rédaction** : Déclenché après validation du plan de mise à jour.
- **Lecture obligatoire** : `.agents/skills/documentation/SKILL.md`.
- **Modèle à appliquer** : Spécifié dans le plan (article deep-dive, README, fiche technique, etc.).

#### 5.2 Checkpoints Obligatoires
**Avant rédaction** :
- [ ] TL;DR présent (section 1 du skill)
- [ ] Problem-first opening (section 2 du skill)

**Pendant rédaction** :
- [ ] Comparaison ❌/✅ (section 4 du skill)
- [ ] Trade-offs table si applicable (section 7 du skill)
- [ ] Golden Rule (section 8 du skill)
- [ ] Éviter les artefacts AI (section 6 du skill)

**Après rédaction** :
- [ ] Validation checklist « Avoiding AI-Generated Feel »
- [ ] Vérification ponctuation (remplacer " - " par ;/:/—)

#### 5.3 Traçabilité
Dans la proposition de mise à jour (Étape 4), ajouter :
#### Application du skill
- **Modèle** : [Article deep-dive | README | Technique]
- **Éléments appliqués** : TL;DR ✔, Problem-First ✔, Comparaison ✔, Trade-offs ✔, Golden Rule ✔

#### 5.4 Hook d'Automation
- **Validation Git** : Commentaire de commit « Guidé par documentation/SKILL.md — sections: [liste] »
- **Blocking** : Le workflow ne peut pas se terminer si les checkpoints ne sont pas cochés
- **Audit trail** : Chaque fichier modifié contient une note de validation interne