---
phase: 32-feasibility-constraint-engine
plan: 02
subsystem: repair-vs-reject-and-ranking-rollups
tags: [feasibility, repair, invalidation, planner, validator, pytest]
requires: [32-01]
provides:
  - repair-if-safe / reject-if-semantic-break posture
  - primary-meaning preservation for grouped actions
  - ranking-safe valid-before-repaired preference
affects: [phase-32, action-constraints, planner, validator]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/recourse/action_constraints.py
    - credit-coach/src/credit_coach/coaching/planner.py
    - credit-coach/tests/test_action_space.py
    - credit-coach/tests/test_planner_denied_objective.py
    - credit-coach/tests/test_recourse_redesign.py
key-decisions:
  - "Composite actions die when the primary semantic anchor disappears after feasibility."
  - "Repaired plans can still compete, but valid plans remain first-class."
  - "Provisional remains dependency-gated realism rather than infeasible failure."
patterns-established:
  - "Constraint resolution is now semantic-preservation aware rather than simple drop-or-keep logic."
requirements-completed: []
duration: manual-execution
completed: 2026-03-21
---

# Phase 32 Plan 02 Summary

**Repair now means “softened without losing meaning,” and invalid now means “the plan stopped being real.”**

## Accomplishments

- Hardened constraint resolution around primary semantic preservation so composite actions cannot survive as secondary-only leftovers.
- Kept `repair-if-safe` behavior for dropped conflicting groups and other safe softening paths, while explicitly killing semantically broken groups.
- Preserved `provisional` for dependency-gated institution behavior instead of collapsing it into failure.
- Added ranking regression coverage showing that repaired plans remain contenders but still trail comparable valid plans.

## Verification

- `python -m pytest credit-coach/tests/test_planner_denied_objective.py credit-coach/tests/test_messaging.py credit-coach/tests/test_portfolio_validation.py credit-coach/tests/test_recourse_generator_action_budget.py -q`

## Notes

- Planner ordering already had most of the valid-before-repaired preference; this plan hardened that behavior with explicit regression protection.
- Validator behavior remained compatible with the new contract because invalid, repaired, and provisional semantics were preserved at plan level.

---
*Phase: 32-feasibility-constraint-engine*
*Completed: 2026-03-21*
