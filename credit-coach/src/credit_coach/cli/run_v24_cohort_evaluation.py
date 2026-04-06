from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from credit_coach.cli.run_recourse import generate_customer_recourse_artifacts
from credit_coach.data.ingest import load_feature_contract
from credit_coach.evaluation.cohort_evidence import (
    build_cohort_evidence_package,
    build_phase60_evidence_summary,
    summarize_population_metrics_from_rows,
    write_phase60_evidence_artifacts,
)
from credit_coach.evaluation.recoverability import (
    best_possible_pd_improvement_from_predictions,
    build_recoverability_signal,
    compute_approval_gap,
)
from credit_coach.model.predict import predict_proba_pd
from credit_coach.model.registry import load_model_bundle
from credit_coach.ops.operator_review import build_operator_review_packet, operator_packet_metrics_fields
from credit_coach.utils.run_context import load_config


COHORT_ORDER = (
    "near_threshold_denied",
    "mid_risk_denied",
    "hard_denied",
)
COHORT_LABELS = {
    0: "near_threshold_denied",
    1: "mid_risk_denied",
    2: "hard_denied",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a 500-customer v2.4 cohort evaluation for movement potential and action diversity."
    )
    parser.add_argument("--base_config", type=str, default="configs/default.yaml")
    parser.add_argument("--model_config", type=str, default="configs/model.yaml")
    parser.add_argument("--recourse_config", type=str, default="configs/recourse.yaml")
    parser.add_argument("--causality_config", type=str, default="configs/causality.yaml")
    parser.add_argument("--safety_config", type=str, default="configs/safety.yaml")
    parser.add_argument("--macro_config", type=str, default="configs/macro.yaml")
    parser.add_argument("--dataset_scope", type=str, default="full_processed", choices=["full_processed", "test_only"])
    parser.add_argument("--n_customers", type=int, default=500)
    parser.add_argument("--sample_seed", type=int, default=42)
    parser.add_argument("--model_version", type=str, default="")
    parser.add_argument("--model_manifest", type=str, default="")
    parser.add_argument("--output_dir", type=str, default="")
    return parser.parse_args()


def _resolve_repo_path(raw_path: str | Path, *, project_root: Path) -> Path:
    path = Path(raw_path)
    if path.exists():
        return path
    candidate = project_root / path
    if candidate.exists():
        return candidate
    return path


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return float(default)
    except Exception:
        pass
    try:
        return float(value)
    except Exception:
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or pd.isna(value):
            return int(default)
    except Exception:
        pass
    try:
        return int(value)
    except Exception:
        return int(default)


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except Exception:
        pass
    text = str(value).strip()
    return text or default


def _json_loads_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    text = _safe_text(value)
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except Exception:
        return []
    return parsed if isinstance(parsed, list) else []


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _normalize_code_list(value: Any) -> list[str]:
    values = value if isinstance(value, list) else _json_loads_list(value)
    normalized: list[str] = []
    for raw in values:
        text = _safe_text(raw)
        if text:
            normalized.append(text)
    return normalized


def _select_live_value(*sources: dict[str, Any], key: str) -> Any:
    for source in sources:
        if key not in source:
            continue
        value = source.get(key)
        if isinstance(value, str) and not value.strip():
            continue
        if value is not None:
            return value
    return None


def _resolve_code_list(
    *,
    roadmap_summary: dict[str, Any],
    metrics_summary: dict[str, Any],
    direct_key: str,
    json_key: str,
    fallback: Any,
) -> list[str]:
    direct = _normalize_code_list(_select_live_value(roadmap_summary, metrics_summary, key=direct_key))
    if direct:
        return direct
    encoded = _normalize_code_list(_select_live_value(roadmap_summary, metrics_summary, key=json_key))
    if encoded:
        return encoded
    return _normalize_code_list(fallback)


def _resolve_recoverability_signal(
    *,
    roadmap_summary: dict[str, Any],
    metrics_summary: dict[str, Any],
    fallback_signal: dict[str, Any],
) -> dict[str, Any]:
    signal = dict(fallback_signal)
    signal["approval_gap"] = _safe_float(
        _select_live_value(roadmap_summary, metrics_summary, key="approval_gap"),
        fallback_signal["approval_gap"],
    )
    signal["normalized_gap"] = _safe_float(
        _select_live_value(roadmap_summary, metrics_summary, key="normalized_gap"),
        fallback_signal["normalized_gap"],
    )
    signal["risk_band"] = _safe_text(
        _select_live_value(roadmap_summary, metrics_summary, key="risk_band"),
        _safe_text(fallback_signal.get("risk_band")),
    )
    signal["recoverability_bucket"] = _safe_text(
        _select_live_value(roadmap_summary, metrics_summary, key="recoverability_bucket"),
        _safe_text(fallback_signal.get("recoverability_bucket")),
    )
    signal["recoverability_score"] = _safe_float(
        _select_live_value(roadmap_summary, metrics_summary, key="recoverability_score"),
        fallback_signal["recoverability_score"],
    )
    signal["has_valid_path_flag"] = int(
        bool(
            _safe_int(
                _select_live_value(roadmap_summary, metrics_summary, key="has_valid_path_flag"),
                _safe_int(fallback_signal.get("has_valid_path_flag", 0), 0),
            )
        )
    )
    signal["has_rankable_path_flag"] = int(
        bool(
            _safe_int(
                _select_live_value(roadmap_summary, metrics_summary, key="has_rankable_path_flag"),
                _safe_int(fallback_signal.get("has_rankable_path_flag", 0), 0),
            )
        )
    )
    signal["threshold_reach_possible"] = bool(
        _safe_int(
            _select_live_value(roadmap_summary, metrics_summary, key="threshold_reach_possible"),
            int(bool(fallback_signal.get("threshold_reach_possible", False))),
        )
    )
    signal["hard_structural_blocker_flag"] = int(
        bool(
            _safe_int(
                _select_live_value(roadmap_summary, metrics_summary, key="hard_structural_blocker_flag"),
                _safe_int(fallback_signal.get("hard_structural_blocker_flag", 0), 0),
            )
        )
    )
    signal["soft_structural_blocker_flag"] = int(
        bool(
            _safe_int(
                _select_live_value(roadmap_summary, metrics_summary, key="soft_structural_blocker_flag"),
                _safe_int(fallback_signal.get("soft_structural_blocker_flag", 0), 0),
            )
        )
    )
    signal["structural_blocker_flag"] = int(
        bool(
            _safe_int(
                _select_live_value(roadmap_summary, metrics_summary, key="structural_blocker_flag"),
                _safe_int(fallback_signal.get("structural_blocker_flag", 0), 0),
            )
        )
    )
    signal["hard_structural_blockers"] = _resolve_code_list(
        roadmap_summary=roadmap_summary,
        metrics_summary=metrics_summary,
        direct_key="hard_structural_blockers",
        json_key="hard_structural_blockers_json",
        fallback=fallback_signal.get("hard_structural_blockers", []),
    )
    signal["soft_structural_blockers"] = _resolve_code_list(
        roadmap_summary=roadmap_summary,
        metrics_summary=metrics_summary,
        direct_key="soft_structural_blockers",
        json_key="soft_structural_blockers_json",
        fallback=fallback_signal.get("soft_structural_blockers", []),
    )
    signal["recoverable_flag"] = bool(
        _safe_int(
            _select_live_value(roadmap_summary, metrics_summary, key="recoverable_flag"),
            int(bool(fallback_signal.get("recoverable_flag", False))),
        )
    )
    signal["recoverability_classifier_version"] = _safe_text(
        _select_live_value(roadmap_summary, metrics_summary, key="recoverability_classifier_version"),
        _safe_text(fallback_signal.get("recoverability_classifier_version")),
    )
    signal["recoverability_signal_reason_codes"] = _resolve_code_list(
        roadmap_summary=roadmap_summary,
        metrics_summary=metrics_summary,
        direct_key="recoverability_signal_reason_codes",
        json_key="recoverability_signal_reason_codes_json",
        fallback=fallback_signal.get("recoverability_signal_reason_codes", []),
    )
    signal["recoverable_reason_codes"] = _resolve_code_list(
        roadmap_summary=roadmap_summary,
        metrics_summary=metrics_summary,
        direct_key="recoverable_reason_codes",
        json_key="recoverable_reason_codes_json",
        fallback=fallback_signal.get("recoverable_reason_codes", []),
    )
    return signal


def _load_population(
    *,
    project_root: Path,
    base_cfg: dict[str, Any],
    dataset_scope: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    processed_root = Path(base_cfg.get("paths", {}).get("processed_data", "data/processed"))
    if not processed_root.is_absolute():
        processed_root = (project_root / processed_root).resolve()
    train_path = processed_root / "train.parquet"
    test_path = processed_root / "test.parquet"
    train_df = pd.read_parquet(train_path).copy()
    test_df = pd.read_parquet(test_path).copy()

    train_df["source_split"] = "train"
    train_df["source_row_index"] = train_df.index.astype(int)
    train_df["customer_id"] = train_df["source_row_index"].map(lambda idx: f"train_{idx:06d}")

    test_df["source_split"] = "test"
    test_df["source_row_index"] = test_df.index.astype(int)
    test_df["customer_id"] = test_df["source_row_index"].map(lambda idx: f"test_{idx:06d}")

    if dataset_scope == "test_only":
        return test_df.reset_index(drop=True), train_df.reset_index(drop=True)

    population_df = pd.concat([train_df, test_df], ignore_index=True)
    return population_df.reset_index(drop=True), train_df.reset_index(drop=True)


def _assign_gap_tertile_cohorts(denied_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, dict[str, float | int]]]:
    if denied_df.empty:
        raise ValueError("No denied customers available for cohort sampling.")
    ranked = denied_df.sort_values(["approval_gap", "customer_id"], ascending=[True, True]).reset_index(drop=True).copy()
    ranked["cohort_bucket"] = np.minimum((ranked.index.to_numpy() * 3) // max(1, len(ranked)), 2)
    ranked["cohort_label"] = ranked["cohort_bucket"].map(COHORT_LABELS)

    boundaries: dict[str, dict[str, float | int]] = {}
    for cohort in COHORT_ORDER:
        cohort_rows = ranked[ranked["cohort_label"] == cohort].copy()
        boundaries[cohort] = {
            "available_count": int(len(cohort_rows)),
            "min_approval_gap": _safe_float(cohort_rows["approval_gap"].min(), 0.0),
            "max_approval_gap": _safe_float(cohort_rows["approval_gap"].max(), 0.0),
        }
    return ranked, boundaries


def _target_counts_by_cohort(available_counts: dict[str, int], total: int) -> dict[str, int]:
    base = total // len(COHORT_ORDER)
    remainder = total % len(COHORT_ORDER)
    targets = {
        cohort: min(available_counts.get(cohort, 0), base + (1 if idx < remainder else 0))
        for idx, cohort in enumerate(COHORT_ORDER)
    }
    assigned = sum(targets.values())
    if assigned >= total:
        return targets

    remaining_capacity = {
        cohort: max(0, available_counts.get(cohort, 0) - targets.get(cohort, 0))
        for cohort in COHORT_ORDER
    }
    while assigned < total and any(capacity > 0 for capacity in remaining_capacity.values()):
        for cohort in COHORT_ORDER:
            if assigned >= total:
                break
            if remaining_capacity[cohort] <= 0:
                continue
            targets[cohort] += 1
            remaining_capacity[cohort] -= 1
            assigned += 1
    return targets


def _sample_cohorts(
    denied_ranked_df: pd.DataFrame,
    *,
    n_customers: int,
    sample_seed: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    available = {
        cohort: int((denied_ranked_df["cohort_label"] == cohort).sum())
        for cohort in COHORT_ORDER
    }
    targets = _target_counts_by_cohort(available, n_customers)
    with_replacement = len(denied_ranked_df) < n_customers
    sampled_frames: list[pd.DataFrame] = []
    for idx, cohort in enumerate(COHORT_ORDER):
        cohort_rows = denied_ranked_df[denied_ranked_df["cohort_label"] == cohort].copy()
        target_n = targets[cohort]
        replace = target_n > len(cohort_rows)
        sampled = cohort_rows.sample(
            n=target_n,
            random_state=sample_seed + idx,
            replace=replace,
        ).copy()
        sampled["cohort_target_n"] = target_n
        sampled["sampled_with_replacement"] = int(replace)
        sampled_frames.append(sampled)
    sampled_df = pd.concat(sampled_frames, ignore_index=True)
    sampled_df = sampled_df.sort_values(["cohort_label", "approval_gap", "customer_id"]).reset_index(drop=True)
    sampled_df["source_customer_id"] = sampled_df["customer_id"].astype(str)
    sampled_df["sample_slot_index"] = sampled_df.index.astype(int)
    sampled_df["evaluation_customer_id"] = sampled_df.apply(
        lambda record: f"{record['source_customer_id']}__eval_{int(record['sample_slot_index']):04d}",
        axis=1,
    )
    sampling_meta = {
        "requested_n": int(n_customers),
        "unique_denied_available": int(len(denied_ranked_df)),
        "realized_sample_n": int(len(sampled_df)),
        "with_replacement": bool(with_replacement),
        "unique_source_customers_in_sample": int(sampled_df["source_customer_id"].nunique()),
        "reused_draw_count": int(len(sampled_df) - sampled_df["source_customer_id"].nunique()),
    }
    return sampled_df, sampling_meta


def _rankable_paths_df(paths_df: pd.DataFrame) -> pd.DataFrame:
    if paths_df.empty:
        return paths_df.copy()
    return paths_df[paths_df.get("rankable_flag", pd.Series(dtype=bool)).astype(bool)].copy()


def _normalize_path_type(path_type: str) -> str:
    raw = _safe_text(path_type).lower()
    if raw == "customer_only":
        return "customer"
    if raw == "institution_assisted":
        return "institution"
    if raw == "hybrid":
        return "hybrid"
    return raw


def _collect_rankable_path_types(paths_df: pd.DataFrame) -> list[str]:
    rankable = _rankable_paths_df(paths_df)
    if rankable.empty:
        return []
    return sorted({_normalize_path_type(value) for value in rankable["path_type"].astype(str).tolist() if _normalize_path_type(value)})


def _collect_action_categories(paths_df: pd.DataFrame) -> list[str]:
    categories: set[str] = set()
    for raw in paths_df.get("action_categories", pd.Series(dtype=object)).tolist():
        values = raw if isinstance(raw, list) else _json_loads_list(raw)
        for value in values:
            text = _safe_text(value)
            if text:
                categories.add(text)
    return sorted(categories)


def _collect_action_keys(paths_df: pd.DataFrame) -> list[str]:
    action_keys: set[str] = set()
    for raw in paths_df.get("action_keys", pd.Series(dtype=object)).tolist():
        values = raw if isinstance(raw, list) else _json_loads_list(raw)
        for value in values:
            text = _safe_text(value)
            if text:
                action_keys.add(text)
    return sorted(action_keys)


def _movement_metrics(
    *,
    base_pd: float,
    tau: float,
    candidate_pool_df: pd.DataFrame,
    paths_df: pd.DataFrame,
) -> dict[str, Any]:
    initial_gap = max(0.0, base_pd - tau)
    rankable_paths = _rankable_paths_df(paths_df)
    if rankable_paths.empty or candidate_pool_df.empty:
        return {
            "movement_potential": "none",
            "structural_limit_flag": 1,
            "max_path_pd_improvement": 0.0,
            "max_gap_closure_rate": 0.0,
            "best_reachable_pd": base_pd,
            "path_reaches_threshold_flag": 0,
        }

    representative_ids = {
        _safe_text(value)
        for value in rankable_paths.get("representative_plan_id", pd.Series(dtype=object)).tolist()
        if _safe_text(value)
    }
    reps_df = candidate_pool_df[
        candidate_pool_df.get("plan_id", pd.Series(dtype=object)).astype(str).isin(representative_ids)
    ].copy()
    if reps_df.empty:
        return {
            "movement_potential": "none",
            "structural_limit_flag": 1,
            "max_path_pd_improvement": 0.0,
            "max_gap_closure_rate": 0.0,
            "best_reachable_pd": base_pd,
            "path_reaches_threshold_flag": 0,
        }

    reps_df["predicted_pd"] = pd.to_numeric(reps_df.get("predicted_pd", pd.Series(dtype=float)), errors="coerce").fillna(base_pd)
    max_improvement = best_possible_pd_improvement_from_predictions(
        base_pd=base_pd,
        predicted_pds=reps_df["predicted_pd"].tolist(),
    )
    best_reachable_pd = _safe_float(reps_df["predicted_pd"].min(), base_pd)
    reach_signal = build_recoverability_signal(
        base_pd=base_pd,
        tau=tau,
        has_valid_path_flag=not paths_df.empty,
        has_rankable_path_flag=not rankable_paths.empty,
        best_possible_pd_improvement=max_improvement,
    )
    reaches_threshold = int(bool(reach_signal["threshold_reach_possible"]))
    gap_closure_rate = 0.0 if initial_gap <= 0 else max(0.0, min(1.0, max_improvement / initial_gap))

    if reaches_threshold:
        movement = "strong"
    elif max_improvement <= 0.01:
        movement = "none"
    elif gap_closure_rate >= 0.50 or max_improvement >= 0.03:
        movement = "strong"
    else:
        movement = "weak"

    return {
        "movement_potential": movement,
        "structural_limit_flag": int(reaches_threshold == 0),
        "max_path_pd_improvement": round(max_improvement, 6),
        "max_gap_closure_rate": round(gap_closure_rate, 6),
        "best_reachable_pd": round(best_reachable_pd, 6),
        "path_reaches_threshold_flag": reaches_threshold,
    }


def _selected_surface_drift_flag(roadmap_summary: dict[str, Any]) -> int:
    return int(
        _safe_text(roadmap_summary.get("decision_status"))
        != _safe_text(roadmap_summary.get("selected_decision_status"))
    )


def _operator_packet_contradiction_flag(
    *,
    roadmap_summary: dict[str, Any],
    operator_metrics: dict[str, Any],
) -> int:
    decision_status = _safe_text(roadmap_summary.get("decision_status"))
    selected_status = _safe_text(operator_metrics.get("operator_selected_decision_status"))
    rendered_blockers = _safe_int(operator_metrics.get("operator_rendered_blocker_count", 0), 0)
    rendered_actions = _safe_int(operator_metrics.get("operator_rendered_action_count", 0), 0)
    readiness_mode = _safe_text(operator_metrics.get("operator_readiness_render_mode"))
    upgrade_text = _safe_text(operator_metrics.get("operator_upgrade_condition_text"))
    coherence_codes = set(_json_loads_list(operator_metrics.get("operator_packet_coherence_codes_json")))
    if not coherence_codes:
        coherence_codes = set(_safe_text(operator_metrics.get("operator_packet_coherence_codes_json")).strip("[]").replace('"', "").split(","))
        coherence_codes = {code.strip() for code in coherence_codes if code.strip()}

    selection_outcome = _safe_text(roadmap_summary.get("selection_outcome"))
    approved_packet_with_blockers = selected_status == "APPROVED" and rendered_blockers > 0
    approved_packet_with_actions = selected_status == "APPROVED" and rendered_actions > 0
    approved_packet_with_upgrade = selected_status == "APPROVED" and bool(upgrade_text)
    readiness_mismatch = (
        (selection_outcome == "no_valid_winner" and readiness_mode != "empty_state_context")
        or (selection_outcome != "no_valid_winner" and selected_status == "APPROVED" and readiness_mode != "approved_info")
    )
    action_blocker_mismatch = "action_blocker_mismatch" in coherence_codes
    decision_mismatch = decision_status != selected_status
    return int(
        approved_packet_with_blockers
        or approved_packet_with_actions
        or approved_packet_with_upgrade
        or readiness_mismatch
        or action_blocker_mismatch
        or decision_mismatch
    )


def _summarize_examples(customer_df: pd.DataFrame) -> dict[str, dict[str, Any]]:
    examples: dict[str, dict[str, Any]] = {}

    strong = customer_df[
        (customer_df["movement_potential"] == "strong")
        & (customer_df["path_count"].astype(int) > 1)
    ].copy()
    if not strong.empty:
        row = strong.sort_values(
            ["path_count", "max_gap_closure_rate", "unique_action_count_per_customer"],
            ascending=[False, False, False],
        ).iloc[0]
        examples["strong_multi_path_case"] = row.to_dict()

    institution = customer_df[
        (customer_df["institution_path_present"].astype(int) == 1)
        | (customer_df["hybrid_path_present"].astype(int) == 1)
    ].copy()
    if not institution.empty:
        row = institution.sort_values(
            ["institution_path_present", "hybrid_path_present", "path_count", "max_gap_closure_rate"],
            ascending=[False, False, False, False],
        ).iloc[0]
        examples["institution_driven_case"] = row.to_dict()

    structural = customer_df[customer_df["structural_limit_flag"].astype(int) == 1].copy()
    if not structural.empty:
        row = structural.sort_values(
            ["cohort_label", "movement_potential", "approval_gap"],
            ascending=[True, True, False],
        ).iloc[0]
        examples["structural_cohort_limited_case"] = row.to_dict()

    return examples


def _build_trust_regression_rows(
    *,
    population_name: str,
    metrics: dict[str, Any],
) -> list[dict[str, Any]]:
    evidence_source = f"{population_name}:cohort_metrics"
    return [
        {
            "suite": "winner_integrity",
            "status": "clean" if _safe_int(metrics.get("selected_invalid_winner_count", 0), 0) == 0 else "regression",
            "evidence_source": evidence_source,
            "notes": f"selected_invalid_winner_count={_safe_int(metrics.get('selected_invalid_winner_count', 0), 0)}",
        },
        {
            "suite": "selected_surface_consistency",
            "status": "clean" if _safe_int(metrics.get("selected_surface_drift_count", 0), 0) == 0 else "regression",
            "evidence_source": evidence_source,
            "notes": f"selected_surface_drift_count={_safe_int(metrics.get('selected_surface_drift_count', 0), 0)}",
        },
        {
            "suite": "operator_packet_coherence",
            "status": "clean"
            if _safe_int(metrics.get("operator_packet_contradiction_count", 0), 0) == 0
            else "regression",
            "evidence_source": evidence_source,
            "notes": (
                f"operator_packet_contradiction_count="
                f"{_safe_int(metrics.get('operator_packet_contradiction_count', 0), 0)}"
            ),
        },
    ]


def _aggregate_metrics(customer_df: pd.DataFrame) -> dict[str, Any]:
    if customer_df.empty:
        return {
            "sample_size": 0,
            "multi_path_rate": 0.0,
            "avg_paths_per_customer": 0.0,
            "max_paths": 0,
            "mean_approval_gap": 0.0,
            "mean_recoverability_score": 0.0,
            "threshold_reach_possible_rate": 0.0,
            "recoverable_customer_rate": 0.0,
            "recoverability_bucket_distribution": {},
            "recoverable_flag_distribution": {},
            "recoverability_classifier_version_distribution": {},
            "non_utilization_action_rate": 0.0,
            "action_category_distribution": {},
            "unique_action_count_per_customer": 0.0,
            "institution_path_rate": 0.0,
            "hybrid_path_rate": 0.0,
            "customers_with_any_movement_rate": 0.0,
            "customers_with_strong_movement_rate": 0.0,
            "structural_cohort_limited_rate": 0.0,
            "selected_invalid_winner_count": 0,
            "selected_surface_drift_count": 0,
            "operator_packet_contradiction_count": 0,
            "movement_potential_distribution": {},
        }

    recoverable_flag = pd.to_numeric(
        customer_df.get("recoverable_flag", pd.Series([0] * len(customer_df))),
        errors="coerce",
    ).fillna(0).astype(int)
    classifier_version = customer_df.get(
        "recoverability_classifier_version",
        pd.Series([""] * len(customer_df), dtype=object),
    ).astype(str).str.strip()
    metrics = {
        "sample_size": int(len(customer_df)),
        "multi_path_rate": round(float((customer_df["path_count"].astype(int) > 1).mean()), 6),
        "avg_paths_per_customer": round(float(customer_df["path_count"].astype(float).mean()), 6),
        "max_paths": int(customer_df["path_count"].astype(int).max()),
        "mean_approval_gap": round(float(customer_df["approval_gap"].astype(float).mean()), 6),
        "mean_recoverability_score": round(float(customer_df["recoverability_score"].astype(float).mean()), 6),
        "threshold_reach_possible_rate": round(
            float(customer_df["threshold_reach_possible"].astype(int).mean()),
            6,
        ),
        "recoverable_customer_rate": round(float(recoverable_flag.mean()), 6),
        "non_utilization_action_rate": round(float(customer_df["uses_non_utilization_action"].astype(int).mean()), 6),
        "unique_action_count_per_customer": round(
            float(customer_df["unique_action_count_per_customer"].astype(float).mean()),
            6,
        ),
        "institution_path_rate": round(float(customer_df["institution_path_present"].astype(int).mean()), 6),
        "hybrid_path_rate": round(float(customer_df["hybrid_path_present"].astype(int).mean()), 6),
        "customers_with_any_movement_rate": round(
            float((customer_df["movement_potential"] != "none").mean()),
            6,
        ),
        "customers_with_strong_movement_rate": round(
            float((customer_df["movement_potential"] == "strong").mean()),
            6,
        ),
        "structural_cohort_limited_rate": round(
            float(customer_df["structural_limit_flag"].astype(int).mean()),
            6,
        ),
        "selected_invalid_winner_count": int(customer_df["selected_invalid_winner_flag"].astype(int).sum()),
        "selected_surface_drift_count": int(customer_df["selected_surface_drift_flag"].astype(int).sum()),
        "operator_packet_contradiction_count": int(
            customer_df["operator_packet_contradiction_flag"].astype(int).sum()
        ),
        "movement_potential_distribution": {
            key: round(float(value), 6)
            for key, value in customer_df["movement_potential"].value_counts(normalize=True).sort_index().items()
        },
        "recoverability_bucket_distribution": {
            key: round(float(value), 6)
            for key, value in customer_df["recoverability_bucket"].astype(str).value_counts(normalize=True).sort_index().items()
        },
        "recoverable_flag_distribution": {
            "recoverable": round(float((recoverable_flag == 1).mean()), 6),
            "not_recoverable": round(float((recoverable_flag == 0).mean()), 6),
        },
        "recoverability_classifier_version_distribution": {
            key: round(float(value), 6)
            for key, value in classifier_version[classifier_version != ""].value_counts(normalize=True).sort_index().items()
        },
    }

    category_counts: dict[str, int] = {}
    for raw in customer_df["action_categories_json"].astype(str).tolist():
        for category in _json_loads_list(raw):
            text = _safe_text(category)
            if text:
                category_counts[text] = category_counts.get(text, 0) + 1
    metrics["action_category_distribution"] = {
        category: round(count / max(1, len(customer_df)), 6)
        for category, count in sorted(category_counts.items(), key=lambda item: (-item[1], item[0]))
    }
    return metrics


def _comparison_rows(customer_df: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for cohort in COHORT_ORDER:
        cohort_df = customer_df[customer_df["cohort_label"] == cohort].copy()
        metrics = _aggregate_metrics(cohort_df)
        rows.append(
            {
                "cohort": cohort,
                "sample_size": metrics["sample_size"],
                "multi_path_rate": metrics["multi_path_rate"],
                "avg_paths_per_customer": metrics["avg_paths_per_customer"],
                "threshold_reach_possible_rate": metrics["threshold_reach_possible_rate"],
                "non_utilization_action_rate": metrics["non_utilization_action_rate"],
                "institution_path_rate": metrics["institution_path_rate"],
                "hybrid_path_rate": metrics["hybrid_path_rate"],
                "customers_with_any_movement_rate": metrics["customers_with_any_movement_rate"],
                "customers_with_strong_movement_rate": metrics["customers_with_strong_movement_rate"],
                "structural_cohort_limited_rate": metrics["structural_cohort_limited_rate"],
                "selected_invalid_winner_count": metrics["selected_invalid_winner_count"],
                "selected_surface_drift_count": metrics["selected_surface_drift_count"],
                "operator_packet_contradiction_count": metrics["operator_packet_contradiction_count"],
            }
        )
    return rows


def _top_five_insights(
    *,
    overall: dict[str, Any],
    by_cohort: dict[str, dict[str, Any]],
) -> list[str]:
    strongest_cohort = max(
        COHORT_ORDER,
        key=lambda cohort: by_cohort[cohort]["customers_with_strong_movement_rate"],
    )
    most_limited_cohort = max(
        COHORT_ORDER,
        key=lambda cohort: by_cohort[cohort]["structural_cohort_limited_rate"],
    )
    insight_1 = (
        f"Strong movement was highest in {strongest_cohort} "
        f"({by_cohort[strongest_cohort]['customers_with_strong_movement_rate']:.1%})."
    )
    insight_2 = (
        f"Structural limitation remained highest in {most_limited_cohort} "
        f"({by_cohort[most_limited_cohort]['structural_cohort_limited_rate']:.1%})."
    )
    insight_3 = (
        f"Multi-path availability reached {overall['multi_path_rate']:.1%} overall, "
        f"with {overall['avg_paths_per_customer']:.2f} paths per customer on average."
    )
    insight_4 = (
        f"Non-utilization actions appeared for {overall['non_utilization_action_rate']:.1%} of customers, "
        f"indicating diversity beyond utilization-only suggestions."
    )
    trust_issue_count = (
        overall["selected_invalid_winner_count"]
        + overall["selected_surface_drift_count"]
        + overall["operator_packet_contradiction_count"]
    )
    insight_5 = (
        "Trust baseline remained intact." if trust_issue_count == 0 else
        f"Trust regressions were detected ({trust_issue_count} total row-level issues across the three trust checks)."
    )
    return [insight_1, insight_2, insight_3, insight_4, insight_5]


def _diagnosis_text(
    *,
    overall: dict[str, Any],
    by_cohort: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    near = by_cohort["near_threshold_denied"]
    mid = by_cohort["mid_risk_denied"]
    hard = by_cohort["hard_denied"]
    movement_increase = overall["customers_with_any_movement_rate"] > 0.0
    concentrated_near = (
        near["customers_with_strong_movement_rate"] > mid["customers_with_strong_movement_rate"]
        and near["customers_with_strong_movement_rate"] > hard["customers_with_strong_movement_rate"]
    )
    institution_meaningful = (
        overall["institution_path_rate"] >= 0.10
        and overall["customers_with_any_movement_rate"] > 0.0
        and (near["institution_path_rate"] > 0.0 or mid["institution_path_rate"] > 0.0)
    )
    structurally_limited_pct = round(overall["structural_cohort_limited_rate"] * 100.0, 2)
    trust_clean = (
        overall["selected_invalid_winner_count"] == 0
        and overall["selected_surface_drift_count"] == 0
        and overall["operator_packet_contradiction_count"] == 0
    )
    ready_for_uplift = (
        trust_clean
        and overall["customers_with_any_movement_rate"] >= 0.20
        and near["customers_with_strong_movement_rate"] >= 0.10
    )
    return {
        "does_v24_increase_movement_potential": (
            "yes_capability_signal"
            if movement_increase
            else "no_material_capability_signal"
        ),
        "is_improvement_concentrated_in_near_threshold": bool(concentrated_near),
        "are_institution_or_hybrid_paths_meaningful": (
            "meaningful"
            if institution_meaningful
            else "mostly_cosmetic_or_sparse"
        ),
        "structurally_limited_customer_pct": structurally_limited_pct,
        "is_system_ready_for_business_uplift_experiments": bool(ready_for_uplift),
        "trust_baseline_intact": bool(trust_clean),
    }


def _markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    header = "| " + " | ".join(label for _, label in columns) + " |"
    divider = "| " + " | ".join(["---"] * len(columns)) + " |"
    body: list[str] = []
    for row in rows:
        values = []
        for key, _label in columns:
            value = row.get(key, "")
            if isinstance(value, float):
                values.append(f"{value:.4f}")
            else:
                values.append(str(value))
        body.append("| " + " | ".join(values) + " |")
    return "\n".join([header, divider, *body])


def _render_report(
    *,
    sampled_df: pd.DataFrame,
    customer_df: pd.DataFrame,
    overall: dict[str, Any],
    by_cohort: dict[str, dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    diagnosis: dict[str, Any],
    examples: dict[str, dict[str, Any]],
    cohort_boundaries: dict[str, dict[str, float | int]],
    sampling_meta: dict[str, Any],
    dataset_scope: str,
    output_root: Path,
) -> str:
    key_metrics = [
        {"metric": "sample_size", "value": overall["sample_size"]},
        {"metric": "multi_path_rate", "value": overall["multi_path_rate"]},
        {"metric": "avg_paths_per_customer", "value": overall["avg_paths_per_customer"]},
        {"metric": "mean_approval_gap", "value": overall["mean_approval_gap"]},
        {"metric": "mean_recoverability_score", "value": overall["mean_recoverability_score"]},
        {"metric": "threshold_reach_possible_rate", "value": overall["threshold_reach_possible_rate"]},
        {"metric": "non_utilization_action_rate", "value": overall["non_utilization_action_rate"]},
        {"metric": "institution_path_rate", "value": overall["institution_path_rate"]},
        {"metric": "hybrid_path_rate", "value": overall["hybrid_path_rate"]},
        {"metric": "customers_with_any_movement_rate", "value": overall["customers_with_any_movement_rate"]},
        {"metric": "customers_with_strong_movement_rate", "value": overall["customers_with_strong_movement_rate"]},
        {"metric": "structural_cohort_limited_rate", "value": overall["structural_cohort_limited_rate"]},
        {"metric": "selected_invalid_winner_count", "value": overall["selected_invalid_winner_count"]},
        {"metric": "selected_surface_drift_count", "value": overall["selected_surface_drift_count"]},
        {"metric": "operator_packet_contradiction_count", "value": overall["operator_packet_contradiction_count"]},
    ]

    boundary_rows = [
        {
            "cohort": cohort,
            "available_count": int(cohort_boundaries[cohort]["available_count"]),
            "min_approval_gap": _safe_float(cohort_boundaries[cohort]["min_approval_gap"], 0.0),
            "max_approval_gap": _safe_float(cohort_boundaries[cohort]["max_approval_gap"], 0.0),
            "sampled_count": int((sampled_df["cohort_label"] == cohort).sum()),
        }
        for cohort in COHORT_ORDER
    ]

    example_lines: list[str] = []
    for label, example in examples.items():
        example_lines.append(
            f"- {label}: {example.get('customer_id', '')} | cohort={example.get('cohort_label', '')} "
            f"| movement={example.get('movement_potential', '')} | path_count={example.get('path_count', 0)} "
            f"| path_types={example.get('path_types_json', '[]')}"
        )
    if not example_lines:
        example_lines.append("- No qualifying examples were available in this sampled run.")

    insights = _top_five_insights(overall=overall, by_cohort=by_cohort)
    report = "\n".join(
        [
            "# v2.4 Cohort Evaluation",
            "",
            "## Scope",
            f"- Sampled customers: {len(customer_df)}",
            "- Evaluation mode: existing v2.4 recourse pipeline only",
            "- Planner changes: none",
            "- Threshold changes: none",
            "- New action types: none",
            f"- Dataset scope: {dataset_scope}",
            f"- Sampling mode: {'with_replacement' if sampling_meta.get('with_replacement') else 'without_replacement'}",
            f"- Unique denied customers available: {sampling_meta.get('unique_denied_available', 0)}",
            "",
            "## Cohort Sampling",
            _markdown_table(
                boundary_rows,
                [
                    ("cohort", "cohort"),
                    ("available_count", "available_count"),
                    ("sampled_count", "sampled_count"),
                    ("min_approval_gap", "min_approval_gap"),
                    ("max_approval_gap", "max_approval_gap"),
                ],
            ),
            "",
            "## Key Metrics",
            _markdown_table(
                key_metrics,
                [("metric", "metric"), ("value", "value")],
            ),
            "",
            "## Cohort Comparison",
            _markdown_table(
                comparison_rows,
                [
                    ("cohort", "cohort"),
                    ("sample_size", "sample_size"),
                    ("multi_path_rate", "multi_path_rate"),
                    ("threshold_reach_possible_rate", "threshold_reach_rate"),
                    ("non_utilization_action_rate", "non_utilization_action_rate"),
                    ("institution_path_rate", "institution_path_rate"),
                    ("hybrid_path_rate", "hybrid_path_rate"),
                    ("customers_with_any_movement_rate", "any_movement_rate"),
                    ("customers_with_strong_movement_rate", "strong_movement_rate"),
                    ("structural_cohort_limited_rate", "structural_limited_rate"),
                ],
            ),
            "",
            "## Cohort Readout",
            f"- near_threshold_denied: strong movement rate {by_cohort['near_threshold_denied']['customers_with_strong_movement_rate']:.1%}; "
            f"structural limitation rate {by_cohort['near_threshold_denied']['structural_cohort_limited_rate']:.1%}.",
            f"- mid_risk_denied: strong movement rate {by_cohort['mid_risk_denied']['customers_with_strong_movement_rate']:.1%}; "
            f"structural limitation rate {by_cohort['mid_risk_denied']['structural_cohort_limited_rate']:.1%}.",
            f"- hard_denied: strong movement rate {by_cohort['hard_denied']['customers_with_strong_movement_rate']:.1%}; "
            f"structural limitation rate {by_cohort['hard_denied']['structural_cohort_limited_rate']:.1%}.",
            "",
            "## Example Customers",
            *example_lines,
            "",
            "## Final Diagnosis",
            f"1. Does v2.4 increase movement potential? {diagnosis['does_v24_increase_movement_potential']}.",
            f"2. Is improvement concentrated in near-threshold cohort? {diagnosis['is_improvement_concentrated_in_near_threshold']}.",
            f"3. Are institution/hybrid paths meaningful or cosmetic? {diagnosis['are_institution_or_hybrid_paths_meaningful']}.",
            f"4. What % of customers remain structurally limited? {diagnosis['structurally_limited_customer_pct']:.2f}%.",
            f"5. Is system ready for business uplift experiments? {diagnosis['is_system_ready_for_business_uplift_experiments']}.",
            "",
            "Capability and outcome remain separated in this diagnosis: path availability shows what the system can propose, not realized business uplift.",
            "",
            "## Top 5 Insights",
            *[f"- {insight}" for insight in insights],
            "",
            "## Output Files",
            f"- customer_level_analysis.csv: {output_root / 'customer_level_analysis.csv'}",
            f"- cohort_metrics.json: {output_root / 'cohort_metrics.json'}",
            f"- cohort_evaluation_report.md: {output_root / 'cohort_evaluation_report.md'}",
        ]
    )
    return report


def main() -> None:
    args = parse_args()
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

    features_config_path = _resolve_repo_path(
        base_cfg.get("features_config", "configs/features_48.yaml"),
        project_root=project_root,
    )
    contract = load_feature_contract(features_config_path)
    feature_cols = contract["features"]
    target_col = contract["target"]

    population_df, train_df = _load_population(
        project_root=project_root,
        base_cfg=base_cfg,
        dataset_scope=args.dataset_scope,
    )

    model, calibrator, manifest, _ = load_model_bundle(
        base_path=model_cfg.get("registry", {}).get("path", "artifacts/models"),
        model_version=str(args.model_version).strip() or None,
        manifest_path=str(args.model_manifest).strip() or None,
    )
    tau = float(model_cfg.get("decision", {}).get("tau_0", 0.35))
    population_df = population_df.copy()
    population_df["base_pd"] = predict_proba_pd(model, calibrator, population_df[feature_cols])
    population_df["denied_base"] = (population_df["base_pd"].astype(float) > tau).astype(int)
    population_df["approval_gap"] = population_df["base_pd"].map(
        lambda value: compute_approval_gap(base_pd=float(value), tau=tau)
    )

    denied_df = population_df[population_df["denied_base"].astype(int) == 1].copy()
    denied_ranked_df, cohort_boundaries = _assign_gap_tertile_cohorts(denied_df)
    sampled_df, sampling_meta = _sample_cohorts(
        denied_ranked_df,
        n_customers=int(args.n_customers),
        sample_seed=int(args.sample_seed),
    )

    graph = None
    graph_out = Path(c_cfg.get("graph", {}).get("output_path", "artifacts/models/causal_graph.json"))
    if not graph_out.is_absolute():
        graph_out = (project_root / graph_out).resolve()
    if graph_out.exists():
        from credit_coach.causality.graph_utils import load_graph

        graph = load_graph(graph_out)

    if str(args.output_dir).strip():
        output_root = Path(args.output_dir).expanduser().resolve()
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_root = project_root / "artifacts" / "evaluations" / f"v24_cohort_eval_{timestamp}"
    output_root.mkdir(parents=True, exist_ok=True)

    candidate_plans_path = output_root / "candidate_plans.jsonl"
    path_groupings_path = output_root / "path_groupings.jsonl"
    selected_plans_path = output_root / "selected_plans.jsonl"
    cohort_sample_path = output_root / "cohort_sample.csv"

    customer_rows: list[dict[str, Any]] = []

    with candidate_plans_path.open("w", encoding="utf-8") as candidate_file, \
        path_groupings_path.open("w", encoding="utf-8") as path_file, \
        selected_plans_path.open("w", encoding="utf-8") as selected_file:
        for idx, row in sampled_df.reset_index(drop=True).iterrows():
            result = generate_customer_recourse_artifacts(
                customer_id=_safe_text(row.get("evaluation_customer_id"), f"customer_{idx:06d}"),
                run_id=f"v24_cohort_eval_{args.sample_seed}",
                row=row,
                test_df=population_df,
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

            roadmap_summary = dict(result.bundle.roadmap.get("summary", {}) or {})
            operator_packet = build_operator_review_packet(result.bundle.roadmap)
            operator_metrics = operator_packet_metrics_fields(
                operator_packet,
                packet_relpath=f"operator_packets/{_safe_text(row.get('evaluation_customer_id'))}/operator_packet.json",
            )
            movement = _movement_metrics(
                base_pd=_safe_float(row.get("base_pd"), 0.0),
                tau=tau,
                candidate_pool_df=result.candidate_pool_df,
                paths_df=result.bundle.paths_df,
            )
            metrics_summary = dict(result.bundle.metrics_summary or {})

            rankable_paths = _rankable_paths_df(result.bundle.paths_df)
            path_types = _collect_rankable_path_types(rankable_paths)
            action_categories = _collect_action_categories(rankable_paths)
            action_keys = _collect_action_keys(rankable_paths)
            uses_non_utilization_action = int(
                any(category != "utilization_capacity" for category in action_categories)
            )

            decision_status = _safe_text(roadmap_summary.get("decision_status"))
            selected_status = _safe_text(roadmap_summary.get("selected_decision_status"), decision_status)
            selected_plan_id = _safe_text(
                roadmap_summary.get("best_plan_id"),
                _safe_text(roadmap_summary.get("selected_plan_id")),
            )
            selected_plan_source = ""
            if selected_plan_id:
                selected_plan_rows = result.candidate_pool_df[
                    result.candidate_pool_df.get("plan_id", pd.Series(dtype=object)).astype(str) == selected_plan_id
                ]
                if not selected_plan_rows.empty:
                    selected_plan_source = _safe_text(selected_plan_rows.iloc[0].get("plan_source"))

            fallback_signal = build_recoverability_signal(
                base_pd=_safe_float(row.get("base_pd"), 0.0),
                tau=tau,
                has_valid_path_flag=not result.bundle.paths_df.empty,
                has_rankable_path_flag=not rankable_paths.empty,
                best_possible_pd_improvement=_safe_float(movement["max_path_pd_improvement"], 0.0),
                selection_outcome=_safe_text(roadmap_summary.get("selection_outcome")),
                expected_readiness=_safe_text(roadmap_summary.get("expected_readiness")),
                credit_readiness_stage=_safe_text(roadmap_summary.get("credit_readiness_stage")),
                offer_maturity=_safe_text(roadmap_summary.get("offer_maturity")),
                offer_plan=bool(_safe_int(roadmap_summary.get("offer_plan", 0), 0)),
            )
            recoverability_signal = _resolve_recoverability_signal(
                roadmap_summary=roadmap_summary,
                metrics_summary=metrics_summary,
                fallback_signal=fallback_signal,
            )

            customer_row = {
                "customer_id": _safe_text(row.get("evaluation_customer_id")),
                "source_customer_id": _safe_text(row.get("source_customer_id"), _safe_text(row.get("customer_id"))),
                "source_split": _safe_text(row.get("source_split")),
                "source_row_index": _safe_int(row.get("source_row_index"), 0),
                "sampled_with_replacement": _safe_int(row.get("sampled_with_replacement"), 0),
                "sample_slot_index": _safe_int(row.get("sample_slot_index"), idx),
                "cohort_label": _safe_text(row.get("cohort_label")),
                "base_pd": round(_safe_float(row.get("base_pd"), 0.0), 6),
                "approval_gap": recoverability_signal["approval_gap"],
                "normalized_gap": recoverability_signal["normalized_gap"],
                "risk_band": _safe_text(recoverability_signal.get("risk_band")),
                "recoverability_bucket": _safe_text(recoverability_signal.get("recoverability_bucket")),
                "recoverability_score": _safe_float(recoverability_signal.get("recoverability_score"), 0.0),
                "has_valid_path_flag": _safe_int(recoverability_signal.get("has_valid_path_flag", 0), 0),
                "has_rankable_path_flag": _safe_int(recoverability_signal.get("has_rankable_path_flag", 0), 0),
                "threshold_reach_possible": int(bool(recoverability_signal.get("threshold_reach_possible", False))),
                "hard_structural_blocker_flag": _safe_int(
                    recoverability_signal.get("hard_structural_blocker_flag", 0),
                    0,
                ),
                "soft_structural_blocker_flag": _safe_int(
                    recoverability_signal.get("soft_structural_blocker_flag", 0),
                    0,
                ),
                "structural_blocker_flag": _safe_int(recoverability_signal.get("structural_blocker_flag", 0), 0),
                "hard_structural_blockers_json": _json_dumps(
                    list(recoverability_signal.get("hard_structural_blockers", []) or [])
                ),
                "soft_structural_blockers_json": _json_dumps(
                    list(recoverability_signal.get("soft_structural_blockers", []) or [])
                ),
                "recoverable_flag": int(bool(recoverability_signal.get("recoverable_flag", False))),
                "recoverability_classifier_version": _safe_text(
                    recoverability_signal.get("recoverability_classifier_version")
                ),
                "recoverability_signal_reason_codes_json": _json_dumps(
                    list(recoverability_signal.get("recoverability_signal_reason_codes", []) or [])
                ),
                "recoverable_reason_codes_json": _json_dumps(
                    list(recoverability_signal.get("recoverable_reason_codes", []) or [])
                ),
                "tau": round(tau, 6),
                "decision_status": decision_status,
                "selected_decision_status": selected_status,
                "selected_plan_id": selected_plan_id,
                "selected_plan_status": _safe_text(roadmap_summary.get("selected_plan_status_internal"), _safe_text(roadmap_summary.get("decision_status_internal"))),
                "best_source": selected_plan_source or _safe_text(roadmap_summary.get("selected_recommendation_source")),
                "best_contender_bucket": _safe_text(metrics_summary.get("best_contender_bucket")),
                "best_status": _safe_text(metrics_summary.get("best_status"), selected_status or decision_status),
                "best_offer_maturity": _safe_text(
                    metrics_summary.get("best_offer_maturity"),
                    _safe_text(roadmap_summary.get("offer_maturity"), "none"),
                ),
                "best_execution_aware_value": _safe_float(metrics_summary.get("best_execution_aware_value"), 0.0),
                "candidate_pool_diversity_index": _safe_float(
                    metrics_summary.get("candidate_pool_diversity_index"),
                    0.0,
                ),
                "candidate_source_entropy": _safe_float(metrics_summary.get("candidate_source_entropy"), 0.0),
                "path_count": _safe_int(metrics_summary.get("available_path_count"), len(result.bundle.paths_df)),
                "rankable_path_count": _safe_int(metrics_summary.get("available_rankable_path_count"), len(rankable_paths)),
                "multi_path_flag": _safe_int(
                    metrics_summary.get("multi_path_flag"),
                    int(len(result.bundle.paths_df) > 1),
                ),
                "path_types_json": _json_dumps(path_types),
                "action_categories_json": _json_dumps(action_categories),
                "action_keys_json": _json_dumps(action_keys),
                "action_diversity_index": _safe_float(metrics_summary.get("action_diversity_index"), 0.0),
                "unique_action_count_per_customer": len(action_keys),
                "uses_non_utilization_action": uses_non_utilization_action,
                "non_utilization_action_rate": _safe_float(
                    metrics_summary.get("non_utilization_action_rate"),
                    float(uses_non_utilization_action),
                ),
                "institution_action_rate": _safe_float(
                    metrics_summary.get("institution_action_rate"),
                    float(int("institution" in path_types or "hybrid" in path_types)),
                ),
                "selected_path_type": _safe_text(
                    metrics_summary.get("selected_path_type"),
                    _safe_text(roadmap_summary.get("selected_path_type")),
                ),
                "offer_ready_contender_share": _safe_float(
                    metrics_summary.get("offer_ready_contender_share"),
                    0.0,
                ),
                "approval_shell_only_share": _safe_float(
                    metrics_summary.get("approval_shell_only_share"),
                    0.0,
                ),
                "movement_potential": movement["movement_potential"],
                "max_path_pd_improvement": movement["max_path_pd_improvement"],
                "max_gap_closure_rate": movement["max_gap_closure_rate"],
                "best_reachable_pd": movement["best_reachable_pd"],
                "path_reaches_threshold_flag": movement["path_reaches_threshold_flag"],
                "structural_limit_flag": movement["structural_limit_flag"],
                "selected_invalid_winner_flag": _safe_int(metrics_summary.get("selected_invalid_winner_flag", 0), 0),
                "selected_surface_drift_flag": _selected_surface_drift_flag(roadmap_summary),
                "operator_packet_contradiction_flag": _operator_packet_contradiction_flag(
                    roadmap_summary=roadmap_summary,
                    operator_metrics=operator_metrics,
                ),
                "institution_path_present": int("institution" in path_types),
                "hybrid_path_present": int("hybrid" in path_types),
                "selection_outcome": _safe_text(roadmap_summary.get("selection_outcome")),
            }
            customer_rows.append(customer_row)

            for record in result.candidate_pool_df.to_dict(orient="records"):
                payload = {
                    "customer_id": customer_row["customer_id"],
                    "source_customer_id": customer_row["source_customer_id"],
                    "cohort_label": customer_row["cohort_label"],
                    **record,
                }
                candidate_file.write(json.dumps(payload, ensure_ascii=False) + "\n")

            for record in result.bundle.paths_df.to_dict(orient="records"):
                payload = {
                    "customer_id": customer_row["customer_id"],
                    "source_customer_id": customer_row["source_customer_id"],
                    "cohort_label": customer_row["cohort_label"],
                    **record,
                }
                path_file.write(json.dumps(payload, ensure_ascii=False) + "\n")

            selected_payload = {
                "customer_id": customer_row["customer_id"],
                "source_customer_id": customer_row["source_customer_id"],
                "cohort_label": customer_row["cohort_label"],
                "decision_status": customer_row["decision_status"],
                "selected_decision_status": customer_row["selected_decision_status"],
                "selected_plan_id": customer_row["selected_plan_id"],
                "selected_plan_status": customer_row["selected_plan_status"],
                "best_source": customer_row["best_source"],
                "selection_outcome": customer_row["selection_outcome"],
            }
            selected_file.write(json.dumps(selected_payload, ensure_ascii=False) + "\n")

    customer_df = pd.DataFrame(customer_rows).sort_values(["cohort_label", "approval_gap", "customer_id"]).reset_index(drop=True)
    customer_csv_path = output_root / "customer_level_analysis.csv"
    customer_df.to_csv(customer_csv_path, index=False)
    sampled_df.to_csv(cohort_sample_path, index=False)

    overall_metrics = _aggregate_metrics(customer_df)
    by_cohort_metrics = {
        cohort: _aggregate_metrics(customer_df[customer_df["cohort_label"] == cohort].copy())
        for cohort in COHORT_ORDER
    }
    comparison_rows = _comparison_rows(customer_df)
    examples = _summarize_examples(customer_df)
    diagnosis = _diagnosis_text(overall=overall_metrics, by_cohort=by_cohort_metrics)
    top_insights = _top_five_insights(overall=overall_metrics, by_cohort=by_cohort_metrics)
    phase_60_packages = [
        build_cohort_evidence_package(
            population_name="overall",
            population_metrics=summarize_population_metrics_from_rows(customer_df),
            movement_summary={},
            trust_regression_status=_build_trust_regression_rows(
                population_name="overall",
                metrics=overall_metrics,
            ),
        )
    ]
    for cohort in COHORT_ORDER:
        cohort_df = customer_df[customer_df["cohort_label"] == cohort].copy()
        phase_60_packages.append(
            build_cohort_evidence_package(
                population_name=cohort,
                population_metrics=summarize_population_metrics_from_rows(cohort_df),
                movement_summary={},
                trust_regression_status=_build_trust_regression_rows(
                    population_name=cohort,
                    metrics=by_cohort_metrics[cohort],
                ),
            )
        )
    phase_60_root = output_root / "phase_60"
    phase_60_summary = build_phase60_evidence_summary(phase_60_packages)
    phase_60_files = write_phase60_evidence_artifacts(
        phase_60_root,
        phase_60_summary,
        prefix="phase_60_cohort_eval",
    )

    metrics_payload = {
        "evaluation": {
            "name": "v2.4_cohort_evaluation",
            "sample_size": int(len(customer_df)),
            "sample_seed": int(args.sample_seed),
            "tau": round(tau, 6),
            "dataset_scope": args.dataset_scope,
            "cohort_assignment": "denied approval-gap rank tertiles",
            "movement_classification_note": (
                "strong if a rankable path reaches threshold or closes at least half of the denial gap; "
                "weak if improvement is positive but below that bar; none otherwise"
            ),
            "structural_limit_note": "true when no rankable path reaches the approval threshold",
            "sampling_mode": "with_replacement" if sampling_meta.get("with_replacement") else "without_replacement",
        },
        "sampling": sampling_meta,
        "cohort_boundaries": cohort_boundaries,
        "overall": overall_metrics,
        "by_cohort": by_cohort_metrics,
        "cohort_comparison": comparison_rows,
        "diagnosis": diagnosis,
        "top_5_insights": top_insights,
        "phase_60_evidence_version": _safe_text(phase_60_summary.get("phase_60_evidence_version")),
        "phase_60_overall_movement_conclusion": _safe_text(phase_60_summary.get("overall_movement_conclusion")),
        "phase_60_overall_trust_conclusion": _safe_text(phase_60_summary.get("overall_trust_conclusion")),
        "examples": examples,
        "artifacts": {
            "customer_level_analysis_csv": str(customer_csv_path),
            "cohort_sample_csv": str(cohort_sample_path),
            "candidate_plans_jsonl": str(candidate_plans_path),
            "path_groupings_jsonl": str(path_groupings_path),
            "selected_plans_jsonl": str(selected_plans_path),
            "phase_60_root": str(phase_60_root),
            "phase_60_files": {
                name: str(phase_60_root / filename)
                for name, filename in phase_60_files.items()
            },
        },
    }
    cohort_metrics_path = output_root / "cohort_metrics.json"
    cohort_metrics_path.write_text(json.dumps(metrics_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    report_text = _render_report(
        sampled_df=sampled_df,
        customer_df=customer_df,
        overall=overall_metrics,
        by_cohort=by_cohort_metrics,
        comparison_rows=comparison_rows,
        diagnosis=diagnosis,
        examples=examples,
        cohort_boundaries=cohort_boundaries,
        sampling_meta=sampling_meta,
        dataset_scope=args.dataset_scope,
        output_root=output_root,
    )
    report_path = output_root / "cohort_evaluation_report.md"
    report_path.write_text(report_text, encoding="utf-8")

    print(str(output_root))


if __name__ == "__main__":
    main()
