import os
import pytest

@pytest.fixture(autouse=True)
def clean_env():
    # Remove BACKTEST_REPORTS_DIR to prevent pollution from the local .env
    # file during unit tests, ensuring they use test-specific temp directories.
    real_env = dict(os.environ)
    if "BACKTEST_REPORTS_DIR" in os.environ:
        del os.environ["BACKTEST_REPORTS_DIR"]
    import hashlib
    # Mock failsafe hashes globally so config parsing doesn't crash in tests
    os.environ["EXPECTED_BYBIT_DEMO_KEY_HASH"] = hashlib.sha256(b"test_key").hexdigest()
    os.environ["EXPECTED_BYBIT_LIVE_KEY_HASH"] = hashlib.sha256(b"live_key").hexdigest()
    os.environ["EXPECTED_T212_DEMO_KEY_HASH"] = hashlib.sha256(b"test_secret").hexdigest()
    os.environ["EXPECTED_T212_LIVE_KEY_HASH"] = hashlib.sha256(b"live_secret").hexdigest()

    # Also force the actual keys to the dummy values to override local .env for isolated tests
    os.environ["T212_API_SECRET"] = "test_secret"
    os.environ["T212_DEMO_API_SECRET"] = "test_secret"
    os.environ["T212_LIVE_API_SECRET"] = "live_secret"
    os.environ["BYBIT_API_KEY"] = "test_key"
    os.environ["BYBIT_DEMO_API_KEY"] = "test_key"
    os.environ["BYBIT_LIVE_API_KEY"] = "live_key"
    os.environ["T212_API_KEY_ID"] = "test_key"

    from unittest.mock import patch
    redis_patch = patch('backtest_engine.live.connection.get_async_redis_client', return_value=None)
    redis_patch.start()

    yield
    redis_patch.stop()
    # Restore the original environment after each test
    os.environ.clear()
    os.environ.update(real_env)
