# 3Commas Bot — Signaux de Momentum Composite

**TL;DR**: Implémentation des signaux de trading algorithmique compatibles avec la plateforme 3Commas. Utilise un composite de RSI, MACD et volumes pour générer des points d'entrée/sortie optimisés par backtest.

---

Les bots 3Commas utilisent des signaux techniques standardisés. Cette stratégie reproduit et améliore ces signaux en backtest, permettant d'optimiser les paramètres avant déploiement sur la plateforme.

## Composite de signaux
```python
score = 0
score += rsi_signal(close, period=14)      # -1, 0, ou +1
score += macd_signal(close)                 # -1, 0, ou +1
score += volume_signal(volume, close)       # confirmation de participation
```

## Signaux
- **BUY** : Score composite ≥ 2 (au moins 2 indicateurs en faveur)
- **SELL** : Score composite ≤ -2

## Filtres additionnels
- **Cooldown post-trade** : Pas de nouvelle entrée pendant N barres
- **Capital bucketing** : Allocation fractionnée du capital par signal

## Trade-offs
| Nombre d'indicateurs | Fiabilité | Opportunités |
|:---|:---|:---|
| 1 seul | Faible | Nombreuses |
| 3 (composite) | Élevée, consensus requis | Modérées |

**Règle d'or** : Un seul indicateur ment. Trois indicateurs qui disent la même chose méritent ton attention.

*Guidé par documentation/SKILL.md — sections: TL;DR, Code, Trade-offs, Golden Rule.*
