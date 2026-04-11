from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any

import pandas as pd

from credit_coach.cli.run_recourse import generate_customer_recourse_artifacts
from credit_coach.data.ingest import load_feature_contract
from credit_coach.model.registry import load_model_bundle
from credit_coach.ops.operator_review import (
    build_operator_review_packet,
    operator_packet_metrics_fields,
    render_operator_review_packet_markdown,
)
from credit_coach.utils.run_context import load_config


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    credit_coach_root = (repo_root / "credit-coach").resolve()
    out_dir = (repo_root / ".planning/phases/68-real-cohort-evidence-run/68-01-operator-packet-contradictions/out").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    os.chdir(credit_coach_root)

    run_dir = Path("artifacts/evaluations/v25_real_cohort_eval_20260411_full_processed_all_denied_n367_seed42").resolve()

    customer_df = pd.read_csv(run_dir / "customer_level_analysis.csv")
    cohort_sample = pd.read_csv(run_dir / "cohort_sample.csv")
    bad_rows = customer_df[customer_df["operator_packet_contradiction_flag"].fillna(0).astype(int) == 1].copy()
    bad_ids = bad_rows["customer_id"].astype(str).tolist()

    base_cfg = load_config(Path("configs/default.yaml"))
    model_cfg = load_config(Path("configs/model.yaml"))
    rec_cfg = load_config(Path("configs/recourse.yaml"))
    c_cfg = load_config(Path("configs/causality.yaml"))
    s_cfg = load_config(Path("configs/safety.yaml"))
    m_cfg = load_config(Path("configs/macro.yaml"))

    features_config_path = Path(base_cfg.get("features_config", "configs/features_48.yaml"))
    contract = load_feature_contract(features_config_path)
    feature_cols = contract["features"]
    target_col = contract["target"]

    processed_root = Path(base_cfg.get("paths", {}).get("processed_data", "data/processed"))
    train_df = pd.read_parquet(processed_root / "train.parquet").copy()
    test_df = pd.read_parquet(processed_root / "test.parquet").copy()
    population_df = pd.concat([train_df, test_df], ignore_index=True)

    model, calibrator, manifest, _ = load_model_bundle(
        base_path=model_cfg.get("registry", {}).get("path", "artifacts/models")
    )

    cases: list[dict[str, Any]] = []
    for customer_id in bad_ids:
        cohort_row = cohort_sample.loc[cohort_sample["evaluation_customer_id"].astype(str) == str(customer_id)]
        if cohort_row.empty:
            raise RuntimeError(f"Missing cohort_sample row for {customer_id}")
        row = cohort_row.iloc[0]

        result = generate_customer_recourse_artifacts(
            customer_id=str(row.get("evaluation_customer_id")),
            run_id="phase_68_operator_packet_investigation",
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
            graph=None,
            persist_repository_records=False,
        )

        roadmap_summary = dict(result.bundle.roadmap.get("summary", {}) or {})
        operator_packet = build_operator_review_packet(result.bundle.roadmap)
        operator_metrics = operator_packet_metrics_fields(
            operator_packet,
            packet_relpath=f"operator_packets/{customer_id}/operator_packet.json",
        )

        decision_status = _safe_text(roadmap_summary.get("decision_status"))
        selected_decision_status = _safe_text(roadmap_summary.get("selected_decision_status"))
        selection_outcome = _safe_text(roadmap_summary.get("selection_outcome"))
        selected_recommendation_source = _safe_text(roadmap_summary.get("selected_recommendation_source"))

        op_selected_status = _safe_text(operator_metrics.get("operator_selected_decision_status"))
        op_readiness_mode = _safe_text(operator_metrics.get("operator_readiness_render_mode"))
        op_blockers = int(operator_metrics.get("operator_rendered_blocker_count", 0) or 0)
        op_actions = int(operator_metrics.get("operator_rendered_action_count", 0) or 0)
        op_upgrade_text = _safe_text(operator_metrics.get("operator_upgrade_condition_text"))
        coherence_codes_json = _safe_text(operator_metrics.get("operator_packet_coherence_codes_json"))

        approved_packet_with_blockers = op_selected_status == "APPROVED" and op_blockers > 0
        approved_packet_with_actions = op_selected_status == "APPROVED" and op_actions > 0
        approved_packet_with_upgrade = op_selected_status == "APPROVED" and bool(op_upgrade_text)
        readiness_mismatch = (
            (selection_outcome == "no_valid_winner" and op_readiness_mode != "empty_state_context")
            or (
                selection_outcome != "no_valid_winner"
                and op_selected_status == "APPROVED"
                and op_readiness_mode != "approved_info"
            )
        )
        action_blocker_mismatch = "action_blocker_mismatch" in (coherence_codes_json or "")
        decision_mismatch = decision_status != op_selected_status

        contradiction_flags = {
            "approved_packet_with_blockers": approved_packet_with_blockers,
            "approved_packet_with_actions": approved_packet_with_actions,
            "approved_packet_with_upgrade": approved_packet_with_upgrade,
            "readiness_mismatch": readiness_mismatch,
            "action_blocker_mismatch": action_blocker_mismatch,
            "decision_mismatch": decision_mismatch,
        }

        case_dir = out_dir / str(customer_id)
        case_dir.mkdir(parents=True, exist_ok=True)

        packet_payload: Any
        if hasattr(operator_packet, "model_dump"):
            packet_payload = operator_packet.model_dump()  # type: ignore[assignment]
        elif hasattr(operator_packet, "dict"):
            packet_payload = operator_packet.dict()  # type: ignore[assignment, no-redef]
        else:
            packet_payload = json.loads(json.dumps(operator_packet, default=str))

        (case_dir / "roadmap_summary.json").write_text(
            json.dumps(roadmap_summary, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (case_dir / "operator_metrics.json").write_text(
            json.dumps(operator_metrics, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (case_dir / "operator_packet.json").write_text(
            json.dumps(packet_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (case_dir / "operator_packet.md").write_text(
            render_operator_review_packet_markdown(operator_packet),
            encoding="utf-8",
        )

        cases.append(
            {
                "customer_id": str(customer_id),
                "source_customer_id": _safe_text(row.get("source_customer_id")),
                "cohort_label": _safe_text(row.get("cohort_label")),
                "decision_status_summary": decision_status,
                "selected_decision_status_summary": selected_decision_status,
                "selection_outcome_summary": selection_outcome,
                "selected_recommendation_source_summary": selected_recommendation_source,
                "selected_action_count_summary": int(roadmap_summary.get("selected_action_count", 0) or 0),
                "recourse_mode_summary": _safe_text(roadmap_summary.get("recourse_mode")),
                "recommendation_mode_summary": _safe_text(roadmap_summary.get("recommendation_mode")),
                "operator_selected_decision_status": op_selected_status,
                "operator_readiness_render_mode": op_readiness_mode,
                "operator_rendered_blocker_count": op_blockers,
                "operator_rendered_action_count": op_actions,
                "operator_upgrade_condition_text_present": bool(op_upgrade_text),
                "operator_packet_coherence_codes_json": coherence_codes_json,
                "contradiction_flags": contradiction_flags,
                "paths": {
                    "case_dir": str(case_dir),
                    "operator_packet_md": str(case_dir / "operator_packet.md"),
                    "operator_packet_json": str(case_dir / "operator_packet.json"),
                    "operator_metrics_json": str(case_dir / "operator_metrics.json"),
                    "roadmap_summary_json": str(case_dir / "roadmap_summary.json"),
                },
            }
        )

    (out_dir / "contradictions.json").write_text(
        json.dumps({"run_dir": str(run_dir), "cases": cases}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
