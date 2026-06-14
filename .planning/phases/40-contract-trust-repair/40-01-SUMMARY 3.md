---
phase: 40-contract-trust-repair
plan: 01
subsystem: raw-contract-normalization
tags: [engine, contract, roadmap, schema, pytest]
requires: []
provides:
  - null-free raw roadmap summary contract
  - bridge-safe external and internal decision fields
  - derived contract-health view from canonical summary truth
affects: [phase-40, trust, raw-artifacts, summary-contract]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/data/schema.py
    - credit-coach/src/credit_coach/cli/run_recourse.py
    - credit-coach/tests/test_recourse_redesign.py
key-decisions:
  - "Raw roadmap `summary` is now the single source of truth for decision-carrying contract fields."
  - "Missing approval or realization probabilities are normalized with contract-safe fallbacks instead of serializing null."
  - "Checkpoint status gaps fall back to `unknown` and become explicit contract-health signals."
patterns-established:
  - "Raw artifact generation now passes through one normalization seam before write."
requirements-completed: [TRST-01]
duration: manual-execution
completed: 2026-03-23
---

# Phase 40 Plan 01 Summary

**Raw customer artifacts now normalize through one deterministic contract seam before they are written.**

## Accomplishments

- Added bridge-safe roadmap vocabulary in schema, including `unknown` checkpoint status compatibility for repaired raw artifacts.
- Introduced one shared normalization helper inside `run_recourse.py` that fills decision-safe defaults, computes `zero_step_flag`, tracks contract-health counts, and derives `contract_health` from canonical `summary`.
- Made raw summary fields null-free for the locked probabilities: `plan_execution_probability`, `approval_dependent_plan_probability`, `offer_acceptance_probability`, and `combined_plan_realization_probability`.
- Added raw summary and bundle regression coverage for missing-field fallback behavior and zero-step rejection behavior.

## Verification

- `python -m pytest credit-coach/tests/test_recourse_redesign.py -q`

## Notes

- This plan establishes trust-safe raw serialization only. Final deterministic decision ownership still belongs to Phase `40.5`.

---
*Phase: 40-contract-trust-repair*
*Completed: 2026-03-23*
