---
phase: 32-feasibility-constraint-engine
plan: 01
subsystem: verdict-and-constraint-family-normalization
tags: [feasibility, constraints, verdicts, traceability, pytest]
requires: []
provides:
  - canonical action-level feasibility verdicts
  - normalized `constraint_family` classification
  - action-level feasibility trace fields carried through schema and runtime
affects: [phase-32, feasibility, constraints, schema, runtime]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/recourse/feasibility.py
    - credit-coach/src/credit_coach/recourse/action_constraints.py
    - credit-coach/src/credit_coach/data/schema.py
    - credit-coach/src/credit_coach/recourse/generator.py
    - credit-coach/src/credit_coach/cli/run_recourse.py
    - credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py
    - credit-coach/tests/test_recourse_feasibility.py
    - credit-coach/tests/test_action_space.py
    - credit-coach/tests/test_recourse_redesign.py
key-decisions:
  - "Legacy `rejected` action-level feasibility is now canonical `invalid`."
  - "Feasibility truth carries one dominant `constraint_family` plus granular reason codes."
  - "Clipped remains action-level while plan-level constraint rollup stays in the valid/repaired/provisional/invalid family."
patterns-established:
  - "Numeric-target feasibility emits raw technical truth that downstream layers can consume without reinterpretation."
requirements-completed: []
duration: manual-execution
completed: 2026-03-21
---

# Phase 32 Plan 01 Summary

**The feasibility layer now speaks one canonical verdict language instead of mixed legacy status terms.**

## Accomplishments

- Replaced action-level `rejected` semantics with canonical `invalid` while preserving `valid`, `clipped`, and `provisional`.
- Added dominant `constraint_family` classification above granular reason codes across feasibility and action-constraint traces.
- Extended `PlanAction` with machine-readable feasibility fields such as `constraint_family`, `constraint_reason_codes`, `was_clipped`, `dependency_gate`, and `semantic_preserved`.
- Pushed the normalized feasibility truth through generator, CLI runtime, and batch-eval construction paths so action artifacts no longer need legacy reinterpretation.
- Added regression coverage for semantic invalidation, missing mandatory dependency input, and normalized interaction/dependency traces.

## Verification

- `python -m pytest credit-coach/tests/test_recourse_feasibility.py credit-coach/tests/test_action_space.py credit-coach/tests/test_recourse_redesign.py -q`

## Notes

- This plan normalized feasibility truth and trace structure only; ranking and business-safe visibility were completed in later Phase 32 plans.
- Existing metric names like `action_realism_rejected_action_count` remain for backward compatibility, but they now count canonical `invalid` events.

---
*Phase: 32-feasibility-constraint-engine*
*Completed: 2026-03-21*
