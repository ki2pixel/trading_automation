import os
import json
import pytest
import requests
from unittest.mock import MagicMock, patch
from requests.exceptions import RequestException

from backtest_engine.live.trading212.config import Trading212Config
from backtest_engine.live.trading212.client import Trading212Client
from backtest_engine.live.trading212.resolver import Trading212TickerResolver
from backtest_engine.live.trading212.bootstrapper import Trading212Bootstrapper
from backtest_engine.live.trading212.ingestor import Trading212PriceIngestor
from backtest_engine.live.trading212.tracker import Trading212PositionTracker


# =====================================================================
# FIXTURES
# =====================================================================

@pytest.fixture
def mock_config():
    # Given: Set environment variables for tests
    with patch.dict(os.environ, {
        "T212_API_KEY_ID": "test_key",
        "T212_API_SECRET": "test_secret",
        "T212_ENV": "demo"
    }):
        config = Trading212Config()
        yield config


@pytest.fixture
def mock_client(mock_config):
    # Given: Client with mocked requests
    client = Trading212Client(mock_config)
    # Speed up tests by disabling throttle delay
    client._endpoint_delays = {k: 0.0 for k in client._endpoint_delays}
    return client


# =====================================================================
# CONFIGURATION TESTS
# =====================================================================

def test_config_demo(mock_config):
    # Given: Environment variables configured for demo
    # When: Configuration is initialized and validated
    mock_config.validate()
    # Then: Configuration matches expected values
    assert mock_config.api_key_id == "test_key"
    assert mock_config.api_secret == "test_secret"
    assert mock_config.env == "demo"
    assert mock_config.base_url == "https://demo.trading212.com"


def test_config_live():
    # Given: Environment variables configured for live
    with patch.dict(os.environ, {
        "T212_API_KEY_ID": "live_key",
        "T212_API_SECRET": "live_secret",
        "T212_ENV": "live"
    }):
        # When: Configuration is loaded
        config = Trading212Config()
        config.validate()
        # Then: Configuration matches live URL
        assert config.env == "live"
        assert config.base_url == "https://live.trading212.com"


def test_config_missing_keys():
    # Given: Missing environment variables
    with patch.dict(os.environ, {}, clear=True):
        # When: Configuration is initialized and validated
        config = Trading212Config(dotenv_path="/nonexistent_env")
        # Then: Raises ValueError on validation
        with pytest.raises(ValueError) as excinfo:
            config.validate()
        assert "Missing Trading 212 credentials" in str(excinfo.value)


# =====================================================================
# CLIENT API TESTS
# =====================================================================

@patch("requests.request")
def test_client_get_positions(mock_request, mock_client):
    # Given: Mock API response for positions
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [{"instrument": {"ticker": "SAPd_EQ"}, "quantity": 10.0}]
    mock_request.return_value = mock_resp

    # When: Client fetches positions
    positions = mock_client.get_positions()

    # Then: Output matches expected list
    assert len(positions) == 1
    assert positions[0]["instrument"]["ticker"] == "SAPd_EQ"
    mock_request.assert_called_once_with(
        "GET",
        "https://demo.trading212.com/api/v0/equity/positions",
        auth=mock_client.auth,
        headers=mock_client.headers,
        params=None,
        json=None,
        timeout=30
    )


@patch("requests.request")
def test_client_retry_on_429(mock_request, mock_client):
    # Given: API returns 429 (rate limit) first, then 200
    mock_resp_429 = MagicMock()
    mock_resp_429.status_code = 429
    mock_resp_429.headers = {"retry-after": "0.1"}

    mock_resp_200 = MagicMock()
    mock_resp_200.status_code = 200
    mock_resp_200.json.return_value = {"status": "success"}

    mock_request.side_effect = [mock_resp_429, mock_resp_200]

    # When: Request is made
    res = mock_client.get_portfolio()

    # Then: It succeeds after retrying once
    assert res == {"status": "success"}
    assert mock_request.call_count == 2


@patch("requests.request")
def test_client_retry_on_500(mock_request, mock_client):
    # Given: API returns 500 (internal server error) first, then 200
    mock_resp_500 = MagicMock()
    mock_resp_500.status_code = 500

    mock_resp_200 = MagicMock()
    mock_resp_200.status_code = 200
    mock_resp_200.json.return_value = {"status": "ok"}

    mock_request.side_effect = [mock_resp_500, mock_resp_200]

    # When: Request is made
    res = mock_client.get_portfolio()

    # Then: It succeeds after retrying once
    assert res == {"status": "ok"}
    assert mock_request.call_count == 2


@patch("requests.request")
def test_client_max_retries_fail(mock_request, mock_client):
    # Given: API consistently returns 500 errors
    mock_resp_500 = MagicMock()
    mock_resp_500.status_code = 500
    mock_request.return_value = mock_resp_500

    # When: Request is made
    # Then: Raises RequestException
    with pytest.raises(RequestException):
        mock_client.get_portfolio()
    assert mock_request.call_count == 3


# =====================================================================
# TICKER RESOLVER TESTS
# =====================================================================

def test_resolver_static_mapping(mock_client):
    # Given: Resolver with static mapping
    resolver = Trading212TickerResolver(mock_client)

    # When: Resolving assets from shortlist
    t1 = resolver.resolve("ZEAL.CO")
    t2 = resolver.resolve("SAP")
    t3 = resolver.resolve("dpwdeeur")

    # Then: Predefined exact tickers are returned
    assert t1 == "TIMd_EQ"
    assert t2 == "SAPd_EQ"
    assert t3 == "DPWd_EQ"


@patch("backtest_engine.live.trading212.client.Trading212Client.get_instruments")
def test_resolver_dynamic_fallback(mock_get_instruments, mock_client, tmp_path):
    # Given: Dummy instruments cache and resolver
    cache_file = str(tmp_path / "instruments.json")
    resolver = Trading212TickerResolver(mock_client, cache_paths=[cache_file])
    
    mock_get_instruments.return_value = [
        {"ticker": "NOTd1_EQ", "name": "Novartis", "isin": "CH0012005267", "currencyCode": "EUR"}
    ]

    # When: Resolving an unmapped asset like Novartis (name query)
    res = resolver.resolve("Novartis")

    # Then: Resolves correctly using cached dynamic fallback
    assert res == "NOTd1_EQ"
    assert os.path.exists(cache_file)


def test_resolver_not_found(mock_client, tmp_path):
    # Given: Resolver with empty cache path and mocked client response
    cache_file = str(tmp_path / "empty_instruments.json")
    resolver = Trading212TickerResolver(mock_client, cache_paths=[cache_file])
    resolver.instruments = []
    mock_client.get_instruments = MagicMock(return_value=[])

    # When: Resolving nonexistent asset
    # Then: Raises ValueError
    with pytest.raises(ValueError) as excinfo:
        resolver.resolve("NONEXISTENT_STOCK")
    assert "Could not resolve Trading 212 ticker" in str(excinfo.value)



# =====================================================================
# PORTFOLIO BOOTSTRAPPER TESTS
# =====================================================================

def test_bootstrapper_all_held(mock_client):
    # Given: Portfolio has all 21 micro positions already opened
    resolver = Trading212TickerResolver(mock_client)
    bootstrapper = Trading212Bootstrapper(mock_client, resolver)
    
    target_tickers = bootstrapper.get_target_tickers()
    
    # Mock positions returns all targets
    mock_positions = [{"instrument": {"ticker": ticker}, "quantity": 0.0001} for ticker in target_tickers]
    mock_client.get_positions = MagicMock(return_value=mock_positions)
    mock_client.get_pending_orders = MagicMock(return_value=[])
    mock_client.place_market_order = MagicMock()

    # When: Running bootstrap
    placed = bootstrapper.bootstrap()

    # Then: No buy order is placed
    assert len(placed) == 0
    mock_client.place_market_order.assert_not_called()


def test_bootstrapper_missing_placed(mock_client):
    # Given: Portfolio is missing SAPd_EQ, no pending order
    resolver = Trading212TickerResolver(mock_client)
    bootstrapper = Trading212Bootstrapper(mock_client, resolver)
    
    target_tickers = bootstrapper.get_target_tickers()
    assert "SAPd_EQ" in target_tickers
    
    # Mock positions returns all targets EXCEPT SAPd_EQ
    mock_positions = [{"instrument": {"ticker": ticker}, "quantity": 0.0001} for ticker in target_tickers if ticker != "SAPd_EQ"]
    mock_client.get_positions = MagicMock(return_value=mock_positions)
    mock_client.get_pending_orders = MagicMock(return_value=[])
    mock_client.place_market_order = MagicMock(return_value={"id": 123, "status": "NEW"})

    # When: Running bootstrap
    placed = bootstrapper.bootstrap()

    # Then: Place market order is called for SAPd_EQ
    assert len(placed) == 1
    assert placed[0] == "SAPd_EQ"
    mock_client.place_market_order.assert_called_once_with("SAPd_EQ", 0.0001)


def test_bootstrapper_pending_skipped(mock_client):
    # Given: Portfolio is missing SAPd_EQ, but a pending buy order exists
    resolver = Trading212TickerResolver(mock_client)
    bootstrapper = Trading212Bootstrapper(mock_client, resolver)
    
    target_tickers = bootstrapper.get_target_tickers()
    
    mock_positions = [{"instrument": {"ticker": ticker}, "quantity": 0.0001} for ticker in target_tickers if ticker != "SAPd_EQ"]
    mock_client.get_positions = MagicMock(return_value=mock_positions)
    
    # Pending order exists for SAPd_EQ
    mock_orders = [{"ticker": "SAPd_EQ", "side": "BUY", "status": "NEW"}]
    mock_client.get_pending_orders = MagicMock(return_value=mock_orders)
    mock_client.place_market_order = MagicMock()

    # When: Running bootstrap
    placed = bootstrapper.bootstrap()

    # Then: SAPd_EQ is skipped to avoid double buying
    assert len(placed) == 0
    mock_client.place_market_order.assert_not_called()


# =====================================================================
# PRICE INGESTOR TESTS
# =====================================================================

def test_ingestor_success(mock_client, tmp_path):
    # Given: Price ingestor with dummy cache path and mock positions
    cache_file = str(tmp_path / "prices.json")
    ingestor = Trading212PriceIngestor(mock_client, cache_path=cache_file)
    
    mock_positions = [
        {"instrument": {"ticker": "SAPd_EQ"}, "currentPrice": 185.5},
        {"instrument": {"ticker": "TIMd_EQ"}, "price": 25.2}
    ]
    mock_client.get_positions = MagicMock(return_value=mock_positions)

    # When: Running poll and cache
    prices = ingestor.poll_and_cache()

    # Then: Prices are resolved, stored in dictionary, and cached to file
    assert prices == {"SAPd_EQ": 185.5, "TIMd_EQ": 25.2}
    assert os.path.exists(cache_file)
    with open(cache_file, "r") as f:
        cached_data = json.load(f)
    assert cached_data == {"SAPd_EQ": 185.5, "TIMd_EQ": 25.2}


def test_ingestor_empty(mock_client, tmp_path):
    # Given: Price ingestor and empty positions return
    cache_file = str(tmp_path / "prices.json")
    ingestor = Trading212PriceIngestor(mock_client, cache_path=cache_file)
    
    mock_client.get_positions = MagicMock(return_value=[])

    # When: Running poll
    prices = ingestor.poll_and_cache()

    # Then: Prices dictionary is empty, cache file not created
    assert prices == {}
    assert not os.path.exists(cache_file)


# =====================================================================
# POSITION TRACKER TESTS
# =====================================================================

def test_tracker_filtering(mock_client):
    # Given: Portfolio has real positions and micro monitoring positions
    tracker = Trading212PositionTracker(mock_client)
    
    mock_positions = [
        {"instrument": {"ticker": "SAPd_EQ"}, "quantity": 10.0},
        {"instrument": {"ticker": "TIMd_EQ"}, "quantity": 0.0001},
        {"instrument": {"ticker": "NOVCd_EQ"}, "quantity": 0.00005},
        {"instrument": {"ticker": "EVDd_EQ"}, "quantity": 5.5}
    ]
    mock_client.get_positions = MagicMock(return_value=mock_positions)

    # When: Tracking positions
    real_pos = tracker.get_real_positions()
    micro_pos = tracker.get_micro_positions()

    # Then: Real positions filter matches quantity threshold (> 0.0001)
    assert len(real_pos) == 2
    assert real_pos[0]["instrument"]["ticker"] == "SAPd_EQ"
    assert real_pos[1]["instrument"]["ticker"] == "EVDd_EQ"
    
    # Then: Micro positions filter matches quantity threshold (<= 0.0001)
    assert len(micro_pos) == 2
    assert micro_pos[0]["instrument"]["ticker"] == "TIMd_EQ"
    assert micro_pos[1]["instrument"]["ticker"] == "NOVCd_EQ"


# =====================================================================
# DEPLOYMENT & INTEGRATION TESTS
# =====================================================================

def test_ingestor_env_cache_path(mock_client):
    # Given: T212_PRICE_CACHE_PATH is set in environment
    with patch.dict(os.environ, {"T212_PRICE_CACHE_PATH": "/tmp/custom_env_path.json"}):
        # When: Ingestor is initialized without explicit cache_path
        ingestor = Trading212PriceIngestor(mock_client)
        # Then: cache_path matches env var
        assert ingestor.cache_path == "/tmp/custom_env_path.json"


def test_ingestor_graceful_shutdown(mock_client, tmp_path):
    # Given: Price ingestor
    cache_file = str(tmp_path / "prices.json")
    ingestor = Trading212PriceIngestor(mock_client, cache_path=cache_file)
    mock_client.get_positions = MagicMock(return_value=[])

    # When: Running loop, but a thread sets _running = False or we interrupt immediately
    # We mock poll_and_cache to change _running to False to simulate signal received
    original_poll = ingestor.poll_and_cache
    def mock_poll():
        ingestor._running = False
        return original_poll()
        
    ingestor.poll_and_cache = mock_poll

    # start_loop should terminate immediately after one poll
    ingestor.start_loop(interval_seconds=1)
    
    # Then: Loop stops cleanly without hanging
    assert ingestor._running is False


def test_run_ingestor_web_app():
    from run_ingestor import health_check, get_prices
    import run_ingestor
    
    # Given: We mock run_ingestor's ingestor instance
    mock_ing = MagicMock()
    mock_ing.read_cache.return_value = {"AAPL": 150.0}
    run_ingestor.ingestor = mock_ing
    
    # When: Calling health_check
    resp_health = health_check()
    # Then: Health is OK
    assert resp_health == {"status": "healthy"}
    
    # When: Calling get_prices
    resp_prices = get_prices()
    # Then: Prices are returned
    assert resp_prices == {"AAPL": 150.0}


def test_bootstrapper_env_quantity(mock_client):
    resolver = Trading212TickerResolver(mock_client)
    # Given: T212_BOOTSTRAP_QTY is set in environment
    with patch.dict(os.environ, {"T212_BOOTSTRAP_QTY": "0.015"}):
        bootstrapper = Trading212Bootstrapper(mock_client, resolver)
        # Then: micro_qty is resolved to the env value
        assert bootstrapper.micro_qty == 0.015


def test_tracker_env_threshold(mock_client):
    # Given: T212_MICRO_POSITION_THRESHOLD is set in environment
    with patch.dict(os.environ, {"T212_MICRO_POSITION_THRESHOLD": "0.005"}):
        tracker = Trading212PositionTracker(mock_client)
        # Then: micro_threshold matches env value
        assert tracker.micro_threshold == 0.005

    # Given: Only T212_BOOTSTRAP_QTY is set in environment
    with patch.dict(os.environ, {"T212_BOOTSTRAP_QTY": "0.02"}):
        tracker = Trading212PositionTracker(mock_client)
        # Then: micro_threshold falls back to T212_BOOTSTRAP_QTY value
        assert tracker.micro_threshold == 0.02
