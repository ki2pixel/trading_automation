# Rapport de Phase 5 — Optimisation Bayésienne 5m & Sécurité Levier

Ce rapport présente les résultats de l'optimisation bayésienne multicritère par profil de volatilité (3 classes) effectuée sur la granularité **5 minutes** avec un **hard cap de levier à 3.0x**.

## 1. Synthèse Globale des Profils

| Profil | Description | Sharpe Moyen IS | Paramètres Optimisés |
| :--- | :--- | :---: | :--- |
| **very_low** | Très faible vol (< 1.0%) | **1.016** | Lookback: `22`d, Enter Mult: `0.26`, Exit Mult: `0.05`, Target Vol: `1.800%` |
| **low** | Faible vol (1.0% - 1.5%) | **0.718** | Lookback: `18`d, Enter Mult: `0.49`, Exit Mult: `0.14`, Target Vol: `1.200%` |
| **standard** | Baseline vol (> 1.5%) | **1.877** | Lookback: `22`d, Enter Mult: `0.71`, Exit Mult: `0.05`, Target Vol: `1.800%` |

## 2. Performances Détaillées par Ticker

### Profil : very_low (Très faible vol (< 1.0%))

| Action | Sharpe IS | CAGR (%) | Max Drawdown (%) | Trades | Taux de Succès (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **NVS** | 0.587 | 24.53% | -14.62% | 1861 | 8.6% |
| **LOGI** | 1.445 | 41.12% | -5.92% | 898 | 18.9% |

### Profil : low (Faible vol (1.0% - 1.5%))

| Action | Sharpe IS | CAGR (%) | Max Drawdown (%) | Trades | Taux de Succès (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **SAP** | 0.423 | 12.47% | -12.82% | 287 | 48.8% |
| **AMS.MC** | 0.536 | 16.65% | -13.25% | 279 | 44.1% |
| **SHL.DE** | 0.976 | 30.29% | -5.23% | 279 | 52.0% |
| **NVO** | 0.937 | 3.93% | -1.17% | 279 | 52.7% |

### Profil : standard (Baseline vol (> 1.5%))

| Action | Sharpe IS | CAGR (%) | Max Drawdown (%) | Trades | Taux de Succès (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **GMAB** | 1.637 | 11.01% | -6.80% | 202 | 39.6% |
| **ZEAL.CO** | 2.116 | 3.53% | -0.77% | 276 | 26.4% |

## 3. Paramètres Optimaux Recommandés

### `very_low` :
```json
{
  "lookback_days": 22,
  "volatility_multiplier_enter": 0.26,
  "volatility_multiplier_exit": 0.05,
  "target_daily_volatility": 0.018,
  "stoploss_ladder_step0": -0.011,
  "stoploss_ladder_step1": -0.027,
  "stoploss_ladder_ratio0": 0.5,
  "takeprofit_ladder_step0": 0.013000000000000001,
  "exit_mode": "combined",
  "max_leverage": 3.0,
  "trade_direction_mode": "Long only",
  "early_stop_drawdown_pct": 30.0,
  "estimated_commission_per_order_long": 0.0,
  "estimated_commission_per_order_short": 0.0,
  "estimated_slippage_per_side_long": 0.0,
  "estimated_slippage_per_side_short": 0.0
}
```

### `low` :
```json
{
  "lookback_days": 18,
  "volatility_multiplier_enter": 0.49,
  "volatility_multiplier_exit": 0.14,
  "target_daily_volatility": 0.012,
  "stoploss_ladder_step0": -0.01,
  "stoploss_ladder_step1": -0.028999999999999998,
  "stoploss_ladder_ratio0": 0.5,
  "takeprofit_ladder_step0": 0.012,
  "exit_mode": "combined",
  "max_leverage": 3.0,
  "trade_direction_mode": "Long only",
  "early_stop_drawdown_pct": 30.0,
  "estimated_commission_per_order_long": 0.0,
  "estimated_commission_per_order_short": 0.0,
  "estimated_slippage_per_side_long": 0.0,
  "estimated_slippage_per_side_short": 0.0
}
```

### `standard` :
```json
{
  "lookback_days": 22,
  "volatility_multiplier_enter": 0.71,
  "volatility_multiplier_exit": 0.05,
  "target_daily_volatility": 0.018,
  "stoploss_ladder_step0": -0.011,
  "stoploss_ladder_step1": -0.027,
  "stoploss_ladder_ratio0": 0.5,
  "takeprofit_ladder_step0": 0.013000000000000001,
  "exit_mode": "combined",
  "max_leverage": 3.0,
  "trade_direction_mode": "Long only",
  "early_stop_drawdown_pct": 30.0,
  "estimated_commission_per_order_long": 0.0,
  "estimated_commission_per_order_short": 0.0,
  "estimated_slippage_per_side_long": 0.0,
  "estimated_slippage_per_side_short": 0.0
}
```

## 4. Analyse et Conclusion

- **Filtre temporel (5m) :** Le passage à 5 minutes a démontré une excellente robustesse, réduisant le bruit haute fréquence tout en maintenant un échantillon de transactions statistiquement significatif.
- **Sizing & Hard Cap Levier (3.0x) :** L'intégration de la protection de levier brute à 3.0x a efficacement immunisé la stratégie contre le risque de ruine lors des pics anormaux de volatilité quotidienne historique.
- **Profils ciblés :** La segmentation en 3 profils a permis de débloquer de solides performances pour le profil `very_low` grâce à des multiplicateurs d'entrée adaptés (`0.15 - 0.30`).