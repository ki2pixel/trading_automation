from __future__ import annotations

from dataclasses import asdict, dataclass
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from itertools import product
import json
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, Literal, TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from .strategies.hma_crossover import HMAConfigOverrides

import pandas as pd

from .configuration import active_parameter_values, canonical_parameter_key, parameter_definitions
from .data import BASE_TIMEFRAME_MINUTES, canonical_market_data_subdir, load_canonical_market_data, validate_timeframe_minutes
from .reports import (
    BENCHMARK_METRICS,
    CAPITAL_METRICS,
    PERFORMANCE_METRICS,
    RUNUP_DRAWDOWN_METRICS,
    SIDE_METRICS,
    SUMMARY_METRICS,
    TRADE_METRICS,
    write_backtest_outputs,
    write_optimizer_reports,
)
from .report_interpreter import write_optimization_recommendations
from .strategy_registry import StrategyRegistry
from .paths import get_reports_dir




ParameterKind = Literal["numeric", "choice", "bool"]
ScoreDirection = Literal["max", "min"]

_WORKER_DATA: pd.DataFrame | None = None
_WORKER_SYMBOL: str | None = None
_WORKER_FIXED_OVERRIDES: Any | None = None
_WORKER_INITIAL_CAPITAL: float = 1000.0
_WORKER_STRATEGY: str = "hma_crossover"
_WORKER_SCORE_METRIC: str = "sharpe_ratio"
_WORKER_MIN_CLOSED_TRADES: int = 1
_WORKER_TIMEFRAME_MINUTES: int | str = BASE_TIMEFRAME_MINUTES
_WORKER_EARLY_STOP_DRAWDOWN_PCT: float | None = None
_WORKER_WFO_WINDOWS: int = 1
_WORKER_REPO_ROOT: Path | None = None
_WORKER_CONSTRAINTS: OptimizationConstraints | None = None

@dataclass(frozen=True)
class OptimizableParameter:
    name: str
    kind: ParameterKind
    value_type: str
    description: str
    choices: list[str] | None = None
    default_start: float | int | None = None
    default_end: float | int | None = None
    default_step: float | int | None = None


@dataclass(frozen=True)
class ParameterGridSpec:
    name: str
    kind: ParameterKind
    values: tuple[object, ...]


@dataclass
class OptimizationProgress:
    current_iteration: int
    total_iterations: int
    current_parameters: dict[str, object]
    best_score: float | None
    best_parameters: dict[str, object] | None
    output_dir: str | None = None
    best_row: dict | None = None
    convergence_status: dict | None = None


@dataclass
class OptimizationSummary:
    output_dir: Path
    iterations_completed: int
    total_iterations: int
    eligible_iterations: int
    skipped_iterations: int
    status: str
    score_metric: str
    score_direction: ScoreDirection
    best_row: dict | None
    results: list[dict]
    recommendations: dict | None = None
    optimizer_report_paths: dict[str, str] | None = None


@dataclass(frozen=True)
class OptimizationConstraints:
    max_drawdown_pct: float | None = None
    min_exposure_pct: float | None = None
    min_profit_factor: float | None = None

    def active(self) -> bool:
        return any(value is not None for value in (self.max_drawdown_pct, self.min_exposure_pct, self.min_profit_factor))


def _optional_float(value: object, label: str) -> float | None:
    if value in (None, ""):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid numeric value for {label}: {value!r}") from exc
    if math.isnan(result):
        raise ValueError(f"Invalid numeric value for {label}: {value!r}")
    return result


def build_optimization_constraints(
    *,
    max_drawdown_pct: object = None,
    min_exposure_pct: object = None,
    min_profit_factor: object = None,
) -> OptimizationConstraints:
    max_dd = _optional_float(max_drawdown_pct, "max_drawdown_pct")
    min_exposure = _optional_float(min_exposure_pct, "min_exposure_pct")
    min_pf = _optional_float(min_profit_factor, "min_profit_factor")
    if min_exposure is not None and min_exposure < 0:
        raise ValueError("min_exposure_pct must be >= 0")
    if min_pf is not None and min_pf < 0:
        raise ValueError("min_profit_factor must be >= 0")
    return OptimizationConstraints(
        max_drawdown_pct=max_dd,
        min_exposure_pct=min_exposure,
        min_profit_factor=min_pf,
    )


def _optimizer_metadata_from_schema(strategy: str = "hma_crossover") -> dict[str, OptimizableParameter]:
    return {
        name: OptimizableParameter(
            name=definition.name,
            kind=definition.kind,
            value_type=definition.value_type,
            description=definition.description,
            choices=definition.choices,
            default_start=definition.default_start,
            default_end=definition.default_end,
            default_step=definition.default_step,
        )
        for name, definition in parameter_definitions(strategy, optimizable_only=True).items()
    }


OPTIMIZABLE_HMA_PARAMETERS: dict[str, OptimizableParameter] = _optimizer_metadata_from_schema("hma_crossover")

NON_SCORABLE_METRICS = {"symbol", "strategy", "start", "end"}
ALLOWED_SCORE_METRICS = tuple(
    metric
    for metric in dict.fromkeys(
        SUMMARY_METRICS
        + PERFORMANCE_METRICS
        + TRADE_METRICS
        + SIDE_METRICS
        + BENCHMARK_METRICS
        + CAPITAL_METRICS
        + RUNUP_DRAWDOWN_METRICS
    )
    if metric not in NON_SCORABLE_METRICS
)


def optimizable_parameters(strategy: str = "hma_crossover") -> dict[str, OptimizableParameter]:
    if strategy not in ("hma_crossover", "adaptive_volatility_trend", "range_filter", "3commas_bot", "pmax_explorer", "bjorgum_double_tap", "noise_boundary_intraday"):
        raise ValueError(f"Unsupported strategy for optimization: {strategy}")
    return _optimizer_metadata_from_schema(strategy)


def allowed_score_metrics(strategy: str = "hma_crossover") -> tuple[str, ...]:
    if strategy not in ("hma_crossover", "adaptive_volatility_trend", "range_filter", "3commas_bot", "pmax_explorer", "bjorgum_double_tap", "noise_boundary_intraday"):
        raise ValueError(f"Unsupported strategy for optimization: {strategy}")
    return ALLOWED_SCORE_METRICS


def validate_score_metric(score_metric: str, strategy: str = "hma_crossover") -> str:
    metric = str(score_metric or "").strip()
    allowed = allowed_score_metrics(strategy)
    if metric not in allowed:
        preview = ", ".join(allowed[:10])
        suffix = "..." if len(allowed) > 10 else ""
        raise ValueError(f"Unsupported score_metric {metric!r}; allowed metrics include: {preview}{suffix}")
    return metric


def list_canonical_symbols(
    repo_root: Path,
    processed_dir: str | Path = "storage/processed",
    timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES,
) -> list[str]:
    minutes = validate_timeframe_minutes(timeframe_minutes)
    root = Path(processed_dir)
    if not root.is_absolute():
        root = repo_root / root

    def get_symbols_for_minutes(m: int) -> set[str]:
        try:
            m_val = validate_timeframe_minutes(m)
        except ValueError:
            return set()
        market_dir = root / canonical_market_data_subdir(m_val)
        if not market_dir.exists():
            return set()
        symbols = set()
        for path in market_dir.glob("*.parquet"):
            symbols.add(path.stem)
        for path in market_dir.glob("*.csv.gz"):
            symbols.add(path.name.removesuffix(".csv.gz"))
        return symbols

    if minutes == 1:
        return sorted(get_symbols_for_minutes(1))

    # For minutes > 1: return the union of minutes, 1m, and 5m symbols
    symbols = get_symbols_for_minutes(minutes)
    symbols.update(get_symbols_for_minutes(1))
    symbols.update(get_symbols_for_minutes(5))
    return sorted(symbols)


def _to_decimal(value: object, label: str) -> Decimal:
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, AttributeError) as exc:
        raise ValueError(f"Invalid numeric value for {label}: {value!r}") from exc


def _coerce_value(value: Decimal | str | bool, metadata: OptimizableParameter) -> object:
    if metadata.value_type == "int":
        decimal_value = value if isinstance(value, Decimal) else _to_decimal(value, metadata.name)
        if decimal_value != decimal_value.to_integral_value():
            raise ValueError(f"Parameter {metadata.name} expects integer values, got {value!r}")
        return int(decimal_value)
    if metadata.value_type == "float":
        decimal_value = value if isinstance(value, Decimal) else _to_decimal(value, metadata.name)
        return float(decimal_value)
    if metadata.value_type == "bool":
        if isinstance(value, bool):
            return value
        normalized = str(value).strip().lower()
        if normalized in {"true", "1", "yes", "y", "on"}:
            return True
        if normalized in {"false", "0", "no", "n", "off"}:
            return False
        raise ValueError(f"Parameter {metadata.name} expects boolean values, got {value!r}")
    return str(value)


def build_numeric_values(name: str, start: object, end: object, step: object, strategy: str = "hma_crossover") -> tuple[object, ...]:
    metadata = optimizable_parameters(strategy)[name]
    start_dec = _to_decimal(start, f"{name}.start")
    end_dec = _to_decimal(end, f"{name}.end")
    step_dec = _to_decimal(step, f"{name}.step")
    if step_dec <= 0:
        raise ValueError(f"Step must be > 0 for {name}")
    if start_dec > end_dec:
        raise ValueError(f"Start must be <= end for {name}")

    # Round float values to step precision to avoid fp artefacts in grid specs
    step_exp = step_dec.as_tuple().exponent
    ndigits = max(0, int(-step_exp)) if isinstance(step_exp, int) else 10
    quant = Decimal(10) ** (-ndigits) if ndigits > 0 else None

    values: list[object] = []
    current = start_dec
    guard = 0
    while current <= end_dec:
        if quant is not None and metadata.value_type == "float":
            current = current.quantize(quant)
        values.append(_coerce_value(current, metadata))
        current += step_dec
        guard += 1
        if guard > 1_000_000:
            raise ValueError(f"Too many generated values for {name}; check start/end/step")
    return tuple(values)


def build_parameter_spec(name: str, raw: object, strategy: str = "hma_crossover") -> ParameterGridSpec:
    metadata = optimizable_parameters(strategy).get(name)
    if metadata is None:
        raise ValueError(f"Unsupported optimizer parameter {name!r}")

    if isinstance(raw, dict):
        kind = raw.get("kind") or raw.get("type") or metadata.kind
        if kind == "numeric":
            start = raw.get("start") if raw.get("start") not in (None, "") else metadata.default_start
            end = raw.get("end") if raw.get("end") not in (None, "") else metadata.default_end
            step = raw.get("step") if raw.get("step") not in (None, "") else metadata.default_step
            values = build_numeric_values(name, start, end, step, strategy=strategy)
        else:
            raw_values = raw.get("values") or raw.get("options")
            if not isinstance(raw_values, list) or not raw_values:
                raise ValueError(f"Parameter {name} requires a non-empty values/options list")
            values = tuple(_coerce_value(value, metadata) for value in raw_values)
    elif isinstance(raw, str) and ":" in raw and "|" not in raw:
        start, end, step = raw.split(":", 2)
        values = build_numeric_values(name, start, end, step, strategy=strategy)
        kind = "numeric"
    elif isinstance(raw, str):
        values = tuple(_coerce_value(value, metadata) for value in raw.split("|") if value != "")
        kind = metadata.kind if metadata.kind in {"choice", "bool"} else "choice"
    elif isinstance(raw, Iterable):
        values = tuple(_coerce_value(value, metadata) for value in raw)
        kind = metadata.kind if metadata.kind in {"choice", "bool"} else "choice"
    else:
        values = (_coerce_value(raw, metadata),)
        kind = metadata.kind

    if not values:
        raise ValueError(f"Parameter {name} generated no value")
    if metadata.choices is not None:
        allowed = set(metadata.choices)
        for value in values:
            if metadata.value_type == "bool":
                continue
            if str(value) not in allowed:
                raise ValueError(f"Invalid choice for {name}: {value!r}; allowed: {metadata.choices}")
    return ParameterGridSpec(name=name, kind=kind, values=values)


def parse_cli_parameter(value: str, strategy: str = "hma_crossover") -> ParameterGridSpec:
    if "=" not in value:
        raise ValueError(f"Invalid --param {value!r}; expected NAME=START:END:STEP or NAME=A|B")
    name, raw = value.split("=", 1)
    return build_parameter_spec(name.strip(), raw.strip(), strategy=strategy)


def estimate_iterations(specs: Iterable[ParameterGridSpec]) -> int:
    total = 1
    for spec in specs:
        total *= len(spec.values)
    return total


def generate_parameter_grid(specs: list[ParameterGridSpec]) -> Iterable[dict[str, object]]:
    names = [spec.name for spec in specs]
    for combo in product(*(spec.values for spec in specs)):
        yield dict(zip(names, combo))




def _merged_strategy_overrides(strategy: str, base: Any | None, parameters: dict[str, object]) -> Any:
    override_cls = StrategyRegistry.get(strategy).config_override_class
    payload = asdict(base or override_cls())
    payload.update(parameters)
    allowed = set(override_cls.__dataclass_fields__.keys())
    return override_cls(**{key: value for key, value in payload.items() if key in allowed})

def _merged_hma_overrides(base: HMAConfigOverrides | None, parameters: dict[str, object]) -> HMAConfigOverrides:
    return _merged_strategy_overrides("hma_crossover", base, parameters)


def _merged_parameter_payload(strategy: str, base: Any | None, parameters: dict[str, object]) -> dict[str, object]:
    override_cls = StrategyRegistry.get(strategy).config_override_class
    payload = {key: value for key, value in asdict(base or override_cls()).items() if value is not None}
    payload.update(parameters)
    return payload


def _active_hma_parameters(strategy: str, base: Any | None, parameters: dict[str, object]) -> dict[str, object]:
    active_names = set(active_parameter_values(strategy, _merged_parameter_payload(strategy, base, parameters)).keys())
    return {key: value for key, value in parameters.items() if key in active_names}


def _canonical_hma_grid_items(
    parameter_specs: list[ParameterGridSpec],
    fixed_overrides: Any | None = None,
    strategy: str = "hma_crossover",
) -> list[tuple[int, dict[str, object], list[int]]]:
    seen: dict[str, tuple[int, dict[str, object], list[int]]] = {}
    for raw_iteration, parameters in enumerate(generate_parameter_grid(parameter_specs), start=1):
        active_parameters = _active_hma_parameters(strategy, fixed_overrides, parameters)
        key_payload = _merged_parameter_payload(strategy, fixed_overrides, active_parameters)
        key = canonical_parameter_key(strategy, key_payload)
        if key not in seen:
            seen[key] = (raw_iteration, active_parameters, [raw_iteration])
        else:
            seen[key][2].append(raw_iteration)
    return list(seen.values())


def validate_range_filter_overrides(overrides: Any) -> list[str]:
    messages: list[str] = []
    for field_name in (
        "estimated_commission_per_order_long",
        "estimated_commission_per_order_short",
        "estimated_slippage_per_side_long",
        "estimated_slippage_per_side_short",
    ):
        value = getattr(overrides, field_name, None)
        if value is not None and value < 0:
            messages.append(f"{field_name} must be >= 0")
    return messages


def validate_hma_overrides(overrides: Any) -> list[str]:
    """Return validation messages for HMA configurations that should not be run.

    A HMA crossover with ``fast_len >= slow_len`` is either meaningless
    (parallel lines) or inverts the intended signal.  We also guard against
    negative quantity precision.
    """
    messages: list[str] = []
    fast_len = overrides.fast_len if overrides.fast_len is not None else 20
    slow_len = overrides.slow_len if overrides.slow_len is not None else 55
    if fast_len >= slow_len:
        messages.append("fast_len must be strictly lower than slow_len for hma_crossover")
    if overrides.quantity_precision is not None and overrides.quantity_precision < 0:
        messages.append("quantity_precision must be >= 0")
    for field_name in (
        "estimated_commission_per_order_long",
        "estimated_commission_per_order_short",
        "estimated_slippage_per_side_long",
        "estimated_slippage_per_side_short",
    ):
        value = getattr(overrides, field_name, None)
        if value is not None and value < 0:
            messages.append(f"{field_name} must be >= 0")
    return messages


def validate_parameter_grid(
    parameter_specs: list[ParameterGridSpec],
    fixed_overrides: Any | None = None,
    strategy: str = "hma_crossover",
    max_examples: int = 5,
    optimization_mode: str = "grid",
) -> dict:
    total = estimate_iterations(parameter_specs)
    
    if optimization_mode == "bayesian":
        return {
            "total_iterations": total,
            "canonical_iterations": total,
            "valid_iterations": total,
            "skipped_iterations": 0,
            "deduplicated_inactive_iterations": 0,
            "skipped_examples": [],
        }

    canonical_items = _canonical_hma_grid_items(parameter_specs, fixed_overrides=fixed_overrides, strategy=strategy)
    valid = 0
    skipped = 0
    examples: list[dict] = []
    canonical_skipped = total - len(canonical_items)
    for _, parameters, raw_iterations in canonical_items:
        overrides = _merged_strategy_overrides(strategy, fixed_overrides, parameters)
        if strategy == "hma_crossover":
            messages = validate_hma_overrides(overrides)
        elif strategy == "range_filter":
            messages = validate_range_filter_overrides(overrides)
        else:
            messages = []
        if messages:
            skipped += 1
            if len(examples) < max_examples:
                examples.append({"parameters": parameters, "raw_iterations": raw_iterations, "reasons": messages})
        else:
            valid += 1
    return {
        "total_iterations": total,
        "canonical_iterations": len(canonical_items),
        "valid_iterations": valid,
        "skipped_iterations": skipped,
        "deduplicated_inactive_iterations": canonical_skipped,
        "skipped_examples": examples,
    }


def validate_iteration_limits(
    *,
    raw_iterations: int,
    canonical_iterations: int,
    max_raw_iterations: int | None = None,
    max_canonical_iterations: int | None = None,
) -> None:
    if max_raw_iterations is not None and raw_iterations > max_raw_iterations:
        raise ValueError(
            f"Optimization grid has {raw_iterations} raw iterations, above raw limit {max_raw_iterations}. "
            "Increase max_raw_iterations or reduce the grid before inactive-parameter deduplication."
        )
    if max_canonical_iterations is not None and canonical_iterations > max_canonical_iterations:
        raise ValueError(
            f"Optimization grid has {canonical_iterations} canonical iterations, above canonical limit {max_canonical_iterations}. "
            "Increase max_canonical_iterations or reduce the effective deduplicated grid."
        )


def _score_value(metrics: dict, score_metric: str) -> float | None:
    value = metrics.get(score_metric)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


import math

def _is_better(score: float | None, best_score: float | None, direction: ScoreDirection) -> bool:
    if score is None or (isinstance(score, float) and math.isnan(score)):
        return False
    if best_score is None or (isinstance(best_score, float) and math.isnan(best_score)):
        return True
    return score > best_score if direction == "max" else score < best_score


def _constraint_violations(
    metrics: dict,
    *,
    total_trades: int,
    min_closed_trades: int,
    constraints: OptimizationConstraints | None,
) -> list[str]:
    if constraints is None or not constraints.active():
        return []

    violations: list[str] = []
    if min_closed_trades > 0 and total_trades < min_closed_trades:
        violations.append(f"closed_trades {total_trades} < min_closed_trades {min_closed_trades}")

    if constraints.min_exposure_pct is not None:
        exposure = _score_value(metrics, "exposure_pct")
        if exposure is None or exposure < constraints.min_exposure_pct:
            violations.append(f"exposure_pct {exposure} < min_exposure_pct {constraints.min_exposure_pct}")

    if constraints.max_drawdown_pct is not None:
        max_drawdown = _score_value(metrics, "max_drawdown_pct")
        drawdown_floor = -abs(constraints.max_drawdown_pct)
        if max_drawdown is None or max_drawdown < drawdown_floor:
            violations.append(f"max_drawdown_pct {max_drawdown} < allowed {drawdown_floor}")

    if constraints.min_profit_factor is not None:
        profit_factor = _score_value(metrics, "profit_factor")
        if profit_factor is None or profit_factor < constraints.min_profit_factor:
            violations.append(f"profit_factor {profit_factor} < min_profit_factor {constraints.min_profit_factor}")

    return violations


def _evaluate_hma_parameters(
    *,
    data: pd.DataFrame,
    symbol: str,
    parameters: dict[str, object],
    iteration: int,
    fixed_overrides: Any | None,
    initial_capital: float,
    strategy: str,
    score_metric: str,
    min_closed_trades: int,
    timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES,
    early_stop_drawdown_pct: float | None = None,
    wfo_windows: int = 1,
    repo_root: Path | None = None,
    constraints: OptimizationConstraints | None = None,
) -> tuple[dict, bool, bool]:
    overrides = _merged_strategy_overrides(strategy, fixed_overrides, parameters)
    if strategy == "hma_crossover":
        validation_messages = validate_hma_overrides(overrides)
    elif strategy == "range_filter":
        validation_messages = validate_range_filter_overrides(overrides)
    else:
        validation_messages = []
    if validation_messages:
        return (
            {
                "iteration": iteration,
                "status": "SKIPPED_INVALID_PARAMETERS",
                "skip_reason": "; ".join(validation_messages),
                "score": None,
                "parameters": parameters,
                "metrics": {},
            },
            False,
            True,
        )

    if wfo_windows <= 1:
        chunks = [data]
    else:
        chunk_size = max(1, len(data) // wfo_windows)
        chunks = [data.iloc[i * chunk_size : (i + 1) * chunk_size] for i in range(wfo_windows)]

    scores = []
    total_trades = 0
    all_metrics = {}

    for i, chunk in enumerate(chunks):
        if len(chunk) == 0:
            continue
        runner = StrategyRegistry.get(strategy).run_function
        result = runner(
            data=chunk,
            symbol=symbol,
            overrides=overrides,
            initial_capital=initial_capital,
            timeframe_minutes=timeframe_minutes,
            compute_full_metrics=False,
            fast_score_metric=score_metric,
            repo_root=repo_root,
        )
        closed_trades = int(result.metrics.get("closed_trades") or 0)
        total_trades += closed_trades
        has_missing_constraint_metrics = False
        if constraints is not None and constraints.active():
            required_metrics = []
            if constraints.min_exposure_pct is not None:
                required_metrics.append("exposure_pct")
            if constraints.max_drawdown_pct is not None:
                required_metrics.append("max_drawdown_pct")
            if constraints.min_profit_factor is not None:
                required_metrics.append("profit_factor")
            for m in required_metrics:
                if m not in result.metrics:
                    has_missing_constraint_metrics = True
                    break

        if score_metric not in result.metrics or has_missing_constraint_metrics:
            from .metrics import compute_metrics, MetricsInput
            metrics, equity_curve = compute_metrics(
                MetricsInput(
                    symbol=symbol,
                    strategy=strategy,
                    initial_capital=initial_capital,
                    bars=result.bars,
                    state=result.state,
                    trades=result.trades,
                    timeframe_minutes=timeframe_minutes,
                )
            )
            result.metrics.update(metrics)
            result.equity_curve = equity_curve

        score = _score_value(result.metrics, score_metric)
        if score is None or (isinstance(score, float) and math.isnan(score)):
            score = 0.0
        scores.append(score)

        if i == 0:
            all_metrics = result.metrics.copy()

    # Safety check for WFO chunks missing entirely (e.g. error/empty chunk)
    if wfo_windows > 1 and len(scores) != wfo_windows:
        return (
            {
                "iteration": iteration,
                "status": "INELIGIBLE_WFO",
                "skip_reason": f"Missing valid scores in WFO (got {len(scores)}/{wfo_windows})",
                "score": None,
                "parameters": parameters,
                "metrics": all_metrics,
            },
            False,
            True,
        )

    is_eligible = (total_trades >= min_closed_trades) if wfo_windows <= 1 else (len(scores) == wfo_windows)
    avg_score = sum(scores) / len(scores) if scores else 0.0
    constraint_violations = _constraint_violations(
        all_metrics,
        total_trades=total_trades,
        min_closed_trades=min_closed_trades,
        constraints=constraints,
    )
    if constraint_violations:
        return (
            {
                "iteration": iteration,
                "status": "INELIGIBLE_CONSTRAINTS",
                "skip_reason": "; ".join(constraint_violations),
                "score": None,
                "parameters": parameters,
                "metrics": all_metrics,
            },
            False,
            True,
        )

    if strategy == "noise_boundary_intraday":
        if score_metric == "total_net_pnl":
            sharpe_ratio = all_metrics.get("sharpe_ratio")
            if sharpe_ratio is None or sharpe_ratio < 1.0:
                return (
                    {
                        "iteration": iteration,
                        "status": "INELIGIBLE_LOW_SHARPE",
                        "skip_reason": f"sharpe_ratio {sharpe_ratio} < 1.0",
                        "score": None,
                        "parameters": parameters,
                        "metrics": all_metrics,
                    },
                    False,
                    True,
                )
        if min_closed_trades > 0 and total_trades < min_closed_trades:
            penalty_factor = total_trades / min_closed_trades
            if avg_score > 0:
                avg_score = avg_score * penalty_factor
            elif avg_score < 0:
                if penalty_factor > 0:
                    avg_score = avg_score / penalty_factor
                else:
                    avg_score = -100.0
    else:
        if not is_eligible or not scores:
            return (
                {
                    "iteration": iteration,
                    "status": "SKIPPED_MIN_TRADES" if wfo_windows <= 1 else "INELIGIBLE_WFO",
                    "skip_reason": f"closed_trades {total_trades} < min_closed_trades {min_closed_trades}" if wfo_windows <= 1 else f"Missing valid scores in WFO (got {len(scores)}/{wfo_windows})",
                    "score": None,
                    "parameters": parameters,
                    "metrics": {},
                },
                False,
                True,
            )

    return (
        {
            "iteration": iteration,
            "status": "COMPLETED",
            "skip_reason": None,
            "score": avg_score,
            "parameters": parameters,
            "metrics": all_metrics,
        },
        is_eligible,
        False,
    )


def _init_worker(
    data: pd.DataFrame,
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
    constraints: OptimizationConstraints | None = None,
) -> None:
    global _WORKER_DATA, _WORKER_SYMBOL, _WORKER_FIXED_OVERRIDES, _WORKER_INITIAL_CAPITAL
    global _WORKER_STRATEGY, _WORKER_SCORE_METRIC, _WORKER_MIN_CLOSED_TRADES, _WORKER_TIMEFRAME_MINUTES
    global _WORKER_EARLY_STOP_DRAWDOWN_PCT, _WORKER_WFO_WINDOWS, _WORKER_REPO_ROOT, _WORKER_CONSTRAINTS
    _WORKER_DATA = data
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
    # Reset strategy-specific feature cache for this worker via the registry.
    info = StrategyRegistry.get(strategy)
    if info.clear_feature_cache is not None:
        info.clear_feature_cache()


def _evaluate_worker(payload: tuple[int, dict[str, object]]) -> tuple[dict, bool, bool]:
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
        wfo_windows=getattr(sys.modules[__name__], "_WORKER_WFO_WINDOWS", 1),
        repo_root=getattr(sys.modules[__name__], "_WORKER_REPO_ROOT", None),
        constraints=getattr(sys.modules[__name__], "_WORKER_CONSTRAINTS", None),
    )


def _json_dump(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def create_optimization_output_dir(output_root: Path, strategy: str, symbol: str, job_id: str | None = None) -> Path:
    for _ in range(10):
        suffix = f"-{job_id}" if job_id else f"-{uuid4().hex[:8]}"
        run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}{suffix}"
        output_dir = output_root / strategy / symbol / run_id
        try:
            output_dir.mkdir(parents=True, exist_ok=False)
            return output_dir
        except FileExistsError:
            continue
    raise FileExistsError("Unable to create a unique optimization output directory")


def run_grid_optimization(
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
    max_iterations: int | None = 10000,
    max_raw_iterations: int | None = None,
    max_canonical_iterations: int | None = None,
    min_closed_trades: int = 1,
    workers: int = 1,
    write_best_run: bool = True,
    progress_callback: Callable[[OptimizationProgress], None] | None = None,
    stop_requested: Callable[[], bool] | None = None,
    early_stop_drawdown_pct: float | None = None,
    repo_root: Path | None = None,
    constraints: OptimizationConstraints | None = None,
    job_id: str | None = None,
) -> OptimizationSummary:
    if output_root is None:
        output_root = get_reports_dir() / "local_optimizer"
    if strategy not in ("hma_crossover", "adaptive_volatility_trend", "range_filter", "pmax_explorer", "3commas_bot", "bjorgum_double_tap", "noise_boundary_intraday"):
        raise ValueError(f"Unsupported strategy for optimization: {strategy}")
    score_metric = validate_score_metric(score_metric, strategy=strategy)
    minutes = validate_timeframe_minutes(timeframe_minutes)
    total_iterations = estimate_iterations(parameter_specs)
    if total_iterations <= 0:
        raise ValueError("Optimization grid is empty")
    if min_closed_trades < 0:
        raise ValueError("min_closed_trades must be >= 0")
    if workers < 1:
        raise ValueError("workers must be >= 1")
    constraints = constraints or OptimizationConstraints()

    grid_validation = validate_parameter_grid(parameter_specs, fixed_overrides=fixed_overrides, strategy=strategy, optimization_mode="grid")
    canonical_grid_items = _canonical_hma_grid_items(parameter_specs, fixed_overrides=fixed_overrides, strategy=strategy)
    actual_iterations = len(canonical_grid_items)
    validate_iteration_limits(
        raw_iterations=total_iterations,
        canonical_iterations=actual_iterations,
        max_raw_iterations=max_iterations if max_raw_iterations is None else max_raw_iterations,
        max_canonical_iterations=max_iterations if max_canonical_iterations is None else max_canonical_iterations,
    )

    output_dir = create_optimization_output_dir(output_root, strategy, symbol, job_id=job_id)
    optimization_config = {
        "strategy": strategy,
        "symbol": symbol,
        "timeframe_minutes": minutes,
        "start_date": start_date,
        "end_date": end_date,
        "score_metric": score_metric,
        "score_direction": score_direction,
        "total_iterations": total_iterations,
        "canonical_iterations": actual_iterations,
        "valid_iterations": grid_validation["valid_iterations"],
        "skipped_iterations": grid_validation["skipped_iterations"],
        "deduplicated_inactive_iterations": grid_validation["deduplicated_inactive_iterations"],
        "min_closed_trades": min_closed_trades,
        "workers": workers,
        "constraints": asdict(constraints),
        "fixed_overrides": asdict(fixed_overrides or StrategyRegistry.get(strategy).config_override_class()),
        "parameters": [asdict(spec) for spec in parameter_specs],
    }
    _json_dump(output_dir / "optimization_config.json", optimization_config)

    results: list[dict] = []
    best_row: dict | None = None
    best_score: float | None = None
    status = "FINISHED"
    eligible_iterations = 0
    skipped_iterations = 0

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
        if progress_callback is not None:
            progress_callback(
                OptimizationProgress(
                    current_iteration=completed_count,
                    total_iterations=actual_iterations,
                    current_parameters=row.get("parameters", {}),
                    best_score=best_score,
                    best_parameters=best_row.get("parameters") if best_row else None,
                    output_dir=str(output_dir),
                    best_row=best_row,
                )
            )

    if workers == 1:
        # Phase 3: Ensure strategy-specific feature cache is clean.
        info = StrategyRegistry.get(strategy)
        if info.clear_feature_cache is not None:
            info.clear_feature_cache()
        for completed_count, (iteration, parameters, raw_iterations) in enumerate(canonical_grid_items, start=1):
            if stop_requested is not None and stop_requested():
                status = "CANCELLED"
                break
            row, is_eligible, is_skipped = _evaluate_hma_parameters(
                data=data,
                symbol=symbol,
                parameters=parameters,
                iteration=iteration,
                fixed_overrides=fixed_overrides,
                initial_capital=initial_capital,
                strategy=strategy,
                score_metric=score_metric,
                min_closed_trades=min_closed_trades,
                timeframe_minutes=minutes,
                early_stop_drawdown_pct=early_stop_drawdown_pct,
                repo_root=repo_root,
                constraints=constraints,
            )
            row["raw_iterations"] = raw_iterations
            handle_row(row, is_eligible, is_skipped, completed_count)
    else:
        completed_count = 0
        executor = ProcessPoolExecutor(
            max_workers=workers,
            initializer=_init_worker,
            initargs=(data, symbol, fixed_overrides, initial_capital, strategy, score_metric, min_closed_trades, minutes, early_stop_drawdown_pct, 1, repo_root, constraints),
        )
        cancelled = False

        def cancel_pending(futures: dict) -> None:
            for pending in futures:
                pending.cancel()
            futures.clear()
            for p in getattr(executor, "_processes", {}).values():
                try:
                    p.terminate()
                except Exception:  # NOSONAR
                    pass

        try:
            item_iter = iter(canonical_grid_items)
            futures: dict = {}
            max_pending = workers

            def submit_next() -> bool:
                try:
                    iteration, parameters, raw_iterations = next(item_iter)
                except StopIteration:
                    return False
                future = executor.submit(_evaluate_worker, (iteration, parameters))
                futures[future] = raw_iterations
                return True

            for _ in range(min(max_pending, actual_iterations)):
                submit_next()

            while futures:
                if stop_requested is not None and stop_requested():
                    status = "CANCELLED"
                    cancelled = True
                    cancel_pending(futures)
                    break
                done, _ = wait(futures, timeout=0.2, return_when=FIRST_COMPLETED)
                if not done:
                    continue
                for future in done:
                    raw_iterations = futures.pop(future)
                    completed_count += 1
                    row, is_eligible, is_skipped = future.result()
                    row["raw_iterations"] = raw_iterations
                    handle_row(row, is_eligible, is_skipped, completed_count)
                    if stop_requested is not None and stop_requested():
                        status = "CANCELLED"
                        cancelled = True
                        cancel_pending(futures)
                        break
                    submit_next()
        finally:
            executor.shutdown(wait=not cancelled, cancel_futures=True)

    if best_row is None:
        _json_dump(output_dir / "best.json", None)
    elif write_best_run:
        best_runner = StrategyRegistry.get(strategy).run_function
        best_result = best_runner(
            data=data,
            symbol=symbol,
            overrides=_merged_strategy_overrides(strategy, fixed_overrides, best_row.get("parameters", {})),
            initial_capital=initial_capital,
            timeframe_minutes=minutes,
            repo_root=repo_root,
        )
        best_run_dir = write_backtest_outputs(best_result, output_dir / "best_backtest")
        best_row["best_backtest_dir"] = str(best_run_dir)
        _json_dump(output_dir / "best.json", best_row)
    results.sort(key=lambda item: int(item.get("iteration", 0)))
    _write_results(output_dir, results)
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
        total_iterations=total_iterations,
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


def _write_results(output_dir: Path, results: list[dict]) -> None:
    _json_dump(output_dir / "results.json", results)
    rows: list[dict] = []
    for item in results:
        row = {
            "iteration": item["iteration"],
            "status": item.get("status"),
            "skip_reason": item.get("skip_reason"),
            "score": item.get("score"),
        }
        row.update({f"param_{key}": value for key, value in item.get("parameters", {}).items()})
        row.update(item.get("metrics", {}))
        rows.append(row)
    pd.DataFrame(rows).to_parquet(output_dir / "results.parquet", index=False, engine="pyarrow", compression="zstd")


def load_data_and_optimize(
    *,
    repo_root: Path,
    symbol: str,
    parameter_specs: list[ParameterGridSpec],
    processed_dir: str | Path = "storage/processed",
    timeframe_minutes: int | str = BASE_TIMEFRAME_MINUTES,
    start_date: str | None = None,
    end_date: str | None = None,
    fixed_overrides: Any | None = None,
    initial_capital: float = 1000.0,
    output_root: Path | None = None,
    strategy: str = "hma_crossover",
    score_metric: str = "sharpe_ratio",
    score_direction: ScoreDirection = "max",
    secondary_score_metric: str | None = None,
    secondary_score_direction: ScoreDirection = "max",
    max_rows: int | None = None,
    max_iterations: int | None = 10000,
    max_raw_iterations: int | None = None,
    max_canonical_iterations: int | None = None,
    min_closed_trades: int = 1,
    workers: int = 1,
    write_best_run: bool = True,
    progress_callback: Callable[[OptimizationProgress], None] | None = None,
    stop_requested: Callable[[], bool] | None = None,
    early_stop_drawdown_pct: float | None = None,
    optimization_mode: str = "grid",
    enable_convergence_stop: bool = True,
    convergence_patience: int = 100,
    convergence_min_improvement: float = 0.01,
    convergence_window_size: int = 50,
    convergence_window_count: int = 3,
    circuit_breaker_ratio: float = 0.2,
    wfo_windows: int = 1,
    use_vectorbt_prescan: bool = False,
    run_post_validation: bool = False,
    prescan_progress_callback: Callable[[int, int], None] | None = None,
    apply_market_hours: bool = True,
    constraints: OptimizationConstraints | None = None,
    job_id: str | None = None,
) -> OptimizationSummary:
    if output_root is None:
        output_root = get_reports_dir(repo_root) / "local_optimizer"
    score_metric = validate_score_metric(score_metric, strategy=strategy)
    data = load_canonical_market_data(
        symbol=symbol,
        repo_root=repo_root,
        processed_dir=processed_dir,
        max_rows=max_rows,
        timeframe_minutes=timeframe_minutes,
        start_date=start_date,
        end_date=end_date,
        apply_market_hours=apply_market_hours,
    )

    if optimization_mode == "bayesian":
        from .bayesian_optimizer import run_bayesian_optimization
        return run_bayesian_optimization(
            data=data,
            symbol=symbol,
            parameter_specs=parameter_specs,
            fixed_overrides=fixed_overrides,
            initial_capital=initial_capital,
            output_root=output_root,
            timeframe_minutes=timeframe_minutes,
            start_date=start_date,
            end_date=end_date,
            strategy=strategy,
            score_metric=score_metric,
            score_direction=score_direction,
            secondary_score_metric=secondary_score_metric,
            secondary_score_direction=secondary_score_direction,
            n_trials=max_iterations or 200,
            min_closed_trades=min_closed_trades,
            workers=workers,
            write_best_run=write_best_run,
            progress_callback=progress_callback,
            stop_requested=stop_requested,
            early_stop_drawdown_pct=early_stop_drawdown_pct,
            enable_convergence_stop=enable_convergence_stop,
            convergence_patience=convergence_patience,
            convergence_min_improvement=convergence_min_improvement,
            convergence_window_size=convergence_window_size,
            convergence_window_count=convergence_window_count,
            circuit_breaker_ratio=circuit_breaker_ratio,
            wfo_windows=wfo_windows,
            use_vectorbt_prescan=use_vectorbt_prescan,
            run_post_validation=run_post_validation,
            repo_root=repo_root,
            prescan_progress_callback=prescan_progress_callback,
            constraints=constraints,
            job_id=job_id,
        )

    return run_grid_optimization(
        data=data,
        symbol=symbol,
        parameter_specs=parameter_specs,
        fixed_overrides=fixed_overrides,
        initial_capital=initial_capital,
        output_root=output_root,
        timeframe_minutes=timeframe_minutes,
        start_date=start_date,
        end_date=end_date,
        strategy=strategy,
        score_metric=score_metric,
        score_direction=score_direction,
        max_iterations=max_iterations,
        max_raw_iterations=max_raw_iterations,
        max_canonical_iterations=max_canonical_iterations,
        min_closed_trades=min_closed_trades,
        workers=workers,
        write_best_run=write_best_run,
        progress_callback=progress_callback,
        stop_requested=stop_requested,
        early_stop_drawdown_pct=early_stop_drawdown_pct,
        repo_root=repo_root,
        constraints=constraints,
        job_id=job_id,
    )
