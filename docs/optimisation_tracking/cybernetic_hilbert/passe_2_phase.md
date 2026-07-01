# Rapport : Cybernetic Hilbert - Passe 2 (Mode Phase / Oscillation)

**Date d'analyse** : 05 Juin 2026
**Objectif de la Passe** : Activer le filtre cyclique (Phase Mode) pour vérifier s'il améliore l'edge identifié lors de la Passe 1 (Trend Mode) sur les actifs NVO et ZEAL.CO.
**Configurations bloquées** : `phase_mode_enabled = true`, et les paramètres optimaux de la Passe 1 figés pour chaque actif (`hilbert_smooth_period`, `take_profit_net_percent`, `stop_loss_net_percent`).
**Paramètres optimisés** : `require_cycling_bars`.
**Métriques cibles** : `return_vs_buy_hold_pct_points` avec les mêmes contraintes de drawdown et de profit factor.

---

## 1. Analyse Globale des Résultats

L'analyse des rapports de l'optimiseur local pour la Passe 2 indique un **rejet total** sur tous les actifs testés.
* **Total itérations** : 1000 par actif.
* **Itérations éligibles** : 0 (pour NVO, ZEAL.CO, ainsi que pour les nouveaux actifs qualifiés LXSDEEUR et MRKDEEUR).
* L'optimiseur a convergé (early stop) après avoir sauté des centaines d'itérations, indiquant que le filtre cyclique détériore de manière critique le système.

---

## 2. Synthèse et Conclusion

L'activation du Mode Phase (`phase_mode_enabled = true`) combinée à l'exigence d'une confirmation de cycle (`require_cycling_bars`) a complètement anéanti l'Edge identifié en Passe 1 sur tous les actifs (NVO, ZEAL.CO, LXSDEEUR, MRKDEEUR).
Ce comportement suggère que la force de la stratégie `cybernetic_hilbert` réside exclusivement dans son suivi de tendance (Trend Mode) et que l'ajout d'une contrainte cyclique agit comme un filtre trop restrictif ou génère des faux signaux conduisant à la violation des contraintes de risque (Drawdown ou Profit Factor).

### 🔴 Résultat
**Aucun edge trouvé en Passe 2.**

### Recommandations
1. **Désactiver définitivement le Phase Mode** (`phase_mode_enabled = false`) pour NVO et ZEAL.CO.
2. Utiliser exclusivement les paramètres validés lors de la Passe 1 (Trend Mode) pour l'intégration en production live (pour les actions).

---

## 3. Résultats Campagne Crypto (Nouveaux Actifs)

Contrairement à l'univers des actions, l'activation du Mode Phase (`phase_mode_enabled = true`) a généré des résultats très positifs pour plusieurs actifs cryptos, en réduisant drastiquement le Drawdown tout en maintenant une sur-performance nette.

### 🟢 Les Sur-Performants (Qualifiés)
4 configurations cryptos ont validé la Passe 2 avec succès (`require_cycling_bars = 1` pour toutes) :

* **APTUSDT (10min)** : Score `+92.2019` (`hilbert_smooth_period: 12`, `take_profit_net_percent: 18.0`, `stop_loss_net_percent: 1.0`, `require_cycling_bars: 1`). 175 trades, PF: 2.450, Sharpe: 0.460, Max DD: -0.17%.
* **DOTUSDT (10min)** : Score `+48.0587` (`hilbert_smooth_period: 10`, `take_profit_net_percent: 20.0`, `stop_loss_net_percent: 1.0`, `require_cycling_bars: 1`). 246 trades, PF: 2.019, Sharpe: 0.245, Max DD: -0.86%.
* **DOTUSDT (45min)** : Score `+48.3492` (`hilbert_smooth_period: 8`, `take_profit_net_percent: 19.0`, `stop_loss_net_percent: 1.0`, `require_cycling_bars: 1`). 79 trades, PF: 2.232, Sharpe: 0.105, Max DD: -0.60%.
* **LTCUSDT (30min)** : Score `+87.8043` (`hilbert_smooth_period: 9`, `take_profit_net_percent: 20.0`, `stop_loss_net_percent: 1.0`, `require_cycling_bars: 1`). 99 trades, PF: 2.772, Sharpe: 0.221, Max DD: -2.71%.

### 🔴 Les Rejetés (Nouveaux Actifs Crypto)
Ces configurations n'ont pas produit de combinaison valide ou ont sous-performé le Buy & Hold en mode oscillation :
* **DOTUSDT (1h)** : Aucune combinaison valide respectant les filtres de risque.
* **LTCUSDT (45min)** : Aucune combinaison valide respectant les filtres de risque.
* **ETHUSDT (45min)** : Rejeté en raison d'un score négatif vs B&H (`-330.7373`), malgré un excellent PF de 4.353 sur 91 trades (Max DD: -21.60%).

### Recommandations pour la Passe 3
1. **Groupe Phase (Qualifiés P2)** : Pour `APTUSDT` (10m), `DOTUSDT` (10m, 45m) et `LTCUSDT` (30m), continuer vers la Passe 3 en bloquant `phase_mode_enabled = true` et `require_cycling_bars = 1`, puis optimiser le `safety_stop`.
2. **Groupe Trend (Échoués P2 mais Qualifiés P1)** : Pour `ETHUSDT` (45m), `DOTUSDT` (1h) et `LTCUSDT` (45m), continuer vers la Passe 3 en bloquant `phase_mode_enabled = false` (retour au mode tendance) et optimiser le `safety_stop`.
