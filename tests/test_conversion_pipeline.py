import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from backtest_engine.live.bybit.conversion.accumulator import AccumulatorBuffer
from backtest_engine.live.bybit.conversion.margin_simulator import UTAMarginSimulator, MarginCheckResult
from backtest_engine.live.bybit.conversion.order_types import ConversionOrder, ConversionOrderStatus
from backtest_engine.live.bybit.conversion.spot_router import SpotConversionRouter
from backtest_engine.live.bybit.ingestor import BybitPriceIngestor


# ---------------------------------------------------------
# 1. Accumulator Buffer Tests
# ---------------------------------------------------------

def test_accumulator_deposit_decimal_only():
    accumulator = AccumulatorBuffer(threshold=Decimal("15.00"))
    
    # Passing float should raise TypeError
    with pytest.raises(TypeError):
        accumulator.deposit(conn=None, amount=15.0)  # type: ignore
        
    with pytest.raises(TypeError):
        accumulator.deposit(conn=None, amount="15.00")  # type: ignore


def test_accumulator_below_minimum_threshold():
    # Attempting to initialize with a threshold under 5 USDC should raise ValueError
    with pytest.raises(ValueError):
        AccumulatorBuffer(threshold=Decimal("4.99"))


def test_accumulator_threshold_trigger():
    # Mocking database connection and cursor
    conn_mock = MagicMock()
    cur_mock = MagicMock()
    conn_mock.cursor.return_value.__enter__.return_value = cur_mock
    
    accumulator = AccumulatorBuffer(threshold=Decimal("15.00"))
    
    # 1. Deposit 10 USDC (below threshold)
    cur_mock.fetchone.return_value = (Decimal("10.00"),)
    balance = accumulator.deposit(conn_mock, Decimal("10.00"))
    assert balance == Decimal("10.00")
    
    should_trigger, current = accumulator.should_trigger(conn_mock)
    assert should_trigger is False
    assert current == Decimal("10.00")
    
    # 2. Deposit another 10 USDC (total 20 USDC, above threshold)
    cur_mock.fetchone.return_value = (Decimal("20.00"),)
    balance = accumulator.deposit(conn_mock, Decimal("10.00"))
    assert balance == Decimal("20.00")
    
    should_trigger, current = accumulator.should_trigger(conn_mock)
    assert should_trigger is True
    assert current == Decimal("20.00")


# ---------------------------------------------------------
# 2. Margin Simulator Tests
# ---------------------------------------------------------

def test_margin_simulator_no_positions():
    client_mock = MagicMock()
    # Mock response from get_account_summary
    client_mock.config.base_currency = "USDC"
    client_mock.get_account_summary.return_value = {
        "retCode": 0,
        "result": {
            "list": [
                {
                    "totalEquity": "10000.00",
                    "totalMaintenanceMargin": "0.00",
                    "totalAvailableBalance": "10000.00"
                }
            ]
        }
    }
    
    sim = UTAMarginSimulator(client_mock)
    state = sim.fetch_margin_state()
    assert state.total_equity == Decimal("10000.00")
    assert state.total_maintenance_margin == Decimal("0.00")
    
    # Pre-trade check should be safe since there are no open positions (MM = 0)
    result = sim.check_conversion_safety(Decimal("5000.00"))
    assert result.is_safe is True
    assert result.headroom == Decimal("5000.00")  # (10000 - 5000) - (0 * 1.2)


def test_margin_simulator_safe():
    client_mock = MagicMock()
    client_mock.config.base_currency = "USDC"
    client_mock.get_account_summary.return_value = {
        "retCode": 0,
        "result": {
            "list": [
                {
                    "totalEquity": "10000.00",
                    "totalMaintenanceMargin": "2000.00",
                    "totalAvailableBalance": "8000.00"
                }
            ]
        }
    }
    
    sim = UTAMarginSimulator(client_mock)
    # Check conversion of 1000 USDC
    # post_equity = 9000, required_min = 2000 * 1.2 = 2400.
    # 9000 > 2400 -> Safe
    result = sim.check_conversion_safety(Decimal("1000.00"))
    assert result.is_safe is True
    assert result.headroom == Decimal("6600.00")  # 9000 - 2400


def test_margin_simulator_unsafe_blocks():
    client_mock = MagicMock()
    client_mock.config.base_currency = "USDC"
    client_mock.get_account_summary.return_value = {
        "retCode": 0,
        "result": {
            "list": [
                {
                    "totalEquity": "5000.00",
                    "totalMaintenanceMargin": "4000.00",
                    "totalAvailableBalance": "1000.00"
                }
            ]
        }
    }
    
    sim = UTAMarginSimulator(client_mock)
    # Check conversion of 1000 USDC
    # post_equity = 4000, required_min = 4000 * 1.2 = 4800.
    # 4000 < 4800 -> Unsafe! Blocks conversion
    result = sim.check_conversion_safety(Decimal("1000.00"))
    assert result.is_safe is False
    assert result.headroom == Decimal("-800.00")
    assert sim.is_locked is True


def test_margin_check_with_volatile_drop():
    client_mock = MagicMock()
    client_mock.config.base_currency = "USDC"
    
    # 30% drop simulation (equity goes from 10000 to 7000, while MM stays at 5000)
    client_mock.get_account_summary.return_value = {
        "retCode": 0,
        "result": {
            "list": [
                {
                    "totalEquity": "7000.00",
                    "totalMaintenanceMargin": "5000.00",
                    "totalAvailableBalance": "2000.00"
                }
            ]
        }
    }
    
    sim = UTAMarginSimulator(client_mock)
    # post_equity = 7000 - 15 = 6985. required_min = 5000 * 1.2 = 6000.
    # 6985 > 6000 -> Safe but headroom is tight (985)
    result = sim.check_conversion_safety(Decimal("15.00"))
    assert result.is_safe is True
    assert result.headroom == Decimal("985.00")
    
    # Converting 1200 USDC:
    # post_equity = 7000 - 1200 = 5800. required_min = 6000.
    # 5800 < 6000 -> Unsafe!
    result_large = sim.check_conversion_safety(Decimal("1200.00"))
    assert result_large.is_safe is False


# ---------------------------------------------------------
# 3. Spot Router & Order Types Tests
# ---------------------------------------------------------

def test_spot_router_payload_structure():
    order = ConversionOrder(qty_usdc=Decimal("150.00"))
    payload = order.to_bybit_payload()
    
    assert payload["category"] == "spot"
    assert payload["symbol"] == "EURUSDC"
    assert payload["side"] == "Buy"
    assert payload["orderType"] == "Market"
    assert payload["qty"] == "150.00"
    assert payload["marketUnit"] == "quoteCoin"
    assert payload["orderLinkId"] == order.client_order_id


def test_spot_router_dry_run():
    conn_mock = MagicMock()
    cur_mock = MagicMock()
    conn_mock.cursor.return_value.__enter__.return_value = cur_mock
    
    accumulator_mock = MagicMock()
    accumulator_mock.should_trigger.return_value = (True, Decimal("20.00"))
    
    margin_sim_mock = MagicMock()
    margin_sim_mock.is_locked = False
    margin_sim_mock.check_conversion_safety.return_value = MarginCheckResult(
        is_safe=True,
        margin_state=None,  # type: ignore
        post_conversion_equity=Decimal("0"),
        required_minimum=Decimal("0"),
        headroom=Decimal("0"),
        reason=""
    )
    
    client_mock = MagicMock()
    
    router = SpotConversionRouter(
        client_mock, accumulator_mock, margin_sim_mock, dry_run=True
    )
    
    order = router.try_convert(conn_mock)
    assert order is not None
    assert order.status == ConversionOrderStatus.FILLED
    assert order.qty_usdc == Decimal("20.00")
    # In dry-run, we drain the accumulator
    accumulator_mock.drain.assert_called_once_with(conn_mock, order.client_order_id)
    # We shouldn't call Bybit API in dry-run
    client_mock._request.assert_not_called()


def test_spot_router_idempotent_recovery():
    conn_mock = MagicMock()
    cur_mock = MagicMock()
    conn_mock.cursor.return_value.__enter__.return_value = cur_mock
    
    accumulator_mock = MagicMock()
    accumulator_mock.should_trigger.return_value = (True, Decimal("20.00"))
    
    margin_sim_mock = MagicMock()
    margin_sim_mock.is_locked = False
    margin_sim_mock.check_conversion_safety.return_value = MarginCheckResult(
        is_safe=True,
        margin_state=None,  # type: ignore
        post_conversion_equity=Decimal("0"),
        required_minimum=Decimal("0"),
        headroom=Decimal("0"),
        reason=""
    )
    
    client_mock = MagicMock()
    # Simulate API returns 110071 (duplicate orderLinkId) on post
    response_post_mock = MagicMock()
    response_post_mock.json.return_value = {
        "retCode": 110071,
        "retMsg": "Duplicate orderLinkId"
    }
    
    # Simulate realtime order query returns the filled order details
    response_get_mock = MagicMock()
    response_get_mock.json.return_value = {
        "retCode": 0,
        "result": {
            "list": [
                {
                    "orderId": "bybit_order_123",
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
    
    order = router.try_convert(conn_mock)
    assert order is not None
    assert order.status == ConversionOrderStatus.FILLED
    assert order.broker_order_id == "bybit_order_123"
    assert order.filled_qty_eur == Decimal("18.50")
    assert order.avg_fill_price == Decimal("1.08")
    
    # Real order fill drains the accumulator
    accumulator_mock.drain.assert_called_once_with(conn_mock, order.client_order_id)


# ---------------------------------------------------------
# 4. Symbol Resolution & Type Safety Tests
# ---------------------------------------------------------

def test_usdc_migration_symbol_resolution():
    client_mock = MagicMock()
    client_mock.config.base_currency = "USDC"
    
    with patch.dict("os.environ", {"BYBIT_ASSETS": "LTC,DOT,BTC"}):
        ingestor = BybitPriceIngestor(client_mock)
        assert ingestor.symbols == ["LTCUSDC", "DOTUSDC", "BTCUSDC"]
        
    client_mock.config.base_currency = "USDT"
    with patch.dict("os.environ", {"BYBIT_ASSETS": "LTC,DOT"}):
        ingestor = BybitPriceIngestor(client_mock)
        assert ingestor.symbols == ["LTCUSDT", "DOTUSDT"]


def test_no_float_in_critical_path():
    # Grep-like test to verify that the conversion package does not contain 'float('
    import os
    import re
    
    conversion_dir = os.path.join(
        os.path.dirname(__file__), "../backtest_engine/live/bybit/conversion"
    )
    float_pattern = re.compile(r"\bfloat\(")
    
    for root, _, files in os.walk(conversion_dir):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    matches = float_pattern.findall(content)
                    assert not matches, f"Forbidden usage of float() found in {path}"
