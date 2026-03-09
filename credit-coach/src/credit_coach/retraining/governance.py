from __future__ import annotations


def governance_decision(champion_metrics: dict, challenger_metrics: dict, gates: dict) -> tuple[str, list[str]]:
    reasons = []

    min_auc = float(gates.get("min_auc", 0.75))
    max_ece = float(gates.get("max_ece", 0.05))
    max_fair = float(gates.get("max_fairness_gap", 0.10))

    auc = float(challenger_metrics.get("auc", 0.0))
    ece = float(challenger_metrics.get("ece", 1.0))
    fair = float(challenger_metrics.get("fairness_gap", 0.0))

    if auc < min_auc:
        reasons.append(f"AUC below gate: {auc:.4f} < {min_auc:.4f}")
    if ece > max_ece:
        reasons.append(f"ECE above gate: {ece:.4f} > {max_ece:.4f}")
    if fair > max_fair:
        reasons.append(f"Fairness gap above gate: {fair:.4f} > {max_fair:.4f}")

    status = "PASS" if not reasons else "FAIL"
    return status, reasons


def evaluate_governance_workflow(
    *,
    champion_metrics: dict,
    challenger_metrics: dict,
    gates: dict,
    approvals: dict[str, bool] | None = None,
    release_artifacts: dict[str, str] | None = None,
    rollback_test_passed: bool = False,
) -> dict:
    status, reasons = governance_decision(champion_metrics, challenger_metrics, gates)

    approvals = approvals or {}
    required_approvers = list(gates.get("required_approvers", ["model_owner", "risk", "compliance", "ops"]))
    missing_approvals = [a for a in required_approvers if not bool(approvals.get(a, False))]

    release_artifacts = release_artifacts or {}
    required_artifacts = list(
        gates.get(
            "required_artifact_hashes",
            ["model_hash", "config_hash", "data_hash", "evidence_hash"],
        )
    )
    missing_artifacts = [k for k in required_artifacts if not str(release_artifacts.get(k, "")).strip()]

    if missing_approvals:
        reasons.append(f"Missing approvals: {','.join(missing_approvals)}")
    if missing_artifacts:
        reasons.append(f"Missing release artifacts: {','.join(missing_artifacts)}")
    if bool(gates.get("require_rollback_drill", True)) and not bool(rollback_test_passed):
        reasons.append("Rollback drill not passed")

    final_status = "PASS" if not reasons else "FAIL"
    return {
        "status": final_status,
        "reasons": reasons,
        "approval_compliance": float((len(required_approvers) - len(missing_approvals)) / max(1, len(required_approvers))),
        "release_artifact_completeness": float((len(required_artifacts) - len(missing_artifacts)) / max(1, len(required_artifacts))),
        "rollback_test_passed": bool(rollback_test_passed),
        "base_model_gate_status": status,
        "required_approvers": required_approvers,
        "required_artifacts": required_artifacts,
    }
