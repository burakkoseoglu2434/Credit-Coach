---
phase: 38-calibration-validation
plan: 03
subsystem: review-packaging
tags: [validation, review, business-safe, suite, honesty]
requires: []
provides:
  - business-safe calibration review packaging
  - suite-aligned validation contract
  - final regression closure for Phase 38
affects: [phase-38, review, suite, portfolio-validation]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/evaluation/portfolio_validation.py
    - credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py
    - credit-coach/tests/test_portfolio_validation.py
    - credit-coach/tests/test_phase_experiment_suite.py
provides_notes:
  - "No separate UI-side or proof-side validation logic was introduced."
key-decisions:
  - "Validation review stays more honest than impressive."
  - "Calibration truth is rendered as a dedicated review section instead of being buried under numeric impact."
  - "Suite consumers mirror the same validation contract rather than inventing alternate rollups."
patterns-established:
  - "Business review remains concise while technical transparency stays available through the same artifact family."
requirements-completed: [CAL-01]
duration: manual-execution
completed: 2026-03-22
---

# Phase 38 Plan 03 Summary

**The portfolio review can now say whether personalized numeric planning is realistic, optimistic, unstable, or narrower than expected.**

## Accomplishments

- Added a dedicated `Calibration & Validation` section to the portfolio review with:
  - realism-clean plan rate
  - false optimism exposure
  - unstable target range exposure
  - validated execution-aware carry-through
  - narrow distribution exposure
- Added supporting insight lines for:
  - highest realism segment
  - highest optimism segment
  - highest instability segment
  - narrowest unit family
- Kept the review business-safe while preserving the technical breakdowns and suite-level mirrors underneath.

## Verification

- `python -m pytest credit-coach/tests/test_portfolio_validation.py credit-coach/tests/test_phase_experiment_suite.py credit-coach/tests/test_kpi_contract.py credit-coach/tests/test_batch_candidate_diversity.py -q`

## Notes

- No new UI-side interpretation was introduced; downstream consumers still read one engine-owned validation contract.

---
*Phase: 38-calibration-validation*
*Completed: 2026-03-22*
