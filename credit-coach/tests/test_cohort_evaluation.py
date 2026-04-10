from __future__ import annotations

import json
from types import SimpleNamespace

import pandas as pd

from credit_coach.cli.run_recourse import CustomerArtifactBundle, CustomerRecourseRunResult
from credit_coach.cli import run_v24_cohort_evaluation as cohort_eval
from credit_coach.evaluation.cohort_evidence import (
    build_cohort_evidence_package,
    build_phase60_evidence_summary,
    summarize_population_metrics_from_rows,
    write_phase60_evidence_artifacts,
)


def test_summarize_population_metrics_from_rows_handles_empty_population() -> None:
    metrics = summarize_population_metrics_from_rows(pd.DataFrame())

    assert metrics["multi_path_rate"] == 0.0
    assert metrics["path_count"] == 0.0
    assert metrics["rankable_path_count"] == 0.0
    assert metrics["non_empty_contender_share"] == 0.0
    assert metrics["threshold_reach_possible_rate"] == 0.0
    assert metrics["recoverable_customer_rate"] == 0.0
    assert metrics["recoverable_flag_distribution"] == {}
    assert metrics["recoverability_classifier_version_distribution"] == {}
    assert metrics["recourse_mode_distribution"] == {}
    assert metrics["recommendation_mode_distribution"] == {}
    assert metrics["limited_customer_rate"] == 0.0
    assert metrics["informational_recommendation_rate"] == 0.0
    assert metrics["selected_source_distribution"] == {}
    assert metrics["mean_movement_score"] == 0.0
    assert metrics["mean_threshold_reach_probability"] == 0.0
    assert metrics["threshold_reach_priority_rate"] == 0.0
    assert metrics["selected_path_movement_strength_distribution"] == {}


def test_summarize_population_metrics_from_rows_uses_existing_batch_contract() -> None:
    rows = pd.DataFrame(
        [
            {
                "best_source": "internal",
                "best_contender_bucket": "ACTIONABLE",
                "best_status": "APPROVED",
                "best_offer_maturity": "active_rankable",
                "best_execution_aware_value": -1.5,
                "candidate_pool_diversity_index": 0.50,
                "candidate_source_entropy": 0.35,
                "multi_path_flag": 1,
                "path_count": 3,
                "rankable_path_count": 2,
                "action_diversity_index": 0.60,
                "non_utilization_action_rate": 0.40,
                "institution_action_rate": 0.20,
                "selected_path_type": "customer_only",
                "approval_gap": 0.05,
                "recoverability_score": 0.80,
                "threshold_reach_possible": 1,
                "recoverability_bucket": "near_threshold",
                "recoverable_flag": 1,
                "recoverability_classifier_version": "phase_62_v1",
                "recourse_mode": "full",
                "recommendation_mode": "actionable",
                "selected_recommendation_source": "selected_plan",
                "selected_action_count": 1,
                "cohort_label": "near_threshold_denied",
                "movement_score": 0.84,
                "threshold_reach_probability": 0.72,
                "threshold_reach_priority_flag": 1,
                "selected_path_movement_strength": "strong",
            },
            {
                "best_source": "rule",
                "best_contender_bucket": "APPROVAL_SHELL_ONLY",
                "best_status": "NEEDS_REVIEW",
                "best_offer_maturity": "provisional",
                "best_execution_aware_value": -0.5,
                "candidate_pool_diversity_index": 0.30,
                "candidate_source_entropy": 0.15,
                "multi_path_flag": 0,
                "path_count": 1,
                "rankable_path_count": 1,
                "action_diversity_index": 0.10,
                "non_utilization_action_rate": 0.20,
                "institution_action_rate": 0.60,
                "selected_path_type": "hybrid",
                "approval_gap": 0.22,
                "recoverability_score": 0.12,
                "threshold_reach_possible": 0,
                "recoverability_bucket": "mid_risk",
                "recoverable_flag": 0,
                "recoverability_classifier_version": "phase_62_v1",
                "recourse_mode": "limited",
                "recommendation_mode": "informational",
                "selected_recommendation_source": "empty_state",
                "selected_action_count": 0,
                "cohort_label": "mid_risk_denied",
                "movement_score": 0.0,
                "threshold_reach_probability": 0.0,
                "threshold_reach_priority_flag": 0,
                "selected_path_movement_strength": "",
            },
        ]
    )

    metrics = summarize_population_metrics_from_rows(rows)

    assert metrics["candidate_pool_diversity_index"] == 0.4
    assert metrics["candidate_source_entropy"] == 0.25
    assert metrics["multi_path_rate"] == 0.5
    assert metrics["path_count"] == 2.0
    assert metrics["rankable_path_count"] == 1.5
    assert metrics["non_empty_contender_share"] == 1.0
    assert metrics["approved_or_conditional_contender_share"] == 1.0
    assert metrics["best_source_internal_rate"] == 0.5
    assert metrics["best_source_rule_rate"] == 0.5
    assert metrics["mean_approval_gap"] == 0.135
    assert metrics["mean_recoverability_score"] == 0.46
    assert metrics["threshold_reach_possible_rate"] == 0.5
    assert metrics["recoverable_customer_rate"] == 0.5
    assert metrics["recoverability_bucket_distribution"] == {"mid_risk": 0.5, "near_threshold": 0.5}
    assert metrics["recoverable_flag_distribution"] == {"recoverable": 0.5, "not_recoverable": 0.5}
    assert metrics["recoverability_classifier_version_distribution"] == {"phase_62_v1": 1.0}
    assert metrics["recourse_mode_distribution"] == {"full": 0.5, "limited": 0.5}
    assert metrics["recommendation_mode_distribution"] == {"actionable": 0.5, "informational": 0.5}
    assert metrics["limited_customer_rate"] == 0.5
    assert metrics["informational_recommendation_rate"] == 0.5
    assert metrics["empty_state_rate"] == 0.5
    assert metrics["zero_action_rate"] == 0.5
    assert metrics["mean_movement_score"] == 0.42
    assert metrics["mean_threshold_reach_probability"] == 0.36
    assert metrics["threshold_reach_priority_rate"] == 0.5
    assert metrics["movement_rate"] == 0.5
    assert metrics["strong_movement_rate"] == 0.5
    assert metrics["selected_path_movement_strength_distribution"] == {"strong": 1.0}
    assert metrics["threshold_gap_distribution"] == {"mid_risk_denied": 0.5, "near_threshold_denied": 0.5}
    assert metrics["selected_source_distribution"]["internal"] == 0.5


def test_cohort_evidence_package_infers_default_trust_rows_from_movement_summary() -> None:
    metrics = {
        "non_empty_contender_share": 0.80,
        "approved_or_conditional_contender_share": 0.65,
        "mean_execution_aware_value": -2.0,
        "multi_path_rate": 0.45,
        "path_count": 2.2,
        "rankable_path_count": 1.8,
        "action_diversity_index": 0.55,
        "non_utilization_action_rate": 0.35,
        "institution_action_rate": 0.20,
        "offer_ready_contender_share": 0.25,
        "approval_shell_only_share": 0.10,
        "selected_plan_category_customer_only_rate": 0.70,
        "selected_plan_category_institution_assisted_rate": 0.20,
        "selected_plan_category_hybrid_rate": 0.10,
        "mean_approval_gap": 0.11,
        "mean_recoverability_score": 0.42,
        "threshold_reach_possible_rate": 0.18,
        "recoverable_customer_rate": 0.12,
        "recoverability_bucket_distribution": {"mid_risk": 0.60, "near_threshold": 0.40},
        "recoverable_flag_distribution": {"recoverable": 0.12, "not_recoverable": 0.88},
        "recoverability_classifier_version_distribution": {"phase_62_v1": 1.0},
        "recourse_mode_distribution": {"full": 0.88, "limited": 0.12},
        "recommendation_mode_distribution": {"actionable": 0.88, "informational": 0.12},
        "limited_customer_rate": 0.12,
        "informational_recommendation_rate": 0.12,
        "empty_state_rate": 0.12,
        "zero_action_rate": 0.18,
        "movement_rate": 0.88,
        "strong_movement_rate": 0.30,
        "mean_movement_score": 0.44,
        "mean_threshold_reach_probability": 0.31,
        "threshold_reach_priority_rate": 0.18,
        "selected_path_movement_strength_distribution": {"moderate": 0.70, "strong": 0.30},
        "threshold_gap_distribution": {"mid_risk_denied": 0.60, "near_threshold_denied": 0.40},
    }
    movement = {
        "dominant_movement_bottleneck": "structural_cohort_limited",
        "movement_guardrail_summary": "Structural cohort pressure remains dominant.",
        "trust_guardrails": {
            "selected_invalid_winner_count": 0,
            "selected_dice_valid_rate": 1.0,
            "selected_decision_mismatch_count": 0,
            "approved_with_blocker_count": 0,
            "approved_with_action_count": 0,
            "approved_with_upgrade_condition_count": 0,
            "action_blocker_mismatch_count": 0,
            "readiness_decision_mismatch_count": 0,
        },
    }

    pkg = build_cohort_evidence_package("pilot_mixed", metrics, movement)

    assert pkg["population"] == "pilot_mixed"
    assert pkg["movement_potential"]["dominant_movement_bottleneck"] == "structural_cohort_limited"
    assert pkg["path_diversity"]["mean_path_count"] == 2.2
    assert pkg["selected_path_distribution"]["selected_customer_only_share"] == 0.7
    assert pkg["movement_ranking"]["mean_movement_score"] == 0.44
    assert pkg["movement_ranking"]["mean_threshold_reach_probability"] == 0.31
    assert pkg["movement_ranking"]["threshold_reach_priority_rate"] == 0.18
    assert pkg["movement_ranking"]["selected_path_movement_strength_distribution"] == {
        "moderate": 0.70,
        "strong": 0.30,
    }
    assert pkg["targeted_evaluation"]["movement_rate"] == 0.88
    assert pkg["targeted_evaluation"]["strong_movement_rate"] == 0.30
    assert pkg["targeted_evaluation"]["empty_state_rate"] == 0.12
    assert pkg["targeted_evaluation"]["zero_action_rate"] == 0.18
    assert pkg["targeted_evaluation"]["threshold_gap_distribution"] == {
        "mid_risk_denied": 0.60,
        "near_threshold_denied": 0.40,
    }
    assert pkg["recoverability_signal"]["threshold_reach_possible_rate"] == 0.18
    assert pkg["recoverability_signal"]["recoverable_customer_rate"] == 0.12
    assert pkg["recoverability_signal"]["recoverable_flag_distribution"] == {
        "recoverable": 0.12,
        "not_recoverable": 0.88,
    }
    assert pkg["recoverability_signal"]["recoverability_classifier_version_distribution"] == {"phase_62_v1": 1.0}
    assert pkg["recourse_gate"]["recourse_mode_distribution"] == {"full": 0.88, "limited": 0.12}
    assert pkg["recourse_gate"]["recommendation_mode_distribution"] == {
        "actionable": 0.88,
        "informational": 0.12,
    }
    assert pkg["recourse_gate"]["limited_customer_rate"] == 0.12
    assert pkg["recourse_gate"]["informational_recommendation_rate"] == 0.12
    assert {row["suite"] for row in pkg["trust_regression"]} == {
        "winner_integrity",
        "contender_quality",
        "selected_surface_consistency",
        "operator_packet_coherence",
    }


def test_phase60_summary_and_artifact_writer_materialize_expected_files(tmp_path) -> None:
    package = build_cohort_evidence_package(
        "denied",
        {
            "non_empty_contender_share": 0.75,
            "approved_or_conditional_contender_share": 0.55,
            "mean_execution_aware_value": -1.25,
            "multi_path_rate": 0.50,
            "path_count": 2.0,
            "rankable_path_count": 1.5,
            "action_diversity_index": 0.45,
            "non_utilization_action_rate": 0.30,
            "institution_action_rate": 0.25,
            "offer_ready_contender_share": 0.20,
            "approval_shell_only_share": 0.12,
            "selected_plan_category_customer_only_rate": 0.60,
            "selected_plan_category_institution_assisted_rate": 0.25,
            "selected_plan_category_hybrid_rate": 0.15,
            "mean_approval_gap": 0.16,
            "mean_recoverability_score": 0.36,
            "threshold_reach_possible_rate": 0.14,
            "recoverable_customer_rate": 0.20,
            "recoverability_bucket_distribution": {"mid_risk": 0.50, "structural_limited": 0.50},
            "recoverable_flag_distribution": {"recoverable": 0.20, "not_recoverable": 0.80},
            "recoverability_classifier_version_distribution": {"phase_62_v1": 1.0},
            "selected_source_distribution": {"internal": 0.50, "dice": 0.30, "rule": 0.20},
            "recourse_mode_distribution": {"full": 0.80, "limited": 0.20},
            "recommendation_mode_distribution": {"actionable": 0.80, "informational": 0.20},
            "limited_customer_rate": 0.20,
            "informational_recommendation_rate": 0.20,
            "empty_state_rate": 0.20,
            "zero_action_rate": 0.25,
            "movement_rate": 0.80,
            "strong_movement_rate": 0.25,
            "mean_movement_score": 0.51,
            "mean_threshold_reach_probability": 0.29,
            "threshold_reach_priority_rate": 0.14,
            "selected_path_movement_strength_distribution": {"moderate": 0.75, "strong": 0.25},
            "threshold_gap_distribution": {"mid_risk_denied": 0.50, "near_threshold_denied": 0.50},
        },
        {"dominant_movement_bottleneck": "structural_cohort_limited"},
        [{"suite": "winner_integrity", "status": "passed", "evidence_source": "pytest", "notes": ""}],
    )
    summary = build_phase60_evidence_summary([package])
    files = write_phase60_evidence_artifacts(tmp_path, summary, prefix="phase_60_test")

    assert summary["overall_movement_conclusion"] == "structural_bottleneck_remains_dominant"
    assert summary["overall_trust_conclusion"] == "trust_baseline_intact"
    assert set(files) == {
        "cohort_evidence_summary_json",
        "cohort_evidence_summary_md",
        "movement_potential_table_csv",
        "path_diversity_table_csv",
        "action_coverage_table_csv",
        "selected_path_distribution_table_csv",
        "movement_ranking_table_csv",
        "targeted_evaluation_table_csv",
        "recoverability_signal_table_csv",
        "recourse_gate_table_csv",
        "trust_regression_table_csv",
    }
    for filename in files.values():
        assert (tmp_path / filename).exists()
    payload = json.loads((tmp_path / files["cohort_evidence_summary_json"]).read_text(encoding="utf-8"))
    assert payload["populations"] == ["denied"]
    assert payload["recoverability_signal_table"][0]["threshold_reach_possible_rate"] == 0.14
    assert payload["recoverability_signal_table"][0]["recoverable_customer_rate"] == 0.2
    assert payload["recoverability_signal_table"][0]["recoverability_classifier_version_distribution"] == {
        "phase_62_v1": 1.0
    }
    assert payload["movement_ranking_table"][0]["mean_movement_score"] == 0.51
    assert payload["movement_ranking_table"][0]["threshold_reach_priority_rate"] == 0.14
    assert payload["movement_ranking_table"][0]["selected_path_movement_strength_distribution"] == {
        "moderate": 0.75,
        "strong": 0.25,
    }
    assert payload["targeted_evaluation_table"][0]["movement_rate"] == 0.8
    assert payload["targeted_evaluation_table"][0]["strong_movement_rate"] == 0.25
    assert payload["targeted_evaluation_table"][0]["empty_state_rate"] == 0.2
    assert payload["targeted_evaluation_table"][0]["threshold_gap_distribution"] == {
        "mid_risk_denied": 0.5,
        "near_threshold_denied": 0.5,
    }
    assert payload["recourse_gate_table"][0]["limited_customer_rate"] == 0.2
    assert payload["recourse_gate_table"][0]["recourse_mode_distribution"] == {"full": 0.8, "limited": 0.2}


def test_cohort_evaluation_main_writes_recoverability_fields(tmp_path, monkeypatch) -> None:
    population_df = pd.DataFrame(
        [
            {"customer_id": "cust-1", "feature_a": 1.0},
            {"customer_id": "cust-2", "feature_a": 2.0},
            {"customer_id": "cust-3", "feature_a": 3.0},
        ]
    )
    train_df = population_df.copy()
    pd_values = pd.Series([0.39, 0.50, 0.69], dtype=float)

    def _fake_load_config(path):
        text = str(path)
        if "default" in text:
            return {"features_config": "configs/features_48.yaml"}
        if "model" in text:
            return {"decision": {"tau_0": 0.35}, "registry": {"path": "artifacts/models"}}
        return {}

    def _fake_generate_customer_recourse_artifacts(**kwargs):
        customer_id = kwargs["customer_id"]
        paths_df = pd.DataFrame(
            [
                {
                    "path_id": f"{customer_id}-path-1",
                    "path_type": "customer_only",
                    "rankable_flag": 1,
                    "representative_plan_id": f"{customer_id}-plan-1",
                    "action_categories": ["payment_history"],
                    "action_keys": ["reduce_delinquency"],
                }
            ]
        )
        bundle = CustomerArtifactBundle(
            customer_id=customer_id,
            plans_df=pd.DataFrame(),
            roadmap={
                "customer_id": customer_id,
                "best_plan_id": f"{customer_id}-plan-1",
                "best_plan_source": "internal",
                "summary": {
                    "decision_status": "REJECTED",
                    "selected_decision_status": "REJECTED",
                    "decision_status_internal": "REJECTED",
                    "selected_plan_status_internal": "REJECTED",
                    "selection_outcome": "selected_valid_winner",
                    "credit_readiness_stage": "week_4",
                    "expected_readiness": "week_4",
                    "offer_maturity": "none",
                    "offer_plan": 0,
                    "recoverable_flag": True,
                    "recoverability_classifier_version": "phase_62_live_test",
                    "recoverability_signal_reason_codes": [
                        "LOW_APPROVAL_GAP",
                        "HAS_VALID_PATH",
                        "HAS_RANKABLE_PATH",
                        "THRESHOLD_REACHABLE",
                    ],
                    "recoverable_reason_codes": [
                        "WITHIN_RECOVERABLE_BAND",
                        "HAS_VALID_PATH",
                        "HAS_RANKABLE_PATH",
                        "THRESHOLD_REACHABLE",
                        "NO_ACTIVE_CLASSIFIER_BLOCKERS",
                        "RECOVERABLE",
                    ],
                    "recourse_mode": "full",
                    "recommendation_mode": "actionable",
                    "recourse_gate_version": "phase_63_v1",
                    "recourse_gate_reason_codes": ["RECOVERABLE_FULL_MODE"],
                    "selected_action_count": 1,
                    "movement_score": 0.81,
                    "threshold_reach_probability": 0.69,
                    "threshold_reach_priority_flag": 1,
                    "movement_rank_reason_codes": [
                        "THRESHOLD_REACH_PRIORITY",
                        "REALISTIC_MOVEMENT_ADVANTAGE",
                    ],
                    "selected_path_movement_strength": "moderate",
                },
            },
            roadmap_steps_df=pd.DataFrame(),
            metrics_summary={
                "selected_invalid_winner_flag": 0,
                "recoverable_flag": 1,
                "recoverability_classifier_version": "phase_62_live_test",
                "best_contender_bucket": "ACTIONABLE",
                "best_status": "REJECTED",
                "best_offer_maturity": "none",
                "best_execution_aware_value": -0.25,
                "candidate_pool_diversity_index": 0.5,
                "candidate_source_entropy": 0.25,
                "multi_path_flag": 0,
                "action_diversity_index": 0.5,
                "non_utilization_action_rate": 1.0,
                "institution_action_rate": 0.0,
                "selected_path_type": "customer_only",
                "offer_ready_contender_share": 0.0,
                "approval_shell_only_share": 0.0,
                "recoverability_signal_reason_codes_json": json.dumps(
                    [
                        "LOW_APPROVAL_GAP",
                        "HAS_VALID_PATH",
                        "HAS_RANKABLE_PATH",
                        "THRESHOLD_REACHABLE",
                    ]
                ),
                "recoverable_reason_codes_json": json.dumps(
                    [
                        "WITHIN_RECOVERABLE_BAND",
                        "HAS_VALID_PATH",
                        "HAS_RANKABLE_PATH",
                        "THRESHOLD_REACHABLE",
                        "NO_ACTIVE_CLASSIFIER_BLOCKERS",
                        "RECOVERABLE",
                    ]
                ),
                "recourse_mode": "full",
                "recommendation_mode": "actionable",
                "recourse_gate_version": "phase_63_v1",
                "recourse_gate_reason_codes_json": json.dumps(["RECOVERABLE_FULL_MODE"]),
                "movement_score": 0.81,
                "threshold_reach_probability": 0.69,
                "threshold_reach_priority_flag": 1,
                "movement_rank_reason_codes_json": json.dumps(
                    ["THRESHOLD_REACH_PRIORITY", "REALISTIC_MOVEMENT_ADVANTAGE"]
                ),
                "selected_path_movement_strength": "moderate",
            },
            paths_df=paths_df,
        )
        return CustomerRecourseRunResult(
            bundle=bundle,
            local_reason_bundle={},
            adverse_action_reasons=[],
            dice_df=pd.DataFrame(),
            dice_records=[],
            dice_backend="",
            dice_telemetry={},
            candidate_pool_df=pd.DataFrame(
                [
                    {
                        "plan_id": f"{customer_id}-plan-1",
                        "plan_source": "internal",
                        "predicted_pd": 0.31,
                    }
                ]
            ),
            decision_log_record={},
            decision_log_summary={},
        )

    monkeypatch.setattr(
        cohort_eval,
        "parse_args",
        lambda: SimpleNamespace(
            base_config="configs/default.yaml",
            model_config="configs/model.yaml",
            recourse_config="configs/recourse.yaml",
            causality_config="configs/causality.yaml",
            safety_config="configs/safety.yaml",
            macro_config="configs/macro.yaml",
            dataset_scope="full_processed",
            n_customers=3,
            sample_seed=7,
            model_version="",
            model_manifest="",
            output_dir=str(tmp_path),
        ),
    )
    monkeypatch.setattr(cohort_eval, "load_config", _fake_load_config)
    monkeypatch.setattr(cohort_eval, "load_feature_contract", lambda path: {"features": ["feature_a"], "target": "target"})
    monkeypatch.setattr(cohort_eval, "_load_population", lambda **kwargs: (population_df.copy(), train_df.copy()))
    monkeypatch.setattr(cohort_eval, "load_model_bundle", lambda **kwargs: (object(), object(), {"model_version": "test-model"}, None))
    monkeypatch.setattr(cohort_eval, "predict_proba_pd", lambda model, calibrator, frame: pd_values.iloc[: len(frame)].reset_index(drop=True))
    monkeypatch.setattr(cohort_eval, "generate_customer_recourse_artifacts", _fake_generate_customer_recourse_artifacts)
    monkeypatch.setattr(cohort_eval, "build_operator_review_packet", lambda roadmap: {})
    monkeypatch.setattr(
        cohort_eval,
        "operator_packet_metrics_fields",
        lambda operator_packet, packet_relpath: {
            "operator_selected_decision_status": "REJECTED",
            "operator_rendered_blocker_count": 0,
            "operator_rendered_action_count": 0,
            "operator_readiness_render_mode": "rejected",
            "operator_upgrade_condition_text": "",
        },
    )

    cohort_eval.main()

    customer_df = pd.read_csv(tmp_path / "customer_level_analysis.csv")
    metrics_payload = json.loads((tmp_path / "cohort_metrics.json").read_text(encoding="utf-8"))

    assert "recoverability_bucket" in customer_df.columns
    assert "recoverable_flag" in customer_df.columns
    assert "recoverability_classifier_version" in customer_df.columns
    assert "recoverability_signal_reason_codes_json" in customer_df.columns
    assert "recoverable_reason_codes_json" in customer_df.columns
    assert "recourse_mode" in customer_df.columns
    assert "recommendation_mode" in customer_df.columns
    assert "recourse_gate_version" in customer_df.columns
    assert "recourse_gate_reason_codes_json" in customer_df.columns
    assert "movement_score" in customer_df.columns
    assert "threshold_reach_probability" in customer_df.columns
    assert "threshold_reach_priority_flag" in customer_df.columns
    assert "movement_rank_reason_codes_json" in customer_df.columns
    assert "selected_path_movement_strength" in customer_df.columns
    assert "threshold_reach_possible" in customer_df.columns
    assert "primary_population" in customer_df.columns
    assert "in_global_denied_population" in customer_df.columns
    assert "in_recoverable_full_mode_population" in customer_df.columns
    assert "in_non_recoverable_limited_mode_population" in customer_df.columns
    assert "empty_state_flag" in customer_df.columns
    assert "zero_action_flag" in customer_df.columns
    assert customer_df["recoverable_flag"].astype(int).eq(1).all()
    assert customer_df["recourse_mode"].eq("full").all()
    assert customer_df["recommendation_mode"].eq("actionable").all()
    assert customer_df["primary_population"].eq("recoverable_full_mode").all()
    assert customer_df["in_global_denied_population"].astype(int).eq(1).all()
    assert customer_df["in_recoverable_full_mode_population"].astype(int).eq(1).all()
    assert customer_df["in_non_recoverable_limited_mode_population"].astype(int).eq(0).all()
    assert customer_df["empty_state_flag"].astype(int).eq(0).all()
    assert customer_df["zero_action_flag"].astype(int).eq(0).all()
    assert customer_df["recourse_gate_version"].eq("phase_63_v1").all()
    assert customer_df["movement_score"].astype(float).eq(0.81).all()
    assert customer_df["threshold_reach_probability"].astype(float).eq(0.69).all()
    assert customer_df["threshold_reach_priority_flag"].astype(int).eq(1).all()
    assert customer_df["selected_path_movement_strength"].eq("moderate").all()
    assert customer_df["movement_rank_reason_codes_json"].map(json.loads).map(
        lambda codes: codes == ["THRESHOLD_REACH_PRIORITY", "REALISTIC_MOVEMENT_ADVANTAGE"]
    ).all()
    assert set(customer_df["recoverability_classifier_version"]) == {"phase_62_live_test"}
    assert customer_df["recoverability_signal_reason_codes_json"].map(json.loads).map(
        lambda codes: codes[-1]
    ).eq("THRESHOLD_REACHABLE").all()
    assert customer_df["recoverable_reason_codes_json"].map(json.loads).map(lambda codes: codes[-1]).eq(
        "RECOVERABLE"
    ).all()
    assert customer_df["recourse_gate_reason_codes_json"].map(json.loads).map(
        lambda codes: codes == ["RECOVERABLE_FULL_MODE"]
    ).all()
    assert customer_df["threshold_reach_possible"].astype(int).eq(1).all()
    assert metrics_payload["overall"]["threshold_reach_possible_rate"] == 1.0
    assert metrics_payload["overall"]["recoverable_customer_rate"] == 1.0
    assert metrics_payload["overall"]["recoverable_flag_distribution"] == {
        "recoverable": 1.0,
        "not_recoverable": 0.0,
    }
    assert metrics_payload["overall"]["recourse_mode_distribution"] == {"full": 1.0, "limited": 0.0}
    assert metrics_payload["overall"]["recommendation_mode_distribution"] == {
        "actionable": 1.0,
        "informational": 0.0,
    }
    assert metrics_payload["overall"]["limited_customer_rate"] == 0.0
    assert metrics_payload["overall"]["informational_recommendation_rate"] == 0.0
    assert metrics_payload["overall"]["empty_state_rate"] == 0.0
    assert metrics_payload["overall"]["zero_action_rate"] == 0.0
    assert metrics_payload["overall"]["mean_movement_score"] == 0.81
    assert metrics_payload["overall"]["mean_threshold_reach_probability"] == 0.69
    assert metrics_payload["overall"]["threshold_reach_priority_rate"] == 1.0
    assert metrics_payload["overall"]["movement_rate"] == 1.0
    assert metrics_payload["overall"]["strong_movement_rate"] == 0.0
    assert metrics_payload["overall"]["selected_path_movement_strength_distribution"] == {
        "moderate": 1.0
    }
    assert metrics_payload["overall"]["threshold_gap_distribution"] == {
        "hard_denied": 0.333333,
        "mid_risk_denied": 0.333333,
        "near_threshold_denied": 0.333333,
    }
    assert metrics_payload["overall"]["recoverability_classifier_version_distribution"] == {
        "phase_62_live_test": 1.0
    }
    assert metrics_payload["population_metrics"]["global_denied"]["sample_size"] == 3
    assert metrics_payload["population_metrics"]["recoverable_full_mode"]["sample_size"] == 3
    assert metrics_payload["population_metrics"]["recoverable_full_mode"]["movement_rate"] == 1.0
    assert metrics_payload["population_metrics"]["recoverable_full_mode"]["threshold_reach_priority_rate"] == 1.0
    assert metrics_payload["population_metrics"]["non_recoverable_limited_mode"]["sample_size"] == 0
    assert metrics_payload["targeted_comparison"]["summary"]["recoverable_customer_rate"] == 1.0
    assert metrics_payload["targeted_comparison"]["summary"]["movement_rate_global"] == 1.0
    assert metrics_payload["targeted_comparison"]["summary"]["movement_rate_recoverable"] == 1.0
    assert metrics_payload["targeted_comparison"]["summary"]["strong_movement_rate_global"] == 0.0
    assert metrics_payload["targeted_comparison"]["summary"]["strong_movement_rate_recoverable"] == 0.0
    assert metrics_payload["targeted_comparison"]["summary"]["mean_movement_score_recoverable"] == 0.81
    assert metrics_payload["targeted_comparison"]["summary"]["mean_threshold_reach_probability_recoverable"] == 0.69
    assert metrics_payload["targeted_comparison"]["summary"]["threshold_reach_priority_rate_recoverable"] == 1.0
    assert metrics_payload["targeted_comparison"]["summary"]["limited_customer_rate"] == 0.0
    assert metrics_payload["targeted_comparison"]["summary"]["informational_recommendation_rate"] == 0.0
    assert metrics_payload["targeted_comparison"]["summary"]["empty_state_rate_limited_control"] == 0.0
    assert metrics_payload["targeted_comparison"]["summary"]["zero_action_rate_limited_control"] == 0.0
    assert metrics_payload["targeted_comparison"]["summary"]["recommendation_mode_distribution_global"] == {
        "actionable": 1.0,
        "informational": 0.0,
    }
    assert metrics_payload["targeted_comparison"]["summary"]["threshold_gap_distribution_global"] == {
        "hard_denied": 0.333333,
        "mid_risk_denied": 0.333333,
        "near_threshold_denied": 0.333333,
    }
    assert metrics_payload["targeted_comparison"]["summary"]["selected_path_movement_strength_distribution_recoverable"] == {
        "moderate": 1.0
    }
    assert metrics_payload["phase_60_evidence_version"] == "v2.4_phase_60"
    assert metrics_payload["phase_60_overall_trust_conclusion"] == "trust_baseline_intact"
    assert "cohort_evidence_summary_json" in metrics_payload["artifacts"]["phase_60_files"]
    assert "near_threshold" in metrics_payload["overall"]["recoverability_bucket_distribution"]

    phase_60_payload = json.loads(
        (
            tmp_path / "phase_60" / "phase_60_cohort_eval_cohort_evidence_summary.json"
        ).read_text(encoding="utf-8")
    )
    overall_row = next(row for row in phase_60_payload["recoverability_signal_table"] if row["population"] == "overall")
    assert overall_row["recoverable_customer_rate"] == 1.0
    assert overall_row["recoverability_classifier_version_distribution"] == {"phase_62_live_test": 1.0}
    movement_row = next(row for row in phase_60_payload["movement_ranking_table"] if row["population"] == "overall")
    assert movement_row["mean_movement_score"] == 0.81
    assert movement_row["mean_threshold_reach_probability"] == 0.69
    assert movement_row["threshold_reach_priority_rate"] == 1.0
    assert movement_row["selected_path_movement_strength_distribution"] == {"moderate": 1.0}
    targeted_row = next(row for row in phase_60_payload["targeted_evaluation_table"] if row["population"] == "recoverable_full_mode")
    assert targeted_row["movement_rate"] == 1.0
    assert targeted_row["strong_movement_rate"] == 0.0
    assert targeted_row["empty_state_rate"] == 0.0
    assert targeted_row["threshold_gap_distribution"] == {
        "hard_denied": 0.333333,
        "mid_risk_denied": 0.333333,
        "near_threshold_denied": 0.333333,
    }
    recourse_row = next(row for row in phase_60_payload["recourse_gate_table"] if row["population"] == "overall")
    assert recourse_row["recourse_mode_distribution"] == {"full": 1.0, "limited": 0.0}
    assert recourse_row["recommendation_mode_distribution"] == {"actionable": 1.0, "informational": 0.0}


def test_cohort_evaluation_main_persists_limited_gate_empty_state_posture(tmp_path, monkeypatch) -> None:
    population_df = pd.DataFrame([{"customer_id": "cust-limited", "feature_a": 1.0}])
    train_df = population_df.copy()
    pd_values = pd.Series([0.61], dtype=float)

    def _fake_load_config(path):
        text = str(path)
        if "default" in text:
            return {"features_config": "configs/features_48.yaml"}
        if "model" in text:
            return {"decision": {"tau_0": 0.35}, "registry": {"path": "artifacts/models"}}
        return {}

    def _fake_generate_customer_recourse_artifacts(**kwargs):
        customer_id = kwargs["customer_id"]
        bundle = CustomerArtifactBundle(
            customer_id=customer_id,
            plans_df=pd.DataFrame(),
            roadmap={
                "customer_id": customer_id,
                "best_plan_id": None,
                "best_plan_source": "",
                "summary": {
                    "decision_status": "REJECTED",
                    "selected_decision_status": "REJECTED",
                    "decision_status_internal": "REJECTED",
                    "selected_plan_status_internal": None,
                    "selection_outcome": "no_valid_winner",
                    "selection_stage": "no_valid_winner",
                    "credit_readiness_stage": "not_ready_yet",
                    "expected_readiness": "not_ready_yet",
                    "offer_maturity": "none",
                    "offer_plan": 0,
                    "recoverable_flag": False,
                    "recoverability_classifier_version": "phase_62_live_test",
                    "recoverability_signal_reason_codes": [
                        "LOW_APPROVAL_GAP",
                        "NO_VALID_PATH",
                        "NO_RANKABLE_PATH",
                        "THRESHOLD_NOT_REACHABLE",
                    ],
                    "recoverable_reason_codes": [
                        "OUTSIDE_RECOVERABLE_BAND",
                        "NO_VALID_PATH",
                        "NO_RANKABLE_PATH",
                        "THRESHOLD_NOT_REACHABLE",
                        "NOT_RECOVERABLE",
                    ],
                    "recourse_mode": "limited",
                    "recommendation_mode": "informational",
                    "recourse_gate_version": "phase_63_v1",
                    "recourse_gate_reason_codes": ["NOT_RECOVERABLE_LIMITED_MODE"],
                    "selected_recommendation_source": "empty_state",
                    "selected_action_count": 0,
                    "selected_recommendation_projection_version": "v2.2_phase_47",
                    "movement_score": 0.0,
                    "threshold_reach_probability": 0.0,
                    "threshold_reach_priority_flag": 0,
                    "movement_rank_reason_codes": [],
                    "selected_path_movement_strength": "",
                },
            },
            roadmap_steps_df=pd.DataFrame(),
            metrics_summary={
                "selected_invalid_winner_flag": 0,
                "recoverable_flag": 0,
                "recoverability_classifier_version": "phase_62_live_test",
                "best_contender_bucket": "EMPTY",
                "best_status": "REJECTED",
                "best_offer_maturity": "none",
                "best_execution_aware_value": -0.25,
                "candidate_pool_diversity_index": 0.0,
                "candidate_source_entropy": 0.0,
                "multi_path_flag": 0,
                "action_diversity_index": 0.0,
                "non_utilization_action_rate": 0.0,
                "institution_action_rate": 0.0,
                "selected_path_type": "",
                "offer_ready_contender_share": 0.0,
                "approval_shell_only_share": 0.0,
                "recoverability_signal_reason_codes_json": json.dumps(
                    [
                        "LOW_APPROVAL_GAP",
                        "NO_VALID_PATH",
                        "NO_RANKABLE_PATH",
                        "THRESHOLD_NOT_REACHABLE",
                    ]
                ),
                "recoverable_reason_codes_json": json.dumps(
                    [
                        "OUTSIDE_RECOVERABLE_BAND",
                        "NO_VALID_PATH",
                        "NO_RANKABLE_PATH",
                        "THRESHOLD_NOT_REACHABLE",
                        "NOT_RECOVERABLE",
                    ]
                ),
                "recourse_mode": "limited",
                "recommendation_mode": "informational",
                "recourse_gate_version": "phase_63_v1",
                "recourse_gate_reason_codes_json": json.dumps(["NOT_RECOVERABLE_LIMITED_MODE"]),
                "movement_score": 0.0,
                "threshold_reach_probability": 0.0,
                "threshold_reach_priority_flag": 0,
                "movement_rank_reason_codes_json": json.dumps([]),
                "selected_path_movement_strength": "",
            },
            paths_df=pd.DataFrame(),
        )
        return CustomerRecourseRunResult(
            bundle=bundle,
            local_reason_bundle={},
            adverse_action_reasons=[],
            dice_df=pd.DataFrame(),
            dice_records=[],
            dice_backend="",
            dice_telemetry={},
            candidate_pool_df=pd.DataFrame(),
            decision_log_record={},
            decision_log_summary={},
        )

    monkeypatch.setattr(
        cohort_eval,
        "parse_args",
        lambda: SimpleNamespace(
            base_config="configs/default.yaml",
            model_config="configs/model.yaml",
            recourse_config="configs/recourse.yaml",
            causality_config="configs/causality.yaml",
            safety_config="configs/safety.yaml",
            macro_config="configs/macro.yaml",
            dataset_scope="full_processed",
            n_customers=1,
            sample_seed=7,
            model_version="",
            model_manifest="",
            output_dir=str(tmp_path),
        ),
    )
    monkeypatch.setattr(cohort_eval, "load_config", _fake_load_config)
    monkeypatch.setattr(cohort_eval, "load_feature_contract", lambda path: {"features": ["feature_a"], "target": "target"})
    monkeypatch.setattr(cohort_eval, "_load_population", lambda **kwargs: (population_df.copy(), train_df.copy()))
    monkeypatch.setattr(cohort_eval, "load_model_bundle", lambda **kwargs: (object(), object(), {"model_version": "test-model"}, None))
    monkeypatch.setattr(cohort_eval, "predict_proba_pd", lambda model, calibrator, frame: pd_values.iloc[: len(frame)].reset_index(drop=True))
    monkeypatch.setattr(cohort_eval, "generate_customer_recourse_artifacts", _fake_generate_customer_recourse_artifacts)
    monkeypatch.setattr(cohort_eval, "build_operator_review_packet", lambda roadmap: {})
    monkeypatch.setattr(
        cohort_eval,
        "operator_packet_metrics_fields",
        lambda operator_packet, packet_relpath: {
            "operator_selected_decision_status": "REJECTED",
            "operator_rendered_blocker_count": 0,
            "operator_rendered_action_count": 0,
            "operator_readiness_render_mode": "empty_state_context",
            "operator_upgrade_condition_text": "",
        },
    )

    cohort_eval.main()

    customer_df = pd.read_csv(tmp_path / "customer_level_analysis.csv")
    metrics_payload = json.loads((tmp_path / "cohort_metrics.json").read_text(encoding="utf-8"))

    assert customer_df["recourse_mode"].eq("limited").all()
    assert customer_df["recommendation_mode"].eq("informational").all()
    assert customer_df["primary_population"].eq("non_recoverable_limited_mode").all()
    assert customer_df["in_global_denied_population"].astype(int).eq(1).all()
    assert customer_df["in_recoverable_full_mode_population"].astype(int).eq(0).all()
    assert customer_df["in_non_recoverable_limited_mode_population"].astype(int).eq(1).all()
    assert customer_df["selected_recommendation_source"].eq("empty_state").all()
    assert customer_df["selected_action_count"].astype(int).eq(0).all()
    assert customer_df["empty_state_flag"].astype(int).eq(1).all()
    assert customer_df["zero_action_flag"].astype(int).eq(1).all()
    assert customer_df["movement_score"].astype(float).eq(0.0).all()
    assert customer_df["threshold_reach_probability"].astype(float).eq(0.0).all()
    assert customer_df["threshold_reach_priority_flag"].astype(int).eq(0).all()
    assert customer_df["selected_path_movement_strength"].fillna("").eq("").all()
    assert customer_df["movement_rank_reason_codes_json"].map(json.loads).map(lambda codes: codes == []).all()
    assert customer_df["recourse_gate_reason_codes_json"].map(json.loads).map(lambda codes: codes == ["NOT_RECOVERABLE_LIMITED_MODE"]).all()
    assert metrics_payload["overall"]["recourse_mode_distribution"] == {"full": 0.0, "limited": 1.0}
    assert metrics_payload["overall"]["recommendation_mode_distribution"] == {
        "actionable": 0.0,
        "informational": 1.0,
    }
    assert metrics_payload["overall"]["limited_customer_rate"] == 1.0
    assert metrics_payload["overall"]["informational_recommendation_rate"] == 1.0
    assert metrics_payload["overall"]["empty_state_rate"] == 1.0
    assert metrics_payload["overall"]["zero_action_rate"] == 1.0
    assert metrics_payload["overall"]["mean_movement_score"] == 0.0
    assert metrics_payload["overall"]["mean_threshold_reach_probability"] == 0.0
    assert metrics_payload["overall"]["threshold_reach_priority_rate"] == 0.0
    assert metrics_payload["overall"]["movement_rate"] == 0.0
    assert metrics_payload["overall"]["strong_movement_rate"] == 0.0
    assert metrics_payload["overall"]["selected_path_movement_strength_distribution"] == {}
    assert metrics_payload["overall"]["threshold_gap_distribution"] == {"near_threshold_denied": 1.0}
    assert metrics_payload["population_metrics"]["global_denied"]["sample_size"] == 1
    assert metrics_payload["population_metrics"]["recoverable_full_mode"]["sample_size"] == 0
    assert metrics_payload["population_metrics"]["non_recoverable_limited_mode"]["sample_size"] == 1
    assert metrics_payload["population_metrics"]["non_recoverable_limited_mode"]["empty_state_rate"] == 1.0
    assert metrics_payload["population_metrics"]["non_recoverable_limited_mode"]["zero_action_rate"] == 1.0
    assert metrics_payload["targeted_comparison"]["summary"]["recoverable_customer_rate"] == 0.0
    assert metrics_payload["targeted_comparison"]["summary"]["movement_rate_global"] == 0.0
    assert metrics_payload["targeted_comparison"]["summary"]["movement_rate_recoverable"] == 0.0
    assert metrics_payload["targeted_comparison"]["summary"]["strong_movement_rate_global"] == 0.0
    assert metrics_payload["targeted_comparison"]["summary"]["strong_movement_rate_recoverable"] == 0.0
    assert metrics_payload["targeted_comparison"]["summary"]["mean_movement_score_recoverable"] == 0.0
    assert metrics_payload["targeted_comparison"]["summary"]["mean_threshold_reach_probability_recoverable"] == 0.0
    assert metrics_payload["targeted_comparison"]["summary"]["threshold_reach_priority_rate_recoverable"] == 0.0
    assert metrics_payload["targeted_comparison"]["summary"]["limited_customer_rate"] == 1.0
    assert metrics_payload["targeted_comparison"]["summary"]["informational_recommendation_rate"] == 1.0
    assert metrics_payload["targeted_comparison"]["summary"]["empty_state_rate_limited_control"] == 1.0
    assert metrics_payload["targeted_comparison"]["summary"]["zero_action_rate_limited_control"] == 1.0
    assert metrics_payload["targeted_comparison"]["summary"]["recommendation_mode_distribution_limited_control"] == {
        "actionable": 0.0,
        "informational": 1.0,
    }
    assert metrics_payload["targeted_comparison"]["summary"]["threshold_gap_distribution_global"] == {
        "near_threshold_denied": 1.0
    }
    assert metrics_payload["targeted_comparison"]["summary"]["threshold_gap_distribution_recoverable"] == {}
    assert metrics_payload["targeted_comparison"]["summary"]["selected_path_movement_strength_distribution_recoverable"] == {}
    phase_60_payload = json.loads(
        (
            tmp_path / "phase_60" / "phase_60_cohort_eval_cohort_evidence_summary.json"
        ).read_text(encoding="utf-8")
    )
    limited_targeted_row = next(
        row for row in phase_60_payload["targeted_evaluation_table"] if row["population"] == "non_recoverable_limited_mode"
    )
    assert limited_targeted_row["movement_rate"] == 0.0
    assert limited_targeted_row["empty_state_rate"] == 1.0
    assert limited_targeted_row["zero_action_rate"] == 1.0
    assert limited_targeted_row["threshold_gap_distribution"] == {"near_threshold_denied": 1.0}
    assert metrics_payload["phase_60_overall_movement_conclusion"] in {"movement_diagnosis_pending", "structural_bottleneck_remains_dominant"}
