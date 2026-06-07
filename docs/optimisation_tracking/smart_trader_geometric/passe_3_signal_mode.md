# Rapport : Smart Trader Geometric - Passe 3 (Signal Mode)

**Date d'analyse** : 07 Juin 2026
**Objectif de la Passe** : Évaluer l'impact du mode de génération de signal (`signal_mode = "Live"` vs `"Close"`) sur les performances de la stratégie, en conservant les paramètres optimaux figés lors des Passes 1 et 2.
**Paramètres bloqués** : Configuration Core (Passe 1) et Risk Management asymétrique (Passe 2).

---

## 1. Comparaison des Résultats (Close vs Live)

Le tableau suivant compare les ratios de Sortino et les rendements nets obtenus avec le `signal_mode` défini sur "Close" (Passe 2) puis sur "Live" (Passe 3).

| Actif | TF | Sortino (Close) | Sortino (Live) | Delta | Ret (Close) | Ret (Live) | Delta |
|---|---|---|---|---|---|---|---|
| **ZEAL.CO** | 5m | 1.0179 | 1.0179 | `0.00%` | 8.57% | 8.57% | `0.00%` |
| **ZEAL.CO** | 10m | 0.7821 | 0.7821 | `0.00%` | 45.33% | 45.33% | `0.00%` |
| **LOGI** | 5m | 0.6387 | 0.6387 | `0.00%` | 4.44% | 4.44% | `0.00%` |

---

## 2. Analyse Narrative

* **Stabilité Absolue des Performances** : Les résultats sont mathématiquement identiques entre les deux modes d'évaluation du signal. Le passage en évaluation intra-barre continuelle (`Live`) n'a modifié ni le nombre d'entrées, ni le Win Rate, ni le ratio de Sortino.
* **Explication Technique** : Ce comportement s'explique par la nature de la configuration d'exécution. La stratégie est configurée avec l'option `execute_on_next_bar = true`. Par conséquent, que le signal soit validé au dernier tick d'une bougie clôturée (`Close`) ou recalculé à chaque tick de la bougie en formation (`Live`), l'ordre de marché n'est déclenché et envoyé qu'à l'ouverture de la bougie suivante. De plus, la gestion du risque en cours de trade est entièrement déléguée aux Bracket Exits asymétriques (TP/SL) de la Passe 2, qui opèrent de manière indépendante et intra-barre quel que soit le `signal_mode`.

---

## 3. Conclusion et Recommandation de Production

L'utilisation de `signal_mode = "Live"` n'apporte aucune valeur ajoutée financière à la stratégie Smart Trader Geometric dans sa configuration actuelle. 

**Recommandation Finale** :
La configuration de production doit impérativement conserver **`signal_mode = "Close"`**. Cette décision permet de réduire drastiquement la charge CPU et I/O en production live (évaluation de la logique métier une seule fois par clôture de bougie au lieu de recalculer à chaque tick) sans dégrader ni modifier l'edge de la stratégie. 

**Les paramètres des setups à fort Edge (ZEAL.CO et LOGI) sont désormais définitivement validés et clôturés pour la production.**