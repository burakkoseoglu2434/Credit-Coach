---
phase: 09-kpi-contract-unification
plan: 02
subsystem: provenance
tags: [frozen-model, suite, challenger, registry, pytest]
requires: [09-01]
provides:
  - explicit model manifest resolution and fail-closed loading
  - frozen model provenance carried through seeded suite and batch runs
  - variant-scoped frozen model reuse across challenger seeds
affects: [phase-09, suite, challenger, batch-eval, registry]
tech-stack:
  added: []
  patterns: [resolved manifest handoff, variant-level freeze, fail-closed provenance]
key-files:
  created: []
  modified: [credit-coach/src/credit_coach/model/registry.py, credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py, credit-coach/src/credit_coach/cli/run_recourse.py, credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py, credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py]
key-decisions:
  - "Explicit model selectors resolve into one manifest contract and fail closed on missing or inconsistent snapshots."
  - "Seeded suite and challenger runs now reuse a frozen manifest instead of chasing `latest.json` during repeated evidence collection."
patterns-established:
  - "Runners should pass `--model_manifest` once a snapshot is resolved so downstream comparisons stay like-for-like."
requirements-completed: [KPI-02]
duration: manual-execution
completed: 2026-03-14
---

# Phase 9 Plan 02 Summary

**Frozen-model provenance is now explicit, fail-closed, and reused consistently across repeated seeded suite and challenger runs.**

## Accomplishments
- Added resolved-manifest helpers in `credit_coach.model.registry` so callers can load by model version or manifest path without silently depending on `latest.json`.
- Wired batch and recourse CLIs to record requested versus resolved model provenance and emit frozen-model metadata in run manifests.
- Refactored phase suite and challenger orchestration to freeze one model artifact, pass its manifest into every seeded batch run, and export frozen-model evidence for later acceptance logic.

## Verification
- `python -m pytest credit-coach/tests/test_phase_experiment_suite.py`
- `python -m pytest credit-coach/tests/test_challenger_matrix_selection.py credit-coach/tests/test_production_smoke.py`

## Notes
- Explicit selectors remain fail-closed; implicit latest-model reuse is still available only when no explicit freeze was requested.

---
*Phase: 09-kpi-contract-unification*
*Completed: 2026-03-14*
