# Rapport : Noise Boundary Intraday - Passe 2

**Date d'analyse** : 30 Mai 2026  
**Objectif de la Passe** : Calibrer la fréquence des trades et le délai après ouverture de la session boursière (Timing) sur la base des "Sweet Spots" trouvés en Passe 1.  
**Paramètres optimisés** : `trade_frequency_bars`, `start_trade_after_open_minutes`, `entry_on_high_low`.  
**Paramètres bloqués** : `lookback_days`, `volatility_multiplier_enter`, `volatility_multiplier_exit` (fixés selon les résultats de la Passe 1).

---

## 1. Analyse Globale des Résultats

L'optimisation a été relancée sur les actifs sur-performants (AMS.MC, FPE.DE, GMAB) en utilisant l'outil "Range" pour palier aux limitations de parsing de l'interface.

Les résultats montrent une convergence très nette et étonnamment homogène sur les trois actifs testés : la stratégie privilégie une **haute fréquence d'activité** associée à un **délai d'environ une demi-heure** après l'ouverture.

---

## 2. Résultats par Actif

Voici les "Sweet Spots" extraits du dernier run de la Passe 2 :

### AMS.MC (Timeframe : 60m)
* **Score** : 156.71 (200 itérations éligibles)
* **Paramètres de Timing trouvés** :
  * `trade_frequency_bars` : 1
  * `start_trade_after_open_minutes` : 28
  * `entry_on_high_low` : True

### FPE.DE (Timeframe : 120m)
* **Score** : 44.56 (200 itérations éligibles)
* **Paramètres de Timing trouvés** :
  * `trade_frequency_bars` : 1
  * `start_trade_after_open_minutes` : 34
  * `entry_on_high_low` : True

### GMAB (Timeframe : 30m)
* **Score** : 21.70 (200 itérations éligibles)
* **Paramètres de Timing trouvés** :
  * `trade_frequency_bars` : 1
  * `start_trade_after_open_minutes` : 27
  * `entry_on_high_low` : True

---

## 3. Interprétation & Recommandations

1. **Trade Frequency (Fréquence)** : L'optimiseur sélectionne systématiquement `trade_frequency_bars = 1`. Cela indique que la stratégie "Noise Boundary" n'a pas besoin d'être temporisée/bridée artificiellement après une entrée. Dès que les conditions de volatilité (le signal de la Passe 1) sont réunies, il est statistiquement intéressant de prendre le trade, sans attendre X barres de "refroidissement".
2. **Délai post-ouverture** : Le délai optimal (`start_trade_after_open_minutes`) gravite entre 27 et 34 minutes pour tous les actifs. C'est une information extrêmement précieuse : **le bruit de la première demi-heure de cotation est toxique**. L'algorithme obtient de bien meilleures performances en ignorant les pics d'ouverture et en attendant que le véritable flux de la journée se mette en place (vers 09h30).
3. **Trigger d'entrée** : L'option `entry_on_high_low = True` semble être le standard de facto pour améliorer les entrées sur breakout.

### Prochaine Étape (Passe 3)
La dernière étape consistera à optimiser la **gestion des sorties** (`exit_mode` et les paramètres du mode `ladder`).
Vous devrez bloquer dans votre configuration :
* Les paramètres de la **Passe 1** (`lookback_days`, `volatility_multipliers`)
* Les paramètres de la **Passe 2** (`trade_frequency_bars = 1`, `start_trade_after_open_minutes = 30`, `entry_on_high_low = true`). *(Note : Vous pouvez arrondir le délai à 30 minutes pour plus de standardisation).*
