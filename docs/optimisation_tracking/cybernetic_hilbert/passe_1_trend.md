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
