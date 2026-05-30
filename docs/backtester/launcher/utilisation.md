# Piloter son environnement avec le Launcher

**TL;DR** : Gère l'intégralité de tes processus de backtesting locaux avec une seule commande. Démarre, arrête, redémarre ou vérifie l'état de santé de ton serveur et de ton worker en tâche de fond.

Tu as configuré tes lanceurs et tu es prêt à travailler. Mais comment vérifier que tes deux services (FastAPI et le worker SQLite) tournent correctement sans polluer ton écran de logs verbeuses ? Comment arrêter proprement tout ce beau monde en fin de journée sans risquer de corrompre ta base de données SQLite partagée ?

Le script `start_backtest_engine.sh` te fournit une interface de contrôle complète et intuitive en ligne de commande.

---

## Les commandes de pilotage rapide

Toutes les actions s'exécutent depuis ton terminal à la racine de ton projet.

### 1. Démarrer tout le système (Comportement par défaut)
Pour lancer le serveur web et le worker de calcul en une seule fois :

```bash
./start_backtest_engine.sh
# ou explicitement
./start_backtest_engine.sh start
```

### 2. Arrêter proprement les services
Pour couper tous les processus en tâche de fond de manière propre et libérer ton processeur :

```bash
./start_backtest_engine.sh stop
```

### 3. Diagnostiquer l'état de santé
Pour savoir si tes serveurs sont en ligne et voir leurs identifiants système (PID) :

```bash
./start_backtest_engine.sh status
```

### 4. Tout redémarrer d'un coup
Pratique si tu viens d'effectuer des modifications de code ou de configuration :

```bash
./start_backtest_engine.sh restart
```

---

## Comment fonctionne la surveillance en tâche de fond ?

Lorsque tu exécutes `./start_backtest_engine.sh start`, l'orchestrateur suit un protocole très précis :

1. **Le nettoyage initial** : Il vérifie si le port `8765` est encombré et arrête tout processus gênant.
2. **Le démarrage du Serveur** : Il lance l'API web en arrière-plan et attend qu'elle réponde positivement.
3. **Le démarrage du Worker** : Il active le processus de calcul qui va écouter les tâches d'optimisation SQLite en attente.
4. **La surveillance continue** : Le script ne s'arrête pas là. Il effectue une ronde toutes les 60 secondes pour vérifier la santé de tes processus. Si le système d'exploitation a tué ton worker (par exemple, pour manque de mémoire vive), le superviseur s'en rend compte et relance le service automatiquement pour ne pas bloquer tes calculs.

---

## Les adresses d'accès rapide

Une fois le démarrage confirmé par le statut, tu peux ouvrir ton navigateur web pour accéder à tes outils :

- **L'interface d'accueil** : `http://127.0.0.1:8765/` (pour configurer tes grilles d'optimisation et visualiser tes graphiques de trades).
- **La documentation de l'API REST** : `http://127.0.0.1:8765/docs` (pour voir tous les endpoints exposés par notre serveur web).
