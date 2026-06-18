# Synthèse Stratégique : HMM Regime Filter

**Statut Actuel** : Optimisation Complète et Terminée (Passes 1, 2 et 3 validées).
**Prochaine Étape** : Déploiement en production des configurations sélectionnées.

---

## 1. État de la Recherche

La stratégie **HMM Regime Filter** utilise des modèles de Markov cachés pour estimer les régimes de marché (tendance vs range). En tant que stratégie de Catégorie C (3 passes), l'optimisation s'est effectuée en trois étapes :
1. L'estimation de base (Passe 1 : `obs_len`, `stat_len`, `mu_k`, `stick`).
2. Le filtrage de régime (Passe 2 : `confirm_bars`, `dom_thresh`).
3. Les signaux asymétriques et sorties nettes (Passe 3 : `use_safety_stop`, `take_profit_net_percent`, `stop_loss_net_percent`).

Les campagnes cumulatives ont apporté les conclusions suivantes :
* **Portefeuille d'actifs validés** : 7 actifs affichent un Edge robuste par rapport au Buy & Hold : **NVO** (historique) et 6 nouveaux actifs (**ABIBEEUR**, **ACFREUR**, **DIAITEUR**, **LXSDEEUR**, **MRKDEEUR**, **RIFREUR**).
* **Importance du Stop Loss strict à 1%** : Dans 21 des 22 configurations validées, l'optimum global a convergé vers un Stop Loss fixe de **1.0%** (seul RIFREUR 10m utilise 2.0%). Cette protection rapide contre les faux signaux permet à la stratégie d'exploiter pleinement l'edge de tendance identifié par le modèle de Markov caché.
* **Drawdowns contrôlés** : Grâce au money management strict validé en Passe 3, le Drawdown maximum historique est contenu à des niveaux extrêmement bas (généralement inférieurs à -5% sur les nouveaux actifs).

---

## 2. Configurations Finales Validées (Passe 3)

Voici les paramètres figés à l'issue de la Passe 3 pour l'intégralité des 22 configurations éligibles (prêts pour la production) :

| Actif | TF | obs_len | stat_len | mu_k | stick | confirm_bars | dom_thresh | Safety Stop | TP % | SL % | Score | Max DD | PF |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **NVO** | 10m | 16 | 33 | 2.1 | 0.8 | 2 | 0.3 | False | 6.0% | 1.0% | +29.45 | -7.39% | 1.29 |
| **NVO** | 15m | 5 | 67 | 1.1 | 0.9 | 2 | 0.5 | True | 10.0% | 1.0% | +59.40 | -5.26% | 1.51 |
| **NVO** | 20m | 5 | 13 | 1.2 | 0.5 | 2 | 0.5 | False | 9.0% | 1.0% | +43.14 | -7.25% | 1.33 |
| **NVO** | 30m | 25 | 13 | 2.6 | 0.9 | 2 | 0.5 | False | 17.0% | 1.0% | +71.23 | -4.66% | 1.82 |
| **NVO** | 45m | 24 | 96 | 0.9 | 0.8 | 2 | 0.5 | True | 18.0% | 1.0% | +65.25 | -7.04% | 2.20 |
| **NVO** | 60m | 5 | 12 | 0.7 | 0.9 | 2 | 0.5 | False | 19.0% | 1.0% | +70.27 | -6.33% | 1.92 |
| **NVO** | 120m | 5 | 70 | 1.4 | 0.7 | 2 | 0.3 | True | 20.0% | 1.0% | +29.72 | -9.02% | 1.91 |
| **ABIBEEUR** | 10m | 22 | 79 | 2.9 | 0.9 | 2 | 0.5 | False | 4.0% | 1.0% | +50.57 | -0.95% | 1.46 |
| **ABIBEEUR** | 15m | 28 | 89 | 2.7 | 0.6 | 2 | 0.5 | True | 20.0% | 1.0% | +50.51 | -0.59% | 1.52 |
| **ABIBEEUR** | 45m | 11 | 35 | 2.8 | 0.5 | 1 | 0.3 | False | 20.0% | 1.0% | +48.66 | -1.02% | 1.42 |
| **ACFREUR** | 10m | 30 | 61 | 2.7 | 0.7 | 2 | 0.5 | True | 20.0% | 1.0% | +5.65 | -0.58% | 1.64 |
| **ACFREUR** | 15m | 21 | 91 | 0.5 | 0.6 | 2 | 0.5 | True | 18.0% | 1.0% | +7.42 | -0.68% | 1.73 |
| **DIAITEUR** | 10m | 9 | 17 | 2.3 | 0.8 | 2 | 0.5 | True | 5.0% | 1.0% | +77.80 | -2.62% | 1.38 |
| **DIAITEUR** | 15m | 8 | 16 | 2.0 | 0.7 | 2 | 0.5 | False | 5.0% | 1.0% | +79.54 | -2.26% | 1.45 |
| **DIAITEUR** | 30m | 20 | 25 | 2.6 | 0.5 | 1 | 0.3 | True | 20.0% | 1.0% | +74.88 | -3.64% | 1.46 |
| **LXSDEEUR** | 30m | 28 | 85 | 1.0 | 0.6 | 1 | 0.3 | True | 20.0% | 1.0% | +77.26 | -1.46% | 1.69 |
| **MRKDEEUR** | 10m | 11 | 70 | 2.6 | 0.9 | 2 | 0.5 | True | 5.0% | 1.0% | +6.32 | -1.74% | 1.38 |
| **MRKDEEUR** | 15m | 5 | 44 | 2.1 | 0.9 | 2 | 0.5 | True | 5.0% | 1.0% | +8.29 | -2.43% | 1.43 |
| **MRKDEEUR** | 30m | 5 | 82 | 1.8 | 0.6 | 2 | 0.5 | True | 4.0% | 1.0% | +8.76 | -1.79% | 1.55 |
| **MRKDEEUR** | 45m | 30 | 15 | 2.0 | 0.9 | 2 | 0.3 | True | 4.0% | 1.0% | +15.59 | -2.57% | 1.75 |
| **RIFREUR** | 10m | 26 | 47 | 1.2 | 0.9 | 5 | 0.7 | False | 20.0% | 2.0% | +40.92 | -5.25% | 1.60 |
| **RIFREUR** | 15m | 16 | 26 | 1.8 | 0.9 | 2 | 0.5 | False | 20.0% | 1.0% | +40.64 | -4.20% | 1.57 |

---

## 3. Clôture

La stratégie **HMM Regime Filter** est officiellement validée sur l'ensemble de son périmètre historique et étendu. L'association d'un modèle statistique de Markov de filtrage de régime, de seuils de dominance stricts, et d'un money management robuste (SL court à 1.0% combiné à des Take Profits asymétriques) a permis de dégager un excellent alpha avec des drawdowns historiques infimes (majoritairement sous les -5%).

L'optimisation globale est considérée comme un **succès complet**.
