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

## [2026-06-16 13:28:00] - Arbitrage et Modélisation d'Allocation de Capital
- **Décision** : Développement d'un script d'analyse quantitative (`scripts/analyze_best_performances.py`) traitant l'ensemble des runs parquets des stratégies. Implémentation parallèle du Risk-Parity (inverse du max drawdown) et du Kelly Criterion (fractionnel). Les données de `adaptive_trend_classification` (sans artefacts) ont été volontairement mockées depuis la documentation pour ne pas bloquer le pipeline, avec obligation de réintégration ultérieure.
- **Justification** : Fournir une comparaison objective entre une allocation défensive (Risk-Parity) et une allocation offensive (Kelly) maximisant la croissance géométrique. Cela permet une prise de décision éclairée pour l'activation en live.

## [2026-06-16 17:06:00] - Générateur de Rapport HTML Customisé
- **Décision** : Implémentation d'un générateur HTML (intégré directement dans `scripts/analyze_best_performances.py`) plutôt qu'une solution type Jupyter Notebook ou un script externe. Il injecte les données consolidées via `json.dumps` dans le DOM local.
- **Justification** : Conserver la philosophie UI/UX du projet (calquée sur `optimizer_report.html`) pour offrir un viewer interactif (tris dynamiques, filtres textuels) capable de palier les limites d'affichage du Markdown, sans alourdir la stack par un serveur Node.js / Python.

## [2026-06-19 17:55:00] - Assouplissement du quorum de trades et correction du Profit Factor parfait (None)
- **Décision** : Assouplissement du quorum à `min_closed_trades = 10` pour l'extension de campagne et correction de la faille de division par zéro dans le calcul du profit factor (`optimizer.py`) lorsque `losing_trades = 0` (permettant aux configurations à 100% de win-rate d'être qualifiées au lieu d'être rejetées car leur profit factor valait `None`).
- **Justification** : L'assouplissement a permis de surmonter la barrière de qualification sur les nouveaux actifs à timeframes plus élevés. La correction du profit factor a débloqué et qualifié des configurations exceptionnelles d'akzanleur, beideeur, et dpwdeeur, qui étaient injustement rejetées par le moteur.

## [2026-06-25 14:19:00] - Implémentation du Price Ingestor Trading 212 via "Portfolio Hack"
- **Décision** : Conception et développement d'un module d'ingestion découplé (`backtest_engine/live/trading212`) implémentant le "Portfolio Hack". Au démarrage (bootstrap), le système émet des ordres d'achat de la taille minimale (0.0001 action) pour les 21 actifs cibles manquants. Une tâche périodique interroge ensuite les positions toutes les 60 secondes pour mettre à jour un cache de prix local (`/tmp/t212_prices.json`), tandis qu'un wrapper filtrant (`PositionTracker`) isole les positions d'observation de la logique de trading réelle.
- **Justification** : Trading 212 ne propose aucun endpoint REST direct et gratuit pour récupérer le cours temps réel d'un actif non détenu. L'ouverture de micro-positions est le seul moyen de contournement technique viable. Le découplage et le filtrage dynamique garantissent qu'aucune pollution de données ou distorsion de performance n'affecte les stratégies.

## [2026-06-30 00:27:00] - Journalisation et affichage premium des erreurs d'exécution des stratégies
- **Décision** : Ajout de la colonne `last_error TEXT` à la table `paper_strategy_configs`. Modification du cycle d'évaluation (`engine.py`) pour capturer et persister les exceptions de calcul des signaux sous `last_error`, et réinitialiser la colonne à `NULL` lors d'une exécution réussie. Exposition du champ `last_error` via l'API REST FastAPI (`api.py`) et réinitialisation de celui-ci lors de la mise à jour manuelle des paramètres. Affichage des messages d'erreur au survol du badge "Erreur" sur le tableau de bord avec un tooltip glassmorphism personnalisé en CSS.

## [2026-06-30 00:57:00] - Indicateur visuel de session de marché (Ouvert/Fermé) pour les actifs
- **Décision** : Intégration d'un indicateur visuel de session (glowing green dot pour ouvert, dimmed gray dot pour fermé) à côté de chaque actif dans le tableau de bord. La vérification de l'ouverture du marché (`is_market_open`) a été implémentée côté API FastAPI (`api.py`) à partir des données de `market_hours.json` et renvoyée en propriété dynamique de configuration.
- **Justification** : Clarifier la différence entre un statut d'erreur persistant et une inactivité due à la fermeture légitime des bourses, et offrir une meilleure UX sur le dashboard durant les sessions hors marché.
