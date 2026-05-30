# Intégrer VectorBT : Vitesse brute vs Simulation fidèle

**TL;DR** : Le pont VectorBT est notre accélérateur de calcul. Utilise-le pour pré-filtrer massivement des millions de paramètres en quelques secondes, puis laisse le moteur principal exécuter tes backtests avec toutes tes règles métier et tes frais de courtage exacts.

Tu veux tester des millions de combinaisons de paramètres sur plusieurs actions en même temps. Tu lances ton moteur de simulation local et, même s'il est très performant, le terminal t'indique que le calcul va prendre 45 minutes. C'est dans ce genre de scénario que tu as besoin de la puissance matricielle de **VectorBT**.

Grâce à la compilation JIT (Numba) et à l'utilisation intensive des calculs vectoriels NumPy, VectorBT est capable de simuler des grilles géantes à une vitesse fulgurante.

Mais attention : VectorBT n'est pas un remplaçant magique. Il a ses propres limites et règles du jeu.

---

## Le match : Quand utiliser VectorBT vs le moteur principal ?

| Critère | Moteur Principal (`backtest_engine`) | Pont VectorBT (`vectorbt_bridge`) |
|---|---|---|
| **Vitesse de calcul** | Rapide (30-45 minutes pour 100k runs) | Ultra-rapide (quelques secondes) |
| **Logique Pine Script** | 100% fidèle (exécute tes codes traduits) | Simplifiée (signaux d'entrée/sortie uniquement) |
| **Frais complexes** | Gérés (3 modes de frais, slippage par côté) | Basiques (pourcentage fixe) |
| **Sécurité Stop Loss / TP** | Avancée (safety stops combinés, max bars) | Basique (seuils fixes) |
| **Optimisation** | Bayésienne (Optuna TPE) | Matricielle (Grid uniquement) |

### La règle d'or d'utilisation
- **Utilise VectorBT pour** : Pré-filtrer une grille géante de paramètres (Pre-Scan), simuler des benchmarks aléatoires pour valider ton avantage statistique, ou lancer des analyses Walk-Forward (WFO) rapides sur des indicateurs simples.
- **Utilise le Moteur Principal pour** : Obtenir un rapport financier précis à 100% avec des frais réels de courtage, simuler des safety stops complexes, et valider la viabilité réelle de ton capital avant mise en production.

---

## Les fonctionnalités prêtes à l'emploi du Bridge

Tous les outils de connexion sont regroupés sous `backtest_engine/vectorbt_bridge/`.

### 1. Ingestion de données (`SheetsFinanceData`)
Nous avons écrit un adaptateur de données personnalisé qui permet à VectorBT de lire directement nos fichiers Parquet et CSV locaux issus de ton collecteur Google Drive :

```python
from backtest_engine.vectorbt_bridge.data_adapter import SheetsFinanceData

# Charge tes cours de bourse directement sous forme d'objet VectorBT Data
vbt_data = SheetsFinanceData.fetch_symbol(symbol="AMS.MC", timeframe_minutes=5)
close_prices = vbt_data.get("close")
```

### 2. Balayage de paramètres vectorisé (`vectorized_exploration.py`)
Cette commande fait tourner une recherche de croisements de moyennes mobiles HMA sur une grille immense en une fraction de seconde, puis enregistre le résultat dans un fichier JSON :

```bash
python3 -m backtest_engine.vectorbt_bridge.vectorized_exploration \
    --symbol AMS.MC \
    --fast-range "5:50:5" \
    --slow-range "20:100:10"
```

### 3. Validation par Walk-Forward vectorisé (`vectorized_wfo.py`)
Pour découper tes données en fenêtres glissantes d'entraînement et de test et mesurer la stabilité de tes paramètres à toute vitesse :

```bash
python3 -m backtest_engine.vectorbt_bridge.vectorized_wfo \
    --symbol AMS.MC \
    --fast-range "10:40:10" \
    --slow-range "40:100:20" \
    --n-windows 3
```

### 4. Benchmark de hasard (`random_benchmark.py`)
Comment prouver scientifiquement que ta stratégie possède un réel avantage sur le marché et ne doit pas son profit au pur hasard ? 

Cette commande simule $N$ stratégies totalement aléatoires (achats et ventes au hasard) pour établir une distribution statistique. Si ta stratégie optimisée obtient un score Sharpe largement supérieur à cette distribution, tu as prouvé ton avantage mathématique.

```bash
python3 -m backtest_engine.vectorbt_bridge.random_benchmark \
    --symbol AMS.MC \
    --n-samples 100 \
    --prob-enter 0.1 \
    --prob-exit 0.1
```

### 5. Heatmaps interactifs (`visualization.py`)
Convertit tes rapports JSON complexes en cartes de chaleur 2D interactives sous forme de page HTML :

```bash
python3 -m backtest_engine.vectorbt_bridge.visualization \
    --results-file reports/vectorbt_exploration.json \
    --x fast_window \
    --y slow_window \
    --z total_return_pct \
    --output reports/heatmap.html
```

> [!NOTE]
> Pour consulter tous les détails techniques et méthodologiques de notre audit de performance, jette un œil au **[Rapport d'Audit VectorBT](./vectorbt_audit_report.md)**.
