"""
Order types for the Bybit Spot conversion pipeline.
Implements the FSM (Finite State Machine) from the execution-order-routing skill.
All monetary values use Decimal – float is strictly prohibited.
"""
from enum import Enum
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
from datetime import datetime, timezone
import uuid


class ConversionOrderStatus(Enum):
    """FSM states for a conversion order lifecycle."""
    PENDING = "PENDING"           # Created locally, not yet submitted
    SUBMITTED = "SUBMITTED"       # Sent to Bybit API, awaiting fill
    FILLED = "FILLED"             # Fully executed
    PARTIAL = "PARTIAL"           # Partially filled
    CANCELED = "CANCELED"         # Canceled by Bybit or timeout
    REJECTED = "REJECTED"         # Rejected by pre-trade check or API
    FAILED = "FAILED"             # Unexpected error


@dataclass
class ConversionOrder:
    """
    Represents a USDC → EUR conversion order on Bybit Spot.
    
    Uses client_order_id for idempotence per execution-order-routing skill:
    'Si le script plante juste après avoir envoyé un ordre Buy, au redémarrage,
    il doit vérifier le statut de cet ordre via l'API pour éviter le Double Spend.'
    """
    # Identification
    client_order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    broker_order_id: Optional[str] = None
    
    # Order parameters (Decimal only)
    symbol: str = "EURUSDC"
    side: str = "Buy"            # Buy EUR with USDC
    order_type: str = "Market"
    qty_usdc: Decimal = Decimal("0")  # Amount of USDC to spend
    
    # Execution results
    status: ConversionOrderStatus = ConversionOrderStatus.PENDING
    filled_qty_eur: Decimal = Decimal("0")
    avg_fill_price: Decimal = Decimal("0")
    fee_usdc: Decimal = Decimal("0")
    
    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    
    # Error tracking
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def to_bybit_payload(self) -> dict:
        """
        Generates the exact JSON payload for POST /v5/order/create.
        marketUnit='quoteCoin' ensures qty is interpreted as USDC amount.
        """
        return {
            "category": "spot",
            "symbol": self.symbol,
            "side": self.side,
            "orderType": self.order_type,
            "qty": str(self.qty_usdc),
            "marketUnit": "quoteCoin",
            "orderLinkId": self.client_order_id,
        }
