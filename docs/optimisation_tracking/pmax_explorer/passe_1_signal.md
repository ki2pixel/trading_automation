# Rapport : PMax Explorer - Passe 1 (Le Signal de Base)

**Date d'analyse** : 01 Juin 2026
**Objectif de la Passe** : Valider le signal brut de la stratégie PMax Explorer en bloquant le paramètre `multiplier` du trailing stop ATR à une valeur large (`5.0`) pour éviter les déclenchements prématurés et isoler l'edge directionnel de la moyenne mobile.
**Paramètres cibles optimisés** : `length`, `mav`, `source_col`.
**Paramètre bloqué** : `multiplier = 5.0`.

---

## 1. Analyse Globale des Résultats

Contrairement à la stratégie `noise_boundary_intraday`, **toutes les configurations ont fourni 200 itérations éligibles**. Cela s'explique par la nature continue du signal "trend-following" (suivi de tendance) de la stratégie PMax, qui ne bloque pas sur le filtre `min_closed_trades` car elle est presque toujours en position.

Cependant, de nombreuses configurations affichent des **scores négatifs**. Ces scores représentent une sous-performance par rapport à une stratégie Buy & Hold sur la même période. Cela s'explique principalement par le fait que, sans filtre de tendance fort pour éviter les phases de "range" (marché plat), le signal brut accumule des faux signaux (whipsaws) qui détériorent la performance globale de la stratégie.

---

## 2. Résultats par Catégorie d'Actifs

### 🟢 Les Sur-Performants (Edge Fort)
* **GMAB** : C'est le seul actif de la sélection qui se montre résilient et largement profitable par rapport au Buy & Hold sur les unités de temps inférieures. L'edge est particulièrement visible sur ces "sweet spots" :
  * **30m** : Meilleur score `+4.4499` (`length`: 7, `mav`: `ZLEMA`, `source_col`: `low`).
  * **15m** : Meilleur score `+1.7903` (`length`: 7, `mav`: `VAR`, `source_col`: `open`).
  * *Note : On observe que les moyennes mobiles réactives (ZLEMA, VAR) avec une période très courte (`length: 7`) sont les plus adaptées pour capturer rapidement la tendance sur cet actif.*

### 🟡 Les Neutres / Proches de l'équilibre
Ces actifs limitent la casse avec des sous-performances modérées face au Buy & Hold, ce qui indique un potentiel si des filtres supplémentaires (ou un meilleur stop) sont ajoutés, mais un edge brut moins évident.
* **NVS** : Meilleur score sur **30m** : `-4.2415` (`length`: 5, `mav`: `VAR`, `source_col`: `low`).
* **AMS.MC** : Meilleur score sur **5m** : `-7.6426` (`length`: 6, `mav`: `WMA`, `source_col`: `open`).

### 🔴 Les Rejetés (Absence d'Edge Tendance Court Terme)
Ces actifs ne montrent aucune aptitude à la capture de tendance court terme via ce signal brut. Les scores sont catastrophiques :
* **NVO** : Meilleur score sur 10m à `-25.2139` (`length`: 6, `mav`: `TMA`, `source_col`: `high`).
* **EVD.DE** : Meilleur score sur 15m à `-22.5308` (`length`: 5, `mav`: `WWMA`, `source_col`: `low`).
* **LOGI** : Scores abyssaux, ex: **45m** à `-440.2599`.
* **SAP** : Fortement négatif, ex: **120m** à `-176.5073`.
* **SHL.DE** : Fortement négatif, ex: **15m** à `-107.0933`.
* **ZEAL.CO** : Fortement négatif, ex: **1m** à `-124.7063`.

---

## 3. Recommandations pour la Passe 2

1. **Restriction du périmètre des actifs** : 
   * Valider le passage en Passe 2 **uniquement** pour l'actif viable **GMAB** sur les timeframes **15m et 30m**.
   * Exclure temporairement tous les autres actifs pour cette stratégie (trop de "bruit" et de faux signaux sur la tendance court terme).
2. **Configuration pour la Passe 2** :
   * **Bloquer les sweet spots** : Figer les paramètres `length`, `mav`, et `source_col` sur les valeurs trouvées lors de cette Passe 1 pour GMAB (ex: ZLEMA/VAR, length=7, etc.).
   * **Paramètres à optimiser (Trailing Stop)** : Lancer l'optimisation des paramètres liés au Trailing Stop ATR de PMax, à savoir `periods`, `multiplier` et `change_atr`. L'objectif de la Passe 2 sera de resserrer le stop au bon moment pour protéger les gains sans étouffer la tendance.
