import pytest
import numpy as np
import pandas as pd
from backtest_engine.screening import (
    calculate_hurst_exponent,
    calculate_adf_statistic,
    calculate_half_life,
    get_mahalanobis_distance,
    calculate_adv_currency,
    calculate_realized_volatility
)

def test_calculate_hurst_exponent():
    np.random.seed(42)
    # 1. Marche aléatoire (Hurst ~ 0.5)
    random_walk = np.cumsum(np.random.normal(0, 1, 1000))
    h_rw = calculate_hurst_exponent(pd.Series(random_walk))
    assert 0.35 <= h_rw <= 0.65

    # 2. Série fortement retour à la moyenne (Hurst < 0.5)
    # Processus autoregressif AR(1) avec coefficient négatif fort
    ar_series = [0]
    for _ in range(999):
        ar_series.append(-0.8 * ar_series[-1] + np.random.normal(0, 1))
    h_ar = calculate_hurst_exponent(pd.Series(ar_series))
    assert h_ar < 0.5

    # 3. Série à tendance forte (Hurst > 0.5)
    # Cumulative sum de bruit fortement auto-corrélé positivement
    ar_series_pos = [0]
    for _ in range(999):
        ar_series_pos.append(0.85 * ar_series_pos[-1] + np.random.normal(0, 1))
    trending = np.cumsum(ar_series_pos)
    h_trend = calculate_hurst_exponent(pd.Series(trending))
    assert h_trend > 0.5

def test_calculate_adf_statistic():
    np.random.seed(42)
    # Série stationnaire (doit rejeter l'hypothèse nulle -> p_value très basse)
    stationary = np.random.normal(0, 1, 500)
    res_stat = calculate_adf_statistic(pd.Series(stationary))
    assert res_stat["p_value"] < 0.05

    # Série non stationnaire (marche aléatoire -> p_value élevée)
    non_stationary = np.cumsum(np.random.normal(0, 1, 500))
    res_non_stat = calculate_adf_statistic(pd.Series(non_stationary))
    assert res_non_stat["p_value"] > 0.10

def test_calculate_half_life():
    np.random.seed(42)
    # Série retour à la moyenne rapide (pente beta < 0)
    # dy = -0.3 * x + e -> beta = -0.3
    # demi-vie = -ln(2) / -0.3 = 2.31 bougies
    series = [100.0]
    for _ in range(500):
        prev = series[-1]
        dy = -0.3 * (prev - 100.0) + np.random.normal(0, 1)
        series.append(prev + dy)

    half_life = calculate_half_life(pd.Series(series))
    assert 1.5 <= half_life <= 3.5

    # Série divergente (pente positive) -> pas de retour à la moyenne
    divergent = np.cumsum(np.random.normal(1, 1, 100))
    hl_div = calculate_half_life(pd.Series(divergent))
    assert hl_div == np.inf or np.isnan(hl_div)

def test_get_mahalanobis_distance():
    u = np.array([1.0, 2.0, 3.0])
    v = np.array([1.2, 1.9, 3.1])
    cov = np.eye(3) * 0.5  # Variance de 0.5 sur chaque axe

    d_m = get_mahalanobis_distance(u, v, cov)
    assert d_m > 0
    # La distance de Mahalanobis avec une matrice de covariance diagonale d'identité mise à l'échelle
    # correspond à la distance euclidienne divisée par la racine de la variance.
    # d_e = sqrt(0.2^2 + 0.1^2 + 0.1^2) = sqrt(0.06) = 0.2449
    # d_m = d_e / sqrt(0.5) = 0.2449 / 0.7071 = 0.346
    assert pytest.approx(d_m, rel=1e-2) == 0.346

def test_calculate_adv_currency():
    timestamps = pd.date_range("2026-06-01", periods=5, freq="D")
    df = pd.DataFrame({
        "timestamp": timestamps,
        "close": [10.0, 11.0, 10.5, 9.5, 10.0],
        "volume": [1000, 2000, 1500, 3000, 2500],
        "symbol": ["TEST"] * 5
    })

    # Valeurs échangées quotidiennes :
    # D1 : 10.0 * 1000 = 10 000
    # D2 : 11.0 * 2000 = 22 000
    # D3 : 10.5 * 1500 = 15 750
    # D4 : 9.5 * 3000 = 28 500
    # D5 : 10.0 * 2500 = 25 000
    # Moyenne = (10000 + 22000 + 15750 + 28500 + 25000) / 5 = 101250 / 5 = 20250
    adv = calculate_adv_currency(df)
    assert adv == 20250.0

def test_calculate_realized_volatility():
    # Série à volatilité fixe
    np.random.seed(42)
    daily_prices = [100.0]
    for _ in range(252):
        ret = np.random.normal(0, 0.01) # Écart-type journalier de 1%
        daily_prices.append(daily_prices[-1] * np.exp(ret))

    vol = calculate_realized_volatility(pd.Series(daily_prices))
    # Volatilité annualisée ~ 1% * sqrt(252) ~ 15.8%
    assert 0.10 <= vol <= 0.22
