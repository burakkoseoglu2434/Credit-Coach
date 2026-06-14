---
phase: 31-numeric-target-engine
plan: 01
subsystem: numeric-target-contract-and-unit-catalog
tags: [numeric-targets, units, contract, catalog, pytest]
requires: []
provides:
  - canonical `PrimaryNumericTarget` schema
  - deterministic metric and unit defaults by `action_family`
  - primary-target metadata on semantic actions
affects: [phase-31, action-space, schema, numeric-targets]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/recourse/action_space.py
    - credit-coach/src/credit_coach/data/schema.py
    - credit-coach/tests/test_action_space.py
    - credit-coach/tests/test_recourse_redesign.py
key-decisions:
  - "Numeric targeting starts from minimum credible change rather than optimistic maximum movement."
  - "Each action carries one canonical primary numeric target with deterministic metric key and unit."
  - "Mixed-unit actions keep secondary effects outside the primary business contract."
patterns-established:
  - "Phase 31 starts from engine-owned numeric target identity rather than UI-side interpretation."
requirements-completed: []
duration: manual-execution
completed: 2026-03-21
---

# Phase 31 Plan 01 Summary

**The engine now has a real numeric target contract instead of loosely attached numeric fields.**

## Accomplishments

- Added `PrimaryNumericTarget` as a canonical schema layer with metric key, unit, current value, target value, signed delta, due month, and direction.
- Hardened the action catalog with family-level numeric defaults and explicit feature overrides so metric and unit selection stay deterministic.
- Attached primary target metadata directly to semantic actions, keeping taxonomy and numeric meaning on the same engine-owned seam.
- Extended regression coverage so family defaults, primary-target selection, and fallback population are protected at the schema and action-space layer.

## Verification

- `python -m pytest credit-coach/tests/test_action_space.py -q`
- `python -m pytest credit-coach/tests/test_action_space.py credit-coach/tests/test_recourse_redesign.py -q`

## Notes

- This plan intentionally stops short of feasibility verdicts; it defines the numeric target contract but does not clip, repair, or reject targets yet.
- Mixed-unit actions are now explicitly modeled as one primary numeric target plus technical secondary effects.

---
*Phase: 31-numeric-target-engine*
*Completed: 2026-03-21*
