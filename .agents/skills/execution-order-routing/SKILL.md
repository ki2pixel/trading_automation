---
name: "execution-order-routing"
description: "Expert interaction courtiers, routage d'ordres et exécution live"
---

# Spécialisation: execution-order-routing

## 1. Rôle et Objectifs
Cette spécialisation concerne la traduction de décisions de trading abstraites en ordres concrets sur les marchés réels. C'est la couche la plus basse et la plus critique vis-à-vis des interactions externes. Elle gère la communication avec l'API des brokers (ex: Trading 212), la création des ordres, la surveillance de leur cycle de vie et la synchronisation locale de l'état du portefeuille.

## 2. Principes Fondamentaux & Contraintes

- **Machine à États (FSM)**: Un ordre a un cycle de vie strict. Il ne peut jamais passer magiquement de `Submitted` à `Canceled` sans validation par l'exchange. Gérer les états: `PENDING`, `SUBMITTED`, `FILLED`, `PARTIAL`, `CANCELED`, `REJECTED`, `FAILED`.
- **Idempotence stricte (UUID v4)**: L'utilisation d'UUID v4 standardisés de 36 caractères est obligatoire pour l'identifiant client unique (`client_order_id` ou `orderLinkId`). En cas de retour d'erreur d'identifiant d'ordre existant (ex: code de retour de doublon `110071` sur Bybit), le routeur doit obligatoirement interroger l'état de l'ordre existant (`/v5/order/realtime` puis `/v5/order/history`) pour récupérer son statut réel et éviter un double spend.
- **Routage Actif & Timeouts**: Choisir le courtier adéquat selon la commission, la liquidité et la disponibilité. Chaque appel d'API vers le broker doit comporter un timeout réseau centralisé (ex: `NETWORK_TIMEOUT_DEFAULT = 10.0`).
- **Précision Financière (Live)**: L'utilisation de `float` est **strictement interdite** pour représenter des prix, des quantités ou des montants dans ce module. Utilisez toujours `decimal.Decimal` (ex: commissions Bybit Spot fixées à 0.1000%, Trading 212 à 0.0000%).
- **Transactional Logging**: Chaque exécution Live d'un ordre doit être tracée par un logging transactionnel structuré (format JSON) avec les clés suivantes : `timestamp_utc`, `order_id`, `symbole`, `quantité`, `prix`, `statut`.

## 3. Schémas de Référence (Patterns)

### A. Cycle de Vie d'un Ordre
```python
import uuid
from enum import Enum
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
from datetime import datetime, timezone

class OrderStatus(Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"

@dataclass
class TradeOrder:
    symbol: str
    qty: Decimal
    is_buy: bool
    client_order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    broker_order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    limit_price: Optional[Decimal] = None
```

### B. Soumission avec Idempotence et Récupération post-Duplicate/Timeout
```python
import logging
import json
from datetime import datetime, timezone
from decimal import Decimal

logger = logging.getLogger(__name__)

class SignalExecutionError(Exception):
    pass

async def submit_order_safely(broker_client, order: TradeOrder) -> TradeOrder:
    """
    Soumet un ordre avec validation d'idempotence et récupération de statut en cas de doublon.
    """
    try:
        # Envoi de l'ordre
        response = await broker_client.place_order(
            symbol=order.symbol,
            qty=str(order.qty),
            side="Buy" if order.is_buy else "Sell",
            order_type="Limit" if order.limit_price else "Market",
            limit_price=str(order.limit_price) if order.limit_price else None,
            client_order_id=order.client_order_id,
            timeout=10.0  # Timeout explicite centralisé
        )
        order.broker_order_id = response.get("order_id")
        order.status = OrderStatus.SUBMITTED
        
        # Transactional JSON Logging
        logger.info(json.dumps({
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "order_id": order.client_order_id,
            "symbole": order.symbol,
            "quantité": str(order.qty),
            "prix": str(order.limit_price) if order.limit_price else "MARKET",
            "statut": "SUBMITTED"
        }))
        
    except Exception as e:
        # En cas d'erreur indiquant un doublon d'ID client (ex: ret_code 110071 sur Bybit)
        if getattr(e, "ret_code", None) == 110071:
            logger.warning(f"Doublon d'ID client détecté pour {order.client_order_id}, récupération de l'état...")
            return await recover_order_state(broker_client, order)
        
        order.status = OrderStatus.FAILED
        raise SignalExecutionError(f"Échec de l'ordre: {e}") from e
        
    return order

async def recover_order_state(broker_client, order: TradeOrder) -> TradeOrder:
    """
    Interroge le courtier après un échec/doublon pour synchroniser l'état local de l'ordre.
    """
    try:
        # 1. Vérification des ordres actifs
        orders = await broker_client.get_active_orders(client_order_id=order.client_order_id)
        if not orders:
            # 2. Vérification de l'historique
            orders = await broker_client.get_order_history(client_order_id=order.client_order_id)
            
        if orders:
            existing = orders[0]
            order.broker_order_id = existing.get("order_id")
            bybit_status = existing.get("status")
            if bybit_status == "Filled":
                order.status = OrderStatus.FILLED
            elif bybit_status == "Canceled":
                order.status = OrderStatus.CANCELED
            else:
                order.status = OrderStatus.SUBMITTED
            
            logger.info(f"État de l'ordre récupéré avec succès : {order.status}")
            return order
    except Exception as e:
        logger.error(f"Échec de la récupération de l'ordre {order.client_order_id}: {e}")
        
    order.status = OrderStatus.FAILED
    return order
```

## 4. Pièges à Éviter (Anti-Patterns)
- ❌ **Boucle Active sur le Statut**: Faire du "polling" toutes les millisecondes pour voir si un ordre est exécuté. Privilégier les WebHooks ou les WebSockets si le broker le permet, sinon utiliser un intervalle de polling raisonnable (backoff).
- ❌ Hardcoder les identifiants d'API ou les variables de configuration.
- ❌ Ignorer les "Partial Fills" (exécutions partielles).
- ❌ Utiliser des floats pour les calculs d'exposition, commissions ou prix en Live.

## 5. Interactions avec les autres Skills
- Reçoit les instructions finalisées et dimensionnées depuis `risk-money-management`.
- Utilise les guidelines de `trading212-api` pour interagir spécifiquement avec ce broker particulier.

