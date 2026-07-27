# Smart Trader Geometric — Moyennes Mobiles Géométriques

**TL;DR**: Remplace les MM arithmétiques par des MM géométriques pour mieux capturer les rendements composés. Le croisement déclenche les signaux, filtré par un contrôle de volatilité.

---

Les rendements financiers sont multiplicatifs, pas additifs. Un gain de 10% suivi d'un gain de 10% donne 21%, pas 20%. Les moyennes arithmétiques ignorent cette composition. La moyenne géométrique la capture.

### ❌ Moyenne arithmétique (SMA)
```python
sma = sum(prices[-n:]) / n  # suppose un monde additif
```

### ✅ Moyenne géométrique
```python
geo_ma = exp(mean(log(prices[-n:])))  # respecte la composition
```

## Signaux
- **BUY** : MM géométrique courte > MM géométrique longue + filtre volatilité OK
- **SELL** : MM géométrique courte < MM géométrique longue

## Filtres
- **Volatilité** : Pas d'entrée si ATR > seuil (marché trop agité)
- **Volume** : Confirmation par volume anormal

## Trade-offs
| Type de moyenne | Rendements composés | Calcul |
|:---|:---|:---|
| Arithmétique | Sous-estime la croissance | Simple |
| Géométrique | Mesure exacte | Log/exp, plus lent |

**Règle d'or** : Dans un monde de rendements composés, la géométrie bat l'arithmétique à chaque fois.

*Guidé par documentation/SKILL.md — sections: TL;DR, ❌/✅ Comparison, Trade-offs, Golden Rule.*
