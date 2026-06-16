# Rapport : Lorentzian Classification - Passe 1 (Plus Proches Voisins & Features)

**Date d'analyse** : 16 Juin 2026
**Objectif de la Passe** : Optimiser le nombre de voisins du KNN (`neighbors_count`) et les paramètres des 5 features de base (RSI1, WaveTrend, CCI, ADX, RSI2) comprenant leurs périodes (`param_a`) et lissages/coefficients (`param_b`).
**Paramètres bloqués** : `use_volatility_filter = false`, `use_regime_filter = false`, `use_kernel_filter = false`.
**Métriques cibles** : Score `return_vs_buy_hold_pct_points` > 0 (Surperformance par rapport au Buy & Hold), Max Drawdown tolérable entre 0% et -25%, Profit Factor minimum attendu de 1.25, Nombre minimal de trades clôturés : 50+.

---

## 1. Analyse Globale des Résultats

L'analyse globale a permis de traiter **16 978 itérations éligibles** sur l'ensemble des rapports générés pour la stratégie `lorentzian_classification`.
Il apparaît que la classification KNN avec les caractéristiques brutes (sans filtres macro ou Kernel) a de grandes difficultés à générer un Alpha brut robuste sur la grande majorité des symboles. Les scores de surperformance sont soit largement négatifs, soit marqués par des tirages en capital (drawdowns) excessifs.

---

## 2. Résultats par Catégorie d'Actifs

### 🟢 Les Sur-Performants (Edge Identifié)
**Aucun actif ne valide strictement l'ensemble des critères d'edge.**
Bien que NVO dégage une surperformance absolue par rapport au Buy & Hold sur de multiples unités de temps (scores fortement positifs), le Max Drawdown subi (estimé à plus de -60% du capital alloué, avec des valeurs brutes de -186 à -335) dépasse très largement la tolérance stricte de -25%.

### 🔴 Les Rejetés (Absence d'Edge ou Critères non respectés)
Tous les actifs sont rejetés lors de cette première passe, pour les raisons suivantes :

* **NVO** : Rejeté pour **Max Drawdown excessif**. Il affiche des scores de surperformance exceptionnels (Score +125.94 en 20m, PF 1.38, 1511 trades), mais au prix d'un Drawdown inacceptable. Les paramètres de features génèrent des signaux rentables mais le risque n'est pas maîtrisé.
* **FPE.DE** : Rejeté pour **Sous-performance légère**. Le Profit Factor est très bon (PF 1.53 en 60m) et le Drawdown quasi-nul, mais le système sous-performe très légèrement le Buy & Hold (Score: -3.83).
* **GMAB** : Rejeté pour **Sous-performance**. Bons Profit Factors (ex: PF 1.63 en 30m, PF 1.44 en 15m), mais le score reste négatif (autour de -25).
* **EVD.DE** : Rejeté pour **Sous-performance**. Profit Factor autour de 1.4, Max Drawdown maîtrisé (< 5%), mais les scores sont bloqués à -31.
* **NVS** : Rejeté pour **Sous-performance** (Score: -9.73 en 120m, PF: 1.38).
* **AMS.MC** : Rejeté pour **Sous-performance marquée** (Scores autour de -50).
* **SHL.DE** : Rejeté pour **Sous-performance marquée** (Scores autour de -113).
* **SAP** : Rejeté pour **Forte sous-performance** (Scores autour de -183).
* **LOGI** : Rejeté pour **Forte sous-performance extrême** (Scores autour de -480).
* **ZEAL.CO** : Rejeté (Meilleur score : -14.10, non éligible aux critères PF/DD ou manque de trades/sur-performance).

---

## 3. Recommandations

L'optimisation des features de base du Machine Learning (Lorentzian Classification KNN) montre que le modèle pur, sans lissage, souffre de la volatilité directionnelle (bruit).
* Le modèle sur **NVO** montre que le KNN trouve un edge prédictif très fort, mais son agressivité nécessite l'activation des filtres.
* Les actifs comme **FPE.DE** ou **GMAB** suggèrent que la stratégie est capable de générer d'excellents Profit Factors, mais ne compense pas l'achat et la conservation sur leurs périodes de hausse macroéconomique.

**Plan pour la Passe 2** :
Il n'y a pas d'actif idéal pour l'instant respectant les conditions sans filtres. Il est recommandé de conserver **NVO** (pour l'Alpha directionnel) et **FPE.DE / GMAB** (pour la stabilité du PF et les très bas Drawdowns) afin de mener la Passe 2.
Conformément à la feuille de route, cette seconde passe se concentrera sur l'activation des filtres macroscopiques (`use_volatility_filter`, `use_regime_filter`, `regime_threshold`) pour dompter les drawdowns extrêmes constatés sur NVO et éliminer les signaux KNN contradictoires sur les autres symboles. Le lissage Nadaraya-Watson sera réservé à la Passe 3.

**Paramètres à bloquer en vue de l'optimisation (Base Parameters)** :
* **NVO** :
  * 20m : `neighbors_count: 17`, `f1_param_a: 20`, `f2_param_a: 9`, `f3_param_a: 25`, `f4_param_a: 29`, `f5_param_a: 20`
  * 30m : `neighbors_count: 6`, `f1_param_a: 27`, `f2_param_a: 12`, `f3_param_a: 27`, `f4_param_a: 23`, `f5_param_a: 15`
  * 60m : `neighbors_count: 5`, `f1_param_a: 13`, `f2_param_a: 12`, `f3_param_a: 22`, `f4_param_a: 40`, `f5_param_a: 9`
* **GMAB** :
  * 30m : `neighbors_count: 19`, `f1_param_a: 22`, `f2_param_a: 20`, `f3_param_a: 39`, `f4_param_a: 22`, `f5_param_a: 20`
  * 60m : `neighbors_count: 17`, `f1_param_a: 25`, `f2_param_a: 8`, `f3_param_a: 28`, `f4_param_a: 17`, `f5_param_a: 13`
* **FPE.DE** :
  * 60m : `neighbors_count: 4`, `f1_param_a: 29`, `f2_param_a: 8`, `f3_param_a: 21`, `f4_param_a: 14`, `f5_param_a: 16`
  * 120m : `neighbors_count: 3`, `f1_param_a: 23`, `f2_param_a: 25`, `f3_param_a: 31`, `f4_param_a: 24`, `f5_param_a: 12`
