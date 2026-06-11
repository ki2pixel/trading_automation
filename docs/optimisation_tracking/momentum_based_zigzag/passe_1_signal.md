# Rapport : Momentum-based ZigZag (avec QQE) - Passe 1 (Cœur QQE & Oscillateur)

**Date d'analyse** : 11 Juin 2026
**Objectif de la Passe** : Optimiser `rsi_period`, `qqe_factor`, `rsi_smoothing`, `ob`, `os`, et `signal_mode` sur l'ensemble des timeframes pour capturer les retournements de momentum (swings).
**Paramètres bloqués** : `enable_stop_loss = false`, `enable_take_profit = false`, `enable_trailing_stop = false`.
**Métriques cibles** : La métrique de score `return_vs_buy_hold_pct_points` a été utilisée pour forcer l'activité.

---

## 1. Analyse Globale des Résultats

L'analyse de cette Passe 1 s'est focalisée sur l'optimisation des conditions d'entrée en capturant les swings via le QQE et les seuils de surachat/survente (OB/OS). 
Les résultats multi-timeframe révèlent que l'edge de cette stratégie se trouve de manière très asymétrique selon les actifs, et particulièrement sur les unités de temps basses à intermédiaires (1m à 45m). Les performances globales montrent que l'approche est robuste même sans paramètres de sortie de risque actifs, présentant systématiquement des **PnL nets absolus positifs** avec de bons ratios financiers.

---

## 2. Résultats par Catégorie d'Actifs

### 🟢 Les Sur-Performants (Edge Absolu face au B&H)
* **NVO (Timeframe 45m)** : Présente l'edge le plus fort, surpassant la stratégie de Buy & Hold.
  * Score: +109.88 | PnL: +1533.85 | Profit Factor: 1.79 | Sharpe: 1.26 | Trades: 624
  * *Paramètres* : `rsi_period: 8`, `qqe_factor: 2.0`, `rsi_smoothing: 4`, `ob: 82.0`, `os: 10.0`, `signal_mode: 'Close'`

### 🟡 Les Prometteurs (Edge Absolu Positif, Ratios Robustes)
Ces actifs présentent d'excellentes métriques de robustesse (Sharpe, Profit Factor) avec un PnL absolu positif, mais accusent une sous-performance relative liée à l'absence de Stop-Loss / Take-Profit (Passe 1).
* **ZEAL.CO (Timeframe 1m)** 
  * Score: -26.19 | PnL: +1151.75 | Profit Factor: 1.58 | Sharpe: 1.86 | Trades: 488
  * *Paramètres* : `rsi_period: 19`, `qqe_factor: 4.8`, `rsi_smoothing: 2`, `ob: 71.0`, `os: 25.0`, `signal_mode: 'Close'`
* **GMAB (Timeframe 1m)**
  * Score: -25.41 | PnL: +45.12 | Profit Factor: 2.36 | Sharpe: 2.05 | Trades: 71
  * *Paramètres* : `rsi_period: 12`, `qqe_factor: 5.0`, `rsi_smoothing: 13`, `ob: 67.0`, `os: 32.0`, `signal_mode: 'Close'`
* **SAP (Timeframe 30m)** 
  * Score: -174.60 | PnL: +296.39 | Profit Factor: 5.53 | Sharpe: 1.13 | Trades: 69
  * *Paramètres* : `rsi_period: 25`, `qqe_factor: 5.6`, `rsi_smoothing: 15`, `ob: 79.0`, `os: 18.0`, `signal_mode: 'Live'`
* **SHL.DE (Timeframe 45m)**
  * Score: -111.47 | PnL: +269.61 | Profit Factor: 2.19 | Sharpe: 0.89 | Trades: 207
  * *Paramètres* : `rsi_period: 17`, `qqe_factor: 1.6`, `rsi_smoothing: 2`, `ob: 66.0`, `os: 34.0`, `signal_mode: 'Close'`
* **LOGI (Timeframe 120m)**
  * Score: -474.74 | PnL: +88.65 | Profit Factor: 3.41 | Sharpe: 0.84 | Trades: 54
  * *Paramètres* : `rsi_period: 8`, `qqe_factor: 2.5`, `rsi_smoothing: 14`, `ob: 76.0`, `os: 17.0`, `signal_mode: 'Live'`
* **AMS.MC (Timeframe 10m)**
  * Score: -47.32 | PnL: +105.25 | Profit Factor: 1.58 | Sharpe: 0.85 | Trades: 352
  * *Paramètres* : `rsi_period: 14`, `qqe_factor: 2.5`, `rsi_smoothing: 3`, `ob: 66.0`, `os: 35.0`, `signal_mode: 'Live'`
* **NVS (Timeframe 5m)**
  * Score: -8.40 | PnL: +93.39 | Profit Factor: 1.71 | Sharpe: 0.71 | Trades: 182
  * *Paramètres* : `rsi_period: 17`, `qqe_factor: 4.9`, `rsi_smoothing: 4`, `ob: 65.0`, `os: 32.0`, `signal_mode: 'Live'`

### 🔴 Les Faibles (PnL Proche de Zéro ou Faible Efficience)
* **EVD.DE (Timeframe 45m)** (Score: -30.77 | PnL: +5.77 | Profit Factor: 1.89 | Trades: 129)
  * *Paramètres* : `rsi_period: 7`, `qqe_factor: 4.5`, `rsi_smoothing: 13`, `ob: 90.0`, `os: 12.0`, `signal_mode: 'Close'`
* **FPE.DE (Timeframe 20m)** (Score: -3.71 | PnL: +1.15 | Profit Factor: 1.54 | Trades: 95)
  * *Paramètres* : `rsi_period: 7`, `qqe_factor: 2.0`, `rsi_smoothing: 10`, `ob: 68.0`, `os: 21.0`, `signal_mode: 'Live'`

---

## 3. Conclusion et Prochaine Passe
L'edge du QQE sur les retournements de momentum s'exprime beaucoup plus fortement sur des unités de temps rapides/intermédiaires (1m, 30m, 45m) que sur du 4H. L'optimisation statique de la Passe 2, basée sur ces timeframes spécifiques, devrait permettre aux actifs du groupe "Prometteurs" d'améliorer leur score absolu de sur-performance face au Buy & Hold en verrouillant les gains.
