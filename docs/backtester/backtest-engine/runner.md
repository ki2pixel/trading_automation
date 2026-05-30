# Comment exécuter un backtest unitaire ?

**TL;DR** : Utilise la commande `run` pour faire tourner une simulation unique. Ce guide t'explique comment configurer tes frais, cibler tes fenêtres de dates et simuler des conditions de courtage réalistes à travers un exemple concret.

Imaginons un cas pratique : tu viens de coder une stratégie de croisement de moyennes mobiles (HMA Crossover). Tu veux savoir ce qu'elle aurait donné sur l'action **GMAB** tout au long de l'année dernière. 

Si tu te contentes de lancer la simulation par défaut, tu risques d'obtenir des résultats faussement positifs. Pour avoir une idée fiable de sa rentabilité dans le monde réel, tu dois simuler des frais réels de courtier, gérer le slippage et tester différents horizons de temps. 

Voici pas-à-pas comment configurer et lancer ce test.

---

## Le scénario concret : Lancer HMA Crossover sur GMAB

Pour notre exemple, nous allons utiliser le dataset canonique propre de `GMAB`. Nous voulons exécuter notre stratégie sur un timeframe de 15 minutes, en limitant l'achat si le prix unitaire de l'action dépasse 10 000 unités de compte.

### 1. La commande de base
Pour lancer cette simulation simple avec les paramètres par défaut de la stratégie :

```bash
python3 -m backtest_engine run \
  --strategy hma_crossover \
  --symbol GMAB \
  --config configs/strategies/hma_crossover.default.json \
  --timeframe 15 \
  --max-entry-price 10000
```

### 2. Ajouter les contraintes du monde réel (Frais et Slippage)
Dans la réalité, chaque ordre passé te coûte des frais de courtage, et le prix d'exécution est souvent légèrement moins bon que le prix théorique du graphique (le slippage). 

Si ta stratégie effectue beaucoup de transactions à court terme, ces frais cumulés peuvent transformer une stratégie gagnante en gouffre financier. Voici comment surcharger ces coûts pour simuler des conditions de marché difficiles (par exemple, 1$ de frais à l'achat, 3$ à la vente, et 0.5 unité de slippage de chaque côté) :

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

### 3. Cibler une période historique précise
Pour évaluer le comportement de ta stratégie lors d'un krach boursier ou d'une phase de hausse continue, restreins la période de test à l'aide de bornes temporelles inclusives :

```bash
python3 -m backtest_engine run \
  --strategy hma_crossover \
  --symbol GMAB \
  --start-date 2024-01-01 \
  --end-date 2025-01-01
```

---

## Le simulateur de broker commun

Sous le capot, toutes les stratégies partagent le même moteur de simulation défini dans `backtest_engine/broker.py`. 

C'est ce module qui s'occupe de tâches ingrates mais cruciales :
- **Normaliser les quantités d'achat** : Éviter d'acheter des fractions d'actions non autorisées par ton courtier.
- **Exécuter les ordres au marché** : Valider que les prix demandés correspondent à la réalité de la barre de cours suivante.
- **Gérer les Reversals** : Clôturer proprement une position longue pour ouvrir immédiatement une position courte si le signal s'inverse.
- **Mesurer le Drawdown en temps réel** : Suivre la perte maximale latente pour déclencher des arrêts d'urgence si nécessaire.

### Comment simuler un courtage d'actions entières ?
Si tu backtestes des actions traditionnelles (comme GMAB) et que ton courtier n'autorise pas l'achat de fractions de titres, ajoute l'option `--whole-shares` pour forcer l'arrondi à l'entier inférieur le plus proche :

```bash
python3 -m backtest_engine run --symbol GMAB --whole-shares
```

### Déclencher un coupe-circuit d'urgence (Early Stopping)
Si le marché se retourne violemment contre toi, tu veux éviter de perdre tout ton capital. Tu peux configurer une limite de perte maximale (drawdown) qui arrêtera immédiatement le backtest dès que ton portefeuille chute de plus d'un certain pourcentage :

```bash
python3 -m backtest_engine run \
  --symbol BTCUSD \
  --early-stop-drawdown-pct 30
```

---

## Exemples pour les autres stratégies

Si tu souhaites tester d'autres logiques de signaux, voici les commandes adaptées pour chaque stratégie embarquée :

### Adaptive Volatility Trend (AVT)
```bash
python3 -m backtest_engine run \
  --strategy adaptive_volatility_trend \
  --symbol BTCUSD \
  --config configs/strategies/adaptive_volatility_trend.default.json \
  --timeframe 15 \
  --max-entry-price 50000
```

### Range Filter
```bash
python3 -m backtest_engine run \
  --strategy range_filter \
  --symbol BTCUSD \
  --config configs/strategies/range_filter.default.json \
  --timeframe 15 \
  --sampling-period 50 \
  --range-multiplier 2.5 \
  --max-entry-price 50000
```

### 3Commas Bot
```bash
python3 -m backtest_engine run \
  --strategy 3commas_bot \
  --symbol BTCUSD \
  --config configs/strategies/3commas_bot.default.json \
  --timeframe 15 \
  --max-entry-price 50000
```

### PMax Explorer
```bash
python3 -m backtest_engine run \
  --strategy pmax_explorer \
  --symbol BTCUSD \
  --config configs/strategies/pmax_explorer.default.json \
  --timeframe 15 \
  --max-entry-price 50000
```

### Bjorgum Double Tap
```bash
python3 -m backtest_engine run \
  --strategy bjorgum_double_tap \
  --symbol BTCUSD \
  --config configs/strategies/bjorgum_double_tap.default.json \
  --timeframe 15 \
  --max-entry-price 50000
```

### Noise Boundary Intraday
```bash
python3 -m backtest_engine run \
  --strategy noise_boundary_intraday \
  --symbol BTCUSD \
  --config configs/strategies/noise_boundary_intraday.default.json \
  --timeframe 15 \
  --lookback-days 20 \
  --volatility-multiplier-enter 2.0 \
  --volatility-multiplier-exit 1.0 \
  --max-entry-price 50000
```

---

## Tester en mode diagnostic (Directement sur les CSV bruts)

Si tu n'as pas encore compilé tes datasets Parquet propres et que tu veux juste faire un test rapide directement sur tes fichiers CSV de collecte d'origine, tu peux forcer le mode brut :

```bash
python3 -m backtest_engine run \
  --strategy hma_crossover \
  --symbol GMAB \
  --data-source raw \
  --max-files 1 \
  --price-repair auto \
  --market-divisor 10 \
  --max-entry-price 10000
```
