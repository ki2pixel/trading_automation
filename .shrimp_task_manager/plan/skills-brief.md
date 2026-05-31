# MISSION : CONSTITUTION DE L'ARSENAL DE SPÉCIALISATIONS MÉTIERS (SKILLS) POUR LE TRADING AUTOMATISÉ

L'objectif de cette mission est de concevoir, structurer et implémenter une suite de 7 compétences métiers hautement spécialisées (`SKILL.md`) sous `.agents/skills/` afin de doter les agents IA d'un niveau d'expertise exceptionnel et opérationnel pour le projet Trading Automation v2.

## Spécialisations Métiers à Créer
Chaque spécialisation doit être implémentée sous forme de dossier `.agents/skills/<skill-name>/` contenant un fichier `SKILL.md` complet (contenant YAML Frontmatter, patterns de code de référence, pièges à éviter et standards d'ingénierie propres à la discipline).

1. **`backtesting-engine` (Optimisation du Moteur de Backtest)**
   - *Rôle* : Spécialiste de la vectorisation de données et de la simulation de performance historique.
   - *Contenu clé* : Utilisation optimisée de Numpy/Pandas (éviter les boucles `for` sur les lignes), gestion des glissements (slippage) et frais de transaction, calcul de métriques complexes (Ratio de Sharpe, Sortino, Max Drawdown en temps et amplitude), simulation orientée événements (event-driven) vs vectorisée.

2. **`database-supabase-postgres` (Séries Temporelles & Stockage de Masse)**
   - *Rôle* : Expert en optimisation de bases de données financières relationnelles et temporelles.
   - *Contenu clé* : Conception de schémas de séries temporelles (`ticks`, `candles`), stratégies d'indexation PostgreSQL (B-Tree, BRIN), requêtes brutes optimisées via Supabase, partitionnement de tables massives, et gestion de caches de données historiques.

3. **`risk-money-management` (Gestion du Risque & Allocation)**
   - *Rôle* : Gardien du capital et contrôleur de l'exposition globale du portefeuille.
   - *Contenu clé* : Formules de dimensionnement de positions (Critère de Kelly, fraction fixe), logique stricte de Stop-Loss et Take-Profit dynamique (Trailing Stops), gestion de l'exposition corrélée, coupe-circuits automatiques et modélisation de la ruine.

4. **`market-data-ingestion` (Flux de Données & Ingestion Résiliente)**
   - *Rôle* : Spécialiste de la collecte et de la normalisation des flux de marché en temps réel et différé.
   - *Contenu clé* : Gestion des connexions persistantes (WebSockets) et REST APIs avec Rate Limiting, imputation robuste des bougies ou ticks manquants, déduplication, nettoyage des anomalies (outliers) de prix, et reconstruction de carnets d'ordres.

5. **`indicator-generation` (Signaux Alphas & Indicateurs Techniques)**
   - *Rôle* : Créateur de features mathématiques et d'indicateurs de signaux d'achat/vente.
   - *Contenu clé* : Utilisation performante de TA-Lib / pandas_ta, création d'indicateurs personnalisés (stateless & stateful), engineering de features pour le Machine Learning, et classification de régimes de marché (tendance vs range).

6. **`execution-order-routing` (Routage d'Ordres & Exécution Live)**
   - *Rôle* : Expert de l'interaction bas niveau avec les courtiers et du cycle de vie des ordres réels.
   - *Contenu clé* : Routage résilient d'ordres multi-courtiers (Trading 212, Interactive Brokers), automate à états finis pour le cycle de vie d'un ordre (Submitted, Filled, Canceled, Rejected), tolérance aux pannes réseau, gestion du slippage à l'exécution et synchronisation de la balance du compte en temps réel.

7. **`performance-reporting` (Reporting de Performance & Visuels)**
   - *Rôle* : Générateur d'analyses visuelles et d'attributions de performance pour le trading.
   - *Contenu clé* : Génération de graphiques interactifs (Plotly, intégration KLineChart), PnL attribution, rapports de performance complets exportables (JSON, CSV), et détection des dérives de stratégie (Alpha decay).

## Dépendances
- `market-data-ingestion` et `database-supabase-postgres` doivent être créés en premier.
- Suivis par `backtesting-engine`, `indicator-generation` et `risk-money-management`.
- Enfin, `execution-order-routing` et `performance-reporting`.
