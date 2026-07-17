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
        # Step 0: Check for any unfinished conversion order in database first (idempotency recovery)
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT client_order_id, broker_order_id, status, qty_usdc, filled_qty_eur, avg_fill_price, fee_usdc, error_message, dry_run, created_at
                    FROM conversion_audit_log
                    WHERE status IN ('PENDING', 'SUBMITTED', 'RECONCILIATION_PENDING', 'PARTIAL')
                    LIMIT 1
                """)
                row = cur.fetchone()
                if row:
                    current_status = ConversionOrderStatus(row[2])
                    logger.info(
                        "[SpotRouter] Found unfinished order %s in status %s. Recovering...",
                        row[0], current_status.value,
                    )
                    unfinished_order = ConversionOrder(
                        client_order_id=row[0],
                        broker_order_id=row[1],
                        status=current_status,
                        qty_usdc=Decimal(str(row[3])),
                        filled_qty_eur=Decimal(str(row[4])),
                        avg_fill_price=Decimal(str(row[5])),
                        fee_usdc=Decimal(str(row[6])),
                        error_message=row[7],
                        dry_run=row[8],
                        submitted_at=row[9] if row[9] else datetime.now(timezone.utc),
                    )
                    # J1-FIX: Track how many times we've attempted reconciliation
                    if current_status == ConversionOrderStatus.RECONCILIATION_PENDING:
                        unfinished_order.reconciliation_attempts += 1
                        if unfinished_order.reconciliation_attempts >= unfinished_order.max_reconciliation_attempts:
                            logger.error(
                                "[SpotRouter] Order %s exceeded max reconciliation attempts (%d). Forcing FAILED.",
                                unfinished_order.client_order_id,
                                unfinished_order.max_reconciliation_attempts,
                            )
                            unfinished_order.status = ConversionOrderStatus.FAILED
                            unfinished_order.error_message = (
                                f"Exceeded {unfinished_order.max_reconciliation_attempts} reconciliation attempts "
                                f"with status {current_status.value}"
                            )
                            self._log_conversion(conn, unfinished_order, dry_run=unfinished_order.dry_run)
                            return unfinished_order
                    recovered_order = self._recover_order_state(unfinished_order)
                    self._log_conversion(conn, recovered_order, dry_run=recovered_order.dry_run)
                    if recovered_order.status == ConversionOrderStatus.FILLED:
                        self.accumulator.drain(conn, recovered_order.client_order_id)
                    elif recovered_order.status == ConversionOrderStatus.RECONCILIATION_PENDING:
                        logger.warning(
                            "[SpotRouter] Order %s remains in RECONCILIATION_PENDING. "
                            "Will retry at next cycle (attempt %d/%d).",
                            recovered_order.client_order_id,
                            recovered_order.reconciliation_attempts,
                            recovered_order.max_reconciliation_attempts,
                        )
                    return recovered_order
        except Exception as e:
            logger.error(f"[SpotRouter] Failed to check/recover unfinished orders: {e}")

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
                "[SpotRouter] Conversion locked by margin simulator. Skipping."
            )
            return None

        margin_check = self.margin_sim.check_conversion_safety(balance)
        if not margin_check.is_safe:
            self._log_blocked_conversion(conn, balance, margin_check)
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
            # Do NOT drain accumulator in dry-run!
            self._log_conversion(conn, order, dry_run=True)
            return order

        # Live execution
        # First, persist the order with PENDING status before calling Bybit API
        order.status = ConversionOrderStatus.PENDING
        self._log_conversion(conn, order)

        order = self._submit_order(conn, order)

        if order.status == ConversionOrderStatus.FILLED:
            self.accumulator.drain(conn, order.client_order_id)
            self._log_conversion(conn, order)
        elif order.status == ConversionOrderStatus.RECONCILIATION_PENDING:
            # J1-FIX: Explicit retry via next cycle — Step 0 will attempt recovery
            order.reconciliation_attempts += 1
            if order.reconciliation_attempts >= order.max_reconciliation_attempts:
                logger.error(
                    "[SpotRouter] Order %s exceeded max reconciliation attempts (%d). Forcing FAILED.",
                    order.client_order_id, order.max_reconciliation_attempts,
                )
                order.status = ConversionOrderStatus.FAILED
                order.error_message = (
                    f"Exceeded {order.max_reconciliation_attempts} reconciliation attempts"
                )
            self._log_conversion(conn, order)
        elif order.status in (
            ConversionOrderStatus.REJECTED,
            ConversionOrderStatus.FAILED,
            ConversionOrderStatus.SUBMITTED,
            ConversionOrderStatus.PARTIAL,
        ):
            self._log_conversion(conn, order)

        return order

    def _submit_order(self, conn, order: ConversionOrder) -> ConversionOrder:
        """
        Submits the order to Bybit V5 POST /v5/order/create.
        Implements retry with idempotent client_order_id.
        """
        # Pre-Trade Controls check (ESMA RTS 6 compliance)
        from backtest_engine.live.controls import PreTradeController, PreTradeControlError
        from backtest_engine.live.connection import get_db_connection

        # In actual execution, we fail fast instead of using dummy/fallback values
        nav = None
        price = None

        try:
            with get_db_connection() as db_conn:
                with db_conn.cursor() as cur:
                    cur.execute("SELECT total_nav FROM paper_portfolio_balance WHERE source = 'bybit'")
                    row = cur.fetchone()
                    if row and row[0] is not None:
                        nav = Decimal(str(row[0]))

                    cur.execute("SELECT price FROM live_prices WHERE ticker = 'eurusd'")
                    row = cur.fetchone()
                    if row and row[0] is not None:
                        price = Decimal(str(row[0]))
        except Exception as dbe:
            logger.error(f"[SpotRouter] Failed to query DB for Pre-Trade Controls: {dbe}")
            order.status = ConversionOrderStatus.FAILED
            order.error_message = f"Pre-Trade Controls DB query failed: {dbe}"
            return order

        if nav is None or nav <= Decimal("0") or price is None or price <= Decimal("0"):
            logger.error(f"[SpotRouter] PTC Check Failed: Fresh positive NAV ({nav}) and price ({price}) are required.")
            order.status = ConversionOrderStatus.REJECTED
            order.error_message = f"Pre-Trade Controls Check Failed: invalid NAV ({nav}) or price ({price})"
            return order

        try:
            ptc = PreTradeController()
            ptc.check_limits(
                ticker=order.symbol,
                quantity=order.qty_usdc / price,
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
                # J2-FIX: Do NOT persist SUBMITTED before the API call.
                # The order is already persisted as PENDING (from try_convert).
                # Only transition to SUBMITTED after successful API response.

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
                    # J2-FIX: Transition to SUBMITTED only after confirmed API success
                    order.status = ConversionOrderStatus.SUBMITTED
                    self._log_conversion(conn, order)

                    # Confirm execution status from the broker via reconciliation (non-presumptive)
                    logger.info(
                        f"[SpotRouter] Order submitted successfully: {order.client_order_id} "
                        f"→ Bybit ID: {order.broker_order_id}. Confirming status..."
                    )
                    return self._recover_order_state(order)
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

        # Reconcile status to check if it actually succeeded despite the exceptions/errors
        return self._recover_order_state(order)

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
                    order.filled_at = datetime.now(timezone.utc)
                elif bybit_status == "PartiallyFilled":
                    order.status = ConversionOrderStatus.PARTIAL
                    order.filled_qty_eur = Decimal(
                        existing.get("cumExecQty", "0")
                    )
                    order.avg_fill_price = Decimal(
                        existing.get("avgPrice", "0")
                    )
                elif bybit_status in ("Cancelled", "Rejected"):
                    order.status = ConversionOrderStatus.CANCELED
                else:
                    if order.submitted_at:
                        elapsed = (datetime.now(timezone.utc) - order.submitted_at).total_seconds()
                        if elapsed > 900:  # 15 minutes
                            order.status = ConversionOrderStatus.FAILED
                            order.error_message = f"TTL de réconciliation expiré (15min). Broker status was: {bybit_status}"
                            logger.error(f"[SpotRouter] Order {order.client_order_id} failed: {order.error_message}")
                        elif elapsed > 300:  # 5 minutes
                            order.status = ConversionOrderStatus.RECONCILIATION_PENDING
                            logger.error(f"[SpotRouter] ALERT: Order {order.client_order_id} status '{bybit_status}' unknown after 5m. Pending reconciliation.")
                        elif elapsed > 60:   # 1 minute
                            order.status = ConversionOrderStatus.RECONCILIATION_PENDING
                            logger.warning(f"[SpotRouter] Order {order.client_order_id} status '{bybit_status}' unknown after 1m. Pending reconciliation.")
                        else:
                            order.status = ConversionOrderStatus.SUBMITTED
                    else:
                        order.status = ConversionOrderStatus.SUBMITTED
            else:
                # Si l'ordre n'est pas trouvé chez le courtier et qu'on a eu une exception, il est FAILED
                if order.status == ConversionOrderStatus.PENDING:
                    order.status = ConversionOrderStatus.FAILED
                    order.error_message = "Order not found on broker and submission failed."
                elif order.status in (ConversionOrderStatus.SUBMITTED, ConversionOrderStatus.RECONCILIATION_PENDING):
                    if order.submitted_at:
                        elapsed = (datetime.now(timezone.utc) - order.submitted_at).total_seconds()
                        if elapsed > 900:
                            order.status = ConversionOrderStatus.FAILED
                            order.error_message = "TTL de réconciliation expiré (15min). Order not found."
                            logger.error(f"[SpotRouter] Order {order.client_order_id} failed: TTL expired.")
                        elif elapsed > 300:
                            order.status = ConversionOrderStatus.RECONCILIATION_PENDING
                            logger.error(f"[SpotRouter] ALERT: Order {order.client_order_id} not found after 5m. Pending reconciliation.")
                        elif elapsed > 60:
                            order.status = ConversionOrderStatus.RECONCILIATION_PENDING
                            logger.warning(f"[SpotRouter] Order {order.client_order_id} not found after 1m. Pending reconciliation.")
                        else:
                            order.status = ConversionOrderStatus.SUBMITTED
                    else:
                        order.status = ConversionOrderStatus.SUBMITTED

        except Exception as e:
            logger.error(f"[SpotRouter] Recovery failed: {e}")
            # Do not overwrite a prior SUBMITTED state with FAILED if we just had a temporary network issue on GET
            if order.status not in (ConversionOrderStatus.SUBMITTED, ConversionOrderStatus.RECONCILIATION_PENDING, ConversionOrderStatus.PARTIAL):
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

        # Persist to DB using UPSERT to prevent unique constraint violation on client_order_id
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO conversion_audit_log
                    (client_order_id, broker_order_id, status, qty_usdc,
                     filled_qty_eur, avg_fill_price, fee_usdc,
                     error_message, dry_run, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (client_order_id) DO UPDATE SET
                        broker_order_id = EXCLUDED.broker_order_id,
                        status = EXCLUDED.status,
                        qty_usdc = EXCLUDED.qty_usdc,
                        filled_qty_eur = EXCLUDED.filled_qty_eur,
                        avg_fill_price = EXCLUDED.avg_fill_price,
                        fee_usdc = EXCLUDED.fee_usdc,
                        error_message = EXCLUDED.error_message,
                        dry_run = EXCLUDED.dry_run;
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

    def _log_blocked_conversion(self, conn, amount, margin_check) -> None:
        """J4-FIX: Persist blocked conversion to both logger AND DB audit trail."""
        log_entry = {
            "event": "CONVERSION_BLOCKED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "amount_usdc": str(amount),
            "reason": margin_check.reason,
            "equity": str(margin_check.margin_state.total_equity),
            "maintenance_margin": str(margin_check.margin_state.total_maintenance_margin),
            "headroom": str(margin_check.headroom),
        }
        logger.warning(f"[AUDIT] {json.dumps(log_entry)}")

        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO conversion_audit_log
                    (client_order_id, status, qty_usdc, error_message, dry_run, created_at)
                    VALUES (%s, 'BLOCKED', %s, %s, FALSE, %s)
                    """,
                    (
                        f"blocked-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                        amount,
                        margin_check.reason,
                        datetime.now(timezone.utc),
                    ),
                )
            conn.commit()
        except Exception as e:
            logger.error("[SpotRouter] Failed to persist blocked conversion audit: %s", e)
