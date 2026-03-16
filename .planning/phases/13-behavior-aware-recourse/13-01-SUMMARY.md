---
phase: 13-behavior-aware-recourse
plan: 01
subsystem: recourse-execution-probability
tags: [execution-probability, recourse, serialization, pytest]
requires: [phase-12]
provides:
  - canonical action-level and plan-level execution-likelihood fields
  - group-aware probability aggregation for composite actions
  - backward-compatible execution metadata in generated and serialized plans
affects: [phase-13, generator, recourse-cli, batch-eval]
tech-stack:
  added: [credit-coach/src/credit_coach/recourse/execution_probability.py]
  patterns: [explicit probability seam, action-group aggregation, provisional probability semantics]
key-files:
  created: [credit-coach/src/credit_coach/recourse/execution_probability.py]
  modified: [credit-coach/src/credit_coach/data/schema.py, credit-coach/src/credit_coach/recourse/generator.py, credit-coach/src/credit_coach/cli/run_recourse.py, credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py, credit-coach/tests/test_recourse_redesign.py, credit-coach/tests/test_robust_recourse.py]
key-decisions:
  - "Canonical probability units are action_execution_probability and plan_execution_probability."
  - "Composite actions aggregate through action_group_id before rolling up to the plan level."
  - "Approval-dependent actions expose approval_dependent_probability instead of pretending to be ordinary executable winners."
patterns-established:
  - "annotate_plan_execution_probability(...) is now the shared seam for threading execution-likelihood evidence onto PlanRecord and PlanAction."
requirements-completed: [REC-04]
duration: manual-execution
completed: 2026-03-16
---

# Phase 13 Plan 01 Summary

**Execution likelihood is now explicit in the recourse contract instead of being an implicit assumption hidden behind nominal plan quality.**

## Accomplishments
- Added `action_execution_probability`, `approval_dependent_probability`, `action_group_execution_probability`, and plan-level execution fields to the core plan schemas.
- Introduced a dedicated `execution_probability.py` seam that estimates action and plan execution likelihood from typed action metadata, timing, cost, feasibility state, composite grouping, and lightweight customer context.
- Threaded execution-probability metadata through internal, DICE, fallback, and serialized plan outputs so recourse artifacts stay machine-readable and backward-compatible.

## Verification
- `python -m pytest credit-coach/tests/test_recourse_redesign.py`
- `python -m pytest credit-coach/tests/test_recourse_redesign.py credit-coach/tests/test_robust_recourse.py`

## Notes
- Phase 13 intentionally keeps the estimator heuristic and replaceable; learned compliance models remain deferred until the later outcome-learning milestone.

---
*Phase: 13-behavior-aware-recourse*
*Completed: 2026-03-16*
