# Récupérer des données de marché gratuites avec SheetsFinance

**TL;DR** : Un collecteur automatique basé sur Google Apps Script qui extrait des barres de 5 minutes, les événements de split et les taux de change depuis SheetsFinance, puis dépose le tout sous forme de fichiers CSV propres sur Google Drive.

Tu as besoin de données historiques de qualité pour alimenter tes backtests locaux. Mais si tu as déjà cherché des flux d'historique intraday de 5 minutes pour des actions américaines ou européennes, tu as dû faire face à un problème douloureux : le coût. Les flux professionnels (comme Bloomberg, Reuters ou même des abonnements spécialisés) coûtent des centaines d'euros par mois.

Ce module résout ce problème en tirant parti de **SheetsFinance** via Google Sheets. C'est une solution entièrement gratuite qui permet d'extraire des historiques boursiers de manière extrêmement fiable.

Puisque faire tourner des requêtes lentes sur un tableur est inefficace pour ton code Python local, ce **Collector** déporte tout le travail de collecte dans le cloud de Google via Apps Script. Il extrait les données en tâche de fond et les dépose directement sur ton Google Drive sous forme de fichiers CSV.

---

## Les guides du collecteur

Pour installer, configurer et exploiter ton flux de données gratuites :

- **[Installer le collecteur](./installation.md)** : Crée ton classeur Google Sheets, lie le script Apps Script et initialise l'environnement en un clic.
- **[Configurer tes listes (Watchlist)](./configuration.md)** : Ajoute tes actions préférées, définis ta fenêtre de dates historiques et ajuste les paramètres de vitesse pour ne pas saturer tes quotas Google.
- **[Lancer et automatiser la collecte](./utilisation.md)** : Découvre comment lancer le mode automatique qui enchaîne les tâches et gère les reprises après coupure grâce aux checkpoints.
- **[Résoudre les bugs de collecte](./troubleshooting.md)** : Erreurs d'API, limites de quota Google ou problèmes de détection de devises ; les solutions simples et directes.

---

## Sa place dans notre écosystème

Le collecteur est le point d'entrée de tout notre pipeline. 

Il dépose des fichiers CSV bruts dans ton dossier Google Drive. Une fois synchronisés en local sur ta machine, ces fichiers bruts sont pris en charge par l'outil **[build-canonical](../backtest-engine/canonical-datasets.md)** du moteur de backtest. Celui-ci s'occupe de corriger les décimales, d'ajuster les splits d'actions historiques et de convertir le tout au format Parquet pour que tes simulations se lancent en quelques millisecondes.
