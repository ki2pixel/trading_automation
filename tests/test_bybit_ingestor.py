import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from decimal import Decimal

from backtest_engine.live.bybit.config import BybitConfig
from backtest_engine.live.bybit.client import BybitClient
from backtest_engine.live.bybit.ingestor import BybitPriceIngestor

class TestBybitIngestor(unittest.TestCase):
    def setUp(self):
        # Mock environment variables and prevent loading real .env
        self.env_patcher = patch.dict("os.environ", {
            "BYBIT_API_KEY": "test_key",
            "BYBIT_API_SECRET": "test_secret",
            "BYBIT_DEMO_API_KEY": "test_key",
            "BYBIT_DEMO_API_SECRET": "test_secret",
            "BYBIT_ENV": "testnet",
            "BYBIT_PRICE_CACHE_PATH": "/tmp/test_bybit_prices.json"
        })
        self.env_patcher.start()

        self.dotenv_patcher = patch("dotenv.load_dotenv")
        self.dotenv_patcher.start()

        self.load_patcher = patch.object(BybitConfig, "_load_dotenv", lambda self: None)
        self.load_patcher.start()

        self.config = BybitConfig()
        self.client = BybitClient(self.config)

    def tearDown(self):
        self.load_patcher.stop()
        self.dotenv_patcher.stop()
        self.env_patcher.stop()

    def test_config_resolution(self):
        self.assertEqual(self.config.api_key, "test_key")
        self.assertEqual(self.config.api_secret, "test_secret")
        self.assertEqual(self.config.base_url, "https://api-demo.bybit.com")

    def test_signature_generation(self):
        timestamp = "1672531200000"
        query_str = "category=spot&symbol=LTCUSDT"

        # Expected signature generated via HMAC-SHA256
        # string to sign = timestamp + api_key + recv_window + query_str
        # = "1672531200000" + "test_key" + "5000" + "category=spot&symbol=LTCUSDT"
        import hmac
        import hashlib
        expected_raw = timestamp + "test_key" + "5000" + query_str
        expected_sig = hmac.new(
            b"test_secret",
            expected_raw.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        sig = self.client._sign(timestamp, query_str)
        self.assertEqual(sig, expected_sig)

    @patch("backtest_engine.live.bybit.client.requests.request")
    def test_get_account_summary_headers(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"retCode": 0, "result": {"list": []}}
        mock_request.return_value = mock_resp

        self.client.get_account_summary()

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        headers = kwargs.get("headers", {})
        self.assertIn("X-BAPI-API-KEY", headers)
        self.assertIn("X-BAPI-SIGN", headers)
        self.assertIn("X-BAPI-TIMESTAMP", headers)
        self.assertIn("X-BAPI-RECV-WINDOW", headers)
        self.assertEqual(headers["X-BAPI-API-KEY"], "test_key")

    @patch("backtest_engine.live.bybit.ingestor.get_db_connection")
    def test_bootstrap_historical_candles_reversing(self, mock_get_db):
        # Mock Bybit returning candles descending (newest first)
        mock_klines = {
            "result": {
                "list": [
                    ["1672531260000", "100.5", "101.0", "100.0", "100.8", "1000"], # Newest
                    ["1672531200000", "99.5", "100.2", "99.0", "100.1", "900"]     # Oldest
                ]
            }
        }
        self.client.get_klines = MagicMock(return_value=mock_klines)

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_get_db.return_value.__enter__.return_value = mock_conn

        ingestor = BybitPriceIngestor(self.client, symbols=["LTCUSDT"])
        mock_cur.execute.reset_mock()
        ingestor.bootstrap_historical_candles()

        # Check call order
        self.assertEqual(mock_cur.execute.call_count, 2)

        # Verify first call is the oldest candle (reversing is working)
        first_call_args = mock_cur.execute.call_args_list[0][0]
        self.assertEqual(first_call_args[1][0], "ltcusdt")
        self.assertEqual(first_call_args[1][2], Decimal("99.5")) # Open of oldest

        second_call_args = mock_cur.execute.call_args_list[1][0]
        self.assertEqual(second_call_args[1][2], Decimal("100.5")) # Open of newest

    @patch("backtest_engine.live.bybit.ingestor.get_redis_client")
    @patch("backtest_engine.live.bybit.ingestor.get_db_connection")
    def test_poll_and_cache(self, mock_get_db, mock_get_redis):
        # Mock current price ticker
        mock_ticker = {
            "result": {
                "list": [
                    {"symbol": "LTCUSDT", "lastPrice": "102.5"}
                ]
            }
        }
        self.client.get_ticker_price = MagicMock(return_value=mock_ticker)

        # Mock recent klines
        mock_klines = {
            "result": {
                "list": [
                    ["1672531260000", "102.0", "103.0", "102.0", "102.5", "500"]
                ]
            }
        }
        self.client.get_klines = MagicMock(return_value=mock_klines)

        # Mock Redis
        mock_redis = MagicMock()
        mock_get_redis.return_value = mock_redis

        # Mock DB
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_get_db.return_value.__enter__.return_value = mock_conn

        ingestor = BybitPriceIngestor(self.client, symbols=["LTCUSDT"])
        prices = ingestor.poll_and_cache()

        # Check prices output dict
        self.assertEqual(prices, {"ltcusdt": 102.5})

        # Check Redis pipeline call (G1-FIX: now uses pipeline().set() + execute())
        mock_redis.pipeline.assert_called_once()
        mock_pipeline = mock_redis.pipeline.return_value
        redis_set_call = mock_pipeline.set.call_args
        self.assertEqual(redis_set_call[0][0], "price:ltcusdt")
        import json as _json
        payload = _json.loads(redis_set_call[0][1])
        self.assertEqual(payload["price"], "102.5")
        self.assertIn("timestamp", payload)
        self.assertEqual(redis_set_call[1], {"ex": 180})
        mock_pipeline.execute.assert_called_once()

        # Check DB upsert for live_prices and live_candles_1m
        # 1. Update price
        mock_cur.execute.assert_any_call(
            unittest.mock.ANY,
            ("ltcusdt", Decimal("102.5"))
        )

        # 2. Update candle
        mock_cur.execute.assert_any_call(
            unittest.mock.ANY,
            ("ltcusdt", datetime.fromtimestamp(1672531260.0, tz=timezone.utc), Decimal("102.0"), Decimal("103.0"), Decimal("102.0"), Decimal("102.5"))
        )

    def test_public_only_mode(self):
        # Setup config and client without credentials
        with patch.dict("os.environ", {"BYBIT_API_KEY": "", "BYBIT_API_SECRET": "", "BYBIT_DEMO_API_KEY": "", "BYBIT_DEMO_API_SECRET": ""}):
            config = BybitConfig()
            client = BybitClient(config)

            # Check that validation does not raise ValueError
            config.validate()

            # Check that a signed request raises ValueError
            with self.assertRaises(ValueError) as ctx:
                client.get_account_summary()
            self.assertIn("Cannot perform signed requests", str(ctx.exception))

