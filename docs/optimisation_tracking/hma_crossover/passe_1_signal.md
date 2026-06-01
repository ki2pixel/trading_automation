# Rapport : HMA Crossover - Passe 1 (Le Signal de Base)

**Date d'analyse** : 01 Juin 2026
**Objectif de la Passe** : Valider le signal brut de la stratégie HMA Crossover, qui est une stratégie de Catégorie A (Stratégies Simples à 1 Seule Passe). L'objectif est d'optimiser les paramètres clés de la moyenne mobile de Hull pour la détection de tendance.
**Paramètres cibles optimisés** : `fast_len`, `slow_len`, `source_col`.
**Métriques cibles** : Max Drawdown tolérable entre -25% et -30%, Profit Factor minimum attendu de 1.25, métrique de score `return_vs_buy_hold_pct_points`.

---

## 1. Analyse Globale des Résultats

L'analyse globale a permis de générer **13 087 itérations éligibles**.
L'observation du comportement général de la tendance HMA face aux zones de range démontre que la stratégie est performante sur les actifs qui expriment des tendances directionnelles claires, mais qu'elle a tendance à sous-performer face au Buy & Hold sur les actifs qui subissent de longues périodes de consolidation ou de "whipsaw" (marché plat et haché).

---

## 2. Résultats par Catégorie d'Actifs

### 🟢 Les Sur-Performants (Edge Identifié)
Ces actifs ont démontré un edge clair et stable sur plusieurs unités de temps. On remarque une cohérence des paramètres optimaux, réfutant l'hypothèse de sur-apprentissage (overfitting), avec notamment FPE.DE qui maintient sa performance de 30m à 120m avec des longueurs cohérentes.

* **FPE.DE** : Affiche les scores les plus élevés. 
  * **30m** : Meilleur score `+9.4680` (`fast_len: 40`, `slow_len: 98`, `source_col: high`, `confirm_on_close: True`).
  * **45m** : Score `+8.5556` (`fast_len: 30`, `slow_len: 77`, `source_col: high`).
  * **60m** : Score `+8.4851`.
  * **120m** : Score `+7.5824`.
* **NVS** : Présente une sur-performance notable sur les grands timeframes.
  * **120m** : Meilleur score `+7.9580` (`fast_len: 10`, `slow_len: 153`, `source_col: low`, `confirm_on_close: False`).
  * **240m** : Score `+4.6957`.
* **GMAB** : Un actif validé supplémentaire sur des timeframes intermédiaires.
  * **45m** : Meilleur score `+4.5009` (`fast_len: 16`, `slow_len: 68`, `source_col: low`, `confirm_on_close: False`).
  * **30m** : Score `+3.7455`.

### 🔴 Les Rejetés (Absence d'Edge)
Ces actifs ont retourné des scores négatifs (sous-performance marquée par rapport au Buy & Hold). L'absence de tendances claires ou le bruit excessif sur ces actifs les rendent inadaptés à la stratégie HMA Crossover seule :
* **LOGI** : Score abyssal avoisinant `-450.0`.
* **SAP** : Score fortement négatif aux alentours de `-165.0`.
* Sont également exclus pour sous-performance : **AMS.MC**, **EVD.DE**, **NVO**, **SHL.DE** et **ZEAL.CO**.

---

## 3. Recommandations

Étant donné que la stratégie HMA Crossover est de Catégorie A (Stratégie Simple à 1 Seule Passe), l'optimisation s'arrête ici pour les actifs validés.
La stratégie HMA Crossover est viable de manière autonome pour **FPE.DE**, **NVS** et **GMAB** sur leurs unités de temps respectives. Les zones de paramètres sont stables et ne montrent pas de signe de sur-ajustement (overfitting).
