import pytest
import optuna

from backtest_engine.bayesian_optimizer import (
    _suggest_parameters,
    validate_noise_boundary_constraints
)
from backtest_engine.optimizer import ParameterGridSpec

def test_validate_noise_boundary_constraints():
    assert validate_noise_boundary_constraints({
        "volatility_multiplier_enter": 2.0,
        "volatility_multiplier_exit": 1.0,
        "stoploss_ladder_step0": -0.008,
        "stoploss_ladder_step1": -0.015,
        "takeprofit_ladder_step0": 0.012
    }) == True

    # Invalid: exit >= enter
    assert validate_noise_boundary_constraints({
        "volatility_multiplier_enter": 1.0,
        "volatility_multiplier_exit": 2.0,
    }) == False

    # Invalid: SL step1 >= SL step0
    assert validate_noise_boundary_constraints({
        "stoploss_ladder_step0": -0.015,
        "stoploss_ladder_step1": -0.008,
    }) == False

def test_suggest_parameters_constraints():
    specs = [
        ParameterGridSpec("volatility_multiplier_enter", "numeric", (1.0, 5.0)),
        ParameterGridSpec("volatility_multiplier_exit", "numeric", (0.1, 4.0)),
        ParameterGridSpec("stoploss_ladder_step0", "numeric", (-0.02, -0.002)),
        ParameterGridSpec("stoploss_ladder_step1", "numeric", (-0.03, -0.005)),
    ]
    
    study = optuna.create_study()
    trial = study.ask()
    
    params = _suggest_parameters(trial, specs, strategy="noise_boundary_intraday")
    
    assert params["volatility_multiplier_exit"] < params["volatility_multiplier_enter"]
    assert params["stoploss_ladder_step1"] < params["stoploss_ladder_step0"]
    assert validate_noise_boundary_constraints(params) == True
