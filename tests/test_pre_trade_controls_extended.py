import pytest
import os
import hashlib
from decimal import Decimal
from unittest.mock import patch, MagicMock

from backtest_engine.live.controls import PreTradeController, PreTradeControlError
from backtest_engine.live.bybit.config import BybitConfig
from backtest_engine.live.trading212.config import Trading212Config


# ---------------------------------------------------------
# 1. API Key Hash Validation and Failsafes Tests
# ---------------------------------------------------------

def test_bybit_config_failsafe_live_no_expected_hash():
    """
    Given a BybitConfig configured for 'live' environment
    When it is validated but the expected live key hash environment variable is missing
    Then it should raise a ValueError (fail-fast)
    """
    with patch.dict(os.environ, {
        "BYBIT_ENV": "live",
        "BYBIT_LIVE_API_KEY": "somekey",
        "BYBIT_LIVE_API_SECRET": "somesecret",
        "EXPECTED_BYBIT_LIVE_KEY_HASH": "" # Empty
    }, clear=True):
        config = BybitConfig(dotenv_path="/nonexistent")
        with pytest.raises(ValueError) as excinfo:
            config.validate()
        assert "EXPECTED_BYBIT_LIVE_KEY_HASH is not set" in str(excinfo.value)


def test_bybit_config_failsafe_live_hash_mismatch():
    """
    Given a BybitConfig configured for 'live' environment
    When validated and the key hash does not match the expected live key hash
    Then it should raise a ValueError
    """
    key = "somelivekey"
    correct_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()

    with patch.dict(os.environ, {
        "BYBIT_ENV": "live",
        "BYBIT_LIVE_API_KEY": key,
        "BYBIT_LIVE_API_SECRET": "somesecret",
        "EXPECTED_BYBIT_LIVE_KEY_HASH": correct_hash + "diff" # incorrect hash
    }, clear=True):
        config = BybitConfig(dotenv_path="/nonexistent")
        with pytest.raises(ValueError) as excinfo:
            config.validate()
        assert "does not match EXPECTED_BYBIT_LIVE_KEY_HASH" in str(excinfo.value)


def test_bybit_config_failsafe_live_success():
    """
    Given a BybitConfig configured for 'live' environment
    When validated and the key hash matches the expected live key hash
    Then it should pass validation without raising errors
    """
    key = "somelivekey"
    correct_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()

    with patch.dict(os.environ, {
        "BYBIT_ENV": "live",
        "BYBIT_LIVE_API_KEY": key,
        "BYBIT_LIVE_API_SECRET": "somesecret",
        "EXPECTED_BYBIT_LIVE_KEY_HASH": correct_hash
    }, clear=True):
        config = BybitConfig(dotenv_path="/nonexistent")
        config.validate() # Should not raise any error


def test_t212_config_failsafe_live_no_expected_hash():
    """
    Given a Trading212Config configured for 'live' environment
    When validated but the expected live secret hash environment variable is missing
    Then it should raise a ValueError (fail-fast)
    """
    with patch.dict(os.environ, {
        "T212_ENV": "live",
        "T212_LIVE_API_KEY_ID": "somekeyid",
        "T212_LIVE_API_SECRET": "somesecret",
        "EXPECTED_T212_LIVE_KEY_HASH": "" # Empty
    }, clear=True):
        config = Trading212Config(dotenv_path="/nonexistent")
        with pytest.raises(ValueError) as excinfo:
            config.validate()
        assert "EXPECTED_T212_LIVE_KEY_HASH is not set" in str(excinfo.value)


def test_t212_config_failsafe_live_hash_mismatch():
    """
    Given a Trading212Config configured for 'live' environment
    When validated and the secret hash does not match the expected live secret hash
    Then it should raise a ValueError
    """
    secret = "somelivesecret"
    correct_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()

    with patch.dict(os.environ, {
        "T212_ENV": "live",
        "T212_LIVE_API_KEY_ID": "somekeyid",
        "T212_LIVE_API_SECRET": secret,
        "EXPECTED_T212_LIVE_KEY_HASH": correct_hash + "diff" # incorrect hash
    }, clear=True):
        config = Trading212Config(dotenv_path="/nonexistent")
        with pytest.raises(ValueError) as excinfo:
            config.validate()
        assert "does not match EXPECTED_T212_LIVE_KEY_HASH" in str(excinfo.value)


# ---------------------------------------------------------
# 2. Pre-Trade Controls Strict Validations (C-03)
# ---------------------------------------------------------

def test_ptc_check_limits_missing_nav():
    """
    Given a PreTradeController
    When calling check_limits with zero or negative NAV
    Then it should raise PreTradeControlError instead of defaulting
    """
    ptc = PreTradeController()
    with pytest.raises(PreTradeControlError) as excinfo:
        ptc.check_limits(
            ticker="AAPL",
            quantity=Decimal("10"),
            price=Decimal("150.0"),
            current_nav=Decimal("0.0"), # Invalid NAV
            current_position_qty=Decimal("0"),
            reference_price=Decimal("150.0")
        )
    assert "Fresh positive NAV and reference price are required" in str(excinfo.value)


def test_ptc_check_limits_missing_reference_price():
    """
    Given a PreTradeController
    When calling check_limits with None or zero reference_price
    Then it should raise PreTradeControlError
    """
    ptc = PreTradeController()
    with pytest.raises(PreTradeControlError) as excinfo:
        ptc.check_limits(
            ticker="AAPL",
            quantity=Decimal("10"),
            price=Decimal("150.0"),
            current_nav=Decimal("100000.0"),
            current_position_qty=Decimal("0"),
            reference_price=None # Invalid reference price
        )
    assert "Fresh independent reference price is required" in str(excinfo.value)


def test_ptc_check_limits_volume_violated():
    """
    Given a PreTradeController with 10% max trade limit
    When placing an order representing 15% of NAV
    Then it should raise PreTradeControlError
    """
    ptc = PreTradeController(max_trade_pct_nav=Decimal("0.10"))
    # Order value: 15000 (15% of 100000 NAV)
    with pytest.raises(PreTradeControlError) as excinfo:
        ptc.check_limits(
            ticker="AAPL",
            quantity=Decimal("100"),
            price=Decimal("150.0"),
            current_nav=Decimal("100000.0"),
            current_position_qty=Decimal("0"),
            reference_price=Decimal("150.0")
        )
    assert "Volumetric Limit Violated" in str(excinfo.value)


def test_ptc_check_limits_exposure_violated():
    """
    Given a PreTradeController with 30% max exposure per asset
    When placing an order that brings total exposure to 35% of NAV
    Then it should raise PreTradeControlError
    """
    ptc = PreTradeController(max_asset_pct_nav=Decimal("0.30"))
    # Current holding: 280 units @ 100 (28000 exposure)
    # Order: 50 units @ 100 (5000 value - 5% of NAV, below 10% volumetric limit).
    # Expected exposure: 33000 (33% of 100000 NAV, above 30% exposure limit)
    with pytest.raises(PreTradeControlError) as excinfo:
        ptc.check_limits(
            ticker="AAPL",
            quantity=Decimal("50"),
            price=Decimal("100.0"),
            current_nav=Decimal("100000.0"),
            current_position_qty=Decimal("280"),
            reference_price=Decimal("100.0")
        )
    assert "Notional Exposure Limit Violated" in str(excinfo.value)


def test_ptc_check_limits_price_collar_violated():
    """
    Given a PreTradeController with 3% price collar limit
    When placing an order with 4% deviation from reference price
    Then it should raise PreTradeControlError
    """
    ptc = PreTradeController(price_collar_pct=Decimal("0.03"))
    # Reference price: 100. Order price: 104 (4% deviation)
    with pytest.raises(PreTradeControlError) as excinfo:
        ptc.check_limits(
            ticker="AAPL",
            quantity=Decimal("10"),
            price=Decimal("104.0"),
            current_nav=Decimal("100000.0"),
            current_position_qty=Decimal("0"),
            reference_price=Decimal("100.0")
        )
    assert "Price Collar Violated" in str(excinfo.value)
