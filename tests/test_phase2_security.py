import os
import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from decimal import Decimal
from fastapi.testclient import TestClient

# Import components
from backtest_engine.live.controls import PreTradeController, PreTradeControlError
from backtest_engine.live.kill_switch import KillSwitchListener, is_trading_suspended, set_trading_suspended
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
async def test_kill_switch_trigger():
    """
    Given a KillSwitchListener
    When trigger_kill is executed
    Then it must set trading suspension and cancel Bybit & Trading 212 orders.
    """
    set_trading_suspended(False)
    
    mock_engine = MagicMock()
    mock_bybit = MagicMock()
    mock_t212 = MagicMock()
    mock_engine.bybit_client = mock_bybit
    mock_engine.t212_client = mock_t212
    
    mock_t212.get_pending_orders.return_value = [
        {"orderId": "order-123", "ticker": "AAPL"},
        {"orderId": "order-456", "ticker": "MSFT"}
    ]
    
    mock_redis = AsyncMock()
    
    try:
        with patch("redis.asyncio.from_url", return_value=mock_redis):
            listener = KillSwitchListener(mock_engine, redis_url="redis://localhost:6379")
            await listener.trigger_kill()
            
            assert is_trading_suspended() is True
            mock_redis.set.assert_called_with("trading:suspended", "true")
            
            mock_bybit._request.assert_called_with(
                "POST",
                "/v5/order/cancel-all",
                json_data={"category": "spot"},
                signed=True
            )
            
            mock_t212.get_pending_orders.assert_called_once()
            mock_t212.cancel_order.assert_any_call("order-123")
            mock_t212.cancel_order.assert_any_call("order-456")
    finally:
        set_trading_suspended(False)


def test_fastapi_rate_limiting():
    """
    Given the FastAPI app with RedisRateLimiterMiddleware
    When multiple requests are made
    Then it must return 429 after exceeding limits.
    """
    mock_redis = MagicMock()
    mock_redis.incr.side_effect = [1, 2, 100]
    
    client = TestClient(app)
    
    with patch("backtest_engine.live.connection.get_redis_client", return_value=mock_redis):
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
        assert "Too many requests" in response.json()["detail"]
