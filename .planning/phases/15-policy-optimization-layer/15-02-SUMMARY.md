---
phase: 15-policy-optimization-layer
plan: 02
subsystem: recovery-aware-ranking
tags: [offer-acceptance, recovery-proxy, planner, batch-evidence, pytest]
requires: [15-01]
provides:
  - distinct `offer_acceptance_probability` and combined offer-plan realization semantics
  - governance-first recovery-aware planner ordering
  - canonical batch `offer_optimization_summary.json` and companion breakdown CSVs
affects: [phase-15, planner, batch-eval, repository]
tech-stack:
  added: []
  patterns: [governance-first recovery ranking, explicit proxy deltas, canonical offer evidence]
key-files:
  modified: [credit-coach/src/credit_coach/recourse/execution_probability.py, credit-coach/src/credit_coach/coaching/planner.py, credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py, credit-coach/src/credit_coach/storage/repository.py, credit-coach/tests/test_batch_candidate_diversity.py]
key-decisions:
  - "`offer_acceptance_probability` remains distinct from `plan_execution_probability`."
  - "`combined_plan_realization_probability` is only computed for rankable offer-bearing plans."
  - "`expected_recovery_proxy` can influence ordering only after inherited governance and short-term trajectory checks."
patterns-established:
  - "Batch evaluation is now the canonical owner of Phase 15 offer optimization evidence."
requirements-completed: [REC-08, REC-09]
duration: manual-execution
completed: 2026-03-16
---

# Phase 15 Plan 02 Summary

**Offer ranking is now recovery-aware without weakening the existing safety stack.**

## Accomplishments
- Separated offer acceptance from ordinary action execution and introduced `combined_plan_realization_probability` for rankable offer-bearing plans.
- Layered `expected_recovery_proxy` into planner ordering only below inherited fairness, reliability, telemetry, action-realism, and trajectory-health filters.
- Added canonical batch artifacts: `offer_optimization_summary.json`, `offer_type_breakdown.csv`, `offer_policy_arm_breakdown.csv`, `offer_acceptance_breakdown.csv`, and `offer_proxy_impact_breakdown.csv`.

## Verification
- `python -m pytest credit-coach/tests/test_planner_denied_objective.py credit-coach/tests/test_recourse_funnel_kpis.py credit-coach/tests/test_batch_candidate_diversity.py`

## Notes
- Review remains metric-by-metric: approval, default, and margin proxy deltas are still visible individually.
- Recovery upside does not override governance or trajectory regressions.

---
*Phase: 15-policy-optimization-layer*
*Completed: 2026-03-16*
