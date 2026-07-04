# Le Patron BaseStrategyRunner : Standardiser l'Exécution et l'Héritage des Stratégies

**TL;DR**: La classe abstraite `BaseStrategyRunner` centralise la standardisation des données OHLCV, la reconstruction des états de portefeuille et l'évaluation des règles de sortie; **ce patron réduit la duplication de code de plus de 80% tout en garantissant des simulations fidèles.**

---

## Le Problème : Le Fardeau du Boilerplate

Vous concevez une nouvelle stratégie de trading. Vous voulez vous concentrer uniquement sur la détection de signaux (le croisement d'un indicateur, le filtrage de tendance); mais vous vous retrouvez à devoir copier-coller des centaines de lignes de code utilitaire :
- Normalisation et validation de la structure des colonnes de données (OHLCV).
- Alignement temporel des données et extraction de la chronologie (timestamps).
- Calcul complexe du PnL réalisé et non réalisé par bougie.
- Instanciation et liaison manuelle d'un orchestrateur de règles de sortie (Stop Loss, Take Profit, Trailing Stops, Safety Stops).

Ce code répété obscurcit la logique réelle de l'algorithme, augmente la dette technique et rend les futures évolutions du moteur extrêmement périlleuses. Chaque modification dans le simulateur de courtage nécessite alors d'éditer individuellement chaque fichier de stratégie.

---

## La Solution : Séparation par Blueprints de Simulation

Pour résoudre ce problème, le moteur s'appuie sur deux classes de base situées dans [strategy_base.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/strategies/strategy_base.py) :
1.  `BaseStrategyRunner` : Fournit les fondations de manipulation de données et de reconstruction d'états.
2.  `BaseBrokerStrategyRunner` : Étend la classe de base pour y coupler l'initialisation automatisée du simulateur de courtier et de son orchestre de règles de sortie.

### ❌ Avant : Logique de Stratégie Noyée dans l'Infrastructure
```python
# Fichier : strategies/hma_crossover.py (Ancienne version)
def run_hma_crossover(data, config_overrides, ...):
    # Duplication : Normalisation manuelle
    df = data.copy()
    df = df[["open", "high", "low", "close", "volume"]]

    # Duplication : Surcharge manuelle
    config = default_config.copy()
    if config_overrides:
        for k, v in config_overrides.items():
            config[k] = v

    # Duplication : Instanciation verbeuse du Broker
    broker_config = BrokerConfig(initial_capital=initial_capital, ...)
    broker = BrokerSimulator(broker_config)
    
    # Duplication : Orchestration des sorties
    exit_rules = []
    if config.enable_stop_loss:
        exit_rules.append(NetBracketExitRule(broker, sl_pct=config.stop_loss_pct))
    broker.exit_orchestrator = ExitOrchestrator(exit_rules)
    
    # [Logique réelle de la stratégie...]
```

### ✅ Après : Subclassing Propre et Déclaration d'Intention
```python
# Fichier : strategies/hma_crossover.py (Version standardisée)
from .strategy_base import BaseBrokerStrategyRunner

def run_hma_crossover(data, config_overrides, ...):
    # 1. Standardisation et application des surcharges via les helpers
    ohlcv = BaseBrokerStrategyRunner._to_strategy_ohlcv(data)
    config = BaseBrokerStrategyRunner._apply_overrides(default_config, config_overrides)
    
    # 2. Configuration automatisée du broker et des règles de sortie
    broker, broker_config = BaseBrokerStrategyRunner.setup_broker_simulator(
        overrides=config,
        initial_capital=initial_capital,
        account_currency=account_currency,
        asset_currency=asset_currency,
        fx_rate_provider=fx_rate_provider
    )
    
    # 3. Exécution directe de la logique métier
    # [Calcul des indicateurs, boucle de simulation...]
```

---

## Comparatif des Classes de Base

| Fonctionnalité | BaseStrategyRunner | BaseBrokerStrategyRunner |
| :--- | :--- | :--- |
| **Objectif Principal** | Gestion de données et reconstruction d'états | Orchestration complète du courtier et des sorties |
| **Normalisation OHLCV** | ✅ Intégrée (`_to_strategy_ohlcv`) | ✅ Héritée |
| **Application d'Overrides** | ✅ Intégrée (`_apply_overrides`) | ✅ Héritée |
| **Calcul PnL par Bougie** | ✅ Intégrée (`_build_state_from_broker`) | ✅ Héritée |
| **Configuration Broker** | ❌ Manuelle | ✅ Automatisée (`setup_broker_simulator`) |
| **Orchestrateur de Sorties** | ❌ Manuelle | ✅ Automatique (Net Bracket, Trailing, Safety Stops) |

---

## Le Processus d'Intégration d'une Nouvelle Stratégie

Pour implémenter une nouvelle stratégie dans le système :
1.  **Hériter** de la classe appropriée (généralement `BaseBrokerStrategyRunner` pour les stratégies utilisant la simulation de courtier bar-by-bar).
2.  **Appeler** `_to_strategy_ohlcv` et `_apply_overrides` au début de votre fonction principale d'exécution.
3.  **Initialiser** le courtier via `setup_broker_simulator` pour bénéficier automatiquement de l'orchestration des sorties de sécurité.
4.  **Déclarer** et **enregistrer** votre stratégie dans le registre global [strategy_registry.py](file:///home/kidpixel/trading_automation_v2/backtest_engine/strategy_registry.py).

---

## La Règle d'Or : Standardiser l'État, Concentrer l'Exécution

> **Règle d'or** : Ne réécrivez jamais la logique de calcul d'exposition ou d'évaluation de Stop Loss dans le code d'une stratégie; déléguez la gestion de l'état aux abstractions de base pour préserver la cohérence des indicateurs et la fiabilité des métriques.
