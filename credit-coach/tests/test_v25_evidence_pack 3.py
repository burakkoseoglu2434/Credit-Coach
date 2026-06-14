from __future__ import annotations

import json
from pathlib import Path

from credit_coach.cli.run_v25_evidence_pack import build_evidence_pack


def test_v25_evidence_pack_writes_outputs_and_avoids_banned_language(tmp_path: Path) -> None:
    cohort_dir = tmp_path / "cohort"
    cohort_dir.mkdir(parents=True, exist_ok=True)
    outcome_dir = tmp_path / "outcome_tables"
    outcome_dir.mkdir(parents=True, exist_ok=True)
    planning_root = tmp_path / "planning" / "phases" / "68-real-cohort-evidence-run"

    cohort_payload = {
        "evaluation": {"sample_size": 10},
        "sampling": {"unique_denied_available": 10, "with_replacement": False},
        "overall": {
            "recoverable_customer_rate": 0.2,
            "threshold_reach_possible_rate": 0.1,
            "selected_invalid_winner_count": 0,
            "selected_surface_drift_count": 0,
            "operator_packet_contradiction_count": 0,
        },
        "population_metrics": {
            "global_denied": {"sample_size": 10, "movement_rate": 0.1, "strong_movement_rate": 0.1},
            "recoverable_full_mode": {"sample_size": 2, "movement_rate": 1.0, "strong_movement_rate": 1.0},
            "non_recoverable_limited_mode": {"sample_size": 8, "movement_rate": 0.0, "strong_movement_rate": 0.0},
        },
    }
    (cohort_dir / "cohort_metrics.json").write_text(json.dumps(cohort_payload), encoding="utf-8")

    outcome_payload = {
        "window_days": 90,
        "total_decisions": 10,
        "overall": {"observed_decisions": 1, "observation_coverage_rate": 0.1, "evidence_status": "sparse"},
        "recoverable_vs_limited_summary": [],
        "recoverable_vs_limited_comparison": {},
    }
    (outcome_dir / "outcome_realization_evaluation.json").write_text(json.dumps(outcome_payload), encoding="utf-8")

    outputs = build_evidence_pack(
        cohort_dir=cohort_dir,
        outcome_run_tables_dir=outcome_dir,
        planning_root=planning_root,
        alpha=0.05,
    )

    assert outputs["report"].exists()
    assert outputs["executive_summary"].exists()
    assert outputs["decision"].exists()

    report_text = outputs["report"].read_text(encoding="utf-8").lower()
    exec_text = outputs["executive_summary"].read_text(encoding="utf-8").lower()
    decision_text = outputs["decision"].read_text(encoding="utf-8").lower()

    assert "dataset limitation" in report_text
    assert "trust evidence" in report_text
    assert "realized-outcome evidence" in report_text
    assert "classification:" in decision_text

    for text in [report_text, exec_text, decision_text]:
        assert "causal" not in text
        assert "uplift" not in text
        assert "guarantee" not in text
        assert "proves" not in text

