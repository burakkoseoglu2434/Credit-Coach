---
phase: 37-portfolio-level-numeric-impact
plan: 01
subsystem: numeric-impact-contract
tags: [portfolio, numeric-impact, batch, validation, payoff]
requires: []
provides:
  - canonical portfolio-level numeric-impact metric family
  - batch-row numeric impact ingredients
  - numeric impact and unit-family batch artifacts
affects: [phase-37, portfolio-validation, batch-artifacts]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/evaluation/portfolio_validation.py
    - credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py
    - credit-coach/tests/test_portfolio_validation.py
key-decisions:
  - "The portfolio headline pair is nominal vs execution-aware payoff, but the business headline uses execution-aware payoff."
  - "Requested change burden is normalized across mixed units instead of averaging raw deltas."
  - "Offer-bearing plans use realized offer-supported payoff rather than nominal optimism."
patterns-established:
  - "Batch rows now expose numeric burden and realized-payoff ingredients before higher-level rollups consume them."
duration: manual-execution
completed: 2026-03-22
---

# Phase 37 Plan 01 Summary

**The engine can now quantify portfolio-level numeric burden and realized payoff without reopening single-customer contracts.**

## Accomplishments

- Added a canonical numeric-impact metric family to portfolio validation: `numeric_plan_coverage`, `requested_change_burden`, `nominal_portfolio_payoff`, `execution_aware_portfolio_payoff`, `execution_aware_realization`, `realization_gap`, `payoff_per_unit_burden`, and offer-supported payoff splits.
- Normalized mixed-unit asks through a burden index built from primary numeric targets rather than raw delta averaging.
- Added row-level batch fields so `batch_recourse_results.csv` now carries numeric-target count, normalized burden, nominal payoff, execution-aware payoff, realization gap, and realized offer-supported payoff.
- Emitted dedicated numeric-impact and unit-family artifact seams from the batch runner.

## Verification

- `python -m pytest credit-coach/tests/test_portfolio_validation.py credit-coach/tests/test_phase_experiment_suite.py -q`

## Notes

- This plan established the source-of-truth numeric-impact family; segment-priority strategy and executive review packaging were completed in later Phase 37 plans.

---
*Phase: 37-portfolio-level-numeric-impact*
*Completed: 2026-03-22*
