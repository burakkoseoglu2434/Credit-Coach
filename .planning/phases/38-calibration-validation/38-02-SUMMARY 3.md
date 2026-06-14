---
phase: 38-calibration-validation
plan: 02
subsystem: drift-and-segment-validation
tags: [validation, segments, drift, narrowness, unit-family]
requires: []
provides:
  - risk-first calibration segment rollups
  - unit-family validation breakdowns
  - suite-visible drift and narrowness signals
affects: [phase-38, suite, portfolio-validation]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/evaluation/portfolio_validation.py
    - credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py
    - credit-coach/tests/test_portfolio_validation.py
    - credit-coach/tests/test_phase_experiment_suite.py
key-decisions:
  - "Risk band remains the primary business lens for validation reading."
  - "Unit-family concentration is treated as a narrowness signal instead of being hidden."
  - "Seed drift is a valid honesty signal, not a reason to suppress evidence."
patterns-established:
  - "Validation rollups now stay portfolio-first while still exposing where realism weakens or optimism concentrates."
requirements-completed: [CAL-01]
duration: manual-execution
completed: 2026-03-22
---

# Phase 38 Plan 02 Summary

**Calibration now tells a segment and drift story instead of stopping at one portfolio-wide average.**

## Accomplishments

- Extended portfolio segment breakdowns with:
  - realism-clean plan rate
  - false optimism exposure
  - unstable target range exposure
- Extended unit-family breakdowns with the same validation signals so the portfolio can show where numeric asks concentrate or stretch.
- Added suite aggregation for:
  - numeric unit-family validation rollups
  - calibration validation breakdowns
  - seed-level drift carried into the aggregated validation summary

## Verification

- `python -m pytest credit-coach/tests/test_portfolio_validation.py credit-coach/tests/test_phase_experiment_suite.py credit-coach/tests/test_batch_candidate_diversity.py -q`

## Notes

- The business layer still stays concise; the richer unit-family and drift details remain in shared artifacts for analyst and proof consumers.

---
*Phase: 38-calibration-validation*
*Completed: 2026-03-22*
