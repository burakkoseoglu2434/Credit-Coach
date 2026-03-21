---
phase: 33-action-difficulty-execution-modeling
plan: 02
subsystem: group-and-plan-execution-aggregation
tags: [execution, planner, ranking, aggregation, pytest]
requires:
  - phase: 33-01
    provides: action-level difficulty truth
provides:
  - group-first difficulty-aware plan aggregation
  - stronger planner leverage for realistic follow-through
  - explicit load-sensitive plan ordering
affects: [phase-33, planner, behavior-aware, ranking]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/recourse/execution_probability.py
    - credit-coach/src/credit_coach/coaching/planner.py
    - credit-coach/tests/test_planner_denied_objective.py
    - credit-coach/tests/test_recourse_redesign.py
key-decisions:
  - "Grouped actions collapse to one business-level execution truth before plan-level rollup."
  - "Low readiness and high difficulty produce explicit planner demotion rather than being softened away."
  - "Approval-dependent plan truth remains separate from normal plan execution probability."
patterns-established:
  - "Execution-aware ranking now reads explicit difficulty rollups instead of only raw probability."
requirements-completed: [EXEC-01]
duration: manual-execution
completed: 2026-03-21
---

# Phase 33 Plan 02 Summary

**Plan ordering now treats grouped-action burden, explicit load, and low follow-through readiness as first-class plan-quality signals.**

## Accomplishments

- Preserved weakest-link-aware group aggregation while adding plan-level difficulty rollups and a follow-through readiness label.
- Hardened planner penalties so high-difficulty, low-readiness contenders lose ground more deterministically, especially when multi-action load grows.
- Kept `plan_execution_probability` and `approval_dependent_plan_probability` separate while still letting approval pressure influence defensibility.
- Added regression coverage proving that a steadier lower-burden plan can beat a nominally stronger but execution-weaker alternative.

## Verification

- `python -m pytest tests/test_recourse_redesign.py tests/test_planner_denied_objective.py -q`

## Notes

- This plan focused on aggregation and ordering; business-facing phrasing and proof/suite alignment were completed in `33-03`.

---
*Phase: 33-action-difficulty-execution-modeling*
*Completed: 2026-03-21*
