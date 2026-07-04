---
name: "execution-order-routing"
description: "Expert interaction courtiers, routage d'ordres et exécution live"
---

# Spécialisation: execution-order-routing

## 1. Rôle et Objectifs
Cette spécialisation concerne la traduction de décisions de trading abstraites en ordres concrets sur les marchés réels. C'est la couche la plus basse et la plus critique vis-à-vis des interactions externes. Elle gère la communication avec l'API des brokers (ex: Trading 212), la création des ordres, la surveillance de leur cycle de vie et la synchronisation locale de l'état du portefeuille.

## 2. Principes Fondamentaux & Contraintes

- **Machine à États (FSM)**: Un ordre a un cycle de vie strict. Il ne peut jamais passer magiquement de `Submitted` à `Canceled` sans validation par l'exchange. Gérer les états: `New`, `Pending`, `Filled`, `PartiallyFilled`, `Canceled`, `Rejected`.
- **Tolérance aux Pannes & Idempotence**: Si le script plante juste après avoir envoyé un ordre `Buy`, au redémarrage, il doit vérifier le statut de cet ordre via l'API pour éviter d'acheter une deuxième fois (Double Spend). Utiliser un `client_order_id` unique généré localement.
- **Routage Actif**: Si on supporte plusieurs courtiers, cette couche doit pouvoir choisir vers où diriger l'ordre selon la commission, la liquidité ou la disponibilité.
- **Types d'Ordres**: Préférer les Limit Orders pour contrôler le slippage, sauf cas de sortie d'urgence absolue où un Market Order est requis.
- **Précision Financière (Live)**: L'utilisation de `float` est **strictement interdite** pour représenter des prix, des quantités ou des montants dans ce module. Utilisez toujours `decimal.Decimal`.
- **Transactional Logging**: Chaque exécution Live d'un ordre doit être tracée par un logging transactionnel structuré (format JSON) pour faciliter l'audit, la réconciliation et le calcul des performances réelles.

## 3. Schémas de Référence (Patterns)

### A. Cycle de Vie d'un Ordre
```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal

class OrderStatus(Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"

@dataclass
class TradeOrder:
    internal_id: str
    symbol: str
    qty: Decimal
    is_buy: bool
    status: OrderStatus = OrderStatus.PENDING
    broker_id: Optional[str] = None
    limit_price: Optional[Decimal] = None
```

### B. Soumission d'Ordre Sécurisée avec Vérification
```python
import logging
import asyncio
from httpx import HTTPError, RequestError, TimeoutException

logger = logging.getLogger(__name__)

class SignalExecutionError(Exception):
    """Exception levée en cas d'échec de l'évaluation ou de l'exécution d'un signal."""
    pass

async def submit_order_safely(broker_client, order: TradeOrder) -> TradeOrder:
    """
    Soumet un ordre avec vérification du statut immédiat pour éviter les ordres perdus.
    Utilise un timeout explicite de 10s et gère les exceptions réseau spécifiques.
    """
    try:
        # Envoi à l'API du broker avec un timeout strict
        response = await broker_client.place_order(
            symbol=order.symbol,
            qty=order.qty,
            side="BUY" if order.is_buy else "SELL",
            type="LIMIT" if order.limit_price else "MARKET",
            limitPrice=order.limit_price,
            timeInForce="GTC",
            timeout=10.0  # Timeout explicite et centralisé (10s par défaut)
        )
        
        order.broker_id = response.get("order_id")
        order.status = OrderStatus.SUBMITTED
        logger.info(f"Ordre {order.internal_id} soumis avec succès: {order.broker_id}")
        
    except (TimeoutException, RequestError) as e:
        order.status = OrderStatus.REJECTED
        logger.exception(f"Timeout ou erreur réseau lors de la soumission de l'ordre {order.internal_id}")
        raise SignalExecutionError(f"Échec réseau lors de la soumission: {e}") from e
    except HTTPError as e:
        order.status = OrderStatus.REJECTED
        logger.exception(f"Erreur API HTTP broker lors de la soumission de l'ordre {order.internal_id}")
        raise SignalExecutionError(f"Erreur API broker: {e}") from e
    except Exception as e:
        order.status = OrderStatus.REJECTED
        logger.exception(f"Erreur inattendue et non gérée lors de la soumission de l'ordre {order.internal_id}")
        raise SignalExecutionError(f"Erreur inattendue de soumission d'ordre: {e}") from e
        
    return order
```

## 4. Pièges à Éviter (Anti-Patterns)
- ❌ **Boucle Active sur le Statut**: Faire du "polling" toutes les millisecondes pour voir si un ordre est exécuté. Privilégier les WebHooks ou les WebSockets si le broker le permet, sinon utiliser un intervalle de polling raisonnable (backoff).
- ❌ Hardcoder les identifiants d'API. Ils doivent toujours être isolés dans les configurations de l'environnement (et récupérés selon codingstandards.md).
- ❌ Ignorer les "Partial Fills" (exécutions partielles). Un algorithme naïf peut planter si un ordre de 100 actions n'est rempli qu'à 50%.

## 5. Interactions avec les autres Skills
- Reçoit les instructions finalisées et dimensionnées depuis `risk-money-management`.
- Utilise les guidelines de `trading212-api` pour interagir spécifiquement avec ce broker particulier.
