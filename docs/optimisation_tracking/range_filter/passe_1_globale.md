# Rapport : Range Filter - Passe Unique (Globale)

**Date d'analyse** : 30 Mai 2026
**Objectif de la Passe** : Trouver les meilleurs paramètres (`sampling_period`, `range_multiplier`, `source_col`) en une seule passe, cette stratégie ayant un espace de recherche suffisamment petit pour éviter la sur-optimisation.
**Paramètres optimisés** : `sampling_period`, `range_multiplier`, `source_col`.

---

## 1. Analyse Globale des Résultats

L'analyse des rapports générés par l'optimiseur local révèle des disparités importantes entre les actifs. Seuls certains actifs démontrent une réceptivité positive à cette stratégie, tandis que la majorité affiche des scores de rendement négatifs, confirmant que le Range Filter n'est pas un signal directionnel universel.

Un grand nombre d'itérations sont éligibles (elles passent les filtres de nombre minimal de trades et de drawdown maximal), ce qui prouve que l'algorithme génère des trades réguliers, mais la rentabilité de ces trades est souvent bien inférieure au "Buy & Hold" pour de nombreux actifs.

---

## 2. Résultats par Actif et Timeframe

Voici la synthèse des itérations éligibles et des meilleurs scores (`return_vs_buy_hold_pct_points`) :

### 🟢 Les Sur-Performants (Edge Fort)
* **GMAB** (Genmab) :
  L'actif montre une très belle réceptivité au Range Filter, en particulier sur les timeframes moyens avec énormément d'itérations éligibles (forte robustesse statistique).
  * **20m** : 831 itérations éligibles | Meilleur Score : 13.20
  * **30m** : 300 itérations éligibles | Meilleur Score : 13.25
  * **15m** : 350 itérations éligibles | Meilleur Score : 7.93
  * **45m** : 300 itérations éligibles | Meilleur Score : 5.83

### 🟡 Les Moyens / Modérés
* **FPE.DE** (Fuchs Petrolub) :
  Scores positifs, mais moins marqués que GMAB.
  * **45m** : 333 itérations éligibles | Meilleur Score : 4.39
  * **240m** : 250 itérations éligibles | Meilleur Score : 3.32
  * **5m** : 200 itérations éligibles | Meilleur Score : 1.85
  * **30m** : 77 itérations éligibles | Meilleur Score : 1.51
  * *(Note: Le 20m a un score de 3.64 mais 1 seule itération éligible, non significatif)*
* **NVS** (Novartis) :
  Scores quasi neutres / très légèrement positifs (0.68 sur 120m). Ne présente pas d'avantage clair.

### 🔴 Les Rejetés (Absence d'Edge)
Ces actifs ont affiché des scores de rendement quasi-exclusivement négatifs sur l'ensemble des timeframes, avec parfois un grand nombre d'itérations éligibles (donc beaucoup de trades, mais perdants).
* **AMS.MC** (Amadeus) : Scores de -12 à -27.
* **EVD.DE** : Scores de -5 à -24.
* **LOGI** : Scores très négatifs, entre -44 et -62.
* **NVO** (Novo Nordisk) : Scores de -22 à -41.
* **SAP** : Scores désastreux (-173 à -182).
* **SHL.DE** : Scores désastreux (-97 à -107).
* **ZEAL.CO** : Scores désastreux (-115 à -138).

*Conclusion* : La stratégie Range Filter ne doit être déployée que sur les actifs qui y réagissent favorablement (GMAB, et potentiellement FPE.DE avec prudence). Les autres actifs doivent être écartés pour cette stratégie.

---

## 3. Recommandations et Prochaines Étapes

1. **Rejeter définitivement les actifs 🔴** pour la stratégie Range Filter.
2. La stratégie Range Filter étant de "Catégorie A" (1 seule passe), l'optimisation est **terminée**. Les valeurs trouvées lors de cette passe globale constituent les Sweet Spots définitifs.
3. Les valeurs optimales à conserver pour la configuration de production (ou paper trading) seront consignées dans le fichier `synthese_strategie.md`.
