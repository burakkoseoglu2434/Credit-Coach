from __future__ import annotations


def compare_champion_challenger(champion: dict, challenger: dict) -> dict:
    return {
        "auc_delta": float(challenger.get("auc", 0.0) - champion.get("auc", 0.0)),
        "ece_delta": float(challenger.get("ece", 1.0) - champion.get("ece", 1.0)),
        "fairness_gap_delta": float(challenger.get("fairness_gap", 0.0) - champion.get("fairness_gap", 0.0)),
    }
