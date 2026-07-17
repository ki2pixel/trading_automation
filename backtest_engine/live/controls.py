import os
import logging
from decimal import Decimal
from typing import Any, Optional

logger = logging.getLogger("papertrader")

class PreTradeControlError(ValueError):
    """Raised when an order violates the Pre-Trade Controls (ESMA RTS 6)."""
    pass

class PreTradeController:
    """
    Implements Pre-Trade Controls (PTC) for risk management (ESMA RTS 6 / MiFID II).
    Checks volumetric limits, notional limits, and price collars before orders are sent.
    """
    def __init__(
        self,
        max_trade_pct_nav: Decimal | None = None,
        max_asset_pct_nav: Decimal | None = None,
        price_collar_pct: Decimal | None = None,
    ) -> None:
        # B2-FIX: Read from environment with hardcoded fallback defaults
        self.max_trade_pct_nav = max_trade_pct_nav or Decimal(
            os.getenv("PTC_MAX_TRADE_PCT_NAV", "0.10")
        )
        self.max_asset_pct_nav = max_asset_pct_nav or Decimal(
            os.getenv("PTC_MAX_ASSET_PCT_NAV", "0.30")
        )
        self.price_collar_pct = price_collar_pct or Decimal(
            os.getenv("PTC_PRICE_COLLAR_PCT", "0.03")
        )

    def check_limits(
        self,
        ticker: str,
        quantity: Decimal,
        price: Decimal,
        current_nav: Decimal,
        current_position_qty: Decimal = Decimal("0"),
        reference_price: Optional[Decimal] = None
    ) -> None:
        """
        Validate the order parameters against PTC thresholds.
        Raises PreTradeControlError if any check fails.
        """
        if current_nav <= Decimal("0") or price <= Decimal("0"):
            raise PreTradeControlError("Fresh positive NAV and reference price are required")

        if reference_price is None or reference_price <= Decimal("0"):
            raise PreTradeControlError("Fresh independent reference price is required")

        # 1. Volumetric Check (NAV percentage)
        order_value = abs(quantity * price)
        trade_pct = order_value / current_nav
        if trade_pct > self.max_trade_pct_nav:
            msg = (
                f"[PTC] Volumetric Limit Violated: Order value {order_value:.2f} "
                f"is {trade_pct*100:.1f}% of NAV ({current_nav:.2f}), "
                f"exceeding max allowed {self.max_trade_pct_nav*100:.1f}%"
            )
            logger.error(msg)
            raise PreTradeControlError(msg)

        # 2. Notional Exposure Check (cumulated position value)
        expected_position_qty = current_position_qty + quantity
        expected_exposure = abs(expected_position_qty * price)
        exposure_pct = expected_exposure / current_nav
        if exposure_pct > self.max_asset_pct_nav:
            msg = (
                f"[PTC] Notional Exposure Limit Violated: Cumulative exposure "
                f"on {ticker} would be {expected_exposure:.2f} ({exposure_pct*100:.1f}% of NAV), "
                f"exceeding max allowed {self.max_asset_pct_nav*100:.1f}%"
            )
            logger.error(msg)
            raise PreTradeControlError(msg)

        # 3. Price Collar Check (deviation from reference price)
        if reference_price and reference_price > 0:
            price_deviation = abs(price - reference_price) / reference_price
            if price_deviation > self.price_collar_pct:
                msg = (
                    f"[PTC] Price Collar Violated: Order price {price:.4f} "
                    f"deviates by {price_deviation*100:.2f}% from reference price {reference_price:.4f}, "
                    f"exceeding max allowed {self.price_collar_pct*100:.1f}%"
                )
                logger.error(msg)
                raise PreTradeControlError(msg)

        logger.info(f"[PTC] Order for {ticker} (value: {order_value:.2f}) passed all pre-trade controls.")
