# Rapport d'Arbitrage et d'Optimisation des Stratégies

Ce rapport consolide les résultats d'optimisation et propose une modélisation d'allocation de capital.

## 1. Matrice Globale des Performances

| strategy                  | symbol    | timeframe   |   trades |   win_rate |   profit_factor |   mean_return |   max_drawdown |   sharpe |
|:--------------------------|:----------|:------------|---------:|-----------:|----------------:|--------------:|---------------:|---------:|
| adaptive_volatility_trend | dpwdeeur  | 45m         |       14 |       1.00 |          inf    |          0.20 |          -0.09 |     1.22 |
| adaptive_volatility_trend | telnonok  | 15m         |       11 |       1.00 |          inf    |          0.04 |          -0.13 |     0.57 |
| adaptive_volatility_trend | ergiteur  | 30m         |       12 |       1.00 |          inf    |          0.04 |          -0.11 |     0.51 |
| adaptive_volatility_trend | akzanleur | 30m         |       20 |       1.00 |          inf    |          0.10 |          -0.07 |     1.24 |
| adaptive_volatility_trend | beideeur  | 10m         |       14 |       1.00 |          inf    |          0.07 |          -0.08 |     0.70 |
| momentum_based_zigzag     | SAP       | 30m         |       69 |       0.58 |            5.53 |          0.04 |          -0.02 |     1.13 |
| momentum_based_zigzag     | dotusdt   | 30m         |       63 |       0.57 |            4.62 |          0.10 |          -0.02 |     0.43 |
| cybernetic_hilbert        | ethusdt   | 45m         |       91 |       0.25 |            4.35 |          0.01 |          -0.22 |     0.35 |
| 3commas_bot               | LOGI      | 10m         |      200 |       0.42 |            3.82 |          0.01 |          -0.17 |     0.63 |
| 3commas_bot               | LOGI      | 5m          |       98 |       0.30 |            3.70 |          0.02 |          -0.21 |     0.50 |
| momentum_based_zigzag     | EVD.DE    | 45m         |      143 |       0.48 |            3.58 |          0.01 |          -0.00 |     1.96 |
| momentum_based_zigzag     | beideeur  | 15m         |       52 |       0.48 |            3.47 |          0.02 |          -0.03 |     0.96 |
| momentum_based_zigzag     | LOGI      | 120m        |       54 |       0.46 |            3.41 |          0.04 |          -0.01 |     0.84 |
| adaptive_volatility_trend | NVS       | 60m         |       61 |       0.61 |            3.31 |          0.02 |          -0.05 |     0.69 |
| adaptive_volatility_trend | NVS       | 45m         |       64 |       0.58 |            3.12 |          0.02 |          -0.04 |     0.73 |
| 3commas_bot               | EVD.DE    | 30m         |      110 |       0.63 |            2.87 |          0.01 |          -0.05 |     1.00 |
| 3commas_bot               | LOGI      | 120m        |      120 |       0.62 |            2.87 |          0.02 |          -0.17 |     0.51 |
| momentum_based_zigzag     | AMS.MC    | 10m         |      479 |       0.35 |            2.86 |          0.01 |          -0.01 |     1.86 |
| momentum_based_zigzag     | dotusdt   | 45m         |     2308 |       0.37 |            2.86 |          0.01 |          -0.01 |     1.23 |
| 3commas_bot               | teniteur  | 30m         |       80 |       0.75 |            2.78 |          0.01 |          -0.07 |     1.08 |
| 3commas_bot               | LOGI      | 45m         |      123 |       0.50 |            2.78 |          0.02 |          -0.18 |     0.52 |
| cybernetic_hilbert        | ltcusdt   | 30m         |       99 |       0.21 |            2.77 |          0.01 |          -0.03 |     0.22 |
| lorentzian_classification | FPE.DE    | 120m        |       63 |       0.54 |            2.68 |          0.01 |          -0.00 |     1.03 |
| lorentzian_classification | GMAB      | 30m         |       51 |       0.47 |            2.66 |          0.03 |          -0.01 |     1.81 |
| msl_trend                 | NVS       | 240m        |       58 |       0.57 |            2.62 |          0.02 |          -0.02 |     0.50 |
| momentum_based_zigzag     | NVO       | 45m         |      734 |       0.38 |            2.60 |          0.00 |          -0.05 |     1.89 |
| momentum_based_zigzag     | randnleur | 10m         |       65 |       0.62 |            2.47 |          0.03 |          -0.02 |     1.16 |
| msl_trend                 | NVS       | 60m         |       79 |       0.58 |            2.46 |          0.01 |          -0.01 |     0.68 |
| hmm_regime_filter         | bnbusdt   | 60m         |     1798 |       0.44 |            2.46 |          0.01 |          -0.08 |     0.89 |
| cybernetic_hilbert        | aptusdt   | 10m         |      175 |       0.19 |            2.45 |          0.01 |          -0.00 |     0.46 |
| momentum_based_zigzag     | GMAB      | 1m          |       71 |       0.55 |            2.36 |          0.02 |          -0.01 |     2.05 |
| trend_type                | NVS       | 60m         |      149 |       0.60 |            2.36 |          0.00 |          -0.01 |     0.96 |
| momentum_based_zigzag     | belgbeeur | 10m         |      565 |       0.29 |            2.35 |          0.00 |          -0.00 |     2.18 |
| range_filter              | GMAB      | 30m         |       66 |       0.42 |            2.28 |          0.02 |          -0.07 |     2.11 |
| 3commas_bot               | GMAB      | 60m         |      130 |       0.68 |            2.27 |          0.02 |          -0.06 |     1.65 |
| cybernetic_hilbert        | dotusdt   | 45m         |       79 |       0.32 |            2.23 |          0.01 |          -0.01 |     0.11 |
| msl_trend                 | NVO       | 240m        |       54 |       0.52 |            2.23 |          0.02 |          -0.12 |     0.51 |
| hmm_regime_filter         | NVO       | 45m         |      435 |       0.41 |            2.21 |          0.00 |          -0.07 |     1.30 |
| momentum_based_zigzag     | ltcusdt   | 45m         |      718 |       0.28 |            2.20 |          0.01 |          -0.04 |     0.57 |
| 3commas_bot               | EVD.DE    | 20m         |      146 |       0.59 |            2.19 |          0.01 |          -0.06 |     0.90 |
| 3commas_bot               | GMAB      | 20m         |       98 |       0.57 |            2.19 |          0.01 |          -0.09 |     1.42 |
| momentum_based_zigzag     | SHL.DE    | 45m         |      207 |       0.48 |            2.19 |          0.01 |          -0.02 |     0.89 |
| trend_type                | NVS       | 120m        |      179 |       0.49 |            2.18 |          0.00 |          -0.01 |     0.80 |
| momentum_based_zigzag     | ltcusdt   | 30m         |      910 |       0.27 |            2.17 |          0.01 |          -0.06 |     0.70 |
| momentum_based_zigzag     | daideeur  | 15m         |     1563 |       0.38 |            2.16 |          0.00 |          -0.01 |     2.67 |
| msl_trend                 | NVS       | 10m         |       94 |       0.54 |            2.05 |          0.01 |          -0.01 |     0.58 |
| range_filter              | GMAB      | 20m         |       88 |       0.40 |            2.05 |          0.02 |          -0.08 |     2.18 |
| trend_type                | NVS       | 15m         |      331 |       0.56 |            2.04 |          0.00 |          -0.00 |     1.12 |
| trend_type                | NVS       | 30m         |      158 |       0.50 |            2.03 |          0.00 |          -0.01 |     0.86 |
| cybernetic_hilbert        | dotusdt   | 10m         |      246 |       0.18 |            2.02 |          0.01 |          -0.01 |     0.25 |
| msl_trend                 | NVO       | 30m         |      169 |       0.56 |            2.01 |          0.01 |          -0.14 |     1.03 |
| momentum_based_zigzag     | vnadeeur  | 10m         |      780 |       0.33 |            2.00 |          0.00 |          -0.01 |     2.12 |
| 3commas_bot               | FPE.DE    | 5m          |      255 |       0.60 |            1.99 |          0.00 |          -0.02 |     2.04 |
| trend_type                | NVO       | 60m         |      256 |       0.51 |            1.98 |          0.00 |          -0.08 |     0.82 |
| 3commas_bot               | FPE.DE    | 45m         |      192 |       0.72 |            1.96 |          0.01 |          -0.04 |     0.99 |
| cybernetic_hilbert        | ZEAL.CO   | 60m         |      990 |       0.51 |            1.95 |          0.00 |          -0.04 |     3.37 |
| hma_crossover             | GMAB      | 45m         |       96 |       0.47 |            1.95 |          0.01 |          -0.08 |     1.84 |
| 3commas_bot               | FPE.DE    | 20m         |      237 |       0.59 |            1.94 |          0.00 |          -0.04 |     1.15 |
| trend_type                | NVO       | 45m         |      199 |       0.53 |            1.92 |          0.00 |          -0.09 |     0.71 |
| hmm_regime_filter         | NVO       | 60m         |      643 |       0.43 |            1.92 |          0.00 |          -0.06 |     1.34 |
| hmm_regime_filter         | NVO       | 120m        |      330 |       0.48 |            1.91 |          0.00 |          -0.09 |     0.95 |
| adaptive_volatility_trend | NVS       | 15m         |      167 |       0.55 |            1.89 |          0.01 |          -0.05 |     0.82 |
| adaptive_volatility_trend | NVS       | 10m         |      159 |       0.57 |            1.88 |          0.01 |          -0.10 |     0.72 |
| adaptive_volatility_trend | GMAB      | 5m          |      144 |       0.47 |            1.86 |          0.01 |          -0.10 |     2.18 |
| cybernetic_hilbert        | ZEAL.CO   | 45m         |     1366 |       0.51 |            1.85 |          0.00 |          -0.06 |     3.36 |
| trend_type                | NVS       | 45m         |      239 |       0.54 |            1.84 |          0.00 |          -0.01 |     0.87 |
| msl_trend                 | NVS       | 120m        |      124 |       0.42 |            1.84 |          0.01 |          -0.01 |     0.66 |
| pmax_explorer             | GMAB      | 30m         |       72 |       0.42 |            1.84 |          0.02 |          -0.09 |     1.70 |
| hmm_regime_filter         | NVO       | 30m         |      761 |       0.39 |            1.82 |          0.00 |          -0.05 |     1.45 |
| 3commas_bot               | FPE.DE    | 30m         |      251 |       0.61 |            1.81 |          0.00 |          -0.03 |     1.05 |
| momentum_based_zigzag     | akzanleur | 30m         |      254 |       0.40 |            1.81 |          0.01 |          -0.03 |     1.16 |
| pmax_explorer             | GMAB      | 15m         |       70 |       0.44 |            1.80 |          0.02 |          -0.10 |     1.67 |
| msl_trend                 | NVO       | 45m         |      187 |       0.55 |            1.80 |          0.01 |          -0.14 |     0.88 |
| trend_type                | NVO       | 30m         |      311 |       0.51 |            1.79 |          0.00 |          -0.06 |     0.78 |
| momentum_based_zigzag     | NVS       | 5m          |      211 |       0.46 |            1.75 |          0.01 |          -0.02 |     0.85 |
| hmm_regime_filter         | mrkdeeur  | 45m         |      384 |       0.39 |            1.75 |          0.00 |          -0.02 |     1.43 |
| msl_trend                 | NVO       | 120m        |      179 |       0.53 |            1.73 |          0.01 |          -0.13 |     0.84 |
| hmm_regime_filter         | acfreur   | 15m         |     1296 |       0.40 |            1.73 |          0.00 |          -0.01 |     2.11 |
| hmm_regime_filter         | lxsdeeur  | 30m         |      892 |       0.33 |            1.69 |          0.00 |          -0.01 |     1.60 |
| range_filter              | FPE.DE    | 45m         |       56 |       0.46 |            1.68 |          0.01 |          -0.04 |     0.57 |
| momentum_based_zigzag     | ZEAL.CO   | 1m          |      524 |       0.43 |            1.68 |          0.01 |          -0.11 |     2.26 |
| cybernetic_hilbert        | dotusdt   | 60m         |    17534 |       0.51 |            1.65 |          0.00 |          -0.01 |     2.24 |
| hmm_regime_filter         | acfreur   | 10m         |     1483 |       0.39 |            1.64 |          0.00 |          -0.01 |     2.01 |
| momentum_based_zigzag     | cafreur   | 15m         |      821 |       0.33 |            1.63 |          0.00 |          -0.00 |     1.57 |
| hma_crossover             | FPE.DE    | 30m         |      142 |       0.51 |            1.63 |          0.00 |          -0.04 |     1.01 |
| 3commas_bot               | GMAB      | 15m         |      184 |       0.61 |            1.61 |          0.01 |          -0.12 |     1.21 |
| momentum_based_zigzag     | cpriteur  | 10m         |      125 |       0.41 |            1.61 |          0.01 |          -0.00 |     0.81 |
| hmm_regime_filter         | rifreur   | 10m         |      502 |       0.42 |            1.60 |          0.00 |          -0.05 |     1.52 |
| cybernetic_hilbert        | ZEAL.CO   | 30m         |     1990 |       0.48 |            1.59 |          0.00 |          -0.08 |     3.24 |
| momentum_based_zigzag     | FPE.DE    | 20m         |       99 |       0.38 |            1.58 |          0.00 |          -0.00 |     0.74 |
| hmm_regime_filter         | rifreur   | 15m         |      583 |       0.41 |            1.57 |          0.00 |          -0.04 |     1.50 |
| smart_trader_geometric    | ZEAL.CO   | 10m         |      820 |       0.42 |            1.57 |          0.00 |          -0.04 |     1.86 |
| momentum_based_zigzag     | vpknleur  | 15m         |      152 |       0.43 |            1.57 |          0.01 |          -0.02 |     0.78 |
| trend_type                | NVO       | 120m        |      266 |       0.50 |            1.57 |          0.00 |          -0.11 |     0.58 |
| hma_crossover             | NVS       | 120m        |      227 |       0.35 |            1.57 |          0.00 |          -0.05 |     0.57 |
| cybernetic_hilbert        | ltcusdt   | 45m         |    34612 |       0.51 |            1.56 |          0.00 |          -0.09 |     1.54 |
| msl_trend                 | NVO       | 60m         |      281 |       0.49 |            1.56 |          0.01 |          -0.10 |     0.86 |
| 3commas_bot               | GMAB      | 30m         |      197 |       0.55 |            1.56 |          0.01 |          -0.12 |     1.14 |
| hmm_regime_filter         | mrkdeeur  | 30m         |      758 |       0.48 |            1.55 |          0.00 |          -0.02 |     1.43 |
| hmm_regime_filter         | abibeeur  | 15m         |     1099 |       0.41 |            1.52 |          0.00 |          -0.01 |     1.41 |
| hmm_regime_filter         | NVO       | 15m         |     1762 |       0.44 |            1.51 |          0.00 |          -0.05 |     1.49 |
| cybernetic_hilbert        | ZEAL.CO   | 15m         |     4021 |       0.49 |            1.50 |          0.00 |          -0.04 |     3.78 |
| 3commas_bot               | EVD.DE    | 5m          |      593 |       0.48 |            1.47 |          0.00 |          -0.05 |     1.14 |
| cybernetic_hilbert        | ZEAL.CO   | 20m         |     2994 |       0.48 |            1.47 |          0.00 |          -0.04 |     2.90 |
| hmm_regime_filter         | diaiteur  | 30m         |      779 |       0.33 |            1.46 |          0.00 |          -0.03 |     1.32 |
| hmm_regime_filter         | abibeeur  | 10m         |     1379 |       0.40 |            1.46 |          0.00 |          -0.01 |     1.30 |
| trend_type                | NVS       | 20m         |      549 |       0.54 |            1.45 |          0.00 |          -0.01 |     0.68 |
| hmm_regime_filter         | diaiteur  | 15m         |     1338 |       0.39 |            1.45 |          0.00 |          -0.02 |     1.87 |
| hmm_regime_filter         | mrkdeeur  | 15m         |     1214 |       0.44 |            1.43 |          0.00 |          -0.02 |     1.43 |
| lorentzian_classification | NVO       | 20m         |     1157 |       0.44 |            1.42 |          0.00 |          -0.08 |     1.19 |
| hmm_regime_filter         | abibeeur  | 45m         |      959 |       0.39 |            1.42 |          0.00 |          -0.01 |     1.07 |
| msl_trend                 | AMS.MC    | 120m        |       79 |       0.32 |            1.42 |          0.01 |          -0.02 |     0.40 |
| trend_type                | NVO       | 20m         |     1003 |       0.52 |            1.40 |          0.00 |          -0.07 |     0.94 |
| msl_trend                 | NVO       | 20m         |      891 |       0.39 |            1.40 |          0.00 |          -0.11 |     1.07 |
| range_filter              | FPE.DE    | 240m        |       66 |       0.44 |            1.39 |         -0.00 |          -0.08 |     0.32 |
| msl_trend                 | NVO       | 15m         |      942 |       0.39 |            1.38 |          0.00 |          -0.08 |     1.07 |
| hmm_regime_filter         | mrkdeeur  | 10m         |     1278 |       0.43 |            1.38 |          0.00 |          -0.02 |     1.34 |
| hmm_regime_filter         | diaiteur  | 10m         |     1759 |       0.40 |            1.38 |          0.00 |          -0.02 |     1.78 |
| smart_trader_geometric    | ZEAL.CO   | 5m          |     2141 |       0.44 |            1.38 |          0.00 |          -0.01 |     1.33 |
| msl_trend                 | NVO       | 10m         |     1088 |       0.37 |            1.37 |          0.00 |          -0.08 |     1.05 |
| noise_boundary_intraday   | AMS.MC    | 120m        |      643 |       0.56 |            1.36 |          3.75 |          -0.23 |     0.79 |
| noise_boundary_intraday   | FPE.DE    | 120m        |      274 |       0.51 |            1.36 |          2.14 |          -0.16 |     0.87 |
| cybernetic_hilbert        | NVO       | 45m         |     3703 |       0.50 |            1.36 |          0.00 |          -0.07 |     1.73 |
| trend_type                | NVO       | 10m         |     1804 |       0.48 |            1.35 |          0.00 |          -0.06 |     1.06 |
| hmm_regime_filter         | NVO       | 20m         |     2144 |       0.43 |            1.34 |          0.00 |          -0.07 |     1.13 |
| msl_trend                 | AMS.MC    | 20m         |      634 |       0.45 |            1.33 |          0.00 |          -0.02 |     0.83 |
| noise_boundary_intraday   | GMAB      | 30m         |      385 |       0.50 |            1.32 |          1.49 |          -0.23 |     1.45 |
| msl_trend                 | AMS.MC    | 10m         |      728 |       0.42 |            1.32 |          0.00 |          -0.02 |     0.88 |
| msl_trend                 | AMS.MC    | 15m         |      663 |       0.45 |            1.31 |          0.00 |          -0.02 |     0.84 |
| trend_type                | NVO       | 15m         |     1200 |       0.51 |            1.31 |          0.00 |          -0.10 |     0.80 |
| msl_trend                 | AMS.MC    | 45m         |      633 |       0.44 |            1.31 |          0.00 |          -0.02 |     0.83 |
| noise_boundary_intraday   | AMS.MC    | 60m         |      584 |       0.55 |            1.31 |          4.75 |          -0.24 |     0.72 |
| msl_trend                 | AMS.MC    | 60m         |       58 |       0.52 |            1.30 |          0.01 |          -0.02 |     0.24 |
| cybernetic_hilbert        | mrkdeeur  | 45m         |     3562 |       0.51 |            1.30 |          0.00 |          -0.03 |     1.69 |
| hmm_regime_filter         | NVO       | 10m         |     2178 |       0.40 |            1.29 |          0.00 |          -0.07 |     1.07 |
| smart_trader_geometric    | LOGI      | 5m          |     2774 |       0.44 |            1.29 |          0.00 |          -0.01 |     0.74 |
| cybernetic_hilbert        | lxsdeeur  | 60m         |     2927 |       0.50 |            1.29 |          0.00 |          -0.02 |     1.43 |
| msl_trend                 | AMS.MC    | 30m         |      722 |       0.42 |            1.28 |          0.00 |          -0.02 |     0.85 |

## 2. Performances Absolues et Fréquence de Trading

| strategy                  | symbol    | timeframe   |   duration_years |   net_pnl_currency |   max_dd_currency |   trades_per_month |   trades_per_year |
|:--------------------------|:----------|:------------|-----------------:|-------------------:|------------------:|-------------------:|------------------:|
| adaptive_volatility_trend | dpwdeeur  | 45m         |             9.17 |             822.82 |           -108.60 |               0.13 |              1.53 |
| adaptive_volatility_trend | telnonok  | 15m         |             7.62 |             133.74 |           -129.18 |               0.12 |              1.44 |
| adaptive_volatility_trend | ergiteur  | 30m         |             4.85 |             150.77 |           -122.03 |               0.21 |              2.47 |
| adaptive_volatility_trend | akzanleur | 30m         |             8.68 |             603.80 |            -99.00 |               0.19 |              2.30 |
| adaptive_volatility_trend | beideeur  | 10m         |            10.35 |             278.15 |           -104.55 |               0.11 |              1.35 |
| momentum_based_zigzag     | SAP       | 30m         |            10.60 |             296.39 |            -26.61 |               0.54 |              6.51 |
| momentum_based_zigzag     | dotusdt   | 30m         |             5.15 |             112.57 |            -22.30 |               1.02 |             12.23 |
| cybernetic_hilbert        | ethusdt   | 45m         |             8.26 |            2454.76 |           -591.06 |               0.92 |             11.02 |
| 3commas_bot               | LOGI      | 10m         |            10.52 |             865.02 |           -276.06 |               1.58 |             19.01 |
| 3commas_bot               | LOGI      | 5m          |             6.99 |             504.24 |           -385.26 |               1.17 |             14.02 |
| momentum_based_zigzag     | EVD.DE    | 45m         |             2.91 |               8.45 |             -0.57 |               4.09 |             49.14 |
| momentum_based_zigzag     | beideeur  | 15m         |            10.65 |             123.75 |            -29.99 |               0.41 |              4.88 |
| momentum_based_zigzag     | LOGI      | 120m        |            10.05 |              88.65 |            -15.78 |               0.45 |              5.37 |
| adaptive_volatility_trend | NVS       | 60m         |            10.19 |             303.09 |            -54.45 |               0.50 |              5.99 |
| adaptive_volatility_trend | NVS       | 45m         |            10.37 |             313.62 |            -38.93 |               0.51 |              6.17 |
| 3commas_bot               | EVD.DE    | 30m         |             2.84 |             314.50 |            -58.65 |               3.23 |             38.78 |
| 3commas_bot               | LOGI      | 120m        |            10.35 |             728.28 |           -277.52 |               0.96 |             11.59 |
| momentum_based_zigzag     | AMS.MC    | 10m         |             9.02 |             154.13 |             -6.22 |               4.42 |             53.08 |
| momentum_based_zigzag     | dotusdt   | 45m         |             5.52 |             271.44 |             -7.42 |              34.80 |            418.15 |
| 3commas_bot               | teniteur  | 30m         |             3.38 |             283.09 |            -79.43 |               1.97 |             23.68 |
| 3commas_bot               | LOGI      | 45m         |            10.37 |             762.02 |           -299.27 |               0.99 |             11.87 |
| cybernetic_hilbert        | ltcusdt   | 30m         |             7.99 |              80.00 |            -28.81 |               1.03 |             12.39 |
| lorentzian_classification | FPE.DE    | 120m        |             2.90 |               1.89 |             -0.44 |               1.81 |             21.75 |
| lorentzian_classification | GMAB      | 30m         |             5.68 |              33.56 |             -8.61 |               0.75 |              8.98 |
| msl_trend                 | NVS       | 240m        |            10.13 |              83.03 |            -19.59 |               0.48 |              5.73 |
| momentum_based_zigzag     | NVO       | 45m         |             9.11 |            1977.43 |           -110.21 |               6.70 |             80.56 |
| momentum_based_zigzag     | randnleur | 10m         |             7.88 |              83.97 |            -22.08 |               0.69 |              8.25 |
| msl_trend                 | NVS       | 60m         |            10.29 |              90.98 |            -12.57 |               0.64 |              7.68 |
| hmm_regime_filter         | bnbusdt   | 60m         |             8.30 |            2622.39 |           -157.58 |              18.02 |            216.52 |
| cybernetic_hilbert        | aptusdt   | 10m         |             3.27 |               8.88 |             -1.66 |               4.45 |             53.44 |
| momentum_based_zigzag     | GMAB      | 1m          |             5.69 |              45.12 |            -13.62 |               1.04 |             12.49 |
| trend_type                | NVS       | 60m         |            10.44 |              54.80 |             -8.52 |               1.19 |             14.27 |
| momentum_based_zigzag     | belgbeeur | 10m         |             8.21 |              41.42 |             -1.78 |               5.73 |             68.81 |
| range_filter              | GMAB      | 30m         |             5.79 |             434.62 |            -95.76 |               0.95 |             11.41 |
| 3commas_bot               | GMAB      | 60m         |             5.74 |             617.45 |            -93.99 |               1.88 |             22.63 |
| cybernetic_hilbert        | dotusdt   | 45m         |             5.35 |               6.51 |             -6.01 |               1.23 |             14.77 |
| msl_trend                 | NVO       | 240m        |             8.49 |             724.22 |           -229.06 |               0.53 |              6.36 |
| hmm_regime_filter         | NVO       | 45m         |             9.05 |            1088.80 |           -143.81 |               4.00 |             48.06 |
| momentum_based_zigzag     | ltcusdt   | 45m         |             8.20 |             964.10 |            -56.66 |               7.29 |             87.59 |
| 3commas_bot               | EVD.DE    | 20m         |             2.87 |             244.28 |            -61.27 |               4.23 |             50.84 |
| 3commas_bot               | GMAB      | 20m         |             5.54 |             390.00 |           -122.56 |               1.47 |             17.70 |
| momentum_based_zigzag     | SHL.DE    | 45m         |            10.68 |             269.61 |            -25.18 |               1.61 |             19.39 |
| trend_type                | NVS       | 120m        |            10.44 |              60.52 |             -9.47 |               1.43 |             17.14 |
| momentum_based_zigzag     | ltcusdt   | 30m         |             8.20 |            1215.38 |            -75.71 |               9.24 |            110.98 |
| momentum_based_zigzag     | daideeur  | 15m         |            10.72 |             347.86 |            -12.41 |              12.14 |            145.82 |
| msl_trend                 | NVS       | 10m         |            10.47 |              71.51 |            -12.67 |               0.75 |              8.98 |
| range_filter              | GMAB      | 20m         |             5.78 |             434.20 |           -100.79 |               1.27 |             15.22 |
| trend_type                | NVS       | 15m         |            10.49 |              47.87 |             -4.32 |               2.63 |             31.54 |
| trend_type                | NVS       | 30m         |            10.40 |              38.78 |             -7.45 |               1.26 |             15.19 |
| cybernetic_hilbert        | dotusdt   | 10m         |             5.52 |              16.80 |             -8.61 |               3.71 |             44.59 |
| msl_trend                 | NVO       | 30m         |             9.05 |            1076.77 |           -290.07 |               1.55 |             18.68 |
| momentum_based_zigzag     | vnadeeur  | 10m         |            10.67 |             126.17 |            -11.51 |               6.09 |             73.12 |
| 3commas_bot               | FPE.DE    | 5m          |             2.97 |             199.11 |            -23.39 |               7.15 |             85.92 |
| trend_type                | NVO       | 60m         |             9.10 |             645.09 |            -91.09 |               2.34 |             28.15 |
| 3commas_bot               | FPE.DE    | 45m         |             2.97 |             281.32 |            -45.23 |               5.39 |             64.75 |
| cybernetic_hilbert        | ZEAL.CO   | 60m         |             2.99 |            1919.30 |            -89.00 |              27.59 |            331.44 |
| hma_crossover             | GMAB      | 45m         |             5.55 |             308.60 |           -107.18 |               1.44 |             17.31 |
| 3commas_bot               | FPE.DE    | 20m         |             2.97 |             257.17 |            -43.43 |               6.65 |             79.93 |
| trend_type                | NVO       | 45m         |             9.10 |             554.09 |            -98.20 |               1.82 |             21.88 |
| hmm_regime_filter         | NVO       | 60m         |             9.10 |            1137.49 |           -112.99 |               5.88 |             70.65 |
| hmm_regime_filter         | NVO       | 120m        |             9.02 |             734.74 |           -134.61 |               3.05 |             36.59 |
| adaptive_volatility_trend | NVS       | 15m         |            10.49 |             393.96 |            -59.08 |               1.32 |             15.92 |
| adaptive_volatility_trend | NVS       | 10m         |            10.50 |             337.47 |           -105.96 |               1.26 |             15.14 |
| adaptive_volatility_trend | GMAB      | 5m          |             5.78 |             410.58 |           -135.29 |               2.07 |             24.90 |
| cybernetic_hilbert        | ZEAL.CO   | 45m         |             2.99 |            2039.15 |           -163.00 |              38.06 |            457.32 |
| trend_type                | NVS       | 45m         |            10.46 |              52.36 |             -8.08 |               1.90 |             22.85 |
| msl_trend                 | NVS       | 120m        |            10.15 |              86.65 |            -13.12 |               1.02 |             12.21 |
| pmax_explorer             | GMAB      | 30m         |             5.63 |             311.00 |           -112.25 |               1.06 |             12.78 |
| hmm_regime_filter         | NVO       | 30m         |             9.12 |            1149.25 |            -96.95 |               6.95 |             83.44 |
| 3commas_bot               | FPE.DE    | 30m         |             2.97 |             205.54 |            -34.79 |               7.04 |             84.57 |
| momentum_based_zigzag     | akzanleur | 30m         |             9.07 |             133.51 |            -27.86 |               2.33 |             28.02 |
| pmax_explorer             | GMAB      | 15m         |             5.57 |             308.07 |           -131.54 |               1.05 |             12.56 |
| msl_trend                 | NVO       | 45m         |             9.06 |            1002.73 |           -279.50 |               1.72 |             20.65 |
| trend_type                | NVO       | 30m         |             9.09 |             542.37 |            -76.13 |               2.85 |             34.21 |
| momentum_based_zigzag     | NVS       | 5m          |            10.47 |             107.32 |            -24.77 |               1.68 |             20.15 |
| hmm_regime_filter         | mrkdeeur  | 45m         |            10.38 |             216.24 |            -25.70 |               3.08 |             36.98 |
| msl_trend                 | NVO       | 120m        |             9.04 |             934.68 |           -269.04 |               1.65 |             19.80 |
| hmm_regime_filter         | acfreur   | 15m         |             7.65 |              88.56 |             -6.76 |              14.11 |            169.48 |
| hmm_regime_filter         | lxsdeeur  | 30m         |            10.66 |             119.79 |            -14.59 |               6.97 |             83.69 |
| range_filter              | FPE.DE    | 45m         |             2.75 |              89.64 |            -46.55 |               1.70 |             20.39 |
| momentum_based_zigzag     | ZEAL.CO   | 1m          |             2.99 |            1403.55 |           -225.40 |              14.59 |            175.27 |
| cybernetic_hilbert        | dotusdt   | 60m         |             5.52 |             496.66 |            -13.36 |             264.27 |           3175.16 |
| hmm_regime_filter         | acfreur   | 10m         |             7.65 |              71.32 |             -5.82 |              16.14 |            193.94 |
| momentum_based_zigzag     | cafreur   | 15m         |             9.18 |              41.24 |             -4.95 |               7.44 |             89.43 |
| hma_crossover             | FPE.DE    | 30m         |             2.91 |             101.33 |            -41.13 |               4.06 |             48.75 |
| 3commas_bot               | GMAB      | 15m         |             5.78 |             404.16 |           -174.72 |               2.65 |             31.82 |
| momentum_based_zigzag     | cpriteur  | 10m         |             4.91 |               8.02 |             -4.07 |               2.12 |             25.45 |
| hmm_regime_filter         | rifreur   | 10m         |             9.36 |             156.76 |            -52.55 |               4.47 |             53.66 |
| cybernetic_hilbert        | ZEAL.CO   | 30m         |             2.99 |            1946.05 |           -199.50 |              55.45 |            666.22 |
| momentum_based_zigzag     | FPE.DE    | 20m         |             2.95 |               1.32 |             -0.55 |               2.79 |             33.51 |
| hmm_regime_filter         | rifreur   | 15m         |             9.36 |             153.71 |            -42.04 |               5.19 |             62.32 |
| smart_trader_geometric    | ZEAL.CO   | 10m         |             2.99 |             453.30 |            -52.20 |              22.85 |            274.52 |
| momentum_based_zigzag     | vpknleur  | 15m         |             9.05 |              41.84 |            -21.26 |               1.40 |             16.79 |
| trend_type                | NVO       | 120m        |             9.03 |             469.88 |           -165.74 |               2.45 |             29.44 |
| hma_crossover             | NVS       | 120m        |            10.29 |             248.19 |            -54.89 |               1.84 |             22.06 |
| cybernetic_hilbert        | ltcusdt   | 45m         |             8.21 |            5934.27 |           -103.32 |             351.09 |           4218.23 |
| msl_trend                 | NVO       | 60m         |             9.06 |            1014.11 |           -175.58 |               2.58 |             31.03 |
| 3commas_bot               | GMAB      | 30m         |             5.76 |             378.61 |           -185.12 |               2.85 |             34.20 |
| hmm_regime_filter         | mrkdeeur  | 30m         |            10.39 |             143.99 |            -17.87 |               6.07 |             72.95 |
| hmm_regime_filter         | abibeeur  | 15m         |             9.07 |              81.03 |             -5.93 |              10.09 |            121.24 |
| hmm_regime_filter         | NVO       | 15m         |             9.12 |            1034.83 |            -92.42 |              16.08 |            193.21 |
| cybernetic_hilbert        | ZEAL.CO   | 15m         |             2.99 |            2454.55 |           -110.00 |             111.94 |           1344.94 |
| 3commas_bot               | EVD.DE    | 5m          |             2.97 |             299.39 |            -65.52 |              16.60 |            199.44 |
| cybernetic_hilbert        | ZEAL.CO   | 20m         |             2.99 |            2034.15 |            -93.00 |              83.35 |           1001.43 |
| hmm_regime_filter         | diaiteur  | 30m         |             5.00 |             131.26 |            -36.40 |              12.97 |            155.82 |
| hmm_regime_filter         | abibeeur  | 10m         |             9.07 |              80.70 |             -9.50 |              12.66 |            152.08 |
| trend_type                | NVS       | 20m         |            10.50 |              33.29 |             -8.95 |               4.35 |             52.30 |
| hmm_regime_filter         | diaiteur  | 15m         |             5.00 |             178.00 |            -22.57 |              22.26 |            267.49 |
| hmm_regime_filter         | mrkdeeur  | 15m         |            10.39 |             144.72 |            -24.31 |               9.72 |            116.84 |
| lorentzian_classification | NVO       | 20m         |             9.10 |            1400.87 |           -150.98 |              10.58 |            127.17 |
| hmm_regime_filter         | abibeeur  | 45m         |             9.07 |              62.56 |            -10.25 |               8.81 |            105.79 |
| msl_trend                 | AMS.MC    | 120m        |             5.45 |              30.90 |            -15.61 |               1.21 |             14.51 |
| trend_type                | NVO       | 20m         |             9.12 |             662.51 |           -111.67 |               9.15 |            109.98 |
| msl_trend                 | NVO       | 20m         |             9.08 |            1066.39 |           -238.07 |               8.17 |             98.17 |
| range_filter              | FPE.DE    | 240m        |             2.88 |             -41.67 |            -78.53 |               1.91 |             22.91 |
| msl_trend                 | NVO       | 15m         |             9.08 |            1074.82 |           -171.96 |               8.64 |            103.79 |
| hmm_regime_filter         | mrkdeeur  | 10m         |            10.39 |             128.21 |            -17.44 |              10.24 |            123.00 |
| hmm_regime_filter         | diaiteur  | 10m         |             5.00 |             160.64 |            -26.16 |              29.27 |            351.66 |
| smart_trader_geometric    | ZEAL.CO   | 5m          |             2.99 |              85.71 |             -8.74 |              59.66 |            716.77 |
| msl_trend                 | NVO       | 10m         |             9.08 |            1075.79 |           -170.09 |               9.97 |            119.77 |
| noise_boundary_intraday   | AMS.MC    | 120m        |             0.00 |            2408.62 |           -535.63 |               0.00 |              0.00 |
| noise_boundary_intraday   | FPE.DE    | 120m        |             0.00 |             586.78 |           -280.33 |               0.00 |              0.00 |
| cybernetic_hilbert        | NVO       | 45m         |             9.12 |            1936.81 |           -148.05 |              33.78 |            405.92 |
| trend_type                | NVO       | 10m         |             9.12 |             785.07 |            -96.91 |              16.46 |            197.81 |
| hmm_regime_filter         | NVO       | 20m         |             9.12 |             871.08 |           -127.83 |              19.57 |            235.09 |
| msl_trend                 | AMS.MC    | 20m         |             5.79 |              80.87 |            -17.91 |               9.11 |            109.49 |
| noise_boundary_intraday   | GMAB      | 30m         |             0.00 |             572.41 |           -274.13 |               0.00 |              0.00 |
| msl_trend                 | AMS.MC    | 10m         |             5.79 |              80.80 |            -21.13 |              10.46 |            125.72 |
| msl_trend                 | AMS.MC    | 15m         |             5.79 |              78.70 |            -20.20 |               9.53 |            114.50 |
| trend_type                | NVO       | 15m         |             9.12 |             603.72 |           -148.08 |              10.95 |            131.58 |
| msl_trend                 | AMS.MC    | 45m         |             5.79 |              74.34 |            -18.80 |               9.10 |            109.32 |
| noise_boundary_intraday   | AMS.MC    | 60m         |             0.00 |            2771.70 |           -868.26 |               0.00 |              0.00 |
| msl_trend                 | AMS.MC    | 60m         |             5.67 |              21.70 |            -18.28 |               0.85 |             10.23 |
| cybernetic_hilbert        | mrkdeeur  | 45m         |            10.39 |             401.35 |            -33.98 |              28.54 |            342.92 |
| hmm_regime_filter         | NVO       | 10m         |             9.12 |             737.19 |           -129.44 |              19.88 |            238.82 |
| smart_trader_geometric    | LOGI      | 5m          |            10.37 |              44.42 |             -7.60 |              22.26 |            267.48 |
| cybernetic_hilbert        | lxsdeeur  | 60m         |            10.66 |             161.80 |            -18.04 |              22.86 |            274.62 |
| msl_trend                 | AMS.MC    | 30m         |             5.79 |              71.25 |            -21.20 |              10.38 |            124.69 |

## 3. Estimations de Rendement Périodique (Moyenne)

| strategy                  | symbol    | timeframe   | monthly (%)   | quarterly (%)   | semi (%)   | yearly (%)   | monthly (€)   | quarterly (€)   | semi (€)   | yearly (€)   |
|:--------------------------|:----------|:------------|:--------------|:----------------|:-----------|:-------------|:--------------|:----------------|:-----------|:-------------|
| adaptive_volatility_trend | dpwdeeur  | 45m         | 0.53%         | 1.62%           | 3.08%      | 7.00%        | 6.88 €        | 23.07 €         | 41.73 €    | 91.81 €      |
| adaptive_volatility_trend | telnonok  | 15m         | 0.10%         | 0.31%           | 0.57%      | 1.33%        | 1.20 €        | 1.50 €          | 3.63 €     | 10.86 €      |
| adaptive_volatility_trend | ergiteur  | 30m         | 0.26%         | 0.75%           | 1.47%      | 2.94%        | 3.21 €        | 9.64 €          | 15.27 €    | 30.54 €      |
| adaptive_volatility_trend | akzanleur | 30m         | 0.45%         | 1.37%           | 2.60%      | 5.67%        | 5.65 €        | 14.75 €         | 30.70 €    | 52.46 €      |
| adaptive_volatility_trend | beideeur  | 10m         | 0.18%         | 0.57%           | 1.05%      | 2.11%        | 2.32 €        | 6.02 €          | 11.42 €    | 22.91 €      |
| momentum_based_zigzag     | SAP       | 30m         | 0.20%         | 0.62%           | 1.19%      | 2.44%        | 2.29 €        | 7.05 €          | 13.35 €    | 27.67 €      |
| momentum_based_zigzag     | dotusdt   | 30m         | 0.16%         | 0.48%           | 0.99%      | 1.75%        | 1.71 €        | 5.01 €          | 10.27 €    | 17.87 €      |
| cybernetic_hilbert        | ethusdt   | 45m         | 1.34%         | 4.10%           | 8.45%      | 18.04%       | 24.07 €       | 72.20 €         | 144.40 €   | 275.98 €     |
| 3commas_bot               | LOGI      | 10m         | 0.51%         | 1.55%           | 3.14%      | 5.69%        | 11.23 €       | 31.03 €         | 59.24 €    | 102.14 €     |
| 3commas_bot               | LOGI      | 5m          | 0.46%         | 1.38%           | 2.79%      | 5.49%        | 9.31 €        | 20.78 €         | 39.67 €    | 70.66 €      |
| momentum_based_zigzag     | EVD.DE    | 45m         | 0.02%         | 0.07%           | 0.14%      | 0.29%        | 0.24 €        | 0.72 €          | 1.38 €     | 2.95 €       |
| momentum_based_zigzag     | beideeur  | 15m         | 0.09%         | 0.28%           | 0.54%      | 1.07%        | 1.04 €        | 2.97 €          | 5.65 €     | 11.25 €      |
| momentum_based_zigzag     | LOGI      | 120m        | 0.07%         | 0.21%           | 0.41%      | 0.85%        | 1.42 €        | 3.29 €          | 6.28 €     | 10.88 €      |
| adaptive_volatility_trend | NVS       | 60m         | 0.21%         | 0.64%           | 1.28%      | 2.87%        | 2.41 €        | 7.22 €          | 14.43 €    | 31.84 €      |
| adaptive_volatility_trend | NVS       | 45m         | 0.22%         | 0.66%           | 1.32%      | 2.95%        | 2.49 €        | 7.47 €          | 14.93 €    | 32.91 €      |
| 3commas_bot               | EVD.DE    | 30m         | 0.79%         | 2.42%           | 4.66%      | 9.55%        | 8.88 €        | 27.29 €         | 51.81 €    | 108.86 €     |
| 3commas_bot               | LOGI      | 120m        | 0.45%         | 1.36%           | 2.74%      | 5.43%        | 8.91 €        | 24.42 €         | 46.62 €    | 86.34 €      |
| momentum_based_zigzag     | AMS.MC    | 10m         | 0.13%         | 0.40%           | 0.79%      | 1.59%        | 1.42 €        | 4.24 €          | 8.50 €     | 16.97 €      |
| momentum_based_zigzag     | dotusdt   | 45m         | 0.36%         | 1.09%           | 2.23%      | 4.14%        | 4.10 €        | 12.16 €         | 24.58 €    | 44.00 €      |
| 3commas_bot               | teniteur  | 30m         | 0.61%         | 1.79%           | 3.60%      | 6.42%        | 6.83 €        | 20.01 €         | 40.02 €    | 70.03 €      |
| 3commas_bot               | LOGI      | 45m         | 0.48%         | 1.43%           | 2.87%      | 5.66%        | 8.89 €        | 25.42 €         | 48.53 €    | 89.74 €      |
| cybernetic_hilbert        | ltcusdt   | 30m         | 0.08%         | 0.24%           | 0.46%      | 0.87%        | 0.82 €        | 2.42 €          | 4.71 €     | 8.89 €       |
| lorentzian_classification | FPE.DE    | 120m        | 0.01%         | 0.02%           | 0.03%      | 0.09%        | 0.05 €        | 0.16 €          | 0.31 €     | 0.89 €       |
| lorentzian_classification | GMAB      | 30m         | 0.05%         | 0.13%           | 0.28%      | 0.36%        | 0.49 €        | 1.32 €          | 2.80 €     | 3.64 €       |
| msl_trend                 | NVS       | 240m        | 0.07%         | 0.21%           | 0.42%      | 0.89%        | 0.72 €        | 2.15 €          | 4.30 €     | 9.24 €       |
| momentum_based_zigzag     | NVO       | 45m         | 1.02%         | 3.11%           | 6.02%      | 13.13%       | 18.18 €       | 54.89 €         | 104.29 €   | 219.54 €     |
| momentum_based_zigzag     | randnleur | 10m         | 0.08%         | 0.24%           | 0.48%      | 0.97%        | 0.84 €        | 2.51 €          | 4.99 €     | 10.03 €      |
| msl_trend                 | NVS       | 60m         | 0.07%         | 0.21%           | 0.42%      | 0.88%        | 0.73 €        | 2.20 €          | 4.40 €     | 9.14 €       |
| hmm_regime_filter         | bnbusdt   | 60m         | 1.33%         | 4.09%           | 8.22%      | 16.88%       | 26.49 €       | 79.39 €         | 154.25 €   | 291.10 €     |
| cybernetic_hilbert        | aptusdt   | 10m         | 0.02%         | 0.07%           | 0.13%      | 0.22%        | 0.22 €        | 0.67 €          | 1.27 €     | 2.18 €       |
| momentum_based_zigzag     | GMAB      | 1m          | 0.06%         | 0.19%           | 0.37%      | 0.71%        | 0.66 €        | 1.98 €          | 3.77 €     | 7.24 €       |
| trend_type                | NVS       | 60m         | 0.04%         | 0.13%           | 0.26%      | 0.53%        | 0.44 €        | 1.32 €          | 2.65 €     | 5.46 €       |
| momentum_based_zigzag     | belgbeeur | 10m         | 0.04%         | 0.13%           | 0.24%      | 0.51%        | 0.42 €        | 1.30 €          | 2.43 €     | 5.18 €       |
| range_filter              | GMAB      | 30m         | 0.54%         | 1.35%           | 3.24%      | 3.28%        | 6.25 €        | 15.87 €         | 35.95 €    | 41.71 €      |
| 3commas_bot               | GMAB      | 60m         | 0.70%         | 2.05%           | 4.07%      | 6.47%        | 8.78 €        | 25.80 €         | 50.49 €    | 84.96 €      |
| cybernetic_hilbert        | dotusdt   | 45m         | 0.01%         | 0.03%           | 0.06%      | 0.11%        | 0.10 €        | 0.29 €          | 0.59 €     | 1.07 €       |
| msl_trend                 | NVO       | 240m        | 0.54%         | 1.60%           | 3.12%      | 6.54%        | 6.69 €        | 20.26 €         | 38.39 €    | 81.04 €      |
| hmm_regime_filter         | NVO       | 45m         | 0.69%         | 2.08%           | 4.04%      | 8.71%        | 9.98 €        | 30.02 €         | 57.28 €    | 120.08 €     |
| momentum_based_zigzag     | ltcusdt   | 45m         | 0.69%         | 2.06%           | 4.07%      | 7.91%        | 9.61 €        | 28.55 €         | 55.43 €    | 104.69 €     |
| 3commas_bot               | EVD.DE    | 20m         | 0.58%         | 1.67%           | 3.42%      | 8.87%        | 6.35 €        | 18.31 €         | 37.04 €    | 96.28 €      |
| 3commas_bot               | GMAB      | 20m         | 0.49%         | 1.38%           | 2.86%      | 3.41%        | 5.65 €        | 16.02 €         | 32.50 €    | 41.40 €      |
| momentum_based_zigzag     | SHL.DE    | 45m         | 0.19%         | 0.58%           | 1.10%      | 2.47%        | 2.11 €        | 6.43 €          | 12.30 €    | 27.27 €      |
| trend_type                | NVS       | 120m        | 0.05%         | 0.14%           | 0.28%      | 0.53%        | 0.48 €        | 1.44 €          | 2.88 €     | 5.45 €       |
| momentum_based_zigzag     | ltcusdt   | 30m         | 0.85%         | 2.62%           | 5.29%      | 10.21%       | 12.62 €       | 37.47 €         | 72.74 €    | 137.40 €     |
| momentum_based_zigzag     | daideeur  | 15m         | 0.23%         | 0.70%           | 1.37%      | 2.46%        | 2.70 €        | 8.10 €          | 15.82 €    | 29.01 €      |
| msl_trend                 | NVS       | 10m         | 0.06%         | 0.17%           | 0.34%      | 0.70%        | 0.58 €        | 1.74 €          | 3.49 €     | 7.24 €       |
| range_filter              | GMAB      | 20m         | 0.54%         | 1.45%           | 3.22%      | 3.28%        | 6.26 €        | 16.81 €         | 35.97 €    | 40.70 €      |
| trend_type                | NVS       | 15m         | 0.04%         | 0.11%           | 0.22%      | 0.43%        | 0.38 €        | 1.14 €          | 2.27 €     | 4.41 €       |
| trend_type                | NVS       | 30m         | 0.03%         | 0.09%           | 0.19%      | 0.43%        | 0.31 €        | 0.94 €          | 1.89 €     | 4.34 €       |
| cybernetic_hilbert        | dotusdt   | 10m         | 0.03%         | 0.07%           | 0.15%      | 0.27%        | 0.26 €        | 0.71 €          | 1.53 €     | 2.69 €       |
| msl_trend                 | NVO       | 30m         | 0.70%         | 2.08%           | 4.04%      | 8.61%        | 9.97 €        | 29.77 €         | 57.21 €    | 119.09 €     |
| momentum_based_zigzag     | vnadeeur  | 10m         | 0.09%         | 0.28%           | 0.54%      | 1.09%        | 1.03 €        | 2.92 €          | 5.69 €     | 11.56 €      |
| 3commas_bot               | FPE.DE    | 5m          | 0.47%         | 1.41%           | 2.78%      | 6.77%        | 5.17 €        | 15.49 €         | 30.13 €    | 73.64 €      |
| trend_type                | NVO       | 60m         | 0.48%         | 1.44%           | 2.78%      | 5.96%        | 5.98 €        | 18.01 €         | 34.31 €    | 72.05 €      |
| 3commas_bot               | FPE.DE    | 45m         | 0.71%         | 1.93%           | 4.20%      | 9.07%        | 7.97 €        | 21.97 €         | 46.50 €    | 101.33 €     |
| cybernetic_hilbert        | ZEAL.CO   | 60m         | 3.11%         | 9.68%           | 19.79%     | 49.99%       | 54.35 €       | 167.92 €        | 317.02 €   | 790.45 €     |
| hma_crossover             | GMAB      | 45m         | 0.40%         | 1.03%           | 2.43%      | 2.15%        | 4.47 €        | 11.44 €         | 25.72 €    | 25.85 €      |
| 3commas_bot               | FPE.DE    | 20m         | 0.63%         | 1.67%           | 3.71%      | 8.17%        | 7.01 €        | 18.89 €         | 40.90 €    | 91.29 €      |
| trend_type                | NVO       | 45m         | 0.43%         | 1.28%           | 2.46%      | 5.32%        | 5.17 €        | 15.56 €         | 29.64 €    | 62.24 €      |
| hmm_regime_filter         | NVO       | 60m         | 0.70%         | 2.13%           | 4.13%      | 8.88%        | 10.42 €       | 31.37 €         | 59.76 €    | 125.47 €     |
| hmm_regime_filter         | NVO       | 120m        | 0.53%         | 1.58%           | 3.03%      | 6.45%        | 6.79 €        | 20.52 €         | 38.94 €    | 82.09 €      |
| adaptive_volatility_trend | NVS       | 15m         | 0.27%         | 0.81%           | 1.63%      | 3.09%        | 3.15 €        | 9.44 €          | 18.88 €    | 36.28 €      |
| adaptive_volatility_trend | NVS       | 10m         | 0.24%         | 0.73%           | 1.45%      | 2.89%        | 2.75 €        | 8.24 €          | 16.49 €    | 33.00 €      |
| adaptive_volatility_trend | GMAB      | 5m          | 0.51%         | 1.37%           | 3.10%      | 2.18%        | 5.94 €        | 15.82 €         | 34.16 €    | 26.84 €      |
| cybernetic_hilbert        | ZEAL.CO   | 45m         | 3.13%         | 9.99%           | 20.40%     | 57.25%       | 56.73 €       | 176.23 €        | 330.92 €   | 872.22 €     |
| trend_type                | NVS       | 45m         | 0.04%         | 0.12%           | 0.24%      | 0.56%        | 0.42 €        | 1.25 €          | 2.49 €     | 5.66 €       |
| msl_trend                 | NVS       | 120m        | 0.07%         | 0.20%           | 0.40%      | 0.87%        | 0.70 €        | 2.10 €          | 4.20 €     | 8.98 €       |
| pmax_explorer             | GMAB      | 30m         | 0.41%         | 1.28%           | 2.40%      | 3.21%        | 4.51 €        | 13.78 €         | 25.92 €    | 37.13 €      |
| hmm_regime_filter         | NVO       | 30m         | 0.71%         | 2.15%           | 4.18%      | 8.98%        | 10.55 €       | 31.77 €         | 60.54 €    | 127.09 €     |
| 3commas_bot               | FPE.DE    | 30m         | 0.51%         | 1.34%           | 3.00%      | 6.82%        | 5.58 €        | 14.85 €         | 32.56 €    | 74.27 €      |
| momentum_based_zigzag     | akzanleur | 30m         | 0.12%         | 0.36%           | 0.69%      | 1.46%        | 1.40 €        | 3.80 €          | 7.66 €     | 16.17 €      |
| pmax_explorer             | GMAB      | 15m         | 0.40%         | 1.17%           | 2.42%      | 2.61%        | 4.46 €        | 12.71 €         | 25.67 €    | 30.43 €      |
| msl_trend                 | NVO       | 45m         | 0.66%         | 1.98%           | 3.80%      | 8.27%        | 9.21 €        | 27.68 €         | 52.81 €    | 110.72 €     |
| trend_type                | NVO       | 30m         | 0.42%         | 1.26%           | 2.42%      | 5.28%        | 5.04 €        | 15.22 €         | 28.94 €    | 60.89 €      |
| momentum_based_zigzag     | NVS       | 5m          | 0.08%         | 0.25%           | 0.51%      | 1.14%        | 0.89 €        | 2.66 €          | 5.33 €     | 11.84 €      |
| hmm_regime_filter         | mrkdeeur  | 45m         | 0.16%         | 0.47%           | 0.95%      | 1.77%        | 1.75 €        | 5.19 €          | 10.36 €    | 19.52 €      |
| msl_trend                 | NVO       | 120m        | 0.63%         | 1.92%           | 3.68%      | 8.03%        | 8.64 €        | 26.11 €         | 49.57 €    | 104.44 €     |
| hmm_regime_filter         | acfreur   | 15m         | 0.09%         | 0.27%           | 0.53%      | 1.22%        | 0.97 €        | 2.85 €          | 5.51 €     | 12.62 €      |
| hmm_regime_filter         | lxsdeeur  | 30m         | 0.09%         | 0.26%           | 0.51%      | 1.06%        | 0.92 €        | 2.75 €          | 5.38 €     | 11.13 €      |
| range_filter              | FPE.DE    | 45m         | 0.25%         | 0.66%           | 1.48%      | 4.20%        | 2.56 €        | 6.72 €          | 14.94 €    | 43.02 €      |
| momentum_based_zigzag     | ZEAL.CO   | 1m          | 2.56%         | 8.35%           | 15.90%     | 41.44%       | 39.62 €       | 126.34 €        | 231.13 €   | 581.28 €     |
| cybernetic_hilbert        | dotusdt   | 60m         | 0.61%         | 1.85%           | 3.82%      | 7.13%        | 7.49 €        | 22.24 €         | 44.96 €    | 79.98 €      |
| hmm_regime_filter         | acfreur   | 10m         | 0.08%         | 0.23%           | 0.43%      | 1.00%        | 0.78 €        | 2.32 €          | 4.46 €     | 10.25 €      |
| momentum_based_zigzag     | cafreur   | 15m         | 0.04%         | 0.11%           | 0.22%      | 0.44%        | 0.38 €        | 1.12 €          | 2.20 €     | 4.47 €       |
| hma_crossover             | FPE.DE    | 30m         | 0.28%         | 0.83%           | 1.63%      | 3.82%        | 2.89 €        | 8.58 €          | 16.86 €    | 39.90 €      |
| 3commas_bot               | GMAB      | 15m         | 0.49%         | 1.32%           | 2.91%      | 2.49%        | 5.70 €        | 15.48 €         | 32.77 €    | 30.49 €      |
| momentum_based_zigzag     | cpriteur  | 10m         | 0.01%         | 0.04%           | 0.08%      | 0.17%        | 0.14 €        | 0.42 €          | 0.84 €     | 1.68 €       |
| hmm_regime_filter         | rifreur   | 10m         | 0.13%         | 0.40%           | 0.77%      | 1.70%        | 0.80 €        | 4.20 €          | 8.19 €     | 17.94 €      |
| cybernetic_hilbert        | ZEAL.CO   | 30m         | 3.14%         | 10.24%          | 20.25%     | 51.27%       | 55.00 €       | 171.96 €        | 320.82 €   | 792.52 €     |
| momentum_based_zigzag     | FPE.DE    | 20m         | 0.00%         | 0.01%           | 0.02%      | 0.06%        | 0.04 €        | 0.11 €          | 0.22 €     | 0.65 €       |
| hmm_regime_filter         | rifreur   | 15m         | 0.13%         | 0.39%           | 0.76%      | 1.58%        | 0.75 €        | 4.14 €          | 8.06 €     | 16.68 €      |
| smart_trader_geometric    | ZEAL.CO   | 10m         | 1.09%         | 3.57%           | 6.58%      | 16.86%       | 13.01 €       | 41.72 €         | 75.88 €    | 190.05 €     |
| momentum_based_zigzag     | vpknleur  | 15m         | 0.04%         | 0.12%           | 0.23%      | 0.49%        | 0.27 €        | 1.00 €          | 1.88 €     | 4.97 €       |
| trend_type                | NVO       | 120m        | 0.37%         | 1.10%           | 2.17%      | 4.49%        | 4.36 €        | 12.92 €         | 25.00 €    | 51.70 €      |
| hma_crossover             | NVS       | 120m        | 0.18%         | 0.55%           | 1.10%      | 2.49%        | 2.01 €        | 6.02 €          | 12.04 €    | 27.04 €      |
| cybernetic_hilbert        | ltcusdt   | 45m         | 1.86%         | 5.82%           | 11.98%     | 24.43%       | 58.69 €       | 174.29 €        | 338.33 €   | 639.06 €     |
| msl_trend                 | NVO       | 60m         | 0.67%         | 2.02%           | 3.86%      | 8.20%        | 9.45 €        | 28.30 €         | 54.24 €    | 113.22 €     |
| 3commas_bot               | GMAB      | 30m         | 0.48%         | 1.26%           | 2.84%      | 2.00%        | 5.49 €        | 14.51 €         | 31.58 €    | 23.73 €      |
| hmm_regime_filter         | mrkdeeur  | 30m         | 0.11%         | 0.32%           | 0.64%      | 1.11%        | 1.22 €        | 3.62 €          | 6.83 €     | 11.93 €      |
| hmm_regime_filter         | abibeeur  | 15m         | 0.07%         | 0.21%           | 0.41%      | 0.84%        | 0.74 €        | 2.17 €          | 4.24 €     | 8.69 €       |
| hmm_regime_filter         | NVO       | 15m         | 0.66%         | 2.04%           | 3.83%      | 8.35%        | 9.46 €        | 28.88 €         | 54.25 €    | 115.54 €     |
| cybernetic_hilbert        | ZEAL.CO   | 15m         | 3.61%         | 11.76%          | 23.58%     | 57.61%       | 69.42 €       | 218.04 €        | 404.94 €   | 1019.57 €    |
| 3commas_bot               | EVD.DE    | 5m          | 0.71%         | 2.03%           | 4.23%      | 5.85%        | 8.12 €        | 23.31 €         | 47.39 €    | 69.83 €      |
| cybernetic_hilbert        | ZEAL.CO   | 20m         | 3.27%         | 10.49%          | 20.74%     | 47.95%       | 58.18 €       | 182.98 €        | 339.36 €   | 822.43 €     |
| hmm_regime_filter         | diaiteur  | 30m         | 0.21%         | 0.63%           | 1.28%      | 2.59%        | 2.57 €        | 7.71 €          | 13.27 €    | 26.54 €      |
| hmm_regime_filter         | abibeeur  | 10m         | 0.07%         | 0.21%           | 0.41%      | 0.85%        | 0.74 €        | 2.18 €          | 4.24 €     | 8.73 €       |
| trend_type                | NVS       | 20m         | 0.03%         | 0.08%           | 0.15%      | 0.29%        | 0.26 €        | 0.78 €          | 1.55 €     | 2.92 €       |
| hmm_regime_filter         | diaiteur  | 15m         | 0.28%         | 0.85%           | 1.71%      | 3.46%        | 3.09 €        | 9.28 €          | 18.19 €    | 36.38 €      |
| hmm_regime_filter         | mrkdeeur  | 15m         | 0.11%         | 0.32%           | 0.64%      | 1.04%        | 1.21 €        | 3.59 €          | 6.79 €     | 11.12 €      |
| lorentzian_classification | NVO       | 20m         | 0.84%         | 2.51%           | 4.93%      | 10.65%       | 13.10 €       | 39.10 €         | 75.14 €    | 156.39 €     |
| hmm_regime_filter         | abibeeur  | 45m         | 0.05%         | 0.17%           | 0.31%      | 0.66%        | 0.56 €        | 1.70 €          | 3.22 €     | 6.80 €       |
| msl_trend                 | AMS.MC    | 120m        | 0.04%         | 0.13%           | 0.26%      | 0.11%        | 0.45 €        | 1.34 €          | 2.58 €     | 1.14 €       |
| trend_type                | NVO       | 20m         | 0.48%         | 1.47%           | 2.80%      | 5.93%        | 6.09 €        | 18.31 €         | 34.94 €    | 73.25 €      |
| msl_trend                 | NVO       | 20m         | 0.68%         | 2.08%           | 3.99%      | 8.61%        | 9.81 €        | 29.67 €         | 56.28 €    | 118.68 €     |
| range_filter              | FPE.DE    | 240m        | -0.10%        | 0.01%           | -0.53%     | 1.30%        | -1.04 €       | -0.16 €         | -6.05 €    | 12.14 €      |
| msl_trend                 | NVO       | 15m         | 0.69%         | 2.08%           | 3.99%      | 8.62%        | 9.89 €        | 29.92 €         | 56.74 €    | 119.68 €     |
| hmm_regime_filter         | mrkdeeur  | 10m         | 0.10%         | 0.29%           | 0.58%      | 1.02%        | 1.09 €        | 3.24 €          | 6.14 €     | 10.77 €      |
| hmm_regime_filter         | diaiteur  | 10m         | 0.25%         | 0.76%           | 1.54%      | 3.10%        | 2.72 €        | 8.17 €          | 16.23 €    | 32.47 €      |
| smart_trader_geometric    | ZEAL.CO   | 5m          | 0.23%         | 0.76%           | 1.37%      | 3.92%        | 2.43 €        | 7.90 €          | 14.15 €    | 40.16 €      |
| msl_trend                 | NVO       | 10m         | 0.69%         | 2.10%           | 4.02%      | 8.78%        | 9.92 €        | 30.11 €         | 56.94 €    | 120.44 €     |
| noise_boundary_intraday   | AMS.MC    | 120m        | 1.23%         | 3.71%           | 7.45%      | 15.58%       | 22.20 €       | 66.68 €         | 133.21 €   | 266.70 €     |
| noise_boundary_intraday   | FPE.DE    | 120m        | 1.46%         | 4.42%           | 8.85%      | 24.51%       | 16.85 €       | 50.94 €         | 98.31 €    | 279.82 €     |
| cybernetic_hilbert        | NVO       | 45m         | 1.00%         | 3.04%           | 5.94%      | 12.83%       | 17.76 €       | 53.40 €         | 101.90 €   | 213.61 €     |
| trend_type                | NVO       | 10m         | 0.54%         | 1.65%           | 3.11%      | 6.77%        | 7.14 €        | 21.79 €         | 40.93 €    | 87.16 €      |
| hmm_regime_filter         | NVO       | 20m         | 0.58%         | 1.80%           | 3.39%      | 7.40%        | 7.98 €        | 24.35 €         | 45.77 €    | 97.41 €      |
| msl_trend                 | AMS.MC    | 20m         | 0.11%         | 0.35%           | 0.63%      | 0.82%        | 1.14 €        | 3.57 €          | 6.53 €     | 8.66 €       |
| noise_boundary_intraday   | GMAB      | 30m         | 0.71%         | 1.48%           | 4.01%      | 9.00%        | 8.30 €        | 18.13 €         | 47.70 €    | 106.02 €     |
| msl_trend                 | AMS.MC    | 10m         | 0.11%         | 0.37%           | 0.64%      | 0.96%        | 1.14 €        | 3.77 €          | 6.58 €     | 10.03 €      |
| msl_trend                 | AMS.MC    | 15m         | 0.11%         | 0.35%           | 0.62%      | 0.80%        | 1.11 €        | 3.59 €          | 6.39 €     | 8.36 €       |
| trend_type                | NVO       | 15m         | 0.45%         | 1.38%           | 2.58%      | 5.61%        | 5.52 €        | 16.73 €         | 31.64 €    | 66.92 €      |
| msl_trend                 | AMS.MC    | 45m         | 0.10%         | 0.33%           | 0.59%      | 0.68%        | 1.06 €        | 3.43 €          | 6.10 €     | 7.14 €       |
| noise_boundary_intraday   | AMS.MC    | 60m         | 1.38%         | 4.12%           | 7.97%      | 17.08%       | 25.66 €       | 77.18 €         | 153.98 €   | 308.71 €     |
| msl_trend                 | AMS.MC    | 60m         | 0.03%         | 0.13%           | 0.18%      | 0.20%        | 0.31 €        | 1.31 €          | 1.81 €     | 2.02 €       |
| cybernetic_hilbert        | mrkdeeur  | 45m         | 0.27%         | 0.82%           | 1.63%      | 3.39%        | 3.10 €        | 9.22 €          | 19.13 €    | 39.28 €      |
| hmm_regime_filter         | NVO       | 10m         | 0.52%         | 1.58%           | 3.04%      | 6.40%        | 6.74 €        | 20.46 €         | 38.69 €    | 81.83 €      |
| smart_trader_geometric    | LOGI      | 5m          | 0.03%         | 0.10%           | 0.21%      | 0.43%        | 0.38 €        | 0.96 €          | 1.84 €     | 3.44 €       |
| cybernetic_hilbert        | lxsdeeur  | 60m         | 0.12%         | 0.34%           | 0.69%      | 1.34%        | 1.26 €        | 3.62 €          | 7.34 €     | 14.38 €      |
| msl_trend                 | AMS.MC    | 30m         | 0.10%         | 0.32%           | 0.56%      | 0.66%        | 1.01 €        | 3.30 €          | 5.79 €     | 6.89 €       |

## 4. Adaptive Trend Classification (Données Isolées)

> **Note** : Ces résultats sont isolés car ils ont été récupérés depuis la documentation. Ils devront être réintégrés au tableau principal ultérieurement lorsque de nouveaux artefacts Parquet seront disponibles.

| strategy                      | symbol   | timeframe   |   trades |   win_rate |   profit_factor |   mean_return |   max_drawdown |   sharpe |
|:------------------------------|:---------|:------------|---------:|-----------:|----------------:|--------------:|---------------:|---------:|
| adaptive_trend_classification | NVO      | 60m         |      120 |       0.58 |            1.60 |          0.01 |          -0.06 |     1.70 |
| adaptive_trend_classification | NVO      | 45m         |      150 |       0.55 |            1.45 |          0.01 |          -0.08 |     1.50 |

## 5. Analyse des Flexibilités

- **Stratégies passe-partout** : `momentum_based_zigzag` et `msl_trend` s'illustrent par leur robustesse sur un grand nombre d'actifs et de timeframes.
- **Stratégies spécialisées** : `pmax_explorer` et `range_filter` montrent des edges très concentrés (ex: GMAB et FPE.DE).

## 6. Matrice de Corrélations des Positions

Calculée sur le chevauchement journalier des positions ouvertes.

|                                   |   momentum_based_zigzag_dotusdt_30m |   cybernetic_hilbert_ethusdt_45m |   momentum_based_zigzag_dotusdt_45m |   cybernetic_hilbert_ltcusdt_30m |   hmm_regime_filter_bnbusdt_60m |   cybernetic_hilbert_aptusdt_10m |   cybernetic_hilbert_dotusdt_45m |   momentum_based_zigzag_ltcusdt_45m |   momentum_based_zigzag_ltcusdt_30m |   cybernetic_hilbert_dotusdt_10m |   cybernetic_hilbert_dotusdt_60m |   cybernetic_hilbert_ltcusdt_45m |
|:----------------------------------|------------------------------------:|---------------------------------:|------------------------------------:|---------------------------------:|--------------------------------:|---------------------------------:|---------------------------------:|------------------------------------:|------------------------------------:|---------------------------------:|---------------------------------:|---------------------------------:|
| momentum_based_zigzag_dotusdt_30m |                                1    |                            -0.03 |                               -0.08 |                            -0.03 |                           -0.06 |                            -0.03 |                            -0.02 |                               -0.09 |                               -0.09 |                            -0.03 |                            -0.09 |                            -0.11 |
| cybernetic_hilbert_ethusdt_45m    |                               -0.03 |                             1    |                               -0.02 |                            -0.01 |                           -0.02 |                            -0.01 |                            -0.01 |                               -0.03 |                               -0.03 |                            -0.01 |                            -0.03 |                            -0.03 |
| momentum_based_zigzag_dotusdt_45m |                               -0.08 |                            -0.02 |                                1    |                            -0.03 |                           -0.05 |                            -0.02 |                            -0.02 |                               -0.08 |                               -0.08 |                            -0.03 |                            -0.08 |                            -0.1  |
| cybernetic_hilbert_ltcusdt_30m    |                               -0.03 |                            -0.01 |                               -0.03 |                             1    |                           -0.02 |                            -0.01 |                            -0.01 |                                0.23 |                               -0.03 |                            -0.01 |                            -0.03 |                            -0.04 |
| hmm_regime_filter_bnbusdt_60m     |                               -0.06 |                            -0.02 |                               -0.05 |                            -0.02 |                            1    |                            -0.02 |                            -0.01 |                               -0.06 |                                0.4  |                            -0.02 |                            -0.06 |                            -0.07 |
| cybernetic_hilbert_aptusdt_10m    |                               -0.03 |                            -0.01 |                               -0.02 |                            -0.01 |                           -0.02 |                             1    |                            -0.01 |                               -0.03 |                               -0.03 |                            -0.01 |                            -0.03 |                            -0.03 |
| cybernetic_hilbert_dotusdt_45m    |                               -0.02 |                            -0.01 |                               -0.02 |                            -0.01 |                           -0.01 |                            -0.01 |                             1    |                               -0.02 |                               -0.02 |                            -0.01 |                            -0.02 |                            -0.03 |
| momentum_based_zigzag_ltcusdt_45m |                               -0.09 |                            -0.03 |                               -0.08 |                             0.23 |                           -0.06 |                            -0.03 |                            -0.02 |                                1    |                               -0.09 |                            -0.03 |                            -0.09 |                            -0.11 |
| momentum_based_zigzag_ltcusdt_30m |                               -0.09 |                            -0.03 |                               -0.08 |                            -0.03 |                            0.4  |                            -0.03 |                            -0.02 |                               -0.09 |                                1    |                            -0.03 |                            -0.09 |                            -0.11 |
| cybernetic_hilbert_dotusdt_10m    |                               -0.03 |                            -0.01 |                               -0.03 |                            -0.01 |                           -0.02 |                            -0.01 |                            -0.01 |                               -0.03 |                               -0.03 |                             1    |                            -0.03 |                            -0.04 |
| cybernetic_hilbert_dotusdt_60m    |                               -0.09 |                            -0.03 |                               -0.08 |                            -0.03 |                           -0.06 |                            -0.03 |                            -0.02 |                               -0.09 |                               -0.09 |                            -0.03 |                             1    |                            -0.11 |
| cybernetic_hilbert_ltcusdt_45m    |                               -0.11 |                            -0.03 |                               -0.1  |                            -0.04 |                           -0.07 |                            -0.03 |                            -0.03 |                               -0.11 |                               -0.11 |                            -0.04 |                            -0.11 |                             1    |

## 7. Modélisation de l'Allocation Optimale

Comparatif entre la méthode **Risk-Parity** (Défensive) et **Kelly Criterion** (Offensive).

| strategy                  | symbol    | timeframe   | risk_parity_weight   | kelly_weight   |
|:--------------------------|:----------|:------------|:---------------------|:---------------|
| adaptive_volatility_trend | dpwdeeur  | 45m         | 0.08%                | 3.02%          |
| adaptive_volatility_trend | telnonok  | 15m         | 0.06%                | 3.02%          |
| adaptive_volatility_trend | ergiteur  | 30m         | 0.07%                | 3.02%          |
| adaptive_volatility_trend | akzanleur | 30m         | 0.12%                | 3.02%          |
| adaptive_volatility_trend | beideeur  | 10m         | 0.09%                | 3.02%          |
| momentum_based_zigzag     | SAP       | 30m         | 0.37%                | 1.43%          |
| momentum_based_zigzag     | dotusdt   | 30m         | 0.36%                | 1.09%          |
| cybernetic_hilbert        | ethusdt   | 45m         | 0.04%                | 0.58%          |
| 3commas_bot               | LOGI      | 10m         | 0.05%                | 0.94%          |
| 3commas_bot               | LOGI      | 5m          | 0.04%                | 0.65%          |
| momentum_based_zigzag     | EVD.DE    | 45m         | 12.64%               | 1.03%          |
| momentum_based_zigzag     | beideeur  | 15m         | 0.26%                | 1.03%          |
| momentum_based_zigzag     | LOGI      | 120m        | 0.53%                | 0.99%          |
| adaptive_volatility_trend | NVS       | 60m         | 0.16%                | 1.28%          |
| adaptive_volatility_trend | NVS       | 45m         | 0.21%                | 1.19%          |
| 3commas_bot               | EVD.DE    | 30m         | 0.14%                | 1.23%          |
| 3commas_bot               | LOGI      | 120m        | 0.04%                | 1.23%          |
| momentum_based_zigzag     | AMS.MC    | 10m         | 1.33%                | 0.69%          |
| momentum_based_zigzag     | dotusdt   | 45m         | 1.08%                | 0.67%          |
| 3commas_bot               | teniteur  | 30m         | 0.10%                | 1.45%          |
| 3commas_bot               | LOGI      | 45m         | 0.04%                | 0.97%          |
| cybernetic_hilbert        | ltcusdt   | 30m         | 0.28%                | 0.45%          |
| lorentzian_classification | FPE.DE    | 120m        | 18.95%               | 1.02%          |
| lorentzian_classification | GMAB      | 30m         | 0.91%                | 0.89%          |
| msl_trend                 | NVS       | 240m        | 0.39%                | 1.06%          |
| momentum_based_zigzag     | NVO       | 45m         | 0.16%                | 0.70%          |
| momentum_based_zigzag     | randnleur | 10m         | 0.37%                | 1.11%          |
| msl_trend                 | NVS       | 60m         | 0.61%                | 1.04%          |
| hmm_regime_filter         | bnbusdt   | 60m         | 0.09%                | 0.88%          |
| cybernetic_hilbert        | aptusdt   | 10m         | 4.57%                | 0.31%          |
| momentum_based_zigzag     | GMAB      | 1m          | 0.57%                | 0.96%          |
| trend_type                | NVS       | 60m         | 0.92%                | 1.05%          |
| momentum_based_zigzag     | belgbeeur | 10m         | 4.46%                | 0.50%          |
| range_filter              | GMAB      | 30m         | 0.11%                | 0.72%          |
| 3commas_bot               | GMAB      | 60m         | 0.12%                | 1.16%          |
| cybernetic_hilbert        | dotusdt   | 45m         | 1.27%                | 0.60%          |
| msl_trend                 | NVO       | 240m        | 0.06%                | 0.86%          |
| hmm_regime_filter         | NVO       | 45m         | 0.11%                | 0.68%          |
| momentum_based_zigzag     | ltcusdt   | 45m         | 0.19%                | 0.40%          |
| 3commas_bot               | EVD.DE    | 20m         | 0.13%                | 0.97%          |
| 3commas_bot               | GMAB      | 20m         | 0.09%                | 0.94%          |
| momentum_based_zigzag     | SHL.DE    | 45m         | 0.31%                | 0.78%          |
| trend_type                | NVS       | 120m        | 0.82%                | 0.80%          |
| momentum_based_zigzag     | ltcusdt   | 30m         | 0.13%                | 0.38%          |
| momentum_based_zigzag     | daideeur  | 15m         | 0.75%                | 0.62%          |
| msl_trend                 | NVS       | 10m         | 0.61%                | 0.84%          |
| range_filter              | GMAB      | 20m         | 0.10%                | 0.62%          |
| trend_type                | NVS       | 15m         | 1.81%                | 0.86%          |
| trend_type                | NVS       | 30m         | 1.04%                | 0.77%          |
| cybernetic_hilbert        | dotusdt   | 10m         | 0.88%                | 0.27%          |
| msl_trend                 | NVO       | 30m         | 0.05%                | 0.85%          |
| momentum_based_zigzag     | vnadeeur  | 10m         | 0.71%                | 0.50%          |
| 3commas_bot               | FPE.DE    | 5m          | 0.36%                | 0.90%          |
| trend_type                | NVO       | 60m         | 0.09%                | 0.76%          |
| 3commas_bot               | FPE.DE    | 45m         | 0.20%                | 1.07%          |
| cybernetic_hilbert        | ZEAL.CO   | 60m         | 0.21%                | 0.74%          |
| hma_crossover             | GMAB      | 45m         | 0.09%                | 0.70%          |
| 3commas_bot               | FPE.DE    | 20m         | 0.20%                | 0.87%          |
| trend_type                | NVO       | 45m         | 0.09%                | 0.77%          |
| hmm_regime_filter         | NVO       | 60m         | 0.12%                | 0.62%          |
| hmm_regime_filter         | NVO       | 120m        | 0.08%                | 0.68%          |
| adaptive_volatility_trend | NVS       | 15m         | 0.15%                | 0.78%          |
| adaptive_volatility_trend | NVS       | 10m         | 0.08%                | 0.80%          |
| adaptive_volatility_trend | GMAB      | 5m          | 0.08%                | 0.66%          |
| cybernetic_hilbert        | ZEAL.CO   | 45m         | 0.12%                | 0.71%          |
| trend_type                | NVS       | 45m         | 0.94%                | 0.74%          |
| msl_trend                 | NVS       | 120m        | 0.58%                | 0.58%          |
| pmax_explorer             | GMAB      | 30m         | 0.09%                | 0.58%          |
| hmm_regime_filter         | NVO       | 30m         | 0.16%                | 0.53%          |
| 3commas_bot               | FPE.DE    | 30m         | 0.26%                | 0.83%          |
| momentum_based_zigzag     | akzanleur | 30m         | 0.30%                | 0.54%          |
| pmax_explorer             | GMAB      | 15m         | 0.08%                | 0.59%          |
| msl_trend                 | NVO       | 45m         | 0.05%                | 0.73%          |
| trend_type                | NVO       | 30m         | 0.14%                | 0.68%          |
| momentum_based_zigzag     | NVS       | 5m          | 0.31%                | 0.60%          |
| hmm_regime_filter         | mrkdeeur  | 45m         | 0.34%                | 0.51%          |
| msl_trend                 | NVO       | 120m        | 0.06%                | 0.68%          |
| hmm_regime_filter         | acfreur   | 15m         | 1.13%                | 0.51%          |
| hmm_regime_filter         | lxsdeeur  | 30m         | 0.53%                | 0.41%          |
| range_filter              | FPE.DE    | 45m         | 0.18%                | 0.57%          |
| momentum_based_zigzag     | ZEAL.CO   | 1m          | 0.07%                | 0.52%          |
| cybernetic_hilbert        | dotusdt   | 60m         | 0.60%                | 0.57%          |
| hmm_regime_filter         | acfreur   | 10m         | 1.40%                | 0.46%          |
| momentum_based_zigzag     | cafreur   | 15m         | 1.58%                | 0.39%          |
| hma_crossover             | FPE.DE    | 30m         | 0.19%                | 0.59%          |
| 3commas_bot               | GMAB      | 15m         | 0.07%                | 0.70%          |
| momentum_based_zigzag     | cpriteur  | 10m         | 1.90%                | 0.47%          |
| hmm_regime_filter         | rifreur   | 10m         | 0.16%                | 0.47%          |
| cybernetic_hilbert        | ZEAL.CO   | 30m         | 0.10%                | 0.54%          |
| momentum_based_zigzag     | FPE.DE    | 20m         | 12.64%               | 0.43%          |
| hmm_regime_filter         | rifreur   | 15m         | 0.19%                | 0.45%          |
| smart_trader_geometric    | ZEAL.CO   | 10m         | 0.20%                | 0.47%          |
| momentum_based_zigzag     | vpknleur  | 15m         | 0.38%                | 0.48%          |
| trend_type                | NVO       | 120m        | 0.07%                | 0.54%          |
| hma_crossover             | NVS       | 120m        | 0.14%                | 0.38%          |
| cybernetic_hilbert        | ltcusdt   | 45m         | 0.09%                | 0.54%          |
| msl_trend                 | NVO       | 60m         | 0.08%                | 0.53%          |
| 3commas_bot               | GMAB      | 30m         | 0.06%                | 0.60%          |
| hmm_regime_filter         | mrkdeeur  | 30m         | 0.47%                | 0.51%          |
| hmm_regime_filter         | abibeeur  | 15m         | 1.38%                | 0.43%          |
| hmm_regime_filter         | NVO       | 15m         | 0.14%                | 0.45%          |
| cybernetic_hilbert        | ZEAL.CO   | 15m         | 0.18%                | 0.49%          |
| 3commas_bot               | EVD.DE    | 5m          | 0.15%                | 0.47%          |
| cybernetic_hilbert        | ZEAL.CO   | 20m         | 0.18%                | 0.46%          |
| hmm_regime_filter         | diaiteur  | 30m         | 0.23%                | 0.32%          |
| hmm_regime_filter         | abibeeur  | 10m         | 0.83%                | 0.38%          |
| trend_type                | NVS       | 20m         | 0.88%                | 0.51%          |
| hmm_regime_filter         | diaiteur  | 15m         | 0.38%                | 0.37%          |
| hmm_regime_filter         | mrkdeeur  | 15m         | 0.33%                | 0.40%          |
| lorentzian_classification | NVO       | 20m         | 0.09%                | 0.39%          |
| hmm_regime_filter         | abibeeur  | 45m         | 0.74%                | 0.35%          |
| msl_trend                 | AMS.MC    | 120m        | 0.50%                | 0.28%          |
| trend_type                | NVO       | 20m         | 0.11%                | 0.45%          |
| msl_trend                 | NVO       | 20m         | 0.07%                | 0.33%          |
| range_filter              | FPE.DE    | 240m        | 0.10%                | 0.38%          |
| msl_trend                 | NVO       | 15m         | 0.10%                | 0.32%          |
| hmm_regime_filter         | mrkdeeur  | 10m         | 0.45%                | 0.36%          |
| hmm_regime_filter         | diaiteur  | 10m         | 0.32%                | 0.33%          |
| smart_trader_geometric    | ZEAL.CO   | 5m          | 0.92%                | 0.36%          |
| msl_trend                 | NVO       | 10m         | 0.10%                | 0.30%          |
| noise_boundary_intraday   | AMS.MC    | 120m        | 0.03%                | 0.44%          |
| noise_boundary_intraday   | FPE.DE    | 120m        | 0.05%                | 0.41%          |
| cybernetic_hilbert        | NVO       | 45m         | 0.12%                | 0.40%          |
| trend_type                | NVO       | 10m         | 0.14%                | 0.37%          |
| hmm_regime_filter         | NVO       | 20m         | 0.10%                | 0.33%          |
| msl_trend                 | AMS.MC    | 20m         | 0.43%                | 0.34%          |
| noise_boundary_intraday   | GMAB      | 30m         | 0.03%                | 0.37%          |
| msl_trend                 | AMS.MC    | 10m         | 0.36%                | 0.30%          |
| msl_trend                 | AMS.MC    | 15m         | 0.38%                | 0.32%          |
| trend_type                | NVO       | 15m         | 0.08%                | 0.36%          |
| msl_trend                 | AMS.MC    | 45m         | 0.41%                | 0.32%          |
| noise_boundary_intraday   | AMS.MC    | 60m         | 0.03%                | 0.39%          |
| msl_trend                 | AMS.MC    | 60m         | 0.42%                | 0.36%          |
| cybernetic_hilbert        | mrkdeeur  | 45m         | 0.28%                | 0.35%          |
| hmm_regime_filter         | NVO       | 10m         | 0.10%                | 0.27%          |
| smart_trader_geometric    | LOGI      | 5m          | 1.02%                | 0.30%          |
| cybernetic_hilbert        | lxsdeeur  | 60m         | 0.49%                | 0.34%          |
| msl_trend                 | AMS.MC    | 30m         | 0.36%                | 0.28%          |

## 8. Recommandations de Production

1. **Déploiement Immédiat** : Les setups ayant un Profit Factor >= 1.5 et un Sharpe > 1.0, avec un poids Kelly significatif et un rendement mensuel moyen justifiant le risque.
2. **Surveillance (Paper Trading)** : Les setups avec un Profit Factor entre 1.25 et 1.5, ou une fréquence de trade trop faible (ex: < 1 par mois).
3. **À écarter** : `bjorgum_double_tap` (sans surprise) et les runs où le drawdown absolu en devise excède la tolérance au risque.
