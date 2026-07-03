import os
import base64
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

# Import the app to test
from run_paper_trader import app

client = TestClient(app)

def test_public_endpoints_no_auth():
    # health GET
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

    # health HEAD
    response = client.head("/health")
    assert response.status_code == 200
    assert response.text == ""

    # keep-alive GET
    response = client.get("/keep-alive")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"

    # keep-alive HEAD
    response = client.head("/keep-alive")
    assert response.status_code == 200
    assert response.text == ""

def test_public_endpoints_with_trailing_slash():
    # health with trailing slash
    response = client.get("/health/")
    assert response.status_code == 200

    # keep-alive with trailing slash
    response = client.get("/keep-alive/")
    assert response.status_code == 200

def test_protected_endpoints_missing_auth():
    # root static files
    response = client.get("/")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == 'Basic realm="Paper Trading Access"'

    # status endpoint
    response = client.get("/status")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == 'Basic realm="Paper Trading Access"'

    # API endpoints
    response = client.get("/api/portfolio")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == 'Basic realm="Paper Trading Access"'

def test_protected_endpoints_invalid_scheme():
    # Use Bearer token instead of Basic
    response = client.get("/status", headers={"Authorization": "Bearer token123"})
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == 'Basic realm="Paper Trading Access"'

def test_protected_endpoints_invalid_format():
    # Not base64
    response = client.get("/status", headers={"Authorization": "Basic not_base64_encoded"})
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == 'Basic realm="Paper Trading Access"'

@patch.dict(os.environ, {"PAPER_TRADER_USER": "test_user", "PAPER_TRADER_PASSWORD": "test_password"})
def test_protected_endpoints_incorrect_credentials():
    wrong_creds = base64.b64encode(b"test_user:wrong_password").decode("utf-8")
    response = client.get("/status", headers={"Authorization": f"Basic {wrong_creds}"})
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == 'Basic realm="Paper Trading Access"'

    wrong_user = base64.b64encode(b"wrong_user:test_password").decode("utf-8")
    response = client.get("/status", headers={"Authorization": f"Basic {wrong_user}"})
    assert response.status_code == 401

@patch.dict(os.environ, {"PAPER_TRADER_USER": "test_user", "PAPER_TRADER_PASSWORD": "test_password"})
def test_protected_endpoints_correct_credentials():
    correct_creds = base64.b64encode(b"test_user:test_password").decode("utf-8")
    
    # status endpoint (engine is None by default in test import since we didn't run main())
    # So it should return 200 with engine not initialized message
    response = client.get("/status", headers={"Authorization": f"Basic {correct_creds}"})
    assert response.status_code == 200
    assert response.json() == {"status": "error", "message": "Engine not initialized"}
