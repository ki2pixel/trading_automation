# Noise Boundary Kernel — Noyau de Détection de Frontière de Bruit

**TL;DR**: Version optimisée et "kernelisée" du Noise Boundary Intraday. Utilise des noyaux mathématiques (kernel functions) pour estimer les frontières de bruit avec une précision accrue, conçue pour être pré-scannée par VectorBT.

---

Le Noise Boundary classique calcule des bandes de bruit empiriques. Le Kernel va plus loin en appliquant des fonctions de noyau (gaussien, Epanechnikov) pour estimer la distribution de densité du bruit. Résultat : des frontières plus précises, particulièrement en pré-scan VectorBT.

## Mécanique
```python
# Noyau gaussien pour estimation de densité du bruit
bandwidth = silverman_bandwidth(returns)
noise_density = gaussian_kde(returns, bandwidth)
upper_boundary = close * (1 + noise_density.ppf(0.95))
lower_boundary = close * (1 - noise_density.ppf(0.95))
```

## Signaux
- **BUY** : Close > upper_boundary (sortie haussière de la zone de bruit)
- **SELL** : Close < lower_boundary (sortie baissière de la zone de bruit)

## Trade-offs
| Méthode | Précision frontières | Complexité |
|:---|:---|:---|
| Empirique (classique) | Bonne | Faible |
| Kernel | Excellente, densité estimée | Élevée (KDE) |

**Règle d'or** : Connaître la distribution du bruit est plus important que connaître le signal. Quand tu sais ce qui est "normal", tout le reste est exploitable.

*Guidé par documentation/SKILL.md — sections: TL;DR, Code, Trade-offs, Golden Rule.*
