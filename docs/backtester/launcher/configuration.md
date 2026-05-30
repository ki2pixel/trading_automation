# Configurer les paramètres du Launcher

**TL;DR** : Personnalise l'adresse IP, le port d'écoute et les répertoires d'écriture des rapports directement au début du fichier `start_backtest_engine.sh`.

Tu veux changer le port d'écoute du serveur pour ne pas entrer en conflit avec une autre application locale (comme un serveur de base de données ou un autre robot de trading) ? Ou tu veux héberger l'API sur une adresse IP spécifique de ton réseau local ?

Tous ces réglages système sont regroupés de manière lisible au tout début de notre script de démarrage.

---

## Les variables système disponibles

Pour modifier la configuration, ouvre le fichier `start_backtest_engine.sh` avec ton éditeur de texte préféré. Tu trouveras ces lignes au sommet du fichier :

```bash
HOST="127.0.0.1"           # L'adresse d'écoute locale (par défaut, localhost)
PORT="8765"                # Le port réseau de ton serveur web
REPO_ROOT="."              # Le chemin d'accès à la racine de ton projet
OUTPUT_DIR="reports/local_optimizer"  # Le répertoire où le worker écrit les rapports
```

---

## Les garde-fous intégrés au démarrage

Lorsque tu lances le script, il effectue une série de vérifications de sécurité automatiques pour s'assurer que ton environnement est sain :

- **Libération du port** : Si le port `8765` est déjà occupé par un ancien processus fantôme, le script le détecte et force son arrêt pour éviter que le démarrage du nouveau serveur n'échoue.
- **Importation Python** : Le script tente d'importer le module `backtest_engine` avant de faire quoi que ce soit. Si ton package est mal installé ou si tu n'es pas dans le bon dossier, il t'affiche un message d'explication clair au lieu de planter silencieusement.
- **Droits d'accès (chmod)** : Lors du tout premier lancement, le script s'assure d'avoir les droits de s'exécuter sur ton système Linux en ajustant ses permissions si nécessaire.
