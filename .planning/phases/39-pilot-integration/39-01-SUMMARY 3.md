---
phase: 39-pilot-integration
plan: 01
subsystem: pilot-contract-and-ingestion
tags: [pilot, contract, ingestion, batch, provenance]
requires: []
provides:
  - canonical pilot input contract
  - validated institution-style ingestion seam
  - engine-owned pilot data documentation
affects: [phase-39, pilot, batch, docs]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/pilot/contracts.py
    - credit-coach/src/credit_coach/pilot/io.py
    - credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py
    - credit-coach/src/credit_coach/cli/run_pilot_integration.py
    - credit-coach/tests/test_pilot_integration.py
    - credit-coach/docs/PILOT_DATA_CONTRACT.md
key-decisions:
  - "Pilot input stays export-first and fail-closed instead of pretending to be a live integration."
  - "Identity fallback is allowed only for canonical feature names already present in the export."
  - "The existing batch planning core remains the execution engine underneath pilot intake."
patterns-established:
  - "Validated institution bundles normalize into the same planning core rather than creating a second planner."
duration: manual-execution
completed: 2026-03-22
---

# Phase 39 Plan 01 Summary

**The repo now has one explicit answer to what institution-style pilot data must look like before personalized planning can run.**

## Accomplishments

- Added a canonical pilot input contract with:
  - institution metadata
  - source export definition
  - customer id, target, and group-feature mapping
  - fail-closed feature mapping validation
- Added normalization logic that turns institution exports into:
  - canonical engine features
  - target truth
  - preserved `customer_id`
  - canonical group feature
- Opened the minimum batch seam needed for pilot reuse:
  - external input file path
  - external input format
  - preserved upstream `customer_id`
- Published one engine-owned pilot data contract doc.

## Verification

- `python -m pytest credit-coach/tests/test_pilot_integration.py -q`

## Notes

- This plan locked the entry seam only; pilot guardrails, acceptance posture, and onboarding packaging were completed in the later Phase 39 plans.

---
*Phase: 39-pilot-integration*
*Completed: 2026-03-22*
