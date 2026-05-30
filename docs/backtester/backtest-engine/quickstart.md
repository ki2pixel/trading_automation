# Démarrage rapide : Ton premier backtest local

**TL;DR** : Valide tes données brutes en une ligne, lance un backtest unitaire sur la stratégie de ton choix et consulte les rapports de performance générés en local.

Tu as configuré ton collecteur et tes fichiers CSV bruts commencent à s'accumuler dans ton dossier `SheetsFinance_Export/`. C'est une excellente première étape, mais tu as un problème : comment savoir si ces données sont saines ? Et surtout, comment lancer ta première simulation sans te noyer dans les configurations complexes ?

Ce guide va te guider, étape par étape, de la validation de tes fichiers de cours jusqu'à l'analyse de tes premiers rapports de trading.

---

## Étape 1 : Analyser et valider tes données brutes

Avant de faire confiance à un backtest, tu dois t'assurer que les cours de bourse ne contiennent pas d'incohérences (comme un prix minimum supérieur au prix maximum sur une barre de 5 minutes, ou des virgules décimales mal interprétées).

Le moteur intègre un outil de scan rapide pour faire ce diagnostic :

```bash
python3 -m backtest_engine scan --symbol GMAB --max-files 1
```

### Que faire si tes données contiennent des virgules décimales européennes ?
Si tes fichiers de données proviennent d'un export SheetsFinance mal configuré, il se peut que les décimales utilisent des virgules (ex: `12,34` au lieu de `12.34`). Pour un diagnostic exploratoire rapide, tu peux demander au scanner de tenter une réparation heuristique automatique :

```bash
python3 -m backtest_engine scan --symbol GMAB --max-files 1 --price-repair auto
```

> [!WARNING]
> L'option `--price-repair auto` est un outil de secours temporaire. Pour des résultats fiables à 100%, la bonne approche est de corriger la configuration de ton Google Sheets / Apps Script pour qu'il exporte directement des points comme délimiteurs de décimales.

---

## Étape 2 : Lancer ton tout premier backtest

Le moteur travaille par défaut sur des datasets canoniques propres et optimisés au format Parquet dans `storage/processed/`. Avant de lancer la commande ci-dessous, assure-toi d'avoir exécuté la commande `build-canonical` au moins une fois pour préparer tes fichiers.

### Choisir ta stratégie
Sept stratégies sont déjà codées et prêtes à l'emploi :
- `hma_crossover` : Croisement de moyennes HMA
- `adaptive_volatility_trend` (AVT) : Tendance adaptative selon la volatilité
- `range_filter` : Filtre de bandes de prix dynamique
- `3commas_bot` : Simulation de bots de grille / DCA
- `pmax_explorer` : Suivi de tendance PMax avec lissage
- `bjorgum_double_tap` : Stratégie de double rebond basée sur l'ATR
- `noise_boundary_intraday` : Cassure de bornes de bruit en intraday

Chaque stratégie dispose d'un fichier de configuration par défaut contenant ses paramètres optimaux. Tu peux les trouver dans `configs/strategies/` (ex : `configs/strategies/hma_crossover.default.json`).

### Exécuter la commande run
Pour lancer un test unitaire sur la stratégie `hma_crossover` pour l'action `GMAB` sur un timeframe de 15 minutes :

```bash
python3 -m backtest_engine run \
  --strategy hma_crossover \
  --symbol GMAB \
  --config configs/strategies/hma_crossover.default.json \
  --timeframe 15 \
  --max-entry-price 10000
```

> [!TIP]
> Par défaut, le moteur utilise les données collectées en barres de 5 minutes. Si tu demandes un `--timeframe 15`, le moteur va agréger automatiquement et proprement les barres de 5 minutes à la volée (le prix d'ouverture sera celui de la première barre, le plus haut le max des trois barres, le volume la somme, etc.).

---

## Personnaliser ton test depuis la ligne de commande

Les arguments que tu saisis dans ton terminal sont toujours prioritaires sur le contenu du fichier de configuration JSON. Voici comment adapter ton test rapidement :

### Simuler des frais de courtage et du slippage réalistes
Ne teste jamais une stratégie en supposant que le courtage est gratuit et instantané. Tu peux surcharger les coûts par transaction directement en ligne de commande :

```bash
python3 -m backtest_engine run \
  --strategy hma_crossover \
  --symbol GMAB \
  --config configs/strategies/hma_crossover.default.json \
  --estimated-commission-per-order-long 1 \
  --estimated-commission-per-order-short 3 \
  --estimated-slippage-per-side-long 0.5 \
  --estimated-slippage-per-side-short 0.5
```

### Limiter le test à une période précise (Backtesting historique)
Pour éviter de tester sur des années de données non représentatives ou pour isoler une phase de marché haussière / baissière spécifique :

```bash
python3 -m backtest_engine run \
  --strategy hma_crossover \
  --symbol GMAB \
  --start-date 2024-01-01 \
  --end-date 2025-01-01
```

---

## Étape 3 : Analyser les résultats

Une fois l'exécution terminée, le moteur écrit tous ses rapports dans un sous-dossier unique :

```text
reports/local/{STRATEGY}/{SYMBOL}/{RUN_ID}/
```

Dans ce dossier, tu trouveras plusieurs fichiers clés :
- `trades.csv` : La liste exhaustive de toutes les transactions exécutées, avec leurs prix d'entrée, de sortie, et les frais payés.
- `equity_curve.csv` : L'évolution de ton capital barre après barre.
- `metrics.json` : Un résumé complet de tes performances (Ratios Sharpe et Sortino, Drawdown maximum, profit total, taux de réussite, gains longs vs courts).
- `report.html` : Un rapport visuel simple pour partager ou consulter tes résultats d'un coup d'œil.
