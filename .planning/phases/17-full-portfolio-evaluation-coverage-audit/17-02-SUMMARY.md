---
phase: 17-full-portfolio-evaluation-coverage-audit
plan: 02
subsystem: portfolio-segment-diagnostics
tags: [segments, behavior-aware, offers, trajectory, suite-mirroring, pytest]
requires: [17-01]
provides:
  - segment rollups for risk, income, stress, recoverability, and offer-needed slices
  - explicit behavior-aware vs nominal improvement comparison
  - offer diagnostics and primary trajectory-class proof mirrored into suite outputs
affects: [phase-17, suite, portfolio-proof, offer-proof, trajectory-proof]
tech-stack:
  added: []
  patterns: [derived segments, trajectory classes, seeded suite mirroring]
key-files:
  created: []
  modified: [credit-coach/src/credit_coach/evaluation/portfolio_validation.py, credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py, credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py, credit-coach/tests/test_phase_experiment_suite.py]
key-decisions:
  - "`recoverability_segment` and `offer_needed_segment` are derived proof axes, not underwriting labels."
  - "Each plan maps to one primary trajectory class for portfolio storytelling."
  - "Seeded suite mirrors canonical portfolio proof instead of redefining a second metric language."
patterns-established:
  - "Portfolio proof now surfaces where the engine works, where it struggles, where offers matter, and where early-health breaks."
requirements-completed: [PORT-01]
duration: manual-execution
completed: 2026-03-18
---

# Phase 17 Plan 02 Summary

**Portfolio proof now produces strategy insight, not just slice dumps.**

## Accomplishments
- Extended the portfolio validation seam with segment rollups over `risk_band`, `income_band`, `stress_band`, `recoverability_segment`, and `offer_needed_segment`.
- Added first-class offer diagnostics, behavior-aware vs nominal comparison tables, and canonical trajectory classes such as `early_healthy`, `delayed_only`, and `replan_prone`.
- Mirrored the new proof family through `run_phase_experiment_suite.py` so seeded suite evidence carries the same portfolio story and release-pack references.

## Verification
- `python -m pytest credit-coach/tests/test_phase_experiment_suite.py credit-coach/tests/test_portfolio_validation.py`
- `python -m pytest credit-coach/tests/test_portfolio_validation.py credit-coach/tests/test_batch_candidate_diversity.py`

## Notes
- Product strategy questions can now be answered directly from artifacts: where offers are required, where early health is weak, and which slices have low product-ready coverage.
- Suite-level supporting and release artifacts now include the Phase 17 portfolio proof family.

---
*Phase: 17-full-portfolio-evaluation-coverage-audit*
*Completed: 2026-03-18*
