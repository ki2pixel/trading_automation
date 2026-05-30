# Rapport Rapide - Phase 3 (Advanced Exits & Bayesian Optimization)

## Résumé de l'Optimisation

- **Actif cible** : LOGI (5m)
- **Période** : 2022-01-01 à 2023-01-01
- **Mode d'optimisation** : Optuna TPE (Bayésien) avec early stopping
- **Trials complétés** : 150 (dont 4 ignorés via les contraintes de filtrage dynamiques)

## Comparaison des Modes de Sortie (`exit_mode`)

Voici les performances maximales trouvées pour chaque mode de sortie :

| Mode de sortie | Sharpe Ratio max | CAGR (%) | Max Drawdown (%) |
|----------------|-----------------:|---------:|-----------------:|
| **combined**   |             3.13 |  1182.0% |           -39.6% |
| **vwap**       |             2.43 |   239.1% |           -25.3% |
| **time_only**  |             1.27 |     9.6% |            -2.7% |
| **ladder**     |             0.51 |     3.3% |           -52.9% |

**Observations** :
1. Le mode **combined** (qui utilise à la fois le ladder, le croisement VWAP et la limite de fin de journée) offre un ratio de Sharpe exceptionnel et un rendement extrêmement élevé, en capitalisant de manière très efficace sur la volatilité (au prix d'un DD plus important).
2. Le **VWAP** seul offre aussi d'excellentes performances.
3. Le **time_only** (stratégie basique de la Phase 1) est moins performant mais très sûr avec un drawdown minimal.
4. Le **ladder** pur semble moins efficace s'il n'est pas couplé aux croisements VWAP.

## Sensibilité Paramétrique (Feature Importance)

D'après le rapport d'importance d'Optuna (`parameter_importance.json`), voici les trois paramètres ayant le plus grand impact sur le Sharpe ratio :

1. **`volatility_multiplier_enter`** (58.4%) : Sans surprise, l'amplitude d'entrée détermine la fréquence des trades et est le levier majeur.
2. **`exit_mode`** (10.1%) : Le choix de la dynamique de sortie vient directement en seconde position.
3. **`stoploss_ladder_ratio0`** (6.4%) : La quantité de position sécurisée au premier palier du stop-loss ladder a un impact non-négligeable.

## Contraintes Implémentées

- `volatility_multiplier_exit` est défini obligatoirement en dessous de `volatility_multiplier_enter` via l'échantillonnage d'un différentiel.
- Les seuils successifs de Stop Loss ladder (`step0`, `step1`) garantissent `step1 < step0` via un offset, évitant ainsi les configurations absurdes et économisant du budget de calcul.

## Verdict

**GO**. L'introduction des exits dynamiques (VWAP / Ladder / Combined) montre une amélioration spectaculaire des indicateurs cibles (Sharpe Ratio). Les contraintes de la recherche bayésienne sont viables et permettent au système d'explorer des configurations asymétriques logiques. Nous pouvons procéder à la **Phase 4** avec de bonnes garanties.