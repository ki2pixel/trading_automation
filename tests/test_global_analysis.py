import unittest
import tempfile
import json
import csv
import pandas as pd
from pathlib import Path
from html import escape

from backtest_engine.global_analysis import generate_global_analysis


class TestGlobalAnalysis(unittest.TestCase):
    def test_generate_global_analysis_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            output_dir = "reports/local_optimizer"
            strategy = "hma_crossover"
            
            # Setup folders for multiple symbols: BTCUSDT and ETHUSDT
            strategy_dir = repo_root / output_dir / strategy
            
            btc_dir = strategy_dir / "BTCUSDT"
            eth_dir = strategy_dir / "ETHUSDT"
            
            # BTC has 2 runs with different scores (10.0 and 25.0)
            btc_run1 = btc_dir / "T20240101_120000"
            btc_run2 = btc_dir / "T20240101_130000"
            btc_run1.mkdir(parents=True)
            btc_run2.mkdir(parents=True)
            
            # ETH has 1 run
            eth_run1 = eth_dir / "T20240101_140000"
            eth_run1.mkdir(parents=True)
            
            # Write recommendations and config for BTC run1
            with open(btc_run1 / "recommendations.json", "w", encoding="utf-8") as f:
                json.dump({
                    "score_metric": "sharpe_ratio",
                    "score_direction": "max",
                    "best": {
                        "score": 10.0,
                        "parameters": {"fast_len": 5, "slow_len": 15},
                        "metrics": {"closed_trades": 10, "total_net_pnl": 100.0, "max_drawdown": -0.05, "sharpe_ratio": 1.5}
                    },
                    "recommended": {
                        "score": 8.0,
                        "parameters": {"fast_len": 6, "slow_len": 16},
                        "metrics": {"closed_trades": 8, "total_net_pnl": 80.0, "max_drawdown": -0.04, "sharpe_ratio": 1.2}
                    },
                    "parameters": {
                        "fast_len": {"sweet_spot_range": [4, 6], "confidence": 0.8},
                        "slow_len": {"sweet_spot_range": [14, 16], "confidence": 0.75}
                    }
                }, f)
            with open(btc_run1 / "optimization_config.json", "w", encoding="utf-8") as f:
                json.dump({"timeframe_minutes": 15}, f)
                
            # Write recommendations and config for BTC run2 (better score!)
            with open(btc_run2 / "recommendations.json", "w", encoding="utf-8") as f:
                json.dump({
                    "score_metric": "sharpe_ratio",
                    "score_direction": "max",
                    "best": {
                        "score": 25.0,
                        "parameters": {"fast_len": 4, "slow_len": 14},
                        "metrics": {"closed_trades": 12, "total_net_pnl": 250.0, "max_drawdown": -0.03, "sharpe_ratio": 2.5}
                    },
                    "recommended": {
                        "score": 20.0,
                        "parameters": {"fast_len": 4, "slow_len": 14},
                        "metrics": {"closed_trades": 12, "total_net_pnl": 250.0, "max_drawdown": -0.03, "sharpe_ratio": 2.5}
                    },
                    "parameters": {
                        "fast_len": {"sweet_spot_range": [3, 5], "confidence": 0.9},
                        "slow_len": {"sweet_spot_range": [13, 15], "confidence": 0.85}
                    }
                }, f)
            with open(btc_run2 / "optimization_config.json", "w", encoding="utf-8") as f:
                json.dump({"timeframe_minutes": 60}, f)
                
            # Write recommendations and config for ETH run1
            with open(eth_run1 / "recommendations.json", "w", encoding="utf-8") as f:
                json.dump({
                    "score_metric": "sharpe_ratio",
                    "score_direction": "max",
                    "best": {
                        "score": 5.0,
                        "parameters": {"fast_len": 10, "slow_len": 30},
                        "metrics": {"closed_trades": 5, "total_net_pnl": 50.0, "max_drawdown": -0.1, "sharpe_ratio": 0.5}
                    },
                    "recommended": {
                        "score": 4.0,
                        "parameters": {"fast_len": 11, "slow_len": 31},
                        "metrics": {"closed_trades": 4, "total_net_pnl": 40.0, "max_drawdown": -0.09, "sharpe_ratio": 0.4}
                    },
                    "parameters": {
                        "fast_len": {"sweet_spot_range": [9, 11], "confidence": 0.6},
                        "slow_len": {"sweet_spot_range": [29, 31], "confidence": 0.55}
                    }
                }, f)
            with open(eth_run1 / "optimization_config.json", "w", encoding="utf-8") as f:
                json.dump({"timeframe_minutes": 240}, f)

            # Generate global analysis
            res = generate_global_analysis(repo_root, strategy, output_dir)
            
            # Assert return API paths are correct
            self.assertEqual(res, {
                "parquet": f"/api/global-analysis/{strategy}/global_summary.parquet",
                "html": f"/api/global-analysis/{strategy}/global_summary.html"
            })
            
            # Verify Parquet file existence and content
            parquet_path = strategy_dir / "global_summary.parquet"
            self.assertTrue(parquet_path.exists())
            
            # Load Parquet using pandas and assert shape and sorted symbols
            df = pd.read_parquet(parquet_path)
            self.assertEqual(len(df), 2)
            self.assertEqual(list(df["SYMBOL"]), ["BTCUSDT", "ETHUSDT"])
            
            # BTC should have picked btc_run2 (better score: 25.0 vs 10.0)
            btc_row = df[df["SYMBOL"] == "BTCUSDT"].iloc[0]
            self.assertEqual(btc_row["TIMEFRAME"], 60)
            self.assertEqual(btc_row["BEST_SCORE"], 25.0)
            self.assertEqual(btc_row["BEST_FAST_LEN"], 4)
            self.assertEqual(btc_row["SWEET_SPOT_FAST_LEN"], "[3, 5]")
            self.assertEqual(btc_row["CONF_FAST_LEN"], 0.9)
            
            # ETH should match eth_run1 values
            eth_row = df[df["SYMBOL"] == "ETHUSDT"].iloc[0]
            self.assertEqual(eth_row["TIMEFRAME"], 240)
            self.assertEqual(eth_row["BEST_SCORE"], 5.0)
            self.assertEqual(eth_row["BEST_FAST_LEN"], 10)
            self.assertEqual(eth_row["SWEET_SPOT_SLOW_LEN"], "[29, 31]")
            self.assertEqual(eth_row["CONF_SLOW_LEN"], 0.55)

            # Verify HTML file existence and XSS safety/structure
            html_path = strategy_dir / "global_summary.html"
            self.assertTrue(html_path.exists())
            html_content = html_path.read_text(encoding="utf-8")
            
            self.assertIn("<h1>Synthèse Globale Optimizer — hma_crossover</h1>", html_content)
            self.assertIn("BTCUSDT", html_content)
            self.assertIn("ETHUSDT", html_content)
            self.assertIn("SWEET_SPOT_FAST_LEN", html_content)

    def test_generate_global_analysis_missing_directory_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            # Non-existent strategy directory
            with self.assertRaises(FileNotFoundError):
                generate_global_analysis(repo_root, "missing_strategy")

    def test_generate_global_analysis_no_valid_runs_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            strategy_dir = repo_root / "reports/local_optimizer/hma_crossover"
            btc_dir = strategy_dir / "BTCUSDT"
            btc_dir.mkdir(parents=True)
            
            # Create an empty directory with no T-prefixed runs
            (btc_dir / "not_a_run").mkdir()
            
            with self.assertRaises(ValueError):
                generate_global_analysis(repo_root, "hma_crossover")

    def test_generate_global_analysis_resilience_to_malformed_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp).resolve()
            output_dir = "reports/local_optimizer"
            strategy = "hma_crossover"
            strategy_dir = repo_root / output_dir / strategy
            
            btc_dir = strategy_dir / "BTCUSDT"
            btc_run1 = btc_dir / "T20240101_120000"
            btc_run2 = btc_dir / "T20240101_130000"
            btc_run1.mkdir(parents=True)
            btc_run2.mkdir(parents=True)
            
            # BTC run1 has bad/corrupted JSON file
            with open(btc_run1 / "recommendations.json", "w", encoding="utf-8") as f:
                f.write("{invalid json...")
            
            # BTC run2 has perfectly valid JSON
            with open(btc_run2 / "recommendations.json", "w", encoding="utf-8") as f:
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
            with open(btc_run2 / "optimization_config.json", "w", encoding="utf-8") as f:
                json.dump({"timeframe_minutes": 15}, f)

            # Execution should succeed due to resilience skipping btc_run1 and using btc_run2
            res = generate_global_analysis(repo_root, strategy, output_dir)
            self.assertIn("parquet", res)
            
            df = pd.read_parquet(strategy_dir / "global_summary.parquet")
            self.assertEqual(len(df), 1)
            self.assertEqual(df.iloc[0]["SYMBOL"], "BTCUSDT")
            self.assertEqual(df.iloc[0]["BEST_SCORE"], 10.0)


if __name__ == "__main__":
    unittest.main()
