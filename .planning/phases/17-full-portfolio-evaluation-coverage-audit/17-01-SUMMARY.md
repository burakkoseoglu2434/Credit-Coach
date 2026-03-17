---
phase: 17-full-portfolio-evaluation-coverage-audit
plan: 01
subsystem: portfolio-coverage-foundation
tags: [portfolio-validation, coverage-funnel, reality-gap, batch-eval, pytest]
requires: []
provides:
  - canonical `portfolio_validation_summary.json` for full-cohort proof
  - explicit `raw -> valid -> governance-safe -> product-ready` coverage funnel
  - funnel drop-reason and reality-gap base diagnostics
affects: [phase-17, batch-eval, portfolio-proof, product-readiness]
tech-stack:
  added: [credit-coach/src/credit_coach/evaluation/portfolio_validation.py]
  patterns: [artifact-first portfolio proof, coverage funnel, audit-first reality-gap]
key-files:
  created: [credit-coach/src/credit_coach/evaluation/portfolio_validation.py, credit-coach/tests/test_portfolio_validation.py]
  modified: [credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py]
key-decisions:
  - "Whole-population proof is canonical; denied-only views remain explicit secondary comparisons."
  - "`valid` coverage excludes rejected, infeasible, provisional-only, and degenerate plans."
  - "`product_ready` is downstream of governance safety and the absence of critical reality-gap flags."
patterns-established:
  - "Batch evaluation now emits machine-readable portfolio proof tables alongside existing batch artifacts."
requirements-completed: [PORT-01]
duration: manual-execution
completed: 2026-03-18
---

# Phase 17 Plan 01 Summary

**Phase 17 now has a canonical whole-cohort proof seam instead of relying on selected demo stories.**

## Accomplishments
- Added `portfolio_validation.py` to compute full-population coverage, product-ready rates, and base reality-gap diagnostics from batch outputs.
- Wired `run_batch_recourse_eval.py` to emit `portfolio_validation_summary.json` plus coverage, drop-reason, and reality-gap breakdown tables.
- Added deterministic tests that lock the raw/valid/governance-safe/product-ready funnel and brownfield-safe missing-column behavior.

## Verification
- `python -m pytest credit-coach/tests/test_portfolio_validation.py credit-coach/tests/test_recourse_funnel_kpis.py`
- `python -m pytest credit-coach/tests/test_portfolio_validation.py credit-coach/tests/test_batch_candidate_diversity.py`

## Notes
- Coverage now answers four different questions: can the engine produce anything, can it rank it, can it trust it, and can product surfaces show it without manual cleanup.
- Reality-gap remains audit-first and non-blocking at this layer; it informs product-readiness rather than acting as a hidden gate.

---
*Phase: 17-full-portfolio-evaluation-coverage-audit*
*Completed: 2026-03-18*
