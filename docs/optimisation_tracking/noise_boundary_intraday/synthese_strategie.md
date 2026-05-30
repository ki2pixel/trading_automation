# Synthèse : Noise Boundary Intraday

Ce document consigne les paramètres "bloqués" à l'issue de chaque passe d'optimisation. Ces paramètres doivent être fixés dans le fichier `.json` de configuration pour les passes suivantes.

## Passe 1 : Signal Volatilité Brut
*(Validation du breakout des bandes - Filtres : min 100 trades, Max Drawdown -25%)*

Voici les "Sweet Spots" validés à figer en dur dans vos configurations de backtest pour la Passe 2 :

**Pour AMS.MC**
* **Timeframe 120m** (Idéal) : `lookback_days` = 9 | `volatility_multiplier_enter` = 1.1 | `volatility_multiplier_exit` = 0.11
* **Timeframe 60m** (Alternatif) : `lookback_days` = 17 | `volatility_multiplier_enter` = 1.4 | `volatility_multiplier_exit` = 0.56

**Pour FPE.DE**
* **Timeframe 120m** : `lookback_days` = 8 | `volatility_multiplier_enter` = 0.7 | `volatility_multiplier_exit` = 0.42

**Pour GMAB**
* **Timeframe 20m** : `lookback_days` = 15 | `volatility_multiplier_enter` = 1.8 | `volatility_multiplier_exit` = 1.62
* **Timeframe 30m** : `lookback_days` = 38 | `volatility_multiplier_enter` = 0.7 | `volatility_multiplier_exit` = 0.42

*Note : Les autres symboles (NVO, NVS, SHL.DE) ont des scores positifs mais avec très peu d'itérations éligibles (1 à 11). Ils peuvent être testés en Passe 2, mais avec prudence.*

## Passe 2 : Activité et Timing
*(Calibration du délai d'ouverture et du rythme d'intervention)*

L'analyse de la Passe 2 révèle une excellente convergence entre les différents actifs et timeframes. Vous pouvez fixer les paramètres de timing suivants pour la Passe 3 :

**Pour l'ensemble des actifs performants (AMS.MC, FPE.DE, GMAB)**
* `trade_frequency_bars` = 1 (Pas de délai de refroidissement après un trade)
* `entry_on_high_low` = true
* `start_trade_after_open_minutes` = 30 (L'optimiseur a trouvé des valeurs entre 27 et 34 minutes. Fixer à 30 minutes est un excellent consensus robuste pour éviter le bruit de l'open).

## Passe 3 : Sorties Complexes (Finalisation)
*(Optimisation du ratio risque/rendement via l'Exit Ladder)*

Les backtests confirment que la stratégie de sortie en Ladder améliore drastiquement les scores de rendement absolu. L'actif GMAB 20m est éliminé pour cause d'incompatibilité avec ces filtres combinés.

Voici les paramètres finaux (Ladder) à figer pour achever votre configuration :

**Pour AMS.MC (60m) - *Meilleur rendement absolu***
* `exit_mode` = "ladder"
* `stoploss_ladder_step0` = -0.016
* `stoploss_ladder_step1` = -0.024
* `takeprofit_ladder_step0` = 0.022
* `stoploss_ladder_ratio0` = 0.1 (Approche "laisser courir les gains")

**Pour AMS.MC (120m)**
* `exit_mode` = "ladder"
* `stoploss_ladder_step0` = -0.018
* `stoploss_ladder_step1` = -0.028
* `takeprofit_ladder_step0` = 0.012
* `stoploss_ladder_ratio0` = 0.9 (Approche "sécurisation massive")

**Pour FPE.DE (120m)**
* `exit_mode` = "ladder"
* `stoploss_ladder_step0` = -0.018
* `stoploss_ladder_step1` = -0.022
* `takeprofit_ladder_step0` = 0.017
* `stoploss_ladder_ratio0` = 0.9

**Pour GMAB (30m)**
* `exit_mode` = "ladder"
* `stoploss_ladder_step0` = -0.015
* `stoploss_ladder_step1` = -0.016
* `takeprofit_ladder_step0` = 0.009
* `stoploss_ladder_ratio0` = 0.9

> [!NOTE]  
> **Optimisation Terminée** 🎉. Tous les paramètres figurant dans ce document constituent les configurations définitives "Sweet Spots" pour lancer la stratégie Noise Boundary Intraday en production ou en Paper Trading.
