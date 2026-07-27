# VectorBT Bridge — Pont entre Backtest Engine et VectorBT

**TL;DR**: Le `vectorbt_bridge` fait le lien entre notre moteur de backtest barre-par-barre (fidèle mais lent) et VectorBT (vectorisé, 10-100x plus rapide mais simplifié). Il convertit les signaux, adapte les données, exécute les comparaisons et génère les heatmaps — le tout en garantissant que les deux systèmes parlent le même langage.

---

Le `vectorbt_bridge` n'est pas un remplacement du moteur principal. C'est un **accélérateur de workflow** qui délègue les tâches massivement parallélisables à VectorBT tout en conservant la précision du moteur principal pour les décisions finales.

---

## Modules

```
vectorbt_bridge/
├── data_adapter.py       → Chargement des données canoniques pour VectorBT
├── strategy_bridge.py    → Conversion signaux + comparaison back-to-back
├── visualization.py       → Heatmaps Plotly des grilles de paramètres
├── random_benchmark.py   → Benchmark statistique (modèles aléatoires)
├── compare_hma.py        → Comparaison ciblée HMA Crossover
├── vectorized_exploration.py → Exploration vectorisée de l'espace de paramètres
└── vectorized_wfo.py     → Walk-Forward Optimization vectorisée
```

---

## 1. Data Adapter — `data_adapter.py` (103 LOC)

Convertit les données canoniques SheetsFinance (Parquet) en DataFrames compatibles VectorBT.

```python
from backtest_engine.vectorbt_bridge.data_adapter import load_sheetsfinance_to_vectorbt

# Un seul appel → DataFrame avec DatetimeIndex et colonnes OHLCV
df = load_sheetsfinance_to_vectorbt(
    symbol="AMS.MC",
    timeframe_minutes=5,
    start_date="2023-01-01",
    end_date="2024-12-31",
)
# → pd.DataFrame avec colonnes: open, high, low, close, volume
```

### Data Class VectorBT native

Pour une intégration directe avec le système de données de VectorBT :

```python
from backtest_engine.vectorbt_bridge.data_adapter import SheetsFinanceData

data = SheetsFinanceData.fetch_symbol("AMS.MC", timeframe_minutes=5)
# → VectorBT Data object prêt pour Portfolio.from_signals()
```

---

## 2. Strategy Bridge — `strategy_bridge.py` (194 LOC)

Le cœur du pont. Prend les résultats du backtest engine, extrait les signaux, et les rejoue dans VectorBT pour comparaison.

### Extraction des signaux

```python
from backtest_engine.vectorbt_bridge.strategy_bridge import extract_signals

# À partir d'un résultat de backtest
result: BacktestRunResult = run_strategy(...)
entries, exits = extract_signals(result)
# → pd.Series[bool] prêtes pour vbt.Portfolio.from_signals()
```

### Comparaison back-to-back

```python
from backtest_engine.vectorbt_bridge.strategy_bridge import compare_backtest_vs_vectorbt

comparison = compare_backtest_vs_vectorbt(
    result,            # Résultat du backtest engine
    symbol="AMS.MC",
    close=close_series,
)
# → {
#     "symbol": "AMS.MC",
#     "native_net_pnl": 1234.56,
#     "vbt_net_pnl": 1189.23,
#     "pnl_delta_pct": -3.67,
#     "vbt_max_drawdown_pct": -12.34,
#     "vbt_sharpe": 1.45,
# }
```

Les écarts sont normaux : VectorBT applique une logique de sizing et slippage simplifiée par rapport au moteur principal. L'objectif de la comparaison est de **quantifier** cet écart, pas de l'éliminer.

---

## 3. Visualization — `visualization.py` (73 LOC)

Heatmaps Plotly interactives pour visualiser les grilles de paramètres.

```python
from backtest_engine.vectorbt_bridge.visualization import plot_heatmap

fig = plot_heatmap(
    results_df,          # DataFrame avec colonnes de params + métriques
    x_param="ma_length",
    y_param="atr_multiplier",
    z_metric="sharpe_ratio",
)
fig.show()
```

---

## 4. Random Benchmark — `random_benchmark.py` (85 LOC)

Génère N modèles aléatoires et exécute leur backtest VectorBT. Sert de ligne de base statistique pour mesurer si ta stratégie performe mieux que le hasard.

```python
from backtest_engine.vectorbt_bridge.random_benchmark import run_random_benchmarks

benchmarks = run_random_benchmarks(
    close=close_series,
    n_models=1000,
    seed=42,
)
# → Distribution des Sharpe ratios aléatoires
# Si le Sharpe de ta stratégie > 95th percentile → significatif
```

---

## 5. Vectorized Exploration — `vectorized_exploration.py` (114 LOC)

Explore l'espace de paramètres complet en une seule opération vectorisée. Idéal pour le pré-scan.

---

## 6. Vectorized WFO — `vectorized_wfo.py` (109 LOC)

Walk-Forward Optimization vectorisée. Découpe les données en fenêtres in-sample/out-of-sample et optimise sur chaque fenêtre.

---

## Flux de travail typique

```
1. Charger données  ──▶ data_adapter.load_sheetsfinance_to_vectorbt()
2. Pré-scan VectorBT ──▶ vectorized_exploration (grille large, 2s)
3. Optimisation fine ──▶ backtest_engine.optimizer (Optuna, top 10%)
4. Comparaison       ──▶ strategy_bridge.compare_backtest_vs_vectorbt()
5. Visualisation     ──▶ visualization.plot_heatmap()
6. Benchmark         ──▶ random_benchmark.run_random_benchmarks()
```

---

## Trade-offs VectorBT vs Moteur Principal

| Aspect | VectorBT | Backtest Engine |
|:---|:---|:---|
| **Vitesse** | 10-100x (matriciel JIT) | 1x (barre par barre) |
| **Précision broker** | Simplifiée (sizing fixe) | Complète (commissions, slippage, stops) |
| **Règles de sécurité** | Aucune | MEP, MHP, margin check, kill switch |
| **Usage** | Exploration, pré-scan, benchmark | Optimisation finale, validation |
| **Données** | OHLCV uniquement | OHLCV + états internes |

---

## The Golden Rule

> **Règle d'or** : VectorBT te dit OÙ chercher. Le Backtest Engine te dit QUOI garder. N'inverse jamais les rôles — un Sharpe de 3.5 sur VectorBT ne vaut rien sans validation par le moteur complet.

---

## Références

- **Code source** : `backtest_engine/vectorbt_bridge/` (791 LOC, 7 modules)
- **Audit VectorBT** : `docs/backtester/vectorbt/vectorbt_audit_report.md`
- **Pre-Scan** : `docs/backtester/vectorbt/vectorbt_prescan.md`
- **Stratégies** : Chaque stratégie avec `vectorbt_prescan` dans `strategy_registry.py`

*Guidé par documentation/SKILL.md — sections: TL;DR, Architecture, ❌/✅ Comparison, Trade-offs, Golden Rule.*
