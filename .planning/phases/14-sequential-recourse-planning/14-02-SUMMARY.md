---
phase: 14-sequential-recourse-planning
plan: 02
subsystem: trajectory-simulation
tags: [weekly-loop, checkpoints, replan, suite, batch, pytest]
requires: [14-01]
provides:
  - weekly-loop-based dynamic trajectory simulation
  - hybrid review-boundary transition state in batch and suite artifacts
  - canonical trajectory summary and breakdown artifacts
affects: [phase-14, coaching-loop, batch-eval, suite]
tech-stack:
  added: []
  patterns: [weekly simulation reuse, seeded aggregation, transition breakdowns]
key-files:
  created: []
  modified: [credit-coach/src/credit_coach/coaching/loop.py, credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py, credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py, credit-coach/tests/test_sequential_recourse.py, credit-coach/tests/test_recourse_funnel_kpis.py, credit-coach/tests/test_phase_experiment_suite.py, credit-coach/tests/test_batch_candidate_diversity.py]
key-decisions:
  - "The weekly coaching loop remains the canonical dynamic simulation grain."
  - "Checkpoint order is `4w > 12w > 24w`, with soft monotonicity penalties rather than hard invalidation."
  - "Phase transitions are fixed by phase structure but adaptive at review boundaries."
patterns-established:
  - "Batch and suite now publish `trajectory_summary.json` plus transition and policy breakdown CSVs as seeded machine-readable evidence."
requirements-completed: [REC-07]
duration: manual-execution
completed: 2026-03-16
---

# Phase 14 Plan 02 Summary

**Trajectory evaluation now simulates time, partial execution, and review-boundary replans through the existing weekly loop instead of a disconnected second simulator.**

## Accomplishments
- Extended the weekly coaching loop to emit hybrid transition state such as `trajectory_status`, `current_phase`, `next_review_week`, and `phase_transition_reason`.
- Upgraded batch evaluation to compute dynamic checkpoint metrics, soft regression penalties, trajectory policy labels, and transition breakdown artifacts.
- Aggregated trajectory evidence through the seeded suite so the phase runner can publish deterministic `trajectory_summary.json` and companion CSVs.

## Verification
- `python -m pytest credit-coach/tests/test_sequential_recourse.py credit-coach/tests/test_recourse_funnel_kpis.py credit-coach/tests/test_robust_recourse.py`
- `python -m pytest credit-coach/tests/test_batch_candidate_diversity.py credit-coach/tests/test_phase_experiment_suite.py`

## Notes
- Trajectory health remains supporting evidence under the inherited KPI governance contract; it does not bypass fairness, reliability, or telemetry gates.

---
*Phase: 14-sequential-recourse-planning*
*Completed: 2026-03-16*
