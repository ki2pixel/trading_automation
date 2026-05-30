import numpy as np
import pytest

from backtest_engine.overfitting_analysis import compute_dsr, compute_pbo_cscv


class TestComputePboCscv:
    def test_random_strategies_high_pbo(self):
        np.random.seed(42)
        mat = np.random.randn(20, 256)
        pbo = compute_pbo_cscv(mat, n_splits=16)
        assert 0.0 <= pbo <= 1.0
        # Random strategies should show moderate-to-high PBO
        assert pbo >= 0.3

    def test_perfect_signal_low_pbo(self):
        np.random.seed(7)
        base = np.random.randn(1, 256) * 0.5
        # Strategy 0 is consistently best
        mat = np.vstack([base + 2.0, base + 1.0, base + 0.5, base + 0.0])
        pbo = compute_pbo_cscv(mat, n_splits=8)
        assert 0.0 <= pbo <= 1.0
        # Best IS strategy should also be best OOS -> low PBO
        assert pbo < 0.5

    def test_invalid_splits_raises(self):
        with pytest.raises(ValueError):
            compute_pbo_cscv(np.zeros((5, 100)), n_splits=3)


class TestComputeDsr:
    def test_dsr_positive_with_good_sharpe(self):
        np.random.seed(1)
        returns = np.random.normal(0.001, 0.02, 252)
        sr = 1.5
        dsr = compute_dsr(returns, sr, n_trials=10)
        assert dsr is not None
        assert dsr >= 0.0
        # DSR should generally be <= observed Sharpe
        assert dsr <= sr

    def test_dsr_zero_when_sharpe_below_threshold(self):
        np.random.seed(2)
        returns = np.random.normal(0.0, 0.02, 252)
        sr = 0.1
        dsr = compute_dsr(returns, sr, n_trials=50)
        assert dsr is not None
        assert dsr == 0.0

    def test_dsr_none_on_short_returns(self):
        dsr = compute_dsr(np.array([0.01]), 1.0, n_trials=10)
        assert dsr is None
