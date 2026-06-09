from __future__ import annotations

from dataclasses import asdict
import json
import mimetypes
from pathlib import Path
import re
import shutil
import time
from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator
import uvicorn

from .configuration import inactive_parameter_names, load_strategy_config, parameter_definitions
from .data import BASE_TIMEFRAME_MINUTES, get_canonical_market_data_date_bounds, validate_timeframe_minutes
from .job_store import OptimizerJob, OptimizerJobStore
from .optimizer import (
    OptimizationProgress,
    allowed_score_metrics,
    build_optimization_constraints,
    build_parameter_spec,
    estimate_iterations,
    list_canonical_symbols,
    load_data_and_optimize,
    optimizable_parameters,
    validate_iteration_limits,
    validate_score_metric,
    validate_parameter_grid,
)
from .strategy_registry import StrategyRegistry
from .paths import get_reports_dir



ParameterKindPayload = Literal["numeric", "choice", "bool"]
ScoreDirectionPayload = Literal["max", "min"]
StrategyPayload = str


class ParameterSpecPayload(BaseModel):
    """Pydantic representation of a single optimizer parameter row sent by the UI."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(min_length=1)
    kind: ParameterKindPayload | None = None
    start: Any = None
    end: Any = None
    step: Any = None
    values: list[Any] | None = None


class GlobalAnalysisRequest(BaseModel):
    strategy: str = "hma_crossover"
    output_dir: str | None = None


class BulkDeleteRequest(BaseModel):
    job_ids: list[str]



_VIEWER_STRATEGY_INDICATORS: dict[str, list[str]] = {
    name: info.indicators for name, info in StrategyRegistry.all().items()
}


class ViewerChartRequest(BaseModel):
    """Request model for the interactive backtest viewer chart endpoint."""

    model_config = ConfigDict(extra="allow")

    symbol: str = Field(min_length=1)
    timeframe: str = "1h"
    strategy: str = "hma_crossover"
    start_date: Any = None
    end_date: Any = None
    processed_dir: str | None = None
    initial_capital: float = Field(default=1000.0, gt=0)

    @field_validator("strategy")
    @classmethod
    def _validate_strategy(cls, value: str) -> str:
        allowed = set(_VIEWER_STRATEGY_INDICATORS.keys())
        if value not in allowed:
            raise ValueError(f"Invalid strategy {value!r}; expected one of {sorted(allowed)}")
        return value

    @field_validator("symbol", "processed_dir")
    @classmethod
    def _blank_strings_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class OptimizerRequestPayload(BaseModel):
    """Shared request model for /api/estimate and /api/optimize.

    The model keeps optional/default fields compatible with the existing Vanilla JS
    frontend while delegating strategy-specific validation to the optimizer layer.
    """

    model_config = ConfigDict(extra="allow")

    strategy: StrategyPayload = "hma_crossover"
    symbol: str | None = None
    processed_dir: str | None = None
    output_dir: str | None = None
    timeframe_minutes: int = BASE_TIMEFRAME_MINUTES
    start_date: Any = None
    end_date: Any = None
    config: str | None = None
    fixed_overrides: dict[str, Any] | None = None
    initial_capital: float = Field(default=1000.0, gt=0)
    early_stop_drawdown_pct: float | None = Field(default=None, ge=0, le=100)
    optimization_mode: str = Field(default="grid", pattern="^(grid|bayesian)$")
    score_metric: str = "sharpe_ratio"
    score_direction: ScoreDirectionPayload = "max"
    secondary_score_metric: str | None = None
    secondary_score_direction: ScoreDirectionPayload = "max"
    max_iterations: int = Field(default=10000, ge=1)
    workers: int = Field(default=1, ge=1)
    min_closed_trades: int = Field(default=1, ge=0)
    max_drawdown_pct: float | None = None
    min_exposure_pct: float | None = Field(default=None, ge=0)
    min_profit_factor: float | None = Field(default=None, ge=0)
    max_rows: int | None = Field(default=None, ge=1)
    write_best_run: bool = True
    parameters: list[ParameterSpecPayload] = Field(default_factory=list)
    enable_convergence_stop: bool = True
    convergence_patience: int = Field(default=100, ge=1)
    convergence_min_improvement: float = Field(default=0.01, gt=0)
    convergence_window_size: int = Field(default=50, ge=10)
    convergence_window_count: int = Field(default=3, ge=1)
    circuit_breaker_ratio: float = Field(default=0.2, ge=0.0, le=1.0)
    wfo_windows: int = Field(default=1, ge=1)
    use_vectorbt_prescan: bool = False
    run_post_validation: bool = False

    @field_validator("strategy")
    @classmethod
    def _validate_strategy_dynamic(cls, value: str) -> str:
        allowed = set(StrategyRegistry.list_strategies())
        if value not in allowed:
            raise ValueError(f"Invalid strategy {value!r}; expected one of {sorted(allowed)}")
        return value

    @field_validator("symbol", "processed_dir", "output_dir", "config")
    @classmethod
    def _blank_strings_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    def as_legacy_payload(self) -> dict[str, Any]:
        """Return a plain dict matching the old manually parsed JSON payload."""

        return self.model_dump(mode="python")


def resolve_repo_path(repo_root: Path, raw_path: str | Path, label: str) -> Path:
    """Resolve a user-provided path and ensure it remains under repo_root."""
    repo = repo_root.resolve()
    path = Path(raw_path)
    resolved = path.resolve(strict=False) if path.is_absolute() else (repo / path).resolve(strict=False)
    
    # Allow specific external reporting paths dynamically
    reports_dir = get_reports_dir(repo)
    try:
        resolved.relative_to(reports_dir)
        return resolved
    except ValueError:
        pass
        
    try:
        resolved.relative_to(repo)
    except ValueError as exc:
        raise ValueError(f"{label} must stay under repo_root: {raw_path!r}") from exc
    return resolved


def _parameter_specs_from_payload(payload: dict[str, Any]) -> list:
    specs = []
    strategy = str(payload.get("strategy", "hma_crossover"))
    for item in payload.get("parameters", []):
        if not isinstance(item, dict) or not item.get("name"):
            raise ValueError("Each parameter must be an object with a name")
        specs.append(build_parameter_spec(str(item["name"]), item, strategy=strategy))
    if not specs:
        raise ValueError("At least one optimization parameter is required")
    return specs


def _fixed_overrides_from_payload(payload: dict[str, Any], repo_root: Path) -> Any:
    fixed = payload.get("fixed_overrides") or {}
    strategy = str(payload.get("strategy", "hma_crossover"))
    if payload.get("config"):
        config_path = resolve_repo_path(repo_root, str(payload["config"]), "config")
        runtime_config = load_strategy_config(config_path, strategy=strategy)
        fixed = {**runtime_config.parameters, **fixed}
    if not isinstance(fixed, dict):
        raise ValueError("fixed_overrides must be an object")
    cleaned = {key: value for key, value in fixed.items() if value not in ("", None)}
    info = StrategyRegistry.get(strategy)
    return info.overrides_from_mapping_function(cleaned)


def _validate_window_payload(payload: dict[str, Any]) -> None:
    start_raw = payload.get("start_date")
    end_raw = payload.get("end_date")
    start = pd.to_datetime(start_raw, errors="coerce") if start_raw not in (None, "") else None
    end = pd.to_datetime(end_raw, errors="coerce") if end_raw not in (None, "") else None
    if start_raw not in (None, "") and pd.isna(start):
        raise ValueError(f"Invalid start_date: {start_raw!r}")
    if end_raw not in (None, "") and pd.isna(end):
        raise ValueError(f"Invalid end_date: {end_raw!r}")
    if start is not None and end is not None and pd.Timestamp(start) > pd.Timestamp(end):
        raise ValueError(f"start_date must be <= end_date, got {start} > {end}")


def _validate_optional_repo_paths(payload: dict[str, Any], repo_root: Path, labels: tuple[str, ...] = ("processed_dir", "output_dir")) -> None:
    """Validate optional frontend-provided filesystem paths without requiring them."""

    for label in labels:
        raw_path = payload.get(label)
        if raw_path not in (None, ""):
            resolve_repo_path(repo_root, str(raw_path), label)


def _run_job(
    *,
    job_id: str,
    store: OptimizerJobStore,
    repo_root: Path,
    default_processed_dir: str,
    default_output_dir: str,
) -> None:
    job = store.get(job_id)
    if job is None:
        return
    payload = job.request
    try:
        store.update(job_id, status="IN_PROGRESS")
        parameter_specs = _parameter_specs_from_payload(payload)
        strategy = str(payload.get("strategy", "hma_crossover"))
        score_metric = validate_score_metric(str(payload.get("score_metric", "sharpe_ratio")), strategy=strategy)
        fixed_overrides = _fixed_overrides_from_payload(payload, repo_root)
        processed_root = resolve_repo_path(repo_root, payload.get("processed_dir") or default_processed_dir, "processed_dir")
        output_root = resolve_repo_path(repo_root, payload.get("output_dir") or default_output_dir, "output_dir")
        constraints = build_optimization_constraints(
            max_drawdown_pct=payload.get("max_drawdown_pct"),
            min_exposure_pct=payload.get("min_exposure_pct"),
            min_profit_factor=payload.get("min_profit_factor"),
        )
        total_iterations = estimate_iterations(parameter_specs)
        grid_validation = validate_parameter_grid(
            parameter_specs,
            fixed_overrides=fixed_overrides,
            strategy=strategy,
            optimization_mode=payload.get("optimization_mode", "grid"),
        )
        is_bayesian = payload.get("optimization_mode", "grid") == "bayesian"
        target_iterations = int(payload.get("max_iterations", 10000)) if is_bayesian else grid_validation["canonical_iterations"]
        store.update(job_id, progress={"currentIteration": 0, "totalIterations": target_iterations, "rawIterations": total_iterations})

        def on_progress(progress: OptimizationProgress) -> None:
            store.update(
                job_id,
                progress={
                    "currentIteration": progress.current_iteration,
                    "totalIterations": progress.total_iterations,
                    "currentParameters": progress.current_parameters,
                    "bestScore": progress.best_score,
                    "bestParameters": progress.best_parameters,
                    "convergenceStatus": progress.convergence_status,
                },
                best=progress.best_row,
                output_dir=progress.output_dir,
            )

        def stop_requested() -> bool:
            current = store.get(job_id)
            return bool(current and current.cancel_requested)

        def prescan_progress(current_batch: int, total_batches: int) -> None:
            store.update(
                job_id,
                progress={
                    "currentIteration": current_batch,
                    "totalIterations": total_batches,
                    "stage": "prescan",
                }
            )

        summary = load_data_and_optimize(
            repo_root=repo_root,
            symbol=str(payload["symbol"]),
            processed_dir=processed_root,
            timeframe_minutes=payload.get("timeframe_minutes", BASE_TIMEFRAME_MINUTES),
            start_date=payload.get("start_date"),
            end_date=payload.get("end_date"),
            parameter_specs=parameter_specs,
            fixed_overrides=fixed_overrides,
            initial_capital=float(payload.get("initial_capital", 1000.0)),
            output_root=output_root,
            strategy=strategy,
            score_metric=score_metric,
            score_direction=str(payload.get("score_direction", "max")),
            secondary_score_metric=payload.get("secondary_score_metric"),
            secondary_score_direction=str(payload.get("secondary_score_direction", "max")),
            max_rows=payload.get("max_rows"),
            max_iterations=int(payload.get("max_iterations", 10000)),
            min_closed_trades=int(payload.get("min_closed_trades", 1)),
            workers=int(payload.get("workers", 1)),
            write_best_run=bool(payload.get("write_best_run", True)),
            progress_callback=on_progress,
            stop_requested=stop_requested,
            early_stop_drawdown_pct=float(payload["early_stop_drawdown_pct"]) if payload.get("early_stop_drawdown_pct") is not None else None,
            optimization_mode=str(payload.get("optimization_mode", "grid")),
            enable_convergence_stop=bool(payload.get("enable_convergence_stop", True)),
            convergence_patience=int(payload.get("convergence_patience", 100)),
            convergence_min_improvement=float(payload.get("convergence_min_improvement", 0.01)),
            convergence_window_size=int(payload.get("convergence_window_size", 50)),
            convergence_window_count=int(payload.get("convergence_window_count", 3)),
            circuit_breaker_ratio=float(payload.get("circuit_breaker_ratio", 0.2)),
            wfo_windows=int(payload.get("wfo_windows", 1)),
            use_vectorbt_prescan=bool(payload.get("use_vectorbt_prescan", False)),
            run_post_validation=bool(payload.get("run_post_validation", False)),
            prescan_progress_callback=prescan_progress,
            constraints=constraints,
            job_id=job_id,
        )
        existing_job = store.get(job_id)
        existing_progress = existing_job.progress if existing_job else {}

        store.update(
            job_id,
            status=summary.status,
            output_dir=str(summary.output_dir),
            summary={k: v for k, v in asdict(summary).items() if k != "results"},
            best=summary.best_row,
            progress={
                **existing_progress,
                "currentIteration": summary.iterations_completed,
                "totalIterations": target_iterations,
                "rawIterations": total_iterations,
            },
        )
    except Exception as exc:  # noqa: BLE001 - surfaced to local UI
        # Check if output directory was created before the failure and update store
        try:
            strat = payload.get("strategy") if payload else None
            sym = payload.get("symbol") if payload else None
            if strat and sym:
                potential_output_dir = output_root / strat / sym / f"run_{job_id}"
                if potential_output_dir.exists():
                    store.update(job_id, output_dir=str(potential_output_dir))
        except Exception:
            pass
        store.update(job_id, status="FAILED", error=str(exc))


def _estimate_payload(payload: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    timeframe_minutes = validate_timeframe_minutes(payload.get("timeframe_minutes", BASE_TIMEFRAME_MINUTES))
    _validate_window_payload(payload)
    _validate_optional_repo_paths(payload, repo_root)
    specs = _parameter_specs_from_payload(payload)
    strategy = str(payload.get("strategy", "hma_crossover"))
    validate_score_metric(str(payload.get("score_metric", "sharpe_ratio")), strategy=strategy)
    total = estimate_iterations(specs)
    max_iterations = int(payload.get("max_iterations", 10000))
    fixed_overrides = _fixed_overrides_from_payload(payload, repo_root)
    grid_validation = validate_parameter_grid(
        specs,
        fixed_overrides=fixed_overrides,
        strategy=strategy,
        optimization_mode=payload.get("optimization_mode", "grid"),
    )
    warnings = []
    is_grid = payload.get("optimization_mode", "grid") != "bayesian"
    
    if is_grid:
        if total > max_iterations:
            warnings.append(f"La grille brute dépasse la limite configurée ({max_iterations})")
        if grid_validation["canonical_iterations"] > max_iterations:
            warnings.append(f"La grille canonique dépasse la limite configurée ({max_iterations})")
            
    if grid_validation["skipped_iterations"]:
        warnings.append(
            f"{grid_validation['skipped_iterations']} combinaison(s) seront ignorées "
            "car fast_len doit rester strictement inférieur à slow_len"
        )
    return {
        "timeframe_minutes": timeframe_minutes,
        "start_date": payload.get("start_date"),
        "end_date": payload.get("end_date"),
        "total_iterations": total,
        "canonical_iterations": grid_validation["canonical_iterations"],
        "valid_iterations": grid_validation["valid_iterations"],
        "skipped_iterations": grid_validation["skipped_iterations"],
        "deduplicated_inactive_iterations": grid_validation["deduplicated_inactive_iterations"],
        "skipped_examples": grid_validation["skipped_examples"],
        "parameters": [asdict(spec) for spec in specs],
        "inactive_parameters": sorted(
            inactive_parameter_names(
                strategy,
                {key: value for key, value in asdict(fixed_overrides).items() if value is not None},
            )
        ),
        "warnings": warnings,
    }


def _api_error(message: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse({"error": message}, status_code=status_code)


def _handle_api_optimize(request_payload, store, repo_root, processed_dir, output_dir):
    try:
        payload = request_payload.as_legacy_payload()
        validate_timeframe_minutes(payload.get("timeframe_minutes", BASE_TIMEFRAME_MINUTES))
        _validate_window_payload(payload)
        specs = _parameter_specs_from_payload(payload)
        validate_score_metric(str(payload.get("score_metric", "sharpe_ratio")), strategy=str(payload.get("strategy", "hma_crossover")))
        _validate_optional_repo_paths(payload, repo_root)
        resolve_repo_path(repo_root, payload.get("processed_dir") or processed_dir, "processed_dir")
        resolve_repo_path(repo_root, payload.get("output_dir") or output_dir, "output_dir")
        if payload.get("config"):
            resolve_repo_path(repo_root, str(payload["config"]), "config")
        if not payload.get("symbol"):
            raise ValueError("symbol is required")
        total = estimate_iterations(specs)
        max_iterations = int(payload.get("max_iterations", 10000))
        grid_validation = validate_parameter_grid(
            specs,
            fixed_overrides=_fixed_overrides_from_payload(payload, repo_root),
            strategy=str(payload.get("strategy", "hma_crossover")),
            optimization_mode=payload.get("optimization_mode", "grid"),
        )
        if payload.get("optimization_mode", "grid") == "grid":
            validate_iteration_limits(
                raw_iterations=total,
                canonical_iterations=grid_validation["canonical_iterations"],
                max_raw_iterations=max_iterations,
                max_canonical_iterations=max_iterations,
            )
        is_bayesian = payload.get("optimization_mode", "grid") == "bayesian"
        target_iterations = max_iterations if is_bayesian else grid_validation["canonical_iterations"]
        job = OptimizerJob(
            id=uuid4().hex,
            created_at=time.time(),
            request=payload,
            progress={"currentIteration": 0, "totalIterations": target_iterations, "rawIterations": total},
        )
        store.add(job)
        return job.public_payload()
    except Exception as exc:  # noqa: BLE001 - local API validation response
        return _api_error(str(exc), status_code=400)

def _handle_api_delete_job(job_id, store, repo_root):
    job = store.get(job_id)
    if job is None:
        return _api_error("job not found", status_code=404)
    if job.status in OptimizerJobStore.ACTIVE_STATUSES:
        if not (job.status == "IN_PROGRESS" and job.cancel_requested is True):
            return _api_error("active jobs must be cancelled or finished before deletion", status_code=409)

    output_dir_deleted = False
    output_path = None
    if job.output_dir:
        try:
            output_path = resolve_repo_path(repo_root, job.output_dir, "output_dir")
        except Exception as exc:  # noqa: BLE001 - local API validation response
            return _api_error(str(exc), status_code=400)
    else:
        # Fallback discovery mechanism
        strategy = job.request.get("strategy")
        symbol = job.request.get("symbol")
        if strategy and symbol:
            try:
                reports_dir = get_reports_dir(repo_root)
                potential_path = reports_dir / "local_optimizer" / strategy / symbol / f"run_{job_id}"
                if potential_path.exists():
                    output_path = potential_path
            except Exception:
                pass

    if output_path:
        try:
            # Safety checks to prevent accidental/malicious recursive deletion
            reports_dir = get_reports_dir(repo_root)
            try:
                output_path.relative_to(reports_dir)
            except ValueError:
                return _api_error("job output directory must be inside the reports directory", status_code=400)
            
            # Check depth: must have at least 3 parts relative to reports_dir's parent
            try:
                rel_parts = output_path.relative_to(reports_dir.parent).parts
                if len(rel_parts) < 3:
                    return _api_error("job output directory must be at least 3 levels deep under reports directory parent", status_code=400)
            except ValueError:
                return _api_error("job output directory must be inside the reports directory", status_code=400)
            
            # Check that the job ID is contained in the name of the output directory
            # (or matches the legacy format: timestamp-uuid8)
            is_legacy_dir = bool(re.match(r"^\d{8}T\d{6}Z-[0-9a-f]{8}$", output_path.name))
            if job_id not in output_path.name and not is_legacy_dir:
                return _api_error("job output directory name must contain the job ID", status_code=400)
        except Exception as exc:  # noqa: BLE001 - local API validation response
            return _api_error(str(exc), status_code=400)
        try:
            if output_path.exists():
                if not output_path.is_dir():
                    return _api_error("job output_dir is not a directory", status_code=400)
                shutil.rmtree(output_path, ignore_errors=True)
                output_dir_deleted = True
        except Exception as exc:  # noqa: BLE001 - local filesystem error should be visible in UI
            return _api_error(f"could not delete job output directory: {exc}", status_code=500)

    deleted = store.delete(job_id)
    if deleted is None:
        return _api_error("job not found", status_code=404)
    return {"deleted": True, "job_id": job_id, "output_dir_deleted": output_dir_deleted}


def _handle_api_bulk_delete_jobs(payload, store, repo_root):
    deleted_count = 0
    skipped_active_count = 0
    errors = []

    for job_id in payload.job_ids:
        job = store.get(job_id)
        if job is None:
            continue
        if job.status in OptimizerJobStore.ACTIVE_STATUSES:
            if not (job.status == "IN_PROGRESS" and job.cancel_requested is True):
                skipped_active_count += 1
                continue

        output_path = None
        if job.output_dir:
            try:
                output_path = resolve_repo_path(repo_root, job.output_dir, "output_dir")
            except Exception as exc:
                errors.append(f"Job {job_id}: {exc}")
                continue
        else:
            # Fallback discovery mechanism
            strategy = job.request.get("strategy")
            symbol = job.request.get("symbol")
            if strategy and symbol:
                try:
                    reports_dir = get_reports_dir(repo_root)
                    potential_path = reports_dir / "local_optimizer" / strategy / symbol / f"run_{job_id}"
                    if potential_path.exists():
                        output_path = potential_path
                except Exception:
                    pass

        if output_path:
            try:
                # Safety checks to prevent accidental/malicious recursive deletion
                reports_dir = get_reports_dir(repo_root)
                try:
                    output_path.relative_to(reports_dir)
                except ValueError:
                    errors.append(f"Job {job_id}: job output directory must be inside the reports directory")
                    continue
                
                # Check depth: must have at least 3 parts relative to reports_dir's parent
                try:
                    rel_parts = output_path.relative_to(reports_dir.parent).parts
                    if len(rel_parts) < 3:
                        errors.append(f"Job {job_id}: job output directory must be at least 3 levels deep under reports directory parent")
                        continue
                except ValueError:
                    errors.append(f"Job {job_id}: job output directory must be inside the reports directory")
                    continue
                
                # Check that the job ID is contained in the name of the output directory
                # (or matches the legacy format: timestamp-uuid8)
                is_legacy_dir = bool(re.match(r"^\d{8}T\d{6}Z-[0-9a-f]{8}$", output_path.name))
                if job_id not in output_path.name and not is_legacy_dir:
                    errors.append(f"Job {job_id}: job output directory name must contain the job ID")
                    continue
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Job {job_id}: {exc}")
                continue

            try:
                if output_path.exists():
                    if not output_path.is_dir():
                        errors.append(f"Job {job_id}: job output_dir is not a directory")
                        continue
                    shutil.rmtree(output_path, ignore_errors=True)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"Job {job_id}: could not delete job output directory: {exc}")
                continue

        try:
            deleted = store.delete(job_id)
            if deleted is not None:
                deleted_count += 1
            else:
                errors.append(f"Job {job_id} not found during deletion")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Job {job_id}: could not delete job from store: {exc}")

    return {
        "deleted": deleted_count,
        "skipped_active": skipped_active_count,
        "errors": errors,
    }



def _handle_api_viewer_chart_data(request, repo_root, processed_dir, _run_strategy_for_viewer):
    """Load canonical market data, run the selected strategy, and return chart-ready data."""
    try:
        tf = request.timeframe.strip().lower()
        if tf.endswith("m"):
            minutes = int(tf[:-1])
        elif tf.endswith("h"):
            minutes = int(tf[:-1]) * 60
        elif tf.endswith("d"):
            minutes = int(tf[:-1]) * 60 * 24
        else:
            raise ValueError(f"Invalid timeframe: {request.timeframe!r}")
        minutes = validate_timeframe_minutes(minutes)

        processed_root = resolve_repo_path(repo_root, request.processed_dir or processed_dir, "processed_dir")

        from .data import load_canonical_market_data
        data = load_canonical_market_data(
            symbol=request.symbol,
            repo_root=repo_root,
            processed_dir=processed_root,
            timeframe_minutes=minutes,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        payload = request.model_dump(exclude_none=True)
        payload.pop("strategy", None)
        payload.pop("symbol", None)
        payload.pop("timeframe", None)
        payload.pop("start_date", None)
        payload.pop("end_date", None)
        payload.pop("processed_dir", None)
        payload.pop("initial_capital", None)

        result = _run_strategy_for_viewer(
            strategy=request.strategy,
            data=data,
            symbol=request.symbol,
            overrides=payload,
            initial_capital=request.initial_capital,
            timeframe_minutes=minutes,
        )

        state = result.state
        trades = result.trades

        if not isinstance(state.index, pd.DatetimeIndex):
            return _api_error("Invalid state index: expected DatetimeIndex", status_code=500)

        required_cols = {"open", "high", "low", "close"}
        missing_cols = required_cols - set(state.columns)
        if missing_cols:
            return _api_error(f"Missing required columns in state: {sorted(missing_cols)}", status_code=500)

        klines: list[dict[str, Any]] = []
        indicator_names = _VIEWER_STRATEGY_INDICATORS.get(request.strategy, [])
        indicators: dict[str, list[dict[str, Any]]] = {name: [] for name in indicator_names}

        for timestamp, row in state.iterrows():
            ts_ms = int(timestamp.timestamp() * 1000)
            klines.append({
                "timestamp": ts_ms,
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row.get("volume", 0)),
            })
            for name in indicator_names:
                if name in row and not pd.isna(row[name]):
                    indicators[name].append({"timestamp": ts_ms, "value": float(row[name])})

        signals: list[dict[str, Any]] = []
        for _, trade in trades.iterrows():
            entry_ts = pd.Timestamp(trade["entry_index"])
            entry_ms = int(entry_ts.timestamp() * 1000)
            side = str(trade["side"]).upper()
            entry_price = float(trade["entry_price"]) if "entry_price" in trade and pd.notna(trade["entry_price"]) else None
            signals.append({
                "timestamp": entry_ms,
                "type": "entry",
                "side": side,
                "price": entry_price,
            })
            if "exit_index" in trade and pd.notna(trade["exit_index"]):
                exit_ts = pd.Timestamp(trade["exit_index"])
                exit_ms = int(exit_ts.timestamp() * 1000)
                exit_price = float(trade["exit_price"]) if "exit_price" in trade and pd.notna(trade["exit_price"]) else None
                pnl = float(trade["net_pnl"]) if "net_pnl" in trade and pd.notna(trade["net_pnl"]) else None
                signals.append({
                    "timestamp": exit_ms,
                    "type": "exit",
                    "side": side,
                    "price": exit_price,
                    "pnl": pnl,
                })

        signals.sort(key=lambda x: x["timestamp"])

        return {
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "strategy": request.strategy,
            "klines": klines,
            "indicators": indicators,
            "signals": signals,
            "trade_count": len(trades),
        }
    except Exception as exc:  # noqa: BLE001 - surfaced to local UI
        return _api_error(str(exc), status_code=400)


def _handle_api_job_chart_data(job_id, store, repo_root, processed_dir):
    job = store.get(job_id)
    if job is None:
        return _api_error("job not found", status_code=404)
    if not job.best or not job.best.get("best_backtest_dir"):
        return _api_error("best run not ready", status_code=404)
        
    try:
        best_backtest_dir = resolve_repo_path(repo_root, str(job.best["best_backtest_dir"]), "best_backtest_dir")
        trades_parquet_path = resolve_repo_path(repo_root, best_backtest_dir / "trades.parquet", "trades.parquet")
        equity_parquet_path = resolve_repo_path(repo_root, best_backtest_dir / "equity_curve.parquet", "equity_curve.parquet")
    except Exception as exc:
        return _api_error(str(exc), status_code=400)
        
    payload = job.request
    from .data import load_canonical_market_data
    try:
        market_data = load_canonical_market_data(
            symbol=str(payload["symbol"]),
            repo_root=repo_root,
            processed_dir=resolve_repo_path(repo_root, payload.get("processed_dir") or processed_dir, "processed_dir"),
            timeframe_minutes=payload.get("timeframe_minutes", BASE_TIMEFRAME_MINUTES),
            start_date=payload.get("start_date"),
            end_date=payload.get("end_date"),
        )
    except Exception as exc:
        return _api_error(f"could not load market data: {exc}", status_code=500)

    ohlc = []
    for timestamp, row in market_data.iterrows():
        ts = timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp
        ohlc.append({
            "time": int(ts.timestamp()),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"])
        })

    markers = []
    if trades_parquet_path.exists():
        try:
            trades_df = pd.read_parquet(trades_parquet_path)
            for _, row in trades_df.iterrows():
                entry_ts = pd.Timestamp(row["entry_time"])
                entry_ts = entry_ts.tz_localize("UTC") if entry_ts.tzinfo is None else entry_ts
                side = str(row["side"]).upper()
                
                # Entry marker
                markers.append({
                    "time": int(entry_ts.timestamp()),
                    "position": "belowBar" if side == "LONG" else "aboveBar",
                    "color": "#22c55e" if side == "LONG" else "#ef4444",
                    "shape": "arrowUp" if side == "LONG" else "arrowDown",
                    "text": "Buy" if side == "LONG" else "Sell"
                })
                
                # Exit marker
                if "exit_time" in row and pd.notna(row["exit_time"]):
                    exit_ts = pd.Timestamp(row["exit_time"])
                    exit_ts = exit_ts.tz_localize("UTC") if exit_ts.tzinfo is None else exit_ts
                    pnl = float(row["net_pnl"]) if "net_pnl" in row else 0.0
                    markers.append({
                        "time": int(exit_ts.timestamp()),
                        "position": "aboveBar" if side == "LONG" else "belowBar",
                        "color": "#3b82f6" if pnl >= 0 else "#f97316",
                        "shape": "circle",
                        "text": f"Exit {side} ({pnl:.2f})"
                    })
        except Exception:
            pass
            
    equity = []
    if equity_parquet_path.exists():
        try:
            equity_df = pd.read_parquet(equity_parquet_path)
            time_column = "timestamp" if "timestamp" in equity_df.columns else equity_df.columns[0]
            for _, row in equity_df.iterrows():
                ts = pd.Timestamp(row[time_column])
                ts = ts.tz_localize("UTC") if ts.tzinfo is None else ts
                equity.append({
                    "time": int(ts.timestamp()),
                    "value": float(row["equity"])
                })
        except Exception:
            pass

    markers.sort(key=lambda x: x["time"])

    return {
        "job_id": job_id,
        "ohlc": ohlc,
        "markers": markers,
        "equity": equity
    }


def _handle_api_global_analysis(request, repo_root, output_dir):
    from .global_analysis import generate_global_analysis
    try:
        target_dir = request.output_dir or output_dir
        resolved_target_dir = resolve_repo_path(repo_root, target_dir, "output_dir")
        res = generate_global_analysis(repo_root, request.strategy, resolved_target_dir)
        return res
    except Exception as exc:
        return _api_error(str(exc), status_code=400)


def _handle_api_global_summary_parquet(strategy, repo_root, output_dir):
    try:
        path = resolve_repo_path(repo_root, Path(output_dir) / strategy / "global_summary.parquet", "global_summary.parquet")
        if not path.exists():
            return _api_error("Global summary Parquet not found", status_code=404)
        return FileResponse(path, media_type="application/octet-stream", filename=f"global_summary_{strategy}.parquet")
    except Exception as exc:
        return _api_error(str(exc), status_code=400)


def create_optimizer_app(
    *,
    repo_root: Path,
    processed_dir: str = "storage/processed",
    output_dir: str = "reports/local_optimizer",
    store: OptimizerJobStore | None = None,
) -> FastAPI:
    """Create the FastAPI optimizer web application.

    Route payloads intentionally match the previous local API so the static
    frontend can keep using the same endpoints unchanged.
    """

    repo_root = Path(repo_root)
    if output_dir == "reports/local_optimizer":
        output_dir = str(get_reports_dir(repo_root) / "local_optimizer")
    static_root = Path(__file__).resolve().parent / "web_static"
    if store is None:
        job_store_path = resolve_repo_path(repo_root, Path(output_dir) / "jobs.sqlite3", "job_store")
        store = OptimizerJobStore(storage_path=job_store_path)

    app = FastAPI(title="Backtest Optimizer API", version="0.2.0")
    app.state.optimizer_store = store

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:  # noqa: ARG001
        first_error = exc.errors()[0] if exc.errors() else {}
        message = first_error.get("msg") or "Invalid request payload"
        location = ".".join(str(part) for part in first_error.get("loc", []) if part != "body")
        if location:
            message = f"{location}: {message}"
        return _api_error(str(message), status_code=400)

    @app.get("/api/strategies")
    def api_strategies() -> dict[str, Any]:
        return {
            "strategies": [
                {
                    "name": strategy_name,
                    "parameters": [asdict(param) for param in optimizable_parameters(strategy_name).values()],
                    "schema": [asdict(param) for param in parameter_definitions(strategy_name).values()],
                    "score_metrics": list(allowed_score_metrics(strategy_name)),
                }
                for strategy_name in StrategyRegistry.list_strategies()
            ]
        }

    @app.get("/api/symbols", response_model=None)
    def api_symbols(request: Request) -> dict[str, Any] | JSONResponse:
        try:
            query = request.query_params
            requested_processed_dir = resolve_repo_path(repo_root, query.get("processed_dir", processed_dir), "processed_dir")
            requested_timeframe = query.get("timeframe", query.get("timeframe_minutes", BASE_TIMEFRAME_MINUTES))
            return {
                "symbols": list_canonical_symbols(
                    repo_root,
                    requested_processed_dir,
                    timeframe_minutes=requested_timeframe,
                )
            }
        except Exception as exc:  # noqa: BLE001 - local API validation response
            return _api_error(str(exc), status_code=400)

    @app.get("/api/dataset-bounds", response_model=None)
    def api_dataset_bounds(request: Request) -> dict[str, Any] | JSONResponse:
        try:
            query = request.query_params
            symbol = query.get("symbol", "").strip()
            if not symbol:
                return _api_error("symbol is required", status_code=400)
            processed = query.get("processed_dir", processed_dir)
            requested_processed_dir = resolve_repo_path(repo_root, processed, "processed_dir")
            requested_timeframe = query.get("timeframe_minutes", query.get("timeframe", BASE_TIMEFRAME_MINUTES))
            min_date, max_date = get_canonical_market_data_date_bounds(
                symbol=symbol,
                repo_root=repo_root,
                processed_dir=requested_processed_dir,
                timeframe_minutes=requested_timeframe,
            )
            return {"min_date": min_date, "max_date": max_date}
        except Exception as exc:  # noqa: BLE001 - local API validation response
            return _api_error(str(exc), status_code=400)

    @app.get("/api/jobs")
    def api_jobs() -> dict[str, Any]:
        return {"jobs": store.list()}

    @app.post("/api/estimate", response_model=None)
    def api_estimate(request_payload: OptimizerRequestPayload) -> dict[str, Any] | JSONResponse:
        try:
            return _estimate_payload(request_payload.as_legacy_payload(), repo_root)
        except Exception as exc:  # noqa: BLE001 - local API validation response
            return _api_error(str(exc), status_code=400)

    @app.post("/api/optimize", status_code=202, response_model=None)
    def api_optimize(request_payload: OptimizerRequestPayload) -> dict[str, Any] | JSONResponse:
        return _handle_api_optimize(request_payload, store, repo_root, processed_dir, output_dir)

    @app.get("/api/jobs/{job_id}", response_model=None)
    def api_job(job_id: str) -> dict[str, Any] | JSONResponse:
        job = store.get(job_id)
        if job is None:
            return _api_error("job not found", status_code=404)
        return job.public_payload()

    @app.post("/api/jobs/{job_id}/cancel", response_model=None)
    def api_cancel_job(job_id: str) -> dict[str, Any] | JSONResponse:
        job = store.get(job_id)
        if job is None:
            return _api_error("job not found", status_code=404)
        store.update(job_id, cancel_requested=True)
        updated = store.get(job_id)
        if updated is None:
            return _api_error("job not found", status_code=404)
        return updated.public_payload()

    @app.delete("/api/jobs/{job_id}", response_model=None)
    def api_delete_job(job_id: str) -> dict[str, Any] | JSONResponse:
        return _handle_api_delete_job(job_id, store, repo_root)
    @app.post("/api/jobs/bulk-cancel", response_model=None)
    def api_bulk_cancel_jobs(payload: BulkDeleteRequest) -> dict[str, Any]:
        cancelled_count = 0
        errors = []
        for job_id in payload.job_ids:
            job = store.get(job_id)
            if job is None:
                continue
            if job.status in OptimizerJobStore.ACTIVE_STATUSES:
                try:
                    store.update(job_id, cancel_requested=True)
                    cancelled_count += 1
                except Exception as exc:
                    errors.append(f"Job {job_id}: {exc}")
        return {"cancelled": cancelled_count, "errors": errors}

    @app.post("/api/jobs/bulk-delete", response_model=None)
    def api_bulk_delete_jobs(payload: BulkDeleteRequest) -> dict[str, Any]:
        return _handle_api_bulk_delete_jobs(payload, store, repo_root)
    @app.get("/api/jobs/{job_id}/results.parquet", response_model=None)
    def api_job_results(job_id: str) -> FileResponse | JSONResponse:
        job = store.get(job_id)
        if job is None:
            return _api_error("job not found", status_code=404)
        if not job.output_dir:
            return _api_error("results not ready", status_code=404)
        parquet_path = resolve_repo_path(repo_root, Path(job.output_dir) / "results.parquet", "results.parquet")
        if not parquet_path.exists():
            return _api_error("results not ready", status_code=404)
        return FileResponse(
            parquet_path,
            media_type="application/octet-stream",
            filename=f"optimizer-{job_id}.parquet",
        )

    @app.get("/api/jobs/{job_id}/optimizer_report.parquet", response_model=None)
    def api_job_optimizer_report_parquet(job_id: str) -> FileResponse | JSONResponse:
        job = store.get(job_id)
        if job is None:
            return _api_error("job not found", status_code=404)
        if not job.output_dir:
            return _api_error("optimizer report not ready", status_code=404)
        parquet_path = resolve_repo_path(repo_root, Path(job.output_dir) / "optimizer_report.parquet", "optimizer_report.parquet")
        if not parquet_path.exists():
            return _api_error("optimizer report not ready", status_code=404)
        return FileResponse(
            parquet_path,
            media_type="application/octet-stream",
            filename=f"optimizer-{job_id}-report.parquet",
        )

    @app.get("/api/jobs/{job_id}/optimizer_report.html", response_model=None)
    def api_job_optimizer_report_html(job_id: str) -> FileResponse | JSONResponse:
        job = store.get(job_id)
        if job is None:
            return _api_error("job not found", status_code=404)
        if not job.output_dir:
            return _api_error("optimizer report not ready", status_code=404)
        html_path = resolve_repo_path(repo_root, Path(job.output_dir) / "optimizer_report.html", "optimizer_report.html")
        if not html_path.exists():
            return _api_error("optimizer report not ready", status_code=404)
        return FileResponse(
            html_path,
            media_type="text/html; charset=utf-8",
            filename=f"optimizer-{job_id}-report.html",
        )

    @app.get("/api/jobs/{job_id}/recommendations", response_model=None)
    def api_job_recommendations(job_id: str) -> dict[str, Any] | JSONResponse:
        job = store.get(job_id)
        if job is None:
            return _api_error("job not found", status_code=404)
        if not job.output_dir:
            return _api_error("recommendations not ready", status_code=404)
        try:
            recommendations_path = resolve_repo_path(repo_root, Path(job.output_dir) / "recommendations.json", "recommendations.json")
        except Exception as exc:  # noqa: BLE001 - local API validation response
            return _api_error(str(exc), status_code=400)
        if not recommendations_path.exists():
            return _api_error("recommendations not ready", status_code=404)
        try:
            payload = json.loads(recommendations_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - corrupted local output should be visible in UI
            return _api_error(f"could not read recommendations: {exc}", status_code=500)
        return payload if isinstance(payload, dict) else {"recommendations": payload}

    @app.get("/api/jobs/{job_id}/recommendations.json", response_model=None)
    def api_job_recommendations_file(job_id: str) -> FileResponse | JSONResponse:
        job = store.get(job_id)
        if job is None:
            return _api_error("job not found", status_code=404)
        if not job.output_dir:
            return _api_error("recommendations not ready", status_code=404)
        recommendations_path = resolve_repo_path(repo_root, Path(job.output_dir) / "recommendations.json", "recommendations.json")
        if not recommendations_path.exists():
            return _api_error("recommendations not ready", status_code=404)
        return FileResponse(
            recommendations_path,
            media_type="application/json; charset=utf-8",
            filename=f"optimizer-{job_id}-recommendations.json",
        )

    @app.get("/api/jobs/{job_id}/best-equity", response_model=None)
    def api_job_best_equity(job_id: str) -> dict[str, Any] | JSONResponse:
        job = store.get(job_id)
        if job is None:
            return _api_error("job not found", status_code=404)
        if not job.best or not job.best.get("best_backtest_dir"):
            return _api_error("best run not ready", status_code=404)
        try:
            best_backtest_dir = resolve_repo_path(repo_root, str(job.best["best_backtest_dir"]), "best_backtest_dir")
            parquet_path = resolve_repo_path(repo_root, best_backtest_dir / "equity_curve.parquet", "equity_curve.parquet")
        except Exception as exc:  # noqa: BLE001 - local API validation response
            return _api_error(str(exc), status_code=400)
        if not parquet_path.exists():
            return _api_error("best equity curve not ready", status_code=404)

        try:
            frame = pd.read_parquet(parquet_path)
        except Exception as exc:  # noqa: BLE001 - corrupted local output should be visible in UI
            return _api_error(f"could not read best equity curve: {exc}", status_code=500)

        if "equity" not in frame.columns:
            return _api_error("best equity curve is missing the equity column", status_code=500)

        time_column = "timestamp" if "timestamp" in frame.columns else frame.columns[0]
        points = []
        for record in frame[[time_column, "equity", *( ["drawdown"] if "drawdown" in frame.columns else [] )]].to_dict(orient="records"):
            point = {
                "time": str(record.get(time_column, "")),
                "equity": record.get("equity"),
            }
            if "drawdown" in record:
                point["drawdown"] = record.get("drawdown")
            points.append(point)
        return {"job_id": job_id, "points": points}

    @app.get("/api/jobs/{job_id}/chart-data", response_model=None)
    def api_job_chart_data(job_id: str) -> dict[str, Any] | JSONResponse:
        return _handle_api_job_chart_data(job_id, store, repo_root, processed_dir)
    @app.post("/api/global-analysis", response_model=None)
    def api_global_analysis(request: GlobalAnalysisRequest) -> dict[str, Any] | JSONResponse:
        return _handle_api_global_analysis(request, repo_root, output_dir)
    @app.get("/api/global-analysis/{strategy}/global_summary.parquet", response_model=None)
    def api_global_summary_parquet(strategy: str) -> FileResponse | JSONResponse:
        return _handle_api_global_summary_parquet(strategy, repo_root, output_dir)
    @app.get("/api/global-analysis/{strategy}/global_summary.html", response_model=None)
    def api_global_summary_html(strategy: str) -> FileResponse | JSONResponse:
        try:
            path = resolve_repo_path(repo_root, Path(output_dir) / strategy / "global_summary.html", "global_summary.html")
            if not path.exists():
                return _api_error("Global summary HTML not found", status_code=404)
            return FileResponse(path, media_type="text/html")
        except Exception as exc:
            return _api_error(str(exc), status_code=400)

    @app.get("/api/viewer/timeframes", response_model=None)
    def api_viewer_timeframes(request: Request) -> dict[str, Any] | JSONResponse:
        """Return the list of timeframes for which backtest reports exist for a given symbol."""
        try:
            symbol = request.query_params.get("symbol", "").strip()
            if not symbol:
                return _api_error("symbol is required", status_code=400)
            strategy = request.query_params.get("strategy", "hma_crossover").strip() or "hma_crossover"
            symbol_dir = resolve_repo_path(repo_root, Path(output_dir) / strategy / symbol, "output_dir")
            if not symbol_dir.exists():
                return {"timeframes": []}

            timeframes: set[int] = set()
            for run_dir in symbol_dir.iterdir():
                if not run_dir.is_dir():
                    continue
                config_path = run_dir / "optimization_config.json"
                if config_path.exists():
                    try:
                        cfg = json.loads(config_path.read_text(encoding="utf-8"))
                        tf = cfg.get("timeframe_minutes")
                        if isinstance(tf, int):
                            timeframes.add(tf)
                    except Exception:
                        continue

            def _format_tf(minutes: int) -> dict[str, Any]:
                if minutes < 60:
                    return {"value": f"{minutes}m", "label": f"{minutes} minutes", "minutes": minutes}
                if minutes == 60:
                    return {"value": "1h", "label": "1 heure", "minutes": minutes}
                if minutes < 1440 and minutes % 60 == 0:
                    return {"value": f"{minutes // 60}h", "label": f"{minutes // 60} heures", "minutes": minutes}
                if minutes == 1440:
                    return {"value": "1d", "label": "1 jour", "minutes": minutes}
                if minutes % 1440 == 0:
                    return {"value": f"{minutes // 1440}d", "label": f"{minutes // 1440} jours", "minutes": minutes}
                return {"value": f"{minutes}m", "label": f"{minutes} minutes", "minutes": minutes}

            return {"timeframes": [_format_tf(m) for m in sorted(timeframes)]}
        except Exception as exc:  # noqa: BLE001
            return _api_error(str(exc), status_code=400)

    def _run_strategy_for_viewer(
        strategy: str,
        data: pd.DataFrame,
        symbol: str,
        overrides: dict[str, Any],
        initial_capital: float,
        timeframe_minutes: int,
    ) -> Any:
        """Route viewer request to the correct strategy runner via the registry."""
        info = StrategyRegistry.get(strategy)
        typed_overrides = info.overrides_from_mapping_function(overrides)
        return info.run_function(
            data, symbol,
            overrides=typed_overrides,
            initial_capital=initial_capital,
            timeframe_minutes=timeframe_minutes,
            compute_full_metrics=True,
            repo_root=repo_root,
        )

    @app.post("/api/viewer/chart-data", response_model=None)
    def api_viewer_chart_data(request: ViewerChartRequest) -> dict[str, Any] | JSONResponse:
        return _handle_api_viewer_chart_data(request, repo_root, processed_dir, _run_strategy_for_viewer)
    @app.get("/{request_path:path}", include_in_schema=False, response_model=None)
    def static_files(request_path: str) -> FileResponse | JSONResponse:
        relative = "index.html" if request_path in {"", "/"} else request_path
        path = (static_root / relative).resolve()
        try:
            path.relative_to(static_root.resolve())
        except ValueError:
            return _api_error("not found", status_code=404)
        if not path.exists() or not path.is_file():
            return _api_error("not found", status_code=404)
        return FileResponse(
            path,
            media_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            headers={"Cache-Control": "no-store"},
        )

    return app


def serve_optimizer_app(
    *,
    repo_root: Path,
    host: str = "127.0.0.1",
    port: int = 8765,
    processed_dir: str = "storage/processed",
    output_dir: str = "reports/local_optimizer",
) -> None:
    repo_root = Path(repo_root)
    if output_dir == "reports/local_optimizer":
        output_dir = str(get_reports_dir(repo_root) / "local_optimizer")
    print(f"Backtest optimizer UI available at http://{host}:{port}/")
    print(f"FastAPI documentation available at http://{host}:{port}/docs")
    app = create_optimizer_app(repo_root=repo_root, processed_dir=processed_dir, output_dir=output_dir)
    uvicorn.run(app, host=host, port=port)


def run_optimizer_worker(
    *,
    repo_root: Path,
    processed_dir: str = "storage/processed",
    output_dir: str = "reports/local_optimizer",
    poll_interval: float = 1.0,
    once: bool = False,
    worker_id: str | None = None,
    store: OptimizerJobStore | None = None,
) -> int:
    """Consume queued optimizer jobs from the persistent SQLite store.

    This is intentionally separate from the FastAPI app: the web process enqueues
    jobs and exposes status endpoints, while this worker owns the CPU-heavy
    optimization lifecycle.
    """

    repo_root = Path(repo_root)
    if output_dir == "reports/local_optimizer":
        output_dir = str(get_reports_dir(repo_root) / "local_optimizer")
    if store is None:
        job_store_path = resolve_repo_path(repo_root, Path(output_dir) / "jobs.sqlite3", "job_store")
        store = OptimizerJobStore(storage_path=job_store_path)
    worker_name = worker_id or f"optimizer-worker-{uuid4().hex[:8]}"
    sleep_seconds = max(0.1, float(poll_interval))

    store.mark_interrupted_jobs_failed()

    while True:
        job = store.claim_next(worker_id=worker_name)
        if job is None:
            if once:
                return 0
            time.sleep(sleep_seconds)
            continue
        if job.cancel_requested:
            store.update(job.id, status="CANCELLED")
        else:
            _run_job(
                job_id=job.id,
                store=store,
                repo_root=repo_root,
                default_processed_dir=processed_dir,
                default_output_dir=output_dir,
            )
        if once:
            return 0
