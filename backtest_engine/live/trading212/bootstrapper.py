from typing import Set, List
from backtest_engine.live.trading212.client import Trading212Client
from backtest_engine.live.trading212.resolver import Trading212TickerResolver

class Trading212Bootstrapper:
    """Bootstraps the portfolio by opening micro-positions for monitoring purposes."""

    def __init__(self, client: Trading212Client, resolver: Trading212TickerResolver):
        self.client = client
        self.resolver = resolver
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
                result = self.client.place_market_order(ticker, self.micro_qty)
                print(f"[Bootstrapper] Placed market order for {ticker}: ID {result.get('id')} - Status {result.get('status')}")
                placed_tickers.append(ticker)
            except Exception as e:
                print(f"[Bootstrapper] Failed to place order for {ticker}: {e}")
                
        print(f"[Bootstrapper] Bootstrap complete. Placed {len(placed_tickers)} new micro-position orders.")
        return placed_tickers

if __name__ == "__main__":
    # Executable entry point for manual validation
    from backtest_engine.live.trading212.config import Trading212Config
    
    config = Trading212Config()
    client = Trading212Client(config)
    resolver = Trading212TickerResolver(client)
    bootstrapper = Trading212Bootstrapper(client, resolver)
    
    bootstrapper.bootstrap()
