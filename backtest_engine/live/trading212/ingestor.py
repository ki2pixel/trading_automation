import json
import os
import time
from typing import Dict, Any, Optional
from backtest_engine.live.trading212.client import Trading212Client

class Trading212PriceIngestor:
    """Tâche d'ingestion de prix pour récupérer les cotations via positions."""

    def __init__(self, client: Trading212Client, cache_path: str = "/tmp/t212_prices.json"):
        self.client = client
        self.cache_path = cache_path

    def poll_and_cache(self) -> Dict[str, float]:
        """Polls open positions, extracts current prices, and saves them to the cache file."""
        print("[PriceIngestor] Polling Trading 212 positions for realtime prices...")
        try:
            positions = self.client.get_positions()
        except Exception as e:
            print(f"[PriceIngestor] Error fetching positions: {e}")
            return self.read_cache()
            
        prices: Dict[str, float] = {}
        for pos in positions:
            ticker = pos.get("instrument", {}).get("ticker")
            
            # Extract price. API can return currentPrice or price depending on schema.
            # Fallback values from position schema: currentPrice, averagePricePaid, etc.
            price = pos.get("currentPrice")
            if price is None:
                price = pos.get("price")
                
            if ticker and price is not None:
                try:
                    prices[ticker] = float(price)
                except (ValueError, TypeError):
                    pass
                    
        if prices:
            self._write_cache(prices)
            print(f"[PriceIngestor] Successfully ingested and cached {len(prices)} prices.")
        else:
            print("[PriceIngestor] No pricing data found in positions.")
            
        return prices

    def _write_cache(self, prices: Dict[str, float]) -> None:
        """Writes price dictionary to the JSON cache file."""
        try:
            # Atomic write using a temp file
            temp_path = f"{self.cache_path}.tmp"
            os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
            with open(temp_path, "w") as f:
                json.dump(prices, f)
            os.replace(temp_path, self.cache_path)
        except Exception as e:
            print(f"[PriceIngestor] Failed to write price cache: {e}")

    def read_cache(self) -> Dict[str, float]:
        """Reads cached prices from the JSON file."""
        if not os.path.exists(self.cache_path):
            return {}
        try:
            with open(self.cache_path, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[PriceIngestor] Failed to read price cache: {e}")
            return {}

    def start_loop(self, interval_seconds: int = 60) -> None:
        """Starts a blocking loop that polls prices at the specified interval."""
        print(f"[PriceIngestor] Starting polling loop. Interval: {interval_seconds}s")
        while True:
            try:
                self.poll_and_cache()
            except KeyboardInterrupt:
                print("[PriceIngestor] Polling loop stopped by user.")
                break
            except Exception as e:
                print(f"[PriceIngestor] Unexpected error in polling loop: {e}")
            time.sleep(interval_seconds)

if __name__ == "__main__":
    # Executable entry point for manual validation
    from backtest_engine.live.trading212.config import Trading212Config
    
    config = Trading212Config()
    client = Trading212Client(config)
    ingestor = Trading212PriceIngestor(client)
    
    # Run a single poll or start loop based on arguments/default
    ingestor.poll_and_cache()
