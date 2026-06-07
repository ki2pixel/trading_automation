# Rapport : Smart Trader Geometric - Passe 1 (Géométrie et Quorum)

**Date d'analyse** : 07 Juin 2026
**Objectif de la Passe** : Validation de l'edge géométrique brut (Core) et de la période de lookback.
**Paramètres figés** : `signal_mode = "Close"`, `use_safety_stop = false`, `use_net_bracket_exits = false`.
**Métrique cible** : `return_vs_buy_hold_pct_points` (score) et asymétrie de rendement (`sortino_ratio`).
**Itérations éligibles totales** : 2 237.

---

## 1. Analyse Globale des Résultats

L'analyse de la Passe 1 a généré 2 237 itérations éligibles. La stratégie `smart_trader_geometric` a été évaluée pour identifier si la pure structure géométrique des prix, sans filtre de risque additionnel, permet de dégager un avantage statistique sur le marché. L'objectif était d'isoler la période d'observation optimale (`lookback_period`) et le nombre de slots (`min_long_entry_slots`), qui semble converger invariablement vers 1.

---

## 2. Résultats par Catégorie d'Actifs

### 🟢 Edge Fort (Sortino > 0.50)
Ces actifs et timeframes affichent les meilleurs ratios de Sortino, démontrant un signal d'entrée géométrique robuste et une asymétrie positive des rendements avant même toute gestion des sorties complexes.

* **ZEAL.CO** : Très performant sur les timeframes très courts.
  * **5m** : Sortino 0.8296 | Return 7.32% | `lookback_period` = 12, `min_long_entry_slots` = 1
  * **10m** : Sortino 0.5226 | Return 34.39% | `lookback_period` = 23, `min_long_entry_slots` = 1
* **LOGI** : Solide sur timeframe très court.
  * **5m** : Sortino 0.5368 | Return 4.05% | `lookback_period` = 13, `min_long_entry_slots` = 1

### 🟡 Neutres / Modérés (Sortino 0.30 à 0.49)
Ces actifs présentent un léger edge mais avec une volatilité asymétrique moins favorable. Ils peuvent être conservés pour test mais nécessiteront une gestion stricte du risque.

* **EVD.DE** : Léger edge intraday mais returns très faibles.
  * **15m** : Sortino 0.4655 | `lookback_period` = 10, `min_long_entry_slots` = 1
  * **10m** : Sortino 0.4162 | `lookback_period` = 15, `min_long_entry_slots` = 1
* **SHL.DE** : Edge modéré.
  * **30m** : Sortino 0.3822 | Return 9.90% | `lookback_period` = 14, `min_long_entry_slots` = 1

### 🔴 Rejetés (Absence d'edge - Sortino < 0.30 ou 0 itération)
Ces actifs n'ont pas démontré de viabilité avec cette logique géométrique pure ou ont produit 0 itération respectant les seuils (Drawdown < -30%, etc.).

* **SAP** : Max Sortino 0.2758 sur 60m. Rejeté.
* **AMS.MC** : Max Sortino 0.2411 sur 60m. Rejeté.
* **NVO** : Max Sortino 0.1744 sur 120m. Rejeté.
* **FPE.DE** : Max Sortino 0.1043 sur 240m. Rejeté.

---

## 3. Recommandations pour la Passe 2

Pour la **Passe 2 (Gestion du Risque et Exits)**, l'optimisation doit se concentrer prioritairement sur les actifs de la catégorie **Edge Fort (🟢)** (ZEAL.CO, LOGI).
Les paramètres core identifiés (`lookback_period` et `min_long_entry_slots` = 1) devront être figés en dur pour éviter le sur-apprentissage. 
Les variables à optimiser lors de la prochaine étape devront concerner l'activation des stops (`use_safety_stop`), la gestion des sorties asymétriques (`use_net_bracket_exits`) et les ratios de trailing si pertinents.
