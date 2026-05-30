"""
backtest_engine/bayesian_optimizer.py

Phase 4 — High-Performance Bayesian Optimization engine.

Wraps Optuna to explore the parameter space defined by ParameterGridSpec
objects, using a Tree-structured Parzen Estimator (TPE) sampler. Returns an
OptimizationSummary 100 % compatible with the rest of the pipeline (reports,
FastAPI jobs, recommendation engine).

Key architectural and performance design decisions:
---------------------------------------------------
* **Deadlock-Free Parallelism**: Fully supports concurrent multi-worker study runs
  (using ``workers > 1``) powered by a clean, spawn-based ProcessPoolExecutor,
  completely bypassing LLVM compiler forking deadlocks under Optuna and Numba.
* **POSIX Shared-Memory Grid Architecture**: To eliminate rolling/recursive calculations
  in parallel trial loops, the parent process pre-allocates continuous indicator grids in
  POSIX shared memory (`/dev/shm`) and shares them as zero-copy NumPy views across workers
  for all 7 strategies:
  1. HMA Crossover (Hull MA grids)
  2. PMax Explorer (moving average & ATR grids)
  3. Range Filter (smooth range & filter grids)
  4. Bjorgum Double Tap (ATR, pivots, and rolling min/max grids)
  5. Adaptive Volatility Trend (3D adaptive MA, ATR, and RSI grids)
  6. 3Commas Bot (multi-MA types, ATR, and stacked 3D lowest/highest swing grids)
  7. Noise Boundary Intraday (stacked 3D daily mapped volatility and standard deviation grids)
* **Unlinked Lifecycle Cleanup**: Avoids system-level memory leaks by unlinking and
  releasing all allocated POSIX shared memory segments in a `finally` block.
* **Pruning via early_stop_drawdown_pct**: trial evaluations abort early upon reaching
  drawdown limits, keeping evaluations extremely lightweight.
"""

from __future__ import annotations

import inspect
import json
import logging
import threading
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, TYPE_CHECKING
import psutil

import pandas as pd

from .data import BASE_TIMEFRAME_MINUTES, validate_timeframe_minutes
from .optimizer import (
    ParameterGridSpec,
    OptimizationProgress,
    OptimizationSummary,
    OptimizationConstraints,
    ScoreDirection,
    _evaluate_hma_parameters,
    _is_better,
    _json_dump,
    _merged_strategy_overrides,
    _write_results,
    create_optimization_output_dir,
    validate_hma_overrides,
    validate_score_metric,
    _evaluate_worker,
    _init_worker
)
from .report_interpreter import write_optimization_recommendations
from .reports import write_backtest_outputs, write_optimizer_reports
from .strategy_registry import StrategyRegistry

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# High-Speed Multi-Processing Worker Context with Shared Memory
# ---------------------------------------------------------------------------

_WORKER_DATA: pd.DataFrame | None = None
_WORKER_SYMBOL: str | None = None
_WORKER_FIXED_OVERRIDES: Any | None = None
_WORKER_INITIAL_CAPITAL: float = 1000.0
_WORKER_STRATEGY: str = "hma_crossover"
_WORKER_SCORE_METRIC: str = "sharpe_ratio"
_WORKER_MIN_CLOSED_TRADES: int = 1
_WORKER_TIMEFRAME_MINUTES: int | str = 5
_WORKER_EARLY_STOP_DRAWDOWN_PCT: float | None = None
_WORKER_WFO_WINDOWS: int = 1
_WORKER_REPO_ROOT: Path | None = None
_WORKER_CONSTRAINTS: Any | None = None


def _get_dynamic_memory_limit() -> int:
    """Returns 30% of currently available system memory in bytes, minimum 500MB."""
    available = psutil.virtual_memory().available
    dynamic_limit = int(available * 0.30)
    return max(dynamic_limit, 500 * 1024 * 1024)

def share_dataframe(df: pd.DataFrame) -> tuple[dict, list[Any]]:
    """
    Creates SharedIndicatorVolume segments for each column of the DataFrame
    plus its index, returning a dict of metadata to pass to workers.

    Safe for non-numeric/object columns (like 'symbol') by serializing them directly in
    metadata to completely avoid parent-process memory pointer sharing (which triggers SIGSEGV
    under concurrent multiprocessing worker spawn method).
    """
    from .shared_memory import SharedIndicatorVolume
    import numpy as np

    metadata = {}
    shm_objects = []

    # Save index (as int64 array of nanoseconds)
    idx_arr = df.index.values.astype(np.int64)
    idx_shm = SharedIndicatorVolume(array_to_share=idx_arr)
    metadata["index"] = {
        "shm_name": idx_shm.shm_name,
        "shape": idx_shm.shape,
        "dtype": str(idx_shm.dtype)
    }
    shm_objects.append(idx_shm)

    # Save columns
    metadata["columns"] = {}
    for col in df.columns:
        if df[col].dtype == object:
            # Handle object/string columns safely (avoiding shared memory pointer crashes)
            unique_vals = df[col].unique()
            if len(unique_vals) == 1:
                metadata["columns"][col] = {
                    "kind": "constant",
                    "value": unique_vals[0],
                    "length": len(df)
                }
            else:
                metadata["columns"][col] = {
                    "kind": "serialized",
                    "values": df[col].tolist()
                }
        else:
            col_arr = df[col].to_numpy()
            col_shm = SharedIndicatorVolume(array_to_share=col_arr)
            metadata["columns"][col] = {
                "kind": "shm",
                "shm_name": col_shm.shm_name,
                "shape": col_shm.shape,
                "dtype": str(col_shm.dtype)
            }
            shm_objects.append(col_shm)

    return metadata, shm_objects


def rebuild_dataframe(metadata: dict) -> tuple[pd.DataFrame, list[Any]]:
    """
    Reconstructs a pd.DataFrame with zero-copy numpy views from shared memory metadata.
    Returns the DataFrame and the list of SharedIndicatorVolume objects to keep them alive.
    """
    from .shared_memory import SharedIndicatorVolume
    import pandas as pd
    import numpy as np

    shm_objects = []

    # Attach to index
    idx_meta = metadata["index"]
    idx_vol = SharedIndicatorVolume(
        shm_name=idx_meta["shm_name"],
        shape=idx_meta["shape"],
        dtype=np.dtype(idx_meta["dtype"])
    )
    shm_objects.append(idx_vol)
    idx_arr = idx_vol.get_view()
    index = pd.to_datetime(idx_arr)

    # Attach to columns
    cols_data = {}
    for col, col_meta in metadata["columns"].items():
        kind = col_meta.get("kind", "shm")  # Backwards compatibility
        if kind == "shm":
            shm_name = col_meta.get("shm_name")
            shape = col_meta.get("shape")
            dtype = np.dtype(col_meta.get("dtype"))
            col_vol = SharedIndicatorVolume(
                shm_name=shm_name,
                shape=shape,
                dtype=dtype
            )
            shm_objects.append(col_vol)
            cols_data[col] = col_vol.get_view()
        elif kind == "constant":
            val = col_meta["value"]
            length = col_meta["length"]
            cols_data[col] = np.full(length, val, dtype=object)
        elif kind == "serialized":
            cols_data[col] = np.array(col_meta["values"], dtype=object)

    return pd.DataFrame(cols_data, index=index), shm_objects


_WORKER_SHM_VOLUMES: list = []


def _init_worker_bayesian(
    shm_metadata: dict,
    symbol: str,
    fixed_overrides: Any | None,
    initial_capital: float,
    strategy: str,
    score_metric: str,
    min_closed_trades: int,
    timeframe_minutes: int | str,
    early_stop_drawdown_pct: float | None = None,
    wfo_windows: int = 1,
    repo_root: Path | None = None,
    constraints: Any | None = None,
    hma_shm_metadata: dict | None = None,
    pmax_shm_metadata: dict | None = None,
    rf_shm_metadata: dict | None = None,
    bjorgum_shm_metadata: dict | None = None,
    avt_shm_metadata: dict | None = None,
    commas_bot_shm_metadata: dict | None = None,
    noise_boundary_shm_metadata: dict | None = None,
) -> None:
    global _WORKER_DATA, _WORKER_SYMBOL, _WORKER_FIXED_OVERRIDES, _WORKER_INITIAL_CAPITAL
    global _WORKER_STRATEGY, _WORKER_SCORE_METRIC, _WORKER_MIN_CLOSED_TRADES, _WORKER_TIMEFRAME_MINUTES
    global _WORKER_EARLY_STOP_DRAWDOWN_PCT, _WORKER_WFO_WINDOWS, _WORKER_REPO_ROOT, _WORKER_CONSTRAINTS
    global _WORKER_SHM_VOLUMES

    try:
        # Keep global references to prevent garbage collection and unmapping of shared memory in workers
        _WORKER_SHM_VOLUMES = []

        # Reconstruct DataFrame locally from shared memory zero-copy views
        _WORKER_DATA, shm_objs = rebuild_dataframe(shm_metadata)
        _WORKER_SHM_VOLUMES.extend(shm_objs)

        _WORKER_SYMBOL = symbol
        _WORKER_FIXED_OVERRIDES = fixed_overrides
        _WORKER_INITIAL_CAPITAL = initial_capital
        _WORKER_STRATEGY = strategy
        _WORKER_SCORE_METRIC = score_metric
        _WORKER_MIN_CLOSED_TRADES = min_closed_trades
        _WORKER_TIMEFRAME_MINUTES = timeframe_minutes
        _WORKER_EARLY_STOP_DRAWDOWN_PCT = early_stop_drawdown_pct
        _WORKER_WFO_WINDOWS = wfo_windows
        _WORKER_REPO_ROOT = repo_root
        _WORKER_CONSTRAINTS = constraints

        # Reset strategy-specific feature cache
        info = StrategyRegistry.get(strategy)
        if info.clear_feature_cache is not None:
            info.clear_feature_cache()

        # Mount shared HMA grid if available
        if hma_shm_metadata is not None:
            from .shared_memory import SharedIndicatorVolume
            import numpy as np

            # Attach to the shared HMA grid volume
            hma_vol = SharedIndicatorVolume(
                shm_name=hma_shm_metadata["shm_name"],
                shape=hma_shm_metadata["shape"],
                dtype=np.dtype(hma_shm_metadata["dtype"])
            )
            _WORKER_SHM_VOLUMES.append(hma_vol)
            grid_view = hma_vol.get_view()

            # Reset HMA module lock to prevent deadlock inherited from parent thread fork
            import backtest_engine.strategies.hma_crossover as hc
            import threading
            hc._HMA_MODULE_LOCK = threading.Lock()

            # Mount onto the dynamically loaded strategy module
            from .strategies.hma_crossover import _load_strategy_module
            try:
                strategy_mod = _load_strategy_module()
                strategy_mod._SHARED_HMA_GRID = grid_view
                strategy_mod._SHARED_HMA_LENGTH_TO_IDX = hma_shm_metadata["length_to_idx"]
            except Exception as e:
                logger.warning(f"Failed to mount shared HMA grid onto strategy module: {e}")

        # Mount shared PMax grids if available
        if pmax_shm_metadata is not None:
            from .shared_memory import SharedIndicatorVolume
            import numpy as np

            # Attach to MAvg grid
            mavg_vol = SharedIndicatorVolume(
                shm_name=pmax_shm_metadata["mavg_shm_name"],
                shape=pmax_shm_metadata["mavg_shape"],
                dtype=np.dtype(pmax_shm_metadata["mavg_dtype"])
            )
            _WORKER_SHM_VOLUMES.append(mavg_vol)
            mavg_grid_view = mavg_vol.get_view()

            # Attach to ATR grid
            atr_vol = SharedIndicatorVolume(
                shm_name=pmax_shm_metadata["atr_shm_name"],
                shape=pmax_shm_metadata["atr_shape"],
                dtype=np.dtype(pmax_shm_metadata["atr_dtype"])
            )
            _WORKER_SHM_VOLUMES.append(atr_vol)
            atr_grid_view = atr_vol.get_view()

            # Reset lock and mount onto the dynamically loaded strategy module
            import backtest_engine.strategies.pmax_explorer as pmax_mod_wrapper
            import threading
            pmax_mod_wrapper._PMAX_MODULE_LOCK = threading.Lock()

            from .strategies.pmax_explorer import _load_strategy_module
            try:
                strategy_mod = _load_strategy_module()
                strategy_mod._SHARED_PMAX_MAVG_GRID = mavg_grid_view
                strategy_mod._SHARED_PMAX_MAVG_KEYS = pmax_shm_metadata["mavg_keys"]
                strategy_mod._SHARED_PMAX_ATR_GRID = atr_grid_view
                strategy_mod._SHARED_PMAX_ATR_KEYS = pmax_shm_metadata["atr_keys"]
            except Exception as e:
                logger.warning(f"Failed to mount shared PMax grids onto strategy module: {e}")

        # Mount shared Range Filter grids if available
        if rf_shm_metadata is not None:
            from .shared_memory import SharedIndicatorVolume
            import numpy as np

            # Attach to smrng grid
            smrng_vol = SharedIndicatorVolume(
                shm_name=rf_shm_metadata["smrng_shm_name"],
                shape=rf_shm_metadata["smrng_shape"],
                dtype=np.dtype(rf_shm_metadata["smrng_dtype"])
            )
            _WORKER_SHM_VOLUMES.append(smrng_vol)
            smrng_grid_view = smrng_vol.get_view()

            # Attach to filt grid
            filt_vol = SharedIndicatorVolume(
                shm_name=rf_shm_metadata["filt_shm_name"],
                shape=rf_shm_metadata["filt_shape"],
                dtype=np.dtype(rf_shm_metadata["filt_dtype"])
            )
            _WORKER_SHM_VOLUMES.append(filt_vol)
            filt_grid_view = filt_vol.get_view()

            # Reset lock and mount onto the dynamically loaded strategy module
            import backtest_engine.strategies.range_filter as rf_mod_wrapper
            import threading
            rf_mod_wrapper._RF_MODULE_LOCK = threading.Lock()

            from .strategies.range_filter import _load_strategy_module
            try:
                strategy_mod = _load_strategy_module()
                strategy_mod._SHARED_RF_SMRNG_GRID = smrng_grid_view
                strategy_mod._SHARED_RF_GRID = filt_grid_view
                strategy_mod._SHARED_RF_KEYS = rf_shm_metadata["rf_keys"]
            except Exception as e:
                logger.warning(f"Failed to mount shared Range Filter grids onto strategy module: {e}")

        # Mount shared Bjorgum Double Tap grids if available
        if bjorgum_shm_metadata is not None:
            from .shared_memory import SharedIndicatorVolume
            import numpy as np

            # Attach to ATR grid
            atr_vol = SharedIndicatorVolume(
                shm_name=bjorgum_shm_metadata["atr_shm_name"],
                shape=bjorgum_shm_metadata["atr_shape"],
                dtype=np.dtype(bjorgum_shm_metadata["atr_dtype"])
            )
            _WORKER_SHM_VOLUMES.append(atr_vol)
            atr_grid_view = atr_vol.get_view()

            # Attach to piv_high grid
            piv_high_vol = SharedIndicatorVolume(
                shm_name=bjorgum_shm_metadata["piv_high_shm_name"],
                shape=bjorgum_shm_metadata["piv_high_shape"],
                dtype=np.dtype(bjorgum_shm_metadata["piv_high_dtype"])
            )
            _WORKER_SHM_VOLUMES.append(piv_high_vol)
            piv_high_grid_view = piv_high_vol.get_view()

            # Attach to piv_low grid
            piv_low_vol = SharedIndicatorVolume(
                shm_name=bjorgum_shm_metadata["piv_low_shm_name"],
                shape=bjorgum_shm_metadata["piv_low_shape"],
                dtype=np.dtype(bjorgum_shm_metadata["piv_low_dtype"])
            )
            _WORKER_SHM_VOLUMES.append(piv_low_vol)
            piv_low_grid_view = piv_low_vol.get_view()

            # Attach to roll_min grid
            roll_min_vol = SharedIndicatorVolume(
                shm_name=bjorgum_shm_metadata["roll_min_shm_name"],
                shape=bjorgum_shm_metadata["roll_min_shape"],
                dtype=np.dtype(bjorgum_shm_metadata["roll_min_dtype"])
            )
            _WORKER_SHM_VOLUMES.append(roll_min_vol)
            roll_min_grid_view = roll_min_vol.get_view()

            # Attach to roll_max grid
            roll_max_vol = SharedIndicatorVolume(
                shm_name=bjorgum_shm_metadata["roll_max_shm_name"],
                shape=bjorgum_shm_metadata["roll_max_shape"],
                dtype=np.dtype(bjorgum_shm_metadata["roll_max_dtype"])
            )
            _WORKER_SHM_VOLUMES.append(roll_max_vol)
            roll_max_grid_view = roll_max_vol.get_view()

            # Reset lock and mount onto the dynamically loaded strategy module
            import backtest_engine.strategies.bjorgum_double_tap as bj_mod_wrapper
            import threading
            bj_mod_wrapper._MODULE_LOCK = threading.Lock()

            from .strategies.bjorgum_double_tap import _load_strategy_module
            try:
                strategy_mod = _load_strategy_module()
                strategy_mod._SHARED_BJ_ATR_GRID = atr_grid_view
                strategy_mod._SHARED_BJ_ATR_KEYS = bjorgum_shm_metadata["atr_keys"]
                strategy_mod._SHARED_BJ_PIV_HIGH_GRID = piv_high_grid_view
                strategy_mod._SHARED_BJ_PIV_HIGH_KEYS = bjorgum_shm_metadata["piv_high_keys"]
                strategy_mod._SHARED_BJ_PIV_LOW_GRID = piv_low_grid_view
                strategy_mod._SHARED_BJ_PIV_LOW_KEYS = bjorgum_shm_metadata["piv_low_keys"]
                strategy_mod._SHARED_BJ_ROLL_MIN_GRID = roll_min_grid_view
                strategy_mod._SHARED_BJ_ROLL_MIN_KEYS = bjorgum_shm_metadata["roll_min_keys"]
                strategy_mod._SHARED_BJ_ROLL_MAX_GRID = roll_max_grid_view
                strategy_mod._SHARED_BJ_ROLL_MAX_KEYS = bjorgum_shm_metadata["roll_max_keys"]
            except Exception as e:
                logger.warning(f"Failed to mount shared Bjorgum Double Tap grids onto strategy module: {e}")

        # Mount shared Adaptive Volatility Trend grids if available
        if avt_shm_metadata is not None:
            from .shared_memory import SharedIndicatorVolume
            import numpy as np

            # Attach to AMA grid
            ama_vol = SharedIndicatorVolume(
                shm_name=avt_shm_metadata["ama_shm_name"],
                shape=avt_shm_metadata["ama_shape"],
                dtype=np.dtype(avt_shm_metadata["ama_dtype"])
            )
            _WORKER_SHM_VOLUMES.append(ama_vol)
            ama_grid_view = ama_vol.get_view()

            # Attach to ATR grid
            atr_vol = SharedIndicatorVolume(
                shm_name=avt_shm_metadata["atr_shm_name"],
                shape=avt_shm_metadata["atr_shape"],
                dtype=np.dtype(avt_shm_metadata["atr_dtype"])
            )
            _WORKER_SHM_VOLUMES.append(atr_vol)
            atr_grid_view = atr_vol.get_view()

            # Attach to RSI grid
            rsi_vol = SharedIndicatorVolume(
                shm_name=avt_shm_metadata["rsi_shm_name"],
                shape=avt_shm_metadata["rsi_shape"],
                dtype=np.dtype(avt_shm_metadata["rsi_dtype"])
            )
            _WORKER_SHM_VOLUMES.append(rsi_vol)
            rsi_grid_view = rsi_vol.get_view()

            # Reset lock and mount onto the dynamically loaded strategy module
            import backtest_engine.strategies.adaptive_volatility_trend as avt_mod_wrapper
            import threading
            avt_mod_wrapper._MODULE_LOCK = threading.Lock()

            from .strategies.adaptive_volatility_trend import _load_strategy_module
            try:
                strategy_mod = _load_strategy_module()
                strategy_mod._SHARED_AVT_AMA_GRID = ama_grid_view
                strategy_mod._SHARED_AVT_AMA_KEYS = avt_shm_metadata["ama_keys"]
                strategy_mod._SHARED_AVT_ATR_GRID = atr_grid_view
                strategy_mod._SHARED_AVT_ATR_KEYS = avt_shm_metadata["atr_keys"]
                strategy_mod._SHARED_AVT_RSI_GRID = rsi_grid_view
                strategy_mod._SHARED_AVT_RSI_KEYS = avt_shm_metadata["rsi_keys"]
            except Exception as e:
                logger.warning(f"Failed to mount shared Adaptive Volatility Trend grids onto strategy module: {e}")
            # Mount shared commas_bot grids if available
            if commas_bot_shm_metadata is not None:
                from .shared_memory import SharedIndicatorVolume
                import numpy as np

                # Attach to MA grid
                ma_vol = SharedIndicatorVolume(
                    shm_name=commas_bot_shm_metadata["ma_shm_name"],
                    shape=commas_bot_shm_metadata["ma_shape"],
                    dtype=np.dtype(commas_bot_shm_metadata["ma_dtype"])
                )
                _WORKER_SHM_VOLUMES.append(ma_vol)
                ma_grid_view = ma_vol.get_view()

                # Attach to ATR grid
                atr_vol = SharedIndicatorVolume(
                    shm_name=commas_bot_shm_metadata["atr_shm_name"],
                    shape=commas_bot_shm_metadata["atr_shape"],
                    dtype=np.dtype(commas_bot_shm_metadata["atr_dtype"])
                )
                _WORKER_SHM_VOLUMES.append(atr_vol)
                atr_grid_view = atr_vol.get_view()

                # Attach to Swing grid
                swing_vol = SharedIndicatorVolume(
                    shm_name=commas_bot_shm_metadata["swing_shm_name"],
                    shape=commas_bot_shm_metadata["swing_shape"],
                    dtype=np.dtype(commas_bot_shm_metadata["swing_dtype"])
                )
                _WORKER_SHM_VOLUMES.append(swing_vol)
                swing_grid_view = swing_vol.get_view()

                # Reset lock and mount onto the dynamically loaded strategy module
                import backtest_engine.strategies.commas_bot as commas_mod_wrapper
                import threading
                commas_mod_wrapper._MODULE_LOCK = threading.Lock()

                from .strategies.commas_bot import _load_strategy_module
                try:
                    strategy_mod = _load_strategy_module()
                    strategy_mod._SHARED_CB_MA_GRID = ma_grid_view
                    strategy_mod._SHARED_CB_MA_KEYS = commas_bot_shm_metadata["ma_keys"]
                    strategy_mod._SHARED_CB_ATR_GRID = atr_grid_view
                    strategy_mod._SHARED_CB_ATR_KEYS = commas_bot_shm_metadata["atr_keys"]
                    strategy_mod._SHARED_CB_SWING_GRID = swing_grid_view
                    strategy_mod._SHARED_CB_SWING_KEYS = commas_bot_shm_metadata["swing_keys"]
                except Exception as e:
                    logger.warning(f"Failed to mount shared 3Commas Bot grids onto strategy module: {e}")

            # Mount shared Noise Boundary grids if available
            if noise_boundary_shm_metadata is not None:
                from .shared_memory import SharedIndicatorVolume
                import numpy as np

                # Attach to Vol grid
                vol_vol = SharedIndicatorVolume(
                    shm_name=noise_boundary_shm_metadata["vol_shm_name"],
                    shape=noise_boundary_shm_metadata["vol_shape"],
                    dtype=np.dtype(noise_boundary_shm_metadata["vol_dtype"])
                )
                _WORKER_SHM_VOLUMES.append(vol_vol)
                vol_grid_view = vol_vol.get_view()

                import backtest_engine.strategies.noise_boundary_intraday as nb_mod
                try:
                    nb_mod._SHARED_NB_VOL_GRID = vol_grid_view
                    nb_mod._SHARED_NB_VOL_KEYS = noise_boundary_shm_metadata["vol_keys"]
                except Exception as e:
                    logger.warning(f"Failed to mount shared Noise Boundary grids onto strategy module: {e}")

    except Exception as exc:
        import traceback, sys
        print(f"FATAL EXCEPTION IN WORKER INITIALIZER: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise


def _evaluate_worker_bayesian(payload: tuple[int, dict[str, object]]) -> tuple[dict, bool, bool]:
    try:
        iteration, parameters = payload
        if _WORKER_DATA is None or _WORKER_SYMBOL is None:
            raise RuntimeError("Optimizer worker was not initialized")
        return _evaluate_hma_parameters(
            data=_WORKER_DATA,
            symbol=_WORKER_SYMBOL,
            parameters=parameters,
            iteration=iteration,
            fixed_overrides=_WORKER_FIXED_OVERRIDES,
            initial_capital=_WORKER_INITIAL_CAPITAL,
            strategy=_WORKER_STRATEGY,
            score_metric=_WORKER_SCORE_METRIC,
            min_closed_trades=_WORKER_MIN_CLOSED_TRADES,
            timeframe_minutes=_WORKER_TIMEFRAME_MINUTES,
            early_stop_drawdown_pct=_WORKER_EARLY_STOP_DRAWDOWN_PCT,
            wfo_windows=_WORKER_WFO_WINDOWS,
            repo_root=_WORKER_REPO_ROOT,
            constraints=_WORKER_CONSTRAINTS,
        )
    except Exception as exc:
        import traceback, sys
        print(f"FATAL EXCEPTION IN WORKER EVALUATOR: {exc}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise


# ---------------------------------------------------------------------------
# Helpers — translate ParameterGridSpec ↔ Optuna search space
# ---------------------------------------------------------------------------

def validate_noise_boundary_constraints(params: dict[str, object]) -> bool:
    """Filter invalid parameter combinations for noise_boundary_intraday."""
    if "volatility_multiplier_enter" in params and "volatility_multiplier_exit" in params:
        if params["volatility_multiplier_exit"] >= params["volatility_multiplier_enter"]:
            return False
    if "stoploss_ladder_step0" in params and "stoploss_ladder_step1" in params:
        if params["stoploss_ladder_step1"] >= params["stoploss_ladder_step0"]:
            return False
    if "takeprofit_ladder_step0" in params and "stoploss_ladder_step0" in params:
        if params["takeprofit_ladder_step0"] <= params["stoploss_ladder_step0"]:
            return False
    return True

def _suggest_parameters(
    trial: object,  # optuna.Trial — typed loosely to avoid hard import at module level
    parameter_specs: list[ParameterGridSpec],
    strategy: str = "hma_crossover",
) -> dict[str, object]:
    """Ask Optuna to suggest one value per parameter spec.

    Numeric specs with integer value_type use ``suggest_int``; float specs use
    ``suggest_float`` with the grid step as the quantisation hint.  Choice and
    bool specs map to ``suggest_categorical``.
    """
    from .configuration import parameter_definitions
    from decimal import Decimal

    defs = parameter_definitions(strategy)
    params: dict[str, object] = {}

    def sort_key(spec: ParameterGridSpec) -> int:
        if spec.name == "volatility_multiplier_enter": return 0
        if spec.name == "volatility_multiplier_exit": return 1
        if spec.name == "stoploss_ladder_step0": return 0
        if spec.name == "stoploss_ladder_step1": return 1
        return 2

    sorted_specs = sorted(parameter_specs, key=sort_key)

    for spec in sorted_specs:
        name = spec.name
        pdef = defs.get(name)
        values = list(spec.values)

        if not values:
            continue

        if spec.kind in ("choice", "bool"):
            # Categorical — Optuna picks from the discrete set
            params[name] = trial.suggest_categorical(name, values)

        elif spec.kind == "numeric":
            vtype = pdef.value_type if pdef else "float"
            low = values[0]
            high = values[-1]

            if vtype == "int":
                # Derive step from the grid values
                step = int(values[1]) - int(values[0]) if len(values) > 1 else 1
                params[name] = trial.suggest_int(name, int(low), int(high), step=step)
            else:
                # Float — use log=False, step derived from grid
                step = float(values[1]) - float(values[0]) if len(values) > 1 else None
                if step is not None:
                    step = round(step, 10)
                    # Infer decimal places from the rounded step to sanitize low/high
                    ndigits = max(0, int(-Decimal(str(step)).as_tuple().exponent))
                    low = round(float(low), ndigits)
                    high = round(float(high), ndigits)
                    # Defensive: force the range to be an exact multiple of step using Decimal
                    low_dec = Decimal(str(low))
                    high_dec = Decimal(str(high))
                    step_dec = Decimal(str(step))
                    n_steps = int((high_dec - low_dec) / step_dec)
                    high = float(low_dec + n_steps * step_dec)
                
                if strategy == "noise_boundary_intraday":
                    if name == "volatility_multiplier_exit" and "volatility_multiplier_enter" in params:
                        enter_val = float(params["volatility_multiplier_enter"])
                        diff = trial.suggest_float(f"{name}_diff", 0.1, 0.9, step=0.1)
                        exit_val = enter_val * (1 - diff)
                        params[name] = max(float(low), min(float(high), exit_val))
                        continue
                    elif name == "stoploss_ladder_step1" and "stoploss_ladder_step0" in params:
                        step0_val = float(params["stoploss_ladder_step0"])
                        offset = trial.suggest_float(f"{name}_offset", 0.001, 0.020, step=0.001)
                        step1_val = step0_val - offset
                        params[name] = max(float(low), min(float(high), step1_val))
                        continue

                params[name] = trial.suggest_float(name, float(low), float(high), step=step)

    return params


# ---------------------------------------------------------------------------
# Convergence tracking for early stopping
# ---------------------------------------------------------------------------

class ConvergenceTracker:
    """Tracks optimization progress and detects convergence for early stopping.

    Stops when:
    1. No improvement for `patience` consecutive iterations
    2. No significant improvement (> min_relative_improvement) for `window_count` consecutive windows
    3. The global circuit breaker triggers (total iterations since last improvement exceeds ratio of budget)
    """

    def __init__(
        self,
        score_direction: ScoreDirection,
        patience: int = 100,
        min_relative_improvement: float = 0.01,
        window_size: int = 50,
        window_count: int = 3,
        n_trials: int = 0,
        circuit_breaker_ratio: float = 0.2,
    ):
        self.score_direction = score_direction
        self.patience = patience
        self.min_relative_improvement = min_relative_improvement
        self.window_size = window_size
        self.window_count = window_count
        self.n_trials = n_trials
        self.circuit_breaker_ratio = circuit_breaker_ratio

        self.best_score: float | None = None
        self.iterations_since_improvement = 0
        self.total_iterations_since_improvement = 0
        self.scores_window: list[float] = []
        self.windows_without_improvement = 0
        self.last_window_best: float | None = None
        self.total_iterations = 0

    def _check_circuit_breaker(self) -> bool:
        """Return True if total iterations since improvement exceeds threshold while patience is not met."""
        threshold = self.n_trials * self.circuit_breaker_ratio
        return (self.total_iterations_since_improvement >= threshold) and (self.iterations_since_improvement < self.patience)

    def update(self, score: float | None) -> tuple[bool, str]:
        """Update tracker with new score. Returns (should_stop, reason)."""
        self.total_iterations += 1
        self.total_iterations_since_improvement += 1

        # Check circuit breaker before potential early exit due to None score
        if self._check_circuit_breaker():
            logger.info(
                f"Circuit breaker triggered: no improvement for {self.total_iterations_since_improvement} "
                f"total iterations (threshold: {self.n_trials * self.circuit_breaker_ratio:.1f})"
            )
            return True, "circuit_breaker"

        if score is None:
            return False, ""

        # Check for absolute improvement
        is_better = _is_better(score, self.best_score, self.score_direction)
        if is_better:
            self.best_score = score
            self.iterations_since_improvement = 0
            self.total_iterations_since_improvement = 0
        else:
            self.iterations_since_improvement += 1

        # Add to current window
        self.scores_window.append(score)

        # Check window-based convergence
        if len(self.scores_window) >= self.window_size:
            window_best = max(self.scores_window) if self.score_direction == "max" else min(self.scores_window)

            if self.last_window_best is not None and self.best_score is not None:
                # Check if we had significant improvement relative to best
                if self.score_direction == "max":
                    relative_improvement = (self.best_score - self.last_window_best) / abs(self.last_window_best) if self.last_window_best != 0 else float('inf')
                else:
                    relative_improvement = (self.last_window_best - self.best_score) / abs(self.last_window_best) if self.last_window_best != 0 else float('inf')

                if relative_improvement < self.min_relative_improvement:
                    self.windows_without_improvement += 1
                else:
                    self.windows_without_improvement = 0
            else:
                self.windows_without_improvement = 0

            self.last_window_best = window_best
            self.scores_window = []

        # Check stopping criteria
        if self.iterations_since_improvement >= self.patience:
            logger.info(f"Early stopping: no improvement for {self.patience} iterations")
            return True, "patience"

        if self.windows_without_improvement >= self.window_count:
            logger.info(f"Early stopping: no significant improvement for {self.window_count} consecutive windows")
            return True, "window"

        # Re-check circuit breaker after updates (defensive)
        if self._check_circuit_breaker():
            logger.info(
                f"Circuit breaker triggered: no improvement for {self.total_iterations_since_improvement} "
                f"total iterations (threshold: {self.n_trials * self.circuit_breaker_ratio:.1f})"
            )
            return True, "circuit_breaker"

        return False, ""

    def get_status(self) -> dict:
        """Return current convergence status for logging/debugging."""
        return {
            "iterations_since_improvement": self.iterations_since_improvement,
            "total_iterations_since_improvement": self.total_iterations_since_improvement,
            "circuit_breaker_threshold": self.n_trials * self.circuit_breaker_ratio,
            "windows_without_improvement": self.windows_without_improvement,
            "best_score": self.best_score,
            "current_window_size": len(self.scores_window),
        }


# ---------------------------------------------------------------------------
# Core Bayesian optimization loop
# ---------------------------------------------------------------------------

def run_bayesian_optimization(
    *,
    data: pd.DataFrame,
    symbol: str,
    parameter_specs: list[ParameterGridSpec],
    fixed_overrides: Any | None = None,
    initial_capital: float = 1000.0,
    output_root: Path | None = None,
    timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES,
    start_date: str | None = None,
    end_date: str | None = None,
    strategy: str = "hma_crossover",
    score_metric: str = "sharpe_ratio",
    score_direction: ScoreDirection = "max",
    secondary_score_metric: str | None = None,
    secondary_score_direction: ScoreDirection = "max",
    n_trials: int = 200,
    min_closed_trades: int = 1,
    workers: int = 1,
    write_best_run: bool = True,
    progress_callback: Callable[[OptimizationProgress], None] | None = None,
    stop_requested: Callable[[], bool] | None = None,
    early_stop_drawdown_pct: float | None = None,
    seed: int | None = 42,
    enable_convergence_stop: bool = True,
    convergence_patience: int = 100,
    convergence_min_improvement: float = 0.01,
    convergence_window_size: int = 50,
    convergence_window_count: int = 3,
    circuit_breaker_ratio: float = 0.2,
    wfo_windows: int = 1,
    use_vectorbt_prescan: bool = False,
    run_post_validation: bool = False,
    repo_root: Path | None = None,
    prescan_progress_callback: Callable[[int, int], None] | None = None,
    constraints: OptimizationConstraints | None = None,
    job_id: str | None = None,
) -> OptimizationSummary:
    """Run Bayesian hyperparameter search with Optuna TPE.

    Parameters
    ----------
    n_trials:
        Total number of Optuna trials (≈ function evaluations).  Replaces
        ``max_iterations`` from the grid-search API.
    seed:
        Random seed for Optuna's sampler — guarantees reproducibility.
        Pass ``None`` for a future random run.
    enable_convergence_stop:
        If True, stop early when convergence is detected (no improvement).
    convergence_patience:
        Stop if no improvement for this many consecutive iterations.
    convergence_min_improvement:
        Minimum relative improvement (e.g., 0.01 = 1%) to consider significant.
    convergence_window_size:
        Size of each window for window-based convergence check.
    convergence_window_count:
        Stop after this many consecutive windows without significant improvement.
    circuit_breaker_ratio:
        Ratio of n_trials without improvement to trigger circuit breaker.
    All other parameters mirror ``run_grid_optimization()`` exactly.
    """
    if output_root is None:
        from .paths import get_reports_dir
        output_root = get_reports_dir() / "local_optimizer"
    try:
        import optuna
        from optuna.storages import JournalStorage
        try:
            from optuna.storages import JournalFileStorage
        except ImportError:
            from optuna.storages.journal import JournalFileBackend as JournalFileStorage
    except ImportError as exc:
        raise ImportError(
            "Bayesian optimization requires 'optuna'. "
            "Install it with: pip install optuna"
        ) from exc

    # Silence Optuna's chatty INFO logs — only WARNING+ is useful in prod
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    score_metric = validate_score_metric(score_metric, strategy=strategy)
    minutes = validate_timeframe_minutes(timeframe_minutes)

    if strategy == "noise_boundary_intraday" and min_closed_trades == 1:
        min_closed_trades = 30

    if strategy not in StrategyRegistry.list_strategies():
        raise ValueError(f"Unsupported strategy for Bayesian optimization: {strategy}")
    if n_trials < 1:
        raise ValueError("n_trials must be >= 1")
    if min_closed_trades < 0:
        raise ValueError("min_closed_trades must be >= 0")
    constraints = constraints or OptimizationConstraints()

    output_dir = create_optimization_output_dir(output_root, strategy, symbol, job_id=job_id)
    optimization_config = {
        "strategy": strategy,
        "symbol": symbol,
        "timeframe_minutes": minutes,
        "start_date": start_date,
        "end_date": end_date,
        "score_metric": score_metric,
        "score_direction": score_direction,
        "n_trials": n_trials,
        "optimization_mode": "bayesian",
        "min_closed_trades": min_closed_trades,
        "constraints": asdict(constraints),
        "parameters": [asdict(spec) for spec in parameter_specs],
    }
    _json_dump(output_dir / "optimization_config.json", optimization_config)

    # Shared mutable state across trials (closures avoid global state)
    results: list[dict] =[]
    best_row: dict | None = None
    best_score: float | None = None
    status = "FINISHED"
    eligible_iterations = 0
    skipped_iterations = 0

    # Reset strategy-specific feature cache via the registry
    _cache_clearer = StrategyRegistry.get(strategy).clear_feature_cache
    if _cache_clearer is not None:
        _cache_clearer()

    if secondary_score_metric:
        secondary_score_metric = validate_score_metric(secondary_score_metric, strategy=strategy)
        optuna_direction = ["maximize" if score_direction == "max" else "minimize",
                            "maximize" if secondary_score_direction == "max" else "minimize"]
        _INELIGIBLE_SENTINEL = (
            float("-inf") if score_direction == "max" else float("inf"),
            float("-inf") if secondary_score_direction == "max" else float("inf")
        )
    else:
        optuna_direction = "maximize" if score_direction == "max" else "minimize"
        _INELIGIBLE_SENTINEL = float("-inf") if score_direction == "max" else float("inf")

    # Initialize convergence tracker for early stopping
    convergence_tracker = ConvergenceTracker(
        score_direction=score_direction,
        patience=convergence_patience,
        min_relative_improvement=convergence_min_improvement,
        window_size=convergence_window_size,
        window_count=convergence_window_count,
        n_trials=n_trials,
        circuit_breaker_ratio=circuit_breaker_ratio,
    ) if enable_convergence_stop else None

    def handle_row(row: dict, is_eligible: bool, is_skipped: bool, completed_count: int) -> None:
        nonlocal best_score, best_row, eligible_iterations, skipped_iterations
        row_score = row.get("score")
        results.append(row)
        if is_eligible:
            eligible_iterations += 1
        if is_skipped:
            skipped_iterations += 1
        if _is_better(row_score, best_score, score_direction):
            best_score = row_score
            best_row = row
            _json_dump(output_dir / "best.json", best_row)
        convergence_status = None
        if convergence_tracker is not None:
            status_dict = convergence_tracker.get_status()
            status_dict["patience"] = convergence_tracker.patience
            convergence_status = status_dict

        if progress_callback is not None:
            progress_callback(
                OptimizationProgress(
                    current_iteration=completed_count,
                    total_iterations=n_trials,
                    current_parameters=row.get("parameters", {}),
                    best_score=best_score,
                    best_parameters=best_row.get("parameters") if best_row else None,
                    output_dir=str(output_dir),
                    best_row=best_row,
                    convergence_status=convergence_status,
                )
            )

    has_categorical = any(spec.kind in ("choice", "bool") for spec in parameter_specs)
    if n_trials > 1000 and not has_categorical:
        sampler = optuna.samplers.QMCSampler(qmc_type="sobol", scramble=True, seed=seed)
    else:
        sampler = optuna.samplers.TPESampler(seed=seed, multivariate=True, constant_liar=True)
    
    # Remove stale storage so old distributions (with incorrect bounds) are not reused
    storage_path = output_root / "bayes_opt_journal.log"
    if storage_path.exists():
        storage_path.unlink()
    storage = JournalStorage(JournalFileStorage(str(storage_path)))
    study_name = f"{strategy}_{symbol}_{minutes}m_{score_metric}"
    
    study = optuna.create_study(
        study_name=study_name,
        storage=storage,
        load_if_exists=True,
        directions=optuna_direction if isinstance(optuna_direction, list) else None,
        direction=optuna_direction if not isinstance(optuna_direction, list) else None,
        sampler=sampler
    )

    # === INTELLIGENCE VECTORBT : PRE-SCAN ===
    logger.info(f"use_vectorbt_prescan={use_vectorbt_prescan} for strategy={strategy}")
    if use_vectorbt_prescan:
        prescan_func = StrategyRegistry.get(strategy).vectorbt_prescan
        if prescan_func:
            logger.info(f"Lancement du Pre-Scan VectorBT pour {strategy}...")
            try:
                sig = inspect.signature(prescan_func)
                kwargs: dict[str, Any] = {}
                if "output_dir" in sig.parameters:
                    logger.info(f"Passage output_dir={output_dir} au pre-scan")
                    kwargs["output_dir"] = output_dir
                if "stop_requested" in sig.parameters:
                    kwargs["stop_requested"] = stop_requested
                if "progress_callback" in sig.parameters:
                    kwargs["progress_callback"] = prescan_progress_callback
                if "workers" in sig.parameters:
                    logger.info(f"Passage workers={workers} au pre-scan")
                    kwargs["workers"] = workers
                if kwargs:
                    parameter_specs = prescan_func(data, parameter_specs, minutes, **kwargs)
                else:
                    logger.info("Fonction pre-scan sans parametres optionnels (retro-compatibilite)")
                    parameter_specs = prescan_func(data, parameter_specs, minutes)
                logger.info("Pre-Scan VectorBT termine.")
            except Exception as e:
                logger.warning(f"Erreur Pre-Scan VectorBT pour {strategy}: {e}")
            finally:
                import gc
                gc.collect()
        else:
            logger.info(f"Aucun Pre-Scan VectorBT defini pour {strategy}.")
    # ========================================

    # Inject default parameters as a prior
    from .configuration import default_strategy_parameters, parameter_definitions
    defaults = default_strategy_parameters(strategy)
    pdefs = parameter_definitions(strategy)
    prior_params = {}
    for spec in parameter_specs:
        if not spec.values:
            continue
        val = defaults.get(spec.name)
        if val is not None:
            if spec.kind == "numeric":
                vtype = pdefs.get(spec.name).value_type if pdefs.get(spec.name) else "float"
                low, high = spec.values[0], spec.values[-1]
                if vtype == "int":
                    prior_params[spec.name] = max(int(low), min(int(high), int(val)))
                else:
                    prior_params[spec.name] = max(float(low), min(float(high), float(val)))
            elif spec.kind in ("choice", "bool"):
                if val in spec.values:
                    prior_params[spec.name] = val
                else:
                    prior_params[spec.name] = spec.values[0]
        else:
            prior_params[spec.name] = spec.values[0]

    if prior_params:
        try:
            study.enqueue_trial(prior_params)
            logger.info(f"Enqueued prior trial with parameters: {prior_params}")
        except Exception as e:
            logger.warning(f"Could not enqueue prior trial: {e}")

    # Set up shared memory segment lists for absolute resource unlinking
    shm_objects = []
    try:
        # Drop symbol column to avoid object serialization overhead in shared memory
        data = data.drop(columns=["symbol"], errors="ignore")
        
        # Pre-allocate historical data in POSIX zero-copy memory
        shm_metadata, data_shm_objs = share_dataframe(data)
        shm_objects.extend(data_shm_objs)

        # Pre-allocate strategy indicator grids (HMA, etc.) to completely bypass rolling computations
        hma_shm_metadata = None
        pmax_shm_metadata = None
        rf_shm_metadata = None
        bjorgum_shm_metadata = None
        avt_shm_metadata = None
        commas_bot_shm_metadata = None
        noise_boundary_shm_metadata = None
        if strategy == "hma_crossover":
            fast_specs = next((s for s in parameter_specs if s.name == "fast_len"), None)
            slow_specs = next((s for s in parameter_specs if s.name == "slow_len"), None)
            if fast_specs and slow_specs and fast_specs.values and slow_specs.values:
                from .strategies.hma_crossover import _load_strategy_module
                strategy_mod = _load_strategy_module()
                hma_func = strategy_mod.hma
                import numpy as np
                import gc as _gc
                unique_lengths = sorted(list(set(fast_specs.values) | set(slow_specs.values)))
                length_to_idx = {int(length): i for i, length in enumerate(unique_lengths)}

                # Memory safety: check if grid is too large to preallocate in RAM
                estimated_bytes = len(unique_lengths) * len(data) * 8  # float64
                max_memory_limit = _get_dynamic_memory_limit()
                if estimated_bytes > max_memory_limit:
                    logger.warning(
                        f"Shared memory grid for HMA Crossover is too large "
                        f"({estimated_bytes / (1024**2):.1f} MB, "
                        f"limit: {max_memory_limit / (1024**2):.1f} MB). "
                        f"Skipping precalculation and falling back to on-the-fly "
                        f"calculation to protect system memory."
                    )
                else:
                    close_series = data["close"]
                    hma_grid_arr = np.zeros((len(unique_lengths), len(data)), dtype=np.float64)
                    for i, length in enumerate(unique_lengths):
                        hma_grid_arr[i] = hma_func(close_series, length).values

                    from .shared_memory import SharedIndicatorVolume
                    hma_shm = SharedIndicatorVolume(array_to_share=hma_grid_arr)
                    shm_objects.append(hma_shm)

                    hma_shm_metadata = {
                        "shm_name": hma_shm.shm_name,
                        "shape": hma_shm.shape,
                        "dtype": str(hma_shm.dtype),
                        "length_to_idx": length_to_idx
                    }

                    # Mount indicator references onto local parent context
                    from .strategies.hma_crossover import _load_strategy_module
                    try:
                        strategy_mod = _load_strategy_module()
                        if workers > 1:
                            # Multi-worker: mount zero-copy SHM view, release local array
                            strategy_mod._SHARED_HMA_GRID = hma_shm.get_view()
                            strategy_mod._SHARED_HMA_LENGTH_TO_IDX = length_to_idx
                            del hma_grid_arr
                            _gc.collect()
                        else:
                            # Single-worker: keep the local array for direct access
                            strategy_mod._SHARED_HMA_GRID = hma_grid_arr
                            strategy_mod._SHARED_HMA_LENGTH_TO_IDX = length_to_idx
                    except Exception as e:
                        logger.debug(f"Failed to mount local parent HMA grid: {e}")

        elif strategy == "pmax_explorer":
            periods_specs = next((s for s in parameter_specs if s.name == "periods"), None)
            length_specs = next((s for s in parameter_specs if s.name == "length"), None)
            mav_specs = next((s for s in parameter_specs if s.name == "mav"), None)
            change_atr_specs = next((s for s in parameter_specs if s.name == "change_atr"), None)

            periods_vals = list(periods_specs.values) if (periods_specs and periods_specs.values) else [10]
            length_vals = list(length_specs.values) if (length_specs and length_specs.values) else [10]
            mav_vals = list(mav_specs.values) if (mav_specs and mav_specs.values) else ["EMA"]
            change_atr_vals = list(change_atr_specs.values) if (change_atr_specs and change_atr_specs.values) else [True]

            from .strategies.pmax_explorer import _load_strategy_module
            strategy_mod = _load_strategy_module()
            
            source_col = fixed_overrides.source_col if (fixed_overrides and hasattr(fixed_overrides, "source_col") and fixed_overrides.source_col) else "hl2"
            if source_col == "hl2" and "hl2" not in data.columns:
                hl2_series = (data["high"] + data["low"]) / 2.0
            else:
                hl2_series = data[source_col] if source_col in data.columns else data["close"]
            
            src_arr = hl2_series.to_numpy(dtype=float)
            high_arr = data["high"].to_numpy(dtype=float)
            low_arr = data["low"].to_numpy(dtype=float)
            close_arr = data["close"].to_numpy(dtype=float)

            mavg_combos = []
            for mav in mav_vals:
                for length in length_vals:
                    mavg_combos.append((str(mav), int(length)))
            mavg_keys = {combo: i for i, combo in enumerate(mavg_combos)}

            atr_combos = []
            for periods in periods_vals:
                for change_atr in change_atr_vals:
                    atr_combos.append((int(periods), bool(change_atr)))
            atr_keys = {combo: i for i, combo in enumerate(atr_combos)}

            # Memory safety: check if grid is too large to preallocate in RAM
            estimated_bytes = (len(mavg_combos) + len(atr_combos)) * len(data) * 8
            max_memory_limit = _get_dynamic_memory_limit()
            if estimated_bytes > max_memory_limit:
                logger.warning(
                    f"Shared memory grids for PMax Explorer are too large ({estimated_bytes / (1024**2):.1f} MB, "
                    f"limit: {max_memory_limit / (1024**2):.1f} MB). Skipping precalculation and falling back "
                    f"to on-the-fly calculation to protect system memory."
                )
            else:
                import numpy as np
                mavg_grid_arr = np.zeros((len(mavg_combos), len(data)), dtype=np.float64)
                for combo, idx in mavg_keys.items():
                    mav_type, length = combo
                    if mav_type == "SMA":
                        mavg_grid_arr[idx] = strategy_mod.pine_sma(src_arr, length)
                    elif mav_type == "EMA":
                        mavg_grid_arr[idx] = strategy_mod.pine_ema(src_arr, length)
                    elif mav_type == "WMA":
                        mavg_grid_arr[idx] = strategy_mod.pine_wma(src_arr, length)
                    elif mav_type == "TMA":
                        mavg_grid_arr[idx] = strategy_mod.pine_tma(src_arr, length)
                    elif mav_type == "VAR":
                        mavg_grid_arr[idx] = strategy_mod.pine_var(src_arr, length)
                    elif mav_type == "WWMA":
                        mavg_grid_arr[idx] = strategy_mod.pine_wwma(src_arr, length)
                    elif mav_type == "ZLEMA":
                        mavg_grid_arr[idx] = strategy_mod.pine_zlema(src_arr, length)
                    elif mav_type == "TSF":
                        mavg_grid_arr[idx] = strategy_mod.pine_tsf(src_arr, length)
                    else:
                        mavg_grid_arr[idx] = strategy_mod.pine_ema(src_arr, length)

                atr_grid_arr = np.zeros((len(atr_combos), len(data)), dtype=np.float64)
                for combo, idx in atr_keys.items():
                    periods, change_atr = combo
                    atr_grid_arr[idx] = strategy_mod.compute_atr(high_arr, low_arr, close_arr, periods, change_atr)

                from .shared_memory import SharedIndicatorVolume
                mavg_shm = SharedIndicatorVolume(array_to_share=mavg_grid_arr)
                shm_objects.append(mavg_shm)

                atr_shm = SharedIndicatorVolume(array_to_share=atr_grid_arr)
                shm_objects.append(atr_shm)

                pmax_shm_metadata = {
                    "mavg_shm_name": mavg_shm.shm_name,
                    "mavg_shape": mavg_shm.shape,
                    "mavg_dtype": str(mavg_shm.dtype),
                    "mavg_keys": mavg_keys,
                    "atr_shm_name": atr_shm.shm_name,
                    "atr_shape": atr_shm.shape,
                    "atr_dtype": str(atr_shm.dtype),
                    "atr_keys": atr_keys,
                }

                try:
                    strategy_mod._SHARED_PMAX_MAVG_GRID = mavg_grid_arr
                    strategy_mod._SHARED_PMAX_MAVG_KEYS = mavg_keys
                    strategy_mod._SHARED_PMAX_ATR_GRID = atr_grid_arr
                    strategy_mod._SHARED_PMAX_ATR_KEYS = atr_keys
                except Exception as e:
                    logger.debug(f"Failed to mount local parent PMax grid: {e}")

        elif strategy == "range_filter":
            period_specs = next((s for s in parameter_specs if s.name == "sampling_period"), None)
            mult_specs = next((s for s in parameter_specs if s.name == "range_multiplier"), None)

            period_vals = list(period_specs.values) if (period_specs and period_specs.values) else [100]
            mult_vals = list(mult_specs.values) if (mult_specs and mult_specs.values) else [3.0]

            from .strategies.range_filter import _load_strategy_module
            strategy_mod = _load_strategy_module()
            
            source_col = fixed_overrides.source_col if (fixed_overrides and hasattr(fixed_overrides, "source_col") and fixed_overrides.source_col) else "close"
            src_series = data[source_col] if source_col in data.columns else data["close"]
            
            combos = []
            for period in period_vals:
                for mult in mult_vals:
                    combos.append((int(period), float(mult)))
            rf_keys = {combo: i for i, combo in enumerate(combos)}

            # Memory safety: check if grid is too large to preallocate in RAM (e.g. 1m timeframe)
            estimated_bytes = len(combos) * len(data) * 8 * 2  # 2 grids of float64
            max_memory_limit = _get_dynamic_memory_limit()
            if estimated_bytes > max_memory_limit:
                logger.warning(
                    f"Shared memory grid for Range Filter is too large ({estimated_bytes / (1024**2):.1f} MB, "
                    f"limit: {max_memory_limit / (1024**2):.1f} MB). Skipping precalculation and falling back "
                    f"to on-the-fly calculation to protect system memory."
                )
            else:
                import numpy as np
                smrng_grid_arr = np.zeros((len(combos), len(data)), dtype=np.float64)
                filt_grid_arr = np.zeros((len(combos), len(data)), dtype=np.float64)

                for combo, idx in rf_keys.items():
                    period, mult = combo
                    smrng_series = strategy_mod._smooth_range(src_series, period, mult)
                    filt_series = strategy_mod._range_filter(src_series, smrng_series)
                    
                    smrng_grid_arr[idx] = smrng_series.to_numpy(dtype=float)
                    filt_grid_arr[idx] = filt_series.to_numpy(dtype=float)

                from .shared_memory import SharedIndicatorVolume
                smrng_shm = SharedIndicatorVolume(array_to_share=smrng_grid_arr)
                shm_objects.append(smrng_shm)

                filt_shm = SharedIndicatorVolume(array_to_share=filt_grid_arr)
                shm_objects.append(filt_shm)

                rf_shm_metadata = {
                    "smrng_shm_name": smrng_shm.shm_name,
                    "smrng_shape": smrng_shm.shape,
                    "smrng_dtype": str(smrng_shm.dtype),
                    "filt_shm_name": filt_shm.shm_name,
                    "filt_shape": filt_shm.shape,
                    "filt_dtype": str(filt_shm.dtype),
                    "rf_keys": rf_keys,
                }

                try:
                    strategy_mod._SHARED_RF_SMRNG_GRID = smrng_grid_arr
                    strategy_mod._SHARED_RF_GRID = filt_grid_arr
                    strategy_mod._SHARED_RF_KEYS = rf_keys
                except Exception as e:
                    logger.debug(f"Failed to mount local parent Range Filter grid: {e}")

        elif strategy == "bjorgum_double_tap":
            length_specs = next((s for s in parameter_specs if s.name == "length"), None)
            atr_length_specs = next((s for s in parameter_specs if s.name == "atrLength"), None)
            lookback_specs = next((s for s in parameter_specs if s.name == "lookback"), None)

            length_vals = list(length_specs.values) if (length_specs and length_specs.values) else [50]
            atr_length_vals = list(atr_length_specs.values) if (atr_length_specs and atr_length_specs.values) else [14]
            lookback_vals = list(lookback_specs.values) if (lookback_specs and lookback_specs.values) else [5]

            # Memory safety: check if grid is too large to preallocate in RAM
            estimated_bytes = (2 * len(length_vals) + 2 * len(lookback_vals) + len(atr_length_vals)) * len(data) * 8
            max_memory_limit = _get_dynamic_memory_limit()
            if estimated_bytes > max_memory_limit:
                logger.warning(
                    f"Shared memory grid for Bjorgum Double Tap is too large "
                    f"({estimated_bytes / (1024**2):.1f} MB, "
                    f"limit: {max_memory_limit / (1024**2):.1f} MB). "
                    f"Skipping precalculation to protect system memory."
                )
            else:
                from .strategies.bjorgum_double_tap import _load_strategy_module
                strategy_mod = _load_strategy_module()
    
                # Precalculate pivot high/low rolling grids
                import numpy as np
                import pandas as pd
    
                high_series = data["high"]
                low_series = data["low"]
                close_series = data["close"]
    
                piv_high_grid_arr = np.zeros((len(length_vals), len(data)), dtype=np.float64)
                piv_low_grid_arr = np.zeros((len(length_vals), len(data)), dtype=np.float64)
                for idx, length in enumerate(length_vals):
                    piv_high_grid_arr[idx] = high_series.rolling(int(length), min_periods=1).max().to_numpy()
                    piv_low_grid_arr[idx] = low_series.rolling(int(length), min_periods=1).min().to_numpy()
    
                # Precalculate trailing stop rolling min/max grids
                roll_min_grid_arr = np.zeros((len(lookback_vals), len(data)), dtype=np.float64)
                roll_max_grid_arr = np.zeros((len(lookback_vals), len(data)), dtype=np.float64)
                for idx, lookback in enumerate(lookback_vals):
                    roll_min_grid_arr[idx] = low_series.rolling(int(lookback), min_periods=1).min().to_numpy()
                    roll_max_grid_arr[idx] = high_series.rolling(int(lookback), min_periods=1).max().to_numpy()
    
                # Precalculate ATR grid
                atr_grid_arr = np.zeros((len(atr_length_vals), len(data)), dtype=np.float64)
                
                closes = close_series.to_numpy(dtype=float)
                prev_closes = np.roll(closes, 1)
                prev_closes[0] = closes[0]
                
                tr1 = high_series.to_numpy(dtype=float) - low_series.to_numpy(dtype=float)
                tr2 = np.abs(high_series.to_numpy(dtype=float) - prev_closes)
                tr3 = np.abs(low_series.to_numpy(dtype=float) - prev_closes)
                tr = np.maximum(tr1, np.maximum(tr2, tr3))
                tr_series = pd.Series(tr)
                
                for idx, atr_length in enumerate(atr_length_vals):
                    atr_grid_arr[idx] = tr_series.ewm(alpha=1.0 / int(atr_length), adjust=False).mean().to_numpy()
    
                from .shared_memory import SharedIndicatorVolume
                atr_shm = SharedIndicatorVolume(array_to_share=atr_grid_arr)
                shm_objects.append(atr_shm)
    
                piv_high_shm = SharedIndicatorVolume(array_to_share=piv_high_grid_arr)
                shm_objects.append(piv_high_shm)
    
                piv_low_shm = SharedIndicatorVolume(array_to_share=piv_low_grid_arr)
                shm_objects.append(piv_low_shm)
    
                roll_min_shm = SharedIndicatorVolume(array_to_share=roll_min_grid_arr)
                shm_objects.append(roll_min_shm)
    
                roll_max_shm = SharedIndicatorVolume(array_to_share=roll_max_grid_arr)
                shm_objects.append(roll_max_shm)
    
                bjorgum_shm_metadata = {
                    "atr_shm_name": atr_shm.shm_name,
                    "atr_shape": atr_shm.shape,
                    "atr_dtype": str(atr_shm.dtype),
                    "atr_keys": {int(v): i for i, v in enumerate(atr_length_vals)},
                    
                    "piv_high_shm_name": piv_high_shm.shm_name,
                    "piv_high_shape": piv_high_shm.shape,
                    "piv_high_dtype": str(piv_high_shm.dtype),
                    "piv_high_keys": {int(v): i for i, v in enumerate(length_vals)},
    
                    "piv_low_shm_name": piv_low_shm.shm_name,
                    "piv_low_shape": piv_low_shm.shape,
                    "piv_low_dtype": str(piv_low_shm.dtype),
                    "piv_low_keys": {int(v): i for i, v in enumerate(length_vals)},
    
                    "roll_min_shm_name": roll_min_shm.shm_name,
                    "roll_min_shape": roll_min_shm.shape,
                    "roll_min_dtype": str(roll_min_shm.dtype),
                    "roll_min_keys": {int(v): i for i, v in enumerate(lookback_vals)},
    
                    "roll_max_shm_name": roll_max_shm.shm_name,
                    "roll_max_shape": roll_max_shm.shape,
                    "roll_max_dtype": str(roll_max_shm.dtype),
                    "roll_max_keys": {int(v): i for i, v in enumerate(lookback_vals)},
                }
    
                try:
                    if workers > 1:
                        import gc as _gc
                        strategy_mod._SHARED_BJ_ATR_GRID = atr_shm.get_view()
                        strategy_mod._SHARED_BJ_ATR_KEYS = bjorgum_shm_metadata["atr_keys"]
                        strategy_mod._SHARED_BJ_PIV_HIGH_GRID = piv_high_shm.get_view()
                        strategy_mod._SHARED_BJ_PIV_HIGH_KEYS = bjorgum_shm_metadata["piv_high_keys"]
                        strategy_mod._SHARED_BJ_PIV_LOW_GRID = piv_low_shm.get_view()
                        strategy_mod._SHARED_BJ_PIV_LOW_KEYS = bjorgum_shm_metadata["piv_low_keys"]
                        strategy_mod._SHARED_BJ_ROLL_MIN_GRID = roll_min_shm.get_view()
                        strategy_mod._SHARED_BJ_ROLL_MIN_KEYS = bjorgum_shm_metadata["roll_min_keys"]
                        strategy_mod._SHARED_BJ_ROLL_MAX_GRID = roll_max_shm.get_view()
                        strategy_mod._SHARED_BJ_ROLL_MAX_KEYS = bjorgum_shm_metadata["roll_max_keys"]
                        
                        del piv_high_grid_arr
                        del piv_low_grid_arr
                        del roll_min_grid_arr
                        del roll_max_grid_arr
                        del atr_grid_arr
                        _gc.collect()
                    else:
                        strategy_mod._SHARED_BJ_ATR_GRID = atr_grid_arr
                        strategy_mod._SHARED_BJ_ATR_KEYS = bjorgum_shm_metadata["atr_keys"]
                        strategy_mod._SHARED_BJ_PIV_HIGH_GRID = piv_high_grid_arr
                        strategy_mod._SHARED_BJ_PIV_HIGH_KEYS = bjorgum_shm_metadata["piv_high_keys"]
                        strategy_mod._SHARED_BJ_PIV_LOW_GRID = piv_low_grid_arr
                        strategy_mod._SHARED_BJ_PIV_LOW_KEYS = bjorgum_shm_metadata["piv_low_keys"]
                        strategy_mod._SHARED_BJ_ROLL_MIN_GRID = roll_min_grid_arr
                        strategy_mod._SHARED_BJ_ROLL_MIN_KEYS = bjorgum_shm_metadata["roll_min_keys"]
                        strategy_mod._SHARED_BJ_ROLL_MAX_GRID = roll_max_grid_arr
                        strategy_mod._SHARED_BJ_ROLL_MAX_KEYS = bjorgum_shm_metadata["roll_max_keys"]
                except Exception as e:
                    logger.debug(f"Failed to mount local parent Bjorgum Double Tap grid: {e}")

        elif strategy == "adaptive_volatility_trend":
            source_specs = next((s for s in parameter_specs if s.name == "source"), None)
            length_specs = next((s for s in parameter_specs if s.name == "length"), None)
            smoothing_specs = next((s for s in parameter_specs if s.name == "efficiency_smoothing"), None)
            atr_len_specs = next((s for s in parameter_specs if s.name == "atr_len"), None)
            rsi_len_specs = next((s for s in parameter_specs if s.name == "rsi_len"), None)

            source_vals = list(source_specs.values) if (source_specs and source_specs.values) else ["close"]
            length_vals = list(length_specs.values) if (length_specs and length_specs.values) else [21]
            smoothing_vals = list(smoothing_specs.values) if (smoothing_specs and smoothing_specs.values) else [5]
            atr_len_vals = list(atr_len_specs.values) if (atr_len_specs and atr_len_specs.values) else [14]
            rsi_len_vals = list(rsi_len_specs.values) if (rsi_len_specs and rsi_len_specs.values) else [14]

            from .strategies.adaptive_volatility_trend import _load_strategy_module
            strategy_mod = _load_strategy_module()

            import numpy as np
            import pandas as pd

            # Precalculate Adaptive MA Grid
            ama_combos = []
            for src in source_vals:
                for l in length_vals:
                    for s in smoothing_vals:
                        ama_combos.append((str(src), int(l), int(s)))
            ama_keys = {combo: i for i, combo in enumerate(ama_combos)}

            # Precalculate RSI Grid combos for memory safety check
            rsi_combos = []
            for src in source_vals:
                for rl in rsi_len_vals:
                    rsi_combos.append((str(src), int(rl)))
            rsi_keys = {combo: i for i, combo in enumerate(rsi_combos)}

            # Memory safety: check if grid is too large to preallocate in RAM (e.g. 1m timeframe)
            # ama_grid_arr has shape (len(ama_combos), 2, len(data)) -> len(ama_combos) * 2 * len(data) * 8 bytes
            # atr_grid_arr has shape (len(atr_len_vals), len(data)) -> len(atr_len_vals) * len(data) * 8 bytes
            # rsi_grid_arr has shape (len(rsi_combos), len(data)) -> len(rsi_combos) * len(data) * 8 bytes
            estimated_bytes = (len(ama_combos) * 2 + len(atr_len_vals) + len(rsi_combos)) * len(data) * 8
            max_memory_limit = _get_dynamic_memory_limit()
            if estimated_bytes > max_memory_limit:
                logger.warning(
                    f"Shared memory grids for Adaptive Volatility Trend are too large ({estimated_bytes / (1024**2):.1f} MB, "
                    f"limit: {max_memory_limit / (1024**2):.1f} MB). Skipping precalculation and falling back "
                    f"to on-the-fly calculation to protect system memory."
                )
            else:
                ama_grid_arr = np.zeros((len(ama_combos), 2, len(data)), dtype=np.float64)
                for combo, idx in ama_keys.items():
                    src, l, s = combo
                    source_series = strategy_mod._price_source(data, src)
                    close_series = data["close"]
                    adaptive_line, efficiency_ratio = strategy_mod._adaptive_ma(source_series, close_series, l, s)
                    ama_grid_arr[idx, 0] = adaptive_line.to_numpy(dtype=float)
                    ama_grid_arr[idx, 1] = efficiency_ratio.to_numpy(dtype=float)

                # Precalculate ATR Grid
                high_series = data["high"]
                low_series = data["low"]
                close_series = data["close"]
                
                atr_grid_arr = np.zeros((len(atr_len_vals), len(data)), dtype=np.float64)
                atr_keys = {int(v): i for i, v in enumerate(atr_len_vals)}
                for atr_len, idx in atr_keys.items():
                    atr_series = strategy_mod._atr(high_series, low_series, close_series, atr_len)
                    atr_grid_arr[idx] = atr_series.to_numpy(dtype=float)

                # Precalculate RSI Grid
                rsi_grid_arr = np.zeros((len(rsi_combos), len(data)), dtype=np.float64)
                for combo, idx in rsi_keys.items():
                    src, rl = combo
                    source_series = strategy_mod._price_source(data, src)
                    rsi_series = strategy_mod._rsi(source_series, rl)
                    rsi_grid_arr[idx] = rsi_series.to_numpy(dtype=float)

                from .shared_memory import SharedIndicatorVolume
                ama_shm = SharedIndicatorVolume(array_to_share=ama_grid_arr)
                shm_objects.append(ama_shm)

                atr_shm = SharedIndicatorVolume(array_to_share=atr_grid_arr)
                shm_objects.append(atr_shm)

                rsi_shm = SharedIndicatorVolume(array_to_share=rsi_grid_arr)
                shm_objects.append(rsi_shm)

                avt_shm_metadata = {
                    "ama_shm_name": ama_shm.shm_name,
                    "ama_shape": ama_shm.shape,
                    "ama_dtype": str(ama_shm.dtype),
                    "ama_keys": ama_keys,

                    "atr_shm_name": atr_shm.shm_name,
                    "atr_shape": atr_shm.shape,
                    "atr_dtype": str(atr_shm.dtype),
                    "atr_keys": atr_keys,

                    "rsi_shm_name": rsi_shm.shm_name,
                    "rsi_shape": rsi_shm.shape,
                    "rsi_dtype": str(rsi_shm.dtype),
                    "rsi_keys": rsi_keys,
                }

                try:
                    strategy_mod._SHARED_AVT_AMA_GRID = ama_grid_arr
                    strategy_mod._SHARED_AVT_AMA_KEYS = ama_keys
                    strategy_mod._SHARED_AVT_ATR_GRID = atr_grid_arr
                    strategy_mod._SHARED_AVT_ATR_KEYS = atr_keys
                    strategy_mod._SHARED_AVT_RSI_GRID = rsi_grid_arr
                    strategy_mod._SHARED_AVT_RSI_KEYS = rsi_keys
                except Exception as e:
                    logger.debug(f"Failed to mount local parent Adaptive Volatility Trend grid: {e}")

        elif strategy == "3commas_bot":
            ma_type1_specs = next((s for s in parameter_specs if s.name == "ma_type1"), None)
            ma_type2_specs = next((s for s in parameter_specs if s.name == "ma_type2"), None)
            ma_length1_specs = next((s for s in parameter_specs if s.name == "ma_length1"), None)
            ma_length2_specs = next((s for s in parameter_specs if s.name == "ma_length2"), None)
            atr_len_specs = next((s for s in parameter_specs if s.name == "atr_len"), None)
            swing_lookback_specs = next((s for s in parameter_specs if s.name == "swing_lookback"), None)

            ma_type1_vals = list(ma_type1_specs.values) if (ma_type1_specs and ma_type1_specs.values) else ["EMA"]
            ma_type2_vals = list(ma_type2_specs.values) if (ma_type2_specs and ma_type2_specs.values) else ["EMA"]
            ma_length1_vals = list(ma_length1_specs.values) if (ma_length1_specs and ma_length1_specs.values) else [21]
            ma_length2_vals = list(ma_length2_specs.values) if (ma_length2_specs and ma_length2_specs.values) else [50]
            atr_len_vals = list(atr_len_specs.values) if (atr_len_specs and atr_len_specs.values) else [14]
            swing_lookback_vals = list(swing_lookback_specs.values) if (swing_lookback_specs and swing_lookback_specs.values) else [5]

            from .strategies.commas_bot import _load_strategy_module
            strategy_mod = _load_strategy_module()

            import numpy as np
            import pandas as pd

            # Precalculate MA Grid
            unique_ma_combos = set()
            for t1 in ma_type1_vals:
                for l1 in ma_length1_vals:
                    unique_ma_combos.add((str(t1), int(l1)))
            for t2 in ma_type2_vals:
                for l2 in ma_length2_vals:
                    unique_ma_combos.add((str(t2), int(l2)))

            ma_combos = sorted(list(unique_ma_combos))
            ma_keys = {combo: i for i, combo in enumerate(ma_combos)}

            # Memory safety: check if grid is too large to preallocate in RAM (e.g. 1m timeframe)
            # ma_grid_arr has: len(ma_combos) * len(data) * 8 bytes
            # atr_grid_arr has: len(atr_len_vals) * len(data) * 8 bytes
            # swing_grid_arr has: len(swing_lookback_vals) * 2 * len(data) * 8 bytes
            estimated_bytes = (len(ma_combos) + len(atr_len_vals) + len(swing_lookback_vals) * 2) * len(data) * 8
            max_memory_limit = _get_dynamic_memory_limit()
            if estimated_bytes > max_memory_limit:
                logger.warning(
                    f"Shared memory grids for 3Commas Bot are too large ({estimated_bytes / (1024**2):.1f} MB, "
                    f"limit: {max_memory_limit / (1024**2):.1f} MB). Skipping precalculation and falling back "
                    f"to on-the-fly calculation to protect system memory."
                )
            else:
                ma_grid_arr = np.zeros((len(ma_combos), len(data)), dtype=np.float64)
                close_series = data["close"]
                for combo, idx in ma_keys.items():
                    ma_type, length = combo
                    ma_series = strategy_mod.get_ma(close_series, ma_type, length, df=data)
                    ma_grid_arr[idx] = ma_series.to_numpy(dtype=float)

                # Precalculate ATR Grid
                atr_grid_arr = np.zeros((len(atr_len_vals), len(data)), dtype=np.float64)
                atr_keys = {int(v): i for i, v in enumerate(atr_len_vals)}
                for atr_len, idx in atr_keys.items():
                    atr_series = strategy_mod.atr(data, atr_len)
                    atr_grid_arr[idx] = atr_series.to_numpy(dtype=float)

                # Precalculate Swing Grid
                swing_grid_arr = np.zeros((len(swing_lookback_vals), 2, len(data)), dtype=np.float64)
                swing_keys = {int(v): i for i, v in enumerate(swing_lookback_vals)}
                for swing_lookback, idx in swing_keys.items():
                    low_series = data["low"]
                    high_series = data["high"]
                    low_lowest = strategy_mod.lowest(low_series, swing_lookback)
                    high_highest = strategy_mod.highest(high_series, swing_lookback)
                    swing_grid_arr[idx, 0] = low_lowest.to_numpy(dtype=float)
                    swing_grid_arr[idx, 1] = high_highest.to_numpy(dtype=float)

                from .shared_memory import SharedIndicatorVolume
                ma_shm = SharedIndicatorVolume(array_to_share=ma_grid_arr)
                shm_objects.append(ma_shm)

                atr_shm = SharedIndicatorVolume(array_to_share=atr_grid_arr)
                shm_objects.append(atr_shm)

                swing_shm = SharedIndicatorVolume(array_to_share=swing_grid_arr)
                shm_objects.append(swing_shm)

                commas_bot_shm_metadata = {
                    "ma_shm_name": ma_shm.shm_name,
                    "ma_shape": ma_shm.shape,
                    "ma_dtype": str(ma_shm.dtype),
                    "ma_keys": ma_keys,

                    "atr_shm_name": atr_shm.shm_name,
                    "atr_shape": atr_shm.shape,
                    "atr_dtype": str(atr_shm.dtype),
                    "atr_keys": atr_keys,

                    "swing_shm_name": swing_shm.shm_name,
                    "swing_shape": swing_shm.shape,
                    "swing_dtype": str(swing_shm.dtype),
                    "swing_keys": swing_keys,
                }

                try:
                    strategy_mod._SHARED_CB_MA_GRID = ma_grid_arr
                    strategy_mod._SHARED_CB_MA_KEYS = ma_keys
                    strategy_mod._SHARED_CB_ATR_GRID = atr_grid_arr
                    strategy_mod._SHARED_CB_ATR_KEYS = atr_keys
                    strategy_mod._SHARED_CB_SWING_GRID = swing_grid_arr
                    strategy_mod._SHARED_CB_SWING_KEYS = swing_keys
                except Exception as e:
                    logger.debug(f"Failed to mount local parent 3Commas Bot grid: {e}")

        elif strategy == "noise_boundary_intraday":
            lookback_specs = next((s for s in parameter_specs if s.name == "lookback_days"), None)
            lookback_vals = list(lookback_specs.values) if (lookback_specs and lookback_specs.values) else [20]

            import backtest_engine.strategies.noise_boundary_intraday as nb_mod
            import numpy as np
            import pandas as pd

            # Precalculate mapped_vol and spy_dvol grids
            vol_grid_arr = np.zeros((len(lookback_vals), 2, len(data)), dtype=np.float64)
            vol_keys = {int(v): i for i, v in enumerate(lookback_vals)}

            # Constants for mapped_vol
            normalized_index = data.index.normalize()
            daily_open = data.groupby(normalized_index)["open"].transform("first")
            move_open = (data["close"] / daily_open - 1).abs()
            pivoted_df = pd.DataFrame({"move_open": move_open}, index=data.index)
            pivoted_df["date"] = normalized_index
            pivoted_df["time"] = data.index.time
            pivoted_matrix = pivoted_df.pivot(index="date", columns="time", values="move_open")
            multi_index = pd.MultiIndex.from_arrays([normalized_index, data.index.time], names=["date", "time"])

            # Constants for spy_dvol
            daily_close = data["close"].resample("D").last().dropna()
            daily_returns = daily_close.pct_change()

            for lookback, idx in vol_keys.items():
                # 1. mapped_vol
                rolling_matrix = pivoted_matrix.rolling(window=lookback, min_periods=lookback - 1).mean().shift(1)
                stacked = rolling_matrix.stack(dropna=False)
                mapped_vol = stacked.reindex(multi_index).values
                vol_grid_arr[idx, 0] = mapped_vol

                # 2. spy_dvol
                daily_dvol_series = daily_returns.rolling(window=lookback, min_periods=lookback - 1).std().shift(1)
                spy_dvol = daily_dvol_series.reindex(normalized_index).values
                spy_dvol_filled = np.where(np.isnan(spy_dvol), 0.0, spy_dvol)
                vol_grid_arr[idx, 1] = spy_dvol_filled

            from .shared_memory import SharedIndicatorVolume
            vol_shm = SharedIndicatorVolume(array_to_share=vol_grid_arr)
            shm_objects.append(vol_shm)

            noise_boundary_shm_metadata = {
                "vol_shm_name": vol_shm.shm_name,
                "vol_shape": vol_shm.shape,
                "vol_dtype": str(vol_shm.dtype),
                "vol_keys": vol_keys,
            }

            try:
                nb_mod._SHARED_NB_VOL_GRID = vol_grid_arr
                nb_mod._SHARED_NB_VOL_KEYS = vol_keys
            except Exception as e:
                logger.debug(f"Failed to mount local parent Noise Boundary grid: {e}")

        if workers == 1:
            import gc as _gc_loop
            for iteration in range(1, n_trials + 1):
                if stop_requested is not None and stop_requested():
                    status = "CANCELLED"
                    break
                trial = study.ask()
                parameters = _suggest_parameters(trial, parameter_specs, strategy=strategy)
                row, is_eligible, is_skipped = _evaluate_hma_parameters(
                    data=data, symbol=symbol, parameters=parameters, iteration=iteration,
                    fixed_overrides=fixed_overrides, initial_capital=initial_capital,
                    strategy=strategy, score_metric=score_metric, min_closed_trades=min_closed_trades,
                    timeframe_minutes=minutes, early_stop_drawdown_pct=early_stop_drawdown_pct,
                    wfo_windows=wfo_windows,
                    repo_root=repo_root,
                    constraints=constraints,
                )
                handle_row(row, is_eligible, is_skipped, iteration)
                score = row.get("score")
                
                if secondary_score_metric:
                    sec_score = row.get("metrics", {}).get(secondary_score_metric)
                    optuna_val = (float(score) if score is not None else _INELIGIBLE_SENTINEL[0], 
                                  float(sec_score) if sec_score is not None else _INELIGIBLE_SENTINEL[1])
                else:
                    optuna_val = float(score) if score is not None else _INELIGIBLE_SENTINEL
 
                study.tell(trial, optuna_val)
 
                # Check convergence for early stopping
                if convergence_tracker is not None:
                    should_stop, stop_reason = convergence_tracker.update(score)
                    if should_stop:
                        if stop_reason == "circuit_breaker":
                            logger.info(f"Circuit breaker triggered at iteration {iteration}/{n_trials}. Stopping early.")
                        else:
                            logger.info(f"Convergence detected at iteration {iteration}/{n_trials}. Stopping early.")
                        status = "FINISHED_CONVERGED"
                        break

                # Periodic GC to prevent memory fragmentation from temporary
                # DataFrames created during each trial evaluation.
                if iteration % 50 == 0:
                    _gc_loop.collect()
        else:
            completed_count = 0
            import multiprocessing
            executor = ProcessPoolExecutor(
                max_workers=workers,
                mp_context=multiprocessing.get_context("spawn"),
                initializer=_init_worker_bayesian,
                initargs=(shm_metadata, symbol, fixed_overrides, initial_capital, strategy, score_metric, min_closed_trades, minutes, early_stop_drawdown_pct, wfo_windows, repo_root, constraints, hma_shm_metadata, pmax_shm_metadata, rf_shm_metadata, bjorgum_shm_metadata, avt_shm_metadata, commas_bot_shm_metadata, noise_boundary_shm_metadata),
            )
            cancelled = False

            def cancel_pending(f_dict: dict) -> None:
                for f in f_dict:
                    f.cancel()
                f_dict.clear()
                for p in getattr(executor, "_processes", {}).values():
                    try:
                        p.terminate()
                    except Exception:
                        pass

            try:
                futures_map: dict = {}
                trials_created = 0

                def submit_next() -> bool:
                    nonlocal trials_created
                    if trials_created >= n_trials:
                        return False
                    trial = study.ask()
                    params = _suggest_parameters(trial, parameter_specs, strategy=strategy)
                    iteration = trials_created + 1
                    future = executor.submit(_evaluate_worker_bayesian, (iteration, params))
                    futures_map[future] = trial
                    trials_created += 1
                    return True

                # Initial fill
                for _ in range(min(workers, n_trials)):
                    submit_next()

                while futures_map:
                    if stop_requested is not None and stop_requested():
                        status = "CANCELLED"
                        cancelled = True
                        cancel_pending(futures_map)
                        break

                    done, _ = wait(futures_map.keys(), return_when=FIRST_COMPLETED)
                    
                    for future in done:
                        trial = futures_map.pop(future)
                        completed_count += 1
                        try:
                            row, is_eligible, is_skipped = future.result()
                            handle_row(row, is_eligible, is_skipped, completed_count)
                            score = row.get("score")

                            if secondary_score_metric:
                                sec_score = row.get("metrics", {}).get(secondary_score_metric)
                                optuna_val = (float(score) if score is not None else _INELIGIBLE_SENTINEL[0], 
                                              float(sec_score) if sec_score is not None else _INELIGIBLE_SENTINEL[1])
                            else:
                                optuna_val = float(score) if score is not None else _INELIGIBLE_SENTINEL

                            study.tell(trial, optuna_val)

                            # Check convergence for early stopping
                            if convergence_tracker is not None:
                                should_stop, stop_reason = convergence_tracker.update(score)
                                if should_stop:
                                    if stop_reason == "circuit_breaker":
                                        logger.info(f"Circuit breaker triggered at iteration {completed_count}/{n_trials}. Stopping early.")
                                    else:
                                        logger.info(f"Convergence detected at iteration {completed_count}/{n_trials}. Stopping early.")
                                    status = "FINISHED_CONVERGED"
                                    cancelled = True
                                    cancel_pending(futures_map)
                                    break
                        except Exception as e:
                            logger.error(f"Worker failed: {e}")
                            study.tell(trial, _INELIGIBLE_SENTINEL)

                        if stop_requested is not None and stop_requested():
                            status = "CANCELLED"
                            cancelled = True
                            cancel_pending(futures_map)
                            break

                        if status == "FINISHED_CONVERGED":
                            break

                        submit_next()
            finally:
                executor.shutdown(wait=not cancelled, cancel_futures=True)
    finally:
        # Clean up POSIX shared memory resources definitely to avoid system-level memory leaks
        for shm_obj in shm_objects:
            try:
                shm_obj.unlink()
            except Exception:
                pass
        
        # Reset local parent context
        if strategy == "hma_crossover":
            from .strategies.hma_crossover import _load_strategy_module
            try:
                strategy_mod = _load_strategy_module()
                strategy_mod._SHARED_HMA_GRID = None
                strategy_mod._SHARED_HMA_LENGTH_TO_IDX = None
            except Exception:
                pass
        elif strategy == "pmax_explorer":
            from .strategies.pmax_explorer import _load_strategy_module
            try:
                strategy_mod = _load_strategy_module()
                strategy_mod._SHARED_PMAX_MAVG_GRID = None
                strategy_mod._SHARED_PMAX_MAVG_KEYS = None
                strategy_mod._SHARED_PMAX_ATR_GRID = None
                strategy_mod._SHARED_PMAX_ATR_KEYS = None
            except Exception:
                pass
        elif strategy == "range_filter":
            from .strategies.range_filter import _load_strategy_module
            try:
                strategy_mod = _load_strategy_module()
                strategy_mod._SHARED_RF_SMRNG_GRID = None
                strategy_mod._SHARED_RF_GRID = None
                strategy_mod._SHARED_RF_KEYS = None
            except Exception:
                pass
        elif strategy == "bjorgum_double_tap":
            from .strategies.bjorgum_double_tap import _load_strategy_module
            try:
                strategy_mod = _load_strategy_module()
                strategy_mod._SHARED_BJ_ATR_GRID = None
                strategy_mod._SHARED_BJ_ATR_KEYS = None
                strategy_mod._SHARED_BJ_PIV_HIGH_GRID = None
                strategy_mod._SHARED_BJ_PIV_HIGH_KEYS = None
                strategy_mod._SHARED_BJ_PIV_LOW_GRID = None
                strategy_mod._SHARED_BJ_PIV_LOW_KEYS = None
                strategy_mod._SHARED_BJ_ROLL_MIN_GRID = None
                strategy_mod._SHARED_BJ_ROLL_MIN_KEYS = None
                strategy_mod._SHARED_BJ_ROLL_MAX_GRID = None
                strategy_mod._SHARED_BJ_ROLL_MAX_KEYS = None
            except Exception:
                pass
        elif strategy == "adaptive_volatility_trend":
            from .strategies.adaptive_volatility_trend import _load_strategy_module
            try:
                strategy_mod = _load_strategy_module()
                strategy_mod._SHARED_AVT_AMA_GRID = None
                strategy_mod._SHARED_AVT_AMA_KEYS = None
                strategy_mod._SHARED_AVT_ATR_GRID = None
                strategy_mod._SHARED_AVT_ATR_KEYS = None
                strategy_mod._SHARED_AVT_RSI_GRID = None
                strategy_mod._SHARED_AVT_RSI_KEYS = None
            except Exception:
                pass
        elif strategy == "3commas_bot":
            from .strategies.commas_bot import _load_strategy_module
            try:
                strategy_mod = _load_strategy_module()
                strategy_mod._SHARED_CB_MA_GRID = None
                strategy_mod._SHARED_CB_MA_KEYS = None
                strategy_mod._SHARED_CB_ATR_GRID = None
                strategy_mod._SHARED_CB_ATR_KEYS = None
                strategy_mod._SHARED_CB_SWING_GRID = None
                strategy_mod._SHARED_CB_SWING_KEYS = None
            except Exception:
                pass
        elif strategy == "noise_boundary_intraday":
            import backtest_engine.strategies.noise_boundary_intraday as nb_mod
            try:
                nb_mod._SHARED_NB_VOL_GRID = None
                nb_mod._SHARED_NB_VOL_KEYS = None
            except Exception:
                pass

    # Safety net: check if circuit breaker was triggered by the end of the loop
    if status == "FINISHED" and convergence_tracker is not None:
        if convergence_tracker._check_circuit_breaker():
            logger.info("Circuit breaker triggered post-loop safety net. Forcing FINISHED_CONVERGED.")
            status = "FINISHED_CONVERGED"

    if stop_requested is not None and stop_requested():
        status = "CANCELLED"

    if best_row is None:
        _json_dump(output_dir / "best.json", None)
    elif write_best_run and best_row is not None:
        best_params = best_row.get("parameters", {})
        best_overrides = _merged_strategy_overrides(strategy, fixed_overrides, best_params)
        if strategy == "hma_crossover":
            validation_errors = validate_hma_overrides(best_overrides)
        else:
            validation_errors = []
        if not validation_errors:
            best_runner = StrategyRegistry.get(strategy).run_function
            best_result = best_runner(
                data=data,
                symbol=symbol,
                overrides=best_overrides,
                initial_capital=initial_capital,
                timeframe_minutes=minutes,
                compute_full_metrics=True,
                repo_root=repo_root,
            )
            best_run_dir = write_backtest_outputs(best_result, output_dir / "best_run")
            best_row["best_backtest_dir"] = str(best_run_dir)
            _json_dump(output_dir / "best.json", best_row)
            
    if secondary_score_metric:
        try:
            pareto_trials = study.best_trials
            pareto_front = [
                {
                    "number": t.number,
                    "score": t.values[0] if t.values else None,
                    "secondary_score": t.values[1] if t.values and len(t.values) > 1 else None,
                    "parameters": t.params,
                }
                for t in pareto_trials
            ]
            _json_dump(output_dir / "pareto_front.json", pareto_front)
            logger.info(f"Saved Pareto front with {len(pareto_front)} trials.")
        except Exception as e:
            logger.warning(f"Could not save Pareto front: {e}")

    results.sort(key=lambda item: int(item.get("iteration", 0)))
    _write_results(output_dir, results)

    # Save parameter importance if multiple parameters were evaluated
    try:
        import optuna.importance
        if len(results) > 1 and len(parameter_specs) > 1:
            completed_trials = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
            if len(completed_trials) > 1:
                target_fn = lambda t: t.values[0] if (t.values and len(t.values) > 0) else 0.0
                importances = optuna.importance.get_param_importances(study, target=target_fn)
                _json_dump(output_dir / "parameter_importance.json", importances)
                logger.info("Saved parameter importance report.")
    except Exception as e:
        logger.warning(f"Could not calculate parameter importance: {e}")

    # === INTELLIGENCE VECTORBT : POST-VALIDATION ===
    if run_post_validation and best_row is not None:
        logger.info("Lancement de la Post-Validation VectorBT (Random Benchmark)...")
        try:
            import vectorbt as vbt
            import numpy as np

            price = data["close"]
            n_samples = 100
            entries_data = np.random.choice([True, False], size=(len(price), n_samples), p=[0.1, 0.9])
            exits_data = np.random.choice([True, False], size=(len(price), n_samples), p=[0.1, 0.9])

            entries = pd.DataFrame(entries_data, index=price.index)
            exits = pd.DataFrame(exits_data, index=price.index)

            pf_rand = vbt.Portfolio.from_signals(price, entries, exits, init_cash=initial_capital, freq=f"{minutes}min")
            rand_sharpes = pf_rand.sharpe_ratio().dropna()

            best_sharpe = best_row.get("score") if score_metric == "sharpe_ratio" else best_row.get("metrics", {}).get("sharpe_ratio")

            if len(rand_sharpes) > 0:
                mean_sharpe = float(rand_sharpes.mean())
                max_sharpe = float(rand_sharpes.max())
                prob_outperform = float((rand_sharpes < (best_sharpe or 0)).mean() * 100) if best_sharpe is not None else 0.0

                best_row["vectorbt_validation"] = {
                    "mean_sharpe": mean_sharpe,
                    "max_sharpe": max_sharpe,
                    "prob_outperform_pct": prob_outperform
                }
                _json_dump(output_dir / "best.json", best_row)
        except Exception as e:
            logger.warning(f"Erreur lors de la Post-Validation VectorBT: {e}")
    # ===============================================

    top_q = optimization_config.get("top_quantile") if optimization_config else None
    score_tol = optimization_config.get("score_tolerance_pct") if optimization_config else None
    recommendations = write_optimization_recommendations(
        output_dir,
        results,
        optimization_config,
        top_quantile=top_q,
        score_tolerance_pct=score_tol,
    )
    optimizer_report_paths = write_optimizer_reports(output_dir, results, optimization_config, recommendations)

    summary = OptimizationSummary(
        output_dir=output_dir,
        iterations_completed=len(results),
        total_iterations=n_trials,
        eligible_iterations=eligible_iterations,
        skipped_iterations=skipped_iterations,
        status=status,
        score_metric=score_metric,
        score_direction=score_direction,
        best_row=best_row,
        results=results,
        recommendations=recommendations,
        optimizer_report_paths=optimizer_report_paths,
    )
    _json_dump(output_dir / "summary.json", {k: v for k, v in asdict(summary).items() if k != "results"})
    return summary