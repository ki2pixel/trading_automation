# Adaptive Volatility Trend — Tendance Adaptative à la Volatilité

**TL;DR**: Ajuste dynamiquement les paramètres de la stratégie en fonction de la volatilité mesurée. En période calme, les signaux sont plus sensibles. En période agitée, les seuils sont élargis pour éviter les faux signaux.

---

Une stratégie avec des paramètres fixes fonctionne dans UN seul régime de volatilité. Quand le VIX passe de 12 à 35, tes stops fixes deviennent inadaptés. L'Adaptive Volatility Trend recalibre tout en temps réel.

### ❌ Paramètres fixes
```python
atr_period = 14           # toujours 14, peu importe le régime
stop_multiplier = 2.0     # toujours 2.0
```

### ✅ Paramètres adaptatifs
```python
volatility_regime = classify_volatility(atr, vix_proxy)
atr_period = short if high_volatility else long
stop_multiplier = wide if high_volatility else tight
```

## Signaux
- **BUY** : Tendance haussière confirmée avec paramètres adaptés
- **SELL** : Tendance baissière confirmée avec paramètres adaptés

## Trade-offs
| Paramétrage | Stabilité | Performance cross-régime |
|:---|:---|:---|
| Fixe | Prévisible | Dégradée hors du régime cible |
| Adaptatif | Variable | Consistante à travers les régimes |

**Règle d'or** : Les marchés changent de personnalité. Ta stratégie doit changer avec eux. Ce qui fonctionne en marché calme te tuera en marché volatil — et vice-versa.

*Guidé par documentation/SKILL.md — sections: TL;DR, ❌/✅ Comparison, Trade-offs, Golden Rule.*
