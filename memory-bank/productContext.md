# Contexte Produit : Trading Automation v2

## Objectif du Produit
Ce projet est un système d'automatisation de trading (Trading Automation v2). Son objectif principal est de fournir un moteur robuste de backtest, d'analyse et d'exécution de stratégies financières.

## Architecture Générale
- **Moteur de Backtest & Scripts** : Python (typage statique, performance via Numpy/Pandas).
- **Stockage de données** : Local via fichiers Parquet (pyarrow/fastparquet).
- **Standards** : Définis dans `.agents/rules/codingstandards.md`.