# Le Moteur de Backtest local (Backtest Engine)

**TL;DR** : Le cerveau de simulation locale. Il lit tes datasets canoniques, simule le comportement exact d'un broker avec tes stratégies Pine Script converties, et te sort des rapports de performance ultra-complets.

Quand tu crées ou modifies une stratégie de trading sur TradingView, tester plusieurs combinaisons de paramètres prend un temps infini : tu dois manuellement changer les chiffres dans l'interface, attendre que le graphique charge, et copier-coller les métriques dans un tableur Excel. C'est lent, rébarbatif, et sujet à des erreurs de saisie.

Le **Backtest Engine** est conçu pour casser ce goulot d'étranglement. En exécutant tes stratégies directement en Python sur ta machine, il te permet de lancer des simulations unitaires en quelques millisecondes et des optimisations de milliers de combinaisons en tâche de fond pendant que tu fais autre chose.

---

## Les guides essentiels

Voici comment naviguer dans le moteur selon ce que tu cherches à accomplir :

### 1. Démarrer et configurer
- **[Zéro à un backtest (Quickstart)](./quickstart.md)** : Apprends à valider tes fichiers de données et à lancer ta toute première simulation en ligne de commande.
- **[Philosophie de la configuration](./configuration.md)** : Découvre comment nous gérons les paramètres de stratégie et l'héritage des frais globaux (commissions, slippage, règles de risque) pour éviter la duplication.
- **[Lancer un backtest unitaire](./runner.md)** : Maîtrise la commande `run`, configure le broker et gère les timeframes personnalisés.

### 2. Pousser la stratégie à ses limites
- **[Optimiser les paramètres](./optimization.md)** : Utilise la recherche exhaustive (Grid Search) ou l'intelligence bayésienne (Optuna) pour trouver automatiquement les meilleurs réglages pour tes indicateurs.
- **[Éviter le surapprentissage (Walk-Forward WFO)](./walk-forward.md)** : Ne te fais pas piéger par des paramètres "trop parfaits" sur le passé. Applique des fenêtres glissantes et calcule le score de déflation de Sharpe (PBO/DSR).
- **[Gérer les longs calculs (Job Store)](./job-store.md)** : Comment lancer des optimisations qui durent des heures sans craindre les crashs ou les coupures de courant grâce à la persistence SQLite.

### 3. Analyser et valider
- **[Visualiser les trades sur graphique](./viewer.md)** : Ouvre l'interface interactive KlineChart pour inspecter visuellement chaque entrée et sortie et valider ton code Pine.
- **[Analyser tout ton portefeuille (Global Analysis)](./global-analysis.md)** : Synthétise les résultats d'optimisation de dizaines d'actions en un seul rapport global interactif.
- **[Comment sont préparées les données (Datasets canoniques)](./canonical-datasets.md)** : Rapproche-toi des coulisses de la commande `build-canonical` pour comprendre le nettoyage des splits d'actions.
- **[Mesurer la vitesse (Performance)](./performance.md)** : Découvre les optimisations internes (mise en cache des indicateurs, arrêt précoce) qui permettent de gagner un temps précieux.

### 4. Références et résolution de problèmes
- **[Dictionnaire complet des commandes CLI](./cli-reference.md)** : Une feuille de triche de toutes les commandes et options disponibles dans le terminal.
- **[Roadmap de conversion multi-devises](./currency-conversion-roadmap.md)** : Notre plan technique pour gérer proprement les transactions d'actifs dans des devises différentes de ton capital de base.
- **[Dépannage rapide (Troubleshooting)](./troubleshooting.md)** : "J'ai une erreur de port déjà utilisé ou de module manquant", la solution en deux lignes.

---

## Place dans le pipeline

Le moteur de backtest intervient juste après la phase de préparation des données. Il attend des fichiers Parquet propres et ajustés issus de **[build-canonical](./canonical-datasets.md)**. Une fois sa simulation terminée, il génère des rapports dans le dossier `reports/` (sous forme de JSON, CSV, ou pages HTML interactives).
