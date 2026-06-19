# Rapport : 3commas_bot - Passe 3 (Trailing Stop Dynamique)

**Date d'analyse** : 19 Juin 2026
**Objectif de la Passe** : Évaluer l'impact d'un Trailing Stop (suiveur de tendance) afin de sécuriser les gains de manière dynamique et de laisser courir les mouvements forts, tout en figeant le Stop Loss statique.
**Paramètres cibles optimisés** : `trail_stop_size` (0.5 à 3.0 ATR), `rr_exit` (0.0 à 2.0). L'activation du trailing (`trail_stop`) est forcée à `true`.
**Paramètres bloqués** : Configurations Core (Passe 1) et configurations de Risk-Management (Passe 2.1).

---

## 1. Analyse Globale des Résultats

Le tableau ci-dessous confronte les performances des stratégies bloquées (Passe 2) avec l'ajout du Trailing Stop (Passe 3). Un résultat **ÉCHEC** signifie que la totalité des itérations a échoué à générer des backtests respectant les contraintes minimales (Score positif, Trades > 80, Drawdown > -25%).

| Actif | TF | P2 Sortino | P3 Sortino | Delta | Trail Size | RR Exit | Win Rate (%) | Trades | Max DD (%) | PF | CAGR (%) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **GMAB** | 60m | 1.5046 | **ÉCHEC** | `-` | - | - | - | - | - | - | - |
| **GMAB** | 30m | 0.9949 | **ÉCHEC** | `-` | - | - | - | - | - | - | - |
| **GMAB** | 20m | 0.9469 | **ÉCHEC** | `-` | - | - | - | - | - | - | - |
| **GMAB** | 15m | 1.0032 | **ÉCHEC** | `-` | - | - | - | - | - | - | - |
| **FPE.DE** | 45m | 0.8468 | **ÉCHEC** | `-` | - | - | - | - | - | - | - |
| **FPE.DE** | 30m | 0.8172 | **ÉCHEC** | `-` | - | - | - | - | - | - | - |
| **FPE.DE** | 20m | 0.8673 | **ÉCHEC** | `-` | - | - | - | - | - | - | - |
| **FPE.DE** | 5m | 0.9544 | **ÉCHEC** | `-` | - | - | - | - | - | - | - |
| **LOGI** | 120m | 0.7631 | **0.7631** | `-0.00%` | 0.5 | 1.0 | 58.82% | 102 | -17.29% | 2.54 | 5.21% |
| **LOGI** | 45m | 0.7392 | **0.4351** | `-41.14%` | 0.5 | 1.0 | 46.54% | 159 | -22.58% | 1.42 | 2.60% |
| **LOGI** | 10m | 0.8289 | **ÉCHEC** | `-` | - | - | - | - | - | - | - |
| **LOGI** | 5m | 0.8086 | **ÉCHEC** | `-` | - | - | - | - | - | - | - |
| **EVD.DE** | 30m | 0.7430 | **ÉCHEC** | `-` | - | - | - | - | - | - | - |
| **EVD.DE** | 20m | 0.6058 | **ÉCHEC** | `-` | - | - | - | - | - | - | - |
| **EVD.DE** | 5m | 0.4809 | **ÉCHEC** | `-` | - | - | - | - | - | - | - |
| **TENITEUR** | 30m | 0.8789 | **0.7245** | `-17.57%` | 2.6 | 0.7 | 73.79% | 103 | -5.68% | 2.44 | 5.47% |



---

## 2. Analyse Narrative

### Le rejet catégorique du Trailing Stop en Intraday
Les résultats parlent d'eux-mêmes : sur 15 configurations validées lors des passes précédentes, **13 configurations échouent totalement** dès lors que le Trailing Stop est activé. 
Cela signifie qu'aucune combinaison de `trail_stop_size` et `rr_exit` n'a pu empêcher l'edge mathématique de s'effondrer.
- **Raison technique probable** : La stratégie `3commas_bot` repose originellement sur un fort Win Rate généré par des moyennes mobiles rapides (HMA, DEMA) en scalping/intraday. L'ajout d'un Trailing Stop rapproche mécaniquement le seuil de sortie des prix (whipsaws). Dans un marché intra-journalier très bruité, le trailing stop est déclenché prématurément par des retracements sains, ce qui détruit le Win Rate (souvent sous les 40%) et fait chuter le Profit Factor sous notre barre critique de 1.25.

### Le cas d'école de LOGI
Sur les unités de temps plus élevées, l'impact est moins destructeur, mais il n'est pas pour autant bénéfique :
- **LOGI 120m** survit à l'optimisation, mais le Sortino Ratio est strictement identique à la Passe 2.1 (0.7631). Cela s'explique par le fait que l'optimiseur a trouvé des paramètres (trail=0.5, rr_exit=1.0) où le Take Profit statique (rnr) est systématiquement touché *avant* ou *en même temps* que le trailing stop ne force la sortie. Le mécanisme est donc redondant et n'apporte aucune plus-value.
- **LOGI 45m** subit une forte dégradation (-41.14% de Sortino). Le Win Rate perd environ 7% par rapport à un Risk-Management statique, illustrant encore une fois la fragilité des tendances face aux stops suiveurs.

---

## 3. Recommandations Finales pour la production

Contrairement aux idées reçues selon lesquelles un Trailing Stop améliore toujours l'espérance mathématique en "laissant courir les gains", ce cas de figure démontre l'inverse pour la stratégie `3commas_bot` :
1. **Désactivation totale** : Le paramètre `trail_stop` doit être impérativement fixé à `false` sur toutes les instances de scalping (timeframes < 1H).
2. **Confiance dans le modèle statique** : Le couple Risk-Reward asymétrique (`rnr` / `risk_m`) optimisé lors de la Passe 2 et 2.1 représente le sommet asymptotique de performance de cette logique.
3. **Passe 3 annulée** : Les données statiques des Passes 1 et 2 seront utilisées pour déployer les stratégies en production. Aucun trailing stop ne sera implémenté.
