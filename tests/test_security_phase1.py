"""
Tests for Phase 1 Security hardening:
- HMAC secret separation from user password
- CSRF double-submit cookie protection
- Pydantic IndicatorParamsModel validation
- Security headers (CSP, X-Frame-Options, X-Content-Type-Options, HSTS)
"""
import os
import time
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from run_paper_trader import app, create_session_token, verify_session_token, HMAC_SECRET


client = TestClient(app)


# ─────────────────────────────────────────
# Tâche 1.1 — HMAC Secret Separation Tests
# ─────────────────────────────────────────

class TestHMACSecretSeparation:
    """Verify HMAC signing uses HMAC_SECRET, not user password."""

    def test_hmac_secret_is_set_in_test_env(self):
        """HMAC_SECRET should be auto-generated in test environment."""
        assert HMAC_SECRET is not None
        assert len(HMAC_SECRET) >= 32  # at least 16 bytes hex-encoded

    def test_token_signed_with_hmac_secret_not_password(self):
        """Token created with HMAC_SECRET should not verify with user password."""
        password = os.getenv("PAPER_TRADER_PASSWORD", "test_password")
        expires = int(time.time()) + 3600

        # Create token with HMAC_SECRET (the correct key)
        token = create_session_token("admin", expires, HMAC_SECRET)

        # Verify with HMAC_SECRET → should succeed
        assert verify_session_token(token, HMAC_SECRET) is True

        # Verify with user password → should FAIL (keys are now separate)
        if password != HMAC_SECRET:
            assert verify_session_token(token, password) is False

    def test_token_created_with_password_not_valid(self):
        """A token signed with the user password should not pass HMAC verification."""
        password = "some_user_password"
        expires = int(time.time()) + 3600

        token = create_session_token("admin", expires, password)

        # This token should NOT verify with HMAC_SECRET
        assert verify_session_token(token, HMAC_SECRET) is False

    def test_expired_token_rejected(self):
        """Expired tokens should be rejected regardless of correct secret."""
        expires = int(time.time()) - 1  # already expired
        token = create_session_token("admin", expires, HMAC_SECRET)
        assert verify_session_token(token, HMAC_SECRET) is False

    def test_malformed_token_rejected(self):
        """Malformed tokens should be rejected gracefully."""
        assert verify_session_token("garbage", HMAC_SECRET) is False
        assert verify_session_token("a:b", HMAC_SECRET) is False
        assert verify_session_token("a:not_int:sig", HMAC_SECRET) is False
        assert verify_session_token("", HMAC_SECRET) is False

    @patch.dict(os.environ, {"PAPER_TRADER_USER": "test_user", "PAPER_TRADER_PASSWORD": "test_password"})
    def test_login_flow_uses_hmac_secret(self):
        """Login should create a token signed with HMAC_SECRET, not password."""
        response = client.post("/api/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # Session cookie should be set
        assert "paper_trader_session" in response.cookies
        session_token = response.cookies["paper_trader_session"]

        # Token should verify with HMAC_SECRET
        assert verify_session_token(session_token, HMAC_SECRET) is True

    @patch.dict(os.environ, {"PAPER_TRADER_USER": "test_user", "PAPER_TRADER_PASSWORD": "test_password"})
    def test_login_flow_form_urlencoded_success(self):
        """Form urlencoded login should redirect to / and set session cookie."""
        response = client.post(
            "/api/login",
            data={
                "username": "test_user",
                "password": "test_password"
            },
            follow_redirects=False
        )
        assert response.status_code == 303
        assert response.headers["Location"] == "/"
        assert "paper_trader_session" in response.cookies

    @patch.dict(os.environ, {"PAPER_TRADER_USER": "test_user", "PAPER_TRADER_PASSWORD": "test_password"})
    def test_login_flow_form_urlencoded_failure(self):
        """Form urlencoded login with wrong credentials should redirect to /login.html?error=true."""
        response = client.post(
            "/api/login",
            data={
                "username": "test_user",
                "password": "wrong_password"
            },
            follow_redirects=False
        )
        assert response.status_code == 303
        assert response.headers["Location"] == "/login.html?error=true"
        assert "paper_trader_session" not in response.cookies


# ─────────────────────────────────────
# Tâche 1.2 — CSRF Protection Tests
# ─────────────────────────────────────

class TestCSRFProtection:
    """Verify CSRF double-submit cookie protection."""

    def test_csrf_cookie_set_on_get(self):
        """CSRF token cookie should be set on first GET request."""
        # Clear cookies first
        client.cookies.clear()
        response = client.get("/health")
        assert response.status_code == 200
        # The csrftoken cookie should be set in the response
        assert "csrftoken" in response.cookies or "csrftoken" in client.cookies

    @patch.dict(os.environ, {"PAPER_TRADER_USER": "test_user", "PAPER_TRADER_PASSWORD": "test_password"})
    def test_csrf_exempt_login(self):
        """POST to /api/login should work without CSRF token."""
        client.cookies.clear()
        response = client.post("/api/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        # Login is exempt from CSRF
        assert response.status_code == 200
        assert response.json()["status"] == "success"

    @patch.dict(os.environ, {"PAPER_TRADER_USER": "test_user", "PAPER_TRADER_PASSWORD": "test_password"})
    def test_csrf_exempt_logout(self):
        """POST to /api/logout should work without CSRF token (exempt)."""
        # Login first
        login_resp = client.post("/api/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        session = login_resp.cookies.get("paper_trader_session")
        client.cookies.set("paper_trader_session", session)

        # Clear only the CSRF cookie
        if "csrftoken" in client.cookies:
            client.cookies.delete("csrftoken")

        response = client.post("/api/logout", follow_redirects=False)
        # Logout is exempt from CSRF
        assert response.status_code == 307

    @patch.dict(os.environ, {"PAPER_TRADER_USER": "test_user", "PAPER_TRADER_PASSWORD": "test_password"})
    def test_post_without_csrf_header_returns_403(self):
        """POST to a protected endpoint without X-CSRFToken header should return 403."""
        client.cookies.clear()
        # Login first to get session and csrf cookie
        login_resp = client.post("/api/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        assert login_resp.status_code == 200

        # POST to panic endpoint without X-CSRFToken header
        response = client.post("/api/control/panic")
        assert response.status_code == 403
        assert "CSRF" in response.json()["detail"]

    @patch.dict(os.environ, {"PAPER_TRADER_USER": "test_user", "PAPER_TRADER_PASSWORD": "test_password"})
    def test_post_with_mismatched_csrf_returns_403(self):
        """POST with mismatched CSRF token (cookie vs header) should return 403."""
        client.cookies.clear()
        login_resp = client.post("/api/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        assert login_resp.status_code == 200

        # Send wrong token in header
        response = client.post(
            "/api/control/panic",
            headers={"X-CSRFToken": "wrong_token"}
        )
        assert response.status_code == 403

    @patch("backtest_engine.live.paper_trading.api._get_pool")
    @patch.dict(os.environ, {"PAPER_TRADER_USER": "test_user", "PAPER_TRADER_PASSWORD": "test_password"})
    def test_post_with_valid_csrf_succeeds(self, mock_get_pool):
        """POST with matching CSRF token should succeed (if endpoint is valid)."""
        # Mock asyncpg pool chain: pool.acquire() -> conn.fetch()
        from unittest.mock import AsyncMock, MagicMock
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_conn.transaction = MagicMock()
        mock_transaction = AsyncMock()
        mock_conn.transaction.return_value = mock_transaction
        
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=False)

        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        mock_get_pool.return_value = mock_pool

        client.cookies.clear()
        # First GET health to ensure a csrf cookie exists
        client.get("/health")
        csrf_token_before = client.cookies.get("csrftoken")
        assert csrf_token_before is not None

        login_resp = client.post("/api/login", json={
            "username": "test_user",
            "password": "test_password"
        })
        assert login_resp.status_code == 200
        
        # After login, we can fetch the actual active csrftoken cookie
        csrf_token = client.cookies.get("csrftoken")
        assert csrf_token is not None

        # POST with matching CSRF header — will hit the actual endpoint
        response = client.post(
            "/api/control/panic",
            headers={"X-CSRFToken": csrf_token}
        )
        # Should pass CSRF check (not 403). Should be 200 since DB is mocked.
        assert response.status_code == 200
        assert response.json()["status"] == "success"


# ─────────────────────────────────────────────
# Tâche 1.3 — Pydantic Validation Tests
# ─────────────────────────────────────────────

class TestIndicatorParamsValidation:
    """Verify IndicatorParamsModel validates indicator_params correctly."""

    def test_valid_common_keys_accepted(self):
        """Known common keys should be accepted and typed correctly."""
        from backtest_engine.live.paper_trading.api import IndicatorParamsModel

        model = IndicatorParamsModel(
            quantity_precision=6,
            account_currency="EUR",
            enable_stop_loss=True,
            stop_loss_pct=2.5
        )
        assert model.quantity_precision == 6
        assert model.account_currency == "EUR"
        assert model.enable_stop_loss is True
        assert model.stop_loss_pct == 2.5

    def test_extra_strategy_keys_accepted(self):
        """Strategy-specific keys (extra) should be allowed."""
        from backtest_engine.live.paper_trading.api import IndicatorParamsModel

        model = IndicatorParamsModel(
            hma_length=50,
            pmax_multiplier=2.0,
            rsi_period=14
        )
        dumped = model.model_dump(exclude_none=True)
        assert dumped["hma_length"] == 50
        assert dumped["pmax_multiplier"] == 2.0
        assert dumped["rsi_period"] == 14

    def test_nested_dict_rejected(self):
        """Nested dicts in indicator_params should be rejected."""
        from backtest_engine.live.paper_trading.api import IndicatorParamsModel
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="Nested structures"):
            IndicatorParamsModel(
                malicious_key={"nested": "injection"}
            )

    def test_nested_list_rejected(self):
        """Nested lists in indicator_params should be rejected."""
        from backtest_engine.live.paper_trading.api import IndicatorParamsModel
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="Nested structures"):
            IndicatorParamsModel(
                malicious_key=[1, 2, 3]
            )

    def test_none_indicator_params_accepted(self):
        """ConfigUpdate with indicator_params=None should be valid."""
        from backtest_engine.live.paper_trading.api import ConfigUpdate

        model = ConfigUpdate(
            initial_capital=10000.0,
            initial_capital_bucket=1000.0,
            max_capital_bucket=5000.0,
            max_entry_price=500.0,
            is_active=True,
            indicator_params=None
        )
        assert model.indicator_params is None

    def test_model_dump_excludes_none(self):
        """model_dump(exclude_none=True) should only include set values."""
        from backtest_engine.live.paper_trading.api import IndicatorParamsModel

        model = IndicatorParamsModel(
            quantity_precision=6,
            enable_stop_loss=True
        )
        dumped = model.model_dump(exclude_none=True)
        assert "quantity_precision" in dumped
        assert "enable_stop_loss" in dumped
        assert "account_currency" not in dumped
        assert "point_value" not in dumped


# ─────────────────────────────────────────────
# Tâche 1.4 — Security Headers Tests
# ─────────────────────────────────────────────

class TestSecurityHeaders:
    """Verify security headers are present on responses."""

    def test_x_content_type_options_present(self):
        """X-Content-Type-Options: nosniff should be in every response."""
        response = client.get("/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options_present(self):
        """X-Frame-Options: DENY should be in every response."""
        response = client.get("/health")
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_csp_header_present(self):
        """Content-Security-Policy should be present."""
        response = client.get("/health")
        csp = response.headers.get("Content-Security-Policy")
        assert csp is not None
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp

    def test_hsts_absent_in_non_production(self):
        """HSTS should NOT be set when not in production."""
        with patch.dict(os.environ, {}, clear=False):
            # Remove production indicators
            env = os.environ.copy()
            env.pop("ENVIRONMENT", None)
            env.pop("RENDER", None)
            with patch.dict(os.environ, env, clear=True):
                response = client.get("/health")
                # In test env (not production), HSTS should be absent
                assert "Strict-Transport-Security" not in response.headers

    @patch.dict(os.environ, {"RENDER": "true"})
    def test_hsts_present_in_production(self):
        """HSTS should be set when RENDER env var is present."""
        response = client.get("/health")
        hsts = response.headers.get("Strict-Transport-Security")
        assert hsts is not None
        assert "max-age=31536000" in hsts
