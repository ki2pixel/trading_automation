# Synthèse Stratégique : 3commas_bot

Ce document consolide les paramètres figés à l'issue des différentes passes d'optimisation.

## Paramètres finaux validés en production (Après Campagne Complète)

À l'issue de la **Passe 3 (Trailing Stop)**, il a été mathématiquement prouvé que l'ajout d'un trailing stop détruisait l'edge de la stratégie sur quasiment toutes les unités de temps. Les configurations listées ci-dessous intègrent donc les moyennes mobiles figées en **Passe 1 (Signal Brut)**, et la gestion du risque statique optimale (`rnr`, `risk_m`, `swing_lookback`) validée en **Passe 2 et Passe 2.1**.

Le Trailing Stop est désactivé (`trail_stop = false`) pour tous les actifs.

### GMAB
- **60m** : `ma_type1` = DEMA (8), `ma_type2` = HMA (10), `rnr` = 0.5, `risk_m` = 2.5, `swing_lookback` = 5, `trail_stop` = false
- **30m** : `ma_type1` = HMA (5), `ma_type2` = DEMA (23), `rnr` = 1.1, `risk_m` = 0.8, `swing_lookback` = 5, `trail_stop` = false
- **20m** : `ma_type1` = EMA (6), `ma_type2` = HMA (128), `rnr` = 1.5, `risk_m` = 0.5, `swing_lookback` = 5, `trail_stop` = false
- **15m** : `ma_type1` = HMA (6), `ma_type2` = VWMA (18), `rnr` = 0.8, `risk_m` = 2.6, `swing_lookback` = 5, `trail_stop` = false

### FPE.DE
- **45m** : `ma_type1` = HMA (41), `ma_type2` = WMA (10), `rnr` = 0.6, `risk_m` = 2.9, `swing_lookback` = 5, `trail_stop` = false
- **30m** : `ma_type1` = HMA (52), `ma_type2` = EMA (10), `rnr` = 0.9, `risk_m` = 1.2, `swing_lookback` = 5, `trail_stop` = false
- **20m** : `ma_type1` = DEMA (30), `ma_type2` = HMA (32), `rnr` = 1.0, `risk_m` = 1.5, `swing_lookback` = 5, `trail_stop` = false
- **5m** : `ma_type1` = WMA (36), `ma_type2` = HMA (59), `rnr` = 1.1, `risk_m` = 0.9, `swing_lookback` = 5, `trail_stop` = false

### LOGI
- **120m** : `ma_type1` = HEMA (7), `ma_type2` = SMA (13), `rnr` = 1.0, `risk_m` = 0.6, `swing_lookback` = 9, `trail_stop` = false
- **45m** : `ma_type1` = HEMA (6), `ma_type2` = SMA (13), `rnr` = 1.4, `risk_m` = 0.7, `swing_lookback` = 5, `trail_stop` = false
- **10m** : `ma_type1` = HEMA (5), `ma_type2` = T3 (15), `rnr` = 1.7, `risk_m` = 0.8, `swing_lookback` = 5, `trail_stop` = false
- **5m** : `ma_type1` = HEMA (8), `ma_type2` = HMA (57), `rnr` = 2.5, `risk_m` = 2.4, `swing_lookback` = 5, `trail_stop` = false

### EVD.DE
- **30m** : `ma_type1` = DEMA (40), `ma_type2` = HMA (140), `rnr` = 1.2, `risk_m` = 0.8, `swing_lookback` = 5, `trail_stop` = false
- **20m** : `ma_type1` = WMA (20), `ma_type2` = WMA (71), `rnr` = 1.1, `risk_m` = 0.9, `swing_lookback` = 5, `trail_stop` = false
- **5m** : `ma_type1` = SMA (49), `ma_type2` = VWMA (57), `rnr` = 5.0, `risk_m` = 2.5, `swing_lookback` = 5, `trail_stop` = false

### TENITEUR
- **30m** : `ma_type1` = HEMA (5), `ma_type2` = SMA (38), `rnr` = 0.5, `risk_m` = 0.8, `swing_lookback` = 5, `trail_stop` = false
