# Trend Type — Classification du Type de Tendance

**TL;DR**: Ne se contente pas de dire "tendance haussière ou baissière" — classifie le TYPE de tendance (impulsionnelle, corrective, accumulative) pour adapter la stratégie de trading à la structure du marché.

---

"Le marché monte" ne suffit pas. Une tendance haussière peut être impulsionnelle (forte, exploitable), corrective (faible, dangereuse) ou accumulative (range avec biais). Chaque type exige une approche différente. Trend Type diagnostique la structure avant d'agir.

## Classes de tendance
- **Impulsive** : Mouvement directionnel fort, volume croissant, ATR élevé
- **Corrective** : Retracement contre la tendance principale, volume décroissant
- **Accumulative** : Range étroit avec micro-cassures, volume stable

## Mécanique
```python
trend_type = classify_trend(close, highs, lows, volume_stream, atr_stream)
if trend_type == IMPULSIVE:
    signal = trend_following_entry()
elif trend_type == CORRECTIVE:
    signal = mean_reversion_entry()
elif trend_type == ACCUMULATIVE:
    signal = NO_TRADE  # attendre la résolution
```

## Signaux
- **BUY** : Tendance impulsive haussière confirmée OU corrective terminée
- **SELL** : Tendance impulsive baissière confirmée OU corrective terminée

## Trade-offs
| Classification | Adaptabilité | Complexité |
|:---|:---|:---|
| Binaire (up/down) | Faible — même stratégie pour tout | Simple |
| Type de tendance | Élevée — stratégie adaptée au régime | Plus de calcul, plus de code |

**Règle d'or** : Trader une tendance corrective avec une stratégie de suivi de tendance, c'est comme surfer une vague de 30 cm. Identifie d'abord le type de vague, puis choisis ta planche.

*Guidé par documentation/SKILL.md — sections: TL;DR, Code, Trade-offs, Golden Rule.*
