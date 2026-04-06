from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd


PHASE_60_EVIDENCE_VERSION = "v2.4_phase_60"
DEFAULT_CANDIDATE_SOURCE_CATALOG: tuple[str, ...] = ("internal", "dice", "rule", "fallback")


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return float(default)
        if pd.isna(value):
            return float(default)
    except Exception:
        pass
    try:
        return float(value)
    except Exception:
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return int(default)
        if pd.isna(value):
            return int(default)
    except Exception:
        pass
    try:
        return int(value)
    except Exception:
        return int(default)


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except Exception:
        pass
    text = str(value).strip()
    return text or default


def _round_metric(value: Any, digits: int = 6) -> float:
    return round(_safe_float(value, 0.0), digits)


def _mean_numeric(rows: pd.DataFrame, column: str) -> float:
    return _round_metric(pd.to_numeric(rows.get(column, pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean())


def summarize_population_metrics_from_rows(
    rows: pd.DataFrame,
    *,
    source_catalog: Sequence[str] | None = None,
) -> dict[str, float | dict[str, float]]:
    resolved_catalog = tuple(source_catalog or DEFAULT_CANDIDATE_SOURCE_CATALOG)
    if rows.empty:
        metrics: dict[str, float | dict[str, float]] = {
            "candidate_pool_diversity_index": 0.0,
            "candidate_source_entropy": 0.0,
            "multi_path_rate": 0.0,
            "path_count": 0.0,
            "rankable_path_count": 0.0,
            "action_diversity_index": 0.0,
            "non_utilization_action_rate": 0.0,
            "institution_action_rate": 0.0,
            "non_empty_contender_share": 0.0,
            "approved_or_conditional_contender_share": 0.0,
            "mean_execution_aware_value": 0.0,
            "offer_ready_contender_share": 0.0,
            "provisional_offer_share": 0.0,
            "approval_shell_only_share": 0.0,
            "selected_plan_category_customer_only_rate": 0.0,
            "selected_plan_category_institution_assisted_rate": 0.0,
            "selected_plan_category_hybrid_rate": 0.0,
            "mean_approval_gap": 0.0,
            "mean_recoverability_score": 0.0,
            "threshold_reach_possible_rate": 0.0,
            "recoverability_bucket_distribution": {},
            "selected_source_distribution": {},
        }
        for source in resolved_catalog:
            metrics[f"best_source_{source}_rate"] = 0.0
        return metrics

    best_source = rows.get("best_source", pd.Series([""] * len(rows))).astype(str).str.strip().str.lower()
    contender_bucket = rows.get("best_contender_bucket", pd.Series([""] * len(rows))).astype(str).str.strip().str.upper()
    best_status = rows.get("best_status", pd.Series([""] * len(rows))).astype(str).str.strip().str.upper()
    offer_maturity = rows.get("best_offer_maturity", pd.Series(["none"] * len(rows))).astype(str).str.strip().str.lower()
    selected_path_type = rows.get("selected_path_type", pd.Series([""] * len(rows))).astype(str).str.strip().str.lower()

    metrics: dict[str, float | dict[str, float]] = {
        "candidate_pool_diversity_index": _mean_numeric(rows, "candidate_pool_diversity_index"),
        "candidate_source_entropy": _mean_numeric(rows, "candidate_source_entropy"),
        "multi_path_rate": _mean_numeric(rows, "multi_path_flag"),
        "path_count": _mean_numeric(rows, "path_count"),
        "rankable_path_count": _mean_numeric(rows, "rankable_path_count"),
        "action_diversity_index": _mean_numeric(rows, "action_diversity_index"),
        "non_utilization_action_rate": _mean_numeric(rows, "non_utilization_action_rate"),
        "institution_action_rate": _mean_numeric(rows, "institution_action_rate"),
        "non_empty_contender_share": _round_metric((contender_bucket != "EMPTY").mean()),
        "approved_or_conditional_contender_share": _round_metric(
            best_status.isin(["APPROVED", "CONDITIONAL", "NEEDS_REVIEW"]).mean()
        ),
        "mean_execution_aware_value": _mean_numeric(rows, "best_execution_aware_value"),
        "offer_ready_contender_share": _round_metric((offer_maturity == "active_rankable").mean()),
        "provisional_offer_share": _round_metric((offer_maturity == "provisional").mean()),
        "approval_shell_only_share": _round_metric((contender_bucket == "APPROVAL_SHELL_ONLY").mean()),
        "selected_plan_category_customer_only_rate": _round_metric((selected_path_type == "customer_only").mean()),
        "selected_plan_category_institution_assisted_rate": _round_metric(
            (selected_path_type == "institution_assisted").mean()
        ),
        "selected_plan_category_hybrid_rate": _round_metric((selected_path_type == "hybrid").mean()),
        "mean_approval_gap": _mean_numeric(rows, "approval_gap"),
        "mean_recoverability_score": _mean_numeric(rows, "recoverability_score"),
        "threshold_reach_possible_rate": _mean_numeric(rows, "threshold_reach_possible"),
    }
    recoverability_bucket = rows.get("recoverability_bucket", pd.Series([""] * len(rows))).astype(str).str.strip().str.lower()
    metrics["recoverability_bucket_distribution"] = {
        key: _round_metric(value)
        for key, value in recoverability_bucket[recoverability_bucket != ""].value_counts(normalize=True).sort_index().items()
    }
    selected_source_distribution: dict[str, float] = {}
    for source in resolved_catalog:
        rate = _round_metric((best_source == source).mean())
        metrics[f"best_source_{source}_rate"] = rate
        selected_source_distribution[source] = rate
    metrics["selected_source_distribution"] = selected_source_distribution
    return metrics


def _default_trust_regression_rows(
    movement_summary: Mapping[str, Any] | None,
    *,
    evidence_source: str,
) -> list[dict[str, Any]]:
    trust_guardrails = dict((movement_summary or {}).get("trust_guardrails", {}) or {})
    if not trust_guardrails:
        return []
    operator_signal_count = (
        _safe_int(trust_guardrails.get("approved_with_blocker_count", 0), 0)
        + _safe_int(trust_guardrails.get("approved_with_action_count", 0), 0)
        + _safe_int(trust_guardrails.get("approved_with_upgrade_condition_count", 0), 0)
        + _safe_int(trust_guardrails.get("action_blocker_mismatch_count", 0), 0)
        + _safe_int(trust_guardrails.get("readiness_decision_mismatch_count", 0), 0)
    )
    return [
        {
            "suite": "winner_integrity",
            "status": "clean" if _safe_int(trust_guardrails.get("selected_invalid_winner_count", 0), 0) == 0 else "regression",
            "evidence_source": evidence_source,
            "notes": f"selected_invalid_winner_count={_safe_int(trust_guardrails.get('selected_invalid_winner_count', 0), 0)}",
        },
        {
            "suite": "contender_quality",
            "status": "clean" if _safe_float(trust_guardrails.get("selected_dice_valid_rate", 1.0), 1.0) >= 1.0 else "regression",
            "evidence_source": evidence_source,
            "notes": f"selected_dice_valid_rate={_safe_float(trust_guardrails.get('selected_dice_valid_rate', 1.0), 1.0):.4f}",
        },
        {
            "suite": "selected_surface_consistency",
            "status": "clean" if _safe_int(trust_guardrails.get("selected_decision_mismatch_count", 0), 0) == 0 else "regression",
            "evidence_source": evidence_source,
            "notes": f"selected_decision_mismatch_count={_safe_int(trust_guardrails.get('selected_decision_mismatch_count', 0), 0)}",
        },
        {
            "suite": "operator_packet_coherence",
            "status": "clean" if operator_signal_count == 0 else "regression",
            "evidence_source": evidence_source,
            "notes": f"operator_regression_signal_count={operator_signal_count}",
        },
    ]


def build_cohort_evidence_package(
    population_name: str,
    population_metrics: Mapping[str, Any],
    movement_summary: Mapping[str, Any] | None,
    trust_regression_status: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    metrics = dict(population_metrics or {})
    movement_summary = dict(movement_summary or {})
    selected_source_distribution = dict(metrics.get("selected_source_distribution", {}) or {})
    if not selected_source_distribution:
        selected_source_distribution = {
            source: _safe_float(metrics.get(f"best_source_{source}_rate", 0.0), 0.0)
            for source in DEFAULT_CANDIDATE_SOURCE_CATALOG
        }
    trust_rows = [dict(row) for row in (trust_regression_status or [])]
    if not trust_rows:
        trust_rows = _default_trust_regression_rows(
            movement_summary,
            evidence_source=f"{population_name}:movement_guardrail_summary",
        )

    return {
        "population": population_name,
        "movement_potential": {
            "population": population_name,
            "non_empty_contender_share": _safe_float(
                metrics.get("non_empty_contender_share", metrics.get("candidate_generation_success_rate", 0.0)),
                0.0,
            ),
            "approved_or_conditional_contender_share": _safe_float(
                metrics.get("approved_or_conditional_contender_share", metrics.get("approved_or_conditional_rate", 0.0)),
                0.0,
            ),
            "mean_execution_aware_value": _safe_float(metrics.get("mean_execution_aware_value", 0.0), 0.0),
            "dominant_movement_bottleneck": _safe_str(movement_summary.get("dominant_movement_bottleneck"), "unknown"),
            "movement_guardrail_summary": _safe_str(movement_summary.get("movement_guardrail_summary"), ""),
        },
        "path_diversity": {
            "population": population_name,
            "multi_path_rate": _safe_float(metrics.get("multi_path_rate", 0.0), 0.0),
            "mean_path_count": _safe_float(metrics.get("path_count", metrics.get("mean_path_count", 0.0)), 0.0),
            "mean_rankable_path_count": _safe_float(
                metrics.get("rankable_path_count", metrics.get("mean_rankable_path_count", 0.0)),
                0.0,
            ),
            "mean_action_diversity_index": _safe_float(metrics.get("action_diversity_index", 0.0), 0.0),
        },
        "action_coverage": {
            "population": population_name,
            "non_utilization_action_rate": _safe_float(metrics.get("non_utilization_action_rate", 0.0), 0.0),
            "institution_action_rate": _safe_float(metrics.get("institution_action_rate", 0.0), 0.0),
            "offer_ready_contender_share": _safe_float(metrics.get("offer_ready_contender_share", 0.0), 0.0),
            "approval_shell_only_share": _safe_float(metrics.get("approval_shell_only_share", 0.0), 0.0),
        },
        "selected_path_distribution": {
            "population": population_name,
            "selected_customer_only_share": _safe_float(
                metrics.get("selected_plan_category_customer_only_rate", metrics.get("selected_customer_only_share", 0.0)),
                0.0,
            ),
            "selected_institution_assisted_share": _safe_float(
                metrics.get(
                    "selected_plan_category_institution_assisted_rate",
                    metrics.get("selected_institution_assisted_share", 0.0),
                ),
                0.0,
            ),
            "selected_hybrid_share": _safe_float(
                metrics.get("selected_plan_category_hybrid_rate", metrics.get("selected_hybrid_share", 0.0)),
                0.0,
            ),
            "selected_source_distribution": selected_source_distribution,
        },
        "recoverability_signal": {
            "population": population_name,
            "mean_approval_gap": _safe_float(metrics.get("mean_approval_gap", 0.0), 0.0),
            "mean_recoverability_score": _safe_float(metrics.get("mean_recoverability_score", 0.0), 0.0),
            "threshold_reach_possible_rate": _safe_float(metrics.get("threshold_reach_possible_rate", 0.0), 0.0),
            "recoverability_bucket_distribution": dict(metrics.get("recoverability_bucket_distribution", {}) or {}),
        },
        "trust_regression": trust_rows,
    }


def _movement_conclusion(packages: Sequence[Mapping[str, Any]]) -> str:
    bottlenecks = [
        _safe_str(dict(pkg.get("movement_potential", {}) or {}).get("dominant_movement_bottleneck"))
        for pkg in packages
    ]
    known = [value for value in bottlenecks if value and value != "unknown"]
    if not known:
        return "movement_diagnosis_pending"
    if all(value == "structural_cohort_limited" for value in known):
        return "structural_bottleneck_remains_dominant"
    if any(value == "structural_cohort_limited" for value in known):
        return "mixed_or_softened_structural_bottleneck"
    return "movement_headroom_detected_without_structural_dominance"


def _trust_conclusion(rows: Sequence[Mapping[str, Any]]) -> str:
    if not rows:
        return "trust_evaluation_not_provided"
    statuses = {_safe_str(row.get("status")).lower() for row in rows}
    if statuses.intersection({"failed", "regression", "blocked", "red"}):
        return "trust_regression_detected"
    if statuses.issubset({"clean", "passed", "green"}):
        return "trust_baseline_intact"
    return "trust_evaluation_incomplete"


def build_phase60_evidence_summary(
    packages: Sequence[Mapping[str, Any]],
    *,
    trust_regression_rows: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    package_list = [dict(pkg) for pkg in packages]
    movement_potential_table = [dict(pkg.get("movement_potential", {}) or {}) for pkg in package_list]
    path_diversity_table = [dict(pkg.get("path_diversity", {}) or {}) for pkg in package_list]
    action_coverage_table = [dict(pkg.get("action_coverage", {}) or {}) for pkg in package_list]
    selected_path_distribution_table = [dict(pkg.get("selected_path_distribution", {}) or {}) for pkg in package_list]
    recoverability_signal_table = [dict(pkg.get("recoverability_signal", {}) or {}) for pkg in package_list]
    if trust_regression_rows is not None:
        trust_regression_table = [dict(row) for row in trust_regression_rows]
    else:
        trust_regression_table = [dict(row) for pkg in package_list for row in list(pkg.get("trust_regression", []) or [])]
    return {
        "phase_60_evidence_version": PHASE_60_EVIDENCE_VERSION,
        "populations": [pkg.get("population", "") for pkg in package_list],
        "movement_potential_table": movement_potential_table,
        "path_diversity_table": path_diversity_table,
        "action_coverage_table": action_coverage_table,
        "selected_path_distribution_table": selected_path_distribution_table,
        "recoverability_signal_table": recoverability_signal_table,
        "trust_regression_table": trust_regression_table,
        "population_bottlenecks": {
            row.get("population", ""): row.get("dominant_movement_bottleneck", "")
            for row in movement_potential_table
        },
        "overall_movement_conclusion": _movement_conclusion(package_list),
        "overall_trust_conclusion": _trust_conclusion(trust_regression_table),
    }


def render_phase60_evidence_markdown(summary: Mapping[str, Any]) -> str:
    lines = [
        "# Phase 60 Cohort Evidence",
        "",
        f"- Evidence version: {_safe_str(summary.get('phase_60_evidence_version'), PHASE_60_EVIDENCE_VERSION)}",
        f"- Populations: {', '.join([_safe_str(value) for value in list(summary.get('populations', []) or [])]) or 'n/a'}",
        f"- Movement conclusion: {_safe_str(summary.get('overall_movement_conclusion'), 'movement_diagnosis_pending')}",
        f"- Trust conclusion: {_safe_str(summary.get('overall_trust_conclusion'), 'trust_evaluation_not_provided')}",
        "",
        "## Movement Potential",
    ]
    movement_rows = list(summary.get("movement_potential_table", []) or [])
    if movement_rows:
        for row in movement_rows:
            lines.append(
                "- "
                f"{_safe_str(row.get('population'), 'unknown')}: "
                f"non_empty={_safe_float(row.get('non_empty_contender_share'), 0.0):.4f}, "
                f"approve_or_conditional={_safe_float(row.get('approved_or_conditional_contender_share'), 0.0):.4f}, "
                f"execution_aware={_safe_float(row.get('mean_execution_aware_value'), 0.0):.4f}, "
                f"bottleneck={_safe_str(row.get('dominant_movement_bottleneck'), 'unknown')}"
            )
    else:
        lines.append("- n/a")
    lines.extend(["", "## Path Diversity"])
    path_rows = list(summary.get("path_diversity_table", []) or [])
    if path_rows:
        for row in path_rows:
            lines.append(
                "- "
                f"{_safe_str(row.get('population'), 'unknown')}: "
                f"multi_path={_safe_float(row.get('multi_path_rate'), 0.0):.4f}, "
                f"path_count={_safe_float(row.get('mean_path_count'), 0.0):.4f}, "
                f"rankable_path_count={_safe_float(row.get('mean_rankable_path_count'), 0.0):.4f}, "
                f"action_diversity={_safe_float(row.get('mean_action_diversity_index'), 0.0):.4f}"
            )
    else:
        lines.append("- n/a")
    lines.extend(["", "## Recoverability Signal"])
    recoverability_rows = list(summary.get("recoverability_signal_table", []) or [])
    if recoverability_rows:
        for row in recoverability_rows:
            bucket_distribution = dict(row.get("recoverability_bucket_distribution", {}) or {})
            lines.append(
                "- "
                f"{_safe_str(row.get('population'), 'unknown')}: "
                f"approval_gap={_safe_float(row.get('mean_approval_gap'), 0.0):.4f}, "
                f"recoverability_score={_safe_float(row.get('mean_recoverability_score'), 0.0):.4f}, "
                f"threshold_reach={_safe_float(row.get('threshold_reach_possible_rate'), 0.0):.4f}, "
                f"bucket_distribution={json.dumps(bucket_distribution, ensure_ascii=False, sort_keys=True)}"
            )
    else:
        lines.append("- n/a")
    lines.extend(["", "## Trust Regression"])
    trust_rows = list(summary.get("trust_regression_table", []) or [])
    if trust_rows:
        for row in trust_rows:
            lines.append(
                "- "
                f"{_safe_str(row.get('suite'), 'unknown')}: "
                f"status={_safe_str(row.get('status'), 'unknown')}, "
                f"evidence={_safe_str(row.get('evidence_source'), 'n/a')}, "
                f"notes={_safe_str(row.get('notes'), 'n/a')}"
            )
    else:
        lines.append("- n/a")
    return "\n".join(lines) + "\n"


def write_phase60_evidence_artifacts(
    output_root: Path,
    summary: Mapping[str, Any],
    *,
    prefix: str = "phase_60",
) -> dict[str, str]:
    output_root.mkdir(parents=True, exist_ok=True)
    json_path = output_root / f"{prefix}_cohort_evidence_summary.json"
    md_path = output_root / f"{prefix}_cohort_evidence_summary.md"
    movement_csv = output_root / f"{prefix}_movement_potential_table.csv"
    path_csv = output_root / f"{prefix}_path_diversity_table.csv"
    action_csv = output_root / f"{prefix}_action_coverage_table.csv"
    selected_csv = output_root / f"{prefix}_selected_path_distribution_table.csv"
    recoverability_csv = output_root / f"{prefix}_recoverability_signal_table.csv"
    trust_csv = output_root / f"{prefix}_trust_regression_table.csv"

    json_path.write_text(json.dumps(dict(summary), indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_phase60_evidence_markdown(summary), encoding="utf-8")
    pd.DataFrame(list(summary.get("movement_potential_table", []) or [])).to_csv(movement_csv, index=False)
    pd.DataFrame(list(summary.get("path_diversity_table", []) or [])).to_csv(path_csv, index=False)
    pd.DataFrame(list(summary.get("action_coverage_table", []) or [])).to_csv(action_csv, index=False)
    pd.DataFrame(list(summary.get("selected_path_distribution_table", []) or [])).to_csv(selected_csv, index=False)
    pd.DataFrame(list(summary.get("recoverability_signal_table", []) or [])).to_csv(recoverability_csv, index=False)
    pd.DataFrame(list(summary.get("trust_regression_table", []) or [])).to_csv(trust_csv, index=False)
    return {
        "cohort_evidence_summary_json": json_path.name,
        "cohort_evidence_summary_md": md_path.name,
        "movement_potential_table_csv": movement_csv.name,
        "path_diversity_table_csv": path_csv.name,
        "action_coverage_table_csv": action_csv.name,
        "selected_path_distribution_table_csv": selected_csv.name,
        "recoverability_signal_table_csv": recoverability_csv.name,
        "trust_regression_table_csv": trust_csv.name,
    }
