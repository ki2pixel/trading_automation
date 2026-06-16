# Rapport : Lorentzian Classification - Passe 2 (Filtres Macro)

**Date d'analyse** : 16 Juin 2026
**Objectif de la Passe** : Réduire le bruit (faux positifs) du modèle KNN en activant les filtres de contexte macroéconomique (`use_volatility_filter`, `use_regime_filter`, `regime_threshold`, `use_adx_filter`, `use_ema_filter`, `use_sma_filter`).
**Paramètres bloqués** : Configurations KNN (`neighbors_count`) et indicateurs de base (`f_param_a`) issues de la Passe 1. `use_kernel_filter = false`.
**Métriques cibles** : Réduire le Drawdown de NVO sous la barre des -25%, et retrouver une rentabilité nette positive (Alpha > 0) pour GMAB et FPE.DE.

---

## 1. Analyse Globale des Résultats

L'objectif de cette Passe 2 a été **pleinement atteint**. L'ajout de filtres classiques (ADX, EMA et Régime) en surcouche d'une prédiction de Machine Learning brute a permis de faire chuter de manière drastique les drawdowns et de nettoyer les faux signaux. La totalité des 3 actifs analysés valident désormais les critères minimaux de rentabilité et de risque.

---

## 2. Résultats par Actifs (Sweet Spots Validés)

### 🟢 NVO (Sur-Performance Validée)
La mission principale sur NVO était de dompter un Drawdown inacceptable (> 60%). L'utilisation combinée du filtre de régime (`use_regime_filter = True`) et de volatilité a réussi cet exploit sans tuer la rentabilité.
* **20m** (Le plus performant) :
  * Net PnL : **+ 1518.65 €** | Profit Factor : **1.39** | Max Drawdown : **-19.38%** | Trades : 1331
  * Paramètres filtres : `use_volatility_filter = True`, `use_regime_filter = True`, `regime_threshold = -0.1` (Filtres ADX/EMA désactivés).
* **30m** :
  * Net PnL : + 1074.41 € | Profit Factor : 1.31 | Max Drawdown : -20.14% | Trades : 926
  * Paramètres filtres : Identiques au 20m.

### 🟢 GMAB (Excellence du Profit Factor)
Sur GMAB, la stratégie nécessitait un filtre de forte tendance pour inverser sa sous-performance. L'ajout d'un filtre ADX et d'une EMA permet de concentrer les trades sur les "home runs".
* **30m** (Sweet Spot) :
  * Net PnL : **+ 37.42 €** | Profit Factor : **2.73** | Max Drawdown : **-0.82%** | Trades : 56
  * Paramètres filtres : `regime_threshold = -0.5`, `use_adx_filter = True` (seuil 16), `use_ema_filter = True` (période 164).
* **60m** :
  * Net PnL : + 18.47 € | Profit Factor : 1.44 | Max Drawdown : -1.82% | Trades : 57
  * Paramètres filtres : Seul le filtre de régime a été retenu (`threshold = -0.1`).

### 🟢 FPE.DE (Sécurité Absolue)
FPE.DE continue de s'illustrer par son Drawdown quasi inexistant. L'ajout du filtre ADX lui permet de repasser très légèrement en rentabilité positive avec un ratio de gain extrêmement élevé.
* **120m** :
  * Net PnL : **+ 1.50 €** | Profit Factor : **1.71** | Max Drawdown : **-0.05%** | Trades : 85
  * Paramètres filtres : `regime_threshold = -0.3`, `use_adx_filter = True` (seuil 19).
* **60m** :
  * Net PnL : + 1.19 € | Profit Factor : 1.68 | Max Drawdown : -0.03% | Trades : 101
  * Paramètres filtres : `use_ema_filter = True` (période 50).

---

## 3. Recommandations & Plan pour la Passe 3

Les filtres macroscopiques ont agi comme un excellent filet de sécurité, permettant à la stratégie **Lorentzian Classification** de se qualifier officiellement sur nos 3 actifs. 

**Plan pour la Passe 3 (Lissage & Exits)** :
L'Alpha est désormais propre et sécurisé. La Passe 3 va introduire l'estimateur de **Nadaraya-Watson** (`use_kernel_filter = True`) sur les prix, afin d'optimiser le timing exact de sortie des trades (via `use_dynamic_exits = True` ou `False`). Le Kernel agit comme un lissage final non repoussant qui pourrait théoriquement encore augmenter le Profit Factor global.

Il faudra figer l'ensemble des paramètres trouvés dans cette Passe 2 comme `base_parameters`.
