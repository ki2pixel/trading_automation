"""
Overfitting analysis tools: CSCV PBO (Bailey et al., 2016) and DSR (Lopez de Prado, 2018).
"""

from __future__ import annotations

import math
from itertools import combinations

import numpy as np


def compute_pbo_cscv(
    performance_matrix: np.ndarray,
    n_splits: int = 16,
) -> float:
    """
    Combinatorially Symmetric Cross-Validation Probability of Backtest Overfitting.

    Parameters
    ----------
    performance_matrix : np.ndarray, shape (n_strategies, n_observations)
        Performance (e.g. daily returns or Sharpe ratios) of each strategy
        on each temporal observation.  Must be contiguous in time.
    n_splits : int
        Number of contiguous subsamples to create.  Must be even and >= 4.

    Returns
    -------
    float
        Probability of backtest overfitting in [0, 1].

    References
    ----------
    Bailey, D., Borwein, J., Lopez de Prado, M., & Zhu, Q. (2016).
    "The Probability of Backtest Overfitting." Journal of Computational Finance.
    """
    if n_splits < 4 or n_splits % 2 != 0:
        raise ValueError("n_splits must be an even integer >= 4")

    n_strategies, n_obs = performance_matrix.shape
    if n_strategies < 2:
        return 0.0
    if n_obs < n_splits:
        return 0.0

    # Divide observations into n_splits contiguous blocks
    block_size = n_obs // n_splits
    block_returns = np.zeros((n_strategies, n_splits))
    for s in range(n_splits):
        start = s * block_size
        end = start + block_size if s < n_splits - 1 else n_obs
        block_returns[:, s] = performance_matrix[:, start:end].mean(axis=1)

    # CSCV: all combinations of n_splits/2 blocks as IS, complement as OOS
    S = n_splits // 2
    split_indices = list(range(n_splits))
    overfit_count = 0
    total_count = 0

    for is_combo in combinations(split_indices, S):
        oos_combo = tuple(i for i in split_indices if i not in is_combo)

        is_perf = block_returns[:, list(is_combo)].mean(axis=1)
        oos_perf = block_returns[:, list(oos_combo)].mean(axis=1)

        # Rank strategies by IS performance (descending)
        best_is_idx = int(np.argmax(is_perf))

        # Rank of best-IS strategy in OOS (1 = best, descending)
        oos_order = np.argsort(-oos_perf)
        oos_ranks = np.empty(n_strategies, dtype=int)
        oos_ranks[oos_order] = np.arange(1, n_strategies + 1)
        best_oos_rank = oos_ranks[best_is_idx]
        median_rank = (n_strategies + 1) / 2.0

        if best_oos_rank > median_rank:
            overfit_count += 1
        total_count += 1

    return overfit_count / total_count if total_count > 0 else 0.0


def compute_dsr(
    returns: np.ndarray,
    sharpe_observed: float,
    n_trials: int,
    skewness: float | None = None,
    kurtosis: float | None = None,
) -> float | None:
    """
    Deflated Sharpe Ratio (Lopez de Prado, 2018).

    Adjusts the observed Sharpe ratio for the multiple-testing bias induced
    by trying many strategy configurations and for non-normality of returns.

    Parameters
    ----------
    returns : np.ndarray
        Array of strategy returns (e.g. daily).
    sharpe_observed : float
        The Sharpe ratio observed on the backtest / OOS period.
    n_trials : int
        Number of independent trials explored.
    skewness : float | None
        Skewness of returns.  Computed from *returns* if None.
    kurtosis : float | None
        Excess kurtosis of returns.  Computed from *returns* if None.

    Returns
    -------
    float | None
        The deflated Sharpe ratio, or None if inputs are insufficient.
    """
    returns = np.asarray(returns)
    if len(returns) < 2 or math.isnan(sharpe_observed):
        return None

    # Annualisation factor: assuming daily returns -> 252 trading days
    # The input sharpe_observed is already annualised by the engine.
    # We de-annualise to daily for the formula, then re-annualise.
    # For simplicity we work directly with the annualised SR and adjust.
    sr = float(sharpe_observed)

    if skewness is None:
        # Unbiased skewness (numpy >=2 uses biased by default, correct manually)
        n = len(returns)
        m2 = float(np.var(returns, ddof=1))
        m3 = float(np.mean((returns - np.mean(returns)) ** 3))
        skewness = (m3 / (m2 ** 1.5)) * (n / ((n - 1) * (n - 2))) ** 0.5 if m2 > 0 and n > 2 else 0.0
    if kurtosis is None:
        # Unbiased excess kurtosis (Fisher)
        n = len(returns)
        m2 = float(np.var(returns, ddof=1))
        m4 = float(np.mean((returns - np.mean(returns)) ** 4))
        if m2 > 0 and n > 3:
            g2 = (m4 / (m2 ** 2)) - 3.0
            kurtosis = ((n - 1) / ((n - 2) * (n - 3))) * ((n + 1) * g2 + 6.0)
        else:
            kurtosis = 0.0

    # Non-normality correction factor V (Lopez de Prado, 2018, eq. 5)
    # V = 1 + skewness*SR/2 + (kurtosis-1)*SR^2/6
    # Note: kurtosis here is excess kurtosis, so (kurtosis - 1) corresponds to
    # (excess_kurtosis + 3 - 1) in the original formula.  Many implementations
    # use raw kurtosis directly.  We follow the convention where the term is
    # (kurtosis - 1) with *raw* kurtosis.  Since scipy returns excess kurtosis,
    # raw = excess + 3.
    raw_kurt = kurtosis + 3.0
    V = 1.0 + (skewness * sr) / 2.0 + ((raw_kurt - 1.0) * sr * sr) / 6.0
    if V <= 0 or math.isnan(V):
        V = 1.0

    # Multiple testing correction via expected maximum of standard normals
    # (Bailey & Lopez de Prado, 2014, eq. 1)
    # SR_0 = (1 - gamma) * Phi^{-1}(1 - 1/V) + gamma * Phi^{-1}(1 - 1/(V*e^V))
    # Simplified: approximate SR_0 for multiple trials
    # SR_0 ≈ (1 - 1/V) * sqrt(2 * ln(n_trials))
    if n_trials <= 1:
        sr0 = 0.0
    else:
        sr0 = np.sqrt(2.0 * np.log(n_trials))

    # Deflated Sharpe
    # DSR = SR_estimated * sqrt(1 - V * SR_estimated^2 / (2 * N_obs))
    #      ... but the more common closed form is:
    # DSR ≈ SR_estimated * (1 - V * SR_estimated^2 / (2 * N))^{1/2}
    # We use a practical implementation that compares against sr0:
    if sr <= sr0:
        return 0.0

    # Alternative practical formula (Lopez de Prado, 2018):
    # DSR = SR * psi, where psi = (1 - V*SR^2/(2N))^{1/2}
    N = len(returns)
    psi_sq = 1.0 - (V * sr * sr) / (2.0 * N)
    if psi_sq <= 0:
        return 0.0
    dsr = sr * math.sqrt(psi_sq)
    return float(dsr)
