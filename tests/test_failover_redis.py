import unittest
from unittest.mock import patch, MagicMock
import redis
import urllib.error

from backtest_engine.live.connection import (
    _is_upstash_quota_exhausted,
    FailoverRedisClient,
    FailoverPipeline
)

class MockContextManager:
    def __init__(self, val):
        self.val = val
    def __enter__(self):
        return self.val
    def __exit__(self, *args):
        pass

class TestUpstashQuotaCheck(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_quota_exhausted_under_limit(self, mock_urlopen):
        # Mock database list and database stats responses
        mock_response_db = MagicMock()
        mock_response_db.read.return_value = b'[{"database_id": "db123", "endpoint": "sound-cowbird-92386.upstash.io", "db_request_limit": 500000, "state": "active"}]'
        
        mock_response_stats = MagicMock()
        mock_response_stats.read.return_value = b'{"total_monthly_requests": 100000}'
        
        mock_urlopen.side_effect = [
            MockContextManager(mock_response_db),
            MockContextManager(mock_response_stats)
        ]
        
        result = _is_upstash_quota_exhausted(
            "rediss://default:pwd@sound-cowbird-92386.upstash.io:6379",
            "fake_api",
            "fake@gmail.com"
        )
        self.assertFalse(result)

    @patch("urllib.request.urlopen")
    def test_quota_exhausted_over_limit(self, mock_urlopen):
        mock_response_db = MagicMock()
        mock_response_db.read.return_value = b'[{"database_id": "db123", "endpoint": "sound-cowbird-92386.upstash.io", "db_request_limit": 500000, "state": "active"}]'
        
        mock_response_stats = MagicMock()
        mock_response_stats.read.return_value = b'{"total_monthly_requests": 500000}'
        
        mock_urlopen.side_effect = [
            MockContextManager(mock_response_db),
            MockContextManager(mock_response_stats)
        ]
        
        result = _is_upstash_quota_exhausted(
            "rediss://default:pwd@sound-cowbird-92386.upstash.io:6379",
            "fake_api",
            "fake@gmail.com"
        )
        self.assertTrue(result)

    @patch("urllib.request.urlopen")
    def test_quota_exhausted_suspended_state(self, mock_urlopen):
        mock_response_db = MagicMock()
        # Database state is suspended
        mock_response_db.read.return_value = b'[{"database_id": "db123", "endpoint": "sound-cowbird-92386.upstash.io", "db_request_limit": 500000, "state": "suspended"}]'
        
        mock_urlopen.side_effect = [MockContextManager(mock_response_db)]
        
        result = _is_upstash_quota_exhausted(
            "rediss://default:pwd@sound-cowbird-92386.upstash.io:6379",
            "fake_api",
            "fake@gmail.com"
        )
        self.assertTrue(result)

    @patch("urllib.request.urlopen")
    def test_quota_check_api_error_falls_back_gracefully(self, mock_urlopen):
        # Simulate network or HTTP error from Upstash API
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        
        result = _is_upstash_quota_exhausted(
            "rediss://default:pwd@sound-cowbird-92386.upstash.io:6379",
            "fake_api",
            "fake@gmail.com"
        )
        # Should return False (do not consider exhausted, fallback gracefully to ping test)
        self.assertFalse(result)


class TestFailoverRedisClient(unittest.TestCase):
    @patch("redis.Redis.from_url")
    def test_standard_delegation(self, mock_from_url):
        mock_primary = MagicMock()
        mock_secondary = MagicMock()
        mock_from_url.side_effect = [mock_primary, mock_secondary]
        
        client = FailoverRedisClient("redis://primary", "redis://secondary")
        
        # Test standard method routing
        client.get("test_key")
        mock_primary.get.assert_called_once_with("test_key")
        mock_secondary.get.assert_not_called()

    @patch("redis.Redis.from_url")
    def test_failover_on_connection_error(self, mock_from_url):
        mock_primary = MagicMock()
        mock_primary.get.side_effect = redis.exceptions.ConnectionError("Connection lost")
        
        mock_secondary = MagicMock()
        mock_secondary.get.return_value = "success_val"
        
        mock_from_url.side_effect = [mock_primary, mock_secondary]
        
        client = FailoverRedisClient("redis://primary", "redis://secondary")
        
        # Attempt get, should fail on primary, trigger failover, retry and succeed on secondary
        res = client.get("test_key")
        
        self.assertEqual(res, "success_val")
        self.assertTrue(client._is_failed_over)
        self.assertEqual(client._active_client, mock_secondary)
        mock_primary.get.assert_called_once_with("test_key")
        mock_secondary.get.assert_called_once_with("test_key")

    @patch("redis.Redis.from_url")
    def test_failover_on_quota_response_error(self, mock_from_url):
        mock_primary = MagicMock()
        # ResponseError with quota/limit keyword
        mock_primary.get.side_effect = redis.exceptions.ResponseError("ERR max daily limit exceeded")
        
        mock_secondary = MagicMock()
        mock_secondary.get.return_value = "quota_succeeded"
        
        mock_from_url.side_effect = [mock_primary, mock_secondary]
        
        client = FailoverRedisClient("redis://primary", "redis://secondary")
        
        res = client.get("test_key")
        
        self.assertEqual(res, "quota_succeeded")
        self.assertTrue(client._is_failed_over)
        self.assertEqual(client._active_client, mock_secondary)

    @patch("redis.Redis.from_url")
    def test_no_failover_on_standard_response_error(self, mock_from_url):
        mock_primary = MagicMock()
        # Normal syntax/key error without keywords
        mock_primary.get.side_effect = redis.exceptions.ResponseError("WRONGTYPE Operation against a key holding the wrong kind of value")
        
        mock_secondary = MagicMock()
        mock_from_url.side_effect = [mock_primary, mock_secondary]
        
        client = FailoverRedisClient("redis://primary", "redis://secondary")
        
        # Should raise directly without failing over
        with self.assertRaises(redis.exceptions.ResponseError):
            client.get("test_key")
            
        self.assertFalse(client._is_failed_over)
        self.assertEqual(client._active_client, mock_primary)
        mock_secondary.get.assert_not_called()


class TestFailoverPipeline(unittest.TestCase):
    @patch("redis.Redis.from_url")
    def test_pipeline_recording_and_failover_replay(self, mock_from_url):
        mock_primary = MagicMock()
        mock_primary_pipe = MagicMock()
        mock_primary.pipeline.return_value = mock_primary_pipe
        
        # Set primary execute to raise quota error
        mock_primary_pipe.execute.side_effect = redis.exceptions.ResponseError("ERR quota reached")
        
        mock_secondary = MagicMock()
        mock_secondary_pipe = MagicMock()
        mock_secondary.pipeline.return_value = mock_secondary_pipe
        mock_secondary_pipe.execute.return_value = ["OK", "val"]
        
        mock_from_url.side_effect = [mock_primary, mock_secondary]
        
        client = FailoverRedisClient("redis://primary", "redis://secondary")
        
        # Execute pipeline operations
        pipe = client.pipeline()
        pipe.set("key", "val")
        pipe.get("key")
        
        # This will execute primary, fail, failover, replay commands on secondary, and execute secondary
        res = pipe.execute()
        
        self.assertEqual(res, ["OK", "val"])
        self.assertTrue(client._is_failed_over)
        self.assertEqual(client._active_client, mock_secondary)
        
        # Verify commands were called on primary pipeline
        mock_primary_pipe.set.assert_called_once_with("key", "val")
        mock_primary_pipe.get.assert_called_once_with("key")
        mock_primary_pipe.execute.assert_called_once()
        
        # Verify commands were replayed on secondary pipeline
        mock_secondary_pipe.set.assert_called_once_with("key", "val")
        mock_secondary_pipe.get.assert_called_once_with("key")
        mock_secondary_pipe.execute.assert_called_once()
