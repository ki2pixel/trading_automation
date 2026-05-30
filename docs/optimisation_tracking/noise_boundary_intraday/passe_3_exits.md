# Rapport : Noise Boundary Intraday - Passe 3

**Date d'analyse** : 30 Mai 2026  
**Objectif de la Passe** : Optimiser la gestion des sorties (Exit Mode) et l'échelle de prise de profit / stop loss (Ladder) pour lisser les gains et sécuriser les profits intraday.  
**Paramètres optimisés** : `stoploss_ladder_step0`, `stoploss_ladder_step1`, `stoploss_ladder_ratio0`, `takeprofit_ladder_step0` (avec `exit_mode` = ladder).  
**Paramètres bloqués** :  
* **Passe 1** : `lookback_days`, `vol_enter`, `vol_exit` (spécifiques par actif)
* **Passe 2** : `trade_frequency_bars` = 1, `start_trade_after_open_minutes` = 30, `entry_on_high_low` = true

---

## 1. Analyse Globale des Résultats

L'ajout du système de gestion des sorties en *ladder* (échelle) a **nettement amélioré les scores globaux** de tous les actifs qui ont survécu à l'optimisation. Cela confirme qu'un signal directionnel fort (Passe 1) combiné à un bon timing (Passe 2) bénéficie énormément d'une prise de profit dynamique en intraday.

Cependant, comme constaté par l'utilisateur, l'actif **GMAB sur le timeframe 20m n'a généré aucune itération éligible**.
**Explication** : L'empilement des contraintes commence à se faire sentir. Le signal de la Passe 1 sur GMAB 20m était correct (score de 10.5), mais lorsqu'on lui a imposé d'attendre 30 minutes après l'ouverture (Passe 2) et de sortir en ladder (Passe 3), la stratégie n'arrive plus à générer assez de trades ou dépasse le Drawdown maximum autorisé (-25%). Le "sweet spot" s'est tout simplement volatilisé pour ce timeframe précis. Heureusement, GMAB sur **30m** a brillamment réussi le test.

---

## 2. Résultats par Actif et Timeframe (Score Final)

Voici les "Sweet Spots" définitifs extraits de la Passe 3. Vous noterez l'évolution positive du score par rapport à la Passe 1.

### AMS.MC (Amadeus)
L'actif star de cette stratégie confirme sa puissance sur les grandes timeframes intraday, avec une envolée du score sur le 60m.
* **Timeframe 60m** : 
  * Score Final : **219.49** *(vs 156.71 en Passe 1)* | 250 Itérations éligibles
  * `stoploss_ladder_step0` = -1.6% | `stoploss_ladder_step1` = -2.4%
  * `takeprofit_ladder_step0` = +2.2% | `ratio0` = 0.1 (Ferme 10% de la position, laisse courir le reste)
* **Timeframe 120m** : 
  * Score Final : **194.22** *(vs 183.19 en Passe 1)* | 350 Itérations éligibles
  * `stoploss_ladder_step0` = -1.8% | `stoploss_ladder_step1` = -2.8%
  * `takeprofit_ladder_step0` = +1.2% | `ratio0` = 0.9 (Prend 90% des gains rapidement à +1.2%)

### FPE.DE (Fuchs Petrolub)
* **Timeframe 120m** : 
  * Score Final : **54.83** *(vs 44.56 en Passe 1)* | 200 Itérations éligibles
  * `stoploss_ladder_step0` = -1.8% | `stoploss_ladder_step1` = -2.2%
  * `takeprofit_ladder_step0` = +1.7% | `ratio0` = 0.9 (Prend 90% des gains)

### GMAB (Genmab)
* **Timeframe 30m** : 
  * Score Final : **27.02** *(vs 21.70 en Passe 1)* | 250 Itérations éligibles
  * `stoploss_ladder_step0` = -1.5% | `stoploss_ladder_step1` = -1.6% (Stop suiveur très serré)
  * `takeprofit_ladder_step0` = +0.9% | `ratio0` = 0.9 (Prend 90% des gains très tôt)

---

## 3. Conclusion de la Stratégie Noise Boundary

**La stratégie est validée.** L'approche intraday basée sur la volatilité fonctionne extrêmement bien si on évite le bruit de l'ouverture (30 minutes) et si on cible les bonnes timeframes (60m - 120m pour la majorité, 30m pour certains tickers très spécifiques).

**Recommandation de Money Management (Ladder)** : 
On observe deux écoles très rentables trouvées par l'algorithme :
1. **Sécurisation massive (FPE.DE 120m, GMAB 30m, AMS.MC 120m)** : Le `ratio0` est à 0.9 (90%). L'algorithme prend quasiment tout son profit dès la première cible atteinte (entre +0.9% et +1.7%).
2. **Laisser courir (AMS.MC 60m)** : Le `ratio0` est à 0.1 (10%). L'algorithme prend très peu de profit initial à +2.2% pour s'assurer que le trade est "free", puis laisse le reste de la position attraper les immenses mouvements de la journée. Le score faramineux (219) prouve l'efficacité de cette méthode sur les actifs les plus trendings.
