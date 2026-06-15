# Rapport : HMM Regime Filter - Passe 2 (Filtrage de Régime & Confirmation)

**Date d'analyse** : 15 Juin 2026
**Objectif de la Passe** : Optimiser les paramètres de confirmation de régime (`confirm_bars` et `dom_thresh`) pour filtrer les faux signaux générés par l'estimation de base (Passe 1).
**Paramètres bloqués** : `obs_len`, `stat_len`, `mu_k`, `stick` (issus de la Passe 1).
**Métriques cibles** : Max Drawdown tolérable entre -20% et -25%, Profit Factor minimum attendu de 1.25, métrique de score `return_vs_buy_hold_pct_points`.

---

## 1. Analyse Globale des Résultats

L'analyse de la Passe 2 porte exclusivement sur les unités de temps validées de l'actif **NVO**, étant donné que les autres symboles ont été rejetés lors de la Passe 1.
L'exploration de l'espace des paramètres (`confirm_bars` de 1 à 5, `dom_thresh` de 0.3 à 0.8) a démontré que les valeurs par défaut utililisées en Passe 1 (`confirm_bars = 2` et `dom_thresh = 0.5`) étaient déjà très proches de l'optimum global sur la majorité des timeframes. Néanmoins, un abaissement de la sensibilité (`dom_thresh = 0.3`) a permis de très légères améliorations sur quelques timeframes.

---

## 2. Résultats par Timeframe sur NVO

### 🟢 Améliorations Constatées (Nouveaux Optimums)
L'assouplissement du seuil de dominance (`dom_thresh`) permet d'entrer plus rapidement et de maintenir la position plus longtemps dans un régime identifié, offrant un gain marginal sur ces deux unités de temps :

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
* **45m** (Score: +35.59 | Max DD: -13.29% | Profit Factor: 1.69)
  * Paramètres conservés : `confirm_bars: 2`, `dom_thresh: 0.5`
* **60m** (Score: +35.08 | Max DD: -11.10% | Profit Factor: 1.48)
  * Paramètres conservés : `confirm_bars: 2`, `dom_thresh: 0.5`
* **20m** (Score: +35.05 | Max DD: -7.74% | Profit Factor: 1.29)
  * Paramètres conservés : `confirm_bars: 2`, `dom_thresh: 0.5`
* **30m** (Score: +41.81 | Max DD: -7.73% | Profit Factor: 1.51)
  * Paramètres conservés : `confirm_bars: 2`, `dom_thresh: 0.5`


---

## 3. Recommandations

L'optimisation des filtres de confirmation confirme qu'attendre **2 bougies** de confirmation (`confirm_bars = 2`) est l'équilibre parfait pour éviter le bruit tout en ne ratant pas le début de tendance. Le seuil de dominance de `0.5` reste le standard, sauf sur le 10m et 120m où une sensibilité plus fine (`0.3`) améliore la capture des micro/macro mouvements.

Ces paramètres sont désormais figés. La prochaine étape (Passe 3) évaluera l'opportunité d'intégrer un Stop de Sécurité Asymétrique (`use_safety_stop`) pour ces configurations.
