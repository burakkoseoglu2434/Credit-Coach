from __future__ import annotations

import json

import pandas as pd

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
    assert metrics["selected_source_distribution"] == {}


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
            "selected_source_distribution": {"internal": 0.50, "dice": 0.30, "rule": 0.20},
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
        "trust_regression_table_csv",
    }
    for filename in files.values():
        assert (tmp_path / filename).exists()
    payload = json.loads((tmp_path / files["cohort_evidence_summary_json"]).read_text(encoding="utf-8"))
    assert payload["populations"] == ["denied"]
