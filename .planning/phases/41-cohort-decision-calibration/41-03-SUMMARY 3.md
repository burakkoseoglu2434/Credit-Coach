---
phase: 41-cohort-decision-calibration
plan: 03
subsystem: collection-packaging-and-calibration-review
tags: [engine, artifacts, summary, pytest]
requires: [01, 02]
provides:
  - calibration subtree inside the collection run root
  - calibration-aware manifest and summary outputs
  - backward-compatible packaging for raw, flat, and calibration artifacts
affects: [phase-41, collection-packaging, manifest, summary]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py
    - credit-coach/tests/test_customer_artifact_collection.py
    - credit-coach/tests/test_phase_experiment_suite.py
key-decisions:
  - "Calibration artifacts live under the same collection run root as raw and flat artifacts."
  - "Manifest and summary grow additively while keeping the existing inspection contract intact."
  - "Calibration outputs are clearly read-only measurement artifacts and never decision-truth owners."
patterns-established:
  - "One run ID can now support raw inspection, flat review, funnel review, and shadow calibration together."
requirements-completed: [CAL-01, CAL-02]
duration: manual-execution
completed: 2026-03-23
---

# Phase 41 Plan 03 Summary

**A single collection run now packages raw inspection, flat review, and cohort calibration evidence together without breaking existing artifact consumers.**

## Accomplishments

- Added a `calibration/` subtree with funnel summary, readiness distribution, status-by-readiness, policy comparison, decision shift matrix, segment breakdown, and human-readable calibration review outputs.
- Expanded `collection_manifest.json` with cohort definition, selection semantics, policy versions, funnel summary, readiness summary, and calibration summary.
- Expanded `collection_summary.md` additively with Decision Funnel, Readiness, and Calibration sections while preserving existing inspection and contract-health sections.
- Added regression assertions so calibration packaging stays backward-compatible and clearly analysis-only.

## Verification

- `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py tests/test_phase_experiment_suite.py tests/test_portfolio_validation.py -q`

## Notes

- Phase `41` is now closed. Later phases can consume these collection-level calibration artifacts without redefining decision truth.

---
*Phase: 41-cohort-decision-calibration*
*Completed: 2026-03-23*
