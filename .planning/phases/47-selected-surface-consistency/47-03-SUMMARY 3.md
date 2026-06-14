---
phase: 47-selected-surface-consistency
plan: 03
subsystem: rerun-proof-and-drift-closure
tags: [selected-surface, rerun, regression, verification, artifacts]
requires: [47-01, 47-02]
provides:
  - regression closure for selected-surface drift
  - three-cohort rerun proof for selected-surface consistency
  - collection-summary visibility for selected overlay metrics
affects: [phase-47, tests, collection-summary, rerun-evidence]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py
    - credit-coach/tests/test_phase_experiment_suite.py
key-decisions:
  - "Selected-surface acceptance is proven on the same large-sample collection surfaces used for milestone evaluation."
  - "Rerun proof reads both consumer decision overlay and shared recommendation projection alignment."
patterns-established:
  - "Collection summaries and manifests now expose selected-surface proof fields beside winner-integrity and DICE metrics."
requirements-completed: [CONS-01, CONS-02, CONS-03]
duration: manual-execution
completed: 2026-04-01
---

# Phase 47 Plan 03 Summary

**Phase 47 now has both automated regression proof and three-cohort rerun evidence for selected-surface consistency.**

## Accomplishments

- Verified selected overlay and shared recommendation projection with dedicated and existing regression suites.
- Extended collection summary and manifest outputs with selected-surface evidence:
  - `selected_decision_status_mismatch_count`
  - `selected_empty_state_count`
  - `mean_selected_action_count`
  - `selected_recommendation_projection_versions`
- Ran three deterministic 250-customer reruns:
  - `pilot_mixed`
  - `risk_band_balanced`
  - `offer_needed_balanced`
- Confirmed from `customer_metrics.csv` and `customer_plans.csv` that:
  - selected decision mismatch count is `0`
  - operator selected recommendation text mismatch count is `0`
  - empty-state fake recommendation count is `0`
  - no-valid contract violation count is `0`
  - selected best rows under `no_valid_winner` is `0`

## Verification

- `python -m pytest credit-coach/tests/test_selected_surface_consistency.py credit-coach/tests/test_recourse_redesign.py credit-coach/tests/test_customer_artifact_collection.py credit-coach/tests/test_operator_review_pack.py credit-coach/tests/test_decision_explanation_pack.py credit-coach/tests/test_phase_experiment_suite.py -q`
- `cd credit-coach && MPLCONFIGDIR=/tmp/mpl PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy pilot_mixed`
- `cd credit-coach && MPLCONFIGDIR=/tmp/mpl PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy risk_band_balanced`
- `cd credit-coach && MPLCONFIGDIR=/tmp/mpl PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy offer_needed_balanced`

## Notes

- The three large-sample reruns produced `0` `no_valid_winner` customers, so empty-state cohort proof is vacuously clean there; explicit empty-state behavior is covered by automated regression tests.
- Reruns emitted pandas `FutureWarning` messages about concatenating empty/all-NA frames in collection assembly. These did not block Phase 47 acceptance.

---
*Phase: 47-selected-surface-consistency*
*Completed: 2026-04-01*
