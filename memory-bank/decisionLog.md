# Journal des Décisions

## [2026-07-04 00:38:00] - Phase 5 Hygiène & Dette Technique Backend validée (Dépendances, Docker, Nettoyage)
- **Décision** : Partitionnement des dépendances Python du projet en 3 fichiers (`requirements-base.txt`, `requirements-backtest.txt`, `requirements-live.txt`), suppression de `requirements-backtest-engine.txt`, et build Docker de production allégé en copiant et installant uniquement le live. Nettoyage de la dette technique via la suppression automatisée de 332 imports inutilisés, l'audit du nommage (snake_case), et l'enrichissement des annotations de types statiques sur `connection.py` et `signal_executor.py` (API publique déclarée via `__all__`).
- **Justification** : Réduire le poids de l'image Docker de production sur Render, clarifier la structure des dépendances par environnement pour les développeurs, accélérer les phases de build/CI, améliorer la maintenabilité du code par le typage statique strict et éliminer le code mort (imports inutilisés).

## [2026-07-04 00:15:00] - Phase 4 Robustesse Backend validée (Paper Trading & Optimizer)
- **Décision** : Sécurisation du backend de trading automation via 3 piliers :
  1. **Exceptions Ciblées** : Remplacement des captures d'exceptions génériques (`except Exception`) par des captures typées spécifiques aux couches (DB : `psycopg2.Error`/`asyncpg.PostgresError`, Réseau : `urllib.error`/`requests.exceptions.RequestException`, Validation : `ValueError`/`KeyError`). Utilisation systématique de `logger.exception` pour conserver les stack traces. Création d'exceptions custom `SignalExecutionError` et `PortfolioUpdateError` pour les échecs d'affaires.
  2. **Shielding en Production** : Implémentation du helper `safe_error_response` et configuration de gestionnaires d'exception globaux FastAPI. En production, les erreurs non gérées retournent un message générique masquant les détails techniques et fournissant un UUID de corrélation unique. La trace complète est logguée côté serveur associée à cet UUID. Les détails détaillés restent visibles en mode développement/DEBUG.
  3. **Timeouts Explicites** : Centralisation de `NETWORK_TIMEOUT_DEFAULT = 10.0` dans `utils.py` et application stricte sur tous les appels réseau (Bybit, Trading 212, warm-up) pour prévenir les pannes et blocages silencieux.
- **Justification** : Éliminer la fuite d'informations système et de structure de base de données en production, structurer la gestion d'erreurs pour une meilleure maintenabilité, et interdire les timeouts infinis par défaut sur les requêtes réseau externes.

## [2026-07-03 22:50:00] - Phase 1 Sécurité Critique validée (Paper Trading Backend)
- **Décision** : Implémentation des 4 mesures de sécurité critiques de l'audit pour le backend Paper Trading FastAPI :
  1. **Séparation HMAC** : Utilisation d'une variable d'environnement `HMAC_SECRET` dédiée pour la signature de session (séparée du mot de passe utilisateur, auto-générée en dev/test, requise en prod).
  2. **Protection CSRF** : Implémentation du middleware `CSRFMiddleware` (Double Submit Cookie) vérifiant le header `X-CSRFToken` par rapport au cookie `csrftoken` non HttpOnly sur les requêtes mutantes. Intégration côté client via un intercepteur fetch dans `app.js`.
  3. **Validation Pydantic** : Modèle `IndicatorParamsModel` validant `indicator_params` via `model_validator` pour rejeter les injections (structures imbriquées de type listes/dict) tout en autorisant les clés dynamiques via `extra='allow'`.
  4. **En-têtes CORS/CSP** : Configuration des en-têtes de sécurité de production via `CORSMiddleware` (whitelist stricte, `X-CSRFToken` et `Content-Type` autorisés) et `SecurityHeadersMiddleware` (CSP, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Strict-Transport-Security`).
- **Justification** : Éliminer les risques critiques d'invalidation de mot de passe comme clé HMAC, d'attaques CSRF sur les endpoints mutants d'administration du Paper Trading, de contournement ou d'injections malveillantes via les paramètres de stratégies, et d'expositions inter-origines non sécurisées.

## [2026-07-02 23:15:00] - Conception de la Passerelle de Conversion Réelle Crypto-Fiat (Bybit Live)
- **Décision** : Analyse des vecteurs de conversion et des risques associés à la transition en environnement réel Bybit (UTA, MiCA) suite au rapport `Analyse-Conversion-API-Bybit-EUR.md` :
  1. **Choix du Routage** : Option A (API Spot `EURUSDT` avec `marketUnit="quoteCoin"`) retenue au lieu de l'Option B (Convert API OTC) pour les faibles montants, en raison de frais explicites inférieurs (0,10% - 0,20% Taker vs 0,15% - 0,40% spread OTC) et d'une exécution déterministe.
  2. **Buffer de Rétention** : Utilisation d'un patron d'accumulateur (Buffer de Rétention) avec un seuil de déclenchement à 15 USDT pour respecter le seuil minimal de commande Spot de Bybit (1-5 USDT) et éviter les rejets.
  3. **Contrôle de Marge UTA (Haircut Loss)** : Mise en place obligatoire d'un simulateur de marge pré-trade interrogeant `GET /v5/account/info` avant conversion, afin de s'assurer que le retrait de collatéral (l'EUR ayant un ratio de collatéral de 0%) ne pousse pas le taux de marge de maintien (MMR) au-dessus de 100% (seuil de liquidation).
  4. **Routage MiCA (Juridiction EEE)** : Migration recommandée des stratégies vers une devise de base USDC (stablecoin conforme MiCA avec ratio collatéral de 100% dans l'UTA) pour éliminer le besoin de "Double-Hop Routing" (USDT -> USDC -> EUR) et réduire les frais cumulés.
- **Justification** : Prévenir les rejets d'ordres par le moteur de matching de Bybit, prémunir le compte UTA contre les liquidations accidentelles induites par la perte de collatéral marge, et respecter le cadre réglementaire européen MiCA tout en minimisant les frais de transaction.

## [2026-07-02 22:15:00] - Enrichissement et Stabilisation du Dashboard Paper Trading
- **Décision** : Enrichissement de l'interface de monitoring Paper Trading avec de nouvelles fonctionnalités et correction de la résilience de l'ingesteur :
  1. Intégration de `Lightweight Charts` v4.1.3 avec une échelle double Y (NAV sur l'axe gauche, prix des bougies sur l'axe droit) pour superposer la courbe de stratégie vs Buy & Hold sans distorsion.
  2. Stream en temps réel des logs du moteur de Paper Trading via FastAPI SSE (Server-Sent Events) en redirigeant dynamiquement les sorties standard (prints) vers un logger Python circulaire.
  3. Ajout de contrôles interactifs : interrupteurs d'activation/désactivation de stratégie et bouton de panique (Close All) avec double confirmation modale.
  4. Déplacement de l'initialisation des ingesteurs de prix de `run_ingestor.py` directement dans le context manager `lifespan` de FastAPI pour s'assurer que les workers d'Uvicorn démarrent toujours les tâches d'ingestion asynchrones en arrière-plan.
- **Justification** : Offrir un monitoring temps réel robuste des métriques d'exécution et de performance (calculées en FIFO) et assurer la continuité du flux de données de marché en environnement de production (Render).

## [2026-07-02 20:21:00] - Alignement et Mise à jour des Standards de Code (Trading Automation)
- **Décision** : Mise à jour de `.agents/rules/codingstandards.md` pour refléter la réalité technique de la base de code :
  1. Ingesteur de prix Bybit en mode public-only sur Render (sans clés d'API requises).
  2. Simulation des frais de transaction Bybit Spot à 0.1000% (non-VIP) et Trading 212 à 0.0000% de frais dans le Paper Trading.
  3. Rôle de `shm_allocators.py` dans l'allocation POSIX SHM pour réduire la complexité d'Optuna.
  4. Correction de la confusion sur les métriques : NVO, NVS et AMS.MC sont des actifs/tickers de référence WFA, tandis que PBO et DSR sont les véritables métriques de robustesse.
  5. Organisation plate des données Parquet dans `storage/processed/market_data_{timeframe}m/{symbol}.parquet`.
- **Justification** : Aligner précisément la documentation d'architecture de référence avec le codebase pour éviter la dérive de documentation et guider correctement les futurs développements.

> Ce document trace les décisions techniques majeures et leur justification.

## [2026-07-02 15:00:00] - Architecture Dual-Portefeuille et Intégration Binance API
- **Décision** : Séparation stricte des portefeuilles et de la gestion de balance entre les actions (gérées via Trading212 en EUR) et les crypto-actifs (gérées via Binance en USDT) au sein du moteur de Paper Trading. Migration des tables SQL `trading212_prices` $\rightarrow$ `live_prices` et `trading212_candles_1m` $\rightarrow$ `live_candles_1m` pour unifier les données de marché. Intégration d'un routeur dynamique dans le moteur de paper trading basé sur le suffixe des actifs (ex: `*.usdt` redirigé vers l'écosystème Binance).
- **Justification** : Trading212 interdit le trading algorithmique sur crypto-actifs et n'offre pas de vente à d'API Spot ouverte pour les cryptos. Binance fournit une API Spot Testnet idéale et un écosystème 24/7 complet. La séparation évite d'avoir une surcharge arbitraire de Kelly weight pour les cryptos, préserve la logique financière spécifique à chaque écosystème, et permet une modélisation propre sans pollution mutuelle.

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

## [2026-06-30 11:47:00] - Inclusion du dossier pine_scripts_convert_to_python dans l'image Docker
- **Décision** : Ajout de la ligne `COPY pine_scripts_convert_to_python/ /app/pine_scripts_convert_to_python/` dans le `Dockerfile`.
- **Justification** : Résoudre les exceptions `FileNotFoundError` (crashes d'importation dynamique de modules de stratégie) lors de l'évaluation des stratégies de paper trading en production dans les conteneurs Docker.

## [2026-06-30 11:55:00] - Résolution des permissions pour les stratégies dans Docker
- **Décision** : Ajout de la commande `RUN chmod -R 755 /app` dans le `Dockerfile`.
- **Justification** : Prévenir les erreurs `FileNotFoundError` causées par les restrictions de droits de traversée de répertoires (`x`) pour les utilisateurs non-root exécutant le conteneur dans le cloud (Render).
