import pytest
from fastapi.testclient import TestClient
import time

# Given: FastAPI apps imported from runners
from run_ingestor import app as ingestor_app
from run_paper_trader import app as paper_trader_app

def test_ingestor_keep_alive():
    # Given: Ingestor TestClient
    client = TestClient(ingestor_app)
    
    # When: Querying /keep-alive
    response = client.get("/keep-alive")
    
    # Then: Expect status 200 and dynamic timestamp
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data
    assert isinstance(data["timestamp"], (int, float))
    assert time.time() - data["timestamp"] < 10  # check it's recent

def test_paper_trader_keep_alive():
    # Given: Paper Trader TestClient
    client = TestClient(paper_trader_app)
    
    # When: Querying /keep-alive
    response = client.get("/keep-alive")
    
    # Then: Expect status 200 and dynamic timestamp
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data
    assert isinstance(data["timestamp"], (int, float))
    assert time.time() - data["timestamp"] < 10  # check it's recent
