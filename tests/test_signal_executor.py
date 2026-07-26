import os
import json
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import pandas as pd

from backtest_engine.live.paper_trading.signal_executor import SignalExecutor
from backtest_engine.live.paper_trading.engine import get_eurusd_rate
import backtest_engine.live.utils as utils


@pytest.fixture(autouse=True)
def reset_kill_switch_global():
    from backtest_engine.live.kill_switch import set_trading_suspended
    set_trading_suspended(False)

class TestGetEurUsdRate:
    @pytest.fixture(autouse=True)
    def reset_eurusd_cache(self):
        # Reset global cache to avoid test pollution
        utils._eurusd_cache_rate = None
    @patch('backtest_engine.live.paper_trading.engine.logger')
    def test_eurusd_rate_db_success(self, mock_logger):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = (Decimal("1.10"),)

        rate = get_eurusd_rate(mock_conn)
        assert rate == Decimal("1.10")
        mock_cursor.execute.assert_called_once_with("SELECT price FROM live_prices WHERE ticker = 'eurusd'")

    @patch('urllib.request.urlopen')
    def test_eurusd_rate_api_fallback(self, mock_urlopen):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.side_effect = Exception("DB error")

        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"rates": {"USD": 1.09}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        rate = get_eurusd_rate(mock_conn)
        assert rate == Decimal("1.09")

    @patch('urllib.request.urlopen')
    def test_eurusd_rate_static_fallback(self, mock_urlopen):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.side_effect = Exception("DB error")
        mock_urlopen.side_effect = Exception("Network error")

        rate = get_eurusd_rate(mock_conn)
        assert rate == Decimal("1.08")


class TestSignalExecutor:
    def test_is_market_open_with_custom_func(self):
        custom_func = MagicMock(return_value=True)
        executor = SignalExecutor(is_market_open_func=custom_func)
        assert executor.is_market_open("AAPL") is True
        custom_func.assert_called_once_with("AAPL")

    @patch('backtest_engine.live.paper_trading.signal_executor.datetime')
    @patch('backtest_engine.live.paper_trading.signal_executor.is_market_open')
    def test_is_market_open_delegation(self, mock_is_market_open, mock_datetime):
        mock_now = datetime(2023, 10, 4, 12, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now

        market_hours = {"AAPL": {"open": "09:00", "close": "17:30", "tz_offset": "+01:00"}}
        executor = SignalExecutor(market_hours=market_hours)

        mock_is_market_open.return_value = True
        assert executor.is_market_open("AAPL") is True
        mock_is_market_open.assert_called_once_with("AAPL", market_hours, current_time=mock_now)

    def test_log_evaluation(self):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value

        executor = SignalExecutor()
        executor.log_evaluation(
            mock_conn, "hma_crossover", "AAPL", "5m", Decimal("150.0"),
            "ENTRY", True, "EXECUTED", None, {"details_key": Decimal("42.0")}
        )

        mock_cursor.execute.assert_called_once()
        args = mock_cursor.execute.call_args[0]
        query = args[0]
        params = args[1]
        assert "INSERT INTO paper_evaluations" in query
        assert params[0] == "hma_crossover"
        assert params[1] == "AAPL"
        assert params[2] == "5m"
        assert params[3] == 150.0
        assert params[4] == "ENTRY"
        assert params[5] is True
        assert params[6] == "EXECUTED"
        assert params[7] is None
        assert "42.0" in params[8]  # serialized details

    @patch('backtest_engine.live.connection.get_redis_client')
    @patch('backtest_engine.live.utils.get_eurusd_rate')
    def test_update_portfolio_nav_empty(self, mock_get_rate, mock_get_redis):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value

        # Mock database portfolio balances (cash, secured)
        mock_cursor.fetchall.side_effect = [
            [("trading212", Decimal("100000"), Decimal("0")), ("bybit", Decimal("10000"), Decimal("1000"))], # balance row query
            [] # position query
        ]
        mock_get_rate.return_value = Decimal("1.10")

        # Clients are active
        mock_t212 = MagicMock()
        mock_t212.get_account_summary.return_value = {
            "cash": {"availableToTrade": 105000.0},
            "totalValue": 105000.0
        }

        mock_bybit = MagicMock()
        mock_bybit.config.base_currency = "USDT"
        mock_bybit.get_account_summary.return_value = {
            "result": {"list": [{"coin": [{"coin": "USDT", "walletBalance": "12000.0"}]}]}
        }

        executor = SignalExecutor(t212_client=mock_t212, bybit_client=mock_bybit)
        executor.update_portfolio_nav(mock_conn)

        # check that cash balances were updated from APIs
        update_calls = [
            call for call in mock_cursor.execute.call_args_list
            if "UPDATE paper_portfolio_balance SET paper_cash_balance" in call[0][0]
        ]
        assert len(update_calls) == 2
        # verify total_nav was updated:
        # trading212 = 105000 (from API)
        # bybit = 12000 (from API) + 1000 * 1.10 = 13100
        nav_calls = [
            call for call in mock_cursor.execute.call_args_list
            if "UPDATE paper_portfolio_balance SET total_nav" in call[0][0]
        ]
        assert len(nav_calls) == 2

    @patch('backtest_engine.live.connection.get_redis_client')
    @patch('backtest_engine.live.utils.get_eurusd_rate')
    def test_update_portfolio_nav_with_positions(self, mock_get_rate, mock_get_redis):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value

        # Mock database query results
        mock_cursor.fetchall.side_effect = [
            [("trading212", Decimal("100000"), Decimal("0")), ("bybit", Decimal("10000"), Decimal("0"))], # balance query
            [(1, "BTCUSDT", Decimal("0.5"), Decimal("30000"), Decimal("31000")), (2, "AAPL", Decimal("10"), Decimal("150"), Decimal("155"))] # positions query
        ]
        mock_get_rate.return_value = Decimal("1.08")

        mock_redis = MagicMock()
        now_str = datetime.now(timezone.utc).isoformat()
        mock_redis.mget.return_value = [
            json.dumps({"price": "32000.0", "timestamp": now_str}),
            json.dumps({"price": "160.0", "timestamp": now_str})
        ]
        mock_get_redis.return_value = mock_redis

        # Mock is_market_open to return True
        custom_is_open = MagicMock(return_value=True)
        executor = SignalExecutor(is_market_open_func=custom_is_open)

        executor.update_portfolio_nav(mock_conn)

        # Assert Redis mget was called with correct keys
        mock_redis.mget.assert_called_once_with(["price:btcusdt", "price:aapl"])

        # Check executemany for positions updates:
        # BTCUSDT: price=32000, pnl=(32000-30000)*0.5 = 1000
        # AAPL: price=160, pnl=(160-150)*10 = 100
        mock_cursor.executemany.assert_called_once()
        updates = mock_cursor.executemany.call_args[0][1]
        assert len(updates) == 2
        assert updates[0] == (Decimal("32000.0"), Decimal("1000.0"), 1)
        assert updates[1] == (Decimal("160.0"), Decimal("100.0"), 2)

        # Verify final total nav update calls
        # T212 NAV = 100000 (cash) + 160 * 10 = 101600
        # Bybit NAV = 10000 (cash) + 32000 * 0.5 = 26000
        nav_calls = [
            call for call in mock_cursor.execute.call_args_list
            if "UPDATE paper_portfolio_balance SET total_nav = %s" in call[0][0]
        ]
        assert len(nav_calls) == 2
        # Assert values
        assert float(nav_calls[0][0][1][0]) == 101600.0
        assert float(nav_calls[1][0][1][0]) == 26000.0

    @patch.dict('os.environ', {"T212_PAPER_ROUTING_ENABLED": "false"})
    @patch('backtest_engine.live.connection.get_redis_client', return_value=None)
    @patch('backtest_engine.strategy_registry.StrategyRegistry.get')
    def test_evaluate_and_execute_strategies_buy_order(self, mock_registry_get, mock_get_redis):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value

        # Mock active configs: id, strategy_name, asset, timeframe, kelly_weight, initial_capital, initial_capital_bucket, max_capital_bucket, max_entry_price, indicator_params
        mock_cursor.fetchall.side_effect = [
            [(101, "hma_crossover", "AAPL", "5m", Decimal("0.10"), Decimal("100000"), Decimal("5000"), Decimal("10000"), Decimal("200"), None)], # config query
            [], # positions batch query (no active positions)
            [("trading212", Decimal("100000"), Decimal("100000")), ("bybit", Decimal("100000"), Decimal("100000"))], # balances query
            [
                (datetime.now(), 150.0, 151.0, 149.0, 150.5), # 1m candles
                (datetime.now(), 150.5, 152.0, 150.0, 151.0),
                (datetime.now(), 151.0, 153.0, 151.0, 152.0),
                (datetime.now(), 152.0, 154.0, 152.0, 153.0),
                (datetime.now(), 153.0, 155.0, 153.0, 154.0),
                (datetime.now(), 154.0, 156.0, 154.0, 155.0),
                (datetime.now(), 155.0, 157.0, 155.0, 156.0),
                (datetime.now(), 156.0, 158.0, 156.0, 157.0),
                (datetime.now(), 157.0, 159.0, 157.0, 158.0),
                (datetime.now(), 158.0, 160.0, 158.0, 159.0),
                (datetime.now(), 159.0, 161.0, 159.0, 160.0),
            ]
        ]

        # Mock live price query + RETURNING id for intra-cycle dedup (P1-FIX)
        mock_cursor.fetchone.side_effect = [
            (Decimal("160.0"), datetime.now(timezone.utc)), # price query with updated_at
            (101,),  # RETURNING id from INSERT
        ]

        # Mock strategy registry run results
        mock_run_result = MagicMock()
        # Create a pandas Index of datetimes
        idx = pd.date_range("2023-10-04 12:00:00", periods=3, freq="5min", tz="UTC")
        mock_run_result.bars = pd.DataFrame(
            {"long_entry": [False, True, False], "long_exit": [False, False, False]},
            index=idx
        )

        mock_strat_info = MagicMock()
        mock_strat_info.overrides_from_mapping_function.return_value = {}
        mock_strat_info.run_function.return_value = mock_run_result
        mock_registry_get.return_value = mock_strat_info

        # Market is open
        executor = SignalExecutor(is_market_open_func=lambda x: True)

        # We need to mock the index aggregation timestamp for the df resample to work
        # To avoid actual pandas resampling logic issues with mock candle rows, let's patch pd.DataFrame or mock the Aggregation
        with patch('pandas.DataFrame.resample') as mock_resample:
            mock_resample.return_value.agg.return_value.dropna.return_value = pd.DataFrame(
                {"open": [150.0, 155.0, 160.0], "high": [151.0, 156.0, 161.0], "low": [149.0, 154.0, 159.0], "close": [150.5, 162.0, 165.0]},
                index=idx
            )
            executor.evaluate_and_execute_strategies(mock_conn)

        print("--- BUY TEST EXECUTE CALLS ---")
        for call in mock_cursor.execute.call_args_list:
            print("SQL:", call[0][0])
            if len(call[0]) > 1:
                print("PARAMS:", call[0][1])

        # Verify BUY was executed because long_entry_signal is True for idx[1] (last closed bar is index -2, i.e. idx[1])
        insert_calls = [
            call for call in mock_cursor.execute.call_args_list
            if "INSERT INTO paper_positions" in call[0][0]
        ]
        assert len(insert_calls) == 1
        params = insert_calls[0][0][1]
        assert params[0] == "AAPL"
        assert params[1] == "hma_crossover"
        assert params[2] == "5m"
        # Allocated = min(kelly_size=100000*0.1=10000, cash=100000, initial_capital_bucket=5000) = 5000
        # Qty = 5000 / 160.0 = 31.25. Quantity precision = 6 by default -> 31.25
        assert float(params[3]) == 31.25
        assert params[4] == Decimal("160.0")

        # Balance was updated: cash deducted = 31.25 * 160.0 = 5000 (fee is 0.0 for trading212)
        balance_calls = [
            call for call in mock_cursor.execute.call_args_list
            if "UPDATE paper_portfolio_balance" in call[0][0]
        ]
        assert len(balance_calls) == 1
        assert float(balance_calls[0][0][1][0]) == 5000.0 # cash deducted
        assert float(balance_calls[0][0][1][1]) == 5000.0 # allocated added
        assert balance_calls[0][0][1][2] == "trading212"

    @patch.dict('os.environ', {"T212_PAPER_ROUTING_ENABLED": "false"})
    @patch('backtest_engine.live.connection.get_redis_client', return_value=None)
    @patch('backtest_engine.strategy_registry.StrategyRegistry.get')
    def test_evaluate_and_execute_strategies_sell_order(self, mock_registry_get, mock_get_redis):
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value

        # Mock active configs and positions batch
        mock_cursor.fetchall.side_effect = [
            [(101, "hma_crossover", "AAPL", "5m", Decimal("0.10"), Decimal("100000"), Decimal("5000"), Decimal("10000"), Decimal("200"), None)], # config query
            [(401, "AAPL", "hma_crossover", Decimal("10.0"), Decimal("150.0"), "5m", "VALIDATED")], # positions batch query
            [("trading212", Decimal("100000"), Decimal("100000")), ("bybit", Decimal("100000"), Decimal("100000"))], # balances query
            [
                (datetime.now(), 150.0, 151.0, 149.0, 150.5), # 1m candles
                (datetime.now(), 150.5, 152.0, 150.0, 151.0),
                (datetime.now(), 151.0, 153.0, 151.0, 152.0),
                (datetime.now(), 152.0, 154.0, 152.0, 153.0),
                (datetime.now(), 153.0, 155.0, 153.0, 154.0),
                (datetime.now(), 154.0, 156.0, 154.0, 155.0),
                (datetime.now(), 155.0, 157.0, 155.0, 156.0),
                (datetime.now(), 156.0, 158.0, 156.0, 157.0),
                (datetime.now(), 157.0, 159.0, 157.0, 158.0),
                (datetime.now(), 158.0, 160.0, 158.0, 159.0),
                (datetime.now(), 159.0, 161.0, 159.0, 160.0),
            ]
        ]

        # Mock live price query and DELETE RETURNING
        mock_cursor.fetchone.side_effect = [
            (Decimal("165.0"), datetime.now(timezone.utc)), # price query with updated_at
            (401,), # DELETE ... RETURNING id
        ]

        # Mock strategy registry run results (long_exit is True)
        mock_run_result = MagicMock()
        idx = pd.date_range("2023-10-04 12:00:00", periods=3, freq="5min", tz="UTC")
        mock_run_result.bars = pd.DataFrame(
            {"long_entry": [False, False, False], "long_exit": [False, True, False]},
            index=idx
        )

        mock_strat_info = MagicMock()
        mock_strat_info.overrides_from_mapping_function.return_value = {}
        mock_strat_info.run_function.return_value = mock_run_result
        mock_registry_get.return_value = mock_strat_info

        # Market is open
        executor = SignalExecutor(is_market_open_func=lambda x: True)

        with patch('pandas.DataFrame.resample') as mock_resample:
            mock_resample.return_value.agg.return_value.dropna.return_value = pd.DataFrame(
                {"open": [150.0, 155.0, 160.0], "high": [151.0, 156.0, 161.0], "low": [149.0, 154.0, 159.0], "close": [150.5, 162.0, 165.0]},
                index=idx
            )
            executor.evaluate_and_execute_strategies(mock_conn)

        print("--- SELL TEST EXECUTE CALLS ---")
        for call in mock_cursor.execute.call_args_list:
            print("SQL:", call[0][0])
            if len(call[0]) > 1:
                print("PARAMS:", call[0][1])

        # Verify position was deleted (SELL executed)
        delete_calls = [
            call for call in mock_cursor.execute.call_args_list
            if "DELETE FROM paper_positions WHERE id = %s" in call[0][0]
        ]
        assert len(delete_calls) == 1
        assert delete_calls[0][0][1] == (401,)

        # Verify cash balance updated:
        # net revenue = 10 * 165.0 = 1650 (fee is 0.0 for trading212)
        # entry cost = 10 * 150 = 1500
        # cash balance increased by net_revenue (1650), allocated balance decreased by entry cost (1500)
        balance_calls = [
            call for call in mock_cursor.execute.call_args_list
            if "UPDATE paper_portfolio_balance" in call[0][0]
        ]
        assert len(balance_calls) == 1
        assert float(balance_calls[0][0][1][0]) == 1650.0 # net revenue added
        assert float(balance_calls[0][0][1][1]) == 1500.0 # entry cost deducted
        assert balance_calls[0][0][1][2] == "trading212"


    @patch.dict('os.environ', {"T212_PAPER_ROUTING_ENABLED": "true"})
    @patch('backtest_engine.live.connection.get_redis_client', return_value=None)
    @patch('backtest_engine.strategy_registry.StrategyRegistry.get')
    def test_evaluate_and_execute_strategies_sell_order_with_routing_and_protection(self, mock_registry_get, mock_get_redis):
        # Given: A setup with paper routing enabled and a position to be sold
        mock_conn = MagicMock()
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value

        # Mock active configs and positions batch
        mock_cursor.fetchall.side_effect = [
            [(101, "hma_crossover", "AAPL", "5m", Decimal("0.10"), Decimal("100000"), Decimal("5000"), Decimal("10000"), Decimal("200"), None)],
            [(401, "AAPL", "hma_crossover", Decimal("10.0001"), Decimal("150.0"), "5m", "VALIDATED")], # positions batch query
            [("trading212", Decimal("100000"), Decimal("100000")), ("bybit", Decimal("100000"), Decimal("100000"))], # balances query
            [
                (datetime.now(), 150.0, 151.0, 149.0, 150.5), # 1m candles
                (datetime.now(), 150.5, 152.0, 150.0, 151.0),
                (datetime.now(), 151.0, 153.0, 151.0, 152.0),
                (datetime.now(), 152.0, 154.0, 152.0, 153.0),
                (datetime.now(), 153.0, 155.0, 153.0, 154.0),
                (datetime.now(), 154.0, 156.0, 154.0, 155.0),
                (datetime.now(), 155.0, 157.0, 155.0, 156.0),
                (datetime.now(), 156.0, 158.0, 156.0, 157.0),
                (datetime.now(), 157.0, 159.0, 157.0, 158.0),
                (datetime.now(), 158.0, 160.0, 158.0, 159.0),
                (datetime.now(), 159.0, 161.0, 159.0, 160.0),
            ]
        ]

        # Mock live price query and DELETE RETURNING
        mock_cursor.fetchone.side_effect = [
            (Decimal("165.0"), datetime.now(timezone.utc)), # price query with updated_at
            (401,), # DELETE ... RETURNING id
        ]

        # Mock strategy registry run results (long_exit is True)
        mock_run_result = MagicMock()
        idx = pd.date_range("2023-10-04 12:00:00", periods=3, freq="5min", tz="UTC")
        mock_run_result.bars = pd.DataFrame(
            {"long_entry": [False, False, False], "long_exit": [False, True, False]},
            index=idx
        )

        mock_strat_info = MagicMock()
        mock_strat_info.overrides_from_mapping_function.return_value = {}
        mock_strat_info.run_function.return_value = mock_run_result
        mock_registry_get.return_value = mock_strat_info

        # Mock Trading 212 Client and Bootstrapper
        mock_t212_client = MagicMock()
        mock_t212_client.get_positions.return_value = [
            {"instrument": {"ticker": "SAPd_EQ"}, "quantity": 0.0001},
            {"instrument": {"ticker": "AAPL_T212_TICKER"}, "quantity": 10.0001}  # real qty is 10.0001
        ]
        mock_t212_client.place_market_order.return_value = {"id": "order-123", "status": "FILLED"}

        # Mock Resolver
        mock_resolver = MagicMock()
        mock_resolver.resolve.return_value = "AAPL_T212_TICKER"

        # Mock Bootstrapper
        mock_bootstrapper = MagicMock()
        mock_bootstrapper.micro_qty = 0.0001
        mock_bootstrapper.bootstrap.return_value = []

        # Instancier le SignalExecutor avec nos mocks
        executor = SignalExecutor(
            t212_client=mock_t212_client,
            is_market_open_func=lambda x: True
        )

        # Injecter manuellement le resolver et le bootstrapper pour éviter le chargement réel
        executor._t212_resolver = mock_resolver
        executor._t212_bootstrapper = mock_bootstrapper

        with patch('pandas.DataFrame.resample') as mock_resample:
            mock_resample.return_value.agg.return_value.dropna.return_value = pd.DataFrame(
                {"open": [150.0, 155.0, 160.0], "high": [151.0, 156.0, 161.0], "low": [149.0, 154.0, 159.0], "close": [150.5, 162.0, 165.0]},
                index=idx
            )
            executor.evaluate_and_execute_strategies(mock_conn)

        # Then:
        # 1. Resolver was called to find the ticker
        mock_resolver.resolve.assert_called_once_with("AAPL")

        # 2. Trading 212 Client was called with a quantity protecting the micro-position:
        # paper qty = 10.0001, real qty = 10.0001, micro_qty = 0.0001
        # max_sellable = 10.0001 - 0.0001 = 10.0
        # sell_qty = min(10.0001, max_sellable) = 10.0
        from unittest.mock import ANY
        mock_t212_client.place_market_order.assert_called_once_with(
            ticker="AAPL_T212_TICKER",
            quantity=-10.0,
            client_order_id=ANY
        )

        # 3. Bootstrapper bootstrap was triggered right after exit commit
        mock_bootstrapper.bootstrap.assert_called_once()

