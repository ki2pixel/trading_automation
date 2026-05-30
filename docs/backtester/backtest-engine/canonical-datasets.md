# Les Datasets Canoniques : Préparer des données parfaites

**TL;DR** : L'outil `build-canonical` nettoie tes exports CSV bruts, applique les splits d'actions, réaligne les prix et convertit le tout en fichiers Parquet ultra-rapides pour tes backtests.

Tu as récupéré tes fichiers CSV bruts via ton collecteur Google Drive. C'est parfait. Mais avant de les donner à manger à ton moteur de simulation, tu te retrouves face à un problème invisible mais mortel : la qualité des données. 

Les exports bruts contiennent souvent des anomalies : des virgules décimales mal placées à cause des paramètres régionaux de ton tableur, des valeurs aberrantes ou des trous dans les dates. Plus grave encore, les splits d'actions historiques ne sont pas ajustés. Si une action a subi un split de 2 pour 1, le prix brut est divisé par deux du jour au lendemain, ce qui fera croire à ta stratégie qu'il y a eu un krach boursier imaginaire.

La commande **`build-canonical`** est ton usine de traitement. Elle transforme ces données brutes et désordonnées en un dataset parfait, harmonisé et optimisé au format **Parquet**.

---

## Pourquoi choisir le format Parquet ?

Historiquement, les backtesters lisent des fichiers CSV. C'est un format simple, mais très inefficace. Charger un fichier CSV de plusieurs centaines de mégaoctets en mémoire prend plusieurs secondes.

Le format **Parquet** change la donne :
- **Stockage en colonnes** : Si ta stratégie n'a besoin que du prix de clôture (`close`), Parquet charge uniquement cette colonne sans lire tout le reste de la ligne.
- **Compression native** : Les fichiers Parquet prennent 5 à 10 fois moins de place sur ton disque dur que les CSV classiques.
- **Vitesse de chargement** : Tes backtests se lancent presque instantanément, ce qui te fait gagner un temps précieux lors des optimisations de paramètres.

---

## Nettoyer tes données en pratique

Pour préparer ton environnement et installer les dépendances nécessaires au traitement :

```bash
python3 -m pip install --user -r requirements-backtest-engine.txt
```

### 1. Lancer un traitement complet de tes fichiers
C'est la commande standard à exécuter après chaque session de collecte. Elle traite toutes tes données d'actions et de devises d'un seul coup :

```bash
python3 -m backtest_engine build-canonical \
  --format parquet \
  --divisor-overrides-file configs/canonical_divisor_overrides.json \
  --output-dir storage/processed
```

### 2. Le problème des décimales altérées : Les Diviseurs (Divisor Overrides)
SheetsFinance exporte parfois des prix multipliés par 10 ou 100 à cause de formats régionaux conflictuels (par exemple, un prix réel de `12.34` exporté sous la forme `1234`). 

Pour corriger cela de manière fiable sans modifier tes fichiers sources, tu peux forcer un diviseur spécifique pour certains symboles sensibles :

```bash
python3 -m backtest_engine build-canonical \
  --symbols GMAB,LOGI,ZEAL.CO \
  --divisor-overrides GMAB=10,LOGI=100,ZEAL.CO=10 \
  --format parquet \
  --output-dir storage/processed
```

Pour t'éviter de retaper ces configurations à chaque fois, nous fournissons un fichier de configuration partagé et versionné : `configs/canonical_divisor_overrides.json`. Utilise-le systématiquement pour conserver tes réglages.

### 3. Valider la qualité de tes données (Quality Reports)
Chaque fois que `build-canonical` s'exécute, il génère un rapport de qualité au format JSON pour chaque symbole dans le dossier `storage/processed/quality_reports/`. 

Ces rapports te montrent des statistiques claires :
- Le nombre de lignes contenant des prix invalides ou impossibles (OHLC incohérents).
- Le nombre de barres manquantes (gaps temporels).
- Les corrections et réparations de cours appliquées automatiquement par le script.

Par exemple, sur une reconstruction complète de notre flux de devises `USDEUR` :
- Les horodatages invalides sont tombés à 0.
- Les erreurs OHLC sont tombées à 0.
- Le nombre de barres réparées ou ajustées pour assurer la continuité représente environ 3% du jeu de données, garantissant un historique parfaitement fluide pour tes simulations.
