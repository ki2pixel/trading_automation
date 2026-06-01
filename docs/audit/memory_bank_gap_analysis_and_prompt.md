# Diagnostic et Spécification Technique (Mega-Prompt)

## 1. Analyse Globale (Footprint Analysis)
L'exploration de l'arborescence (via les outils `fast-filesystem`) révèle une infrastructure de Trading Algorithmique v2 particulièrement riche :
- **Moteur de Backtest Haute Performance (`backtest_engine/`)** : Contient des modules avancés comme `bayesian_optimizer.py` (optimisation hyperparamétrique), `walk_forward.py` (WFA), `simulation_kernel.py`, et `shared_memory.py` (multiprocessing).
- **Routage et Exécution (`broker.py`, `trading212/`)** : Intégration de l'API Trading 212, routage d'ordres (marché, limite, stop), et P&L en direct.
- **Gestion des Données (`data.py`, `canonical.py`, `storage/`)** : Ingestion normalisée et stockage local structuré via Parquet pour des lectures vectorisées massives.
- **Analyse et Reporting (`metrics.py`, `overfitting_analysis.py`, `reports.py`, `web.py`)** : Tableaux de bord visuels, calculs de métriques financières (Sharpe, Drawdown, etc.), et prévention de l'overfitting.
- **Gestion des Stratégies et Signaux (`strategies/`)** : Registre de stratégies, calculs d'indicateurs vectorisés.

## 2. Évaluation Qualitative (Gap Analysis)
L'écart entre la réalité du code source et la documentation actuelle de la Memory Bank est critique. Les fichiers actuels sont "squelettiques" et inaptes à guider une IA sur des tâches d'architecture complexe :
- **`productContext.md` (actuellement ~529 octets)** : Ne mentionne que globalement Python et Parquet. Il ignore totalement l'optimisation bayésienne, l'exécution live via Trading 212, l'interface Web embarquée, et la gestion des risques.
- **`systemPatterns.md` (actuellement ~638 octets)** : Liste des concepts très vagues (SoC, typage statique). L'architecture physique réelle (multiprocessing avec shared memory, event-driven kernel vs vectorisation Pandas, infrastructure Optuna pour les hyperparamètres) est totalement inexistante.

---

## MEGA-PROMPT POUR L'IA SUIVANTE

**Rôle** : Architecte Technique & Gestionnaire de la Memory Bank
**Mission** : Combler le "Gap" entre la réalité physique du projet Trading Automation v2 et sa documentation abstraite en enrichissant `productContext.md` et `systemPatterns.md`.

### INSTRUCTIONS PAS-À-PAS

#### Étape 1 : Enrichissement de `productContext.md`
Mettez à jour le fichier (sans en modifier la structure de base si elle convient, mais en élargissant substantiellement le contenu) pour y inclure les objectifs réels et les workflows métier de la v2 :
- **Ingestion & Data** : Ingestion multi-sources et stockage optimisé local en Parquet.
- **Moteur de Simulation** : Simulation vectorisée (Pandas/Numpy), gestion du look-ahead bias, calcul réaliste des frais et du slippage.
- **Optimisation** : Walk-Forward Analysis (WFA) et Optimisation Bayésienne (Optuna).
- **Exécution Réelle** : Connexion à l'API Trading 212, routage des ordres (marché, limite, stop), synchronisation du portefeuille et contrôle de l'exposition.
- **Reporting** : Interface web embarquée et rapports de performance enrichis (Sharpe, Max Drawdown).

#### Étape 2 : Enrichissement de `systemPatterns.md`
Documentez les véritables patrons de conception de l'architecture :
- **Architecture de Concurrence** : Multiprocessing, `shared_memory.py`, thread-safety pour l'optimisation de stratégies à grande échelle.
- **Modèle d'Exécution** : Séparation stricte entre l'approche vectorisée (massive) et l'approche orientée événements (`simulation_kernel.py`).
- **Patterns de Données** : Flux canonique des données (`canonical.py`), architectures de stockage local Parquet pour la rapidité.
- **Résilience et API** : Gestion des exceptions réseau, retry logic, et sécurité de l'intégration Trading 212 (`broker.py`).

#### Étape 3 : Protocole de Mise à Jour (UMB)
Conformément aux directives de `memorybankprotocol.md`, vous devez OBLIGATOIREMENT respecter le protocole suivant lors de votre exécution :
1. Précéder vos premières actions et réflexions de la balise `[MEMORY BANK: UPDATING]`.
2. Utiliser l'outil `edit_file` pour procéder aux mises à jour incrémentales des fichiers (chemins absolus : `/home/kidpixel/trading_automation_v2/memory-bank/productContext.md` et `/home/kidpixel/trading_automation_v2/memory-bank/systemPatterns.md`).
3. Ajouter un log de décision dans `progress.md` (ou dans la section idoine des fichiers mis à jour) au format de timestamp exact : `[YYYY-MM-DD HH:MM:SS] - [Summary]`.
4. Respecter scrupuleusement les `.agents/rules/codingstandards.md` dans la description de vos modèles (typage strict, conventions de nommage).

**Action attendue de l'IA** :
- Validez la bonne réception de ce prompt.
- Effectuez les modifications documentaires requises via les bons outils.
- Clôturez votre tâche en confirmant l'état de synchronisation avec la balise UMB.
