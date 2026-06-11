# Rapport : Adaptive Trend Classification - Passe 1 (Logique d'Adaptation Macro)

**Date d'analyse** : 11 Juin 2026
**Objectif de la Passe** : Configurer la sensibilité et l'inertie du filtre de tendance adaptatif. L'objectif est d'optimiser les paramètres macro : `La`, `De`, `cutout`, `Long_threshold`, `Short_threshold`.
**Paramètres bloqués** : Tous les poids de MA à `1.0` (`ema_w = 1.0`, `hma_w = 1.0`, etc.) et les longueurs à `28` (`ema_len = 28`, etc.).
**Métriques cibles** : Max Drawdown tolérable entre -25% et -30%, Profit Factor minimum attendu de 1.25, métrique de score `return_vs_buy_hold_pct_points`.

---

## 1. Analyse Globale des Résultats

L'analyse globale a permis de traiter **1 761 itérations éligibles**.
L'observation du comportement général montre que la stratégie est très exigeante et peine à trouver un edge sur la majorité des actifs, soulignant la difficulté de configurer la réactivité (La/De) sur des marchés bruités sans filtre ou pondération dynamique.

---

## 2. Résultats par Catégorie d'Actifs

### 🟢 Les Sur-Performants (Edge Identifié)
Un seul actif présente un edge clair, validé par une sur-performance absolue face au Buy & Hold.

* **NVO** : Affiche une sur-performance sur les unités de temps supérieures (45m et 60m).
  * **45m** (Score: +30.84 | 1112 trades | PnL: +743.42 | Max DD: -269.80 | Profit Factor: 1.25 | Éligibles: 200)
    * Paramètres : `La: 0.006`, `De: 0.011`, `cutout: 2`, `Long_threshold: 0.0`, `Short_threshold` (non utilisé/0)
  * **60m** (Score: +19.36 | 793 trades | PnL: +628.66 | Max DD: -258.05 | Profit Factor: 1.25 | Éligibles: 1)
    * Paramètres : `La: 0.079`, `De: 0.014`, `cutout: 2`, `Long_threshold: 0.2`

### 🔴 Les Rejetés (Absence d'Edge)
Tous les autres actifs sont rejetés en raison de performances insuffisantes ou de sous-performance marquée. Notamment :
* **NVS** : 0 itération éligible (Aucun faux positif, rejet total des métriques de robustesse financière sur ce symbole).
* **AMS.MC** : 0 itération éligible (Aucun faux positif, rejet total de l'Average Moat Score Monte Carlo simulé sur ce symbole).
* **GMAB** : Sous-performance (Scores négatifs autour de -27).
* **ZEAL.CO** : Sous-performance (Score: -45.54 en 10m).
* **LOGI, SAP, SHL.DE, FPE.DE, EVD.DE** : 0 itération éligible.

---

## 3. Recommandations

La stratégie Adaptive Trend Classification nécessite une validation rigoureuse des actifs via NVO, NVS et AMS.MC. Étant donné que NVS et AMS.MC ont échoué lors de cette Passe 1 (0 itérations éligibles), la logique d'adaptation macro ne s'avère robuste que sur **NVO**. 
Les configurations sur NVO (45m et 60m) sont retenues pour servir de base à la Passe 2 (Poids & Longueurs des Moyennes Mobiles).

**⚠️ Recommandation Post-Analyse :**
D'un point de vue méthodologique, les paramètres `robustness` (Low/Medium/High) et `signal_mode` (Close/Live) sont des paramètres fondamentaux de la logique macro qui modifient le comportement global avant l'application des poids. Il est fortement conseillé de refaire cette Passe 1 en incluant ces deux paramètres dans l'espace de recherche (la documentation *Roadmap* a été mise à jour en ce sens) afin de s'assurer qu'un réglage différent n'améliorerait pas le filtrage natif (ex: `signal_mode="Live"` pour entrer plus tôt, ou `robustness="High"` pour accroître le Profit Factor).
