# Rapport : 3commas_bot - Passe 2 (Risk-Management)

**Date d'analyse** : 04 Juin 2026
**Objectif de la Passe** : Maximiser le profit statique en trouvant le meilleur couple `rnr` (Take Profit) / `risk_m` (Stop Loss ATR) en figeant les Moyennes Mobiles trouvées en Passe 1.
**Paramètres cibles optimisés** : `rnr`, `risk_m`.
**Paramètres bloqués** : Les configurations Core (`ma_type1`, `ma_length1`, `ma_type2`, `ma_length2`) spécifiques à chaque actif/timeframe validées lors de la Passe 1.

---

## 1. Analyse Globale des Résultats

Le tableau suivant présente les résultats de la Passe 2 et met en évidence l'évolution (Delta) du ratio de Sortino par rapport au signal brut de la Passe 1 :

| Actif | TF | Core MAs (P1) | P1 Sortino | P2 Sortino | Delta Sortino | rnr (TP) | risk_m (SL) | Win Rate (%) | Trades | Max DD (%) | PF | CAGR (%) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **GMAB** | 60m | DEMA 8 / HMA 10 | 1.0578 | **1.5046** | `+42.24%` | 0.5 | 2.5 | 71.43% | 112 | -8.62% | 1.97 | 6.96% |
| **GMAB** | 30m | HMA 5 / DEMA 23 | 0.9536 | **0.9949** | `+4.33%` | 1.1 | 0.8 | 55.33% | 197 | -12.07% | 1.56 | 5.67% |
| **GMAB** | 20m | EMA 6 / HMA 128 | 0.8312 | **0.9469** | `+13.92%` | 1.5 | 0.5 | 57.73% | 97 | -9.06% | 2.10 | 5.65% |
| **GMAB** | 15m | HMA 6 / VWMA 18 | 0.8936 | **1.0032** | `+12.26%` | 0.8 | 2.6 | 60.87% | 184 | -11.52% | 1.61 | 6.00% |
| **FPE.DE** | 45m | HMA 41 / WMA 10 | 0.7597 | **0.8468** | `+11.47%` | 0.6 | 2.9 | 71.12% | 187 | -3.84% | 1.80 | 7.77% |
| **FPE.DE** | 30m | HMA 52 / EMA 10 | 0.7272 | **0.8172** | `+12.38%` | 0.9 | 1.2 | 61.35% | 251 | -2.94% | 1.81 | 6.45% |
| **FPE.DE** | 20m | DEMA 30 / HMA 32 | 0.8538 | **0.8673** | `+1.58%` | 1.0 | 1.5 | 59.81% | 209 | -4.35% | 1.88 | 8.20% |
| **FPE.DE** | 5m | WMA 36 / HMA 59 | 0.8889 | **0.9544** | `+7.37%` | 1.1 | 0.9 | 59.68% | 253 | -2.12% | 1.91 | 5.97% |
| **LOGI** | 120m | HEMA 7 / SMA 13 | 0.6974 | **0.5366** | `-23.06%` | 2.1 | 1.7 | 41.67% | 84 | -22.57% | 2.33 | 4.50% |
| **LOGI** | 45m | HEMA 6 / SMA 13 | 0.6872 | **0.7392** | `+7.57%` | 1.4 | 0.7 | 50.41% | 123 | -18.13% | 2.78 | 5.53% |
| **LOGI** | 10m | HEMA 5 / T3 15 | 0.7066 | **0.8289** | `+17.31%` | 1.7 | 0.8 | 42.00% | 200 | -16.64% | 3.82 | 6.10% |
| **LOGI** | 5m | HEMA 8 / HMA 57 | 0.7391 | **0.8086** | `+9.40%` | 2.5 | 2.4 | 29.59% | 98 | -20.79% | 3.70 | 5.34% |
| **EVD.DE** | 30m | DEMA 40 / HMA 140 | 0.6881 | **0.7430** | `+7.98%` | 1.2 | 0.8 | 62.73% | 110 | -5.28% | 2.87 | 9.34% |
| **EVD.DE** | 20m | WMA 20 / WMA 71 | 0.5965 | **0.6058** | `+1.56%` | 1.1 | 0.9 | 58.90% | 146 | -5.71% | 2.19 | 7.21% |
| **EVD.DE** | 5m | SMA 49 / VWMA 57 | 0.6271 | **0.4809** | `-23.31%` | 5.0 | 2.5 | 23.26% | 331 | -10.76% | 1.36 | 7.05% |

---

## 2. Analyse Narrative

* **Hausses majeures et efficacité du Risk-Management** : L'introduction d'un Stop Loss (basé sur l'ATR via `risk_m`) et d'un Take Profit (ratio `rnr`) améliore la quasi-totalité des configurations validées, particulièrement pour GMAB.
  * Sur **GMAB (60m)**, l'optimisation propulse le Ratio de Sortino à **1.5046**, soit une progression spectaculaire de **+42.24%**. Cette performance est atteinte avec un ratio serré (TP à 0.5 de l'ATR et SL à 2.5 de l'ATR), générant un impressionnant Win Rate de 71.43% et un Profit Factor de 1.97. Le DD reste très contenu (-8.62%).
  * Des améliorations notables sont également observées sur **LOGI 10m (+17.31%)** et **GMAB 20m (+13.92%)**, soulignant la valeur d'une gestion stricte du risque sur ces unités de temps plus courtes.

* **Dégradations et Contraintes** : À l'inverse, l'application de ratios fixes de TP/SL a dégradé les performances sur certains setups spécifiques :
  * Sur **LOGI (120m)**, le Sortino chute de **-23.06%**. Le long timeframe suggère que des cibles fixes limitent trop les profits ou provoquent des sorties prématurées (whipsaws sur ATR large), réduisant le Win Rate à 41.67% pour 84 trades. 
  * Sur **EVD.DE (5m)**, on observe une chute de **-23.31%** (Sortino passant à 0.4809). Les ratios extrêmes sélectionnés par l'optimiseur (`rnr` 5.0 et `risk_m` 2.5) démontrent l'inadaptation de stops/profits fixes très larges sur des timeframes aussi courts, se traduisant par un Win Rate de seulement 23.26%. Les contraintes imposées à l'optimiseur (ex: drawdown max, nombre de trades minimaux) forcent potentiellement la sélection de setups sous-optimaux.

---

## 3. Conclusion et Recommandations (Passe 3)

La majorité des couples d'actifs/timeframes ont grandement bénéficié de cette Passe 2 (Risk-Management statique). Les setups dégradés (LOGI 120m, EVD.DE 5m) devront être surveillés mais pourraient être corrigés par un mécanisme de sortie plus souple.

**Recommandations pour la Passe 3 (Trailing Stop Dynamique)** :
Il est recommandé de poursuivre l'optimisation de l'ensemble de ces setups, y compris ceux ayant subi une baisse, pour évaluer l'impact d'un Trailing Stop. Le mécanisme de "Trailing Stop Dynamique" devrait notamment permettre de pallier les sorties prématurées observées sur les timeframes longs (ex: LOGI 120m) et d'accompagner les fortes tendances qui échappent actuellement aux cibles fixes de Take Profit.
