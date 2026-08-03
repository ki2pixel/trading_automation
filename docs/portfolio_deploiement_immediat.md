# Portfolio de Déploiement Immédiat

Ce document consigne la liste exacte des **51 setups** identifiés pour un déploiement en production ou en paper-trading actif, suite à la campagne globale d'optimisation et d'arbitrage.

### Critères de Sélection
Les setups ci-dessous cochent toutes les conditions de robustesse suivantes :
- **Profit Factor** >= 1.5
- **Sharpe Ratio** > 1.0
- **Kelly Criterion** > 0 (pour garantir un avantage mathématique à l'allocation)
- **Rendement Mensuel Moyen (€)** > 0 (Générateur de profit brut justifiant le risque)

### Remarques Analytiques
- **`3commas_bot`** domine le portefeuille avec une excellente fréquence et de solides performances en euros.
- **`cybernetic_hilbert`** ressort extrêmement fort sur `ZEAL.CO` (nécessite une petite surveillance manuelle initiale pour écarter tout overfitting résiduel).
- **`momentum_based_zigzag`** et **`lorentzian_classification`** offrent d'excellents Profit Factors et des allocations Kelly élevées, parfaits pour la stabilité.

## Les 51 Setups Validés (Triés par Poids Kelly décroissant)

| Stratégie | Actif | Timeframe | Profit Factor | Sharpe | Kelly Weight | Rendement Mensuel (€) |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| `adaptive_volatility_trend` | **dpwdeeur** | 45m | Inf | 1.22 | **3.02%** | 6.88 € |
| `adaptive_volatility_trend` | **akzanleur** | 30m | Inf | 1.24 | **3.02%** | 5.65 € |
| `3commas_bot` | **teniteur** | 30m | 2.78 | 1.08 | **1.45%** | 6.83 € |
| `momentum_based_zigzag` | **SAP** | 30m | 5.53 | 1.13 | **1.43%** | 2.29 € |
| `3commas_bot` | **GMAB** | 60m | 2.27 | 1.65 | **1.16%** | 8.78 € |
| `momentum_based_zigzag` | **randnleur** | 10m | 2.47 | 1.16 | **1.11%** | 0.84 € |
| `momentum_based_zigzag` | **EVD.DE** | 45m | 3.58 | 1.96 | **1.03%** | 0.24 € |
| `lorentzian_classification` | **FPE.DE** | 120m | 2.68 | 1.03 | **1.02%** | 0.05 € |
| `momentum_based_zigzag` | **GMAB** | 1m | 2.36 | 2.05 | **0.96%** | 0.66 € |
| `3commas_bot` | **GMAB** | 20m | 2.19 | 1.42 | **0.94%** | 5.65 € |
| `3commas_bot` | **FPE.DE** | 5m | 1.99 | 2.04 | **0.90%** | 5.17 € |
| `lorentzian_classification` | **GMAB** | 30m | 2.66 | 1.81 | **0.89%** | 0.49 € |
| `3commas_bot` | **FPE.DE** | 20m | 1.94 | 1.15 | **0.87%** | 7.01 € |
| `trend_type` | **NVS** | 15m | 2.04 | 1.12 | **0.86%** | 0.38 € |
| `msl_trend` | **NVO** | 30m | 2.01 | 1.03 | **0.85%** | 9.97 € |
| `3commas_bot` | **FPE.DE** | 30m | 1.81 | 1.05 | **0.83%** | 5.58 € |
| `cybernetic_hilbert` | **ZEAL.CO** | 60m | 1.95 | 3.37 | **0.74%** | 54.35 € |
| `range_filter` | **GMAB** | 30m | 2.28 | 2.11 | **0.72%** | 6.25 € |
| `cybernetic_hilbert` | **ZEAL.CO** | 45m | 1.85 | 3.36 | **0.71%** | 56.73 € |
| `momentum_based_zigzag` | **NVO** | 45m | 2.60 | 1.89 | **0.70%** | 18.18 € |
| `hma_crossover` | **GMAB** | 45m | 1.95 | 1.84 | **0.70%** | 4.47 € |
| `3commas_bot` | **GMAB** | 15m | 1.61 | 1.21 | **0.70%** | 5.70 € |
| `momentum_based_zigzag` | **AMS.MC** | 10m | 2.86 | 1.86 | **0.69%** | 1.42 € |
| `hmm_regime_filter` | **NVO** | 45m | 2.21 | 1.30 | **0.68%** | 9.98 € |
| `momentum_based_zigzag` | **dotusdt** | 45m | 2.86 | 1.23 | **0.67%** | 4.10 € |
| `adaptive_volatility_trend` | **GMAB** | 5m | 1.86 | 2.18 | **0.66%** | 5.94 € |
| `momentum_based_zigzag` | **daideeur** | 15m | 2.16 | 2.67 | **0.62%** | 2.70 € |
| `hmm_regime_filter` | **NVO** | 60m | 1.92 | 1.34 | **0.62%** | 10.42 € |
| `range_filter` | **GMAB** | 20m | 2.05 | 2.18 | **0.62%** | 6.26 € |
| `3commas_bot` | **GMAB** | 30m | 1.56 | 1.14 | **0.60%** | 5.49 € |
| `pmax_explorer` | **GMAB** | 15m | 1.80 | 1.67 | **0.59%** | 4.46 € |
| `hma_crossover` | **FPE.DE** | 30m | 1.63 | 1.01 | **0.59%** | 2.89 € |
| `pmax_explorer` | **GMAB** | 30m | 1.84 | 1.70 | **0.58%** | 4.51 € |
| `cybernetic_hilbert` | **dotusdt** | 60m | 1.65 | 2.24 | **0.57%** | 7.49 € |
| `cybernetic_hilbert` | **ltcusdt** | 45m | 1.56 | 1.54 | **0.54%** | 58.69 € |
| `cybernetic_hilbert` | **ZEAL.CO** | 30m | 1.59 | 3.24 | **0.54%** | 55.00 € |
| `momentum_based_zigzag` | **akzanleur** | 30m | 1.81 | 1.16 | **0.54%** | 1.40 € |
| `hmm_regime_filter` | **NVO** | 30m | 1.82 | 1.45 | **0.53%** | 10.55 € |
| `momentum_based_zigzag` | **ZEAL.CO** | 1m | 1.68 | 2.26 | **0.52%** | 39.62 € |
| `hmm_regime_filter` | **mrkdeeur** | 30m | 1.55 | 1.43 | **0.51%** | 1.22 € |
| `hmm_regime_filter` | **mrkdeeur** | 45m | 1.75 | 1.43 | **0.51%** | 1.75 € |
| `hmm_regime_filter` | **acfreur** | 15m | 1.73 | 2.11 | **0.51%** | 0.97 € |
| `momentum_based_zigzag` | **belgbeeur** | 10m | 2.35 | 2.18 | **0.50%** | 0.42 € |
| `momentum_based_zigzag` | **vnadeeur** | 10m | 2.00 | 2.12 | **0.50%** | 1.03 € |
| `cybernetic_hilbert` | **ZEAL.CO** | 15m | 1.50 | 3.78 | **0.49%** | 69.42 € |
| `hmm_regime_filter` | **rifreur** | 10m | 1.60 | 1.52 | **0.47%** | 0.80 € |
| `smart_trader_geometric` | **ZEAL.CO** | 10m | 1.57 | 1.86 | **0.47%** | 13.01 € |
| `hmm_regime_filter` | **acfreur** | 10m | 1.64 | 2.01 | **0.46%** | 0.78 € |
| `hmm_regime_filter` | **NVO** | 15m | 1.51 | 1.49 | **0.45%** | 9.46 € |
| `hmm_regime_filter` | **rifreur** | 15m | 1.57 | 1.50 | **0.45%** | 0.75 € |
| `hmm_regime_filter` | **abibeeur** | 15m | 1.52 | 1.41 | **0.43%** | 0.74 € |
| `hmm_regime_filter` | **lxsdeeur** | 30m | 1.69 | 1.60 | **0.41%** | 0.92 € |
| `momentum_based_zigzag` | **cafreur** | 15m | 1.63 | 1.57 | **0.39%** | 0.38 € |


## Shortlist Ciblée (37 Configurations)

Extraction par meilleur Rendement Mensuel (€) absolu par combinaison Stratégie/Actif, pour un Paper-Trading concentré :

| Stratégie | Actif | Timeframe | Profit Factor | Sharpe | Kelly Weight | Rendement Mensuel (€) |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| `cybernetic_hilbert` | **ZEAL.CO** | 15m | 1.50 | 3.78 | **0.55%** | 69.42 € |
| `momentum_based_zigzag` | **ZEAL.CO** | 1m | 1.68 | 2.26 | **0.59%** | 39.62 € |
| `momentum_based_zigzag` | **NVO** | 45m | 2.60 | 1.89 | **0.73%** | 18.18 € |
| `smart_trader_geometric` | **ZEAL.CO** | 10m | 1.57 | 1.86 | **0.47%** | 13.01 € |
| `hmm_regime_filter` | **NVO** | 30m | 1.82 | 1.45 | **0.53%** | 10.55 € |
| `msl_trend` | **NVO** | 30m | 2.01 | 1.03 | **0.85%** | 9.97 € |
| `3commas_bot` | **GMAB** | 60m | 2.27 | 1.65 | **1.16%** | 8.78 € |
| `cybernetic_hilbert` | **dotusdt** | 60m | 1.65 | 2.24 | **0.57%** | 7.49 € |
| `3commas_bot` | **FPE.DE** | 20m | 1.94 | 1.15 | **0.87%** | 7.01 € |
| `adaptive_volatility_trend` | **dpwdeeur** | 45m | Inf | 1.22 | **3.02%** | 6.88 € |
| `3commas_bot` | **teniteur** | 30m | 2.78 | 1.08 | **1.45%** | 6.83 € |
| `range_filter` | **GMAB** | 20m | 2.05 | 2.18 | **0.62%** | 6.26 € |
| `adaptive_volatility_trend` | **GMAB** | 5m | 1.86 | 2.18 | **0.66%** | 5.94 € |
| `adaptive_volatility_trend` | **akzanleur** | 30m | Inf | 1.24 | **3.02%** | 5.65 € |
| `pmax_explorer` | **GMAB** | 30m | 1.84 | 1.70 | **0.58%** | 4.51 € |
| `hma_crossover` | **GMAB** | 45m | 1.95 | 1.84 | **0.70%** | 4.47 € |
| `momentum_based_zigzag` | **dotusdt** | 45m | 2.86 | 1.23 | **0.67%** | 4.10 € |
| `hma_crossover` | **FPE.DE** | 30m | 1.63 | 1.01 | **0.59%** | 2.89 € |
| `momentum_based_zigzag` | **daideeur** | 15m | 2.16 | 2.67 | **0.62%** | 2.70 € |
| `momentum_based_zigzag` | **SAP** | 30m | 5.53 | 1.13 | **1.43%** | 2.29 € |
| `hmm_regime_filter` | **mrkdeeur** | 45m | 1.75 | 1.43 | **0.51%** | 1.75 € |
| `momentum_based_zigzag` | **AMS.MC** | 10m | 2.86 | 1.86 | **0.69%** | 1.42 € |
| `momentum_based_zigzag` | **akzanleur** | 30m | 1.81 | 1.16 | **0.54%** | 1.40 € |
| `momentum_based_zigzag` | **vnadeeur** | 10m | 2.00 | 2.12 | **0.50%** | 1.03 € |
| `hmm_regime_filter` | **acfreur** | 15m | 1.73 | 2.11 | **0.51%** | 0.97 € |
| `hmm_regime_filter` | **lxsdeeur** | 30m | 1.69 | 1.60 | **0.41%** | 0.92 € |
| `momentum_based_zigzag` | **randnleur** | 10m | 2.47 | 1.16 | **1.11%** | 0.84 € |
| `hmm_regime_filter` | **rifreur** | 10m | 1.60 | 1.52 | **0.47%** | 0.80 € |
| `hmm_regime_filter` | **abibeeur** | 15m | 1.52 | 1.41 | **0.43%** | 0.74 € |
| `momentum_based_zigzag` | **GMAB** | 1m | 2.36 | 2.05 | **0.96%** | 0.66 € |
| `lorentzian_classification` | **GMAB** | 30m | 2.66 | 1.81 | **0.89%** | 0.49 € |
| `momentum_based_zigzag` | **belgbeeur** | 10m | 2.35 | 2.18 | **0.50%** | 0.42 € |
| `trend_type` | **NVS** | 15m | 2.04 | 1.12 | **0.86%** | 0.38 € |
| `momentum_based_zigzag` | **cafreur** | 15m | 1.63 | 1.57 | **0.39%** | 0.38 € |
| `momentum_based_zigzag` | **EVD.DE** | 45m | 3.58 | 1.96 | **1.03%** | 0.24 € |
| `lorentzian_classification` | **FPE.DE** | 120m | 2.68 | 1.03 | **1.02%** | 0.05 € |
