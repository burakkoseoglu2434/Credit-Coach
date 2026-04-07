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
    _build_selected_surface_projection,
    _merge_dict,
    _normalize_customer_roadmap_contract,
    _safe_text,
    _sync_metrics_summary_with_roadmap_summary,
    generate_customer_recourse_artifacts,
    write_customer_artifact_bundle,
)
from credit_coach.data.ingest import load_feature_contract, validate_and_select_columns
from credit_coach.data.preprocess import preprocess_dataframe
from credit_coach.data.split import split_dataframe
from credit_coach.evaluation.decision_calibration import (
    build_calibration_review_markdown,
    build_funnel_summary,
    build_movement_guardrail_evidence,
    build_movement_guardrail_review_markdown,
    build_outcome_rule_comparison,
    build_policy_baseline_selection,
    build_policy_candidate_disposition,
    build_policy_comparison,
    build_readiness_distribution,
    build_selection_work_frame,
    build_status_by_readiness,
    prepare_metrics_for_calibration,
    rebalance_offer_needed_selection,
    select_initial_cohort,
    summarize_readiness,
)
from credit_coach.evaluation.cohort_evidence import (
    build_cohort_evidence_package,
    build_phase60_evidence_summary,
    summarize_population_metrics_from_rows,
    write_phase60_evidence_artifacts,
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


def _json_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    try:
        parsed = json.loads(str(value or "[]"))
    except Exception:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if str(item)]


def _outcome_rule_note(effect: Mapping[str, Any] | None) -> dict[str, Any]:
    if not effect or int(_safe_int(effect.get("outcome_rule_applied", 0), 0)) != 1:
        return {
            "selected_outcome_rule_applied": 0,
            "selected_outcome_rule_profile_version": "",
            "selected_outcome_rule_source": "",
            "selected_outcome_rule_transition": "",
            "selected_outcome_rule_note": "",
            "selected_outcome_rule_note_localized": None,
        }
    transition = _safe_text(effect.get("outcome_rule_transition"), "none")
    profile_version = _safe_text(effect.get("outcome_rule_profile_version"))
    source = _safe_text(effect.get("outcome_rule_source"))
    messages = {
        "rejected_to_conditional_offer_support": (
            "Aktif kurum destegiyle bu dosya analiz katmaninda REJECTED durumundan CONDITIONAL durumuna tasinirdi.",
            "With active institution support, this file would move from REJECTED to CONDITIONAL in the analysis layer.",
        ),
        "rejected_to_conditional_readiness_support": (
            "Mevcut hazirlik sinyalleriyle bu dosya analiz katmaninda REJECTED durumundan CONDITIONAL durumuna tasinirdi.",
            "With the current readiness evidence, this file would move from REJECTED to CONDITIONAL in the analysis layer.",
        ),
        "conditional_to_approved_offer_support": (
            "Aktif kurum destegiyle bu dosya analiz katmaninda CONDITIONAL durumundan APPROVED durumuna tasinirdi.",
            "With active institution support, this file would move from CONDITIONAL to APPROVED in the analysis layer.",
        ),
        "conditional_to_approved_offer_readiness_combo": (
            "Teklif ve hazirlik birlikte guclendiginde bu dosya analiz katmaninda CONDITIONAL durumundan APPROVED durumuna tasinirdi.",
            "With combined offer and readiness support, this file would move from CONDITIONAL to APPROVED in the analysis layer.",
        ),
    }
    tr_text, en_text = messages.get(
        transition,
        (
            "Sinirli bir teklif/hazirlik kuralı bu dosyada analiz katmaninda yukari yonlu hareket olustururdu.",
            "A bounded offer/readiness rule would create upward movement for this file in the analysis layer.",
        ),
    )
    return {
        "selected_outcome_rule_applied": 1,
        "selected_outcome_rule_profile_version": profile_version,
        "selected_outcome_rule_source": source,
        "selected_outcome_rule_transition": transition,
        "selected_outcome_rule_note": en_text,
        "selected_outcome_rule_note_localized": {"tr": tr_text, "en": en_text},
    }


def _apply_outcome_rule_note_to_bundle(
    bundle: CustomerArtifactBundle,
    *,
    effect: Mapping[str, Any] | None,
) -> None:
    payload = _outcome_rule_note(effect)
    bundle.roadmap.setdefault("summary", {})
    if isinstance(bundle.roadmap.get("summary"), dict):
        bundle.roadmap["summary"].update(payload)
    bundle.metrics_summary.update(payload)


def _aligned_series(
    frame: pd.DataFrame,
    column: str,
    *,
    fill_value: Any,
    dtype: str | type | None = None,
) -> pd.Series:
    if column in frame.columns:
        return frame[column].reindex(frame.index)
    return pd.Series([fill_value] * len(frame), index=frame.index, dtype=dtype)


def _normalized_roadmap_summary(bundle: CustomerArtifactBundle) -> dict[str, Any]:
    bundle.roadmap = _normalize_customer_roadmap_contract(bundle.roadmap)
    bundle.roadmap = _apply_decision_ownership_to_roadmap(bundle.roadmap)
    bundle.roadmap = _build_selected_surface_projection(bundle.roadmap)
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
    bundle.roadmap = _build_selected_surface_projection(bundle.roadmap)
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
    json_list_fields = {
        "recourse_gate_reason_codes_json",
        "recoverability_signal_reason_codes_json",
        "recoverable_reason_codes_json",
        "movement_rank_reason_codes_json",
    }
    optional_render_fields = {
        "selected_path_customer_summary",
        "selected_path_operator_summary",
        "selected_path_render_version",
    }
    field_names = (
        "customer_id",
        "best_plan_id",
        "best_plan_source",
        "decision_status",
        "decision_status_internal",
        "selected_decision_status",
        "selected_plan_status_internal",
        "selected_recommendation_text",
        "selected_recommendation_source",
        "selected_action_count",
        "selected_recommendation_projection_version",
        "selected_path_customer_summary",
        "selected_path_operator_summary",
        "selected_path_render_version",
        "movement_score",
        "threshold_reach_probability",
        "threshold_reach_priority_flag",
        "selected_path_movement_strength",
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
        "selection_outcome",
        "selection_stage",
        "invalid_candidates_removed_count",
        "preferred_pool_invalid_exhausted",
        "no_valid_candidate_available",
        "selected_from_widened_valid_pool",
        "recoverable_flag",
        "recoverability_classifier_version",
        "recourse_mode",
        "recommendation_mode",
        "recourse_gate_version",
        "recourse_gate_reason_codes_json",
        "recoverability_signal_reason_codes_json",
        "recoverable_reason_codes_json",
        "movement_rank_reason_codes_json",
    )
    source_pairs = {
        "customer_id": bundle.customer_id,
        "best_plan_id": _safe_text(bundle.roadmap.get("best_plan_id")),
        "best_plan_source": _safe_text(bundle.roadmap.get("best_plan_source")),
        **{field: summary.get(field) for field in field_names if field in summary},
    }
    source_pairs["best_plan_id"] = _safe_text(source_pairs.get("best_plan_id"))
    source_pairs["best_plan_source"] = _safe_text(source_pairs.get("best_plan_source"))
    for field in (
        "decision_status",
        "decision_status_internal",
        "selected_decision_status",
        "selected_plan_status_internal",
        "selected_recommendation_text",
        "selected_recommendation_source",
        "selected_recommendation_projection_version",
        "selection_outcome",
        "selection_stage",
        "recoverability_classifier_version",
        "recourse_mode",
        "recommendation_mode",
        "recourse_gate_version",
    ):
        source_pairs[field] = _safe_text(source_pairs.get(field))
    for field in field_names:
        expected = source_pairs.get(field, metrics_summary.get(field))
        actual = metrics_row.get(field)
        if field in json_list_fields:
            expected = _json_dumps_compact(_json_list(expected))
            actual = _json_dumps_compact(_json_list(actual))
        if field in optional_render_fields and not _safe_text(expected) and not _safe_text(actual):
            continue
        if not _is_close_contract_value(expected, actual):
            mismatch_fields.append(field)
    if int(_safe_int(summary.get("best_action_count", 0), 0)) != int(len(steps_df)):
        mismatch_fields.append("best_action_count_vs_steps")
    selected_best = plans_df.loc[plans_df.get("selected_best_flag", pd.Series(dtype=int)).fillna(0).astype(int) == 1]
    selection_outcome = _safe_text(summary.get("selection_outcome"))
    best_plan_id = _safe_text(summary.get("best_plan_id"))
    limited_empty_state = (
        _safe_text(summary.get("recourse_mode")) == "limited"
        and _safe_text(summary.get("selected_recommendation_source")) == "empty_state"
        and not best_plan_id
    )
    if (selection_outcome == "no_valid_winner" and not best_plan_id) or limited_empty_state:
        if not selected_best.empty:
            mismatch_fields.append("selected_best_unexpected")
        if _safe_text(metrics_row.get("selected_recommendation_source")) != "empty_state":
            mismatch_fields.append("selected_recommendation_source")
        if _safe_text(metrics_row.get("selected_recommendation_text")):
            mismatch_fields.append("selected_recommendation_text")
        if int(_safe_int(metrics_row.get("selected_action_count", 0), 0)) != 0:
            mismatch_fields.append("selected_action_count")
    elif selected_best.empty:
        mismatch_fields.append("selected_best_plan")
    elif len(selected_best) != 1:
        mismatch_fields.append("selected_best_duplicate")
    elif str(selected_best.iloc[0].get("recommendation_validity_status", "") or "").strip().lower() == "invalid":
        mismatch_fields.append("selected_best_invalid")
    elif str(selected_best.iloc[0].get("plan_source", "") or "").strip().lower() == "dice":
        if int(_safe_int(selected_best.iloc[0].get("dice_contender_eligible", 0), 0)) != 1:
            mismatch_fields.append("selected_best_dice_ineligible")
        if int(_safe_int(selected_best.iloc[0].get("dice_annotation_complete", 0), 0)) != 1:
            mismatch_fields.append("selected_best_dice_annotation_incomplete")
        if str(selected_best.iloc[0].get("dice_semantic_quality_status", "") or "").strip().lower() == "invalid":
            mismatch_fields.append("selected_best_dice_semantic_invalid")
    elif _safe_text(selected_best.iloc[0].get("status")) != _safe_text(summary.get("selected_plan_status_internal")):
        mismatch_fields.append("selected_plan_status_internal")
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


def _default_collection_sample_csv_path(*, project_root: Path) -> Path:
    return project_root / "data" / "sample" / "lending_club_sample_2000.csv"


def _attach_deterministic_customer_ids(df: pd.DataFrame, *, prefix: str) -> pd.DataFrame:
    out = df.reset_index(drop=True).copy()
    generated = [f"{prefix}_{idx:06d}" for idx in range(len(out))]
    if "customer_id" not in out.columns:
        out.insert(0, "customer_id", generated)
        return out
    existing = out["customer_id"].fillna("").astype(str).str.strip()
    out.loc[:, "customer_id"] = [value if value else generated[idx] for idx, value in enumerate(existing)]
    return out


def _build_sample_fallback_frames(
    *,
    sample_csv_path: Path,
    contract: dict[str, Any],
    base_cfg: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_df = pd.read_csv(sample_csv_path)
    min_rows = int(contract.get("rules", {}).get("min_rows", 1))
    if len(raw_df) < min_rows:
        raise ValueError(
            f"Sample fallback dataset is too small: {len(raw_df)} < required minimum {min_rows}"
        )

    selected = validate_and_select_columns(
        df=raw_df,
        features=list(contract["features"]),
        target=str(contract["target"]),
        fail_on_missing=bool(contract.get("rules", {}).get("fail_on_missing", True)),
        drop_extra_columns=bool(contract.get("rules", {}).get("drop_extra_columns", True)),
    )
    processed_df, _ = preprocess_dataframe(selected, list(contract["features"]))
    prepare_cfg = base_cfg.get("prepare_data", {}) if isinstance(base_cfg.get("prepare_data", {}), dict) else {}
    split_cfg = base_cfg.get("split_protocol", {}) if isinstance(base_cfg.get("split_protocol", {}), dict) else {}
    split = split_dataframe(
        processed_df,
        target_col=str(contract["target"]),
        test_size=float(prepare_cfg.get("test_size", 0.2)),
        random_state=int(split_cfg.get("random_state", prepare_cfg.get("random_state", 42))),
        time_column=str(split_cfg.get("time_column", base_cfg.get("time_column", "")) or "").strip() or None,
        out_of_time=bool(split_cfg.get("out_of_time", prepare_cfg.get("out_of_time", False))),
    )
    train_df = _attach_deterministic_customer_ids(split.train_df, prefix="sample_train")
    test_df = _attach_deterministic_customer_ids(split.test_df, prefix="sample_test")
    return test_df, train_df


def _load_collection_input_frames(
    *,
    test_path: Path,
    train_path: Path,
    data_format: str,
    project_root: Path,
    contract: dict[str, Any],
    base_cfg: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if test_path.exists() and train_path.exists():
        test_df = _load_batch_input_frame(test_path, data_format=str(data_format).strip() or test_path.suffix.lstrip(".") or "parquet")
        train_df = _load_batch_input_frame(train_path, data_format=train_path.suffix.lstrip(".") or "parquet")
        return test_df, train_df

    sample_csv_path = _default_collection_sample_csv_path(project_root=project_root)
    if not sample_csv_path.exists():
        missing = [str(path) for path in (test_path, train_path) if not path.exists()]
        raise FileNotFoundError(
            "Processed dataset paths are missing and sample fallback dataset is unavailable. "
            f"Missing: {missing}. Expected fallback: {sample_csv_path}"
        )

    logger.warning(
        "Processed collection dataset missing (test=%s train=%s). Falling back to deterministic sample CSV at %s",
        test_path,
        train_path,
        sample_csv_path,
    )
    return _build_sample_fallback_frames(
        sample_csv_path=sample_csv_path,
        contract=contract,
        base_cfg=base_cfg,
    )


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
    source_summary = dict(result.bundle.roadmap.get("summary", {}) or {})
    roadmap_summary = _normalized_roadmap_summary(result.bundle)
    best_cost = float(pd.to_numeric(result.bundle.roadmap_steps_df.get("estimated_cost_usd", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum())
    metrics = dict(result.bundle.metrics_summary)

    def _reason_codes_json(field: str) -> str:
        explicit_json = _safe_text(source_summary.get(f"{field}_json", ""))
        if explicit_json:
            return explicit_json
        source_codes = source_summary.get(field, [])
        if source_codes:
            return _json_dumps_compact(list(source_codes))
        explicit_json = _safe_text(
            metrics.get(
                f"{field}_json",
                roadmap_summary.get(f"{field}_json", ""),
            )
        )
        if explicit_json:
            return explicit_json
        return _json_dumps_compact(
            list(
                metrics.get(
                    field,
                    source_summary.get(field, roadmap_summary.get(field, [])),
                )
                or []
            )
        )

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
            "best_execution_aware_value": _safe_float(metrics.get("best_execution_aware_value", 0.0), 0.0),
            "candidate_pool_diversity_index": _safe_float(metrics.get("candidate_pool_diversity_index", 0.0), 0.0),
            "candidate_source_entropy": _safe_float(metrics.get("candidate_source_entropy", 0.0), 0.0),
            "candidate_non_empty_count": non_empty_count,
            "candidate_approval_shell_only_count": approval_shell_only_count,
            "candidate_empty_removed_count": empty_removed_count,
            "path_count": int(_safe_int(metrics.get("path_count", roadmap_summary.get("path_count", 0)), 0)),
            "rankable_path_count": int(_safe_int(metrics.get("rankable_path_count", roadmap_summary.get("rankable_path_count", 0)), 0)),
            "multi_path_flag": int(_safe_int(metrics.get("multi_path_flag", roadmap_summary.get("multi_path_flag", 0)), 0)),
            "approval_gap": _safe_float(metrics.get("approval_gap", roadmap_summary.get("approval_gap", 0.0)), 0.0),
            "normalized_gap": _safe_float(metrics.get("normalized_gap", roadmap_summary.get("normalized_gap", 0.0)), 0.0),
            "recoverability_bucket": str(
                metrics.get("recoverability_bucket", roadmap_summary.get("recoverability_bucket", "")) or ""
            ),
            "recoverability_score": _safe_float(
                metrics.get("recoverability_score", roadmap_summary.get("recoverability_score", 0.0)),
                0.0,
            ),
            "has_valid_path_flag": int(
                _safe_int(metrics.get("has_valid_path_flag", roadmap_summary.get("has_valid_path_flag", 0)), 0)
            ),
            "has_rankable_path_flag": int(
                _safe_int(metrics.get("has_rankable_path_flag", roadmap_summary.get("has_rankable_path_flag", 0)), 0)
            ),
            "threshold_reach_possible": int(
                _safe_int(
                    metrics.get("threshold_reach_possible", roadmap_summary.get("threshold_reach_possible", 0)),
                    0,
                )
            ),
            "hard_structural_blocker_flag": int(
                _safe_int(
                    metrics.get(
                        "hard_structural_blocker_flag",
                        roadmap_summary.get("hard_structural_blocker_flag", 0),
                    ),
                    0,
                )
            ),
            "soft_structural_blocker_flag": int(
                _safe_int(
                    metrics.get(
                        "soft_structural_blocker_flag",
                        roadmap_summary.get("soft_structural_blocker_flag", 0),
                    ),
                    0,
                )
            ),
            "structural_blocker_flag": int(
                _safe_int(
                    metrics.get("structural_blocker_flag", roadmap_summary.get("structural_blocker_flag", 0)),
                    0,
                )
            ),
            "recoverable_flag": int(
                _safe_int(metrics.get("recoverable_flag", roadmap_summary.get("recoverable_flag", 0)), 0)
            ),
            "recoverability_classifier_version": str(
                metrics.get(
                    "recoverability_classifier_version",
                    roadmap_summary.get("recoverability_classifier_version", ""),
                )
                or ""
            ),
            "recourse_mode": str(
                metrics.get(
                    "recourse_mode",
                    roadmap_summary.get("recourse_mode", ""),
                )
                or ""
            ),
            "recommendation_mode": str(
                metrics.get(
                    "recommendation_mode",
                    roadmap_summary.get("recommendation_mode", ""),
                )
                or ""
            ),
            "recourse_gate_version": str(
                metrics.get(
                    "recourse_gate_version",
                    roadmap_summary.get("recourse_gate_version", ""),
                )
                or ""
            ),
            "recourse_gate_reason_codes_json": _json_dumps_compact(
                list(
                    metrics.get(
                        "recourse_gate_reason_codes",
                        roadmap_summary.get("recourse_gate_reason_codes", []),
                    )
                    or []
                )
            ),
            "hard_structural_blockers_json": _json_dumps_compact(
                list(
                    metrics.get(
                        "hard_structural_blockers",
                        roadmap_summary.get("hard_structural_blockers", []),
                    )
                    or []
                )
            ),
            "soft_structural_blockers_json": _json_dumps_compact(
                list(
                    metrics.get(
                        "soft_structural_blockers",
                        roadmap_summary.get("soft_structural_blockers", []),
                    )
                    or []
                )
            ),
            "recoverability_signal_reason_codes_json": _json_dumps_compact(
                []
            ),
            "recoverable_reason_codes_json": _json_dumps_compact(
                []
            ),
            "customer_only_path_count": int(_safe_int(metrics.get("customer_only_path_count", roadmap_summary.get("customer_only_path_count", 0)), 0)),
            "institution_assisted_path_count": int(
                _safe_int(metrics.get("institution_assisted_path_count", roadmap_summary.get("institution_assisted_path_count", 0)), 0)
            ),
            "hybrid_path_count": int(_safe_int(metrics.get("hybrid_path_count", roadmap_summary.get("hybrid_path_count", 0)), 0)),
            "action_diversity_index": _safe_float(
                metrics.get("action_diversity_index", roadmap_summary.get("action_diversity_index", 0.0)),
                0.0,
            ),
            "non_utilization_action_rate": _safe_float(
                metrics.get("non_utilization_action_rate", roadmap_summary.get("non_utilization_action_rate", 0.0)),
                0.0,
            ),
            "institution_action_rate": _safe_float(
                metrics.get("institution_action_rate", roadmap_summary.get("institution_action_rate", 0.0)),
                0.0,
            ),
            "recommendation_validity_status": str(metrics.get("recommendation_validity_status", roadmap_summary.get("recommendation_validity_status", "")) or ""),
            "recommendation_invalid_action_count": int(_safe_int(metrics.get("recommendation_invalid_action_count", roadmap_summary.get("recommendation_invalid_action_count", 0)), 0)),
            "recommendation_warning_action_count": int(_safe_int(metrics.get("recommendation_warning_action_count", roadmap_summary.get("recommendation_warning_action_count", 0)), 0)),
            "recommendation_sanity_flag": int(_safe_int(metrics.get("recommendation_sanity_flag", roadmap_summary.get("recommendation_sanity_flag", 0)), 0)),
            "selected_decision_status": str(
                metrics.get("selected_decision_status", roadmap_summary.get("selected_decision_status", "")) or ""
            ),
            "selected_plan_status_internal": str(
                metrics.get(
                    "selected_plan_status_internal",
                    roadmap_summary.get("selected_plan_status_internal", ""),
                )
                or ""
            ),
            "selected_recommendation_text": str(
                metrics.get(
                    "selected_recommendation_text",
                    roadmap_summary.get("selected_recommendation_text", ""),
                )
                or ""
            ),
            "selected_recommendation_source": str(
                metrics.get(
                    "selected_recommendation_source",
                    roadmap_summary.get("selected_recommendation_source", ""),
                )
                or ""
            ),
            "selected_action_count": int(
                _safe_int(
                    metrics.get("selected_action_count", roadmap_summary.get("selected_action_count", 0)),
                    0,
                )
            ),
            "selected_recommendation_projection_version": str(
                metrics.get(
                    "selected_recommendation_projection_version",
                    roadmap_summary.get("selected_recommendation_projection_version", ""),
                )
                or ""
            ),
            "selected_path_id": str(metrics.get("selected_path_id", roadmap_summary.get("selected_path_id", "")) or ""),
            "selected_path_type": str(metrics.get("selected_path_type", roadmap_summary.get("selected_path_type", "")) or ""),
            "selected_path_rank": int(_safe_int(metrics.get("selected_path_rank", roadmap_summary.get("selected_path_rank", 0)), 0)),
            "movement_score": _safe_float(
                metrics.get("movement_score", roadmap_summary.get("movement_score", 0.0)),
                0.0,
            ),
            "threshold_reach_probability": _safe_float(
                metrics.get(
                    "threshold_reach_probability",
                    roadmap_summary.get("threshold_reach_probability", 0.0),
                ),
                0.0,
            ),
            "threshold_reach_priority_flag": int(
                _safe_int(
                    metrics.get(
                        "threshold_reach_priority_flag",
                        roadmap_summary.get("threshold_reach_priority_flag", 0),
                    ),
                    0,
                )
            ),
            "selected_path_movement_strength": str(
                metrics.get(
                    "selected_path_movement_strength",
                    roadmap_summary.get("selected_path_movement_strength", ""),
                )
                or ""
            ),
            "movement_rank_reason_codes_json": _json_dumps_compact(
                list(
                    metrics.get(
                        "movement_rank_reason_codes",
                        roadmap_summary.get("movement_rank_reason_codes", []),
                    )
                    or []
                )
            ),
            "selected_outcome_rule_applied": int(
                _safe_int(
                    metrics.get(
                        "selected_outcome_rule_applied",
                        roadmap_summary.get("selected_outcome_rule_applied", 0),
                    ),
                    0,
                )
            ),
            "selected_outcome_rule_profile_version": str(
                metrics.get(
                    "selected_outcome_rule_profile_version",
                    roadmap_summary.get("selected_outcome_rule_profile_version", ""),
                )
                or ""
            ),
            "selected_outcome_rule_source": str(
                metrics.get(
                    "selected_outcome_rule_source",
                    roadmap_summary.get("selected_outcome_rule_source", ""),
                )
                or ""
            ),
            "selected_outcome_rule_transition": str(
                metrics.get(
                    "selected_outcome_rule_transition",
                    roadmap_summary.get("selected_outcome_rule_transition", ""),
                )
                or ""
            ),
            "selected_outcome_rule_note": str(
                metrics.get(
                    "selected_outcome_rule_note",
                    roadmap_summary.get("selected_outcome_rule_note", ""),
                )
                or ""
            ),
            "selection_outcome": str(metrics.get("selection_outcome", roadmap_summary.get("selection_outcome", "")) or ""),
            "selection_stage": str(metrics.get("selection_stage", roadmap_summary.get("selection_stage", "")) or ""),
            "invalid_candidates_removed_count": int(_safe_int(metrics.get("invalid_candidates_removed_count", roadmap_summary.get("invalid_candidates_removed_count", 0)), 0)),
            "preferred_pool_invalid_exhausted": int(_safe_int(metrics.get("preferred_pool_invalid_exhausted", roadmap_summary.get("preferred_pool_invalid_exhausted", 0)), 0)),
            "no_valid_candidate_available": int(_safe_int(metrics.get("no_valid_candidate_available", roadmap_summary.get("no_valid_candidate_available", 0)), 0)),
            "selected_from_widened_valid_pool": int(_safe_int(metrics.get("selected_from_widened_valid_pool", roadmap_summary.get("selected_from_widened_valid_pool", 0)), 0)),
            "dice_backend_class": str(metrics.get("dice_backend_class", roadmap_summary.get("dice_backend_class", "")) or ""),
            "dice_annotation_complete": int(
                _safe_int(metrics.get("dice_annotation_complete", roadmap_summary.get("dice_annotation_complete", 0)), 0)
            ),
            "dice_semantic_quality_status": str(
                metrics.get("dice_semantic_quality_status", roadmap_summary.get("dice_semantic_quality_status", "")) or ""
            ),
            "dice_semantic_quality_codes_json": _json_dumps_compact(
                list(metrics.get("dice_semantic_quality_codes", roadmap_summary.get("dice_semantic_quality_codes", [])) or [])
            ),
            "dice_contender_eligible": int(
                _safe_int(metrics.get("dice_contender_eligible", roadmap_summary.get("dice_contender_eligible", 0)), 0)
            ),
            "dice_semantic_warning_penalty": _safe_float(
                metrics.get("dice_semantic_warning_penalty", roadmap_summary.get("dice_semantic_warning_penalty", 0.0)),
                0.0,
            ),
            "dice_candidate_count": int(_safe_int(metrics.get("dice_candidate_count", 0), 0)),
            "dice_contender_eligible_count": int(_safe_int(metrics.get("dice_contender_eligible_count", 0), 0)),
            "dice_invalid_candidate_count": int(_safe_int(metrics.get("dice_invalid_candidate_count", 0), 0)),
            "dice_warning_candidate_count": int(_safe_int(metrics.get("dice_warning_candidate_count", 0), 0)),
            "dice_all_candidates_ineligible": int(_safe_int(metrics.get("dice_all_candidates_ineligible", 0), 0)),
            "dice_fallback_flag": int(_safe_int(metrics.get("dice_fallback_flag", 0), 0)),
            "dice_eligible_rate": _safe_float(metrics.get("dice_eligible_rate", 0.0), 0.0),
            "dice_invalid_rate": _safe_float(metrics.get("dice_invalid_rate", 0.0), 0.0),
            "dice_warning_rate": _safe_float(metrics.get("dice_warning_rate", 0.0), 0.0),
            "dice_fallback_rate": _safe_float(metrics.get("dice_fallback_rate", 0.0), 0.0),
            "selected_dice_flag": int(_safe_int(metrics.get("selected_dice_flag", 0), 0)),
            "selected_dice_valid_flag": int(_safe_int(metrics.get("selected_dice_valid_flag", 0), 0)),
            "selected_dice_annotation_complete_flag": int(
                _safe_int(metrics.get("selected_dice_annotation_complete_flag", 0), 0)
            ),
            "selected_dice_semantic_invalid_flag": int(
                _safe_int(metrics.get("selected_dice_semantic_invalid_flag", 0), 0)
            ),
            "selected_dice_valid_rate": _safe_float(metrics.get("selected_dice_valid_rate", 0.0), 0.0),
            "offer_ready_contender_share": _safe_float(metrics.get("offer_ready_contender_share", 0.0), 0.0),
            "provisional_offer_share": _safe_float(metrics.get("provisional_offer_share", 0.0), 0.0),
            "approval_shell_only_share": _safe_float(metrics.get("approval_shell_only_share", 0.0), 0.0),
            "hard_invalid_plan_rate": _safe_float(metrics.get("hard_invalid_plan_rate", 0.0), 0.0),
            "numeric_warning_rate": _safe_float(metrics.get("numeric_warning_rate", 0.0), 0.0),
            "best_plan_warning_rate": _safe_float(metrics.get("best_plan_warning_rate", 0.0), 0.0),
            "selected_invalid_winner_flag": int(_safe_int(metrics.get("selected_invalid_winner_flag", 0), 0)),
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
    metrics["recoverability_signal_reason_codes_json"] = _reason_codes_json("recoverability_signal_reason_codes")
    metrics["recoverable_reason_codes_json"] = _reason_codes_json("recoverable_reason_codes")
    metrics["recourse_gate_reason_codes_json"] = _reason_codes_json("recourse_gate_reason_codes")
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
    if "path_id" not in out.columns:
        out["path_id"] = ""
    if "path_type" not in out.columns:
        out["path_type"] = ""
    if "path_signature" not in out.columns:
        out["path_signature"] = ""
    if "path_rankable_flag" not in out.columns:
        out["path_rankable_flag"] = 0
    if "path_representative_flag" not in out.columns:
        out["path_representative_flag"] = 0
    if "path_rank" not in out.columns:
        out["path_rank"] = pd.Series([pd.NA] * len(out), index=out.index, dtype="object")
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
    if "dice_backend_class" not in out.columns:
        out["dice_backend_class"] = ""
    if "dice_annotation_complete" not in out.columns:
        out["dice_annotation_complete"] = 0
    if "dice_semantic_quality_status" not in out.columns:
        out["dice_semantic_quality_status"] = ""
    if "dice_semantic_quality_codes_json" not in out.columns:
        out["dice_semantic_quality_codes_json"] = "[]"
    if "dice_contender_eligible" not in out.columns:
        out["dice_contender_eligible"] = 0
    if "dice_semantic_warning_penalty" not in out.columns:
        out["dice_semantic_warning_penalty"] = 0.0
    if "dice_quality_gate_version" not in out.columns:
        out["dice_quality_gate_version"] = ""
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
    out.insert(10, "selection_outcome", _safe_text(summary.get("selection_outcome")))
    out.insert(11, "selection_stage", _safe_text(summary.get("selection_stage")))
    out.insert(12, "selected_decision_status", _safe_text(summary.get("selected_decision_status")))
    out.insert(13, "selected_plan_status_internal", _safe_text(summary.get("selected_plan_status_internal")))
    out.insert(14, "selected_recommendation_text", _safe_text(summary.get("selected_recommendation_text")))
    out.insert(15, "selected_recommendation_source", _safe_text(summary.get("selected_recommendation_source")))
    out.insert(
        16,
        "selected_recommendation_projection_version",
        _safe_text(summary.get("selected_recommendation_projection_version")),
    )
    out.insert(17, "selected_action_count", int(_safe_int(summary.get("selected_action_count", 0), 0)))
    out.insert(18, "selected_path_id", _safe_text(summary.get("selected_path_id")))
    out.insert(19, "selected_path_type", _safe_text(summary.get("selected_path_type")))
    out.insert(20, "selected_path_rank", int(_safe_int(summary.get("selected_path_rank", 0), 0)))
    out.insert(21, "movement_score", _safe_float(summary.get("movement_score", 0.0), 0.0))
    out.insert(22, "threshold_reach_probability", _safe_float(summary.get("threshold_reach_probability", 0.0), 0.0))
    out.insert(23, "threshold_reach_priority_flag", int(_safe_int(summary.get("threshold_reach_priority_flag", 0), 0)))
    out.insert(24, "selected_path_movement_strength", _safe_text(summary.get("selected_path_movement_strength")))
    out.insert(25, "movement_rank_reason_codes_json", _json_dumps_compact(summary.get("movement_rank_reason_codes", [])))
    out.insert(26, "selected_path_customer_summary", _safe_text(summary.get("selected_path_customer_summary")))
    out.insert(27, "selected_path_operator_summary", _safe_text(summary.get("selected_path_operator_summary")))
    out.insert(28, "selected_path_render_version", _safe_text(summary.get("selected_path_render_version")))
    if "action_count" in out.columns:
        out.insert(29, "plan_step_count", pd.to_numeric(out["action_count"], errors="coerce").fillna(0).astype(int))
    else:
        out.insert(29, "plan_step_count", 0)
    plan_contract_pass = pd.Series([pd.NA] * len(out), index=out.index, dtype="object")
    selected_mask = out["selected_best_flag"].astype(int) == 1
    plan_contract_pass.loc[selected_mask] = int(_safe_int(summary.get("plan_contract_pass", 0), 0))
    out.insert(30, "plan_contract_pass", plan_contract_pass)
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
    if "dice_annotation_complete" not in out.columns:
        out["dice_annotation_complete"] = 0
    if "dice_semantic_quality_status" not in out.columns:
        out["dice_semantic_quality_status"] = ""
    if "dice_contender_eligible" not in out.columns:
        out["dice_contender_eligible"] = 0
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
    outcome_rule_summary: Mapping[str, Any],
    operator_briefing: Mapping[str, Any],
    movement_guardrail_summary: Mapping[str, Any] | None = None,
    policy_baseline_selection: Mapping[str, Any] | None = None,
    phase_60_files: Mapping[str, Any] | None = None,
    phase_60_summary: Mapping[str, Any] | None = None,
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
    selected_invalid_winner_count = int(
        pd.to_numeric(metrics_df.get("selected_invalid_winner_flag", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum()
    )
    selected_invalid_winner_rate = _safe_float(
        pd.to_numeric(metrics_df.get("selected_invalid_winner_flag", pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean(),
        0.0,
    )
    no_valid_winner_count = int((_aligned_series(metrics_df, "selection_outcome", fill_value="", dtype=object).astype(str) == "no_valid_winner").sum())
    selected_empty_state_count = int(
        (_aligned_series(metrics_df, "selected_recommendation_source", fill_value="", dtype=object).astype(str) == "empty_state").sum()
    )
    selected_decision_status_mismatch_count = int(
        (
            _aligned_series(metrics_df, "decision_status", fill_value="", dtype=object).astype(str)
            != _aligned_series(metrics_df, "selected_decision_status", fill_value="", dtype=object).astype(str)
        ).sum()
    )
    mean_selected_action_count = _safe_float(
        pd.to_numeric(metrics_df.get("selected_action_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean(),
        0.0,
    )
    selected_projection_versions = (
        metrics_df.get("selected_recommendation_projection_version", pd.Series(dtype=object))
        .astype(str)
        .value_counts()
        .sort_index()
        .to_dict()
    )
    widened_valid_selection_rate = _safe_float(
        pd.to_numeric(metrics_df.get("selected_from_widened_valid_pool", pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean(),
        0.0,
    )
    preferred_pool_invalid_exhaustion_rate = _safe_float(
        pd.to_numeric(metrics_df.get("preferred_pool_invalid_exhausted", pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean(),
        0.0,
    )
    directional_invalid_count = int(pd.to_numeric(metrics_df.get("directional_invalid_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum())
    economic_warning_count = int(pd.to_numeric(metrics_df.get("economic_warning_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum())
    dice_candidate_total = int(pd.to_numeric(metrics_df.get("dice_candidate_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum())
    dice_eligible_total = int(pd.to_numeric(metrics_df.get("dice_contender_eligible_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum())
    dice_invalid_total = int(pd.to_numeric(metrics_df.get("dice_invalid_candidate_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum())
    dice_warning_total = int(pd.to_numeric(metrics_df.get("dice_warning_candidate_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum())
    dice_fallback_total = int(pd.to_numeric(metrics_df.get("dice_fallback_flag", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum())
    dice_selected_total = int(pd.to_numeric(metrics_df.get("selected_dice_flag", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum())
    dice_selected_valid_total = int(pd.to_numeric(metrics_df.get("selected_dice_valid_flag", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum())
    dice_eligible_rate = float(dice_eligible_total / max(1, dice_candidate_total))
    dice_invalid_rate = float(dice_invalid_total / max(1, dice_candidate_total))
    dice_warning_rate = float(dice_warning_total / max(1, dice_candidate_total))
    dice_fallback_rate = float(dice_fallback_total / max(1, len(metrics_df)))
    dice_all_ineligible_customer_rate = _safe_float(
        pd.to_numeric(metrics_df.get("dice_all_candidates_ineligible", pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean(),
        0.0,
    )
    selected_dice_valid_rate = 1.0 if dice_selected_total == 0 else float(dice_selected_valid_total / dice_selected_total)
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
    operator_decision_status = _aligned_series(metrics_df, "operator_selected_decision_status", fill_value="", dtype=object).astype(str)
    operator_rendered_blocker_count = pd.to_numeric(
        _aligned_series(metrics_df, "operator_rendered_blocker_count", fill_value=0.0, dtype=float),
        errors="coerce",
    ).fillna(0.0)
    operator_rendered_action_count = pd.to_numeric(
        _aligned_series(metrics_df, "operator_rendered_action_count", fill_value=0.0, dtype=float),
        errors="coerce",
    ).fillna(0.0)
    operator_upgrade_condition_text = _aligned_series(metrics_df, "operator_upgrade_condition_text", fill_value="", dtype=object).fillna("").astype(str)
    operator_readiness_render_mode = _aligned_series(metrics_df, "operator_readiness_render_mode", fill_value="", dtype=object).fillna("").astype(str)
    selected_recommendation_source = _aligned_series(metrics_df, "selected_recommendation_source", fill_value="", dtype=object).fillna("").astype(str)
    selection_outcome_series = _aligned_series(metrics_df, "selection_outcome", fill_value="", dtype=object).fillna("").astype(str)
    approved_with_blocker_count = int(((operator_decision_status == "APPROVED") & (operator_rendered_blocker_count > 0)).sum())
    approved_with_action_count = int(((operator_decision_status == "APPROVED") & (operator_rendered_action_count > 0)).sum())
    approved_with_upgrade_condition_count = int(
        ((operator_decision_status == "APPROVED") & (operator_upgrade_condition_text.str.strip() != "")).sum()
    )
    empty_state_with_action_count = int(
        (((selection_outcome_series == "no_valid_winner") | (selected_recommendation_source == "empty_state")) & (operator_rendered_action_count > 0)).sum()
    )
    action_blocker_mismatch_count = 0
    for _, row in metrics_df.iterrows():
        rendered_actions = _safe_int(row.get("operator_rendered_action_count", 0), 0)
        rendered_blockers = _safe_int(row.get("operator_rendered_blocker_count", 0), 0)
        if rendered_actions <= 0 or rendered_blockers <= 0:
            continue
        blocker_codes = set(_json_list(row.get("operator_top_blocker_codes_json", "[]")))
        first_action_codes = set(_json_list(row.get("operator_first_action_blocker_codes_json", "[]")))
        if blocker_codes and not blocker_codes.intersection(first_action_codes):
            action_blocker_mismatch_count += 1
    readiness_decision_mismatch_count = int(
        (
            ((selection_outcome_series == "no_valid_winner") & (operator_readiness_render_mode != "empty_state_context"))
            | (
                (selection_outcome_series != "no_valid_winner")
                & (operator_decision_status == "APPROVED")
                & (operator_readiness_render_mode != "approved_info")
            )
            | (
                (selection_outcome_series != "no_valid_winner")
                & (operator_decision_status == "CONDITIONAL")
                & (~operator_readiness_render_mode.isin(["conditional_time_gate", "conditional_manual_review"]))
            )
            | (
                (selection_outcome_series != "no_valid_winner")
                & (operator_decision_status == "REJECTED")
                & (~operator_readiness_render_mode.isin(["rejected_not_ready", "rejected_manual_review"]))
            )
        ).sum()
    )
    fallback_blocker_suppressed_count = int(
        pd.to_numeric(metrics_df.get("operator_fallback_blocker_suppressed", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum()
    )
    selected_outcome_rule_applied_count = int(
        pd.to_numeric(metrics_df.get("selected_outcome_rule_applied", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum()
    )
    movement_guardrail_summary = dict(movement_guardrail_summary or {})
    policy_baseline_selection = dict(policy_baseline_selection or {})
    phase_60_files = dict(phase_60_files or {})
    phase_60_summary = dict(phase_60_summary or {})
    threshold_family = dict(movement_guardrail_summary.get("threshold_family", {}) or {})
    outcome_family = dict(movement_guardrail_summary.get("offer_readiness_family", {}) or {})
    trust_guardrails = dict(movement_guardrail_summary.get("trust_guardrails", {}) or {})
    recommendation_space = dict(movement_guardrail_summary.get("recommendation_space", {}) or {})
    structural_cohort = dict(movement_guardrail_summary.get("structural_cohort", {}) or {})
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
            f"- Recommended candidate status: {_safe_text(calibration_summary.get('recommended_candidate_status'), 'no_safe_uplift') or 'no_safe_uplift'}",
            f"- Recommended candidate policy: {_safe_text(calibration_summary.get('recommended_candidate_policy_version'), 'n/a') or 'n/a'}",
            f"- Recommended candidate reason: {_safe_text(calibration_summary.get('recommended_candidate_reason'), 'n/a') or 'n/a'}",
            f"- Baseline north-star pass: {bool(dict(calibration_summary.get('baseline_policy_metrics', {})).get('north_star_pass', False))}",
            f"- Baseline false-positive proxy: {_safe_float(dict(calibration_summary.get('baseline_policy_metrics', {})).get('false_positive_proxy'), 0.0):.4f}",
            "",
            "## Outcome Rules",
            f"- Candidate outcome-rule profiles compared: {', '.join(outcome_rule_summary.get('candidate_outcome_rule_versions_compared', []) or []) or 'n/a'}",
            f"- Recommended outcome-rule status: {_safe_text(outcome_rule_summary.get('recommended_outcome_rule_status'), 'no_safe_uplift') or 'no_safe_uplift'}",
            f"- Recommended outcome-rule profile: {_safe_text(outcome_rule_summary.get('recommended_outcome_rule_profile_version'), 'n/a') or 'n/a'}",
            f"- Recommended outcome-rule reason: {_safe_text(outcome_rule_summary.get('recommended_outcome_rule_reason'), 'n/a') or 'n/a'}",
            f"- Selected outcome-rule note count: {selected_outcome_rule_applied_count}",
            "",
            "## Baseline Selection",
            f"- Preferred demo profile: {_safe_text(policy_baseline_selection.get('preferred_demo_profile'), 'n/a') or 'n/a'}",
            f"- Fallback demo profile: {_safe_text(policy_baseline_selection.get('fallback_demo_profile'), 'n/a') or 'n/a'}",
            f"- Preferred runtime policy: {_safe_text(policy_baseline_selection.get('preferred_runtime_policy_version'), 'n/a') or 'n/a'}",
            f"- Selection reason: {_safe_text(policy_baseline_selection.get('policy_baseline_selection_reason'), 'n/a') or 'n/a'}",
            f"- Threshold family promotion status: {_safe_text(policy_baseline_selection.get('threshold_family_promotion_status'), 'n/a') or 'n/a'}",
            f"- Outcome-rule family promotion status: {_safe_text(policy_baseline_selection.get('outcome_rule_family_promotion_status'), 'n/a') or 'n/a'}",
            f"- Next milestone focus: {_safe_text(policy_baseline_selection.get('next_milestone_focus'), 'n/a') or 'n/a'}",
            "",
            "## Funnel Guardrails",
            f"- Dominant movement bottleneck: {_safe_text(movement_guardrail_summary.get('dominant_movement_bottleneck'), 'n/a') or 'n/a'}",
            f"- Movement guardrail summary: {_safe_text(movement_guardrail_summary.get('movement_guardrail_summary'), 'n/a') or 'n/a'}",
            f"- Promotion blocker summary: {_safe_text(movement_guardrail_summary.get('promotion_blocker_summary'), 'n/a') or 'n/a'}",
            f"- Threshold family status: {_safe_text(threshold_family.get('status'), 'n/a') or 'n/a'}",
            f"- Offer/readiness family status: {_safe_text(outcome_family.get('status'), 'n/a') or 'n/a'}",
            f"- Trust regression detected: {bool(trust_guardrails.get('regression_detected', False))}",
            "",
            "## Movement Diagnosis",
            f"- Recommendation-space signal score: {_safe_int(recommendation_space.get('signal_score', 0), 0)}",
            f"- Structural-cohort signal score: {_safe_int(structural_cohort.get('signal_score', 0), 0)}",
            f"- Recommendation-space top blocker: {_safe_text(recommendation_space.get('top_blocker_title'), 'n/a') or 'n/a'}",
            f"- Structural top blocker: {_safe_text(structural_cohort.get('top_blocker_title'), 'n/a') or 'n/a'}",
            f"- Non-empty contender share: {_safe_float(recommendation_space.get('non_empty_contender_share'), 0.0):.4f}",
            f"- Approval-shell-only share: {_safe_float(recommendation_space.get('approval_shell_only_share'), 0.0):.4f}",
            f"- Not-ready share: {_safe_float(structural_cohort.get('not_ready_share'), 0.0):.4f}",
            f"- Near-term readiness share: {_safe_float(structural_cohort.get('near_term_readiness_share'), 0.0):.4f}",
            f"- Offer-ready contender share: {_safe_float(structural_cohort.get('offer_ready_contender_share'), 0.0):.4f}",
            f"- High-risk share: {_safe_float(structural_cohort.get('high_risk_share'), 0.0):.4f}",
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
            f"- Selected invalid winner count: {selected_invalid_winner_count}",
            f"- Selected invalid winner rate: {selected_invalid_winner_rate:.4f}",
            f"- No-valid-winner count: {no_valid_winner_count}",
            f"- Widened-valid selection rate: {widened_valid_selection_rate:.4f}",
            f"- Preferred-pool invalid exhaustion rate: {preferred_pool_invalid_exhaustion_rate:.4f}",
            f"- Directional invalid count: {directional_invalid_count}",
            f"- Economic warning count: {economic_warning_count}",
            f"- Offer-ready contender share: {offer_ready_share:.4f}",
            f"- Provisional offer share: {provisional_offer_share:.4f}",
            f"- Approval-shell-only share: {approval_shell_only_share:.4f}",
            f"- Best action-class dominance: {best_action_class_dominance:.4f}",
            f"- Best action-family dominance: {best_action_family_dominance:.4f}",
            "",
            "## DICE Lane",
            f"- DICE candidate count: {dice_candidate_total}",
            f"- DICE contender-eligible count: {dice_eligible_total}",
            f"- DICE invalid rate: {dice_invalid_rate:.4f}",
            f"- DICE warning rate: {dice_warning_rate:.4f}",
            f"- DICE eligible rate: {dice_eligible_rate:.4f}",
            f"- DICE fallback rate: {dice_fallback_rate:.4f}",
            f"- DICE all-ineligible customer rate: {dice_all_ineligible_customer_rate:.4f}",
            f"- Selected DICE winner count: {dice_selected_total}",
            f"- Selected DICE valid rate: {selected_dice_valid_rate:.4f}",
            "",
            "## Selected Surface",
            f"- Selected decision mismatch count: {selected_decision_status_mismatch_count}",
            f"- Selected empty-state count: {selected_empty_state_count}",
            f"- Mean selected action count: {mean_selected_action_count:.2f}",
            f"- Selected recommendation projection versions: {selected_projection_versions or '{}'}",
            "",
            "## Phase 60 Cohort Evidence",
            f"- Phase 60 evidence version: {_safe_text(phase_60_summary.get('phase_60_evidence_version'), 'n/a') or 'n/a'}",
            f"- Overall movement conclusion: {_safe_text(phase_60_summary.get('overall_movement_conclusion'), 'n/a') or 'n/a'}",
            f"- Overall trust conclusion: {_safe_text(phase_60_summary.get('overall_trust_conclusion'), 'n/a') or 'n/a'}",
            f"- Pilot-mixed bottleneck: {_safe_text(dict(phase_60_summary.get('population_bottlenecks', {}) or {}).get('pilot_mixed'), 'n/a') or 'n/a'}",
            "",
            "## Operator Packet Coherence",
            f"- Approved with blocker count: {approved_with_blocker_count}",
            f"- Approved with action count: {approved_with_action_count}",
            f"- Approved with upgrade condition count: {approved_with_upgrade_condition_count}",
            f"- Empty-state with action count: {empty_state_with_action_count}",
            f"- Action-blocker mismatch count: {action_blocker_mismatch_count}",
            f"- Readiness-decision mismatch count: {readiness_decision_mismatch_count}",
            f"- Fallback blocker suppressed count: {fallback_blocker_suppressed_count}",
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
            f"- Policy profile catalog: `{manifest_rel_root}/calibration/policy_profile_catalog.json`",
            f"- Policy recommendation summary: `{manifest_rel_root}/calibration/policy_recommendation_summary.json`",
            f"- Outcome-rule comparison: `{manifest_rel_root}/calibration/outcome_rule_comparison.csv`",
            f"- Outcome-rule shift matrix: `{manifest_rel_root}/calibration/outcome_rule_shift_matrix.csv`",
            f"- Outcome-rule customer effects: `{manifest_rel_root}/calibration/outcome_rule_customer_effects.csv`",
            f"- Outcome-rule profile catalog: `{manifest_rel_root}/calibration/outcome_rule_profile_catalog.json`",
            f"- Outcome-rule recommendation summary: `{manifest_rel_root}/calibration/outcome_rule_recommendation_summary.json`",
            f"- Policy baseline selection: `{manifest_rel_root}/calibration/policy_baseline_selection.json`",
            f"- Policy candidate disposition: `{manifest_rel_root}/calibration/policy_candidate_disposition.csv`",
            f"- Movement guardrail summary: `{manifest_rel_root}/calibration/movement_guardrail_summary.json`",
            f"- Movement promotion blockers: `{manifest_rel_root}/calibration/movement_promotion_blockers.csv`",
            f"- Movement bottleneck breakdown: `{manifest_rel_root}/calibration/movement_bottleneck_breakdown.csv`",
            f"- Movement ceiling breakdown: `{manifest_rel_root}/calibration/movement_ceiling_breakdown.csv`",
            f"- Movement guardrail review: `{manifest_rel_root}/calibration/movement_guardrail_review.md`",
            f"- Calibration review: `{manifest_rel_root}/calibration/calibration_review.md`",
            f"- Phase 60 cohort evidence summary: `{manifest_rel_root}/phase_60/{_safe_text(phase_60_files.get('cohort_evidence_summary_json'))}`",
            f"- Phase 60 cohort evidence markdown: `{manifest_rel_root}/phase_60/{_safe_text(phase_60_files.get('cohort_evidence_summary_md'))}`",
            f"- Phase 60 movement table: `{manifest_rel_root}/phase_60/{_safe_text(phase_60_files.get('movement_potential_table_csv'))}`",
            f"- Phase 60 path diversity table: `{manifest_rel_root}/phase_60/{_safe_text(phase_60_files.get('path_diversity_table_csv'))}`",
            f"- Phase 60 action coverage table: `{manifest_rel_root}/phase_60/{_safe_text(phase_60_files.get('action_coverage_table_csv'))}`",
            f"- Phase 60 selected-path table: `{manifest_rel_root}/phase_60/{_safe_text(phase_60_files.get('selected_path_distribution_table_csv'))}`",
            f"- Phase 60 trust regression table: `{manifest_rel_root}/phase_60/{_safe_text(phase_60_files.get('trust_regression_table_csv'))}`",
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
    test_df, train_df = _load_collection_input_frames(
        test_path=test_path,
        train_path=train_path,
        data_format=str(args.input_data_format).strip() or "parquet",
        project_root=project_root,
        contract=contract,
        base_cfg=base_cfg,
    )

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
    pre_customer_records: list[dict[str, Any]] = []
    plan_frames: list[pd.DataFrame] = []
    step_frames: list[pd.DataFrame] = []
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
        pre_customer_records.append(
            {
                "selection_row": selection_row.copy(),
                "result": result,
                "parity": dict(parity),
                "raw_dir": raw_root / f"{int(selection_row['batch_index']):03d}_{_path_safe_customer_id(str(selection_row['customer_id']))}",
                "operator_dir": operator_root / f"{int(selection_row['batch_index']):03d}_{_path_safe_customer_id(str(selection_row['customer_id']))}",
            }
        )
        plan_frames.append(plans_df)
        step_frames.append(steps_df)

    pre_metrics_df = pd.DataFrame(
        [
            _augment_metrics_row(
                collection_run_id=run_ctx.run_id,
                selection_row=record["selection_row"],
                result=record["result"],
            )
            | dict(record["parity"])
            for record in pre_customer_records
        ]
    ).sort_values(["batch_index", "customer_id"]).reset_index(drop=True)
    def _concat_collection_frames(frames: list[pd.DataFrame], *, default_columns: list[str]) -> pd.DataFrame:
        column_order: list[str] = []
        prepared_frames: list[pd.DataFrame] = []
        for frame in frames:
            if frame.empty:
                continue
            for column in frame.columns:
                if column not in column_order:
                    column_order.append(column)
            cleaned_frame = frame.dropna(axis=1, how="all")
            if cleaned_frame.empty:
                continue
            prepared_frames.append(cleaned_frame)
        if not prepared_frames:
            return pd.DataFrame(columns=default_columns)
        return pd.concat(prepared_frames, ignore_index=True).reindex(columns=column_order)

    customer_plans_df = (
        _concat_collection_frames(
            plan_frames,
            default_columns=["collection_run_id", "batch_index", "source_row_index", "customer_id", "plan_id"],
        )
    )
    customer_steps_df = (
        _concat_collection_frames(
            step_frames,
            default_columns=["collection_run_id", "batch_index", "source_row_index", "customer_id"],
        )
    )
    calibration_input_df = prepare_metrics_for_calibration(pre_metrics_df)
    funnel_summary = build_funnel_summary(calibration_input_df)
    readiness_summary = summarize_readiness(calibration_input_df)
    readiness_distribution_df = build_readiness_distribution(calibration_input_df)
    status_by_readiness_df = build_status_by_readiness(calibration_input_df)
    policy_version_evaluated = (
        pre_metrics_df.get("decision_policy_version", pd.Series(dtype=object)).astype(str).mode().iloc[0]
        if not pre_metrics_df.empty and not pre_metrics_df.get("decision_policy_version", pd.Series(dtype=object)).empty
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
    policy_profile_catalog = policy_comparison_payload["policy_profile_catalog"]
    policy_recommendation_summary = policy_comparison_payload["policy_recommendation_summary"]
    outcome_rule_payload = build_outcome_rule_comparison(
        calibration_input_df,
        policy_version_evaluated=policy_version_evaluated,
    )
    outcome_rule_comparison_df = outcome_rule_payload["outcome_rule_comparison"]
    outcome_rule_shift_matrix_df = outcome_rule_payload["outcome_rule_shift_matrix"]
    outcome_rule_customer_effects_df = outcome_rule_payload["outcome_rule_customer_effects"]
    outcome_rule_profile_catalog = outcome_rule_payload["outcome_rule_profile_catalog"]
    outcome_rule_summary = outcome_rule_payload["outcome_rule_summary"]
    outcome_rule_recommendation_summary = outcome_rule_payload["outcome_rule_recommendation_summary"]
    recommended_outcome_rule_profile_version = _safe_text(
        outcome_rule_recommendation_summary.get("recommended_outcome_rule_profile_version")
    )
    selected_effect_map: dict[tuple[int, str], dict[str, Any]] = {}
    if recommended_outcome_rule_profile_version:
        filtered_effects = outcome_rule_customer_effects_df.loc[
            (outcome_rule_customer_effects_df.get("outcome_rule_profile_version", pd.Series(dtype=object)).astype(str) == recommended_outcome_rule_profile_version)
            & (
                pd.to_numeric(
                    outcome_rule_customer_effects_df.get("outcome_rule_applied", pd.Series(dtype=float)),
                    errors="coerce",
                ).fillna(0.0)
                == 1
            )
        ].copy()
        selected_effect_map = {
            (int(row["source_row_index"]), str(row["customer_id"])): dict(row)
            for row in filtered_effects.to_dict(orient="records")
        }

    metrics_rows: list[dict[str, Any]] = []
    operator_packet_records: list[dict[str, Any]] = []
    for record in sorted(pre_customer_records, key=lambda item: (int(item["selection_row"]["batch_index"]), str(item["selection_row"]["customer_id"]))):
        selection_row = record["selection_row"]
        result = record["result"]
        effect = selected_effect_map.get((int(selection_row["source_row_index"]), str(selection_row["customer_id"])))
        _apply_outcome_rule_note_to_bundle(result.bundle, effect=effect)
        metrics_row = _augment_metrics_row(
            collection_run_id=run_ctx.run_id,
            selection_row=selection_row,
            result=result,
        )
        metrics_row.update(record["parity"])
        write_customer_artifact_bundle(result.bundle, record["raw_dir"])
        packet = build_operator_review_packet(result.bundle.roadmap)
        packet_paths = write_operator_review_packet(packet, record["operator_dir"])
        packet_relpath = f"{rel_root}/operator_packets/{record['operator_dir'].name}/operator_packet.json"
        metrics_row.update(operator_packet_metrics_fields(packet, packet_relpath=packet_relpath))
        operator_packet_records.append(
            {
                "customer_id": packet.customer_id,
                "batch_index": int(selection_row["batch_index"]),
                "packet_relpath": packet_relpath,
                "packet": packet.model_dump(mode="json"),
                "markdown_relpath": f"{rel_root}/operator_packets/{record['operator_dir'].name}/operator_packet.md",
                "written_files": {name: str(path) for name, path in packet_paths.items()},
            }
        )
        metrics_rows.append(metrics_row)

    metrics_df = pd.DataFrame(metrics_rows).sort_values(["batch_index", "customer_id"]).reset_index(drop=True)
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

    operator_briefing = build_collection_operator_briefing(
        metrics_df=metrics_df,
        operator_packets=[record["packet"] for record in operator_packet_records],
        funnel_summary=funnel_summary,
        readiness_summary=readiness_summary,
        segment_breakdown_df=segment_breakdown_df,
    )
    movement_guardrail_payload = build_movement_guardrail_evidence(
        metrics_df=metrics_df,
        policy_comparison_df=policy_comparison_df,
        policy_recommendation_summary=policy_recommendation_summary,
        outcome_rule_comparison_df=outcome_rule_comparison_df,
        outcome_rule_recommendation_summary=outcome_rule_recommendation_summary,
        operator_briefing=operator_briefing,
    )
    movement_guardrail_summary = movement_guardrail_payload["movement_guardrail_summary"]
    movement_promotion_blockers_df = movement_guardrail_payload["movement_promotion_blockers"]
    movement_bottleneck_breakdown_df = movement_guardrail_payload["movement_bottleneck_breakdown"]
    movement_ceiling_breakdown_df = movement_guardrail_payload["movement_ceiling_breakdown"]
    policy_candidate_disposition_df = build_policy_candidate_disposition(
        policy_comparison_df=policy_comparison_df,
        outcome_rule_comparison_df=outcome_rule_comparison_df,
    )
    policy_baseline_selection = build_policy_baseline_selection(
        policy_version_evaluated=policy_version_evaluated,
        policy_recommendation_summary=calibration_summary,
        outcome_rule_recommendation_summary=outcome_rule_summary,
        movement_guardrail_summary=movement_guardrail_summary,
        policy_comparison_df=policy_comparison_df,
        outcome_rule_comparison_df=outcome_rule_comparison_df,
    )

    funnel_json = calibration_root / "funnel_summary.json"
    readiness_csv = calibration_root / "readiness_distribution.csv"
    status_by_readiness_csv = calibration_root / "status_by_readiness.csv"
    policy_comparison_csv = calibration_root / "policy_comparison.csv"
    shift_matrix_csv = calibration_root / "decision_shift_matrix.csv"
    segment_breakdown_csv = calibration_root / "segment_breakdown.csv"
    policy_catalog_json = calibration_root / "policy_profile_catalog.json"
    policy_recommendation_json = calibration_root / "policy_recommendation_summary.json"
    outcome_rule_comparison_csv = calibration_root / "outcome_rule_comparison.csv"
    outcome_rule_shift_csv = calibration_root / "outcome_rule_shift_matrix.csv"
    outcome_rule_customer_effects_csv = calibration_root / "outcome_rule_customer_effects.csv"
    outcome_rule_catalog_json = calibration_root / "outcome_rule_profile_catalog.json"
    outcome_rule_recommendation_json = calibration_root / "outcome_rule_recommendation_summary.json"
    policy_baseline_selection_json = calibration_root / "policy_baseline_selection.json"
    policy_candidate_disposition_csv = calibration_root / "policy_candidate_disposition.csv"
    movement_guardrail_summary_json = calibration_root / "movement_guardrail_summary.json"
    movement_promotion_blockers_csv = calibration_root / "movement_promotion_blockers.csv"
    movement_bottleneck_breakdown_csv = calibration_root / "movement_bottleneck_breakdown.csv"
    movement_ceiling_breakdown_csv = calibration_root / "movement_ceiling_breakdown.csv"
    movement_guardrail_review_md = calibration_root / "movement_guardrail_review.md"
    calibration_review_md = calibration_root / "calibration_review.md"
    operator_briefing_md = collection_root / "operator_review_briefing.md"

    funnel_json.write_text(json.dumps(funnel_summary, indent=2, ensure_ascii=False), encoding="utf-8")
    readiness_distribution_df.to_csv(readiness_csv, index=False)
    status_by_readiness_df.to_csv(status_by_readiness_csv, index=False)
    policy_comparison_df.to_csv(policy_comparison_csv, index=False)
    decision_shift_matrix_df.to_csv(shift_matrix_csv, index=False)
    segment_breakdown_df.to_csv(segment_breakdown_csv, index=False)
    policy_catalog_json.write_text(json.dumps(policy_profile_catalog, indent=2, ensure_ascii=False), encoding="utf-8")
    policy_recommendation_json.write_text(
        json.dumps(policy_recommendation_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    outcome_rule_comparison_df.to_csv(outcome_rule_comparison_csv, index=False)
    outcome_rule_shift_matrix_df.to_csv(outcome_rule_shift_csv, index=False)
    outcome_rule_customer_effects_df.to_csv(outcome_rule_customer_effects_csv, index=False)
    outcome_rule_catalog_json.write_text(
        json.dumps(outcome_rule_profile_catalog, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    outcome_rule_recommendation_json.write_text(
        json.dumps(outcome_rule_recommendation_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    policy_baseline_selection_json.write_text(
        json.dumps(policy_baseline_selection, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    policy_candidate_disposition_df.to_csv(policy_candidate_disposition_csv, index=False)
    movement_guardrail_summary_json.write_text(
        json.dumps(movement_guardrail_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    movement_promotion_blockers_df.to_csv(movement_promotion_blockers_csv, index=False)
    movement_bottleneck_breakdown_df.to_csv(movement_bottleneck_breakdown_csv, index=False)
    movement_ceiling_breakdown_df.to_csv(movement_ceiling_breakdown_csv, index=False)
    movement_guardrail_review_md.write_text(
        build_movement_guardrail_review_markdown(movement_guardrail_summary),
        encoding="utf-8",
    )
    calibration_review_md.write_text(
        build_calibration_review_markdown(
            selection_policy_name=str(selection_metadata.get("selection_policy_name", args.cohort_policy)),
            cohort_purpose=str(selection_metadata.get("cohort_purpose", "")),
            funnel_summary=funnel_summary,
            readiness_summary=readiness_summary,
            policy_comparison_df=policy_comparison_df,
            recommendation_summary=policy_recommendation_summary,
            outcome_rule_comparison_df=outcome_rule_comparison_df,
            outcome_rule_recommendation_summary=outcome_rule_recommendation_summary,
        ),
        encoding="utf-8",
    )
    operator_briefing_md.write_text(
        render_collection_operator_briefing_markdown(operator_briefing),
        encoding="utf-8",
    )
    phase_60_root = collection_root / "phase_60"
    phase_60_collection_package = build_cohort_evidence_package(
        population_name="pilot_mixed",
        population_metrics=summarize_population_metrics_from_rows(metrics_df),
        movement_summary=movement_guardrail_summary,
        trust_regression_status=[],
    )
    phase_60_collection_summary = build_phase60_evidence_summary([phase_60_collection_package])
    phase_60_files = write_phase60_evidence_artifacts(
        phase_60_root,
        phase_60_collection_summary,
        prefix="phase_60_collection",
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
        "policy_profile_catalog_version": _safe_text(calibration_summary.get("policy_profile_catalog_version")),
        "recommended_candidate_policy_version": _safe_text(
            calibration_summary.get("recommended_candidate_policy_version")
        ),
        "recommended_candidate_status": _safe_text(calibration_summary.get("recommended_candidate_status")),
        "recommended_candidate_reason": _safe_text(calibration_summary.get("recommended_candidate_reason")),
        "policy_recommendation_summary": dict(policy_recommendation_summary),
        "candidate_outcome_rule_versions_compared": list(outcome_rule_summary.get("candidate_outcome_rule_versions_compared", [])),
        "outcome_rule_catalog_version": _safe_text(outcome_rule_summary.get("outcome_rule_catalog_version")),
        "recommended_outcome_rule_profile_version": _safe_text(
            outcome_rule_summary.get("recommended_outcome_rule_profile_version")
        ),
        "recommended_outcome_rule_status": _safe_text(outcome_rule_summary.get("recommended_outcome_rule_status")),
        "recommended_outcome_rule_reason": _safe_text(outcome_rule_summary.get("recommended_outcome_rule_reason")),
        "outcome_rule_recommendation_summary": dict(outcome_rule_recommendation_summary),
        "preferred_demo_profile": _safe_text(policy_baseline_selection.get("preferred_demo_profile")),
        "fallback_demo_profile": _safe_text(policy_baseline_selection.get("fallback_demo_profile")),
        "policy_baseline_selection_reason": _safe_text(policy_baseline_selection.get("policy_baseline_selection_reason")),
        "threshold_family_promotion_status": _safe_text(policy_baseline_selection.get("threshold_family_promotion_status")),
        "outcome_rule_family_promotion_status": _safe_text(
            policy_baseline_selection.get("outcome_rule_family_promotion_status")
        ),
        "next_milestone_focus": _safe_text(policy_baseline_selection.get("next_milestone_focus")),
        "policy_baseline_selection": dict(policy_baseline_selection),
        "dominant_movement_bottleneck": _safe_text(movement_guardrail_summary.get("dominant_movement_bottleneck")),
        "movement_guardrail_summary": _safe_text(movement_guardrail_summary.get("movement_guardrail_summary")),
        "promotion_blocker_summary": _safe_text(movement_guardrail_summary.get("promotion_blocker_summary")),
        "phase_60_evidence_version": _safe_text(phase_60_collection_summary.get("phase_60_evidence_version")),
        "phase_60_overall_movement_conclusion": _safe_text(phase_60_collection_summary.get("overall_movement_conclusion")),
        "phase_60_overall_trust_conclusion": _safe_text(phase_60_collection_summary.get("overall_trust_conclusion")),
        "raw_root": f"{rel_root}/raw",
        "funnel_summary": funnel_summary,
        "readiness_summary": readiness_summary,
        "calibration_summary": calibration_summary,
        "outcome_rule_summary": outcome_rule_summary,
        "movement_guardrail_summary_payload": movement_guardrail_summary,
        "policy_candidate_disposition_count": int(len(policy_candidate_disposition_df)),
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
            "selected_invalid_winner_count": int(
                pd.to_numeric(metrics_df.get("selected_invalid_winner_flag", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum()
            ),
            "selected_invalid_winner_rate": _safe_float(
                pd.to_numeric(metrics_df.get("selected_invalid_winner_flag", pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean(),
                0.0,
            ),
            "no_valid_winner_count": int(
                (metrics_df.get("selection_outcome", pd.Series(dtype=object)).astype(str) == "no_valid_winner").sum()
            ),
            "widened_valid_selection_rate": _safe_float(
                pd.to_numeric(metrics_df.get("selected_from_widened_valid_pool", pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean(),
                0.0,
            ),
            "preferred_pool_invalid_exhaustion_rate": _safe_float(
                pd.to_numeric(metrics_df.get("preferred_pool_invalid_exhausted", pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean(),
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
        "selected_surface_summary": {
            "selected_decision_status_mismatch_count": int(
                (
                    metrics_df.get("decision_status", pd.Series(dtype=object)).astype(str)
                    != metrics_df.get("selected_decision_status", pd.Series(dtype=object)).astype(str)
                ).sum()
            ),
            "selected_empty_state_count": int(
                (metrics_df.get("selected_recommendation_source", pd.Series(dtype=object)).astype(str) == "empty_state").sum()
            ),
            "mean_selected_action_count": _safe_float(
                pd.to_numeric(metrics_df.get("selected_action_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean(),
                0.0,
            ),
            "selected_recommendation_projection_versions": (
                metrics_df.get("selected_recommendation_projection_version", pd.Series(dtype=object))
                .astype(str)
                .value_counts()
                .sort_index()
                .to_dict()
            ),
        },
        "operator_packet_coherence_summary": {
            "approved_with_blocker_count": int(
                (
                    (metrics_df.get("operator_selected_decision_status", pd.Series(dtype=object)).astype(str) == "APPROVED")
                    & (
                        pd.to_numeric(
                            metrics_df.get("operator_rendered_blocker_count", pd.Series(dtype=float)),
                            errors="coerce",
                        ).fillna(0.0)
                        > 0
                    )
                ).sum()
            ),
            "approved_with_action_count": int(
                (
                    (metrics_df.get("operator_selected_decision_status", pd.Series(dtype=object)).astype(str) == "APPROVED")
                    & (
                        pd.to_numeric(
                            metrics_df.get("operator_rendered_action_count", pd.Series(dtype=float)),
                            errors="coerce",
                        ).fillna(0.0)
                        > 0
                    )
                ).sum()
            ),
            "approved_with_upgrade_condition_count": int(
                (
                    (metrics_df.get("operator_selected_decision_status", pd.Series(dtype=object)).astype(str) == "APPROVED")
                    & (metrics_df.get("operator_upgrade_condition_text", pd.Series(dtype=object)).fillna("").astype(str).str.strip() != "")
                ).sum()
            ),
            "empty_state_with_action_count": int(
                (
                    (
                        (metrics_df.get("selection_outcome", pd.Series(dtype=object)).fillna("").astype(str) == "no_valid_winner")
                        | (metrics_df.get("selected_recommendation_source", pd.Series(dtype=object)).fillna("").astype(str) == "empty_state")
                    )
                    & (
                        pd.to_numeric(
                            metrics_df.get("operator_rendered_action_count", pd.Series(dtype=float)),
                            errors="coerce",
                        ).fillna(0.0)
                        > 0
                    )
                ).sum()
            ),
            "action_blocker_mismatch_count": int(
                sum(
                    1
                    for _, row in metrics_df.iterrows()
                    if _safe_int(row.get("operator_rendered_action_count", 0), 0) > 0
                    and _safe_int(row.get("operator_rendered_blocker_count", 0), 0) > 0
                    and set(_json_list(row.get("operator_top_blocker_codes_json", "[]")))
                    and not set(_json_list(row.get("operator_top_blocker_codes_json", "[]"))).intersection(
                        set(_json_list(row.get("operator_first_action_blocker_codes_json", "[]")))
                    )
                )
            ),
            "readiness_decision_mismatch_count": int(
                (
                    (
                        (metrics_df.get("selection_outcome", pd.Series(dtype=object)).fillna("").astype(str) == "no_valid_winner")
                        & (metrics_df.get("operator_readiness_render_mode", pd.Series(dtype=object)).fillna("").astype(str) != "empty_state_context")
                    )
                    | (
                        (metrics_df.get("selection_outcome", pd.Series(dtype=object)).fillna("").astype(str) != "no_valid_winner")
                        & (metrics_df.get("operator_selected_decision_status", pd.Series(dtype=object)).fillna("").astype(str) == "APPROVED")
                        & (metrics_df.get("operator_readiness_render_mode", pd.Series(dtype=object)).fillna("").astype(str) != "approved_info")
                    )
                    | (
                        (metrics_df.get("selection_outcome", pd.Series(dtype=object)).fillna("").astype(str) != "no_valid_winner")
                        & (metrics_df.get("operator_selected_decision_status", pd.Series(dtype=object)).fillna("").astype(str) == "CONDITIONAL")
                        & (
                            ~metrics_df.get("operator_readiness_render_mode", pd.Series(dtype=object))
                            .fillna("")
                            .astype(str)
                            .isin(["conditional_time_gate", "conditional_manual_review"])
                        )
                    )
                    | (
                        (metrics_df.get("selection_outcome", pd.Series(dtype=object)).fillna("").astype(str) != "no_valid_winner")
                        & (metrics_df.get("operator_selected_decision_status", pd.Series(dtype=object)).fillna("").astype(str) == "REJECTED")
                        & (
                            ~metrics_df.get("operator_readiness_render_mode", pd.Series(dtype=object))
                            .fillna("")
                            .astype(str)
                            .isin(["rejected_not_ready", "rejected_manual_review"])
                        )
                    )
                ).sum()
            ),
            "fallback_blocker_suppressed_count": int(
                pd.to_numeric(metrics_df.get("operator_fallback_blocker_suppressed", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum()
            ),
        },
        "dice_lane_summary": {
            "dice_candidate_count": int(
                pd.to_numeric(metrics_df.get("dice_candidate_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum()
            ),
            "dice_contender_eligible_count": int(
                pd.to_numeric(metrics_df.get("dice_contender_eligible_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum()
            ),
            "dice_invalid_candidate_count": int(
                pd.to_numeric(metrics_df.get("dice_invalid_candidate_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum()
            ),
            "dice_warning_candidate_count": int(
                pd.to_numeric(metrics_df.get("dice_warning_candidate_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum()
            ),
            "dice_eligible_rate": _safe_float(
                pd.to_numeric(metrics_df.get("dice_contender_eligible_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum()
                / max(
                    1.0,
                    float(
                        pd.to_numeric(metrics_df.get("dice_candidate_count", pd.Series(dtype=float)), errors="coerce")
                        .fillna(0.0)
                        .sum()
                    ),
                ),
                0.0,
            ),
            "dice_invalid_rate": _safe_float(
                pd.to_numeric(metrics_df.get("dice_invalid_candidate_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum()
                / max(
                    1.0,
                    float(
                        pd.to_numeric(metrics_df.get("dice_candidate_count", pd.Series(dtype=float)), errors="coerce")
                        .fillna(0.0)
                        .sum()
                    ),
                ),
                0.0,
            ),
            "dice_warning_rate": _safe_float(
                pd.to_numeric(metrics_df.get("dice_warning_candidate_count", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum()
                / max(
                    1.0,
                    float(
                        pd.to_numeric(metrics_df.get("dice_candidate_count", pd.Series(dtype=float)), errors="coerce")
                        .fillna(0.0)
                        .sum()
                    ),
                ),
                0.0,
            ),
            "dice_fallback_rate": _safe_float(
                pd.to_numeric(metrics_df.get("dice_fallback_flag", pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean(),
                0.0,
            ),
            "dice_all_ineligible_customer_rate": _safe_float(
                pd.to_numeric(metrics_df.get("dice_all_candidates_ineligible", pd.Series(dtype=float)), errors="coerce").fillna(0.0).mean(),
                0.0,
            ),
            "selected_dice_valid_rate": _safe_float(
                1.0
                if float(
                    pd.to_numeric(metrics_df.get("selected_dice_flag", pd.Series(dtype=float)), errors="coerce")
                    .fillna(0.0)
                    .sum()
                )
                == 0.0
                else (
                    pd.to_numeric(metrics_df.get("selected_dice_valid_flag", pd.Series(dtype=float)), errors="coerce")
                    .fillna(0.0)
                    .sum()
                    / float(
                        pd.to_numeric(metrics_df.get("selected_dice_flag", pd.Series(dtype=float)), errors="coerce")
                        .fillna(0.0)
                        .sum()
                    )
                ),
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
            "policy_profile_catalog_json": f"{rel_root}/calibration/policy_profile_catalog.json",
            "policy_recommendation_summary_json": f"{rel_root}/calibration/policy_recommendation_summary.json",
            "outcome_rule_comparison_csv": f"{rel_root}/calibration/outcome_rule_comparison.csv",
            "outcome_rule_shift_matrix_csv": f"{rel_root}/calibration/outcome_rule_shift_matrix.csv",
            "outcome_rule_customer_effects_csv": f"{rel_root}/calibration/outcome_rule_customer_effects.csv",
            "outcome_rule_profile_catalog_json": f"{rel_root}/calibration/outcome_rule_profile_catalog.json",
            "outcome_rule_recommendation_summary_json": f"{rel_root}/calibration/outcome_rule_recommendation_summary.json",
            "policy_baseline_selection_json": f"{rel_root}/calibration/policy_baseline_selection.json",
            "policy_candidate_disposition_csv": f"{rel_root}/calibration/policy_candidate_disposition.csv",
            "movement_guardrail_summary_json": f"{rel_root}/calibration/movement_guardrail_summary.json",
            "movement_promotion_blockers_csv": f"{rel_root}/calibration/movement_promotion_blockers.csv",
            "movement_bottleneck_breakdown_csv": f"{rel_root}/calibration/movement_bottleneck_breakdown.csv",
            "movement_ceiling_breakdown_csv": f"{rel_root}/calibration/movement_ceiling_breakdown.csv",
            "movement_guardrail_review_md": f"{rel_root}/calibration/movement_guardrail_review.md",
            "calibration_review_md": f"{rel_root}/calibration/calibration_review.md",
        },
        "phase_60_files": {
            key: f"{rel_root}/phase_60/{value}"
            for key, value in phase_60_files.items()
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
        outcome_rule_summary=outcome_rule_summary,
        operator_briefing=operator_briefing,
        movement_guardrail_summary=movement_guardrail_summary,
        policy_baseline_selection=policy_baseline_selection,
        phase_60_files=phase_60_files,
        phase_60_summary=phase_60_collection_summary,
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
