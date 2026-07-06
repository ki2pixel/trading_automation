import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi import Request
from fastapi.testclient import TestClient

from backtest_engine.live.paper_trading.exceptions import (
    PaperTradingException,
    SignalExecutionError,
    PortfolioUpdateError,
)
from run_paper_trader import app as paper_app, safe_error_response as paper_safe_error_response
from backtest_engine.web import create_optimizer_app

# --- Test suite for Robustness (Phase 4) ---

def test_custom_exceptions():
    """
    Given the custom paper trading exceptions
    When they are raised
    Then they should inherit from PaperTradingException/Exception and carry messages
    """
    with pytest.raises(SignalExecutionError) as exc_info:
        raise SignalExecutionError("order rejected")
    assert exc_info.value.args[0] == "order rejected"
    assert isinstance(exc_info.value, PaperTradingException)

    with pytest.raises(PortfolioUpdateError) as exc_info:
        raise PortfolioUpdateError("NAV mismatch")
    assert exc_info.value.args[0] == "NAV mismatch"
    assert isinstance(exc_info.value, PaperTradingException)


def test_safe_error_response_development():
    """
    Given the safe_error_response helper
    When an exception is handled in development environment
    Then it should return detailed error trace and correlation_id
    """
    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/test-route"
    
    with patch.dict(os.environ, {"ENVIRONMENT": "development", "DEBUG": "false"}):
        try:
            raise ValueError("Secret database credentials leak")
        except ValueError as exc:
            response = paper_safe_error_response(exc, mock_request)
            
    assert response.status_code == 500
    data = response.body.decode("utf-8")
    import json
    parsed = json.loads(data)
    assert "error" in parsed
    assert "Secret database credentials leak" in parsed["error"]
    assert "traceback" in parsed
    assert "correlation_id" in parsed


def test_safe_error_response_production():
    """
    Given the safe_error_response helper
    When an exception is handled in production environment with DEBUG=false
    Then it should return a generic shielded error message with correlation UUID and no traceback
    """
    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/test-route"
    
    with patch.dict(os.environ, {"ENVIRONMENT": "production", "RENDER": "true", "DEBUG": "false"}):
        try:
            raise ValueError("Secret database credentials leak")
        except ValueError as exc:
            response = paper_safe_error_response(exc, mock_request)
            
    assert response.status_code == 500
    data = response.body.decode("utf-8")
    import json
    parsed = json.loads(data)
    assert "error" in parsed
    assert "An internal error occurred. Reference: " in parsed["error"]
    assert "traceback" not in parsed
    assert "Secret database credentials" not in parsed["error"]


def test_global_handler_paper_trader():
    """
    Given the paper trading FastAPI app
    When an endpoint raises an unhandled error under production environment
    Then the global exception handler should intercept it and return a shielded error
    """
    client = TestClient(paper_app, raise_server_exceptions=False)
    
    with patch("run_paper_trader.verify_session_token", return_value=True):
        client.cookies.set("paper_trader_session", "mock_token")
        with patch("backtest_engine.live.paper_trading.api._get_pool", side_effect=RuntimeError("Mock DB pool crashed!")):
            with patch.dict(os.environ, {"ENVIRONMENT": "production", "DEBUG": "false"}):
                response = client.get("/api/portfolio")
        
    assert response.status_code == 500
    parsed = response.json()
    assert "error" in parsed
    assert "An internal error occurred. Reference: " in parsed["error"]
    assert "Mock DB pool crashed!" not in parsed["error"]


def test_global_handler_optimizer():
    """
    Given the backtest optimizer FastAPI app
    When an endpoint raises an unhandled error under production environment
    Then the global exception handler should shield the internal details
    """
    mock_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    optimizer_app = create_optimizer_app(repo_root=Path(mock_root), output_dir="reports/test_optimizer")
    client = TestClient(optimizer_app, raise_server_exceptions=False)
    
    with patch.object(optimizer_app.state.optimizer_store, "get", side_effect=RuntimeError("Mock filesystem storage error!")):
        with patch.dict(os.environ, {"ENVIRONMENT": "production", "DEBUG": "false"}):
            response = client.get("/api/jobs/some-job-id")
        
    assert response.status_code == 500
    parsed = response.json()
    assert "error" in parsed
    assert "An internal error occurred. Reference: " in parsed["error"]
    assert "Mock filesystem storage error!" not in parsed["error"]


def test_network_timeouts_constants():
    """
    Given the live utilities
    When accessing NETWORK_TIMEOUT_DEFAULT
    Then it should be defined and set to 10.0
    """
    from backtest_engine.live.utils import NETWORK_TIMEOUT_DEFAULT
    assert NETWORK_TIMEOUT_DEFAULT == 10.0


@patch("requests.request")
def test_bybit_client_timeout(mock_request):
    """
    Given the BybitClient
    When requests.request raises requests.exceptions.Timeout
    Then it should retry and eventually raise RequestsException
    """
    from backtest_engine.live.bybit.client import BybitClient
    from backtest_engine.live.bybit.config import BybitConfig
    import requests
    
    mock_request.side_effect = requests.exceptions.Timeout("Request timed out")
    
    with patch.dict(os.environ, {"BYBIT_API_KEY": "mock_key", "BYBIT_API_SECRET": "mock_secret", "BYBIT_BASE_URL": "http://mock-bybit"}):
        config = BybitConfig(dotenv_path="/nonexistent")
    client = BybitClient(config)
    
    with patch("time.sleep") as mock_sleep:
        with pytest.raises(requests.exceptions.RequestException):
            client.get_ticker_price("BTCUSDT")
            
    assert mock_request.call_count == 3
    # Check that it passed timeout=10.0 (or whatever NETWORK_TIMEOUT_DEFAULT is)
    kwargs = mock_request.call_args[1]
    assert kwargs["timeout"] == 10.0


@patch("requests.request")
def test_trading212_client_timeout(mock_request):
    """
    Given the Trading212Client
    When requests.request raises requests.exceptions.Timeout
    Then it should retry and eventually raise RequestsException
    """
    from backtest_engine.live.trading212.client import Trading212Client
    from backtest_engine.live.trading212.config import Trading212Config
    import requests
    
    mock_request.side_effect = requests.exceptions.Timeout("Request timed out")
    
    with patch.dict(os.environ, {"T212_API_KEY_ID": "mock_key", "T212_API_SECRET": "mock_secret", "T212_ENV": "demo"}):
        config = Trading212Config(dotenv_path="/nonexistent")
    client = Trading212Client(config)
    
    with patch("time.sleep") as mock_sleep:
        with pytest.raises(requests.exceptions.RequestException):
            client.get_positions()
            
    assert mock_request.call_count == 3
    kwargs = mock_request.call_args[1]
    assert kwargs["timeout"] == 10.0


@patch("urllib.request.urlopen")
def test_eurusd_rate_timeout(mock_urlopen):
    """
    Given the get_eurusd_rate function
    When the database fails and public API times out (raises URLError)
    Then it should catch the exception and fall back to the static rate
    """
    from backtest_engine.live.paper_trading.engine import get_eurusd_rate
    from decimal import Decimal
    import urllib.error
    
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
    mock_cursor.fetchone.side_effect = Exception("DB failed")
    
    mock_urlopen.side_effect = urllib.error.URLError("Connection timed out")
    
    rate = get_eurusd_rate(mock_conn)
    assert rate == Decimal("1.08")


@patch("requests.request")
def test_trading212_client_order_capping(mock_request):
    """
    Given a Trading212Client
    When trying to place a SELL order for more units than held on the broker
    Then it should cap the quantity to the held amount
    """
    from backtest_engine.live.trading212.client import Trading212Client
    from backtest_engine.live.trading212.config import Trading212Config
    from decimal import Decimal
    
    # Mock T212 config
    with patch.dict(os.environ, {"T212_API_KEY_ID": "mock_key", "T212_API_SECRET": "mock_secret", "T212_ENV": "demo"}):
        config = Trading212Config(dotenv_path="/nonexistent")
    client = Trading212Client(config)
    
    # Mock database connections to avoid real SQL queries
    mock_conn = MagicMock()
    mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
    mock_cursor.fetchone.return_value = (Decimal("10.0"),) # Price, NAV, current_qty
    
    # Mock positions response
    positions_payload = [
        {
            "instrument": {"ticker": "AMSe_EQ"},
            "quantity": 0.1
        }
    ]
    
    # Mock methods on client
    client.get_positions = MagicMock(return_value=positions_payload)
    client._request = MagicMock()
    
    # Mock connection functions
    with patch("backtest_engine.live.connection.get_redis_client", return_value=None), \
         patch("backtest_engine.live.connection.get_db_connection", return_value=mock_conn):
         
        # Case 1: Sell 5.7 units when holding 0.1 -> should cap to 0.1
        client.place_market_order("AMSe_EQ", -5.7)
        
        # Verify that client._request was called with adjusted quantity -0.1
        client._request.assert_called_once_with(
            "POST", "/equity/orders/market",
            json_data={"ticker": "AMSe_EQ", "quantity": -0.1},
            max_retries=1
        )
        
        # Reset mocks
        client._request.reset_mock()
        
        # Case 2: Sell 5.7 units when holding 0.0 -> should skip the order
        client.get_positions.return_value = []
        res = client.place_market_order("AMSe_EQ", -5.7)
        assert res["status"] == "FILLED"
        assert res["comment"] == "Skipped real order (0 held)"
        client._request.assert_not_called()

