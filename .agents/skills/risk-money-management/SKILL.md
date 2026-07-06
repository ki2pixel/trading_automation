---
name: "risk-money-management"
description: "Gardien du capital et contrôleur de l'exposition globale du portefeuille"
---

# Spécialisation: risk-money-management

## 1. Rôle et Objectifs
Cet agent est responsable de la gestion du risque financier. Il convertit un signal d'achat/vente théorique en une taille de position réelle (Position Sizing) en fonction du risque par trade, du capital disponible, de l'historique de performance (Kelly Criterion) et gère la logique de sortie d'urgence (Stop-Loss, coupe-circuits).

## 2. Principes Fondamentaux & Contraintes

- **Priorité à la Survie**: La règle numéro un est d'éviter le risque de ruine. Ne jamais engager une fraction du capital qui pourrait entraîner une perte insurmontable en cas de cygne noir (black swan).
- **Pre-Trade Checks (Marge et Exposition)**: Avant tout envoi d'ordre au courtier, des contrôles pré-trade synchrones doivent obligatoirement vérifier la marge disponible (MMR check > 1.2x, et utilisation du simulateur de marge UTA pour Bybit), l'exposition maximale autorisée par rapport au capital et l'absence de conflit d'ordre (ordres concurrents ou contradictoires sur le même ticker).
- **Position Sizing Dynamique (Decimal en Live)**: Calculer la taille de position de manière dynamique en fonction du risque par trade (ex: 1% de la NAV divisé par la distance au Stop-Loss). Tous les calculs financiers (marge, NAV, taille de position, prix) en Live et Paper Trading doivent utiliser exclusivement le type `decimal.Decimal` pour éviter les erreurs d'arrondis.
- **Circuit Breakers**: Arrêt global automatique en mode "Close-Only" (fermeture uniquement) dès que le Max Drawdown journalier autorisé est atteint ou en cas d'anomalie détectée du nombre de requêtes réseau par seconde (protection anti-bouclage).
- **Corrélations**: Empêcher le cumul d'exposition sur des actifs fortement corrélés.
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
