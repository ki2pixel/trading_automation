# Rapport : Adaptive Trend Classification - Passe 2 (Poids & Longueurs des Moyennes Mobiles)

**Date d'analyse** : 11 Juin 2026
**Objectif de la Passe** : Ajuster la composition du panier de filtres pour donner la priorité aux moyennes mobiles les plus pertinentes pour le sous-jacent.
**Paramètres optimisés** : Poids (`ema_w`, `hma_w`, `wma_w`, `dema_w`, `lsma_w`, `kama_w`) et longueurs (`ema_len`, `hull_len`, `wma_len`, `dema_len`, `lsma_len`, `kama_len`).
**Paramètres bloqués** : La logique macro de la Passe 1 (`La`, `De`, `cutout`, `Long_threshold`, `Short_threshold`).
**Actifs ciblés** : NVO (45m et 60m) - seuls timeframes validés lors de la Passe 1.

---

## 1. Analyse Globale des Résultats

L'optimisation des pondérations et longueurs des composantes de la tendance a permis une amélioration drastique des métriques par rapport à la Passe 1. 
En sélectionnant les MAs les plus adaptées au comportement spécifique de NVO sur ces unités de temps, le score global a pratiquement doublé, avec un meilleur Profit Factor et une réduction significative du Drawdown.

---

## 2. Résultats Détaillés

### 🟢 NVO (Amélioration confirmée)

* **45m** (Score: +56.37 | Amélioration vs Passe 1 : **+25.53 pts**)
  * **Métriques** : 1165 trades | PnL: +998.79 | Max DD: -227.73 | Profit Factor: 1.35
  * **Configuration MAs** :
    * Faible influence : `ema_w=0.1`, `kama_w=0.0`
    * Forte influence : `dema_w=1.0`, `wma_w=0.8`, `lsma_w=0.8`, `hma_w=0.7`
    * Longueurs clés : `ema_len=87`, `hull_len=99`, `dema_len=44`, `lsma_len=33`, `kama_len=29`, `wma_len=20`
  * *Note* : La DEMA et les moyennes pondérées rapides dominent le signal. Le KAMA est totalement écarté par l'optimiseur.

* **60m** (Score: +37.92 | Amélioration vs Passe 1 : **+18.56 pts**)
  * **Métriques** : 746 trades | PnL: +814.25 | Max DD: -222.75 | Profit Factor: 1.32
  * **Configuration MAs** :
    * Faible influence : `hma_w=0.2`, `wma_w=0.3`, `dema_w=0.3`
    * Forte influence : `ema_w=1.5`, `kama_w=1.4`, `lsma_w=1.1`
    * Longueurs clés : `ema_len=59`, `hull_len=44`, `dema_len=35`, `kama_len=31`, `lsma_len=27`, `wma_len=14`
  * *Note* : À l'inverse du 45m, le 60m donne beaucoup de poids à l'EMA classique et au KAMA, avec un lissage plus fort.

---

## 3. Recommandations

La Passe 2 valide l'approche modulaire de la stratégie Adaptive Trend Classification. L'ajustement du panier de Moyennes Mobiles a permis de doubler l'edge identifié lors de la Passe 1, prouvant l'intérêt de la pondération dynamique.
La stratégie étant de Catégorie B (2 passes), l'optimisation est considérée comme terminée. Les configurations trouvées sur NVO 45m et 60m peuvent être intégrées en production.
