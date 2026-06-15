# Rapport : HMM Regime Filter - Passe 1 (Estimation des États (Markov))

**Date d'analyse** : 15 Juin 2026
**Objectif de la Passe** : Optimiser les paramètres d'état caché de Markov (`obs_len`, `stat_len`, `mu_k`, `stick`) pour identifier correctement les régimes de marché.
**Paramètres bloqués** : `confirm_bars = 2`, `dom_thresh = 0.5`.
**Métriques cibles** : Max Drawdown tolérable entre -20% et -25% (les tirages inférieurs en valeur absolue sont acceptés et encouragés), Profit Factor minimum attendu de 1.25, métrique de score `return_vs_buy_hold_pct_points`.

---

## 1. Analyse Globale des Résultats

L'analyse globale a permis de traiter **17 237 itérations éligibles** sur l'ensemble des rapports générés pour la stratégie `hmm_regime_filter`.
Il apparaît que ce filtre de régime Markovien a du mal à générer de l'Alpha sur une majorité de symboles (les scores de sur-performance étant largement négatifs). Seul un actif (NVO) se détache avec une sur-performance prononcée et de nombreuses configurations valides.

---

## 2. Résultats par Catégorie d'Actifs

### 🟢 Les Sur-Performants (Edge Identifié)
Un seul actif présente un edge clair, validé par une sur-performance absolue face au Buy & Hold dans les limites fixées de Max Drawdown et Profit Factor.

* **NVO** : Affiche une sur-performance notable sur plusieurs unités de temps.
  * **15m** (Score: +44.93 | Max DD: -6.32% | Profit Factor: 1.41)
    * Paramètres : `obs_len: 5`, `stat_len: 67`, `mu_k: 1.1`, `stick: 0.9`
  * **30m** (Score: +41.81 | Max DD: -7.73% | Profit Factor: 1.51)
    * Paramètres : `obs_len: 25`, `stat_len: 13`, `mu_k: 2.6`, `stick: 0.9`
  * **45m** (Score: +35.59 | Max DD: -13.29% | Profit Factor: 1.69)
    * Paramètres : `obs_len: 24`, `stat_len: 96`, `mu_k: 0.9`, `stick: 0.8`
  * **60m** (Score: +35.08 | Max DD: -11.10% | Profit Factor: 1.48)
    * Paramètres : `obs_len: 5`, `stat_len: 12`, `mu_k: 0.7`, `stick: 0.9`
  * **20m** (Score: +35.05 | Max DD: -7.74% | Profit Factor: 1.29)
    * Paramètres : `obs_len: 5`, `stat_len: 13`, `mu_k: 1.2`, `stick: 0.5`
  * **10m** (Score: +21.89 | Max DD: -14.77% | Profit Factor: 1.25)
    * Paramètres : `obs_len: 16`, `stat_len: 33`, `mu_k: 2.1`, `stick: 0.8`
  * **120m** (Score: +13.16 | Max DD: -10.21% | Profit Factor: 1.58)
    * Paramètres : `obs_len: 5`, `stat_len: 70`, `mu_k: 1.4`, `stick: 0.7`

### 🔴 Les Rejetés (Absence d'Edge)
Tous les autres actifs sont rejetés en raison de performances insuffisantes ou de sous-performance marquée par rapport au Buy & Hold. Notamment :
* **AMS.MC** : Sous-performance significative sur l'ensemble des timeframes (Meilleur score : -51.58 en 45m).
* **EVD.DE** : Sous-performance (Scores stables autour de -31).
* **FPE.DE** : Sous-performance modérée (Meilleur score : -3.77 en 120m).
* **GMAB** : Sous-performance (Scores autour de -26 à -29).
* **LOGI** : Forte sous-performance (Scores proches de -480).
* **NVS** : Sous-performance (Meilleur score : -13.46 en 15m).
* **SAP** : Sous-performance importante (Scores autour de -190).
* **SHL.DE** : Sous-performance (Scores autour de -124 à -134).
* **ZEAL.CO** : Sous-performance (Scores allant de -57 à -129).

---

## 3. Recommandations

L'optimisation des états du modèle de Markov caché (HMM) confirme que l'approche `hmm_regime_filter` trouve un edge de momentum/réversion valide uniquement sur **NVO**.
Les configurations sur NVO (10m, 15m, 20m, 30m, 45m, 60m, 120m) sont retenues pour servir de base à la Passe 2 (Filtrage de Régime & Confirmation).
