# Rapport : Cybernetic Hilbert - Passe 3 (Time Stop)

**Date d'analyse** : 05 Juin 2026
**Objectif de la Passe** : Activer le filtre temporel (Time Stop) pour couper les positions stagnantes et vérifier si cela améliore l'edge identifié lors de la Passe 1 (Trend Mode) sur les actifs NVO et ZEAL.CO.
**Configurations bloquées** : `phase_mode_enabled = false`, `use_safety_stop = true` et les paramètres optimaux de la Passe 1 figés pour chaque actif.
**Paramètres optimisés** : `safety_max_bars_in_trade`.
**Métriques cibles** : `return_vs_buy_hold_pct_points` avec les mêmes contraintes de drawdown et de profit factor.

---

## 1. Analyse Globale des Résultats

L'analyse des rapports de l'optimiseur local pour la Passe 3 montre que l'optimiseur a convergé en trouvant des configurations éligibles, mais sans aucune amélioration par rapport à la Passe 1.

* **NVO** : Le meilleur score reste à `+149.4814` avec la recommandation `safety_max_bars_in_trade: 0`. Les métriques (Sharpe 1.734, PF 1.356) sont strictement identiques à la Passe 1.
* **ZEAL.CO** : Le meilleur score reste à `+52.4314` avec la recommandation `safety_max_bars_in_trade: 0`. Les métriques (Sharpe 3.366, PF 1.949) sont strictement identiques à la Passe 1.
* **LXSDEEUR** : Le meilleur score reste à `+81.7414` avec la recommandation `safety_max_bars_in_trade: 0`. Les métriques (Sharpe 1.432, PF 1.291) sont strictement identiques à la Passe 1.
* **MRKDEEUR** : Le meilleur score reste à `+33.9415` avec la recommandation `safety_max_bars_in_trade: 0`. Les métriques (Sharpe 1.688, PF 1.296) sont strictement identiques à la Passe 1.

---

## 2. Synthèse et Conclusion

L'optimiseur a systématiquement rejeté la coupure anticipée des trades au profit d'une valeur de `0` pour `safety_max_bars_in_trade` (désactivation effective du Time Stop). 
Cela signifie que couper les positions qui durent dans le temps ne permet pas d'améliorer le ratio gain/risque (Sharpe Ratio) ni la rentabilité globale. La stratégie est plus performante lorsqu'elle laisse les tendances se développer jusqu'à ce que le signal s'inverse de lui-même ou qu'un TP/SL (Bracket Exits) soit touché.

### 🔴 Résultat
**Aucune amélioration identifiée en Passe 3.** L'ajout d'un Time Stop n'apporte aucun bénéfice statistique.

### Recommandations
1. **Désactiver le Time Stop** (`safety_max_bars_in_trade = 0` ou `use_safety_stop = false`) pour NVO et ZEAL.CO.
2. S'en tenir exclusivement aux paramètres validés lors de la Passe 1 (Trend Mode + Bracket Exits purs) pour l'intégration en production live (pour les actions).

---

## 3. Résultats Campagne Crypto (Nouveaux Actifs)

Contrairement à l'univers des actions, l'optimisation de la Passe 3 (Time Stop) a montré un bénéfice ou une stabilisation intéressante pour certaines configurations cryptos, en particulier pour limiter la durée d'exposition sur les timeframes intermédiaires et courts.

### 🟢 Les Qualifiés Finalisés (Passe 3)
Les 7 configurations ont validé la Passe 3. Elles sont divisées selon leur mode optimal (Phase ou Trend) validé lors des passes précédentes :

#### Groupe Phase (Mode Oscillation)
* **APTUSDT (10min)** : Score `+92.2019` (`safety_max_bars_in_trade: 0` - Time Stop inactif). PF: 2.450, Sharpe: 0.460, Max DD: -0.17%.
* **DOTUSDT (10min)** : Score `+48.0587` (`safety_max_bars_in_trade: 5`). PF: 2.019, Sharpe: 0.245, Max DD: -0.86%.
* **DOTUSDT (45min)** : Score `+48.3492` (`safety_max_bars_in_trade: 0` - Time Stop inactif). PF: 2.232, Sharpe: 0.105, Max DD: -0.60%.
* **LTCUSDT (30min)** : Score `+87.8043` (`safety_max_bars_in_trade: 0` - Time Stop inactif). PF: 2.772, Sharpe: 0.221, Max DD: -2.71%.

#### Groupe Trend (Mode Tendance)
* **ETHUSDT (45min)** : Score `+6960.3557` (`safety_max_bars_in_trade: 5`). PF: 1.527, Sharpe: 2.036, Max DD: -10.06%.
* **DOTUSDT (1h)** : Score `+99.0538` (`safety_max_bars_in_trade: 50`). PF: 1.655, Sharpe: 2.240, Max DD: -1.26%.
* **LTCUSDT (45min)** : Score `+674.0878` (`safety_max_bars_in_trade: 20`). PF: 1.563, Sharpe: 1.541, Max DD: -8.70%.

### Synthèse et Recommandations Crypto

Les 7 configurations cryptos ci-dessus sont désormais pleinement qualifiées et stabilisées à l'issue de cette Passe 3.
1. **APT 10m, DOT 45m, LTC 30m** : Utiliser la configuration issue de la **Passe 2** (Phase Mode, Cycling Bars 1, Time Stop désactivé).
2. **DOT 10m** : Utiliser la configuration issue de la **Passe 3** (Phase Mode, Cycling Bars 1, Time Stop actif à 5 bougies).
3. **ETH 45m, DOT 1h, LTC 45m** : Utiliser la configuration issue de la **Passe 3** (Trend Mode, Time Stop actif avec leurs durées maximales respectives).
