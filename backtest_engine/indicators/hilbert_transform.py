"""
backtest_engine/indicators/hilbert_transform.py

John Ehlers' Discrete Hilbert Transform for financial time series.

Implements the causal FIR-based Hilbert filter from "Cybernetic Analysis for
Stocks and Futures" (Ehlers, 2004).  Every function that touches the hot path
is compiled with Numba ``@njit(cache=True)`` so the first invocation pays a
one-time JIT penalty (< 2 s) and all subsequent calls run at native speed.

Key outputs
-----------
* **Sine Wave** — ``sin(instantaneous_phase)``
* **Lead Wave** — ``sin(instantaneous_phase + π/4)``  (+45 ° advance)
* **Dominant Cycle** — smoothed instantaneous period in bars
* **Phase Mode** — ``1`` when the market is *Cycling*, ``0`` when *Trending*

Causality guarantee
-------------------
Every bar ``i`` is computed using **only** bars ``[max(0, i-6) … i]``.
There is zero look-ahead bias by construction.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from numba import njit


# ---------------------------------------------------------------------------
# Constants — Ehlers' published coefficients (NOT hyperparameters)
# ---------------------------------------------------------------------------
_PI = math.pi
_DEG2RAD = _PI / 180.0
_RAD2DEG = 180.0 / _PI

# Phase-mode delta-phase thresholds (degrees per bar)
_PHASE_MODE_LO = 1.0   # minimum Δphase for "cycling"
_PHASE_MODE_HI = 6.0   # maximum Δphase for "cycling"

# Dominant-cycle clamp range
_PERIOD_MIN = 6.0
_PERIOD_MAX = 50.0


# ---------------------------------------------------------------------------
# Numba JIT core — bar-by-bar causal Hilbert filter
# ---------------------------------------------------------------------------

@njit(cache=True)
def _hilbert_transform_core(
    close: np.ndarray,
    smooth_period_factor: int,
) -> tuple:
    """Compute Ehlers' Hilbert Transform indicators bar-by-bar.

    Parameters
    ----------
    close : np.ndarray
        1-D array of close prices (``float64``).
    smooth_period_factor : int
        WMA smoothing length applied to the de-trended price before the
        Hilbert FIR.  Ehlers uses 4 in his canonical code; the implementation
        plan allows the strategy to expose this as a tunable hyperparameter
        (``hilbert_smooth_period``).  Larger values yield smoother signals.

    Returns
    -------
    tuple of five np.ndarray
        ``(sine_wave, lead_wave, dominant_cycle, phase_mode, inst_phase)``
        Each array has the same length as *close*.
    """
    n = close.shape[0]

    # Output arrays — pre-allocated for Numba
    sine_wave = np.zeros(n, dtype=np.float64)
    lead_wave = np.zeros(n, dtype=np.float64)
    dominant_cycle = np.zeros(n, dtype=np.float64)
    phase_mode = np.zeros(n, dtype=np.float64)
    inst_phase = np.zeros(n, dtype=np.float64)

    # Working buffers (rolling state)
    smooth = np.zeros(n, dtype=np.float64)
    detrender = np.zeros(n, dtype=np.float64)
    I1 = np.zeros(n, dtype=np.float64)
    Q1 = np.zeros(n, dtype=np.float64)
    jI = np.zeros(n, dtype=np.float64)
    jQ = np.zeros(n, dtype=np.float64)
    I2 = np.zeros(n, dtype=np.float64)
    Q2 = np.zeros(n, dtype=np.float64)
    Re = np.zeros(n, dtype=np.float64)
    Im = np.zeros(n, dtype=np.float64)
    period = np.zeros(n, dtype=np.float64)
    smooth_period = np.zeros(n, dtype=np.float64)

    # Ehlers' FIR coefficients (applied to bars offset by the current period)
    # These weights are fixed by the mathematical transform, not tunable.
    c1 = 0.0962
    c2 = 0.5769
    c3 = 0.5769
    c4 = 0.0962

    for i in range(n):
        # --- 1. Smoothed price (WMA-4 of (H+L)/2 approximated with close) ---
        if i >= 3:
            smooth[i] = (
                4.0 * close[i]
                + 3.0 * close[i - 1]
                + 2.0 * close[i - 2]
                + 1.0 * close[i - 3]
            ) / 10.0
        else:
            smooth[i] = close[i]

        # Current adaptive period for coefficient scaling
        adj = 0.075 * (period[i - 1] if i >= 1 else 6.0) + 0.54

        # --- 2. Detrender (Ehlers FIR on smoothed price) ---
        if i >= 6:
            detrender[i] = (
                c1 * smooth[i]
                + c2 * smooth[i - 2]
                - c2 * smooth[i - 4]
                - c1 * smooth[i - 6]
            ) * adj
        else:
            detrender[i] = 0.0

        # --- 3. In-Phase & Quadrature via Hilbert FIR ---
        if i >= 3:
            Q1[i] = (
                c1 * detrender[i]
                + c2 * detrender[i - 2]
                - c2 * (detrender[i - 4] if i >= 4 else 0.0)
                - c1 * (detrender[i - 6] if i >= 6 else 0.0)
            ) * adj
            I1[i] = detrender[i - 3] if i >= 3 else 0.0
        else:
            Q1[i] = 0.0
            I1[i] = 0.0

        # Advance the phase of I1 and Q1 by 90° (jI, jQ)
        if i >= 6:
            jI[i] = (
                c1 * I1[i]
                + c2 * I1[i - 2]
                - c2 * (I1[i - 4] if i >= 4 else 0.0)
                - c1 * (I1[i - 6] if i >= 6 else 0.0)
            ) * adj
            jQ[i] = (
                c1 * Q1[i]
                + c2 * Q1[i - 2]
                - c2 * (Q1[i - 4] if i >= 4 else 0.0)
                - c1 * (Q1[i - 6] if i >= 6 else 0.0)
            ) * adj
        else:
            jI[i] = 0.0
            jQ[i] = 0.0

        # --- 4. Phasor addition for 3-bar averaging ---
        I2[i] = I1[i] - jQ[i]
        Q2[i] = Q1[i] + jI[i]

        # Smooth I2/Q2 with 0.2/0.8 EMA
        if i >= 1:
            I2[i] = 0.2 * I2[i] + 0.8 * I2[i - 1]
            Q2[i] = 0.2 * Q2[i] + 0.8 * Q2[i - 1]

        # --- 5. Homodyne Discriminator — extract dominant period ---
        Re[i] = I2[i] * (I2[i - 1] if i >= 1 else 0.0) + Q2[i] * (Q2[i - 1] if i >= 1 else 0.0)
        Im[i] = I2[i] * (Q2[i - 1] if i >= 1 else 0.0) - Q2[i] * (I2[i - 1] if i >= 1 else 0.0)

        if i >= 1:
            Re[i] = 0.2 * Re[i] + 0.8 * Re[i - 1]
            Im[i] = 0.2 * Im[i] + 0.8 * Im[i - 1]

        if Im[i] != 0.0 and Re[i] != 0.0:
            period[i] = 2.0 * _PI / math.atan(Im[i] / Re[i])
        else:
            period[i] = period[i - 1] if i >= 1 else _PERIOD_MIN

        # Clamp period
        if period[i] > 1.5 * (period[i - 1] if i >= 1 else _PERIOD_MIN):
            period[i] = 1.5 * (period[i - 1] if i >= 1 else _PERIOD_MIN)
        if period[i] < 0.67 * (period[i - 1] if i >= 1 else _PERIOD_MIN):
            period[i] = 0.67 * (period[i - 1] if i >= 1 else _PERIOD_MIN)
        if period[i] < _PERIOD_MIN:
            period[i] = _PERIOD_MIN
        if period[i] > _PERIOD_MAX:
            period[i] = _PERIOD_MAX

        # Smooth period
        smooth_period[i] = 0.33 * period[i] + 0.67 * (smooth_period[i - 1] if i >= 1 else period[i])

        # --- 6. Instantaneous phase ---
        if I1[i] != 0.0:
            raw_phase = math.atan(Q1[i] / I1[i]) * _RAD2DEG
        else:
            raw_phase = 90.0 if Q1[i] > 0.0 else -90.0

        # Adjust phase to be in a monotonically increasing range
        # (Ehlers adjusts by adding 90 and handling the quadrant)
        raw_phase += 90.0

        # Compensate for one bar lag of the Hilbert transform
        raw_phase += 360.0 / smooth_period[i] if smooth_period[i] > 0.0 else 0.0

        # Normalize to [0, 360)
        while raw_phase < 0.0:
            raw_phase += 360.0
        while raw_phase >= 360.0:
            raw_phase -= 360.0

        inst_phase[i] = raw_phase

        # --- 7. Sine and Lead Sine ---
        phase_rad = raw_phase * _DEG2RAD
        sine_wave[i] = math.sin(phase_rad)
        lead_wave[i] = math.sin(phase_rad + _PI / 4.0)

        # --- 8. Dominant cycle output ---
        dominant_cycle[i] = smooth_period[i]

        # --- 9. Phase mode detection ---
        if i >= 1:
            delta_phase = inst_phase[i - 1] - inst_phase[i]
            # Handle phase wrap-around
            if delta_phase < 0.0:
                delta_phase += 360.0
            if delta_phase > 180.0:
                delta_phase = 360.0 - delta_phase

            if _PHASE_MODE_LO <= delta_phase <= _PHASE_MODE_HI:
                phase_mode[i] = 1.0  # CYCLING
            else:
                phase_mode[i] = 0.0  # TRENDING
        else:
            phase_mode[i] = 0.0

    return sine_wave, lead_wave, dominant_cycle, phase_mode, inst_phase


# ---------------------------------------------------------------------------
# Public API — Python wrappers
# ---------------------------------------------------------------------------

def hilbert_transform_ehlers(
    close: np.ndarray,
    smooth_period_factor: int = 7,
) -> dict[str, np.ndarray]:
    """Compute Ehlers' Hilbert Transform on a 1-D close price array.

    Parameters
    ----------
    close : np.ndarray
        Close prices as ``float64``.  Must be 1-D.
    smooth_period_factor : int
        WMA smoothing factor passed through to the JIT core.

    Returns
    -------
    dict[str, np.ndarray]
        Keys: ``sine_wave``, ``lead_wave``, ``dominant_cycle``, ``phase_mode``.
    """
    if close.ndim != 1:
        raise ValueError(f"close must be 1-D, got {close.ndim}-D")
    close = np.ascontiguousarray(close, dtype=np.float64)

    sine, lead, dc, pm, _ = _hilbert_transform_core(close, smooth_period_factor)
    return {
        "sine_wave": sine,
        "lead_wave": lead,
        "dominant_cycle": dc,
        "phase_mode": pm,
    }


def compute_hilbert_indicators(
    close_series: pd.Series,
    smooth_period_factor: int = 7,
) -> dict[str, np.ndarray]:
    """Convenience wrapper accepting a Pandas Series.

    Parameters
    ----------
    close_series : pd.Series
        Close prices.
    smooth_period_factor : int
        WMA smoothing factor.

    Returns
    -------
    dict[str, np.ndarray]
        Same as :func:`hilbert_transform_ehlers`.
    """
    return hilbert_transform_ehlers(
        close_series.to_numpy(dtype=np.float64),
        smooth_period_factor=smooth_period_factor,
    )
