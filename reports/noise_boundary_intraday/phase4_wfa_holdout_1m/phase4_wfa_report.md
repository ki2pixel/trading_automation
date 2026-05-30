# Phase 4 — Validation Hold-out 1m (8 Tickers EUR/CHF/DKK/USD)

**Date d'exécution:** 2026-05-22 07:39 UTC
**Fenêtres:** rolling IS/OOS (2y/1y par défaut, 1y/1y pour ZEAL.CO)
**Ré-optimisation:** Non (baseline fixe uniquement)

---

## SAP

*Config: 2y IS / 1y OOS, end=2025-01-01*

| Fold | IS | OOS | Sharpe IS (base) | Sharpe OOS (base) | CAGR OOS (base) | MDD OOS (base) | Trades OOS (base) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | 2021-04-16 → 2023-04-16 | 2023-04-16 → 2024-04-16 | 0.182 | 0.571 | 38.939 | -15.531 | 294 |

**Dégradation baseline:** IS Sharpe moyen = 0.182, OOS Sharpe moyen = 0.571

---

## LOGI

*Config: 2y IS / 1y OOS, end=2025-01-01*

| Fold | IS | OOS | Sharpe IS (base) | Sharpe OOS (base) | CAGR OOS (base) | MDD OOS (base) | Trades OOS (base) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | 2021-06-17 → 2023-06-17 | 2023-06-17 → 2024-06-17 | 0.048 | 0.210 | 5.317 | -13.569 | 23 |

**Dégradation baseline:** IS Sharpe moyen = 0.048, OOS Sharpe moyen = 0.210

---

## Synthèse Globale

- **Baseline fixe** — Sharpe OOS moyen sur tous les actifs: 0.390 (min=0.210, max=0.571)

### Par devise

- **CHF** — Sharpe OOS moyen: 0.210 (min=0.210, max=0.210, n=1 folds)
- **EUR** — Sharpe OOS moyen: 0.571 (min=0.571, max=0.571, n=1 folds)

### Verdict

**NO-GO** — Le Sharpe OOS moyen est inférieur à 0.5, insuffisant pour le live.