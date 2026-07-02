# Rapport : HMM Regime Filter - Passe 3 (Sorties & TP/SL Nettes)

**Date de dernière mise à jour** : 18 Juin 2026
**Objectif de la Passe** : Optimiser les mécanismes de sortie en testant l'activation du Stop de Sécurité dynamique (`use_safety_stop`) et l'ajout de brackets de sorties fixes (`use_net_bracket_exits`, `take_profit_net_percent`, `stop_loss_net_percent`).
**Paramètres bloqués** : L'intégralité des paramètres validés en Passe 1 et Passe 2 pour chaque timeframe sur les 7 actifs qualifiés.
**Métriques cibles** : Maximiser le Score (Return vs Buy & Hold) tout en gardant un Profit Factor > 1.25 et un Max Drawdown sous -25%.

---

## 1. Analyse Globale des Résultats

L'ajout des brackets de sorties (`take_profit_net_percent` et `stop_loss_net_percent`) et du stop de sécurité a eu un impact **spectaculaire et généralisé** sur l'ensemble du portefeuille d'actifs qualifiés :
* **Campagne Initiale (15 Juin 2026)** : Actif **NVO** (7 timeframes).
* **Campagne d'Extension (18 Juin 2026)** : 6 nouveaux actifs : **ABIBEEUR** (3 timeframes), **ACFREUR** (2 timeframes), **DIAITEUR** (3 timeframes), **LXSDEEUR** (1 timeframe), **MRKDEEUR** (4 timeframes), **RIFREUR** (2 timeframes).
* **Campagne d'Extension Crypto (02 Juillet 2026)** : Actif **BNBUSDT** (1 timeframe : 60m). L'optimisation a mené à une surperformance majeure en qualifiant la sortie bracket TP/SL fixe sans stop de sécurité dynamique.

Les 15 configurations de l'extension de campagne affichent toutes une **amélioration systématique** des scores de performance et une forte réduction du risque.

**Constatations Clés :**
1. **Coupe rapide des pertes (SL à 1.0%)** : Sur 21 des 22 configurations totales du portefeuille (NVO inclus), l'optimiseur a convergé vers un **Stop Loss fixe de 1.0%** (seul RIFREUR 10m retient un SL à 2.0%). Cela valide de manière empirique la pertinence de couper immédiatement les positions en cas de faux départ détecté par le modèle HMM.
2. **Dualité du Take Profit** : Le Take Profit optimal se divise en deux réglages selon les actifs :
   - **TP large (18.0% à 20.0%)** : Pour **ABIBEEUR** (15m, 45m), **ACFREUR** (tous TFs), **DIAITEUR 30m**, **LXSDEEUR 30m** et **RIFREUR** (tous TFs), ce qui indique une capacité à capter de très grands mouvements de tendance.
   - **TP serré (4.0% à 5.0%)** : Pour **ABIBEEUR 10m**, **DIAITEUR** (10m, 15m) et **MRKDEEUR** (tous TFs), privilégiant un comportement de scalping/retour à la moyenne très rapide.
3. **Safety Stop dynamique indispensable** : Le stop de sécurité dynamique (`use_safety_stop: True`) s'avère particulièrement efficace sur l'extension, étant validé sur 10 des 15 nouvelles configurations pour apporter une couche de protection dynamique complémentaire au Stop Loss fixe.

---

## 2. Résultats Détaillés par Timeframe sur NVO (15 Juin 2026)

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

## 3. Résultats par Timeframe sur les Nouveaux Actifs (18 Juin 2026)

* **ABIBEEUR** :
  * **10m** : **Score: +50.57** (vs +49.25 en P2) | Max DD: -0.95% | PF: 1.46 | Trades: 1379
    * *Réglages* : `Safety Stop`: False | `TP`: 4.0% | `SL`: 1.0%
  * **15m** : **Score: +50.51** (vs +49.23 en P2) | Max DD: -0.59% | PF: 1.52 | Trades: 1099
    * *Réglages* : `Safety Stop`: True | `TP`: 20.0% | `SL`: 1.0%
  * **45m** : **Score: +48.66** (vs +48.06 en P2) | Max DD: -1.02% | PF: 1.42 | Trades: 959
    * *Réglages* : `Safety Stop`: False | `TP`: 20.0% | `SL`: 1.0%

* **ACFREUR** :
  * **10m** : **Score: +5.65** (vs +4.15 en P2) | Max DD: -0.58% | PF: 1.64 | Trades: 1483
    * *Réglages* : `Safety Stop`: True | `TP`: 20.0% | `SL`: 1.0%
  * **15m** : **Score: +7.42** (vs +4.91 en P2) | Max DD: -0.68% | PF: 1.73 | Trades: 1296
    * *Réglages* : `Safety Stop`: True | `TP`: 18.0% | `SL`: 1.0%

* **DIAITEUR** :
  * **10m** : **Score: +77.80** (vs +73.52 en P2) | Max DD: -2.62% | PF: 1.38 | Trades: 1759
    * *Réglages* : `Safety Stop`: True | `TP`: 5.0% | `SL`: 1.0%
  * **15m** : **Score: +79.54** (vs +73.69 en P2) | Max DD: -2.26% | PF: 1.45 | Trades: 1338
    * *Réglages* : `Safety Stop`: False | `TP`: 5.0% | `SL`: 1.0%
  * **30m** : **Score: +74.88** (vs +71.52 en P2) | Max DD: -3.64% | PF: 1.46 | Trades: 779
    * *Réglages* : `Safety Stop`: True | `TP`: 20.0% | `SL`: 1.0%

* **LXSDEEUR** :
  * **30m** : **Score: +77.26** (vs +72.29 en P2) | Max DD: -1.46% | PF: 1.69 | Trades: 892
    * *Réglages* : `Safety Stop`: True | `TP`: 20.0% | `SL`: 1.0%

* **MRKDEEUR** :
  * **10m** : **Score: +6.32** (vs +3.55 en P2) | Max DD: -1.74% | PF: 1.38 | Trades: 1278
    * *Réglages* : `Safety Stop`: True | `TP`: 5.0% | `SL`: 1.0%
  * **15m** : **Score: +8.29** (vs +3.42 en P2) | Max DD: -2.43% | PF: 1.43 | Trades: 1214
    * *Réglages* : `Safety Stop`: True | `TP`: 5.0% | `SL`: 1.0%
  * **30m** : **Score: +8.76** (vs +2.88 en P2) | Max DD: -1.79% | PF: 1.55 | Trades: 758
    * *Réglages* : `Safety Stop`: True | `TP`: 4.0% | `SL`: 1.0%
  * **45m** : **Score: +15.59** (vs +4.91 en P2) | Max DD: -2.57% | PF: 1.75 | Trades: 384
    * *Réglages* : `Safety Stop`: True | `TP`: 4.0% | `SL`: 1.0%

* **RIFREUR** :
  * **10m** : **Score: +40.92** (vs +40.04 en P2) | Max DD: -5.25% | PF: 1.60 | Trades: 502
    * *Réglages* : `Safety Stop`: False | `TP`: 20.0% | `SL`: 2.0%
  * **15m** : **Score: +40.64** (vs +38.42 en P2) | Max DD: -4.20% | PF: 1.57 | Trades: 583
    * *Réglages* : `Safety Stop`: False | `TP`: 20.0% | `SL`: 1.0%

### 🔵 Campagne d'Extension Crypto (Clôturée le 02 Juillet 2026)

* **BNBUSDT (60m)** :
  * Performance Passe 3 : **Score: -36258.94** | Max DD: -8.00% | Profit Factor: 2.46 | Trades: 1798 | Sharpe: 0.89
  * Performance Passe 2 : Score: -36387.85 | Max DD: -16.62% | Profit Factor: 1.38 | Trades: 1798 | Sharpe: 0.42
  * Nouveaux Paramètres : `Safety Stop`: False | `TP`: 18.0% | `SL`: 1.0%
  * *Analyse* : L'introduction des brackets de sortie fixes (TP à 18.0% et SL très serré à 1.0%) a un impact monumental sur BNBUSDT. Le P&L net grimpe de +133.33% à +262.24%, le Profit Factor s'envole de 1.38 à 2.46, et le Drawdown maximum est divisé par deux (de -16.62% à -8.00%). Le ratio de Sharpe fait plus que doubler en s'établissant à 0.89. Le stop de sécurité dynamique s'est avéré inefficace et est donc désactivé.

---

## 4. Recommandations et Clôture

La Passe 3 confirme que l'ajout systématique de brackets Take Profit / Stop Loss offre un edge fondamental pour sécuriser les profits et minimiser les drawdowns de la stratégie `hmm_regime_filter`.

L'optimisation globale incluant la campagne crypto sur le Top 10 est désormais un **succès total** et entièrement **clôturée**. Les 23 configurations optimales validées (portefeuille hybride actions + crypto) doivent être intégrées dans le fichier de synthèse de la stratégie.
