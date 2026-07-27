# Pivot Retest — Re-test de Pivots

**TL;DR**: Plutôt que d'entrer sur la cassure initiale, cette stratégie attend que le prix revienne tester le niveau de pivot (support/résistance) pour offrir une entrée à meilleur prix avec un stop plus serré.

---

Les cassures de support/résistance sont excitantes mais risquées : le prix peut casser puis immédiatement revenir (fakeout). Le Pivot Retest entre uniquement APRÈS que le prix est revenu toucher le niveau cassé et a montré un rejet.

## Mécanique
```
Cassure du pivot → attente du retest → confirmation du rejet → entrée
```

### ❌ Entrée sur cassure
```python
if close > resistance:
    BUY  # risque de fakeout immédiat
```

### ✅ Entrée sur retest
```python
if close > resistance:  # cassure
    pivot_level = resistance
    wait_for_retest()
    if close touches pivot_level and bullish_rejection():
        BUY  # entrée après confirmation
```

## Signaux
- **BUY** : Retest haussier d'un pivot de résistance cassé
- **SELL** : Retest baissier d'un pivot de support cassé

## Trade-offs
| Stratégie | Taux de réussite | Opportunités manquées |
|:---|:---|:---|
| Cassure directe | ~40% (beaucoup de fakeouts) | Aucune |
| Retest | ~65% (filtré) | ~30% des cassures ne retestent pas |

**Règle d'or** : Le marché revient toujours dire bonjour aux niveaux importants. Sois patient, attends le retest, et ton stop sera 2x plus serré.

*Guidé par documentation/SKILL.md — sections: TL;DR, ❌/✅ Comparison, Trade-offs, Golden Rule.*
