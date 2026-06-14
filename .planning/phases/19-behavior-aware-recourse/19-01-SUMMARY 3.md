---
phase: 19-behavior-aware-recourse
plan: 01
subsystem: execution-truth-hardening
tags: [behavior-aware, execution-probability, realism, pytest]
requires: []
provides:
  - conservative execution-probability posture
  - weighted min-average composite aggregation
  - dual executable vs approval-dependent realization truth
affects: [phase-19, recourse-plans, ranking-inputs, decision-logging]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/recourse/execution_probability.py
    - credit-coach/src/credit_coach/data/schema.py
    - credit-coach/src/credit_coach/cli/run_recourse.py
    - credit-coach/tests/test_recourse_redesign.py
key-decisions:
  - "Execution probability now defaults mildly conservative, especially when burden and horizon compound."
  - "Ambiguous action semantics are penalized rather than receiving optimistic default uplift."
  - "Composite action groups now use a weighted min-average hybrid instead of collapsing to a naive mean or pure minimum."
  - "Approval-dependent realization is serialized separately from executable plan realization."
patterns-established:
  - "Behavior-aware truth is now explicit enough to distinguish executable follow-through from approval-gated branches."
requirements-completed: [PORT-03]
duration: manual-execution
completed: 2026-03-19
---

# Phase 19 Plan 01 Summary

**Execution truth now behaves like a realism-preserving trust layer instead of a neutral heuristic.**

## Accomplishments
- Hardened `execution_probability.py` so long-horizon and high-burden actions are penalized more aggressively, with ambiguity defaulting lower to avoid false optimism.
- Added weighted min-average composite aggregation so grouped actions keep weakest-link pressure without collapsing fully to a pure minimum.
- Extended the plan contract with `approval_dependent_plan_probability` and `mean_approval_dependent_probability` so executable and approval-dependent realization stay distinct.
- Updated recourse serialization to carry the new realization-layer fields into downstream artifacts.
- Added regression tests covering burden-plus-horizon conservatism, weighted composite aggregation, and dual-realization plan truth.

## Verification
- `python -m pytest credit-coach/tests/test_recourse_redesign.py credit-coach/tests/test_planner_denied_objective.py -q`

## Notes
- This is a hardening pass over shipped behavior-aware seams, not a new learned execution model.
- `plan_execution_probability` remains the canonical executable follow-through signal; approval-dependent realization is additive rather than folded into that score.

---
*Phase: 19-behavior-aware-recourse*
*Completed: 2026-03-19*
