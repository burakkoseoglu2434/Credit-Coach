from __future__ import annotations

import argparse
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from credit_coach.causality.action_constraints import causal_penalty
from credit_coach.causality.graph_utils import load_graph
from credit_coach.causality.rex_runner import run_rex_adapter
from credit_coach.coaching.messaging import (
    build_adverse_action_reasons,
    build_customer_roadmap_narrative,
    build_recourse_path_render_payload,
)
from credit_coach.coaching.planner import (
    BestPlanSelectionResult,
    CANDIDATE_SOURCE_CATALOG,
    annotate_plan_planner_quality,
    candidate_pool_diversity_index,
    candidate_source_counts,
    candidate_source_entropy,
    candidate_source_presence_flags,
    choose_best_plan,
    contender_bucket_counts,
    execution_aware_value,
    filter_empty_contenders,
    filter_selectable_contenders,
)
from credit_coach.data.ingest import load_feature_contract
from credit_coach.data.schema import PlanAction, PlanRecord, RecoursePathRecord
from credit_coach.decision.ownership import build_customer_decision_payload
from credit_coach.evaluation.fairness import build_group_advantage_penalties, lookup_group_penalty
from credit_coach.evaluation.recoverability import (
    best_possible_pd_improvement_from_predictions,
    build_recoverability_signal,
    recoverability_risk_band,
    resolve_recoverability_thresholds,
)
from credit_coach.macro.impact import dynamic_alpha
from credit_coach.macro.sources import load_macro_snapshot_mock
from credit_coach.macro.stress_index import compute_macro_stress_index
from credit_coach.model.predict import predict_proba_pd
from credit_coach.model.registry import load_model_bundle
from credit_coach.recourse.action_space import (
    estimate_action_cost_usd,
    get_action_metadata,
    get_dice_generatable_features,
    get_action_spec,
    normalize_dice_target_value,
)
from credit_coach.recourse.action_constraints import enforce_action_constraints
from credit_coach.recourse.dice_baseline import generate_dice_counterfactual_actions
from credit_coach.recourse.dice_quality import (
    annotate_dice_candidate_quality,
    classify_dice_backend_class,
    dice_candidate_is_invalid,
    dice_candidate_is_warning,
    selected_dice_is_clean,
    split_dice_planner_eligible,
    summarize_dice_candidate_metrics,
)
from credit_coach.recourse.execution_probability import annotate_plan_execution_probability
from credit_coach.recourse.feasibility import apply_target_feasibility_with_details
from credit_coach.recourse.generator import build_canonical_plan_action, generate_nine_plans
from credit_coach.recourse.institution_quality import (
    annotate_rule_candidate_quality,
    split_rule_planner_eligible,
)
from credit_coach.recourse.institution_rules import generate_institution_rule_action_sets
from credit_coach.recourse.offer_optimization import annotate_offer_optimization
from credit_coach.recourse.pathing import build_recourse_path_records, summarize_path_metrics
from credit_coach.recourse.recommendation_validity import (
    annotate_action_recommendation_validity,
    annotate_plan_recommendation_validity,
)
from credit_coach.recourse.trajectory import (
    attach_canonical_trajectory,
    build_canonical_phases,
    build_nominal_trajectory_checkpoints,
    phase_id_for_month,
    phase_title,
    predict_plan_pd_at_month,
)
from credit_coach.safety.validator import validate_plan
from credit_coach.storage.repository import build_decision_logging_summary, save_plan
from credit_coach.utils.run_context import create_run_context, load_config
from credit_coach.xai.shap_local import compute_local_reason_bundle

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_recourse")

_ROADMAP_STEP_COLUMNS = [
    "customer_id",
    "best_plan_id",
    "phase_id",
    "phase_title",
    "target_window_weeks",
    "action_key",
    "action_class",
    "action_title",
    "action_group_id",
    "composite_action",
    "feature_name",
    "metric_key",
    "unit",
    "current_value",
    "target_value",
    "delta",
    "time_months",
    "due_month",
    "direction",
    "generation_notes_json",
    "estimated_cost_usd",
    "requires_institutional_approval",
    "approval_pending_semantic_only",
    "action_status",
    "constraint_family",
    "constraint_reason_codes_json",
    "was_clipped",
    "repair_applied",
    "dependency_gate",
    "semantic_preserved",
    "recommendation_validity_status",
    "recommendation_validity_codes_json",
    "recommendation_sanity_flag",
]

FLOAT_PARITY_TOLERANCE = 1e-6
_CHECKPOINT_WEEKS = (4, 12, 24)
_CRITICAL_SOURCE_SUMMARY_FIELDS = (
    "decision_status",
    "credit_readiness_stage",
    "plan_execution_probability",
    "approval_dependent_plan_probability",
    "offer_acceptance_probability",
    "combined_plan_realization_probability",
)
_DATA_ISSUE_CODE_ORDER = (
    "missing_required_field",
    "checkpoint_status_missing",
    "parity_mismatch",
    "zero_step_no_path",
)
_EXTERNAL_STATUS_BRIDGE = {
    "APPROVED": "APPROVED",
    "CONDITIONAL": "CONDITIONAL",
    "REJECTED": "REJECTED",
    "NEEDS_REVIEW": "CONDITIONAL",
    "PENDING": "CONDITIONAL",
    "": "CONDITIONAL",
}
_INTERNAL_STATUS_ALLOWED = {"APPROVED", "CONDITIONAL", "REJECTED", "NEEDS_REVIEW"}
_VALID_EXTERNAL_DECISIONS = {"APPROVED", "CONDITIONAL", "REJECTED"}
_VALID_INTERNAL_DECISIONS = {"APPROVED", "CONDITIONAL", "REJECTED", "NEEDS_REVIEW"}
_SELECTED_RECOMMENDATION_EMPTY_STATE_EN = "No valid recommendation path is currently available."
_SELECTED_RECOMMENDATION_EMPTY_STATE_TR = "Su an icin gecerli bir oneri yolu yok."
_SELECTED_RECOMMENDATION_PROJECTION_VERSION = "v2.2_phase_47"


@dataclass
class CustomerArtifactBundle:
    customer_id: str
    plans_df: pd.DataFrame
    roadmap: dict[str, Any]
    roadmap_steps_df: pd.DataFrame
    metrics_summary: dict[str, Any]
    paths_df: pd.DataFrame = field(default_factory=pd.DataFrame)


@dataclass
class CustomerRecourseRunResult:
    bundle: CustomerArtifactBundle
    local_reason_bundle: dict[str, Any]
    adverse_action_reasons: list[Any]
    dice_df: pd.DataFrame
    dice_records: list[PlanRecord]
    dice_backend: str
    dice_telemetry: dict[str, Any]
    candidate_pool_df: pd.DataFrame
    decision_log_record: dict[str, Any]
    decision_log_summary: dict[str, Any]


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate recourse plans")
    p.add_argument("--customer_id", type=str, default="demo")
    p.add_argument("--row_index", type=int, default=0)
    p.add_argument("--explain_only", action="store_true")
    p.add_argument("--base_config", type=str, default="configs/default.yaml")
    p.add_argument("--model_config", type=str, default="configs/model.yaml")
    p.add_argument("--recourse_config", type=str, default="configs/recourse.yaml")
    p.add_argument("--causality_config", type=str, default="configs/causality.yaml")
    p.add_argument("--safety_config", type=str, default="configs/safety.yaml")
    p.add_argument("--macro_config", type=str, default="configs/macro.yaml")
    p.add_argument("--model_version", type=str, default="")
    p.add_argument("--model_manifest", type=str, default="")
    return p.parse_args(argv)


def _merge_dict(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge_dict(out[k], v)
        else:
            out[k] = v
    return out


def _safe_float(v, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return float(default)


def _safe_int(v, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return int(default)


def _safe_text(v: Any, default: str = "") -> str:
    text = str(v or "").strip()
    return text or default


def _is_missing_contract_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return False


def _dedupe_issue_codes(values: Sequence[Any]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in values:
        code = _safe_text(raw)
        if not code:
            continue
        if code not in _DATA_ISSUE_CODE_ORDER:
            continue
        if code in seen:
            continue
        seen.add(code)
        ordered.append(code)
    return sorted(ordered, key=lambda code: _DATA_ISSUE_CODE_ORDER.index(code))


def _legacy_external_decision_status(value: Any) -> str:
    normalized = _safe_text(value).upper()
    return _EXTERNAL_STATUS_BRIDGE.get(normalized, "CONDITIONAL")


def _legacy_internal_decision_status(value: Any, fallback: str) -> str:
    normalized = _safe_text(value).upper()
    if normalized in _INTERNAL_STATUS_ALLOWED:
        return normalized
    return _safe_text(fallback, "CONDITIONAL").upper()


def _extract_checkpoint_status_map(checkpoints: Sequence[dict[str, Any]]) -> dict[int, str]:
    status_map = {week: "unknown" for week in _CHECKPOINT_WEEKS}
    for checkpoint in checkpoints:
        week = int(_safe_int(checkpoint.get("week", 0), 0))
        if week not in status_map:
            continue
        status_map[week] = _safe_text(checkpoint.get("status"), "unknown")
    return status_map


def _checkpoint_status_fallbacks(checkpoints: Sequence[Any]) -> tuple[list[dict[str, Any]], int]:
    normalized: list[dict[str, Any]] = []
    missing_count = 0
    for raw_checkpoint in checkpoints:
        checkpoint = dict(raw_checkpoint) if isinstance(raw_checkpoint, dict) else {}
        status = _safe_text(checkpoint.get("status"))
        if not status:
            status = "unknown"
            missing_count += 1
        checkpoint["status"] = status
        normalized.append(checkpoint)
    return normalized, missing_count


def _build_contract_health_from_summary(summary: dict[str, Any]) -> dict[str, Any]:
    critical_null_count = int(_safe_int(summary.get("critical_field_null_count", 0), 0))
    missing_checkpoint_status_count = int(_safe_int(summary.get("missing_checkpoint_status_count", 0), 0))
    field_count = max(1, len(_CRITICAL_SOURCE_SUMMARY_FIELDS))
    return {
        "critical_field_null_count": critical_null_count,
        "missing_checkpoint_status_count": missing_checkpoint_status_count,
        "raw_contract_pass": int(bool(_safe_int(summary.get("raw_contract_pass", 0), 0))),
        "parity_pass": int(bool(_safe_int(summary.get("parity_pass", 1), 1))),
        "data_issue_flag": int(bool(_safe_int(summary.get("data_issue_flag", 0), 0))),
        "data_issue_codes": _dedupe_issue_codes(summary.get("data_issue_codes", [])),
        "zero_step_flag": int(bool(_safe_int(summary.get("zero_step_flag", 0), 0))),
        "best_action_count": int(_safe_int(summary.get("best_action_count", 0), 0)),
        "checkpoint_status_4w": _safe_text(summary.get("checkpoint_status_4w"), "unknown"),
        "checkpoint_status_12w": _safe_text(summary.get("checkpoint_status_12w"), "unknown"),
        "checkpoint_status_24w": _safe_text(summary.get("checkpoint_status_24w"), "unknown"),
        "summary_field_completion_rate": float(max(0.0, (field_count - critical_null_count) / field_count)),
    }


def _selection_meta_dict(selection_result: BestPlanSelectionResult | None) -> dict[str, Any]:
    if selection_result is None:
        return {
            "selection_outcome": "",
            "selection_stage": "",
            "invalid_candidates_removed_count": 0,
            "preferred_pool_invalid_exhausted": 0,
            "no_valid_candidate_available": 0,
            "selected_from_widened_valid_pool": 0,
        }
    return {
        "selection_outcome": str(selection_result.selection_outcome),
        "selection_stage": str(selection_result.selection_stage),
        "invalid_candidates_removed_count": int(selection_result.invalid_candidates_removed_count),
        "preferred_pool_invalid_exhausted": int(bool(selection_result.preferred_pool_invalid_exhausted)),
        "no_valid_candidate_available": int(bool(selection_result.no_valid_candidate_available)),
        "selected_from_widened_valid_pool": int(bool(selection_result.selected_from_widened_valid_pool)),
    }


def _path_records_to_df(path_records: list[RecoursePathRecord]) -> pd.DataFrame:
    rows = [record.model_dump(mode="json") for record in path_records]
    if not rows:
        return pd.DataFrame(
            columns=[
                "path_id",
                "customer_id",
                "path_type",
                "path_signature",
                "rankable_flag",
                "path_rank",
                "representative_plan_id",
                "representative_plan_source",
                "representative_contender_bucket",
                "member_plan_ids",
                "member_plan_count",
                "member_source_counts",
                "action_keys",
                "action_owners",
                "action_categories",
                "primary_metric_keys",
                "offer_plan",
                "offer_maturity",
                "selected_path_flag",
            ]
        )
    return pd.DataFrame(rows)


def _attach_path_summary_to_roadmap(
    roadmap: dict[str, Any],
    *,
    path_records: list[RecoursePathRecord],
) -> dict[str, Any]:
    out = dict(roadmap or {})
    summary = dict(out.get("summary", {}) or {})
    path_metrics = summarize_path_metrics(path_records)
    summary.update(path_metrics)
    summary["available_path_ids"] = [record.path_id for record in path_records]
    summary["available_path_types"] = [str(record.path_type) for record in path_records]
    summary["available_path_count"] = int(len(path_records))
    summary["available_rankable_path_count"] = int(sum(1 for record in path_records if record.rankable_flag))
    summary["alternative_path_count"] = max(0, int(path_metrics.get("rankable_path_count", 0)) - 1)
    selected_path = next((record for record in path_records if record.selected_path_flag), None)
    if selected_path is not None:
        summary["selected_path_customer_summary"] = _safe_text(
            getattr(getattr(selected_path, "customer_summary", None), "en", None)
        )
        summary["selected_path_operator_summary"] = _safe_text(
            getattr(getattr(selected_path, "operator_summary", None), "en", None)
        )
        summary["selected_path_render_version"] = _safe_text(getattr(selected_path, "render_version", ""))
    else:
        summary["selected_path_customer_summary"] = ""
        summary["selected_path_operator_summary"] = ""
        summary["selected_path_render_version"] = ""
    out["summary"] = summary
    out["paths"] = [record.model_dump(mode="json") for record in path_records]
    return out


def _attach_path_render_summaries(
    path_records: list[RecoursePathRecord],
    *,
    plan_lookup: Mapping[str, PlanRecord],
) -> None:
    for record in path_records:
        representative_plan = plan_lookup.get(_safe_text(record.representative_plan_id))
        payload = build_recourse_path_render_payload(record, representative_plan)
        record.customer_summary = payload.get("customer_summary")
        record.operator_summary = payload.get("operator_summary")
        record.render_version = payload.get("render_version")


def _best_possible_pd_improvement_for_paths(
    *,
    base_pd: float,
    path_records: list[RecoursePathRecord],
    plan_lookup: Mapping[str, PlanRecord],
) -> float:
    representative_ids = [
        _safe_text(getattr(record, "representative_plan_id", ""))
        for record in path_records
        if bool(getattr(record, "rankable_flag", False))
    ]
    predicted_pds = [
        getattr(plan_lookup[plan_id], "predicted_pd", base_pd)
        for plan_id in representative_ids
        if plan_id in plan_lookup
    ]
    return best_possible_pd_improvement_from_predictions(
        base_pd=base_pd,
        predicted_pds=predicted_pds,
    )


def _attach_recoverability_signal_to_roadmap(
    roadmap: dict[str, Any],
    *,
    base_pd: float,
    tau: float,
    segment_context: Mapping[str, Any],
    path_records: list[RecoursePathRecord],
    plan_lookup: Mapping[str, PlanRecord],
) -> dict[str, Any]:
    out = dict(roadmap or {})
    summary = dict(out.get("summary", {}) or {})
    signal = build_recoverability_signal(
        base_pd=base_pd,
        tau=tau,
        thresholds={
            "near_upper": _safe_float(segment_context.get("recoverability_near_upper", 0.10), 0.10),
            "mid_upper": _safe_float(segment_context.get("recoverability_mid_upper", 0.25), 0.25),
        },
        has_valid_path_flag=bool(path_records),
        has_rankable_path_flag=any(bool(getattr(record, "rankable_flag", False)) for record in path_records),
        best_possible_pd_improvement=_best_possible_pd_improvement_for_paths(
            base_pd=base_pd,
            path_records=path_records,
            plan_lookup=plan_lookup,
        ),
        selection_outcome=_safe_text(summary.get("selection_outcome")),
        expected_readiness=_safe_text(summary.get("expected_readiness")),
        credit_readiness_stage=_safe_text(summary.get("credit_readiness_stage")),
        offer_maturity=_safe_text(summary.get("offer_maturity")),
        offer_plan=bool(_safe_int(summary.get("offer_plan", 0), 0)),
    )
    summary.update(signal)
    summary["recoverability_signal_reason_codes_json"] = json.dumps(
        signal["recoverability_signal_reason_codes"],
        ensure_ascii=False,
    )
    summary["recoverable_reason_codes_json"] = json.dumps(signal["recoverable_reason_codes"], ensure_ascii=False)
    out["summary"] = summary
    return out


def _selected_plan_id(best: PlanRecord | None) -> str:
    return str(best.plan_id) if best is not None else ""


def _selected_plan_source(best: PlanRecord | None) -> str:
    return str(getattr(best, "plan_source", "") or "") if best is not None else ""


def _derive_nominal_pd_improvement(*, base_pd: float, plan: PlanRecord) -> float:
    explicit = getattr(plan, "nominal_pd_improvement", None)
    if explicit is not None:
        return _safe_float(explicit, 0.0)
    predicted_pd = getattr(plan, "predicted_pd", None)
    if predicted_pd is None:
        return 0.0
    return float(base_pd - _safe_float(predicted_pd, base_pd))


def _localized_projection_payload(payload: Any) -> dict[str, str] | None:
    if isinstance(payload, dict):
        tr = _safe_text(payload.get("tr"))
        en = _safe_text(payload.get("en"))
        if tr or en:
            return {
                "tr": tr or en,
                "en": en or tr,
            }
    text = _safe_text(payload)
    if text:
        return {"tr": text, "en": text}
    return None


def _localized_projection_text(payload: Any, *, locale: str = "en") -> str | None:
    normalized = _localized_projection_payload(payload)
    if not normalized:
        return None
    primary = _safe_text(normalized.get(locale))
    if primary:
        return primary
    secondary = "tr" if locale == "en" else "en"
    return _safe_text(normalized.get(secondary)) or None


def _build_selected_surface_projection(roadmap: dict[str, Any]) -> dict[str, Any]:
    out = dict(roadmap or {})
    summary = dict(out.get("summary", {}) or {})
    narrative = dict(out.get("narrative", {}) or {})
    raw_steps = narrative.get("steps", [])
    steps = [step for step in raw_steps if isinstance(step, dict)] if isinstance(raw_steps, list) else []

    selection_outcome = _safe_text(summary.get("selection_outcome"))
    selected_decision_status = _safe_text(summary.get("decision_status"), "CONDITIONAL")
    selected_plan_status_internal = _safe_text(summary.get("selected_plan_status_internal"), _safe_text(out.get("best_status")))
    selected_action_count = int(_safe_int(summary.get("best_action_count", len(steps)), len(steps)))

    if selection_outcome == "no_valid_winner" or not _safe_text(summary.get("best_plan_id")):
        summary.update(
            {
                "selected_decision_status": selected_decision_status,
                "selected_plan_status_internal": None,
                "selected_recommendation_text": None,
                "selected_recommendation_text_localized": None,
                "selected_institution_condition": None,
                "selected_institution_condition_localized": None,
                "selected_recommendation_source": "empty_state",
                "selected_action_count": 0,
                "selected_recommendation_projection_version": _SELECTED_RECOMMENDATION_PROJECTION_VERSION,
            }
        )
        out["summary"] = summary
        return out

    selected_recommendation_payload = None
    selected_institution_condition_payload = None
    for raw_step in steps:
        if selected_recommendation_payload is None:
            selected_recommendation_payload = _localized_projection_payload(raw_step.get("primary_recommendation"))
            if selected_recommendation_payload is None:
                selected_recommendation_payload = _localized_projection_payload(raw_step.get("action_summary"))
        if selected_institution_condition_payload is None:
            selected_institution_condition_payload = _localized_projection_payload(raw_step.get("institution_condition"))
        if selected_recommendation_payload is not None and selected_institution_condition_payload is not None:
            break

    summary.update(
        {
            "selected_decision_status": selected_decision_status,
            "selected_plan_status_internal": selected_plan_status_internal or None,
            "selected_recommendation_text": _localized_projection_text(selected_recommendation_payload, locale="en"),
            "selected_recommendation_text_localized": selected_recommendation_payload,
            "selected_institution_condition": _localized_projection_text(
                selected_institution_condition_payload,
                locale="en",
            ),
            "selected_institution_condition_localized": selected_institution_condition_payload,
            "selected_recommendation_source": "selected_plan",
            "selected_action_count": max(0, selected_action_count),
            "selected_recommendation_projection_version": _SELECTED_RECOMMENDATION_PROJECTION_VERSION,
        }
    )
    out["summary"] = summary
    return out


def _inject_decision_inputs_into_roadmap(
    roadmap: dict[str, Any],
    *,
    best: PlanRecord | None,
    base_pd: float,
    local_reason_bundle: dict[str, Any] | None,
) -> dict[str, Any]:
    out = dict(roadmap or {})
    summary = dict(out.get("summary", {}) or {})
    nominal_pd_improvement = _derive_nominal_pd_improvement(base_pd=base_pd, plan=best) if best is not None else 0.0
    selected_plan_id = _safe_text(summary.get("best_plan_id"), _safe_text(out.get("best_plan_id"), _selected_plan_id(best)))
    plan_execution_probability = _safe_float(
        summary.get("plan_execution_probability", getattr(best, "plan_execution_probability", 0.0)),
        0.0,
    )
    summary.update(
        {
            "best_plan_id": selected_plan_id or None,
            "best_constraint_status": _safe_text(
                summary.get("best_constraint_status"),
                _safe_text(out.get("best_constraint_status"), str(getattr(best, "constraint_status", "") or "")),
            ),
            "plan_contract_pass": int(
                bool(
                    selected_plan_id
                    and str(getattr(best, "constraint_status", "valid") or "valid").strip().lower() != "invalid"
                )
            ),
            "offer_plan": int(bool(getattr(best, "offer_plan", False))),
            "rankable_offer_count": int(_safe_int(getattr(best, "rankable_offer_count", 0), 0)),
            "approval_pending_action_count": int(_safe_int(getattr(best, "approval_pending_action_count", 0), 0)),
            "nominal_pd_improvement": _safe_float(summary.get("nominal_pd_improvement", nominal_pd_improvement), nominal_pd_improvement),
            "expected_pd_improvement": _safe_float(
                summary.get(
                    "expected_pd_improvement",
                    (
                        getattr(best, "expected_pd_improvement", None)
                        if getattr(best, "expected_pd_improvement", None) is not None
                        else nominal_pd_improvement * plan_execution_probability
                    ),
                ),
                nominal_pd_improvement * plan_execution_probability,
            ),
            "local_explainability_confidence": _safe_float(
                summary.get("local_explainability_confidence", (local_reason_bundle or {}).get("meta", {}).get("explainability_confidence", 0.50)),
                0.50,
            ),
        }
    )
    out["summary"] = summary
    return out


def _apply_decision_ownership_to_roadmap(
    roadmap: dict[str, Any],
    *,
    debug_mode: bool = False,
) -> dict[str, Any]:
    out = dict(roadmap or {})
    summary = dict(out.get("summary", {}) or {})
    payload = build_customer_decision_payload(summary, debug_mode=debug_mode)
    summary.update(payload)
    out["summary"] = summary
    out["contract_health"] = _build_contract_health_from_summary(summary)
    return out


def _normalize_customer_roadmap_contract(roadmap: dict[str, Any]) -> dict[str, Any]:
    out = dict(roadmap or {})
    summary = dict(out.get("summary", {}) or {})
    checkpoints_raw = out.get("checkpoints", [])
    checkpoints, missing_checkpoint_status_count = _checkpoint_status_fallbacks(
        checkpoints_raw if isinstance(checkpoints_raw, list) else []
    )
    status_map = _extract_checkpoint_status_map(checkpoints)
    best_action_count = int(
        sum(
            len(phase.get("steps", []))
            for phase in out.get("phases", [])
            if isinstance(phase, dict) and isinstance(phase.get("steps", []), list)
        )
    )
    zero_step_flag = int(best_action_count == 0)
    plan_execution_probability = _safe_float(summary.get("plan_execution_probability", 0.0), 0.0)
    approval_dependent_plan_probability = (
        plan_execution_probability
        if _is_missing_contract_value(summary.get("approval_dependent_plan_probability"))
        else _safe_float(summary.get("approval_dependent_plan_probability", 0.0), plan_execution_probability)
    )
    offer_acceptance_probability = (
        0.0
        if _is_missing_contract_value(summary.get("offer_acceptance_probability"))
        else _safe_float(summary.get("offer_acceptance_probability", 0.0), 0.0)
    )
    combined_plan_realization_probability = (
        plan_execution_probability
        if _is_missing_contract_value(summary.get("combined_plan_realization_probability"))
        else _safe_float(summary.get("combined_plan_realization_probability", 0.0), plan_execution_probability)
    )
    summary.update(
        {
            "plan_execution_probability": plan_execution_probability,
            "approval_dependent_plan_probability": approval_dependent_plan_probability,
            "offer_acceptance_probability": offer_acceptance_probability,
            "combined_plan_realization_probability": combined_plan_realization_probability,
        }
    )

    critical_field_null_count = int(
        sum(1 for field in _CRITICAL_SOURCE_SUMMARY_FIELDS if _is_missing_contract_value(summary.get(field)))
    )
    missing_checkpoint_status_count = max(
        missing_checkpoint_status_count,
        int(_safe_int(summary.get("missing_checkpoint_status_count", 0), 0)),
    )
    data_issue_codes = _dedupe_issue_codes(summary.get("data_issue_codes", []))
    if critical_field_null_count > 0:
        data_issue_codes.append("missing_required_field")
    if missing_checkpoint_status_count > 0:
        data_issue_codes.append("checkpoint_status_missing")
    if zero_step_flag:
        data_issue_codes.append("zero_step_no_path")
    data_issue_codes = _dedupe_issue_codes(data_issue_codes)

    raw_contract_pass = int(critical_field_null_count == 0 and missing_checkpoint_status_count == 0)
    parity_pass = int(bool(_safe_int(summary.get("parity_pass", 1), 1)))
    data_issue_flag = int(
        critical_field_null_count > 0
        or missing_checkpoint_status_count > 0
        or parity_pass == 0
    )
    if parity_pass == 0:
        data_issue_codes.append("parity_mismatch")
        data_issue_codes = _dedupe_issue_codes(data_issue_codes)
    data_issue_flag = int(bool(data_issue_flag))
    final_policy_present = bool(_safe_text(summary.get("decision_policy_version")))
    if final_policy_present:
        decision_status = _safe_text(summary.get("decision_status"), "CONDITIONAL").upper()
        if decision_status not in _VALID_EXTERNAL_DECISIONS:
            decision_status = "CONDITIONAL"
        decision_status_internal = _safe_text(summary.get("decision_status_internal"), decision_status).upper()
        if decision_status_internal not in _VALID_INTERNAL_DECISIONS:
            decision_status_internal = "NEEDS_REVIEW"
        if zero_step_flag:
            decision_status = "REJECTED"
            decision_status_internal = "REJECTED"
    else:
        legacy_status = _safe_text(
            summary.get("decision_status"),
            _safe_text(out.get("best_status"), "CONDITIONAL"),
        ).upper()
        decision_status = _legacy_external_decision_status(legacy_status)
        decision_status_internal = _legacy_internal_decision_status(legacy_status, decision_status)
        if zero_step_flag:
            decision_status = "REJECTED"
            decision_status_internal = "REJECTED"
        elif parity_pass == 0:
            decision_status = "CONDITIONAL"
            decision_status_internal = "NEEDS_REVIEW"
        elif data_issue_flag:
            decision_status = "CONDITIONAL"
            decision_status_internal = decision_status

    summary.update(
        {
            "decision_status": decision_status,
            "decision_status_internal": decision_status_internal,
            "credit_readiness_stage": _safe_text(summary.get("credit_readiness_stage"), "not_ready_yet"),
            "plan_execution_probability": plan_execution_probability,
            "approval_dependent_plan_probability": approval_dependent_plan_probability,
            "offer_acceptance_probability": offer_acceptance_probability,
            "combined_plan_realization_probability": combined_plan_realization_probability,
            "best_action_count": best_action_count,
            "zero_step_flag": zero_step_flag,
            "critical_field_null_count": critical_field_null_count,
            "missing_checkpoint_status_count": missing_checkpoint_status_count,
            "checkpoint_status_4w": status_map[4],
            "checkpoint_status_12w": status_map[12],
            "checkpoint_status_24w": status_map[24],
            "raw_contract_pass": raw_contract_pass,
            "parity_pass": parity_pass,
            "data_issue_flag": data_issue_flag,
            "data_issue_codes": data_issue_codes,
        }
    )
    out["summary"] = summary
    out["checkpoints"] = checkpoints
    out["contract_health"] = _build_contract_health_from_summary(summary)
    return out


def _sync_metrics_summary_with_roadmap_summary(
    metrics_summary: dict[str, Any],
    *,
    roadmap: dict[str, Any],
) -> dict[str, Any]:
    out = dict(metrics_summary or {})
    summary = dict(roadmap.get("summary", {}) or {})
    contract_health = dict(roadmap.get("contract_health", {}) or {})
    out.update(
        {
            "decision_status": _safe_text(summary.get("decision_status"), "CONDITIONAL"),
            "decision_status_internal": _safe_text(summary.get("decision_status_internal"), "CONDITIONAL"),
            "selected_decision_status": _safe_text(summary.get("selected_decision_status"), _safe_text(summary.get("decision_status"), "CONDITIONAL")),
            "selected_plan_status_internal": _safe_text(summary.get("selected_plan_status_internal"), ""),
            "selected_recommendation_text": _safe_text(summary.get("selected_recommendation_text"), ""),
            "selected_recommendation_source": _safe_text(summary.get("selected_recommendation_source"), ""),
            "selected_action_count": int(_safe_int(summary.get("selected_action_count", 0), 0)),
            "selected_recommendation_projection_version": _safe_text(
                summary.get("selected_recommendation_projection_version"),
                "",
            ),
            "path_count": int(_safe_int(summary.get("path_count", 0), 0)),
            "rankable_path_count": int(_safe_int(summary.get("rankable_path_count", 0), 0)),
            "multi_path_flag": int(_safe_int(summary.get("multi_path_flag", 0), 0)),
            "customer_only_path_count": int(_safe_int(summary.get("customer_only_path_count", 0), 0)),
            "institution_assisted_path_count": int(_safe_int(summary.get("institution_assisted_path_count", 0), 0)),
            "hybrid_path_count": int(_safe_int(summary.get("hybrid_path_count", 0), 0)),
            "action_diversity_index": _safe_float(summary.get("action_diversity_index", 0.0), 0.0),
            "non_utilization_action_rate": _safe_float(summary.get("non_utilization_action_rate", 0.0), 0.0),
            "institution_action_rate": _safe_float(summary.get("institution_action_rate", 0.0), 0.0),
            "selected_path_id": _safe_text(summary.get("selected_path_id"), ""),
            "selected_path_type": _safe_text(summary.get("selected_path_type"), ""),
            "selected_path_rank": int(_safe_int(summary.get("selected_path_rank", 0), 0)),
            "selected_path_customer_summary": _safe_text(summary.get("selected_path_customer_summary"), ""),
            "selected_path_operator_summary": _safe_text(summary.get("selected_path_operator_summary"), ""),
            "selected_path_render_version": _safe_text(summary.get("selected_path_render_version"), ""),
            "decision_policy_version": _safe_text(summary.get("decision_policy_version"), ""),
            "decision_confidence": _safe_float(summary.get("decision_confidence", 0.0), 0.0),
            "expected_readiness": _safe_text(summary.get("expected_readiness"), ""),
            "decision_reason_summary": _safe_text(summary.get("decision_reason_summary"), ""),
            "decision_reason_primary": _safe_text(summary.get("decision_reason_primary"), ""),
            "decision_reason_drivers": list(summary.get("decision_reason_drivers", [])),
            "decision_reason_drivers_json": json.dumps(summary.get("decision_reason_drivers", []), ensure_ascii=False),
            "rejection_type": _safe_text(summary.get("rejection_type"), ""),
            "conditional_type": _safe_text(summary.get("conditional_type"), ""),
            "upgrade_condition": _safe_text(summary.get("upgrade_condition"), ""),
            "recommendation_validity_status": _safe_text(summary.get("recommendation_validity_status"), ""),
            "recommendation_invalid_action_count": int(_safe_int(summary.get("recommendation_invalid_action_count", 0), 0)),
            "recommendation_warning_action_count": int(_safe_int(summary.get("recommendation_warning_action_count", 0), 0)),
            "recommendation_validity_codes": list(summary.get("recommendation_validity_codes", [])),
            "recommendation_validity_codes_json": json.dumps(summary.get("recommendation_validity_codes", []), ensure_ascii=False),
            "recommendation_sanity_flag": int(bool(_safe_int(summary.get("recommendation_sanity_flag", 0), 0))),
            "dice_backend_class": _safe_text(summary.get("dice_backend_class"), ""),
            "dice_annotation_complete": int(bool(_safe_int(summary.get("dice_annotation_complete", 0), 0))),
            "dice_semantic_quality_status": _safe_text(summary.get("dice_semantic_quality_status"), ""),
            "dice_semantic_quality_codes": list(summary.get("dice_semantic_quality_codes", [])),
            "dice_semantic_quality_codes_json": json.dumps(
                summary.get("dice_semantic_quality_codes", []),
                ensure_ascii=False,
            ),
            "dice_contender_eligible": int(bool(_safe_int(summary.get("dice_contender_eligible", 0), 0))),
            "dice_semantic_warning_penalty": _safe_float(summary.get("dice_semantic_warning_penalty", 0.0), 0.0),
            "selection_outcome": _safe_text(summary.get("selection_outcome"), ""),
            "selection_stage": _safe_text(summary.get("selection_stage"), ""),
            "invalid_candidates_removed_count": int(_safe_int(summary.get("invalid_candidates_removed_count", 0), 0)),
            "preferred_pool_invalid_exhausted": int(bool(_safe_int(summary.get("preferred_pool_invalid_exhausted", 0), 0))),
            "no_valid_candidate_available": int(bool(_safe_int(summary.get("no_valid_candidate_available", 0), 0))),
            "selected_from_widened_valid_pool": int(bool(_safe_int(summary.get("selected_from_widened_valid_pool", 0), 0))),
            "approval_gap": _safe_float(summary.get("approval_gap", 0.0), 0.0),
            "normalized_gap": _safe_float(summary.get("normalized_gap", 0.0), 0.0),
            "recoverability_bucket": _safe_text(summary.get("recoverability_bucket"), ""),
            "recoverability_score": _safe_float(summary.get("recoverability_score", 0.0), 0.0),
            "has_valid_path_flag": int(bool(_safe_int(summary.get("has_valid_path_flag", 0), 0))),
            "has_rankable_path_flag": int(bool(_safe_int(summary.get("has_rankable_path_flag", 0), 0))),
            "threshold_reach_possible": int(bool(summary.get("threshold_reach_possible", False))),
            "hard_structural_blocker_flag": int(bool(_safe_int(summary.get("hard_structural_blocker_flag", 0), 0))),
            "soft_structural_blocker_flag": int(bool(_safe_int(summary.get("soft_structural_blocker_flag", 0), 0))),
            "structural_blocker_flag": int(bool(_safe_int(summary.get("structural_blocker_flag", 0), 0))),
            "hard_structural_blockers": list(summary.get("hard_structural_blockers", [])),
            "hard_structural_blockers_json": json.dumps(summary.get("hard_structural_blockers", []), ensure_ascii=False),
            "soft_structural_blockers": list(summary.get("soft_structural_blockers", [])),
            "soft_structural_blockers_json": json.dumps(summary.get("soft_structural_blockers", []), ensure_ascii=False),
            "recoverable_flag": int(bool(summary.get("recoverable_flag", False))),
            "recoverability_classifier_version": _safe_text(summary.get("recoverability_classifier_version"), ""),
            "recoverability_signal_reason_codes": list(summary.get("recoverability_signal_reason_codes", [])),
            "recoverability_signal_reason_codes_json": json.dumps(
                summary.get("recoverability_signal_reason_codes", []),
                ensure_ascii=False,
            ),
            "recoverable_reason_codes": list(summary.get("recoverable_reason_codes", [])),
            "recoverable_reason_codes_json": json.dumps(summary.get("recoverable_reason_codes", []), ensure_ascii=False),
            "realization_anchor": _safe_float(summary.get("realization_anchor", 0.0), 0.0),
            "strong_execution_flag": int(bool(_safe_int(summary.get("strong_execution_flag", 0), 0))),
            "offer_maturity": _safe_text(summary.get("offer_maturity"), ""),
            "decision_gate_trace": dict(summary.get("decision_gate_trace", {}) or {}),
            "decision_gate_trace_json": json.dumps(summary.get("decision_gate_trace", {}), ensure_ascii=False),
            "credit_readiness_stage": _safe_text(summary.get("credit_readiness_stage"), "not_ready_yet"),
            "plan_execution_probability": _safe_float(summary.get("plan_execution_probability", 0.0), 0.0),
            "approval_dependent_plan_probability": _safe_float(
                summary.get("approval_dependent_plan_probability", 0.0),
                0.0,
            ),
            "offer_acceptance_probability": _safe_float(summary.get("offer_acceptance_probability", 0.0), 0.0),
            "combined_plan_realization_probability": _safe_float(
                summary.get("combined_plan_realization_probability", 0.0),
                0.0,
            ),
            "best_action_count": int(_safe_int(summary.get("best_action_count", 0), 0)),
            "zero_step_flag": int(bool(_safe_int(summary.get("zero_step_flag", 0), 0))),
            "critical_field_null_count": int(_safe_int(summary.get("critical_field_null_count", 0), 0)),
            "missing_checkpoint_status_count": int(_safe_int(summary.get("missing_checkpoint_status_count", 0), 0)),
            "checkpoint_status_4w": _safe_text(summary.get("checkpoint_status_4w"), "unknown"),
            "checkpoint_status_12w": _safe_text(summary.get("checkpoint_status_12w"), "unknown"),
            "checkpoint_status_24w": _safe_text(summary.get("checkpoint_status_24w"), "unknown"),
            "raw_contract_pass": int(bool(_safe_int(summary.get("raw_contract_pass", 0), 0))),
            "parity_pass": int(bool(_safe_int(summary.get("parity_pass", 1), 1))),
            "data_issue_flag": int(bool(_safe_int(summary.get("data_issue_flag", 0), 0))),
            "data_issue_codes": list(summary.get("data_issue_codes", [])),
            "summary_field_completion_rate": float(
                contract_health.get("summary_field_completion_rate", 0.0)
            ),
        }
    )
    return out


def _compute_income_edges(values: pd.Series, quantiles: list[float]) -> tuple[float, float, float]:
    s = pd.to_numeric(values, errors="coerce").dropna()
    if s.empty:
        return (0.0, 0.0, 0.0)
    q = [max(0.0, min(1.0, float(v))) for v in quantiles]
    if len(q) != 3:
        q = [0.25, 0.50, 0.75]
    q1, q2, q3 = [float(s.quantile(v)) for v in q]
    return (q1, q2, q3)


def _income_band_from_value(value: float, edges: tuple[float, float, float]) -> str:
    q1, q2, q3 = edges
    v = float(value)
    if v <= q1:
        return "q1"
    if v <= q2:
        return "q2"
    if v <= q3:
        return "q3"
    return "q4"


def _risk_band_from_pd(base_pd: float, tau: float, segment_caps_cfg: dict) -> str:
    thresholds = resolve_recoverability_thresholds(segment_caps_cfg)
    return recoverability_risk_band(
        approval_gap=max(0.0, float(base_pd) - float(tau)),
        near_upper=thresholds["near_upper"],
        mid_upper=thresholds["mid_upper"],
    )


def _build_segment_context(
    *,
    row: pd.Series,
    base_pd: float,
    tau: float,
    denied_mode: bool,
    segment_caps_cfg: dict,
    income_edges: tuple[float, float, float],
) -> dict:
    annual_inc = _safe_float(row.get("annual_inc"), 0.0)
    income_band = _income_band_from_value(annual_inc, income_edges)
    risk_band = _risk_band_from_pd(base_pd, tau, segment_caps_cfg)
    thresholds = resolve_recoverability_thresholds(segment_caps_cfg)

    enabled = bool(segment_caps_cfg.get("enabled", False))
    denied_only = bool(segment_caps_cfg.get("denied_only", True))
    can_apply = enabled and (not denied_only or denied_mode)

    income_mult_map = (
        segment_caps_cfg.get("income_band_multipliers", {})
        if isinstance(segment_caps_cfg.get("income_band_multipliers", {}), dict)
        else {}
    )
    risk_mult_map = (
        segment_caps_cfg.get("risk_band_multipliers", {})
        if isinstance(segment_caps_cfg.get("risk_band_multipliers", {}), dict)
        else {}
    )
    m_income = float(income_mult_map.get(income_band, 1.0))
    m_risk = float(risk_mult_map.get(risk_band, 1.0))
    m_total = float(m_income * m_risk)

    max_mult = max(1.0, float(segment_caps_cfg.get("cap_multiplier_max", 2.2)))
    min_mult = max(0.0, float(segment_caps_cfg.get("cap_multiplier_min", 1.0)))
    m_total = min(max_mult, max(min_mult, m_total))
    if not can_apply:
        m_total = 1.0
        m_income = 1.0
        m_risk = 1.0

    feature_mults: dict[str, float] = {}
    feature_cfg = (
        segment_caps_cfg.get("feature_cap_multipliers", {})
        if isinstance(segment_caps_cfg.get("feature_cap_multipliers", {}), dict)
        else {}
    )
    for feat, feat_rules in feature_cfg.items():
        if not isinstance(feat_rules, dict):
            continue
        inc_m = float(feat_rules.get("income_band_multipliers", {}).get(income_band, 1.0)) if isinstance(
            feat_rules.get("income_band_multipliers", {}), dict
        ) else 1.0
        risk_m = float(feat_rules.get("risk_band_multipliers", {}).get(risk_band, 1.0)) if isinstance(
            feat_rules.get("risk_band_multipliers", {}), dict
        ) else 1.0
        feature_mults[str(feat)] = float(max(0.0, inc_m * risk_m))

    return {
        "income_band": income_band,
        "risk_band": risk_band,
        "recoverability_near_upper": float(thresholds["near_upper"]),
        "recoverability_mid_upper": float(thresholds["mid_upper"]),
        "segment_caps_applied": bool(can_apply and abs(m_total - 1.0) > 1e-12),
        "cap_multiplier_income": float(m_income),
        "cap_multiplier_risk": float(m_risk),
        "cap_multiplier": float(m_total),
        "cap_multiplier_min": float(min_mult),
        "cap_multiplier_max": float(max_mult),
        "feature_cap_multipliers": feature_mults,
    }


def _is_denied_target(base_pd: float, tau: float, denied_cfg: dict) -> bool:
    if not bool(denied_cfg.get("enabled", False)):
        return False
    margin = float(denied_cfg.get("activation_margin", 0.0))
    return float(base_pd) > float(tau) + margin


def _effective_recourse_search(
    *,
    base_pd: float,
    tau: float,
    topk: int,
    horizons: list[int],
    strategies: list[str],
    robust_cfg: dict,
    dice_cfg: dict,
    rec_cfg: dict,
) -> tuple[dict, dict, dict]:
    denied_cfg = rec_cfg.get("denied_target", {}) if isinstance(rec_cfg.get("denied_target", {}), dict) else {}
    action_budget_cfg = rec_cfg.get("action_budget", {}) if isinstance(rec_cfg.get("action_budget", {}), dict) else {}
    search_budget_cfg = rec_cfg.get("search_budget", {}) if isinstance(rec_cfg.get("search_budget", {}), dict) else {}
    adaptive_cfg_raw = rec_cfg.get("adaptive_steps", {}) if isinstance(rec_cfg.get("adaptive_steps", {}), dict) else {}
    weekly_cfg_raw = rec_cfg.get("weekly_optimizer", {}) if isinstance(rec_cfg.get("weekly_optimizer", {}), dict) else {}
    adaptive_cfg = dict(adaptive_cfg_raw)
    weekly_cfg = dict(weekly_cfg_raw)
    if bool(adaptive_cfg.get("only_denied", False)):
        adaptive_cfg["enabled"] = False
    if bool(weekly_cfg.get("only_denied", True)):
        weekly_cfg["enabled"] = False
    action_budget_enabled = bool(action_budget_cfg.get("enabled", False))
    max_actions_regular = int(action_budget_cfg.get("max_actions_regular", topk))
    max_actions_denied = int(action_budget_cfg.get("max_actions_denied", max(max_actions_regular, topk)))
    effective = {
        "is_denied_target": False,
        "topk": int(topk),
        "horizons": list(horizons),
        "strategies": list(strategies),
        "search_cfg": {
            "adaptive_steps": adaptive_cfg,
            "weekly_optimizer": weekly_cfg,
            "denied_mode": False,
            "action_budget": {
                "enabled": action_budget_enabled,
                "max_actions": max_actions_regular,
            },
            "time_budget_ms": int(search_budget_cfg.get("per_customer_time_budget_ms", 0)),
            "candidate_pool_max_size": int(search_budget_cfg.get("candidate_pool_max_size", 0)),
            "skip_dice_when_internal_approved": bool(search_budget_cfg.get("skip_dice_when_internal_approved", False)),
            "skip_dice_for_non_denied": bool(search_budget_cfg.get("skip_dice_for_non_denied", False)),
        },
    }
    robust_eff = dict(robust_cfg or {})
    dice_eff = dict(dice_cfg or {})

    if not _is_denied_target(base_pd, tau, denied_cfg):
        return effective, robust_eff, dice_eff

    effective["is_denied_target"] = True
    effective["search_cfg"]["denied_mode"] = True
    if bool(adaptive_cfg_raw.get("only_denied", False)):
        denied_adaptive = dict(adaptive_cfg_raw)
        denied_adaptive["enabled"] = bool(adaptive_cfg_raw.get("enabled", True))
        effective["search_cfg"]["adaptive_steps"] = denied_adaptive
    if bool(weekly_cfg_raw.get("only_denied", True)):
        denied_weekly = dict(weekly_cfg_raw)
        denied_weekly["enabled"] = bool(weekly_cfg_raw.get("enabled", True))
        effective["search_cfg"]["weekly_optimizer"] = denied_weekly
    topk_multiplier = max(1.0, float(denied_cfg.get("topk_multiplier", 1.5)))
    min_topk = max(1, int(denied_cfg.get("min_topk", topk)))
    effective["topk"] = max(min_topk, int(round(topk * topk_multiplier)))

    denied_horizons = denied_cfg.get("horizons", horizons)
    if isinstance(denied_horizons, list) and denied_horizons:
        filtered = [int(h) for h in denied_horizons if int(h) in (3, 6, 12)]
        if filtered:
            effective["horizons"] = filtered

    denied_strategies = denied_cfg.get("strategies", strategies)
    if isinstance(denied_strategies, list) and denied_strategies:
        filtered_s = [str(s) for s in denied_strategies if str(s) in {"conservative", "balanced", "aggressive"}]
        if filtered_s:
            effective["strategies"] = filtered_s

    robust_eff["min_reliability"] = float(denied_cfg.get("strict_min_reliability", robust_eff.get("min_reliability", 0.7)))
    robust_eff["min_worst_risk_margin"] = float(
        denied_cfg.get("strict_min_worst_risk_margin", robust_eff.get("min_worst_risk_margin", -0.05))
    )

    dice_eff["total_cfs"] = int(
        max(
            1,
            round(
                int(dice_eff.get("total_cfs", 3))
                * max(1.0, float(denied_cfg.get("dice_total_cfs_multiplier", 1.5)))
            ),
        )
    )
    dice_eff["max_actions"] = int(
        max(
            1,
            round(
                int(dice_eff.get("max_actions", 4))
                * max(1.0, float(denied_cfg.get("dice_max_actions_multiplier", 1.5)))
            ),
        )
    )
    denied_max_actions = int(denied_cfg.get("max_actions", max_actions_denied))
    effective["search_cfg"]["action_budget"] = {
        "enabled": action_budget_enabled,
        "max_actions": denied_max_actions,
    }
    return effective, robust_eff, dice_eff


def _plan_cost(plan: PlanRecord) -> float:
    return float(sum(float(a.estimated_cost_usd) for a in plan.actions))


def _plan_proximity_l1(plan: PlanRecord) -> float:
    return float(sum(abs(float(a.delta)) for a in plan.actions))


def _phase_id_for_month(month: int) -> str:
    return phase_id_for_month(month)


def _phase_title(phase_id: str) -> str:
    return phase_title(phase_id)


def _decision_log_record(
    *,
    run_id: str,
    customer_id: str,
    plan: PlanRecord | None,
) -> dict:
    if plan is None:
        return {
            "decision_id": f"{run_id}_{customer_id}",
            "run_id": str(run_id),
            "customer_id": str(customer_id),
            "policy_arm": "control",
            "policy_arm_profile": {
                "offer_family": "control",
                "scoring_profile": "control",
                "term_generation_rule": "",
            },
            "candidate_set_id": f"{run_id}:{customer_id}",
            "selected_plan_id": "",
            "selected_plan_status": "",
            "selected_offer_type": "",
            "selection_propensity": 0.0,
            "propensity_source": "no_valid_winner",
            "reason_codes": ["no_valid_winner"],
            "recommended_plan_flag": False,
            "selected_plan_policy_label": "",
            "trajectory_status": "",
            "decision_status": "REJECTED",
            "approved": False,
            "predicted_pd": 0.0,
            "plan_execution_probability": None,
            "mean_group_difficulty_score": None,
            "peak_group_difficulty_score": None,
            "follow_through_readiness_label": "",
            "approval_dependent_plan_probability": None,
            "offer_acceptance_probability": None,
            "combined_plan_realization_probability": None,
        }
    policy_arm = str(getattr(plan, "offer_policy_arm", "") or "control")
    if policy_arm == "control":
        policy_arm_profile = {
            "offer_family": "control",
            "scoring_profile": "control",
            "term_generation_rule": "",
        }
    else:
        policy_arm_profile = {
            "offer_family": str(getattr(plan, "offer_family", "") or ""),
            "scoring_profile": str(getattr(plan, "offer_scoring_profile", "") or ""),
            "term_generation_rule": str(getattr(plan, "term_generation_rule", "") or ""),
        }
    reason_codes = []
    if str(plan.status_reason or "").strip():
        reason_codes.extend(piece for piece in str(plan.status_reason).split("|") if piece)
    if not reason_codes:
        reason_codes = ["selected_best_plan"]
    return {
        "decision_id": f"{run_id}_{customer_id}",
        "run_id": str(run_id),
        "customer_id": str(customer_id),
        "policy_arm": policy_arm,
        "policy_arm_profile": policy_arm_profile,
        "candidate_set_id": f"{run_id}:{customer_id}",
        "selected_plan_id": str(plan.plan_id),
        "selected_plan_status": str(plan.status),
        "selected_offer_type": str(getattr(plan, "dominant_offer_type", "") or ""),
        "selection_propensity": 1.0,
        "propensity_source": "deterministic_fallback",
        "reason_codes": reason_codes,
        "recommended_plan_flag": True,
        "selected_plan_policy_label": str(getattr(plan, "trajectory_policy_label", "") or ""),
        "trajectory_status": str(getattr(plan, "trajectory_status", "") or ""),
        "decision_status": str(plan.status),
        "approved": bool(str(plan.status) == "APPROVED"),
        "predicted_pd": _safe_float(getattr(plan, "predicted_pd", None), 0.0),
        "plan_execution_probability": (
            _safe_float(getattr(plan, "plan_execution_probability", 0.0), 0.0)
            if getattr(plan, "plan_execution_probability", None) is not None
            else None
        ),
        "mean_group_difficulty_score": (
            _safe_float(getattr(plan, "mean_group_difficulty_score", 0.0), 0.0)
            if getattr(plan, "mean_group_difficulty_score", None) is not None
            else None
        ),
        "peak_group_difficulty_score": (
            _safe_float(getattr(plan, "peak_group_difficulty_score", 0.0), 0.0)
            if getattr(plan, "peak_group_difficulty_score", None) is not None
            else None
        ),
        "dominant_difficulty_label": str(getattr(plan, "dominant_difficulty_label", "") or ""),
        "follow_through_readiness_label": str(getattr(plan, "follow_through_readiness_label", "") or ""),
        "approval_dependent_plan_probability": (
            _safe_float(getattr(plan, "approval_dependent_plan_probability", 0.0), 0.0)
            if getattr(plan, "approval_dependent_plan_probability", None) is not None
            else None
        ),
        "offer_acceptance_probability": (
            _safe_float(getattr(plan, "offer_acceptance_probability", 0.0), 0.0)
            if getattr(plan, "offer_acceptance_probability", None) is not None
            else None
        ),
        "combined_plan_realization_probability": (
            _safe_float(getattr(plan, "combined_plan_realization_probability", 0.0), 0.0)
            if getattr(plan, "combined_plan_realization_probability", None) is not None
            else None
        ),
    }


def _sync_decision_log_with_roadmap_summary(
    decision_log_record: dict[str, Any],
    *,
    roadmap: dict[str, Any],
) -> dict[str, Any]:
    out = dict(decision_log_record or {})
    summary = dict(roadmap.get("summary", {}) or {})
    out.update(
        {
            "decision_status": _safe_text(summary.get("decision_status"), _safe_text(out.get("decision_status"), "CONDITIONAL")),
            "approved": bool(_safe_text(summary.get("decision_status"), "").upper() == "APPROVED"),
            "plan_execution_probability": _safe_float(summary.get("plan_execution_probability", out.get("plan_execution_probability", 0.0)), 0.0),
            "approval_dependent_plan_probability": _safe_float(
                summary.get("approval_dependent_plan_probability", out.get("approval_dependent_plan_probability", 0.0)),
                0.0,
            ),
            "offer_acceptance_probability": _safe_float(
                summary.get("offer_acceptance_probability", out.get("offer_acceptance_probability", 0.0)),
                0.0,
            ),
            "combined_plan_realization_probability": _safe_float(
                summary.get("combined_plan_realization_probability", out.get("combined_plan_realization_probability", 0.0)),
                0.0,
            ),
            "reason_codes": list(out.get("reason_codes", []) or []),
        }
    )
    return out


def _build_customer_roadmap(
    *,
    customer_id: str,
    base_pd: float,
    tau: float,
    best: PlanRecord | None,
    best_source: str,
    selection_result: BestPlanSelectionResult,
    row: pd.Series,
    model,
    calibrator,
    feature_cols: list[str],
    local_reason_bundle: dict | None = None,
) -> dict:
    if best is not None and not list(getattr(best, "phases", [])):
        best.phases = build_canonical_phases(
            best.actions,
            base_pd=base_pd,
            predicted_pd=getattr(best, "predicted_pd", None),
            tau=tau,
        )
    if best is not None and not list(getattr(best, "trajectory_checkpoints", [])):
        best.trajectory_checkpoints = build_nominal_trajectory_checkpoints(
            row=row,
            plan=best,
            base_pd=base_pd,
            tau=tau,
            model=model,
            calibrator=calibrator,
            feature_cols=feature_cols,
        )

    phases: list[dict] = []
    for phase in list(getattr(best, "phases", [])):
        steps = []
        for step_idx, action in enumerate(list(getattr(phase, "steps", [])), start=1):
            step_id = (
                str(getattr(action, "action_group_id", "") or "")
                or str(getattr(action, "action_key", "") or "")
                or f"{getattr(phase, 'phase_id', 'phase')}_step_{step_idx}"
            )
            business_view = getattr(action, "business_view").model_dump(mode="json")
            technical_view = getattr(action, "technical_view").model_dump(mode="json")
            primary_numeric_target = getattr(action, "primary_numeric_target", None)
            steps.append(
                {
                    "step_id": step_id,
                    "action_key": str(business_view.get("action_key", "") or ""),
                    "action_class": str(business_view.get("action_class", "") or ""),
                    "action_family": str(business_view.get("action_family", "") or ""),
                    "action_title": str(business_view.get("action_title", "") or ""),
                    "action_description": str(business_view.get("action_description", "") or ""),
                    "action_group_id": str(business_view.get("action_group_id", "") or ""),
                    "business_view": business_view,
                    "technical_view": technical_view,
                    "primary_numeric_target": (
                        primary_numeric_target.model_dump(mode="json")
                        if primary_numeric_target is not None
                        else None
                    ),
                    "composite_action": int(bool(getattr(action, "composite_action", False))),
                    "time_months": int(max(1, _safe_int(getattr(action, "time_months", 1), 1))),
                    "estimated_cost_usd": _safe_float(getattr(action, "estimated_cost_usd", 0.0), 0.0),
                    "requires_institutional_approval": int(
                        bool(getattr(action, "requires_institutional_approval", False))
                    ),
                    "institutional_approval_state": str(getattr(action, "institutional_approval_state", "") or ""),
                    "approval_pending_semantic_only": int(
                        bool(getattr(action, "approval_pending_semantic_only", False))
                    ),
                    "offer_type": str(getattr(action, "offer_type", "") or ""),
                    "offer_terms": dict(getattr(action, "offer_terms", {}) or {}),
                    "offer_terms_complete": int(bool(getattr(action, "offer_terms_complete", False))),
                    "requires_acceptance": int(bool(getattr(action, "requires_acceptance", False))),
                    "offer_family": str(getattr(action, "offer_family", "") or ""),
                    "offer_scoring_profile": str(getattr(action, "offer_scoring_profile", "") or ""),
                    "term_generation_rule": str(getattr(action, "term_generation_rule", "") or ""),
                    "offer_policy_arm": str(getattr(action, "offer_policy_arm", "") or ""),
                    "plan_constraint_status": str(getattr(best, "constraint_status", "valid") or "valid"),
                    "action_status": str(getattr(action, "action_status", "") or ""),
                    "action_status_reason": str(getattr(action, "action_status_reason", "") or ""),
                    "constraint_family": str(getattr(action, "constraint_family", "") or ""),
                    "constraint_reason_codes": list(getattr(action, "constraint_reason_codes", [])),
                    "was_clipped": int(bool(getattr(action, "was_clipped", False))),
                    "repair_applied": int(bool(getattr(action, "repair_applied", False))),
                    "dependency_gate": int(bool(getattr(action, "dependency_gate", False))),
                    "semantic_preserved": getattr(action, "semantic_preserved", None),
                    "diagnostic_flags": list(getattr(action, "diagnostic_flags", [])),
                    "action_execution_probability": (
                        _safe_float(getattr(action, "action_execution_probability", 0.0), 0.0)
                        if getattr(action, "action_execution_probability", None) is not None
                        else None
                    ),
                    "approval_dependent_probability": (
                        _safe_float(getattr(action, "approval_dependent_probability", 0.0), 0.0)
                        if getattr(action, "approval_dependent_probability", None) is not None
                        else None
                    ),
                    "action_group_execution_probability": (
                        _safe_float(getattr(action, "action_group_execution_probability", 0.0), 0.0)
                        if getattr(action, "action_group_execution_probability", None) is not None
                        else None
                    ),
                    "difficulty_score": (
                        _safe_float(getattr(action, "difficulty_score", 0.0), 0.0)
                        if getattr(action, "difficulty_score", None) is not None
                        else None
                    ),
                    "difficulty_label": str(getattr(action, "difficulty_label", "") or ""),
                    "difficulty_drivers": dict(getattr(action, "difficulty_drivers", {}) or {}),
                    "approval_friction": (
                        _safe_float(getattr(action, "approval_friction", 0.0), 0.0)
                        if getattr(action, "approval_friction", None) is not None
                        else None
                    ),
                    "recommendation_validity_status": str(getattr(action, "recommendation_validity_status", "") or ""),
                    "recommendation_validity_codes": list(getattr(action, "recommendation_validity_codes", []) or []),
                    "recommendation_sanity_flag": int(bool(getattr(action, "recommendation_sanity_flag", False))),
                }
            )
        phases.append(
            {
                "phase_id": str(getattr(phase, "phase_id", "") or ""),
                "phase_title": str(getattr(phase, "phase_title", "") or ""),
                "target_window_weeks": str(getattr(phase, "target_window_weeks", "") or ""),
                "target_window_months": list(getattr(phase, "target_window_months", [])),
                "review_week": int(_safe_int(getattr(phase, "review_week", 4), 4)),
                "target_pd": (
                    _safe_float(getattr(phase, "target_pd", 0.0), 0.0)
                    if getattr(phase, "target_pd", None) is not None
                    else None
                ),
                "gate_pass_target": bool(getattr(phase, "gate_pass_target", False)),
                "action_count": int(len(steps)),
                "phase_cost_usd": float(sum(float(step.get("estimated_cost_usd", 0.0)) for step in steps)),
                "steps": steps,
            }
        )

    checkpoints: list[dict] = []
    for checkpoint in list(getattr(best, "trajectory_checkpoints", [])):
        checkpoint_week = int(_safe_int(getattr(checkpoint, "week", 0), 0))
        checkpoints.append(
            {
                "checkpoint_id": f"checkpoint_week_{checkpoint_week}",
                "week": checkpoint_week,
                "month": int(_safe_int(getattr(checkpoint, "month", 0), 0)),
                "phase_id": str(getattr(checkpoint, "phase_id", "") or ""),
                "checkpoint_type": str(getattr(checkpoint, "checkpoint_type", "") or ""),
                "checkpoint_label": str(getattr(checkpoint, "checkpoint_label", "") or ""),
                "predicted_pd": _safe_float(getattr(checkpoint, "predicted_pd", base_pd), base_pd),
                "pd_delta_vs_base": _safe_float(getattr(checkpoint, "pd_delta_vs_base", 0.0), 0.0),
                "gate_pass_estimate": int(_safe_int(getattr(checkpoint, "gate_pass_estimate", 0), 0)),
                "checkpoint_priority": int(_safe_int(getattr(checkpoint, "checkpoint_priority", 0), 0)),
                "status": str(getattr(checkpoint, "status", "") or ""),
                "trajectory_jump_flag": int(bool(getattr(checkpoint, "trajectory_jump_flag", False))),
                "non_monotonic_flag": int(bool(getattr(checkpoint, "non_monotonic_flag", False))),
                "checkpoint_inconsistency_flag": int(
                    bool(getattr(checkpoint, "checkpoint_inconsistency_flag", False))
                ),
            }
        )

    selection_meta = _selection_meta_dict(selection_result)
    selected_plan_id = _selected_plan_id(best)
    roadmap = {
        "customer_id": str(customer_id),
        "base_pd": float(base_pd),
        "tau": float(tau),
        "best_plan_id": selected_plan_id or None,
        "best_plan_source": str(best_source or "") or None,
        "best_status": str(best.status) if best is not None else "",
        "best_constraint_status": str(getattr(best, "constraint_status", "") or ""),
        "trajectory_status": str(getattr(best, "trajectory_status", "unknown") or "unknown"),
        "current_phase": str(getattr(best, "current_phase", "") or ""),
        "phase_transition_reason": str(getattr(best, "phase_transition_reason", "") or ""),
        "replanned_from_phase": str(getattr(best, "replanned_from_phase", "") or ""),
        "phases": phases,
        "checkpoints": checkpoints,
        "next_review_week": int(_safe_int(getattr(best, "next_review_week", 4), 4)),
    }
    checkpoint_map = {
        int(_safe_int(checkpoint.get("week", 0), 0)): checkpoint
        for checkpoint in checkpoints
        if isinstance(checkpoint, dict)
    }
    checkpoint_4w = checkpoint_map.get(4, {})
    checkpoint_12w = checkpoint_map.get(12, {})
    checkpoint_24w = checkpoint_map.get(24, {})
    approval_ready_4w = bool(_safe_int(checkpoint_4w.get("gate_pass_estimate", 0), 0))
    approval_ready_12w = bool(_safe_int(checkpoint_12w.get("gate_pass_estimate", 0), 0))
    approval_ready_24w = bool(_safe_int(checkpoint_24w.get("gate_pass_estimate", 0), 0))
    credit_readiness_stage = "not_ready_yet"
    if str(getattr(best, "status", "") or "") == "APPROVED":
        if approval_ready_4w:
            credit_readiness_stage = "week_4"
        elif approval_ready_12w:
            credit_readiness_stage = "week_12"
        elif approval_ready_24w:
            credit_readiness_stage = "week_24"
        else:
            credit_readiness_stage = "now"
    roadmap["summary"] = {
        "base_pd": float(base_pd),
        "target_pd_4w": _safe_float(checkpoint_4w.get("predicted_pd", base_pd), base_pd),
        "target_pd_12w": _safe_float(checkpoint_12w.get("predicted_pd", base_pd), base_pd),
        "target_pd_24w": _safe_float(checkpoint_24w.get("predicted_pd", base_pd), base_pd),
        "plan_execution_probability": _safe_float(getattr(best, "plan_execution_probability", 0.0), 0.0),
        "approval_dependent_plan_probability": _safe_float(getattr(best, "approval_dependent_plan_probability", 0.0), 0.0),
        "offer_acceptance_probability": _safe_float(getattr(best, "offer_acceptance_probability", 0.0), 0.0),
        "combined_plan_realization_probability": _safe_float(getattr(best, "combined_plan_realization_probability", 0.0), 0.0),
        "trajectory_status": str(getattr(best, "trajectory_status", "unknown") or "unknown"),
        "decision_status": str(getattr(best, "status", "") or "REJECTED"),
        "approval_ready_now": bool(str(getattr(best, "status", "") or "") == "APPROVED" and approval_ready_4w),
        "approval_ready_4w": approval_ready_4w,
        "approval_ready_12w": approval_ready_12w,
        "approval_ready_24w": approval_ready_24w,
        "credit_readiness_stage": credit_readiness_stage,
        "mean_group_difficulty_score": getattr(best, "mean_group_difficulty_score", None),
        "peak_group_difficulty_score": getattr(best, "peak_group_difficulty_score", None),
        "dominant_difficulty_label": str(getattr(best, "dominant_difficulty_label", "") or ""),
        "follow_through_readiness_label": str(getattr(best, "follow_through_readiness_label", "") or ""),
        "best_plan_id": selected_plan_id or None,
        "best_plan_source": str(best_source or "") or None,
        "best_constraint_status": str(getattr(best, "constraint_status", "") or ""),
        "recommendation_validity_status": str(getattr(best, "recommendation_validity_status", "") or "") or None,
        "recommendation_invalid_action_count": int(getattr(best, "recommendation_invalid_action_count", 0) or 0),
        "recommendation_warning_action_count": int(getattr(best, "recommendation_warning_action_count", 0) or 0),
        "recommendation_validity_codes": list(getattr(best, "recommendation_validity_codes", []) or []),
        "recommendation_sanity_flag": int(bool(getattr(best, "recommendation_sanity_flag", False))),
        "dice_backend_class": (
            str(getattr(best, "dice_backend_class", "") or "") if _selected_plan_source(best) == "dice" else None
        ),
        "dice_annotation_complete": int(
            bool(getattr(best, "dice_annotation_complete", False)) if _selected_plan_source(best) == "dice" else 0
        ),
        "dice_semantic_quality_status": (
            str(getattr(best, "dice_semantic_quality_status", "") or "") if _selected_plan_source(best) == "dice" else None
        ),
        "dice_semantic_quality_codes": (
            list(getattr(best, "dice_semantic_quality_codes", []) or []) if _selected_plan_source(best) == "dice" else []
        ),
        "dice_contender_eligible": int(
            bool(getattr(best, "dice_contender_eligible", False)) if _selected_plan_source(best) == "dice" else 0
        ),
        "dice_semantic_warning_penalty": (
            _safe_float(getattr(best, "dice_semantic_warning_penalty", 0.0), 0.0)
            if _selected_plan_source(best) == "dice"
            else 0.0
        ),
        "offer_plan": int(bool(getattr(best, "offer_plan", False))),
        "rankable_offer_count": int(_safe_int(getattr(best, "rankable_offer_count", 0), 0)),
        "approval_pending_action_count": int(_safe_int(getattr(best, "approval_pending_action_count", 0), 0)),
        "nominal_pd_improvement": _derive_nominal_pd_improvement(base_pd=base_pd, plan=best) if best is not None else 0.0,
        "expected_pd_improvement": (
            _safe_float(getattr(best, "expected_pd_improvement", 0.0), 0.0)
            if getattr(best, "expected_pd_improvement", None) is not None
            else (_derive_nominal_pd_improvement(base_pd=base_pd, plan=best) if best is not None else 0.0)
            * _safe_float(getattr(best, "plan_execution_probability", 0.0), 0.0)
        ),
        "local_explainability_confidence": float((local_reason_bundle or {}).get("meta", {}).get("explainability_confidence", 0.50)),
        "plan_contract_pass": int(
            bool(selected_plan_id.strip()) and str(getattr(best, "constraint_status", "valid") or "valid").strip().lower() != "invalid"
        ),
        **selection_meta,
    }
    roadmap = _normalize_customer_roadmap_contract(roadmap)
    roadmap = _inject_decision_inputs_into_roadmap(
        roadmap,
        best=best,
        base_pd=base_pd,
        local_reason_bundle=local_reason_bundle,
    )
    roadmap = _apply_decision_ownership_to_roadmap(roadmap)
    normalized_summary = dict(roadmap.get("summary", {}) or {})
    roadmap["narrative"] = build_customer_roadmap_narrative(
        base_pd=base_pd,
        tau=tau,
        phases=roadmap.get("phases", []),
        checkpoints=roadmap.get("checkpoints", []),
        status=_safe_text(normalized_summary.get("decision_status"), str(getattr(best, "status", "") or "REJECTED")),
        local_reason_bundle=local_reason_bundle or {},
        constraint_trace=list(getattr(best, "constraint_trace", [])),
        plan_execution_probability=normalized_summary.get("plan_execution_probability", None),
        approval_dependent_plan_probability=normalized_summary.get("approval_dependent_plan_probability", None),
        offer_acceptance_probability=normalized_summary.get("offer_acceptance_probability", None),
        combined_plan_realization_probability=normalized_summary.get("combined_plan_realization_probability", None),
        mean_group_difficulty_score=getattr(best, "mean_group_difficulty_score", None),
        peak_group_difficulty_score=getattr(best, "peak_group_difficulty_score", None),
        follow_through_readiness_label=getattr(best, "follow_through_readiness_label", None),
        decision_status_internal=_safe_text(normalized_summary.get("decision_status_internal"), ""),
        decision_confidence=normalized_summary.get("decision_confidence", None),
        expected_readiness=_safe_text(normalized_summary.get("expected_readiness"), ""),
        decision_reason_summary=_safe_text(normalized_summary.get("decision_reason_summary"), ""),
        decision_reason_primary=_safe_text(normalized_summary.get("decision_reason_primary"), ""),
        rejection_type=_safe_text(normalized_summary.get("rejection_type"), ""),
        conditional_type=_safe_text(normalized_summary.get("conditional_type"), ""),
        upgrade_condition=_safe_text(normalized_summary.get("upgrade_condition"), ""),
        decision_policy_version=_safe_text(normalized_summary.get("decision_policy_version"), ""),
        decision_gate_trace=dict(normalized_summary.get("decision_gate_trace", {}) or {}),
        offer_maturity=_safe_text(normalized_summary.get("offer_maturity"), ""),
        customer_context={str(k): row.get(k) for k in row.index},
    ).model_dump(mode="json")
    roadmap = _build_selected_surface_projection(roadmap)
    return roadmap


def _build_bundle_plans_df(
    *,
    validated: list[PlanRecord],
    candidate_pool: list[PlanRecord],
) -> pd.DataFrame:
    ordered_plan_ids: list[str] = []
    rows_by_plan_id: dict[str, dict[str, Any]] = {}

    def _upsert(plan: PlanRecord, *, plan_stage: str) -> None:
        plan_id = str(getattr(plan, "plan_id", "") or "")
        if not plan_id:
            return
        row = _plan_to_row(plan)
        row["plan_stage"] = plan_stage
        existing = rows_by_plan_id.get(plan_id)
        if existing is None:
            ordered_plan_ids.append(plan_id)
            rows_by_plan_id[plan_id] = row
            return
        if existing.get("plan_stage") != "validated" or plan_stage == "validated":
            rows_by_plan_id[plan_id] = row

    for plan in candidate_pool:
        _upsert(plan, plan_stage="candidate_only")
    for plan in validated:
        _upsert(plan, plan_stage="validated")

    if not ordered_plan_ids:
        return pd.DataFrame()
    return pd.DataFrame([rows_by_plan_id[plan_id] for plan_id in ordered_plan_ids])


def _plan_to_row(plan: PlanRecord) -> dict:
    annotate_plan_planner_quality(plan)
    timeline_steps: list[dict] = []
    phase_1_count = 0
    phase_2_count = 0
    phase_3_count = 0
    for action in sorted(
        list(plan.actions),
        key=lambda a: (
            _safe_int(getattr(a, "time_months", 0), 0),
            str(getattr(a, "feature_name", "")),
        ),
    ):
        m = max(1, _safe_int(getattr(action, "time_months", 1), 1))
        phase_id = _phase_id_for_month(m)
        if phase_id == "phase_1_stabilize":
            phase_1_count += 1
        elif phase_id == "phase_2_build":
            phase_2_count += 1
        else:
            phase_3_count += 1
        primary_numeric_target = getattr(action, "primary_numeric_target", None)
        offer_contract = getattr(action, "offer_contract", None)
        timeline_steps.append(
            {
                "phase_id": phase_id,
                "phase_title": _phase_title(phase_id),
                "time_months": int(m),
                "action_key": str(getattr(action, "action_key", "") or ""),
                "action_class": str(getattr(action, "action_class", "") or ""),
                "action_title": str(getattr(action, "action_title", "") or ""),
                "action_group_id": str(getattr(action, "action_group_id", "") or ""),
                "feature_name": str(getattr(action, "feature_name", "") or ""),
                "business_view": dict(getattr(action, "business_view").model_dump(mode="json")),
                "technical_view": dict(getattr(action, "technical_view").model_dump(mode="json")),
                "primary_numeric_target": (
                    primary_numeric_target.model_dump(mode="json")
                    if primary_numeric_target is not None
                    else None
                ),
                "estimated_cost_usd": _safe_float(getattr(action, "estimated_cost_usd", 0.0), 0.0),
                "requires_institutional_approval": int(
                    bool(getattr(action, "requires_institutional_approval", False))
                ),
                "institutional_approval_state": str(getattr(action, "institutional_approval_state", "") or ""),
                "approval_pending_semantic_only": int(
                    bool(getattr(action, "approval_pending_semantic_only", False))
                ),
                "offer_contract": (
                    offer_contract.model_dump(mode="json")
                    if offer_contract is not None
                    else None
                ),
                "offer_type": str(getattr(action, "offer_type", "") or ""),
                "offer_terms": dict(getattr(action, "offer_terms", {}) or {}),
                "offer_terms_complete": int(bool(getattr(action, "offer_terms_complete", False))),
                "requires_acceptance": int(bool(getattr(action, "requires_acceptance", False))),
                "offer_family": str(getattr(action, "offer_family", "") or ""),
                "offer_scoring_profile": str(getattr(action, "offer_scoring_profile", "") or ""),
                "term_generation_rule": str(getattr(action, "term_generation_rule", "") or ""),
                "offer_policy_arm": str(getattr(action, "offer_policy_arm", "") or ""),
                "plan_constraint_status": str(getattr(plan, "constraint_status", "valid") or "valid"),
                "action_status": str(getattr(action, "action_status", "") or ""),
                "action_status_reason": str(getattr(action, "action_status_reason", "") or ""),
                "constraint_family": str(getattr(action, "constraint_family", "") or ""),
                "constraint_reason_codes": list(getattr(action, "constraint_reason_codes", [])),
                "was_clipped": int(bool(getattr(action, "was_clipped", False))),
                "repair_applied": int(bool(getattr(action, "repair_applied", False))),
                "dependency_gate": int(bool(getattr(action, "dependency_gate", False))),
                "semantic_preserved": getattr(action, "semantic_preserved", None),
                "diagnostic_flags": list(getattr(action, "diagnostic_flags", [])),
                "difficulty_score": (
                    _safe_float(getattr(action, "difficulty_score", 0.0), 0.0)
                    if getattr(action, "difficulty_score", None) is not None
                    else None
                ),
                "action_execution_probability": (
                    _safe_float(getattr(action, "action_execution_probability", 0.0), 0.0)
                    if getattr(action, "action_execution_probability", None) is not None
                    else None
                ),
                "approval_dependent_probability": (
                    _safe_float(getattr(action, "approval_dependent_probability", 0.0), 0.0)
                    if getattr(action, "approval_dependent_probability", None) is not None
                    else None
                ),
                "action_group_execution_probability": (
                    _safe_float(getattr(action, "action_group_execution_probability", 0.0), 0.0)
                    if getattr(action, "action_group_execution_probability", None) is not None
                    else None
                ),
                "difficulty_label": str(getattr(action, "difficulty_label", "") or ""),
                "difficulty_drivers": dict(getattr(action, "difficulty_drivers", {}) or {}),
                "approval_friction": (
                    _safe_float(getattr(action, "approval_friction", 0.0), 0.0)
                    if getattr(action, "approval_friction", None) is not None
                    else None
                ),
                "recommendation_validity_status": str(getattr(action, "recommendation_validity_status", "") or ""),
                "recommendation_validity_codes": list(getattr(action, "recommendation_validity_codes", []) or []),
                "recommendation_sanity_flag": int(bool(getattr(action, "recommendation_sanity_flag", False))),
                "offer_required_flag": int(bool(getattr(action, "offer_required_flag", False))),
                "offer_feasibility": str(getattr(action, "offer_feasibility", "") or ""),
            }
        )
    canonical_phases = list(getattr(plan, "phases", [])) or build_canonical_phases(
        plan.actions,
        predicted_pd=getattr(plan, "predicted_pd", None),
    )
    phases_json = json.dumps(
        [phase.model_dump(mode="json") for phase in canonical_phases],
        ensure_ascii=False,
    )
    checkpoints_json = json.dumps(
        [checkpoint.model_dump(mode="json") for checkpoint in list(getattr(plan, "trajectory_checkpoints", []))],
        ensure_ascii=False,
    )
    return {
        "plan_id": plan.plan_id,
        "plan_source": str(getattr(plan, "plan_source", "") or ""),
        "path_id": str(getattr(plan, "path_id", "") or ""),
        "path_type": str(getattr(plan, "path_type", "") or ""),
        "path_signature": str(getattr(plan, "path_signature", "") or ""),
        "path_rankable_flag": int(bool(getattr(plan, "path_rankable_flag", False))),
        "path_representative_flag": int(bool(getattr(plan, "path_representative_flag", False))),
        "path_rank": (
            int(getattr(plan, "path_rank", 0) or 0)
            if getattr(plan, "path_rank", None) is not None
            else None
        ),
        "contender_bucket": str(getattr(plan, "contender_bucket", "") or ""),
        "empty_candidate_reason": str(getattr(plan, "empty_candidate_reason", "") or ""),
        "approval_shell_only_flag": int(bool(getattr(plan, "approval_shell_only_flag", False))),
        "offer_maturity": str(getattr(plan, "offer_maturity", "") or ""),
        "recommendation_validity_status": str(getattr(plan, "recommendation_validity_status", "") or ""),
        "recommendation_invalid_action_count": int(getattr(plan, "recommendation_invalid_action_count", 0) or 0),
        "recommendation_warning_action_count": int(getattr(plan, "recommendation_warning_action_count", 0) or 0),
        "recommendation_validity_codes_json": json.dumps(
            list(getattr(plan, "recommendation_validity_codes", []) or []),
            ensure_ascii=False,
        ),
        "recommendation_sanity_flag": int(bool(getattr(plan, "recommendation_sanity_flag", False))),
        "rule_annotation_complete": int(bool(getattr(plan, "rule_annotation_complete", False))),
        "rule_semantic_quality_status": str(getattr(plan, "rule_semantic_quality_status", "") or ""),
        "rule_semantic_quality_codes_json": json.dumps(
            list(getattr(plan, "rule_semantic_quality_codes", []) or []),
            ensure_ascii=False,
        ),
        "rule_contender_eligible": int(bool(getattr(plan, "rule_contender_eligible", False))),
        "rule_semantic_warning_penalty": _safe_float(getattr(plan, "rule_semantic_warning_penalty", 0.0), 0.0),
        "rule_quality_gate_version": str(getattr(plan, "rule_quality_gate_version", "") or ""),
        "dice_backend_class": str(getattr(plan, "dice_backend_class", "") or ""),
        "dice_annotation_complete": int(bool(getattr(plan, "dice_annotation_complete", False))),
        "dice_semantic_quality_status": str(getattr(plan, "dice_semantic_quality_status", "") or ""),
        "dice_semantic_quality_codes_json": json.dumps(
            list(getattr(plan, "dice_semantic_quality_codes", []) or []),
            ensure_ascii=False,
        ),
        "dice_contender_eligible": int(bool(getattr(plan, "dice_contender_eligible", False))),
        "dice_semantic_warning_penalty": _safe_float(getattr(plan, "dice_semantic_warning_penalty", 0.0), 0.0),
        "dice_quality_gate_version": str(getattr(plan, "dice_quality_gate_version", "") or ""),
        "horizon": plan.horizon_months,
        "strategy": plan.strategy,
        "predicted_pd": plan.predicted_pd,
        "reliability": plan.reliability,
        "ci_low": plan.ci_low,
        "ci_high": plan.ci_high,
        "risk_margin": plan.risk_margin,
        "robust_score": plan.robust_score,
        "robust_margin": plan.robust_margin,
        "robust_anchor_pd": plan.robust_anchor_pd,
        "robust_method": plan.robust_method,
        "robust_worst_risk_margin": plan.robust_worst_risk_margin,
        "causal_penalty": plan.causal_penalty,
        "score": plan.score,
        "cost": _plan_cost(plan),
        "action_count": len(plan.actions),
        "phase_1_action_count": int(phase_1_count),
        "phase_2_action_count": int(phase_2_count),
        "phase_3_action_count": int(phase_3_count),
        "proximity_l1": _plan_proximity_l1(plan),
        "timeline_steps_json": json.dumps(timeline_steps, ensure_ascii=False),
        "phases_json": phases_json,
        "trajectory_checkpoints_json": checkpoints_json,
        "constraint_status": str(getattr(plan, "constraint_status", "valid") or "valid"),
        "constraint_reason": str(getattr(plan, "constraint_reason", "") or ""),
        "constraint_trace_json": json.dumps(getattr(plan, "constraint_trace", []), ensure_ascii=False),
        "plan_execution_probability": (
            _safe_float(getattr(plan, "plan_execution_probability", 0.0), 0.0)
            if getattr(plan, "plan_execution_probability", None) is not None
            else None
        ),
        "approval_dependent_plan_probability": (
            _safe_float(getattr(plan, "approval_dependent_plan_probability", 0.0), 0.0)
            if getattr(plan, "approval_dependent_plan_probability", None) is not None
            else None
        ),
        "mean_action_execution_probability": (
            _safe_float(getattr(plan, "mean_action_execution_probability", 0.0), 0.0)
            if getattr(plan, "mean_action_execution_probability", None) is not None
            else None
        ),
        "mean_approval_dependent_probability": (
            _safe_float(getattr(plan, "mean_approval_dependent_probability", 0.0), 0.0)
            if getattr(plan, "mean_approval_dependent_probability", None) is not None
            else None
        ),
        "mean_group_difficulty_score": (
            _safe_float(getattr(plan, "mean_group_difficulty_score", 0.0), 0.0)
            if getattr(plan, "mean_group_difficulty_score", None) is not None
            else None
        ),
        "peak_group_difficulty_score": (
            _safe_float(getattr(plan, "peak_group_difficulty_score", 0.0), 0.0)
            if getattr(plan, "peak_group_difficulty_score", None) is not None
            else None
        ),
        "dominant_difficulty_label": str(getattr(plan, "dominant_difficulty_label", "") or ""),
        "follow_through_readiness_label": str(getattr(plan, "follow_through_readiness_label", "") or ""),
        "nominal_pd_improvement": _safe_float(getattr(plan, "nominal_pd_improvement", 0.0), 0.0),
        "expected_pd_improvement": _safe_float(getattr(plan, "expected_pd_improvement", 0.0), 0.0),
        "executable_action_count": int(getattr(plan, "executable_action_count", 0) or 0),
        "executable_action_group_count": int(getattr(plan, "executable_action_group_count", 0) or 0),
        "approval_pending_action_count": int(getattr(plan, "approval_pending_action_count", 0) or 0),
        "offer_plan": int(bool(getattr(plan, "offer_plan", False))),
        "rankable_offer_count": int(getattr(plan, "rankable_offer_count", 0) or 0),
        "offer_acceptance_probability": (
            _safe_float(getattr(plan, "offer_acceptance_probability", 0.0), 0.0)
            if getattr(plan, "offer_acceptance_probability", None) is not None
            else None
        ),
        "combined_plan_realization_probability": (
            _safe_float(getattr(plan, "combined_plan_realization_probability", 0.0), 0.0)
            if getattr(plan, "combined_plan_realization_probability", None) is not None
            else None
        ),
        "expected_recovery_proxy": _safe_float(getattr(plan, "expected_recovery_proxy", 0.0), 0.0),
        "approval_rate_proxy_delta": _safe_float(getattr(plan, "approval_rate_proxy_delta", 0.0), 0.0),
        "default_rate_90d_proxy_delta": _safe_float(getattr(plan, "default_rate_90d_proxy_delta", 0.0), 0.0),
        "avg_margin_90d_proxy_delta": _safe_float(getattr(plan, "avg_margin_90d_proxy_delta", 0.0), 0.0),
        "governance_safe_offer": int(bool(getattr(plan, "governance_safe_offer", False))),
        "dominant_offer_type": str(getattr(plan, "dominant_offer_type", "") or ""),
        "offer_policy_arm": str(getattr(plan, "offer_policy_arm", "") or ""),
        "offer_family": str(getattr(plan, "offer_family", "") or ""),
        "offer_scoring_profile": str(getattr(plan, "offer_scoring_profile", "") or ""),
        "term_generation_rule": str(getattr(plan, "term_generation_rule", "") or ""),
        "trajectory_status": str(getattr(plan, "trajectory_status", "on_track") or "on_track"),
        "current_phase": str(getattr(plan, "current_phase", "") or ""),
        "next_review_week": int(_safe_int(getattr(plan, "next_review_week", 4), 4)),
        "phase_transition_reason": str(getattr(plan, "phase_transition_reason", "") or ""),
        "replanned_from_phase": str(getattr(plan, "replanned_from_phase", "") or ""),
        "trajectory_policy_label": str(getattr(plan, "trajectory_policy_label", "") or ""),
        "trajectory_policy_score": (
            _safe_float(getattr(plan, "trajectory_policy_score", 0.0), 0.0)
            if getattr(plan, "trajectory_policy_score", None) is not None
            else None
        ),
        "status": plan.status,
        "status_reason": plan.status_reason,
    }


def _dice_plan_record(
    idx: int,
    customer_id: str,
    run_id: str,
    row: pd.Series,
    feature_cols: list[str],
    actions: list[dict],
    model,
    calibrator,
    tau: float,
    graph: dict | None,
    causal_weight: float = 0.3,
    feasibility_profile: dict | None = None,
    segment_context: dict | None = None,
    source_tag: str = "dice",
) -> PlanRecord:
    customer_context = {str(k): row.get(k) for k in row.index}
    plan_actions: list[PlanAction] = []

    for a in actions:
        feature = str(a["feature_name"])
        spec = get_action_spec(feature)
        action_month = max(1, int(spec.time_months))
        current = float(a["current_value"])
        action_meta = get_action_metadata(
            feature,
            action_month=action_month,
            action_phase=phase_id_for_month(action_month),
            allow_mapped_feature=True,
        )
        requested_target = normalize_dice_target_value(
            feature,
            current_value=current,
            target_value=float(a["target_value"]),
        )
        detail = apply_target_feasibility_with_details(
            feature_name=feature,
            current_value=current,
            target_value=requested_target,
            horizon_months=6,
            profile=feasibility_profile,
            segment_context=segment_context,
            action_class=action_meta.get("action_class"),
            action_context=customer_context,
        )
        target = float(detail["target_value"])
        if str(detail["status"]) == "invalid":
            continue
        plan_actions.append(
            build_canonical_plan_action(
                feature_name=feature,
                current_value=current,
                target_value=target,
                requested_target_value=requested_target,
                action_month=action_month,
                action_context=customer_context,
                action_status=str(detail["status"]),
                action_status_reason=detail.get("status_reason"),
                constraint_family=detail.get("constraint_family"),
                constraint_reason_codes=list(detail.get("reason_codes", [])),
                was_clipped=bool(detail.get("was_clipped", False)),
                semantic_preserved=detail.get("semantic_preserved"),
                diagnostic_flags=list(detail.get("reason_codes", [])),
                allow_mapped_feature=True,
            )
        )

    constraint_result = enforce_action_constraints(
        plan_actions,
        action_context=customer_context,
    )
    plan_actions = [
        annotate_action_recommendation_validity(action, customer_context=customer_context)
        for action in list(constraint_result.actions)
    ]
    x_prime = row.copy()
    for action in plan_actions:
        x_prime[str(action.feature_name)] = float(action.target_value)

    x_input = pd.DataFrame([x_prime[feature_cols].values], columns=feature_cols)
    pred_pd = float(predict_proba_pd(model, calibrator, x_input)[0])
    cost = float(sum(a.estimated_cost_usd for a in plan_actions))
    cpen = float(causal_penalty(actions, graph, penalty_weight=causal_weight)) if graph else 0.0
    score = float((max(0.0, tau - pred_pd) * 100.0) - (cost * 0.001) - cpen)

    base_input = pd.DataFrame([row[feature_cols].values], columns=feature_cols)
    base_pd = float(predict_proba_pd(model, calibrator, base_input)[0])
    plan = PlanRecord(
        plan_id=f"{run_id}_{customer_id}_{source_tag}_{idx}",
        customer_id=customer_id,
        run_id=run_id,
        horizon_months=6,
        strategy="balanced",
        actions=plan_actions,
        plan_source=str(source_tag),
        predicted_pd=pred_pd,
        causal_penalty=cpen,
        score=score,
        constraint_status=constraint_result.status,
        constraint_reason=constraint_result.reason,
        constraint_trace=list(constraint_result.trace),
        status="PENDING",
    )
    annotate_plan_execution_probability(
        plan,
        base_pd=base_pd,
        customer_context=customer_context,
        segment_context=segment_context,
    )
    attach_canonical_trajectory(
        plan,
        row=row,
        base_pd=base_pd,
        tau=tau,
        model=model,
        calibrator=calibrator,
        feature_cols=feature_cols,
    )
    annotate_offer_optimization(
        plan,
        customer_context=customer_context,
        segment_context=segment_context,
    )
    return annotate_plan_recommendation_validity(plan, customer_context=customer_context)


def _candidate_rank_tuple(plan: PlanRecord) -> tuple:
    return (
        plan.status != "APPROVED",
        -(float(plan.robust_score) if plan.robust_score is not None else float(plan.score or -1e9)),
        int(len(plan.actions)),
        float(sum(float(a.estimated_cost_usd) for a in plan.actions)),
        float(plan.predicted_pd or 1.0),
    )


def _prune_candidate_pool(plans: list[PlanRecord], max_size: int) -> list[PlanRecord]:
    if max_size <= 0 or len(plans) <= max_size:
        return plans
    return sorted(plans, key=_candidate_rank_tuple)[:max_size]


def main(argv: Sequence[str] | None = None):
    args = parse_args(argv)
    base_cfg = load_config(args.base_config)
    model_cfg = load_config(args.model_config)
    rec_cfg = load_config(args.recourse_config)
    c_cfg = load_config(args.causality_config)
    s_cfg = load_config(args.safety_config)
    m_cfg = load_config(args.macro_config)
    cfg = _merge_dict(
        _merge_dict(_merge_dict(_merge_dict(base_cfg, model_cfg), rec_cfg), _merge_dict(c_cfg, s_cfg)),
        {"macro": m_cfg},
    )
    run_ctx = create_run_context(cfg, base_artifact_dir="artifacts/runs")

    contract = load_feature_contract(base_cfg.get("features_config", "configs/features_48.yaml"))
    feature_cols = contract["features"]
    target_col = contract["target"]

    processed_root = Path(base_cfg.get("paths", {}).get("processed_data", "data/processed"))
    test_path = processed_root / "test.parquet"
    train_path = processed_root / "train.parquet"
    if not test_path.exists() or not train_path.exists():
        raise FileNotFoundError("Processed data missing. Run run_prepare_data first.")

    test_df = pd.read_parquet(test_path)
    train_df = pd.read_parquet(train_path)
    row_idx = max(0, min(args.row_index, len(test_df) - 1))
    row = test_df.iloc[row_idx]

    model, calibrator, manifest, _ = load_model_bundle(
        base_path=model_cfg.get("registry", {}).get("path", "artifacts/models"),
        model_version=str(args.model_version).strip() or None,
        manifest_path=str(args.model_manifest).strip() or None,
    )

    graph_out = Path(c_cfg.get("graph", {}).get("output_path", "artifacts/models/causal_graph.json"))
    if graph_out.exists():
        graph = load_graph(graph_out)
    else:
        graph = run_rex_adapter(
            train_df,
            feature_cols=feature_cols,
            min_edge_weight=float(c_cfg.get("graph", {}).get("min_edge_weight", 0.1)),
            algorithm=c_cfg.get("algorithm", "pc"),
            output_path=graph_out,
        )

    if args.explain_only:
        local_reason_bundle = compute_local_reason_bundle(
            model,
            row[feature_cols],
            top_k=int(rec_cfg.get("shap", {}).get("topk_features", 10)),
            perturbations=int(rec_cfg.get("shap", {}).get("stability_perturbations", 6)),
            noise_std=float(rec_cfg.get("shap", {}).get("stability_noise_std", 0.01)),
            random_state=int(rec_cfg.get("shap", {}).get("stability_seed", 42)),
            background_df=train_df[feature_cols].sample(
                n=min(len(train_df), int(rec_cfg.get("shap", {}).get("background_samples", 256))),
                random_state=int(rec_cfg.get("shap", {}).get("stability_seed", 42)),
            ),
        )
        reasons_path = run_ctx.tables_dir / "local_reasons.json"
        reasons_path.write_text(json.dumps(local_reason_bundle, indent=2, ensure_ascii=False), encoding="utf-8")
        adverse_action_reasons = build_adverse_action_reasons(local_reason_bundle.get("reasons", []), max_items=4)
        adverse_out = run_ctx.tables_dir / "adverse_action_reasons.json"
        adverse_out.write_text(json.dumps({"reasons": adverse_action_reasons}, indent=2, ensure_ascii=False), encoding="utf-8")
        conf = local_reason_bundle.get("meta", {}).get("explainability_confidence")
        logger.info("Explain-only mode complete. Reasons saved: %s confidence=%s", reasons_path, conf)
        return run_ctx

    result = generate_customer_recourse_artifacts(
        customer_id=args.customer_id,
        run_id=run_ctx.run_id,
        row=row,
        test_df=test_df,
        train_df=train_df,
        model=model,
        calibrator=calibrator,
        manifest=manifest,
        feature_cols=feature_cols,
        target_col=target_col,
        model_cfg=model_cfg,
        rec_cfg=rec_cfg,
        c_cfg=c_cfg,
        s_cfg=s_cfg,
        m_cfg=m_cfg,
        graph=graph,
        persist_repository_records=True,
    )

    reasons_path = run_ctx.tables_dir / "local_reasons.json"
    reasons_path.write_text(json.dumps(result.local_reason_bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    adverse_out = run_ctx.tables_dir / "adverse_action_reasons.json"
    adverse_out.write_text(
        json.dumps({"reasons": result.adverse_action_reasons}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    plans_df = result.bundle.plans_df
    plans_csv = run_ctx.tables_dir / "plans.csv"
    plans_json = run_ctx.tables_dir / "plans.json"
    plans_df.to_csv(plans_csv, index=False)
    plans_json.write_text(plans_df.to_json(orient="records", indent=2), encoding="utf-8")

    dice_df = result.dice_df
    dice_csv = run_ctx.tables_dir / "dice_plans.csv"
    dice_json = run_ctx.tables_dir / "dice_plans.json"
    dice_df.to_csv(dice_csv, index=False)
    dice_json.write_text(dice_df.to_json(orient="records", indent=2), encoding="utf-8")
    dice_tel_json = run_ctx.tables_dir / "dice_telemetry.json"
    dice_tel_json.write_text(json.dumps(result.dice_telemetry, indent=2, ensure_ascii=False), encoding="utf-8")

    pool_df = result.candidate_pool_df
    pool_csv = run_ctx.tables_dir / "candidate_pool.csv"
    pool_json = run_ctx.tables_dir / "candidate_pool.json"
    pool_df.to_csv(pool_csv, index=False)
    pool_json.write_text(pool_df.to_json(orient="records", indent=2), encoding="utf-8")

    roadmap_json = run_ctx.tables_dir / "customer_roadmap.json"
    roadmap_json.write_text(json.dumps(result.bundle.roadmap, indent=2, ensure_ascii=False), encoding="utf-8")
    paths_json = run_ctx.tables_dir / "customer_paths.json"
    paths_json.write_text(result.bundle.paths_df.to_json(orient="records", indent=2), encoding="utf-8")
    roadmap_steps_csv = run_ctx.tables_dir / "customer_roadmap_steps.csv"
    result.bundle.roadmap_steps_df.to_csv(roadmap_steps_csv, index=False)

    decision_log_out = run_ctx.tables_dir / "decision_log_record.json"
    decision_log_summary_out = run_ctx.tables_dir / "decision_logging_summary.json"
    decision_log_out.write_text(json.dumps(result.decision_log_record, indent=2, ensure_ascii=False), encoding="utf-8")
    decision_log_summary_out.write_text(
        json.dumps(result.decision_log_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    summary = result.bundle.metrics_summary
    run_ctx.save_metrics(summary)

    logger.info(
        "Recourse run complete. plans=%s approved=%s denied_target=%s best_source=%s",
        summary["plan_count"],
        summary["approved_count"],
        summary["denied_target_mode"],
        summary["best_plan_source"],
    )
    logger.info("Plan outputs: %s %s", plans_csv, plans_json)
    logger.info("DiCE outputs: %s %s %s backend=%s", dice_csv, dice_json, dice_tel_json, result.dice_backend)
    logger.info("Candidate pool outputs: %s %s", pool_csv, pool_json)
    logger.info("Roadmap outputs: %s %s %s", roadmap_json, paths_json, roadmap_steps_csv)
    logger.info("Decision logging outputs: %s %s", decision_log_out, decision_log_summary_out)
    logger.info("Adverse action reasons: %s", adverse_out)
    return run_ctx

    args = parse_args()
    base_cfg = load_config(args.base_config)
    model_cfg = load_config(args.model_config)
    rec_cfg = load_config(args.recourse_config)
    c_cfg = load_config(args.causality_config)
    s_cfg = load_config(args.safety_config)
    m_cfg = load_config(args.macro_config)
    cfg = _merge_dict(
        _merge_dict(_merge_dict(_merge_dict(base_cfg, model_cfg), rec_cfg), _merge_dict(c_cfg, s_cfg)),
        {"macro": m_cfg},
    )

    run_ctx = create_run_context(cfg, base_artifact_dir="artifacts/runs")

    contract = load_feature_contract(base_cfg.get("features_config", "configs/features_48.yaml"))
    feature_cols = contract["features"]
    target_col = contract["target"]

    processed_root = Path(base_cfg.get("paths", {}).get("processed_data", "data/processed"))
    test_path = processed_root / "test.parquet"
    train_path = processed_root / "train.parquet"
    if not test_path.exists() or not train_path.exists():
        raise FileNotFoundError("Processed data missing. Run run_prepare_data first.")

    test_df = pd.read_parquet(test_path)
    train_df = pd.read_parquet(train_path)

    row_idx = max(0, min(args.row_index, len(test_df) - 1))
    row = test_df.iloc[row_idx]

    model, calibrator, manifest, _ = load_model_bundle(
        base_path=model_cfg.get("registry", {}).get("path", "artifacts/models"),
        model_version=str(args.model_version).strip() or None,
        manifest_path=str(args.model_manifest).strip() or None,
    )

    local_reason_bundle = compute_local_reason_bundle(
        model,
        row[feature_cols],
        top_k=int(rec_cfg.get("shap", {}).get("topk_features", 10)),
        perturbations=int(rec_cfg.get("shap", {}).get("stability_perturbations", 6)),
        noise_std=float(rec_cfg.get("shap", {}).get("stability_noise_std", 0.01)),
        random_state=int(rec_cfg.get("shap", {}).get("stability_seed", 42)),
        background_df=train_df[feature_cols].sample(
            n=min(len(train_df), int(rec_cfg.get("shap", {}).get("background_samples", 256))),
            random_state=int(rec_cfg.get("shap", {}).get("stability_seed", 42)),
        ),
    )
    reasons_path = run_ctx.tables_dir / "local_reasons.json"
    reasons_path.write_text(json.dumps(local_reason_bundle, indent=2, ensure_ascii=False), encoding="utf-8")
    adverse_action_reasons = build_adverse_action_reasons(local_reason_bundle.get("reasons", []), max_items=4)
    adverse_out = run_ctx.tables_dir / "adverse_action_reasons.json"
    adverse_out.write_text(json.dumps({"reasons": adverse_action_reasons}, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.explain_only:
        conf = local_reason_bundle.get("meta", {}).get("explainability_confidence")
        logger.info("Explain-only mode complete. Reasons saved: %s confidence=%s", reasons_path, conf)
        return

    graph_out = Path(c_cfg.get("graph", {}).get("output_path", "artifacts/models/causal_graph.json"))
    if graph_out.exists():
        graph = load_graph(graph_out)
    else:
        graph = run_rex_adapter(
            train_df,
            feature_cols=feature_cols,
            min_edge_weight=float(c_cfg.get("graph", {}).get("min_edge_weight", 0.1)),
            algorithm=c_cfg.get("algorithm", "pc"),
            output_path=graph_out,
        )

    tau = float(model_cfg.get("decision", {}).get("tau_0", 0.35))
    horizons = [int(v) for v in rec_cfg.get("horizons", [3, 6, 12])]
    strategies = [str(v) for v in rec_cfg.get("strategies", ["conservative", "balanced", "aggressive"])]
    robust_cfg_base = rec_cfg.get("robust", {}) if isinstance(rec_cfg.get("robust", {}), dict) else {}
    dice_cfg_base = rec_cfg.get("dice", {}) if isinstance(rec_cfg.get("dice", {}), dict) else {}
    scenarios = m_cfg.get("shock_scenarios", []) if isinstance(m_cfg.get("shock_scenarios", []), list) else []
    threshold_shift = float(m_cfg.get("event_impact", {}).get("threshold_shift_per_msi_unit", 0.0))
    uncertainty_cfg = s_cfg.get("uncertainty", {}) if isinstance(s_cfg.get("uncertainty", {}), dict) else {}
    conformal_artifact_path = manifest.get("conformal_calibration_path")
    if conformal_artifact_path:
        uncertainty_cfg = dict(uncertainty_cfg)
        conformal_cfg = uncertainty_cfg.get("conformal", {}) if isinstance(uncertainty_cfg.get("conformal", {}), dict) else {}
        conformal_cfg = dict(conformal_cfg)
        if not str(conformal_cfg.get("calibration_artifact_path", "")).strip():
            conformal_cfg["calibration_artifact_path"] = str(conformal_artifact_path)
        uncertainty_cfg["conformal"] = conformal_cfg

        robust_cfg_base = dict(robust_cfg_base)
        gate_obj = robust_cfg_base.get("gate_objective", {}) if isinstance(robust_cfg_base.get("gate_objective", {}), dict) else {}
        gate_obj = dict(gate_obj)
        unc_cfg = gate_obj.get("uncertainty", {}) if isinstance(gate_obj.get("uncertainty", {}), dict) else {}
        unc_cfg = dict(unc_cfg)
        if not str(unc_cfg.get("calibration_artifact_path", "")).strip():
            unc_cfg["calibration_artifact_path"] = str(conformal_artifact_path)
        gate_obj["uncertainty"] = unc_cfg
        robust_cfg_base["gate_objective"] = gate_obj

    actionable = set(get_dice_generatable_features(feature_cols))
    local_reasons = local_reason_bundle.get("reasons", [])
    candidate_features = [r for r in local_reasons if str(r.get("feature", "")) in actionable]

    base_pd = float(predict_proba_pd(model, calibrator, pd.DataFrame([row[feature_cols].values], columns=feature_cols))[0])
    topk_default = int(rec_cfg.get("shap", {}).get("topk_features", 10))
    segment_caps_cfg = rec_cfg.get("segment_caps", {}) if isinstance(rec_cfg.get("segment_caps", {}), dict) else {}
    q_cfg = segment_caps_cfg.get("income_quantiles", [0.25, 0.50, 0.75])
    q_list = list(q_cfg) if isinstance(q_cfg, list) else [0.25, 0.50, 0.75]
    income_edges = _compute_income_edges(test_df.get("annual_inc", pd.Series(dtype=float)), q_list)
    feasibility_cfg = rec_cfg.get("feasibility", {}) if isinstance(rec_cfg.get("feasibility", {}), dict) else {}
    feasibility_profile: dict | None = None
    if bool(feasibility_cfg.get("enabled", False)):
        profile_path = str(feasibility_cfg.get("profile_path", "")).strip()
        if profile_path:
            feasibility_profile = load_config(profile_path)
    feasibility_internal_profile = feasibility_profile if bool(feasibility_cfg.get("enforce_on_internal", True)) else None
    feasibility_dice_profile = feasibility_profile if bool(feasibility_cfg.get("enforce_on_dice", True)) else None
    search_profile, robust_cfg, dice_cfg = _effective_recourse_search(
        base_pd=base_pd,
        tau=tau,
        topk=topk_default,
        horizons=horizons,
        strategies=strategies,
        robust_cfg=robust_cfg_base,
        dice_cfg=dice_cfg_base,
        rec_cfg=rec_cfg,
    )
    segment_context = _build_segment_context(
        row=row,
        base_pd=base_pd,
        tau=tau,
        denied_mode=bool(search_profile.get("is_denied_target", False)),
        segment_caps_cfg=segment_caps_cfg,
        income_edges=income_edges,
    )
    search_cfg_patch = search_profile.get("search_cfg", {}) if isinstance(search_profile.get("search_cfg", {}), dict) else {}
    search_cfg_patch = dict(search_cfg_patch)
    search_cfg_patch["segment_context"] = segment_context
    search_profile["search_cfg"] = search_cfg_patch
    robust_objective = str(robust_cfg.get("objective", "cvar"))
    robust_cvar_quantile = float(robust_cfg.get("cvar_quantile", 0.9))
    min_reliability = robust_cfg.get("min_reliability")
    min_worst_margin = robust_cfg.get("min_worst_risk_margin")
    min_reliability_f = float(min_reliability) if min_reliability is not None else None
    min_worst_margin_f = float(min_worst_margin) if min_worst_margin is not None else None

    fairness_cfg = rec_cfg.get("fairness", {}) if isinstance(rec_cfg.get("fairness", {}), dict) else {}
    fairness_group_col = str(fairness_cfg.get("group_feature", "home_ownership"))
    fairness_penalty = 0.0
    if fairness_group_col in test_df.columns and fairness_group_col in row.index:
        sample_n = min(len(test_df), int(fairness_cfg.get("penalty_sample_n", 3000)))
        fairness_sample = test_df.sample(n=sample_n, random_state=int(fairness_cfg.get("penalty_seed", 42)))
        fairness_proba = pd.Series(
            predict_proba_pd(model, calibrator, fairness_sample[feature_cols]),
            index=fairness_sample.index,
            dtype=float,
        )
        fairness_scored = pd.DataFrame(
            {
                fairness_group_col: fairness_sample[fairness_group_col].astype(str).fillna("unknown"),
                "approve": (fairness_proba <= tau).astype(int),
            }
        )
        group_penalties = build_group_advantage_penalties(
            fairness_scored,
            group_col=fairness_group_col,
            approval_col="approve",
            tolerance=float(fairness_cfg.get("advantage_tolerance", 0.01)),
        )
        fairness_penalty = lookup_group_penalty(row[fairness_group_col], group_penalties)

    recourse_start_ts = time.perf_counter()
    plans = generate_nine_plans(
        customer_id=args.customer_id,
        run_id=run_ctx.run_id,
        row=row,
        model=model,
        calibrator=calibrator,
        feature_cols=feature_cols,
        graph=graph,
        tau=tau,
        horizons=search_profile["horizons"],
        strategies=search_profile["strategies"],
        candidate_features=candidate_features,
        topk=int(search_profile["topk"]),
        scenarios=scenarios,
        threshold_shift_per_msi_unit=threshold_shift,
        robust_cfg=robust_cfg,
        search_cfg=search_profile.get("search_cfg", {}),
        fairness_penalty=fairness_penalty,
        feasibility_profile=feasibility_internal_profile,
        segment_context=segment_context,
    )

    macro_snapshot = load_macro_snapshot_mock()
    msi = compute_macro_stress_index(macro_snapshot, m_cfg.get("stress_index_weights", {}))
    base_alpha = float(s_cfg.get("confidence", {}).get("base_alpha", 0.05))
    high_stress_alpha = float(s_cfg.get("confidence", {}).get("high_stress_alpha", 0.01))
    stress_threshold = float(m_cfg.get("stress_threshold", 0.7))
    alpha = dynamic_alpha(msi, base_alpha=base_alpha, high_stress_alpha=high_stress_alpha, threshold=stress_threshold)

    b = int(s_cfg.get("bootstrap", {}).get("B", 500))
    validated = [
        validate_plan(
            plan,
            tau=tau,
            alpha=alpha,
            bootstrap_b=b,
            scenarios=scenarios,
            threshold_shift_per_msi_unit=threshold_shift,
            robust_objective=robust_objective,
            robust_cvar_quantile=robust_cvar_quantile,
            min_reliability=min_reliability_f,
            min_worst_risk_margin=min_worst_margin_f,
            uncertainty_cfg=uncertainty_cfg,
            segment_context=segment_context,
        )
        for plan in plans
    ]

    for p in validated:
        save_plan(p)

    plans_df = pd.DataFrame([_plan_to_row(p) for p in validated])
    plans_csv = run_ctx.tables_dir / "plans.csv"
    plans_json = run_ctx.tables_dir / "plans.json"
    plans_df.to_csv(plans_csv, index=False)
    plans_json.write_text(plans_df.to_json(orient="records", indent=2), encoding="utf-8")

    search_cfg = search_profile.get("search_cfg", {}) if isinstance(search_profile.get("search_cfg", {}), dict) else {}
    internal_approved_count = int(sum(1 for p in validated if p.status == "APPROVED"))
    deny_mode = bool(search_profile.get("is_denied_target", False))
    time_budget_ms = int(search_cfg.get("time_budget_ms", 0))
    skip_dice_when_internal_approved = bool(search_cfg.get("skip_dice_when_internal_approved", False))
    skip_dice_for_non_denied = bool(search_cfg.get("skip_dice_for_non_denied", False))
    elapsed_so_far_ms = float((time.perf_counter() - recourse_start_ts) * 1000.0)
    remaining_budget_ms = int(max(0.0, float(time_budget_ms) - elapsed_so_far_ms)) if time_budget_ms > 0 else 0

    skip_dice_reason = ""
    if skip_dice_when_internal_approved and internal_approved_count > 0:
        skip_dice_reason = "internal_already_approved"
    if not skip_dice_reason and skip_dice_for_non_denied and not deny_mode:
        skip_dice_reason = "non_denied_profile"
    if not skip_dice_reason and time_budget_ms > 0 and elapsed_so_far_ms >= float(time_budget_ms):
        skip_dice_reason = "time_budget_exceeded"

    dice_records: list[PlanRecord] = []
    dice_backend = "skipped"
    dice_telemetry = {
        "method_requested": str(dice_cfg.get("method", "random")),
        "method_used": "skipped",
        "fallback_reason": skip_dice_reason or "skipped_by_policy",
        "attempted_method_count": 0,
    }
    if not skip_dice_reason:
        configured_timeout_ms = int(dice_cfg.get("timeout_ms", 0))
        dice_timeout_ms = configured_timeout_ms
        if dice_timeout_ms > 0 and remaining_budget_ms > 0:
            dice_timeout_ms = min(dice_timeout_ms, remaining_budget_ms)
        dice_action_sets, dice_backend, dice_telemetry = generate_dice_counterfactual_actions(
            row=row,
            feature_cols=feature_cols,
            actionable_features=sorted(actionable),
            model=model,
            calibrator=calibrator,
            train_df=train_df,
            target_col=target_col,
            total_cfs=int(dice_cfg.get("total_cfs", 3)),
            random_seed=int(dice_cfg.get("seed", 42)),
            dice_method=str(dice_cfg.get("method", "random")),
            max_actions=int(dice_cfg.get("max_actions", 4)),
            enable_method_fallback=bool(dice_cfg.get("enable_method_fallback", True)),
            timeout_ms=int(max(0, dice_timeout_ms)),
            stopping_threshold=float(tau),
        )
        for idx, actions in enumerate(dice_action_sets, start=1):
            p = _dice_plan_record(
                idx=idx,
                customer_id=args.customer_id,
                run_id=run_ctx.run_id,
                row=row,
                feature_cols=feature_cols,
                actions=actions,
                model=model,
                calibrator=calibrator,
                tau=tau,
                graph=graph,
                causal_weight=float(c_cfg.get("penalty_weight", 0.3)),
                feasibility_profile=feasibility_dice_profile,
                segment_context=segment_context,
            )
            p = validate_plan(
                p,
                tau=tau,
                alpha=alpha,
                bootstrap_b=b,
                scenarios=scenarios,
                threshold_shift_per_msi_unit=threshold_shift,
                robust_objective=robust_objective,
                robust_cvar_quantile=robust_cvar_quantile,
                min_reliability=min_reliability_f,
                min_worst_risk_margin=min_worst_margin_f,
                uncertainty_cfg=uncertainty_cfg,
                segment_context=segment_context,
            )
            p = annotate_dice_candidate_quality(
                p,
                backend_class=classify_dice_backend_class(dice_backend),
            )
            dice_records.append(p)
            save_plan(p)

    dice_df = pd.DataFrame([_plan_to_row(annotate_plan_planner_quality(p)) for p in dice_records])
    dice_csv = run_ctx.tables_dir / "dice_plans.csv"
    dice_json = run_ctx.tables_dir / "dice_plans.json"
    dice_df.to_csv(dice_csv, index=False)
    dice_json.write_text(dice_df.to_json(orient="records", indent=2), encoding="utf-8")
    dice_tel_json = run_ctx.tables_dir / "dice_telemetry.json"
    dice_tel_json.write_text(json.dumps(dice_telemetry, indent=2, ensure_ascii=False), encoding="utf-8")

    rule_cfg = rec_cfg.get("rule_generator", {}) if isinstance(rec_cfg.get("rule_generator", {}), dict) else {}
    rule_action_sets = (
        generate_institution_rule_action_sets(
            row=row,
            feature_cols=feature_cols,
            max_candidates=int(rule_cfg.get("max_actions", 4)),
        )
        if bool(rule_cfg.get("enabled", True))
        else []
    )
    rule_records: list[PlanRecord] = []
    for ridx, actions in enumerate(rule_action_sets, start=1):
        rp = _dice_plan_record(
            idx=ridx,
            customer_id=args.customer_id,
            run_id=run_ctx.run_id,
            row=row,
            feature_cols=feature_cols,
            actions=actions,
            model=model,
            calibrator=calibrator,
            tau=tau,
            graph=graph,
            causal_weight=float(c_cfg.get("penalty_weight", 0.3)),
            feasibility_profile=feasibility_dice_profile,
            segment_context=segment_context,
            source_tag="rule",
        )
        rp = validate_plan(
            rp,
            tau=tau,
            alpha=alpha,
            bootstrap_b=b,
            scenarios=scenarios,
            threshold_shift_per_msi_unit=threshold_shift,
            robust_objective=robust_objective,
            robust_cvar_quantile=robust_cvar_quantile,
            min_reliability=min_reliability_f,
            min_worst_risk_margin=min_worst_margin_f,
            uncertainty_cfg=uncertainty_cfg,
            segment_context=segment_context,
        )
        rp = annotate_rule_candidate_quality(rp)
        rule_records.append(rp)
        save_plan(rp)

    rule_df = pd.DataFrame([_plan_to_row(annotate_plan_planner_quality(plan)) for plan in rule_records])
    rule_csv = run_ctx.tables_dir / "rule_plans.csv"
    rule_json = run_ctx.tables_dir / "rule_plans.json"
    rule_df.to_csv(rule_csv, index=False)
    rule_json.write_text(rule_df.to_json(orient="records", indent=2), encoding="utf-8")

    candidate_pool = validated + dice_records + rule_records
    planner_candidate_pool, _ineligible_dice_candidates = split_dice_planner_eligible(candidate_pool)
    planner_candidate_pool, _ineligible_rule_candidates = split_rule_planner_eligible(planner_candidate_pool)
    candidate_pool_max_size = int(search_cfg.get("candidate_pool_max_size", 0))
    candidate_pool = [annotate_plan_planner_quality(plan) for plan in candidate_pool]
    planner_candidate_pool = _prune_candidate_pool(planner_candidate_pool, candidate_pool_max_size)
    planner_candidate_pool = [annotate_plan_planner_quality(plan) for plan in planner_candidate_pool]

    candidate_pool_for_best, _removed_empty_candidates = filter_empty_contenders(planner_candidate_pool)
    if candidate_pool_for_best:
        selectable_candidate_pool, _non_selectable = filter_selectable_contenders(candidate_pool_for_best)
        if selectable_candidate_pool:
            candidate_pool_for_best = selectable_candidate_pool
    if not candidate_pool_for_best:
        candidate_pool_for_best = planner_candidate_pool

    selection_result = choose_best_plan(
        candidate_pool_for_best,
        base_pd=base_pd,
        tau=tau,
        min_reliability=min_reliability_f,
        min_worst_risk_margin=min_worst_margin_f,
        fairness_penalty=fairness_penalty,
        denied_mode=bool(search_profile.get("is_denied_target", False)),
        segment_context=segment_context,
        denied_objective_cfg=robust_cfg.get("denied_objective", {}),
    )
    best = selection_result.best_plan
    best_source = _selected_plan_source(best)
    path_records = build_recourse_path_records(
        planner_candidate_pool,
        selected_plan_id=_selected_plan_id(best),
        base_pd=base_pd,
        tau=tau,
        min_reliability=min_reliability_f,
        min_worst_risk_margin=min_worst_margin_f,
        fairness_penalty=fairness_penalty,
        denied_mode=bool(search_profile.get("is_denied_target", False)),
        segment_context=segment_context,
        denied_objective_cfg=robust_cfg.get("denied_objective", {}),
    )
    pool_df = pd.DataFrame([_plan_to_row(plan) for plan in candidate_pool])
    pool_csv = run_ctx.tables_dir / "candidate_pool.csv"
    pool_json = run_ctx.tables_dir / "candidate_pool.json"
    pool_df.to_csv(pool_csv, index=False)
    pool_json.write_text(pool_df.to_json(orient="records", indent=2), encoding="utf-8")
    roadmap = _build_customer_roadmap(
        customer_id=args.customer_id,
        base_pd=base_pd,
        tau=tau,
        best=best,
        best_source=best_source,
        selection_result=selection_result,
        row=row,
        model=model,
        calibrator=calibrator,
        feature_cols=feature_cols,
        local_reason_bundle=local_reason_bundle,
    )
    roadmap = _attach_path_summary_to_roadmap(roadmap, path_records=path_records)
    roadmap_json = run_ctx.tables_dir / "customer_roadmap.json"
    roadmap_json.write_text(json.dumps(roadmap, indent=2, ensure_ascii=False), encoding="utf-8")
    roadmap_steps_rows: list[dict] = []
    for phase in roadmap.get("phases", []):
        phase_id = str(phase.get("phase_id", ""))
        phase_title = str(phase.get("phase_title", ""))
        for step in phase.get("steps", []):
            technical_view = step.get("technical_view", {})
            if not isinstance(technical_view, dict):
                technical_view = {}
            primary_numeric_target = step.get("primary_numeric_target", {})
            if not isinstance(primary_numeric_target, dict):
                primary_numeric_target = {}
            row_out = {
                "customer_id": str(args.customer_id),
                "best_plan_id": _selected_plan_id(best),
                "phase_id": phase_id,
                "phase_title": phase_title,
                "target_window_weeks": str(phase.get("target_window_weeks", "")),
                "action_key": str(step.get("action_key", "")),
                "action_class": str(step.get("action_class", "")),
                "action_title": str(step.get("action_title", "")),
                "action_group_id": str(step.get("action_group_id", "")),
                "composite_action": _safe_int(step.get("composite_action", 0), 0),
                "feature_name": str(technical_view.get("feature_name", step.get("feature_name", "")) or ""),
                "metric_key": str(primary_numeric_target.get("metric_key", "") or ""),
                "unit": str(primary_numeric_target.get("unit", "") or ""),
                "current_value": _safe_float(
                    primary_numeric_target.get("current_value", technical_view.get("current_value", step.get("current_value", 0.0))),
                    0.0,
                ),
                "target_value": _safe_float(
                    primary_numeric_target.get("target_value", technical_view.get("target_value", step.get("target_value", 0.0))),
                    0.0,
                ),
                "delta": _safe_float(
                    primary_numeric_target.get("delta_value", technical_view.get("delta", step.get("delta", 0.0))),
                    0.0,
                ),
                "time_months": _safe_int(step.get("time_months", 0), 0),
                "due_month": _safe_int(primary_numeric_target.get("due_month", step.get("time_months", 0)), 0),
                "direction": str(primary_numeric_target.get("direction", "") or ""),
                "generation_notes_json": json.dumps(
                    list(primary_numeric_target.get("generation_notes", [])),
                    ensure_ascii=False,
                ),
                "estimated_cost_usd": _safe_float(step.get("estimated_cost_usd", 0.0), 0.0),
                "requires_institutional_approval": _safe_int(step.get("requires_institutional_approval", 0), 0),
                "approval_pending_semantic_only": _safe_int(step.get("approval_pending_semantic_only", 0), 0),
                "action_status": str(step.get("action_status", "") or ""),
                "constraint_family": str(step.get("constraint_family", "") or ""),
                "constraint_reason_codes_json": json.dumps(
                    list(step.get("constraint_reason_codes", [])),
                    ensure_ascii=False,
                ),
                "was_clipped": _safe_int(step.get("was_clipped", 0), 0),
                "repair_applied": _safe_int(step.get("repair_applied", 0), 0),
                "dependency_gate": _safe_int(step.get("dependency_gate", 0), 0),
                "semantic_preserved": (
                    bool(step.get("semantic_preserved"))
                    if step.get("semantic_preserved", None) is not None
                    else None
        ),
    }


def _build_customer_roadmap_steps_df(
    *,
    customer_id: str,
    best_plan_id: str,
    roadmap: dict[str, Any],
) -> pd.DataFrame:
    roadmap_steps_rows: list[dict[str, Any]] = []
    for phase in roadmap.get("phases", []):
        phase_id = str(phase.get("phase_id", ""))
        phase_title = str(phase.get("phase_title", ""))
        for step in phase.get("steps", []):
            technical_view = step.get("technical_view", {})
            if not isinstance(technical_view, dict):
                technical_view = {}
            primary_numeric_target = step.get("primary_numeric_target", {})
            if not isinstance(primary_numeric_target, dict):
                primary_numeric_target = {}
            row_out = {
                "customer_id": str(customer_id),
                "best_plan_id": str(best_plan_id),
                "phase_id": phase_id,
                "phase_title": phase_title,
                "target_window_weeks": str(phase.get("target_window_weeks", "")),
                "action_key": str(step.get("action_key", "")),
                "action_class": str(step.get("action_class", "")),
                "action_title": str(step.get("action_title", "")),
                "action_group_id": str(step.get("action_group_id", "")),
                "composite_action": _safe_int(step.get("composite_action", 0), 0),
                "feature_name": str(technical_view.get("feature_name", step.get("feature_name", "")) or ""),
                "metric_key": str(primary_numeric_target.get("metric_key", "") or ""),
                "unit": str(primary_numeric_target.get("unit", "") or ""),
                "current_value": _safe_float(
                    primary_numeric_target.get(
                        "current_value",
                        technical_view.get("current_value", step.get("current_value", 0.0)),
                    ),
                    0.0,
                ),
                "target_value": _safe_float(
                    primary_numeric_target.get(
                        "target_value",
                        technical_view.get("target_value", step.get("target_value", 0.0)),
                    ),
                    0.0,
                ),
                "delta": _safe_float(
                    primary_numeric_target.get(
                        "delta_value",
                        technical_view.get("delta", step.get("delta", 0.0)),
                    ),
                    0.0,
                ),
                "time_months": _safe_int(step.get("time_months", 0), 0),
                "due_month": _safe_int(primary_numeric_target.get("due_month", step.get("time_months", 0)), 0),
                "direction": str(primary_numeric_target.get("direction", "") or ""),
                "generation_notes_json": json.dumps(
                    list(primary_numeric_target.get("generation_notes", [])),
                    ensure_ascii=False,
                ),
                "estimated_cost_usd": _safe_float(step.get("estimated_cost_usd", 0.0), 0.0),
                "requires_institutional_approval": _safe_int(step.get("requires_institutional_approval", 0), 0),
                "approval_pending_semantic_only": _safe_int(step.get("approval_pending_semantic_only", 0), 0),
                "action_status": str(step.get("action_status", "") or ""),
                "constraint_family": str(step.get("constraint_family", "") or ""),
                "constraint_reason_codes_json": json.dumps(
                    list(step.get("constraint_reason_codes", [])),
                    ensure_ascii=False,
                ),
                "was_clipped": _safe_int(step.get("was_clipped", 0), 0),
                "repair_applied": _safe_int(step.get("repair_applied", 0), 0),
                "dependency_gate": _safe_int(step.get("dependency_gate", 0), 0),
                "semantic_preserved": (
                    bool(step.get("semantic_preserved"))
                    if step.get("semantic_preserved", None) is not None
                    else None
                ),
                "recommendation_validity_status": str(step.get("recommendation_validity_status", "") or ""),
                "recommendation_validity_codes_json": json.dumps(
                    list(step.get("recommendation_validity_codes", [])),
                    ensure_ascii=False,
                ),
                "recommendation_sanity_flag": _safe_int(step.get("recommendation_sanity_flag", 0), 0),
            }
            roadmap_steps_rows.append(row_out)
    if not roadmap_steps_rows:
        return pd.DataFrame(columns=_ROADMAP_STEP_COLUMNS)
    return pd.DataFrame(roadmap_steps_rows, columns=_ROADMAP_STEP_COLUMNS)


def _build_customer_metrics_summary(
    *,
    model_version: str,
    customer_id: str,
    base_pd: float,
    search_profile: dict[str, Any],
    segment_context: dict[str, Any],
    validated: list[PlanRecord],
    candidate_pool: list[PlanRecord],
    best: PlanRecord | None,
    best_source: str,
    selection_result: BestPlanSelectionResult,
    roadmap: dict[str, Any],
    msi: float,
    alpha: float,
    robust_objective: str,
    robust_cvar_quantile: float,
    local_reason_bundle: dict[str, Any],
    adverse_action_reasons: list[Any],
    dice_backend: str,
    dice_records: list[PlanRecord],
    dice_telemetry: dict[str, Any],
    search_elapsed_ms: float,
    fairness_penalty: float,
    decision_log_record: dict[str, Any],
    decision_log_summary: dict[str, Any],
) -> dict[str, Any]:
    roadmap = _normalize_customer_roadmap_contract(roadmap)
    candidate_pool = [annotate_plan_planner_quality(plan) for plan in candidate_pool]
    if best is not None:
        best = annotate_plan_planner_quality(best)
    selection_meta = _selection_meta_dict(selection_result)
    roadmap_tau = roadmap.get("tau", None)
    cp_week4 = next((c for c in roadmap.get("checkpoints", []) if int(c.get("week", 0)) == 4), {})
    cp_week12 = next((c for c in roadmap.get("checkpoints", []) if int(c.get("week", 0)) == 12), {})
    cp_week24 = next((c for c in roadmap.get("checkpoints", []) if int(c.get("week", 0)) == 24), {})
    avg_reliability = (
        float(sum(float(p.reliability or 0.0) for p in validated) / max(1, len(validated)))
        if validated
        else 0.0
    )
    avg_robust_score = (
        float(sum(float(p.robust_score or 0.0) for p in validated) / max(1, len(validated)))
        if validated
        else 0.0
    )
    min_robust_margin = (
        float(min(float(p.robust_margin or 0.0) for p in validated))
        if validated
        else 0.0
    )
    source_counts = candidate_source_counts(candidate_pool)
    source_presence = candidate_source_presence_flags(candidate_pool)
    contender_counts = contender_bucket_counts(candidate_pool)
    dice_quality = summarize_dice_candidate_metrics(dice_records, selected_plan=best)
    selected_dice_flag = int(dice_quality["selected_dice_flag"])
    selected_dice_valid_flag = int(dice_quality["selected_dice_valid_flag"])
    metrics_summary = {
        "model_version": model_version,
        "customer_id": customer_id,
        "base_pd": base_pd,
        "denied_target_mode": bool(search_profile.get("is_denied_target", False)),
        "income_band": str(segment_context.get("income_band", "")),
        "risk_band": str(segment_context.get("risk_band", "")),
        "segment_caps_applied": bool(segment_context.get("segment_caps_applied", False)),
        "cap_multiplier_income": float(segment_context.get("cap_multiplier_income", 1.0)),
        "cap_multiplier_risk": float(segment_context.get("cap_multiplier_risk", 1.0)),
        "cap_multiplier_total": float(segment_context.get("cap_multiplier", 1.0)),
        "plan_count": len(validated),
        "approved_count": int(sum(1 for p in validated if p.status == "APPROVED")),
        "candidate_pool_count": len(candidate_pool),
        "candidate_pool_approved_count": int(sum(1 for p in candidate_pool if p.status == "APPROVED")),
        "candidate_pool_diversity_index": candidate_pool_diversity_index(candidate_pool),
        "candidate_source_entropy": candidate_source_entropy(candidate_pool),
        "best_plan_id": _selected_plan_id(best),
        "best_plan_source": str(best_source or ""),
        "best_contender_bucket": str(getattr(best, "contender_bucket", "") or ""),
        "best_offer_maturity": str(getattr(best, "offer_maturity", "none") or "none"),
        "best_execution_aware_value": (
            execution_aware_value(best, base_pd=base_pd, tau=_safe_float(roadmap_tau, 0.0) if roadmap_tau is not None else None)
            if best is not None
            else 0.0
        ),
        "best_status": str(getattr(best, "status", "") or ""),
        "trajectory_pd_4w": _safe_float(cp_week4.get("predicted_pd", base_pd), base_pd),
        "trajectory_pd_12w": _safe_float(cp_week12.get("predicted_pd", base_pd), base_pd),
        "trajectory_pd_24w": _safe_float(cp_week24.get("predicted_pd", base_pd), base_pd),
        "trajectory_gate_pass_4w": _safe_int(cp_week4.get("gate_pass_estimate", 0), 0),
        "trajectory_gate_pass_12w": _safe_int(cp_week12.get("gate_pass_estimate", 0), 0),
        "trajectory_gate_pass_24w": _safe_int(cp_week24.get("gate_pass_estimate", 0), 0),
        "trajectory_next_review_week": _safe_int(roadmap.get("next_review_week", 4), 4),
        "trajectory_phase_count": int(len(roadmap.get("phases", []))),
        "trajectory_step_count": int(sum(len(p.get("steps", [])) for p in roadmap.get("phases", []))),
        "mean_group_difficulty_score": (
            _safe_float(getattr(best, "mean_group_difficulty_score", 0.0), 0.0)
            if getattr(best, "mean_group_difficulty_score", None) is not None
            else None
        ),
        "peak_group_difficulty_score": (
            _safe_float(getattr(best, "peak_group_difficulty_score", 0.0), 0.0)
            if getattr(best, "peak_group_difficulty_score", None) is not None
            else None
        ),
        "dominant_difficulty_label": str(getattr(best, "dominant_difficulty_label", "") or ""),
        "follow_through_readiness_label": str(getattr(best, "follow_through_readiness_label", "") or ""),
        "macro_stress_index": msi,
        "alpha_used": alpha,
        "robust_objective": robust_objective,
        "robust_cvar_quantile": robust_cvar_quantile,
        "avg_reliability": avg_reliability,
        "avg_robust_score": avg_robust_score,
        "min_robust_margin": min_robust_margin,
        "local_explainability_confidence": float(local_reason_bundle.get("meta", {}).get("explainability_confidence", 0.0)),
        "local_shap_stability_score": float(local_reason_bundle.get("meta", {}).get("stability_score", 0.0)),
        "local_shap_baseline_drift_l1": float(local_reason_bundle.get("meta", {}).get("baseline_drift_l1", 0.0)),
        "adverse_action_reasons": adverse_action_reasons,
        "dice_backend": dice_backend,
        "dice_backend_class": classify_dice_backend_class(dice_backend),
        "dice_plan_count": len(dice_records),
        "dice_method_requested": dice_telemetry.get("method_requested"),
        "dice_method_used": dice_telemetry.get("method_used"),
        "dice_fallback_reason": dice_telemetry.get("fallback_reason"),
        "dice_changed_features": int(dice_telemetry.get("changed_feature_union_count", 0)),
        "dice_attempted_method_count": int(dice_telemetry.get("attempted_method_count", 0)),
        "dice_skipped_reason": str(dice_telemetry.get("fallback_reason") or ""),
        "search_time_budget_ms": int(
            (
                search_profile.get("search_cfg", {})
                if isinstance(search_profile.get("search_cfg", {}), dict)
                else {}
            ).get("time_budget_ms", 0)
        ),
        "search_elapsed_ms": float(search_elapsed_ms),
        "fairness_penalty": float(fairness_penalty),
        "decision_id": str(decision_log_record["decision_id"]),
        "selection_propensity": float(decision_log_record["selection_propensity"]),
        "decision_log_completeness": float(decision_log_summary.get("decision_log_completeness", 0.0)),
        "selected_dice_flag": selected_dice_flag,
        "selected_dice_valid_flag": selected_dice_valid_flag,
        "selected_dice_annotation_complete_flag": int(
            selected_dice_flag == 1 and bool(getattr(best, "dice_annotation_complete", False))
        ),
        "selected_dice_semantic_invalid_flag": int(
            selected_dice_flag == 1
            and str(getattr(best, "dice_semantic_quality_status", "") or "").strip().lower() == "invalid"
        ),
        **selection_meta,
        **dice_quality,
    }
    for source in CANDIDATE_SOURCE_CATALOG:
        metrics_summary[f"candidate_source_{source}_count"] = int(source_counts.get(source, 0))
        metrics_summary[f"candidate_source_{source}_present"] = int(source_presence.get(source, 0))
    metrics_summary.update(
        {
            "candidate_non_empty_count": int(contender_counts["ACTIONABLE"] + contender_counts["APPROVAL_SHELL_ONLY"]),
            "candidate_approval_shell_only_count": int(contender_counts["APPROVAL_SHELL_ONLY"]),
            "candidate_empty_removed_count": int(contender_counts["EMPTY"]),
            "hard_invalid_plan_rate": float(
                sum(1 for plan in candidate_pool if str(getattr(plan, "recommendation_validity_status", "valid")) == "invalid")
                / max(1, len(candidate_pool))
            ),
            "numeric_warning_rate": float(
                sum(1 for plan in candidate_pool if str(getattr(plan, "recommendation_validity_status", "valid")) == "warning")
                / max(1, len(candidate_pool))
            ),
            "best_plan_warning_rate": float(
                1.0 if str(getattr(best, "recommendation_validity_status", "valid")) == "warning" else 0.0
            ),
            "selected_invalid_winner_flag": int(
                selection_result.selection_outcome == "selected_valid_winner"
                and str(getattr(best, "recommendation_validity_status", "") or "") == "invalid"
            ),
            "directional_invalid_count": int(
                sum(
                    1
                    for plan in candidate_pool
                    if any(
                        code in {"directional_worsens_risk", "no_effect_target", "customer_institution_mislabel"}
                        for code in list(getattr(plan, "recommendation_validity_codes", []) or [])
                    )
                )
            ),
            "economic_warning_count": int(
                sum(
                    1
                    for plan in candidate_pool
                    if any(
                        code in {"economic_delta_large", "economic_delta_implausible", "feasibility_band_exceeded"}
                        for code in list(getattr(plan, "recommendation_validity_codes", []) or [])
                    )
                )
            ),
            "offer_ready_contender_share": float(
                sum(1 for plan in candidate_pool if str(getattr(plan, "offer_maturity", "none")) == "active_rankable")
                / max(1, len(candidate_pool))
            ),
            "provisional_offer_share": float(
                sum(1 for plan in candidate_pool if str(getattr(plan, "offer_maturity", "none")) == "provisional")
                / max(1, len(candidate_pool))
            ),
            "approval_shell_only_share": float(
                contender_counts["APPROVAL_SHELL_ONLY"] / max(1, len(candidate_pool))
            ),
            "dice_eligible_rate": float(
                dice_quality["dice_contender_eligible_count"] / max(1, dice_quality["dice_candidate_count"])
            ),
            "dice_invalid_rate": float(
                dice_quality["dice_invalid_candidate_count"] / max(1, dice_quality["dice_candidate_count"])
            ),
            "dice_warning_rate": float(
                dice_quality["dice_warning_candidate_count"] / max(1, dice_quality["dice_candidate_count"])
            ),
            "dice_fallback_rate": float(
                dice_quality["dice_fallback_candidate_count"] / max(1, dice_quality["dice_candidate_count"])
            ),
            "selected_dice_valid_rate": float(
                1.0 if selected_dice_flag == 0 else (selected_dice_valid_flag / selected_dice_flag)
            ),
        }
    )
    return _sync_metrics_summary_with_roadmap_summary(metrics_summary, roadmap=roadmap)


def build_customer_artifact_bundle(
    *,
    customer_id: str,
    model_version: str,
    base_pd: float,
    search_profile: dict[str, Any],
    segment_context: dict[str, Any],
    validated: list[PlanRecord],
    candidate_pool: list[PlanRecord],
    best: PlanRecord | None,
    best_source: str,
    selection_result: BestPlanSelectionResult,
    roadmap: dict[str, Any],
    msi: float,
    alpha: float,
    robust_objective: str,
    robust_cvar_quantile: float,
    local_reason_bundle: dict[str, Any],
    adverse_action_reasons: list[Any],
    dice_backend: str,
    dice_records: list[PlanRecord],
    dice_telemetry: dict[str, Any],
    search_elapsed_ms: float,
    fairness_penalty: float,
    decision_log_record: dict[str, Any],
    decision_log_summary: dict[str, Any],
    path_records: list[RecoursePathRecord] | None = None,
) -> CustomerArtifactBundle:
    roadmap = _normalize_customer_roadmap_contract(roadmap)
    plan_lookup = {
        _safe_text(getattr(plan, "plan_id", "")): plan
        for plan in [*validated, *candidate_pool]
        if _safe_text(getattr(plan, "plan_id", ""))
    }
    if path_records:
        _attach_path_render_summaries(path_records, plan_lookup=plan_lookup)
    roadmap = _attach_path_summary_to_roadmap(roadmap, path_records=path_records or [])
    roadmap = _inject_decision_inputs_into_roadmap(
        roadmap,
        best=best,
        base_pd=base_pd,
        local_reason_bundle=local_reason_bundle,
    )
    roadmap = _apply_decision_ownership_to_roadmap(roadmap)
    roadmap = _build_selected_surface_projection(roadmap)
    roadmap = _attach_recoverability_signal_to_roadmap(
        roadmap,
        base_pd=base_pd,
        tau=_safe_float(roadmap.get("tau", 0.0), 0.0),
        segment_context=segment_context,
        path_records=path_records or [],
        plan_lookup=plan_lookup,
    )
    plans_df = _build_bundle_plans_df(validated=validated, candidate_pool=candidate_pool)
    roadmap_steps_df = _build_customer_roadmap_steps_df(
        customer_id=customer_id,
        best_plan_id=_selected_plan_id(best),
        roadmap=roadmap,
    )
    metrics_summary = _build_customer_metrics_summary(
        model_version=model_version,
        customer_id=customer_id,
        base_pd=base_pd,
        search_profile=search_profile,
        segment_context=segment_context,
        validated=validated,
        candidate_pool=candidate_pool,
        best=best,
        best_source=best_source,
        selection_result=selection_result,
        roadmap=roadmap,
        msi=msi,
        alpha=alpha,
        robust_objective=robust_objective,
        robust_cvar_quantile=robust_cvar_quantile,
        local_reason_bundle=local_reason_bundle,
        adverse_action_reasons=adverse_action_reasons,
        dice_backend=dice_backend,
        dice_records=dice_records,
        dice_telemetry=dice_telemetry,
        search_elapsed_ms=search_elapsed_ms,
        fairness_penalty=fairness_penalty,
        decision_log_record=decision_log_record,
        decision_log_summary=decision_log_summary,
    )
    paths_df = _path_records_to_df(path_records or [])
    return CustomerArtifactBundle(
        customer_id=str(customer_id),
        plans_df=plans_df,
        roadmap=roadmap,
        roadmap_steps_df=roadmap_steps_df,
        metrics_summary=metrics_summary,
        paths_df=paths_df,
    )


def write_customer_artifact_bundle(bundle: CustomerArtifactBundle, output_dir: Path) -> dict[str, Path]:
    bundle.roadmap = _normalize_customer_roadmap_contract(bundle.roadmap)
    if _safe_text(bundle.roadmap.get("summary", {}).get("decision_policy_version")):
        bundle.roadmap = _apply_decision_ownership_to_roadmap(bundle.roadmap)
    bundle.roadmap = _build_selected_surface_projection(bundle.roadmap)
    bundle.metrics_summary = _sync_metrics_summary_with_roadmap_summary(
        bundle.metrics_summary,
        roadmap=bundle.roadmap,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    plans_json = output_dir / "plans.json"
    roadmap_json = output_dir / "customer_roadmap.json"
    metrics_json = output_dir / "metrics.json"
    paths_json = output_dir / "customer_paths.json"
    roadmap_steps_csv = output_dir / "customer_roadmap_steps.csv"
    plans_json.write_text(bundle.plans_df.to_json(orient="records", indent=2), encoding="utf-8")
    roadmap_json.write_text(json.dumps(bundle.roadmap, indent=2, ensure_ascii=False), encoding="utf-8")
    metrics_json.write_text(json.dumps(bundle.metrics_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    paths_json.write_text(bundle.paths_df.to_json(orient="records", indent=2), encoding="utf-8")
    bundle.roadmap_steps_df.to_csv(roadmap_steps_csv, index=False)
    return {
        "plans_json": plans_json,
        "roadmap_json": roadmap_json,
        "metrics_json": metrics_json,
        "paths_json": paths_json,
        "roadmap_steps_csv": roadmap_steps_csv,
    }


def generate_customer_recourse_artifacts(
    *,
    customer_id: str,
    run_id: str,
    row: pd.Series,
    test_df: pd.DataFrame,
    train_df: pd.DataFrame,
    model,
    calibrator,
    manifest: dict[str, Any],
    feature_cols: list[str],
    target_col: str,
    model_cfg: dict[str, Any],
    rec_cfg: dict[str, Any],
    c_cfg: dict[str, Any],
    s_cfg: dict[str, Any],
    m_cfg: dict[str, Any],
    graph,
    persist_repository_records: bool = True,
) -> CustomerRecourseRunResult:
    local_reason_bundle = compute_local_reason_bundle(
        model,
        row[feature_cols],
        top_k=int(rec_cfg.get("shap", {}).get("topk_features", 10)),
        perturbations=int(rec_cfg.get("shap", {}).get("stability_perturbations", 6)),
        noise_std=float(rec_cfg.get("shap", {}).get("stability_noise_std", 0.01)),
        random_state=int(rec_cfg.get("shap", {}).get("stability_seed", 42)),
        background_df=train_df[feature_cols].sample(
            n=min(len(train_df), int(rec_cfg.get("shap", {}).get("background_samples", 256))),
            random_state=int(rec_cfg.get("shap", {}).get("stability_seed", 42)),
        ),
    )
    adverse_action_reasons = build_adverse_action_reasons(local_reason_bundle.get("reasons", []), max_items=4)

    tau = float(model_cfg.get("decision", {}).get("tau_0", 0.35))
    horizons = [int(v) for v in rec_cfg.get("horizons", [3, 6, 12])]
    strategies = [str(v) for v in rec_cfg.get("strategies", ["conservative", "balanced", "aggressive"])]
    robust_cfg_base = rec_cfg.get("robust", {}) if isinstance(rec_cfg.get("robust", {}), dict) else {}
    dice_cfg_base = rec_cfg.get("dice", {}) if isinstance(rec_cfg.get("dice", {}), dict) else {}
    scenarios = m_cfg.get("shock_scenarios", []) if isinstance(m_cfg.get("shock_scenarios", []), list) else []
    threshold_shift = float(m_cfg.get("event_impact", {}).get("threshold_shift_per_msi_unit", 0.0))
    uncertainty_cfg = s_cfg.get("uncertainty", {}) if isinstance(s_cfg.get("uncertainty", {}), dict) else {}
    conformal_artifact_path = manifest.get("conformal_calibration_path")
    if conformal_artifact_path:
        uncertainty_cfg = dict(uncertainty_cfg)
        conformal_cfg = (
            uncertainty_cfg.get("conformal", {})
            if isinstance(uncertainty_cfg.get("conformal", {}), dict)
            else {}
        )
        conformal_cfg = dict(conformal_cfg)
        if not str(conformal_cfg.get("calibration_artifact_path", "")).strip():
            conformal_cfg["calibration_artifact_path"] = str(conformal_artifact_path)
        uncertainty_cfg["conformal"] = conformal_cfg

        robust_cfg_base = dict(robust_cfg_base)
        gate_obj = (
            robust_cfg_base.get("gate_objective", {})
            if isinstance(robust_cfg_base.get("gate_objective", {}), dict)
            else {}
        )
        gate_obj = dict(gate_obj)
        unc_cfg = gate_obj.get("uncertainty", {}) if isinstance(gate_obj.get("uncertainty", {}), dict) else {}
        unc_cfg = dict(unc_cfg)
        if not str(unc_cfg.get("calibration_artifact_path", "")).strip():
            unc_cfg["calibration_artifact_path"] = str(conformal_artifact_path)
        gate_obj["uncertainty"] = unc_cfg
        robust_cfg_base["gate_objective"] = gate_obj

    actionable = set(get_dice_generatable_features(feature_cols))
    local_reasons = local_reason_bundle.get("reasons", [])
    candidate_features = [r for r in local_reasons if str(r.get("feature", "")) in actionable]

    base_pd = float(
        predict_proba_pd(
            model,
            calibrator,
            pd.DataFrame([row[feature_cols].values], columns=feature_cols),
        )[0]
    )
    topk_default = int(rec_cfg.get("shap", {}).get("topk_features", 10))
    segment_caps_cfg = rec_cfg.get("segment_caps", {}) if isinstance(rec_cfg.get("segment_caps", {}), dict) else {}
    q_cfg = segment_caps_cfg.get("income_quantiles", [0.25, 0.50, 0.75])
    q_list = list(q_cfg) if isinstance(q_cfg, list) else [0.25, 0.50, 0.75]
    income_edges = _compute_income_edges(test_df.get("annual_inc", pd.Series(dtype=float)), q_list)
    feasibility_cfg = rec_cfg.get("feasibility", {}) if isinstance(rec_cfg.get("feasibility", {}), dict) else {}
    feasibility_profile: dict[str, Any] | None = None
    if bool(feasibility_cfg.get("enabled", False)):
        profile_path = str(feasibility_cfg.get("profile_path", "")).strip()
        if profile_path:
            feasibility_profile = load_config(profile_path)
    feasibility_internal_profile = feasibility_profile if bool(feasibility_cfg.get("enforce_on_internal", True)) else None
    feasibility_dice_profile = feasibility_profile if bool(feasibility_cfg.get("enforce_on_dice", True)) else None
    search_profile, robust_cfg, dice_cfg = _effective_recourse_search(
        base_pd=base_pd,
        tau=tau,
        topk=topk_default,
        horizons=horizons,
        strategies=strategies,
        robust_cfg=robust_cfg_base,
        dice_cfg=dice_cfg_base,
        rec_cfg=rec_cfg,
    )
    segment_context = _build_segment_context(
        row=row,
        base_pd=base_pd,
        tau=tau,
        denied_mode=bool(search_profile.get("is_denied_target", False)),
        segment_caps_cfg=segment_caps_cfg,
        income_edges=income_edges,
    )
    search_cfg_patch = (
        search_profile.get("search_cfg", {})
        if isinstance(search_profile.get("search_cfg", {}), dict)
        else {}
    )
    search_cfg_patch = dict(search_cfg_patch)
    search_cfg_patch["segment_context"] = segment_context
    search_profile["search_cfg"] = search_cfg_patch
    robust_objective = str(robust_cfg.get("objective", "cvar"))
    robust_cvar_quantile = float(robust_cfg.get("cvar_quantile", 0.9))
    min_reliability = robust_cfg.get("min_reliability")
    min_worst_margin = robust_cfg.get("min_worst_risk_margin")
    min_reliability_f = float(min_reliability) if min_reliability is not None else None
    min_worst_margin_f = float(min_worst_margin) if min_worst_margin is not None else None

    fairness_cfg = rec_cfg.get("fairness", {}) if isinstance(rec_cfg.get("fairness", {}), dict) else {}
    fairness_group_col = str(fairness_cfg.get("group_feature", "home_ownership"))
    fairness_penalty = 0.0
    if fairness_group_col in test_df.columns and fairness_group_col in row.index:
        sample_n = min(len(test_df), int(fairness_cfg.get("penalty_sample_n", 3000)))
        fairness_sample = test_df.sample(n=sample_n, random_state=int(fairness_cfg.get("penalty_seed", 42)))
        fairness_proba = pd.Series(
            predict_proba_pd(model, calibrator, fairness_sample[feature_cols]),
            index=fairness_sample.index,
            dtype=float,
        )
        fairness_scored = pd.DataFrame(
            {
                fairness_group_col: fairness_sample[fairness_group_col].astype(str).fillna("unknown"),
                "approve": (fairness_proba <= tau).astype(int),
            }
        )
        group_penalties = build_group_advantage_penalties(
            fairness_scored,
            group_col=fairness_group_col,
            approval_col="approve",
            tolerance=float(fairness_cfg.get("advantage_tolerance", 0.01)),
        )
        fairness_penalty = lookup_group_penalty(row[fairness_group_col], group_penalties)

    recourse_start_ts = time.perf_counter()
    plans = generate_nine_plans(
        customer_id=customer_id,
        run_id=run_id,
        row=row,
        model=model,
        calibrator=calibrator,
        feature_cols=feature_cols,
        graph=graph,
        tau=tau,
        horizons=search_profile["horizons"],
        strategies=search_profile["strategies"],
        candidate_features=candidate_features,
        topk=int(search_profile["topk"]),
        scenarios=scenarios,
        threshold_shift_per_msi_unit=threshold_shift,
        robust_cfg=robust_cfg,
        search_cfg=search_profile.get("search_cfg", {}),
        fairness_penalty=fairness_penalty,
        feasibility_profile=feasibility_internal_profile,
        segment_context=segment_context,
    )

    macro_snapshot = load_macro_snapshot_mock()
    msi = compute_macro_stress_index(macro_snapshot, m_cfg.get("stress_index_weights", {}))
    base_alpha = float(s_cfg.get("confidence", {}).get("base_alpha", 0.05))
    high_stress_alpha = float(s_cfg.get("confidence", {}).get("high_stress_alpha", 0.01))
    stress_threshold = float(m_cfg.get("stress_threshold", 0.7))
    alpha = dynamic_alpha(msi, base_alpha=base_alpha, high_stress_alpha=high_stress_alpha, threshold=stress_threshold)

    bootstrap_b = int(s_cfg.get("bootstrap", {}).get("B", 500))
    validated = [
        validate_plan(
            plan,
            tau=tau,
            alpha=alpha,
            bootstrap_b=bootstrap_b,
            scenarios=scenarios,
            threshold_shift_per_msi_unit=threshold_shift,
            robust_objective=robust_objective,
            robust_cvar_quantile=robust_cvar_quantile,
            min_reliability=min_reliability_f,
            min_worst_risk_margin=min_worst_margin_f,
            uncertainty_cfg=uncertainty_cfg,
            segment_context=segment_context,
        )
        for plan in plans
    ]

    if persist_repository_records:
        for plan in validated:
            save_plan(plan)

    search_cfg = (
        search_profile.get("search_cfg", {})
        if isinstance(search_profile.get("search_cfg", {}), dict)
        else {}
    )
    internal_approved_count = int(sum(1 for plan in validated if plan.status == "APPROVED"))
    deny_mode = bool(search_profile.get("is_denied_target", False))
    time_budget_ms = int(search_cfg.get("time_budget_ms", 0))
    skip_dice_when_internal_approved = bool(search_cfg.get("skip_dice_when_internal_approved", False))
    skip_dice_for_non_denied = bool(search_cfg.get("skip_dice_for_non_denied", False))
    elapsed_so_far_ms = float((time.perf_counter() - recourse_start_ts) * 1000.0)
    remaining_budget_ms = int(max(0.0, float(time_budget_ms) - elapsed_so_far_ms)) if time_budget_ms > 0 else 0

    skip_dice_reason = ""
    if skip_dice_when_internal_approved and internal_approved_count > 0:
        skip_dice_reason = "internal_already_approved"
    if not skip_dice_reason and skip_dice_for_non_denied and not deny_mode:
        skip_dice_reason = "non_denied_profile"
    if not skip_dice_reason and time_budget_ms > 0 and elapsed_so_far_ms >= float(time_budget_ms):
        skip_dice_reason = "time_budget_exceeded"

    dice_records: list[PlanRecord] = []
    dice_backend = "skipped"
    dice_telemetry: dict[str, Any] = {
        "method_requested": str(dice_cfg.get("method", "random")),
        "method_used": "skipped",
        "fallback_reason": skip_dice_reason or "skipped_by_policy",
        "attempted_method_count": 0,
    }
    if not skip_dice_reason:
        configured_timeout_ms = int(dice_cfg.get("timeout_ms", 0))
        dice_timeout_ms = configured_timeout_ms
        if dice_timeout_ms > 0 and remaining_budget_ms > 0:
            dice_timeout_ms = min(dice_timeout_ms, remaining_budget_ms)
        dice_action_sets, dice_backend, dice_telemetry = generate_dice_counterfactual_actions(
            row=row,
            feature_cols=feature_cols,
            actionable_features=sorted(actionable),
            model=model,
            calibrator=calibrator,
            train_df=train_df,
            target_col=target_col,
            total_cfs=int(dice_cfg.get("total_cfs", 3)),
            random_seed=int(dice_cfg.get("seed", 42)),
            dice_method=str(dice_cfg.get("method", "random")),
            max_actions=int(dice_cfg.get("max_actions", 4)),
            enable_method_fallback=bool(dice_cfg.get("enable_method_fallback", True)),
            timeout_ms=int(max(0, dice_timeout_ms)),
            stopping_threshold=float(tau),
        )
        for idx, actions in enumerate(dice_action_sets, start=1):
            plan = _dice_plan_record(
                idx=idx,
                customer_id=customer_id,
                run_id=run_id,
                row=row,
                feature_cols=feature_cols,
                actions=actions,
                model=model,
                calibrator=calibrator,
                tau=tau,
                graph=graph,
                causal_weight=float(c_cfg.get("penalty_weight", 0.3)),
                feasibility_profile=feasibility_dice_profile,
                segment_context=segment_context,
            )
            plan = validate_plan(
                plan,
                tau=tau,
                alpha=alpha,
                bootstrap_b=bootstrap_b,
                scenarios=scenarios,
                threshold_shift_per_msi_unit=threshold_shift,
                robust_objective=robust_objective,
                robust_cvar_quantile=robust_cvar_quantile,
                min_reliability=min_reliability_f,
                min_worst_risk_margin=min_worst_margin_f,
                uncertainty_cfg=uncertainty_cfg,
                segment_context=segment_context,
            )
            plan = annotate_dice_candidate_quality(
                plan,
                backend_class=classify_dice_backend_class(dice_backend),
            )
            dice_records.append(plan)
            if persist_repository_records:
                save_plan(plan)

    dice_df = pd.DataFrame([_plan_to_row(annotate_plan_planner_quality(plan)) for plan in dice_records])
    rule_cfg = rec_cfg.get("rule_generator", {}) if isinstance(rec_cfg.get("rule_generator", {}), dict) else {}
    rule_action_sets = (
        generate_institution_rule_action_sets(
            row=row,
            feature_cols=feature_cols,
            max_candidates=int(rule_cfg.get("max_actions", 4)),
        )
        if bool(rule_cfg.get("enabled", True))
        else []
    )
    rule_records: list[PlanRecord] = []
    for ridx, actions in enumerate(rule_action_sets, start=1):
        plan = _dice_plan_record(
            idx=ridx,
            customer_id=customer_id,
            run_id=run_id,
            row=row,
            feature_cols=feature_cols,
            actions=actions,
            model=model,
            calibrator=calibrator,
            tau=tau,
            graph=graph,
            causal_weight=float(c_cfg.get("penalty_weight", 0.3)),
            feasibility_profile=feasibility_dice_profile,
            segment_context=segment_context,
            source_tag="rule",
        )
        plan = validate_plan(
            plan,
            tau=tau,
            alpha=alpha,
            bootstrap_b=bootstrap_b,
            scenarios=scenarios,
            threshold_shift_per_msi_unit=threshold_shift,
            robust_objective=robust_objective,
            robust_cvar_quantile=robust_cvar_quantile,
            min_reliability=min_reliability_f,
            min_worst_risk_margin=min_worst_margin_f,
            uncertainty_cfg=uncertainty_cfg,
            segment_context=segment_context,
        )
        plan = annotate_rule_candidate_quality(plan)
        rule_records.append(plan)
        if persist_repository_records:
            save_plan(plan)

    candidate_pool = validated + dice_records + rule_records
    planner_candidate_pool, _ineligible_dice_candidates = split_dice_planner_eligible(candidate_pool)
    planner_candidate_pool, _ineligible_rule_candidates = split_rule_planner_eligible(planner_candidate_pool)
    candidate_pool_max_size = int(search_cfg.get("candidate_pool_max_size", 0))
    candidate_pool = [annotate_plan_planner_quality(plan) for plan in candidate_pool]
    planner_candidate_pool = _prune_candidate_pool(planner_candidate_pool, candidate_pool_max_size)
    planner_candidate_pool = [annotate_plan_planner_quality(plan) for plan in planner_candidate_pool]

    candidate_pool_for_best, _removed_empty_candidates = filter_empty_contenders(planner_candidate_pool)
    if candidate_pool_for_best:
        selectable_candidate_pool, _non_selectable = filter_selectable_contenders(candidate_pool_for_best)
        if selectable_candidate_pool:
            candidate_pool_for_best = selectable_candidate_pool
    if not candidate_pool_for_best:
        candidate_pool_for_best = planner_candidate_pool

    selection_result = choose_best_plan(
        candidate_pool_for_best,
        base_pd=base_pd,
        tau=tau,
        min_reliability=min_reliability_f,
        min_worst_risk_margin=min_worst_margin_f,
        fairness_penalty=fairness_penalty,
        denied_mode=bool(search_profile.get("is_denied_target", False)),
        segment_context=segment_context,
        denied_objective_cfg=robust_cfg.get("denied_objective", {}),
    )
    best = selection_result.best_plan
    best_source = _selected_plan_source(best)
    path_records = build_recourse_path_records(
        planner_candidate_pool,
        selected_plan_id=_selected_plan_id(best),
        base_pd=base_pd,
        tau=tau,
        min_reliability=min_reliability_f,
        min_worst_risk_margin=min_worst_margin_f,
        fairness_penalty=fairness_penalty,
        denied_mode=bool(search_profile.get("is_denied_target", False)),
        segment_context=segment_context,
        denied_objective_cfg=robust_cfg.get("denied_objective", {}),
    )
    candidate_pool_df = pd.DataFrame([_plan_to_row(plan) for plan in candidate_pool])
    roadmap = _build_customer_roadmap(
        customer_id=customer_id,
        base_pd=base_pd,
        tau=tau,
        best=best,
        best_source=best_source,
        selection_result=selection_result,
        row=row,
        model=model,
        calibrator=calibrator,
        feature_cols=feature_cols,
        local_reason_bundle=local_reason_bundle,
    )
    decision_log_record = _decision_log_record(
        run_id=run_id,
        customer_id=str(customer_id),
        plan=best,
    )
    decision_log_summary = build_decision_logging_summary([decision_log_record])
    artifact_bundle = build_customer_artifact_bundle(
        customer_id=customer_id,
        model_version=str(manifest["model_version"]),
        base_pd=base_pd,
        search_profile=search_profile,
        segment_context=segment_context,
        validated=validated,
        candidate_pool=candidate_pool,
        best=best,
        best_source=best_source,
        selection_result=selection_result,
        roadmap=roadmap,
        msi=msi,
        alpha=alpha,
        robust_objective=robust_objective,
        robust_cvar_quantile=robust_cvar_quantile,
        local_reason_bundle=local_reason_bundle,
        adverse_action_reasons=adverse_action_reasons,
        dice_backend=dice_backend,
        dice_records=dice_records,
        dice_telemetry=dice_telemetry,
        search_elapsed_ms=float((time.perf_counter() - recourse_start_ts) * 1000.0),
        fairness_penalty=fairness_penalty,
        decision_log_record=decision_log_record,
        decision_log_summary=decision_log_summary,
        path_records=path_records,
    )
    decision_log_record = _sync_decision_log_with_roadmap_summary(
        decision_log_record,
        roadmap=artifact_bundle.roadmap,
    )
    decision_log_summary = build_decision_logging_summary([decision_log_record])
    return CustomerRecourseRunResult(
        bundle=artifact_bundle,
        local_reason_bundle=local_reason_bundle,
        adverse_action_reasons=adverse_action_reasons,
        dice_df=dice_df,
        dice_records=dice_records,
        dice_backend=dice_backend,
        dice_telemetry=dice_telemetry,
        candidate_pool_df=candidate_pool_df,
        decision_log_record=decision_log_record,
        decision_log_summary=decision_log_summary,
    )
if __name__ == "__main__":
    main()
