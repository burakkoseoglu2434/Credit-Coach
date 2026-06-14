# Phase 69: Evidence Amplification — Research

**Researched:** 2026-04-11  
**Purpose:** capture the minimum operational knowledge needed to plan a recoverable-heavy cohort rerun + (optional) synthetic realized-outcome artifacts without changing shipped runtime logic.

## Goal Translation (What Phase 69 actually needs)

Phase 69 is an evidence-amplification pass over the shipped runtime. The only lever is **cohort selection**.

Locked constraints:
- no model / `tau_0` / planner / recourse / ranking changes
- no new action types
- reporting must be descriptive and non-causal

## Canonical Source Population (Phase 68)

Canonical real cohort run (full available denied under shipped runtime, `full_processed`, `n=367`):
- `credit-coach/artifacts/evaluations/v25_real_cohort_eval_20260411_full_processed_all_denied_n367_seed42`

Key artifact for selection:
- `customer_level_analysis.csv` includes runtime-first fields needed for deterministic selection:
  - `threshold_reach_possible` (runtime-derived via recoverability signal)
  - `approval_gap`
  - stable source identifiers: `source_customer_id`, `source_split`, `source_row_index`

## Cohort Runner (Existing evaluation pipeline to reuse)

Module:
- `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py`

Current limitation (relevant to Phase 69):
- The runner always forms a denied population from `full_processed`, assigns gap-tertile cohorts, then **samples** `n_customers` (with replacement when needed).
- Phase 69 needs: **no sampling** + **explicit cohort manifest** (use all eligible customers).

Minimum implementation seam needed for Phase 69 (evaluation-only; does not change runtime logic):
- Add a CLI option to run the runner over an **explicit list of `source_customer_id`** (or a manifest CSV containing `source_customer_id`), bypassing the sampling path.
- Ensure the runner still emits the same artifact family:
  - `customer_level_analysis.csv`
  - `cohort_metrics.json`
  - `cohort_evaluation_report.md`
  - (and optional: `cohort_sample.csv` should become the manifest echo + metadata)

Selection reproducibility:
- Because `_load_population(...)` assigns stable IDs (`train_000123`, `test_000456`) based on row index, a manifest of `source_customer_id` is sufficient to re-materialize the cohort from `full_processed` deterministically.

## Recoverability signals (for the secondary approval-gap constraint)

Module:
- `credit-coach/src/credit_coach/evaluation/recoverability.py`

Relevant constants and fields:
- `compute_approval_gap(base_pd, tau)`
- Default band thresholds:
  - `DEFAULT_NEAR_UPPER = 0.10`
  - `DEFAULT_MID_UPPER = 0.25`

Phase 69 “lowest approval-gap segment” should be implemented as a deterministic cutoff:
- prefer `approval_gap <= near_upper`
- if too few customers, relax to `approval_gap <= mid_upper`
- record the exact cutoff and counts in `selection_summary.json`

## Outcome realization artifacts (existing runner to reuse)

Module:
- `credit-coach/src/credit_coach/cli/run_outcome_feedback.py`

Inputs (optional CSVs):
- `--outcomes_csv` (upsert into DB)
- `--action_events_csv` (append-only into DB)

Outputs:
- under `credit-coach/artifacts/runs/<run_id>/tables/`:
  - `outcome_realization_summary.json`
  - `outcome_realization_evaluation.json`
  - `outcome_realization_report.md`

How to support Phase 69 “synthetic” realized-outcome artifacts without changing runtime logic:
- generate deterministic, explicitly labeled synthetic CSV inputs that populate:
  - `DecisionOutcomeRecord` fields (decision-level observed outcomes)
  - optionally `DecisionActionExecutionEventRecord` fields (action execution events)
- run `run_outcome_feedback.py` against an **isolated** SQLite DB (`DB_URL=sqlite:///...`) to avoid contaminating any existing state.

Determinism note:
- The outcome-feedback runner’s `run_id` is timestamp/nonce based. Evidence reproducibility can still be achieved by:
  - recording the generated run directory path and the synthetic input CSV hashes in a Phase 69 summary
  - (optional improvement) adding `--output_dir` / `--run_id` overrides to the runner for deterministic artifact placement (evaluation-only change).

## Evidence comparison (Phase 69 vs Phase 68)

Existing pack generator:
- `credit-coach/src/credit_coach/cli/run_v25_evidence_pack.py` builds Phase 68-style evidence pack docs from a `cohort_metrics.json` (+ optional outcome tables dir) with non-causal language guards.

Phase 69 needs:
- a Phase 69 evidence pack (same structure as Phase 68) for the new cohort
- a concise descriptive comparison section vs Phase 68 canonical cohort using like-for-like metrics already emitted by `cohort_metrics.json`

## Validation Architecture (tests to use as guardrails)

Recommended minimal pytest slice during Phase 69 development:
- `cd credit-coach && PYTHONPATH=src python -m pytest tests/test_cohort_evaluation.py -q`
- `cd credit-coach && PYTHONPATH=src python -m pytest tests/test_outcome_feedback.py -q` (if synthetic outcome ingestion touches runner inputs or report wiring)

---

## RESEARCH COMPLETE

