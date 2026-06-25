import time
import requests
from requests.auth import HTTPBasicAuth
from typing import Any, Dict, List, Optional
from backtest_engine.live.trading212.config import Trading212Config

class Trading212Client:
    """HTTP client wrapper for the Trading 212 official REST API (Beta)."""

    def __init__(self, config: Trading212Config):
        self.config = config
        self.config.validate()
        self.auth = HTTPBasicAuth(self.config.api_key_id, self.config.api_secret)
        self.headers = {"Content-Type": "application/json"}
        
        # Throttling trackers (timestamps of last calls)
        self._last_call_times: Dict[str, float] = {}
        
        # Min delays between calls in seconds
        self._endpoint_delays = {
            "/equity/metadata/instruments": 50.0,
            "/equity/positions": 1.0,
            "/equity/portfolio": 1.0,
            "/equity/account/summary": 5.0,
            "/equity/orders": 5.0,
            "/equity/orders/market": 1.2, # 50/min is 1.2s
        }

    def _throttle(self, endpoint: str) -> None:
        """Enforces client-side rate limits to prevent 429s."""
        min_delay = self._endpoint_delays.get(endpoint, 1.0)
        last_call = self._last_call_times.get(endpoint, 0.0)
        elapsed = time.time() - last_call
        if elapsed < min_delay:
            time.sleep(min_delay - elapsed)
        self._last_call_times[endpoint] = time.time()

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
    ) -> requests.Response:
        """Sends an HTTP request with automatic rate limiting and exponential backoff retries."""
        url = f"{self.config.base_url}/api/v0{endpoint}"
        
        for attempt in range(max_retries):
            # Enforce throttling before each attempt
            self._throttle(endpoint)
            try:
                response = requests.request(
                    method,
                    url,
                    auth=self.auth,
                    headers=self.headers,
                    params=params,
                    json=json_data,
                    timeout=30,
                )
                
                # Check for rate limiting responses
                if response.status_code == 429:
                    retry_after = response.headers.get("retry-after")
                    wait_time = float(retry_after) if retry_after else (backoff_factor ** attempt)
                    print(f"[Trading212Client] Rate limit hit (429). Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                    
                # Retry on temporary server errors
                if response.status_code >= 500:
                    wait_time = backoff_factor ** attempt
                    print(f"[Trading212Client] Server error ({response.status_code}). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                    
                response.raise_for_status()
                return response
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    print(f"[Trading212Client] Request failed after {max_retries} attempts: {e}")
                    raise e
                wait_time = backoff_factor ** attempt
                time.sleep(wait_time)
                
        raise requests.exceptions.RequestException("Request failed due to excessive retries.")

    def get_instruments(self) -> List[Dict[str, Any]]:
        """Retrieves all available market instruments."""
        response = self._request("GET", "/equity/metadata/instruments")
        return response.json()

    def get_positions(self) -> List[Dict[str, Any]]:
        """Retrieves all open portfolio positions."""
        response = self._request("GET", "/equity/positions")
        return response.json()

    def get_portfolio(self) -> List[Dict[str, Any]]:
        """Retrieves portfolio summary statistics for all assets."""
        response = self._request("GET", "/equity/portfolio")
        return response.json()

    def get_pending_orders(self) -> List[Dict[str, Any]]:
        """Retrieves active pending orders."""
        response = self._request("GET", "/equity/orders")
        return response.json()

    def place_market_order(self, ticker: str, quantity: float) -> Dict[str, Any]:
        """Places a market order. Positive quantity for buy, negative for sell."""
        # Ensure quantity is formatted cleanly (Trading212 uses float/double)
        payload = {
            "ticker": ticker,
            "quantity": float(quantity)
        }
        response = self._request("POST", "/equity/orders/market", json_data=payload)
        return response.json()
