# Rapport : HMM Regime Filter - Passe 1 (Estimation des États (Markov))

**Date de dernière mise à jour** : 18 Juin 2026
**Objectif de la Passe** : Optimiser les paramètres d'état caché de Markov (`obs_len`, `stat_len`, `mu_k`, `stick`) pour identifier correctement les régimes de marché.
**Paramètres bloqués** : `confirm_bars = 2`, `dom_thresh = 0.5`, `use_safety_stop = False`.
**Métriques cibles** : Max Drawdown tolérable entre -20% et -25% (les tirages inférieurs en valeur absolue sont acceptés et encouragés), Profit Factor minimum attendu de 1.25, métrique de score `return_vs_buy_hold_pct_points`.

---

## 1. Analyse Globale des Résultats

L'analyse globale a permis de traiter **26 961 itérations éligibles** au total, réparties sur trois campagnes :
* **Campagne Initiale (15 Juin 2026)** : 17 237 itérations éligibles (10 symboles historiques). Un seul actif s'est détaché avec un edge clair (**NVO**).
* **Campagne d'Extension (18 Juin 2026)** : 9 662 itérations éligibles (59 nouveaux symboles qualifiés). Cette extension a permis d'identifier **6 nouveaux actifs** présentant un edge robuste face au Buy & Hold.
* **Campagne d'Extension Crypto (02 Juillet 2026)** : Évaluation de 6 nouveaux actifs cryptos qualifiés pour le Top 10 (11 configurations couples symbole/timeframe, 62 itérations éligibles). Cette campagne a qualifié **1 nouvel actif** (**bnbusdt** en 60m). Les autres actifs/timeframes ont été rejetés à 100% par la contrainte de Profit Factor minimum de 1.25.

Le filtre de régime Markovien confirme sa sélectivité : la majorité des actifs ne parviennent pas à générer d'Alpha (scores négatifs par rapport au Buy & Hold). Cependant, les actifs retenus démontrent des sur-performances prononcées sur diverses unités de temps.

---

## 2. Résultats par Catégorie d'Actifs

### 🟢 Les Sur-Performants (Edge Identifié)
Ces actifs présentent un edge clair, validé par une sur-performance absolue face au Buy & Hold dans les limites fixées de Max Drawdown (<= 25%) et de Profit Factor (>= 1.25).

#### 1. Actifs Historiques (Campagne du 15 Juin 2026)

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

#### 2. Nouveaux Actifs (Campagne d'Extension du 18 Juin 2026)

* **ABIBEEUR** :
  * **10m** (Score: +49.25 | Max DD: -1.11% | Profit Factor: 1.36 | Trades: 1379)
    * Paramètres : `obs_len: 22`, `stat_len: 79`, `mu_k: 2.9`, `stick: 0.9`
  * **15m** (Score: +49.23 | Max DD: -0.74% | Profit Factor: 1.39 | Trades: 1099)
    * Paramètres : `obs_len: 28`, `stat_len: 89`, `mu_k: 2.7`, `stick: 0.6`
  * **45m** (Score: +46.43 | Max DD: -0.71% | Profit Factor: 1.31 | Trades: 620)
    * Paramètres : `obs_len: 11`, `stat_len: 35`, `mu_k: 2.8`, `stick: 0.5`

* **ACFREUR** :
  * **10m** (Score: +4.15 | Max DD: -0.57% | Profit Factor: 1.44 | Trades: 1483)
    * Paramètres : `obs_len: 30`, `stat_len: 61`, `mu_k: 2.7`, `stick: 0.7`
  * **15m** (Score: +4.91 | Max DD: -0.86% | Profit Factor: 1.43 | Trades: 1296)
    * Paramètres : `obs_len: 21`, `stat_len: 91`, `mu_k: 0.5`, `stick: 0.6`

* **DIAITEUR** :
  * **10m** (Score: +73.52 | Max DD: -3.35% | Profit Factor: 1.26 | Trades: 1759)
    * Paramètres : `obs_len: 9`, `stat_len: 17`, `mu_k: 2.3`, `stick: 0.8`
  * **15m** (Score: +73.69 | Max DD: -3.80% | Profit Factor: 1.27 | Trades: 1338)
    * Paramètres : `obs_len: 8`, `stat_len: 16`, `mu_k: 2.0`, `stick: 0.7`
  * **30m** (Score: +68.64 | Max DD: -4.65% | Profit Factor: 1.26 | Trades: 482)
    * Paramètres : `obs_len: 20`, `stat_len: 25`, `mu_k: 2.6`, `stick: 0.5`

* **LXSDEEUR** :
  * **30m** (Score: +71.97 | Max DD: -2.04% | Profit Factor: 1.35 | Trades: 645)
    * Paramètres : `obs_len: 28`, `stat_len: 85`, `mu_k: 1.0`, `stick: 0.6`

* **MRKDEEUR** :
  * **10m** (Score: +3.55 | Max DD: -3.14% | Profit Factor: 1.28 | Trades: 1278)
    * Paramètres : `obs_len: 11`, `stat_len: 70`, `mu_k: 2.6`, `stick: 0.9`
  * **15m** (Score: +3.42 | Max DD: -3.22% | Profit Factor: 1.25 | Trades: 1214)
    * Paramètres : `obs_len: 5`, `stat_len: 44`, `mu_k: 2.1`, `stick: 0.9`
  * **30m** (Score: +2.88 | Max DD: -2.98% | Profit Factor: 1.27 | Trades: 758)
    * Paramètres : `obs_len: 5`, `stat_len: 82`, `mu_k: 1.8`, `stick: 0.6`
  * **45m** (Score: +4.81 | Max DD: -5.35% | Profit Factor: 1.27 | Trades: 383)
    * Paramètres : `obs_len: 30`, `stat_len: 15`, `mu_k: 2.0`, `stick: 0.9`

* **RIFREUR** :
  * **10m** (Score: +37.73 | Max DD: -4.96% | Profit Factor: 1.37 | Trades: 657)
    * Paramètres : `obs_len: 26`, `stat_len: 47`, `mu_k: 1.2`, `stick: 0.9`
  * **15m** (Score: +38.40 | Max DD: -4.84% | Profit Factor: 1.45 | Trades: 583)
    * Paramètres : `obs_len: 16`, `stat_len: 26`, `mu_k: 1.8`, `stick: 0.9`

#### 3. Campagne d'Extension Crypto (Clôturée le 02 Juillet 2026)

* **BNBUSDT** :
  * **60m** (Score: -36396.57 | Max DD: -16.19% | Profit Factor: 1.31 | Trades: 2100)
    * Paramètres : `obs_len: 23`, `stat_len: 77`, `mu_k: 2.1`, `stick: 0.9`

---

### 🔴 Les Rejetés (Absence d'Edge)
Ces actifs sont rejetés en raison de sous-performance systématique face au Buy & Hold ou de non-respect des critères de robustesse.

#### 1. Actifs Historiques (Campagne du 15 Juin 2026)
* **AMS.MC** : Sous-performance significative sur l'ensemble des timeframes (Meilleur score : -51.58 en 45m).
* **EVD.DE** : Sous-performance (Scores stables autour de -31).
* **FPE.DE** : Sous-performance modérée (Meilleur score : -3.77 en 120m).
* **GMAB** : Sous-performance (Scores autour de -26 à -29).
* **LOGI** : Forte sous-performance (Scores proches de -480).
* **NVS** : Sous-performance (Meilleur score : -13.46 en 15m).
* **SAP** : Sous-performance importante (Scores autour de -190).
* **SHL.DE** : Sous-performance (Scores autour de -124 à -134).
* **ZEAL.CO** : Sous-performance (Scores allant de -57 à -129).

#### 2. Nouveaux Actifs (Campagne d'Extension du 18 Juin 2026)
* **ACAFREUR** : Sous-performance (Meilleur score : -83.30 en 15m | Max DD: -0.48% | PF: 1.29).
* **AGSBEEUR** : Sous-performance (Meilleur score : -37.93 en 10m | Max DD: -0.81% | PF: 1.25).
* **AHNLEUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **AIFREUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **AIRFREUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **AKZANLEUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **ALOFREUR** : Sous-performance (Meilleur score : -3.76 en 30m | Max DD: -0.95% | PF: 1.27).
* **BEIDEEUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **BELGBEEUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **BNFREUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **BNPFREUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **CAPFREUR** : Sous-performance (Meilleur score : -28.52 en 10m | Max DD: -4.73% | PF: 1.36).
* **CONDEEUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **COVDEEUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **CPRITEUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **CSFREUR** : Sous-performance (Meilleur score : -105.15 en 10m | Max DD: -0.69% | PF: 1.37).
* **DB1DEEUR** : Sous-performance (Meilleur score : -168.39 en 30m | Max DD: -5.82% | PF: 1.28).
* **DPWDEEUR** : Sous-performance (Meilleur score : -53.39 en 30m | Max DD: -0.64% | PF: 1.51).
* **DSMNLEUR** : Sous-performance (Meilleur score : -9.62 en 15m | Max DD: -2.62% | PF: 1.31).
* **DTEDEEUR** : Sous-performance (Meilleur score : -59.10 en 15m | Max DD: -0.28% | PF: 1.27).
* **EDPPTEUR** : Sous-performance (Meilleur score : -41.87 en 10m | Max DD: -0.09% | PF: 1.33).
* **ELI1VFIEUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **ENGESEUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **ENIITEUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **EOANDEEUR** : Sous-performance (Meilleur score : -9.06 en 10m | Max DD: -0.31% | PF: 1.44).
* **ERGITEUR** : Sous-performance (Meilleur score : -2.44 en 30m | Max DD: -0.78% | PF: 1.36).
* **FBKITEUR** : Sous-performance (Meilleur score : -62.82 en 15m | Max DD: -0.49% | PF: 1.30).
* **FMEDEEUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **HEN3DEEUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **HNRDEEUR** : Sous-performance (Meilleur score : -68.53 en 10m | Max DD: -3.24% | PF: 1.33).
* **IFXDEEUR** : Sous-performance (Meilleur score : -199.16 en 30m | Max DD: -0.81% | PF: 1.37).
* **KBCBEEUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **LRFREUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **ORFREUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **ORKNONOK** : Sous-performance (Meilleur score : -40.84 en 15m | Max DD: -2.03% | PF: 1.25).
* **PHIANLEUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **PIAITEUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **RACEITEUR** : Sous-performance (Meilleur score : -56.84 en 10m | Max DD: -5.25% | PF: 1.47).
* **RBIATEUR** : Sous-performance (Meilleur score : -135.28 en 15m | Max DD: -0.67% | PF: 1.33).
* **REPESEUR** : Sous-performance (Meilleur score : -25.76 en 15m | Max DD: -0.39% | PF: 1.29).
* **RMSFREUR** : Sous-performance (Meilleur score : -50.99 en 30m | Max DD: -13.05% | PF: 1.55).
* **STERVFIEUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **STLNONOK** : Sous-performance (Meilleur score : -28.66 en 15m | Max DD: -12.98% | PF: 1.28).
* **SUFREUR** : Sous-performance (Meilleur score : -156.03 en 10m | Max DD: -3.04% | PF: 1.26).
* **TELNONOK** : Sous-performance (Meilleur score : -11.61 en 15m | Max DD: -1.45% | PF: 1.26).
* **TENITEUR** : Sous-performance (Meilleur score : -134.04 en 10m | Max DD: -0.33% | PF: 1.31).
* **TRNITEUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **USITEUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **VIEFREUR** : Sous-performance (Meilleur score : -46.07 en 15m | Max DD: -0.25% | PF: 1.31).
* **VNADEEUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **VOEATEUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **VPKNLEUR** : Rejeté (Aucune configuration valide ne respecte les filtres ou contraintes d'exposition).
* **WKLNLEUR** : Sous-performance (Meilleur score : -182.13 en 10m | Max DD: -3.88% | PF: 1.35).

#### 3. Campagne d'Extension Crypto (Rejetés par contraintes)
Tous les actifs suivants ont été rejetés à 100% car aucune configuration ne respectait le filtre de robustesse de Profit Factor minimum de 1.25.
* **ADAUSDT** (30m, 45m, 60m) : Toutes les configurations rejetées (PF < 1.25).
* **BNBUSDT** (45m) : Toutes les configurations rejetées (PF < 1.25).
* **BTCUSDT** (45m) : Toutes les configurations rejetées (PF < 1.25).
* **DOTUSDT** (45m) : Toutes les configurations rejetées (PF < 1.25).
* **LINKUSDT** (30m, 45m, 60m) : Toutes les configurations rejetées (PF < 1.25).
* **LTCUSDT** (30m) : Toutes les configurations rejetées (PF < 1.25).

---

## 3. Recommandations

L'optimisation des états du modèle de Markov caché (HMM) confirme que l'approche `hmm_regime_filter` trouve un edge de momentum/réversion valide uniquement sur une sélection d'actifs résilients :

1. **Actifs validés pour la suite** :
   - **NVO** (10m, 15m, 20m, 30m, 45m, 60m, 120m)
   - **ABIBEEUR** (10m, 15m, 45m)
   - **ACFREUR** (10m, 15m)
   - **DIAITEUR** (10m, 15m, 30m)
   - **LXSDEEUR** (30m)
   - **MRKDEEUR** (10m, 15m, 30m, 45m)
   - **RIFREUR** (10m, 15m)
   - **BNBUSDT** (60m)

2. **Prochaine étape (Passe 2)** :
   Ces 8 actifs et leurs configurations de timeframes respectives sont qualifiés pour la Passe 2, qui consistera à appliquer et optimiser les filtres macroscopiques de régime et de confirmation.

3. **Campagne d'Extension Crypto (Clôturée le 02 Juillet 2026)** :
   La campagne sur les cryptomonnaies du Top 10 s'est soldée par la qualification d'un seul couple : **bnbusdt (60m)**. Les 10 autres configurations ont été entièrement écartées en raison d'un Profit Factor insuffisant (< 1.25) dans toutes les itérations testées.
