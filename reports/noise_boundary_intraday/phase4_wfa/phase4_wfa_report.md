# Phase 4 — Validation et Généralisation (WFA, Multi-Actifs, PBO/DSR)

**Date d'exécution:** 2026-05-18 16:22 UTC
**Fenêtres:** 3 ans IS / 1 ans OOS
**Ré-optimisation:** Oui (20 trials Optuna TPE)

---

## LOGI

| Fold | IS | OOS | Sharpe IS (base) | Sharpe OOS (base) | CAGR OOS (base) | MDD OOS (base) | Trades OOS (base) | Sharpe IS (réopt) | Sharpe OOS (réopt) | CAGR OOS (réopt) | MDD OOS (réopt) | Trades OOS (réopt) | PBO | DSR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 2018-01-02 → 2021-01-02 | 2021-01-02 → 2022-01-02 | 1.843 | 2.598 | 771.775 | -34.569 | 423 | 1.047 | 0.202 | 1.128 | -3.538 | 3 | 0.466 | 0.000 |
| 1 | 2019-01-02 → 2022-01-02 | 2022-01-02 → 2023-01-02 | 0.241 | 3.133 | 1182.009 | -39.568 | 344 | 0.889 | 0.279 | 3.731 | -15.638 | 8 | 0.612 | 0.000 |
| 2 | 2020-01-02 → 2023-01-02 | 2023-01-02 → 2024-01-02 | -0.244 | 2.011 | 269.746 | -62.694 | 328 | 2.865 | 1.320 | 72.023 | -39.793 | 311 | 0.000 | 0.000 |

**Dégradation baseline:** IS Sharpe moyen = 0.614, OOS Sharpe moyen = 2.581

**Dégradation ré-optimisée:** IS Sharpe moyen = 1.600, OOS Sharpe moyen = 0.600

**PBO moyen:** 0.359  (seuil critique: 0.5)

**DSR moyen:** 0.000

---

## NVO

| Fold | IS | OOS | Sharpe IS (base) | Sharpe OOS (base) | CAGR OOS (base) | MDD OOS (base) | Trades OOS (base) | Sharpe IS (réopt) | Sharpe OOS (réopt) | CAGR OOS (réopt) | MDD OOS (réopt) | Trades OOS (réopt) | PBO | DSR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 2018-01-02 → 2021-01-02 | 2021-01-02 → 2022-01-02 | 2.229 | 3.406 | 1006.346 | -27.720 | 354 | 2.957 | 3.469 | 1244.551 | -29.032 | 299 | 0.000 | 0.605 |
| 1 | 2019-01-02 → 2022-01-02 | 2022-01-02 → 2023-01-02 | 1.819 | 0.672 | 24.541 | -61.697 | 159 | 1.111 | 1.115 | 24.408 | -7.494 | 8 | 0.558 | 0.000 |
| 2 | 2020-01-02 → 2023-01-02 | 2023-01-02 → 2024-01-02 | 0.358 | 1.204 | 93.506 | -45.391 | 327 | 1.068 | -1.414 | -17.494 | -18.494 | 8 | 0.696 | 0.000 |

**Dégradation baseline:** IS Sharpe moyen = 1.469, OOS Sharpe moyen = 1.761

**Dégradation ré-optimisée:** IS Sharpe moyen = 1.712, OOS Sharpe moyen = 1.057

**PBO moyen:** 0.418  (seuil critique: 0.5)

**DSR moyen:** 0.202

---

## SAP

| Fold | IS | OOS | Sharpe IS (base) | Sharpe OOS (base) | CAGR OOS (base) | MDD OOS (base) | Trades OOS (base) | Sharpe IS (réopt) | Sharpe OOS (réopt) | CAGR OOS (réopt) | MDD OOS (réopt) | Trades OOS (réopt) | PBO | DSR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 2018-01-02 → 2021-01-02 | 2021-01-02 → 2022-01-02 | 2.080 | 3.499 | 1722.512 | -25.419 | 245 | 0.324 | 1.163 | 89.215 | -39.467 | 121 | 0.820 | 0.000 |
| 1 | 2019-01-02 → 2022-01-02 | 2022-01-02 → 2023-01-02 | 2.303 | 4.707 | 4463.203 | -23.842 | 289 | 2.791 | 3.944 | 5559.587 | -31.021 | 306 | 0.000 | 1.239 |
| 2 | 2020-01-02 → 2023-01-02 | 2023-01-02 → 2024-01-02 | 3.512 | 3.188 | 845.555 | -37.127 | 304 | 1.122 | 1.004 | 24.827 | -16.625 | 21 | 0.315 | 0.000 |

**Dégradation baseline:** IS Sharpe moyen = 2.632, OOS Sharpe moyen = 3.798

**Dégradation ré-optimisée:** IS Sharpe moyen = 1.412, OOS Sharpe moyen = 2.037

**PBO moyen:** 0.378  (seuil critique: 0.5)

**DSR moyen:** 0.413

---

## NVS

| Fold | IS | OOS | Sharpe IS (base) | Sharpe OOS (base) | CAGR OOS (base) | MDD OOS (base) | Trades OOS (base) | Sharpe IS (réopt) | Sharpe OOS (réopt) | CAGR OOS (réopt) | MDD OOS (réopt) | Trades OOS (réopt) | PBO | DSR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 2018-01-02 → 2021-01-02 | 2021-01-02 → 2022-01-02 | 3.738 | 1.043 | 71.997 | -47.743 | 448 | 1.385 | -2.036 | -84.822 | -87.151 | 148 | 0.047 | 0.000 |
| 1 | 2019-01-02 → 2022-01-02 | 2022-01-02 → 2023-01-02 | 2.157 | 4.208 | 4295.026 | -36.212 | 358 | 0.730 | -0.658 | -5.797 | -11.278 | 9 | 0.859 | 0.000 |
| 2 | 2020-01-02 → 2023-01-02 | 2023-01-02 → 2024-01-02 | 2.986 | 3.588 | 1452.460 | -28.003 | 357 | 0.469 | -0.605 | -9.216 | -12.930 | 28 | 0.808 | 0.000 |

**Dégradation baseline:** IS Sharpe moyen = 2.960, OOS Sharpe moyen = 2.946

**Dégradation ré-optimisée:** IS Sharpe moyen = 0.862, OOS Sharpe moyen = -1.099

**PBO moyen:** 0.571  (seuil critique: 0.5)

**DSR moyen:** 0.000

---

## GMAB

| Fold | IS | OOS | Sharpe IS (base) | Sharpe OOS (base) | CAGR OOS (base) | MDD OOS (base) | Trades OOS (base) | Sharpe IS (réopt) | Sharpe OOS (réopt) | CAGR OOS (réopt) | MDD OOS (réopt) | Trades OOS (réopt) | PBO | DSR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 2020-01-02 → 2023-01-02 | 2023-01-02 → 2024-01-02 | 2.092 | 2.870 | 805.028 | -35.770 | 305 | 0.615 | 1.317 | 9.218 | -2.994 | 1 | 0.498 | 0.000 |

**Dégradation baseline:** IS Sharpe moyen = 2.092, OOS Sharpe moyen = 2.870

**Dégradation ré-optimisée:** IS Sharpe moyen = 0.615, OOS Sharpe moyen = 1.317

**PBO moyen:** 0.498  (seuil critique: 0.5)

**DSR moyen:** 0.000

---

## Synthèse Globale

- **Baseline fixe** — Sharpe OOS moyen sur tous les actifs: 2.779 (min=0.672, max=4.707)
- **Ré-optimisée** — Sharpe OOS moyen: 0.700 (min=-2.036, max=3.944)
- **PBO moyen:** 0.437  → Risque modéré
- **DSR moyen:** 0.142  → Significativité statistique douteuse

### Verdict

**CONDITIONAL-GO** — Les performances OOS sont positives mais la granularité 5m limite la confiance. Recommandation: (1) collecter des données 1m, (2) valider sur une période hold-out indépendante, (3) tester en paper trading avant mise en production.