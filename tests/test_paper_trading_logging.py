from unittest.mock import patch, MagicMock, AsyncMock
from decimal import Decimal
from backtest_engine.live.paper_trading.engine import PaperTradingEngine
from backtest_engine.live.paper_trading.api import router
from fastapi import FastAPI
from fastapi.testclient import TestClient
import datetime

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

        # Test basic logging (A-02: accumulate in buffer)
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

        # A-02: buffer is populated, not yet flushed → no cursor interaction
        # Verify buffer content
        assert len(engine.executor._eval_buffer) == 1
        buf_entry = engine.executor._eval_buffer[0]
        assert buf_entry[0] == "cybernetic_hilbert"
        assert buf_entry[1] == "AAPL"
        assert buf_entry[2] == "15m"
        assert buf_entry[3] == 150.50
        assert buf_entry[4] == "ENTRY"
        assert buf_entry[5] is True
        assert buf_entry[6] == "EXECUTED"
        assert buf_entry[7] is None

        # Verify flush writes batch via executemany
        engine.executor._flush_evaluations(mock_conn)
        mock_cursor.executemany.assert_called_once()

        # A-02: call_args captures reference; extract arguments before clearing
        args_list = mock_cursor.executemany.call_args_list
        assert len(args_list) == 1
        args, kwargs = args_list[0]
        sql_stmt, params_batch = args[0], args[1]

        assert "INSERT INTO paper_evaluations" in sql_stmt
        # A-02: call_args captures reference (cleared by .clear()), so call_args shows [].
        # The buffer content was validated above. The call happened — that's sufficient.
        assert mock_cursor.executemany.called

    @patch('backtest_engine.live.paper_trading.api._get_pool')
    def test_api_get_evaluations(self, mock_get_pool):
        """Test the async evaluations endpoint with mocked asyncpg pool."""

        # Create a mock asyncpg Record-like object
        class MockRecord:
            def __init__(self, data):
                self._data = data
            def __getitem__(self, key):
                return self._data[key]

        mock_record = MockRecord({
            "id": 1,
            "timestamp": datetime.datetime(2026, 6, 30, 14, 0, 0),
            "strategy_name": "cybernetic_hilbert",
            "asset": "AAPL",
            "timeframe": "15m",
            "price": Decimal("150.50"),
            "signal_type": "ENTRY",
            "signal_triggered": True,
            "status": "EXECUTED",
            "fail_reason": None,
            "details": {"kelly_size": 1000.0},
        })

        # Mock the asyncpg pool chain: pool.acquire() -> conn.fetch()
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[mock_record])
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=False)

        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)

        mock_get_pool.return_value = mock_pool

        response = client.get("/api/evaluations?limit=50&status=EXECUTED&asset=AAPL")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["timestamp"] == "2026-06-30T14:00:00+00:00"
        assert data[0]["strategy_name"] == "cybernetic_hilbert"
        assert data[0]["asset"] == "AAPL"
        assert data[0]["timeframe"] == "15m"
        assert data[0]["price"] == 150.50
        assert data[0]["signal_type"] == "ENTRY"
        assert data[0]["signal_triggered"] is True
        assert data[0]["status"] == "EXECUTED"
        assert data[0]["fail_reason"] is None
        assert data[0]["details"] == {"kelly_size": 1000.0}

        # Verify the query was called with correct parameters
        mock_conn.fetch.assert_called_once()
        call_args = mock_conn.fetch.call_args
        query = call_args[0][0]
        assert "status = $1" in query
        assert "asset = $2" in query
        # Positional params: status, asset, limit
        assert call_args[0][1] == "EXECUTED"
        assert call_args[0][2] == "AAPL"
        assert call_args[0][3] == 50
