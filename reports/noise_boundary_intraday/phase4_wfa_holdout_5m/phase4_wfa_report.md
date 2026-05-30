# Phase 4 — Validation Hold-out 1m (8 Tickers EUR/CHF/DKK/USD)

**Date d'exécution:** 2026-05-22 07:35 UTC
**Fenêtres:** rolling IS/OOS (2y/1y par défaut, 1y/1y pour ZEAL.CO)
**Ré-optimisation:** Non (baseline fixe uniquement)

---

## SAP

*Config: 2y IS / 1y OOS, end=2025-01-01*

| Fold | IS | OOS | Sharpe IS (base) | Sharpe OOS (base) | CAGR OOS (base) | MDD OOS (base) | Trades OOS (base) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | 2021-04-16 → 2023-04-16 | 2023-04-16 → 2024-04-16 | 0.331 | 0.615 | 39.242 | -14.273 | 258 |

**Dégradation baseline:** IS Sharpe moyen = 0.331, OOS Sharpe moyen = 0.615

---

## LOGI

*Config: 2y IS / 1y OOS, end=2025-01-01*

| Fold | IS | OOS | Sharpe IS (base) | Sharpe OOS (base) | CAGR OOS (base) | MDD OOS (base) | Trades OOS (base) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | 2021-06-17 → 2023-06-17 | 2023-06-17 → 2024-06-17 | 0.011 | 0.737 | 0.487 | -0.140 | 2 |

**Dégradation baseline:** IS Sharpe moyen = 0.011, OOS Sharpe moyen = 0.737

---

## Synthèse Globale

- **Baseline fixe** — Sharpe OOS moyen sur tous les actifs: 0.676 (min=0.615, max=0.737)

### Par devise

- **CHF** — Sharpe OOS moyen: 0.737 (min=0.737, max=0.737, n=1 folds)
- **EUR** — Sharpe OOS moyen: 0.615 (min=0.615, max=0.615, n=1 folds)

### Verdict

**CONDITIONAL-GO** — Les performances OOS sur granularité 1m sont positives. Recommandation: (1) ajuster les paramètres pour les devises non-EUR si dégradation, (2) tester en paper trading avant mise en production.