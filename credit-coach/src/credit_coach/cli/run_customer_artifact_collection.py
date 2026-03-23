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
    _merge_dict,
    _normalize_customer_roadmap_contract,
    _safe_text,
    _sync_metrics_summary_with_roadmap_summary,
    generate_customer_recourse_artifacts,
    write_customer_artifact_bundle,
)
from credit_coach.data.ingest import load_feature_contract
from credit_coach.model.predict import predict_proba_pd
from credit_coach.model.registry import load_model_bundle
from credit_coach.utils.hashing import hash_config
from credit_coach.utils.run_context import create_run_context, load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
logger = logging.getLogger("run_customer_artifact_collection")


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
        choices=("denied_first_near", "union_denied_near", "denied_only", "random_mixed"),
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
    data_issue_codes = list(summary.get("data_issue_codes", []))
    if mismatch_fields and "parity_mismatch" not in data_issue_codes:
        data_issue_codes.append("parity_mismatch")
    data_issue_flag = int(
        bool(_safe_int(summary.get("data_issue_flag", 0), 0))
        or bool(mismatch_fields)
    )
    zero_step_flag = int(_safe_int(summary.get("zero_step_flag", 0), 0))
    if zero_step_flag:
        decision_status = "REJECTED"
        decision_status_internal = "REJECTED"
    elif mismatch_fields:
        decision_status = "CONDITIONAL"
        decision_status_internal = "NEEDS_REVIEW"
    else:
        decision_status = _safe_text(summary.get("decision_status"), "CONDITIONAL")
        decision_status_internal = _safe_text(summary.get("decision_status_internal"), decision_status)
    bundle.roadmap["summary"].update(
        {
            "parity_pass": parity_pass,
            "data_issue_flag": data_issue_flag,
            "data_issue_codes": data_issue_codes,
            "decision_status": decision_status,
            "decision_status_internal": decision_status_internal,
        }
    )
    bundle.roadmap = _normalize_customer_roadmap_contract(bundle.roadmap)
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
    work = input_df.copy()
    if "source_row_index" not in work.columns:
        work = work.reset_index().rename(columns={"index": "source_row_index"})
    else:
        work = work.reset_index(drop=True)
    work["_frame_position"] = range(len(work))
    work["base_pd"] = base_pd.reset_index(drop=True).astype(float).values
    work["denied_base"] = work["base_pd"].astype(float) > float(tau)
    work["risk_band"] = work["base_pd"].map(lambda value: _risk_band_from_pd(float(value), float(tau), segment_caps_cfg))
    work["customer_id"] = [
        _cohort_customer_id(row, fallback=f"customer_{int(row['source_row_index'])}")
        for _, row in work.iterrows()
    ]

    requested = max(1, int(n_customers))
    seed = int(sample_seed)

    def _sample(frame: pd.DataFrame, n: int, random_state: int) -> pd.DataFrame:
        if frame.empty or n <= 0:
            return frame.iloc[0:0].copy()
        keep = min(int(n), len(frame))
        return frame.sample(n=keep, random_state=random_state).copy()

    if cohort_policy == "denied_only":
        selected = _sample(work[work["denied_base"]].copy(), requested, seed)
        selected["selection_reason"] = "denied_only"
    elif cohort_policy == "random_mixed":
        selected = _sample(work, requested, seed)
        selected["selection_reason"] = "random_mixed"
    elif cohort_policy == "union_denied_near":
        union = work[work["denied_base"] | (work["risk_band"].astype(str).str.lower() == "near")].copy()
        selected = _sample(union, requested, seed)
        selected["selection_reason"] = selected["denied_base"].map(lambda denied: "denied_union" if bool(denied) else "near_union")
    else:
        denied = _sample(work[work["denied_base"]].copy(), requested, seed)
        denied["selection_reason"] = "denied"
        remaining = requested - len(denied)
        if remaining > 0:
            near_candidates = work[
                (~work["_frame_position"].isin(denied["_frame_position"]))
                & (work["risk_band"].astype(str).str.lower() == "near")
            ].copy()
            near_fill = _sample(near_candidates, remaining, seed + 1)
            near_fill["selection_reason"] = "near_fill"
            selected = pd.concat([denied, near_fill], ignore_index=True)
        else:
            selected = denied.reset_index(drop=True)

    selected = selected.reset_index(drop=True)
    selected["cohort_policy"] = str(cohort_policy)
    selected["batch_index"] = range(len(selected))
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
    metrics.update(
        {
            "collection_run_id": str(collection_run_id),
            "batch_index": int(selection_row["batch_index"]),
            "source_row_index": int(selection_row["source_row_index"]),
            "selection_reason": str(selection_row["selection_reason"]),
            "cohort_policy": str(selection_row["cohort_policy"]),
            "denied_base": int(selection_row["denied_base"]),
            "best_action_count": int(_safe_int(roadmap_summary.get("best_action_count", 0), 0)),
            "best_cost_usd": best_cost,
            "best_plan_execution_probability": _safe_float(roadmap_summary.get("plan_execution_probability"), 0.0),
            "best_combined_plan_realization_probability": _safe_float(
                roadmap_summary.get("combined_plan_realization_probability"),
                0.0,
            ),
            "data_issue_codes_json": _json_dumps_compact(list(roadmap_summary.get("data_issue_codes", []))),
        }
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
    out.insert(0, "collection_run_id", str(collection_run_id))
    out.insert(1, "batch_index", int(selection_row["batch_index"]))
    out.insert(2, "source_row_index", int(selection_row["source_row_index"]))
    out.insert(3, "customer_id", str(selection_row["customer_id"]))
    out.insert(4, "selection_reason", str(selection_row["selection_reason"]))
    out.insert(5, "cohort_policy", str(selection_row["cohort_policy"]))
    out.insert(6, "selected_best_flag", (out.get("plan_id", pd.Series(dtype=object)).astype(str) == _safe_text(bundle.roadmap.get("best_plan_id"))).astype(int))
    if "action_count" in out.columns:
        out.insert(7, "plan_step_count", pd.to_numeric(out["action_count"], errors="coerce").fillna(0).astype(int))
    else:
        out.insert(7, "plan_step_count", 0)
    plan_contract_pass = pd.Series([pd.NA] * len(out), index=out.index, dtype="object")
    selected_mask = out["selected_best_flag"].astype(int) == 1
    plan_contract_pass.loc[selected_mask] = int(_safe_int(summary.get("raw_contract_pass", 0), 0))
    out.insert(8, "plan_contract_pass", plan_contract_pass)
    return out


def _augment_steps_df(
    *,
    collection_run_id: str,
    selection_row: pd.Series,
    steps_df: pd.DataFrame,
) -> pd.DataFrame:
    out = steps_df.copy()
    out.insert(0, "collection_run_id", str(collection_run_id))
    out.insert(1, "batch_index", int(selection_row["batch_index"]))
    out.insert(2, "source_row_index", int(selection_row["source_row_index"]))
    out.insert(3, "selection_reason", str(selection_row["selection_reason"]))
    out.insert(4, "cohort_policy", str(selection_row["cohort_policy"]))
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
    return "\n".join(
        [
            "# Customer Artifact Collection",
            "",
            f"- Selected customers: {len(selection_df)}",
            f"- Denied-selected: {int(selection_df.get('denied_base', pd.Series(dtype=int)).astype(int).sum())}",
            f"- Near-fill: {int((selection_df.get('selection_reason', pd.Series(dtype=object)) == 'near_fill').sum())}",
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
            "## Contract Health",
            f"- Critical field null rate: {_safe_float(metrics_df.get('critical_field_null_count', pd.Series(dtype=float)).gt(0).mean(), 0.0):.4f}",
            f"- Missing checkpoint status rate: {_safe_float(metrics_df.get('missing_checkpoint_status_count', pd.Series(dtype=float)).gt(0).mean(), 0.0):.4f}",
            f"- Raw contract pass rate: {_safe_float(metrics_df.get('raw_contract_pass', pd.Series(dtype=float)).mean(), 0.0):.4f}",
            f"- Parity mismatch count: {int((metrics_df.get('parity_pass', pd.Series(dtype=float)).fillna(0).astype(int) == 0).sum())}",
            f"- Data issue count: {int(metrics_df.get('data_issue_flag', pd.Series(dtype=float)).fillna(0).astype(int).sum())}",
            "",
            "## Review Files",
            f"- Metrics: `{manifest_rel_root}/flat/customer_metrics.csv`",
            f"- Plans: `{manifest_rel_root}/flat/customer_plans.csv`",
            f"- Roadmap steps: `{manifest_rel_root}/flat/customer_roadmap_steps.csv`",
            f"- Selection: `{manifest_rel_root}/flat/customer_selection.csv`",
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
    selection_df = _selection_frame(
        input_df=test_df,
        base_pd=base_proba,
        tau=tau,
        n_customers=max(1, int(args.n_customers)),
        sample_seed=int(args.sample_seed),
        cohort_policy=str(args.cohort_policy),
        segment_caps_cfg=segment_caps_cfg,
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

    collection_root = run_ctx.tables_dir / "customer_artifact_collection"
    raw_root = collection_root / "raw"
    flat_root = collection_root / "flat"
    raw_root.mkdir(parents=True, exist_ok=True)
    flat_root.mkdir(parents=True, exist_ok=True)

    def _process_selection(selection_row: pd.Series) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
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
        return metrics_row, plans_df, steps_df

    rows = [row for _, row in selection_df.iterrows()]
    metrics_rows: list[dict[str, Any]] = []
    plan_frames: list[pd.DataFrame] = []
    step_frames: list[pd.DataFrame] = []
    n_workers = max(1, int(args.n_workers))
    if n_workers == 1:
        for selection_row in rows:
            metrics_row, plans_df, steps_df = _process_selection(selection_row)
            metrics_rows.append(metrics_row)
            plan_frames.append(plans_df)
            step_frames.append(steps_df)
    else:
        with ThreadPoolExecutor(max_workers=n_workers) as executor:
            futures = {executor.submit(_process_selection, selection_row): selection_row for selection_row in rows}
            for future in as_completed(futures):
                metrics_row, plans_df, steps_df = future.result()
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

    metrics_csv = flat_root / "customer_metrics.csv"
    plans_csv = flat_root / "customer_plans.csv"
    steps_csv = flat_root / "customer_roadmap_steps.csv"
    selection_csv = flat_root / "customer_selection.csv"
    metrics_df.to_csv(metrics_csv, index=False)
    customer_plans_df.to_csv(plans_csv, index=False)
    customer_steps_df.to_csv(steps_csv, index=False)
    selection_out.to_csv(selection_csv, index=False)

    rel_root = "tables/customer_artifact_collection"
    manifest_payload = {
        "collection_run_id": run_ctx.run_id,
        "cohort_policy": str(args.cohort_policy),
        "requested_n_customers": int(args.n_customers),
        "selected_n_customers": int(len(selection_out)),
        "denied_selected_count": int(selection_out["denied_base"].astype(int).sum()) if not selection_out.empty else 0,
        "near_fill_count": int((selection_out["selection_reason"] == "near_fill").sum()) if not selection_out.empty else 0,
        "input_data_path": str(test_path),
        "model_version": str(manifest.get("model_version", "")),
        "config_hash": hash_config(cfg),
        "raw_root": f"{rel_root}/raw",
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
    }
    manifest_path = collection_root / "collection_manifest.json"
    manifest_path.write_text(json.dumps(manifest_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    summary_md = _collection_summary_markdown(
        selection_df=selection_out,
        metrics_df=metrics_df,
        steps_df=customer_steps_df,
        manifest_rel_root=rel_root,
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
