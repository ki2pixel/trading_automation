from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from decimal import Decimal

from backtest_engine.live.paper_trading.engine import PaperTradingEngine
from backtest_engine.live.paper_trading.api import router

# Setup dummy FastAPI app for testing API
from fastapi import FastAPI
app = FastAPI()
app.include_router(router)
client = TestClient(app)

class TestPaperTradingEngine:
    
    @patch('backtest_engine.live.paper_trading.engine.datetime')
    def test_market_hours_open(self, mock_datetime):
        # Mocking time to be Wednesday 12:00 UTC
        from datetime import datetime
        import pytz
        
        mock_now = datetime(2023, 10, 4, 12, 0, tzinfo=pytz.utc) # Wed
        mock_datetime.now.return_value = mock_now
        
        engine = PaperTradingEngine(db_url="sqlite:///:memory:")
        # Provide dummy market hours for test
        engine.market_hours = {
            "TEST.ASSET": {
                "open": "09:00",
                "close": "17:30",
                "tz_offset": "+01:00"
            }
        }
        
        # UTC 12:00 -> +01:00 is 13:00, which is between 09:00 and 17:30
        assert engine.is_market_open("TEST.ASSET") == True

    @patch('backtest_engine.live.paper_trading.engine.datetime')
    def test_market_hours_closed_weekend(self, mock_datetime):
        from datetime import datetime
        import pytz
        
        # Mocking time to be Saturday 12:00 UTC
        mock_now = datetime(2023, 10, 7, 12, 0, tzinfo=pytz.utc) # Sat
        mock_datetime.now.return_value = mock_now
        
        engine = PaperTradingEngine(db_url="sqlite:///:memory:")
        engine.market_hours = {
            "TEST.ASSET": {
                "open": "09:00",
                "close": "17:30",
                "tz_offset": "+01:00"
            }
        }
        
        # Weekend should be false
        assert engine.is_market_open("TEST.ASSET") == False

    @patch('backtest_engine.live.paper_trading.engine.datetime')
    def test_market_hours_closed_time(self, mock_datetime):
        from datetime import datetime
        import pytz
        
        # Mocking time to be Wed 20:00 UTC -> 21:00 local (+1)
        mock_now = datetime(2023, 10, 4, 20, 0, tzinfo=pytz.utc) # Wed
        mock_datetime.now.return_value = mock_now
        
        engine = PaperTradingEngine(db_url="sqlite:///:memory:")
        engine.market_hours = {
            "TEST.ASSET": {
                "open": "09:00",
                "close": "17:30",
                "tz_offset": "+01:00"
            }
        }
        
        assert engine.is_market_open("TEST.ASSET") == False

    @patch('backtest_engine.live.paper_trading.api._get_pool')
    def test_api_config_update(self, mock_get_pool):
        # Mock asyncpg pool chain: pool.acquire() -> conn.execute()
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(return_value="UPDATE 1")
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=False)

        mock_pool = AsyncMock()
        mock_pool.acquire = MagicMock(return_value=mock_conn)
        mock_get_pool.return_value = mock_pool
        
        payload = {
            "initial_capital": 2000,
            "initial_capital_bucket": 500,
            "max_capital_bucket": 1500,
            "max_entry_price": 50,
            "is_active": False
        }
        
        response = client.put("/api/configs/1", json=payload)
        assert response.status_code == 200
        assert response.json() == {"status": "success", "message": "Configuration updated"}
        
        # Check if execute was called properly
        mock_conn.execute.assert_called_once()
        call_args = mock_conn.execute.call_args
        query = call_args[0][0]
        assert "UPDATE paper_strategy_configs" in query
        # asyncpg uses positional $N params
        assert call_args[0][1] == 2000.0  # initial_capital
        assert call_args[0][2] == 500.0   # initial_capital_bucket
        assert call_args[0][5] == False   # is_active
        assert call_args[0][6] == 'inactive'  # run_status
        assert call_args[0][7] == 1  # config_id

    def test_update_portfolio_nav_active_api(self):
        # GIVEN: A database connection returning initial balances, and an active Trading 212 Client returning a total value
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        queries = {}
        def mock_execute(query, params=None):
            queries[query] = params
            
        mock_cursor.execute = MagicMock(side_effect=mock_execute)
        
        def mock_fetchone():
            last_query = mock_cursor.execute.call_args[0][0]
            if "SELECT cash_balance" in last_query:
                return [4995.58]
            if "SELECT current_price" in last_query:
                return [150.0]
            return None

        def mock_fetchall():
            last_query = mock_cursor.execute.call_args[0][0]
            if "SELECT id, asset, qty, entry_price" in last_query:
                return [(1, "AAPL", 10, 100.0, 150.0)]
            if "FROM paper_portfolio_balance" in last_query:
                return [("trading212", 4872.03, 0.0), ("bybit", 10000.0, 0.0)]
            if "SELECT ticker, price, updated_at FROM live_prices" in last_query:
                return [("aapl", 150.0, None)]
            return []
            
        mock_cursor.fetchone = MagicMock(side_effect=mock_fetchone)
        mock_cursor.fetchall = MagicMock(side_effect=mock_fetchall)

        engine = PaperTradingEngine(db_url="sqlite:///:memory:")
        engine.t212_client = MagicMock()
        engine.t212_client.get_account_summary.return_value = {
            "cash": {"availableToTrade": 4872.03, "reservedForOrders": 0, "inPies": 0},
            "totalValue": 4995.58
        }
        engine.is_market_open = MagicMock(return_value=True)

        with patch('backtest_engine.live.connection.get_redis_client', return_value=None):
            # WHEN: _update_portfolio_nav is executed
            engine._update_portfolio_nav(mock_conn)

        # THEN:
        # 1. Trading 212 Client summary should be requested
        engine.t212_client.get_account_summary.assert_called_once()
        
        # 2. Local DB cash_balance should be updated with API's availableToTrade
        update_calls = [
            call[0] for call in mock_cursor.execute.call_args_list 
            if "UPDATE paper_portfolio_balance SET cash_balance" in call[0][0]
        ]
        assert len(update_calls) == 1
        from decimal import Decimal
        assert update_calls[0][1] == (Decimal('4872.03'),)

        # 3. Total NAV should be updated in DB (cash_balance 4872.03 + position value 10 * 150.0 = 6372.03)
        nav_update_calls = [
            call[0] for call in mock_cursor.execute.call_args_list 
            if "UPDATE paper_portfolio_balance SET total_nav" in call[0][0]
        ]
        assert len(nav_update_calls) == 2
        assert nav_update_calls[0][1] == (Decimal('6372.03'),)
        assert nav_update_calls[1][1] == (Decimal('10000.0'),)

    def test_update_portfolio_nav_fallback_local(self):
        # GIVEN: A database connection returning a local cash balance, and no Trading 212 Client (None)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        queries = {}
        def mock_execute(query, params=None):
            queries[query] = params
            
        mock_cursor.execute = MagicMock(side_effect=mock_execute)
        
        def mock_fetchone():
            last_query = mock_cursor.execute.call_args[0][0]
            if "SELECT cash_balance" in last_query:
                return [100000.00]
            if "SELECT current_price" in last_query:
                return [150.0]
            return None

        def mock_fetchall():
            last_query = mock_cursor.execute.call_args[0][0]
            if "SELECT id, asset, qty, entry_price" in last_query:
                return [(1, "AAPL", 10, 100.0, 150.0)]
            if "FROM paper_portfolio_balance" in last_query:
                return [("trading212", 100000.0, 0.0), ("bybit", 10000.0, 0.0)]
            if "SELECT ticker, price, updated_at FROM live_prices" in last_query:
                return [("aapl", 150.0, None)]
            return []
            
        mock_cursor.fetchone = MagicMock(side_effect=mock_fetchone)
        mock_cursor.fetchall = MagicMock(side_effect=mock_fetchall)

        engine = PaperTradingEngine(db_url="sqlite:///:memory:")
        engine.t212_client = None
        engine.is_market_open = MagicMock(return_value=True)

        with patch('backtest_engine.live.connection.get_redis_client', return_value=None):
            # WHEN: _update_portfolio_nav is executed
            engine._update_portfolio_nav(mock_conn)

        # THEN:
        # 1. No query to UPDATE cash_balance should be performed
        update_calls = [
            call[0] for call in mock_cursor.execute.call_args_list 
            if "UPDATE paper_portfolio_balance SET cash_balance" in call[0][0]
        ]
        assert len(update_calls) == 0

        # 2. Total NAV should be updated in DB using the local cash balance (cash_balance 100000.00 + position value 10 * 150.0 = 101500.0)
        nav_update_calls = [
            call[0] for call in mock_cursor.execute.call_args_list 
            if "UPDATE paper_portfolio_balance SET total_nav" in call[0][0]
        ]
        assert len(nav_update_calls) == 2
        assert nav_update_calls[0][1] == (Decimal('101500.0'),)
        assert nav_update_calls[1][1] == (Decimal('10000.0'),)

    @patch('backtest_engine.live.connection.get_redis_client', return_value=None)
    @patch('backtest_engine.strategy_registry.StrategyRegistry.get')
    def test_evaluate_and_execute_strategies_buy_signal(self, mock_strat_registry_get, mock_get_redis_client):
        # GIVEN: An active strategy config, market open, no position, and a buy signal from strategy
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Mock database responses for configurations, positions, candles, balance
        from datetime import datetime, timezone
        from decimal import Decimal
        import pandas as pd
        
        def mock_fetchone():
            last_query = mock_cursor.execute.call_args[0][0]
            if "SELECT cash_balance, total_nav FROM paper_portfolio_balance" in last_query:
                return [10000.0, 10000.0] # 10k cash and nav
            if "SELECT price, updated_at FROM live_prices" in last_query:
                return (Decimal("10.0"), datetime.now(timezone.utc))
            return None

        # Return mock candles (at least 15 minutes of candles)
        mock_candles = [
            (datetime(2023, 10, 4, 12, i, tzinfo=timezone.utc), 10.0, 10.5, 9.8, 10.2)
            for i in range(30)
        ]

        def mock_fetchall():
            last_query = mock_cursor.execute.call_args[0][0]
            if "SELECT id, strategy_name, asset, timeframe" in last_query:
                # Active config
                return [(1, "momentum_based_zigzag", "ZEAL.CO", "15m", 0.1, 1000.0, 1000.0, 5000.0, 100.0, {})]
            if "SELECT id, asset, strategy_name, qty, entry_price FROM paper_positions" in last_query:
                return [] # No active positions (batched query)
            if "live_candles_1m" in last_query:
                return mock_candles
            if "SELECT ticker, price, updated_at FROM live_prices" in last_query:
                return [("zeal.co", Decimal("10.0"), datetime.now(timezone.utc))]
            return []

        mock_cursor.fetchone = MagicMock(side_effect=mock_fetchone)
        mock_cursor.fetchall = MagicMock(side_effect=mock_fetchall)

        # Mock StrategyRegistry run_function to return a Buy signal
        mock_strat_info = MagicMock()
        mock_strat_registry_get.return_value = mock_strat_info
        
        # We need run_result.bars to contain a long_entry at the last closed time
        # Let's align the times
        df_1m = pd.DataFrame(mock_candles, columns=["timestamp_minute", "open", "high", "low", "close"])
        df_1m.set_index("timestamp_minute", inplace=True)
        df_aggregated = df_1m.resample("15min").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
        
        last_closed_time = df_aggregated.index[-2]
        
        result_bars = df_aggregated.copy()
        result_bars["long_entry"] = False
        result_bars.loc[last_closed_time, "long_entry"] = True # Set Buy signal
        
        mock_run_result = MagicMock()
        mock_run_result.bars = result_bars
        mock_strat_info.run_function.return_value = mock_run_result
        mock_strat_info.overrides_from_mapping_function.return_value = MagicMock()

        engine = PaperTradingEngine(db_url="sqlite:///:memory:")
        engine.t212_client = MagicMock()
        engine.is_market_open = MagicMock(return_value=True)

        # WHEN: _evaluate_and_execute_strategies is executed
        engine._evaluate_and_execute_strategies(mock_conn)

        # THEN:
        # 1. The strategy registry should be queried for "momentum_based_zigzag"
        mock_strat_registry_get.assert_called_once_with("momentum_based_zigzag")
        
        # 2. A buy order should be written to the database (10% Kelly of 10k NAV = 1000 EUR allocated, 100 units @ 10.0 EUR)
        buy_calls = [
            call[0] for call in mock_cursor.execute.call_args_list
            if "INSERT INTO paper_positions" in call[0][0]
        ]
        assert len(buy_calls) == 1
        assert "ZEAL.CO" in buy_calls[0][1]
        assert buy_calls[0][1][2] == 100.0 # qty
        assert buy_calls[0][1][3] == Decimal('10.0') # entry_price

        # 3. Cash balance should be deducted
        cash_deduct_calls = [
            call[0] for call in mock_cursor.execute.call_args_list
            if "UPDATE paper_portfolio_balance" in call[0][0]
        ]
        assert len(cash_deduct_calls) == 1
        assert cash_deduct_calls[0][1] == (Decimal('1000.0'), Decimal('1000.0'), 'trading212')

    @patch('backtest_engine.live.connection.get_redis_client', return_value=None)
    @patch('backtest_engine.strategy_registry.StrategyRegistry.get')
    def test_evaluate_and_execute_strategies_error_logging(self, mock_strat_registry_get, mock_get_redis_client):
        # GIVEN: An active strategy config, and an exception raised during strategy run
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        from datetime import datetime, timezone
        
        # Return mock configs, positions, candles
        mock_candles = [
            (datetime(2023, 10, 4, 12, i, tzinfo=timezone.utc), 10.0, 10.5, 9.8, 10.2)
            for i in range(30)
        ]
        
        def mock_fetchall():
            last_query = mock_cursor.execute.call_args[0][0]
            if "SELECT id, strategy_name, asset, timeframe" in last_query:
                return [(1, "momentum_based_zigzag", "ZEAL.CO", "15m", 0.1, 1000.0, 1000.0, 5000.0, 100.0, {})]
            if "live_candles_1m" in last_query:
                return mock_candles
            if "SELECT ticker, price, updated_at FROM live_prices" in last_query:
                return [("zeal.co", Decimal("10.0"), datetime.now(timezone.utc))]
            return []

        def mock_fetchone():
            last_query = mock_cursor.execute.call_args[0][0]
            if "SELECT id, qty, entry_price FROM paper_positions" in last_query:
                return None # No position open
            if "SELECT price, updated_at FROM live_prices" in last_query:
                return (Decimal("10.0"), datetime.now(timezone.utc))
            return None

        mock_cursor.fetchone = MagicMock(side_effect=mock_fetchone)
        mock_cursor.fetchall = MagicMock(side_effect=mock_fetchall)

        # Force the strategy execution to raise an exception
        mock_strat_registry_get.side_effect = Exception("Test strategy simulation error")

        engine = PaperTradingEngine(db_url="sqlite:///:memory:")
        engine.is_market_open = MagicMock(return_value=True)

        # WHEN: _evaluate_and_execute_strategies is executed
        engine._evaluate_and_execute_strategies(mock_conn)

        # THEN: The database status should be set to 'error' and last_error recorded
        error_update_calls = [
            call[0] for call in mock_cursor.execute.call_args_list
            if "UPDATE paper_strategy_configs" in call[0][0] and "run_status = 'error'" in call[0][0]
        ]
        assert len(error_update_calls) == 1
        assert "last_error = %s" in error_update_calls[0][0]
        assert error_update_calls[0][1] == ("Test strategy simulation error", 1)

    @patch('backtest_engine.live.connection.get_redis_client', return_value=None)
    @patch('backtest_engine.strategy_registry.StrategyRegistry.get')
    def test_evaluate_and_execute_strategies_success_clears_error(self, mock_strat_registry_get, mock_get_redis_client):
        # GIVEN: An active strategy config, and a successful run
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        from datetime import datetime, timezone
        import pandas as pd
        
        # Return mock configs, positions, candles
        mock_candles = [
            (datetime(2023, 10, 4, 12, i, tzinfo=timezone.utc), 10.0, 10.5, 9.8, 10.2)
            for i in range(30)
        ]
        
        def mock_fetchone():
            last_query = mock_cursor.execute.call_args[0][0]
            if "SELECT id, qty, entry_price FROM paper_positions" in last_query:
                return None # No position open
            if "SELECT cash_balance, total_nav FROM paper_portfolio_balance" in last_query:
                return [10000.0, 10000.0]
            if "SELECT price, updated_at FROM live_prices" in last_query:
                return (Decimal("10.0"), datetime.now(timezone.utc))
            return None

        def mock_fetchall():
            last_query = mock_cursor.execute.call_args[0][0]
            if "SELECT id, strategy_name, asset, timeframe" in last_query:
                return [(1, "momentum_based_zigzag", "ZEAL.CO", "15m", 0.1, 1000.0, 1000.0, 5000.0, 100.0, {})]
            if "live_candles_1m" in last_query:
                return mock_candles
            if "SELECT ticker, price, updated_at FROM live_prices" in last_query:
                return [("zeal.co", Decimal("10.0"), datetime.now(timezone.utc))]
            return []

        mock_cursor.fetchone = MagicMock(side_effect=mock_fetchone)
        mock_cursor.fetchall = MagicMock(side_effect=mock_fetchall)

        # Mock StrategyRegistry run_function to return a dummy result without entry signals
        mock_strat_info = MagicMock()
        mock_strat_registry_get.return_value = mock_strat_info
        
        df_1m = pd.DataFrame(mock_candles, columns=["timestamp_minute", "open", "high", "low", "close"])
        df_1m.set_index("timestamp_minute", inplace=True)
        df_aggregated = df_1m.resample("15min").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
        
        last_closed_time = df_aggregated.index[-2]
        result_bars = df_aggregated.copy()
        result_bars["long_entry"] = False
        result_bars["long_exit"] = False
        
        mock_run_result = MagicMock()
        mock_run_result.bars = result_bars
        mock_strat_info.run_function.return_value = mock_run_result
        mock_strat_info.overrides_from_mapping_function.return_value = MagicMock()

        engine = PaperTradingEngine(db_url="sqlite:///:memory:")
        engine.is_market_open = MagicMock(return_value=True)

        # WHEN: _evaluate_and_execute_strategies is executed
        engine._evaluate_and_execute_strategies(mock_conn)

        # THEN: The database status should be set to 'active' and last_error reset to NULL
        active_update_calls = [
            call[0] for call in mock_cursor.execute.call_args_list
            if "UPDATE paper_strategy_configs" in call[0][0] and "run_status = 'active'" in call[0][0]
        ]
        assert len(active_update_calls) == 1
        assert "last_error = NULL" in active_update_calls[0][0]
        assert active_update_calls[0][1] == (1,)

    @patch('backtest_engine.live.connection.get_redis_client', return_value=None)
    @patch('backtest_engine.strategy_registry.StrategyRegistry.get')
    def test_bybit_crypto_transaction_fees(self, mock_strat_registry_get, mock_get_redis_client):
        # GIVEN: A crypto configuration for ltcusdt (Bybit)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        from datetime import datetime, timezone
        from decimal import Decimal
        import pandas as pd
        
        mock_candles = [
            (datetime(2023, 10, 4, 12 + i // 60, i % 60, tzinfo=timezone.utc), 10.0, 10.5, 9.8, 10.2)
            for i in range(120)
        ]
        
        def mock_fetchone():
            last_query = mock_cursor.execute.call_args[0][0]
            if "SELECT cash_balance, total_nav FROM paper_portfolio_balance" in last_query:
                return [10000.0, 10000.0]
            if "SELECT price, updated_at FROM live_prices" in last_query:
                return (Decimal("10.0"), datetime.now(timezone.utc))
            return None

        def mock_fetchall():
            last_query = mock_cursor.execute.call_args[0][0]
            if "SELECT id, strategy_name, asset, timeframe" in last_query:
                return [(904, "cybernetic_hilbert", "ltcusdt", "45m", 0.1, 1000.0, 1000.0, 5000.0, 100.0, {})]
            if "SELECT id, asset, strategy_name, qty, entry_price FROM paper_positions" in last_query:
                return [] # No active positions (batched query)
            if "live_candles_1m" in last_query:
                return mock_candles
            if "SELECT ticker, price, updated_at FROM live_prices" in last_query:
                return [("ltcusdt", Decimal("10.0"), datetime.now(timezone.utc))]
            return []

        mock_cursor.fetchone = MagicMock(side_effect=mock_fetchone)
        mock_cursor.fetchall = MagicMock(side_effect=mock_fetchall)

        # Mock StrategyRegistry to trigger a BUY signal
        mock_strat_info = MagicMock()
        mock_strat_registry_get.return_value = mock_strat_info
        
        df_1m = pd.DataFrame(mock_candles, columns=["timestamp_minute", "open", "high", "low", "close"])
        df_1m.set_index("timestamp_minute", inplace=True)
        df_aggregated = df_1m.resample("45min").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
        
        last_closed_time = df_aggregated.index[-2]
        result_bars = df_aggregated.copy()
        result_bars["long_entry"] = False
        result_bars["long_exit"] = False
        result_bars.loc[last_closed_time, "long_entry"] = True # Buy signal
        
        mock_run_result = MagicMock()
        mock_run_result.bars = result_bars
        mock_strat_info.run_function.return_value = mock_run_result
        mock_strat_info.overrides_from_mapping_function.return_value = MagicMock()

        engine = PaperTradingEngine(db_url="sqlite:///:memory:")
        engine.is_market_open = MagicMock(return_value=True)

        # WHEN: _evaluate_and_execute_strategies is executed
        engine._evaluate_and_execute_strategies(mock_conn)

        # THEN: The BUY cost should include the 0.1% Bybit fee
        # 10% Kelly of 10k NAV = 1000 USDT allocated, at 10.2 USDT price -> 98.039216 units
        # Rounded to 6 decimals (precision by default): 98.039216
        # Cost = 98.039216 * 10.2 = 1000.0000032
        # Fee = 1000.0000032 * 0.001 = 1.0000000032
        # Total buy cost = 1001.0000032032
        balance_update_calls = [
            call for call in mock_cursor.execute.call_args_list
            if "UPDATE paper_portfolio_balance" in call[0][0] and "cash_balance = cash_balance -" in call[0][0]
        ]
        assert len(balance_update_calls) == 1
        total_cost_arg = balance_update_calls[0][0][1][0]
        allocated_arg = balance_update_calls[0][0][1][1]
        source_arg = balance_update_calls[0][0][1][2]
        
        # Verify that total deducted cost is higher than allocated value by exactly 0.1%
        assert source_arg == 'bybit'
        assert abs(total_cost_arg - allocated_arg * Decimal('1.001')) < Decimal('0.00001')
        
        # Verify transaction log records total cost including fee
        tx_calls = [
            call for call in mock_cursor.execute.call_args_list
            if "INSERT INTO paper_transactions" in call[0][0] and "BUY" in call[0][0]
        ]
        assert len(tx_calls) == 1
        tx_total_value = tx_calls[0][0][1][4]
        assert tx_total_value == total_cost_arg


    @patch('backtest_engine.live.paper_trading.engine.get_eurusd_rate')
    @patch('backtest_engine.strategy_registry.StrategyRegistry.get')
    @patch('backtest_engine.live.connection.get_redis_client', return_value=None)
    def test_bybit_secured_profit_routing(self, mock_get_redis_client, mock_strat_registry_get, mock_get_eurusd_rate):
        # GIVEN: A crypto position for ltcusdt (Bybit) with a profitable exit trigger
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        from datetime import datetime, timezone
        from decimal import Decimal
        import pandas as pd
        
        mock_get_eurusd_rate.return_value = Decimal('1.10')
        mock_get_redis_client.return_value = None
        
        # Candles for historical reference
        from datetime import timedelta
        start_time = datetime(2023, 10, 4, 12, 0, tzinfo=timezone.utc)
        mock_candles = [
            (start_time + timedelta(minutes=i), 100.0, 100.0, 100.0, 100.0)
            for i in range(2500)
        ]
        
        def mock_fetchone():
            last_query = mock_cursor.execute.call_args[0][0]
            if "DELETE FROM paper_positions WHERE id = %s RETURNING id" in last_query:
                return (99,)
            if "SELECT price, updated_at FROM live_prices" in last_query:
                return (Decimal("120.0"), datetime.now(timezone.utc))
            return None

        def mock_fetchall():
            last_query = mock_cursor.execute.call_args[0][0]
            if "SELECT id, strategy_name, asset, timeframe" in last_query:
                return [(904, "cybernetic_hilbert", "ltcusdt", "45m", 0.1, 1000.0, 1000.0, 5000.0, 100.0, {"enable_take_profit": True, "take_profit_pct": 5.0})]
            if "SELECT id, asset, strategy_name, qty, entry_price FROM paper_positions" in last_query:
                return [(99, "ltcusdt", "cybernetic_hilbert", Decimal("10.0"), Decimal("100.0"))]
            if "live_candles_1m" in last_query:
                return mock_candles
            if "SELECT ticker, price, updated_at FROM live_prices" in last_query:
                return [("ltcusdt", Decimal("120.0"), datetime.now(timezone.utc))]
            return []

        mock_cursor.fetchone = MagicMock(side_effect=mock_fetchone)
        mock_cursor.fetchall = MagicMock(side_effect=mock_fetchall)

        # Mock StrategyRegistry to return a result
        mock_strat_info = MagicMock()
        mock_strat_registry_get.return_value = mock_strat_info
        
        df_1m = pd.DataFrame(mock_candles, columns=["timestamp_minute", "open", "high", "low", "close"])
        df_1m.set_index("timestamp_minute", inplace=True)
        df_aggregated = df_1m.resample("45min").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
        
        result_bars = df_aggregated.copy()
        result_bars["long_entry"] = False
        result_bars["long_exit"] = False
        
        mock_run_result = MagicMock()
        mock_run_result.bars = result_bars
        mock_strat_info.run_function.return_value = mock_run_result
        mock_strat_info.overrides_from_mapping_function.return_value = MagicMock()

        engine = PaperTradingEngine(db_url="sqlite:///:memory:")
        engine.is_market_open = MagicMock(return_value=True)

        # WHEN: _evaluate_and_execute_strategies is executed
        engine._evaluate_and_execute_strategies(mock_conn)

        # THEN:
        portfolio_update_calls = [
            call for call in mock_cursor.execute.call_args_list
            if "UPDATE paper_portfolio_balance" in call[0][0]
        ]
        assert len(portfolio_update_calls) == 1
        query, params = portfolio_update_calls[0][0]
        assert "secured_balance = secured_balance +" in query
        assert "cash_balance = cash_balance +" in query
        
        cash_balance_added = params[0]
        secured_balance_added = params[1]
        allocated_balance_removed = params[2]
        source_arg = params[3]
        
        assert source_arg == 'bybit'
        assert abs(cash_balance_added - Decimal('1001.0')) < Decimal('0.0001')
        assert abs(secured_balance_added - Decimal('179.818181')) < Decimal('0.0001')
        assert abs(allocated_balance_removed - Decimal('1000.0')) < Decimal('0.0001')


