---
phase: 12-action-realism-feasibility-expansion
plan: 02
subsystem: recourse-feasibility
tags: [feasibility, diagnostics, batch, pytest]
requires: [12-01]
provides:
  - financially realistic feasibility rules for income, utilization, credit-limit, and capacity transitions
  - semantic clip-vs-reject behavior for typed actions
  - machine-readable action realism diagnostics in generator and batch outputs
affects: [phase-12, generator, batch-eval, denied-objective]
tech-stack:
  added: []
  patterns: [reason-coded feasibility details, semantic rejection, runtime action realism counters]
key-files:
  created: []
  modified: [credit-coach/src/credit_coach/recourse/feasibility.py, credit-coach/src/credit_coach/recourse/generator.py, credit-coach/src/credit_coach/cli/run_recourse.py, credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py, credit-coach/tests/test_recourse_feasibility.py, credit-coach/tests/test_recourse_generator_action_budget.py]
key-decisions:
  - "Behavioral actions clip first, but structural and institutional actions can be rejected when clipping destroys the action's semantic intent."
  - "Feasibility outcomes must be surfaced as reason-coded runtime diagnostics rather than hidden inside plan scoring."
patterns-established:
  - "apply_target_feasibility_with_details(...) is the canonical seam for realism constraints and semantic rejection."
requirements-completed: [REC-02]
duration: manual-execution
completed: 2026-03-15
---

# Phase 12 Plan 02 Summary

**Financial realism is now enforced with reason-coded clipping and rejection, and recourse runs expose why actions became constrained or infeasible.**

## Accomplishments
- Expanded feasibility rules with monthly-change, income-growth, utilization-drop, credit-limit, and financial-capacity constraints.
- Added semantic rejection logic so heavily clipped structural or institutional actions stop pretending to be valid recommendations.
- Threaded action realism counters and rejection reasons into generator runtime diagnostics and batch summary artifacts.

## Verification
- `python -m pytest credit-coach/tests/test_recourse_feasibility.py`
- `python -m pytest credit-coach/tests/test_recourse_generator_action_budget.py credit-coach/tests/test_planner_denied_objective.py`

## Notes
- Infeasible plans are now measurable through runtime and batch diagnostics instead of appearing as silently weakened high-scoring candidates.

---
*Phase: 12-action-realism-feasibility-expansion*
*Completed: 2026-03-15*
