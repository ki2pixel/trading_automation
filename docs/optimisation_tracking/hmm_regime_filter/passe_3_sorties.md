# Rapport : HMM Regime Filter - Passe 3 (Sorties & TP/SL Nettes)

**Date d'analyse** : 15 Juin 2026
**Objectif de la Passe** : Optimiser les mécanismes de sortie en testant l'activation du Stop de Sécurité dynamique (`use_safety_stop`) et l'ajout de brackets de sorties fixes (`use_net_bracket_exits`, `take_profit_net_percent`, `stop_loss_net_percent`).
**Paramètres bloqués** : L'intégralité des paramètres validés en Passe 1 et Passe 2 pour chaque timeframe sur **NVO**.
**Métriques cibles** : Maximiser le Score (Return vs Buy & Hold) tout en gardant un Profit Factor > 1.25 et un Max Drawdown sous -25%.

---

## 1. Analyse Globale des Résultats

L'ajout des brackets de sorties (`take_profit_net_percent` et `stop_loss_net_percent`) a eu un impact **spectaculaire** sur les performances de la stratégie HMM. Les scores finaux ont quasiment doublé sur les grosses unités de temps, propulsant cette stratégie parmi les plus rentables et robustes optimisées à ce jour.

**Découverte Majeure : La Coupe Rapide des Pertes**
L'optimiseur a systématiquement convergé vers un **Stop Loss fixe de 1.0%** sur absolument toutes les unités de temps. Cela démontre que si le modèle de Markov se trompe sur le régime (faux signal de tendance), il est préférable de couper la perte immédiatement à -1.0% plutôt que d'attendre un signal de retournement de la mécanique interne.

**Le Take Profit s'adapte à la volatilité**
Le Take Profit, en revanche, évolue de manière quasi-linéaire avec l'unité de temps : plus le timeframe est grand, plus on laisse courir les gains (de 6.0% sur le 10m jusqu'à 20.0% sur le 120m).

**Le Safety Stop Dynamique est divisé**
Le paramètre `use_safety_stop` (qui ajoute une couche de sortie asymétrique dynamique) a été conservé (`True`) sur le 15m, 45m et 120m, mais désactivé (`False`) sur le reste. Le Stop Loss de 1.0% faisant déjà le gros du travail de protection, ce stop dynamique s'avère souvent redondant.

---

## 2. Résultats Détaillés par Timeframe sur NVO

Voici les paramètres finaux optimisés de la Passe 3, démontrant des Drawdowns infimes et des Profit Factors exceptionnels :

* **10m** (Score: +29.45 | Max DD: -7.39% | Profit Factor: 1.29)
  * Amélioration vs Passe 2 : +6.86 points
  * `Safety Stop`: False | `TP`: 6.0% | `SL`: 1.0%
* **15m** (Score: +59.40 | Max DD: -5.26% | Profit Factor: 1.51)
  * Amélioration vs Passe 2 : +14.47 points
  * `Safety Stop`: True | `TP`: 10.0% | `SL`: 1.0%
* **20m** (Score: +43.14 | Max DD: -7.25% | Profit Factor: 1.33)
  * Amélioration vs Passe 2 : +8.09 points
  * `Safety Stop`: False | `TP`: 9.0% | `SL`: 1.0%
* **30m** (Score: +71.23 | Max DD: -4.66% | Profit Factor: 1.82)
  * Amélioration vs Passe 2 : +29.42 points
  * `Safety Stop`: False | `TP`: 17.0% | `SL`: 1.0%
* **45m** (Score: +65.25 | Max DD: -7.04% | Profit Factor: 2.20)
  * Amélioration vs Passe 2 : +29.66 points
  * `Safety Stop`: True | `TP`: 18.0% | `SL`: 1.0%
* **60m** (Score: +70.27 | Max DD: -6.33% | Profit Factor: 1.92)
  * Amélioration vs Passe 2 : +35.19 points
  * `Safety Stop`: False | `TP`: 19.0% | `SL`: 1.0%
* **120m** (Score: +29.72 | Max DD: -9.02% | Profit Factor: 1.91)
  * Amélioration vs Passe 2 : +16.32 points
  * `Safety Stop`: True | `TP`: 20.0% | `SL`: 1.0%

---

## 3. Recommandations et Clôture

La stratégie HMM Regime Filter est désormais **entièrement optimisée** sur NVO. L'intégration des brackets de sortie (Take Profit asymétrique long, Stop Loss très court à 1.0%) a révélé l'Edge final du modèle : capter les très longues tendances en coupant immédiatement les faux départs.

L'optimisation sur NVO est considérée comme un **succès total** et la campagne d'optimisation (Passes 1, 2 et 3) est **clôturée**. Les paramètres de la Passe 3 doivent être injectés dans la configuration de production finale de la stratégie.
