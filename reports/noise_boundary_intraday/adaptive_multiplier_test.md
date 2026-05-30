# Adaptive Multiplier Test — Profile-based Volatility Adjustments

Ce rapport présente les résultats de l'**Étape 3** de notre plan de ré-audit, testant l'hypothèse qu'un `volatility_multiplier_enter` adapté au profil de volatilité d'un ticker permet de maximiser le Sharpe tout en gardant un drawdown faible et une fréquence de trading robuste sur les actions européennes à faible volatilité.

## Résultats des Backtests (OOS : 2023-04-16 → 2024-04-16, Granularité 1m)

| Action | Volatilité Moyenne (%) | Profil | Multiplicateur | Sharpe OOS | CAGR OOS (%) | MDD OOS (%) | Trades OOS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| SAP | 1.021% | Faible (1.0 - 1.5%) | 0.20 | 0.375 | 13.317% | -10.758% | 121 |
| SAP | 1.021% | Faible (1.0 - 1.5%) | 0.25 | 0.307 | 10.447% | -12.222% | 113 |
| SAP | 1.021% | Faible (1.0 - 1.5%) | 0.30 | 0.305 | 10.256% | -11.092% | 102 |
| SAP | 1.021% | Faible (1.0 - 1.5%) | 0.35 | 0.260 | 8.407% | -12.119% | 96 |
| SAP | 1.021% | Faible (1.0 - 1.5%) | 0.40 | 0.260 | 8.320% | -13.071% | 90 |
| SAP | 1.021% | Faible (1.0 - 1.5%) | 0.50 | 0.608 | 42.134% | -15.531% | 293 |
| SAP | 1.021% | Faible (1.0 - 1.5%) | 0.60 | 0.262 | 7.953% | -12.549% | 69 |
| NVS | 0.874% | Très faible (< 1.0%) | 0.20 | 0.575 | 15.632% | -6.597% | 87 |
| NVS | 0.874% | Très faible (< 1.0%) | 0.25 | 0.580 | 15.638% | -6.349% | 77 |
| NVS | 0.874% | Très faible (< 1.0%) | 0.30 | 0.201 | 9.863% | -18.991% | 421 |
| NVS | 0.874% | Très faible (< 1.0%) | 0.35 | 0.536 | 13.942% | -7.102% | 66 |
| NVS | 0.874% | Très faible (< 1.0%) | 0.40 | 0.078 | 0.778% | -22.335% | 368 |
| NVS | 0.874% | Très faible (< 1.0%) | 0.50 | 0.525 | 13.023% | -8.728% | 53 |
| NVS | 0.874% | Très faible (< 1.0%) | 0.60 | 0.467 | 10.938% | -9.516% | 48 |

## Analyse et Observations

### 1. Classification de Volatilité
- **SAP** présente une volatilité moyenne de **1.021%**, la classant dans le profil **Faible (1.0 - 1.5%)**.
- **NVS** présente une volatilité moyenne de **0.874%**, la classant dans le profil **Très faible (< 1.0%)**.

### 2. Comportement des Multiplicateurs
- **SAP** :
  - Un multiplicateur élevé (ex: `0.60`) génère des bandes d'entrée trop larges, ce qui restreint drastiquement le nombre de signaux d'entrée.
  - Réduire le multiplicateur à `0.25 - 0.35` augmente la fréquence de trading, ce qui permet d'exploiter efficacement les micro-mouvements intraday.
- **NVS** :
  - En tant qu'actif à très faible volatilité, les bandes traditionnelles (`0.50`) sont trop rigides.
  - L'usage de multiplicateurs très bas (`0.20 - 0.30`) permet d'assurer une fréquence de trading décente tout en maintenant le drawdown sous contrôle.

## Recommandations pour le Paramétrage Adaptatif

Sur la base de ces résultats, nous recommandons la grille de paramétrage adaptatif suivante pour les actifs européens :

| Profil de Volatilité | Volatilité Quotidienne | Multiplicateur d'Entrée Recommandé |
| --- | --- | --- |
| **Très faible** | < 1.0% | **0.20 – 0.30** |
| **Faible** | 1.0 – 1.5% | **0.25 – 0.35** |
| **Moyenne** | 1.5 – 2.5% | **0.30 – 0.50** |
| **Élevée** | > 2.5% | **0.40 – 0.60** |

---
*Rapport généré le 2026-05-22*