# Rapport : Cybernetic Hilbert - Passe 1 (Mode Tendance)

**Date d'analyse** : 05 Juin 2026
**Objectif de la Passe** : Valider le comportement du mode tendance (Trend Mode) de la stratégie `cybernetic_hilbert` en bloquant le mode oscillation. Cette passe prépare la Passe 2 en déterminant les valeurs optimales pour le filtre de base.
**Configurations bloquées** : `phase_mode_enabled = false`, `use_net_bracket_exits = true`, `use_safety_stop = false`.
**Paramètres cibles optimisés** : `hilbert_smooth_period` (Int), `take_profit_net_percent` (Float) et `stop_loss_net_percent` (Float).
**Métriques cibles** : `return_vs_buy_hold_pct_points` (Max Drawdown tolérable entre -20% et -25%, Profit Factor minimum 1.25, minimum de trades 30-50).

---

## 1. Analyse Globale des Résultats

L'analyse globale a permis de générer **6 617 itérations éligibles**.
L'objectif de cette passe est d'identifier un Edge solide en suivant la tendance globale grâce à la transformée de Hilbert, avant d'activer le filtre cyclique (Phase Mode) dans la passe suivante.

---

## 2. Résultats par Catégorie d'Actifs

### 🟢 Les Sur-Performants (Edge Identifié)

Ces actifs ont démontré un edge clair et stable, justifiant de geler leurs paramètres pour poursuivre l'optimisation en Passe 2.

* **ZEAL.CO** : Présente une excellente rentabilité sur plusieurs unités de temps.
  * **15m (Best)** : Score `+102.9989` (`hilbert_smooth_period: 13`, `take_profit_net_percent: 15.0`, `stop_loss_net_percent: 1.0`). 4021 trades, PF: 1.497, Sharpe: 3.777, Sortino: 4.940.
  * **45m** : Score `+65.7837` (`hilbert_smooth_period: 12`, `take_profit_net_percent: 12.0`, `stop_loss_net_percent: 1.0`). 1366 trades, PF: 1.850, Sharpe: 3.360, Sortino: 4.108.
  * **20m** : Score `+62.5085` (`hilbert_smooth_period: 10`, `take_profit_net_percent: 9.0`, `stop_loss_net_percent: 1.0`). 2994 trades, PF: 1.475, Sharpe: 2.901, Sortino: 3.739.
  * **10m** : Score `+54.0317` (`hilbert_smooth_period: 20`, `take_profit_net_percent: 20.0`, `stop_loss_net_percent: 1.0`). 6112 trades, PF: 1.295, Sharpe: 3.200, Sortino: 3.732.
  * **30m** : Score `+53.9174` (`hilbert_smooth_period: 9`, `take_profit_net_percent: 20.0`, `stop_loss_net_percent: 1.0`). 1990 trades, PF: 1.586, Sharpe: 3.244, Sortino: 3.807.
  * **60m** : Score `+52.4314` (`hilbert_smooth_period: 12`, `take_profit_net_percent: 12.0`, `stop_loss_net_percent: 1.0`). 990 trades, PF: 1.949, Sharpe: 3.366, Sortino: 4.148.

* **NVO** : Présente également un edge très clair.
  * **45m** : Score `+149.4814` (`hilbert_smooth_period: 11`, `take_profit_net_percent: 6.0`, `stop_loss_net_percent: 1.0`). 3703 trades, PF: 1.356, Sharpe: 1.734, Sortino: 1.778.

### 🔴 Les Rejetés (Absence d'Edge ou Contraintes non respectées)
Ces actifs sous-performent tous le Buy & Hold ou n'ont aucune itération éligible aux filtres de risque. Ils sont donc écartés pour les passes suivantes :
* **AMS.MC**
* **EVD.DE**
* **FPE.DE**
* **GMAB** (sauf 45m qui est marginalement rejeté)
* **LOGI**
* **NVS**
* **SAP**
* **SHL.DE**

---

## 3. Recommandations

L'optimisation de la Passe 1 a permis de valider des paramètres très stables et performants pour **NVO (45m)** et **ZEAL.CO (15m, 45m)**. 
Les valeurs optimales (`hilbert_smooth_period`, `take_profit_net_percent` et `stop_loss_net_percent`) doivent être figées afin de servir de base pour la Passe 2.


## 4. Résultats Campagne d'Extension (Nouveaux Actifs)

### 🟢 Les Sur-Performants (Nouveaux Actifs)

* **LXSDEEUR** : Edge identifié.
  * **60m (Best)** : Score `+81.7414` (`hilbert_smooth_period: 14`, `take_profit_net_percent: 20.0`, `stop_loss_net_percent: 1.0`). 2927 trades, PF: 1.291, Sharpe: 1.432, Sortino: 1.570.

* **MRKDEEUR** : Edge identifié.
  * **45m (Best)** : Score `+33.9415` (`hilbert_smooth_period: 12`, `take_profit_net_percent: 9.0`, `stop_loss_net_percent: 1.0`). 3562 trades, PF: 1.296, Sharpe: 1.688, Sortino: 2.050.

### 🔴 Les Rejetés (Nouveaux Actifs)

Ces actifs n'ont produit aucune combinaison rentable par rapport au Buy & Hold ou n'ont pas respecté les critères stricts de la Passe 1 :
* **AMSESEUR**
* **BASDEEUR**
* **BAYNDEEUR**
* **CAPFREUR**
* **DGFREUR**
* **DPWDEEUR**
* **DSMNLEUR**
* **EDPPTEUR**
* **ERGITEUR**
* **FPFREUR**
* **GASESEUR**
* **HNRDEEUR**
* **IFXDEEUR**
* **MCFREUR**
* **MHGNONOK**
* **ORAFREUR**
* **PHIANLEUR**
* **RACEITEUR**
* **RANDNLEUR**
* **RBIATEUR**
* **RDSANLEUR**
* **RECITEUR**
* **RENNLEUR**
* **RMSFREUR**
* **SRTDEEUR**
* **STERVFIEUR**
* **STLNONOK**
* **TENITEUR**
* **UMIBEEUR**
* **VPKNLEUR**

---

## 5. Résultats Campagne Crypto (Nouveaux Actifs)

### 🟢 Les Sur-Performants (Nouveaux Actifs Crypto)

Ces actifs présentent une sur-performance significative par rapport au Buy & Hold (score positif) tout en satisfaisant les critères stricts de la Passe 1 (closed_trades >= 50, profit_factor >= 1.25, max_drawdown >= -25.0%) :

* **APTUSDT** : Edge identifié.
  * **10min (Best)** : Score `+114.5822` (`hilbert_smooth_period: 12`, `take_profit_net_percent: 18.0`, `stop_loss_net_percent: 1.0`). 63 282 trades, PF: 1.269, Sharpe: 3.574, Max DD: -0.26%.

* **DOTUSDT** : Multiples timeframes qualifiés avec un edge robuste.
  * **10min (Best)** : Score `+119.8589` (`hilbert_smooth_period: 10`, `take_profit_net_percent: 20.0`, `stop_loss_net_percent: 1.0`). 104 476 trades, PF: 1.316, Sharpe: 3.016, Max DD: -0.73%.
  * **45min** : Score `+111.7093` (`hilbert_smooth_period: 8`, `take_profit_net_percent: 19.0`, `stop_loss_net_percent: 1.0`). 23 164 trades, PF: 1.750, Sharpe: 2.700, Max DD: -1.11%.
  * **1h** : Score `+99.0538` (`hilbert_smooth_period: 6`, `take_profit_net_percent: 19.0`, `stop_loss_net_percent: 1.0`). 17 534 trades, PF: 1.655, Sharpe: 2.240, Max DD: -1.26%.

* **ETHUSDT** : Sur-performance historique majeure sur le timeframe intermédiaire.
  * **45min (Best)** : Score `+6960.3557` (`hilbert_smooth_period: 9`, `take_profit_net_percent: 19.0`, `stop_loss_net_percent: 1.0`). 35 664 trades, PF: 1.527, Sharpe: 2.036, Max DD: -10.06%.

* **LTCUSDT** : Bon comportement sur le court et moyen terme.
  * **30min (Best)** : Score `+704.2893` (`hilbert_smooth_period: 9`, `take_profit_net_percent: 20.0`, `stop_loss_net_percent: 1.0`). 52 158 trades, PF: 1.455, Sharpe: 1.851, Max DD: -4.90%.
  * **45min** : Score `+674.0878` (`hilbert_smooth_period: 12`, `take_profit_net_percent: 20.0`, `stop_loss_net_percent: 1.0`). 34 612 trades, PF: 1.563, Sharpe: 1.541, Max DD: -8.70%.

### 🔴 Les Rejetés (Nouveaux Actifs Crypto)

Ces actifs n'ont produit aucune combinaison rentable par rapport au Buy & Hold ou n'ont pas respecté les critères stricts de la Passe 1 :
* **ADAUSDT** (10min, 30min, 45min, 1h)
* **BNBUSDT** (10min, 15min, 30min, 45min, 1h)
* **BTCUSDT** (30min, 45min)
* **ETHUSDT** (10min, 30min)
* **LINKUSDT** (10min, 30min, 45min)

