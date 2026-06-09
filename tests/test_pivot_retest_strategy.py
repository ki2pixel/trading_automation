import pytest
import pandas as pd
import numpy as np
import time

from backtest_engine.indicators.pivot_retest import PivotRetest
from pine_scripts_convert_to_python.strategy.pivot_retest_strategy import PivotRetestStrategyConfig, run_pivot_retest_strategy
from backtest_engine.strategy_registry import StrategyRegistry

def generate_test_data(rows: int) -> pd.DataFrame:
    # Generate random walk data for 1 minute timeframe over multiple days
    dates = pd.date_range("2024-01-01 00:00", periods=rows, freq="1min")
    close = np.cumsum(np.random.randn(rows) * 0.1) + 100
    high = close + np.random.rand(rows) * 0.2
    low = close - np.random.rand(rows) * 0.2
    open_price = close - np.random.randn(rows) * 0.05
    
    return pd.DataFrame({
        "open": open_price,
        "high": high,
        "low": low,
        "close": close,
        "volume": np.random.randint(1, 100, rows)
    }, index=dates)

def test_pivot_retest_no_lookahead():
    """
    Vérifie que la stratégie ne présente aucun lookahead bias :
    les signaux du jour N ne doivent pas dépendre du futur N+1.
    """
    df = generate_test_data(5000) # Environ 3.5 jours de données 1-min
    config = PivotRetestStrategyConfig(pivot_timeframe="D", retest_bars=5)
    
    df_copy = df.copy()
    run_pivot_retest_strategy(df_copy, config)
    
    signals_full = df_copy['long_entry'].copy()
    
    # On coupe les données au milieu (à T=2500)
    df_half = df.iloc[:2500].copy()
    run_pivot_retest_strategy(df_half, config)
    
    signals_half = df_half['long_entry'].copy()
    
    # La série des signaux calculée sur la moitié des données doit être STRICTEMENT identique
    # à la première moitié des signaux calculée sur l'ensemble complet.
    pd.testing.assert_series_equal(signals_full.iloc[:2500], signals_half, check_names=False)

def test_pivot_retest_numba_performance():
    """
    Vérifie que la fonction compilée njit() répond aux exigences de performance (sous la milliseconde pour un array).
    """
    df = generate_test_data(10000) # Environ 7 jours
    config = PivotRetestStrategyConfig(pivot_timeframe="D", retest_bars=5)
    
    # Warmup Numba compiler
    df_warmup = df.iloc[:100].copy()
    run_pivot_retest_strategy(df_warmup, config)
    
    df_perf = df.copy()
    start_time = time.perf_counter()
    run_pivot_retest_strategy(df_perf, config)
    end_time = time.perf_counter()
    
    elapsed_ms = (end_time - start_time) * 1000
    assert elapsed_ms < 50.0, f"Performance issue: Numba computation took {elapsed_ms:.2f} ms"

def test_pivot_retest_registry():
    """
    Vérifie que la stratégie s'enregistre et se charge correctement dans le Registry.
    """
    info = StrategyRegistry.get("pivot_retest")
    assert info is not None
    assert info.name == "pivot_retest"
    assert "bullish_signal" in info.indicators
