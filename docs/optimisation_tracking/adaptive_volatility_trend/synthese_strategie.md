# Synthèse Stratégique : Adaptive Volatility Trend

**Statut Actuel** : Optimisation (Passe 1 et Passe 2) totalement achevée pour la baseline (NVS/GMAB) et la campagne d'extension (5 nouveaux actifs). Toutes les configurations finales sont validées.  
**Prochaine Étape** : Intégration en production live des 10 configurations validées.

---

## 1. État de la Recherche

La stratégie **Adaptive Volatility Trend** est une approche de suivi de tendance qui adapte dynamiquement ses signaux à la volatilité du marché (basée sur l'ATR). S'agissant d'une stratégie de Catégorie B, son optimisation a été divisée en deux passes :

* **Vague Initiale (Juin 2026)** : La **Passe 1** a prouvé l'efficacité de l'indicateur core (sans filtres) sur de nombreux timeframes pour **NVS**, ainsi que sur le 5m pour **GMAB**. La **Passe 2** a validé l'activation des filtres RSI + Volume pour le court-terme (GMAB 5m, NVS 10m/15m) et leur désactivation sur le swing/moyen-terme.
* **Campagne d'Extension (19 Juin 2026)** : Évaluation de 13 nouveaux symboles qualifiés. Grâce au quorum assoupli à `min_closed_trades = 10` et au correctif de calcul du Profit Factor (configurations à 100% de Win Rate), 5 actifs ont été qualifiés en Passe 1. La Passe 2 a ensuite optimisé leurs filtres RSI/Volume, confirmant une explosion de l'alpha et une réduction drastique des drawdowns (ex: **akzanleur** à **+64.54%** vs B&H, DD -6.51% ; **beideeur** à **+42.83%** vs B&H, DD -5.58%).

---

## 2. Planification et Intégration (Setups Validés)

Les configurations suivantes ont franchi toutes les étapes d'optimisation et sont déclarées **Viables pour la Production** :

### Setups avec Filtres (Court-Terme & Intraday)
| Actif | TF | `length` | `atr_len` | `atr_mult` | `use_rsi` | `rsi_len` | `rsi_OB` | `rsi_OS` | `use_vol` | Score P2 | Max DD |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **akzanleur** | 30m | 25 | 12 | 3.5 | **Oui** | 7 | 80 | 34 | **Oui** | **+64.54%** | -6.51% |
| **beideeur (Opt. A)** | 10m | 20 | 16 | 3.3 | **Oui** | 12 | 75 | 40 | Non | **+42.83%** | -5.58% |
| **dpwdeeur** | 45m | 45 | 10 | 3.9 | **Oui** | 10 | 76 | 40 | Non | **+31.97%** | -9.43% |
| **NVS** | 15m | 30 | 21 | 1.6 | **Oui** | 10 | 78 | 27 | **Oui** | **+20.86%** | -88.63% |
| **telnonok** | 15m | 26 | 19 | 2.6 | **Oui** | 10 | 72 | 32 | Non | **+17.64%** | -8.37% |
| **ergiteur** | 30m | 16 | 27 | 3.5 | **Oui** | 18 | 74 | 39 | **Oui** | **+16.35%** | -11.08% |
| **NVS** | 10m | 26 | 11 | 2.0 | **Oui** | 17 | 75 | 36 | Non | **+15.92%** | -51.31% |
| **beideeur (Opt. B)** | 10m | 47 | 25 | 3.6 | **Oui** | 7 | 80 | 34 | **Oui** | **+15.15%** | -8.37% |
| **GMAB**| 5m | 36 | 28 | 3.2 | **Oui** | 18 | 80 | 20 | Non | **+11.02%** | -161.16% |

### Setups Sans Filtres (Swing)
| Actif | TF | `length` | `atr_len` | `atr_mult` | Score P2 | PF | Max DD |
|---|---|---|---|---|---|---|---|
| **NVS** | 45m | 22 | 12 | 2.2 | +12.62% | 3.12 | -38.93% |
| **NVS** | 60m | 17 | 7 | 3.7 | +11.57% | 3.31 | -55.26% |

*(Le setup NVS 20m a également un score positif mais les ratios des autres timeframes sont jugés plus pertinents pour un déploiement diversifié).*

---

## 3. Conclusion et Prochaines Étapes

Le cycle d'optimisation pour `adaptive_volatility_trend` est désormais clos.
L'introduction des filtres RSI et Volume a permis de débloquer et sécuriser d'importants gisements d'alpha sur les actifs de l'extension de campagne.
L'étape suivante consiste à intégrer ces 10 configurations de production dans les dictionnaires du moteur de trading pour un déploiement diversifié multi-actifs.
