# Phase 70: Lending Club Full Dataset Validation - Context

**Gathered:** 2026-04-11  
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 70 validates the **full end-to-end system** on the complete Lending Club dataset (**~1.3M rows**) using the **same locked 48-feature schema**, without changing any:
- model bundle / weights / calibration
- `tau_0` or any threshold policy
- planner / recourse / ranking logic
- action semantics

This phase owns:
- preparing the full dataset into parquet (`train.parquet` / `test.parquet`) under a **separate processed-data root** to avoid accidental destructive overwrites
- schema compatibility validation (48 features; no feature additions/removals)
- controlled cohort evaluations at increasing scale (n≈100–500 → 1k–5k → large/full stress runs)
- descriptive comparisons vs Phase 68 / Phase 69 artifacts (non-causal)
- a Phase 70 descriptive report that classifies evidence strength as `strong / weak / inconclusive`

This phase does not own:
- any optimization work (no tuning, no parameter changes)
- any causal attribution, uplift, or business-impact claims

</domain>

<decisions>
## Implementation Decisions

### Dataset feature lock (locked)
- Use `credit-coach/configs/features_48.yaml` as the single source of truth for the 48-feature contract.
- Any missing required column in the raw CSV is a **hard stop** (compatibility failure).
- Extra columns in the raw CSV may be dropped, but must be reported (descriptive only).

### Full dataset location (locked, user-provided)
- The full Lending Club CSV is expected to be provided locally (not committed to git).
- Phase 70 will reference it via `paths.raw_csv` in a dedicated base config (see plan).

### Processed data output location (locked: non-destructive)
- Do **not** overwrite `credit-coach/data/processed/` (the small n≈1600 processed dataset).
- Write Phase 70 outputs to:
  - `credit-coach/data/processed_lendingclub_full/`
  - `credit-coach/data/splits_lendingclub_full/`

### Evaluation runner (locked)
- Use the shipped cohort runner:
  - `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py`
- Only configuration and orchestration are allowed; no behavioral changes.

### Scale protocol (locked)
- Run at increasing `--n_customers` sizes using the full dataset as the population:
  - Wave 1: `n=100–500` (smoke)
  - Wave 2: `n=1,000–5,000` (medium)
  - Wave 3: large/full stress (`n>=20,000` as feasible), plus descriptive comparison vs Phase 68/69
- If any run uses sampling with replacement, it must be recorded and interpreted conservatively.

### Reporting (locked)
- Reporting is descriptive and non-causal.
- Evidence strength classification must be tied to:
  - trust-clean gating (`selected_invalid_winner_count`, `selected_surface_drift_count`, `operator_packet_contradiction_count`)
  - cohort size sufficiency
  - metric stability across scale increases (no “wins” cherry-picked)

</decisions>

<specifics>
## Specifics and Assumptions (to be confirmed/encoded in plan)

- The full dataset CSV uses the same column names as the 48-feature contract and includes the expected target column.
- Disk + memory budget is sufficient for parquet conversion and cohort evaluations.
- Phase 68/69 comparison anchors:
  - Phase 68 canonical run dir: `credit-coach/artifacts/evaluations/v25_real_cohort_eval_20260411_full_processed_all_denied_n367_seed42`
  - Phase 69 run dir: `credit-coach/artifacts/evaluations/v25_phase69_recoverable_heavy_eval_20260411_full_processed_thr_reach_low_gap_all_seed42`

</specifics>

<code_context>
## Existing Code Insights

- Data prep CLI: `credit-coach/src/credit_coach/cli/run_prepare_data.py`
  - uses `features_48.yaml` via feature contract (schema lock)
  - writes parquet train/test to `paths.processed_data`
- Cohort evaluation CLI: `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py`
  - reads parquet from `paths.processed_data`
  - supports `--n_customers` and `--sample_seed`
  - emits:
    - `customer_level_analysis.csv`
    - `cohort_metrics.json`
    - `cohort_evaluation_report.md`

</code_context>

<deferred>
## Deferred Ideas (explicitly out of Phase 70 scope)

- Any model retraining, recalibration, or threshold policy iteration
- Any planner / recourse / ranking modifications
- Any feature engineering beyond minimal compatibility fixes required to ingest the dataset under the existing 48-feature contract
- Any causal study design or business uplift claims

</deferred>

---

*Phase: 70-lendingclub-full-dataset-validation*  
*Context gathered: 2026-04-11*

