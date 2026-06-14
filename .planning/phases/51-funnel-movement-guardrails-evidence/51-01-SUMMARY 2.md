---
phase: 51-funnel-movement-guardrails-evidence
plan: 01
subsystem: movement-guardrail-owner
tags: [calibration, guardrails, diagnosis, evidence]
requires: []
provides:
  - canonical movement guardrail summary
  - promotion-blocker matrix
  - dominant bottleneck classifier
affects: [phase-51, decision-calibration, calibration-evidence]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/evaluation/decision_calibration.py
    - credit-coach/tests/test_decision_calibration.py
key-decisions:
  - "Phase 51 reuses Phase 49 and Phase 50 comparison outputs instead of inventing a new policy family."
  - "Trust regressions remain first-class hard blockers and override all other diagnoses."
  - "Threshold-family and offer/readiness-family evidence stays attributable as separate candidate families."
patterns-established:
  - "decision_calibration now owns one deterministic explanation for absent funnel movement instead of scattered no_safe_uplift tables."
requirements-completed: [FUN-01, FUN-02, FUN-03]
duration: manual-execution
completed: 2026-04-03
---

# Phase 51 Plan 01 Summary

**Phase 51 now has one canonical owner for movement diagnosis instead of loosely interpreted Phase 49 and Phase 50 outputs.**

## Accomplishments

- Extended `credit-coach/src/credit_coach/evaluation/decision_calibration.py` with a deterministic Phase 51 evidence layer:
  - `build_movement_guardrail_evidence(...)`
  - `build_movement_guardrail_review_markdown(...)`
  - trust-guardrail summary
  - candidate-family summaries
  - promotion-blocker matrix
  - structural and recommendation-space ceiling signals
- Added explicit bottleneck labels:
  - `trust_regression_blocked`
  - `threshold_guardrail_blocked`
  - `offer_readiness_guardrail_blocked`
  - `recommendation_space_limited`
  - `structural_cohort_limited`
  - `mixed_no_safe_uplift`
- Extended Phase 49 and Phase 50 comparison rows with movement counters:
  - `rejected_to_conditional_count`
  - `conditional_to_approved_count`
  - `direct_rejected_to_approved_count`
- Added regression coverage in `credit-coach/tests/test_decision_calibration.py` for:
  - movement-count continuity
  - deterministic structural bottleneck classification
  - guardrail summary markdown rendering

## Verification

- `python -m py_compile credit-coach/src/credit_coach/evaluation/decision_calibration.py credit-coach/tests/test_decision_calibration.py`
- `cd credit-coach && python -m pytest tests/test_decision_calibration.py -q`

## Notes

- This plan introduced no live decision-policy change.
- The primary output is diagnosis quality, not uplift.

---
*Phase: 51-funnel-movement-guardrails-evidence*
*Completed: 2026-04-03*
