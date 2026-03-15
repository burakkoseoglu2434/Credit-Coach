---
phase: 12-action-realism-feasibility-expansion
plan: 01
subsystem: recourse-actions
tags: [taxonomy, recourse, serialization, pytest]
requires: [phase-11]
provides:
  - typed behavioral, structural, and institutional action metadata across recourse plans
  - shared action grouping for composite actions such as refinance
  - user-facing action identity in roadmap and plan serialization
affects: [phase-12, generator, roadmap, dice]
tech-stack:
  added: []
  patterns: [hybrid action unit, action_key-first serialization, shared action-group ids]
key-files:
  created: []
  modified: [credit-coach/src/credit_coach/data/schema.py, credit-coach/src/credit_coach/recourse/action_space.py, credit-coach/src/credit_coach/recourse/generator.py, credit-coach/src/credit_coach/cli/run_recourse.py, credit-coach/tests/test_action_space.py, credit-coach/tests/test_recourse_funnel_kpis.py]
key-decisions:
  - "The primary action unit stays hybrid: action_key is user-facing while feature_name remains the effect anchor."
  - "Composite actions are represented as multiple PlanAction rows under one stable action_group_id instead of a second plan object."
patterns-established:
  - "Typed action metadata now flows from ACTION_CATALOG into generator, DICE, roadmap JSON, and plan rows."
requirements-completed: [REC-01]
duration: manual-execution
completed: 2026-03-15
---

# Phase 12 Plan 01 Summary

**Typed action taxonomy now expresses behavioral, structural, and institutional recommendations without dropping the existing feature-grounded planner seam.**

## Accomplishments
- Added explicit action metadata fields to `PlanAction` so generated plans carry `action_key`, `action_class`, grouping, approval, and diagnostic semantics.
- Rebuilt `action_space.py` around a shared catalog of real-world action templates and mapped actionable features onto that catalog.
- Extended internal and DICE serialization so roadmap outputs and tabular plan rows expose the typed action contract.

## Verification
- `python -m pytest credit-coach/tests/test_action_space.py`
- `python -m pytest credit-coach/tests/test_recourse_funnel_kpis.py credit-coach/tests/test_recourse_redesign.py`

## Notes
- The taxonomy intentionally remains hybrid for brownfield compatibility: planner effects are still feature-level even though user-facing outputs are now action-key-first.

---
*Phase: 12-action-realism-feasibility-expansion*
*Completed: 2026-03-15*
