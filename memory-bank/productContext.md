# Contexte Produit : Trading Automation v2

## Objectif du Produit
Ce projet est un système d'automatisation de trading (Trading Automation v2). Son objectif principal est de fournir un moteur professionnel et robuste de backtest, d'analyse, d'optimisation, et d'exécution live de stratégies financières.

## Piliers Fonctionnels

### 1. Ingestion & Data Flow
Le système assure l'ingestion normalisée et vectorisée de données de marché. Pour garantir une vélocité maximale lors des analyses massives, le stockage de données s'effectue localement sous forme de fichiers Parquet structurés (via pyarrow/fastparquet).

### 2. Moteur de Simulation
Le cœur du backtesting repose sur un moteur de simulation hautement vectorisé (basé sur Pandas et Numpy). Il est conçu avec une gestion stricte du look-ahead bias et intègre de manière réaliste les contraintes du marché : simulation précise des frais de courtage, calcul du slippage et exécution asynchrone des signaux.

### 3. Moteur d'Optimisation
L'architecture intègre un moteur d'optimisation hyperparamétrique avancé (utilisant Optuna pour l'optimisation bayésienne). Pour lutter efficacement contre le surapprentissage (overfitting), les stratégies sont soumises à une validation par Walk-Forward Analysis (WFA).

### 4. Exécution & Routage Réels
Au-delà de la simulation, le projet offre une intégration complète en temps réel de l'API Trading 212. Ce module gère la synchronisation du portefeuille en direct, le routage d'ordres avancés (marché, limite, stop) et implémente une boucle de contrôle des risques (gestion stricte du capital et de l'exposition globale).

### 5. Dashboard & Performance Reporting
L'analyse des performances est restituée au travers d'une interface web embarquée (`web.py`). Ce module de reporting offre des rapports visuels détaillés (via `reports.py` et `metrics.py`), permettant le suivi d'indicateurs financiers clés tels que le ratio de Sharpe, le Maximum Drawdown et l'attribution de performance.

## Architecture Générale
- **Moteur de Backtest & Scripts** : Python (typage statique strict, haute performance).
- **Stockage de données** : Local via fichiers Parquet (pyarrow/fastparquet).
- **Standards** : Les règles de développement sont définies dans `.agents/rules/codingstandards.md`.