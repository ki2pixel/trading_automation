# Accélérer les optimisations avec le Pre-Scan VectorBT

**TL;DR** : Le Pre-Scan utilise la rapidité de VectorBT pour éliminer les pires configurations de paramètres en 2 secondes, permettant à l'optimizer bayésien de se concentrer uniquement sur les zones de paramètres prometteuses.

Tu lances une recherche de paramètres sur un espace géant de 20 000 combinaisons possibles pour une nouvelle stratégie. Même en utilisant l'intelligence bayésienne de notre outil, l'algorithme va devoir faire tourner au moins 500 simulations complètes barres par barres pour trouver les meilleurs réglages. Cela prend plusieurs minutes.

Et si on pouvait élaguer 90% des pires configurations de paramètres en 2 secondes chrono avant même de commencer ?

C'est exactement le rôle du **Pre-Scan VectorBT**. Il utilise le calcul matriciel JIT de VectorBT pour balayer rapidement les paramètres simples (comme les longueurs de moyennes mobiles), identifie le top 5% des meilleures zones (les sweet spots théoriques), et resserre automatiquement les bornes de recherche de l'optimizer bayésien. 

Celui-ci peut alors explorer cette zone restreinte avec la logique complète et ultra-précise du moteur principal.

---

## L'architecture du Pre-Scan

Notre module d'optimisation bayésienne (`bayesian_optimizer.py`) est totalement agnostique : il ne connaît pas les détails mathématiques de tes indicateurs. 

Pour réaliser son pre-scan, il délègue le calcul à une fonction spécifique codée directement dans le fichier de ta stratégie. Cette liaison est gérée par notre registre centralisé : `StrategyRegistry` (dans `backtest_engine/strategy_registry.py`).

```
[ Paramètres de base de l'UI ] 
       |
       v
+-------------------------------+
|  Pre-Scan VectorBT (2s)       |  <- Élimine instantanément les zones aberrantes
+-------------------------------+
       |
       v [ Bornes de recherche resserrées ]
+-------------------------------+
|  Optimizer Bayésien (Optuna)  |  <- Calcule la stratégie fine dans la zone idéale
+-------------------------------+
```

---

## Comment ajouter le pre-scan à une nouvelle stratégie ?

Si tu développes une nouvelle stratégie et que tu souhaites lui faire bénéficier de ce gain de vitesse, suis ces deux étapes simples.

### Étape 1 : Créer la fonction `vectorbt_prescan` dans ta stratégie
Ouvre le fichier de ta stratégie (ex : `backtest_engine/strategies/ma_strategie.py`) et ajoute une fonction respectant cette signature :

```python
import logging
import pandas as pd
from typing import Any
from ..optimizer import ParameterGridSpec

def vectorbt_prescan(
    data: pd.DataFrame,
    parameter_specs: list[Any],  # La liste des plages de paramètres initiales
    timeframe_minutes: int | str
) -> list[Any]:
    """
    Balaye rapidement l'espace de recherche via VectorBT pour resserrer les bornes.
    """
    logger = logging.getLogger(__name__)

    # 1. Extraire les variables à pré-scanner
    fast_specs = next((s for s in parameter_specs if s.name == "fast_len"), None)
    
    if not fast_specs or not fast_specs.values:
        return parameter_specs  # Retourne les specs d'origine s'il n'y a rien à scanner

    try:
        import vectorbt as vbt
        import numpy as np
        
        # 2. Convertir les valeurs en tableaux NumPy pour VectorBT
        fast_windows = np.array([int(v) for v in fast_specs.values])

        # 3. Lancer la simulation vectorisée rapide de signaux
        # entries = ...
        # exits = ...
        # pf = vbt.Portfolio.from_signals(data["close"], entries, exits, freq=f"{timeframe_minutes}min")
        # returns = pf.total_return()

        # 4. Identifier la meilleure zone (Top 5%)
        # top_n = max(1, int(len(returns) * 0.05))
        # top_params = returns.nlargest(top_n).index.tolist()

        # 5. Calculer les nouvelles bornes resserrées avec une marge de sécurité
        # new_min = max(int(fast_specs.values[0]), min(top_params) - 2)
        # new_max = min(int(fast_specs.values[-1]), max(top_params) + 2)

        # 6. Reconstruire les spécifications de paramètres mis à jour
        new_specs = []
        for s in parameter_specs:
            if s.name == "fast_len":
                new_vals = tuple(v for v in s.values if new_min <= int(v) <= new_max)
                new_specs.append(ParameterGridSpec(name=s.name, kind=s.kind, values=new_vals or s.values))
            else:
                new_specs.append(s)

        logger.info(f"Bornes réduites via Pre-Scan VectorBT : fast_len({new_min}-{new_max})")
        return new_specs

    except ImportError:
        logger.warning("VectorBT n'est pas installé sur la machine. Pre-scan ignoré.")
    except Exception as e:
        logger.warning(f"Incident lors du pre-scan VectorBT : {e}. Utilisation des bornes globales.")

    return parameter_specs
```

### Étape 2 : Enregistrer ta fonction dans le registre
Ouvre le fichier `backtest_engine/strategy_registry.py`.

1. Importe ta nouvelle fonction de pre-scan en haut du fichier.
2. Déclare-la lors de l'enregistrement de ta stratégie à l'aide de l'argument `vectorbt_prescan` :

```python
StrategyRegistry.register(
    StrategyInfo(
        name="ma_strategie",
        config_override_class=MaStrategieConfigOverrides,
        run_function=run_ma_strategie,
        vectorbt_prescan=ma_strategie_prescan,  # <-- C'est ici que la magie s'opère !
        clear_feature_cache=None,
    )
)
```

---

## Trois règles d'or pour un pre-scan réussi

### 1. Reste tolérant (Garde une marge de sécurité)
La simulation rapide sous VectorBT est simplifiée et n'applique pas tes règles de Stop Loss ou de Take Profit. La zone de paramètres idéale trouvée par VectorBT sera donc légèrement décalée par rapport au sweet spot réel de ton backtester complet. Conserve toujours une marge de sécurité d'au moins 10% autour des bornes resserrées.

### 2. Sois extrêmement rapide
La phase de pre-scan doit s'exécuter en moins de 3 secondes. Si ton algorithme de pré-calcul est trop lourd, il perd tout son intérêt face à la recherche bayésienne.

### 3. Prévois toujours un plan de secours (Fail-Safe)
Ta fonction de pre-scan doit être robuste. Encapsule toujours ton code VectorBT dans un bloc `try...except`. Si VectorBT n'est pas installé ou s'il manque des données, la fonction doit renvoyer la plage de paramètres initiale intacte pour que ton optimisation bayésienne classique puisse démarrer sans planter.