#!/usr/bin/env python3
"""
Scratch script to investigate the sizing and MDD on SAP (OOS period: 2023-04-16 to 2024-04-16).
Compares the OLD mode (where volatility is calculated on 1m bars, leading to huge sizes)
with the NEW mode (where the precalculated daily historical volatility is passed).
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Ensure repo root is in python path
repo = Path(__file__).resolve().parent.parent
if str(repo) not in sys.path:
    sys.path.insert(0, str(repo))

from backtest_engine.data import load_canonical_market_data
from backtest_engine.strategies.noise_boundary_intraday import run_noise_boundary_intraday, noise_boundary_overrides_from_mapping
from backtest_engine.broker import BrokerSimulator

def main():
    print("=" * 60)
    print("Sizing & MDD Investigation: SAP OOS (2023-04-16 -> 2024-04-16)")
    print("=" * 60)

    # 1. Load Data
    print("Loading SAP data...")
    df = load_canonical_market_data(
        symbol="SAP",
        repo_root=repo,
        start_date="2023-04-16",
        end_date="2024-04-16",
        timeframe_minutes=1
    )
    print(f"Loaded {len(df)} rows.")

    # 2. Parameters (Phase 3 Baseline)
    params = {
        "lookback_days": 17,
        "volatility_multiplier_enter": 0.5,
        "volatility_multiplier_exit": 0.1,
        "target_daily_volatility": 0.018,
        "exit_mode": "combined",
        "stoploss_ladder_step0": -0.018,
        "stoploss_ladder_step1": -0.020,
        "stoploss_ladder_ratio0": 0.8,
        "takeprofit_ladder_step0": 0.028,
        "use_sequential_ladder": True,
        "entry_on_high_low": True
    }
    
    overrides = noise_boundary_overrides_from_mapping(params)

    # Save original calculate_position_size
    original_calculate_position_size = BrokerSimulator.calculate_position_size

    # --- RUN OLD MODE ---
    print("\n--- Running OLD MODE (Intraday 1m Volatility Fallback) ---")
    def mock_calculate_position_size_old(self, price, equity, realized_volatility=None, bars_for_vol=None):
        # Ignore realized_volatility to trigger the intraday 1m fallback
        return original_calculate_position_size(self, price, equity, realized_volatility=None, bars_for_vol=bars_for_vol)

    BrokerSimulator.calculate_position_size = mock_calculate_position_size_old
    
    try:
        res_old = run_noise_boundary_intraday(
            data=df,
            symbol="SAP",
            overrides=overrides,
            initial_capital=1000.0,
            timeframe_minutes=1,
            repo_root=repo
        )
        metrics_old = res_old.metrics
        equity_old = res_old.equity_curve
        trades_old = res_old.trades
        
        print(f"Old Mode Metrics:")
        print(f"  Sharpe Ratio: {metrics_old.get('sharpe_ratio')}")
        print(f"  CAGR: {metrics_old.get('cagr_pct')}%")
        print(f"  Max Drawdown: {metrics_old.get('max_drawdown_pct')}%")
        print(f"  Total Trades: {metrics_old.get('closed_trades')}")
        
        if not trades_old.empty:
            max_size_old = trades_old["quantity"].abs().max()
            max_value_old = (trades_old["quantity"].abs() * trades_old["entry_price"]).max()
            print(f"  Max Position Size: {max_size_old:.2f} shares")
            print(f"  Max Position Value: {max_value_old:.2f} EUR (leverage: {max_value_old / 1000.0:.1f}x)")
        else:
            print("  No trades in Old Mode.")
            
    except Exception as e:
        print(f"Old Mode failed: {e}")
        import traceback
        traceback.print_exc()

    # --- RUN NEW MODE ---
    print("\n--- Running NEW MODE (Precalculated Daily Volatility Passed) ---")
    # Restore original calculate_position_size
    BrokerSimulator.calculate_position_size = original_calculate_position_size

    try:
        res_new = run_noise_boundary_intraday(
            data=df,
            symbol="SAP",
            overrides=overrides,
            initial_capital=1000.0,
            timeframe_minutes=1,
            repo_root=repo
        )
        metrics_new = res_new.metrics
        equity_new = res_new.equity_curve
        trades_new = res_new.trades
        
        print(f"New Mode Metrics:")
        print(f"  Sharpe Ratio: {metrics_new.get('sharpe_ratio')}")
        print(f"  CAGR: {metrics_new.get('cagr_pct')}%")
        print(f"  Max Drawdown: {metrics_new.get('max_drawdown_pct')}%")
        print(f"  Total Trades: {metrics_new.get('closed_trades')}")
        
        if not trades_new.empty:
            max_size_new = trades_new["quantity"].abs().max()
            max_value_new = (trades_new["quantity"].abs() * trades_new["entry_price"]).max()
            print(f"  Max Position Size: {max_size_new:.2f} shares")
            print(f"  Max Position Value: {max_value_new:.2f} EUR (leverage: {max_value_new / 1000.0:.1f}x)")
        else:
            print("  No trades in New Mode.")
            
    except Exception as e:
        print(f"New Mode failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == "__main__":
    main()
