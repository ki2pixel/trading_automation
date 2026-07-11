import os
import time
import threading
import socket
import pytest
from unittest.mock import MagicMock
from contextlib import asynccontextmanager

# Set test environment flags
os.environ["PAPER_TRADER_USER"] = "admin_test"
os.environ["PAPER_TRADER_PASSWORD"] = "password_test"

# Import connection module and patch functions to avoid DB/Redis connections during testing
import backtest_engine.live.connection
backtest_engine.live.connection.get_redis_client = MagicMock(return_value=None)
backtest_engine.live.connection.get_db_connection = MagicMock()

# Import run_paper_trader
import run_paper_trader

# Bypass FastAPI lifespan context completely to avoid starting uvicorn background loops, db, or engine setup
@asynccontextmanager
async def dummy_lifespan(app):
    yield

run_paper_trader.app.router.lifespan_context = dummy_lifespan

# Now import uvicorn and playwright
import uvicorn
from playwright.sync_api import sync_playwright
from run_paper_trader import app

# Find a free port
def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    port = s.getsockname()[1]
    s.close()
    return port

class UvicornServer(uvicorn.Server):
    def install_signal_handlers(self):
        pass

    @property
    def is_running(self):
        return self.started

@pytest.fixture(scope="module")
def live_server():
    port = get_free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = UvicornServer(config)
    thread = threading.Thread(target=server.run)
    thread.daemon = True
    thread.start()
    
    # Wait for server to start
    for _ in range(50):
        if server.is_running:
            break
        time.sleep(0.1)
        
    yield f"http://127.0.0.1:{port}"
    
    # Shutdown server
    server.should_exit = True
    thread.join(timeout=2)

def test_frontend_login_and_security(live_server):
    # Given: Le serveur de paper trading est démarré avec bypass de connexion
    # When: L'utilisateur tente de se connecter avec des identifiants corrects/incorrects
    # Then: L'authentification réussit ou renvoie une erreur textuelle sécurisée
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        # 1. Test redirect to login.html
        page.goto(live_server)
        page.wait_for_url("**/login.html")
        assert "Connexion - Paper Trading Dashboard" in page.title()
        
        # 2. Test invalid credentials
        page.wait_for_selector("#username")
        page.evaluate("document.getElementById('username').value = 'wrong_user'")
        page.evaluate("document.getElementById('password').value = 'wrong_pass'")
        page.evaluate("document.getElementById('submitBtn').click()")
        
        # Wait for error message
        error_el = page.locator("#errorAlert")
        page.wait_for_selector("#errorAlert:not([style*='display: none'])")
        err_text = error_el.text_content().lower()
        assert "incorrect" in err_text or "invalid" in err_text
        
        # 3. Test valid login
        page.evaluate("document.getElementById('username').value = 'admin_test'")
        page.evaluate("document.getElementById('password').value = 'password_test'")
        page.evaluate("document.getElementById('submitBtn').click()")
        
        page.wait_for_url(f"{live_server}/")
        assert "Paper Trading" in page.title()
        
        browser.close()

def test_frontend_responsive_sidebar(live_server):
    # Given: L'utilisateur est connecté sur mobile (résolution étroite)
    # When: L'interface se charge
    # Then: La sidebar se replie en haut sans provoquer d'overflow masqué
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        # Login
        page.goto(f"{live_server}/login.html")
        page.wait_for_selector("#username")
        page.evaluate("document.getElementById('username').value = 'admin_test'")
        page.evaluate("document.getElementById('password').value = 'password_test'")
        page.evaluate("document.getElementById('submitBtn').click()")
        page.wait_for_url(f"{live_server}/")
        
        # Change viewport to mobile (375x667)
        page.set_viewport_size({"width": 375, "height": 667})
        
        # Verify responsive sidebar layout
        sidebar = page.locator(".sidebar")
        box = sidebar.bounding_box()
        # En mode responsive, la sidebar prend toute la largeur (- marges) donc supérieure à 300px
        assert box["width"] > 300
        
        browser.close()

def test_frontend_modal_accessibility(live_server):
    # Given: Le panneau d'administration est ouvert
    # When: L'utilisateur ouvre la modale Panic Close et interagit
    # Then: Le focus est piégé et la touche Escape ferme proprement la modale en restaurant le focus
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        # Login
        page.goto(f"{live_server}/login.html")
        page.wait_for_selector("#username")
        page.evaluate("document.getElementById('username').value = 'admin_test'")
        page.evaluate("document.getElementById('password').value = 'password_test'")
        page.evaluate("document.getElementById('submitBtn').click()")
        page.wait_for_url(f"{live_server}/")
        
        # Open Panic Modal
        page.click("#panic-btn")
        page.wait_for_selector("#panic-modal:not([style*='display: none'])")
        
        # Check that focus was set to cancel button (safer option)
        page.wait_for_timeout(100)
        is_focused = page.evaluate("document.activeElement.id === 'cancel-panic-btn'")
        assert is_focused
        
        # Press Escape to close
        page.keyboard.press("Escape")
        page.wait_for_selector("#panic-modal[style*='display: none']", state="hidden")
        
        # Check focus returned to panic button
        is_panic_focused = page.evaluate("document.activeElement.id === 'panic-btn'")
        assert is_panic_focused
        
        browser.close()