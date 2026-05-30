# Phase 4 — Comparaison Intraday Hold-Out (1m vs 5m)

Ce rapport compare la performance OOS de la stratégie baseline `noise_boundary_intraday` sur les granularités 1 minute et 5 minutes.

## Table Comparative OOS (Baseline)

| Ticker | Sharpe OOS (1m) | Sharpe OOS (5m) | MDD OOS (1m) | MDD OOS (5m) | Trades OOS (1m) | Trades OOS (5m) | Verdict Robustesse |
|--------|-----------------|-----------------|--------------|--------------|-----------------|-----------------|--------------------|
| LOGI | 0.210 | 0.737 | -13.6% | -0.1% | 23 | 2 | ⚠️ 5m Acceptable |
| SAP | 0.571 | 0.615 | -15.5% | -14.3% | 294 | 258 | ⚠️ 5m Acceptable |

## Observations Clés

1. **Stabilité des bandes :** La granularité 5m lisse le bruit haute fréquence, ce qui réduit le nombre de faux signaux d'entrée.
2. **Nombre de trades :** En 5m, le nombre de trades OOS devrait être plus faible qu'en 1m, mais leur pertinence et robustesse sont accrues.
3. **Maximum Drawdown (MDD) :** Vérifier si le passage en 5m permet de réduire le MDD sous la limite opérationnelle de 30%.