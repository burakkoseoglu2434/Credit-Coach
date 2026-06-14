from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from credit_coach.evaluation.coverage_diagnostics import (
    assign_coverage_loss_bucket,
    build_customer_breakdown,
    write_coverage_diagnostics,
)


def test_assign_coverage_loss_bucket_classifies_key_cases() -> None:
    gap_closure_epsilon = 0.05

    def bucket(payload: dict) -> str:
        return assign_coverage_loss_bucket(pd.Series(payload), gap_closure_epsilon=gap_closure_epsilon)

    assert (
        bucket(
            {
                "selected_recommendation_source": "selected_plan",
                "recommendation_mode": "actionable",
                "has_valid_path_flag": 1,
                "has_rankable_path_flag": 1,
                "rankable_path_count": 1,
            }
        )
        == "selected_plan_present"
    )

    assert bucket({"selected_invalid_winner_flag": 1}) == "trust_blocked"
    assert bucket({"has_valid_path_flag": 0}) == "no_valid_path"
    assert bucket({"has_valid_path_flag": 1, "has_rankable_path_flag": 0}) == "valid_but_not_rankable"
    assert (
        bucket(
            {
                "has_valid_path_flag": 1,
                "has_rankable_path_flag": 1,
                "rankable_path_count": 2,
                "movement_potential": "none",
                "path_reaches_threshold_flag": 0,
            }
        )
        == "rankable_but_no_movement"
    )
    assert (
        bucket(
            {
                "has_valid_path_flag": 1,
                "has_rankable_path_flag": 1,
                "rankable_path_count": 1,
                "movement_potential": "weak",
                "threshold_reach_possible": 0,
                "path_reaches_threshold_flag": 0,
                "max_gap_closure_rate": 0.01,
            }
        )
        == "movement_but_no_threshold_signal"
    )
    assert (
        bucket(
            {
                "has_valid_path_flag": 1,
                "has_rankable_path_flag": 1,
                "rankable_path_count": 1,
                "movement_potential": "strong",
                "threshold_reach_possible": 1,
                "max_gap_closure_rate": 0.2,
                "recourse_mode": "limited",
                "recommendation_mode": "informational",
                "empty_state_flag": 1,
                "selected_recommendation_source": "empty_state",
            }
        )
        == "latent_value_but_gate_suppressed"
    )
    assert (
        bucket(
            {
                "has_valid_path_flag": 1,
                "has_rankable_path_flag": 1,
                "rankable_path_count": 1,
                "movement_potential": "strong",
                "threshold_reach_possible": 1,
                "max_gap_closure_rate": 0.2,
                "recourse_mode": "full",
                "recommendation_mode": "",
                "empty_state_flag": 1,
                "selected_recommendation_source": "empty_state",
            }
        )
        == "post_gate_surface_collapsed_to_empty_state"
    )


def test_build_customer_breakdown_maps_structural_limited_to_hard_denied() -> None:
    breakdown = build_customer_breakdown(
        pd.DataFrame(
            [
                {
                    "customer_id": "c1",
                    "recoverability_bucket": "structural_limited",
                    "has_valid_path_flag": 1,
                    "has_rankable_path_flag": 1,
                    "rankable_path_count": 1,
                    "movement_potential": "none",
                }
            ]
        )
    )
    assert breakdown.loc[0, "segment"] == "hard_denied"


def test_write_coverage_diagnostics_emits_required_artifacts(tmp_path: Path) -> None:
    df = pd.DataFrame(
        [
            {
                "customer_id": "a1",
                "source_customer_id": "s1",
                "cohort_label": "near_threshold_denied",
                "recoverability_bucket": "near_threshold",
                "recourse_mode": "full",
                "recommendation_mode": "actionable",
                "selected_recommendation_source": "selected_plan",
                "empty_state_flag": 0,
                "zero_action_flag": 0,
                "has_valid_path_flag": 1,
                "has_rankable_path_flag": 1,
                "rankable_path_count": 1,
                "threshold_reach_possible": 1,
                "path_reaches_threshold_flag": 1,
                "movement_potential": "strong",
                "max_gap_closure_rate": 0.9,
            },
            {
                "customer_id": "a2",
                "source_customer_id": "s2",
                "cohort_label": "mid_risk_denied",
                "recoverability_bucket": "mid_risk",
                "recourse_mode": "limited",
                "recommendation_mode": "informational",
                "selected_recommendation_source": "empty_state",
                "empty_state_flag": 1,
                "zero_action_flag": 1,
                "has_valid_path_flag": 1,
                "has_rankable_path_flag": 1,
                "rankable_path_count": 1,
                "threshold_reach_possible": 0,
                "path_reaches_threshold_flag": 0,
                "movement_potential": "weak",
                "max_gap_closure_rate": 0.1,
            },
        ]
    )

    paths = write_coverage_diagnostics(customer_df=df, output_dir=tmp_path, gap_closure_epsilon=0.05)

    assert paths.customer_breakdown_csv.is_file()
    assert paths.summary_json.is_file()
    assert paths.reason_frequency_csv.is_file()
    assert paths.empty_state_decomposition_json.is_file()

    summary = json.loads(paths.summary_json.read_text(encoding="utf-8"))
    assert summary["thresholds"]["gap_closure_epsilon"] == 0.05
    assert summary["overall"]["n_customers"] == 2
    assert "by_segment" in summary

    freq = pd.read_csv(paths.reason_frequency_csv)
    assert int(freq["count"].sum()) == 2

