import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller
import scipy.spatial.distance as dist
from typing import Dict, Any, Tuple

def calculate_hurst_exponent(series: pd.Series, max_lag: int = 100) -> float:
    """
    Calcul de l'exposant de Hurst (H) pour évaluer la persistance temporelle.
    H < 0.5 : retour à la moyenne (anti-persistant)
    H = 0.5 : marche aléatoire
    H > 0.5 : tendance (persistant)
    """
    clean_series = series.dropna().values
    n = len(clean_series)
    if n < max_lag * 2:
        return np.nan
        
    lags = np.arange(2, min(max_lag, n // 10))
    tau = []
    for lag in lags:
        # Écart-type des différences retardées de lag périodes
        diff = clean_series[lag:] - clean_series[:-lag]
        tau.append(np.std(diff))
        
    # Régression linéaire de ln(tau) sur ln(lag)
    # log(std) = H * log(lag) + C
    try:
        poly = np.polyfit(np.log(lags), np.log(tau), 1)
        return float(poly[0])
    except Exception:
        return np.nan

def calculate_adf_statistic(series: pd.Series) -> Dict[str, float]:
    """
    Exécute le test Augmented Dickey-Fuller (ADF) pour évaluer la stationnarité.
    Retourne la statistique de test et la p-value.
    """
    clean_series = series.dropna()
    if len(clean_series) < 50:
        return {"stat": 0.0, "p_value": 1.0}
    try:
        # Utilisation de la régression constante avec sélection automatique AIC
        res = adfuller(clean_series, regression='c', autolag='AIC')
        return {
            "stat": float(res[0]),
            "p_value": float(res[1])
        }
    except Exception:
        return {"stat": np.nan, "p_value": np.nan}

def calculate_half_life(series: pd.Series) -> float:
    """
    Calcule la demi-vie de retour à la moyenne (en nombre de bougies)
    via un modèle d'Ornstein-Uhlenbeck discrétisé (AR(1)).
    Retourne np.inf si aucun retour à la moyenne n'est détecté (pente positive).
    """
    clean_series = series.dropna()
    if len(clean_series) < 20:
        return np.nan
        
    x = clean_series.shift(1).iloc[1:].values
    y = clean_series.diff().iloc[1:].values
    
    try:
        # Régression linéaire : dy = alpha + beta * x
        beta, alpha = np.polyfit(x, y, 1)
        if beta >= 0:
            return np.inf  # Pas de mean reversion
            
        # demi-vie = -ln(2) / beta
        half_life = -np.log(2) / beta
        return float(half_life)
    except Exception:
        return np.nan

def calculate_autocorrelation(series: pd.Series, lag: int = 1) -> float:
    """
    Calcule l'autocorrélation à un lag donné.
    """
    clean_series = series.dropna()
    if len(clean_series) < lag + 5:
        return np.nan
    try:
        return float(clean_series.autocorr(lag=lag))
    except Exception:
        return np.nan

def get_mahalanobis_distance(u: np.ndarray, v: np.ndarray, cov: np.ndarray) -> float:
    """
    Calcule la distance de Mahalanobis entre deux vecteurs u et v
    à l'aide de la matrice de covariance cov.
    """
    try:
        inv_cov = np.linalg.inv(cov)
        return float(dist.mahalanobis(u, v, inv_cov))
    except Exception:
        # Repli sur la distance euclidienne si la matrice n'est pas inversible
        return float(dist.euclidean(u, v))

def calculate_adv_currency(df: pd.DataFrame) -> float:
    """
    Calcule la valeur moyenne échangée quotidiennement (Average Daily Volume en devise).
    """
    df_temp = df.copy()
    if 'timestamp' in df_temp.columns:
        df_temp = df_temp.set_index('timestamp')
    if not isinstance(df_temp.index, pd.DatetimeIndex):
        df_temp.index = pd.to_datetime(df_temp.index)
        
    daily_value = (df_temp['close'] * df_temp['volume']).resample('D').sum()
    daily_value = daily_value[daily_value > 0]
    if len(daily_value) == 0:
        return 0.0
    return float(daily_value.mean())

def calculate_realized_volatility(series: pd.Series, periods: int = 252) -> float:
    """
    Calcule la volatilité historique annualisée sur la base des rendements logarithmiques.
    """
    clean_series = series.dropna()
    if len(clean_series) < 10:
        return np.nan
    log_returns = np.log(clean_series / clean_series.shift(1)).dropna()
    return float(log_returns.std() * np.sqrt(periods))

def extract_statistical_signature(df: pd.DataFrame, target_col: str = 'close') -> Dict[str, Any]:
    """
    Extrait le profil statistique complet (la signature) d'un jeu de données.
    """
    df_clean = df.copy()
    if 'timestamp' in df_clean.columns:
        df_clean = df_clean.set_index('timestamp')
    if not isinstance(df_clean.index, pd.DatetimeIndex):
        df_clean.index = pd.to_datetime(df_clean.index)
        
    series = df_clean[target_col]
    
    hurst = calculate_hurst_exponent(series)
    adf = calculate_adf_statistic(series)
    half_life = calculate_half_life(series)
    rho_1 = calculate_autocorrelation(series, lag=1)
    rho_5 = calculate_autocorrelation(series, lag=5)
    
    # Rendements journaliers pour la volatilité
    daily_series = series.resample('D').last().dropna()
    vol = calculate_realized_volatility(daily_series)
    
    adv = calculate_adv_currency(df_clean)
    
    # Nombre d'années de données
    total_days = (df_clean.index[-1] - df_clean.index[0]).days
    history_years = total_days / 365.25
    
    return {
        "hurst": hurst,
        "adf_stat": adf["stat"],
        "adf_pvalue": adf["p_value"],
        "half_life": half_life,
        "volatility_daily": vol,
        "rho_1": rho_1,
        "rho_5": rho_5,
        "adv": adv,
        "history_years": history_years
    }
