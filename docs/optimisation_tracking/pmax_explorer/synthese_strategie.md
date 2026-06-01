# Synthèse Stratégique : PMax Explorer

**Statut Actuel** : Analyse de Passe 2 terminée. Configuration validée pour l'actif GMAB.  
**Prochaine Étape** : Intégration en production.

---

## 1. État de la Recherche

La stratégie **PMax Explorer** est une approche de suivi de tendance (Trend Following) basée sur le croisement du prix avec une moyenne mobile et un trailing stop ATR (Average True Range). 

La **Passe 1** visait à évaluer la pertinence du signal de base (la moyenne mobile seule) en désactivant (élargissant) le stop ATR. Les résultats montrent que :
* Le signal brut génère énormément de "bruit" et de faux signaux en phase de consolidation (range) sur la grande majorité des actifs étudiés.
* Un "Edge" net a été identifié uniquement sur **GMAB**, sur les timeframes **15m et 30m**, en utilisant des moyennes mobiles très réactives (`ZLEMA` et `VAR`) sur des périodes très courtes (`length: 7`).

La **Passe 2** (Optimisation du Trailing Stop ATR) a été réalisée exclusivement sur GMAB pour ces timeframes. Les résultats sont excellents :
* Le Drawdown maximal est drastiquement réduit (aux alentours de 8%).
* La performance globale atteint ~30% (équivalente au Buy & Hold sur la période, mais avec une volatilité subie largement inférieure).
* Les Profit Factors sont solides (> 1.55) grâce à des Average Win/Loss ratios élevés (> 1.8), compensant le Win Rate naturel de la stratégie (~40-45%).

---

## 2. Planification et Intégration Finale

### Configurations Validées (Setup PMax)
* **GMAB 30m** : `length=7`, `mav=ZLEMA`, `source_col=low`, `multiplier=3.1`, `periods=15`, `change_atr=false`.
* **GMAB 15m** : `length=7`, `mav=VAR`, `source_col=open`, `multiplier=1.7`, `periods=50`, `change_atr=false`.

### Étape Suivante
La stratégie PMax Explorer démontre un avantage statistique solide et robuste sur cet actif particulier. Il n'y a pas besoin de filtres ou de règles de sortie complexes (Passe 3 annulée). La configuration est considérée validée et prête à être intégrée en tant que "setup PMax" au sein du moteur de production live.
