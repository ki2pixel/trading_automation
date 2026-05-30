# Phase 4 — Validation et Généralisation (WFA, Multi-Actifs, PBO/DSR)

**Date d'exécution:** 2026-05-18 16:01 UTC
**Fenêtres:** 3 ans IS / 1 ans OOS
**Ré-optimisation:** Non (baseline fixe uniquement)

---

## LOGI

| Fold | IS | OOS | Sharpe IS (base) | Sharpe OOS (base) | CAGR OOS (base) | MDD OOS (base) | Trades OOS (base) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 2018-01-02 → 2021-01-02 | 2021-01-02 → 2022-01-02 | 1.843 | 2.598 | 771.775 | -34.569 | 423 |
| 1 | 2019-01-02 → 2022-01-02 | 2022-01-02 → 2023-01-02 | 0.241 | 3.133 | 1182.009 | -39.568 | 344 |
| 2 | 2020-01-02 → 2023-01-02 | 2023-01-02 → 2024-01-02 | -0.244 | 2.011 | 269.746 | -62.694 | 328 |

**Dégradation baseline:** IS Sharpe moyen = 0.614, OOS Sharpe moyen = 2.581

---

## Synthèse Globale

- **Baseline fixe** — Sharpe OOS moyen sur tous les actifs: 2.581 (min=2.011, max=3.133)

### Verdict

**CONDITIONAL-GO** — Les performances OOS sont positives mais la granularité 5m limite la confiance. Recommandation: (1) collecter des données 1m, (2) valider sur une période hold-out indépendante, (3) tester en paper trading avant mise en production.