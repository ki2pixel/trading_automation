import os
import asyncio
import json
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError as RedisConnectionError

from backtest_engine.live.controls import PreTradeController, PreTradeControlError
from backtest_engine.live.kill_switch import (
    KillSwitchListener,
    KillSwitchStateError,
    KillSwitchStatus,
    get_kill_switch_channel,
    get_kill_switch_state_key,
    get_kill_switch_status,
    is_trading_suspended,
    resume_trading,
    set_trading_suspended,
)
from run_paper_trader import app


def test_pre_trade_controls():
    """
    Given a PreTradeController
    When orders are validated
    Then it must enforce volumetric limits, notional limits, and price collars.
    """
    ptc = PreTradeController(
        max_trade_pct_nav=Decimal("0.10"),
        max_asset_pct_nav=Decimal("0.30"),
        price_collar_pct=Decimal("0.03")
    )

    current_nav = Decimal("10000.0")

    # 1. Valid order
    ptc.check_limits(
        ticker="AAPL",
        quantity=Decimal("5"),
        price=Decimal("150.0"),
        current_nav=current_nav,
        current_position_qty=Decimal("0"),
        reference_price=Decimal("150.0")
    )

    # 2. Volumetric violation (order is 15% of NAV > 10% allowed)
    with pytest.raises(PreTradeControlError) as exc_info:
        ptc.check_limits(
            ticker="AAPL",
            quantity=Decimal("10"),
            price=Decimal("150.0"),
            current_nav=current_nav,
            current_position_qty=Decimal("0"),
            reference_price=Decimal("150.0")
        )
    assert "Volumetric Limit Violated" in str(exc_info.value)

    # 3. Notional cumulative violation (total exposure is 45% of NAV > 30% allowed)
    with pytest.raises(PreTradeControlError) as exc_info:
        ptc.check_limits(
            ticker="AAPL",
            quantity=Decimal("5"),  # 750 value (7.5% of NAV) - passes volumetric check
            price=Decimal("150.0"),
            current_nav=current_nav,
            current_position_qty=Decimal("25.0"),  # 25 * 150 = 3750. Total expected: 4500 (45% NAV)
            reference_price=Decimal("150.0")
        )
    assert "Notional Exposure Limit Violated" in str(exc_info.value)

    # 4. Price Collar violation (price deviates by 5% > 3% allowed)
    with pytest.raises(PreTradeControlError) as exc_info:
        ptc.check_limits(
            ticker="AAPL",
            quantity=Decimal("5"),
            price=Decimal("157.5"),
            current_nav=current_nav,
            current_position_qty=Decimal("0"),
            reference_price=Decimal("150.0")
        )
    assert "Price Collar Violated" in str(exc_info.value)


@pytest.mark.asyncio
async def test_kill_switch_trigger_persists_namespaced_state_and_cancels_orders(monkeypatch):
    monkeypatch.setenv("PAPER_TRADER_ENV", "paper-test")
    set_trading_suspended(False)

    mock_engine = MagicMock()
    mock_bybit = MagicMock()
    mock_t212 = MagicMock()
    mock_engine.bybit_client = mock_bybit
    mock_engine.t212_client = mock_t212
    mock_t212.get_pending_orders.return_value = [
        {"orderId": "order-123", "ticker": "AAPL"},
        {"orderId": "order-456", "ticker": "MSFT"},
    ]
    mock_redis = MagicMock()

    try:
        with patch("backtest_engine.live.connection.get_redis_client", return_value=mock_redis):
            listener = KillSwitchListener(mock_engine, redis_url="redis://localhost:6379")
            await listener.trigger_kill()

        assert is_trading_suspended() is True
        state_call = next(
            call for call in mock_redis.set.call_args_list
            if call.args[0] == get_kill_switch_state_key()
        )
        state_payload = json.loads(state_call.args[1])
        assert state_payload["status"] == "suspended"
        assert state_payload["source"] == "redis_command"
        mock_redis.publish.assert_called_with(get_kill_switch_channel(), "SUSPEND")
        mock_redis.set.assert_any_call(
            "paper_trader:paper-test:kill_switch:confirmed",
            "true",
            ex=60,
        )
        mock_bybit._request.assert_called_with(
            "POST",
            "/v5/order/cancel-all",
            json_data={"category": "spot"},
            signed=True,
        )
        mock_t212.get_pending_orders.assert_called_once()
        mock_t212.cancel_order.assert_any_call("order-123")
        mock_t212.cancel_order.assert_any_call("order-456")
    finally:
        set_trading_suspended(False)


def test_kill_switch_keys_are_namespaced_by_environment(monkeypatch):
    monkeypatch.setenv("KILL_SWITCH_NAMESPACE", "Paper Test / EU")

    assert get_kill_switch_state_key() == "paper-test-eu:kill_switch:state"
    assert get_kill_switch_channel() == "paper-test-eu:kill_switch:urgency"


def test_distributed_active_state_clears_stale_local_suspension(monkeypatch):
    monkeypatch.setenv("PAPER_TRADER_ENV", "paper-test")
    set_trading_suspended(True)
    mock_redis = MagicMock()
    mock_redis.get.return_value = json.dumps(
        {
            "status": "active",
            "source": "dashboard",
            "reason": "Operator-confirmed resume",
            "event_id": "event-1",
            "updated_at": "2026-07-15T12:00:00+00:00",
        }
    )

    try:
        status = get_kill_switch_status(mock_redis)

        assert status.suspended is False
        assert status.source == "redis"
        assert is_trading_suspended() is False
        mock_redis.get.assert_called_once_with(get_kill_switch_state_key())
    finally:
        set_trading_suspended(False)


def test_legacy_distributed_state_remains_fail_closed_until_explicit_resume(monkeypatch):
    monkeypatch.setenv("PAPER_TRADER_ENV", "paper-test")
    set_trading_suspended(False)
    mock_redis = MagicMock()
    mock_redis.get.side_effect = [None, "true"]

    try:
        status = get_kill_switch_status(mock_redis)

        assert status.suspended is True
        assert status.source == "legacy"
        assert is_trading_suspended() is True
    finally:
        set_trading_suspended(False)


def test_malformed_distributed_state_fails_closed(monkeypatch):
    monkeypatch.setenv("PAPER_TRADER_ENV", "paper-test")
    mock_redis = MagicMock()
    mock_redis.get.return_value = "not-json"

    try:
        status = get_kill_switch_status(mock_redis)

        assert status.suspended is True
        assert status.healthy is False
        assert status.source == "invalid_state"
    finally:
        set_trading_suspended(False)


@pytest.mark.asyncio
async def test_resume_persists_active_state_and_notifies_workers(monkeypatch):
    monkeypatch.setenv("PAPER_TRADER_ENV", "paper-test")
    mock_redis = MagicMock()
    set_trading_suspended(True)

    try:
        with patch("backtest_engine.live.connection.get_redis_client", return_value=mock_redis):
            status = await resume_trading("dashboard")

        state_call = mock_redis.set.call_args
        state_payload = json.loads(state_call.args[1])
        assert state_call.args[0] == get_kill_switch_state_key()
        assert state_payload["status"] == "active"
        assert status.suspended is False
        assert is_trading_suspended() is False
        mock_redis.publish.assert_called_once_with(get_kill_switch_channel(), "RESUME")
    finally:
        set_trading_suspended(False)


@pytest.mark.asyncio
async def test_resume_failure_keeps_local_trading_suspended(monkeypatch):
    monkeypatch.setenv("PAPER_TRADER_ENV", "paper-test")
    mock_redis = MagicMock()
    mock_redis.set.side_effect = RedisConnectionError("offline")
    set_trading_suspended(True)

    try:
        with patch("backtest_engine.live.connection.get_redis_client", return_value=mock_redis):
            with pytest.raises(KillSwitchStateError, match="Unable to persist"):
                await resume_trading("dashboard")

        assert is_trading_suspended() is True
    finally:
        set_trading_suspended(False)


@pytest.mark.asyncio
async def test_resume_endpoint_returns_503_when_distributed_resume_fails():
    from backtest_engine.live.paper_trading.api import resume_trading as resume_endpoint

    with patch(
        "backtest_engine.live.kill_switch.resume_trading",
        new=AsyncMock(side_effect=KillSwitchStateError("offline")),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await resume_endpoint()

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Unable to synchronize the Kill Switch state. Trading remains suspended."


def test_fastapi_rate_limiting():
    """
    Given the FastAPI app with RedisRateLimiterMiddleware
    When multiple requests are made
    Then it must return 429 after exceeding limits.
    """
    class MockAsyncRedis:
        def __init__(self):
            self.calls = 0
        async def incr(self, key):
            self.calls += 1
            if self.calls == 1: return 1
            if self.calls == 2: return 2
            return 100
        async def expire(self, key, time):
            pass

    mock_redis = MockAsyncRedis()

    client = TestClient(app)

    with patch("backtest_engine.live.connection.get_async_redis_client", return_value=mock_redis):
        # /health is public and exempt from auth/rate-limiting
        response = client.get("/health")
        assert response.status_code == 200

        # /api/strategy-configs is rate-limited (and auth-limited, returning 401 but not 429 initially)
        response = client.get("/api/strategy-configs")
        assert response.status_code == 401

        response = client.get("/api/strategy-configs")
        assert response.status_code == 401

        response = client.get("/api/strategy-configs")
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json().get("error", "") or "Too many requests" in response.json().get("detail", "")
