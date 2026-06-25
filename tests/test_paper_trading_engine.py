import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backtest_engine.live.paper_trading.engine import PaperTradingEngine
from backtest_engine.live.paper_trading.api import router, ConfigUpdate

# Setup dummy FastAPI app for testing API
from fastapi import FastAPI
app = FastAPI()
app.include_router(router)
client = TestClient(app)

class TestPaperTradingEngine:
    
    @patch('backtest_engine.live.paper_trading.engine.datetime')
    def test_market_hours_open(self, mock_datetime):
        # Mocking time to be Wednesday 12:00 UTC
        from datetime import datetime
        import pytz
        
        mock_now = datetime(2023, 10, 4, 12, 0, tzinfo=pytz.utc) # Wed
        mock_datetime.now.return_value = mock_now
        
        engine = PaperTradingEngine(db_url="sqlite:///:memory:")
        # Provide dummy market hours for test
        engine.market_hours = {
            "TEST.ASSET": {
                "open": "09:00",
                "close": "17:30",
                "tz_offset": "+01:00"
            }
        }
        
        # UTC 12:00 -> +01:00 is 13:00, which is between 09:00 and 17:30
        assert engine.is_market_open("TEST.ASSET") == True

    @patch('backtest_engine.live.paper_trading.engine.datetime')
    def test_market_hours_closed_weekend(self, mock_datetime):
        from datetime import datetime
        import pytz
        
        # Mocking time to be Saturday 12:00 UTC
        mock_now = datetime(2023, 10, 7, 12, 0, tzinfo=pytz.utc) # Sat
        mock_datetime.now.return_value = mock_now
        
        engine = PaperTradingEngine(db_url="sqlite:///:memory:")
        engine.market_hours = {
            "TEST.ASSET": {
                "open": "09:00",
                "close": "17:30",
                "tz_offset": "+01:00"
            }
        }
        
        # Weekend should be false
        assert engine.is_market_open("TEST.ASSET") == False

    @patch('backtest_engine.live.paper_trading.engine.datetime')
    def test_market_hours_closed_time(self, mock_datetime):
        from datetime import datetime
        import pytz
        
        # Mocking time to be Wed 20:00 UTC -> 21:00 local (+1)
        mock_now = datetime(2023, 10, 4, 20, 0, tzinfo=pytz.utc) # Wed
        mock_datetime.now.return_value = mock_now
        
        engine = PaperTradingEngine(db_url="sqlite:///:memory:")
        engine.market_hours = {
            "TEST.ASSET": {
                "open": "09:00",
                "close": "17:30",
                "tz_offset": "+01:00"
            }
        }
        
        assert engine.is_market_open("TEST.ASSET") == False

    @patch('backtest_engine.live.paper_trading.api.get_db_connection')
    def test_api_config_update(self, mock_get_db_connection):
        # Mock DB connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        mock_cursor.rowcount = 1
        
        payload = {
            "initial_capital": 2000,
            "initial_capital_bucket": 500,
            "max_capital_bucket": 1500,
            "max_entry_price": 50,
            "is_active": False
        }
        
        response = client.put("/api/configs/1", json=payload)
        assert response.status_code == 200
        assert response.json() == {"status": "success", "message": "Configuration updated"}
        
        # Check if execute was called properly
        mock_cursor.execute.assert_called_once()
        args, kwargs = mock_cursor.execute.call_args
        
        assert "UPDATE paper_strategy_configs" in args[0]
        assert args[1] == (2000.0, 500.0, 1500.0, 50.0, False, 1)
