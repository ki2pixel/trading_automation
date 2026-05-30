# Choix d'architecture : Pourquoi ce pipeline ?

**TL;DR** : Une séparation stricte entre la collecte cloud (Google Sheets), le nettoyage local (Python/Parquet) et le moteur de simulation. **Cette isolation garantit des backtests fiables sans goulot d'étranglement.**

Quand on construit un système de backtest, la tentation est grande de tout coder dans un seul gros script : un outil unique qui télécharge les données, calcule les indicateurs, passe les ordres fictifs et trace les graphiques. 

C'est une erreur classique. Très vite, on se heurte à plusieurs murs :
1. **Le problème de la source de données** : Les APIs gratuites de qualité sont rares, et coder des connecteurs vers des courtiers change sans arrêt.
2. **La corruption silencieuse** : Les données brutes contiennent toujours des anomalies (virgules mal placées, splits d'actions non ajustés) qui faussent complètement les résultats de simulation.
3. **La lenteur de calcul** : Lire des millions de lignes CSV à chaque backtest détruit les performances.

Voici comment notre architecture découpe ces problèmes pour les résoudre un par un.

---

## Le flux de données en un coup d'œil

Les composants ne communiquent pas en direct ; ils se transmettent des fichiers de données via des étapes bien définies.

```
SheetsFinance ( Données brutes chez Google )
      |
      v
+------------------------------------+
|       Collector (Apps Script)      |  <- Isole la collecte du code Python
|  Extraits de cours, splits, devises |
+------------------------------------+
      |
      v
Google Drive / Local (Fichiers CSV bruts)
      |
      v
+------------------------------------+
|      build-canonical (Python)      |  <- Répare et optimise les données une fois pour toutes
|  Ajustements, Parquet, filtres      |
+------------------------------------+
      |
      v
Dossier storage/processed/ (Fichiers Parquet ultra-rapides)
      |
      v
+------------------------------------+
|       Backtest Engine (Python)     |  <- Simule le trading sur des données propres
|  Exécution, commissions, rapports  |
+------------------------------------+
      |
      v
Dossier reports/ (CSV, HTML de visualisation)
```

---

## Pourquoi ce découpage ?

### 1. Collector : Pourquoi Apps Script et Google Drive ?
Le stockage et la mise à jour de données boursières de qualité professionnelle coûtent cher. Nous avons choisi d'utiliser **SheetsFinance** via Google Sheets car c'est une solution gratuite et extrêmement robuste pour récupérer l'historique des actions.

Cependant, faire tourner du code Python qui appelle directement des fonctions Google Sheets à chaque itération est d'une lenteur exaspérante. Le **Collector** résout ce problème en s'exécutant directement dans le cloud Google via Apps Script. Il extrait les données en tâche de fond, gère ses propres checkpoints pour ne jamais rater de données, et dépose le résultat sous forme de fichiers CSV sur Google Drive.

Ton code local n'a jamais besoin de parler à Google Sheets ; il a juste besoin de lire des fichiers CSV locaux synchronisés.

### 2. build-canonical : Le filtre indispensable
Ne lance jamais un backtest directement sur des données brutes de collecte. C'est le meilleur moyen de se retrouver avec des trades aberrants à cause d'un split d'actions non pris en compte (une action qui passe de 100$ à 50$ suite à un split de 2:1 ressemble à une chute de 50% pour ton algorithme, alors que sa valeur réelle n'a pas bougé).

L'outil **`build-canonical`** est notre garde-fou. Il s'exécute en local et fait un travail de nettoyage minutieux :
- Il convertit les formats numériques (virgules décimales européennes en points).
- Il détecte et répare les anomalies OHLC évidentes.
- Il applique de manière rétroactive les splits d'actions historiques pour que la courbe des prix soit continue et réaliste.
- Il convertit les fichiers volumineux au format **Parquet**.

Le format Parquet est un choix technique clé : il se charge et se filtre en mémoire 10 à 50 fois plus vite que le CSV compressé.

### 3. Backtest Engine : La simulation pure et dure
Une fois que les données dans `storage/processed/` sont garanties propres et saines, le **Backtest Engine** peut travailler sereinement.

Sa seule et unique responsabilité est d'exécuter la logique de ta stratégie sur ce dataset parfait. Il intègre un simulateur de courtier (broker) très réaliste qui gère les frais réels, le slippage, et le type de passage d'ordre (long, short, reversal).

Puisque les données sont pré-nettoyées et au format Parquet, le moteur peut enchaîner des milliers de simulations de paramètres en quelques secondes. Pour les optimisations massives nécessitant des millions de calculs, un pont optionnel vers **VectorBT** permet d'exploiter la puissance des processeurs vectoriels sans complexifier le moteur de simulation principal.

### 4. Launcher : Simplifier l'exploitation
Le moteur de backtest expose une API Web FastAPI pour permettre à des interfaces graphiques d'interagir avec lui. Pour éviter que tu doives ouvrir trois terminaux différents pour lancer l'API, le worker de tâches de fond et la base SQLite locale, le **Launcher** encapsule tout cela dans un script unique.

C'est la couche de confort qui fait le lien entre un outil CLI et une application de bureau utilisable au quotidien.
