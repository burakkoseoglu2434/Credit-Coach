# Phase 68: Real Cohort Evidence Run - Context

**Gathered:** 2026-04-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 68 converts the **v2.5 audit-passed capability** into **evidence-backed product proof** by running a large denied-cohort evaluation (≥500 denied customers), integrating Phase 67 realized-outcome artifacts (when available), and publishing an evidence-grade report + investor-ready executive summary.

This phase owns:
- running a **large denied cohort** on `full_processed` data with reproducible seeds and recorded sampling metadata
- extracting and reporting the three required metrics (global + targeted where applicable):
  - `recoverable_rate`
  - `movement_rate` (recoverable/full vs global denied)
  - `threshold_reach_possible_rate`
- integrating Phase 67 realized outcomes (observed execution/realization) into the evidence narrative **without causal claims**
- producing two human-readable deliverables:
  - evidence-grade cohort report (technical but readable, audit-friendly)
  - investor-ready summary (one-page, non-technical, conservative)
- producing a final decision: **evidence strong** vs **evidence weak**

This phase does not own:
- changes to planner, thresholds, recoverability classifier, recourse gating, or narrative contracts (v2.5 runtime must remain unchanged)
- any new action types or action-surface expansion
- causal attribution or business-uplift claims (observational evidence only unless a future randomized design exists)

</domain>

<decisions>
## Implementation Decisions

### 1) “Real cohort” definition and sampling truth

Phase 68 defines “real cohort” as:
- `dataset_scope=full_processed` (uses `credit-coach/data/processed/train.parquet` + `test.parquet`)
- `n_customers >= 500` denied customers sampled via the cohort runner
- sampling metadata must be recorded and reported:
  - `unique_denied_available`
  - `realized_sample_n`
  - `with_replacement` vs `without_replacement`

Locked decision (evidence grade):
- If `with_replacement=true`, the run is still valid as a **stress test**, but the evidence is classified **weak** unless a subsequent `without_replacement` run reaches ≥500 unique denied customers.

### 2) Required metrics (must be explicitly reported)

Phase 68 must report (at minimum):
- `recoverable_customer_rate` (recoverable rate in denied cohort)
- `movement_rate_global` vs `movement_rate_recoverable_full_mode` (or equivalent targeted comparison output)
- `threshold_reach_possible_rate` (global denied)

These metrics must be sourced from **engine-owned cohort artifacts** (no ad-hoc recomputation).

### 3) Phase 67 realized-outcome integration (descriptive only)

Phase 68 must integrate Phase 67 realized outcomes via the existing outcome-feedback runner outputs:
- `outcome_realization_summary.json`
- `outcome_realization_evaluation.json`
- `outcome_realization_report.md`

Locked decision:
- Realized outcomes are treated as **descriptive observation** and **calibration-style** evidence only.
- The report must explicitly separate:
  1) **movement concentration** (model/runtime capability) and
  2) **realized execution/outcomes** (observed follow-through / outcome signals)

If realized-outcome data is sparse or missing, this must be explicitly called out and should bias the final decision toward **evidence weak**.

### 4) No causal claims / wording guardrails

The evidence report and investor summary must not use causal language unless a future experimental design exists.

Banned/avoid phrases in Phase 68 deliverables:
- “caused”, “causal”, “uplift”, “increases approvals”, “proves”, “guarantees”

Allowed phrasing:
- “concentrates movement potential”
- “observed association”
- “descriptive evidence”
- “predicted vs observed gap (non-causal)”

### 5) Evidence strength decision rubric (strong vs weak)

Phase 68 outputs one explicit decision with deterministic criteria:

**Evidence strong** requires:
- denied cohort size: `realized_sample_n >= 500`
- sampling: `with_replacement=false` (≥500 unique denied customers available)
- recoverable/full sample size: `recoverable_full_mode.sample_size >= 50` (or explicit recoverable full-mode count)
- movement concentration: `movement_rate_recoverable_full_mode > movement_rate_global_denied` with a reported uncertainty bound (CI) that does not cross 0
- realized outcomes: Phase 67 evaluation artifacts exist and report non-zero observation coverage with explicit sparse-evidence posture

Otherwise: **evidence weak** (still useful, but not investor-grade proof of product impact).

### Claude's Discretion
- Choice of statistical interval method (e.g., Wilson interval for proportions) as long as it is conservative and clearly labeled “non-causal”.
- Whether to run one seed or multiple seeds; if multiple, pick ≤3 seeds and report stability/variance.
- Exact report formatting, as long as it is audit-friendly and the separation of capability vs outcomes remains explicit.

</decisions>

<specifics>
## Specific Ideas

- Use the existing cohort runner (`run_v24_cohort_evaluation`) as the single source of truth for movement and recoverability metrics.
- Generate a deterministic “evidence pack” that points to the raw artifact folders and summarizes only aggregated metrics + uncertainty bounds.
- Treat Phase 67 realized outcomes as a “coverage and calibration” appendix unless observation coverage is meaningfully high.

</specifics>

<code_context>
## Existing Code Insights

- Cohort runner: `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py`
  - supports `--dataset_scope full_processed` and `--n_customers 500`
  - publishes `cohort_metrics.json` and `cohort_evaluation_report.md`
  - includes sampling metadata (`unique_denied_available`, `with_replacement`)

- Outcome feedback runner (Phase 67): `credit-coach/src/credit_coach/cli/run_outcome_feedback.py`
  - publishes `outcome_realization_summary.json`, `outcome_realization_evaluation.json`, and `outcome_realization_report.md` under `artifacts/runs/*/tables/`
  - enforces non-causal guardrails inside the generated report text

</code_context>

<deferred>
## Deferred Ideas

- Any claim of business lift (requires a causal design and/or institutional approval outcome linkage beyond current scope).
- Any new data source integration beyond the shipped processed dataset and optional outcomes/action-events CSVs.

</deferred>

---

*Phase: 68-real-cohort-evidence-run*
*Context gathered: 2026-04-11*

