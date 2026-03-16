---
phase: 13-behavior-aware-recourse
plan: 02
subsystem: recourse-ranking
tags: [planner, expected-utility, challenger, batch, pytest]
requires: [13-01]
provides:
  - expected-utility-aware ranking under inherited gate constraints
  - high-risk ordering that prefers likely, feasible plans without overriding governance
  - canonical behavior-aware batch and challenger evidence artifacts
affects: [phase-13, planner, batch-eval, challenger]
tech-stack:
  added: []
  patterns: [gate-first ranking, non-blocking expected utility, behavior-aware evidence]
key-files:
  created: []
  modified: [credit-coach/src/credit_coach/coaching/planner.py, credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py, credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py, credit-coach/tests/test_planner_denied_objective.py, credit-coach/tests/test_batch_candidate_diversity.py, credit-coach/tests/test_challenger_matrix_selection.py]
key-decisions:
  - "Expected utility uses the locked primary term plan_execution_probability × nominal_pd_improvement."
  - "Gate filters remain authoritative; execution likelihood only reorders plans after safety and governance eligibility."
  - "High-risk ranking keeps nominal lift as the primary signal and uses execution likelihood as ordering evidence."
patterns-established:
  - "behavior_aware_summary.json plus execution_probability_breakdown.csv and partial_execution_breakdown.csv are the canonical Phase 13 evidence bundle."
requirements-completed: [REC-04, REC-05]
duration: manual-execution
completed: 2026-03-16
---

# Phase 13 Plan 02 Summary

**Planner ranking is now behavior-aware: among safe plans, more executable recommendations can outrank less realistic ones without weakening inherited fairness, reliability, or telemetry gates.**

## Accomplishments
- Extended planner sorting so expected PD improvement and plan execution probability affect ordering only after constraint and gate checks.
- Published canonical `behavior_aware_summary.json` and companion breakdown CSVs from batch evaluation, then carried that evidence into challenger summaries.
- Added regression coverage for expected-utility ordering and behavior-aware artifact generation so later tuning cannot silently bypass the gate-first ranking rule.

## Verification
- `python -m pytest credit-coach/tests/test_planner_denied_objective.py`
- `python -m pytest credit-coach/tests/test_batch_candidate_diversity.py credit-coach/tests/test_challenger_matrix_selection.py`

## Notes
- Behavior-aware evidence is mandatory supporting evidence in Phase 13, but it is intentionally non-blocking and does not redefine the release or milestone-acceptance contract.

---
*Phase: 13-behavior-aware-recourse*
*Completed: 2026-03-16*
