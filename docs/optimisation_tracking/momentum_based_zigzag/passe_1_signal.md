# Rapport : Momentum-based ZigZag (avec QQE) - Passe 1 (Cœur QQE & Oscillateur)

**Date de dernière mise à jour** : 19 Juin 2026
**Objectif de la Passe** : Optimiser `rsi_period`, `qqe_factor`, `rsi_smoothing`, `ob`, `os`, et `signal_mode` sur l'ensemble des timeframes pour capturer les retournements de momentum (swings).
**Paramètres bloqués** : `enable_stop_loss = false`, `enable_take_profit = false`, `enable_trailing_stop = false`.
**Métriques cibles** : La métrique de score `return_vs_buy_hold_pct_points` a été utilisée pour forcer l'activité (sur-performance vs B&H).

---

## 1. Analyse Globale des Résultats

L'analyse de cette Passe 1 s'est focalisée sur l'optimisation des conditions d'entrée en capturant les swings via le QQE et les seuils de surachat/survente (OB/OS). Les résultats sont divisés en deux vagues d'optimisation :

*   **Vague de Baseline (11 Juin 2026)** : Évaluation sur les 9 actifs historiques du portefeuille. Un seul actif a montré un edge directionnel direct face au Buy & Hold (**NVO** sur 45m). Les 8 autres sous-performaient le B&H bien que générant des PnL absolus positifs robustes, justifiant le passage à la Passe 2 (SL/TP) pour figer les gains.
*   **Vague d'Extension (19 Juin 2026)** : Évaluation sur les 20 nouveaux actifs qualifiés issus du rapport de screening. Les résultats sont remarquables avec **9 actifs sur 20** qui dégagent un score de sur-performance positif face au Buy & Hold dès cette Passe 1, notamment **belgbeeur** (+79.51 points), **daideeur** (+56.93 points), **cpriteur** (+41.43 points) et **cafreur** (+41.02 points).

---

## 2. Résultats de la Campagne de Baseline (11 Juin 2026)

### 🟢 Les Sur-Performants (Edge Absolu face au B&H)
*   **NVO (Timeframe 45m)** : Présente l'edge le plus fort, surpassant la stratégie de Buy & Hold.
    *   Score: +109.88 | PnL: +1533.85 | Profit Factor: 1.79 | Sharpe: 1.26 | Trades: 624
    *   *Paramètres* : `rsi_period: 8`, `qqe_factor: 2.0`, `rsi_smoothing: 4`, `ob: 82.0`, `os: 10.0`, `signal_mode: 'Close'`

### 🟡 Les Prometteurs (Edge Absolu Positif, Ratios Robustes)
Ces actifs présentent d'excellentes métriques de robustesse (Sharpe, Profit Factor) avec un PnL absolu positif, mais accusent une sous-performance relative liée à l'absence de Stop-Loss / Take-Profit (Passe 1).
*   **ZEAL.CO (Timeframe 1m)** : Score: -26.19 | PnL: +1151.75 | Profit Factor: 1.58 | Sharpe: 1.86 | Trades: 488
    *   *Paramètres* : `rsi_period: 19`, `qqe_factor: 4.8`, `rsi_smoothing: 2`, `ob: 71.0`, `os: 25.0`, `signal_mode: 'Close'`
*   **GMAB (Timeframe 1m)** : Score: -25.41 | PnL: +45.12 | Profit Factor: 2.36 | Sharpe: 2.05 | Trades: 71
    *   *Paramètres* : `rsi_period: 12`, `qqe_factor: 5.0`, `rsi_smoothing: 13`, `ob: 67.0`, `os: 32.0`, `signal_mode: 'Close'`
*   **SAP (Timeframe 30m)** : Score: -174.60 | PnL: +296.39 | Profit Factor: 5.53 | Sharpe: 1.13 | Trades: 69
    *   *Paramètres* : `rsi_period: 25`, `qqe_factor: 5.6`, `rsi_smoothing: 15`, `ob: 79.0`, `os: 18.0`, `signal_mode: 'Live'`
*   **SHL.DE (Timeframe 45m)** : Score: -111.47 | PnL: +269.61 | Profit Factor: 2.19 | Sharpe: 0.89 | Trades: 207
    *   *Paramètres* : `rsi_period: 17`, `qqe_factor: 1.6`, `rsi_smoothing: 2`, `ob: 66.0`, `os: 34.0`, `signal_mode: 'Close'`
*   **LOGI (Timeframe 120m)** : Score: -474.74 | PnL: +88.65 | Profit Factor: 3.41 | Sharpe: 0.84 | Trades: 54
    *   *Paramètres* : `rsi_period: 8`, `qqe_factor: 2.5`, `rsi_smoothing: 14`, `ob: 76.0`, `os: 17.0`, `signal_mode: 'Live'`
*   **AMS.MC (Timeframe 10m)** : Score: -47.32 | PnL: +105.25 | Profit Factor: 1.58 | Sharpe: 0.85 | Trades: 352
    *   *Paramètres* : `rsi_period: 14`, `qqe_factor: 2.5`, `rsi_smoothing: 3`, `ob: 66.0`, `os: 35.0`, `signal_mode: 'Live'`
*   **NVS (Timeframe 5m)** : Score: -8.40 | PnL: +93.39 | Profit Factor: 1.71 | Sharpe: 0.71 | Trades: 182
    *   *Paramètres* : `rsi_period: 17`, `qqe_factor: 4.9`, `rsi_smoothing: 4`, `ob: 65.0`, `os: 32.0`, `signal_mode: 'Live'`

### 🔴 Les Faibles (PnL Proche de Zéro ou Faible Efficience)
*   **EVD.DE (Timeframe 45m)** : Score: -30.77 | PnL: +5.77 | Profit Factor: 1.89 | Trades: 129
    *   *Paramètres* : `rsi_period: 7`, `qqe_factor: 4.5`, `rsi_smoothing: 13`, `ob: 90.0`, `os: 12.0`, `signal_mode: 'Close'`
*   **FPE.DE (Timeframe 20m)** : Score: -3.71 | PnL: +1.15 | Profit Factor: 1.54 | Trades: 95
    *   *Paramètres* : `rsi_period: 7`, `qqe_factor: 2.0`, `rsi_smoothing: 10`, `ob: 68.0`, `os: 21.0`, `signal_mode: 'Live'`

---

## 3. Résultats de la Campagne d'Extension (19 Juin 2026)

Résultats triés par Score de sur-performance décroissant (contrainte ferme de `closed_trades >= 50` appliquée) :

| Actif | TF | Score (vs B&H) | PnL Net (€) | Profit Factor | Sharpe | Trades | Paramètres Optimisés (Passe 1) | Statut |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | :--- | :--- |
| **belgbeeur** | 10m | **+79.51%** | +34.15 | 2.19 | 1.19 | 254 | `rsi_period: 22, qqe_factor: 5.0, rsi_smoothing: 15, ob: 90.0, os: 24.0, signal_mode: 'Live'` | **✅ Qualifié** |
| **daideeur** | 15m | **+56.93%** | +228.45 | 1.44 | 1.43 | 1418 | `rsi_period: 17, qqe_factor: 4.1, rsi_smoothing: 5, ob: 89.0, os: 10.0, signal_mode: 'Close'` | **✅ Qualifié** |
| **cpriteur** | 10m | **+41.43%** | +8.02 | 1.61 | 0.81 | 125 | `rsi_period: 17, qqe_factor: 2.3, rsi_smoothing: 7, ob: 66.0, os: 31.0, signal_mode: 'Close'` | **✅ Qualifié** |
| **cafreur** | 15m | **+41.02%** | +30.72 | 1.40 | 1.02 | 730 | `rsi_period: 15, qqe_factor: 1.5, rsi_smoothing: 10, ob: 82.0, os: 23.0, signal_mode: 'Close'` | **✅ Qualifié** |
| **vnadeeur** | 10m | **+37.25%** | +110.67 | 1.68 | 1.63 | 698 | `rsi_period: 16, qqe_factor: 1.6, rsi_smoothing: 15, ob: 76.0, os: 20.0, signal_mode: 'Live'` | **✅ Qualifié** |
| **akzanleur** | 30m | **+17.45%** | +133.51 | 1.81 | 1.16 | 254 | `rsi_period: 29, qqe_factor: 6.0, rsi_smoothing: 12, ob: 90.0, os: 10.0, signal_mode: 'Live'` | **✅ Qualifié** |
| **randnleur** | 10m | **+16.12%** | +83.97 | 2.47 | 1.16 | 65 | `rsi_period: 18, qqe_factor: 6.0, rsi_smoothing: 2, ob: 73.0, os: 28.0, signal_mode: 'Live'` | **✅ Qualifié** |
| **vpknleur** | 15m | **+15.09%** | +41.84 | 1.57 | 0.78 | 152 | `rsi_period: 27, qqe_factor: 1.9, rsi_smoothing: 4, ob: 66.0, os: 34.0, signal_mode: 'Close'` | **✅ Qualifié** |
| **beideeur** | 15m | **+2.00%** | +123.75 | 3.47 | 0.96 | 52 | `rsi_period: 27, qqe_factor: 2.9, rsi_smoothing: 15, ob: 67.0, os: 18.0, signal_mode: 'Live'` | **✅ Qualifié** |
| **ergiteur** | 30m | -0.53% | +35.03 | 1.89 | 1.20 | 178 | `rsi_period: 15, qqe_factor: 4.0, rsi_smoothing: 10, ob: 90.0, os: 18.0, signal_mode: 'Live'` | ❌ Rejeté (Score < 0) |
| **mhgnonok** | 10m | -16.74% | +421.63 | 3.45 | 1.58 | 80 | `rsi_period: 21, qqe_factor: 3.9, rsi_smoothing: 13, ob: 70.0, os: 25.0, signal_mode: 'Close'` | ❌ Rejeté (Score < 0) |
| **stervfieur** | 15m | -19.89% | +24.56 | 1.53 | 0.89 | 260 | `rsi_period: 7, qqe_factor: 4.5, rsi_smoothing: 2, ob: 68.0, os: 21.0, signal_mode: 'Close'` | ❌ Rejeté (Score < 0) |
| **eli1vfieur** | 30m | -21.86% | +29.99 | 1.53 | 0.37 | 112 | `rsi_period: 16, qqe_factor: 1.7, rsi_smoothing: 12, ob: 65.0, os: 11.0, signal_mode: 'Live'` | ❌ Rejeté (Score < 0) |
| **edppteur** | 30m | -41.82% | +6.31 | 1.55 | 1.17 | 448 | `rsi_period: 7, qqe_factor: 2.4, rsi_smoothing: 3, ob: 72.0, os: 18.0, signal_mode: 'Live'` | ❌ Rejeté (Score < 0) |
| **gaseseur** | 10m | -46.57% | +45.04 | 1.93 | 1.65 | 338 | `rsi_period: 27, qqe_factor: 5.1, rsi_smoothing: 3, ob: 81.0, os: 19.0, signal_mode: 'Close'` | ❌ Rejeté (Score < 0) |
| **hnrdeeur** | 15m | -52.03% | +299.63 | 2.26 | 2.84 | 277 | `rsi_period: 30, qqe_factor: 1.7, rsi_smoothing: 3, ob: 74.0, os: 13.0, signal_mode: 'Live'` | ❌ Rejeté (Score < 0) |
| **covdeeur** | 15m | -54.15% | +34.13 | 2.44 | 1.57 | 91 | `rsi_period: 19, qqe_factor: 5.7, rsi_smoothing: 13, ob: 80.0, os: 11.0, signal_mode: 'Live'` | ❌ Rejeté (Score < 0) |
| **dtedeeur** | 15m | -57.56% | +25.04 | 1.44 | 0.85 | 524 | `rsi_period: 7, qqe_factor: 2.3, rsi_smoothing: 8, ob: 68.0, os: 11.0, signal_mode: 'Live'` | ❌ Rejeté (Score < 0) |
| **siedeeur** | 45m | -105.27% | +331.01 | 1.35 | 1.01 | 1381 | `rsi_period: 12, qqe_factor: 1.6, rsi_smoothing: 2, ob: 86.0, os: 12.0, signal_mode: 'Live'` | ❌ Rejeté (Score < 0) |
| **teniteur** | 30m | -133.55% | +19.35 | 1.79 | 1.62 | 209 | `rsi_period: 20, qqe_factor: 2.2, rsi_smoothing: 3, ob: 77.0, os: 14.0, signal_mode: 'Live'` | ❌ Rejeté (Score < 0) |

---

## 4. Analyse Narrative & Observations Clés

*   **Une moisson d'actifs exceptionnels en extension** : Alors que la baseline initiale n'avait produit qu'un seul actif sur-performant (NVO), la vague d'extension en qualifie **9** avec des scores robustes.
*   **belgbeeur & daideeur en leaders** : `belgbeeur` (10m) offre la meilleure sur-performance brute face au B&H avec **+79.51%** et un Sharpe de 1.19 pour 254 trades. `daideeur` (15m) impressionne par son volume d'activité (**1418 trades**) et un Sharpe élevé de 1.43, tout en sur-performant le B&H de **+56.93%**.
*   **Des ratios Sharpe/Profit Factor remarquables** : De nombreux actifs rejetés pour score négatif vs B&H (car le Buy & Hold de ces actifs sur la période a été extrêmement haussier) affichent pourtant des métriques intrinsèques excellentes. Par exemple, **hnrdeeur** affiche un Sharpe exceptionnel de **2.84** et un PF de **2.26** avec un PnL absolu de +299.63€ (277 trades).
*   **Importance du Signal Mode** : Une majorité de configurations optimales privilégient le mode `Live` (calcul dynamique intra-bougie pour le QQE/Oscillateur), ce qui valide l'importance de ce paramètre introduit dans la grille de Passe 1.

---

## 5. Recommandations pour la Passe 2 (Gestion du Risque)

1.  **Figer les configurations Core (Passe 1)** : Verrouiller les paramètres optimisés pour les **9 actifs d'extension qualifiés** et l'actif de baseline **NVO**.
2.  **Lancer la Passe 2 (SL/TP)** : Construire et exécuter le script de queue de Passe 2 pour optimiser les sorties asymétriques :
    *   `enable_stop_loss = [True]` avec `stop_loss_pct` de 1.0% à 10.0% (pas de 0.5%).
    *   `enable_take_profit = [True]` avec `take_profit_pct` de 2.0% à 25.0% (pas de 1.0%).
    *   *Objectif* : Améliorer les scores absolus, réduire les drawdowns maximaux et figer les gains.
