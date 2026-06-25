import os
from typing import Set, List, Dict, Any
from backtest_engine.live.trading212.client import Trading212Client
from backtest_engine.live.trading212.resolver import Trading212TickerResolver

class Trading212Bootstrapper:
    """Bootstraps the portfolio by opening micro-positions for monitoring purposes."""

    def __init__(self, client: Trading212Client, resolver: Trading212TickerResolver):
        self.client = client
        self.resolver = resolver
        try:
            self.micro_qty = float(os.getenv("T212_BOOTSTRAP_QTY") or "0.0001")
        except (ValueError, TypeError):
            self.micro_qty = 0.0001

    def get_target_tickers(self) -> Set[str]:
        """Resolves all 21 target assets to their exact T212 tickers."""
        tickers = set()
        for asset in Trading212TickerResolver.STATIC_MAPPING.keys():
            try:
                ticker = self.resolver.resolve(asset)
                tickers.add(ticker)
            except Exception as e:
                print(f"[Bootstrapper] Error resolving asset {asset}: {e}")
        return tickers

    def bootstrap(self) -> List[str]:
        """Runs the bootstrap check and submits market buy orders for missing micro-positions."""
        target_tickers = self.get_target_tickers()
        print(f"[Bootstrapper] Starting bootstrap for {len(target_tickers)} target tickers.")
        
        # 1. Fetch current open positions
        try:
            positions = self.client.get_positions()
        except Exception as e:
            print(f"[Bootstrapper] Failed to retrieve open positions: {e}")
            return []
            
        held_tickers = set()
        for pos in positions:
            ticker = pos.get("instrument", {}).get("ticker")
            if ticker:
                held_tickers.add(ticker)
                
        # 2. Fetch current pending/NEW orders to avoid placing duplicates if market is closed
        try:
            orders = self.client.get_pending_orders()
        except Exception as e:
            print(f"[Bootstrapper] Failed to retrieve pending orders: {e}")
            orders = []
            
        pending_tickers = set()
        for order in orders:
            # Only consider buy orders that are active/waiting
            if order.get("side") == "BUY" and order.get("status") in ("NEW", "UNCONFIRMED", "LOCAL"):
                ticker = order.get("ticker")
                if ticker:
                    pending_tickers.add(ticker)

        # 3. Place market orders for target tickers that are not held and not pending
        placed_tickers = []
        for ticker in target_tickers:
            if ticker in held_tickers:
                print(f"[Bootstrapper] Ticker {ticker} is already held in portfolio. Skipping.")
                continue
            if ticker in pending_tickers:
                print(f"[Bootstrapper] Ticker {ticker} already has a pending buy order. Skipping.")
                continue
                
            print(f"[Bootstrapper] Ticker {ticker} is missing. Placing micro market buy order of {self.micro_qty} shares...")
            try:
                result = self._place_adaptive_market_order(ticker, self.micro_qty)
                print(f"[Bootstrapper] Placed market order for {ticker}: ID {result.get('id')} - Status {result.get('status')}")
                placed_tickers.append(ticker)
            except Exception as e:
                print(f"[Bootstrapper] Failed to place order for {ticker}: {e}")
                
        print(f"[Bootstrapper] Bootstrap complete. Placed {len(placed_tickers)} new micro-position orders.")
        return placed_tickers

    def _place_adaptive_market_order(self, ticker: str, quantity: float, precision: int = 8, depth: int = 0) -> Dict[str, Any]:
        """Places a market order and dynamically adapts to quantity/precision limits on errors."""
        if depth > 3:
            raise RuntimeError(f"Max adaptive order retries exceeded for {ticker}")
        
        qty = round(quantity, precision)
        
        try:
            return self.client.place_market_order(ticker, qty)
        except Exception as e:
            if hasattr(e, "response") and e.response is not None and e.response.status_code == 400:
                try:
                    err_data = e.response.json()
                    err_type = err_data.get("type", "")
                    err_detail = err_data.get("detail", "")
                    
                    # Case 1: Quantity is too small (Min Order Value limit)
                    if "min-quantity" in err_type or "must trade at least" in err_detail:
                        import re
                        match = re.search(r"must trade at least ([\d\.]+)", err_detail)
                        if match:
                            min_qty = float(match.group(1))
                            target_qty = min_qty + 1e-6
                            print(f"[Bootstrapper] Ticker {ticker} needs larger quantity. Re-trying with target_qty={target_qty}...")
                            return self._place_adaptive_market_order(ticker, target_qty, precision, depth + 1)
                            
                    # Case 2: Precision mismatch
                    if "quantity-precision" in err_type or "invalid quantity precision" in err_detail:
                        import re
                        match = re.search(r"invalid quantity precision (\d+)", err_detail)
                        if match:
                            allowed_precision = int(match.group(1))
                            print(f"[Bootstrapper] Ticker {ticker} has quantity precision limit of {allowed_precision}. Re-rounding...")
                            
                            import math
                            factor = 10 ** allowed_precision
                            target_qty = math.ceil(quantity * factor) / factor
                            
                            return self._place_adaptive_market_order(ticker, target_qty, allowed_precision, depth + 1)
                            
                except Exception as inner_err:
                    print(f"[Bootstrapper] Inner adaptive logic failed for {ticker}: {inner_err}")
            
            raise e

if __name__ == "__main__":
    # Executable entry point for manual validation
    from backtest_engine.live.trading212.config import Trading212Config
    
    config = Trading212Config()
    client = Trading212Client(config)
    resolver = Trading212TickerResolver(client)
    bootstrapper = Trading212Bootstrapper(client, resolver)
    
    bootstrapper.bootstrap()
