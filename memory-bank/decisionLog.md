# Journal des Décisions

> Ce document trace les décisions techniques majeures et leur justification.

## [2026-05-30 16:15:00] - Initialisation de la documentation
- **Décision** : Nettoyage de l'historique hérité du projet précédent et initialisation des fichiers du Memory Bank Protocol (`productContext.md`, `activeContext.md`, `systemPatterns.md`, `decisionLog.md`, `progress.md`) pour le projet `trading_automation_v2`.
- **Justification** : Repartir sur une base propre adaptée aux règles et au domaine financier de ce projet.

## [2026-05-30 16:33:00] - Alignement et Documentation de l'Optimisation Bayésienne Avancée
- **Décision** : Ajout et documentation des concepts d'Optimisation Multi-Objectif (Front de Pareto) et d'Importance des Paramètres (fANOVA) dans `optimization.md` pour refléter les fonctionnalités réelles de `bayesian_optimizer.py`.
- **Justification** : Combler un écart documentaire majeur pour les développeurs utilisant les capacités d'exploration intelligente d'Optuna.

## [2026-05-31 01:33:00] - Suppression de l'archive inactive KLineChart
- **Décision** : Suppression définitive de `ressources/KLineChart-10.0.0-beta1/` (6.2 Mo) et retrait de son ignorance dans `.gitignore`.
- **Justification** : Alléger le dépôt des fichiers sources et documentations non utilisés, sachant que le projet charge la librairie de manière autonome via `vendor/klinecharts.min.js`.
