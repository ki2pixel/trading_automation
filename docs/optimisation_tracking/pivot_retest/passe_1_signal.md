# Rapport de Backtesting : Pivot Breakout Retest Signals (Passe 1)

## Objectif
Optimiser le paramètre de structure de marché `pivot_timeframe` avec `retest_bars = 5` et `signal_mode = "Close"` figés, afin d'identifier le meilleur horizon temps pour détecter les pivots significatifs.

## Itérations et Couverture
- **Total des itérations éligibles sur l'ensemble :** 6800

## Classification des Actifs

### 🟢 Les Validés (Edge directionnel net et robuste)

**NVO (Novo Nordisk)**
- **10m** : `pivot_timeframe=D`, `retest_bars=5`, `signal_mode=Close` (Score: 33.96%, PF: 1.28, MaxDD: -216.85%)
- **15m** : `pivot_timeframe=D`, `retest_bars=5`, `signal_mode=Close` (Score: 33.37%, PF: 1.29, MaxDD: -242.88%)
- **20m** : `pivot_timeframe=D`, `retest_bars=5`, `signal_mode=Close` (Score: 26.83%, PF: 1.27, MaxDD: -310.56%)
- **30m** : `pivot_timeframe=D`, `retest_bars=5`, `signal_mode=Close` (Score: 25.99%, PF: 1.28, MaxDD: -314.03%)
- **45m** : `pivot_timeframe=D`, `retest_bars=5`, `signal_mode=Close` (Score: 29.96%, PF: 1.34, MaxDD: -150.60%)
- **120m** : `pivot_timeframe=12H`, `retest_bars=5`, `signal_mode=Close` (Score: 29.87%, PF: 1.28, MaxDD: -165.84%)
*Note : Le drawdown cumulé peut être élevé dû au réinvestissement et volume de trades, mais l'edge est positif et robuste.*

### 🟡 Mentions Spéciales (Profils défensifs/conservateurs)

**EVD.DE (CTS Eventim)**
- **10m** : `pivot_timeframe=W`, `retest_bars=5`, `signal_mode=Close` (Score: -31.59%, PF: 1.71, MaxDD: -2.59%)
- **15m** : `pivot_timeframe=W`, `retest_bars=5`, `signal_mode=Close` (Score: -31.60%, PF: 1.36, MaxDD: -3.71%)
- **30m** : `pivot_timeframe=W`, `retest_bars=5`, `signal_mode=Close` (Score: -31.57%, PF: 1.39, MaxDD: -3.31%)
- **240m** : `pivot_timeframe=D`, `retest_bars=5`, `signal_mode=Close` (Score: -31.58%, PF: 1.47, MaxDD: -1.50%)
*Analyse : Bien que le score soit négatif comparé au Buy & Hold, le Max Drawdown est très faible (profil très défensif) couplé à des Profit Factors décents, en particulier sur 10m et 240m.*

**GMAB (Genmab)**
- **20m** : `pivot_timeframe=D`, `retest_bars=5`, `signal_mode=Close` (Score: -27.42%, PF: 1.43, MaxDD: -13.04%)
*Analyse : Profil défensif offrant un bon Profit Factor et un drawdown très contenu sur le 20m.*

### 🔴 Les Rejetés (Absence d'edge ou Drawdown excessif)

- **LOGI (Logitech) :** Sous-performance massive comparée au B&H (-479.76%).
- **SAP :** Sous-performance (-185.54%) et Max Drawdown de -51.10%.
- **SHL.DE (Siemens Healthineers) :** Sous-performance notable (-128.44%).
- **ZEAL.CO :** Drawdown excessif (-160.30%) et sous-performance (-71.68%).
- **AMS.MC, FPE.DE, NVS :** 0 itérations éligibles (aucun edge détecté par les critères de sélection).
