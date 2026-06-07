# Rapport : Smart Trader Geometric - Passe 2 (Risk-Management)

**Date d'analyse** : 07 Juin 2026
**Objectif de la Passe** : Maximiser l'edge identifié en Passe 1 en trouvant les paramètres optimaux pour les sorties asymétriques (Take Profit / Stop Loss) via `use_net_bracket_exits` ou `use_safety_stop`.
**Paramètres bloqués** : La configuration Core géométrique (`lookback_period` et `min_long_entry_slots = 1`) validée lors de la Passe 1.

---

## 1. Résultats de l'Optimisation des Exits

Le tableau suivant présente les résultats de la Passe 2 et met en évidence l'évolution (Delta) du ratio de Sortino par rapport au signal brut géométrique de la Passe 1. Les optimisations ont clairement favorisé l'utilisation des Net Bracket Exits (`use_net_bracket_exits = true`) au détriment des Safety Stops dynamiques (`use_safety_stop = false`).

| Actif | TF | Core (LB) | Sortino P1 | **Sortino P2** | Delta | TP Net % | SL Net % | Win Rate | Trades | Max DD |
|---|---|---|---|---|---|---|---|---|---|---|
| **ZEAL.CO** | 5m | 12 | 0.8296 | **1.0179** | `+22.70%` | 12.0% | 1.0% | 43.72% | 2141 | -0.82% |
| **ZEAL.CO** | 10m | 23 | 0.5226 | **0.7821** | `+49.65%` | 12.0% | 1.0% | 42.44% | 820 | -3.76% |
| **LOGI** | 5m | 13 | 0.5368 | **0.6387** | `+18.98%` | 8.0% | 1.0% | 43.98% | 2774 | -0.74% |

---

## 2. Analyse Narrative

* **Uniformité des Stops et Asymétrie** : L'algorithme d'optimisation a convergé sur des ratios risque/rendement hautement asymétriques et extrêmement similaires entre les actifs. Le Stop Loss Net optimal s'établit universellement à **1.0%**, coupant les pertes très rapidement. Les Take Profit Nets sont beaucoup plus larges, se situant entre **8.0% et 12.0%**.
* **Impact sur la Volatilité** : Ces Bracket Exits ont un impact drastique sur la maîtrise du Drawdown. Sur ZEAL.CO 5m, le Max Drawdown est réduit à un très modeste -0.82%, tandis que le Sortino dépasse la barre symbolique de 1.00 (1.0179).
* **Maintien du Win Rate** : Bien que les Take Profits soient placés très loin (8 à 12 fois le risque initial), le Win Rate se maintient autour de 43%. L'edge brut du signal géométrique (Passe 1) fournit des entrées d'une précision suffisante pour permettre à ce risk management asymétrique de prospérer de manière profitable.

---

## 3. Conclusion et Recommandations (Passe 3)

L'utilisation de Bracket Exits asymétriques (TP 8-12% / SL 1%) a systématiquement amélioré la performance de la stratégie Smart Trader Geometric par rapport aux signaux bruts. Les variables `use_net_bracket_exits`, `take_profit_net_percent` et `stop_loss_net_percent` doivent être intégrées dans la synthèse stratégique en tant que configuration de production validée.

**Recommandations pour la Passe 3** :
La prochaine passe pourra, si nécessaire, explorer l'activation d'un Trailing Stop. Si l'edge est jugé satisfaisant et complet en l'état, cette configuration peut directement basculer en production live.