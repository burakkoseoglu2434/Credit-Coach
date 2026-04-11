# Phase 69: Evidence Amplification - Context

**Gathered:** 2026-04-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 69 constructs a **recoverable-heavy denied cohort** from the **full available denied population under the shipped runtime** and re-runs the **existing evaluation pipeline** (Phase 68-style) to test whether evidence becomes strong and stable **under the correct population**, without changing runtime logic.

This phase owns:
- cohort selection / filtering (recoverable-heavy denied cohort)
- re-running the existing cohort evaluation pipeline using the shipped runtime (model bundle + `tau_0` + planner + recourse unchanged)
- optional deterministic outcome simulation that is explicitly labeled **synthetic** and **non-causal**
- descriptive comparison vs Phase 68 canonical cohort evidence
- final classification: `strong evidence` / `weak evidence` / `inconclusive`

This phase does not own:
- any changes to model, `tau_0`, thresholds, planner logic, recourse logic, ranking logic, or trust-check logic
- any new action types
- any causal attribution or uplift claims

</domain>

<decisions>
## Implementation Decisions

### Source population (locked)
- The **source denied population** is the Phase 68 canonical real cohort run (full available denied under shipped runtime):  
  `credit-coach/artifacts/evaluations/v25_real_cohort_eval_20260411_full_processed_all_denied_n367_seed42`
- Dataset limitation must be carried forward explicitly:
  - full available denied population under shipped runtime on `full_processed` is **n=367**

### Recoverable-heavy cohort definition (locked)
Primary filter (C):
- Eligible customers are those with **runtime-emitted** `threshold_reach_possible = true`.

Secondary constraint (A):
- Within `threshold_reach_possible = true`, further restrict to the **lowest approval-gap segment** to make the cohort “recoverable-heavy”.

Determinism and audit rule:
- Cohort membership must be reproducible from **runtime-first artifacts** (no new learned model, no downstream recomputation that changes truth).
- The selection logic must emit an auditable manifest:
  - `selected_customer_ids.csv`
  - `selection_summary.json` (counts before/after each filter, plus approval-gap cutoff used)

Operational fallback (allowed within Phase 69, still selection-only):
- If the combined filter yields too few customers to be informative, relax only the **secondary approval-gap constraint** (do not relax the `threshold_reach_possible=true` primary filter). Any relaxation must be recorded explicitly in `selection_summary.json` and the report.

### Cohort size (locked)
- Use **all eligible customers** (no sampling, no replacement).
- Any seed parameter should be carried only for run-ID convention and determinism auditing, not for sampling.

### Evidence rubric (locked: must be detailed and deterministic)
Phase 69 must define a detailed rubric that outputs one of:
- `strong evidence`
- `weak evidence`
- `inconclusive`

Rubric requirements:
- Must remain **descriptive** and **non-causal**.
- Must include **trust-clean gating**:
  - `selected_invalid_winner_count = 0`
  - `selected_surface_drift_count = 0`
  - `operator_packet_contradiction_count = 0`
- Must include **population sufficiency** gates (explicit minimum N; rationale: avoid over-reading tiny cohorts).
- Must compare to Phase 68 canonical cohort using like-for-like metrics already emitted by the pipeline, including:
  - movement rate
  - strong movement rate
  - `threshold_reach_possible_rate`
  - `threshold_reach_priority_rate`
  - `selected_path_movement_strength_distribution`
  - recoverability / gap distributions
- Must include a **stability check** appropriate for “no sampling” runs (e.g., rerun reproducibility or multi-run hash equivalence), without introducing new heuristics.

### Deterministic outcome simulation (included; explicitly synthetic)
- Include a deterministic outcome-simulation pass that produces **additive** realized-outcome-style artifacts for the Phase 69 cohort.
- Simulation must be:
  - deterministic (same inputs → same outputs)
  - explicitly labeled synthetic / simulated
  - non-causal (no uplift or cause language)
  - constrained to existing action types and selected-path truth (no invented actions)
- Simulation outputs must not be mixed with real observations; they must live in a separate artifact directory with clear naming (e.g., `synthetic_...`).

</decisions>

<specifics>
## Specifics and Assumptions (to be confirmed/encoded in plan)

### “Lowest approval-gap segment” interpretation
- Default interpretation to encode in the plan: apply an approval-gap cutoff within the `threshold_reach_possible=true` subset, using the shipped recoverability band thresholds as the first choice:
  - near-threshold cutoff: `approval_gap <= near_upper` (default `0.10` unless config overrides)
  - if too small, relax to `approval_gap <= mid_upper` (default `0.25`)
- The exact cutoff used must be recorded and reported.

### Phase 68 comparison anchor
- Phase 68 canonical cohort metrics and report remain the baseline for comparisons:
  - `credit-coach/artifacts/evaluations/v25_real_cohort_eval_20260411_full_processed_all_denied_n367_seed42/cohort_metrics.json`
  - deterministic evidence pack docs under `.planning/phases/68-real-cohort-evidence-run/`

</specifics>

<code_context>
## Existing Code Insights

### Reusable assets
- `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py`: canonical cohort-evaluation runner that emits:
  - `customer_level_analysis.csv`
  - `cohort_metrics.json`
  - `cohort_evaluation_report.md`
  - trust counters and targeted population slices
- `credit-coach/src/credit_coach/evaluation/recoverability.py`:
  - defines `approval_gap` and `threshold_reach_possible`
  - documents near/mid thresholds (`DEFAULT_NEAR_UPPER=0.10`, `DEFAULT_MID_UPPER=0.25`)
- `credit-coach/src/credit_coach/cli/run_outcome_feedback.py` (Phase 67 runner):
  - produces realized-outcome artifacts from action execution events and observed outcomes
  - enforces non-causal descriptive reporting patterns

### Integration points
- Add a Phase 69 cohort-selection step that reads runtime-first Phase 68 canonical artifacts (customer-level outputs), filters into a deterministic customer-id manifest, then re-runs the evaluation pipeline over that manifest without changing runtime logic.
- Add a separate outcome-simulation producer that writes synthetic observation tables for the Phase 69 cohort and then invokes the existing outcome-feedback runner to generate additive realized-outcome artifacts (still labeled synthetic).

</code_context>

<deferred>
## Deferred Ideas (explicitly out of Phase 69 scope)

- Any model retraining or new scoring layer
- Any changes to `tau_0` / threshold policy
- Any planner / recourse / ranking modifications
- Any new action types or broadened action semantics
- Any causal study design, uplift claims, or business-impact conclusions

</deferred>

---

*Phase: 69-evidence-amplification*  
*Context gathered: 2026-04-11*

