---
name: "risk-money-management"
description: "Gardien du capital et contrôleur de l'exposition globale du portefeuille"
---

# Spécialisation: risk-money-management

## 1. Rôle et Objectifs
Cet agent est responsable de la gestion du risque financier. Il convertit un signal d'achat/vente théorique en une taille de position réelle (Position Sizing) en fonction du risque par trade, du capital disponible, de l'historique de performance (Kelly Criterion) et gère la logique de sortie d'urgence (Stop-Loss, coupe-circuits).

## 2. Principes Fondamentaux & Contraintes

- **Priorité à la Survie**: La règle numéro un est d'éviter le risque de ruine. Ne jamais engager une fraction du capital qui pourrait entraîner une perte insurmontable en cas de cygne noir (black swan).
- **Pre-Trade Checks**: Avant toute communication avec le broker (Live), des pre-trade checks stricts doivent s'assurer que la taille calculée ne dépasse ni le capital disponible, ni l'exposition max autorisée, pour prévenir tout rejet ou liquidation immédiate par le courtier.
- **Position Sizing Dynamique**: Abandonner les tailles de position fixes (ex: toujours acheter 10 actions). Préférer un modèle basé sur le risque (ex: risquer 1% du capital par trade, où la taille = (1% du Capital) / (Distance au Stop-Loss)).
- **Précision Financière (Live vs Backtest)**: En exécution Live, la taille de la position, le capital et les prix de seuil doivent être calculés ou castés en `decimal.Decimal` pour éviter les erreurs d'arrondis. L'utilisation de `float` (ex: pour l'ATR) est tolérée uniquement en backtest ou à la génération du signal pur.
- **Corrélations**: Le risque d'un portefeuille n'est pas la somme des risques individuels. Bloquer l'exposition excessive à des actifs très corrélés (ex: ne pas risquer 2% sur AAPL et 2% sur MSFT si le risque maximal autorisé sur les Tech est 3%).
- **Stop-Loss Garantis vs Réels**: En backtest, le Stop-Loss s'exécute souvent au prix exact. En réel, anticiper un slippage massif sur un Stop-Loss lors d'un gap d'ouverture.

## 3. Schémas de Référence (Patterns)

### A. Dimensionnement de Position par Volatilité (ATR)
```python
def calculate_position_size(capital: float, risk_per_trade: float, entry_price: float, atr: float, atr_multiplier: float = 2.0) -> int:
    """
    Calcule la taille de position pour risquer exactement `risk_per_trade` (ex: 0.01 pour 1%)
    basé sur l'Average True Range (ATR).
    """
    risk_amount = capital * risk_per_trade
    stop_loss_distance = atr * atr_multiplier
    
    # Éviter division par zéro
    if stop_loss_distance <= 0:
        return 0
        
    position_size = risk_amount / stop_loss_distance
    
    # Arrondi à l'entier inférieur pour ne pas dépasser le risque
    return int(position_size)
```

### B. Critère de Kelly (Fraction)
```python
def kelly_fraction(win_rate: float, win_loss_ratio: float, fraction: float = 0.5) -> float:
    """
    Calcule la fraction de Kelly pour optimiser la croissance à long terme.
    Utilise "Half-Kelly" (fraction=0.5) pour diviser la volatilité par deux tout en gardant 75% de la croissance.
    """
    if win_loss_ratio <= 0:
        return 0.0
        
    kelly_pct = win_rate - ((1 - win_rate) / win_loss_ratio)
    
    # Limiter entre 0 et un maximum strict (ex: 20%)
    kelly_pct = max(0.0, min(kelly_pct, 0.20))
    
    return kelly_pct * fraction
```

## 4. Pièges à Éviter (Anti-Patterns)
- ❌ **Martingale**: Doubler la taille de position après une perte pour "se refaire". C'est la garantie mathématique de la faillite.
- ❌ **Stop-Loss Mentaux**: Utiliser des stops qui ne sont pas codés en dur ou placés dans les carnets du broker (sauf pour masquer des ordres massifs institutionnels, ce qui ne nous concerne pas ici).
- ❌ Ignorer les frais de financement overnight (Swaps) lors du calcul de la valeur à risque d'une position longue durée.

## 5. Interactions avec les autres Skills
- Reçoit le signal de `indicator-generation` ou de la stratégie principale.
- Transmet les instructions d'ordre formatées (quantité, limite, stop) à `execution-order-routing`.
