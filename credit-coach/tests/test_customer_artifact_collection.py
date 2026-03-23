from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

from credit_coach.cli import run_customer_artifact_collection as collector
from credit_coach.cli.run_recourse import (
    CustomerArtifactBundle,
    CustomerRecourseRunResult,
    _build_customer_roadmap,
    _plan_to_row,
    build_customer_artifact_bundle,
    write_customer_artifact_bundle,
)
from credit_coach.data.schema import PlanAction, PlanRecord, TrajectoryCheckpoint, TrajectoryPhase


class _DummyModel:
    def predict_proba(self, x):
        frame = x if isinstance(x, pd.DataFrame) else pd.DataFrame(x)
        income = pd.to_numeric(frame.get("annual_inc", pd.Series([50_000.0] * len(frame))), errors="coerce").fillna(50_000.0)
        util = pd.to_numeric(frame.get("revol_util", pd.Series([50.0] * len(frame))), errors="coerce").fillna(50.0)
        pd_values = (0.72 - (income / 250000.0) + (util / 500.0)).clip(0.05, 0.99).to_numpy()
        return pd.DataFrame({"good": 1.0 - pd_values, "bad": pd_values}).to_numpy()


def test_selection_frame_denied_first_near_prioritizes_denied_then_fills_near() -> None:
    frame = pd.DataFrame(
        {
            "source_row_index": [10, 11, 12, 13, 14],
            "customer_id": ["c-10", "c-11", "c-12", "c-13", "c-14"],
        }
    )
    base_pd = pd.Series([0.62, 0.49, 0.37, 0.34, 0.12], dtype=float)

    selected = collector._selection_frame(
        input_df=frame,
        base_pd=base_pd,
        tau=0.35,
        n_customers=4,
        sample_seed=7,
        cohort_policy="denied_first_near",
        segment_caps_cfg={},
    )

    assert list(selected["selection_reason"])[:3] == ["denied", "denied", "denied"]
    assert selected.iloc[3]["selection_reason"] == "near_fill"
    assert int(selected["denied_base"].astype(int).sum()) == 3
    assert list(selected["batch_index"]) == [0, 1, 2, 3]


def test_collection_parity_failure_marks_internal_review_and_external_conditional() -> None:
    bundle = CustomerArtifactBundle(
        customer_id="cust-parity",
        plans_df=pd.DataFrame([{"plan_id": "plan-a", "action_count": 1}]),
        roadmap={
            "customer_id": "cust-parity",
            "best_plan_id": "plan-a",
            "best_plan_source": "internal",
            "phases": [
                {
                    "phase_id": "phase_1_stabilize",
                    "steps": [{"step_id": "step-1"}],
                }
            ],
            "checkpoints": [
                {"week": 4, "status": "at_risk"},
                {"week": 12, "status": "on_track"},
                {"week": 24, "status": "on_track"},
            ],
            "summary": {
                "decision_status": "APPROVED",
                "credit_readiness_stage": "week_4",
                "plan_execution_probability": 0.62,
                "approval_dependent_plan_probability": 0.62,
                "offer_acceptance_probability": 0.0,
                "combined_plan_realization_probability": 0.62,
            },
        },
        roadmap_steps_df=pd.DataFrame(
            [
                {"customer_id": "cust-parity", "best_plan_id": "plan-a", "action_key": "limit_credit_usage"},
            ]
        ),
        metrics_summary={"customer_id": "cust-parity", "best_plan_id": "plan-a", "best_plan_source": "internal"},
    )
    metrics_row = {
        "customer_id": "cust-parity",
        "best_plan_id": "plan-a",
        "best_plan_source": "internal",
        "decision_status": "APPROVED",
        "decision_status_internal": "APPROVED",
        "credit_readiness_stage": "week_4",
        "plan_execution_probability": 0.62,
        "approval_dependent_plan_probability": 0.62,
        "offer_acceptance_probability": 0.0,
        "combined_plan_realization_probability": 0.62,
        "best_action_count": 99,
        "zero_step_flag": 0,
        "checkpoint_status_4w": "at_risk",
        "checkpoint_status_12w": "on_track",
        "checkpoint_status_24w": "on_track",
        "raw_contract_pass": 1,
        "parity_pass": 1,
        "data_issue_flag": 0,
    }
    plans_df = pd.DataFrame(
        [
            {"plan_id": "plan-a", "selected_best_flag": 1},
        ]
    )

    parity = collector._validate_customer_artifact_parity(
        bundle=bundle,
        metrics_row=metrics_row,
        plans_df=plans_df,
        steps_df=bundle.roadmap_steps_df,
    )
    assert parity["parity_pass"] == 0
    assert "best_action_count" in parity["parity_mismatch_fields"]

    collector._apply_collection_parity_classification(
        bundle,
        mismatch_fields=parity["parity_mismatch_fields"],
    )
    summary = bundle.roadmap["summary"]
    assert summary["decision_status"] == "CONDITIONAL"
    assert summary["decision_status_internal"] == "NEEDS_REVIEW"
    assert int(summary["parity_pass"]) == 0
    assert int(summary["data_issue_flag"]) == 1
    assert "parity_mismatch" in summary["data_issue_codes"]


def test_customer_artifact_bundle_matches_single_customer_row_shape(tmp_path: Path) -> None:
    action = PlanAction(
        feature_name="revol_util",
        current_value=71.0,
        target_value=52.0,
        delta=-19.0,
        time_months=1,
        estimated_cost_usd=15.0,
        action_key="limit_credit_usage",
        action_class="behavioral",
        action_title="Limit credit usage",
        action_group_id="limit_credit_usage:phase_1_stabilize",
        action_execution_probability=0.66,
        difficulty_score=0.41,
        difficulty_label="moderate",
        difficulty_drivers={
            "burden": 0.2,
            "horizon": 0.1,
            "action_class": 0.3,
            "coordination_load": 0.1,
        },
        approval_friction=0.0,
        diagnostic_flags=["utilization_relief"],
    )
    plan = PlanRecord(
        plan_id="bundle-plan",
        customer_id="cust-bundle",
        run_id="run-bundle",
        horizon_months=6,
        strategy="balanced",
        actions=[action],
        phases=[
            TrajectoryPhase(
                phase_id="phase_1_stabilize",
                phase_title="Ilk 4 Hafta - Stabilizasyon",
                target_window_weeks="1-4",
                target_window_months=[1],
                review_week=4,
                target_pd=0.40,
                gate_pass_target=False,
                steps=[action],
            ),
            TrajectoryPhase(
                phase_id="phase_2_build",
                phase_title="1-3 Ay - Guclendirme",
                target_window_weeks="5-12",
                target_window_months=[2, 3],
                review_week=12,
                target_pd=0.32,
                gate_pass_target=True,
                steps=[],
            ),
            TrajectoryPhase(
                phase_id="phase_3_optimize",
                phase_title="3-6 Ay - Optimizasyon",
                target_window_weeks="13-24",
                target_window_months=[4, 5, 6],
                review_week=24,
                target_pd=0.30,
                gate_pass_target=True,
                steps=[],
            ),
        ],
        trajectory_checkpoints=[
            TrajectoryCheckpoint(
                week=4,
                month=1,
                phase_id="phase_1_stabilize",
                checkpoint_type="primary",
                checkpoint_label="early_stabilization",
                predicted_pd=0.40,
                pd_delta_vs_base=0.04,
                gate_pass_estimate=0,
                checkpoint_priority=1,
                status="at_risk",
            ),
            TrajectoryCheckpoint(
                week=12,
                month=3,
                phase_id="phase_2_build",
                checkpoint_type="confirmation",
                checkpoint_label="approval_readiness",
                predicted_pd=0.32,
                pd_delta_vs_base=0.12,
                gate_pass_estimate=1,
                checkpoint_priority=2,
                status="on_track",
            ),
            TrajectoryCheckpoint(
                week=24,
                month=6,
                phase_id="phase_3_optimize",
                checkpoint_type="stability",
                checkpoint_label="durable_optimization",
                predicted_pd=0.30,
                pd_delta_vs_base=0.14,
                gate_pass_estimate=1,
                checkpoint_priority=3,
                status="on_track",
            ),
        ],
        predicted_pd=0.30,
        score=0.2,
        robust_score=0.2,
        status="APPROVED",
        constraint_status="valid",
        trajectory_status="on_track",
        next_review_week=4,
        plan_execution_probability=0.66,
        mean_group_difficulty_score=0.41,
        peak_group_difficulty_score=0.41,
        dominant_difficulty_label="moderate",
        follow_through_readiness_label="moderate",
    )

    roadmap = _build_customer_roadmap(
        customer_id="cust-bundle",
        base_pd=0.44,
        tau=0.35,
        best=plan,
        best_source="internal",
        row=pd.Series({"revol_util": 71.0}),
        model=_DummyModel(),
        calibrator=None,
        feature_cols=["revol_util"],
        local_reason_bundle={
            "reasons": [{"feature": "revol_util", "direction": "increase_risk", "abs_contribution": 0.2}],
            "meta": {"explainability_confidence": 0.8, "stability_score": 0.9, "baseline_drift_l1": 0.02},
        },
    )
    bundle = build_customer_artifact_bundle(
        customer_id="cust-bundle",
        model_version="model-001",
        base_pd=0.44,
        search_profile={"is_denied_target": True, "search_cfg": {"time_budget_ms": 0}},
        segment_context={"income_band": "q2", "risk_band": "high", "segment_caps_applied": False},
        validated=[plan],
        candidate_pool=[plan],
        best=plan,
        best_source="internal",
        roadmap=roadmap,
        msi=0.2,
        alpha=0.05,
        robust_objective="cvar",
        robust_cvar_quantile=0.9,
        local_reason_bundle={
            "reasons": [{"feature": "revol_util"}],
            "meta": {"explainability_confidence": 0.8, "stability_score": 0.9, "baseline_drift_l1": 0.02},
        },
        adverse_action_reasons=[{"feature": "revol_util"}],
        dice_backend="skipped",
        dice_records=[],
        dice_telemetry={"method_requested": "random", "method_used": "skipped", "fallback_reason": "skipped_by_policy"},
        search_elapsed_ms=12.5,
        fairness_penalty=0.0,
        decision_log_record={"decision_id": "d-1", "selection_propensity": 1.0},
        decision_log_summary={"decision_log_completeness": 1.0},
    )

    assert bundle.plans_df.to_dict(orient="records")[0] == _plan_to_row(plan)
    assert bundle.roadmap_steps_df.iloc[0]["customer_id"] == "cust-bundle"
    assert bundle.metrics_summary["best_plan_id"] == "bundle-plan"

    out_dir = tmp_path / "raw" / "cust-bundle"
    paths = write_customer_artifact_bundle(bundle, out_dir)
    assert paths["plans_json"].exists()
    assert paths["roadmap_json"].exists()
    assert paths["metrics_json"].exists()
    assert paths["roadmap_steps_csv"].exists()


def test_run_customer_artifact_collection_emits_raw_and_flat_outputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    processed_root = tmp_path / "processed"
    processed_root.mkdir(parents=True, exist_ok=True)

    features_path = tmp_path / "features.yaml"
    features_path.write_text(
        yaml.safe_dump({"features": ["annual_inc", "revol_util"], "target": {"name": "loan_status"}}),
        encoding="utf-8",
    )
    base_config = tmp_path / "base.yaml"
    base_config.write_text(
        yaml.safe_dump({"features_config": str(features_path), "paths": {"processed_data": str(processed_root)}}),
        encoding="utf-8",
    )
    model_config = tmp_path / "model.yaml"
    model_config.write_text(
        yaml.safe_dump({"decision": {"tau_0": 0.35}, "registry": {"path": str(tmp_path / "models")}}),
        encoding="utf-8",
    )
    recourse_config = tmp_path / "recourse.yaml"
    recourse_config.write_text(yaml.safe_dump({"segment_caps": {}}), encoding="utf-8")
    causality_config = tmp_path / "causality.yaml"
    causality_config.write_text(yaml.safe_dump({"graph": {"output_path": str(tmp_path / "graph.json")}}), encoding="utf-8")
    safety_config = tmp_path / "safety.yaml"
    safety_config.write_text(yaml.safe_dump({}), encoding="utf-8")
    macro_config = tmp_path / "macro.yaml"
    macro_config.write_text(yaml.safe_dump({}), encoding="utf-8")

    train_df = pd.DataFrame(
        [
            {"annual_inc": 50000.0, "revol_util": 55.0, "loan_status": 0},
            {"annual_inc": 62000.0, "revol_util": 42.0, "loan_status": 0},
        ]
    )
    test_df = pd.DataFrame(
        [
            {"customer_id": "cust-1", "annual_inc": 25000.0, "revol_util": 88.0, "loan_status": 1},
            {"customer_id": "cust-2", "annual_inc": 32000.0, "revol_util": 74.0, "loan_status": 1},
            {"customer_id": "cust-3", "annual_inc": 54000.0, "revol_util": 44.0, "loan_status": 0},
            {"customer_id": "cust-4", "annual_inc": 90000.0, "revol_util": 18.0, "loan_status": 0},
        ]
    )
    train_df.to_parquet(processed_root / "train.parquet", index=False)
    test_csv = processed_root / "test.csv"
    test_df.to_csv(test_csv, index=False)

    monkeypatch.setattr(
        collector,
        "load_model_bundle",
        lambda **kwargs: (_DummyModel(), None, {"model_version": "model-001"}, None),
    )
    monkeypatch.setattr(
        collector,
        "predict_proba_pd",
        lambda model, calibrator, frame: pd.to_numeric(frame["revol_util"], errors="coerce").fillna(0.0).div(100.0).to_numpy(),
    )
    monkeypatch.setattr(collector, "run_rex_adapter", lambda *args, **kwargs: {})

    def _fake_customer_result(**kwargs):
        customer_id = str(kwargs["customer_id"])
        plans_df = pd.DataFrame(
            [
                {"plan_id": f"{customer_id}-plan-a", "plan_score": 0.4},
                {"plan_id": f"{customer_id}-plan-b", "plan_score": 0.3},
            ]
        )
        steps_df = pd.DataFrame(
            [
                {
                    "customer_id": customer_id,
                    "best_plan_id": f"{customer_id}-plan-a",
                    "phase_id": "phase_1_stabilize",
                    "phase_title": "Stabilize",
                    "target_window_weeks": "1-4",
                    "action_key": "limit_credit_usage",
                    "action_class": "behavioral",
                    "action_title": "Limit credit usage",
                    "action_group_id": f"{customer_id}:phase_1",
                    "composite_action": 0,
                    "feature_name": "revol_util",
                    "metric_key": "credit_utilization_pct",
                    "unit": "percentage_points",
                    "current_value": 70.0,
                    "target_value": 45.0,
                    "delta": -25.0,
                    "time_months": 1,
                    "due_month": 1,
                    "direction": "decrease",
                    "generation_notes_json": "[]",
                    "estimated_cost_usd": 25.0,
                    "requires_institutional_approval": 0,
                    "approval_pending_semantic_only": 0,
                    "action_status": "valid",
                    "constraint_family": "",
                    "constraint_reason_codes_json": "[]",
                    "was_clipped": 0,
                    "repair_applied": 0,
                    "dependency_gate": 0,
                    "semantic_preserved": True,
                },
                {
                    "customer_id": customer_id,
                    "best_plan_id": f"{customer_id}-plan-a",
                    "phase_id": "phase_2_build",
                    "phase_title": "Build",
                    "target_window_weeks": "5-12",
                    "action_key": "pay_down_revolving_balance",
                    "action_class": "structural",
                    "action_title": "Pay down balance",
                    "action_group_id": f"{customer_id}:phase_2",
                    "composite_action": 0,
                    "feature_name": "revol_util",
                    "metric_key": "credit_utilization_pct",
                    "unit": "percentage_points",
                    "current_value": 45.0,
                    "target_value": 35.0,
                    "delta": -10.0,
                    "time_months": 3,
                    "due_month": 3,
                    "direction": "decrease",
                    "generation_notes_json": "[]",
                    "estimated_cost_usd": 55.0,
                    "requires_institutional_approval": 0,
                    "approval_pending_semantic_only": 0,
                    "action_status": "valid",
                    "constraint_family": "",
                    "constraint_reason_codes_json": "[\"capacity_cap\"]",
                    "was_clipped": 1,
                    "repair_applied": 0,
                    "dependency_gate": 0,
                    "semantic_preserved": True,
                },
            ]
        )
        bundle = CustomerArtifactBundle(
            customer_id=customer_id,
            plans_df=plans_df,
            roadmap={
                "customer_id": customer_id,
                "best_plan_id": f"{customer_id}-plan-a",
                "best_plan_source": "internal",
                "summary": {
                    "decision_status": "NEEDS_REVIEW",
                    "credit_readiness_stage": "week_12",
                    "plan_execution_probability": 0.61,
                    "approval_dependent_plan_probability": None,
                    "offer_acceptance_probability": None,
                    "combined_plan_realization_probability": None,
                },
                "phases": [
                    {
                        "phase_id": "phase_1_stabilize",
                        "steps": [{"step_id": f"{customer_id}:step-1"}],
                    },
                    {
                        "phase_id": "phase_2_build",
                        "steps": [{"step_id": f"{customer_id}:step-2"}],
                    },
                ],
                "checkpoints": [
                    {"week": 4, "status": "at_risk"},
                    {"week": 12, "status": "on_track"},
                    {"week": 24, "status": "on_track"},
                ],
            },
            roadmap_steps_df=steps_df,
            metrics_summary={
                "customer_id": customer_id,
                "best_status": "NEEDS_REVIEW",
                "best_plan_id": f"{customer_id}-plan-a",
                "best_plan_source": "internal",
                "plan_count": 2,
                "approved_count": 0,
                "denied_target_mode": True,
            },
        )
        return CustomerRecourseRunResult(
            bundle=bundle,
            local_reason_bundle={"reasons": [], "meta": {}},
            adverse_action_reasons=[],
            dice_df=pd.DataFrame(),
            dice_records=[],
            dice_backend="skipped",
            dice_telemetry={"method_requested": "random", "method_used": "skipped", "fallback_reason": "skipped_by_policy"},
            candidate_pool_df=pd.DataFrame(),
            decision_log_record={"decision_id": f"decision-{customer_id}", "selection_propensity": 1.0},
            decision_log_summary={"decision_log_completeness": 1.0},
        )

    monkeypatch.setattr(collector, "generate_customer_recourse_artifacts", _fake_customer_result)

    run_ctx = collector.main(
        [
            "--base_config",
            str(base_config),
            "--model_config",
            str(model_config),
            "--recourse_config",
            str(recourse_config),
            "--causality_config",
            str(causality_config),
            "--safety_config",
            str(safety_config),
            "--macro_config",
            str(macro_config),
            "--input_data_path",
            str(test_csv),
            "--input_data_format",
            "csv",
            "--n_customers",
            "3",
            "--cohort_policy",
            "denied_first_near",
            "--artifact_root",
            str(tmp_path / "runs"),
        ]
    )

    collection_root = run_ctx.tables_dir / "customer_artifact_collection"
    raw_dirs = [path for path in (collection_root / "raw").iterdir() if path.is_dir()]
    assert len(raw_dirs) == 3
    for raw_dir in raw_dirs:
        assert (raw_dir / "customer_roadmap.json").exists()
        assert (raw_dir / "plans.json").exists()
        assert (raw_dir / "metrics.json").exists()
        assert (raw_dir / "customer_roadmap_steps.csv").exists()

    metrics_df = pd.read_csv(collection_root / "flat" / "customer_metrics.csv")
    plans_df = pd.read_csv(collection_root / "flat" / "customer_plans.csv")
    steps_df = pd.read_csv(collection_root / "flat" / "customer_roadmap_steps.csv")
    selection_df = pd.read_csv(collection_root / "flat" / "customer_selection.csv")
    assert len(metrics_df) == 3
    assert len(plans_df) == 6
    assert len(steps_df) == 6
    assert len(selection_df) == 3
    assert (collection_root / "collection_manifest.json").exists()
    assert (collection_root / "collection_summary.md").exists()
    assert set(metrics_df["decision_status"]) == {"CONDITIONAL"}
    assert set(metrics_df["decision_status_internal"]) == {"CONDITIONAL"}
    assert (metrics_df["best_action_count"] == 2).all()
    assert (metrics_df["parity_pass"] == 1).all()
    assert (metrics_df["raw_contract_pass"] == 0).all()
    assert (metrics_df["data_issue_flag"] == 1).all()
    assert (metrics_df["checkpoint_status_4w"] == "at_risk").all()
    assert "data_issue_codes_json" in metrics_df.columns
    assert "selected_best_flag" in plans_df.columns
    assert "plan_step_count" in plans_df.columns
    assert "plan_contract_pass" in plans_df.columns

    manifest = json.loads((collection_root / "collection_manifest.json").read_text(encoding="utf-8"))
    assert "contract_health" in manifest
    assert "raw_flat_mismatch_count" in manifest["contract_health"]

    summary_md = (collection_root / "collection_summary.md").read_text(encoding="utf-8")
    assert "## Contract Health" in summary_md
    assert "Decision status distribution" in summary_md
