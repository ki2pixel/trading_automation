import os
import pytest

@pytest.fixture(autouse=True)
def clean_env():
    # Remove BACKTEST_REPORTS_DIR to prevent pollution from the local .env
    # file during unit tests, ensuring they use test-specific temp directories.
    real_env = dict(os.environ)
    if "BACKTEST_REPORTS_DIR" in os.environ:
        del os.environ["BACKTEST_REPORTS_DIR"]
    yield
    # Restore the original environment after each test
    os.environ.clear()
    os.environ.update(real_env)
