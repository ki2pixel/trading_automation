# PMax Explorer — Stop Suiveur Dynamique ATR

**TL;DR**: Combine une moyenne mobile avec un stop suiveur basé sur l'ATR. Le stop s'ajuste à la volatilité du marché : plus large quand c'est agité, plus serré en période calme.

---

Les stops fixes (ex: -2%, -5%) ignorent la volatilité. Sur un actif à ATR élevé, vous sortez prématurément. Sur un actif calme, vous laissez trop de marge. Le PMax utilise le multiplicateur d'ATR comme stop adaptatif.

### ❌ Stop fixe
```python
stop_price = entry_price * 0.95  # -5% fixe, ignorant l'ATR
```

### ✅ PMax ATR Stop
```python
atr_stop = ma - (atr_multiplier * atr)
pmax = if close > prev_pmax then max(atr_stop, prev_pmax) else atr_stop
```

## Signaux
- **BUY** : Close > PMax (le prix dépasse le stop suiveur)
- **SELL** : Close < PMax (le stop est touché)

## Paramètres clés
| Paramètre | Rôle | Plage typique |
|:---|:---|:---|
| `ma_length` | Période de la moyenne mobile | 10-50 |
| `atr_multiplier` | Largeur du stop en ATR | 1.5-5.0 |
| `atr_length` | Période de calcul ATR | 10-20 |

**Règle d'or** : Le PMax est un outil de sortie, pas d'entrée. Le signal d'entrée doit venir de ta stratégie principale, le PMax gère la sortie.

*Guidé par documentation/SKILL.md — sections: TL;DR, ❌/✅ Comparison, Trade-offs, Golden Rule.*
