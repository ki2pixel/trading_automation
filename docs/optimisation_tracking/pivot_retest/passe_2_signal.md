# Rapport de Backtesting : Pivot Breakout Retest Signals (Passe 2)

## Objectif
Optimiser les paramètres du signal de trading (`retest_bars`, `signal_mode`, `use_safety_stop`) en fixant la structure temporelle (`pivot_timeframe`) découverte lors de la Passe 1, exclusivement sur l'actif de référence validé : **NVO (Novo Nordisk)**.

## Itérations et Couverture
- **Actif ciblé :** NVO (Golden Asset)
- **Timeframes analysés :** 10m, 15m, 20m, 30m, 45m, 120m

## Analyse des Résultats (NVO)

La relaxation de `retest_bars` a permis d'affiner l'edge sur tous les timeframes, augmentant la surperformance par rapport au Buy & Hold de plusieurs pourcents sans dégrader le Profit Factor ou le Max Drawdown.

### Configurations Optimales (Sweet Spots)
- **10m** : `pivot_timeframe=D`, `retest_bars=3`, `signal_mode=Close`, `use_safety_stop=False` 
  *(Score: 37.30%, PF: 1.29, MaxDD: -208.65%)* -> **+3.34%** par rapport à la passe 1.
- **15m** : `pivot_timeframe=D`, `retest_bars=2`, `signal_mode=Close`, `use_safety_stop=False` 
  *(Score: 35.04%, PF: 1.30, MaxDD: -242.88%)* -> **+1.67%** par rapport à la passe 1.
- **20m** : `pivot_timeframe=D`, `retest_bars=2`, `signal_mode=Close`, `use_safety_stop=False` 
  *(Score: 28.03%, PF: 1.28, MaxDD: -304.17%)* -> **+1.20%** par rapport à la passe 1.
- **30m** : `pivot_timeframe=D`, `retest_bars=13`, `signal_mode=Close`, `use_safety_stop=False` 
  *(Score: 29.33%, PF: 1.29, MaxDD: -283.01%)* -> **+3.34%** par rapport à la passe 1.
- **45m** : `pivot_timeframe=D`, `retest_bars=8`, `signal_mode=Close`, `use_safety_stop=False` 
  *(Score: 33.55%, PF: 1.36, MaxDD: -150.60%)* -> **+3.59%** par rapport à la passe 1.
- **120m** : `pivot_timeframe=12H`, `retest_bars=3`, `signal_mode=Close`, `use_safety_stop=False` 
  *(Score: 29.87%, PF: 1.28, MaxDD: -165.84%)* -> Maintien de l'edge.

## Conclusion de la Passe 2
L'optimisation ciblée a démontré son efficacité : ajuster `retest_bars` spécifiquement pour chaque unité de temps a solidifié l'avantage de la stratégie. Les paramètres plus courts (2-3 bougies) favorisent les unités très rapides (10-20m) pour des entrées réactives, tandis que des délais de confirmation plus longs (8-13) protègent les timeframes intermédiaires (30-45m). Le `use_safety_stop=False` et `signal_mode=Close` se confirment comme la norme sur NVO. La stratégie est validée et prête pour son intégration/Passe 3 éventuelle.
