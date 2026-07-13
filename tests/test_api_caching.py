import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Import the router to test
from backtest_engine.live.paper_trading.api import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)

class TestApiCaching:

    @patch('backtest_engine.live.paper_trading.api._get_pool')
    @patch('backtest_engine.live.connection.get_redis_client')
    def test_get_candles_caching(self, mock_get_redis_client, mock_get_pool):
        # Given: Mock Redis client & Database connection
        mock_redis = MagicMock()
        mock_get_redis_client.return_value = mock_redis
        
        # Redis key does not exist initially
        mock_redis.get.return_value = None
        
        # Mock database pool
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {
                "timestamp_minute": datetime(2023, 10, 4, 12, 0, tzinfo=timezone.utc),
                "open": 100.0,
                "high": 105.0,
                "low": 95.0,
                "close": 102.0
            }
        ])
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=False)
        
        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        mock_get_pool.return_value = mock_pool

        # When: Calling the endpoint for the first time (cache miss)
        response = client.get("/api/candles?ticker=aapl&limit=1000")
        
        # Then:
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["open"] == 100.0
        
        # Verify database was queried and cache was populated
        mock_conn.fetch.assert_called_once()
        mock_redis.get.assert_called_once_with("candles:aapl:1000")
        mock_redis.setex.assert_called_once()
        cache_key, ttl, cache_val = mock_redis.setex.call_args[0]
        assert cache_key == "candles:aapl:1000"
        assert ttl == 20
        assert "100.0" in cache_val

        # Reset mocks
        mock_conn.fetch.reset_mock()
        mock_redis.get.reset_mock()
        mock_redis.setex.reset_mock()

        # Given: Cache hit (Redis has the data)
        cached_data = [{"time": 1696420800, "open": 100.0, "high": 105.0, "low": 95.0, "close": 102.0}]
        mock_redis.get.return_value = json.dumps(cached_data)

        # When: Calling the endpoint again
        response2 = client.get("/api/candles?ticker=aapl&limit=1000")

        # Then:
        assert response2.status_code == 200
        assert response2.json() == cached_data
        # Database should NOT be queried
        mock_conn.fetch.assert_not_called()
        mock_redis.get.assert_called_once_with("candles:aapl:1000")
        mock_redis.setex.assert_not_called()

    @patch('backtest_engine.live.paper_trading.api._get_pool')
    @patch('backtest_engine.live.connection.get_redis_client')
    def test_get_performance_metrics_caching_zero_trades(self, mock_get_redis_client, mock_get_pool):
        # Given: Mock Redis client & Database connection
        mock_redis = MagicMock()
        mock_get_redis_client.return_value = mock_redis
        mock_redis.get.return_value = None
        
        mock_conn = AsyncMock()
        # 1. config_row fetchrow
        # 2. candle_rows fetch
        # 3. tx_rows fetch
        mock_conn.fetchrow = AsyncMock(return_value={"initial_capital": 1000.0})
        mock_conn.fetch = AsyncMock(side_effect=[
            # candle_rows
            [
                {
                    "timestamp_minute": datetime(2023, 10, 4, 12, 0, tzinfo=timezone.utc),
                    "open": 100.0,
                    "high": 105.0,
                    "low": 95.0,
                    "close": 102.0
                }
            ],
            # tx_rows (empty for zero trades)
            []
        ])
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=False)
        
        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        mock_get_pool.return_value = mock_pool

        # When: Calling performance metrics (zero trades)
        response = client.get("/api/performance/metrics?ticker=aapl")
        
        # Then:
        assert response.status_code == 200
        result = response.json()
        assert result["total_trades"] == 0
        
        # Redis key check should occur and cache populate even with 0 trades
        mock_redis.get.assert_called_once_with("perf_metrics:aapl")
        mock_redis.setex.assert_called_once()
        cache_key, ttl, cache_val = mock_redis.setex.call_args[0]
        assert cache_key == "perf_metrics:aapl"
        assert ttl == 300
        assert '"total_trades": 0' in cache_val
