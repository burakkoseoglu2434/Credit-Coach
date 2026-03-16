---
phase: 14-sequential-recourse-planning
plan: 03
subsystem: phase-aware-optimization
tags: [planner, challenger, suite, review, pytest]
requires: [14-01, 14-02]
provides:
  - short-term-first phase-aware planner ordering
  - trajectory-aware suite and challenger evidence
  - explanation-first review coverage for trajectory quality
affects: [phase-14, planner, challenger, suite, acceptance-review]
tech-stack:
  added: []
  patterns: [gate-first ranking, policy labels, shared trajectory evidence]
key-files:
  created: []
  modified: [credit-coach/src/credit_coach/coaching/planner.py, credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py, credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py, credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py, credit-coach/src/credit_coach/ops/kpi_contract.py, credit-coach/tests/test_planner_denied_objective.py, credit-coach/tests/test_challenger_matrix_selection.py, credit-coach/tests/test_phase_experiment_suite.py]
key-decisions:
  - "Short-term checkpoint health stays primary; long-horizon upside is bonus only when early health is acceptable."
  - "High-risk ordering is more conservative and still subordinate to inherited gates."
  - "Trajectory quality is surfaced through interpretable policy labels: `stabilize_first`, `balanced_progress`, and `long_horizon_heavy`."
patterns-established:
  - "Batch, suite, challenger, and acceptance review now share one trajectory evidence language."
requirements-completed: [REC-06, REC-07]
duration: manual-execution
completed: 2026-03-16
---

# Phase 14 Plan 03 Summary

**The planner now ranks trajectories with an explicit short-term-first policy, and the resulting trajectory quality is comparable across batch, suite, challenger, and review outputs.**

## Accomplishments
- Added a phase-aware planner score and policy labels without weakening inherited gate-first behavior.
- Surfaced trajectory summaries and breakdowns through suite and challenger artifacts under stable machine-readable names.
- Extended milestone review rendering with a concise `Trajectory Summary` section so checkpoint health and replan pressure are visible in release review.

## Verification
- `python -m pytest credit-coach/tests/test_planner_denied_objective.py`
- `python -m pytest credit-coach/tests/test_challenger_matrix_selection.py tests/test_phase_experiment_suite.py tests/test_recourse_funnel_kpis.py`

## Notes
- Trajectory evidence remains mandatory supporting evidence and non-blocking, consistent with the Phase 13 behavior-aware contract.

---
*Phase: 14-sequential-recourse-planning*
*Completed: 2026-03-16*
