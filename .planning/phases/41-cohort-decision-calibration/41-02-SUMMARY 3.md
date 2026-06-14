---
phase: 41-cohort-decision-calibration
plan: 02
subsystem: shadow-calibration-and-policy-comparison
tags: [engine, calibration, thresholds, pytest]
requires: [01]
provides:
  - analysis-only candidate policy comparison
  - false-positive proxy and delta-vs-baseline metrics
  - decision shift matrix and segment breakdown artifacts
affects: [phase-41, shadow-calibration, policy-comparison, threshold-review]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/evaluation/decision_calibration.py
    - credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py
    - credit-coach/tests/test_decision_calibration.py
    - credit-coach/tests/test_customer_artifact_collection.py
key-decisions:
  - "Candidate policies are evaluated in shadow only and can never overwrite raw or business-facing decision truth."
  - "False-positive proxy is formalized from low realization, weak readiness alignment, and internal-review pressure."
  - "Calibration comparisons are cohort-first with supporting segment lenses rather than becoming a second decision system."
patterns-established:
  - "Threshold review now produces baseline deltas and shift matrices under one reusable comparison contract."
requirements-completed: [CAL-02]
duration: manual-execution
completed: 2026-03-23
---

# Phase 41 Plan 02 Summary

**The repo can now compare shipped and candidate decision policies without leaking candidate outcomes into customer-facing truth.**

## Accomplishments

- Added analysis-only candidate policy evaluation on top of the shipped Phase 40.5 payload, including relaxed and strict shadow policy baselines.
- Implemented the formal `false_positive_proxy` contract and delta-vs-baseline reporting to distinguish healthy approval lift from optimism drift.
- Added decision shift-matrix output and supporting segment breakdowns for `risk_band`, `expected_readiness`, `conditional_type`, `offer_needed_flag`, and `decision_confidence_band`.
- Kept policy comparison explicitly read-only so Phase 41 remains a measurement layer, not a second decision owner.

## Verification

- `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py -q`

## Notes

- This plan closes the calibration-analysis seam. Final packaging into manifest, summary, and collection-root artifacts completes in Plan `03`.

---
*Phase: 41-cohort-decision-calibration*
*Completed: 2026-03-23*
