# Visualiser tes trades sur un graphique interactif

**TL;DR** : Un visualiseur local basé sur KLineChart qui affiche tes bougies OHLCV, tes courbes d'indicateurs et tes flèches de transaction. C'est l'outil parfait pour auditer visuellement ta stratégie en un clic.

Ta simulation vient de se terminer. Les chiffres bruts dans ton fichier `metrics.json` affichent un taux de réussite flatteur de 65%. Pourtant, tu as un doute persistant : est-ce que tes ordres d'achat et de vente s'exécutent réellement au bon moment ? Est-ce que le signal ne s'est pas déclenché avec une bougie de retard à cause d'une erreur d'indexation dans ton code Python ? 

Essayer de vérifier cela en croisant une liste de dates dans un fichier CSV avec un graphique TradingView externe est un travail de titan. 

Le **Backtest Viewer** résout ce problème. Il te propose une réplique locale de l'interface TradingView, directement connectée à ton moteur de simulation.

---

## Ce que tu vas voir sur ton écran

Le visualiseur s'appuie sur la bibliothèque haute performance **KLineChart** pour t'offrir un rendu fluide, même avec des dizaines de milliers de bougies historiques.

- **Le graphique des prix** : Des chandeliers japonais classiques (OHLCV) avec un zoom et un déplacement (pan) d'une fluidité parfaite.
- **Les indicateurs superposés** : Le graphique affiche en direct les indicateurs calculés par ta stratégie (comme tes moyennes HMA rapide et lente, ou tes bandes de volatilité).
- **Les flèches d'exécution** : Des marqueurs visuels clairs (flèches colorées) sont placés précisément sur la bougie exacte où le broker a exécuté ton ordre. Tu repères instantanément les entrées et les sorties de position.
- **Le panneau de contrôle interactif** : Tu n'as pas besoin de retourner dans ton terminal pour modifier un paramètre. Un panneau latéral te permet de changer le symbole, d'ajuster la sensibilité de ton indicateur et de relancer la simulation. Le graphique se met à jour instantanément sous tes yeux.

---

## Comment lancer le visualiseur en 2 minutes ?

Puisque le visualiseur est intégré directement dans notre serveur web local, tu n'as besoin que d'une seule commande pour y accéder.

### 1. Démarre le serveur API Web
Dans ton terminal, lance le service web d'écoute :

```bash
python3 -m backtest_engine serve --host 127.0.0.1 --port 8765
```

### 2. Ouvre ton navigateur
Rends-toi sur l'adresse locale suivante :

```text
http://127.0.0.1:8765/
```

### 3. Ajuste et observe
Dans l'interface web, sélectionne l'onglet du visualiseur. Choisis ton action (ex : `GMAB`), ajuste les dates et clique sur lancer. Le backend recalcule la stratégie à la volée en tâche de fond et met à jour le graphique KLineChart avec tes indicateurs et tes signaux. Tu peux maintenant inspecter chaque trade visuellement pour valider la logique de ton code.
