from __future__ import annotations

from collections import defaultdict
import json
import math
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


DEFAULT_TOP_QUANTILE = 0.95
DEFAULT_SCORE_TOLERANCE_PCT = 0.10


def _json_default(value: object) -> object:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return str(value)


def _finite_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if hasattr(value, "item"):
        return _json_safe(value.item())
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _parameter_specs_by_name(optimization_config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    specs: dict[str, dict[str, Any]] = {}
    for spec in optimization_config.get("parameters") or []:
        if isinstance(spec, dict) and spec.get("name"):
            specs[str(spec["name"])] = spec
    return specs


def _row_parameters(row: dict[str, Any]) -> dict[str, Any]:
    if isinstance(row.get("parameters"), dict):
        return dict(row["parameters"])
    return {key.removeprefix("param_"): value for key, value in row.items() if str(key).startswith("param_")}


def _completed_frame(results: Iterable[dict[str, Any]], direction: str) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for row in results:
        score = _finite_float(row.get("score"))
        if row.get("status") != "COMPLETED" or score is None:
            continue
        rows.append(
            {
                "iteration": row.get("iteration"),
                "score": score,
                "effective_score": score if direction == "max" else -score,
                "parameters": _row_parameters(row),
                "metrics": row.get("metrics") if isinstance(row.get("metrics"), dict) else {},
                "raw_row": row,
            }
        )
    return pd.DataFrame(rows)


def _weighted_quantile(values: list[float], weights: list[float], quantile: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(zip(values, weights), key=lambda item: item[0])
    total = sum(max(0.0, weight) for _, weight in ordered)
    if total <= 0:
        return ordered[len(ordered) // 2][0]
    threshold = total * quantile
    cumulative = 0.0
    for value, weight in ordered:
        cumulative += max(0.0, weight)
        if cumulative >= threshold:
            return value
    return ordered[-1][0]


def _snap_numeric(value: float, allowed_values: list[Any], value_type: str | None) -> int | float:
    numeric_allowed = [candidate for candidate in (_finite_float(item) for item in allowed_values) if candidate is not None]
    if numeric_allowed:
        value = min(numeric_allowed, key=lambda candidate: (abs(candidate - value), candidate))
    if value_type == "int" or all(float(candidate).is_integer() for candidate in numeric_allowed or [value]):
        return int(round(value))
    return round(float(value), 10)


def _confidence_from_share(share: float, evidence_count: int) -> str:
    if evidence_count < 3:
        return "low"
    if share >= 0.65:
        return "high"
    if share >= 0.45:
        return "medium"
    return "low"


def _numeric_confidence(q25: float, q75: float, all_values: list[float], evidence_count: int) -> str:
    if evidence_count < 5 or not all_values:
        return "low"
    full_width = max(all_values) - min(all_values)
    if full_width <= 0:
        return "high"
    robust_width = max(0.0, q75 - q25)
    ratio = robust_width / full_width
    if ratio <= 0.25 and evidence_count >= 20:
        return "high"
    if ratio <= 0.50:
        return "medium"
    return "low"


def _parameter_value(row: pd.Series, name: str) -> Any:
    parameters = row.get("parameters") or {}
    return parameters.get(name) if isinstance(parameters, dict) else None


def _build_weights(candidate_frame: pd.DataFrame) -> list[float]:
    if candidate_frame.empty:
        return []
    scores = [float(value) for value in candidate_frame["effective_score"].tolist()]
    score_min = min(scores)
    score_max = max(scores)
    if score_max <= score_min:
        return [1.0] * len(scores)
    return [0.25 + 0.75 * ((score - score_min) / (score_max - score_min)) for score in scores]


def _recommend_numeric_parameter(
    name: str,
    spec: dict[str, Any],
    candidate_frame: pd.DataFrame,
    completed_frame: pd.DataFrame,
    weights: list[float],
    best_parameters: dict[str, Any],
) -> dict[str, Any]:
    candidate_values = [_finite_float(_parameter_value(row, name)) for _, row in candidate_frame.iterrows()]
    weighted_values = [(value, weights[index]) for index, value in enumerate(candidate_values) if value is not None]
    values = [value for value, _ in weighted_values]
    value_weights = [weight for _, weight in weighted_values]
    allowed_values = spec.get("values") if isinstance(spec.get("values"), list) else []
    all_numeric_values = [value for value in (_finite_float(item) for item in allowed_values) if value is not None]
    if not all_numeric_values:
        all_numeric_values = [
            value
            for value in (_finite_float(_parameter_value(row, name)) for _, row in completed_frame.iterrows())
            if value is not None
        ]
    if not values:
        return {"kind": "numeric", "recommended_value": None, "confidence": "low", "reason": "no candidate value"}

    q10 = _weighted_quantile(values, value_weights, 0.10)
    q25 = _weighted_quantile(values, value_weights, 0.25)
    median = _weighted_quantile(values, value_weights, 0.50)
    q75 = _weighted_quantile(values, value_weights, 0.75)
    q90 = _weighted_quantile(values, value_weights, 0.90)
    value_type = spec.get("value_type")
    recommended = _snap_numeric(median, allowed_values or all_numeric_values, value_type)
    return {
        "kind": "numeric",
        "recommended_value": recommended,
        "sweet_spot_range": [
            _snap_numeric(q25, allowed_values or all_numeric_values, value_type),
            _snap_numeric(q75, allowed_values or all_numeric_values, value_type),
        ],
        "extended_range": [
            _snap_numeric(q10, allowed_values or all_numeric_values, value_type),
            _snap_numeric(q90, allowed_values or all_numeric_values, value_type),
        ],
        "best_value": best_parameters.get(name),
        "evidence_count": len(values),
        "confidence": _numeric_confidence(q25, q75, all_numeric_values, len(values)),
    }


def _recommend_discrete_parameter(
    name: str,
    spec: dict[str, Any],
    candidate_frame: pd.DataFrame,
    weights: list[float],
    best_parameters: dict[str, Any],
) -> dict[str, Any]:
    weighted_counts: dict[str, float] = defaultdict(float)
    raw_values: dict[str, Any] = {}
    for index, (_, row) in enumerate(candidate_frame.iterrows()):
        value = _parameter_value(row, name)
        key = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
        raw_values[key] = value
        weighted_counts[key] += weights[index]
    if not weighted_counts:
        return {"kind": spec.get("kind", "choice"), "recommended_value": None, "confidence": "low", "reason": "no candidate value"}
    total = sum(weighted_counts.values())
    ordered = sorted(weighted_counts.items(), key=lambda item: item[1], reverse=True)
    best_key, best_weight = ordered[0]
    distribution = [
        {"value": raw_values[key], "weight_share": round(weight / total, 6), "weighted_count": round(weight, 6)}
        for key, weight in ordered
    ]
    share = best_weight / total if total else 0.0
    return {
        "kind": spec.get("kind", "choice"),
        "recommended_value": raw_values[best_key],
        "best_value": best_parameters.get(name),
        "distribution": distribution,
        "evidence_count": len(candidate_frame),
        "confidence": _confidence_from_share(share, len(candidate_frame)),
    }


def _row_distance(
    row: pd.Series,
    target_parameters: dict[str, Any],
    specs: dict[str, dict[str, Any]],
    ranges: dict[str, float],
) -> float:
    distance = 0.0
    count = 0
    row_parameters = row.get("parameters") or {}
    for name, target in target_parameters.items():
        count += 1
        row_value = row_parameters.get(name) if isinstance(row_parameters, dict) else None
        if specs.get(name, {}).get("kind") == "numeric":
            left = _finite_float(row_value)
            right = _finite_float(target)
            if left is None or right is None:
                distance += 1.0
            else:
                distance += abs(left - right) / max(ranges.get(name, 1.0), 1e-12)
        else:
            distance += 0.0 if row_value == target else 1.0
    return distance / max(count, 1)


def _compact_row(row: pd.Series | None) -> dict[str, Any] | None:
    if row is None:
        return None
    metrics = row.get("metrics") or {}
    compact_metrics = {
        key: metrics.get(key)
        for key in ("closed_trades", "total_net_pnl", "max_drawdown", "profit_factor", "sharpe_ratio", "sortino_ratio")
        if key in metrics
    }
    return {
        "iteration": _json_safe(row.get("iteration")),
        "score": _json_safe(row.get("score")),
        "parameters": _json_safe(row.get("parameters") or {}),
        "metrics": _json_safe(compact_metrics),
    }


def interpret_optimization_results(
    results: list[dict[str, Any]],
    optimization_config: dict[str, Any],
    *,
    top_quantile: float = DEFAULT_TOP_QUANTILE,
    score_tolerance_pct: float = DEFAULT_SCORE_TOLERANCE_PCT,
) -> dict[str, Any]:
    """Summarize an optimizer job into robust post-run parameter recommendations.

    The optimizer's ``best`` row remains the maximum observed score. This function
    instead looks for a higher-density high-performing area and returns both per-
    parameter sweet spots and an already-tested row closest to those sweet spots.
    """

    direction = str(optimization_config.get("score_direction") or "max")
    if direction not in {"max", "min"}:
        direction = "max"
    specs = _parameter_specs_by_name(optimization_config)
    completed = _completed_frame(results, direction)
    base_payload: dict[str, Any] = {
        "schema_version": 1,
        "strategy": optimization_config.get("strategy"),
        "symbol": optimization_config.get("symbol"),
        "score_metric": optimization_config.get("score_metric"),
        "score_direction": direction,
        "selection_settings": {
            "top_quantile": top_quantile,
            "score_tolerance_pct": score_tolerance_pct,
        },
    }
    if completed.empty:
        return {
            **base_payload,
            "best": None,
            "recommended": None,
            "parameters": {},
            "candidate_pool": {"eligible_rows": 0, "selected_rows": 0, "selection_rule": "no completed rows with finite score"},
            "notes": ["Aucune itération terminée avec un score exploitable n'a pu être interprétée."],
        }

    best_index = completed["effective_score"].idxmax()
    best_row = completed.loc[best_index]
    best_effective = float(best_row["effective_score"])
    effective_scores = completed["effective_score"].astype(float)
    score_span = float(effective_scores.max() - effective_scores.min())
    quantile = min(1.0, max(0.0, float(top_quantile)))
    quantile_cutoff = float(effective_scores.quantile(quantile))
    tolerance = max(abs(best_effective) * max(0.0, float(score_tolerance_pct)), score_span * max(0.0, float(score_tolerance_pct)) * 0.25)
    tolerance_cutoff = best_effective - tolerance
    cutoff = min(quantile_cutoff, tolerance_cutoff)
    
    selection_rule = "rows in top quantile or within score tolerance of best"
    candidates = completed[completed["effective_score"] >= cutoff].copy()
    if candidates.empty:
        candidates = completed.nlargest(max(1, min(10, len(completed))), "effective_score").copy()
        selection_rule = "fallback top candidates (empty standard cutoff)"
        
    min_candidates = max(50, int(len(completed) * 0.05))
    if len(candidates) < min_candidates:
        candidates = completed.nlargest(min_candidates, "effective_score").copy()
        selection_rule = "minimum candidates absolute floor triggered"
        
    weights = _build_weights(candidates)

    best_parameters = dict(best_row.get("parameters") or {})
    parameter_recommendations: dict[str, Any] = {}
    target_parameters: dict[str, Any] = {}
    ranges: dict[str, float] = {}
    for name, spec in specs.items():
        kind = spec.get("kind")
        if kind == "numeric":
            recommendation = _recommend_numeric_parameter(name, spec, candidates, completed, weights, best_parameters)
            numeric_allowed = [value for value in (_finite_float(item) for item in spec.get("values", [])) if value is not None]
            if numeric_allowed:
                ranges[name] = max(numeric_allowed) - min(numeric_allowed)
        else:
            recommendation = _recommend_discrete_parameter(name, spec, candidates, weights, best_parameters)
        parameter_recommendations[name] = recommendation
        if recommendation.get("recommended_value") is not None:
            target_parameters[name] = recommendation["recommended_value"]

    ranked_rows: list[tuple[float, float, int, pd.Series]] = []
    for row_number, (_, row) in enumerate(candidates.iterrows()):
        distance = _row_distance(row, target_parameters, specs, ranges)
        ranked_rows.append((distance, -float(row["effective_score"]), row_number, row))
    ranked_rows.sort(key=lambda item: item[:3])
    recommended_row = ranked_rows[0][3] if ranked_rows else best_row

    return {
        **base_payload,
        "best": _compact_row(best_row),
        "recommended": _compact_row(recommended_row),
        "parameters": parameter_recommendations,
        "candidate_pool": {
            "eligible_rows": int(len(completed)),
            "selected_rows": int(len(candidates)),
            "selection_rule": selection_rule,
            "effective_score_cutoff": cutoff,
            "quantile_cutoff": quantile_cutoff,
            "tolerance_cutoff": tolerance_cutoff,
        },
        "notes": [
            "Le best reste le maximum observé; la recommandation privilégie une zone robuste de configurations performantes.",
            "La ligne recommended correspond à une combinaison réellement testée, proche des sweet spots par paramètre.",
        ],
    }


def load_optimization_artifacts(job_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    results_path = job_dir / "results.json"
    config_path = job_dir / "optimization_config.json"
    results = json.loads(results_path.read_text(encoding="utf-8"))
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(results, list):
        raise ValueError(f"{results_path} must contain a JSON array")
    if not isinstance(config, dict):
        raise ValueError(f"{config_path} must contain a JSON object")
    return results, config


def write_optimization_recommendations(
    output_dir: Path,
    results: list[dict[str, Any]] | None = None,
    optimization_config: dict[str, Any] | None = None,
    *,
    top_quantile: float | None = None,
    score_tolerance_pct: float | None = None,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    if results is None or optimization_config is None:
        loaded_results, loaded_config = load_optimization_artifacts(output_dir)
        results = loaded_results if results is None else results
        optimization_config = loaded_config if optimization_config is None else optimization_config
    if top_quantile is None:
        top_quantile = optimization_config.get("top_quantile", DEFAULT_TOP_QUANTILE)
    if score_tolerance_pct is None:
        score_tolerance_pct = optimization_config.get("score_tolerance_pct", DEFAULT_SCORE_TOLERANCE_PCT)
    report = interpret_optimization_results(
        results,
        optimization_config,
        top_quantile=top_quantile,
        score_tolerance_pct=score_tolerance_pct,
    )
    report["path"] = str(output_dir / "recommendations.json")
    report = _json_safe(report)
    (output_dir / "recommendations.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=_json_default),
        encoding="utf-8",
    )
    return report
