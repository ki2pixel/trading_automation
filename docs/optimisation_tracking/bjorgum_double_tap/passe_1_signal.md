# Rapport : bjorgum_double_tap - Passe 1 (Détection du Pattern)

**Date d'analyse** : 04 Juin 2026
**Objectif de la Passe** : Trouver la combinaison stable de détection offrant un edge brut réel (optimisation de `tol`, `length`, `dLong`, `dShort`).
**Paramètres figés** : `fib = 100`, `stopPer = 0`, `atrStop = false`.
**Métrique cible** : `return_vs_buy_hold_pct_points`.
**Itérations éligibles totales** : 1 858.

---

## 1. Analyse Globale des Résultats

L'analyse de la Passe 1 a généré **1 858 itérations éligibles** sur un panel de 10 actifs (AMS.MC, EVD.DE, FPE.DE, GMAB, LOGI, NVO, NVS, SAP, SHL.DE, ZEAL.CO), évalués sur des timeframes de 5m à 240m.
Le but était d'isoler la logique de détection de pattern (Double Tap) offrant un avantage statistique positif net (Edge) comparé au Buy & Hold, avant d'introduire des niveaux de cibles ou un stop loss suiveur (Passe 2 et 3).

Cependant, les résultats globaux montrent qu'**aucune combinaison de paramètres n'a réussi à produire un edge positif net** sur les configurations testées. Tous les scores optimaux dégagés par la recherche locale étaient strictement négatifs.

---

## 2. Résultats par Catégorie d'Actifs

### 🟢 Edge Fort (Profit Factor > 1.25 et Net Score positif)
*Aucun actif ne remplit ces critères.*

### 🟡 Neutres / Modérés (Edge faible ou limite)
*Aucun actif ne remplit ces critères.*

### 🔴 Rejetés (Absence d'edge - Net Score négatif ou null)
Tous les actifs et timeframes ayant généré des itérations éligibles ont produit des résultats nettement sous-performants par rapport au Buy & Hold (Return vs B&H fortement négatif).

* **SHL.DE** :
  * **10m** (138 itérations) : Score Max -132.29
  * **15m** (200 itérations) : Score Max -130.04
  * **20m** (200 itérations) : Score Max -130.42
  * **30m** (200 itérations) : Score Max -128.04
  * **45m** (200 itérations) : Score Max -127.18
  * **60m** (184 itérations) : Score Max -130.30
* **AMS.MC** :
  * **15m** (200 itérations) : Score Max -44.50
  * **20m** (168 itérations) : Score Max -47.70
* **NVS** :
  * **5m** (368 itérations) : Score Max -13.50

Les autres couples Symbol/Timeframe (EVD.DE, FPE.DE, GMAB, LOGI, NVO, SAP, ZEAL.CO) n'ont généré aucune itération éligible (0), signifiant que les conditions minimales de trades (Min Trades : 30 à 50) n'ont probablement même pas été atteintes avec ces paramètres, ou que la stratégie ne déclenche pas le pattern.

---

## 3. Recommandations pour la Passe 2

En l'état, **la stratégie `bjorgum_double_tap` échoue à la Passe 1**. Le signal de base (détection de pattern) sans gestion du risque avancée détruit la valeur du capital de manière agressive face au Buy & Hold.

**Recommandation** : Ne pas procéder à la Passe 2 (Cibles & Stops Statiques) sur ces actifs avec cette configuration brute. Il est conseillé de revoir la logique intrinsèque du signal `bjorgum_double_tap`, d'introduire des filtres de tendance supplémentaires, ou d'abandonner son utilisation sur ces actifs.
