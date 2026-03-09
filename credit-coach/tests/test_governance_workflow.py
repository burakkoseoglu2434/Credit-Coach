from __future__ import annotations

from credit_coach.retraining.governance import evaluate_governance_workflow


def test_evaluate_governance_workflow_passes_when_all_controls_met():
    out = evaluate_governance_workflow(
        champion_metrics={"auc": 0.80, "ece": 0.03, "fairness_gap": 0.05},
        challenger_metrics={"auc": 0.82, "ece": 0.02, "fairness_gap": 0.04},
        gates={"min_auc": 0.75, "max_ece": 0.05, "max_fairness_gap": 0.10},
        approvals={"model_owner": True, "risk": True, "compliance": True, "ops": True},
        release_artifacts={
            "model_hash": "a",
            "config_hash": "b",
            "data_hash": "c",
            "evidence_hash": "d",
        },
        rollback_test_passed=True,
    )
    assert out["status"] == "PASS"
    assert out["approval_compliance"] == 1.0
    assert out["release_artifact_completeness"] == 1.0


def test_evaluate_governance_workflow_fails_on_missing_controls():
    out = evaluate_governance_workflow(
        champion_metrics={"auc": 0.80, "ece": 0.03, "fairness_gap": 0.05},
        challenger_metrics={"auc": 0.70, "ece": 0.08, "fairness_gap": 0.20},
        gates={"min_auc": 0.75, "max_ece": 0.05, "max_fairness_gap": 0.10},
        approvals={"model_owner": True, "risk": False},
        release_artifacts={"model_hash": "a"},
        rollback_test_passed=False,
    )
    assert out["status"] == "FAIL"
    assert len(out["reasons"]) >= 1
