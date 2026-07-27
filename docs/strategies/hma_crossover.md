# HMA Crossover — Croisement de Hull Moving Averages

**TL;DR**: La Hull Moving Average élimine le lag des moyennes classiques grâce à une moyenne pondérée de WMA. Cette stratégie détecte les changements de tendance par croisement de deux HMA.

---

Les MAs classiques (SMA, EMA) accusent un retard proportionnel à leur période. La HMA de Alan Hull résout ce problème en appliquant une racine carrée à la période effective, produisant une courbe réactive sans sacrifier le lissage.

### ❌ SMA classique
```python
sma = close.rolling(period).mean()  # lag = period/2
```

### ✅ Hull Moving Average
```python
wma_half = WMA(close, period // 2)
wma_full = WMA(close, period)
# HMA = WMA de (2 × WMA_half - WMA_full) sur sqrt(period)
hma = wma(2 * wma_half - wma_full, int(sqrt(period)))
```

## Signaux
- **BUY** : HMA courte croise au-dessus de la HMA longue
- **SELL** : HMA courte croise en dessous de la HMA longue

## Trade-offs
| Période courte | Réactivité | Faux signaux |
|:---|:---|:---|
| Faible (< 20) | Excellente | Élevés |
| Moyenne (20-55) | Bonne | Modérés |
| Élevée (> 55) | Faible | Très faibles |

**Règle d'or** : La HMA n'élimine pas tout le lag — elle le réduit. Combine-la avec un filtre de volatilité pour les marchés latéraux.

*Guidé par documentation/SKILL.md — sections: TL;DR, ❌/✅ Comparison, Trade-offs, Golden Rule.*
