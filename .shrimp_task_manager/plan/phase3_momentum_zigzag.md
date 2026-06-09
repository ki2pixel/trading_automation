# Plan d'implémentation : Momentum-based ZigZag (Accélération Numba)

## Objectif
Intégrer l'indicateur stateful **Momentum-based ZigZag** (basé sur le script Pine original) dans le moteur de backtest avec une accélération Numba haute performance sous VectorBT.
Créer la stratégie associée, configurer les fichiers par défaut, et valider le tout avec des tests de non-régression et de performance sans Lookahead Bias.

## Étapes prévues

### 1. Développement de l'Indicateur Numba
Fichier : `backtest_engine/indicators/momentum_based_zigzag.py`
- Traduction de la logique QQE (RSI lissé, ATR lissé, dar, longband/shortband cumulatifs).
- Traduction de la logique ZigZag avec gestion stateful (`zz_peak`, `zz_bottom`).
- Implémentation en `njit(cache=True)` pour une accélération maximale.
- Intégration via `vbt.IndicatorFactory`.

### 2. Squelette de Stratégie
Fichier : `pine_scripts_convert_to_python/strategy/momentum_based_zigzag_strategy.py`
- Configuration Pydantic `MomentumBasedZigZagStrategyConfig`.
- Fonction d'exécution générant les signaux longs/shorts et stop-loss dynamiques.

### 3. Enregistrement et Configuration
- Création de `backtest_engine/strategies/momentum_based_zigzag.py` pour orchestrer le backtest.
- Ajout à `strategy_registry.py` de manière propre.
- Création du JSON par défaut `configs/strategies/momentum_based_zigzag.default.json`.

### 4. Tests et Validation
Fichier : `tests/test_momentum_based_zigzag.py`
- Tests d'absence de Lookahead Bias (comparaison sur N bars vs all bars).
- Validation des performances de Numba (exécution < 150ms pour 10 000 bars).
- Tests de comportements multi-symboles/colonnes.

## Points de Risque et Analyse Numba
- **Lookahead Bias** : Les indicateurs QQE et ZigZag utilisent l'historique précédent (ex: `zz_peak[1]`). L'implémentation avec boucle `for i in range(1, len)` évitera naturellement l'accès aux données futures.
- **Thread-Safety** : VectorBT peut paralléliser sur plusieurs symboles/timeframes (via axes en 2D). La fonction njit doit correctement itérer sur les colonnes (symbole) et lignes (bars) en gardant les états séparés par colonne.
- **Types array** : Utilisation stricte de `np.float64` pour assurer une compilation Numba efficace, notamment depuis pandas DataFrames ou des arrays existants VectorBT.
