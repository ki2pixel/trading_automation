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
| **TENITEUR** | 30m | HEMA 5 / SMA 38 | 0.7379 | **0.8789** | `+19.11%` | 0.5 | 0.8 | 75.00% | 80 | -7.31% | 2.78 | 7.60% |

---

## 2. Analyse Narrative

* **Hausses majeures et efficacité du Risk-Management** : L'introduction d'un Stop Loss (basé sur l'ATR via `risk_m`) et d'un Take Profit (ratio `rnr`) améliore la quasi-totalité des configurations validées, particulièrement pour GMAB.
  * Sur **GMAB (60m)**, l'optimisation propulse le Ratio de Sortino à **1.5046**, soit une progression spectaculaire de **+42.24%**. Cette performance est atteinte avec un ratio serré (TP à 0.5 de l'ATR et SL à 2.5 de l'ATR), générant un impressionnant Win Rate de 71.43% et un Profit Factor de 1.97. Le DD reste très contenu (-8.62%).
  * Des améliorations notables sont également observées sur **LOGI 10m (+17.31%)**, **GMAB 20m (+13.92%)** et sur le nouvel actif de l'extension de campagne **TENITEUR 30m (+19.11%)**, soulignant la valeur d'une gestion stricte du risque sur ces unités de temps plus courtes. Sur TENITEUR, un ratio risk/reward inversé très serré (`rnr` 0.5, `risk_m` 0.8) permet d'atteindre 75% de Win Rate pour un Drawdown maîtrisé de -7.31%.

* **Dégradations et Contraintes** : À l'inverse, l'application de ratios fixes de TP/SL a dégradé les performances sur certains setups spécifiques :
  * Sur **LOGI (120m)**, le Sortino chute de **-23.06%**. Le long timeframe suggère que des cibles fixes limitent trop les profits ou provoquent des sorties prématurées (whipsaws sur ATR large), réduisant le Win Rate à 41.67% pour 84 trades. 
  * Sur **EVD.DE (5m)**, on observe une chute de **-23.31%** (Sortino passant à 0.4809). Les ratios extrêmes sélectionnés par l'optimiseur (`rnr` 5.0 et `risk_m` 2.5) démontrent l'inadaptation de stops/profits fixes très larges sur des timeframes aussi courts, se traduisant par un Win Rate de seulement 23.26%. Les contraintes imposées à l'optimiseur (ex: drawdown max, nombre de trades minimaux) forcent potentiellement la sélection de setups sous-optimaux.

---

## 3. Conclusion et Recommandations (Passe 3)

La majorité des couples d'actifs/timeframes ont grandement bénéficié de cette Passe 2 (Risk-Management statique). Les setups dégradés (LOGI 120m, EVD.DE 5m) devront être surveillés mais pourraient être corrigés par un mécanisme de sortie plus souple.

**Recommandations pour la Passe 3 (Trailing Stop Dynamique)** :
Il est recommandé de poursuivre l'optimisation de l'ensemble de ces setups, y compris ceux ayant subi une baisse, pour évaluer l'impact d'un Trailing Stop. Le mécanisme de "Trailing Stop Dynamique" devrait notamment permettre de pallier les sorties prématurées observées sur les timeframes longs (ex: LOGI 120m) et d'accompagner les fortes tendances qui échappent actuellement aux cibles fixes de Take Profit.

---

## 4. Passe 2.1 : Impact de l'optimisation du Swing Lookback

Afin de vérifier si le paramètre `swing_lookback` (qui détermine la profondeur de recherche des plus hauts/plus bas pour le calcul des stops/objectifs) pouvait améliorer l'edge, une nouvelle campagne d'optimisation en 3D (`rnr`, `risk_m`, `swing_lookback` de 1 à 20) a été lancée sur les 15 configurations de la baseline.

**Tableau des résultats convergents :**

| Actif | TF | Core MAs (P1) | P1 Sortino | P2.1 Sortino | Delta Sortino (vs P1) | rnr (TP) | risk_m (SL) | swing | Win Rate (%) | Trades | Max DD (%) | PF | CAGR (%) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **GMAB** | 20m | EMA 6 / HMA 128 | 0.8312 | **0.9419** | `+13.32%` | 0.9 | 5.0 | 18 | 68.75% | 80 | -11.99% | 1.69 | 5.88% |
| **LOGI** | 120m | HEMA 7 / SMA 13 | 0.6974 | **0.7631** | `+9.42%` | 1.0 | 0.6 | 9 | 58.82% | 102 | -17.29% | 2.54 | 5.21% |
| **LOGI** | 45m | HEMA 6 / SMA 13 | 0.6872 | **0.5816** | `-15.36%` | 1.2 | 1.5 | 10 | 53.49% | 86 | -19.34% | 1.98 | 4.08% |
| **LOGI** | 10m | HEMA 5 / T3 15 | 0.7066 | **0.6877** | `-2.67%` | 2.6 | 2.3 | 6 | 35.37% | 82 | -22.33% | 2.41 | 4.78% |
| **LOGI** | 5m | HEMA 8 / HMA 57 | 0.7391 | **0.3490** | `-52.78%` | 1.7 | 2.6 | 5 | 34.12% | 85 | -20.68% | 1.72 | 1.87% |

**Analyse :**
1. **Échec massif de la convergence** : Sur les 15 configurations lancées, l'élargissement de l'espace de recherche (ajoutant 20 variations de `swing_lookback`) a fait échouer l'optimiseur bayésien sur 10 configurations (0 itération éligible). La dilution de l'espace de recherche confirme que les combinaisons viables (Sortino > 0 et Trades > 80) sont extrêmement rares.
2. **Correction du LOGI 120m** : L'intuition était excellente pour les timeframes longs. Le LOGI 120m, qui s'était dégradé lors de la Passe 2 (chute à 0.5366), bénéficie grandement de l'ajustement du `swing_lookback` à **9** (au lieu des 5 par défaut). Son Sortino remonte à **0.7631** (+9.42% par rapport au signal brut), avec un excellent Profit Factor de 2.54. Cela prouve que sur des unités de temps élevées, le regard en arrière (`lookback`) nécessite une extension pour identifier les vrais pivots.
3. **Instabilité en Intraday** : Pour les unités de temps très courtes (LOGI 5m, 10m, 45m), faire varier ce paramètre n'a mené qu'à des configurations inférieures à celles trouvées en Passe 2 classique. Le bruit de marché rend l'ajustement millimétré du `swing` très fragile (overfitting).
4. **Conclusion** : Le paramètre `swing_lookback` possède un véritable impact, principalement pour resynchroniser les timeframes de plus d'une heure. Il devra être conservé pour les optimisations futures sur de l'Hourly/Daily, mais peut être figé à sa valeur par défaut (5) pour le scalping afin de ne pas "perdre" l'optimiseur.
