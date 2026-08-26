import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient
from backtest_engine.live.paper_trading.api import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

class TestTransactionsEndpoint:

    @patch('backtest_engine.live.paper_trading.api._get_pool')
    def test_tc_tr_01_get_transactions_with_asset_success(self, mock_get_pool):
        # Given: Mock DB pool with transaction record for asset 'nvo'
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [
            {
                "id": 1,
                "timestamp": datetime(2026, 8, 20, 10, 0, 0),
                "asset": "nvo",
                "strategy_name": "TestStrategy",
                "action": "BUY",
                "qty": 10.0,
                "price": 100.0,
                "total_value": 1000.0
            }
        ]
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=False)
        
        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        mock_get_pool.return_value = mock_pool

        # When: Request sent with asset parameter aligned to 5th argument
        response = client.get("/api/transactions?limit=5000&offset=0&asset=nvo")

        # Then: HTTP 200 OK and list containing asset transaction
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["asset"] == "nvo"

    @patch('backtest_engine.live.paper_trading.api._get_pool')
    def test_tc_tr_02_get_transactions_pagination_cursor_success(self, mock_get_pool):
        # Given: Mock DB pool configured for cursor-based pagination
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = []
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=False)
        
        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        mock_get_pool.return_value = mock_pool

        # When: Pagination request matching modules/logs.js with integer cursor_id
        response = client.get("/api/transactions?limit=50&offset=0&cursor_timestamp=2026-08-20T10:00:00Z&cursor_id=42")

        # Then: HTTP 200 OK without validation error
        assert response.status_code == 200
        assert response.json() == []

    def test_tc_tr_03_invalid_string_cursor_id_fails_fastapi_validation(self):
        # Given: FastAPI test client
        # When: String ticker passed mistakenly as cursor_id (reproducing bug 422)
        response = client.get("/api/transactions?limit=5000&offset=0&cursor_id=NVO")

        # Then: FastAPI Pydantic returns HTTP 422 Unprocessable Entity
        assert response.status_code == 422
        err = response.json()
        assert "detail" in err
        assert any(d.get("loc") == ["query", "cursor_id"] for d in err["detail"])

    @patch('backtest_engine.live.paper_trading.api._get_pool')
    def test_tc_tr_04_get_transactions_null_cursor_default_offset(self, mock_get_pool):
        # Given: Mock DB pool with no cursor
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = []
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=False)
        
        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        mock_get_pool.return_value = mock_pool

        # When: Default call without cursor or asset
        response = client.get("/api/transactions?limit=50&offset=0")

        # Then: HTTP 200 OK
        assert response.status_code == 200
        assert response.json() == []

    @patch('backtest_engine.live.paper_trading.api._get_pool')
    def test_tc_tr_05_limit_boundary_clamping(self, mock_get_pool):
        # Given: Mock DB pool
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = []
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=False)
        
        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        mock_get_pool.return_value = mock_pool

        # When: Calling with limit = 15000 (exceeding maximum 10000)
        response = client.get("/api/transactions?limit=15000&offset=0")

        # Then: HTTP 200 OK and limit clamped to 10000 in SQL query
        assert response.status_code == 200
        call_args = mock_conn.fetch.call_args[0]
        assert 10000 in call_args

    @patch('backtest_engine.live.paper_trading.api._get_pool')
    def test_tc_tr_06_invalid_timestamp_format_returns_400(self, mock_get_pool):
        # Given: Mock pool & FastAPI test client
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        # When: Invalid ISO timestamp passed with integer cursor_id
        response = client.get("/api/transactions?limit=50&cursor_timestamp=invalid-date&cursor_id=1")

        # Then: HTTP 400 Bad Request
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid cursor_timestamp format"
