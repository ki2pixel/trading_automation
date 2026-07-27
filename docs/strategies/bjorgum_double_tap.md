# Bjorgum Double Tap — Double Confirmation de Retournement

**TL;DR**: Exige deux confirmations consécutives de divergence (prix vs momentum) avant de déclencher un signal. Le premier "tap" détecte la divergence, le second la confirme.

---

Les divergences RSI classiques donnent beaucoup de faux signaux : le prix continue sa tendance après un premier avertissement. Le Double Tap résout ce problème en exigeant que la divergence se produise DEUX FOIS dans une fenêtre temporelle courte.

## Mécanique
```
Divergence détectée (Tap 1) → attente → re-test du niveau → confirmation (Tap 2) → signal
```

### ❌ Divergence simple
```python
if price_makes_higher_high and rsi_makes_lower_high:
    signal = SELL  # Faux signal si la tendance continue
```

### ✅ Double Tap
```python
if tap1_divergence and within_window(tap1, now, max_bars=10):
    if tap2_divergence:  # confirmation
        signal = SELL
```

## Signaux
- **BUY** : Double divergence haussière confirmée
- **SELL** : Double divergence baissière confirmée

## Trade-offs
| Approche | Faux signaux | Signaux manqués |
|:---|:---|:---|
| Divergence simple | Très élevés | Très rares |
| Double Tap | Très faibles | Certains vrais signaux ignorés |

**Règle d'or** : En trading de divergence, la patience est ta meilleure arme. Attends le deuxième tap — le marché te le rendra.

*Guidé par documentation/SKILL.md — sections: TL;DR, ❌/✅ Comparison, Trade-offs, Golden Rule.*
