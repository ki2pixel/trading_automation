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

## [2026-05-31 15:55:00] - Diagnostic du Safety Stop 5% sur SAP
- **Décision** : Maintien du paramètre `use_safety_stop: true` à 5% par défaut pour les stratégies de suivi de tendance (Range Filter, HMA Crossover, PMax Explorer), et abandon des tests de ces algorithmes sur l'actif SAP.
- **Justification** : Un test A/B a prouvé que les performances (très négatives) sur SAP sont structurellement identiques avec ou sans le safety stop. La destruction de valeur provient des faux signaux réguliers (whipsaws) générés par le prix sur cet actif, déclenchant des sorties avant d'atteindre les -5%.

## [2026-06-01 01:45:00] - Résolution du bug de l'optimiseur (INELIGIBLE_CONSTRAINTS)
- **Décision** : Ajout d'une détection dynamique des métriques requises par les contraintes (exposure_pct, max_drawdown_pct, profit_factor) dans l'optimiseur (`_evaluate_hma_parameters`). Si ces métriques sont absentes car `compute_full_metrics=False` et que le score a réussi avec les métriques rapides, le calcul complet est désormais forcé.
- **Justification** : Résolution du bug critique systémique qui marquait toutes les itérations viables comme inéligibles lors du calcul des contraintes, car les valeurs restaient à `None`.

## [2026-06-09 14:05:00] - Vectorisation Native Pandas pour VectorBT
- **Décision** : Remplacement des appels à des librairies externes inexistantes (comme `talib`) par des opérations natives Pandas (`ewm`, `np.maximum`, `ffill`) dans l'implémentation de l'ATR, de l'ADX et du ZLEMA pour VectorBT.
- **Justification** : Satisfaire l'exigence absolue de "zéro boucle Python" tout en s'assurant de la portabilité et de l'exécution matricielle immédiate du code, sans dépendre d'une librairie C externe.
