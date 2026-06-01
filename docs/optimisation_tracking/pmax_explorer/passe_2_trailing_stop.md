# Rapport : PMax Explorer - Passe 2 (Le Trailing Stop ATR)

**Date d'analyse** : 01 Juin 2026
**Objectif de la Passe** : Optimiser les paramètres du Trailing Stop ATR (`multiplier`, `periods`, `change_atr`) pour l'actif **GMAB** sur les timeframes **30m** et **15m**, afin d'améliorer la gestion du risque et protéger les profits identifiés lors de la Passe 1.
**Paramètres fixés (issus de la Passe 1)** :
- 30m : `length: 7`, `mav: ZLEMA`, `source_col: low`
- 15m : `length: 7`, `mav: VAR`, `source_col: open`

---

## 1. Analyse Globale des Résultats

L'optimisation du Trailing Stop ATR s'est avérée être un franc succès. La stratégie PMax démontre ici sa capacité à capturer la quasi-totalité de la performance d'une approche Buy & Hold (+30% sur la période étudiée) tout en divisant drastiquement le risque (Drawdown maximal d'environ 8% pour la stratégie contre les fortes chutes subies par le B&H).

Ce comportement est exactement ce qui est recherché dans une approche de Trend Following intraday : 
- Les faux signaux (whipsaws) en phase de consolidation génèrent de petites pertes, coupées rapidement par le stop serré.
- Les véritables tendances sont chevauchées jusqu'à épuisement.
Cela se traduit par un Win Rate naturel d'environ 40% à 45%, mais un Average Win/Loss Ratio excellent (> 1.8), poussant le Profit Factor au-delà de 1.55.

---

## 2. Résultats Détaillés et Sweet Spots

### 🟢 GMAB - Timeframe 30m
* **Score (Outperformance vs B&H)** : `-0.21` points de pourcentage (Performance quasi-identique au B&H).
* **Métriques clés** :
  * Total Net PnL : +30.0%
  * Max Drawdown : -8.45% (Excellent)
  * Profit Factor : 1.579
  * Win Rate : 45.3%
  * Ratio Gain/Perte Moyen : 1.87
* **Configuration Optimale** :
  * `multiplier` : 3.1
  * `periods` : 15
  * `change_atr` : false

### 🟢 GMAB - Timeframe 15m
* **Score (Outperformance vs B&H)** : `-0.52` points de pourcentage.
* **Métriques clés** :
  * Total Net PnL : +29.51%
  * Max Drawdown : -7.63% (Excellent)
  * Profit Factor : 1.558
  * Win Rate : 40.9%
  * Ratio Gain/Perte Moyen : 2.22
* **Configuration Optimale** :
  * `multiplier` : 1.7
  * `periods` : 50
  * `change_atr` : false

*Note sur la dynamique* : En 15m (plus bruité), la stratégie préfère un ATR lissé sur une très longue période (`periods: 50`) avec un multiplicateur très serré (`1.7`). À l'inverse, en 30m, elle opte pour un ATR très réactif (`periods: 15`) avec un multiplicateur plus large (`3.1`). Ces deux approches différentes parviennent au même objectif de protection du capital face au bruit de marché.

---

## 3. Recommandations et Conclusion

La configuration pour **GMAB** est désormais validée. Le signal de base (Moyenne Mobile ultra-réactive) combiné à un Trailing Stop adapté à l'unité de temps fournit une stratégie de suivi de tendance robuste, affichant un Risk/Reward (Net Profit to Max Drawdown) d'environ 300%.

**Prochaines Étapes** :
1. Figer ces deux configurations (`GMAB_30m` et `GMAB_15m`) dans les portefeuilles de production.
2. La stratégie PMax Explorer est considérée "Prête à l'emploi" pour cet actif spécifique. Il n'est pas nécessaire de lancer une Passe 3 (sorties alternatives ou filtres complexes), le Trailing Stop ATR remplissant parfaitement son rôle directionnel et défensif.
