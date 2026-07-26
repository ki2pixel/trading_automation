import os
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

    # login.html
    response = client.get("/login.html")
    assert response.status_code == 200
    assert "Login - Paper Trading Dashboard" in response.text

    # style.css
    response = client.get("/style.css")
    assert response.status_code == 200

def test_public_endpoints_with_trailing_slash():
    # health with trailing slash
    response = client.get("/health/")
    assert response.status_code == 200

    # keep-alive with trailing slash
    response = client.get("/keep-alive/")
    assert response.status_code == 200

def test_protected_endpoints_redirects_to_login():
    # root page redirect to login
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["Location"] == "/login.html"

    # specific page redirect to login
    response = client.get("/index.html", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["Location"] == "/login.html"

def test_protected_api_endpoints_return_401():
    # status endpoint returns 401 JSON directly, no redirect
    response = client.get("/api/status", follow_redirects=False)
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}

    # portfolio endpoint
    response = client.get("/api/portfolio", follow_redirects=False)
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}

@patch.dict(os.environ, {"PAPER_TRADER_USER": "test_user", "PAPER_TRADER_PASSWORD": "test_password"})
def test_login_endpoint_incorrect_credentials():
    # Invalid password
    response = client.post("/api/login", json={"username": "test_user", "password": "wrong_password"})
    assert response.status_code == 401
    assert response.json()["status"] == "error"

    # Invalid username
    response = client.post("/api/login", json={"username": "wrong_user", "password": "test_password"})
    assert response.status_code == 401
    assert response.json()["status"] == "error"

@patch.dict(os.environ, {"PAPER_TRADER_USER": "test_user", "PAPER_TRADER_PASSWORD": "test_password"})
def test_login_logout_flow_and_authenticated_access():
    # 1. Login with correct credentials
    response = client.post("/api/login", json={"username": "test_user", "password": "test_password"})
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # Verify cookie was set
    assert "paper_trader_session" in response.cookies
    session_cookie = response.cookies["paper_trader_session"]
    assert session_cookie != ""

    # 2. Access protected endpoint with the session cookie
    client.cookies.set("paper_trader_session", session_cookie)
    response = client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"status": "error", "message": "Engine not initialized"}

    # Access page without redirect
    response = client.get("/", follow_redirects=False)
    # Serves the static index.html or returns 200/404 based on StaticFiles
    # Since index.html exists in static folder, it should return 200
    assert response.status_code == 200

    # 3. Logout to clear session
    response = client.post("/api/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["Location"] == "/login.html"

    # Cookie should be deleted/expired in response headers
    cookie_headers = response.headers.get("set-cookie", "")
    assert "paper_trader_session=;" in cookie_headers or 'Max-Age=0' in cookie_headers or 'expires=Thursday, 01-Jan-1970 00:00:00 GMT' in cookie_headers
