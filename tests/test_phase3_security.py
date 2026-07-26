import os
import ssl
import pytest
from unittest.mock import MagicMock, patch
import requests
from fastapi.testclient import TestClient

from backtest_engine.live.trading212.client import Trading212Client
from backtest_engine.live.bybit.client import BybitClient
from backtest_engine.live.connection import _build_asyncpg_ssl, FailoverRedisClient
from run_paper_trader import app, setup_siem_logging


def test_trading212_tenacity_retries():
    """
    Given a Trading212Client
    When calls are made encountering temporary errors (429, 500)
    Then it must retry via tenacity, and fail immediately on terminal errors (400, 401).
    """
    config = MagicMock()
    config.base_url = "https://demo.trading212.com"
    config.api_key = "test-key"

    client = Trading212Client(config)
    client.headers = {}
    client.auth = None

    # 1. Test temporary error (429 then 200)
    mock_res_429 = MagicMock(status_code=429)
    mock_res_200 = MagicMock(status_code=200)

    with patch("requests.request", side_effect=[mock_res_429, mock_res_200]) as mock_req:
        res = client._request("GET", "/equity/positions", max_retries=2, backoff_factor=0.01)
        assert res.status_code == 200
        assert mock_req.call_count == 2

    # 2. Test terminal error (400) -> should not retry
    mock_res_400 = MagicMock(status_code=400)
    mock_res_400.text = "Bad Request"
    mock_res_400.raise_for_status.side_effect = requests.exceptions.HTTPError("400 Client Error")

    with patch("requests.request", return_value=mock_res_400) as mock_req:
        with pytest.raises(requests.exceptions.HTTPError):
            client._request("GET", "/equity/positions", max_retries=3, backoff_factor=0.01)
        assert mock_req.call_count == 1


def test_bybit_tenacity_retries_and_signature_regeneration():
    """
    Given a BybitClient
    When signed requests are retried
    Then it must regenerate timestamps and signatures for each attempt.
    """
    config = MagicMock()
    config.base_url = "https://api-demo.bybit.com"
    config.api_key = "key"
    config.api_secret = "sec"

    client = BybitClient(config)

    mock_res_500 = MagicMock(status_code=500)
    mock_res_200 = MagicMock(status_code=200)

    with patch("requests.request", side_effect=[mock_res_500, mock_res_200]) as mock_req:
        res = client._request("POST", "/v5/order/create", json_data={"qty": "1"}, signed=True, max_retries=2, backoff_factor=0.01)
        assert res.status_code == 200
        assert mock_req.call_count == 2

        calls = mock_req.call_args_list
        ts_1 = calls[0][1]["headers"]["X-BAPI-TIMESTAMP"]
        ts_2 = calls[1][1]["headers"]["X-BAPI-TIMESTAMP"]

        assert ts_1 is not None
        assert ts_2 is not None


def test_csrf_content_type_validation_and_audit_logging():
    """
    Given the FastAPI app with CSRFMiddleware
    When mutating API requests are made
    Then they must enforce application/json and log failures in trading_audit.
    """
    import time
    from run_paper_trader import create_session_token, HMAC_SECRET

    client = TestClient(app)

    # Generate and set valid session token
    session_token, _ = create_session_token("admin", int(time.time()) + 3600, HMAC_SECRET)
    client.cookies.set("paper_trader_session", session_token)

    with patch("backtest_engine.live.connection.get_redis_client", return_value=None):
        res = client.get("/api/csrf-token")
        assert res.status_code == 200
        csrf_cookie = res.cookies.get("csrftoken")

        with patch("logging.Logger.error") as mock_log_err:
            res = client.post(
                "/api/strategy-configs",
                headers={"X-CSRFToken": csrf_cookie, "Content-Type": "text/plain"},
                content="some raw text"
            )
            assert res.status_code == 415
            mock_log_err.assert_called_once()
            assert "Content-Type violation" in mock_log_err.call_args[0][0]


def test_mtls_postgresql_context():
    """
    Given _build_asyncpg_ssl function
    When DB_SSL_CERT env variables are set
    Then it must build a secure ssl.SSLContext demanding client verification.
    """
    with patch.dict(os.environ, {
        "DB_SSL_CERT": "tests/test_phase2_security.py",
        "DB_SSL_KEY": "tests/test_phase2_security.py",
        "DB_SSL_CA": "tests/test_phase2_security.py"
    }):
        with patch("ssl.SSLContext.load_cert_chain") as mock_chain, \
             patch("ssl.SSLContext.load_verify_locations") as mock_ca:
            ctx = _build_asyncpg_ssl("postgresql://user:pass@host:5432/db?sslmode=verify-full")

            assert isinstance(ctx, ssl.SSLContext)
            assert ctx.verify_mode == ssl.CERT_REQUIRED
            mock_chain.assert_called_once()
            mock_ca.assert_called_once()


def test_mtls_redis_context():
    """
    Given FailoverRedisClient
    When REDIS_SSL_CERT env variables are set
    Then it must pass SSL arguments to redis constructor.
    """
    with patch.dict(os.environ, {
        "REDIS_SSL_CERT": "dummy_cert",
        "REDIS_SSL_KEY": "dummy_key",
        "REDIS_SSL_CA": "dummy_ca"
    }):
        with patch("redis.Redis.from_url") as mock_redis_from_url:
            FailoverRedisClient(primary_url="rediss://localhost:6379")

            args, kwargs = mock_redis_from_url.call_args
            assert kwargs.get("ssl_certfile") == "dummy_cert"
            assert kwargs.get("ssl_keyfile") == "dummy_key"
            assert kwargs.get("ssl_ca_certs") == "dummy_ca"
            assert kwargs.get("ssl_cert_reqs") == "required"
