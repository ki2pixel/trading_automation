from typing import List, Dict, Any
from backtest_engine.live.trading212.client import Trading212Client

class Trading212PositionTracker:
    """Position tracker wrapper that excludes micro-positions used for price monitoring."""

    def __init__(self, client: Trading212Client, micro_threshold: float = 0.0001):
        self.client = client
        self.micro_threshold = micro_threshold

    def get_real_positions(self) -> List[Dict[str, Any]]:
        """Retrieves open positions from Trading 212 and filters out micro-positions of quantity <= 0.0001."""
        try:
            positions = self.client.get_positions()
        except Exception as e:
            print(f"[PositionTracker] Error fetching positions: {e}")
            raise e
            
        real_positions = []
        for pos in positions:
            quantity = pos.get("quantity")
            if quantity is not None:
                try:
                    qty = float(quantity)
                    # Skip micro monitoring positions (quantity <= threshold)
                    # Note: Using a small tolerance for floating point comparisons
                    if qty > self.micro_threshold + 1e-9:
                        real_positions.append(pos)
                except (ValueError, TypeError):
                    # In case parsing fails, keep it in real positions as a safety fallback
                    real_positions.append(pos)
            else:
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
            quantity = pos.get("quantity")
            if quantity is not None:
                try:
                    qty = float(quantity)
                    if qty <= self.micro_threshold + 1e-9:
                        micro_positions.append(pos)
                except (ValueError, TypeError):
                    pass
        return micro_positions
