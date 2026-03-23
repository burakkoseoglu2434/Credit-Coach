---
phase: 41-cohort-decision-calibration
plan: 01
subsystem: cohort-semantics-and-funnel-contract
tags: [engine, collection, calibration, pytest]
requires: []
provides:
  - deterministic cohort policies for pilot and stress-test collection runs
  - canonical funnel summary over external and internal decision states
  - readiness distribution and normalized status-by-readiness outputs
affects: [phase-41, cohort-selection, funnel-reporting, readiness-contract]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/evaluation/decision_calibration.py
    - credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py
    - credit-coach/tests/test_decision_calibration.py
    - credit-coach/tests/test_customer_artifact_collection.py
key-decisions:
  - "Collection runner now measures the shipped decision owner across explicit cohort policies instead of relying on denied-only sampling."
  - "Readiness reporting reuses the Phase 40.5 taxonomy exactly and exposes normalized `P(status | readiness)` tables."
  - "Stress-test and pilot-like cohorts are both explicit and machine-readable in collection metadata."
patterns-established:
  - "Cohort semantics and funnel math live in a shared evaluation module rather than ad hoc collector branches."
requirements-completed: [CAL-01]
duration: manual-execution
completed: 2026-03-23
---

# Phase 41 Plan 01 Summary

**Collection runs now understand real cohort semantics and can describe the shipped decision owner as a fintech funnel instead of only a denied-customer artifact dump.**

## Accomplishments

- Added a shared `decision_calibration` module that owns cohort policy semantics for `pilot_mixed`, `risk_band_balanced`, `ops_queue_replay`, `offer_needed_balanced`, and `denied_first_near`.
- Reworked collection selection to record deterministic metadata such as `selection_policy_name`, `selection_fill_behavior`, `cohort_bucket`, and cohort-purpose definitions.
- Added canonical funnel aggregates for external three-state decisions plus internal review share, alongside readiness distribution and normalized `status_by_readiness` outputs.
- Preserved the Phase 40.5 decision owner as the only decision truth while making cohort selection and funnel reporting reusable outside the collector.

## Verification

- `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py -q`

## Notes

- This plan establishes the measurement baseline. Shadow policy comparison, false-positive proxy math, and packaging closure continue in Plans `02` and `03`.

---
*Phase: 41-cohort-decision-calibration*
*Completed: 2026-03-23*
