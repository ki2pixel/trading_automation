import pytest
from fastapi.testclient import TestClient
import time
from unittest.mock import patch, MagicMock

# Given: FastAPI apps imported from runners
from run_ingestor import app as ingestor_app
from run_paper_trader import app as paper_trader_app

@patch("run_ingestor.get_redis_client")
def test_ingestor_keep_alive(mock_get_redis_client):
    # Given: Mock Redis client
    mock_redis = MagicMock()
    mock_get_redis_client.return_value = mock_redis

    # Given: Ingestor TestClient
    client = TestClient(ingestor_app)
    
    # When: Querying GET /keep-alive
    response = client.get("/keep-alive")
    
    # Then: Expect status 200 and dynamic timestamp
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data
    assert isinstance(data["timestamp"], (int, float))
    assert time.time() - data["timestamp"] < 10  # check it's recent
    
    # Then: verify that Redis set keep-alive was triggered
    mock_redis.set.assert_called_once()
    args, kwargs = mock_redis.set.call_args
    assert args[0] == "ping:keepalive"

def test_ingestor_keep_alive_head():
    # Given: Ingestor TestClient
    client = TestClient(ingestor_app)
    
    # When: Querying HEAD /keep-alive
    response = client.head("/keep-alive")
    
    # Then: Expect status 200 and empty content
    assert response.status_code == 200
    assert response.text == ""

def test_ingestor_health_get():
    # Given: Ingestor TestClient
    client = TestClient(ingestor_app)
    
    # When: Querying GET /health
    response = client.get("/health")
    
    # Then: Expect status 200 and health status check
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_ingestor_health_head():
    # Given: Ingestor TestClient
    client = TestClient(ingestor_app)
    
    # When: Querying HEAD /health
    response = client.head("/health")
    
    # Then: Expect status 200 and empty content
    assert response.status_code == 200
    assert response.text == ""

def test_paper_trader_keep_alive():
    # Given: Paper Trader TestClient
    client = TestClient(paper_trader_app)
    
    # When: Querying GET /keep-alive
    response = client.get("/keep-alive")
    
    # Then: Expect status 200 and dynamic timestamp
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data
    assert isinstance(data["timestamp"], (int, float))
    assert time.time() - data["timestamp"] < 10  # check it's recent

def test_paper_trader_keep_alive_head():
    # Given: Paper Trader TestClient
    client = TestClient(paper_trader_app)
    
    # When: Querying HEAD /keep-alive
    response = client.head("/keep-alive")
    
    # Then: Expect status 200 and empty content
    assert response.status_code == 200
    assert response.text == ""

def test_paper_trader_health_get():
    # Given: Paper Trader TestClient
    client = TestClient(paper_trader_app)
    
    # When: Querying GET /health
    response = client.get("/health")
    
    # Then: Expect status 200 and health status check
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_paper_trader_health_head():
    # Given: Paper Trader TestClient
    client = TestClient(paper_trader_app)
    
    # When: Querying HEAD /health
    response = client.head("/health")
    
    # Then: Expect status 200 and empty content
    assert response.status_code == 200
    assert response.text == ""
