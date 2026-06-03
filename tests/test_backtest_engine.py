from __future__ import annotations

import io
import importlib.util
import json
import sys
import tempfile
from contextlib import redirect_stdout
from threading import Thread
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
import pandas as pd

from backtest_engine.__main__ import build_parser, cmd_interpret_optimization, cmd_optimize
from backtest_engine.broker import BrokerConfig, BrokerSimulator, Order
from backtest_engine.configuration import inactive_parameter_names, load_strategy_config
from backtest_engine.data import filter_time_window, load_canonical_market_data, resample_canonical_market_data, validate_timeframe_minutes
from backtest_engine.metrics import MetricsInput, bars_per_year_for_timeframe, compute_metrics
from backtest_engine.optimizer import (
    allowed_score_metrics,
    build_parameter_spec,
    create_optimization_output_dir,
    estimate_iterations,
    generate_parameter_grid,
    parse_cli_parameter,
    run_grid_optimization,
    list_canonical_symbols,
    validate_iteration_limits,
    validate_score_metric,
    validate_parameter_grid,
)
from backtest_engine.reports import BacktestRunResult, write_html_summary
from backtest_engine.report_interpreter import interpret_optimization_results
import backtest_engine.strategies.hma_crossover as hma_crossover_module
from backtest_engine.strategies.hma_crossover import HMAConfigOverrides, run_hma_crossover
from backtest_engine.web import OptimizerJob, OptimizerJobStore, create_optimizer_app, resolve_repo_path, run_optimizer_worker


class CanonicalDataLoaderTests(unittest.TestCase):
    def test_loads_canonical_csv_gzip_with_timestamp_column(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            out = repo_root / "storage" / "processed" / "market_data_5m"
            out.mkdir(parents=True)
            frame = pd.DataFrame(
                {
                    "timestamp": pd.date_range("2024-01-01", periods=3, freq="5min"),
                    "symbol": ["TEST"] * 3,
                    "open": [10.0, 11.0, 12.0],
                    "high": [10.5, 11.5, 12.5],
                    "low": [9.5, 10.5, 11.5],
                    "close": [10.2, 11.2, 12.2],
                    "volume": [100, 200, 300],
                }
            )
            frame.to_csv(out / "TEST.csv.gz", index=False, compression="gzip")

            loaded = load_canonical_market_data("TEST", repo_root=repo_root)

            self.assertEqual(len(loaded), 3)
            self.assertIsInstance(loaded.index, pd.DatetimeIndex)
            self.assertEqual(list(loaded["close"]), [10.2, 11.2, 12.2])

    def test_rejects_invalid_canonical_ohlc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            out = repo_root / "storage" / "processed" / "market_data_5m"
            out.mkdir(parents=True)
            frame = pd.DataFrame(
                {
                    "timestamp": ["2024-01-01 00:00:00"],
                    "open": [10.0],
                    "high": [9.0],
                    "low": [9.5],
                    "close": [10.0],
                    "volume": [100],
                }
            )
            frame.to_csv(out / "BAD.csv.gz", index=False, compression="gzip")

            with self.assertRaisesRegex(ValueError, "invalid OHLC"):
                load_canonical_market_data("BAD", repo_root=repo_root)

    def test_rejects_unsupported_timeframes(self) -> None:
        with self.assertRaisesRegex(ValueError, "one of"):
            validate_timeframe_minutes(7)

        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            with self.assertRaisesRegex(ValueError, "one of"):
                load_canonical_market_data("TEST", repo_root=repo_root, timeframe_minutes=7)

    def test_resamples_canonical_5m_data_to_requested_timeframe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            out = repo_root / "storage" / "processed" / "market_data_5m"
            out.mkdir(parents=True)
            frame = pd.DataFrame(
                {
                    "timestamp": pd.date_range("2024-01-01 09:30:00", periods=6, freq="5min"),
                    "symbol": ["TEST"] * 6,
                    "open": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0],
                    "high": [10.5, 11.5, 12.5, 13.5, 14.5, 15.5],
                    "low": [9.5, 10.5, 11.5, 12.5, 13.5, 14.5],
                    "close": [10.2, 11.2, 12.2, 13.2, 14.2, 15.2],
                    "volume": [100, 200, 300, 400, 500, 600],
                }
            )
            frame.to_csv(out / "TEST.csv.gz", index=False, compression="gzip")

            loaded = load_canonical_market_data("TEST", repo_root=repo_root, timeframe_minutes=15)

            self.assertEqual(len(loaded), 2)
            self.assertEqual(list(loaded.index), list(pd.to_datetime(["2024-01-01 09:30:00", "2024-01-01 09:45:00"])))
            self.assertEqual(list(loaded["open"]), [10.0, 13.0])
            self.assertEqual(list(loaded["high"]), [12.5, 15.5])
            self.assertEqual(list(loaded["low"]), [9.5, 12.5])
            self.assertEqual(list(loaded["close"]), [12.2, 15.2])
            self.assertEqual(list(loaded["volume"]), [600, 1500])

    def test_loads_direct_higher_timeframe_dataset_when_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            out_5m = repo_root / "storage" / "processed" / "market_data_5m"
            out_15m = repo_root / "storage" / "processed" / "market_data_15m"
            out_5m.mkdir(parents=True)
            out_15m.mkdir(parents=True)
            base_frame = pd.DataFrame(
                {
                    "timestamp": pd.date_range("2024-01-01 09:30:00", periods=3, freq="5min"),
                    "open": [10.0, 11.0, 12.0],
                    "high": [10.5, 11.5, 12.5],
                    "low": [9.5, 10.5, 11.5],
                    "close": [10.2, 11.2, 12.2],
                    "volume": [100, 200, 300],
                }
            )
            direct_frame = pd.DataFrame(
                {
                    "timestamp": ["2024-01-01 09:30:00"],
                    "open": [50.0],
                    "high": [55.0],
                    "low": [45.0],
                    "close": [54.0],
                    "volume": [999],
                }
            )
            base_frame.to_csv(out_5m / "TEST.csv.gz", index=False, compression="gzip")
            direct_frame.to_csv(out_15m / "TEST.csv.gz", index=False, compression="gzip")

            loaded = load_canonical_market_data("TEST", repo_root=repo_root, timeframe_minutes=15)

            self.assertEqual(len(loaded), 1)
            self.assertEqual(float(loaded.iloc[0]["close"]), 54.0)
            self.assertEqual(float(loaded.iloc[0]["volume"]), 999.0)

    def test_list_canonical_symbols_uses_timeframe_with_5m_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            out = repo_root / "storage" / "processed" / "market_data_5m"
            out.mkdir(parents=True)
            (out / "TEST.csv.gz").write_bytes(b"")

            self.assertEqual(list_canonical_symbols(repo_root, timeframe_minutes=15), ["TEST"])

    def test_resample_helper_preserves_ohlcv_rules(self) -> None:
        index = pd.date_range("2024-01-01 00:00:00", periods=3, freq="5min")
        data = pd.DataFrame(
            {
                "open": [1.0, 2.0, 3.0],
                "high": [2.0, 3.0, 4.0],
                "low": [0.5, 1.5, 2.5],
                "close": [1.5, 2.5, 3.5],
                "volume": [10, 20, 30],
            },
            index=index,
        )

        resampled = resample_canonical_market_data(data, 15)

        self.assertEqual(len(resampled), 1)
        self.assertEqual(float(resampled.iloc[0]["open"]), 1.0)
        self.assertEqual(float(resampled.iloc[0]["high"]), 4.0)
        self.assertEqual(float(resampled.iloc[0]["low"]), 0.5)
        self.assertEqual(float(resampled.iloc[0]["close"]), 3.5)
        self.assertEqual(float(resampled.iloc[0]["volume"]), 60.0)

    def test_filters_canonical_data_to_inclusive_date_window(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            out = repo_root / "storage" / "processed" / "market_data_5m"
            out.mkdir(parents=True)
            frame = pd.DataFrame(
                {
                    "timestamp": pd.date_range("2024-01-01", periods=5, freq="D"),
                    "open": [10.0, 11.0, 12.0, 13.0, 14.0],
                    "high": [10.5, 11.5, 12.5, 13.5, 14.5],
                    "low": [9.5, 10.5, 11.5, 12.5, 13.5],
                    "close": [10.2, 11.2, 12.2, 13.2, 14.2],
                    "volume": [100, 200, 300, 400, 500],
                }
            )
            frame.to_csv(out / "TEST.csv.gz", index=False, compression="gzip")

            loaded = load_canonical_market_data(
                "TEST",
                repo_root=repo_root,
                start_date="2024-01-02",
                end_date="2024-01-04",
            )

            self.assertEqual(len(loaded), 3)
            self.assertEqual(str(loaded.index[0]), "2024-01-02 00:00:00")
            self.assertEqual(str(loaded.index[-1]), "2024-01-04 00:00:00")

    def test_filter_time_window_rejects_inverted_dates(self) -> None:
        data = pd.DataFrame(
            {"close": [1.0]},
            index=pd.DatetimeIndex(["2024-01-01"]),
        )

        with self.assertRaisesRegex(ValueError, "start_date must be <= end_date"):
            filter_time_window(data, start_date="2024-01-02", end_date="2024-01-01")


class MetricsTests(unittest.TestCase):
    def test_compute_metrics_adds_benchmark_exposure_and_trade_stats(self) -> None:
        index = pd.date_range("2024-01-01", periods=3, freq="5min")
        bars = pd.DataFrame({"close": [10.0, 11.0, 12.0]}, index=index)
        bars["high"] = [10.5, 11.5, 12.5]
        bars["low"] = [9.5, 10.5, 11.5]
        state = pd.DataFrame(
            {
                "realized_net_pnl_on_fill": [0.0, 2.0, -1.0],
                "estimated_net_if_closed_now": [0.0, 0.0, 0.0],
                "position_abs_size": [0.0, 1.0, 1.0],
                "position_avg_price": [0.0, 10.0, 10.0],
            },
            index=index,
        )
        trades = pd.DataFrame(
            {
                "entry_index": [index[0], index[1]],
                "exit_index": [index[1], index[2]],
                "side": ["long", "short"],
                "qty": [1.0, 1.0],
                "entry_price": [10.0, 11.0],
                "net_pnl": [2.0, -1.0],
                "estimated_costs": [0.1, 0.2],
                "bars_held": [2, 4],
            }
        )

        metrics, equity = compute_metrics(
            MetricsInput(
                symbol="TEST",
                strategy="unit",
                initial_capital=100.0,
                bars=bars,
                state=state,
                trades=trades,
            )
        )

        self.assertEqual(metrics["closed_trades"], 2)
        self.assertAlmostEqual(metrics["average_bars_held"], 3.0)
        self.assertAlmostEqual(metrics["exposure_pct"], 2 / 3 * 100.0)
        self.assertAlmostEqual(metrics["buy_hold_return_pct"], 20.0)
        self.assertAlmostEqual(metrics["commission_paid"], 0.3)
        self.assertEqual(metrics["long_closed_trades"], 1)
        self.assertEqual(metrics["short_closed_trades"], 1)
        self.assertAlmostEqual(metrics["average_win_loss_ratio"], 2.0)
        self.assertAlmostEqual(metrics["max_trade_runup"], 1.5)
        self.assertAlmostEqual(metrics["max_trade_drawdown"], -1.5)
        self.assertAlmostEqual(metrics["max_position_value"], 10.0)
        self.assertIn("sharpe_ratio", metrics)
        self.assertIn("peak_equity", equity.columns)

    def test_trade_excursion_metrics_are_vectorized_for_multiple_trade_windows(self) -> None:
        index = pd.date_range("2024-01-01", periods=5, freq="5min")
        bars = pd.DataFrame(
            {
                "close": [10.0, 11.0, 12.0, 8.0, 14.0],
                "high": [10.0, 12.0, 13.0, 11.0, 15.0],
                "low": [9.0, 8.0, 10.0, 7.0, 14.0],
            },
            index=index,
        )
        state = pd.DataFrame(
            {
                "realized_net_pnl_on_fill": [0.0] * len(index),
                "estimated_net_if_closed_now": [0.0] * len(index),
            },
            index=index,
        )
        trades = pd.DataFrame(
            {
                "entry_index": [index[0], index[1], index[3], index[0], index[0], pd.Timestamp("2023-12-31"), index[4]],
                "exit_index": [index[2], index[3], index[4], index[2], index[2], index[1], index[3]],
                "side": ["long", "short", "long", "long", "flat", "long", "long"],
                "qty": [2.0, 3.0, 1.0, 0.0, 1.0, 1.0, 1.0],
                "entry_price": [10.0, 12.0, 8.0, 10.0, 10.0, 10.0, 10.0],
                "net_pnl": [0.0] * 7,
            }
        )

        metrics, _ = compute_metrics(
            MetricsInput(
                symbol="TEST",
                strategy="unit",
                initial_capital=100.0,
                bars=bars,
                state=state,
                trades=trades,
            )
        )

        self.assertAlmostEqual(metrics["max_trade_runup"], 15.0)
        self.assertAlmostEqual(metrics["max_trade_runup_pct"], 87.5)
        self.assertAlmostEqual(metrics["max_trade_drawdown"], -4.0)
        self.assertAlmostEqual(metrics["max_trade_drawdown_pct"], -20.0)
        self.assertAlmostEqual(metrics["average_trade_runup"], 28.0 / 3.0)
        self.assertAlmostEqual(metrics["average_trade_drawdown"], -8.0 / 3.0)

    def test_risk_ratios_use_requested_timeframe_for_annualization(self) -> None:
        index = pd.date_range("2024-01-01", periods=5, freq="5min")
        bars = pd.DataFrame({"close": [100.0, 101.0, 100.5, 102.0, 101.0]}, index=index)
        bars["high"] = bars["close"]
        bars["low"] = bars["close"]
        state = pd.DataFrame(
            {
                "realized_net_pnl_on_fill": [0.0, 1.0, -0.5, 1.5, -1.0],
                "estimated_net_if_closed_now": [0.0] * len(index),
            },
            index=index,
        )

        metrics_5m, _ = compute_metrics(
            MetricsInput(
                symbol="TEST",
                strategy="unit",
                initial_capital=100.0,
                bars=bars,
                state=state,
                trades=pd.DataFrame(),
                timeframe_minutes=5,
            )
        )
        metrics_15m, _ = compute_metrics(
            MetricsInput(
                symbol="TEST",
                strategy="unit",
                initial_capital=100.0,
                bars=bars,
                state=state,
                trades=pd.DataFrame(),
                timeframe_minutes=15,
            )
        )

        self.assertEqual(bars_per_year_for_timeframe(5), 252 * 78)
        self.assertEqual(bars_per_year_for_timeframe(15), 252 * 26)
        self.assertIsNotNone(metrics_5m["sharpe_ratio"])
        self.assertIsNotNone(metrics_15m["sharpe_ratio"])
        self.assertGreater(abs(metrics_5m["sharpe_ratio"]), abs(metrics_15m["sharpe_ratio"]))


class BrokerSimulatorTests(unittest.TestCase):
    def test_market_round_trip_closes_trade(self) -> None:
        broker = BrokerSimulator(BrokerConfig(initial_capital=1000.0, commission_fixed=1.0))

        broker.fill_order(Order(id="entry", side="buy", quantity=2), "t0", 10.0)
        broker.fill_order(Order(id="exit", side="sell", quantity=2, comment="close"), "t1", 12.0)

        trades = broker.closed_trades_frame()
        self.assertTrue(broker.position.is_flat)
        self.assertEqual(len(trades), 1)
        self.assertAlmostEqual(float(trades.iloc[0]["gross_pnl"]), 4.0)
        self.assertAlmostEqual(float(trades.iloc[0]["net_pnl"]), 2.0)

    def test_side_specific_short_costs_are_allocated_round_trip(self) -> None:
        broker = BrokerSimulator(
            BrokerConfig(
                initial_capital=1000.0,
                commission_fixed_short=3.0,
                slippage_per_side_short=0.5,
            )
        )

        broker.fill_order(Order(id="entry", side="sell", quantity=1, cost_side="short"), "t0", 20.0)
        broker.fill_order(Order(id="exit", side="buy", quantity=1, cost_side="short"), "t1", 15.0)

        trade = broker.closed_trades_frame().iloc[0]
        self.assertAlmostEqual(float(trade["gross_pnl"]), 5.0)
        self.assertAlmostEqual(float(trade["commission"]), 7.0)
        self.assertAlmostEqual(float(trade["net_pnl"]), -2.0)

    def test_pyramided_entries_allocate_all_entry_commissions(self) -> None:
        broker = BrokerSimulator(BrokerConfig(initial_capital=1000.0, commission_fixed=1.0))

        broker.fill_order(Order(id="entry-1", side="buy", quantity=1), "t0", 10.0)
        broker.fill_order(Order(id="entry-2", side="buy", quantity=1), "t1", 12.0)
        broker.fill_order(Order(id="exit", side="sell", quantity=2, comment="close"), "t2", 15.0)

        trade = broker.closed_trades_frame().iloc[0]
        self.assertTrue(broker.position.is_flat)
        self.assertAlmostEqual(float(trade["entry_price"]), 11.0)
        self.assertAlmostEqual(float(trade["gross_pnl"]), 8.0)
        self.assertAlmostEqual(float(trade["commission"]), 3.0)
        self.assertAlmostEqual(float(trade["net_pnl"]), 5.0)
        self.assertEqual(trade["entry_order_id"], "entry-1")

    def test_reversal_prorates_exit_and_new_entry_commission(self) -> None:
        broker = BrokerSimulator(BrokerConfig(initial_capital=1000.0, commission_fixed=3.0))

        broker.fill_order(Order(id="long-entry", side="buy", quantity=2), "t0", 10.0)
        broker.fill_order(Order(id="reverse-short", side="sell", quantity=3), "t1", 9.0)
        broker.fill_order(Order(id="short-exit", side="buy", quantity=1), "t2", 8.0)

        trades = broker.closed_trades_frame()
        self.assertTrue(broker.position.is_flat)
        self.assertEqual(len(trades), 2)
        self.assertAlmostEqual(float(trades.iloc[0]["gross_pnl"]), -2.0)
        self.assertAlmostEqual(float(trades.iloc[0]["commission"]), 5.0)
        self.assertAlmostEqual(float(trades.iloc[0]["net_pnl"]), -7.0)
        self.assertAlmostEqual(float(trades.iloc[1]["gross_pnl"]), 1.0)
        self.assertAlmostEqual(float(trades.iloc[1]["commission"]), 4.0)
        self.assertAlmostEqual(float(trades.iloc[1]["net_pnl"]), -3.0)
        self.assertAlmostEqual(float(trades["commission"].sum()), 9.0)

    def test_mark_to_market_equity_uses_point_value(self) -> None:
        broker = BrokerSimulator(BrokerConfig(initial_capital=10000.0, point_value=10.0))

        broker.fill_order(Order(id="entry", side="buy", quantity=2), "t0", 100.0)

        self.assertAlmostEqual(broker.cash, 8000.0)
        self.assertAlmostEqual(broker.mark_to_market_equity(105.0), 10100.0)

        broker.fill_order(Order(id="exit", side="sell", quantity=2), "t1", 105.0)
        trade = broker.closed_trades_frame().iloc[0]
        self.assertAlmostEqual(float(trade["gross_pnl"]), 100.0)
        self.assertAlmostEqual(broker.cash, 10100.0)


class StrategyConfigurationTests(unittest.TestCase):
    def test_loads_hma_json_config_and_coerces_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "hma_test_config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "strategy": "hma_crossover",
                        "parameters": {
                            "fast_len": "48",
                            "slow_len": 100.0,
                            "confirm_on_close": "true",
                            "estimated_commission_per_order_short": "0",
                            "unknown_custom_field": "ignored",
                        },
                        "backtest": {
                            "initial_capital": 1000,
                            "base_currency": "Default",
                            "default_order_size": 100,
                            "commission": 0,
                        },
                    }
                ),
                encoding="utf-8",
            )

            config = load_strategy_config(config_path, strategy="hma_crossover")

        self.assertEqual(config.strategy, "hma_crossover")
        self.assertEqual(config.parameters["fast_len"], 48)
        self.assertEqual(config.parameters["slow_len"], 100)
        self.assertEqual(config.parameters["confirm_on_close"], True)
        self.assertEqual(config.parameters["estimated_commission_per_order_short"], 0.0)
        self.assertNotIn("unknown_custom_field", config.parameters)
        self.assertEqual(config.backtest["initial_capital"], 1000)
        self.assertEqual(config.backtest["base_currency"], "Default")
        self.assertEqual(config.backtest["default_order_size"], {"value": 100.0, "type": "percent_of_equity"})
        self.assertEqual(config.backtest["commission"], {"value": 0.0, "type": "percent"})

    def test_default_hma_config_is_loadable_without_freezing_customizable_values(self) -> None:
        config = load_strategy_config("configs/strategies/hma_crossover.default.json", strategy="hma_crossover")

        self.assertEqual(config.strategy, "hma_crossover")
        self.assertIsInstance(config.parameters.get("fast_len"), int)
        self.assertIsInstance(config.parameters.get("slow_len"), int)
        self.assertIn(config.parameters.get("trade_direction_mode"), {"Long & Short", "Long only", "Short only"})
        self.assertEqual(config.backtest["default_order_size"].get("type"), "percent_of_equity")
        self.assertIn("value", config.backtest["commission"])

    def test_inactive_parameters_follow_direction_and_risk_switches(self) -> None:
        inactive = inactive_parameter_names(
            "hma_crossover",
            {
                "trade_direction_mode": "Long only",
                "use_net_bracket_exits": False,
                "use_safety_stop": False,
            },
        )

        self.assertIn("estimated_commission_per_order_short", inactive)
        self.assertIn("estimated_slippage_per_side_short", inactive)
        self.assertIn("take_profit_net_percent", inactive)
        self.assertIn("safety_stop_mode", inactive)


class HMACrossoverBrokerIntegrationTests(unittest.TestCase):
    def test_strategy_module_loader_caches_converted_module(self) -> None:
        first = hma_crossover_module._load_strategy_module()
        second = hma_crossover_module._load_strategy_module()

        self.assertIs(first, second)
        self.assertIs(sys.modules["converted_hma_crossover"], first)

    def test_hma_runner_uses_common_broker_for_realized_costs(self) -> None:
        index = pd.date_range("2024-01-01 09:30:00", periods=90, freq="5min")
        closes = [100.0 + ((-1) ** (i // 4)) * (i % 8) * 0.9 for i in range(len(index))]
        bars = pd.DataFrame(
            {
                "open": closes,
                "high": [value + 0.5 for value in closes],
                "low": [value - 0.5 for value in closes],
                "close": closes,
                "volume": [1000] * len(index),
            },
            index=index,
        )

        result = run_hma_crossover(
            bars,
            symbol="TEST",
            overrides=HMAConfigOverrides(
                fast_len=3,
                slow_len=5,
                max_entry_price=1000.0,
                max_capital_bucket=300.0,
                initial_capital_bucket=300.0,
                trade_direction_mode="Long & Short",
                quantity_precision=6,
            ),
        )

        if result.trades.empty:
            self.skipTest("Synthetic HMA fixture did not generate a closed trade")
        self.assertIn("estimated_costs", result.trades.columns)
        self.assertTrue((result.trades["estimated_costs"] >= 0).all() if not result.trades.empty else True)
        self.assertIn("peak_equity", result.equity_curve.columns)


class ConvertedStrategyBrokerMigrationTests(unittest.TestCase):
    STRATEGY_DIR = Path(__file__).resolve().parents[1] / "pine_scripts_convert_to_python" / "strategy"

    def _load_converted_module(self, filename: str, module_name: str):
        path = self.STRATEGY_DIR / filename
        spec = importlib.util.spec_from_file_location(module_name, path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader if spec is not None else None)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        assert spec is not None and spec.loader is not None
        spec.loader.exec_module(module)
        return module

    def _bars(self) -> pd.DataFrame:
        index = pd.date_range("2024-01-01 09:30:00", periods=5, freq="5min")
        close = [100.0, 100.0, 110.0, 110.0, 90.0]
        return pd.DataFrame(
            {
                "open": close,
                "high": [value + 1.0 for value in close],
                "low": [value - 1.0 for value in close],
                "close": close,
                "volume": [1000.0] * len(close),
            },
            index=index,
        )

    def _install_spy_broker(self, module):
        instances = []

        class SpyBroker(BrokerSimulator):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                instances.append(self)

        module.BrokerSimulator = SpyBroker
        return instances

    def test_range_filter_uses_common_broker_for_closed_trade_costs(self) -> None:
        module = self._load_converted_module(
            "Range-Filter-Buy-and-Sell-5min-V3-Capped-Bucket-by-PHVNTOM_TRADER.py",
            "converted_range_filter_test",
        )
        instances = self._install_spy_broker(module)

        def fake_features(df, cfg):
            out = df.copy()
            out["allow_long"] = True
            out["allow_short"] = True
            out["long_signal"] = [True, False, False, False, False]
            out["short_signal"] = [False, False, True, False, False]
            return out

        module.add_range_filter_columns = fake_features
        cfg = module.RangeFilterConfig(
            fill_model="close",
            fee_mode="Disabled: always reverse/close on opposite signal",
            max_entry_price=1000.0,
            estimated_commission_per_order_long=1.0,
        )

        _, trades = module.run_range_filter_strategy(self._bars(), cfg)

        self.assertTrue(instances)
        self.assertFalse(trades.empty)
        self.assertIn("commission", trades.columns)
        self.assertAlmostEqual(float(trades.iloc[0]["commission"]), 2.0)
        self.assertAlmostEqual(float(trades.iloc[0]["net_pnl"]), float(trades.iloc[0]["gross_pnl"]) - 2.0)

    def test_avt_uses_common_broker_for_closed_trade_costs(self) -> None:
        module = self._load_converted_module(
            "Adaptive-Volatility-Trend-Strategy-V3-Capped-Bucket-by-WillyAlgoTrader.py",
            "converted_avt_test",
        )
        instances = self._install_spy_broker(module)

        def fake_features(df, config):
            out = df.copy()
            out["avt_long_signal"] = [True, False, False, False, False]
            out["avt_short_signal"] = [False, False, True, False, False]
            return out

        module.add_avt_features = fake_features
        cfg = module.AVTConfig(
            execution="close",
            fee_mode="Disabled: always reverse/close on opposite signal",
            max_entry_price=1000.0,
            estimated_commission_per_order_long=1.0,
        )

        _, trades = module.backtest_avt_strategy(self._bars(), cfg)

        self.assertTrue(instances)
        self.assertFalse(trades.empty)
        self.assertIn("commission", trades.columns)
        self.assertTrue((trades["commission"] >= 0).all())
        self.assertGreater(float(trades["commission"].max()), 0.0)


class OptimizerTests(unittest.TestCase):
    def test_report_interpreter_prefers_robust_plateau_over_isolated_best(self) -> None:
        results = []
        scores = {1: 10.0, 2: 20.0, 3: 30.0, 4: 89.0, 5: 92.0, 6: 90.0, 7: 35.0, 8: 40.0, 9: 45.0, 10: 100.0}
        for value, score in scores.items():
            results.append(
                {
                    "iteration": value,
                    "status": "COMPLETED",
                    "score": score,
                    "parameters": {
                        "fast_len": value,
                        "trade_direction_mode": "Long only" if value in {4, 5, 6, 10} else "Long & Short",
                        "allow_fractional_quantity": value in {4, 5, 6, 10},
                    },
                    "metrics": {"closed_trades": 10 + value, "total_net_pnl": score, "max_drawdown": -value},
                }
            )
        config = {
            "strategy": "hma_crossover",
            "symbol": "TEST",
            "score_metric": "total_net_pnl",
            "score_direction": "max",
            "parameters": [
                {"name": "fast_len", "kind": "numeric", "value_type": "int", "values": list(range(1, 11))},
                {"name": "trade_direction_mode", "kind": "choice", "values": ["Long only", "Long & Short"]},
                {"name": "allow_fractional_quantity", "kind": "bool", "values": [True, False]},
            ],
        }

        report = interpret_optimization_results(results, config, top_quantile=0.6, score_tolerance_pct=0.20)

        self.assertEqual(report["best"]["parameters"]["fast_len"], 10)
        self.assertNotEqual(report["parameters"]["fast_len"]["recommended_value"], 10)
        self.assertIn(report["parameters"]["fast_len"]["recommended_value"], {5, 6})
        self.assertEqual(report["parameters"]["trade_direction_mode"]["recommended_value"], "Long only")
        self.assertIs(report["parameters"]["allow_fractional_quantity"]["recommended_value"], True)
        self.assertIn(report["recommended"]["parameters"]["fast_len"], {5, 6})

    def test_parameter_specs_generate_grid_and_iteration_count(self) -> None:
        specs = [
            parse_cli_parameter("fast_len=3:5:1"),
            parse_cli_parameter("trade_direction_mode=Long only|Long & Short"),
            build_parameter_spec("allow_fractional_quantity", {"kind": "bool", "values": ["true", "false"]}),
        ]

        self.assertEqual(estimate_iterations(specs), 12)
        grid = list(generate_parameter_grid(specs))

        self.assertEqual(grid[0]["fast_len"], 3)
        self.assertEqual(grid[-1]["fast_len"], 5)
        self.assertIs(grid[0]["allow_fractional_quantity"], True)
        self.assertIs(grid[1]["allow_fractional_quantity"], False)

    def test_rejects_invalid_optimizer_range(self) -> None:
        with self.assertRaisesRegex(ValueError, "Step must be > 0"):
            parse_cli_parameter("fast_len=3:5:0")

        with self.assertRaisesRegex(ValueError, "expects integer"):
            parse_cli_parameter("fast_len=3.5:5.5:1")

    def test_build_parameter_spec_uses_schema_defaults_for_empty_numeric_fields(self) -> None:
        spec = build_parameter_spec(
            "safety_max_net_loss_percent",
            {"kind": "numeric", "start": "0", "end": "20", "step": ""},
        )

        self.assertEqual(spec.values[0], 0.0)
        self.assertEqual(spec.values[1], 1.0)
        self.assertEqual(spec.values[-1], 20.0)

    def test_run_grid_optimization_writes_result_files(self) -> None:
        index = pd.date_range("2024-01-01 09:30:00", periods=80, freq="5min")
        closes = [100.0 + ((-1) ** (i // 5)) * (i % 10) * 0.8 for i in range(len(index))]
        bars = pd.DataFrame(
            {
                "open": closes,
                "high": [value + 0.5 for value in closes],
                "low": [value - 0.5 for value in closes],
                "close": closes,
                "volume": [1000] * len(index),
            },
            index=index,
        )
        with tempfile.TemporaryDirectory() as tmp:
            summary = run_grid_optimization(
                data=bars,
                symbol="TEST",
                parameter_specs=[parse_cli_parameter("fast_len=3:4:1")],
                fixed_overrides=HMAConfigOverrides(
                    slow_len=5,
                    max_entry_price=1000.0,
                    max_capital_bucket=300.0,
                    initial_capital_bucket=300.0,
                    trade_direction_mode="Long & Short",
                ),
                output_root=Path(tmp),
                max_iterations=10,
                min_closed_trades=0,
                write_best_run=False,
            )

            self.assertEqual(summary.total_iterations, 2)
            self.assertEqual(summary.iterations_completed, 2)
            self.assertEqual(summary.status, "FINISHED")
            self.assertTrue((summary.output_dir / "results.parquet").exists())
            self.assertTrue((summary.output_dir / "results.json").exists())
            self.assertTrue((summary.output_dir / "best.json").exists())
            self.assertTrue((summary.output_dir / "recommendations.json").exists())
            self.assertTrue((summary.output_dir / "optimizer_report.parquet").exists())
            self.assertTrue((summary.output_dir / "optimizer_report.html").exists())
            self.assertIsNotNone(summary.optimizer_report_paths)
            report_frame = pd.read_parquet(summary.output_dir / "optimizer_report.parquet")
            self.assertIn("PARAMETERS", report_frame.columns)
            self.assertIn("NETPROFITAMOUNT", report_frame.columns)
            self.assertIn("FAST HMA LENGTH", report_frame.columns)
            html = (summary.output_dir / "optimizer_report.html").read_text(encoding="utf-8")
            self.assertIn("Optimizer report", html)
            self.assertIn("report-table", html)
            self.assertIn("id=\"page-size\"", html)
            self.assertIn("Showing 0 to 0 of 0 rows", html)
            self.assertIn("rows per page", html)
            self.assertNotIn("top:52px", html)
            self.assertIsNotNone(summary.best_row)
            self.assertIsNotNone(summary.recommendations)
            self.assertIn("recommended", summary.recommendations)

    def test_hma_grid_validation_skips_equal_or_inverted_lengths(self) -> None:
        specs = [parse_cli_parameter("fast_len=19:21:1")]
        validation = validate_parameter_grid(
            specs,
            fixed_overrides=HMAConfigOverrides(slow_len=20),
        )

        self.assertEqual(validation["total_iterations"], 3)
        self.assertEqual(validation["canonical_iterations"], 3)
        self.assertEqual(validation["valid_iterations"], 1)
        self.assertEqual(validation["skipped_iterations"], 2)

    def test_hma_grid_validation_deduplicates_inactive_short_costs_when_long_only(self) -> None:
        specs = [
            parse_cli_parameter("estimated_commission_per_order_short=0:2:1"),
            parse_cli_parameter("estimated_slippage_per_side_short=0:2:1"),
        ]
        validation = validate_parameter_grid(
            specs,
            fixed_overrides=HMAConfigOverrides(fast_len=3, slow_len=5, trade_direction_mode="Long only"),
        )

        self.assertEqual(validation["total_iterations"], 9)
        self.assertEqual(validation["canonical_iterations"], 1)
        self.assertEqual(validation["deduplicated_inactive_iterations"], 8)
        self.assertEqual(validation["valid_iterations"], 1)

    def test_no_trade_combinations_are_not_eligible_for_best_by_default(self) -> None:
        index = pd.date_range("2024-01-01 09:30:00", periods=40, freq="5min")
        bars = pd.DataFrame(
            {
                "open": [100.0] * len(index),
                "high": [100.0] * len(index),
                "low": [100.0] * len(index),
                "close": [100.0] * len(index),
                "volume": [1000] * len(index),
            },
            index=index,
        )
        with tempfile.TemporaryDirectory() as tmp:
            summary = run_grid_optimization(
                data=bars,
                symbol="TEST",
                parameter_specs=[parse_cli_parameter("fast_len=3:3:1")],
                fixed_overrides=HMAConfigOverrides(slow_len=5, max_entry_price=1000.0),
                output_root=Path(tmp),
                max_iterations=10,
                write_best_run=False,
            )

            self.assertEqual(summary.eligible_iterations, 0)
            self.assertEqual(summary.skipped_iterations, 1)
            self.assertIsNone(summary.best_row)
            self.assertEqual(summary.results[0]["status"], "SKIPPED_MIN_TRADES")
            self.assertTrue((summary.output_dir / "best.json").exists())

    def test_score_metric_must_be_known(self) -> None:
        self.assertIn("total_net_pnl", allowed_score_metrics())
        self.assertEqual(validate_score_metric("total_net_pnl"), "total_net_pnl")
        with self.assertRaisesRegex(ValueError, "Unsupported score_metric"):
            validate_score_metric("does_not_exist")

    def test_parallel_grid_optimization_completes_all_iterations(self) -> None:
        index = pd.date_range("2024-01-01 09:30:00", periods=60, freq="5min")
        closes = [100.0 + ((-1) ** (i // 4)) * (i % 8) * 0.9 for i in range(len(index))]
        bars = pd.DataFrame(
            {
                "open": closes,
                "high": [value + 0.5 for value in closes],
                "low": [value - 0.5 for value in closes],
                "close": closes,
                "volume": [1000] * len(index),
            },
            index=index,
        )
        with tempfile.TemporaryDirectory() as tmp:
            summary = run_grid_optimization(
                data=bars,
                symbol="TEST",
                parameter_specs=[parse_cli_parameter("fast_len=3:4:1")],
                fixed_overrides=HMAConfigOverrides(slow_len=5, max_entry_price=1000.0),
                output_root=Path(tmp),
                max_iterations=10,
                min_closed_trades=0,
                workers=2,
                write_best_run=False,
            )

            self.assertEqual(summary.total_iterations, 2)
            self.assertEqual(summary.iterations_completed, 2)
            self.assertEqual([row["iteration"] for row in summary.results], [1, 2])

    def test_output_directories_include_uuid_suffix_to_avoid_collisions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = create_optimization_output_dir(Path(tmp), "hma_crossover", "TEST")
            second = create_optimization_output_dir(Path(tmp), "hma_crossover", "TEST")

            self.assertNotEqual(first, second)
            self.assertTrue(first.exists())
            self.assertTrue(second.exists())
            self.assertRegex(first.name, r"^\d{8}T\d{6}Z-[0-9a-f]{8}$")

    def test_output_directories_include_job_id_suffix_when_provided(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            job_id = "my-custom-job-id-12345"
            output_dir = create_optimization_output_dir(Path(tmp), "hma_crossover", "TEST", job_id=job_id)
            self.assertTrue(output_dir.exists())
            self.assertIn(job_id, output_dir.name)
            self.assertTrue(output_dir.name.endswith(f"-{job_id}"))

    def test_iteration_limits_report_raw_and_canonical_separately(self) -> None:
        with self.assertRaisesRegex(ValueError, "raw iterations"):
            validate_iteration_limits(raw_iterations=9, canonical_iterations=1, max_raw_iterations=8, max_canonical_iterations=10)

        with self.assertRaisesRegex(ValueError, "canonical iterations"):
            validate_iteration_limits(raw_iterations=9, canonical_iterations=6, max_raw_iterations=10, max_canonical_iterations=5)

    def test_cli_optimize_applies_specific_raw_and_canonical_limits(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "optimize",
                "--symbol",
                "TEST",
                "--param",
                "estimated_commission_per_order_short=0:2:1",
                "--param",
                "estimated_slippage_per_side_short=0:2:1",
                "--trade-direction-mode",
                "Long only",
                "--max-iterations",
                "1",
                "--max-raw-iterations",
                "9",
                "--max-canonical-iterations",
                "1",
                "--dry-run",
            ]
        )

        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = cmd_optimize(args)
        payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["total_iterations"], 9)
        self.assertEqual(payload["canonical_iterations"], 1)
        self.assertEqual(payload["max_raw_iterations"], 9)
        self.assertEqual(payload["max_canonical_iterations"], 1)

    def test_cli_worker_accepts_repo_root_after_subcommand(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["worker", "--repo-root", ".", "--output-dir", "reports/local_optimizer", "--once"])

        self.assertEqual(args.command, "worker")
        self.assertEqual(args.repo_root, ".")
        self.assertEqual(args.output_dir, "reports/local_optimizer")
        self.assertTrue(args.once)

    def test_cli_interpret_optimization_writes_recommendations_for_existing_job_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            job_dir = Path(tmp)
            (job_dir / "optimization_config.json").write_text(
                json.dumps(
                    {
                        "strategy": "hma_crossover",
                        "symbol": "TEST",
                        "score_metric": "total_net_pnl",
                        "score_direction": "max",
                        "parameters": [{"name": "fast_len", "kind": "numeric", "value_type": "int", "values": [3, 4, 5]}],
                    }
                ),
                encoding="utf-8",
            )
            (job_dir / "results.json").write_text(
                json.dumps(
                    [
                        {"iteration": 1, "status": "COMPLETED", "score": 1.0, "parameters": {"fast_len": 3}, "metrics": {}},
                        {"iteration": 2, "status": "COMPLETED", "score": 2.0, "parameters": {"fast_len": 4}, "metrics": {}},
                        {"iteration": 3, "status": "COMPLETED", "score": 1.5, "parameters": {"fast_len": 5}, "metrics": {}},
                    ]
                ),
                encoding="utf-8",
            )
            parser = build_parser()
            args = parser.parse_args(["interpret-optimization", "--job-dir", str(job_dir)])

            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = cmd_interpret_optimization(args)

            self.assertEqual(exit_code, 0)
            self.assertTrue((job_dir / "recommendations.json").exists())
            self.assertEqual(json.loads(output.getvalue())["recommended"]["parameters"]["fast_len"], 4)

    def test_report_interpreter_absolute_min_candidates_floor(self) -> None:
        results = []
        # We create a setup where there is 1 outstanding outlier best, and many other lower scores
        # len(completed) = 100
        # Best score = 100.0 (iterations 1-10). All others have score 1.0.
        # min_candidates = max(50, 100 * 0.05) = 50.
        # With default quantile 0.95:
        # 10% of values are 100.0, so the 95% quantile is 100.0.
        # score_span = 99.0. Best score = 100.0. Tolerance cutoff = 100.0 - 100.0 * 0.10 = 90.0.
        # Standard cutoff = min(100.0, 90.0) = 90.0.
        # Standard selection only yields 10 candidates (iterations 1 to 10 with score 100.0).
        # Since 10 < 50, the absolute floor should trigger and select the top 50 rows.
        for i in range(1, 101):
            results.append(
                {
                    "iteration": i,
                    "status": "COMPLETED",
                    "score": 100.0 if i <= 10 else 1.0,
                    "parameters": {"fast_len": i},
                    "metrics": {}
                }
            )
        config = {
            "strategy": "hma_crossover",
            "symbol": "TEST",
            "score_metric": "total_net_pnl",
            "score_direction": "max",
            "parameters": [
                {"name": "fast_len", "kind": "numeric", "value_type": "int", "values": list(range(1, 101))}
            ],
        }
        report = interpret_optimization_results(results, config)
        self.assertEqual(report["candidate_pool"]["selected_rows"], 50)
        self.assertEqual(report["candidate_pool"]["selection_rule"], "minimum candidates absolute floor triggered")

    def test_write_recommendations_fallback_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            job_dir = Path(tmp)
            (job_dir / "optimization_config.json").write_text(
                json.dumps(
                    {
                        "strategy": "hma_crossover",
                        "symbol": "TEST",
                        "score_metric": "total_net_pnl",
                        "score_direction": "max",
                        "top_quantile": 0.6,
                        "score_tolerance_pct": 0.2,
                        "parameters": [{"name": "fast_len", "kind": "numeric", "value_type": "int", "values": [3, 4, 5]}],
                    }
                ),
                encoding="utf-8",
            )
            (job_dir / "results.json").write_text(
                json.dumps(
                    [
                        {"iteration": 1, "status": "COMPLETED", "score": 1.0, "parameters": {"fast_len": 3}, "metrics": {}},
                        {"iteration": 2, "status": "COMPLETED", "score": 2.0, "parameters": {"fast_len": 4}, "metrics": {}},
                        {"iteration": 3, "status": "COMPLETED", "score": 1.5, "parameters": {"fast_len": 5}, "metrics": {}},
                    ]
                ),
                encoding="utf-8",
            )
            
            # 1. Test CLI with no arguments - should fallback to custom config values 0.6 and 0.2
            parser = build_parser()
            args = parser.parse_args(["interpret-optimization", "--job-dir", str(job_dir)])
            self.assertIsNone(args.top_quantile)
            self.assertIsNone(args.score_tolerance_pct)
            
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = cmd_interpret_optimization(args)
            self.assertEqual(exit_code, 0)
            
            report = json.loads((job_dir / "recommendations.json").read_text(encoding="utf-8"))
            self.assertEqual(report["selection_settings"]["top_quantile"], 0.6)
            self.assertEqual(report["selection_settings"]["score_tolerance_pct"], 0.2)
            
            # 2. Test CLI with explicit arguments - should override config
            args_override = parser.parse_args(["interpret-optimization", "--job-dir", str(job_dir), "--top-quantile", "0.8", "--score-tolerance-pct", "0.05"])
            self.assertEqual(args_override.top_quantile, 0.8)
            self.assertEqual(args_override.score_tolerance_pct, 0.05)
            
            output_override = io.StringIO()
            with redirect_stdout(output_override):
                exit_code_override = cmd_interpret_optimization(args_override)
            self.assertEqual(exit_code_override, 0)
            
            report_override = json.loads((job_dir / "recommendations.json").read_text(encoding="utf-8"))
            self.assertEqual(report_override["selection_settings"]["top_quantile"], 0.8)
            self.assertEqual(report_override["selection_settings"]["score_tolerance_pct"], 0.05)


class BackendSecurityTests(unittest.TestCase):
    def test_fastapi_strategies_endpoint_exposes_optimizer_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app = create_optimizer_app(
                repo_root=Path(tmp),
                store=OptimizerJobStore(ttl_seconds=None, storage_path=Path(tmp) / "jobs.sqlite3"),
            )
            client = TestClient(app)

            response = client.get("/api/strategies")

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["strategies"][0]["name"], "hma_crossover")
            self.assertTrue(payload["strategies"][0]["parameters"])
            self.assertIn("total_net_pnl", payload["strategies"][0]["score_metrics"])

    def test_fastapi_estimate_returns_legacy_error_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app = create_optimizer_app(
                repo_root=Path(tmp),
                store=OptimizerJobStore(ttl_seconds=None, storage_path=Path(tmp) / "jobs.sqlite3"),
            )
            client = TestClient(app)

            response = client.post("/api/estimate", json={"parameters": []})

            self.assertEqual(response.status_code, 400)
            self.assertIn("error", response.json())
            self.assertIn("At least one optimization parameter", response.json()["error"])

    def test_fastapi_symbols_endpoint_confines_processed_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            app = create_optimizer_app(
                repo_root=repo_root,
                store=OptimizerJobStore(ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3"),
            )
            client = TestClient(app)

            response = client.get("/api/symbols", params={"processed_dir": "../outside"})

            self.assertEqual(response.status_code, 400)
            self.assertIn("repo_root", response.json()["error"])

    def test_fastapi_estimate_confines_processed_and_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            app = create_optimizer_app(
                repo_root=repo_root,
                store=OptimizerJobStore(ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3"),
            )
            client = TestClient(app)
            payload = {
                "processed_dir": "../outside",
                "output_dir": "/tmp/outside",
                "parameters": [{"name": "fast_len", "kind": "numeric", "start": 5, "end": 5, "step": 1}],
            }

            response = client.post("/api/estimate", json=payload)

            self.assertEqual(response.status_code, 400)
            self.assertIn("repo_root", response.json()["error"])

    def test_fastapi_request_payload_rejects_invalid_numeric_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            app = create_optimizer_app(
                repo_root=repo_root,
                store=OptimizerJobStore(ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3"),
            )
            client = TestClient(app)
            payload = {
                "initial_capital": 0,
                "workers": 0,
                "parameters": [{"name": "fast_len", "kind": "numeric", "start": 5, "end": 5, "step": 1}],
            }

            response = client.post("/api/estimate", json=payload)

            self.assertEqual(response.status_code, 400)
            self.assertIn("error", response.json())

    def test_fastapi_missing_job_returns_legacy_404_error_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            app = create_optimizer_app(
                repo_root=Path(tmp),
                store=OptimizerJobStore(ttl_seconds=None, storage_path=Path(tmp) / "jobs.sqlite3"),
            )
            client = TestClient(app)

            response = client.get("/api/jobs/missing")

            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json(), {"error": "job not found"})

    def test_fastapi_best_equity_endpoint_serves_best_run_curve(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            best_dir = repo_root / "reports" / "best_backtest"
            best_dir.mkdir(parents=True)
            pd.DataFrame(
                {
                    "timestamp": ["2024-01-01 09:30:00", "2024-01-01 09:35:00"],
                    "equity": [1000.0, 1012.5],
                    "drawdown": [0.0, -1.0],
                }
            ).to_parquet(best_dir / "equity_curve.parquet", index=False, engine="pyarrow", compression="zstd")
            store = OptimizerJobStore(ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3")
            store.add(
                OptimizerJob(
                    id="done",
                    created_at=1.0,
                    request={},
                    status="FINISHED",
                    best={"best_backtest_dir": str(best_dir)},
                )
            )
            app = create_optimizer_app(repo_root=repo_root, store=store)
            client = TestClient(app)

            response = client.get("/api/jobs/done/best-equity")

            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertEqual(payload["job_id"], "done")
            self.assertEqual(len(payload["points"]), 2)
            self.assertEqual(payload["points"][1]["equity"], 1012.5)
            self.assertEqual(payload["points"][0]["time"], "2024-01-01 09:30:00")

    def test_fastapi_recommendations_endpoint_serves_interpreter_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            output_dir = repo_root / "reports" / "optimizer-job"
            output_dir.mkdir(parents=True)
            recommendations = {"recommended": {"parameters": {"fast_len": 4}}, "parameters": {"fast_len": {"recommended_value": 4}}}
            (output_dir / "recommendations.json").write_text(json.dumps(recommendations), encoding="utf-8")
            store = OptimizerJobStore(ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3")
            store.add(OptimizerJob(id="done", created_at=1.0, request={}, status="FINISHED", output_dir=str(output_dir)))
            app = create_optimizer_app(repo_root=repo_root, store=store)
            client = TestClient(app)

            response = client.get("/api/jobs/done/recommendations")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["recommended"]["parameters"]["fast_len"], 4)

            file_response = client.get("/api/jobs/done/recommendations.json")
            self.assertEqual(file_response.status_code, 200)
            self.assertEqual(file_response.json()["parameters"]["fast_len"]["recommended_value"], 4)

    def test_fastapi_optimizer_report_endpoints_serve_parquet_and_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            output_dir = repo_root / "reports" / "optimizer-job"
            output_dir.mkdir(parents=True)
            pd.DataFrame({"PARAMETERS": [3], "NETPROFITAMOUNT": ["+1.00"]}).to_parquet(output_dir / "optimizer_report.parquet", engine="pyarrow", compression="zstd")
            (output_dir / "optimizer_report.html").write_text("<!doctype html><title>Optimizer report</title>", encoding="utf-8")
            store = OptimizerJobStore(ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3")
            store.add(OptimizerJob(id="done", created_at=1.0, request={}, status="FINISHED", output_dir=str(output_dir)))
            app = create_optimizer_app(repo_root=repo_root, store=store)
            client = TestClient(app)

            parquet_response = client.get("/api/jobs/done/optimizer_report.parquet")
            html_response = client.get("/api/jobs/done/optimizer_report.html")

            self.assertEqual(parquet_response.status_code, 200)
            self.assertEqual(parquet_response.headers["content-type"], "application/octet-stream")
            import io
            report_frame = pd.read_parquet(io.BytesIO(parquet_response.content))
            self.assertIn("PARAMETERS", report_frame.columns)
            self.assertEqual(html_response.status_code, 200)
            self.assertIn("Optimizer report", html_response.text)

    def test_fastapi_best_equity_endpoint_reports_not_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = OptimizerJobStore(ttl_seconds=None, storage_path=Path(tmp) / "jobs.sqlite3")
            store.add(OptimizerJob(id="running", created_at=1.0, request={}, status="IN_PROGRESS", best={"score": 1.0}))
            app = create_optimizer_app(repo_root=Path(tmp), store=store)
            client = TestClient(app)

            response = client.get("/api/jobs/running/best-equity")

            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json(), {"error": "best run not ready"})

    def test_fastapi_delete_job_removes_store_row_and_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            output_dir = repo_root / "reports" / "local_optimizer" / "done"
            output_dir.mkdir(parents=True)
            (output_dir / "results.parquet").write_bytes(b"dummy")
            store = OptimizerJobStore(ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3")
            store.add(OptimizerJob(id="done", created_at=1.0, request={}, status="FINISHED", output_dir=str(output_dir)))
            app = create_optimizer_app(repo_root=repo_root, store=store)
            client = TestClient(app)

            response = client.delete("/api/jobs/done")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["deleted"], True)
            self.assertEqual(response.json()["output_dir_deleted"], True)
            self.assertIsNone(store.get("done"))
            self.assertFalse(output_dir.exists())

    def test_fastapi_delete_job_refuses_active_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            store = OptimizerJobStore(ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3")
            store.add(OptimizerJob(id="running", created_at=1.0, request={}, status="IN_PROGRESS"))
            app = create_optimizer_app(repo_root=repo_root, store=store)
            client = TestClient(app)

            response = client.delete("/api/jobs/running")

            self.assertEqual(response.status_code, 409)
            self.assertIn("active jobs", response.json()["error"])
            self.assertIsNotNone(store.get("running"))

    def test_fastapi_delete_job_accepts_cancelled_in_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            store = OptimizerJobStore(ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3")
            store.add(OptimizerJob(id="cancelled_in_progress", created_at=1.0, request={}, status="IN_PROGRESS", cancel_requested=True))
            app = create_optimizer_app(repo_root=repo_root, store=store)
            client = TestClient(app)

            response = client.delete("/api/jobs/cancelled_in_progress")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["deleted"], True)
            self.assertIsNone(store.get("cancelled_in_progress"))

    def test_fastapi_delete_job_confines_output_dir_to_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            store = OptimizerJobStore(ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3")
            store.add(OptimizerJob(id="bad", created_at=1.0, request={}, status="FINISHED", output_dir="../outside"))
            app = create_optimizer_app(repo_root=repo_root, store=store)
            client = TestClient(app)

            response = client.delete("/api/jobs/bad")

            self.assertEqual(response.status_code, 400)
            self.assertIn("repo_root", response.json()["error"])
            self.assertIsNotNone(store.get("bad"))

    def test_fastapi_delete_job_refuses_when_job_id_is_missing_from_output_dir_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            output_dir = repo_root / "reports" / "local_optimizer" / "timestamp-randomhex"
            output_dir.mkdir(parents=True)
            store = OptimizerJobStore(ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3")
            store.add(OptimizerJob(id="job12345", created_at=1.0, request={}, status="FINISHED", output_dir=str(output_dir)))
            app = create_optimizer_app(repo_root=repo_root, store=store)
            client = TestClient(app)

            response = client.delete("/api/jobs/job12345")

            self.assertEqual(response.status_code, 400)
            self.assertIn("must contain the job ID", response.json()["error"])
            self.assertIsNotNone(store.get("job12345"))

    def test_fastapi_delete_job_succeeds_when_job_id_is_present_in_output_dir_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            output_dir = repo_root / "reports" / "local_optimizer" / "20260522T231608Z-job12345"
            output_dir.mkdir(parents=True)
            (output_dir / "results.parquet").write_bytes(b"dummy")
            store = OptimizerJobStore(ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3")
            store.add(OptimizerJob(id="job12345", created_at=1.0, request={}, status="FINISHED", output_dir=str(output_dir)))
            app = create_optimizer_app(repo_root=repo_root, store=store)
            client = TestClient(app)

            response = client.delete("/api/jobs/job12345")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["deleted"], True)
            self.assertEqual(response.json()["output_dir_deleted"], True)
            self.assertIsNone(store.get("job12345"))
            self.assertFalse(output_dir.exists())

    def test_fastapi_delete_job_succeeds_with_legacy_dir_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            output_dir = repo_root / "reports" / "local_optimizer" / "20260522T211608Z-a1b2c3d4"
            output_dir.mkdir(parents=True)
            (output_dir / "results.parquet").write_bytes(b"dummy")
            store = OptimizerJobStore(ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3")
            store.add(OptimizerJob(id="da212d065e894028b36921e9a2d36a61", created_at=1.0, request={}, status="FINISHED", output_dir=str(output_dir)))
            app = create_optimizer_app(repo_root=repo_root, store=store)
            client = TestClient(app)

            response = client.delete("/api/jobs/da212d065e894028b36921e9a2d36a61")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["deleted"], True)
            self.assertEqual(response.json()["output_dir_deleted"], True)
            self.assertIsNone(store.get("da212d065e894028b36921e9a2d36a61"))
            self.assertFalse(output_dir.exists())

    def test_fastapi_bulk_delete_jobs_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            
            # Setup job 1: finished with valid output directory
            output_dir_1 = repo_root / "reports" / "local_optimizer" / "20260522T231608Z-job1"
            output_dir_1.mkdir(parents=True)
            (output_dir_1 / "results.parquet").write_bytes(b"dummy1")
            
            # Setup job 2: failed with valid output directory
            output_dir_2 = repo_root / "reports" / "local_optimizer" / "20260522T231608Z-job2"
            output_dir_2.mkdir(parents=True)
            (output_dir_2 / "results.parquet").write_bytes(b"dummy2")
            
            # Setup job 3: no output directory, status cancelled
            
            store = OptimizerJobStore(ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3")
            store.add(OptimizerJob(id="job1", created_at=1.0, request={}, status="FINISHED", output_dir=str(output_dir_1)))
            store.add(OptimizerJob(id="job2", created_at=2.0, request={}, status="FAILED", output_dir=str(output_dir_2)))
            store.add(OptimizerJob(id="job3", created_at=3.0, request={}, status="CANCELLED", output_dir=None))
            
            app = create_optimizer_app(repo_root=repo_root, store=store)
            client = TestClient(app)

            response = client.post("/api/jobs/bulk-delete", json={"job_ids": ["job1", "job2", "job3", "missing_job"]})

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["deleted"], 3)
            self.assertEqual(data["skipped_active"], 0)
            self.assertEqual(data["errors"], [])
            
            # Verify jobs are removed from store
            self.assertIsNone(store.get("job1"))
            self.assertIsNone(store.get("job2"))
            self.assertIsNone(store.get("job3"))
            
            # Verify output directories are deleted
            self.assertFalse(output_dir_1.exists())
            self.assertFalse(output_dir_2.exists())

    def test_fastapi_bulk_delete_jobs_skips_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            
            # Setup job 1: finished
            output_dir_1 = repo_root / "reports" / "local_optimizer" / "20260522T231608Z-job1"
            output_dir_1.mkdir(parents=True)
            (output_dir_1 / "results.parquet").write_bytes(b"dummy1")
            
            # Setup job 2: pending (active)
            # Setup job 3: running (active)
            
            store = OptimizerJobStore(ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3")
            store.add(OptimizerJob(id="job1", created_at=1.0, request={}, status="FINISHED", output_dir=str(output_dir_1)))
            store.add(OptimizerJob(id="job2", created_at=2.0, request={}, status="PENDING"))
            store.add(OptimizerJob(id="job3", created_at=3.0, request={}, status="IN_PROGRESS"))
            
            app = create_optimizer_app(repo_root=repo_root, store=store)
            client = TestClient(app)

            response = client.post("/api/jobs/bulk-delete", json={"job_ids": ["job1", "job2", "job3"]})

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["deleted"], 1)
            self.assertEqual(data["skipped_active"], 2)
            self.assertEqual(data["errors"], [])
            
            # Verify finished job is deleted
            self.assertIsNone(store.get("job1"))
            self.assertFalse(output_dir_1.exists())
            
            # Verify active jobs are NOT deleted
            self.assertIsNotNone(store.get("job2"))
            self.assertIsNotNone(store.get("job3"))

    def test_fastapi_bulk_delete_jobs_deletes_cancelled_in_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            
            # Setup job 1: running (active), cancel_requested is True
            # Setup job 2: pending (active), cancel_requested is False (should be skipped)
            
            store = OptimizerJobStore(ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3")
            store.add(OptimizerJob(id="job1", created_at=1.0, request={}, status="IN_PROGRESS", cancel_requested=True))
            store.add(OptimizerJob(id="job2", created_at=2.0, request={}, status="PENDING", cancel_requested=False))
            
            app = create_optimizer_app(repo_root=repo_root, store=store)
            client = TestClient(app)

            response = client.post("/api/jobs/bulk-delete", json={"job_ids": ["job1", "job2"]})

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["deleted"], 1)
            self.assertEqual(data["skipped_active"], 1)
            self.assertEqual(data["errors"], [])
            
            # Verify job1 is deleted
            self.assertIsNone(store.get("job1"))
            
            # Verify job2 is NOT deleted
            self.assertIsNotNone(store.get("job2"))

    def test_fastapi_bulk_delete_jobs_reports_security_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            
            # Setup job 1: path outside repo_root
            # Setup job 2: path too shallow (<3 parts under reports parent)
            output_dir_2 = repo_root / "reports"
            # Setup job 3: missing job ID in output dir name
            output_dir_3 = repo_root / "reports" / "local_optimizer" / "timestamp-randomhex"
            output_dir_3.mkdir(parents=True)
            
            store = OptimizerJobStore(ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3")
            store.add(OptimizerJob(id="job1", created_at=1.0, request={}, status="FINISHED", output_dir="../outside"))
            store.add(OptimizerJob(id="job2", created_at=2.0, request={}, status="FINISHED", output_dir=str(output_dir_2)))
            store.add(OptimizerJob(id="job3", created_at=3.0, request={}, status="FINISHED", output_dir=str(output_dir_3)))
            
            app = create_optimizer_app(repo_root=repo_root, store=store)
            client = TestClient(app)

            response = client.post("/api/jobs/bulk-delete", json={"job_ids": ["job1", "job2", "job3"]})

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["deleted"], 0)
            self.assertEqual(data["skipped_active"], 0)
            self.assertEqual(len(data["errors"]), 3)
            
            # Verify error messages
            self.assertTrue(any("repo_root" in err or "inside the reports directory" in err for err in data["errors"]))
            self.assertTrue(any("3 levels deep" in err for err in data["errors"]))
            self.assertTrue(any("must contain the job ID" in err for err in data["errors"]))
            
            # Verify jobs are NOT deleted from store
            self.assertIsNotNone(store.get("job1"))
            self.assertIsNotNone(store.get("job2"))
            self.assertIsNotNone(store.get("job3"))

    def test_resolve_repo_path_confines_user_paths_to_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()

            self.assertEqual(resolve_repo_path(repo_root, "storage/processed", "processed_dir"), repo_root / "storage" / "processed")
            self.assertEqual(resolve_repo_path(repo_root, repo_root / "reports", "output_dir"), repo_root / "reports")

            with self.assertRaisesRegex(ValueError, "repo_root"):
                resolve_repo_path(repo_root, "../outside", "processed_dir")
            with self.assertRaisesRegex(ValueError, "repo_root"):
                resolve_repo_path(repo_root, "/tmp/outside", "output_dir")

    def test_fastapi_optimize_enqueues_pending_job_without_inline_thread(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            store = OptimizerJobStore(ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3")
            app = create_optimizer_app(repo_root=repo_root, store=store)
            client = TestClient(app)

            response = client.post(
                "/api/optimize",
                json={
                    "symbol": "TEST",
                    "timeframe_minutes": 15,
                    "parameters": [{"name": "fast_len", "kind": "numeric", "start": 5, "end": 5, "step": 1}],
                },
            )

            self.assertEqual(response.status_code, 202)
            payload = response.json()
            self.assertEqual(payload["status"], "PENDING")
            self.assertEqual(payload["request"]["timeframe_minutes"], 15)
            self.assertEqual(payload["request"]["parameters"][0]["name"], "fast_len")
            queued = store.get(payload["id"])
            self.assertIsNotNone(queued)
            self.assertEqual(queued.status, "PENDING")

            jobs_response = client.get("/api/jobs")
            self.assertEqual(jobs_response.status_code, 200)
            self.assertEqual(jobs_response.json()["jobs"][0]["request"]["timeframe_minutes"], 15)

    def test_optimizer_job_store_persists_limits_and_marks_restarted_jobs_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            storage_path = Path(tmp) / "jobs.sqlite3"
            store = OptimizerJobStore(max_jobs=2, ttl_seconds=None, storage_path=storage_path)
            store.add(OptimizerJob(id="old", created_at=1.0, request={}, status="FINISHED"))
            store.add(OptimizerJob(id="running", created_at=2.0, request={"symbol": "TEST"}, status="IN_PROGRESS"))
            store.add(OptimizerJob(id="new", created_at=3.0, request={}, status="FINISHED"))

            self.assertIsNone(store.get("old"))
            self.assertIsNotNone(store.get("running"))
            self.assertIsNotNone(store.get("new"))
            self.assertTrue(storage_path.exists())

            reloaded = OptimizerJobStore(max_jobs=10, ttl_seconds=None, storage_path=storage_path)
            reloaded.mark_interrupted_jobs_failed()  # Explicitly trigger cleanup of active jobs on reload
            restarted = reloaded.get("running")

            self.assertIsNotNone(restarted)
            self.assertEqual(restarted.status, "FAILED")
            self.assertIn("restart", restarted.error)

    def test_optimizer_job_store_marks_worker_crashed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            storage_path = Path(tmp) / "jobs.sqlite3"
            store = OptimizerJobStore(max_jobs=10, ttl_seconds=None, storage_path=storage_path)
            
            # Add two jobs in progress for different workers
            store.add(OptimizerJob(id="job-worker-1", created_at=1.0, request={}, status="PENDING"))
            store.claim_next(worker_id="worker-1")
            
            store.add(OptimizerJob(id="job-worker-2", created_at=2.0, request={}, status="PENDING"))
            store.claim_next(worker_id="worker-2")
            
            self.assertEqual(store.get("job-worker-1").status, "IN_PROGRESS")
            self.assertEqual(store.get("job-worker-2").status, "IN_PROGRESS")
            
            # Mark worker-1 as crashed
            count = store.mark_worker_crashed(worker_id="worker-1", error_message="Worker worker-1 died!")
            self.assertEqual(count, 1)
            
            self.assertEqual(store.get("job-worker-1").status, "FAILED")
            self.assertEqual(store.get("job-worker-1").error, "Worker worker-1 died!")
            
            # Worker 2 should still be in progress (safe multi-worker isolation!)
            self.assertEqual(store.get("job-worker-2").status, "IN_PROGRESS")

    def test_optimizer_job_store_limit_never_removes_active_jobs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            storage_path = Path(tmp) / "jobs.sqlite3"
            store = OptimizerJobStore(max_jobs=2, ttl_seconds=None, storage_path=storage_path)
            store.add(OptimizerJob(id="done-1", created_at=1.0, request={}, status="FINISHED"))
            store.add(OptimizerJob(id="pending", created_at=2.0, request={}, status="PENDING"))
            store.add(OptimizerJob(id="running", created_at=3.0, request={}, status="IN_PROGRESS"))
            store.add(OptimizerJob(id="done-2", created_at=4.0, request={}, status="FINISHED"))
            store.add(OptimizerJob(id="started", created_at=5.0, request={}, status="STARTED"))

            self.assertIsNone(store.get("done-1"))
            self.assertIsNone(store.get("done-2"))
            self.assertIsNotNone(store.get("pending"))
            self.assertIsNotNone(store.get("running"))
            self.assertIsNone(store.get("started"))
            self.assertEqual(len(store.list()), 2)

    def test_optimizer_job_store_serializes_concurrent_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            storage_path = Path(tmp) / "jobs.sqlite3"
            store = OptimizerJobStore(max_jobs=50, ttl_seconds=None, storage_path=storage_path)
            errors: list[Exception] = []

            def worker(index: int) -> None:
                try:
                    job_id = f"job-{index}"
                    store.add(OptimizerJob(id=job_id, created_at=float(index), request={"worker": index}))
                    for step in range(5):
                        store.update(job_id, status="IN_PROGRESS", progress={"step": step})
                    store.update(job_id, status="FINISHED", summary={"worker": index})
                except Exception as exc:  # noqa: BLE001 - collected for assertion after join
                    errors.append(exc)

            threads = [Thread(target=worker, args=(index,)) for index in range(12)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            self.assertEqual(errors, [])

            reloaded = OptimizerJobStore(max_jobs=50, ttl_seconds=None, storage_path=storage_path)
            self.assertEqual(len(reloaded.list()), 12)
            for index in range(12):
                job = reloaded.get(f"job-{index}")
                self.assertIsNotNone(job)
                self.assertEqual(job.status, "FINISHED")
                self.assertEqual(job.summary, {"worker": index})

    def test_optimizer_job_store_claims_oldest_pending_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            storage_path = Path(tmp) / "jobs.sqlite3"
            store = OptimizerJobStore(max_jobs=10, ttl_seconds=None, storage_path=storage_path)
            store.add(OptimizerJob(id="new", created_at=2.0, request={}, status="PENDING"))
            store.add(OptimizerJob(id="old", created_at=1.0, request={}, status="PENDING"))

            claimed = store.claim_next(worker_id="test-worker")

            self.assertIsNotNone(claimed)
            self.assertEqual(claimed.id, "old")
            self.assertEqual(store.get("old").status, "IN_PROGRESS")
            self.assertEqual(store.get("new").status, "PENDING")

    def test_optimizer_job_store_delete_returns_payload_and_removes_only_requested_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            storage_path = Path(tmp) / "jobs.sqlite3"
            store = OptimizerJobStore(max_jobs=10, ttl_seconds=None, storage_path=storage_path)
            store.add(OptimizerJob(id="keep", created_at=1.0, request={"symbol": "KEEP"}, status="FINISHED"))
            store.add(OptimizerJob(id="remove", created_at=2.0, request={"symbol": "REMOVE"}, status="FAILED"))

            deleted = store.delete("remove")

            self.assertIsNotNone(deleted)
            self.assertEqual(deleted.id, "remove")
            self.assertEqual(deleted.request, {"symbol": "REMOVE"})
            self.assertIsNone(store.get("remove"))
            self.assertIsNotNone(store.get("keep"))
            self.assertIsNone(store.delete("missing"))

    def test_optimizer_worker_once_processes_claimed_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            store = OptimizerJobStore(max_jobs=10, ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3")
            store.add(OptimizerJob(id="queued", created_at=1.0, request={"symbol": "TEST"}, status="PENDING"))
            calls: list[str] = []

            web_module = __import__("backtest_engine.web").web
            original_run_job = web_module._run_job
            try:
                def fake_run_job(**kwargs) -> None:
                    calls.append(kwargs["job_id"])
                    kwargs["store"].update(kwargs["job_id"], status="FINISHED", summary={"worker": "done"})

                web_module._run_job = fake_run_job
                exit_code = run_optimizer_worker(repo_root=repo_root, store=store, once=True, worker_id="unit-test")
            finally:
                web_module._run_job = original_run_job

            self.assertEqual(exit_code, 0)
            self.assertEqual(calls, ["queued"])
            self.assertEqual(store.get("queued").status, "FINISHED")
            self.assertEqual(store.get("queued").summary, {"worker": "done"})

    def test_run_optimizer_worker_marks_interrupted_jobs_failed_at_startup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            store = OptimizerJobStore(max_jobs=10, ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3")
            store.add(OptimizerJob(id="stuck", created_at=1.0, request={}, status="IN_PROGRESS"))
            
            exit_code = run_optimizer_worker(repo_root=repo_root, store=store, once=True, worker_id="unit-test")
            
            self.assertEqual(exit_code, 0)
            stuck = store.get("stuck")
            self.assertEqual(stuck.status, "FAILED")
            self.assertIn("interrupted", stuck.error or "")

    def test_optimizer_job_store_expires_non_active_jobs(self) -> None:
        now = 1_000_000.0
        with tempfile.TemporaryDirectory() as tmp:
            storage_path = Path(tmp) / "jobs.sqlite3"
            store = OptimizerJobStore(max_jobs=10, ttl_seconds=60, storage_path=storage_path)
            store.add(OptimizerJob(id="expired", created_at=now - 120, request={}, status="FINISHED"))
            store.add(OptimizerJob(id="active", created_at=now - 120, request={}, status="IN_PROGRESS"))

            original_time = __import__("backtest_engine.job_store").job_store.time.time
            try:
                __import__("backtest_engine.job_store").job_store.time.time = lambda: now
                self.assertIsNone(store.get("expired"))
                self.assertIsNotNone(store.get("active"))
            finally:
                __import__("backtest_engine.job_store").job_store.time.time = original_time

    def test_fastapi_global_analysis_endpoint_success_and_confinement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            output_dir = "reports/local_optimizer"
            strategy = "hma_crossover"
            strategy_dir = repo_root / output_dir / strategy
            
            btc_dir = strategy_dir / "BTCUSDT"
            btc_run = btc_dir / "T20240101_120000"
            btc_run.mkdir(parents=True)
            
            with open(btc_run / "recommendations.json", "w", encoding="utf-8") as f:
                json.dump({
                    "score_metric": "sharpe_ratio",
                    "score_direction": "max",
                    "best": {
                        "score": 10.0,
                        "parameters": {"fast_len": 5},
                        "metrics": {"closed_trades": 5, "total_net_pnl": 50.0}
                    },
                    "recommended": {
                        "score": 8.0,
                        "parameters": {"fast_len": 5},
                        "metrics": {"closed_trades": 4, "total_net_pnl": 40.0}
                    },
                    "parameters": {
                        "fast_len": {"sweet_spot_range": [4, 6], "confidence": 0.8}
                    }
                }, f)
            with open(btc_run / "optimization_config.json", "w", encoding="utf-8") as f:
                json.dump({"timeframe_minutes": 15}, f)

            app = create_optimizer_app(
                repo_root=repo_root,
                store=OptimizerJobStore(ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3"),
            )
            client = TestClient(app)

            # Successful run
            response = client.post(
                "/api/global-analysis",
                json={"strategy": "hma_crossover", "output_dir": "reports/local_optimizer"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {
                "parquet": "/api/global-analysis/hma_crossover/global_summary.parquet",
                "html": "/api/global-analysis/hma_crossover/global_summary.html"
            })
            self.assertTrue((strategy_dir / "global_summary.parquet").exists())
            self.assertTrue((strategy_dir / "global_summary.html").exists())

            # Confinement test
            response_conf = client.post(
                "/api/global-analysis",
                json={"strategy": "hma_crossover", "output_dir": "../outside"},
            )
            self.assertEqual(response_conf.status_code, 400)
            self.assertIn("repo_root", response_conf.json()["error"])

    def test_fastapi_global_analysis_summary_serving_endpoints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            strategy_dir = repo_root / "reports" / "local_optimizer" / "hma_crossover"
            strategy_dir.mkdir(parents=True)
            
            pd.DataFrame({"SYMBOL": ["BTCUSDT"], "BEST_SCORE": [10.0]}).to_parquet(strategy_dir / "global_summary.parquet", engine="pyarrow")
            (strategy_dir / "global_summary.html").write_text("<html>Summary</html>", encoding="utf-8")

            app = create_optimizer_app(
                repo_root=repo_root,
                store=OptimizerJobStore(ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3"),
            )
            client = TestClient(app)

            # Serve Parquet
            parquet_response = client.get("/api/global-analysis/hma_crossover/global_summary.parquet")
            self.assertEqual(parquet_response.status_code, 200)
            self.assertEqual(parquet_response.headers["content-type"], "application/octet-stream")
            import io
            summary_frame = pd.read_parquet(io.BytesIO(parquet_response.content))
            self.assertIn("BTCUSDT", list(summary_frame["SYMBOL"]))

            # Serve HTML
            html_response = client.get("/api/global-analysis/hma_crossover/global_summary.html")
            self.assertEqual(html_response.status_code, 200)
            self.assertEqual(html_response.headers["content-type"], "text/html; charset=utf-8")
            self.assertEqual(html_response.text, "<html>Summary</html>")

            # Missing files (404)
            missing_response = client.get("/api/global-analysis/missing_strategy/global_summary.parquet")
            self.assertEqual(missing_response.status_code, 404)

    def test_fastapi_viewer_timeframes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            symbol_dir = repo_root / "reports" / "local_optimizer" / "hma_crossover" / "BTCUSDT"
            run_dir = symbol_dir / "T20240101_120000"
            run_dir.mkdir(parents=True)
            
            with open(run_dir / "optimization_config.json", "w", encoding="utf-8") as f:
                json.dump({"timeframe_minutes": 60}, f)

            app = create_optimizer_app(
                repo_root=repo_root,
                store=OptimizerJobStore(ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3"),
            )
            client = TestClient(app)

            # Success
            response = client.get("/api/viewer/timeframes", params={"symbol": "BTCUSDT", "strategy": "hma_crossover"})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {
                "timeframes": [{"value": "1h", "label": "1 heure", "minutes": 60}]
            })

            # Empty state
            response_empty = client.get("/api/viewer/timeframes", params={"symbol": "ETHUSDT"})
            self.assertEqual(response_empty.status_code, 200)
            self.assertEqual(response_empty.json(), {"timeframes": []})

            # Missing symbol parameter
            response_err = client.get("/api/viewer/timeframes")
            self.assertEqual(response_err.status_code, 400)
            self.assertIn("symbol is required", response_err.json()["error"])

    def test_fastapi_viewer_chart_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            
            # Setup dummy processed market data
            out = repo_root / "storage" / "processed" / "market_data_15m"
            out.mkdir(parents=True)
            
            # Generate more than 20 periods to allow simple indicators (e.g. SMA/HMA of length 5)
            index = pd.date_range("2024-01-01 09:30:00", periods=40, freq="15min")
            closes = [100.0 + (i % 5) for i in range(len(index))]
            frame = pd.DataFrame(
                {
                    "timestamp": index,
                    "symbol": ["TEST"] * len(index),
                    "open": closes,
                    "high": [val + 0.5 for val in closes],
                    "low": [val - 0.5 for val in closes],
                    "close": closes,
                    "volume": [1000] * len(index),
                    "quote_asset_volume": [1000.0] * len(index),
                    "number_of_trades": [10] * len(index),
                    "taker_buy_base_asset_volume": [500.0] * len(index),
                    "taker_buy_quote_asset_volume": [500.0] * len(index),
                }
            )
            frame.to_csv(out / "TEST.csv.gz", index=False, compression="gzip")

            app = create_optimizer_app(
                repo_root=repo_root,
                store=OptimizerJobStore(ttl_seconds=None, storage_path=repo_root / "jobs.sqlite3"),
            )
            client = TestClient(app)

            # Success with HMA strategy
            payload = {
                "symbol": "TEST",
                "timeframe": "15m",
                "strategy": "hma_crossover",
                "fast_len": 5,
                "slow_len": 15,
                "initial_capital": 1000.0,
            }
            response = client.post("/api/viewer/chart-data", json=payload)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["symbol"], "TEST")
            self.assertGreater(len(data["klines"]), 0)
            self.assertIn("hma_fast", data["indicators"])
            self.assertIn("hma_slow", data["indicators"])

            # Invalid timeframe validation
            payload_bad_tf = payload.copy()
            payload_bad_tf["timeframe"] = "invalid"
            response_bad_tf = client.post("/api/viewer/chart-data", json=payload_bad_tf)
            self.assertEqual(response_bad_tf.status_code, 400)
            self.assertIn("invalid literal", response_bad_tf.json()["error"])



class HtmlReportSecurityTests(unittest.TestCase):
    def test_html_report_escapes_symbol_and_metric_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.html"
            index = pd.DatetimeIndex(["2024-01-01"])
            bars = pd.DataFrame({"open": [1.0], "high": [1.0], "low": [1.0], "close": [1.0], "volume": [1.0]}, index=index)
            result = BacktestRunResult(
                strategy="hma<script>",
                symbol="<img src=x onerror=alert(1)>",
                config={},
                bars=bars,
                state=pd.DataFrame(index=index),
                trades=pd.DataFrame(),
                equity_curve=pd.DataFrame(index=index),
                metrics={"total_net_pnl": "<script>alert(1)</script>"},
            )

            write_html_summary(result, path)
            html = path.read_text(encoding="utf-8")

            self.assertIn("&lt;img src=x onerror=alert(1)&gt;", html)
            self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
            self.assertNotIn("<img src=x onerror=alert(1)>", html)
            self.assertNotIn("<script>alert(1)</script>", html)


class BacktestReportsDirTests(unittest.TestCase):
    def test_get_reports_dir_unset(self) -> None:
        import os
        from backtest_engine.paths import get_reports_dir
        orig = os.environ.get("BACKTEST_REPORTS_DIR")
        try:
            if "BACKTEST_REPORTS_DIR" in os.environ:
                del os.environ["BACKTEST_REPORTS_DIR"]
            resolved = get_reports_dir(Path("/tmp/repo"))
            self.assertEqual(resolved, Path("/tmp/repo/reports"))
        finally:
            if orig is not None:
                os.environ["BACKTEST_REPORTS_DIR"] = orig

    def test_get_reports_dir_set(self) -> None:
        import os
        from backtest_engine.paths import get_reports_dir
        orig = os.environ.get("BACKTEST_REPORTS_DIR")
        try:
            os.environ["BACKTEST_REPORTS_DIR"] = "/mnt/custom/reports"
            resolved = get_reports_dir(Path("/tmp/repo"))
            self.assertEqual(resolved, Path("/mnt/custom/reports"))
        finally:
            if orig is not None:
                os.environ["BACKTEST_REPORTS_DIR"] = orig
            else:
                if "BACKTEST_REPORTS_DIR" in os.environ:
                    del os.environ["BACKTEST_REPORTS_DIR"]

    def test_resolve_repo_path_external_reports(self) -> None:
        import os
        from backtest_engine.web import resolve_repo_path
        orig = os.environ.get("BACKTEST_REPORTS_DIR")
        try:
            os.environ["BACKTEST_REPORTS_DIR"] = "/mnt/custom/reports"
            repo_root = Path("/home/user/repo")
            
            # Should allow path inside repo
            p1 = resolve_repo_path(repo_root, "storage/processed", "processed")
            self.assertEqual(p1, Path("/home/user/repo/storage/processed"))
            
            # Should allow path inside external BACKTEST_REPORTS_DIR
            p2 = resolve_repo_path(repo_root, "/mnt/custom/reports/local_optimizer/job1", "job_dir")
            self.assertEqual(p2, Path("/mnt/custom/reports/local_optimizer/job1"))
            
            # Should reject path outside both
            with self.assertRaises(ValueError):
                resolve_repo_path(repo_root, "/var/log/syslog", "invalid")
        finally:
            if orig is not None:
                os.environ["BACKTEST_REPORTS_DIR"] = orig
            else:
                if "BACKTEST_REPORTS_DIR" in os.environ:
                    del os.environ["BACKTEST_REPORTS_DIR"]


if __name__ == "__main__":
    unittest.main()
