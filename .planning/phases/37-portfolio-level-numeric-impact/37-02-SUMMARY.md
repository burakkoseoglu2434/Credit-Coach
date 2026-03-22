---
phase: 37-portfolio-level-numeric-impact
plan: 02
subsystem: segment-strategy-rollups
tags: [portfolio, segments, risk-band, recoverability, offer-dependency]
requires: []
provides:
  - strategy-oriented numeric-impact segment rollups
  - highest-payoff and highest-strain segment insight
  - offer-dependency portfolio narrative
affects: [phase-37, segment-breakdown, portfolio-strategy]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/evaluation/portfolio_validation.py
    - credit-coach/tests/test_portfolio_validation.py
key-decisions:
  - "Risk band remains the primary portfolio lens for numeric-impact reading."
  - "Recoverability is the secondary lens for burden-versus-realization strain."
  - "Offer dependency remains explicit rather than hidden inside aggregate payoff."
patterns-established:
  - "Segment reporting stays executive and strategy-oriented while technical tables still carry the full breakdown."
duration: manual-execution
completed: 2026-03-22
---

# Phase 37 Plan 02 Summary

**Portfolio impact now tells a segment strategy story instead of stopping at cohort-wide averages.**

## Accomplishments

- Extended the segment breakdown contract with numeric plan coverage, requested-change burden, nominal and execution-aware payoff, realization gap, payoff-per-unit-burden, and realized offer-supported payoff.
- Added explicit segment-priority outputs for:
  - highest payoff segment
  - highest burden / lowest realization segment
  - offer-dependent segment
- Kept `risk_band` as the primary business lens, `recoverability_segment` as the strain lens, and `offer_needed_segment` as the offer-dependency lens.

## Verification

- `python -m pytest credit-coach/tests/test_portfolio_validation.py credit-coach/tests/test_phase_experiment_suite.py -q`

## Notes

- The default business layer still avoids raw slice dumps; the richer per-segment numeric columns remain available in the technical breakdown CSV.

---
*Phase: 37-portfolio-level-numeric-impact*
*Completed: 2026-03-22*
