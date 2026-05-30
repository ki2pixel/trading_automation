# Trading Automation v2

Pipeline complet de collecte de données financières, backtest et optimisation de stratégies algorithmiques.

Ce dépôt centralise l'infrastructure technique permettant de collecter des séries financières intraday, de construire des jeux de données propres et d'exécuter des simulations de trading robustes avec des outils d'optimisation et de validation de pointe.

---

## Table des matières

1. [Architecture globale](#architecture-globale)
2. [Collector SheetsFinance](#collector-sheetsfinance)
3. [Backtest Engine](#backtest-engine)
4. [Intégration VectorBT](#intégration-vectorbt)
5. [Lanceur de production](#lanceur-de-production)
6. [Tests unitaires et d'intégration](#tests-unitaires-et-dintégration)
7. [Documentation détaillée](#documentation-détaillée)

---

## Architecture globale

Le projet est conçu sous la forme d'un pipeline modulaire en trois étapes successives :

```text
SheetsFinance (données brutes)
      |
      v
+----------------------------------+
|         Collector (Apps Script)  |
|  - barres 5min OHLCV              |
|  - splits                         |
|  - taux FX                        |
+----------------------------------+
      |
      v
Google Drive (CSV bruts)
      |
      v
+----------------------------------+
|     build-canonical (Python)     |
|  - nettoyage, ajustement splits   |
|  - normalisation numérique        |
|  - conversion Parquet             |
+----------------------------------+
      |
      v
storage/processed/ (Parquet canoniques)
      |
      v
+----------------------------------+
|      Backtest Engine (Python)    |
|  - exécution stratégies           |
|  - broker simulator               |
|  - métriques / rapports           |
|  - optimizer (grid + bayésien)    |
|  - visualiseur interactif (KLine) |
+----------------------------------+
      |
      v
reports/ (CSV, HTML, JSON)
```

Pour comprendre en profondeur le flux de données et la responsabilité de chaque couche, consultez le guide de l'**[Architecture détaillée](./docs/backtester/architecture.md)**.

---

## Collector SheetsFinance

Le **Collector** est un script Google Apps Script autonome lié à un classeur Google Sheets léger qui fait office de panneau de configuration. Il permet d'extraire de manière résiliente et automatique des barres intraday **5 minutes**, les **taux de change FX** et les **splits** depuis SheetsFinance, puis de les stocker sur **Google Drive** sous forme de fichiers CSV mensuels bruts.

Grâce à un système de **checkpoints** et un superviseur automatique à base de triggers, le collecteur gère les interruptions temporaires et poursuit sa tâche jusqu'à atteindre la date de fin configurée sans intervention humaine.

Pour installer, configurer et administrer le collecteur, consultez la documentation modulaire :
- 📦 **[Installation](./docs/backtester/collector/installation.md)** — Déploiement du script Apps Script et initialisation.
- ⚙️ **[Configuration](./docs/backtester/collector/configuration.md)** — Paramétrage de la watchlist, des devises et des fenêtres de calcul.
- 🚀 **[Utilisation](./docs/backtester/collector/utilisation.md)** — Lancement manuel, mode automatique par superviseur et reprise sur checkpoint.
- 🛠️ **[Dépannage](./docs/backtester/collector/troubleshooting.md)** — Résolution des erreurs de staging, timeouts et limitations.

---

## Backtest Engine

Le **Backtest Engine** est le cœur d'analyse quantitative écrit en Python. Il charge les datasets canoniques convertis au format performant Parquet (produits par la commande `build-canonical`), simule un broker réaliste avec commissions et slippage (mode Long/Short/Reversal), et exécute des stratégies de trading complexes converties depuis TradingView/Pine Script.

### Fonctionnalités principales

- **7 stratégies intégrées** : HMA Crossover, Adaptive Volatility Trend (AVT), Range Filter, 3Commas Bot, PMax Explorer, Bjorgum Double Tap et Noise Boundary Intraday.
- **Optimisation multi-cœurs** :
  - *Grid Search* (recherche exhaustive sur grille) avec déduplication active des paramètres inactifs.
  - *Bayesian Optimization* (Tree-structured Parzen Estimator via Optuna TPE) pour converger rapidement vers les meilleures configurations en limitant les itérations, avec arrêt dynamique sur convergence.
- **Validation Walk-Forward (WFA)** : Découpage IS/OOS dynamique via le flag `--wfo-windows` pour tester la robustesse temporelle des paramètres optimisés.
- **Diagnostics de Surapprentissage** : Calcul automatique du **PBO** (CSCV) et du **DSR** (Deflated Sharpe Ratio) pour corriger le biais lié aux tests multiples.
- **Sweet Spot Recommendations** : Génération automatique du fichier `recommendations.json` (sweet spots théoriques et runs robustes conseillés) via le module `report_interpreter.py` ou la commande CLI dédiée.
- **Visualiseur Interactif** : Graphique financier dynamique local basé sur **KLineChart** permettant de tracer l'equity curve, les indicateurs calculés et les signaux d'achat/vente.
- **Persistance des jobs (FastAPI + SQLite)** : Découplage complet de l'interface graphique FastAPI et des workers d'arrière-plan via un store SQLite robuste.

### Entrées rapides de la CLI

Pour piloter le moteur, utilisez la commande Python :

```bash
# Scanner la qualité des données brutes
python3 -m backtest_engine scan --symbol GMAB

# Lancer un backtest unitaire
python3 -m backtest_engine run --strategy hma_crossover --symbol GMAB --config configs/strategies/hma_crossover.default.json

# Lancer une optimisation bayésienne
python3 -m backtest_engine optimize --strategy hma_crossover --symbol BTCUSD --optimization-mode bayesian --max-iterations 300 --param fast_len=5:60:1 --param slow_len=20:120:1

# Générer les sweet spots d'un run existant
python3 -m backtest_engine interpret-optimization --job-dir reports/local_optimizer/hma_crossover/GMAB/RunID

# Démarrer le serveur HTTP web FastAPI
python3 -m backtest_engine serve

# Lancer le worker consommant les jobs SQLite persistants
python3 -m backtest_engine worker

# Nettoyer les jobs d'un worker crashé (ex: OOM Kill, Segfault)
python3 -m backtest_engine mark-crashed --worker-id worker-01 --exit-code 137

# Reconstruire les Parquets canoniques à partir des CSV Google Drive
python3 -m backtest_engine build-canonical --format parquet --divisor-overrides-file configs/canonical_divisor_overrides.json
```

Pour consulter le guide complet par thématique, reportez-vous aux documents suivants :
- 🎯 **[Quickstart](./docs/backtester/backtest-engine/quickstart.md)** — Premiers pas, scan initial et backtests de démonstration.
- 🔧 **[Configuration](./docs/backtester/backtest-engine/configuration.md)** — Paramétrage JSON des stratégies et propriétés TradingView.
- 🏃 **[Runner](./docs/backtester/backtest-engine/runner.md)** — Exécution, timeframes intraday multiples et broker simulator.
- 📊 **[Optimization](./docs/backtester/backtest-engine/optimization.md)** — Grille exhaustive, optimisation bayésienne, sweet spots et early convergence.
- 📐 **[Walk-Forward & Overfitting](./docs/backtester/backtest-engine/walk-forward.md)** — Validation glissante (WFA) et métriques de surapprentissage (PBO CSCV, DSR).
- 🗄️ **[Job Store SQLite](./docs/backtester/backtest-engine/job-store.md)** — Architecture asynchrone, cycle de vie des jobs et gestion des crashs.
- 🖥️ **[Viewer interactif](./docs/backtester/backtest-engine/viewer.md)** — Graphiques financiers locaux riches avec KLineChart.
- ⚡ **[Performance](./docs/backtester/backtest-engine/performance.md)** : Fast scoring, early stopping et cache des indicateurs.
- 💾 **[Datasets canoniques Parquet](./docs/backtester/backtest-engine/canonical-datasets.md)** — Commande build-canonical et overrides de diviseurs.
- 📋 **[Référence complète CLI](./docs/backtester/backtest-engine/cli-reference.md)** — Syntaxe, arguments et exemples de toutes les sous-commandes.
- 🗺️ **[Roadmap Multi-devises](./docs/backtester/backtest-engine/currency-conversion-roadmap.md)** — Gestion des conversions de devises, implémentation transverse et validation.
- 🐞 **[Dépannage](./docs/backtester/backtest-engine/troubleshooting.md)** — Résolution des erreurs courantes du moteur de backtest.

---

## Intégration VectorBT

En complément du moteur local fin, le projet intègre un bridge vers le framework de calcul vectorisé **VectorBT** à des fins d'exploration et d'audit. Ce bridge permet d'analyser massivement des millions de grilles de paramètres à très haute performance, d'effectuer de la validation Walk-Forward vectorisée et de confronter des signaux de trading à du benchmarking aléatoire (Monte Carlo).

Pour en savoir plus, consultez la documentation :
- 🔍 **[Rapport d'Audit VectorBT](./docs/backtester/vectorbt/vectorbt_audit_report.md)** — Comparatifs de performance et pertinence des cas d'usage.
- 📘 **[Guide du Bridge VectorBT](./docs/backtester/vectorbt/README.md)** — Commandes d'exploration, WFO vectorisé et benchmarking de signaux.
- ⚡ **[Pre-Scan VectorBT](./docs/backtester/vectorbt/vectorbt_prescan.md)** — Réduction d'espace intelligente intégrée à l'optimizer.

---

## Lanceur de production

Le **Launcher** est un utilitaire d'exploitation système sous Linux permettant de démarrer ou d'arrêter proprement l'ensemble des processus (le serveur web FastAPI et le worker SQLite de calcul d'optimisation) en gérant la surveillance des processus et la ré-allocation en cas de crash. Des raccourcis graphiques desktop sont fournis pour faciliter son utilisation au quotidien.

Toutes les informations pratiques sont regroupées dans la documentation :
- 🚀 **[Utilisation](./docs/backtester/launcher/utilisation.md)** — Commandes d'exploitation du script `start_backtest_engine.sh` (start, stop, status).
- ⚙️ **[Configuration launcher](./docs/backtester/launcher/configuration.md)** — Paramètres système (ports, host, variables).
- 🖥️ **[Raccourcis bureau .desktop](./docs/backtester/launcher/desktop-launchers.md)** — Installation des lanceurs graphiques d'exécution, d'arrêt et de statut.

---

## Tests unitaires et d'intégration

Le projet intègre une suite de tests complète pour valider la non-régression du moteur de calcul et du broker simulator.

Pour exécuter l'ensemble de la suite de tests via **pytest** (recommandé) :

```bash
python3 -m pytest tests/
```

Ou en natif avec **unittest** :

```bash
python3 -m unittest discover -s tests
```

---

## Documentation détaillée

Pour naviguer facilement dans les modules, utilisez le tableau récapitulatif des ressources :

| Module | Liens de documentation |
|---|---|
| **Collector** | [Installation](./docs/backtester/collector/installation.md) · [Configuration](./docs/backtester/collector/configuration.md) · [Utilisation](./docs/backtester/collector/utilisation.md) · [Dépannage](./docs/backtester/collector/troubleshooting.md) |
| **Backtest Engine** | [Quickstart](./docs/backtester/backtest-engine/quickstart.md) · [Configuration](./docs/backtester/backtest-engine/configuration.md) · [Runner](./docs/backtester/backtest-engine/runner.md) · [Optimization](./docs/backtester/backtest-engine/optimization.md) · [Global Analysis](./docs/backtester/backtest-engine/global-analysis.md) · [Walk-Forward](./docs/backtester/backtest-engine/walk-forward.md) · [Job Store](./docs/backtester/backtest-engine/job-store.md) · [Viewer](./docs/backtester/backtest-engine/viewer.md) · [Performance](./docs/backtester/backtest-engine/performance.md) · [Datasets canoniques](./docs/backtester/backtest-engine/canonical-datasets.md) · [CLI Reference](./docs/backtester/backtest-engine/cli-reference.md) · [Roadmap Multi-devises](./docs/backtester/backtest-engine/currency-conversion-roadmap.md) · [Dépannage](./docs/backtester/backtest-engine/troubleshooting.md) |
| **VectorBT Bridge** | [Rapport d'Audit](./docs/backtester/vectorbt/vectorbt_audit_report.md) · [Guide d'utilisation](./docs/backtester/vectorbt/README.md) · [Pre-Scan VectorBT](./docs/backtester/vectorbt/vectorbt_prescan.md) |
| **Launcher** | [Utilisation](./docs/backtester/launcher/utilisation.md) · [Configuration](./docs/backtester/launcher/configuration.md) · [Lanceurs graphiques](./docs/backtester/launcher/desktop-launchers.md) |
| **Architecture** | [Architecture globale](./docs/backtester/architecture.md) |
