# Synthèse Stratégique : Pivot Breakout Retest Signals

## Statut Actuel & Prochaine Étape
- **Statut** : Passe 2 (Paramètres du Signal) terminée sur l'actif de référence (NVO).
- **Prochaine étape** : Intégration en live de la stratégie validée (ou Passe 3 de gestion des sorties si nécessaire).

## État de la Recherche
L'analyse de la stratégie **Pivot Breakout Retest Signals** a d'abord évalué 6800 itérations (Passe 1) pour identifier l'horizon idéal du pivot, isolant clairement NVO comme "Golden Asset". EVD.DE et GMAB ont été conservés en Mention Spéciale.

La Passe 2 s'est focalisée exclusivement sur NVO afin d'optimiser la mécanique du signal (`retest_bars`). Cette approche a permis de booster le score initial jusqu'à +3.59% sans détériorer le Max Drawdown, générant des configurations asymétriques selon le timeframe (retest court en 10-20m, retest plus long en 30-45m).

## Configurations Validées (Sweet Spots à figer pour la Passe 2)

### NVO (Novo Nordisk) - Final Passe 2
- **10m** : `pivot_timeframe=D`, `retest_bars=3`, `signal_mode=Close`
- **15m** : `pivot_timeframe=D`, `retest_bars=2`, `signal_mode=Close`
- **20m** : `pivot_timeframe=D`, `retest_bars=2`, `signal_mode=Close`
- **30m** : `pivot_timeframe=D`, `retest_bars=13`, `signal_mode=Close`
- **45m** : `pivot_timeframe=D`, `retest_bars=8`, `signal_mode=Close`
- **120m** : `pivot_timeframe=12H`, `retest_bars=3`, `signal_mode=Close`
- *Note* : Edge optimisé de plusieurs pourcents. Configurations prêtes à l'emploi.

### EVD.DE (CTS Eventim)
- **10m** : `pivot_timeframe=W`, `retest_bars=5`, `signal_mode=Close`
- **15m** : `pivot_timeframe=W`, `retest_bars=5`, `signal_mode=Close`
- **30m** : `pivot_timeframe=W`, `retest_bars=5`, `signal_mode=Close`
- **240m** : `pivot_timeframe=D`, `retest_bars=5`, `signal_mode=Close`
- *Note* : Mention spéciale défensive avec Max DD très faible.

### GMAB (Genmab)
- **20m** : `pivot_timeframe=D`, `retest_bars=5`, `signal_mode=Close`
- *Note* : Mention spéciale défensive (Max DD de -13.04%, Profit Factor 1.43).
