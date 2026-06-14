# Phase 68: Real Cohort Evidence Run — Research

**Researched:** 2026-04-11
**Purpose:** capture the minimum operational + statistical knowledge needed to plan an evidence-grade cohort run without changing runtime behavior.

## Existing Runners (Source of Truth)

### 1) Cohort evaluation runner (movement + targeting evidence)

Module: `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py`

Key parameters:
- `--dataset_scope`: `full_processed` (default) or `test_only`
- `--n_customers`: requested cohort size (default `500`)
- `--sample_seed`: deterministic sampling seed (default `42`)
- `--output_dir`: explicit output folder (recommended for evidence runs)

Key outputs (in `output_dir`):
- `cohort_metrics.json` (machine-readable)
- `cohort_evaluation_report.md` (human-readable)
- `customer_level_analysis.csv` (row-level diagnostics)
- `cohort_sample.csv` (sampled customer IDs + cohort labels + sampling meta)

Sampling behavior to report:
- If `unique_denied_available < n_customers`, sampling uses replacement at the cohort-slice level and records:
  - `with_replacement: true`
  - `reused_draw_count` and `unique_source_customers_in_sample`

Phase 68 implication:
- A ≥500 run can be executed even with replacement, but “evidence strong” should prefer `with_replacement=false`.

### 2) Outcome feedback runner (Phase 67 realized outcomes)

Module: `credit-coach/src/credit_coach/cli/run_outcome_feedback.py`

Key parameters:
- `--outcomes_csv` (optional upsert)
- `--action_events_csv` (optional append-only)
- `--window_days` (default `90`)

Key outputs (under `artifacts/runs/<run_id>/tables/`):
- `outcome_realization_summary.json`
- `outcome_realization_evaluation.json`
- `outcome_realization_report.md`

Phase 68 implication:
- Realized outcomes can be integrated even when sparse; the runner itself prints guardrails and avoids causal claims.

## Statistical Framing (Non-Causal)

Phase 68 needs to enforce two boundaries:
1) **Statistical support is not causality.** Even a “significant” delta is observational unless there is randomization or a credible causal design.
2) The strongest permissible claim is concentration/association (e.g., “recoverable cohort shows higher movement selection density than global denied in this dataset/run”).

Recommended reporting primitives (conservative):
- difference in proportions (movement rate recoverable/full minus global)
- 95% confidence interval for the delta (method documented)
- sample sizes for both populations and the sampling mode (with/without replacement)

## Report Construction Strategy

To avoid manual transcription:
- build a small evidence-pack step that reads:
  - `cohort_metrics.json` (from cohort runner)
  - `outcome_realization_evaluation.json` (from outcome runner, if present)
- writes:
  - evidence-grade report (audit-friendly, explicit limitations)
  - investor-ready summary (one-page, conservative)
  - explicit decision: evidence strong / weak (deterministic rubric)

## Validation Architecture

Use tests as guardrails (no runtime changes expected in Phase 68):
- `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py tests/test_outcome_feedback.py -q`

Plus a lightweight “language guard” check on generated markdown outputs:
- ensure banned causal/uplift phrases are absent
- ensure required guardrail section exists

---

## RESEARCH COMPLETE

