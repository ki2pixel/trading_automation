# Backtester : Guide de démarrage

**TL;DR** : Un pipeline local complet pour collecter tes données, nettoyer tes datasets et exécuter tes backtests et optimisations de stratégies Pine Script sans dépendre des limites et du coût de TradingView.

Tu en as marre des limitations de TradingView ? Payer un abonnement mensuel coûteux pour te retrouver bloqué par la limite des 10 000 ou 20 000 barres historiques, ou par l'impossibilité d'automatiser des optimisations complexes sur des centaines de paramètres ?

Ce projet a été conçu exactement pour résoudre ce problème. Il te permet de récupérer des données historiques gratuitement, de générer des fichiers de données optimisés et d'exécuter des simulations ultra-précises en local sur ta machine, à une fraction de seconde par test.

---

## Comment ça marche ?

Le pipeline est divisé en quatre blocs simples et autonomes. Pour comprendre comment les données circulent entre ces composants, jette un œil au guide de l'**[Architecture globale](./architecture.md)**.

### 1. Collector
La collecte commence dans le cloud. Ce module est un script Google Apps Script qui extrait des barres de 5 minutes, les splits d'actions et les taux de change directement depuis SheetsFinance. Les fichiers sont déposés sous forme de CSV bruts sur ton Google Drive pour ne pas surcharger tes feuilles de calcul.
- [Installer le collecteur](./collector/installation.md)
- [Configurer les variables](./collector/configuration.md)
- [Lancer et exploiter la collecte](./collector/utilisation.md)
- [Que faire en cas de bug de collecte ?](./collector/troubleshooting.md)

### 2. Backtest Engine (Le Cœur)
C'est le moteur Python local. Il prend tes fichiers CSV bruts, les convertit en datasets Parquet ultra-rapides à charger, exécute tes stratégies (traduites de Pine Script), simule les frais de courtage et le slippage, puis génère des rapports de performance exhaustifs.
- [Démarrage rapide (Zéro à un backtest)](./backtest-engine/quickstart.md)
- [Comprendre et modifier la configuration](./backtest-engine/configuration.md)
- [Lancer un backtest unitaire](./backtest-engine/runner.md)
- [Optimiser les paramètres d'une stratégie](./backtest-engine/optimization.md)
- [Analyser les performances de plusieurs symboles](./backtest-engine/global-analysis.md)
- [Tester la robustesse avec le Walk-Forward (WFO)](./backtest-engine/walk-forward.md)
- [Gérer les optimisations longues avec le Job Store](./backtest-engine/job-store.md)
- [Visualiser tes trades sur un graphique interactif](./backtest-engine/viewer.md)
- [Mesurer les performances du moteur](./backtest-engine/performance.md)
- [Comment sont construits les datasets canoniques](./backtest-engine/canonical-datasets.md)
- [Référence complète des commandes CLI](./backtest-engine/cli-reference.md)
- [Roadmap de conversion multi-devises](./backtest-engine/currency-conversion-roadmap.md)
- [Guide de dépannage du moteur](./backtest-engine/troubleshooting.md)

### 3. VectorBT Integration (L'accélérateur)
Quand l'optimisation sur un CPU classique devient trop lente, le pont VectorBT prend le relais. Il utilise le calcul vectorisé pour tester des millions de combinaisons en quelques secondes. C'est l'outil parfait pour pré-filtrer des paramètres ou simuler des benchmarks aléatoires.
- [Quand utiliser VectorBT ? (Rapport d'audit)](./vectorbt/vectorbt_audit_report.md)
- [Comment exploiter le Bridge VectorBT](./vectorbt/README.md)
- [Valider tes données avec le Pre-Scan](./vectorbt/vectorbt_prescan.md)

### 4. Launcher
Parce que démarrer des serveurs FastAPI et des workers SQLite en ligne de commande à chaque fois est fastidieux, le Launcher fournit un script simple et des lanceurs d'application `.desktop` pour Linux. Tu lances ton serveur de backtest d'un double-clic.
- [Démarrer le serveur et le worker](./launcher/utilisation.md)
- [Configurer les variables du launcher](./launcher/configuration.md)
- [Créer des raccourcis graphiques sous Linux](./launcher/desktop-launchers.md)

---

## Où dois-je aller maintenant ?

Voici un raccourci direct selon ton besoin immédiat :

- **"Je veux juste faire tourner mon tout premier test sur GMAB"** : Rends-toi sur le [Quickstart du moteur](./backtest-engine/quickstart.md).
- **"Je dois récupérer de nouvelles données historiques d'action"** : Configure le collecteur dans [Collector / Configuration](./collector/configuration.md).
- **"Mon optimisation plante ou prend trop de temps"** : Découvre comment le [Job Store](./backtest-engine/job-store.md) gère les reprises sur panne ou utilise le pont [VectorBT](./vectorbt/README.md) pour aller 100 fois plus vite.
- **"Je veux vérifier la logique exacte d'une commande CLI"** : Consulte la [Référence CLI](./backtest-engine/cli-reference.md).
