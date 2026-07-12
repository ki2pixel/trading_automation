import os
import sqlite3
import pytest
from pathlib import Path
from unittest.mock import patch
from backtest_engine.job_store import SQLiteOptimizerJobStore, OptimizerJob, JobIntegrityError, calculate_job_signature


def test_job_signature_validation(tmp_path):
    """
    Given a SQLiteOptimizerJobStore with a configured HMAC secret
    When jobs are created, claimed, or updated
    Then their cryptographic signatures must be computed, stored, and verified dynamically.
    """
    db_path = tmp_path / "jobs.sqlite3"
    secret = "my_super_secret_hmac_key"
    
    with patch.dict(os.environ, {"JOB_STORE_HMAC_SECRET": secret}):
        store = SQLiteOptimizerJobStore(storage_path=db_path, ttl_seconds=None)
        
        # 1. Create a job
        job = OptimizerJob(
            id="job-1",
            created_at=123456789.0,
            request={"param": 42},
            status="PENDING"
        )
        store.add(job)
        
        # Verify it can be fetched successfully (signature is verified and matches)
        fetched = store.get("job-1")
        assert fetched is not None
        assert fetched.status == "PENDING"
        
        # 2. Claim the job (this atomically changes status to IN_PROGRESS and recalculates signature)
        claimed = store.claim_next(worker_id="worker-abc")
        assert claimed is not None
        assert claimed.status == "IN_PROGRESS"
        
        # Verify from database directly that the status is updated and signature is changed
        with sqlite3.connect(db_path) as conn:
            row = conn.execute("SELECT status, signature FROM optimizer_jobs WHERE id = 'job-1'").fetchone()
            assert row[0] == "IN_PROGRESS"
            sig_after_claim = row[1]
            assert sig_after_claim is not None
            
        # 3. Simulate database tampering (modify the status without updating the signature)
        with sqlite3.connect(db_path) as conn:
            conn.execute("UPDATE optimizer_jobs SET status = 'FAILED' WHERE id = 'job-1'")
            
        # Try to load the tampered job and verify it raises JobIntegrityError
        with pytest.raises(JobIntegrityError) as exc_info:
            store.get("job-1")
        assert "signature mismatch" in str(exc_info.value)
        
        # Restore status to let it pass
        with sqlite3.connect(db_path) as conn:
            conn.execute("UPDATE optimizer_jobs SET status = 'IN_PROGRESS' WHERE id = 'job-1'")
            
        # Verify we can fetch it again
        assert store.get("job-1") is not None
        
        # 4. Perform an update using the store interface and verify the signature updates
        store.update("job-1", status="FINISHED", error="None")
        with sqlite3.connect(db_path) as conn:
            row = conn.execute("SELECT status, signature FROM optimizer_jobs WHERE id = 'job-1'").fetchone()
            assert row[0] == "FINISHED"
            sig_after_update = row[1]
            assert sig_after_update != sig_after_claim


def test_sqlite_encryption_and_sqlcipher_handling(tmp_path):
    """
    Given the SQLiteOptimizerJobStore connection builder
    When SQLITE_ENCRYPTION_KEY is set
    Then it should attempt to load sqlcipher3 and enforce PRAGMA keys or fallback safely in dev.
    """
    db_path = tmp_path / "jobs_encrypted.sqlite3"
    
    # 1. Dev environment fallback check
    with patch.dict(os.environ, {"SQLITE_ENCRYPTION_KEY": "some-key", "ENVIRONMENT": "development"}):
        # Should not raise exception, but fallback with warning (tested implicitly by succeeding)
        store = SQLiteOptimizerJobStore(storage_path=db_path, ttl_seconds=None)
        job = OptimizerJob(id="job-dev", created_at=100.0, request={})
        store.add(job)
        assert store.get("job-dev") is not None
            
    # 2. Prod environment fail-fast check
    with patch.dict(os.environ, {"SQLITE_ENCRYPTION_KEY": "some-key", "ENVIRONMENT": "production", "JOB_STORE_HMAC_SECRET": "some-hmac-secret"}):
        # We mock that importing sqlcipher3 fails by patching sys.modules or raising ImportError on import
        # Let's mock a failure to import sqlcipher3 inside the _connect method
        with patch("sys.modules", {"sqlcipher3": None, "sqlcipher3.dbapi2": None}):
            with pytest.raises(ImportError) as exc_info:
                # Force _connect to run
                store = SQLiteOptimizerJobStore(storage_path=db_path, ttl_seconds=None)
            assert "SQLCipher is required in production" in str(exc_info.value)


def test_environment_failsafe():
    """
    Given BybitConfig and Trading212Config
    When a key belongs to another environment (live key in demo env, or vice versa)
    Then validate() must raise a ValueError immediately (Fail-Fast).
    """
    from backtest_engine.live.bybit.config import BybitConfig
    from backtest_engine.live.trading212.config import Trading212Config
    import hashlib

    live_key = "live_api_key_secret_12345"
    demo_key = "demo_api_key_secret_abcde"
    
    live_hash = hashlib.sha256(live_key.encode("utf-8")).hexdigest()
    demo_hash = hashlib.sha256(demo_key.encode("utf-8")).hexdigest()

    # 1. Bybit Failsafe Checks
    with patch.dict(os.environ, {
        "BYBIT_API_KEY": demo_key,
        "BYBIT_API_SECRET": "secret",
        "BYBIT_ENV": "live",
        "EXPECTED_BYBIT_DEMO_KEY_HASH": demo_hash,
        "EXPECTED_BYBIT_LIVE_KEY_HASH": live_hash,
        "BYBIT_LIVE_API_KEY": "",
        "BYBIT_LIVE_API_SECRET": ""
    }):
        config = BybitConfig()
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "Demo API key detected in Live environment" in str(exc_info.value)

    with patch.dict(os.environ, {
        "BYBIT_API_KEY": live_key,
        "BYBIT_API_SECRET": "secret",
        "BYBIT_ENV": "testnet",
        "EXPECTED_BYBIT_DEMO_KEY_HASH": demo_hash,
        "EXPECTED_BYBIT_LIVE_KEY_HASH": live_hash,
        "BYBIT_DEMO_API_KEY": "",
        "BYBIT_DEMO_API_SECRET": ""
    }):
        config = BybitConfig()
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "Live API key detected in Demo/Testnet environment" in str(exc_info.value)

    # 2. Trading 212 Failsafe Checks
    with patch.dict(os.environ, {
        "T212_API_KEY_ID": "key_id",
        "T212_API_SECRET": demo_key,
        "T212_ENV": "live",
        "EXPECTED_T212_DEMO_KEY_HASH": demo_hash,
        "EXPECTED_T212_LIVE_KEY_HASH": live_hash,
        "T212_LIVE_API_KEY_ID": "",
        "T212_LIVE_API_SECRET": ""
    }):
        config = Trading212Config()
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "Demo API key/secret detected in Live environment" in str(exc_info.value)

    with patch.dict(os.environ, {
        "T212_API_KEY_ID": "key_id",
        "T212_API_SECRET": live_key,
        "T212_ENV": "demo",
        "EXPECTED_T212_DEMO_KEY_HASH": demo_hash,
        "EXPECTED_T212_LIVE_KEY_HASH": live_hash,
        "T212_DEMO_API_KEY_ID": "",
        "T212_DEMO_API_SECRET": ""
    }):
        config = Trading212Config()
        with pytest.raises(ValueError) as exc_info:
            config.validate()
        assert "Live API key/secret detected in Demo environment" in str(exc_info.value)


def test_trading212_idempotency_and_reconciliation():
    """
    Given Trading212Client
    When concurrent orders or network retries occur
    Then Redis lock must block duplicates, and the client must reconcile with positions to avoid double spend.
    """
    from backtest_engine.live.trading212.client import Trading212Client
    from backtest_engine.live.trading212.config import Trading212Config
    from unittest.mock import MagicMock
    import requests

    with patch.dict(os.environ, {
        "T212_API_KEY_ID": "id",
        "T212_API_SECRET": "secret",
        "T212_ENV": "demo"
    }):
        config = Trading212Config()
        client = Trading212Client(config)

    # Mock DB for PTC checks in client.place_market_order
    mock_db_ctx = MagicMock()
    mock_db_conn = mock_db_ctx.__enter__.return_value
    mock_db_cur = mock_db_conn.cursor.return_value.__enter__.return_value

    def mock_db_fetchone():
        q = mock_db_cur.execute.call_args[0][0]
        if "total_nav" in q:
            return (10000.0,)
        if "price FROM live_prices" in q:
            return (150.0,)
        return None

    mock_db_cur.fetchone = MagicMock(side_effect=mock_db_fetchone)

    # Mock currency check to avoid consuming _request side_effects
    client._get_instrument_currency = MagicMock(return_value="EUR")

    mock_redis = MagicMock()
    mock_redis.set.side_effect = [True, False]

    with patch("backtest_engine.live.connection.get_db_connection", return_value=mock_db_ctx), \
         patch("backtest_engine.live.connection.get_redis_client", return_value=mock_redis):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value.json.return_value = {"id": 111, "status": "NEW"}

            with patch.object(client, "get_positions", return_value=[]):
                res1 = client.place_market_order("AAPL_US_EQ", 1.5)
                assert res1["id"] == 111
                mock_redis.set.assert_called_with("lock:t212:order:AAPL_US_EQ", "locked", ex=15, nx=True)
                mock_redis.delete.assert_called_with("lock:t212:order:AAPL_US_EQ")

        with pytest.raises(ValueError) as exc_info:
            client.place_market_order("AAPL_US_EQ", 1.5)
        assert "Duplicate concurrent order blocked" in str(exc_info.value)

    mock_redis.set.side_effect = [True]

    with patch("backtest_engine.live.connection.get_db_connection", return_value=mock_db_ctx), \
         patch("backtest_engine.live.connection.get_redis_client", return_value=mock_redis):
        with patch.object(client, "_request") as mock_req:
            mock_req.side_effect = [
                requests.exceptions.Timeout("Request timed out"),
                requests.exceptions.Timeout("Request timed out")
            ]

            with patch.object(client, "get_positions", side_effect=[
                [],
                [{"instrument": {"ticker": "AAPL_US_EQ"}, "quantity": 1.5}]
            ]):
                res = client.place_market_order("AAPL_US_EQ", 1.5)

                assert res["status"] == "FILLED"
                assert res.get("reconciled") is True
                assert mock_req.call_count == 1


