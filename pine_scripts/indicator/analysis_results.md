# Analyse des Indicateurs Pine Script pour Conversion VectorBT

## 1. Méthodologie d'Évaluation
40 scripts Pine Script ont été analysés pour identifier les meilleurs candidats à une intégration dans le moteur de trading quantitatif basé sur `vectorbt`.
L'analyse s'est basée sur 4 critères cardinaux :
1. **Vectorisation (VectorBT)** : Rejet des scripts utilisant des boucles `for/while` imbriquées ou des tableaux dynamiques (`array.new`) sans équivalent matriciel évident. Ces approches "stateful" brisent les performances de pandas/vectorbt.
2. **Absence de Repaint / Data Leakage** : Élimination des scripts exploitant `request.security` avec anticipation temporelle (lookahead), ce qui fausserait les résultats du backtest.
3. **Clarté du Signal (Alpha)** : Capacité de l'indicateur à générer des signaux exploitables (`entries`/`exits`) ou des filtres de régimes précis.
4. **Indépendance aux Données Exotiques** : Priorité aux algorithmes se contentant des données OHLCV standards, sans dépendre de données de carnet d'ordres intra-bougie indisponibles.

Sur les 40 fichiers, **plus de 25 contiennent des boucles ou des manipulations de tableaux** complexes (souvent liées à l'affichage de l'UI sur TradingView : boîtes, lignes, labels). Nous avons filtré la logique mathématique sous-jacente pour extraire les **7 meilleurs candidats** offrant le meilleur ratio "Valeur Alpha / Faisabilité Technique".

---

## 2. Top Candidats Sélectionnés

### 1. Trend Type Indicator (BobRivera990)
- **Type** : Filtre de Tendance et Régime (basé ATR, ADX, DMI).
- **Rationale & Intérêt** : Combine de multiples métriques de volatilité (ATR) et de force directionnelle (ADX) pour définir de manière déterministe si le marché est en range ou en tendance. Parfait comme filtre macroscopique "stateless" pour bloquer le surtrading en range.
- **Complexité d'Implémentation** : **Facile**.
- **Implémentation VectorBT** : Logique purement matricielle.
  ```python
  # Concept VectorBT
  atr = vbt.ATR.run(high, low, close, window=14).atr
  adx = vbt.ADX.run(high, low, close, window=14).adx
  is_trending = adx > 20
  # Utiliser is_trending comme masque (filtre de régime)
  ```

### 2. HMM Regime Filter Market State
- **Type** : Machine Learning / Filtre de Régimes (Modèles de Markov Cachés).
- **Rationale & Intérêt** : Infère la probabilité d'être dans l'un des 3 états cachés du marché (Hausse, Baisse, Range) via des calculs de probabilités bayésiennes. L'alpha généré est extrêmement puissant pour ajuster dynamiquement l'exposition au risque.
- **Complexité d'Implémentation** : **Difficile mais Crucial**.
- **Implémentation VectorBT** : La matrice de transition HMM est "stateful". Cela nécessitera la création d'une fonction accélérée par `@njit` (Numba) couplée à `vbt.Indicator.from_custom_func` pour itérer sans boucle Python.

### 3. Machine Learning Lorentzian Classification
- **Type** : Machine Learning (k-Nearest Neighbors avec distance de Lorentz).
- **Rationale & Intérêt** : Offre des signaux de retournement hautement qualitatifs basés sur la similarité des prix historiques. Très réputé pour sa précision en clustering non-paramétrique.
- **Complexité d'Implémentation** : **Très Difficile**.
- **Implémentation VectorBT** : L'algorithme kNN nécessite de mesurer la distance entre le vecteur actuel et tous les vecteurs passés. Cela exige une forte optimisation Numba/C++ pour ne pas s'effondrer en calcul lors d'un backtest sur des millions de ticks.

### 4. Pivot Breakout Retest Signals (algo-aakash)
- **Type** : Structure de Marché (Pivots, Breakouts, Retests).
- **Rationale & Intérêt** : Automatise l'identification mathématique de la cassure des zones de liquidité (pivots locaux) et confirme les entrées sur retest.
- **Complexité d'Implémentation** : **Moyen**.
- **Implémentation VectorBT** : Remplacer l'historique par des `rolling_max` et `rolling_min` couplés à des opérations logiques décalées (`shift(1)`) pour valider qu'un ancien plafond devient un nouveau plancher.

### 5. Adaptive Trend Classification Moving Averages
- **Type** : Suivi de Tendance Adaptatif.
- **Rationale & Intérêt** : S'ajuste à la volatilité du marché (KAMA/FRAMA) pour réduire les faux signaux (whipsaws) typiques des SMA/EMA classiques en période de consolidation.
- **Complexité d'Implémentation** : **Facile à Moyen**.
- **Implémentation VectorBT** : Soit l'utilisation de `vbt.IndicatorFactory` pour recréer la pondération adaptative via Numpy, soit l'intégration d'une librairie externe type `ta-lib` si l'indicateur adaptatif standard y figure.

### 6. Momentum-based ZigZag (incl QQE)
- **Type** : Momentum & Swings.
- **Rationale & Intérêt** : Le QQE (Quantitative Qualitative Estimation) est un oscillateur robuste (RSI lissé couplé à de l'ATR) qui filtre mieux le bruit. Le script originel utilise le QQE pour valider les pivots d'un ZigZag "Non-Repainting".
- **Complexité d'Implémentation** : **Moyen**.
- **Implémentation VectorBT** : Le calcul du QQE est 100% vectorisable. Le tracé mathématique des sommets/creux du ZigZag nécessitera un buffer Numba stateful pour gérer l'oscillation.

### 7. MSL Friendly Trend
- **Type** : Suivi de Tendance via Market Structure Levels (MSL).
- **Rationale & Intérêt** : Aligne l'identification de tendance avec les cassures réelles de la structure des prix. Produit des signaux de continuation robustes sur les pullbacks.
- **Complexité d'Implémentation** : **Facile**.
- **Implémentation VectorBT** : Des conditions booléennes simples comparant les cours de clôture aux `highest(high, n)` ou `lowest(low, n)` décalés. Idéal pour être transformé en composant signalétique pur.

---

## 3. Conclusion & Recommandations
Pour intégrer ces concepts dans le moteur tout en garantissant un temps de simulation inférieur à la milliseconde :
1. **Phase 1 (Quick Wins Vectorisés)** : Implémenter immédiatement `Trend Type Indicator` et `MSL Friendly Trend`. Ils sont nativement matriciels et offriront une base de filtrage macroscopique solide.
2. **Phase 2 (Accélération Numba)** : Développer un squelette Numba standard pour le moteur permettant d'embarquer les indicateurs stateful comme le `HMM Regime Filter` et le `ZigZag`.
3. **Phase 3 (Recherche Deep ML)** : Isoler le `Lorentzian Classification` en un projet de recherche à part entière, nécessitant potentiellement un module compilé C++ / Cython pour être utilisable en batch sur VectorBT.

---

## 4. Méthodologie d'Intégration (D'Indicateur à Stratégie)

Suite au succès de l'intégration des "Quick Wins", l'architecture standardisée pour convertir un indicateur Pine Script isolé en stratégie de backtest automatisée se décompose en trois couches :

1. **Création de l'Indicateur Core (`backtest_engine/indicators/`)**
   - Utilisation de `vbt.IndicatorFactory` pour recréer la logique mathématique pure.
   - Vectorisation totale via Pandas/NumPy (ex: calculs RMA/ATR avec `.ewm()` et gestion d'état avec `np.select` et `ffill()`).
   - *Règle stricte* : Aucune boucle Python `for`/`while`, assurant des temps de calculs optimaux (0 milliseconde par indicateur).

2. **Couche Logique et Signalétique (`pine_scripts_convert_to_python/strategy/`)**
   - Définition des paramètres d'optimisation (Search Space) via une classe Pydantic (`Config`).
   - Appel à l'indicateur Core pour extraire l'état du marché (ex: `-1.0` / `1.0`).
   - Génération des vecteurs booléens de signaux (`long_entry`, `short_entry`, `long_exit`, `short_exit`) basés sur les transitions d'états (ex: croisement d'états).

3. **Couche d'Exécution & Registre (`backtest_engine/strategies/` & `configs/`)**
   - Création du wrapper `run_***()` chargé de piloter le `BrokerSimulator`.
   - Simulation exhaustive : application des Stop-Loss (Safety Stops), Trailing Stops, Commissions estimées, Slippage et gestion multi-devises (Forex V3).
   - Ajout d'une configuration `.default.json` complète dans `configs/strategies/`.
   - Enregistrement final au sein du `StrategyRegistry` pour rendre la stratégie officiellement exploitable par le Dashboard Web et l'Optimiseur Bayésien (Optuna).

---

## 5. Statut d'Avancement du Projet

- **[TERMINE] Phase 1 & 2 : "Quick Wins Vectorisés" (Juin 2026)**
  - ✅ **Trend Type Indicator** : Totalement implémenté en tant que stratégie (`trend_type`). Indicateur 100% natif Pandas (RMA/ATR).
  - ✅ **MSL Friendly Trend** : Totalement implémenté en tant que stratégie (`msl_trend`). Vectorisation des trailing stops par forward filling.
  
- **[EN COURS] Phase 3 : "Accélération Numba et Stateful"**
  - ✅ Pivot Breakout Retest Signals
  - ✅ Adaptive Trend Classification
  - ✅ Momentum-based ZigZag
  - ⏳ HMM Regime Filter

- **[A FAIRE] Phase 4 : "Recherche Machine Learning"**
  - ⏳ Lorentzian Classification

