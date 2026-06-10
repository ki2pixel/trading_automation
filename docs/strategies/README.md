# Stratégies de Trading

Ce répertoire regroupe l'ensemble des stratégies disponibles dans le moteur de backtest. Le système intègre 16 stratégies traduits ou inspirés de Pine Script, optimisées localement en Python et Numba.

---

## Organisation et Régimes de Marché

Les stratégies sont classées selon leur logique d'exécution et le régime de marché pour lequel elles ont été conçues.

### 1. Suivi de Tendance (Trend Following)
Ces stratégies visent à capturer des mouvements directionnels longs. Elles souffrent de faux signaux lors des phases de consolidation mais surperforment dans les marchés directionnels.
*   **HMA Crossover** : Croisement simple de deux moyennes mobiles de Hull.
*   **PMax Explorer** : Croisement d'une moyenne mobile avec un stop suiveur dynamique basé sur l'ATR.
*   **Adaptive Volatility Trend (AVT)** : Mesure de tendance avec adaptation automatique à la volatilité via le ratio d'efficience de Kaufman.
*   **Range Filter** : Filtre de bruit identifiant les débuts de tendances majeures.
*   **MSL Friendly Trend** : Suivi de tendance calé sur les cassures de structures de marché (Market Structure Levels).
*   **Trend Type Indicator** : Filtre macro combinant l'ADX, le DMI et l'ATR pour définir la force directionnelle.
*   **Adaptive Trend Classification** : Classification des tendances par pondération adaptative de six types de moyennes mobiles.

### 2. Retour à la Moyenne & Intraday (Mean Reversion)
Stratégies cherchant à exploiter les extrêmes de prix et les épuisements de momentum.
*   **Noise Boundary Intraday** : Bandes de volatilité ancrées à l'ouverture quotidienne et au close de la veille; intègre des sorties complexes en escalier (ladder exits). Guide technique : [noise_boundary_intraday.md](./noise_boundary_intraday.md).
*   **Cybernetic Trading (Transformée de Hilbert)** : Traitement de signal par quadrature et phase pour identifier le cycle dominant sans lag. Guide technique : [cybernetic_hilbert.md](./cybernetic_hilbert.md).
*   **Smart Trader Geometric** : Analyse géométrique isotrope mesurant l'aire et les distances par rapport aux pivots sans aucun lissage temporel.

### 3. Modèles Statistiques & Machine Learning
Stratégies prédictives non-paramétriques et bayésiennes s'adaptant dynamiquement à l'historique récent.
*   **Lorentzian Classification (KNN)** : Classifieur de plus proches voisins mesurant la distance dans un espace de Lorentz déformé à multi-dimensions. Guide technique : [lorentzian_classification.md](./lorentzian_classification.md).
*   **HMM Regime Filter** : Modèle de Markov Caché (HMM) probabiliste à transitions d'état stabilisées par inertie. Guide technique : [hmm_regime_filter.md](./hmm_regime_filter.md).

### 4. Swing Trading & Exécutions Complexes
Stratégies axées sur la détection de structures de chandeliers ou la gestion avancée de positions (DCA/Grid).
*   **3Commas-Bot** : Simulateur de bot DCA classique avec croisement de moyennes et stops ATR.
*   **Bjorgum Double Tap** : Détection de patterns Double Top et Double Bottom avec sorties de cibles Fibonacci.
*   **Pivot Breakout Retest Signals** : Détection des cassures de pivots majeurs suivies d'une validation temporelle sur le retest.
*   **Momentum-based ZigZag** : Swing trading basé sur un oscillateur QQE lissé et un tracé de ZigZag stateful anti-lookahead.

---

## Configuration et Intégration

### Fichiers de Configuration
Chaque stratégie possède un fichier de configuration par défaut au format JSON dans le dossier `configs/strategies/` (ex : `hma_crossover.default.json`). Ce fichier définit :
1.  **Les paramètres spécifiques** de l'indicateur (périodes, multiplicateurs, sources).
2.  **Les paramètres du broker** associés (commissions, slippage, direction autorisée, bracket exits, safety stops).

### Enregistrement des Stratégies
L'intégration d'une stratégie au moteur de backtest s'effectue dans [strategy_registry.py](../../backtest_engine/strategy_registry.py) :
```python
StrategyRegistry.register(
    StrategyInfo(
        name="nom_strategie",
        config_override_class=ConfigOverridesClass,
        run_function=run_function,
        load_overrides_function=load_overrides,
        overrides_from_mapping_function=overrides_from_mapping,
        indicators=["liste", "indicateurs"],
        vectorbt_prescan=vectorbt_prescan_function_or_none,
    )
)
```

Pour comprendre comment paramétrer au mieux les optimisations de chaque stratégie et éviter le sur-ajustement (curve-fitting), consultez la [Feuille de Route d'Optimisation](../../configs/strategies/README_OPTIMIZATION_ROADMAP.md).
