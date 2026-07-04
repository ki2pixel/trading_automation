"""
Spot Order Router – Executes USDC→EUR conversions on Bybit Spot V5.

Implements:
- FSM lifecycle (execution-order-routing skill)
- Idempotent submission via client_order_id (anti-double-spend)
- Transactional JSON logging for audit
- Pre-trade margin check integration (risk-money-management skill)
"""
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional
import json
import logging

from .order_types import ConversionOrder, ConversionOrderStatus
from .margin_simulator import UTAMarginSimulator
from .accumulator import AccumulatorBuffer

logger = logging.getLogger("bybit.conversion")


class SpotConversionRouter:
    """
    Orchestrates the full conversion pipeline:
    1. Check accumulator threshold
    2. Run margin simulation
    3. Submit spot order
    4. Track order lifecycle (FSM)
    5. Drain accumulator on success
    """

    def __init__(
        self,
        bybit_client,
        accumulator: AccumulatorBuffer,
        margin_simulator: UTAMarginSimulator,
        dry_run: bool = True,  # Safety: dry-run by default
    ):
        self.client = bybit_client
        self.accumulator = accumulator
        self.margin_sim = margin_simulator
        self.dry_run = dry_run

    def try_convert(self, conn) -> Optional[ConversionOrder]:
        """
        Main entry point: attempts a conversion cycle.
        Returns the ConversionOrder if executed, None otherwise.
        """
        # Step 1: Check accumulator threshold
        should_trigger, balance = self.accumulator.should_trigger(conn)
        if not should_trigger:
            logger.debug(
                f"[SpotRouter] Buffer below threshold: "
                f"{balance}/{self.accumulator.threshold} USDC"
            )
            return None

        # Step 2: Pre-trade margin check
        if self.margin_sim.is_locked:
            logger.warning(
                "[SpotRouter] Conversion locked by margin simulator. "
                "Skipping."
            )
            return None

        margin_check = self.margin_sim.check_conversion_safety(balance)
        if not margin_check.is_safe:
            self._log_blocked_conversion(balance, margin_check)
            return None

        # Step 3: Create and submit order
        order = ConversionOrder(qty_usdc=balance)
        
        if self.dry_run:
            logger.info(
                f"[SpotRouter] DRY-RUN: Would submit conversion order: "
                f"{order.qty_usdc} USDC → EUR on {order.symbol}. "
                f"Payload: {json.dumps(order.to_bybit_payload())}"
            )
            order.status = ConversionOrderStatus.FILLED  # Simulate success
            order.filled_qty_eur = balance  # Approximate
            self.accumulator.drain(conn, order.client_order_id)
            self._log_conversion(conn, order, dry_run=True)
            return order

        # Live execution
        order = self._submit_order(order)
        
        if order.status == ConversionOrderStatus.FILLED:
            self.accumulator.drain(conn, order.client_order_id)
            self._log_conversion(conn, order)
        elif order.status in (
            ConversionOrderStatus.REJECTED,
            ConversionOrderStatus.FAILED
        ):
            self._log_conversion(conn, order)
        
        return order

    def _submit_order(self, order: ConversionOrder) -> ConversionOrder:
        """
        Submits the order to Bybit V5 POST /v5/order/create.
        Implements retry with idempotent client_order_id.
        """
        # Pre-Trade Controls check (ESMA RTS 6 compliance)
        from backtest_engine.live.controls import PreTradeController, PreTradeControlError
        from backtest_engine.live.connection import get_db_connection
        
        nav = Decimal("100000.0")
        price = Decimal("1.08") # Default fallback for EURUSDC
        
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT total_nav FROM paper_portfolio_balance WHERE source = 'bybit'")
                    row = cur.fetchone()
                    if row and row[0] is not None:
                        nav = Decimal(str(row[0]))
                        
                    cur.execute("SELECT price FROM live_prices WHERE ticker = 'eurusd'")
                    row = cur.fetchone()
                    if row and row[0] is not None:
                        price = Decimal(str(row[0]))
        except Exception as dbe:
            logger.warning(f"[SpotRouter] PTC warning: Failed to query database: {dbe}")
            
        try:
            ptc = PreTradeController()
            ptc.check_limits(
                ticker=order.symbol,
                quantity=order.qty_usdc / price if price > 0 else order.qty_usdc,
                price=price,
                current_nav=nav,
                current_position_qty=Decimal("0"),
                reference_price=price
            )
        except PreTradeControlError as ptce:
            order.status = ConversionOrderStatus.REJECTED
            order.error_message = str(ptce)
            logger.error(f"[SpotRouter] Order REJECTED by Pre-Trade Controls: {ptce}")
            return order

        payload = order.to_bybit_payload()
        
        for attempt in range(order.max_retries):
            try:
                order.submitted_at = datetime.now(timezone.utc)
                order.status = ConversionOrderStatus.SUBMITTED
                
                response = self.client._request(
                    "POST",
                    "/v5/order/create",
                    json_data=payload,
                    signed=True
                )
                data = response.json()
                
                ret_code = data.get("retCode", -1)
                if ret_code == 0:
                    result = data.get("result", {})
                    order.broker_order_id = result.get("orderId")
                    order.status = ConversionOrderStatus.FILLED
                    order.filled_at = datetime.now(timezone.utc)
                    
                    logger.info(
                        f"[SpotRouter] Order FILLED: {order.client_order_id} "
                        f"→ Bybit ID: {order.broker_order_id}"
                    )
                    return order
                else:
                    error_msg = data.get("retMsg", "Unknown error")
                    order.error_message = f"retCode={ret_code}: {error_msg}"
                    order.retry_count = attempt + 1
                    
                    # Check for duplicate order (idempotence check)
                    if ret_code == 110071:  # Duplicate orderLinkId
                        logger.warning(
                            f"[SpotRouter] Duplicate order detected: "
                            f"{order.client_order_id}. Recovering state..."
                        )
                        return self._recover_order_state(order)
                    
                    logger.warning(
                        f"[SpotRouter] Order rejected (attempt {attempt+1}): "
                        f"{order.error_message}"
                    )
                    
            except Exception as e:
                order.error_message = str(e)
                order.retry_count = attempt + 1
                logger.error(
                    f"[SpotRouter] Submit failed (attempt {attempt+1}): {e}"
                )

        order.status = ConversionOrderStatus.FAILED
        return order

    def _recover_order_state(self, order: ConversionOrder) -> ConversionOrder:
        """
        Récupère l'état d'un ordre existant via son orderLinkId.
        Anti-double-spend: vérifie si l'ordre a déjà été exécuté.
        """
        try:
            # 1. Tenter de récupérer depuis les ordres actifs (realtime)
            response = self.client._request(
                "GET",
                "/v5/order/realtime",
                params={
                    "category": "spot",
                    "orderLinkId": order.client_order_id,
                },
                signed=True
            )
            data = response.json()
            orders = data.get("result", {}).get("list", [])
            
            # 2. Si non trouvé, chercher dans l'historique (cas d'ordre déjà rempli et archivé)
            if not orders:
                response = self.client._request(
                    "GET",
                    "/v5/order/history",
                    params={
                        "category": "spot",
                        "orderLinkId": order.client_order_id,
                    },
                    signed=True
                )
                data = response.json()
                orders = data.get("result", {}).get("list", [])
            
            if orders:
                existing = orders[0]
                bybit_status = existing.get("orderStatus", "")
                order.broker_order_id = existing.get("orderId")
                
                if bybit_status == "Filled":
                    order.status = ConversionOrderStatus.FILLED
                    order.filled_qty_eur = Decimal(
                        existing.get("cumExecQty", "0")
                    )
                    order.avg_fill_price = Decimal(
                        existing.get("avgPrice", "0")
                    )
                elif bybit_status == "PartiallyFilled":
                    order.status = ConversionOrderStatus.PARTIAL
                elif bybit_status in ("Cancelled", "Rejected"):
                    order.status = ConversionOrderStatus.CANCELED
                    
        except Exception as e:
            logger.error(f"[SpotRouter] Recovery failed: {e}")
            order.status = ConversionOrderStatus.FAILED
            order.error_message = f"Recovery failed: {e}"
        
        return order

    def _log_conversion(
        self, conn, order: ConversionOrder, dry_run: bool = False
    ) -> None:
        """Logging transactionnel structuré (JSON) pour audit."""
        log_entry = {
            "event": "CONVERSION_EXECUTED" if not dry_run else "CONVERSION_DRY_RUN",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "client_order_id": order.client_order_id,
            "broker_order_id": order.broker_order_id,
            "status": order.status.value,
            "qty_usdc": str(order.qty_usdc),
            "filled_qty_eur": str(order.filled_qty_eur),
            "avg_fill_price": str(order.avg_fill_price),
            "fee_usdc": str(order.fee_usdc),
            "error": order.error_message,
            "dry_run": dry_run,
        }
        logger.info(f"[AUDIT] {json.dumps(log_entry)}")
        
        # Persist to DB
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO conversion_audit_log 
                    (client_order_id, broker_order_id, status, qty_usdc,
                     filled_qty_eur, avg_fill_price, fee_usdc, 
                     error_message, dry_run, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    order.client_order_id, order.broker_order_id,
                    order.status.value, order.qty_usdc,
                    order.filled_qty_eur, order.avg_fill_price,
                    order.fee_usdc, order.error_message, dry_run,
                    datetime.now(timezone.utc)
                ))
            conn.commit()
        except Exception as e:
            logger.error(f"[SpotRouter] Failed to persist audit log: {e}")

    def _log_blocked_conversion(self, amount, margin_check) -> None:
        """Log détaillé lorsqu'une conversion est bloquée par le Risk Controller."""
        logger.warning(
            f"[SpotRouter] CONVERSION BLOCKED: {amount} USDC. "
            f"Reason: {margin_check.reason}. "
            f"Equity: {margin_check.margin_state.total_equity}, "
            f"MM: {margin_check.margin_state.total_maintenance_margin}, "
            f"Headroom: {margin_check.headroom}"
        )
