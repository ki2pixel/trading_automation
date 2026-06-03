# Synthèse Stratégique : Adaptive Volatility Trend

**Statut Actuel** : Optimisation (Passe 1 et Passe 2) totalement achevée. Configurations finales validées pour NVS et GMAB.  
**Prochaine Étape** : Intégration en production live.

---

## 1. État de la Recherche

La stratégie **Adaptive Volatility Trend** est une approche de suivi de tendance qui adapte dynamiquement ses signaux à la volatilité du marché (basée sur l'ATR). S'agissant d'une stratégie de Catégorie B, son optimisation a été divisée en deux passes :

La **Passe 1** a prouvé l'efficacité de l'indicateur core (sans filtres) sur de nombreux timeframes pour **NVS**, ainsi que sur le 5m pour **GMAB**. Tous les autres actifs ont été écartés car l'indicateur générait beaucoup trop de faux signaux en période de consolidation pour eux.

La **Passe 2** (Filtres RSI & Volume) a produit deux constats majeurs :
* **Sur le court-terme (GMAB 5m, NVS 10m et 15m)** : L'ajout des filtres (spécialement le RSI, et le Volume pour le 15m) est un succès spectaculaire. Ils filtrent près d'un tiers des trades de type "whipsaw" et propulsent la rentabilité.
* **Sur le swing/moyen-terme (NVS 45m, 60m)** : Les filtres ont été rejetés par l'optimiseur. L'indicateur se suffit à lui-même sur les bougies longues pour maintenir de forts Profit Factors sans se faire parasiter par le bruit intraday.

---

## 2. Planification et Intégration (Setups Validés)

Les configurations suivantes ont franchi toutes les étapes d'optimisation et sont déclarées **Viables pour la Production** :

### Setups avec Filtres (Court-Terme)
| Actif | TF | `length` | `atr_len` | `atr_mult` | `use_rsi` | `rsi_len` | `rsi_OB` | `rsi_OS` | `use_vol` | Score P2 |
|---|---|---|---|---|---|---|---|---|---|---|
| **NVS** | 15m | 30 | 21 | 1.6 | **Oui** | 10 | 78 | 27 | **Oui** | +20.86% |
| **NVS** | 10m | 26 | 11 | 2.0 | **Oui** | 17 | 75 | 36 | Non | +15.92% |
| **GMAB**| 5m | 36 | 28 | 3.2 | **Oui** | 18 | 80 | 20 | Non | +11.02% |

### Setups Sans Filtres (Swing)
| Actif | TF | `length` | `atr_len` | `atr_mult` | Score P2 | PF |
|---|---|---|---|---|---|---|
| **NVS** | 45m | 22 | 12 | 2.2 | +12.62% | 3.12 |
| **NVS** | 60m | 17 | 7 | 3.7 | +11.57% | 3.31 |

*(Le setup NVS 20m a également un score positif mais les ratios des autres timeframes sont jugés plus pertinents pour un déploiement diversifié).*

### Étape Suivante
Le cycle d'optimisation pour `adaptive_volatility_trend` est clos. L'étape suivante consiste à intégrer ces setups exacts dans les dictionnaires de production du moteur de trading en direct.
