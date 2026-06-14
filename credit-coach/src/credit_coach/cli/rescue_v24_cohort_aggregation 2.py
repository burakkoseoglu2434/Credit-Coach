from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd

from credit_coach.cli import run_v24_cohort_evaluation as v24
from credit_coach.data.ingest import load_feature_contract
from credit_coach.evaluation.cohort_evidence import (
    build_cohort_evidence_package,
    build_phase60_evidence_summary,
    summarize_population_metrics_from_rows,
    write_phase60_evidence_artifacts,
)
from credit_coach.evaluation.recoverability import build_recoverability_signal
from credit_coach.model.predict import predict_proba_pd
from credit_coach.model.registry import load_model_bundle
from credit_coach.utils.run_context import load_config

_SEED_RE = re.compile(r"v24_cohort_eval_(\d+)")
_EVAL_SLOT_RE = re.compile(r"__eval_(\d+)$")
_SOURCE_ID_RE = re.compile(r"^(train|test)_(\d+)$")
_VALID_OFFER_MATURITY = {"none", "inactive", "provisional", "active_rankable"}
_SOURCE_CATALOG: tuple[str, ...] = ("internal", "dice", "rule", "fallback")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Aggregation-only rescue for run_v24_cohort_evaluation: rebuild "
            "customer_level_analysis.csv, cohort_metrics.json, cohort_evaluation_report.md "
            "from existing JSONL artifacts without regenerating candidate plans."
        )
    )
    parser.add_argument("--run_dir", type=str, required=True, help="Existing cohort run directory (output_root).")
    parser.add_argument("--base_config", type=str, default="configs/default.yaml")
    parser.add_argument("--model_config", type=str, default="configs/model.yaml")
    parser.add_argument("--causality_config", type=str, default="configs/causality.yaml")
    parser.add_argument("--dataset_scope", type=str, default="full_processed", choices=["full_processed", "test_only"])
    parser.add_argument("--model_version", type=str, default="")
    parser.add_argument("--model_manifest", type=str, default="")
    parser.add_argument(
        "--customer_manifest_csv",
        type=str,
        default="",
        help="Optional manifest CSV (must match the original run if used).",
    )
    return parser.parse_args(argv)


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            yield json.loads(line)


def _read_first_jsonl(path: Path) -> dict[str, Any] | None:
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            return json.loads(line)
    return None


def _infer_seed(*, candidate_plans_path: Path, selected_plans_path: Path) -> int | None:
    for probe in (candidate_plans_path, selected_plans_path):
        first = _read_first_jsonl(probe)
        if not first:
            continue
        for key in ("plan_id", "selected_plan_id"):
            pid = str(first.get(key, "") or "")
            match = _SEED_RE.search(pid)
            if match:
                return int(match.group(1))
    return None


def _eval_slot(customer_id: str) -> int:
    match = _EVAL_SLOT_RE.search(str(customer_id))
    if not match:
        return -1
    return int(match.group(1))


def _source_id_from_eval(customer_id: str) -> str:
    return str(customer_id).split("__eval_", 1)[0]


def _canonical_plan_source(plan_source: Any, plan_id: Any) -> str:
    explicit = str(plan_source or "").strip().lower()
    if explicit in _SOURCE_CATALOG:
        return explicit
    pid = str(plan_id or "")
    if "_fallback_" in pid:
        return "fallback"
    if "_dice_" in pid:
        return "dice"
    if "_rule_" in pid:
        return "rule"
    return "internal"


def _normalized_offer_maturity(record: Mapping[str, Any]) -> str:
    explicit = str(record.get("offer_maturity", "") or "").strip().lower()
    if explicit in _VALID_OFFER_MATURITY:
        return explicit
    offer_plan = bool(record.get("offer_plan", False))
    if not offer_plan:
        return "none"
    approval_pending = v24._safe_int(record.get("approval_pending_action_count", 0), 0)
    rankable_offer = v24._safe_int(record.get("rankable_offer_count", 0), 0)
    if approval_pending > 0:
        return "provisional"
    if rankable_offer > 0:
        return "active_rankable"
    return "inactive"


def _safe_float(value: Any, default: float = 0.0) -> float:
    return v24._safe_float(value, default)


def _safe_text(value: Any, default: str = "") -> str:
    return v24._safe_text(value, default)


def _jaccard_distance(a: set[str], b: set[str]) -> float:
    union = len(a | b)
    if union <= 0:
        return 0.0
    return float(1.0 - (len(a & b) / union))


def _candidate_pool_diversity_index(candidate_pool: list[dict[str, Any]]) -> float:
    signatures: list[set[str]] = []
    for record in candidate_pool:
        raw_sig = record.get("path_signature")
        if not raw_sig:
            continue
        try:
            sig_obj = json.loads(raw_sig) if isinstance(raw_sig, str) else raw_sig
        except Exception:
            continue
        action_keys = sig_obj.get("action_keys") if isinstance(sig_obj, dict) else None
        if not isinstance(action_keys, list):
            continue
        keys = {str(value).strip() for value in action_keys if str(value).strip()}
        if keys:
            signatures.append(keys)
    if len(signatures) <= 1:
        return 0.0
    distances: list[float] = []
    for i in range(len(signatures)):
        for j in range(i + 1, len(signatures)):
            distances.append(_jaccard_distance(signatures[i], signatures[j]))
    if not distances:
        return 0.0
    return float(sum(distances) / float(len(distances)))


def _candidate_source_entropy(candidate_pool: list[dict[str, Any]]) -> float:
    if not candidate_pool:
        return 0.0
    counts = {source: 0 for source in _SOURCE_CATALOG}
    for record in candidate_pool:
        counts[_canonical_plan_source(record.get("plan_source"), record.get("plan_id"))] += 1
    total = float(len(candidate_pool))
    nonzero = [count for count in counts.values() if count > 0]
    if not nonzero:
        return 0.0
    entropy = 0.0
    for count in nonzero:
        probability = float(count) / total
        if probability > 0.0:
            entropy -= probability * math.log(probability, 2.0)
    max_entropy = math.log(max(1, len(nonzero)), 2.0)
    if max_entropy <= 0.0:
        return 0.0
    return float(entropy / max_entropy)


def _execution_aware_value(record: dict[str, Any]) -> float:
    explicit = record.get("expected_recovery_proxy")
    if explicit is not None:
        return max(0.0, _safe_float(explicit, 0.0))
    return max(0.0, _safe_float(record.get("expected_pd_improvement"), 0.0))


def _path_action_diversity_index(paths_df: pd.DataFrame) -> float:
    if paths_df.empty:
        return 0.0
    rankable = paths_df[paths_df.get("rankable_flag", pd.Series(dtype=bool)).astype(bool)].copy()
    if rankable.empty:
        return 0.0
    action_sets: list[set[str]] = []
    for raw in rankable.get("action_keys", pd.Series(dtype=object)).tolist():
        values = raw if isinstance(raw, list) else v24._json_loads_list(raw)
        keys = {str(value).strip() for value in values if str(value).strip()}
        if keys:
            action_sets.append(keys)
    if len(action_sets) <= 1:
        return 0.0
    distances: list[float] = []
    for idx, left in enumerate(action_sets):
        for right in action_sets[idx + 1:]:
            distances.append(_jaccard_distance(left, right))
    if not distances:
        return 0.0
    return float(sum(distances) / float(len(distances)))


def _non_utilization_action_rate(paths_df: pd.DataFrame) -> float:
    if paths_df.empty:
        return 0.0
    rankable = paths_df[paths_df.get("rankable_flag", pd.Series(dtype=bool)).astype(bool)].copy()
    if rankable.empty:
        return 0.0
    count = 0
    for raw in rankable.get("action_categories", pd.Series(dtype=object)).tolist():
        values = raw if isinstance(raw, list) else v24._json_loads_list(raw)
        if any(_safe_text(value) and _safe_text(value) != "utilization_capacity" for value in values):
            count += 1
    return float(count / max(1, len(rankable)))


def _institution_action_rate(paths_df: pd.DataFrame) -> float:
    if paths_df.empty:
        return 0.0
    rankable = paths_df[paths_df.get("rankable_flag", pd.Series(dtype=bool)).astype(bool)].copy()
    if rankable.empty:
        return 0.0
    count = int(
        sum(1 for value in rankable.get("path_type", pd.Series(dtype=object)).astype(str).tolist() if value in {"institution_assisted", "hybrid"})
    )
    return float(count / max(1, len(rankable)))


def run(args: argparse.Namespace) -> dict[str, str]:
    run_dir = Path(args.run_dir).expanduser().resolve()
    candidate_plans_path = run_dir / "candidate_plans.jsonl"
    path_groupings_path = run_dir / "path_groupings.jsonl"
    selected_plans_path = run_dir / "selected_plans.jsonl"

    if not selected_plans_path.exists():
        raise FileNotFoundError(f"Missing required artifact: {selected_plans_path}")
    if selected_plans_path.stat().st_size <= 0:
        raise ValueError(f"selected_plans.jsonl is empty: {selected_plans_path}")
    if not candidate_plans_path.exists():
        raise FileNotFoundError(f"Missing required artifact: {candidate_plans_path}")
    if not path_groupings_path.exists():
        raise FileNotFoundError(f"Missing required artifact: {path_groupings_path}")

    selected_by_customer: dict[str, dict[str, Any]] = {}
    ordered_customers: list[str] = []
    for obj in _iter_jsonl(selected_plans_path):
        customer_id = _safe_text(obj.get("customer_id"))
        if not customer_id:
            continue
        ordered_customers.append(customer_id)
        selected_by_customer[customer_id] = dict(obj)
    if not ordered_customers:
        raise ValueError(f"selected_plans.jsonl contains no usable rows: {selected_plans_path}")

    sample_size = int(len(ordered_customers))

    inferred_seed = _infer_seed(candidate_plans_path=candidate_plans_path, selected_plans_path=selected_plans_path)
    if inferred_seed is None:
        raise ValueError("Unable to infer sample_seed from artifacts (missing v24_cohort_eval_<seed> in plan ids).")

    project_root = Path(__file__).resolve().parents[3]
    base_config_path = v24._resolve_repo_path(args.base_config, project_root=project_root)
    model_config_path = v24._resolve_repo_path(args.model_config, project_root=project_root)
    causality_config_path = v24._resolve_repo_path(args.causality_config, project_root=project_root)

    base_cfg = load_config(base_config_path)
    model_cfg = load_config(model_config_path)
    c_cfg = load_config(causality_config_path)

    features_config_path = v24._resolve_repo_path(
        base_cfg.get("features_config", "configs/features_48.yaml"),
        project_root=project_root,
    )
    contract = load_feature_contract(features_config_path)
    feature_cols = contract["features"]
    target_col = contract["target"]

    population_df, train_df = v24._load_population(
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
        lambda value: v24.compute_approval_gap(base_pd=float(value), tau=tau)
    )

    denied_df = population_df[population_df["denied_base"].astype(int) == 1].copy()
    denied_ranked_df, cohort_boundaries = v24._assign_gap_tertile_cohorts(denied_df)

    sampled_df: pd.DataFrame
    sampling_meta: dict[str, Any]
    manifest_csv = _safe_text(getattr(args, "customer_manifest_csv", ""))
    if manifest_csv:
        manifest_path = v24._resolve_repo_path(manifest_csv, project_root=project_root)
        manifest_ids = v24._load_customer_manifest_ids(manifest_path)
        sampled_df, sampling_meta = v24._select_manifest_customers(
            denied_ranked_df,
            manifest_ids=manifest_ids,
            manifest_path=manifest_path,
        )
    else:
        sampled_df, sampling_meta = v24._sample_cohorts(
            denied_ranked_df,
            n_customers=sample_size,
            sample_seed=inferred_seed,
        )

    expected_ids = set(sampled_df.get("evaluation_customer_id", pd.Series(dtype=object)).astype(str).tolist())
    observed_ids = set(ordered_customers)
    sampling_matches = expected_ids == observed_ids
    if not sampling_matches:
        # Fallback: reconstruct sampled_df directly from observed evaluation ids.
        manifest_df = pd.DataFrame(
            {
                "customer_id": pd.Series([_source_id_from_eval(cid) for cid in ordered_customers], dtype=object),
                "evaluation_customer_id": pd.Series(list(ordered_customers), dtype=object),
                "sample_slot_index": pd.Series([_eval_slot(cid) for cid in ordered_customers], dtype=int),
            }
        )
        joined = denied_ranked_df.merge(manifest_df, on="customer_id", how="inner")
        if len(joined) != sample_size:
            missing = sorted(set(manifest_df["customer_id"].astype(str).tolist()) - set(joined["customer_id"].astype(str).tolist()))
            raise ValueError(
                "Unable to reconstruct sampled cohort rows from artifacts. "
                f"Missing {len(missing)} source_customer_id values in denied population (first 5: {missing[:5]})."
            )
        sampled_df = joined.sort_values(["sample_slot_index", "approval_gap", "customer_id"], ascending=[True, True, True], kind="stable").reset_index(drop=True)
        sampled_df["source_customer_id"] = sampled_df["customer_id"].astype(str)
        sampling_meta = {
            "requested_n": int(sample_size),
            "unique_denied_available": int(len(denied_ranked_df)),
            "realized_sample_n": int(sample_size),
            "with_replacement": bool(sampled_df["source_customer_id"].nunique() < len(sampled_df)),
            "unique_source_customers_in_sample": int(sampled_df["source_customer_id"].nunique()),
            "reused_draw_count": int(len(sampled_df) - sampled_df["source_customer_id"].nunique()),
            "rescue_sampling_fallback": True,
        }

    sampled_df = sampled_df.copy()
    sampled_df["base_pd"] = sampled_df["base_pd"].astype(float)
    sampled_df["approval_gap"] = sampled_df["approval_gap"].astype(float)

    sampled_lookup = {
        _safe_text(row.get("evaluation_customer_id")): row
        for row in sampled_df.to_dict(orient="records")
        if _safe_text(row.get("evaluation_customer_id"))
    }

    candidate_by_customer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in _iter_jsonl(candidate_plans_path):
        customer_id = _safe_text(record.get("customer_id"))
        if customer_id in selected_by_customer:
            candidate_by_customer[customer_id].append(dict(record))

    paths_by_customer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in _iter_jsonl(path_groupings_path):
        customer_id = _safe_text(record.get("customer_id"))
        if customer_id in selected_by_customer:
            paths_by_customer[customer_id].append(dict(record))

    customer_rows: list[dict[str, Any]] = []
    for customer_id in ordered_customers:
        selected = selected_by_customer.get(customer_id, {})
        sampled_row = sampled_lookup.get(customer_id)
        if sampled_row is None:
            raise ValueError(f"Sample reconstruction missing customer_id={customer_id}")

        candidate_pool = candidate_by_customer.get(customer_id, [])
        candidate_pool_df = pd.DataFrame(candidate_pool)

        paths_records = paths_by_customer.get(customer_id, [])
        paths_df = pd.DataFrame(paths_records)

        base_pd = _safe_float(sampled_row.get("base_pd"), 0.0)
        approval_gap = _safe_float(sampled_row.get("approval_gap"), 0.0)

        movement = v24._movement_metrics(
            base_pd=base_pd,
            tau=tau,
            candidate_pool_df=candidate_pool_df,
            paths_df=paths_df,
        )

        rankable_paths = v24._rankable_paths_df(paths_df)
        path_types = v24._collect_rankable_path_types(rankable_paths)
        action_categories = v24._collect_action_categories(rankable_paths)
        action_keys = v24._collect_action_keys(rankable_paths)
        uses_non_utilization_action = int(any(category != "utilization_capacity" for category in action_categories))

        decision_status = _safe_text(selected.get("decision_status"))
        selected_status = _safe_text(selected.get("selected_decision_status"), decision_status)
        selected_plan_id = _safe_text(selected.get("selected_plan_id"))
        selected_plan_status = _safe_text(selected.get("selected_plan_status"))
        selection_outcome = _safe_text(selected.get("selection_outcome"))

        selected_plan_record: dict[str, Any] | None = None
        if selected_plan_id and not candidate_pool_df.empty:
            matches = candidate_pool_df[
                candidate_pool_df.get("plan_id", pd.Series(dtype=object)).astype(str) == selected_plan_id
            ]
            if not matches.empty:
                selected_plan_record = matches.iloc[0].to_dict()

        selected_action_count = 0
        selected_plan_source = ""
        if selected_plan_record:
            selected_action_count = v24._safe_int(selected_plan_record.get("action_count", 0), 0)
            selected_plan_source = _safe_text(selected_plan_record.get("plan_source"))
        selected_action_count = v24._safe_int(selected.get("selected_action_count", selected_action_count), selected_action_count)
        selected_recommendation_source = _safe_text(
            selected.get("selected_recommendation_source"),
            "selected_plan" if selected_plan_id else "empty_state",
        )

        offer_maturity = _safe_text((selected_plan_record or {}).get("offer_maturity"), "")
        offer_plan = v24._safe_int((selected_plan_record or {}).get("offer_plan", 0), 0)

        fallback_signal = build_recoverability_signal(
            base_pd=base_pd,
            tau=tau,
            has_valid_path_flag=not paths_df.empty,
            has_rankable_path_flag=not rankable_paths.empty,
            best_possible_pd_improvement=_safe_float(movement.get("max_path_pd_improvement"), 0.0),
            selection_outcome=selection_outcome,
            expected_readiness="",
            credit_readiness_stage="",
            offer_maturity=offer_maturity,
            offer_plan=bool(offer_plan),
        )
        recoverability_signal = v24._resolve_recoverability_signal(
            roadmap_summary={},
            metrics_summary={},
            fallback_signal=fallback_signal,
        )
        # run_v24_cohort_evaluation normally reads this from the roadmap summary; in rescue mode
        # we use the gate emitted by build_recoverability_signal to keep behavior deterministic.
        recourse_gate = {
            "recourse_mode": _safe_text(recoverability_signal.get("recourse_mode")),
            "recommendation_mode": _safe_text(recoverability_signal.get("recommendation_mode")),
            "recourse_gate_version": _safe_text(recoverability_signal.get("recourse_gate_version")),
            "recourse_gate_reason_codes": list(recoverability_signal.get("recourse_gate_reason_codes", []) or []),
        }

        recoverable_flag = int(bool(recoverability_signal.get("recoverable_flag", False)))
        recourse_mode = _safe_text(recourse_gate.get("recourse_mode"))
        primary_population = v24._targeted_population_label(
            recoverable_flag=recoverable_flag,
            recourse_mode=recourse_mode,
        )

        selected_path_type = ""
        if not paths_df.empty and "selected_path_flag" in paths_df.columns:
            flagged = paths_df[paths_df["selected_path_flag"].astype(bool)]
            if not flagged.empty:
                selected_path_type = _safe_text(flagged.iloc[0].get("path_type"))

        candidate_pool_diversity_index = _candidate_pool_diversity_index(candidate_pool)
        candidate_source_entropy = _candidate_source_entropy(candidate_pool)
        offer_ready_contender_share = 0.0
        approval_shell_only_share = 0.0
        if candidate_pool:
            offer_ready_contender_share = float(
                sum(1 for plan in candidate_pool if _normalized_offer_maturity(plan) == "active_rankable")
                / max(1, len(candidate_pool))
            )
            approval_shell_only_share = float(
                sum(
                    1
                    for plan in candidate_pool
                    if str(plan.get("contender_bucket", "") or "").strip().upper() == "APPROVAL_SHELL_ONLY"
                )
                / max(1, len(candidate_pool))
            )

        best_contender_bucket = _safe_text((selected_plan_record or {}).get("contender_bucket"))
        best_status = _safe_text((selected_plan_record or {}).get("status"), selected_plan_status or selected_status or decision_status)
        best_offer_maturity = _safe_text((selected_plan_record or {}).get("offer_maturity"), offer_maturity or "none")
        best_execution_aware_value = 0.0 if not selected_plan_record else _execution_aware_value(selected_plan_record)

        selected_invalid_winner_flag = 0
        if selected_plan_record and selection_outcome == "selected_valid_winner":
            if _safe_text(selected_plan_record.get("recommendation_validity_status")) == "invalid":
                selected_invalid_winner_flag = 1

        selected_surface_drift_flag = int(decision_status != selected_status)
        operator_packet_contradiction_flag = 0

        path_count = int(len(paths_df)) if not paths_df.empty else 0
        rankable_path_count = int(len(rankable_paths)) if not rankable_paths.empty else 0
        action_diversity_index = _path_action_diversity_index(paths_df)
        non_utilization_action_rate = _non_utilization_action_rate(paths_df)
        institution_action_rate = _institution_action_rate(paths_df)

        customer_row = {
            "customer_id": customer_id,
            "source_customer_id": _safe_text(selected.get("source_customer_id"), _safe_text(sampled_row.get("source_customer_id"))),
            "source_split": _safe_text(sampled_row.get("source_split")),
            "source_row_index": v24._safe_int(sampled_row.get("source_row_index"), 0),
            "sampled_with_replacement": v24._safe_int(sampled_row.get("sampled_with_replacement"), 0),
            "sample_slot_index": v24._safe_int(sampled_row.get("sample_slot_index"), _eval_slot(customer_id)),
            "cohort_label": _safe_text(selected.get("cohort_label"), _safe_text(sampled_row.get("cohort_label"))),
            "base_pd": round(base_pd, 6),
            "approval_gap": _safe_float(recoverability_signal.get("approval_gap"), approval_gap),
            "normalized_gap": _safe_float(recoverability_signal.get("normalized_gap"), 0.0),
            "risk_band": _safe_text(recoverability_signal.get("risk_band")),
            "recoverability_bucket": _safe_text(recoverability_signal.get("recoverability_bucket")),
            "recoverability_score": _safe_float(recoverability_signal.get("recoverability_score"), 0.0),
            "has_valid_path_flag": v24._safe_int(recoverability_signal.get("has_valid_path_flag", 0), 0),
            "has_rankable_path_flag": v24._safe_int(recoverability_signal.get("has_rankable_path_flag", 0), 0),
            "threshold_reach_possible": int(bool(recoverability_signal.get("threshold_reach_possible", False))),
            "hard_structural_blocker_flag": v24._safe_int(recoverability_signal.get("hard_structural_blocker_flag", 0), 0),
            "soft_structural_blocker_flag": v24._safe_int(recoverability_signal.get("soft_structural_blocker_flag", 0), 0),
            "structural_blocker_flag": v24._safe_int(recoverability_signal.get("structural_blocker_flag", 0), 0),
            "hard_structural_blockers_json": json.dumps(
                list(recoverability_signal.get("hard_structural_blockers", []) or []),
                ensure_ascii=False,
            ),
            "soft_structural_blockers_json": json.dumps(
                list(recoverability_signal.get("soft_structural_blockers", []) or []),
                ensure_ascii=False,
            ),
            "recoverable_flag": recoverable_flag,
            "recoverability_classifier_version": _safe_text(recoverability_signal.get("recoverability_classifier_version")),
            "recoverability_signal_reason_codes_json": json.dumps(
                list(recoverability_signal.get("recoverability_signal_reason_codes", []) or []),
                ensure_ascii=False,
            ),
            "recoverable_reason_codes_json": json.dumps(
                list(recoverability_signal.get("recoverable_reason_codes", []) or []),
                ensure_ascii=False,
            ),
            "recourse_mode": _safe_text(recourse_gate.get("recourse_mode")),
            "recommendation_mode": _safe_text(recourse_gate.get("recommendation_mode")),
            "recourse_gate_version": _safe_text(recourse_gate.get("recourse_gate_version")),
            "recourse_gate_reason_codes_json": json.dumps(
                list(recourse_gate.get("recourse_gate_reason_codes", []) or []),
                ensure_ascii=False,
            ),
            "selected_recommendation_source": selected_recommendation_source,
            "selected_action_count": int(selected_action_count),
            "selected_recommendation_text": _safe_text(selected.get("selected_recommendation_text")),
            "selected_recommendation_projection_version": _safe_text(selected.get("selected_recommendation_projection_version")),
            "translated_from_latent": bool(selected.get("translated_from_latent", False)),
            "latent_plan_type": _safe_text(selected.get("latent_plan_type")),
            "translated_action_text": _safe_text(selected.get("translated_action_text")),
            "translation_confidence": _safe_text(selected.get("translation_confidence")),
            "primary_population": primary_population,
            "in_global_denied_population": 1,
            "in_recoverable_full_mode_population": int(primary_population == "recoverable_full_mode"),
            "in_non_recoverable_limited_mode_population": int(primary_population == "non_recoverable_limited_mode"),
            "empty_state_flag": int(selected_recommendation_source == "empty_state"),
            "zero_action_flag": int(int(selected_action_count) == 0),
            "tau": round(float(tau), 6),
            "decision_status": decision_status,
            "selected_decision_status": selected_status,
            "selected_plan_id": selected_plan_id,
            "selected_plan_status": selected_plan_status,
            "best_source": _safe_text(selected.get("best_source"), selected_plan_source),
            "best_contender_bucket": best_contender_bucket,
            "best_status": best_status,
            "best_offer_maturity": best_offer_maturity,
            "best_execution_aware_value": _safe_float(best_execution_aware_value, 0.0),
            "candidate_pool_diversity_index": _safe_float(candidate_pool_diversity_index, 0.0),
            "candidate_source_entropy": _safe_float(candidate_source_entropy, 0.0),
            "path_count": path_count,
            "rankable_path_count": rankable_path_count,
            "multi_path_flag": int(rankable_path_count > 1),
            "path_types_json": json.dumps(list(path_types), ensure_ascii=False),
            "action_categories_json": json.dumps(list(action_categories), ensure_ascii=False),
            "action_keys_json": json.dumps(list(action_keys), ensure_ascii=False),
            "action_diversity_index": _safe_float(action_diversity_index, 0.0),
            "unique_action_count_per_customer": int(len(action_keys)),
            "uses_non_utilization_action": uses_non_utilization_action,
            "non_utilization_action_rate": _safe_float(non_utilization_action_rate, float(uses_non_utilization_action)),
            "institution_action_rate": _safe_float(institution_action_rate, 0.0),
            "selected_path_type": selected_path_type,
            "movement_score": _safe_float(selected.get("movement_score"), 0.0),
            "threshold_reach_probability": _safe_float(selected.get("threshold_reach_probability"), 0.0),
            "threshold_reach_priority_flag": v24._safe_int(selected.get("threshold_reach_priority_flag"), 0),
            "selected_path_movement_strength": _safe_text(selected.get("selected_path_movement_strength")),
            "movement_rank_reason_codes_json": _safe_text(selected.get("movement_rank_reason_codes_json"), "[]"),
            "offer_ready_contender_share": _safe_float(offer_ready_contender_share, 0.0),
            "approval_shell_only_share": _safe_float(approval_shell_only_share, 0.0),
            "movement_potential": _safe_text(movement.get("movement_potential")),
            "max_path_pd_improvement": _safe_float(movement.get("max_path_pd_improvement"), 0.0),
            "max_gap_closure_rate": _safe_float(movement.get("max_gap_closure_rate"), 0.0),
            "best_reachable_pd": _safe_float(movement.get("best_reachable_pd"), base_pd),
            "path_reaches_threshold_flag": v24._safe_int(movement.get("path_reaches_threshold_flag"), 0),
            "structural_limit_flag": v24._safe_int(movement.get("structural_limit_flag"), 1),
            "selected_invalid_winner_flag": selected_invalid_winner_flag,
            "selected_surface_drift_flag": selected_surface_drift_flag,
            "operator_packet_contradiction_flag": operator_packet_contradiction_flag,
            "institution_path_present": int("institution" in path_types),
            "hybrid_path_present": int("hybrid" in path_types),
            "selection_outcome": selection_outcome,
        }
        customer_rows.append(customer_row)

    customer_df = (
        pd.DataFrame(customer_rows)
        .sort_values(["cohort_label", "approval_gap", "customer_id"])
        .reset_index(drop=True)
    )
    customer_csv_path = run_dir / "customer_level_analysis.csv"
    cohort_sample_path = run_dir / "cohort_sample.csv"
    customer_df.to_csv(customer_csv_path, index=False)
    sampled_df.to_csv(cohort_sample_path, index=False)

    overall_metrics = v24._aggregate_metrics(customer_df)
    targeted_population_metrics = v24._targeted_population_metrics(customer_df)
    targeted_comparison = v24._targeted_comparison_payload(targeted_population_metrics)
    targeted_evaluation_result = v24._targeted_evaluation_result(targeted_comparison)
    by_cohort_metrics = {
        cohort: v24._aggregate_metrics(customer_df[customer_df["cohort_label"] == cohort].copy())
        for cohort in v24.COHORT_ORDER
    }
    comparison_rows = v24._comparison_rows(customer_df)
    examples = v24._summarize_examples(customer_df)
    diagnosis = v24._diagnosis_text(overall=overall_metrics, by_cohort=by_cohort_metrics)
    top_insights = v24._top_five_insights(overall=overall_metrics, by_cohort=by_cohort_metrics)

    phase_60_packages = [
        build_cohort_evidence_package(
            population_name="overall",
            population_metrics=summarize_population_metrics_from_rows(customer_df),
            movement_summary={},
            trust_regression_status=v24._build_trust_regression_rows(
                population_name="overall",
                metrics=overall_metrics,
            ),
        )
    ]
    for population_name, population_df in {
        "global_denied": customer_df.copy(),
        "recoverable_full_mode": customer_df[customer_df["primary_population"] == "recoverable_full_mode"].copy(),
        "non_recoverable_limited_mode": customer_df[
            customer_df["primary_population"] == "non_recoverable_limited_mode"
        ].copy(),
    }.items():
        phase_60_packages.append(
            build_cohort_evidence_package(
                population_name=population_name,
                population_metrics=summarize_population_metrics_from_rows(population_df),
                movement_summary={},
                trust_regression_status=v24._build_trust_regression_rows(
                    population_name=population_name,
                    metrics=v24._aggregate_metrics(population_df),
                ),
            )
        )
    for cohort in v24.COHORT_ORDER:
        cohort_df = customer_df[customer_df["cohort_label"] == cohort].copy()
        phase_60_packages.append(
            build_cohort_evidence_package(
                population_name=cohort,
                population_metrics=summarize_population_metrics_from_rows(cohort_df),
                movement_summary={},
                trust_regression_status=v24._build_trust_regression_rows(
                    population_name=cohort,
                    metrics=by_cohort_metrics[cohort],
                ),
            )
        )
    phase_60_root = run_dir / "phase_60"
    phase_60_summary = build_phase60_evidence_summary(phase_60_packages)
    phase_60_files = write_phase60_evidence_artifacts(
        phase_60_root,
        phase_60_summary,
        prefix="phase_60_cohort_eval",
    )

    metrics_payload = {
        "evaluation": {
            "name": "v2.5_targeted_cohort_evaluation",
            "sample_size": int(len(customer_df)),
            "sample_seed": int(inferred_seed),
            "tau": round(float(tau), 6),
            "dataset_scope": args.dataset_scope,
            "cohort_assignment": "denied approval-gap rank tertiles",
            "primary_comparison": "recoverable_full_mode_vs_global_denied",
            "honesty_control_population": "non_recoverable_limited_mode",
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
        "population_metrics": targeted_population_metrics,
        "targeted_comparison": targeted_comparison,
        "targeted_evaluation_result": targeted_evaluation_result,
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
            "phase_60_files": {name: str(phase_60_root / filename) for name, filename in phase_60_files.items()},
        },
    }
    cohort_metrics_path = run_dir / "cohort_metrics.json"
    cohort_metrics_path.write_text(json.dumps(metrics_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    report_text = v24._render_report(
        sampled_df=sampled_df,
        customer_df=customer_df,
        overall=overall_metrics,
        targeted_comparison=targeted_comparison,
        by_cohort=by_cohort_metrics,
        comparison_rows=comparison_rows,
        diagnosis=diagnosis,
        examples=examples,
        cohort_boundaries=cohort_boundaries,
        sampling_meta=sampling_meta,
        dataset_scope=args.dataset_scope,
        output_root=run_dir,
    )
    report_path = run_dir / "cohort_evaluation_report.md"
    report_path.write_text(report_text, encoding="utf-8")

    trust_counters_present = all(
        key in overall_metrics
        for key in (
            "selected_invalid_winner_count",
            "selected_surface_drift_count",
            "operator_packet_contradiction_count",
        )
    )
    print(f"[rescue] sample_size={sample_size}")
    print(f"[rescue] inferred_seed={inferred_seed}")
    print(f"[rescue] trust_counters_present={trust_counters_present} (operator_packet_contradiction assumes 0 in rescue)")
    print(f"[rescue] wrote: {customer_csv_path}")
    print(f"[rescue] wrote: {cohort_sample_path}")
    print(f"[rescue] wrote: {cohort_metrics_path}")
    print(f"[rescue] wrote: {report_path}")
    return {
        "customer_level_analysis_csv": str(customer_csv_path),
        "cohort_sample_csv": str(cohort_sample_path),
        "cohort_metrics_json": str(cohort_metrics_path),
        "cohort_evaluation_report_md": str(report_path),
    }


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
