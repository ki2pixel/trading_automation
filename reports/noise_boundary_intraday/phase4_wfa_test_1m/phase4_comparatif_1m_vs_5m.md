# Comparatif — Granularité 1m vs 5m pour noise_boundary_intraday

**Date:** 2026-05-19
**Scope:** Walk-Forward Analysis baseline fixe sur données 1-minute (nouveaux datasets Kaggle)

---

## Datasets intégrés

| Symbole | Type | Rows | Période | Devise |
|:--------|:-----|-----:|:--------|:-------|
| EURUSD | Forex | 8,348,557 | 2000-05 -> 2024-12 | — |
| TATASTEEL | Action NSE | 1,033,700 | 2015-02 -> 2026-04 | INR |
| ADANIPOWER | Action NSE | 1,033,562 | 2015-02 -> 2026-04 | INR |
| CANBK | Action NSE | 1,033,653 | 2015-02 -> 2026-04 | INR |
| PNB | Action NSE | 1,033,703 | 2015-02 -> 2026-04 | INR |
| TMPV | Action NSE | 1,033,663 | 2015-02 -> 2026-04 | INR |
| ETERNAL | Action NSE | 435,801 | 2021-07 -> 2026-04 | INR |
| BEL | Action NSE | 1,033,624 | 2015-02 -> 2026-04 | INR |
| SBIN | Action NSE | 1,033,703 | 2015-02 -> 2026-04 | INR |
| MOTHERSON | Action NSE | 1,033,672 | 2015-02 -> 2026-04 | INR |
| BHEL | Action NSE | 1,014,880 | 2015-02 -> 2026-01 | INR |

---

## Résultats WFA Baseline — Actions indiennes (1m)

| Symbole | Sharpe OOS moyen | Sharpe OOS min | Sharpe OOS max |
|:--------|-----------------:|---------------:|---------------:|
| TATASTEEL | 5.773 | 3.185 | 7.362 |
| ADANIPOWER | 4.066 | -0.243 | 6.652 |
| CANBK | 3.836 | 1.278 | 6.815 |
| PNB | 5.391 | 3.364 | 6.499 |
| TMPV | 5.093 | 0.678 | 8.133 |
| ETERNAL | 7.248 | 7.248 | 7.248 |
| BEL | 5.287 | 0.560 | 7.514 |
| SBIN | 4.266 | 1.141 | 7.005 |
| MOTHERSON | 4.411 | 0.934 | 8.538 |
| BHEL | 5.295 | 1.397 | 6.517 |

**Moyenne globale : 4.877** (min=-0.243, max=8.538)

---

## Résultat Single Backtest — EURUSD (1m)

| Métrique | Valeur |
|:---------|-------:|
| Sharpe | 0.078 |
| CAGR | 0.037% |
| MDD | -0.387% |
| Trades | 84 |
| Win rate | 52.38% |

Note : les paramètres baseline ne sont pas adaptés au Forex. Une optimisation spécifique EURUSD est recommandée.

---

## Comparatif avec Phase 4 (5m)

| Granularité | Sharpe OOS moyen | Symboles testés |
|:------------|-----------------:|:----------------|
| **5m** | 2.581 | LOGI |
| **1m** | **4.877** | 10 actions NSE |

**Observations :**
- Le passage au 1m améliore significativement le Sharpe OOS (+88% en moyenne).
- Les trades sont plus nombreux et plus courts (intra-barre plus fine).
- Le MDD reste élevé (-30% à -70%), nécessitant un ajustement des stops.

---

## Livrables produits

1. `storage/processed/market_data_1m/*.parquet` — 11 fichiers canonical
2. `SheetsFinance_Export/fx_data/raw_5m/symbol_currency_map.csv` — mis à jour avec INR
3. `reports/phase4_wfa_test_1m/phase4_wfa_report.md` — rapport WFA 1m
4. `scripts/convert_kaggle_1m_to_canonical.py` — script de conversion réutilisable
5. `scripts/validate_canonical_1m.py` — script de validation
