# Simplifier la gestion des processus locaux avec le Launcher

**TL;DR** : Un script de contrôle unifié `start_backtest_engine.sh` et des raccourcis graphiques sous Linux pour démarrer, surveiller et arrêter proprement tes serveurs API et tes workers locaux en une seule action.

Pour faire tourner ton environnement de backtesting en local, tu as besoin de deux processus Python distincts qui tournent en même temps en tâche de fond :
1. **Le serveur d'API Web (FastAPI)** : Pour recevoir les demandes de backtest et afficher l'interface graphique.
2. **Le worker de tâche de fond (SQLite)** : Pour exécuter les calculs d'optimisation lourds sur ton processeur.

Ouvrir deux onglets de terminaux différents à chaque fois, taper de longues commandes à la main, surveiller si l'un d'eux n'a pas planté par manque de mémoire, et devoir les tuer proprement un par un avant d'éteindre ta machine... c'est un enfer de gestion de processus.

Le **Launcher** résout ce problème. Il encapsule ces deux services dans un script unique qui s'occupe de les orchestrer à ta place.

---

## Les guides du lanceur

Découvre comment configurer et exploiter tes lanceurs locaux :

- **[Utiliser le script en ligne de commande](./utilisation.md)** : Apprends les commandes d'arrêt, de redémarrage et de diagnostic pour piloter ton environnement.
- **[Ajuster la configuration](./configuration.md)** : Personnalise les ports d'écoute, l'adresse locale et les répertoires de stockage des rapports de simulation.
- **[Installer des raccourcis graphiques sous Linux](./desktop-launchers.md)** : Crée de vrais raccourcis d'applications `.desktop` sur ton bureau pour démarrer le backtester d'un simple double-clic de souris.
