---
phase: 12-action-realism-feasibility-expansion
plan: 03
subsystem: recourse-planner
tags: [constraints, planner, approval, diagnostics, pytest]
requires: [12-01, 12-02]
provides:
  - machine-readable dependency, conflict, and approval constraint evaluation for typed actions
  - repaired or provisional plan semantics before ranking
  - canonical action realism summary and breakdown artifacts for Phase 12 evidence
affects: [phase-12, planner, validator, batch-eval, roadmap]
tech-stack:
  added: []
  patterns: [repair-if-safe, hard prerequisites, provisional institutional branch, action realism evidence]
key-files:
  created: [credit-coach/src/credit_coach/recourse/action_constraints.py]
  modified: [credit-coach/src/credit_coach/coaching/planner.py, credit-coach/src/credit_coach/recourse/generator.py, credit-coach/src/credit_coach/safety/validator.py, credit-coach/src/credit_coach/cli/run_recourse.py, credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py, credit-coach/tests/test_action_space.py, credit-coach/tests/test_planner_denied_objective.py, credit-coach/tests/test_recourse_redesign.py]
key-decisions:
  - "Requires relations are hard prerequisites, while institutional approval is carried as a provisional non-winner branch."
  - "Conflict handling uses repair-if-safe and records dropped actions as machine-readable trace events."
patterns-established:
  - "Constraint status now distinguishes valid, repaired, provisional, and invalid plans before ranking."
requirements-completed: [REC-03]
duration: manual-execution
completed: 2026-03-15
---

# Phase 12 Plan 03 Summary

**Action interaction constraints now repair conflicting bundles, preserve approval-pending recommendations as provisional evidence, and keep invalid combinations out of normal winner selection.**

## Accomplishments
- Added a dedicated `action_constraints.py` layer that evaluates prerequisites, conflicts, provided tags, and institutional-approval behavior.
- Taught generator, validator, and planner to carry plan-level constraint status so repaired plans remain explainable and provisional plans stop winning like ordinary recommendations.
- Extended batch outputs with `action_realism_summary.json`, `action_type_breakdown.csv`, `constraint_repair_breakdown.csv`, and `approval_pending_breakdown.csv`.

## Verification
- `python -m pytest credit-coach/tests/test_action_space.py`
- `python -m pytest credit-coach/tests/test_planner_denied_objective.py credit-coach/tests/test_recourse_redesign.py`

## Notes
- Approval-required actions still exist as evidence, but the ranking path now prefers valid or repaired plans whenever they are available.

---
*Phase: 12-action-realism-feasibility-expansion*
*Completed: 2026-03-15*
