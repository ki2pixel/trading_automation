import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from backtest_engine.live.paper_trading.engine import PaperTradingEngine
from backtest_engine.live.paper_trading.api import router, _get_evaluations_sync
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()
app.include_router(router)
client = TestClient(app)

class TestPaperTradingLogging:

    def test_log_evaluation_inserts_data(self):
        # Mock DB connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        engine = PaperTradingEngine(db_url="sqlite:///:memory:")
        
        # Test basic logging
        engine._log_evaluation(
            mock_conn,
            strategy_name="cybernetic_hilbert",
            asset="AAPL",
            timeframe="15m",
            price=Decimal("150.50"),
            signal_type="ENTRY",
            signal_triggered=True,
            status="EXECUTED",
            fail_reason=None,
            details={"kelly_size": Decimal("1000.00"), "indicators": {"rsi": 45.2}}
        )

        # Verify SQL statement execution
        mock_cursor.execute.assert_called_once()
        args, kwargs = mock_cursor.execute.call_args
        
        assert "INSERT INTO paper_evaluations" in args[0]
        # Check params (timestamp is CURRENT_TIMESTAMP)
        params = args[1]
        assert params[0] == "cybernetic_hilbert"
        assert params[1] == "AAPL"
        assert params[2] == "15m"
        assert params[3] == 150.50
        assert params[4] == "ENTRY"
        assert params[5] is True
        assert params[6] == "EXECUTED"
        assert params[7] is None
        # Check details is formatted properly as JSON string and Decimal converted to float
        import json
        details = json.loads(params[8])
        assert details["kelly_size"] == 1000.0
        assert details["indicators"]["rsi"] == 45.2

    @patch('backtest_engine.live.paper_trading.api.get_db_connection')
    def test_api_get_evaluations(self, mock_get_db_connection):
        # Mock DB connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db_connection.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock fetchall returns
        import datetime
        mock_cursor.fetchall.return_value = [
            (1, datetime.datetime(2026, 6, 30, 14, 0, 0), "cybernetic_hilbert", "AAPL", "15m", Decimal("150.50"), "ENTRY", True, "EXECUTED", None, {"kelly_size": 1000.0})
        ]

        response = client.get("/api/evaluations?limit=50&status=EXECUTED&asset=AAPL")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["strategy_name"] == "cybernetic_hilbert"
        assert data[0]["asset"] == "AAPL"
        assert data[0]["timeframe"] == "15m"
        assert data[0]["price"] == 150.50
        assert data[0]["signal_type"] == "ENTRY"
        assert data[0]["signal_triggered"] is True
        assert data[0]["status"] == "EXECUTED"
        assert data[0]["fail_reason"] is None
        assert data[0]["details"] == {"kelly_size": 1000.0}

        # Check execute was called with correct filter parameters
        mock_cursor.execute.assert_called_once()
        args = mock_cursor.execute.call_args[0]
        assert "status = %s" in args[0]
        assert "asset = %s" in args[0]
        assert args[1] == ("EXECUTED", "AAPL", 50)
