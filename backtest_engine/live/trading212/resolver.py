import os
import json
import time
from typing import Dict, List, Any
from backtest_engine.live.trading212.client import Trading212Client
from backtest_engine.live.utils import T212_STATIC_MAPPING

class Trading212TickerResolver:
    """Service to map shortlist assets to precise Trading 212 tickers in EUR."""

    # Static validated mappings for the 21 unique assets to T212 EUR tickers
    STATIC_MAPPING = T212_STATIC_MAPPING


    def __init__(
        self,
        client: Trading212Client,
        cache_paths: List[str] = ["/tmp/t212_instruments.json", "/tmp/instruments.json"],
    ):
        self.client = client
        self.cache_paths = cache_paths
        self.instruments: List[Dict[str, Any]] = []

    def get_instruments_cache_path(self) -> str:
        """Returns the primary cache path or the first available writeable path."""
        for path in self.cache_paths:
            if os.path.exists(path):
                return path
        return self.cache_paths[0]

    def _load_instruments(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Loads instruments from cache or fetches from API if cache is stale or missing."""
        cache_path = self.get_instruments_cache_path()
        now = time.time()
        
        # Check if cache exists and is fresh (< 1 hour old)
        if not force_refresh and os.path.exists(cache_path):
            mtime = os.path.getmtime(cache_path)
            if now - mtime < 3600:
                try:
                    with open(cache_path, "r") as f:
                        self.instruments = json.load(f)
                    if self.instruments:
                        return self.instruments
                except Exception as e:
                    print(f"[TickerResolver] Stale instruments cache read error: {e}")

        # Cache missing, stale, or refresh forced -> fetch from API
        print(f"[TickerResolver] Fetching and caching instruments list...")
        try:
            self.instruments = self.client.get_instruments()
            # Ensure parent directories exist
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, "w") as f:
                json.dump(self.instruments, f)
            return self.instruments
        except Exception as e:
            print(f"[TickerResolver] Failed to refresh instruments list: {e}")
            # Fallback to loading whatever exists in cache even if stale
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, "r") as f:
                        self.instruments = json.load(f)
                    return self.instruments
                except Exception:
                    pass
            raise e

    def resolve(self, asset: str) -> str:
        """Resolves an asset string to its precise Trading 212 ticker symbol."""
        # 1. First check the static mapping
        if asset in self.STATIC_MAPPING:
            return self.STATIC_MAPPING[asset]
            
        # 2. Dynamic lookup fallback using cache
        if not self.instruments:
            self._load_instruments()
            
        # Standard cleaning of queries (removing suffixes like .DE, deeur, etc.)
        query = asset.lower()
        for suffix in [".de", ".co", ".mc", "deeur", "iteur", "nleur", "freur", "beeur"]:
            if query.endswith(suffix):
                query = query[:-len(suffix)]
                break

        # Search matching ticker, name, or shortName
        matches = []
        for inst in self.instruments:
            ticker = inst.get("ticker", "").lower()
            name = inst.get("name", "").lower()
            short_name = inst.get("shortName", "").lower()
            isin = inst.get("isin", "").lower()
            
            # Prioritize exact ticker/isin matches
            if query == ticker or query == short_name or query == isin:
                matches.append((100, inst))
            elif query in ticker or query in name or query in short_name:
                # Prefer EUR assets
                score = 50
                if inst.get("currencyCode") == "EUR":
                    score += 10
                matches.append((score, inst))
                
        if matches:
            # Sort by score descending, then by ticker
            matches.sort(key=lambda x: (-x[0], x[1].get("ticker")))
            resolved = matches[0][1].get("ticker")
            print(f"[TickerResolver] Dynamic mapping fallback: {asset} -> {resolved}")
            return resolved
            
        raise ValueError(f"Could not resolve Trading 212 ticker for asset: {asset}")
