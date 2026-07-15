import time
import hmac
import hashlib
import urllib.parse
import json
import requests
from typing import Any, Dict, Optional
from backtest_engine.live.bybit.config import BybitConfig
from backtest_engine.live.utils import NETWORK_TIMEOUT_DEFAULT

class BybitClient:
    """HTTP client wrapper for the Bybit Spot V5 REST API."""

    def __init__(self, config: BybitConfig):
        self.config = config
        self.config.validate()
        self.recv_window = "5000"

    def _sign(self, timestamp: str, params_str: str) -> str:
        """Generates HMAC-SHA256 signature for Bybit V5 APIs."""
        val = timestamp + self.config.api_key + self.recv_window + params_str
        return hmac.new(
            self.config.api_secret.encode("utf-8"),
            val.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        signed: bool = False,
        max_retries: int = 3,
        backoff_factor: float = 1.5,
    ) -> requests.Response:
        """Sends an HTTP request with automatic Bybit V5 signature and retries."""
        url = f"{self.config.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        req_params = params.copy() if params else {}

        from tenacity import Retrying, stop_after_attempt, wait_random_exponential, retry_if_exception

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
                    if signed:
                        if not self.config.api_key or not self.config.api_secret:
                            raise ValueError("Missing Bybit credentials. Cannot perform signed requests.")
                        timestamp = str(int(time.time() * 1000))
                        if method == "GET":
                            query_str = urllib.parse.urlencode(req_params)
                            signature = self._sign(timestamp, query_str)
                        else:
                            body_str = json.dumps(json_data) if json_data else ""
                            signature = self._sign(timestamp, body_str)

                        headers.update({
                            "X-BAPI-API-KEY": self.config.api_key,
                            "X-BAPI-SIGN": signature,
                            "X-BAPI-TIMESTAMP": timestamp,
                            "X-BAPI-RECV-WINDOW": self.recv_window
                        })

                    response = requests.request(
                        method,
                        url,
                        headers=headers,
                        params=req_params if method == "GET" else None,
                        json=json_data if method != "GET" else None,
                        timeout=NETWORK_TIMEOUT_DEFAULT,
                    )

                    if response.status_code == 429 or response.status_code >= 500:
                        raise requests.exceptions.HTTPError(
                            f"Temporary error {response.status_code}",
                            response=response
                        )

                    response.raise_for_status()
                    return response
        except Exception as e:
            print(f"[BybitClient] Request failed after tenacity retries: {e}")
            raise e

    def get_ticker_price(self, symbol: str) -> Dict[str, Any]:
        """Retrieves the current ticker price for a specific spot symbol."""
        params = {
            "category": "spot",
            "symbol": symbol.upper()
        }
        response = self._request("GET", "/v5/market/tickers", params=params)
        return response.json()

    def get_klines(self, symbol: str, interval: str, limit: int = 200) -> Dict[str, Any]:
        """Retrieves historical kline/candle bars for a symbol."""
        params = {
            "category": "spot",
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit
        }
        response = self._request("GET", "/v5/market/kline", params=params)
        return response.json()

    def get_account_summary(self, coin: str = "USDC") -> Dict[str, Any]:
        """Retrieves account balance information (Signed)."""
        # Unified account balance endpoint
        params = {
            "accountType": "UNIFIED",
            "coin": coin
        }
        response = self._request("GET", "/v5/account/wallet-balance", params=params, signed=True)
        return response.json()
