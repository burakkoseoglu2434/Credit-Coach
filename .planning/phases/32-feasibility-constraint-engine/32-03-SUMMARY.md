---
phase: 32-feasibility-constraint-engine
plan: 03
subsystem: feasibility-visibility-and-downstream-alignment
tags: [feasibility, messaging, proof, portfolio, runtime, pytest]
requires: [32-01, 32-02]
provides:
  - business-safe feasibility outcome labels
  - technical reveal with minimum feasibility trace fields
  - portfolio validation aligned to canonical feasibility drop reasons
affects: [phase-32, messaging, runtime, portfolio-validation, proof]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/coaching/messaging.py
    - credit-coach/src/credit_coach/cli/run_recourse.py
    - credit-coach/src/credit_coach/evaluation/portfolio_validation.py
    - credit-coach/tests/test_messaging.py
    - credit-coach/tests/test_portfolio_validation.py
requirements-completed:
  - FEAS-01
duration: manual-execution
completed: 2026-03-21
---

# Phase 32 Plan 03 Summary

**Feasibility truth now shows up at the right density: business-safe by default and technically explicit on demand.**

## Accomplishments

- Added business-safe feasibility outcome labels to step narratives without leaking raw reason codes into default product language.
- Normalized technical reveal output so `constraints_applied` now includes the minimum canonical feasibility fields across action-level and plan-level truth.
- Extended runtime roadmap serialization with feasibility metadata so engine-owned product consumers do not need to infer or invent feasibility state.
- Updated portfolio validation to reason about canonical feasibility statuses and drop reasons rather than legacy ad hoc status interpretation.
- Closed `FEAS-01` and aligned the milestone state to start Phase 33.

## Verification

- `python -m pytest credit-coach/tests/test_recourse_feasibility.py credit-coach/tests/test_action_space.py credit-coach/tests/test_recourse_redesign.py credit-coach/tests/test_planner_denied_objective.py credit-coach/tests/test_messaging.py credit-coach/tests/test_portfolio_validation.py credit-coach/tests/test_recourse_generator_action_budget.py -q`
- `git diff --check`

## Notes

- `invalid` remains technical-only: it never appears as a default product-facing feasibility label.
- Raw reason codes still exist, but they are confined to technical reveal, batch analysis, and validation layers.

---
*Phase: 32-feasibility-constraint-engine*
*Completed: 2026-03-21*
