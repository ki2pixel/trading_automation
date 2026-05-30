#!/usr/bin/env python3
"""
Phase 4 — Bayesian Optimization by Volatility Profile (1m).
Optimizes parameters globally for low-volatility and high-volatility profiles.
"""

from __future__ import annotations

import json
import logging
import sys
import multiprocessing
from pathlib import Path
import pandas as pd
import numpy as np
import optuna

# Ensure repo root is on path for absolute imports
_repo = Path(__file__).resolve().parent.parent
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))

from backtest_engine.data import load_canonical_market_data
from backtest_engine.walk_forward import _run_single_backtest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("phase4_bayesian_by_vol")

# Volatility profiles definitions
PROFILES = {
    "low_vol": {
        "tickers": ["NVS", "SAP", "LOGI", "AMS.MC", "SHL.DE", "NVO"],
        "trials": 2,
        "description": "Faible vol (< 2.0%)"
    },
    "high_vol": {
        "tickers": ["GMAB", "ZEAL.CO"],
        "trials": 2,
        "description": "Élevée vol (≥ 2.0%)"
    }
}

# IS dates from raw_results.json (2 years before OOS)
IS_WINDOWS = {
    "AMS.MC":  {"start": "2021-11-14", "end": "2023-11-14"},
    "GMAB":    {"start": "2021-01-02", "end": "2023-01-02"},
    "LOGI":    {"start": "2021-06-17", "end": "2023-06-17"},
    "NVO":     {"start": "2021-11-08", "end": "2023-11-08"},
    "NVS":     {"start": "2021-06-16", "end": "2023-06-16"},
    "SAP":     {"start": "2021-04-16", "end": "2023-04-16"},
    "SHL.DE":  {"start": "2021-04-20", "end": "2023-04-20"},
    "ZEAL.CO": {"start": "2023-01-02", "end": "2024-01-02"},
}

GLOBAL_TICKER_DFS: dict[str, pd.DataFrame] = {}

def get_ticker_df(symbol: str, repo_root: Path) -> pd.DataFrame:
    df = GLOBAL_TICKER_DFS.get(symbol)
    if df is not None and not df.empty:
        return df
    window = IS_WINDOWS[symbol]
    try:
        df = load_canonical_market_data(
            symbol=symbol,
            repo_root=repo_root,
            processed_dir="storage/processed",
            start_date=window["start"],
            end_date=window["end"],
            timeframe_minutes=1,
        )
        GLOBAL_TICKER_DFS[symbol] = df
    except Exception as e:
        logger.error(f"Failed to load {symbol} inside worker: {e}")
        df = pd.DataFrame()
        GLOBAL_TICKER_DFS[symbol] = df
    return df


class ProfileObjective:
    def __init__(self, profile_name: str, tickers: list[str], repo_root: Path):
        self.profile_name = profile_name
        self.tickers = tickers
        self.repo_root = repo_root

    def __call__(self, trial: optuna.Trial) -> float:
        # Parameter suggestions
        lookback_days = trial.suggest_int("lookback_days", 10, 30)
        volatility_multiplier_enter = trial.suggest_float("volatility_multiplier_enter", 0.20, 0.60, step=0.05)
        volatility_multiplier_exit = trial.suggest_float("volatility_multiplier_exit", 0.05, 0.20, step=0.01)
        
        # Constraint: exit must be strictly smaller than enter
        if volatility_multiplier_exit >= volatility_multiplier_enter:
            volatility_multiplier_exit = volatility_multiplier_enter - 0.01
            
        target_daily_volatility = trial.suggest_float("target_daily_volatility", 0.008, 0.018, step=0.001)
        
        stoploss_step0 = trial.suggest_float("stoploss_ladder_step0", -0.020, -0.010, step=0.001)
        stoploss_step1 = trial.suggest_float("stoploss_ladder_step1", -0.030, -0.015, step=0.001)
        
        # Constraint: step1 < step0
        if stoploss_step1 >= stoploss_step0:
            stoploss_step1 = stoploss_step0 - 0.002
            
        stoploss_ratio0 = trial.suggest_float("stoploss_ladder_ratio0", 0.5, 0.9, step=0.1)
        takeprofit_step0 = trial.suggest_float("takeprofit_ladder_step0", 0.010, 0.030, step=0.001)
        
        params = {
            "lookback_days": int(lookback_days),
            "volatility_multiplier_enter": float(round(volatility_multiplier_enter, 4)),
            "volatility_multiplier_exit": float(round(volatility_multiplier_exit, 4)),
            "target_daily_volatility": float(round(target_daily_volatility, 4)),
            "exit_mode": "combined",
            "stoploss_ladder_step0": float(round(stoploss_step0, 4)),
            "stoploss_ladder_step1": float(round(stoploss_step1, 4)),
            "stoploss_ladder_ratio0": float(round(stoploss_ratio0, 2)),
            "takeprofit_ladder_step0": float(round(takeprofit_step0, 4)),
        }
        
        scores = []
        for symbol in self.tickers:
            df = get_ticker_df(symbol, self.repo_root)
            if df.empty:
                scores.append(-2.0)
                continue
            try:
                res = _run_single_backtest(
                    data=df,
                    symbol=symbol,
                    params=params,
                    initial_capital=1000.0,
                    timeframe_minutes=1,
                    repo_root=self.repo_root,
                    strategy="noise_boundary_intraday",
                    compute_full_metrics=False,
                    fast_score_metric="sharpe_ratio",
                )
                m = res.metrics
                trades = m.get("closed_trades") or 0
                sharpe = m.get("sharpe_ratio")
                if sharpe is None or pd.isna(sharpe):
                    sharpe = -1.0
                
                # Penalize lack of trading on 2-year IS data
                if trades < 20:
                    sharpe -= (20 - trades) * 0.1
                    
                scores.append(sharpe)
            except Exception as e:
                logger.warning(f"Backtest failed for {symbol} in trial {trial.number}: {e}")
                scores.append(-3.0)
                
        # Return average Sharpe ratio
        return float(np.mean(scores))


def run_worker(profile_name: str, tickers: list[str], n_trials: int, repo_root: Path) -> None:
    # Setup worker study and optimize single-threaded
    study = optuna.create_study(
        study_name=f"phase4_{profile_name}",
        storage=f"sqlite:///{repo_root}/storage/optuna_study.db",
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=42),
        load_if_exists=True
    )
    study.optimize(
        ProfileObjective(profile_name, tickers, repo_root),
        n_trials=n_trials,
        n_jobs=1
    )


def main() -> None:
    repo_root = Path("/home/kidpixel/trading_automation_v2")
    
    # Clean up previous Optuna DB to prevent conflict
    db_path = repo_root / "storage/optuna_study.db"
    if db_path.exists():
        logger.info(f"Removing old Optuna DB at {db_path}...")
        db_path.unlink()
        
    # Pre-load IS data for all tickers
    logger.info("Pre-loading IS canonical market data (1m)...")
    for symbol, window in IS_WINDOWS.items():
        logger.info(f"Loading {symbol} IS: {window['start']} -> {window['end']}")
        try:
            df = load_canonical_market_data(
                symbol=symbol,
                repo_root=repo_root,
                processed_dir="storage/processed",
                start_date=window["start"],
                end_date=window["end"],
                timeframe_minutes=1,
            )
            GLOBAL_TICKER_DFS[symbol] = df
            logger.info(f"  Loaded {len(df)} bars")
        except Exception as e:
            logger.error(f"  Failed to load {symbol}: {e}")
            GLOBAL_TICKER_DFS[symbol] = pd.DataFrame()

    results_by_profile = {}

    for profile_name, info in PROFILES.items():
        logger.info("=" * 60)
        logger.info(f"Starting Bayesian Optimization for profile: {profile_name} ({info['description']})")
        logger.info("=" * 60)
        
        tickers = info["tickers"]
        trials = info["trials"]
        
        study = optuna.create_study(
            study_name=f"phase4_{profile_name}",
            storage=f"sqlite:///{repo_root}/storage/optuna_study.db",
            direction="maximize",
            sampler=optuna.samplers.TPESampler(seed=42),
            load_if_exists=True
        )
        
        # Enqueue baseline conservative low vol parameters as prior for low_vol
        if profile_name == "low_vol":
            prior = {
                "lookback_days": 17,
                "volatility_multiplier_enter": 0.25,
                "volatility_multiplier_exit": 0.08,
                "target_daily_volatility": 0.012,
                "stoploss_ladder_step0": -0.015,
                "stoploss_ladder_step1": -0.020,
                "stoploss_ladder_ratio0": 0.8,
                "takeprofit_ladder_step0": 0.020,
            }
            study.enqueue_trial(prior)
            logger.info(f"Enqueued conservative low vol prior for {profile_name}")
            
        # Determine trials per worker dynamically
        n_workers = 8
        trials_per_worker = int(np.ceil(trials / n_workers))
        logger.info(f"Spawning {n_workers} processes with {trials_per_worker} trials each...")
        
        processes = []
        for _ in range(n_workers):
            p = multiprocessing.Process(
                target=run_worker,
                args=(profile_name, tickers, trials_per_worker, repo_root)
            )
            p.start()
            processes.append(p)
            
        for p in processes:
            p.join()
        
        best_trial = study.best_trial
        logger.info(f"Finished {profile_name}. Best average Sharpe IS: {best_trial.value:.3f}")
        logger.info(f"Best parameters: {best_trial.params}")
        
        # Run backtest for each ticker in the profile under best parameters to get detailed metrics
        best_params = best_trial.params.copy()
        # Enforce manual constraints if they were violated/adjusted
        if best_params.get("volatility_multiplier_exit", 0.08) >= best_params.get("volatility_multiplier_enter", 0.25):
            best_params["volatility_multiplier_exit"] = best_params["volatility_multiplier_enter"] - 0.01
        if best_params.get("stoploss_ladder_step1", -0.02) >= best_params.get("stoploss_ladder_step0", -0.015):
            best_params["stoploss_ladder_step1"] = best_params["stoploss_ladder_step0"] - 0.002
            
        best_params["exit_mode"] = "combined"
        
        ticker_metrics = {}
        for symbol in tickers:
            df = get_ticker_df(symbol, repo_root)
            if df.empty:
                continue
            res = _run_single_backtest(
                data=df,
                symbol=symbol,
                params=best_params,
                initial_capital=1000.0,
                timeframe_minutes=1,
                repo_root=repo_root,
                strategy="noise_boundary_intraday",
            )
            m = res.metrics
            ticker_metrics[symbol] = {
                "sharpe": m.get("sharpe_ratio"),
                "cagr": m.get("cagr_pct"),
                "mdd": m.get("max_drawdown_pct"),
                "trades": m.get("closed_trades"),
                "win_rate": m.get("win_rate_pct"),
            }
            
        results_by_profile[profile_name] = {
            "profile_name": profile_name,
            "description": info["description"],
            "best_value": best_trial.value,
            "best_params": best_params,
            "ticker_metrics": ticker_metrics
        }

    # Save to report dir
    out_dir = repo_root / "reports/noise_boundary_intraday/phase4_wfa_holdout_1m"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "bayesian_by_profile.json"
    
    out_path.write_text(json.dumps(results_by_profile, indent=2, default=str), encoding="utf-8")
    logger.info(f"\nAll profile optimization results saved to {out_path}")

if __name__ == "__main__":
    main()
