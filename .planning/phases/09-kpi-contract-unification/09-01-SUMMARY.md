---
phase: 09-kpi-contract-unification
plan: 01
subsystem: ops
tags: [kpi-contract, smoke, challenger, suite, pytest]
requires: []
provides:
  - shared KPI comparator and snapshot helpers
  - aligned failed-check naming across suite, smoke, and challenger
  - challenger violation scoring built on the shared KPI contract
affects: [phase-09, smoke, suite, challenger, release-decision]
tech-stack:
  added: []
  patterns: [shared KPI contract helper, canonical metric normalization]
key-files:
  created: []
  modified: [credit-coach/src/credit_coach/ops/kpi_contract.py, credit-coach/src/credit_coach/ops/release_decision.py, credit-coach/src/credit_coach/cli/run_production_smoke.py, credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py, credit-coach/tests/test_phase_experiment_suite.py, credit-coach/tests/test_production_smoke.py]
key-decisions:
  - "Threshold direction, failed-check naming, and violation scoring now come from `credit_coach.ops.kpi_contract` rather than runner-private logic."
  - "Phase 8 release semantics stay layered above the shared KPI evaluator instead of being redefined in a runner."
patterns-established:
  - "Runners should normalize local metrics into canonical KPI names before evaluating pass/fail semantics."
requirements-completed: [KPI-01]
duration: manual-execution
completed: 2026-03-14
---

# Phase 9 Plan 01 Summary

**Shared KPI semantics are now centralized, and smoke, suite, and challenger all consume the same threshold and failed-check contract.**

## Accomplishments
- Expanded `credit_coach.ops.kpi_contract` into a comparator, failed-check, violation-score, and snapshot helper layer.
- Refactored release-decision seed evaluation to reuse the shared KPI contract for lift, reliability, and secondary fairness checks.
- Replaced smoke snapshot mapping and challenger gate-violation scoring with the shared KPI helper path.

## Verification
- `python -m pytest credit-coach/tests/test_phase_experiment_suite.py credit-coach/tests/test_production_smoke.py credit-coach/tests/test_challenger_matrix_selection.py credit-coach/tests/test_release_decision.py`

## Notes
- Task commits remain consolidated because the local GSD helper is incomplete in this repo.

---
*Phase: 09-kpi-contract-unification*
*Completed: 2026-03-14*
