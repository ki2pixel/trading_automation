# Rapport : 3commas_bot - Passe 1 (Le Signal de Base)

**Date d'analyse** : 03 Juin 2026
**Objectif de la Passe** : Validation du signal de croisement MA brut (Croisement de Moyennes Mobiles).
**Paramètres figés** : `trail_stop = false`, `rnr = 1.0`, `risk_m = 1.0`, `use_safety_stop = false`.
**Métrique cible** : `sortino_ratio`.
**Itérations éligibles totales** : 44 014.

---

## 1. Analyse Globale des Résultats

L'analyse de la Passe 1 a généré un volume important de **44 014 itérations éligibles** sur 10 actifs, évalués sur des timeframes de 1m à 240m. 
Le but était d'isoler les paires de moyennes mobiles (types et longueurs) offrant un avantage statistique (edge) mesuré par le Ratio de Sortino, avant d'introduire tout paramètre de gestion du risque ou de trailing stop.

---

## 2. Résultats par Catégorie d'Actifs

### 🟢 Edge Fort (Sortino > 0.50)
Ces actifs et timeframes affichent les meilleurs ratios de Sortino, démontrant un signal de croisement robuste et une asymétrie positive des rendements.

* **GMAB** : Très performant sur les timeframes courts et moyens.
  * **60m** : Score 1.0578 (`DEMA 8` / `HMA 10`)
  * **30m** : Score 0.9536 (`HMA 5` / `DEMA 23`)
  * **20m** : Score 0.8312 (`EMA 6` / `HMA 128`)
  * **15m** : Score 0.8936 (`HMA 6` / `VWMA 18`)
* **FPE.DE** : Excellents résultats sur timeframes très courts à moyens.
  * **45m** : Score 0.7597 (`HMA 41` / `WMA 10`)
  * **30m** : Score 0.7272 (`HMA 52` / `EMA 10`)
  * **20m** : Score 0.8538 (`DEMA 30` / `HMA 32`)
  * **5m** : Score 0.8889 (`WMA 36` / `HMA 59`)
* **LOGI** : Solide sur une large gamme de timeframes.
  * **120m** : Score 0.6974 (`HEMA 7` / `SMA 13`)
  * **45m** : Score 0.6872 (`HEMA 6` / `SMA 13`)
  * **10m** : Score 0.7066 (`HEMA 5` / `T3 15`)
  * **5m** : Score 0.7391 (`HEMA 8` / `HMA 57`)
* **EVD.DE** : Bons signaux identifiés principalement en intraday.
  * **30m** : Score 0.6881 (`DEMA 40` / `HMA 140`)
  * **20m** : Score 0.5965 (`WMA 20` / `WMA 71`)
  * **5m** : Score 0.6271 (`SMA 49` / `VWMA 57`)

### 🟡 Neutres / Modérés (Sortino 0.30 à 0.49)
Ces actifs présentent un léger edge mais avec une volatilité asymétrique moins favorable. Ils peuvent être conservés pour test mais nécessiteront une gestion stricte du risque.

* **SAP** : 45m (Score 0.4615 | `WMA 5` / `HMA 33`)
* **ZEAL.CO** : 45m (Score 0.4248 | `DEMA 8` / `HMA 13`)
* **NVS** : 10m (Score 0.3763 | `HEMA 5` / `EMA 40`)
* **SHL.DE** : 20m (Score 0.3550 | `SMA 22` / `HMA 81`)

### 🔴 Rejetés (Absence d'edge - Sortino < 0.30)
Ces actifs n'ont pas démontré de viabilité avec cette logique de croisement brut.

* **AMS.MC** : Max 0.3533 sur 120m, mais en moyenne très bas. Rejeté.
* **NVO** : Max 0.2722 sur 5m. Rejeté.

---

## 3. Recommandations pour la Passe 2

Pour la **Passe 2 (Risk-Management et Ratios de Profit)**, l'optimisation doit se concentrer exclusivement sur les actifs de la catégorie **Edge Fort (🟢)**.
Les couples de moyennes mobiles identifiés pour ces actifs devront être figés en dur pour éviter le sur-apprentissage et réduire l'espace de recherche. Les variables à optimiser lors de la prochaine étape incluront les niveaux de stop loss, take profit (ratios risk/reward) et les paramètres de filtres additionnels si nécessaire.

---

## 4. Résultats Extension de Campagne (18 Juin 2026)

L'extension de campagne sur les nouveaux actifs screenés a généré un total de **461 itérations éligibles**. La stratégie s'est révélée très sélective sur cette cohorte, la grande majorité des candidats ne parvenant pas à franchir les contraintes strictes imposées (notamment le minimum de trades et la rentabilité requise).

### 🟢 Edge Fort (Sortino > 0.50)
* **TENITEUR** : Score 0.7379 sur 30m (`HEMA 5` / `SMA 38`) [223 itérations éligibles]

### 🟡 Neutres / Modérés (Sortino 0.30 à 0.49)
*Aucun actif dans cette catégorie.*

### 🔴 Rejetés (Absence d'edge - Sortino < 0.30 ou 0 itération)
* **PHIANLEUR** (Max 0.2852 sur 45m), **MRKDEEUR** (Max 0.2475 sur 45m), **ABIBEEUR** (Max 0.0000), **AIFREUR** (Max 0.0000), **AKZANLEUR** (Max 0.0000), **BEIDEEUR** (Max 0.0000), **BNFREUR** (Max 0.0000), **CAPFREUR** (Max 0.0000), **COVDEEUR** (Max 0.0000), **DIAITEUR** (Max 0.0000), **DPWDEEUR** (Max 0.0000), **DSMNLEUR** (Max 0.0000), **EDPPTEUR** (Max 0.0000), **ELI1VFIEUR** (Max 0.0000), **ERGITEUR** (Max 0.0000), **HEN3DEEUR** (Max 0.0000), **HNRDEEUR** (Max 0.0000), **ITXESEUR** (Max 0.0000), **MBITEUR** (Max 0.0000), **MHGNONOK** (Max 0.0000), **ORKNONOK** (Max 0.0000), **RECITEUR** (Max 0.0000), **RMSFREUR** (Max 0.0000), **STERVFIEUR** (Max 0.0000), **TELNONOK** (Max 0.0000), **TRNITEUR** (Max 0.0000), **VIEFREUR** (Max 0.0000), **VPKNLEUR** (Max 0.0000). Rejetés.

---

## 5. Mise à jour des Recommandations pour la Passe 2

Pour la **Passe 2**, nous intégrons le nouvel actif validé **TENITEUR** à la liste des actifs qualifiés. Les paramètres de base devront être figés sur `HEMA 5` et `SMA 38` pour cet actif.
