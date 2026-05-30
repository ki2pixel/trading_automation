# Rapport : Noise Boundary Intraday - Passe 1

**Date d'analyse** : 29 Mai 2026  
**Objectif de la Passe** : Prouver que le breakout des bandes de volatilité possède un edge directionnel brut (sans sorties complexes).  
**Paramètres optimisés** : `lookback_days`, `volatility_multiplier_enter`, `volatility_multiplier_exit`.  
**Paramètres bloqués** : `exit_mode = time_only`, Safety stop OFF, filtres VWAP OFF.

---

## 1. Analyse Globale des Résultats

L'analyse des rapports générés par l'optimiseur local a révélé une disparité très importante selon les actifs (Symboles) et les unités de temps (Timeframes).

Beaucoup de rapports affichent **0 itérations éligibles**. Cela est dû aux filtres stricts du backtesteur (ex: `min_closed_trades = 100`, `max_drawdown_pct = -25.0%`). Pour une passe 1 qui évalue un signal "brut" (sans trailing stop ni prise de profit ladder), de nombreuses combinaisons n'arrivent pas à maintenir un drawdown faible ou à générer 100 trades sur la période.

Cependant, certains couples Symbole/Timeframe ont brillamment passé ces filtres, prouvant la présence d'un edge directionnel fort.

---

## 2. Résultats par Actif et Timeframe

Voici la synthèse des itérations éligibles et des meilleurs scores (`return_vs_buy_hold_pct_points`) :

### 🟢 Les Sur-Performants (Edge Fort)
Ces actifs ont montré une grande robustesse, avec de nombreuses itérations éligibles et des scores très élevés.
* **AMS.MC** (Amadeus) :
  * **120m** : 239 itérations éligibles | Meilleur Score : 183.18
  * **60m** : 432 itérations éligibles | Meilleur Score : 156.70
  * **45m** : 108 itérations éligibles | Meilleur Score : 133.11
  * *Note : Excellente réaction de cet actif sur les timeframes moyennes/longues en intraday.*
* **FPE.DE** (Fuchs Petrolub) :
  * **120m** : 115 itérations éligibles | Meilleur Score : 44.56
* **GMAB** (Genmab) :
  * **20m** : 169 itérations éligibles | Meilleur Score : 10.51
  * **30m** : 20 itérations éligibles | Meilleur Score : 21.70

### 🟡 Les Moyens / Spécifiques
Ces actifs ne passent les filtres que sur un timeframe très spécifique, ou avec peu d'itérations éligibles.
* **NVO** (Novo Nordisk) : **120m** (1 itération éligible, Score : 133.11)
* **NVS** (Novartis) : **15m** (1 itération éligible, Score : 26.60)
* **SHL.DE** (Siemens Healthineers) : **15m** (11 itérations éligibles, Score : 2.21)

### 🔴 Les Rejetés (Absence d'Edge)
Même après un assouplissement des filtres lors d'une seconde tentative, ces actifs démontrent que le signal brut n'est pas viable pour eux :
* **EVD.DE** : Quelques itérations éligibles sur `5m` (9 itérations), mais avec un score fortement négatif (-16.91).
* **ZEAL.CO** : Des itérations éligibles sur `45m`, `60m`, et `120m`, mais avec des scores catastrophiques (allant de -104 à -116).
* **LOGI** et **SAP** : Toujours 0 itération éligible sur l'ensemble des timeframes testés.

*Conclusion pour ces actifs* : Le comportement de ces sous-jacents (probablement mean-reverting ou trop peu volatils en intraday) est structurellement incompatible avec la stratégie Noise Boundary. Il est recommandé de **ne pas les inclure** dans les passes suivantes pour cette stratégie.

---

## 3. Recommandations et Prochaines Étapes

1. **Adapter les filtres pour la Passe 1** : Les symboles classés 🔴 ne sont pas nécessairement inexploitables. Sur de grandes unités de temps (ex: 120m, 240m), imposer 100 trades minimum est mathématiquement difficile si le signal est sélectif. 
   * *Recommandation* : Pour relancer ou évaluer ces actifs lors d'une passe de signal brut, il conviendrait d'assouplir le `min_closed_trades` (ex: 50) ou le `max_drawdown_pct` (ex: -30%), en sachant que la Passe 3 (Sorties) viendra réduire le drawdown par la suite.
2. **Fixer les Sweet Spots par groupe de Timeframe** :
   * La stratégie ne se comporte pas de la même façon sur du 15m (bruit élevé) et du 120m (tendance intraday forte). 
   * Pour préparer la **Passe 2**, vous devriez extraire les paramètres `lookback_days` et `volatility_multiplier` du meilleur résultat 120m pour AMS.MC, et l'utiliser comme base solide pour optimiser le timing sur ces timeframes.
3. **Passe 2** : Les actifs performants (AMS.MC, FPE.DE, GMAB) sont prêts pour la Passe 2. Vous pouvez bloquer les valeurs trouvées dans les `best.json` de leurs meilleurs timeframes respectifs, et lancer l'optimisation des paramètres d'activité (`trade_frequency_bars`, `start_trade_after_open_minutes`, etc.).
