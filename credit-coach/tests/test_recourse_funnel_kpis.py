from __future__ import annotations

from io import StringIO

import numpy as np
import pandas as pd

from credit_coach.cli.run_batch_recourse_eval import (
    _apply_label_aware_fairness_guard,
    _build_denied_diagnostics,
    _extract_reliability_thresholds_by_risk_band,
    _plan_trajectory_metrics,
    _root_cause_from_status_reasons,
)
from credit_coach.cli.run_recourse import _plan_to_row
from credit_coach.data.schema import PlanAction, PlanRecord


def test_build_denied_diagnostics_outputs_expected_rates():
    batch_df = pd.DataFrame(
        [
            {
                "customer_id": "c1",
                "denied_base": 1,
                "best_status": "APPROVED",
                "had_any_candidate": 1,
                "gate_pass_any_candidate": 1,
                "income_band": "q1",
                "risk_band": "near",
                "internal_gate_pass_any": 1,
                "dice_gate_pass_any": 0,
            },
            {
                "customer_id": "c2",
                "denied_base": 1,
                "best_status": "NEEDS_REVIEW",
                "had_any_candidate": 1,
                "gate_pass_any_candidate": 0,
                "income_band": "q1",
                "risk_band": "mid",
                "internal_gate_pass_any": 0,
                "dice_gate_pass_any": 1,
                "best_reliability": 0.50,
                "best_ci_high": 0.30,
                "best_worst_risk_margin": -0.01,
                "denied_not_approved_root_cause": "reliability_gate",
            },
            {
                "customer_id": "c3",
                "denied_base": 1,
                "best_status": "NEEDS_REVIEW",
                "had_any_candidate": 1,
                "gate_pass_any_candidate": 0,
                "income_band": "q2",
                "risk_band": "mid",
                "internal_gate_pass_any": 1,
                "dice_gate_pass_any": 1,
                "best_reliability": 0.90,
                "best_ci_high": 0.50,
                "best_worst_risk_margin": 0.10,
                "denied_not_approved_root_cause": "ci_gate",
            },
            {
                "customer_id": "c4",
                "denied_base": 1,
                "best_status": "NEEDS_REVIEW",
                "had_any_candidate": 1,
                "gate_pass_any_candidate": 0,
                "income_band": "q3",
                "risk_band": "high",
                "internal_gate_pass_any": 0,
                "dice_gate_pass_any": 0,
                "best_reliability": 0.90,
                "best_ci_high": 0.33,
                "best_worst_risk_margin": -0.20,
                "denied_not_approved_root_cause": "worst_margin_gate",
            },
            {
                "customer_id": "c5",
                "denied_base": 0,
                "best_status": "APPROVED",
                "had_any_candidate": 1,
                "gate_pass_any_candidate": 1,
                "income_band": "q4",
                "risk_band": "near",
                "internal_gate_pass_any": 1,
                "dice_gate_pass_any": 0,
            },
        ]
    )

    gate_df, source_df, income_df, risk_df, metrics = _build_denied_diagnostics(
        batch_df,
        tau=0.35,
        min_reliability=0.70,
        min_worst_risk_margin=-0.05,
    )
    assert {"ci_gate", "reliability_gate", "worst_margin_gate"} <= set(gate_df["gate"].tolist())
    assert abs(float(metrics["denied_reliability_violation_rate"]) - (1.0 / 3.0)) < 1e-9
    assert abs(float(metrics["denied_ci_violation_rate"]) - (1.0 / 3.0)) < 1e-9
    assert abs(float(metrics["denied_worst_margin_violation_rate"]) - (1.0 / 3.0)) < 1e-9
    assert abs(float(metrics["denied_internal_gate_pass_share"]) - 0.5) < 1e-9
    assert abs(float(metrics["denied_dice_gate_pass_share"]) - 0.5) < 1e-9
    assert abs(float(metrics["denied_internal_vs_dice_gate_pass_share"]) - 0.5) < 1e-9
    assert abs(float(metrics["denied_nonrejected_best_rate"]) - 1.0) < 1e-9
    assert abs(float(metrics["denied_nan_gate_fields_rate"]) - 0.0) < 1e-9
    assert {"internal_only", "dice_only", "both", "none"} <= set(source_df["source_bucket"].tolist())
    assert "denied_to_approved_lift" in income_df.columns
    assert "denied_to_approved_lift" in risk_df.columns


def test_root_cause_from_status_reasons_marks_multi_gate():
    reasons = [
        "CI upper bound exceeds threshold (conformal); reliability 0.40 below min 0.70",
        "worst_risk_margin -0.20 below min -0.05",
    ]
    assert _root_cause_from_status_reasons(reasons) == "multi_gate"


def test_root_cause_from_single_reason_string():
    reason = "CI upper bound exceeds threshold (conformal); reliability 0.40 below min 0.70"
    assert _root_cause_from_status_reasons(reason) == "multi_gate"


def test_build_denied_diagnostics_counts_nan_as_violation():
    batch_df = pd.DataFrame(
        [
            {
                "customer_id": "c1",
                "denied_base": 1,
                "best_status": "REJECTED",
                "had_any_candidate": 1,
                "gate_pass_any_candidate": 0,
                "income_band": "q1",
                "risk_band": "high",
                "internal_gate_pass_any": 0,
                "dice_gate_pass_any": 0,
                "best_ci_high": float("nan"),
                "best_reliability": float("nan"),
                "best_worst_risk_margin": float("nan"),
                "denied_not_approved_root_cause": "feasibility_gate",
            }
        ]
    )
    _, _, _, _, metrics = _build_denied_diagnostics(
        batch_df,
        tau=0.35,
        min_reliability=0.70,
        min_worst_risk_margin=-0.05,
    )
    assert float(metrics["denied_ci_violation_rate"]) == 1.0
    assert float(metrics["denied_reliability_violation_rate"]) == 1.0
    assert float(metrics["denied_worst_margin_violation_rate"]) == 1.0
    assert float(metrics["denied_nan_gate_fields_rate"]) == 1.0


def test_extract_reliability_thresholds_by_risk_band_applies_overrides():
    thresholds = _extract_reliability_thresholds_by_risk_band(
        uncertainty_cfg={
            "reliability_profiles": {
                "default": {"min_reliability": 0.30},
                "denied": {"min_reliability": 0.15},
                "high": {"min_reliability": 0.05},
            }
        },
        default_min_reliability=0.60,
    )
    assert float(thresholds["default"]) == 0.30
    assert float(thresholds["high"]) == 0.05
    assert float(thresholds["mid"]) == 0.15


def test_apply_label_aware_fairness_guard_demotes_when_gaps_exceed_targets():
    batch_df = pd.DataFrame(
        [
            {
                "batch_index": 0,
                "denied_base": 1,
                "best_status": "APPROVED",
                "gate_pass_any_candidate": 1,
                "approved_plan_count": 1,
                "best_pd": 0.20,
                "base_pd": 0.60,
                "risk_band": "high",
                "candidate_pd_delta": 0.05,
                "best_reliability": 0.20,
                "best_worst_risk_margin": -0.30,
                "best_cost_usd": 100.0,
                "best_status_reason": "",
            },
            {
                "batch_index": 1,
                "denied_base": 1,
                "best_status": "APPROVED",
                "gate_pass_any_candidate": 1,
                "approved_plan_count": 1,
                "best_pd": 0.25,
                "base_pd": 0.62,
                "risk_band": "high",
                "candidate_pd_delta": 0.04,
                "best_reliability": 0.22,
                "best_worst_risk_margin": -0.28,
                "best_cost_usd": 90.0,
                "best_status_reason": "",
            },
            {
                "batch_index": 2,
                "denied_base": 1,
                "best_status": "NEEDS_REVIEW",
                "gate_pass_any_candidate": 0,
                "approved_plan_count": 0,
                "best_pd": 0.58,
                "base_pd": 0.58,
                "risk_band": "high",
                "candidate_pd_delta": 0.00,
                "best_reliability": 0.10,
                "best_worst_risk_margin": -0.40,
                "best_cost_usd": 0.0,
                "best_status_reason": "",
            },
            {
                "batch_index": 3,
                "denied_base": 1,
                "best_status": "NEEDS_REVIEW",
                "gate_pass_any_candidate": 0,
                "approved_plan_count": 0,
                "best_pd": 0.57,
                "base_pd": 0.57,
                "risk_band": "high",
                "candidate_pd_delta": 0.00,
                "best_reliability": 0.10,
                "best_worst_risk_margin": -0.40,
                "best_cost_usd": 0.0,
                "best_status_reason": "",
            },
        ]
    )
    sampled_sorted = pd.DataFrame(
        [
            {"home_ownership": "A", "target": 1},
            {"home_ownership": "A", "target": 1},
            {"home_ownership": "B", "target": 1},
            {"home_ownership": "B", "target": 1},
        ]
    )
    rec_cfg = {
        "fairness": {
            "postprocess_guard": {
                "enabled": True,
                "target_equalized_odds_gap_delta": 0.01,
                "target_approval_gap_after": 0.10,
                "target_recourse_success_gap": 0.10,
                "max_demotions": 4,
                "max_iterations": 10,
                "min_denied_to_approved_lift": 0.09,
                "min_denied_high_risk_lift": 0.03,
            }
        }
    }
    adjusted, metrics = _apply_label_aware_fairness_guard(
        batch_df=batch_df,
        sampled_sorted=sampled_sorted,
        group_feature="home_ownership",
        target_col="target",
        tau=0.35,
        rec_cfg=rec_cfg,
    )
    assert int(metrics["fairness_guard_enabled"]) == 1
    assert int(metrics["fairness_guard_demotion_count"]) >= 1
    assert float(metrics["fairness_guard_final_recourse_success_gap"]) <= float(
        metrics["fairness_guard_initial_recourse_success_gap"]
    )
    assert int(adjusted["fairness_guard_demoted"].astype(int).sum()) >= 1


def test_plan_trajectory_metrics_uses_time_layered_actions():
    class _DummyModel:
        def predict_proba(self, x):
            p = np.clip(pd.to_numeric(x["score"], errors="coerce").fillna(0.0).to_numpy(dtype=float) / 100.0, 0.0, 1.0)
            return np.column_stack([1.0 - p, p])

    row = pd.Series({"score": 60.0})
    plan = PlanRecord(
        plan_id="p1",
        customer_id="c1",
        run_id="r1",
        horizon_months=6,
        strategy="balanced",
        actions=[
            PlanAction(
                feature_name="score",
                current_value=60.0,
                target_value=50.0,
                delta=-10.0,
                time_months=1,
                estimated_cost_usd=10.0,
            ),
            PlanAction(
                feature_name="score",
                current_value=50.0,
                target_value=30.0,
                delta=-20.0,
                time_months=6,
                estimated_cost_usd=20.0,
            ),
        ],
        predicted_pd=0.30,
        status="APPROVED",
    )
    out = _plan_trajectory_metrics(
        row=row,
        plan=plan,
        base_pd=0.60,
        tau=0.35,
        model=_DummyModel(),
        calibrator=None,
        feature_cols=["score"],
        partial_progress_min_pd_delta=0.05,
    )
    assert float(out["trajectory_pd_4w"]) <= 0.50
    assert float(out["trajectory_pd_24w"]) <= float(out["trajectory_pd_12w"])
    assert int(out["trajectory_gate_pass_24w"]) == 1
    assert int(out["trajectory_partial_progress"]) == 1


def test_plan_row_serialization_keeps_typed_action_fields():
    plan = PlanRecord(
        plan_id="p2",
        customer_id="c2",
        run_id="r2",
        horizon_months=6,
        strategy="balanced",
        actions=[
            PlanAction(
                feature_name="int_rate",
                current_value=18.0,
                target_value=15.0,
                delta=-3.0,
                time_months=3,
                estimated_cost_usd=50.0,
                action_key="refinance",
                action_class="structural",
                action_title="Refinance or restructure debt",
                action_group_id="refinance:m3",
                composite_action=True,
            ),
            PlanAction(
                feature_name="installment",
                current_value=450.0,
                target_value=380.0,
                delta=-70.0,
                time_months=3,
                estimated_cost_usd=40.0,
                action_key="refinance",
                action_class="structural",
                action_title="Refinance or restructure debt",
                action_group_id="refinance:m3",
                composite_action=True,
            ),
        ],
        predicted_pd=0.30,
        status="APPROVED",
    )
    row = _plan_to_row(plan)
    steps = pd.read_json(StringIO(row["timeline_steps_json"]))
    assert set(steps["action_key"]) == {"refinance"}
    assert set(steps["action_class"]) == {"structural"}
    assert set(steps["action_group_id"]) == {"refinance:m3"}
    assert int(row["phase_2_action_count"]) == 2
