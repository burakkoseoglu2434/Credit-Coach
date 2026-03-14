---
phase: 09-kpi-contract-unification
plan: 03
subsystem: acceptance
tags: [acceptance, smoke, challenger, suite, pytest]
requires: [09-01, 09-02]
provides:
  - canonical runner-level KPI contract snapshots
  - milestone acceptance summaries derived from repeated seeded evidence
  - smoke and challenger semantics aligned to acceptance eligibility
affects: [phase-09, acceptance, smoke, suite, challenger]
tech-stack:
  added: []
  patterns: [canonical json contract, derived review markdown, degraded evidence gating]
key-files:
  created: []
  modified: [credit-coach/src/credit_coach/ops/kpi_contract.py, credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py, credit-coach/src/credit_coach/cli/run_production_smoke.py, credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py, credit-coach/tests/test_phase_experiment_suite.py, credit-coach/tests/test_production_smoke.py, credit-coach/tests/test_challenger_matrix_selection.py, credit-coach/tests/test_release_decision.py]
key-decisions:
  - "Repeated seeded evidence is now the canonical acceptance source; single-run smoke fallback remains operational only."
  - "Human-readable milestone review is derived from `milestone_acceptance_summary.json` rather than bespoke markdown state."
patterns-established:
  - "Runner-level `kpi_contract_snapshot.json` is the machine-readable source of truth for smoke, suite, and challenger outputs."
requirements-completed: [KPI-03, KPI-01, KPI-02]
duration: manual-execution
completed: 2026-03-14
---

# Phase 9 Plan 03 Summary

**Milestone acceptance is now grounded in repeated seeded evidence, and smoke, suite, and challenger all emit or consume the same contract-shaped KPI semantics.**

## Accomplishments
- Added canonical contract and acceptance helpers in `credit_coach.ops.kpi_contract` for runner snapshots, acceptance summaries, and derived review markdown.
- Extended the phase suite to emit `kpi_contract_snapshot.json`, `milestone_acceptance_summary.json`, and `milestone_acceptance_review.md` from seeded evidence and frozen-model provenance.
- Updated smoke and challenger flows to expose degraded evidence, acceptance eligibility, and promotion constraints instead of treating one passing run as acceptance-grade truth.

## Verification
- `python -m pytest credit-coach/tests/test_phase_experiment_suite.py credit-coach/tests/test_release_decision.py`
- `python -m pytest credit-coach/tests/test_production_smoke.py credit-coach/tests/test_challenger_matrix_selection.py`

## Notes
- Single-run fallback still computes a release decision for operational smoke feedback, but now always marks `acceptance_eligible = false` and `broad_rollout_allowed = false`.

---
*Phase: 09-kpi-contract-unification*
*Completed: 2026-03-14*
