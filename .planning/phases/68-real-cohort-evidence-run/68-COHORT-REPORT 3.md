# Phase 68 Evidence Pack — Cohort Report

## Source Artifacts

- Cohort dir: /Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/artifacts/evaluations/v25_real_cohort_eval_20260411_full_processed_all_denied_n367_seed42
- Cohort metrics: /Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/artifacts/evaluations/v25_real_cohort_eval_20260411_full_processed_all_denied_n367_seed42/cohort_metrics.json
- Outcome tables dir: /Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/artifacts/runs/20260411_184556_2fe5e6_86f8a1/tables

## Dataset Limitation

- Canonical denied cohort size under shipped runtime on `full_processed`: 367 (full available denied population)
- Unique denied available: 367
- Sampling mode: without_replacement

## Descriptive Guardrails

- This pack summarizes observed artifact outputs from the shipped runtime and does not make cause-and-effect claims.
- Differences between slices are descriptive comparisons only; they do not establish downstream business outcomes.
- Sparse or missing observations must be treated as incomplete evidence rather than success or failure.

## Capability Evidence (Cohort Runner Outputs)

- global_denied sample_size: 367
- recoverable_full_mode sample_size: 4
- non_recoverable_limited_mode sample_size: 363

### Headline Rates

- Recoverable customer rate (denied cohort): 1.1%
- Threshold reach possible rate (denied cohort): 2.5%

### Targeted Slice Comparison (Recoverable Full vs Global Denied)

- Movement rate (global): 1.1% (k=4, n=367; Wilson 0.4%..2.8%)
- Movement rate (recoverable/full): 100.0% (k=4, n=4; Wilson 51.0%..100.0%)
- Movement delta (recoverable/full - global): 98.9% (conservative 48.2%..99.6%)

- Strong movement rate (global): 1.1% (k=4, n=367; Wilson 0.4%..2.8%)
- Strong movement rate (recoverable/full): 100.0% (k=4, n=4; Wilson 51.0%..100.0%)
- Strong movement delta (recoverable/full - global): 98.9% (conservative 48.2%..99.6%)

## Trust Evidence

- Trust counters (cohort overall):
  - selected_invalid_winner_count: 0
  - selected_surface_drift_count: 0
  - operator_packet_contradiction_count: 0

## Realized-Outcome Evidence (Outcome Feedback Layer)

- Window days: 90
- Decisions: 367
- Observed decisions: 28
- Observation coverage: 7.6%
- Evidence status: sparse

- Artifact paths:
  - outcome_realization_evaluation_json: /Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/artifacts/runs/20260411_184556_2fe5e6_86f8a1/tables/outcome_realization_evaluation.json
  - outcome_realization_report_md: /Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/artifacts/runs/20260411_184556_2fe5e6_86f8a1/tables/outcome_realization_report.md
  - outcome_realization_summary_json: /Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/artifacts/runs/20260411_184556_2fe5e6_86f8a1/tables/outcome_realization_summary.json
  - path_realization_summary_json: /Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/artifacts/runs/20260411_184556_2fe5e6_86f8a1/tables/path_realization_summary.json
  - action_execution_events_csv: /Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/artifacts/runs/20260411_184556_2fe5e6_86f8a1/tables/action_execution_events.csv

## Limitations

- The canonical denied cohort reflects the full available denied population under the shipped runtime on the provided `full_processed` dataset; it is not an expanded population run.
- Recoverable/full slice size is small in this cohort; uncertainty bounds reflect that.
- Realized-outcome observation coverage may be sparse; treat realized metrics as descriptive evidence only.

## Recommendation (Next Work)

- Expand `full_processed` denied coverage to increase evidence strength under the shipped runtime (aim for a larger denied cohort without replacement).
- Increase recoverable/full representation (or explicitly collect a recoverable-heavy denied cohort) to support stable comparisons.
- Ingest real action execution events and delayed outcome signals for the cohort to improve observation coverage.
