# Synthèse Stratégique : HMM Regime Filter

**Statut Actuel** : Optimisation Complète et Terminée (Passes 1, 2 et 3 validées).
**Prochaine Étape** : Déploiement en production ou passage à une nouvelle stratégie.

---

## 1. État de la Recherche

La stratégie **HMM Regime Filter** utilise des modèles de Markov cachés pour estimer les régimes de marché (tendance vs range). En tant que stratégie de Catégorie C (3 passes), l'optimisation s'est effectuée en trois étapes :
1. L'estimation de base (Passe 1 : `obs_len`, `stat_len`, `mu_k`, `stick`).
2. Le filtrage de régime (Passe 2 : `confirm_bars`, `dom_thresh`).
3. Les signaux asymétriques et sorties nettes (Passe 3 : `use_safety_stop`, `take_profit_net_percent`, `stop_loss_net_percent`).

Les résultats cumulés de l'ensemble de la campagne montrent que :
* **NVO** est l'unique actif sur lequel un Edge clair a été identifié.
* L'ajout d'un **Stop Loss strict de 1.0%** en Passe 3 a drastiquement augmenté la rentabilité du modèle, prouvant que le point faible du HMM était sa lenteur à infirmer un faux signal. En coupant les pertes immédiatement, on laisse courir les gains grâce à des Take Profits allant de 6.0% à 20.0% selon le timeframe.

---

## 2. Planification et Intégration

### Configurations Finales Validées (Passe 3)

#### NVO (Sur-Performance Absolue)
Les paramètres figés à l'issue de la Passe 3 pour la stratégie `hmm_regime_filter` sur NVO sont les suivants (prêts pour la production) :

* **15m** (Score: +59.40 | Max DD: -5.26% | Profit Factor: 1.51)
  * `obs_len=5`, `stat_len=67`, `mu_k=1.1`, `stick=0.9`, `confirm_bars=2`, `dom_thresh=0.5`
  * `use_safety_stop=True`, `take_profit_net_percent=10.0`, `stop_loss_net_percent=1.0`
* **30m** (Score: +71.23 | Max DD: -4.66% | Profit Factor: 1.82)
  * `obs_len=25`, `stat_len=13`, `mu_k=2.6`, `stick=0.9`, `confirm_bars=2`, `dom_thresh=0.5`
  * `use_safety_stop=False`, `take_profit_net_percent=17.0`, `stop_loss_net_percent=1.0`
* **45m** (Score: +65.25 | Max DD: -7.04% | Profit Factor: 2.20)
  * `obs_len=24`, `stat_len=96`, `mu_k=0.9`, `stick=0.8`, `confirm_bars=2`, `dom_thresh=0.5`
  * `use_safety_stop=True`, `take_profit_net_percent=18.0`, `stop_loss_net_percent=1.0`
* **60m** (Score: +70.27 | Max DD: -6.33% | Profit Factor: 1.92)
  * `obs_len=5`, `stat_len=12`, `mu_k=0.7`, `stick=0.9`, `confirm_bars=2`, `dom_thresh=0.5`
  * `use_safety_stop=False`, `take_profit_net_percent=19.0`, `stop_loss_net_percent=1.0`
* **20m** (Score: +43.14 | Max DD: -7.25% | Profit Factor: 1.33)
  * `obs_len=5`, `stat_len=13`, `mu_k=1.2`, `stick=0.5`, `confirm_bars=2`, `dom_thresh=0.5`
  * `use_safety_stop=False`, `take_profit_net_percent=9.0`, `stop_loss_net_percent=1.0`
* **10m** (Score: +29.45 | Max DD: -7.39% | Profit Factor: 1.29)
  * `obs_len=16`, `stat_len=33`, `mu_k=2.1`, `stick=0.8`, `confirm_bars=2`, `dom_thresh=0.3`
  * `use_safety_stop=False`, `take_profit_net_percent=6.0`, `stop_loss_net_percent=1.0`
* **120m** (Score: +29.72 | Max DD: -9.02% | Profit Factor: 1.91)
  * `obs_len=5`, `stat_len=70`, `mu_k=1.4`, `stick=0.7`, `confirm_bars=2`, `dom_thresh=0.3`
  * `use_safety_stop=True`, `take_profit_net_percent=20.0`, `stop_loss_net_percent=1.0`

### Clôture
La stratégie **HMM Regime Filter** est officiellement validée. Les résultats démontrent une excellente capacité à extraire des rendements avec des Drawdowns très contrôlés (sous les -10% dans toutes les configurations) grâce à l'association d'un modèle statistique lourd (Markov) et d'un money management strict (SL à 1%).
