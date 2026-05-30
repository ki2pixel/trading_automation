# Documentation : Moteur de Métriques & Fast Score

## TL;DR

**TL;DR** : Si votre optimiseur local n'a besoin que d'un ratio de Sharpe, ne construisez pas un dictionnaire de métriques de 50 champs. Utilisez `compute_fast_score` pour une évaluation ultra-rapide d'une seule métrique, et réservez `compute_metrics` pour les rapports finaux.

## Le Piège du Dictionnaire de Métriques Complet

Vous exécutez une optimisation Optuna sur 10 000 essais. À la fin de chaque simulation, vous devez noter le résultat. Le premier réflexe est de faire appel à votre fidèle fonction `compute_metrics`.

❌ **L'Approche "Calcul Intégral"**

```python
# Calcule plus de 50 champs incluant max_drawdown_period_bars et les excursions de trades
metrics, equity = compute_metrics(payload)
return metrics["sharpe_ratio"]
```

Le problème ? Calculer le `max_trade_runup` nécessite de déterminer les extrema de la plage à l'aide de sauts binaires (binary lifting) sur des tableaux NumPy compilés avec Numba. Calculer `max_drawdown_period_bars` implique des agrégations pandas complexes. Faire cela 10 000 fois détruit tous les gains de performance obtenus en compilant le noyau de backtest avec Numba.

✅ **L'Approche "Extraction Ciblée"**

```python
# Calcule UNIQUEMENT la courbe d'équité et le ratio de Sharpe de manière mathématique
return compute_fast_score(trades_df, "sharpe_ratio", state=state_df)
```

## L'Architecture du Fast Score

La fonction `compute_fast_score` implémente des chemins rapides (fast-paths) ciblés pour les métriques réellement utilisées par l'optimiseur bayésien et les grilles d'optimisation locales :

- **Métriques basées sur les trades** (`total_net_pnl`, `win_rate_pct`, `profit_factor`) : Calculées en utilisant de simples sommes vectorisées Pandas/NumPy directement sur le DataFrame `trades`.
- **Métriques ajustées au risque** (`sharpe_ratio`, `sortino_ratio`) : Reconstruit une courbe d'équité minimale à partir du DataFrame `state` (en utilisant uniquement le PnL réalisé et ouvert), calcule les variations en pourcentage, et renvoie le ratio annualisé.
- **Performance relative** (`return_vs_buy_hold_pct_points`) : Calcule uniquement les prix de départ/fin et l'équité finale.

### Tableau des Compromis : Granularité vs Débit

| Approche | Latence par Essai | Granularité en Sortie | Surcharge Mémoire |
| -------- | ----------------- | --------------------- | ----------------- |
| `compute_metrics` | ~15-20ms | > 50 champs (Excursions) | Élevée (DataFrames) |
| `compute_fast_score` | < 1ms | 1 métrique spécifique | ✅ Faible |

## La Règle d'Or : Ne Calculez Pas Ce Que Vous Ne Lisez Pas

**La Règle d'Or : Le calcul des métriques doit s'adapter à son public.** 

Lorsque le public est un humain lisant un rapport HTML, exécutez `compute_metrics` pour fournir des informations approfondies (runup, excursions, ratios gains/pertes). Lorsque le public est un algorithme d'optimisation qui n'évalue qu'un simple flottant (par ex., Ratio de Sharpe) pour guider sa descente de gradient, utilisez `compute_fast_score`.
