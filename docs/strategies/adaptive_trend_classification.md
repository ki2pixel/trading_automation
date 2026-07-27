# Adaptive Trend Classification — Classification Adaptative de Tendance

**TL;DR**: Pondère 6 types de moyennes mobiles (SMA, EMA, WMA, HMA, ALMA, KAMA) pour classifier la tendance. Chaque MA vote; la classification finale est la somme pondérée de leurs signaux normalisés.

---

Une seule MA donne une vision biaisée du marché. La SMA est lente mais stable. L'EMA est réactive mais bruyante. La KAMA s'adapte à la volatilité. Plutôt que choisir, cette stratégie fait voter les 6 et pondère leurs réponses.

## Architecture
```
close → SMA(period) ────┐
close → EMA(period) ────┤
close → WMA(period) ────┤
close → HMA(period) ────┼─→ Vote pondéré → Classification (Bull/Bear/Neutral)
close → ALMA(period) ───┤
close → KAMA(period) ───┘
```

## Classes de tendance
- **Bull** : Majorité pondérée des MAs en hausse
- **Bear** : Majorité pondérée des MAs en baisse
- **Neutral** : Pas de consensus clair — pas de trade

## Signaux
- **BUY** : Classification Bull + confirmation momentum
- **SELL** : Classification Bear + confirmation momentum

## Trade-offs
| Approche | Robustesse | Latence |
|:---|:---|:---|
| **MA unique** | Faible — un seul angle mort | Variable |
| **Vote 6 MAs** | Élevée — consensus requis pour agir | Acceptable |

**Règle d'or** : Si 6 MAs ne sont pas d'accord, tu ne devrais pas trader. Le consensus est la seule information fiable.

*Guidé par documentation/SKILL.md — sections: TL;DR, Architecture, Trade-offs, Golden Rule.*
