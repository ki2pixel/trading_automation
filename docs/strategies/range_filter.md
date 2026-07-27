# Range Filter — Filtre de Bruit et Détection de Tendance

**TL;DR**: Un filtre adaptatif qui identifie les débuts de tendance en mesurant la distance du prix par rapport à une plage de bruit calculée dynamiquement. Ignore le bruit, capture les mouvements significatifs.

---

Les marchés passent 70% du temps en range. Entrer pendant ces phases, c'est accumuler des frais pour des micro-profits. Le Range Filter calcule la largeur de la plage de bruit et ne génère des signaux que lorsque le prix en sort significativement.

## Mécanique
```python
range_size = average_true_range(sampled_prices, range_period)
filtered_price = close.copy()
if abs(close - prev_filtered) < range_size:
    filtered_price = prev_filtered  # dans la plage: pas de mouvement
else:
    filtered_price = close  # sortie de plage: signal
```

## Signaux
- **BUY** : Le prix filtré passe au-dessus du prix précédent ET du filtre de bruit
- **SELL** : Le prix filtré passe en dessous ET confirme la sortie de plage

## Trade-offs
| Range Period | Sensibilité | Filtrage du bruit |
|:---|:---|:---|
| Court (10-20) | Élevée, détecte les micro-tendances | Faible |
| Moyen (30-50) | Équilibrée | Bon |
| Long (60-100) | Faible, uniquement les macro-tendances | Excellent |

**Règle d'or** : Le Range Filter te dit QUAND le marché bouge. Un autre indicateur doit te dire DANS QUELLE DIRECTION.

*Guidé par documentation/SKILL.md — sections: TL;DR, Code, Trade-offs, Golden Rule.*
