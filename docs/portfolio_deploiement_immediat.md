# Portfolio de Déploiement Immédiat

Ce document consigne la liste exacte des **37 setups** identifiés pour un déploiement en production ou en paper-trading actif, suite à la campagne globale d'optimisation et d'arbitrage.

### Critères de Sélection
Les setups ci-dessous cochent toutes les conditions de robustesse suivantes :
- **Profit Factor** > 1.5
- **Sharpe Ratio** > 1.0
- **Kelly Criterion** > 0 (pour garantir un avantage mathématique à l'allocation)
- **Rendement Mensuel Moyen (€)** > 0 (Générateur de profit brut justifiant le risque)

### Remarques Analytiques
- **`3commas_bot`** domine le portefeuille avec une excellente fréquence et de solides performances en euros.
- **`cybernetic_hilbert`** ressort extrêmement fort sur `ZEAL.CO` (nécessite une petite surveillance manuelle initiale pour écarter tout overfitting résiduel).
- **`momentum_based_zigzag`** et **`lorentzian_classification`** offrent d'excellents Profit Factors et des allocations Kelly élevées, parfaits pour la stabilité.

## Les 37 Setups Validés (Triés par Poids Kelly décroissant)

| Stratégie | Actif | Timeframe | Profit Factor | Sharpe | Kelly Weight | Rendement Mensuel (€) |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| `momentum_based_zigzag` | **SAP** | 30m | 5.53 | 1.37 | **2.26%** | 2.29 € |
| `3commas_bot` | **EVD.DE** | 30m | 2.87 | 2.27 | **1.93%** | 8.88 € |
| `3commas_bot` | **GMAB** | 60m | 2.27 | 1.82 | **1.80%** | 8.78 € |
| `momentum_based_zigzag` | **GMAB** | 1m | 2.36 | 1.07 | **1.70%** | 0.66 € |
| `3commas_bot` | **FPE.DE** | 45m | 1.96 | 2.57 | **1.68%** | 7.97 € |
| `trend_type` | **NVS** | 60m | 2.36 | 1.16 | **1.68%** | 0.44 € |
| `momentum_based_zigzag` | **EVD.DE** | 45m | 3.58 | 2.32 | **1.67%** | 0.24 € |
| `lorentzian_classification` | **FPE.DE** | 120m | 2.68 | 1.49 | **1.61%** | 0.05 € |
| `lorentzian_classification` | **GMAB** | 30m | 2.66 | 1.10 | **1.55%** | 0.49 € |
| `3commas_bot` | **EVD.DE** | 20m | 2.19 | 1.65 | **1.50%** | 6.35 € |
| `msl_trend` | **NVO** | 30m | 2.01 | 1.18 | **1.42%** | 9.97 € |
| `3commas_bot` | **FPE.DE** | 5m | 1.99 | 2.57 | **1.41%** | 5.17 € |
| `3commas_bot` | **GMAB** | 20m | 2.19 | 1.32 | **1.40%** | 5.65 € |
| `trend_type` | **NVS** | 15m | 2.04 | 1.31 | **1.36%** | 0.38 € |
| `3commas_bot` | **FPE.DE** | 20m | 1.94 | 1.83 | **1.36%** | 7.01 € |
| `3commas_bot` | **FPE.DE** | 30m | 1.81 | 2.22 | **1.30%** | 5.58 € |
| `trend_type` | **NVS** | 120m | 2.18 | 1.17 | **1.25%** | 0.48 € |
| `adaptive_volatility_trend` | **NVS** | 15m | 1.89 | 1.01 | **1.25%** | 3.15 € |
| `cybernetic_hilbert` | **ZEAL.CO** | 60m | 1.95 | 3.50 | **1.22%** | 54.35 € |
| `momentum_based_zigzag` | **SHL.DE** | 45m | 2.19 | 1.12 | **1.20%** | 2.11 € |
| `msl_trend` | **NVO** | 45m | 1.80 | 1.10 | **1.18%** | 9.21 € |
| `cybernetic_hilbert` | **ZEAL.CO** | 45m | 1.85 | 3.19 | **1.15%** | 56.73 € |
| `msl_trend` | **NVO** | 120m | 1.73 | 1.10 | **1.14%** | 8.64 € |
| `momentum_based_zigzag` | **AMS.MC** | 10m | 2.86 | 1.95 | **1.13%** | 1.42 € |
| `momentum_based_zigzag` | **NVO** | 45m | 2.60 | 2.47 | **1.07%** | 18.18 € |
| `hmm_regime_filter` | **NVO** | 45m | 2.21 | 1.43 | **1.05%** | 9.98 € |
| `adaptive_volatility_trend` | **GMAB** | 5m | 1.86 | 1.02 | **1.00%** | 5.94 € |
| `range_filter` | **GMAB** | 20m | 2.05 | 1.04 | **0.97%** | 6.26 € |
| `3commas_bot` | **GMAB** | 15m | 1.61 | 1.15 | **0.97%** | 5.70 € |
| `hmm_regime_filter` | **NVO** | 60m | 1.92 | 1.75 | **0.96%** | 10.42 € |
| `cybernetic_hilbert` | **ZEAL.CO** | 30m | 1.59 | 2.99 | **0.91%** | 55.00 € |
| `momentum_based_zigzag` | **ZEAL.CO** | 1m | 1.68 | 2.21 | **0.87%** | 39.62 € |
| `msl_trend` | **NVO** | 60m | 1.56 | 1.03 | **0.84%** | 9.45 € |
| `hmm_regime_filter` | **NVO** | 30m | 1.82 | 1.63 | **0.82%** | 10.55 € |
| `3commas_bot` | **GMAB** | 30m | 1.56 | 1.17 | **0.77%** | 5.49 € |
| `hmm_regime_filter` | **NVO** | 15m | 1.51 | 1.73 | **0.72%** | 9.46 € |
| `smart_trader_geometric` | **ZEAL.CO** | 10m | 1.57 | 2.22 | **0.69%** | 13.01 € |

## Shortlist Ciblée (9 Configurations)
Extraction par meilleur Rendement Mensuel (€) absolu par combinaison Stratégie/Actif, pour un Paper-Trading concentré :

| Stratégie | Actif | Timeframe | Profit Factor | Sharpe | Kelly Weight | Rendement Mensuel (€) |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: |
| `cybernetic_hilbert` | **ZEAL.CO** | 45m | 1.85 | 3.19 | **1.15%** | 56.73 € |
| `hmm_regime_filter` | **NVO** | 30m | 1.82 | 1.63 | **0.82%** | 10.55 € |
| `3commas_bot` | **EVD.DE** | 30m | 2.87 | 2.27 | **1.93%** | 8.88 € |
| `3commas_bot` | **GMAB** | 60m | 2.27 | 1.82 | **1.80%** | 8.78 € |
| `3commas_bot` | **FPE.DE** | 45m | 1.96 | 2.57 | **1.68%** | 7.97 € |
| `adaptive_volatility_trend` | **NVS** | 15m | 1.89 | 1.01 | **1.25%** | 3.15 € |
| `momentum_based_zigzag` | **SAP** | 30m | 5.53 | 1.37 | **2.26%** | 2.29 € |
| `momentum_based_zigzag` | **SHL.DE** | 45m | 2.19 | 1.12 | **1.20%** | 2.11 € |
| `momentum_based_zigzag` | **AMS.MC** | 10m | 2.86 | 1.95 | **1.13%** | 1.42 € |
