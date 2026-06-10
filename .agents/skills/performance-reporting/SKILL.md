---
name: "performance-reporting"
description: "Générateur d'analyses visuelles et d'attributions de performance"
---

# Spécialisation: performance-reporting

## 1. Rôle et Objectifs
L'agent en charge de cette compétence a pour mission de rendre les résultats du trading (en backtest ou en live) compréhensibles pour l'humain. Il génère des rapports visuels, analyse l'attribution du Profit and Loss (PnL), détecte la dégradation (alpha decay) et exporte les logs pour la traçabilité.

## 2. Principes Fondamentaux & Contraintes

- **Séparation de la Présentation**: La logique d'affichage doit être strictement séparée de la logique de calcul. Ce module ne recalcule pas le PnL, il consomme les données pré-calculées par `backtesting-engine`.
- **Interopérabilité des Formats**: Les rapports doivent être exportables en formats standardisés (JSON pour une API, CSV pour l'analyse Excel, HTML pour les visualisations Plotly).
- **Attribution de Performance**: Savoir dissocier le rendement dû au marché (Beta) du rendement lié à la compétence de l'algorithme (Alpha).
- **Analyse des Trades**: Documenter non seulement le PnL global, mais aussi les statistiques par trade (Win Rate, Average Win, Average Loss, Consecutive Losses).
- **Reporting WFA & Métriques Clés**: Les rapports finaux et logs structurés (JSON) doivent impérativement intégrer les métriques NVO, NVS et AMS.MC pour permettre la validation formelle des stratégies post-Optuna.

## 3. Schémas de Référence (Patterns)

### A. Génération de Rapport JSON Standardisé
```python
import pandas as pd
import json

def generate_performance_report(metrics_dict: dict, trades_df: pd.DataFrame, filepath: str):
    """
    Crée un rapport JSON complet avec les métriques globales et des statistiques sur les trades individuels.
    """
    winning_trades = trades_df[trades_df['pnl'] > 0]
    losing_trades = trades_df[trades_df['pnl'] <= 0]
    
    report = {
        "global_metrics": metrics_dict,
        "trade_statistics": {
            "total_trades": len(trades_df),
            "win_rate": len(winning_trades) / len(trades_df) if len(trades_df) > 0 else 0,
            "average_win": winning_trades['pnl'].mean() if not winning_trades.empty else 0.0,
            "average_loss": losing_trades['pnl'].mean() if not losing_trades.empty else 0.0,
            "largest_win": winning_trades['pnl'].max() if not winning_trades.empty else 0.0,
            "largest_loss": losing_trades['pnl'].min() if not losing_trades.empty else 0.0
        }
    }
    
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=4)
        
    return report
```

### B. Visualisation Plotly de l'Équity Curve
```python
import plotly.graph_objects as go
import pandas as pd

def plot_equity_curve(df: pd.DataFrame, output_file: str = "equity_curve.html"):
    """
    Génère un graphique interactif de la courbe de capital.
    """
    fig = go.Figure()
    
    # Courbe principale (Stratégie)
    fig.add_trace(go.Scatter(
        x=df.index, 
        y=df['cumulative_returns'],
        mode='lines',
        name='Strategy Returns',
        line=dict(color='blue')
    ))
    
    # Courbe de Benchmark (Buy & Hold) - Optionnelle
    if 'benchmark_returns' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, 
            y=df['benchmark_returns'],
            mode='lines',
            name='Benchmark',
            line=dict(color='gray', dash='dash')
        ))
        
    fig.update_layout(
        title="Performance Backtest",
        xaxis_title="Date",
        yaxis_title="Cumulative Returns",
        template="plotly_dark"
    )
    
    fig.write_html(output_file)
```

## 4. Pièges à Éviter (Anti-Patterns)
- ❌ Coder des visualisations en dur en utilisant `matplotlib.pyplot.show()` dans des scripts destinés à tourner sur un serveur sans interface graphique. Toujours exporter vers des fichiers (`.png`, `.html`).
- ❌ Moyenne arithmétique des rendements annuels pour calculer le Compound Annual Growth Rate (CAGR). Utiliser la formule géométrique correcte: `(Valeur_Finale / Valeur_Initiale) ^ (1 / Années) - 1`.
- ❌ Ignorer le Drawdown dans les graphiques. La zone sous l'eau (underwater plot) doit souvent être visualisée conjointement pour évaluer la douleur de la stratégie.

## 5. Interactions avec les autres Skills
- Consomme les données nettoyées et métriques brutes de `backtesting-engine`.
- Peut être invoqué de façon asynchrone pour générer des tableaux de bord sur l'état de `execution-order-routing` (monitoring live).
