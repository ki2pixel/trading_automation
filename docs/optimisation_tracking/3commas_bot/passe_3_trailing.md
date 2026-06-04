# Rapport : 3commas_bot - Passe 3 (Trailing Stop Dynamique)

**Date d'analyse** : 04 Juin 2026
**Objectif de la Passe** : Laisser courir les gains une fois la cible atteinte en optimisant le Trailing Stop ATR (`trail_stop_size`) et son seuil de déclenchement (`rr_exit`).
**Paramètres cibles optimisés** : `trail_stop_size`, `rr_exit`.
**Paramètres bloqués** : Configurations Core (Moyennes Mobiles) de la Passe 1 et gestion du risque statique (`rnr`, `risk_m`) de la Passe 2.
**Filtre imposé par l'optimiseur** : `trail_stop = true`.

---

## 1. Analyse Globale des Résultats

Le tableau suivant présente les résultats de la Passe 3 en comparant la performance avec la Passe 2 (Risk-Management statique) :

| Actif | TF | Core MAs (P1) | P2 Sortino | P3 Sortino | Delta P2->P3 | trail_stop_size | rr_exit | Win Rate (%) | Trades | Max DD (%) | PF | CAGR (%) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **GMAB** | 60m | DEMA 8 / HMA 10 | 1.5046 | **1.8379** | `+22.15%` | 1.9 | 0.5 | 68.46% | 130 | -6.32% | 2.27 | 8.50% |
| **GMAB** | 30m | HMA 5 / DEMA 23 | 0.9949 | **0.9949** | `0.00%` | 2.4 | 1.2 | 55.33% | 197 | -12.07% | 1.56 | 5.67% |
| **GMAB** | 20m | EMA 6 / HMA 128 | 0.9469 | **0.9689** | `+2.32%` | 2.7 | 0.8 | 57.14% | 98 | -8.63% | 2.19 | 5.82% |
| **GMAB** | 15m | HMA 6 / VWMA 18 | 1.0032 | **1.0032** | `0.00%` | 1.4 | 1.9 | 60.87% | 184 | -11.52% | 1.61 | 6.00% |
| **FPE.DE** | 45m | HMA 41 / WMA 10 | 0.8468 | **0.9207** | `+8.73%` | 0.5 | 0.9 | 72.40% | 192 | -3.85% | 1.96 | 8.64% |
| **FPE.DE** | 30m | HMA 52 / EMA 10 | 0.8172 | **0.8172** | `0.00%` | 1.4 | 1.9 | 61.35% | 251 | -2.94% | 1.81 | 6.45% |
| **FPE.DE** | 20m | DEMA 30 / HMA 32 | 0.8673 | **0.8673** | `0.00%` | 1.4 | 1.9 | 59.81% | 209 | -4.35% | 1.88 | 8.20% |
| **FPE.DE** | 5m | WMA 36 / HMA 59 | 0.9544 | **1.0052** | `+5.32%` | 3.0 | 0.9 | 60.00% | 255 | -2.12% | 1.99 | 6.26% |
| **LOGI** | 120m | HEMA 7 / SMA 13 | 0.5366 | **0.4813** | `-10.31%` | 2.4 | 0.4 | 45.68% | 81 | -11.45% | 2.07 | 3.36% |
| **LOGI** | 45m | HEMA 6 / SMA 13 | 0.7392 | **0.7392** | `0.00%` | 1.4 | 1.9 | 50.41% | 123 | -18.13% | 2.78 | 5.53% |
| **LOGI** | 10m | HEMA 5 / T3 15 | 0.8289 | **0.8289** | `0.00%` | 2.0 | 1.4 | 42.00% | 200 | -16.64% | 3.82 | 6.10% |
| **LOGI** | 5m | HEMA 8 / HMA 57 | 0.8086 | **0.8086** | `0.00%` | 2.4 | 1.2 | 29.59% | 98 | -20.79% | 3.70 | 5.34% |
| **EVD.DE** | 30m | DEMA 40 / HMA 140 | 0.7430 | **0.7430** | `0.00%` | 1.4 | 1.9 | 62.73% | 110 | -5.28% | 2.87 | 9.34% |
| **EVD.DE** | 20m | WMA 20 / WMA 71 | 0.6058 | **0.6058** | `0.00%` | 1.4 | 1.9 | 58.90% | 146 | -5.71% | 2.19 | 7.21% |
| **EVD.DE** | 5m | SMA 49 / VWMA 57 | 0.4809 | **0.7951** | `+65.34%` | 1.2 | 0.2 | 48.23% | 593 | -5.15% | 1.47 | 9.15% |

---

## 2. Analyse Narrative et Décisions

### 🟡 Le "Court-Circuit" Logique du Trailing Stop (Aucune Évolution)
Sur un très grand nombre de configurations (EVD.DE 20m/30m, FPE.DE 20m/30m, GMAB 15m/30m, LOGI 5m/10m/45m), l'optimiseur a renvoyé des métriques **strictement identiques** à celles de la Passe 2. 
**Explication technique** : La Passe 3 forçait l'activation du Trailing Stop (`trail_stop = true`). Cependant, l'optimiseur a compris que le sweet spot statique de la Passe 2 était supérieur. Il a donc délibérément sélectionné une valeur de `rr_exit` (seuil de déclenchement du trailing stop) **supérieure ou égale au paramètre de Take Profit fixe (`rnr`)**.
- En conséquence, le Take Profit statique est atteint et déclenché *avant même* que le système n'ait le temps d'activer le trailing stop. Le système retombe alors élégamment sur le comportement statique de la Passe 2 sans dégradation. 
- *Décision* : Pour ces actifs, le Trailing Stop n'apporte aucune plus-value technique ; nous conserverons les paramètres statiques de la Passe 2 (`trail_stop = false`).

### 🟢 Améliorations Majeures via le Trailing Stop
Là où la tendance a pu véritablement s'exprimer avant que le Take Profit ne coupe la position, les gains sont massifs :
- **EVD.DE (5m)** : C'est la configuration qui avait le plus souffert en Passe 2 à cause d'un Take Profit beaucoup trop large (`rnr = 5.0`). Le déclenchement d'un trailing stop très rapide (`rr_exit = 0.2`) et très serré (`trail_stop_size = 1.2 ATR`) corrige le tir : la stratégie encaisse ses micro-gains, remonte le Win Rate de 23.26% à 48.23%, réduit le Drawdown de moitié, et fait bondir le Sortino de 0.4809 à **0.7951** (+65.34%).
- **GMAB (60m)** : Le Take Profit statique était serré (`rnr = 0.5`). L'optimiseur a ajusté le déclencheur exactement sur ce seuil (`rr_exit = 0.5`), transformant le TP fixe en point de bascule vers le suivi de tendance (`trail_stop_size = 1.9 ATR`). Résultat : le Sortino explose à **1.8379** (+22.15%), pour un Profit Factor très solide de 2.27.
- Des hausses notables sont également enregistrées sur **FPE.DE 45m** (+8.73%) grâce aux sauts de volatilité intra-bougie, et **GMAB 20m** (+2.32%).

### 🔴 Dégradation : LOGI 120m
Sur **LOGI (120m)**, l'obligation d'activer le Trailing Stop a empiré les résultats. Le Sortino est tombé à **0.4813** (contre 0.5366 en Passe 2, et 0.6974 en Passe 1). Sur ce grand timeframe, les cibles fixes trop agressives ou le suivi de tendance limitent l'efficacité du crossover brut. *Décision* : Retourner au signal brut ou au modèle statique si plus conservateur.

---

## 3. Conclusion

La Passe 3 confirme qu'un Take Profit statique bien calibré suffit souvent dans la majorité des configurations de trading de `3commas_bot`, car un Trailing Stop risque souvent d'étouffer la position trop tôt sur les bruits intra-bougies (whipsaw). Cependant, sur certains profils particuliers (comme EVD.DE en 5m pour corriger un TP agressif, ou GMAB 60m pour surfer la tendance naissante), il apporte une très forte valeur ajoutée.

Ces paramètres finaux sont désormais validés et consolidés dans le fichier de synthèse globale de la stratégie.
