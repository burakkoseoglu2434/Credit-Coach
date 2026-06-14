# Phase 69 Evidence Pack — Cohort Report

This report is descriptive and does not make cause-and-effect claims.

## Dataset Limitation

- Phase 68 canonical denied population under shipped runtime (`full_processed`): 367
- Phase 69 cohort is a filtered subset of that denied population (selection is deterministic and auditable).
- Phase 69 cohort size (all eligible): 9

## Cohort Selection (Deterministic)

- Canonical Phase 68 cohort dir: `/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/artifacts/evaluations/v25_real_cohort_eval_20260411_full_processed_all_denied_n367_seed42`
- Selection summary: `/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/artifacts/evaluations/v25_phase69_recoverable_heavy_eval_20260411_full_processed_thr_reach_low_gap_all_seed42/selection_summary.json`
- Manifest: `/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/artifacts/evaluations/v25_phase69_recoverable_heavy_eval_20260411_full_processed_thr_reach_low_gap_all_seed42/selected_customer_ids.csv`
- Manifest SHA256: `3bcf19445f457eb568186bff0d79b8a931091f94bcbeb82473c67842fab44ed8`

- Primary filter: threshold_reach_possible == true
- Secondary filter: approval_gap cutoff (lowest-gap segment)
- Cutoff used: mid_upper_relaxed = 0.25
- Eligible primary n: 9
- Eligible secondary n: 9

## Capability Evidence (Phase 69 Cohort Metrics)

- Phase 69 cohort metrics: `/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/artifacts/evaluations/v25_phase69_recoverable_heavy_eval_20260411_full_processed_thr_reach_low_gap_all_seed42/cohort_metrics.json`
- movement_rate (global_denied): 33.3%
- strong_movement_rate (global_denied): 33.3%
- threshold_reach_possible_rate (global_denied): 88.9%
- threshold_reach_priority_rate (global_denied): 33.3%
- recoverable_customer_rate (global_denied): 33.3%
- selected_path_movement_strength_distribution (global_denied): `{"strong": 1.0}`

## Trust Evidence

- Trust counters (Phase 69 cohort overall):
  - selected_invalid_winner_count: 0
  - selected_surface_drift_count: 0
  - operator_packet_contradiction_count: 0

## Realized-Outcome Evidence (Additive)

- This section is descriptive and does not make cause-and-effect claims.
- If the provided outcome tables are synthetic, they are labeled synthetic and must not be treated as observed outcomes.
- Outcome tables dir: `/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/artifacts/evaluations/v25_phase69_recoverable_heavy_eval_20260411_full_processed_thr_reach_low_gap_all_seed42/synthetic_outcome_feedback_run/tables`
- Decisions observed: 9
- Observation coverage: 100.0%
- Realized movement rate: 33.3%
- Threshold-reaching realization rate: 33.3%
- Evidence status: sufficient

## Classification Rubric (Deterministic, Descriptive)

- `inconclusive` if any trust counter is non-zero or if required artifacts are missing.
- `weak evidence` if trust-clean but Phase 69 cohort size < 50 (insufficient population for stable conclusions).
- `strong evidence` requires (all): trust-clean, Phase 69 cohort size ≥ 50, and conservative lower-bounds for both movement-rate and strong-movement-rate deltas vs Phase 68 baseline are > 0 (descriptive concentration evidence only).

- Phase 69 cohort size: 9
- Trust-clean: True
- Movement rate delta vs Phase 68 baseline (point): 0.3224
- Movement rate delta bounds (conservative): [0.0929, 0.6416]
- Strong movement rate delta vs Phase 68 baseline (point): 0.3224
- Strong movement rate delta bounds (conservative): [0.0929, 0.6416]

## Result

- Classification: **weak evidence**
