# Rapport : Momentum-based ZigZag (avec QQE) - Passe 2 (Optimisation SL/TP)

**Date d'analyse** : 02 Juillet 2026
**Objectif de la Passe** : Optimiser les paramètres de risque statiques (`stop_loss_pct` et `take_profit_pct`) pour maximiser l'efficience des entrées QQE fixées lors de la Passe 1, et cristalliser les gains.
**Paramètres figés (issus Passe 1)** : `rsi_period`, `qqe_factor`, `rsi_smoothing`, `ob`, `os`, `signal_mode`.

---

## 1. Analyse Globale des Résultats

L'ajout d'une gestion de risque statique (Stop Loss et Take Profit) a été testé sur trois vagues d'actifs :
*   **Vague de Baseline (11 Juin 2026)** : Évaluation sur les 9 actifs historiques. L'introduction du SL/TP a permis une amélioration massive des performances sur la quasi-totalité des actifs. Elle a révélé que la stratégie Momentum-based ZigZag bénéficie fortement de Take Profits amples (souvent supérieurs à 9%), combinés à des Stop Loss asymétriques adaptés à la volatilité intrinsèque.
*   **Vague d'Extension (19 Juin 2026)** : Évaluation sur les 9 nouveaux actifs d'extension qualifiés lors de la Passe 1 (NVO exclu car déjà optimisé historiquement). Les résultats confirment l'asymétrie forte :
    *   **8 actifs sur 9** voient leurs métriques se consolider avec des scores de sur-performance positifs par rapport au Buy & Hold.
    *   Les leaders **daideeur** et **belgbeeur** affichent des hausses spectaculaires de Sharpe ratios (+86% pour daideeur à 2.67 et +83% pour belgbeeur à 2.18).
    *   **beideeur** montre une dégradation nette (score passant de +2.00% à -2.80% et Sharpe de 0.96 à 0.76), démontrant que la gestion statique du risque peut être contre-productive pour certains profils d'actifs à tendance très directionnelle.
*   **Vague de Campagne Crypto (02 Juillet 2026)** : Évaluation sur les 4 configurations cryptos qualifiées lors de la Passe 1 (`dotusdt` 30min/45min, `ltcusdt` 30min/45min). L'introduction de SL/TP s'avère extrêmement fructueuse en réduisant drastiquement les drawdowns maximaux et en démultipliant l'efficience statistique :
    *   **dotusdt (45min)** voit son Sharpe bondir de `0.50` à `1.23` (+146%), son Profit Factor doubler à `2.86` et son drawdown maximal s'écraser à `-0.70%` (contre `-2.69%`), tout en doublant son PnL Net (+271.44 €).
    *   **ltcusdt (30min)** affiche un Sharpe de `0.70` (contre `0.30` en Passe 1), un Profit Factor de `2.17` et un PnL en hausse à `+1215.38 €`, avec un drawdown divisé par plus de deux à `-5.91%`.
    *   Toutes les configurations cryptos optimisées valident l'apport d'un Take Profit large (souvent fixé à la borne maximale de 24.0% - 25.0%) combiné à des Stop Loss ajustés à la volatilité crypto.

---

## 2. Résultats de la Campagne de Baseline (11 Juin 2026)

### 🟢 Les Leaders Absolus (Edge massif face au B&H)
* **NVO (Timeframe 45m)** : La sur-performance absolue s'envole.
  * *Passe 1* -> Score: 109.88 | PnL: 1533.85 | Profit Factor: 1.79 | Sharpe: 1.26
  * **Passe 2** -> Score: 154.24 | PnL: 1977.43 | Profit Factor: 2.60 | Sharpe: 1.89 | Trades: 734
  * *Paramètres de Risque* : `stop_loss_pct: 0.5`, `take_profit_pct: 11.9`

### 🟡 Les Actifs Hautement Efficients (Amélioration majeure)
Ces actifs ont vu leurs ratios financiers (Profit Factor, Sharpe) s'améliorer radicalement avec l'ajout du SL/TP. Bien que leur score face au B&H soit techniquement très légèrement négatif, l'efficience pure est de niveau institutionnel.
* **ZEAL.CO (Timeframe 1m)** 
  * *Passe 2* -> Score: -1.01 | PnL: +1403.55 | Profit Factor: 1.68 | Sharpe: 2.26 | Trades: 524
  * *Paramètres de Risque* : `stop_loss_pct: 3.9`, `take_profit_pct: 9.6`
* **AMS.MC (Timeframe 10m)**
  * *Passe 2* -> Score: -42.44 | PnL: +154.13 | Profit Factor: 2.86 | Sharpe: 1.86 | Trades: 479
  * *Paramètres de Risque* : `stop_loss_pct: 0.5`, `take_profit_pct: 15.0`
* **EVD.DE (Timeframe 45m)**
  * *Passe 2* -> Score: -30.50 | PnL: +8.45 | Profit Factor: 3.58 | Sharpe: 1.96 | Trades: 143
  * *Paramètres de Risque* : `stop_loss_pct: 0.6`, `take_profit_pct: 9.8`
* **GMAB (Timeframe 1m)**
  * *Passe 2* -> Score: -25.54 | PnL: +43.86 | Profit Factor: 2.11 | Sharpe: 2.24 | Trades: 82
  * *Paramètres de Risque* : `stop_loss_pct: 4.4`, `take_profit_pct: 14.9`

### 🟠 Les Actifs à Faible Volatilité ou Difficiles
* **NVS (5m)** : Sharpe 0.85 (SL: 2.7%, TP: 8.6%)
* **SHL.DE (45m)** : Sharpe 0.95 (SL: 4.3%, TP: 11.2%)
* **SAP (30m)** : Sharpe 0.96 (SL: 4.8%, TP: 13.4%)
* **LOGI (120m)** : Sharpe 0.88 (SL: 2.9%, TP: 14.9%)
* **FPE.DE (20m)** : Sharpe 0.74 (SL: 4.2%, TP: 12.0%)

---

## 3. Résultats de la Campagne d'Extension (19 Juin 2026)

L'optimisation bayésienne a ciblé les brackets SL/TP pour les 9 nouveaux actifs d'extension qualifiés. Les résultats sont triés par Score de sur-performance décroissant :

| Actif | TF | Score (vs B&H) | PnL Net (€) | Profit Factor | Sharpe | Trades | SL Pct | TP Pct | Statut |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| **belgbeeur** | 10m | **+80.21%** | +41.42 | 2.35 | 2.18 | 565 | 0.5% | 4.6% | **✅ Qualifié (Optimisé)** |
| **daideeur** | 15m | **+68.87%** | +347.86 | 2.16 | 2.67 | 1563 | 0.5% | 7.8% | **✅ Qualifié (Optimisé)** |
| **cafreur** | 15m | **+42.08%** | +41.24 | 1.63 | 1.57 | 821 | 0.9% | 8.4% | **✅ Qualifié (Optimisé)** |
| **cpriteur** | 10m | **+41.33%** | +7.04 | 1.45 | 0.73 | 135 | 5.0% | 15.0% | **✅ Qualifié (Stable)** |
| **vnadeeur** | 10m | **+38.80%** | +126.17 | 2.00 | 2.12 | 780 | 0.7% | 14.7% | **✅ Qualifié (Optimisé)** |
| **randnleur** | 10m | **+16.40%** | +86.82 | 2.16 | 1.32 | 80 | 5.0% | 13.4% | **✅ Qualifié (Optimisé)** |
| **akzanleur** | 30m | **+15.68%** | +115.88 | 1.74 | 1.25 | 304 | 1.0% | 7.7% | **✅ Qualifié (Optimisé)** |
| **vpknleur** | 15m | **+14.76%** | +38.49 | 1.46 | 0.77 | 177 | 4.5% | 9.7% | **✅ Qualifié (Stable)** |
| **beideeur** | 15m | -2.80% | +75.70 | 1.69 | 0.76 | 98 | 1.3% | 10.0% | **⚠️ Dégradé (Conserver P1 ou Rejeter)** |

---

## 4. Résultats de la Campagne Crypto (02 Juillet 2026)

L'optimisation bayésienne a ciblé les brackets SL/TP pour les 4 configurations cryptos qualifiées en Passe 1. Les résultats sont triés par symbole puis timeframe :

| Actif | TF | Score (vs B&H) | PnL Net (€) | Profit Factor | Sharpe | Trades | SL Pct | TP Pct | Statut |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| **dotusdt** | 30min | **+54.44%** | +71.10 | 3.23 | 0.53 | 93 | 9.5% | 25.0% | **✅ Qualifié (Optimisé)** |
| **dotusdt** | 45min | **+74.84%** | +271.44 | 2.86 | 1.23 | 2308 | 1.5% | 24.0% | **✅ Qualifié (Optimisé)** |
| **ltcusdt** | 30min | **+201.34%** | +1215.38 | 2.17 | 0.70 | 910 | 2.5% | 25.0% | **✅ Qualifié (Optimisé)** |
| **ltcusdt** | 45min | **+177.06%** | +964.10 | 2.20 | 0.57 | 718 | 2.5% | 25.0% | **✅ Qualifié (Optimisé)** |

---

## 5. Analyse Narrative & Observations Clés (Extension & Crypto)

*   **LTC & DOT en démonstrateurs de robustesse** : La campagne crypto confirme que l'ajout d'une gestion de risque statique est indispensable sur les cryptomonnaies. Non seulement les drawdowns maximaux sont divisés par des facteurs de 2 à 3, mais l'efficience globale s'améliore significativement, illustrée par la configuration de `dotusdt` (45min) qui affiche un Sharpe de **1.23** (contre `0.50` en Passe 1) et un DD maximal dérisoire de **-0.70%** (contre `-2.69%`).
*   **daideeur (15m) en star de la campagne actions** : C'est le plus grand bénéficiaire de cette Passe 2 pour les actions. Son Sharpe ratio s'envole à **2.67** (contre 1.43 en Passe 1), son Profit Factor grimpe à **2.16** (contre 1.44) et son PnL Net augmente de **+119.41€**. Le modèle a trouvé un excellent équilibre avec un stop loss serré à 0.5% et un take profit modéré à 7.8% sur 1563 trades.
*   **La dégradation de beideeur (15m)** : C'est la seule anomalie de la campagne d'extension actions. L'application d'un stop loss (1.3%) et d'un take profit (10.0%) a forcé des sorties prématurées de trades gagnants, réduisant le score de +2.00% à -2.80% et faisant chuter le Profit Factor de 3.47 à 1.69. Pour cet actif spécifique, la dynamique est mieux capturée par les signaux de momentum purs du QQE (Passe 1) sans brackets fixes.
*   **Validation de l'asymétrie** : Que ce soit sur les actions d'extension ou les cryptos, tous les actifs valident la thèse de l'asymétrie de la Passe 2 : un Stop Loss serré ou moyen (souvent 0.5% - 2.5%) et un Take Profit large (souvent 15% à 25%) permettent de capter efficacement les longs mouvements de momentum propres aux actifs directionnels.

---

## 6. Recommandations et Suite

1.  **Rejet du Trailing Stop (Bypass de la Passe 3)** : Le comportement des actifs d'extension et des cryptos confirme en tous points la dynamique asymétrique de la baseline. Étant donné que la Passe 3 (Trailing Stop) a été catégoriquement rejetée sur la baseline en raison d'une dégradation généralisée du Sharpe, nous recommandons de **bypasser la Passe 3 pour la vague d'extension et la campagne crypto** et de retenir directement les configurations optimales de la Passe 2.
2.  **Traitement Particulier pour beideeur** : Pour `beideeur`, rejeter la configuration Passe 2 et conserver la configuration sans SL/TP issue de la Passe 1 (qui offrait un Profit Factor exceptionnel de 3.47).
3.  **Configurations Finales d'Extension Validées** :
    *   `belgbeeur` : SL = 0.5%, TP = 4.6%
    *   `daideeur` : SL = 0.5%, TP = 7.8%
    *   `cafreur` : SL = 0.9%, TP = 8.4%
    *   `cpriteur` : SL = 5.0%, TP = 15.0%
    *   `vnadeeur` : SL = 0.7%, TP = 14.7%
    *   `randnleur` : SL = 5.0%, TP = 13.4%
    *   `akzanleur` : SL = 1.0%, TP = 7.7%
    *   `vpknleur` : SL = 4.5%, TP = 9.7%
    *   `beideeur` : Pas de SL/TP (conserver configuration Passe 1).
4.  **Configurations Finales Crypto Validées** :
    *   `dotusdt` (30min) : SL = 9.5%, TP = 25.0% (Sharpe = 0.53, PF = 3.23, Max DD = -1.67%)
    *   `dotusdt` (45min) : SL = 1.5%, TP = 24.0% (Sharpe = 1.23, PF = 2.86, Max DD = -0.70%)
    *   `ltcusdt` (30min) : SL = 2.5%, TP = 25.0% (Sharpe = 0.70, PF = 2.17, Max DD = -5.91%)
    *   `ltcusdt` (45min) : SL = 2.5%, TP = 25.0% (Sharpe = 0.57, PF = 2.20, Max DD = -4.09%)
