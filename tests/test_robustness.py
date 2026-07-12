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

@pytest.fixture(autouse=True)
def reset_eurusd_cache():
    import backtest_engine.live.utils as utils
    utils._eurusd_cache_rate = None
    utils._eurusd_cache_expiry = 0.0

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
    
    with patch.dict(os.environ, {"ENVIRONMENT": "development", "DEBUG": "true"}):
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
    mock_conn.__enter__.return_value = mock_conn
    mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
    mock_cursor.fetchone.side_effect = [
        (Decimal("100000.00"),), # NAV (Case 1)
        (Decimal("10.00"),),     # Price (Case 1)
        (Decimal("10.00"),),     # Position Qty (Case 1)
        (Decimal("100000.00"),), # NAV (Case 2)
        (Decimal("10.00"),),     # Price (Case 2)
        (Decimal("0.00"),)       # Position Qty (Case 2)
    ]
    
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


@patch("requests.request")
def test_trading212_client_precision_mismatch(mock_request):
    """
    Given a Trading212Client
    When trying to place an order that returns a 400 precision mismatch error
    Then it should parse the allowed precision, round the quantity, and retry successfully
    """
    from backtest_engine.live.trading212.client import Trading212Client
    from backtest_engine.live.trading212.config import Trading212Config
    from decimal import Decimal
    import requests
    
    # Mock T212 config
    with patch.dict(os.environ, {"T212_API_KEY_ID": "mock_key", "T212_API_SECRET": "mock_secret", "T212_ENV": "demo"}):
        config = Trading212Config(dotenv_path="/nonexistent")
    client = Trading212Client(config)
    
    # Mock database connections to avoid real SQL queries
    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn
    mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
    mock_cursor.fetchone.side_effect = [
        (Decimal("100000.00"),), # NAV
        (Decimal("10.00"),),     # Price
        (Decimal("0.00"),)       # Position Qty (empty)
    ]
    
    client.get_positions = MagicMock(return_value=[])
    
    # Mock requests.exceptions.HTTPError for 400 Bad Request
    response_400 = requests.Response()
    response_400.status_code = 400
    response_400._content = b'{"type": "/api-errors/quantity-precision-mismatch", "detail": "invalid quantity precision 3"}'
    
    # Second response is success 200
    response_200 = requests.Response()
    response_200.status_code = 200
    response_200._content = b'{"status": "NEW", "id": 12345}'
    
    # We patch the client's internal _request method
    calls = []
    def mock_request_side_effect(*args, **kwargs):
        import copy
        calls.append((args, copy.deepcopy(copy.deepcopy(kwargs))))
        if len(calls) == 1:
            raise requests.exceptions.HTTPError("Bad Request", response=response_400)
        return response_200

    client._request = MagicMock(side_effect=mock_request_side_effect)
    
    with patch("backtest_engine.live.connection.get_redis_client", return_value=None), \
         patch("backtest_engine.live.connection.get_db_connection", return_value=mock_conn):
         
        # Place order with 6 decimal places (13.256739)
        res = client.place_market_order("VNAd_EQ", 13.256739)
        
        assert res["status"] == "NEW"
        assert res["id"] == 12345
        
        # Verify it was called twice: once with 13.256739, second with rounded 13.257
        assert len(calls) == 2
        assert calls[0][1]["json_data"]["quantity"] == 13.256739
        assert calls[1][1]["json_data"]["quantity"] == 13.257


# ---------------------------------------------------------
# Phase 4 Robustness and Recovery Tests
# ---------------------------------------------------------

def test_bybit_conversion_crash_recovery():
    """
    Given a SpotConversionRouter
    When an order was already submitted but crashed, returning duplicate orderLinkId on retry
    Then the router must recover the filled status and drain the accumulator
    """
    from backtest_engine.live.bybit.conversion.spot_router import SpotConversionRouter
    from backtest_engine.live.bybit.conversion.order_types import ConversionOrder, ConversionOrderStatus
    from backtest_engine.live.bybit.conversion.margin_simulator import MarginCheckResult
    from decimal import Decimal
    
    conn_mock = MagicMock()
    cur_mock = MagicMock()
    conn_mock.cursor.return_value.__enter__.return_value = cur_mock
    
    # 1. No unfinished order initially, but should trigger = True (with balance 20)
    # The query for step 0 checks if there is any unfinished order in status PENDING/SUBMITTED/PARTIAL
    cur_mock.fetchone.side_effect = [
        None, # Step 0 check: no unfinished order
        (True, Decimal("20.00")), # accumulator.should_trigger
    ]
    
    accumulator_mock = MagicMock()
    accumulator_mock.should_trigger.return_value = (True, Decimal("20.00"))
    
    margin_sim_mock = MagicMock()
    margin_sim_mock.is_locked = False
    margin_sim_mock.check_conversion_safety.return_value = MarginCheckResult(
        is_safe=True,
        margin_state=None,
        post_conversion_equity=Decimal("0"),
        required_minimum=Decimal("0"),
        headroom=Decimal("0"),
        reason=""
    )
    
    client_mock = MagicMock()
    
    # Mock POST returning duplicate orderLinkId
    response_post_mock = MagicMock()
    response_post_mock.json.return_value = {
        "retCode": 110071,
        "retMsg": "Duplicate orderLinkId"
    }
    
    # Mock GET /v5/order/realtime returning Filled status
    response_get_mock = MagicMock()
    response_get_mock.json.return_value = {
        "retCode": 0,
        "result": {
            "list": [
                {
                    "orderId": "bybit_order_crashed_123",
                    "orderStatus": "Filled",
                    "cumExecQty": "18.50",
                    "avgPrice": "1.08"
                }
            ]
        }
    }
    
    client_mock._request.side_effect = [response_post_mock, response_get_mock]
    
    router = SpotConversionRouter(
        client_mock, accumulator_mock, margin_sim_mock, dry_run=False
    )
    
    # Mock DB PTC query
    with patch("backtest_engine.live.connection.get_db_connection") as mock_db_conn:
        mock_conn_inner = MagicMock()
        mock_cur_inner = MagicMock()
        mock_db_conn.return_value.__enter__.return_value = mock_conn_inner
        mock_conn_inner.cursor.return_value.__enter__.return_value = mock_cur_inner
        # Return NAV and reference price for PTC check
        mock_cur_inner.fetchone.side_effect = [
            (Decimal("100000.00"),), # NAV
            (Decimal("1.08"),),      # Price eurusd
        ]
        
        order = router.try_convert(conn_mock)
        
    assert order is not None
    assert order.status == ConversionOrderStatus.FILLED
    assert order.broker_order_id == "bybit_order_crashed_123"
    assert order.filled_qty_eur == Decimal("18.50")
    
    # Confirm accumulator is drained on verified filled status
    accumulator_mock.drain.assert_called_once_with(conn_mock, order.client_order_id)

def test_bybit_conversion_dry_run_not_destructive():
    """
    Given a SpotConversionRouter in dry-run mode
    When try_convert is executed
    Then it should NOT drain the accumulator buffer
    """
    from backtest_engine.live.bybit.conversion.spot_router import SpotConversionRouter
    from backtest_engine.live.bybit.conversion.margin_simulator import MarginCheckResult
    from backtest_engine.live.bybit.conversion.order_types import ConversionOrderStatus
    from decimal import Decimal
    
    conn_mock = MagicMock()
    cur_mock = MagicMock()
    conn_mock.cursor.return_value.__enter__.return_value = cur_mock
    
    # Step 0 check: no unfinished order
    cur_mock.fetchone.return_value = None
    
    accumulator_mock = MagicMock()
    accumulator_mock.should_trigger.return_value = (True, Decimal("20.00"))
    
    margin_sim_mock = MagicMock()
    margin_sim_mock.is_locked = False
    margin_sim_mock.check_conversion_safety.return_value = MarginCheckResult(
        is_safe=True,
        margin_state=None,
        post_conversion_equity=Decimal("0"),
        required_minimum=Decimal("0"),
        headroom=Decimal("0"),
        reason=""
    )
    
    client_mock = MagicMock()
    router = SpotConversionRouter(
        client_mock, accumulator_mock, margin_sim_mock, dry_run=True
    )
    
    # Mock DB PTC query
    with patch("backtest_engine.live.connection.get_db_connection") as mock_db_conn:
        mock_conn_inner = MagicMock()
        mock_cur_inner = MagicMock()
        mock_db_conn.return_value.__enter__.return_value = mock_conn_inner
        mock_conn_inner.cursor.return_value.__enter__.return_value = mock_cur_inner
        mock_cur_inner.fetchone.side_effect = [
            (Decimal("100000.00"),), # NAV
            (Decimal("1.08"),),      # Price eurusd
        ]
        
        order = router.try_convert(conn_mock)
        
    assert order is not None
    assert order.status == ConversionOrderStatus.FILLED
    
    # Accumulator MUST NOT be drained in dry_run
    accumulator_mock.drain.assert_not_called()


def test_margin_simulator_available_balance():
    """
    Given a UTAMarginSimulator
    When checking conversion safety but the required USDC amount exceeds available balance
    Then the check should return unsafe even if maintenance margin is zero
    """
    from backtest_engine.live.bybit.conversion.margin_simulator import UTAMarginSimulator
    from decimal import Decimal
    
    client_mock = MagicMock()
    client_mock.config.base_currency = "USDC"
    # Available balance 2000, equity 5000, maintenance margin 0
    client_mock.get_account_summary.return_value = {
        "retCode": 0,
        "result": {
            "list": [
                {
                    "totalEquity": "5000.00",
                    "totalMaintenanceMargin": "0.00",
                    "totalAvailableBalance": "2000.00"
                }
            ]
        }
    }
    
    sim = UTAMarginSimulator(client_mock)
    
    # Try converting 3000 USDC (exceeds available balance of 2000)
    result = sim.check_conversion_safety(Decimal("3000.00"))
    assert result.is_safe is False
    assert "exceeds available balance" in result.reason
    assert sim.is_locked is True


def test_stale_redis_price_resolution():
    """
    Given a SignalExecutor resolving live prices
    When the Redis cache contains a price older than 3 minutes
    Then it should ignore the Redis price and fallback to SQL or skip the evaluation
    """
    from backtest_engine.live.paper_trading.signal_executor import SignalExecutor
    from backtest_engine.strategy_registry import StrategyRegistry
    from decimal import Decimal
    from datetime import datetime, timezone, timedelta
    import json
    import pandas as pd
    
    executor = SignalExecutor()
    
    redis_client_mock = MagicMock()
    # Mock price in Redis stale by 5 minutes (300 seconds)
    stale_time = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    stale_payload = json.dumps({
        "price": "150.00",
        "timestamp": stale_time
    })
    redis_client_mock.get.return_value = stale_payload
    
    conn_mock = MagicMock()
    cur_mock = MagicMock()
    conn_mock.cursor.return_value.__enter__.return_value = cur_mock
    
    # Mock SQL fallback also stale (4 minutes)
    stale_sql_time = datetime.now(timezone.utc) - timedelta(minutes=4)
    cur_mock.fetchone.return_value = (149.00, stale_sql_time)
    
    # 100 candle rows 1 minute apart to satisfy minimum bars and resampling
    base_time = pd.Timestamp("2026-07-11 00:00:00", tz='UTC')
    mock_candles = [
        (base_time + timedelta(minutes=i), 100.0, 101.0, 99.0, 100.0)
        for i in range(100)
    ]
    
    # Mock StrategyRegistry.get to return a mock strategy that succeeds and triggers buy
    mock_strat_info = MagicMock()
    mock_run_result = MagicMock()
    last_closed_time = base_time + timedelta(minutes=98)
    mock_run_result.bars = pd.DataFrame(
        {"long_entry": [True], "long_exit": [False]}, 
        index=[last_closed_time]
    )
    mock_strat_info.run_function.return_value = mock_run_result
    mock_strat_info.overrides_from_mapping_function.return_value = {}
    
    with patch("backtest_engine.live.connection.get_redis_client", return_value=redis_client_mock), \
         patch.object(StrategyRegistry, "get", return_value=mock_strat_info), \
         patch.object(SignalExecutor, "is_market_open", return_value=True):
         
        # We mock active config fetch and candle queries
        cur_mock.fetchall.side_effect = [
            [(1, "RSI", "AAPL", "1m", 0.1, 1000, 1000, 5000, 10000, {})], # configs
            [], # positions
            mock_candles # candles
        ]
        
        executor.evaluate_and_execute_strategies(conn_mock)
        
        # Check that it did NOT trigger any trade, and evaluations logged 'WAITING_DATA' due to stale price
        logged = False
        for call in cur_mock.execute.call_args_list:
            args = call[0]
            if len(args) > 1 and "paper_evaluations" in args[0] and "No fresh price available" in args[1]:
                logged = True
                break
        assert logged, "Expected WAITING_DATA evaluation log not found"


def test_connection_singletons_thread_safety():
    """
    Given: Concurrent calls to get_db_pool() and get_redis_client()
    When: Multiple threads attempt to initialize the pool/client concurrently
    Then: ThreadedConnectionPool / FailoverRedisClient must be initialized exactly once
    """
    import threading
    import os
    from backtest_engine.live.connection import get_db_pool, get_redis_client
    import backtest_engine.live.connection as connection
    
    # Reset singleton states
    original_db_pool = connection._db_pool
    original_redis_client = connection._redis_client
    
    connection._db_pool = None
    connection._redis_client = None
    
    db_pool_inits = 0
    redis_client_inits = 0
    init_lock = threading.Lock()
    
    # Mock OS environment
    with patch.dict(os.environ, {
        "DATABASE_URL": "postgresql://localhost:5432/test",
        "REDIS_URL": "redis://localhost:6379/0"
    }):
        # Mock ThreadedConnectionPool creation and redis.Redis.from_url / FailoverRedisClient
        def mock_pool_init(*args, **kwargs):
            nonlocal db_pool_inits
            with init_lock:
                db_pool_inits += 1
            return MagicMock()
            
        def mock_redis_init(*args, **kwargs):
            nonlocal redis_client_inits
            with init_lock:
                redis_client_inits += 1
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            return mock_client

        with patch("psycopg2.pool.ThreadedConnectionPool", side_effect=mock_pool_init), \
             patch("redis.Redis.from_url", side_effect=mock_redis_init):
            
            # Run get_db_pool and get_redis_client concurrently
            threads = []
            for _ in range(20):
                t1 = threading.Thread(target=get_db_pool)
                t2 = threading.Thread(target=get_redis_client)
                threads.extend([t1, t2])
                t1.start()
                t2.start()
                
            for t in threads:
                t.join()
                
            assert db_pool_inits == 1
            assert redis_client_inits == 1
            
    # Restore original states
    connection._db_pool = original_db_pool
    connection._redis_client = original_redis_client

