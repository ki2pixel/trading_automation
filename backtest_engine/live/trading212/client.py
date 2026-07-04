import time
import requests
from requests.auth import HTTPBasicAuth
from typing import Any, Dict, List, Optional
from backtest_engine.live.trading212.config import Trading212Config
from backtest_engine.live.utils import NETWORK_TIMEOUT_DEFAULT

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
        """Sends an HTTP request with automatic rate limiting and tenacity retries."""
        from tenacity import Retrying, stop_after_attempt, wait_random_exponential, retry_if_exception
        url = f"{self.config.base_url}/api/v0{endpoint}"
        
        def is_temporary_error(exception: Exception) -> bool:
            if isinstance(exception, requests.exceptions.RequestException):
                if isinstance(exception, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
                    return True
                if hasattr(exception, "response") and exception.response is not None:
                    status_code = exception.response.status_code
                    return status_code == 429 or status_code >= 500
            return False

        try:
            for attempt in Retrying(
                stop=stop_after_attempt(max_retries),
                wait=wait_random_exponential(multiplier=backoff_factor, max=10),
                retry=retry_if_exception(is_temporary_error),
                reraise=True
            ):
                with attempt:
                    self._throttle(endpoint)
                    response = requests.request(
                        method,
                        url,
                        auth=self.auth,
                        headers=self.headers,
                        params=params,
                        json=json_data,
                        timeout=NETWORK_TIMEOUT_DEFAULT,
                    )
                    
                    # Raise temporary HTTPError to trigger Tenacity retry
                    if response.status_code == 429 or response.status_code >= 500:
                        raise requests.exceptions.HTTPError(
                            f"Temporary error {response.status_code}",
                            response=response
                        )
                        
                    response.raise_for_status()
                    return response
        except Exception as e:
            print(f"[Trading212Client] Request failed after tenacity retries: {e}")
            raise e

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

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancels a pending order by its ID."""
        response = self._request("DELETE", f"/equity/orders/{order_id}")
        return response.json()

    def place_market_order(self, ticker: str, quantity: float) -> Dict[str, Any]:
        """Places a market order idempotently with a Redis SETNX lock and a pre-trade/retry portfolio reconciliation."""
        from backtest_engine.live.connection import get_redis_client
        
        redis_client = None
        lock_acquired = False
        lock_key = f"lock:t212:order:{ticker}"
        
        try:
            redis_client = get_redis_client()
        except Exception as e:
            print(f"[Trading212Client] WARNING: Could not connect to Redis: {e}")
            
        if redis_client:
            lock_acquired = redis_client.set(lock_key, "locked", ex=15, nx=True)
            if not lock_acquired:
                raise ValueError(f"Duplicate concurrent order blocked for ticker {ticker}")
                
        try:
            # Pre-Trade Controls check
            from backtest_engine.live.controls import PreTradeController, Decimal
            from backtest_engine.live.connection import get_db_connection
            
            nav = Decimal("100000.0")
            price = Decimal("0.0")
            current_qty = Decimal("0.0")
            
            try:
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT total_nav FROM paper_portfolio_balance WHERE source = 'trading212'")
                        row = cur.fetchone()
                        if row and row[0] is not None:
                            nav = Decimal(str(row[0]))
                            
                        cur.execute("SELECT price FROM live_prices WHERE ticker = %s", (ticker.lower(),))
                        row = cur.fetchone()
                        if row and row[0] is not None:
                            price = Decimal(str(row[0]))
                            
                        cur.execute("SELECT quantity FROM paper_positions WHERE ticker = %s AND status = 'OPEN'", (ticker,))
                        row = cur.fetchone()
                        if row and row[0] is not None:
                            current_qty = Decimal(str(row[0]))
            except Exception as dbe:
                print(f"[Trading212Client] PTC Warning: Failed to query DB for risk controls: {dbe}")
                
            if price <= 0:
                price = Decimal("1.0")
                
            ptc = PreTradeController()
            ptc.check_limits(
                ticker=ticker,
                quantity=Decimal(str(quantity)),
                price=price,
                current_nav=nav,
                current_position_qty=current_qty,
                reference_price=price
            )

            # Fetch initial quantity of the ticker
            initial_qty = 0.0
            try:
                positions = self.get_positions()
                matching = [p for p in positions if p.get("ticker") == ticker]
                if matching:
                    initial_qty = float(matching[0].get("quantity", 0.0))
            except Exception as pe:
                print(f"[Trading212Client] Pre-trade check positions fetch failed: {pe}")

            payload = {
                "ticker": ticker,
                "quantity": float(quantity)
            }
            
            max_attempts = 3
            last_error = None
            
            for attempt in range(max_attempts):
                if attempt > 0:
                    print(f"[Trading212Client] Reconciling state before retry attempt {attempt + 1}...")
                    try:
                        positions = self.get_positions()
                        matching = [p for p in positions if p.get("ticker") == ticker]
                        current_qty = float(matching[0].get("quantity", 0.0)) if matching else 0.0
                        
                        expected_qty = initial_qty + float(quantity)
                        if abs(current_qty - expected_qty) < 1e-7:
                            print(f"[Trading212Client] Reconciliation SUCCESS: Position quantity matches expected {expected_qty}. Aborting retry to prevent duplicate.")
                            return {"ticker": ticker, "quantity": quantity, "status": "FILLED", "reconciled": True}
                    except Exception as re:
                        print(f"[Trading212Client] Reconciliation failed during retry: {re}")
                
                try:
                    response = self._request("POST", "/equity/orders/market", json_data=payload, max_retries=1)
                    return response.json()
                except Exception as e:
                    last_error = e
                    print(f"[Trading212Client] Order attempt {attempt + 1} failed: {e}")
                    
                    if hasattr(e, "response") and e.response is not None:
                        status_code = e.response.status_code
                        if status_code < 500 and status_code != 429:
                            raise e
                    
                    import time
                    time.sleep(0.1 * (2 ** attempt)) # Fast backoff for testing and live speed
            
            raise last_error or RuntimeError("Order execution failed after multiple reconciled attempts.")
            
        finally:
            if redis_client and lock_acquired:
                try:
                    redis_client.delete(lock_key)
                except Exception as de:
                    print(f"[Trading212Client] Failed to release lock {lock_key}: {de}")

    def get_account_summary(self) -> Dict[str, Any]:
        """Retrieves trading account details including cash and investments."""
        response = self._request("GET", "/equity/account/summary")
        return response.json()
