# Raccourcis graphiques pour ton bureau Linux

**TL;DR** : Utilise les raccourcis `.desktop` fournis pour lancer ton serveur de backtest, surveiller son statut ou tout arrêter d'un simple double-clic, sans jamais ouvrir de terminal manuel.

Tu adores utiliser le backtester, mais tu en as assez de devoir ouvrir ton terminal et naviguer dans tes dossiers à chaque fois que tu veux l'allumer. Tu aimerais pouvoir le lancer aussi simplement que n'importe quelle autre application de ta machine : d'un simple double-clic sur ton bureau.

Pour t'offrir ce confort sous Linux, nous avons préparé trois fichiers de configuration `.desktop` à la racine de ton projet.

---

## Les trois lanceurs à ta disposition

### 1. Démarrer le système (`BacktestEngine.desktop`)
Ce raccourci lance l'orchestrateur. Il s'occupe de démarrer le serveur FastAPI, d'activer le worker de calcul en arrière-plan, et d'ouvrir une fenêtre de surveillance pour te montrer que tout s'est bien déroulé.

### 2. Consulter l'état (`BacktestEngine_Status.desktop`)
Un doute sur l'activité de tes workers ? Double-clique sur ce raccourci pour ouvrir un moniteur système rapide dans ton terminal. Il te montrera les identifiants des processus (PID) actifs et te confirmera si l'API répond.

### 3. Tout éteindre (`BacktestEngine_Stop.desktop`)
Pour libérer ton processeur et fermer proprement tous les services avant d'éteindre ton ordinateur, ce raccourci envoie un signal d'arrêt propre à tous tes processus en cours.

---

## Comment les installer sur ton système ?

Pour intégrer ces lanceurs à ton environnement graphique Linux, tu as deux choix.

### Option A : Les placer sur ton bureau
Pour créer des raccourcis directement accessibles sur ton écran d'accueil :

```bash
cp BacktestEngine*.desktop ~/Bureau/
```

*(Note : selon ta distribution Linux, tu devras peut-être faire un clic droit sur les fichiers du bureau et sélectionner "Autoriser le lancement".)*

### Option B : Les ajouter à ton menu d'applications (Recommandé)
Pour que le backtester apparaisse dans ton menu de démarrage (comme Firefox ou ton éditeur de code) sous la catégorie "Développement" :

```bash
cp BacktestEngine*.desktop ~/.local/share/applications/
```

Une fois cette copie effectuée, tu pourras chercher "Backtest Engine" directement dans la barre de recherche d'applications de ton système pour le lancer instantanément.
