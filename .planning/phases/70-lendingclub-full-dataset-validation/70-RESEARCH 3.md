# Phase 70: Lending Club Full Dataset Validation — Research

**Researched:** 2026-04-11  
**Purpose:** capture the minimum operational knowledge needed to validate the shipped system on the full Lending Club dataset (≈1.3M rows) without changing model / thresholds / planner / recourse / ranking logic.

## What “full dataset validation” means operationally

Phase 70 changes only the **data scale and population** (full Lending Club CSV → parquet) and observes whether:
- ingestion + preprocessing still satisfy the 48-feature contract
- cohort evaluation still runs end-to-end at increasing `n_customers`
- trust counters remain clean
- metrics behave consistently (no hidden breakage) as scale increases

## Where the raw dataset comes from

`credit-coach/configs/default.yaml` references:
- `paths.raw_csv: data/lending club/lending_club_48_features_20251026_114053.csv`

In practice, the full CSV is too large for git, so Phase 70 should treat the CSV as **user-provided local data**:
- recommended: store outside the repo and point `paths.raw_csv` to the absolute path
- alternative: place under `credit-coach/data/` but ensure it is ignored (do not commit)

## Feature contract enforcement (schema compatibility)

Contract source:
- `credit-coach/configs/features_48.yaml` via `credit-coach/src/credit_coach/data/ingest.py`

Enforcement behavior:
- missing required columns → hard failure (expected in Phase 70 if CSV mismatches)
- extra columns may be dropped (descriptive reporting should note extras and final kept columns)

Phase 70 should log / capture:
- row count and column count at raw ingestion
- list of kept columns (48 + target)
- hash of raw CSV file (for reproducibility)

## CSV → parquet conversion path

Canonical CLI:
- `credit-coach/src/credit_coach/cli/run_prepare_data.py`

Important knobs:
- `prepare_data.sample_rows` controls sampling during ingestion; to process the full dataset it must be **null/omitted**.
- `paths.processed_data` and `paths.splits` can be pointed to phase-specific directories to avoid overwriting the small processed dataset.

Potential scaling failure modes:
- OOM during `pandas.read_csv` for full CSV
- slow conversion due to dtype inference

Phase 70 stance:
- do not prematurely optimize; attempt the canonical path first
- if conversion fails, treat chunked/streaming ingest as a **compatibility fix**, not a feature change

## Cohort evaluation at scale

Runner:
- `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py`

Scale protocol:
- increasing `--n_customers` (smoke → medium → large) using the full processed dataset as the population
- record sampling metadata from `cohort_metrics.json` (`with_replacement`, `unique_denied_available`, etc.)

Phase 70 metrics of interest (descriptive only)
- denied availability: `unique_denied_available` (from `cohort_metrics.json.sampling`)
- recoverable rate: `population_metrics.global_denied.recoverable_customer_rate`
- threshold reach possible: `population_metrics.global_denied.threshold_reach_possible_rate`
- counterfactual availability proxy:
  - `population_metrics.global_denied.multi_path_rate` and/or
  - `population_metrics.global_denied.avg_paths_per_customer` and/or
  - `population_metrics.global_denied.customers_with_any_movement_rate`

## Comparison anchors (Phase 68 / Phase 69)

Existing baseline artifacts:
- Phase 68 canonical cohort dir:
  - `credit-coach/artifacts/evaluations/v25_real_cohort_eval_20260411_full_processed_all_denied_n367_seed42`
- Phase 69 rerun dir:
  - `credit-coach/artifacts/evaluations/v25_phase69_recoverable_heavy_eval_20260411_full_processed_thr_reach_low_gap_all_seed42`

Comparison guidance:
- compare like-for-like fields from `cohort_metrics.json`
- emphasize dataset differences and sampling limitations
- avoid causal or uplift language

## Validation Architecture

Phase 70 validation is intentionally simple: the goal is to detect **breakage under scale** and keep trust checks clean, not to optimize.

**Primary gates (hard-stop):**
- Schema lock: `configs/features_48.yaml` contract holds (missing required columns → stop).
- Trust counters remain clean in `cohort_metrics.json`:
  - `selected_invalid_winner_count = 0`
  - `selected_surface_drift_count = 0`
  - `operator_packet_contradiction_count = 0`

**Scale ladder checks (interpretation-strength, not hard-stop):**
- As `n_customers` increases (smoke → medium → large):
  - sampling metadata remains interpretable (`with_replacement` is recorded)
  - key rates remain stable enough to summarize descriptively:
    - `threshold_reach_possible_rate`
    - `recoverable_customer_rate`
    - `avg_paths_per_customer`, `multi_path_rate`
    - movement proxies (`customers_with_any_movement_rate`, `customers_with_strong_movement_rate`)

**Non-causal reporting guardrail:**
- All Phase 70 written artifacts (especially `70-REPORT.md`) must avoid causal/uplift language and must state dataset + sampling limitations explicitly.

---

## RESEARCH COMPLETE
