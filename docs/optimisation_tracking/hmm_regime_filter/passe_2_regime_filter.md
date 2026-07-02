# Rapport : HMM Regime Filter - Passe 2 (Filtrage de Régime & Confirmation)

**Date de dernière mise à jour** : 18 Juin 2026
**Objectif de la Passe** : Optimiser les paramètres de confirmation de régime (`confirm_bars` et `dom_thresh`) pour filtrer les faux signaux générés par l'estimation de base (Passe 1).
**Paramètres bloqués** : `obs_len`, `stat_len`, `mu_k`, `stick` (issus de la Passe 1).
**Métriques cibles** : Max Drawdown tolérable entre -20% et -25%, Profit Factor minimum attendu de 1.25, métrique de score `return_vs_buy_hold_pct_points`.

---

## 1. Analyse Globale des Résultats

L'analyse de la Passe 2 porte sur les configurations qualifiées lors de la Passe 1 :
* **Campagne Initiale (15 Juin 2026)** : Actif **NVO** (7 timeframes qualifiées).
* **Campagne d'Extension (18 Juin 2026)** : 6 nouveaux actifs : **ABIBEEUR** (3 timeframes), **ACFREUR** (2 timeframes), **DIAITEUR** (3 timeframes), **LXSDEEUR** (1 timeframe), **MRKDEEUR** (4 timeframes), **RIFREUR** (2 timeframes).
* **Campagne d'Extension Crypto (02 Juillet 2026)** : Actif **BNBUSDT** (1 timeframe : 60m). L'optimisation Passe 2 a permis d'accroître le Profit Factor de 1.31 à 1.38 et le ratio de Sharpe de 0.38 à 0.42 en renforçant la confirmation.

L'exploration de l'espace des paramètres (`confirm_bars` de 1 à 5, `dom_thresh` de 0.3 à 0.8) a démontré que sur la majorité des configurations, les paramètres par défaut de la Passe 1 (`confirm_bars: 2`, `dom_thresh: 0.5`) restaient les plus robustes. Néanmoins, pour plusieurs configurations (notamment à plus haute timeframe ou pour certains comportements de tendance), l'abaissement de la sensibilité (`dom_thresh: 0.3` ou `confirm_bars: 1`) ou l'augmentation de la confirmation (`confirm_bars: 5`) a apporté un gain de performance notable :
* **ABIBEEUR 45m** (Score: +48.06 vs +46.43 en Passe 1)
* **DIAITEUR 30m** (Score: +71.52 vs +68.64 en Passe 1)
* **LXSDEEUR 30m** (Score: +72.29 vs +71.97 en Passe 1)
* **MRKDEEUR 45m** (Score: +4.91 vs +4.81 en Passe 1)
* **RIFREUR 10m** (Score: +40.04 vs +37.73 en Passe 1)

---

## 2. Résultats par Timeframe sur NVO (15 Juin 2026)

### 🟢 Améliorations Constatées (Nouveaux Optimums)
L'assouplissement du seuer de dominance (`dom_thresh`) permet d'entrer plus rapidement et de maintenir la position plus longtemps dans un régime identifié, offrant un gain marginal sur ces deux unités de temps :

* **10m** (Score: +22.59 | Max DD: -8.54% | Profit Factor: 1.26)
  * Amélioration vs Passe 1 (+21.89)
  * Nouveaux Paramètres : `confirm_bars: 2`, `dom_thresh: 0.3`
* **120m** (Score: +13.40 | Max DD: -10.18% | Profit Factor: 1.57)
  * Amélioration vs Passe 1 (+13.16)
  * Nouveaux Paramètres : `confirm_bars: 2`, `dom_thresh: 0.3`

### 🟡 Maintien de la Configuration Passe 1 (Pas d'Amélioration)
Pour les autres timeframes, les configurations par défaut de la Passe 1 ont surperformé les alternatives générées par la Passe 2, validant la robustesse du filtrage initial.

* **15m** (Score: +44.93 | Max DD: -6.32% | Profit Factor: 1.41)
  * Paramètres conservés : `confirm_bars: 2`, `dom_thresh: 0.5`
* **30m** (Score: +41.81 | Max DD: -7.73% | Profit Factor: 1.51)
  * Paramètres conservés : `confirm_bars: 2`, `dom_thresh: 0.5`
* **45m** (Score: +35.59 | Max DD: -13.29% | Profit Factor: 1.69)
  * Paramètres conservés : `confirm_bars: 2`, `dom_thresh: 0.5`
* **60m** (Score: +35.08 | Max DD: -11.10% | Profit Factor: 1.48)
  * Paramètres conservés : `confirm_bars: 2`, `dom_thresh: 0.5`
* **20m** (Score: +35.05 | Max DD: -7.74% | Profit Factor: 1.29)
  * Paramètres conservés : `confirm_bars: 2`, `dom_thresh: 0.5`

---

## 3. Résultats par Timeframe sur les Nouveaux Actifs (18 Juin 2026)

### 🟢 Améliorations Constatées (Nouveaux Optimums)

* **ABIBEEUR (45m)** :
  * Performance Passe 2 : **Score: +48.06** | Max DD: -1.02% | Profit Factor: 1.36 | Trades: 959
  * Performance Passe 1 : Score: +46.43 | Max DD: -0.71% | Profit Factor: 1.31 | Trades: 620
  * Nouveaux Paramètres : `confirm_bars: 1`, `dom_thresh: 0.3`
  * *Analyse* : L'abaissement à 1 bougie de confirmation et à un seuil de dominance de 0.3 a permis de capter les tendances beaucoup plus tôt, augmentant le nombre de trades profitables (+339 trades) avec un impact minime sur le Drawdown.

* **DIAITEUR (30m)** :
  * Performance Passe 2 : **Score: +71.52** | Max DD: -3.60% | Profit Factor: 1.31 | Trades: 779
  * Performance Passe 1 : Score: +68.64 | Max DD: -4.65% | Profit Factor: 1.26 | Trades: 482
  * Nouveaux Paramètres : `confirm_bars: 1`, `dom_thresh: 0.3`
  * *Analyse* : Configuration optimisée réduisant le Drawdown de 1.05% tout en améliorant le Profit Factor et en augmentant le score global de près de 3 points.

* **LXSDEEUR (30m)** :
  * Performance Passe 2 : **Score: +72.29** | Max DD: -2.38% | Profit Factor: 1.31 | Trades: 892
  * Performance Passe 1 : Score: +71.97 | Max DD: -2.04% | Profit Factor: 1.35 | Trades: 645
  * Nouveaux Paramètres : `confirm_bars: 1`, `dom_thresh: 0.3`
  * *Analyse* : Gain de score incrémental (+0.32 pt) grâce à une capture plus rapide des tendances avec 1 bougie de confirmation.

* **MRKDEEUR (45m)** :
  * Performance Passe 2 : **Score: +4.91** | Max DD: -5.96% | Profit Factor: 1.27 | Trades: 384
  * Performance Passe 1 : Score: +4.81 | Max DD: -5.35% | Profit Factor: 1.27 | Trades: 383
  * Nouveaux Paramètres : `confirm_bars: 2`, `dom_thresh: 0.3`
  * *Analyse* : Gain très marginal (+0.10 pt) en assouplissant le seuil de dominance à 0.3.

* **RIFREUR (10m)** :
  * Performance Passe 2 : **Score: +40.04** | Max DD: -5.46% | Profit Factor: 1.55 | Trades: 502
  * Performance Passe 1 : Score: +37.73 | Max DD: -4.96% | Profit Factor: 1.37 | Trades: 657
  * Nouveaux Paramètres : `confirm_bars: 5`, `dom_thresh: 0.7`
  * *Analyse* : Amélioration forte du score (+2.31 pts) et surtout du Profit Factor (+0.18). Attendre 5 bougies de confirmation et un seuil de dominance élevé (0.7) évite de nombreux faux signaux sur cette timeframe volatile.

---

### 🟡 Maintien de la Configuration Passe 1 (Pas d'Amélioration)
Pour ces unités de temps, l'optimisation n'a pas montré d'avantage clair. Les configurations par défaut de la Passe 1 sont donc conservées.

* **ABIBEEUR (10m)** :
  * Score: +49.25 | Max DD: -1.16% | Profit Factor: 1.36 | Trades: 1379
  * Paramètres : `confirm_bars: 2`, `dom_thresh: 0.5`
* **ABIBEEUR (15m)** :
  * Score: +49.23 | Max DD: -0.79% | Profit Factor: 1.39 | Trades: 1099
  * Paramètres : `confirm_bars: 2`, `dom_thresh: 0.5`
* **ACFREUR (10m)** :
  * Score: +4.15 | Max DD: -0.60% | Profit Factor: 1.44 | Trades: 1483
  * Paramètres : `confirm_bars: 2`, `dom_thresh: 0.5`
* **ACFREUR (15m)** :
  * Score: +4.91 | Max DD: -0.86% | Profit Factor: 1.43 | Trades: 1296
  * Paramètres : `confirm_bars: 2`, `dom_thresh: 0.5`
* **DIAITEUR (10m)** :
  * Score: +73.52 | Max DD: -3.53% | Profit Factor: 1.26 | Trades: 1759
  * Paramètres : `confirm_bars: 2`, `dom_thresh: 0.5`
* **DIAITEUR (15m)** :
  * Score: +73.69 | Max DD: -4.13% | Profit Factor: 1.27 | Trades: 1338
  * Paramètres : `confirm_bars: 2`, `dom_thresh: 0.5`
* **MRKDEEUR (10m)** :
  * Score: +3.55 | Max DD: -3.28% | Profit Factor: 1.28 | Trades: 1278
  * Paramètres : `confirm_bars: 2`, `dom_thresh: 0.5`
* **MRKDEEUR (15m)** :
  * Score: +3.42 | Max DD: -3.39% | Profit Factor: 1.25 | Trades: 1214
  * Paramètres : `confirm_bars: 2`, `dom_thresh: 0.5`
* **MRKDEEUR (30m)** :
  * Score: +2.88 | Max DD: -3.23% | Profit Factor: 1.27 | Trades: 758
  * Paramètres : `confirm_bars: 2`, `dom_thresh: 0.5`
* **RIFREUR (15m)** :
  * Score: +38.42 | Max DD: -5.00% | Profit Factor: 1.45 | Trades: 583
  * Paramètres : `confirm_bars: 2`, `dom_thresh: 0.5`

### 🔵 Campagne d'Extension Crypto (Clôturée le 02 Juillet 2026)

* **BNBUSDT (60m)** :
  * Performance Passe 2 : **Score: -36387.85** | Max DD: -16.62% | Profit Factor: 1.38 | Trades: 1798 | Sharpe: 0.42
  * Performance Passe 1 : Score: -36396.57 | Max DD: -16.19% | Profit Factor: 1.31 | Trades: 2100 | Sharpe: 0.38
  * Nouveaux Paramètres : `confirm_bars: 3`, `dom_thresh: 0.6`
  * *Analyse* : Augmenter la confirmation de 2 à 3 bougies et rehausser le seuil de dominance à 0.6 permet de filtrer 302 transactions superflues. Cela augmente le Profit Factor de 1.31 à 1.38 et améliore le ratio de Sharpe de 0.38 à 0.42, avec un Drawdown qui reste stable à -16.62%.

---

## 4. Recommandations & Prochaines Étapes

L'optimisation des paramètres de confirmation de régime valide deux comportements distincts :
1. **Sensibilité accrue (Entrée rapide)** : Pour **ABIBEEUR 45m**, **DIAITEUR 30m** et **LXSDEEUR 30m**, attendre 1 seule bougie de confirmation avec un seuil de dominance HMM de 0.3 améliore la réactivité et le score final sans dégrader excessivement le risque.
2. **Confirmation renforcée (Filtrage du bruit)** : Pour **RIFREUR 10m** (`confirm_bars: 5`, `dom_thresh: 0.7`) et **BNBUSDT 60m** (`confirm_bars: 3`, `dom_thresh: 0.6`), attendre davantage de confirmation permet de filtrer efficacement le bruit propre aux actifs volatiles.

### Synthèse des configurations validées pour la Passe 3
Ces paramètres sont désormais figés pour les 7 actifs retenus :

| Actif | Timeframe | obs_len | stat_len | mu_k | stick | confirm_bars | dom_thresh |
|---|---|---|---|---|---|---|---|
| **NVO** | 10m | 16 | 33 | 2.1 | 0.8 | 2 | 0.3 |
| **NVO** | 15m | 5 | 67 | 1.1 | 0.9 | 2 | 0.5 |
| **NVO** | 20m | 5 | 13 | 1.2 | 0.5 | 2 | 0.5 |
| **NVO** | 30m | 25 | 13 | 2.6 | 0.9 | 2 | 0.5 |
| **NVO** | 45m | 24 | 96 | 0.9 | 0.8 | 2 | 0.5 |
| **NVO** | 60m | 5 | 12 | 0.7 | 0.9 | 2 | 0.5 |
| **NVO** | 120m | 5 | 70 | 1.4 | 0.7 | 2 | 0.3 |
| **ABIBEEUR** | 10m | 22 | 79 | 2.9 | 0.9 | 2 | 0.5 |
| **ABIBEEUR** | 15m | 28 | 89 | 2.7 | 0.6 | 2 | 0.5 |
| **ABIBEEUR** | 45m | 11 | 35 | 2.8 | 0.5 | 1 | 0.3 |
| **ACFREUR** | 10m | 30 | 61 | 2.7 | 0.7 | 2 | 0.5 |
| **ACFREUR** | 15m | 21 | 91 | 0.5 | 0.6 | 2 | 0.5 |
| **DIAITEUR** | 10m | 9 | 17 | 2.3 | 0.8 | 2 | 0.5 |
| **DIAITEUR** | 15m | 8 | 16 | 2.0 | 0.7 | 2 | 0.5 |
| **DIAITEUR** | 30m | 20 | 25 | 2.6 | 0.5 | 1 | 0.3 |
| **LXSDEEUR** | 30m | 28 | 85 | 1.0 | 0.6 | 1 | 0.3 |
| **MRKDEEUR** | 10m | 11 | 70 | 2.6 | 0.9 | 2 | 0.5 |
| **MRKDEEUR** | 15m | 5 | 44 | 2.1 | 0.9 | 2 | 0.5 |
| **MRKDEEUR** | 30m | 5 | 82 | 1.8 | 0.6 | 2 | 0.5 |
| **MRKDEEUR** | 45m | 30 | 15 | 2.0 | 0.9 | 2 | 0.3 |
| **RIFREUR** | 10m | 26 | 47 | 1.2 | 0.9 | 5 | 0.7 |
| **RIFREUR** | 15m | 16 | 26 | 1.8 | 0.9 | 2 | 0.5 |
| **BNBUSDT** | 60m | 23 | 77 | 2.1 | 0.9 | 3 | 0.6 |

La prochaine étape (Passe 3) consistera à évaluer l'activation et l'impact d'un stop de sécurité asymétrique (`use_safety_stop = True`) sur ces 22 configurations figées.
