import logging
from pathlib import Path
from backtest_engine.optimizer import ParameterGridSpec, load_data_and_optimize

logging.basicConfig(level=logging.INFO)

def main():
    specs = [
        ParameterGridSpec("lookback_days", "numeric", (5, 6, 30)),
        ParameterGridSpec("volatility_multiplier_enter", "numeric", (0.5, 0.6, 3.0)),
        ParameterGridSpec("volatility_multiplier_exit", "numeric", (0.1, 0.2, 2.0)),
        ParameterGridSpec("target_daily_volatility", "numeric", (0.005, 0.006, 0.02)),
        ParameterGridSpec("exit_mode", "choice", ("time_only", "vwap", "ladder", "combined")),
        ParameterGridSpec("stoploss_ladder_step0", "numeric", (-0.020, -0.019, -0.002)),
        ParameterGridSpec("stoploss_ladder_step1", "numeric", (-0.030, -0.029, -0.005)),
        ParameterGridSpec("stoploss_ladder_ratio0", "numeric", (0.1, 0.2, 0.9)),
        ParameterGridSpec("takeprofit_ladder_step0", "numeric", (0.005, 0.006, 0.030)),
    ]

    summary = load_data_and_optimize(
        repo_root=Path("."),
        symbol="LOGI",
        processed_dir="storage/processed",
        output_root=Path("reports/noise_boundary_intraday/phase3_optim"),
        strategy="noise_boundary_intraday",
        score_metric="sharpe_ratio",
        score_direction="max",
        timeframe_minutes=5,
        parameter_specs=specs,
        optimization_mode="bayesian",
        max_iterations=150, # maps to n_trials in bayesian
        workers=1,
        enable_convergence_stop=True,
        convergence_patience=100,
        convergence_window_size=50,
        start_date="2022-01-01",
        end_date="2023-01-01"
    )
    print("Optimization finished at:", summary.output_dir)

if __name__ == "__main__":
    main()
