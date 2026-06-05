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
* **Itérations éligibles** : 0 (pour NVO comme pour ZEAL.CO).
* L'optimiseur a convergé (early stop) après avoir sauté des centaines d'itérations, indiquant que le filtre cyclique détériore de manière critique le système.

---

## 2. Synthèse et Conclusion

L'activation du Mode Phase (`phase_mode_enabled = true`) combinée à l'exigence d'une confirmation de cycle (`require_cycling_bars`) a complètement anéanti l'Edge identifié en Passe 1 sur NVO et ZEAL.CO.
Ce comportement suggère que la force de la stratégie `cybernetic_hilbert` sur ces actifs réside exclusivement dans son suivi de tendance (Trend Mode) et que l'ajout d'une contrainte cyclique agit comme un filtre trop restrictif ou génère des faux signaux conduisant à la violation des contraintes de risque (Drawdown ou Profit Factor).

### 🔴 Résultat
**Aucun edge trouvé en Passe 2.**

### Recommandations
1. **Désactiver définitivement le Phase Mode** (`phase_mode_enabled = false`) pour NVO et ZEAL.CO.
2. Utiliser exclusivement les paramètres validés lors de la Passe 1 (Trend Mode) pour l'intégration en production live.
