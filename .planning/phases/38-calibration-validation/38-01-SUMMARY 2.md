---
phase: 38-calibration-validation
plan: 01
subsystem: calibration-contract
tags: [validation, calibration, portfolio, batch, realism]
requires: []
provides:
  - canonical calibration and validation summary
  - row-level validation ingredients in batch outputs
  - calibration validation batch artifact seam
affects: [phase-38, portfolio-validation, batch-artifacts]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/evaluation/portfolio_validation.py
    - credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py
    - credit-coach/tests/test_portfolio_validation.py
    - credit-coach/tests/test_phase_experiment_suite.py
key-decisions:
  - "Recommendation calibration stays separate from base PD model calibration."
  - "Realism-clean share, false optimism, and unstable target exposure are first-class validation truths."
  - "Batch rows remain the ingredient source for higher-level validation rollups."
patterns-established:
  - "Validation is added as a new portfolio contract rather than by reopening target generation or feasibility logic."
requirements-completed: [CAL-01]
duration: manual-execution
completed: 2026-03-22
---

# Phase 38 Plan 01 Summary

**The engine can now judge whether personalized numeric plans are realistic and honest, not just high-payoff on paper.**

## Accomplishments

- Added a canonical `calibration_validation` summary block to portfolio validation with headline truth for:
  - realism-clean plan rate
  - false optimism exposure
  - unstable target range exposure
  - validated execution-aware carry-through
- Added row-level validation ingredients to batch outputs so the batch seam now carries:
  - false optimism flags
  - unstable target flags
  - realism-clean flags
- Emitted a dedicated `portfolio_calibration_validation_breakdown.csv` artifact from the batch runner.

## Verification

- `python -m pytest credit-coach/tests/test_portfolio_validation.py credit-coach/tests/test_phase_experiment_suite.py -q`

## Notes

- This plan established the validation source-of-truth; segment drift and executive packaging were completed in later Phase 38 plans.

---
*Phase: 38-calibration-validation*
*Completed: 2026-03-22*
