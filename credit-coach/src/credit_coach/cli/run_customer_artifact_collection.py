from __future__ import annotations

import argparse
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from credit_coach.causality.graph_utils import load_graph
from credit_coach.causality.rex_runner import run_rex_adapter
from credit_coach.cli.run_batch_recourse_eval import (
    _load_batch_input_frame,
    _resolve_repo_path,
    _risk_band_from_pd,
)
from credit_coach.cli.run_recourse import (
    CustomerArtifactBundle,
    CustomerRecourseRunResult,
    FLOAT_PARITY_TOLERANCE,
    _apply_decision_ownership_to_roadmap,
    _merge_dict,
    _normalize_customer_roadmap_contract,
    _safe_text,
    _sync_metrics_summary_with_roadmap_summary,
    generate_customer_recourse_artifacts,
    write_customer_artifact_bundle,
)
from credit_coach.data.ingest import load_feature_contract
from credit_coach.evaluation.decision_calibration import (
    build_calibration_review_markdown,
    build_funnel_summary,
    build_policy_comparison,
    build_readiness_distribution,
    build_selection_work_frame,
    build_status_by_readiness,
    prepare_metrics_for_calibration,
    rebalance_offer_needed_selection,
    select_initial_cohort,
    summarize_readiness,
)
from credit_coach.model.predict import predict_proba_pd
from credit_coach.model.registry import load_model_bundle
from credit_coach.ops.operator_review import (
    build_collection_operator_briefing,
    build_operator_review_packet,
    operator_packet_metrics_fields,
    render_collection_operator_briefing_markdown,
    write_operator_review_packet,
)
from credit_coach.utils.hashing import hash_config
from credit_coach.utils.run_context import create_run_context, load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_customer_artifact_collection")
_CANDIDATE_SOURCE_CATALOG: tuple[str, ...] = ("internal", "dice", "rule", "fallback")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect single-customer recourse artifacts for a deterministic cohort")
    parser.add_argument("--base_config", type=str, default="configs/default.yaml")
    parser.add_argument("--model_config", type=str, default="configs/model.yaml")
    parser.add_argument("--recourse_config", type=str, default="configs/recourse.yaml")
    parser.add_argument("--causality_config", type=str, default="configs/causality.yaml")
    parser.add_argument("--safety_config", type=str, default="configs/safety.yaml")
    parser.add_argument("--macro_config", type=str, default="configs/macro.yaml")
    parser.add_argument("--n_customers", type=int, default=50)
    parser.add_argument("--sample_seed", type=int, default=42)
    parser.add_argument("--n_workers", type=int, default=1)
    parser.add_argument("--input_data_path", type=str, default="")
    parser.add_argument("--input_data_format", type=str, default="parquet")
    parser.add_argument(
        "--cohort_policy",
        type=str,
        default="denied_first_near",
        choices=(
            "pilot_mixed",
            "risk_band_balanced",
            "ops_queue_replay",
            "offer_needed_balanced",
            "denied_first_near",
            "union_denied_near",
            "denied_only",
            "random_mixed",
        ),
    )
    parser.add_argument("--model_version", type=str, default="")
    parser.add_argument("--model_manifest", type=str, default="")
    parser.add_argument("--artifact_root", type=str, default="artifacts/runs")
    return parser.parse_args(argv)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _json_dumps_compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _normalized_roadmap_summary(bundle: CustomerArtifactBundle) -> dict[str, Any]:
    bundle.roadmap = _normalize_customer_roadmap_contract(bundle.roadmap)
    bundle.roadmap = _apply_decision_ownership_to_roadmap(bundle.roadmap)
    bundle.metrics_summary = _sync_metrics_summary_with_roadmap_summary(bundle.metrics_summary, roadmap=bundle.roadmap)
    return dict(bundle.roadmap.get("summary", {}) or {})


def _is_close_contract_value(left: Any, right: Any) -> bool:
    try:
        if left is None or right is None:
            return left is right
        if isinstance(left, bool) or isinstance(right, bool):
            return bool(left) == bool(right)
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return abs(float(left) - float(right)) <= FLOAT_PARITY_TOLERANCE
    except Exception:
        return False
    return left == right


def _apply_collection_parity_classification(
    bundle: CustomerArtifactBundle,
    *,
    mismatch_fields: list[str],
) -> None:
    summary = _normalized_roadmap_summary(bundle)
    parity_pass = int(not mismatch_fields)
    parity_mismatch_fields = sorted(set(str(field) for field in mismatch_fields if str(field)))
    data_issue_codes = list(summary.get("data_issue_codes", []))
    if mismatch_fields and "parity_mismatch" not in data_issue_codes:
        data_issue_codes.append("parity_mismatch")
    data_issue_flag = int(bool(_safe_int(summary.get("data_issue_flag", 0), 0)) or bool(mismatch_fields))
    bundle.roadmap["summary"].update(
        {
            "parity_pass": parity_pass,
            "data_issue_flag": data_issue_flag,
            "data_issue_codes": data_issue_codes,
            "parity_mismatch_count": len(parity_mismatch_fields),
            "parity_mismatch_fields": parity_mismatch_fields,
            "parity_mismatch_fields_json": _json_dumps_compact(parity_mismatch_fields),
        }
    )
    bundle.roadmap = _normalize_customer_roadmap_contract(bundle.roadmap)
    bundle.roadmap = _apply_decision_ownership_to_roadmap(bundle.roadmap)
    bundle.metrics_summary = _sync_metrics_summary_with_roadmap_summary(bundle.metrics_summary, roadmap=bundle.roadmap)


def _validate_customer_artifact_parity(
    *,
    bundle: CustomerArtifactBundle,
    metrics_row: dict[str, Any],
    plans_df: pd.DataFrame,
    steps_df: pd.DataFrame,
) -> dict[str, Any]:
    summary = _normalized_roadmap_summary(bundle)
    metrics_summary = dict(bundle.metrics_summary)
    mismatch_fields: list[str] = []
    field_names = (
        "customer_id",
        "best_plan_id",
        "best_plan_source",
        "decision_status",
        "decision_status_internal",
        "credit_readiness_stage",
        "plan_execution_probability",
        "approval_dependent_plan_probability",
        "offer_acceptance_probability",
        "combined_plan_realization_probability",
        "best_action_count",
        "zero_step_flag",
        "checkpoint_status_4w",
        "checkpoint_status_12w",
        "checkpoint_status_24w",
        "raw_contract_pass",
        "parity_pass",
        "data_issue_flag",
    )
    source_pairs = {
        "customer_id": bundle.customer_id,
        "best_plan_id": _safe_text(bundle.roadmap.get("best_plan_id")),
        "best_plan_source": _safe_text(bundle.roadmap.get("best_plan_source")),
        **{field: summary.get(field) for field in field_names if field in summary},
    }
    for field in field_names:
        expected = source_pairs.get(field, metrics_summary.get(field))
        actual = metrics_row.get(field)
        if not _is_close_contract_value(expected, actual):
            mismatch_fields.append(field)
    if int(_safe_int(summary.get("best_action_count", 0), 0)) != int(len(steps_df)):
        mismatch_fields.append("best_action_count_vs_steps")
    selected_best = plans_df.loc[plans_df.get("selected_best_flag", pd.Series(dtype=int)).fillna(0).astype(int) == 1]
    if selected_best.empty:
        mismatch_fields.append("selected_best_plan")
    return {
        "parity_pass": int(not mismatch_fields),
        "parity_mismatch_count": len(mismatch_fields),
        "parity_mismatch_fields": sorted(set(mismatch_fields)),
        "parity_mismatch_fields_json": _json_dumps_compact(sorted(set(mismatch_fields))),
    }


def _path_safe_customer_id(customer_id: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", str(customer_id).strip())
    return cleaned.strip("._") or "customer"


def _cohort_customer_id(row: pd.Series, *, fallback: str) -> str:
    raw = str(row.get("customer_id", "") or "").strip()
    return raw or fallback


def _resolve_train_path(*, test_path: Path, processed_root: Path) -> Path:
    candidates = [
        test_path.parent / "train.parquet",
        test_path.parent / "train.csv",
        processed_root / "train.parquet",
        processed_root / "train.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _selection_frame(
    *,
    input_df: pd.DataFrame,
    base_pd: pd.Series,
    tau: float,
    n_customers: int,
    sample_seed: int,
    cohort_policy: str,
    segment_caps_cfg: dict[str, Any],
) -> pd.DataFrame:
    work = build_selection_work_frame(
        input_df=input_df,
        base_pd=base_pd,
        tau=tau,
        risk_band_fn=_risk_band_from_pd,
        segment_caps_cfg=segment_caps_cfg,
        customer_id_getter=_cohort_customer_id,
    )
    selected = select_initial_cohort(
        work=work,
        requested_n=max(1, int(n_customers)),
        sample_seed=int(sample_seed),
        cohort_policy=str(cohort_policy),
    ).selected
    return selected[
        [
            "batch_index",
            "_frame_position",
            "source_row_index",
            "customer_id",
            "base_pd",
            "denied_base",
            "risk_band",
            "selection_reason",
            "cohort_policy",
            "cohort_bucket",
            "selection_policy_name",
            "selection_fill_behavior",
        ]
    ].copy()


def _augment_metrics_row(
    *,
    collection_run_id: str,
    selection_row: pd.Series,
    result: CustomerRecourseRunResult,
) -> dict[str, Any]:
    roadmap_summary = _normalized_roadmap_summary(result.bundle)
    best_cost = float(pd.to_numeric(result.bundle.roadmap_steps_df.get("estimated_cost_usd", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum())
    metrics = dict(result.bundle.metrics_summary)
    candidate_pool_df = result.candidate_pool_df.copy()
    if "plan_source" in candidate_pool_df.columns:
        source_counts = candidate_pool_df["plan_source"].astype(str).value_counts().to_dict()
    else:
        source_counts = {}
    candidate_count = int(metrics.get("candidate_pool_count", len(candidate_pool_df)))
    if "contender_bucket" in candidate_pool_df.columns:
        contender_bucket = candidate_pool_df["contender_bucket"].astype(str).str.upper()
        non_empty_count = int((contender_bucket != "EMPTY").sum())
        approval_shell_only_count = int((contender_bucket == "APPROVAL_SHELL_ONLY").sum())
        empty_removed_count = int((contender_bucket == "EMPTY").sum())
    else:
        non_empty_count = int(metrics.get("candidate_non_empty_count", candidate_count))
        approval_shell_only_count = int(metrics.get("candidate_approval_shell_only_count", 0))
        empty_removed_count = int(metrics.get("candidate_empty_removed_count", 0))
    metrics.update(
        {
            "collection_run_id": str(collection_run_id),
            "batch_index": int(selection_row["batch_index"]),
            "source_row_index": int(selection_row["source_row_index"]),
            "selection_reason": str(selection_row["selection_reason"]),
            "cohort_policy": str(selection_row["cohort_policy"]),
            "denied_base": int(selection_row["denied_base"]),
            "cohort_bucket": str(selection_row.get("cohort_bucket", "")),
            "selection_policy_name": str(selection_row.get("selection_policy_name", selection_row["cohort_policy"])),
            "selection_fill_behavior": str(selection_row.get("selection_fill_behavior", "")),
            "best_action_count": int(_safe_int(roadmap_summary.get("best_action_count", 0), 0)),
            "best_cost_usd": best_cost,
            "best_plan_execution_probability": _safe_float(roadmap_summary.get("plan_execution_probability"), 0.0),
            "best_combined_plan_realization_probability": _safe_float(
                roadmap_summary.get("combined_plan_realization_probability"),
                0.0,
            ),
            "best_contender_bucket": str(metrics.get("best_contender_bucket", "") or ""),
            "best_offer_maturity": str(metrics.get("best_offer_maturity", roadmap_summary.get("offer_maturity", "none")) or "none"),
            "candidate_pool_diversity_index": _safe_float(metrics.get("candidate_pool_diversity_index", 0.0), 0.0),
            "candidate_source_entropy": _safe_float(metrics.get("candidate_source_entropy", 0.0), 0.0),
            "candidate_non_empty_count": non_empty_count,
            "candidate_approval_shell_only_count": approval_shell_only_count,
            "candidate_empty_removed_count": empty_removed_count,
            "recommendation_validity_status": str(metrics.get("recommendation_validity_status", roadmap_summary.get("recommendation_validity_status", "valid"))),
            "recommendation_invalid_action_count": int(_safe_int(metrics.get("recommendation_invalid_action_count", roadmap_summary.get("recommendation_invalid_action_count", 0)), 0)),
            "recommendation_warning_action_count": int(_safe_int(metrics.get("recommendation_warning_action_count", roadmap_summary.get("recommendation_warning_action_count", 0)), 0)),
            "recommendation_sanity_flag": int(_safe_int(metrics.get("recommendation_sanity_flag", roadmap_summary.get("recommendation_sanity_flag", 0)), 0)),
            "offer_ready_contender_share": _safe_float(metrics.get("offer_ready_contender_share", 0.0), 0.0),
            "provisional_offer_share": _safe_float(metrics.get("provisional_offer_share", 0.0), 0.0),
            "approval_shell_only_share": _safe_float(metrics.get("approval_shell_only_share", 0.0), 0.0),
            "hard_invalid_plan_rate": _safe_float(metrics.get("hard_invalid_plan_rate", 0.0), 0.0),
            "numeric_warning_rate": _safe_float(metrics.get("numeric_warning_rate", 0.0), 0.0),
            "best_plan_warning_rate": _safe_float(metrics.get("best_plan_warning_rate", 0.0), 0.0),
            "directional_invalid_count": int(_safe_int(metrics.get("directional_invalid_count", 0), 0)),
            "economic_warning_count": int(_safe_int(metrics.get("economic_warning_count", 0), 0)),
            "data_issue_codes_json": _json_dumps_compact(list(roadmap_summary.get("data_issue_codes", []))),
            "offer_needed_flag": "offer_needed"
            if (
                int(_safe_int(roadmap_summary.get("offer_plan", 0), 0)) == 1
                or _safe_text(roadmap_summary.get("offer_maturity"), "none").lower() != "none"
                or _safe_float(roadmap_summary.get("offer_acceptance_probability"), 0.0) > 0.0
            )
            else "no_offer_needed",
        }
    )
    for source in _CANDIDATE_SOURCE_CATALOG:
        metrics[f"candidate_source_{source}_count"] = int(metrics.get(f"candidate_source_{source}_count", source_counts.get(source, 0)))
        metrics[f"candidate_source_{source}_present"] = int(
            metrics.get(f"candidate_source_{source}_present", int(source_counts.get(source, 0) > 0))
        )
    return metrics


def _augment_plans_df(
    *,
    collection_run_id: str,
    selection_row: pd.Series,
    plans_df: pd.DataFrame,
    bundle: CustomerArtifactBundle,
) -> pd.DataFrame:
    summary = _normalized_roadmap_summary(bundle)
    out = plans_df.copy()
    if "plan_source" not in out.columns:
        out["plan_source"] = ""
    if "contender_bucket" not in out.columns:
        out["contender_bucket"] = ""
    if "empty_candidate_reason" not in out.columns:
        out["empty_candidate_reason"] = ""
    if "approval_shell_only_flag" not in out.columns:
        out["approval_shell_only_flag"] = 0
    if "offer_maturity" not in out.columns:
        out["offer_maturity"] = "none"
    if "recommendation_validity_status" not in out.columns:
        out["recommendation_validity_status"] = "valid"
    if "recommendation_validity_codes_json" not in out.columns:
        out["recommendation_validity_codes_json"] = "[]"
    if "recommendation_sanity_flag" not in out.columns:
        out["recommendation_sanity_flag"] = 0
    if "plan_stage" not in out.columns:
        out["plan_stage"] = "validated"
    out.insert(0, "collection_run_id", str(collection_run_id))
    out.insert(1, "batch_index", int(selection_row["batch_index"]))
    out.insert(2, "source_row_index", int(selection_row["source_row_index"]))
    out.insert(3, "customer_id", str(selection_row["customer_id"]))
    out.insert(4, "selection_reason", str(selection_row["selection_reason"]))
    out.insert(5, "cohort_policy", str(selection_row["cohort_policy"]))
    out.insert(6, "cohort_bucket", str(selection_row.get("cohort_bucket", "")))
    out.insert(7, "selection_policy_name", str(selection_row.get("selection_policy_name", selection_row["cohort_policy"])))
    out.insert(8, "selection_fill_behavior", str(selection_row.get("selection_fill_behavior", "")))
    out.insert(9, "selected_best_flag", (out.get("plan_id", pd.Series(dtype=object)).astype(str) == _safe_text(bundle.roadmap.get("best_plan_id"))).astype(int))
    if "action_count" in out.columns:
        out.insert(10, "plan_step_count", pd.to_numeric(out["action_count"], errors="coerce").fillna(0).astype(int))
    else:
        out.insert(10, "plan_step_count", 0)
    plan_contract_pass = pd.Series([pd.NA] * len(out), index=out.index, dtype="object")
    selected_mask = out["selected_best_flag"].astype(int) == 1
    plan_contract_pass.loc[selected_mask] = int(_safe_int(summary.get("plan_contract_pass", 0), 0))
    out.insert(11, "plan_contract_pass", plan_contract_pass)
    return out


def _augment_steps_df(
    *,
    collection_run_id: str,
    selection_row: pd.Series,
    steps_df: pd.DataFrame,
) -> pd.DataFrame:
    out = steps_df.copy()
    if "recommendation_validity_status" not in out.columns:
        out["recommendation_validity_status"] = "valid"
    if "recommendation_validity_codes_json" not in out.columns:
        out["recommendation_validity_codes_json"] = "[]"
    if "recommendation_sanity_flag" not in out.columns:
        out["recommendation_sanity_flag"] = 0
    out.insert(0, "collection_run_id", str(collection_run_id))
    out.insert(1, "batch_index", int(selection_row["batch_index"]))
    out.insert(2, "source_row_index", int(selection_row["source_row_index"]))
    out.insert(3, "selection_reason", str(selection_row["selection_reason"]))
    out.insert(4, "cohort_policy", str(selection_row["cohort_policy"]))
    out.insert(5, "cohort_bucket", str(selection_row.get("cohort_bucket", "")))
    out.insert(6, "selection_policy_name", str(selection_row.get("selection_policy_name", selection_row["cohort_policy"])))
    out.insert(7, "selection_fill_behavior", str(selection_row.get("selection_fill_behavior", "")))
    return out


def _top_constraint_reason(steps_df: pd.DataFrame) -> str:
    if steps_df.empty or "constraint_reason_codes_json" not in steps_df.columns:
        return ""
    counts: dict[str, int] = {}
    for raw in steps_df["constraint_reason_codes_json"].fillna("[]").astype(str):
        try:
            values = json.loads(raw)
        except Exception:
            values = []
        for value in values if isinstance(values, list) else []:
            key = str(value).strip()
            if key:
                counts[key] = counts.get(key, 0) + 1
    if not counts:
        return ""
    return max(counts.items(), key=lambda item: (item[1], item[0]))[0]


def _collection_summary_markdown(
    *,
    selection_df: pd.DataFrame,
    metrics_df: pd.DataFrame,
    steps_df: pd.DataFrame,
    manifest_rel_root: str,
    selection_metadata: Mapping[str, Any],
    funnel_summary: Mapping[str, Any],
    readiness_summary: Mapping[str, Any],
    calibration_summary: Mapping[str, Any],
    operator_briefing: Mapping[str, Any],
) -> str:
    decision_status_counts = (
        metrics_df.get("decision_status", metrics_df.get("best_status", pd.Series(dtype=object)))
        .astype(str)
        .value_counts()
        .sort_index()
        .to_dict()
    )
    risk_band_counts = (
        selection_df.get("risk_band", pd.Series(dtype=object))
        .astype(str)
        .value_counts()
        .sort_index()
        .to_dict()
    )
    top_action_key = ""
    top_action_family = ""
    if not steps_df.empty:
        top_action_key = (
            steps_df.get("action_key", pd.Series(dtype=object)).astype(str).value_counts().idxmax()
            if not steps_df.get("action_key", pd.Series(dtype=object)).empty
            else ""
        )
        top_action_family = (
            steps_df.get("action_class", pd.Series(dtype=object)).astype(str).value_counts().idxmax()
            if not steps_df.get("action_class", pd.Series(dtype=object)).empty
            else ""
        )
    readiness_distribution = dict(readiness_summary.get("distribution", {}))
    readiness_bits = ", ".join(
        [
            f"{label}={int(dict(readiness_distribution.get(label, {})).get('count', 0))}"
            for label in ("now", "week_4", "week_12", "week_24", "not_ready", "unknown_review")
        ]
    )
    priority_queues = list(operator_briefing.get("priority_queues", []) or [])
    dominant_blockers = list(operator_briefing.get("dominant_blockers", []) or [])
    conditional_hotspots = list(operator_briefing.get("conditional_hotspots", []) or [])
    offer_hotspots = list(operator_briefing.get("offer_hotspots", []) or [])
    review_guidance = list(operator_briefing.get("review_guidance", []) or [])
    health_note = _safe_text(operator_briefing.get("health_note"))
    priority_queue_summary = ", ".join(
        [f"{_safe_text(queue.get('label'))}={int(queue.get('count', 0))}" for queue in priority_queues]
    ) or "n/a"
    dominant_blocker_summary = ", ".join(
        [f"{_safe_text(item.get('title'))}={int(item.get('count', 0))}" for item in dominant_blockers]
    ) or "n/a"
    conditional_hotspot_summary = ", ".join(
        [f"{_safe_text(item.get('conditional_type'))}={int(item.get('count', 0))}" for item in conditional_hotspots]
    ) or "n/a"
    offer_hotspot_summary = ", ".join(
        [
            f"{_safe_text(item.get('offer_needed_flag'))}/{_safe_text(item.get('decision_status'))}={int(item.get('count', 0))}"
            for item in offer_hotspots
        ]
    ) or "n/a"
    review_guidance_summary = " | ".join([_safe_text(item) for item in review_guidance]) or "n/a"
    best_source_counts = (
        metrics_df.get("best_plan_source", pd.Series(dtype=object)).astype(str).value_counts().sort_index().to_dict()
    )
    mean_source_entropy = _safe_float(metrics_df.get("candidate_source_entropy", pd.Series(dtype=float)).mean(), 0.0)
    mean_pool_diversity = _safe_float(metrics_df.get("candidate_pool_diversity_index", pd.Series(dtype=float)).mean(), 0.0)
    non_empty_share = _safe_float(
        (
            pd.to_numeric(metrics_df.get("candidate_non_empty_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
            / pd.to_numeric(metrics_df.get("candidate_pool_count", pd.Series(dtype=float)), errors="coerce").replace(0, pd.NA)
        ).fillna(0.0).mean(),
        0.0,
    )
    offer_ready_share = _safe_float(metrics_df.get("offer_ready_contender_share", pd.Series(dtype=float)).mean(), 0.0)
    provisional_offer_share = _safe_float(metrics_df.get("provisional_offer_share", pd.Series(dtype=float)).mean(), 0.0)
    approval_shell_only_share = _safe_float(metrics_df.get("approval_shell_only_share", pd.Series(dtype=float)).mean(), 0.0)
    hard_invalid_plan_rate = _safe_float(metrics_df.get("hard_invalid_plan_rate", pd.Series(dtype=float)).mean(), 0.0)
    numeric_warning_rate = _safe_float(metrics_df.get("numeric_warning_rate", pd.Series(dtype=float)).mean(), 0.0)
    best_plan_warning_rate = _safe_float(metrics_df.get("best_plan_warning_rate", pd.Series(dtype=float)).mean(), 0.0)
    directional_invalid_count = int(pd.to_numeric(metrics_df.get("directional_invalid_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum())
    economic_warning_count = int(pd.to_numeric(metrics_df.get("economic_warning_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum())
    best_action_class_dominance = 0.0
    best_action_family_dominance = 0.0
    if not steps_df.empty and "action_class" in steps_df.columns:
        class_counts = steps_df["action_class"].astype(str).value_counts()
        if not class_counts.empty:
            best_action_class_dominance = float(class_counts.iloc[0] / max(1, int(class_counts.sum())))
    if not steps_df.empty and "action_key" in steps_df.columns:
        family_counts = steps_df["action_key"].astype(str).value_counts()
        if not family_counts.empty:
            best_action_family_dominance = float(family_counts.iloc[0] / max(1, int(family_counts.sum())))
    return "\n".join(
        [
            "# Customer Artifact Collection",
            "",
            f"- Selected customers: {len(selection_df)}",
            f"- Denied-selected: {int(selection_df.get('denied_base', pd.Series(dtype=int)).astype(int).sum())}",
            f"- Near-fill: {int((selection_df.get('selection_reason', pd.Series(dtype=object)) == 'near_fill').sum())}",
            f"- Selection policy: {selection_metadata.get('selection_policy_name', '')}",
            f"- Selection fill behavior: {selection_metadata.get('selection_fill_behavior', '')}",
            f"- Cohort purpose: {selection_metadata.get('cohort_purpose', '')}",
            "",
            "## Portfolio Readout",
            f"- Decision status distribution: {decision_status_counts or '{}'}",
            f"- Risk band distribution: {risk_band_counts or '{}'}",
            f"- Mean best action count: {_safe_float(metrics_df.get('best_action_count', pd.Series(dtype=float)).mean(), 0.0):.2f}",
            f"- Mean best cost USD: {_safe_float(metrics_df.get('best_cost_usd', pd.Series(dtype=float)).mean(), 0.0):.2f}",
            f"- Mean best plan execution probability: {_safe_float(metrics_df.get('best_plan_execution_probability', pd.Series(dtype=float)).mean(), 0.0):.4f}",
            f"- Most frequent action key: {top_action_key or 'n/a'}",
            f"- Most frequent action family: {top_action_family or 'n/a'}",
            f"- Most frequent constraint reason: {_top_constraint_reason(steps_df) or 'n/a'}",
            "",
            "## Decision Funnel",
            f"- Approved share: {_safe_float(funnel_summary.get('approved_share'), 0.0):.4f}",
            f"- Conditional share: {_safe_float(funnel_summary.get('conditional_share'), 0.0):.4f}",
            f"- Rejected share: {_safe_float(funnel_summary.get('rejected_share'), 0.0):.4f}",
            f"- Internal needs-review share: {_safe_float(funnel_summary.get('internal_needs_review_share'), 0.0):.4f}",
            f"- Approve + conditional share: {_safe_float(funnel_summary.get('approve_plus_conditional_share'), 0.0):.4f}",
            f"- Conditional-to-approved potential: {_safe_float(funnel_summary.get('conditional_to_approved_potential'), 0.0):.4f}",
            "",
            "## Readiness",
            f"- Distribution: {readiness_bits or 'n/a'}",
            f"- Baseline readiness story: approved/conditional customers concentrate in {', '.join([label for label in ('now', 'week_4', 'week_12', 'week_24') if int(dict(readiness_distribution.get(label, {})).get('count', 0)) > 0]) or 'n/a'}",
            "",
            "## Contract Health",
            f"- Critical field null rate: {_safe_float(metrics_df.get('critical_field_null_count', pd.Series(dtype=float)).gt(0).mean(), 0.0):.4f}",
            f"- Missing checkpoint status rate: {_safe_float(metrics_df.get('missing_checkpoint_status_count', pd.Series(dtype=float)).gt(0).mean(), 0.0):.4f}",
            f"- Raw contract pass rate: {_safe_float(metrics_df.get('raw_contract_pass', pd.Series(dtype=float)).mean(), 0.0):.4f}",
            f"- Parity mismatch count: {int((metrics_df.get('parity_pass', pd.Series(dtype=float)).fillna(0).astype(int) == 0).sum())}",
            f"- Data issue count: {int(metrics_df.get('data_issue_flag', pd.Series(dtype=float)).fillna(0).astype(int).sum())}",
            "",
            "## Calibration",
            f"- Policy version evaluated: {calibration_summary.get('policy_version_evaluated', '')}",
            f"- Candidate policies compared: {', '.join(calibration_summary.get('candidate_policy_versions_compared', []) or []) or 'n/a'}",
            f"- Baseline north-star pass: {bool(dict(calibration_summary.get('baseline_policy_metrics', {})).get('north_star_pass', False))}",
            f"- Baseline false-positive proxy: {_safe_float(dict(calibration_summary.get('baseline_policy_metrics', {})).get('false_positive_proxy'), 0.0):.4f}",
            "",
            "## Planner Source Mix",
            f"- Best-plan source distribution: {best_source_counts or '{}'}",
            f"- Mean candidate source entropy: {mean_source_entropy:.4f}",
            f"- Mean candidate pool diversity index: {mean_pool_diversity:.4f}",
            f"- Internal vs dice competitiveness: internal={_safe_float((metrics_df.get('best_plan_source', pd.Series(dtype=object)).astype(str) == 'internal').mean(), 0.0):.4f}, dice={_safe_float((metrics_df.get('best_plan_source', pd.Series(dtype=object)).astype(str) == 'dice').mean(), 0.0):.4f}",
            f"- Recovery lanes: rule={_safe_float((metrics_df.get('best_plan_source', pd.Series(dtype=object)).astype(str) == 'rule').mean(), 0.0):.4f}, fallback={_safe_float((metrics_df.get('best_plan_source', pd.Series(dtype=object)).astype(str) == 'fallback').mean(), 0.0):.4f}",
            "",
            "## Planner Quality",
            f"- Non-empty contender share: {non_empty_share:.4f}",
            f"- Hard-invalid plan rate: {hard_invalid_plan_rate:.4f}",
            f"- Numeric warning rate: {numeric_warning_rate:.4f}",
            f"- Best-plan warning rate: {best_plan_warning_rate:.4f}",
            f"- Directional invalid count: {directional_invalid_count}",
            f"- Economic warning count: {economic_warning_count}",
            f"- Offer-ready contender share: {offer_ready_share:.4f}",
            f"- Provisional offer share: {provisional_offer_share:.4f}",
            f"- Approval-shell-only share: {approval_shell_only_share:.4f}",
            f"- Best action-class dominance: {best_action_class_dominance:.4f}",
            f"- Best action-family dominance: {best_action_family_dominance:.4f}",
            "",
            "## Operator Review",
            f"- Likely-to-upgrade-soon queue: {int(next((queue.get('count', 0) for queue in priority_queues if str(queue.get('queue_key')) == 'likely_to_upgrade_soon'), 0))}",
            f"- Priority queues: {priority_queue_summary}",
            f"- Dominant blockers: {dominant_blocker_summary}",
            f"- Conditional hotspots: {conditional_hotspot_summary}",
            f"- Offer hotspots: {offer_hotspot_summary}",
            f"- Review guidance: {review_guidance_summary}",
            f"- Health note: {health_note or 'n/a'}",
            "",
            "## Review Files",
            f"- Metrics: `{manifest_rel_root}/flat/customer_metrics.csv`",
            f"- Plans: `{manifest_rel_root}/flat/customer_plans.csv`",
            f"- Roadmap steps: `{manifest_rel_root}/flat/customer_roadmap_steps.csv`",
            f"- Selection: `{manifest_rel_root}/flat/customer_selection.csv`",
            f"- Funnel summary: `{manifest_rel_root}/calibration/funnel_summary.json`",
            f"- Policy comparison: `{manifest_rel_root}/calibration/policy_comparison.csv`",
            f"- Calibration review: `{manifest_rel_root}/calibration/calibration_review.md`",
            f"- Operator briefing: `{manifest_rel_root}/operator_review_briefing.md`",
            f"- Operator packets: `{manifest_rel_root}/operator_packets/`",
        ]
    ) + "\n"


def main(argv: Sequence[str] | None = None):
    args = parse_args(argv)
    project_root = Path(__file__).resolve().parents[3]
    base_config_path = _resolve_repo_path(args.base_config, project_root=project_root)
    model_config_path = _resolve_repo_path(args.model_config, project_root=project_root)
    recourse_config_path = _resolve_repo_path(args.recourse_config, project_root=project_root)
    causality_config_path = _resolve_repo_path(args.causality_config, project_root=project_root)
    safety_config_path = _resolve_repo_path(args.safety_config, project_root=project_root)
    macro_config_path = _resolve_repo_path(args.macro_config, project_root=project_root)

    base_cfg = load_config(base_config_path)
    model_cfg = load_config(model_config_path)
    rec_cfg = load_config(recourse_config_path)
    c_cfg = load_config(causality_config_path)
    s_cfg = load_config(safety_config_path)
    m_cfg = load_config(macro_config_path)
    cfg = _merge_dict(
        _merge_dict(_merge_dict(_merge_dict(base_cfg, model_cfg), rec_cfg), _merge_dict(c_cfg, s_cfg)),
        {
            "macro": m_cfg,
            "collection": {
                "n_customers": int(args.n_customers),
                "sample_seed": int(args.sample_seed),
                "n_workers": int(args.n_workers),
                "cohort_policy": str(args.cohort_policy),
            },
        },
    )
    run_ctx = create_run_context(cfg, base_artifact_dir=args.artifact_root)

    features_config_path = _resolve_repo_path(
        base_cfg.get("features_config", "configs/features_48.yaml"),
        project_root=project_root,
    )
    contract = load_feature_contract(features_config_path)
    feature_cols = contract["features"]
    target_col = contract["target"]

    processed_root = Path(base_cfg.get("paths", {}).get("processed_data", "data/processed"))
    if not processed_root.is_absolute():
        processed_root = (base_config_path.parent.parent / processed_root).resolve()
    test_path = Path(str(args.input_data_path).strip()) if str(args.input_data_path).strip() else processed_root / "test.parquet"
    train_path = _resolve_train_path(test_path=test_path, processed_root=processed_root)
    test_df = _load_batch_input_frame(test_path, data_format=str(args.input_data_format).strip() or "parquet")
    train_df = _load_batch_input_frame(train_path, data_format=train_path.suffix.lstrip(".") or "parquet")

    model, calibrator, manifest, _ = load_model_bundle(
        base_path=model_cfg.get("registry", {}).get("path", "artifacts/models"),
        model_version=str(args.model_version).strip() or None,
        manifest_path=str(args.model_manifest).strip() or None,
    )
    tau = float(model_cfg.get("decision", {}).get("tau_0", 0.35))
    base_proba = pd.Series(predict_proba_pd(model, calibrator, test_df[feature_cols]), dtype=float)
    segment_caps_cfg = rec_cfg.get("segment_caps", {}) if isinstance(rec_cfg.get("segment_caps", {}), dict) else {}
    selection_work = build_selection_work_frame(
        input_df=test_df,
        base_pd=base_proba,
        tau=tau,
        risk_band_fn=_risk_band_from_pd,
        segment_caps_cfg=segment_caps_cfg,
        customer_id_getter=_cohort_customer_id,
    )
    selection_result = select_initial_cohort(
        work=selection_work,
        requested_n=max(1, int(args.n_customers)),
        sample_seed=int(args.sample_seed),
        cohort_policy=str(args.cohort_policy),
    )
    selection_df = selection_result.selected.copy()
    selection_metadata = dict(selection_result.metadata)

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

    collection_root = run_ctx.tables_dir / "customer_artifact_collection"
    raw_root = collection_root / "raw"
    flat_root = collection_root / "flat"
    calibration_root = collection_root / "calibration"
    operator_root = collection_root / "operator_packets"
    rel_root = "tables/customer_artifact_collection"
    raw_root.mkdir(parents=True, exist_ok=True)
    flat_root.mkdir(parents=True, exist_ok=True)
    calibration_root.mkdir(parents=True, exist_ok=True)
    operator_root.mkdir(parents=True, exist_ok=True)

    def _process_selection(selection_row: pd.Series) -> dict[str, Any]:
        frame_position = int(selection_row["_frame_position"])
        row = test_df.iloc[frame_position]
        result = generate_customer_recourse_artifacts(
            customer_id=str(selection_row["customer_id"]),
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
            persist_repository_records=False,
        )
        _normalized_roadmap_summary(result.bundle)
        return {
            "selection": dict(selection_row),
            "result": result,
        }

    rows = [row for _, row in selection_df.iterrows()]
    processed_records: list[dict[str, Any]] = []
    n_workers = max(1, int(args.n_workers))
    if n_workers == 1:
        for selection_row in rows:
            processed_records.append(_process_selection(selection_row))
    else:
        with ThreadPoolExecutor(max_workers=n_workers) as executor:
            futures = {executor.submit(_process_selection, selection_row): selection_row for selection_row in rows}
            for future in as_completed(futures):
                processed_records.append(future.result())

    if str(args.cohort_policy) == "offer_needed_balanced":
        pre_metrics_rows: list[dict[str, Any]] = []
        for record in processed_records:
            selection_row = pd.Series(record["selection"])
            summary = _normalized_roadmap_summary(record["result"].bundle)
            pre_metrics_rows.append(
                {
                    "source_row_index": int(selection_row["source_row_index"]),
                    "customer_id": str(selection_row["customer_id"]),
                    "offer_needed_flag": "offer_needed"
                    if (
                        int(_safe_int(summary.get("offer_plan", 0), 0)) == 1
                        or _safe_text(summary.get("offer_maturity"), "none").lower() != "none"
                        or _safe_float(summary.get("offer_acceptance_probability"), 0.0) > 0.0
                    )
                    else "no_offer_needed",
                }
            )
        selection_df, rebalance_metadata = rebalance_offer_needed_selection(
            selection_df=selection_df,
            metrics_df=pd.DataFrame(pre_metrics_rows),
            requested_n=max(1, int(args.n_customers)),
            sample_seed=int(args.sample_seed),
        )
        selection_metadata.update(rebalance_metadata)

    record_lookup = {
        (int(record["selection"]["source_row_index"]), str(record["selection"]["customer_id"])): record["result"]
        for record in processed_records
    }
    metrics_rows: list[dict[str, Any]] = []
    plan_frames: list[pd.DataFrame] = []
    step_frames: list[pd.DataFrame] = []
    operator_packet_records: list[dict[str, Any]] = []
    for _, selection_row in selection_df.sort_values(["batch_index", "customer_id"]).iterrows():
        result = record_lookup[(int(selection_row["source_row_index"]), str(selection_row["customer_id"]))]
        metrics_row = _augment_metrics_row(
            collection_run_id=run_ctx.run_id,
            selection_row=selection_row,
            result=result,
        )
        plans_df = _augment_plans_df(
            collection_run_id=run_ctx.run_id,
            selection_row=selection_row,
            plans_df=result.bundle.plans_df,
            bundle=result.bundle,
        )
        steps_df = _augment_steps_df(
            collection_run_id=run_ctx.run_id,
            selection_row=selection_row,
            steps_df=result.bundle.roadmap_steps_df,
        )
        parity = _validate_customer_artifact_parity(
            bundle=result.bundle,
            metrics_row=metrics_row,
            plans_df=plans_df,
            steps_df=steps_df,
        )
        _apply_collection_parity_classification(
            result.bundle,
            mismatch_fields=list(parity.get("parity_mismatch_fields", [])),
        )
        metrics_row = _augment_metrics_row(
            collection_run_id=run_ctx.run_id,
            selection_row=selection_row,
            result=result,
        )
        plans_df = _augment_plans_df(
            collection_run_id=run_ctx.run_id,
            selection_row=selection_row,
            plans_df=result.bundle.plans_df,
            bundle=result.bundle,
        )
        parity = _validate_customer_artifact_parity(
            bundle=result.bundle,
            metrics_row=metrics_row,
            plans_df=plans_df,
            steps_df=steps_df,
        )
        metrics_row.update(parity)
        result.bundle.metrics_summary.update(parity)
        result.bundle.roadmap["summary"].update(parity)
        result.bundle.roadmap = _normalize_customer_roadmap_contract(result.bundle.roadmap)
        result.bundle.metrics_summary = _sync_metrics_summary_with_roadmap_summary(
            result.bundle.metrics_summary,
            roadmap=result.bundle.roadmap,
        )
        metrics_row = _augment_metrics_row(
            collection_run_id=run_ctx.run_id,
            selection_row=selection_row,
            result=result,
        )
        metrics_row.update(parity)
        raw_dir = raw_root / f"{int(selection_row['batch_index']):03d}_{_path_safe_customer_id(str(selection_row['customer_id']))}"
        write_customer_artifact_bundle(result.bundle, raw_dir)
        packet = build_operator_review_packet(result.bundle.roadmap)
        operator_dir = operator_root / f"{int(selection_row['batch_index']):03d}_{_path_safe_customer_id(str(selection_row['customer_id']))}"
        packet_paths = write_operator_review_packet(packet, operator_dir)
        packet_relpath = f"{rel_root}/operator_packets/{operator_dir.name}/operator_packet.json"
        metrics_row.update(operator_packet_metrics_fields(packet, packet_relpath=packet_relpath))
        operator_packet_records.append(
            {
                "customer_id": packet.customer_id,
                "batch_index": int(selection_row["batch_index"]),
                "packet_relpath": packet_relpath,
                "packet": packet.model_dump(mode="json"),
                "markdown_relpath": f"{rel_root}/operator_packets/{operator_dir.name}/operator_packet.md",
                "written_files": {name: str(path) for name, path in packet_paths.items()},
            }
        )
        metrics_rows.append(metrics_row)
        plan_frames.append(plans_df)
        step_frames.append(steps_df)

    metrics_df = pd.DataFrame(metrics_rows).sort_values(["batch_index", "customer_id"]).reset_index(drop=True)
    customer_plans_df = (
        pd.concat(plan_frames, ignore_index=True)
        if plan_frames
        else pd.DataFrame(columns=["collection_run_id", "batch_index", "source_row_index", "customer_id", "plan_id"])
    )
    customer_steps_df = (
        pd.concat(step_frames, ignore_index=True)
        if step_frames
        else pd.DataFrame(columns=["collection_run_id", "batch_index", "source_row_index", "customer_id"])
    )
    selection_out = selection_df.drop(columns=["_frame_position"]).copy()
    selection_out.insert(0, "collection_run_id", run_ctx.run_id)
    selection_out = selection_out.merge(
        metrics_df[["source_row_index", "customer_id", "offer_needed_flag"]].drop_duplicates(),
        on=["source_row_index", "customer_id"],
        how="left",
    )

    metrics_csv = flat_root / "customer_metrics.csv"
    plans_csv = flat_root / "customer_plans.csv"
    steps_csv = flat_root / "customer_roadmap_steps.csv"
    selection_csv = flat_root / "customer_selection.csv"
    metrics_df.to_csv(metrics_csv, index=False)
    customer_plans_df.to_csv(plans_csv, index=False)
    customer_steps_df.to_csv(steps_csv, index=False)
    selection_out.to_csv(selection_csv, index=False)

    calibration_input_df = prepare_metrics_for_calibration(metrics_df)
    funnel_summary = build_funnel_summary(calibration_input_df)
    readiness_summary = summarize_readiness(calibration_input_df)
    readiness_distribution_df = build_readiness_distribution(calibration_input_df)
    status_by_readiness_df = build_status_by_readiness(calibration_input_df)
    policy_version_evaluated = (
        metrics_df.get("decision_policy_version", pd.Series(dtype=object)).astype(str).mode().iloc[0]
        if not metrics_df.empty and not metrics_df.get("decision_policy_version", pd.Series(dtype=object)).empty
        else ""
    )
    policy_comparison_payload = build_policy_comparison(
        calibration_input_df,
        policy_version_evaluated=policy_version_evaluated,
    )
    policy_comparison_df = policy_comparison_payload["policy_comparison"]
    decision_shift_matrix_df = policy_comparison_payload["decision_shift_matrix"]
    segment_breakdown_df = policy_comparison_payload["segment_breakdown"]
    calibration_summary = policy_comparison_payload["calibration_summary"]
    operator_briefing = build_collection_operator_briefing(
        metrics_df=metrics_df,
        operator_packets=[record["packet"] for record in operator_packet_records],
        funnel_summary=funnel_summary,
        readiness_summary=readiness_summary,
        segment_breakdown_df=segment_breakdown_df,
    )

    funnel_json = calibration_root / "funnel_summary.json"
    readiness_csv = calibration_root / "readiness_distribution.csv"
    status_by_readiness_csv = calibration_root / "status_by_readiness.csv"
    policy_comparison_csv = calibration_root / "policy_comparison.csv"
    shift_matrix_csv = calibration_root / "decision_shift_matrix.csv"
    segment_breakdown_csv = calibration_root / "segment_breakdown.csv"
    calibration_review_md = calibration_root / "calibration_review.md"
    operator_briefing_md = collection_root / "operator_review_briefing.md"

    funnel_json.write_text(json.dumps(funnel_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    readiness_distribution_df.to_csv(readiness_csv, index=False)
    status_by_readiness_df.to_csv(status_by_readiness_csv, index=False)
    policy_comparison_df.to_csv(policy_comparison_csv, index=False)
    decision_shift_matrix_df.to_csv(shift_matrix_csv, index=False)
    segment_breakdown_df.to_csv(segment_breakdown_csv, index=False)
    calibration_review_md.write_text(
        build_calibration_review_markdown(
            selection_policy_name=str(selection_metadata.get("selection_policy_name", args.cohort_policy)),
            cohort_purpose=str(selection_metadata.get("cohort_purpose", "")),
            funnel_summary=funnel_summary,
            readiness_summary=readiness_summary,
            policy_comparison_df=policy_comparison_df,
        ),
        encoding="utf-8",
    )
    operator_briefing_md.write_text(
        render_collection_operator_briefing_markdown(operator_briefing),
        encoding="utf-8",
    )
    manifest_payload = {
        "collection_run_id": run_ctx.run_id,
        "cohort_policy": str(args.cohort_policy),
        "selection_policy_name": str(selection_metadata.get("selection_policy_name", args.cohort_policy)),
        "selection_fill_behavior": str(selection_metadata.get("selection_fill_behavior", "")),
        "cohort_definition": dict(selection_metadata.get("cohort_definition", {})),
        "cohort_purpose": str(selection_metadata.get("cohort_purpose", "")),
        "requested_n_customers": int(args.n_customers),
        "selected_n_customers": int(len(selection_out)),
        "denied_selected_count": int(selection_out["denied_base"].astype(int).sum()) if not selection_out.empty else 0,
        "near_fill_count": int((selection_out["selection_reason"] == "near_fill").sum()) if not selection_out.empty else 0,
        "input_data_path": str(test_path),
        "model_version": str(manifest.get("model_version", "")),
        "config_hash": hash_config(cfg),
        "policy_version_evaluated": policy_version_evaluated,
        "candidate_policy_versions_compared": list(calibration_summary.get("candidate_policy_versions_compared", [])),
        "raw_root": f"{rel_root}/raw",
        "funnel_summary": funnel_summary,
        "readiness_summary": readiness_summary,
        "calibration_summary": calibration_summary,
        "operator_briefing_summary": operator_briefing,
        "source_mix_summary": {
            "best_source_distribution": metrics_df.get("best_plan_source", pd.Series(dtype=object)).astype(str).value_counts().sort_index().to_dict(),
            "mean_candidate_source_entropy": _safe_float(
                metrics_df.get("candidate_source_entropy", pd.Series(dtype=float)).mean(),
                0.0,
            ),
            "mean_candidate_pool_diversity_index": _safe_float(
                metrics_df.get("candidate_pool_diversity_index", pd.Series(dtype=float)).mean(),
                0.0,
            ),
        },
        "plan_quality_summary": {
            "non_empty_contender_share": _safe_float(
                (
                    pd.to_numeric(metrics_df.get("candidate_non_empty_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
                    / pd.to_numeric(metrics_df.get("candidate_pool_count", pd.Series(dtype=float)), errors="coerce").replace(0, pd.NA)
                ).fillna(0.0).mean(),
                0.0,
            ),
            "hard_invalid_plan_rate": _safe_float(
                metrics_df.get("hard_invalid_plan_rate", pd.Series(dtype=float)).mean(),
                0.0,
            ),
            "numeric_warning_rate": _safe_float(
                metrics_df.get("numeric_warning_rate", pd.Series(dtype=float)).mean(),
                0.0,
            ),
            "best_plan_warning_rate": _safe_float(
                metrics_df.get("best_plan_warning_rate", pd.Series(dtype=float)).mean(),
                0.0,
            ),
            "directional_invalid_count": int(
                pd.to_numeric(metrics_df.get("directional_invalid_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum()
            ),
            "economic_warning_count": int(
                pd.to_numeric(metrics_df.get("economic_warning_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum()
            ),
            "offer_ready_contender_share": _safe_float(
                metrics_df.get("offer_ready_contender_share", pd.Series(dtype=float)).mean(),
                0.0,
            ),
            "provisional_offer_share": _safe_float(
                metrics_df.get("provisional_offer_share", pd.Series(dtype=float)).mean(),
                0.0,
            ),
            "approval_shell_only_share": _safe_float(
                metrics_df.get("approval_shell_only_share", pd.Series(dtype=float)).mean(),
                0.0,
            ),
        },
        "contract_health": {
            "critical_field_null_rate": _safe_float(
                metrics_df.get("critical_field_null_count", pd.Series(dtype=float)).gt(0).mean(),
                0.0,
            ),
            "missing_checkpoint_status_rate": _safe_float(
                metrics_df.get("missing_checkpoint_status_count", pd.Series(dtype=float)).gt(0).mean(),
                0.0,
            ),
            "raw_contract_pass_rate": _safe_float(
                metrics_df.get("raw_contract_pass", pd.Series(dtype=float)).mean(),
                0.0,
            ),
            "raw_flat_mismatch_count": int(
                (metrics_df.get("parity_pass", pd.Series(dtype=float)).fillna(0).astype(int) == 0).sum()
            ),
            "zero_step_rejected_count": int(
                (
                    metrics_df.get("zero_step_flag", pd.Series(dtype=float)).fillna(0).astype(int) == 1
                ).sum()
            ),
            "data_issue_conditional_count": int(
                (
                    (metrics_df.get("data_issue_flag", pd.Series(dtype=float)).fillna(0).astype(int) == 1)
                    & (metrics_df.get("decision_status", pd.Series(dtype=object)).astype(str) == "CONDITIONAL")
                ).sum()
            ),
            "summary_field_completion_rate": _safe_float(
                metrics_df.get("summary_field_completion_rate", pd.Series(dtype=float)).mean(),
                0.0,
            ),
        },
        "flat_files": {
            "customer_metrics_csv": f"{rel_root}/flat/customer_metrics.csv",
            "customer_plans_csv": f"{rel_root}/flat/customer_plans.csv",
            "customer_roadmap_steps_csv": f"{rel_root}/flat/customer_roadmap_steps.csv",
            "customer_selection_csv": f"{rel_root}/flat/customer_selection.csv",
        },
        "calibration_files": {
            "funnel_summary_json": f"{rel_root}/calibration/funnel_summary.json",
            "readiness_distribution_csv": f"{rel_root}/calibration/readiness_distribution.csv",
            "status_by_readiness_csv": f"{rel_root}/calibration/status_by_readiness.csv",
            "policy_comparison_csv": f"{rel_root}/calibration/policy_comparison.csv",
            "decision_shift_matrix_csv": f"{rel_root}/calibration/decision_shift_matrix.csv",
            "segment_breakdown_csv": f"{rel_root}/calibration/segment_breakdown.csv",
            "calibration_review_md": f"{rel_root}/calibration/calibration_review.md",
        },
        "operator_files": {
            "operator_briefing_md": f"{rel_root}/operator_review_briefing.md",
            "operator_packets_root": f"{rel_root}/operator_packets",
        },
    }
    manifest_path = collection_root / "collection_manifest.json"
    manifest_path.write_text(json.dumps(manifest_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    summary_md = _collection_summary_markdown(
        selection_df=selection_out,
        metrics_df=metrics_df,
        steps_df=customer_steps_df,
        manifest_rel_root=rel_root,
        selection_metadata=selection_metadata,
        funnel_summary=funnel_summary,
        readiness_summary=readiness_summary,
        calibration_summary=calibration_summary,
        operator_briefing=operator_briefing,
    )
    summary_path = collection_root / "collection_summary.md"
    summary_path.write_text(summary_md, encoding="utf-8")

    logger.info(
        "Customer artifact collection complete. requested=%s selected=%s policy=%s",
        int(args.n_customers),
        len(selection_out),
        args.cohort_policy,
    )
    logger.info("Outputs: %s", collection_root)
    return run_ctx


if __name__ == "__main__":
    main()
