import os
from typing import List, Dict, Any, Optional
from backtest_engine.live.trading212.client import Trading212Client

class Trading212PositionTracker:
    """Position tracker wrapper that excludes micro-positions used for price monitoring."""

    def __init__(self, client: Trading212Client, micro_threshold: Optional[float] = None):
        self.client = client
        if micro_threshold is not None:
            self.micro_threshold = micro_threshold
        else:
            try:
                self.micro_threshold = float(os.getenv("T212_MICRO_POSITION_THRESHOLD") or os.getenv("T212_BOOTSTRAP_QTY") or "0.2")
            except (ValueError, TypeError):
                self.micro_threshold = 0.2

    def get_real_positions(self) -> List[Dict[str, Any]]:
        """Retrieves open positions from Trading 212 and filters out micro-positions."""
        try:
            positions = self.client.get_positions()
        except Exception as e:
            print(f"[PositionTracker] Error fetching positions: {e}")
            raise e
            
        real_positions = []
        for pos in positions:
            if self._is_micro_position(pos):
                continue
            real_positions.append(pos)
                
        return real_positions

    def get_micro_positions(self) -> List[Dict[str, Any]]:
        """Retrieves only the micro-positions used for price monitoring."""
        try:
            positions = self.client.get_positions()
        except Exception as e:
            print(f"[PositionTracker] Error fetching positions: {e}")
            raise e
            
        micro_positions = []
        for pos in positions:
            if self._is_micro_position(pos):
                micro_positions.append(pos)
        return micro_positions

    def _is_micro_position(self, pos: Dict[str, Any]) -> bool:
        """Helper to determine if a position is a micro monitoring position."""
        quantity = pos.get("quantity")
        if quantity is None:
            return False
            
        try:
            qty = float(quantity)
        except (ValueError, TypeError):
            return False

        # 1. Quantity-based check
        if qty <= self.micro_threshold + 1e-9:
            return True

        # 2. Value-based check (under 2.0 units of account currency)
        wallet_impact = pos.get("walletImpact")
        if wallet_impact and isinstance(wallet_impact, dict):
            val = wallet_impact.get("currentValue")
            if val is not None:
                try:
                    if float(val) < 2.0:
                        return True
                except (ValueError, TypeError):
                    pass

        return False
