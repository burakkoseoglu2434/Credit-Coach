---
phase: 33-action-difficulty-execution-modeling
plan: 01
subsystem: action-difficulty-contract
tags: [execution, difficulty, schema, runtime, pytest]
requires: []
provides:
  - canonical action-level difficulty truth
  - alive-only difficulty emission
  - approval-friction separation from customer effort
affects: [phase-33, execution, runtime, schema, messaging]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/data/schema.py
    - credit-coach/src/credit_coach/recourse/execution_probability.py
    - credit-coach/src/credit_coach/cli/run_recourse.py
    - credit-coach/tests/test_recourse_redesign.py
key-decisions:
  - "Difficulty remains distinct from feasibility and only exists for surviving actions."
  - "Approval friction stays separate from customer-effort drivers."
  - "Difficulty truth serializes explicitly instead of being inferred from probability downstream."
patterns-established:
  - "Action-level execution truth now ships as score + label + drivers + approval friction."
requirements-completed: [EXEC-01]
duration: manual-execution
completed: 2026-03-21
---

# Phase 33 Plan 01 Summary

**The execution estimator now emits an explicit action-level difficulty contract instead of leaving follow-through burden implicit inside probability math.**

## Accomplishments

- Added canonical difficulty fields to action and plan contracts: `difficulty_score`, `difficulty_label`, `difficulty_drivers`, `approval_friction`, plan-level difficulty rollups, and follow-through readiness.
- Hardened estimator behavior so invalid or semantic-break actions emit no difficulty truth, while repaired and provisional actions remain eligible.
- Kept approval-dependent friction distinct from customer burden for institutional or dependency-gated actions.
- Extended runtime serialization so roadmap rows, decision logs, and plan rows carry the new difficulty truth without UI-side inference.
- Added regression coverage for long-horizon burden, approval-friction handling, alive-only difficulty emission, and runtime serialization.

## Verification

- `python -m pytest tests/test_recourse_redesign.py tests/test_planner_denied_objective.py -q`

## Notes

- This plan established the explicit difficulty contract; planner leverage and business-safe messaging were tightened in later Phase 33 plans.

---
*Phase: 33-action-difficulty-execution-modeling*
*Completed: 2026-03-21*
