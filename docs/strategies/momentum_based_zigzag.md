# Momentum-Based Zigzag — Détection de Zigzag par Momentum

**TL;DR**: Détecte les points de retournement (pivots) en analysant le momentum des vagues de prix plutôt que les prix eux-mêmes. Combine l'algorithme Zigzag classique avec un filtre de momentum.

---

Le Zigzag classique trace des lignes entre les pivots de prix uniquement sur les seuils de prix. Résultat : il ignore les faux mouvements sans momentum. Cette stratégie ajoute une confirmation par le momentum pour filtrer les retournements illusoires.

### ❌ Zigzag prix pur
```python
if abs(close - last_pivot) / last_pivot > threshold:
    new_pivot = close  # sensible au bruit sans momentum
```

### ✅ Zigzag filtré par momentum
```python
if abs(close - last_pivot) / last_pivot > threshold:
    if momentum_score(close, period=5) > momentum_threshold:
        new_pivot = close  # confirmé par le momentum
```

## Signaux
- **BUY** : Retournement haussier confirmé sur un creux de zigzag
- **SELL** : Retournement baissier confirmé sur un sommet de zigzag

## Trade-offs
| Filtre | Fidélité des pivots | Retard de détection |
|:---|:---|:---|
| Prix seul (classique) | Faible, beaucoup de faux pivots | Immédiat |
| Prix + Momentum | Élevée, pivots significatifs | 1-3 barres de retard |

**Règle d'or** : Un pivot sans momentum est un mirage. Le prix peut toucher un niveau sans conviction — c'est le momentum qui confirme l'intention.

*Guidé par documentation/SKILL.md — sections: TL;DR, ❌/✅ Comparison, Trade-offs, Golden Rule.*
