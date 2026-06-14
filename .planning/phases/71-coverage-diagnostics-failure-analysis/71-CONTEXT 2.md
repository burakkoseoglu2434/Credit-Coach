# Phase 71: Coverage Diagnostics & Failure Analysis - Context

**Gathered:** 2026-04-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 71 explains why the current shipped system produces actionable output for only about `~3%` of W2a customers while routing about `~97%` into `recourse_mode=limited` and empty-state selected surfaces.

This phase owns:
- a deterministic failure-taxonomy artifact for coverage loss
- segment-level explanation of `full` versus `limited` routing
- latent-path versus surfaced-path mismatch analysis
- decomposition of the empty-state population into quantified buckets
- a concrete diagnostic recommendation for Phase 72

This phase does not own:
- any runtime behavior change
- gate relaxation, threshold redesign, or new recourse modes
- new action semantics
- model retraining
- customer/operator wording changes

Guardrail:
- Phase 71 is diagnostic only. It may add audit-only or standalone diagnostics, but it must not silently change selected truth, gate semantics, or artifact comparability for shipped outputs.

</domain>

<decisions>
## Implementation Decisions

### 1) Artifact ownership: standalone diagnostic artifact first
- Phase 71 should own its taxonomy in a **standalone diagnostic artifact set**, not by immediately redefining the canonical `customer_level_analysis.csv` contract.
- Recommended artifact family:
  - `coverage_diagnostic_summary.json`
  - `coverage_diagnostic_customer_breakdown.csv`
  - `coverage_reason_frequency.csv`
  - `latent_vs_surfaced_mismatch.csv`
  - `empty_state_decomposition.json`
  - `coverage_diagnostic_report.md`
- The standalone artifact should join existing runtime/evaluation outputs rather than replace them.
- Small durable fields may be proposed later, but this phase should keep the first diagnostic surface additive and low-risk.

### 2) Diagnostic taxonomy should be derived, not a new shipped gate vocabulary
- Keep shipped gate reason codes unchanged:
  - `RECOVERABLE_FULL_MODE`
  - `NOT_RECOVERABLE_LIMITED_MODE`
- Phase 71 should derive its coverage-loss buckets from:
  - recoverability signal reason codes
  - recoverable reason codes
  - structural blocker flags
  - pre-gate latent path evidence
  - selected surface outcome
- Do **not** introduce a new runtime gate vocabulary in this phase.
- Rationale:
  - the current gate contract is intentionally tiny and stable
  - Phase 71 needs explanatory buckets, not a semantics rewrite
  - Phase 72 can consume the diagnostic taxonomy without pretending that shipped runtime behavior already changed

### 3) Use pre-gate shadow truth to separate structural limitation from suppression
- Phase 71 should distinguish customer states using **pre-gate shadow truth**, not only post-gate selected outputs.
- Locked interpretation:
  - **structurally limited** = no credible latent path signal survives after considering valid/rankable path evidence, movement evidence, threshold-reaching evidence, and structural blockers
  - **policy-suppressed / potentially useful** = latent path evidence exists with non-trivial potential, but the shipped gate or selected-surface policy suppresses it into limited/empty-state output
- This shadow truth must stay audit-only in Phase 71.
- It must not alter the shipped selected recommendation, operator packet, explanation pack, or trust counters.

### 4) Smallest mandatory slice before Phase 72
- The minimum admissible diagnostic slice is:
  - `W2a` as the primary diagnosis cohort
  - plus **one control anchor** to confirm the taxonomy is not a one-run artifact
- Preferred control anchor:
  - one earlier canonical denied-cohort anchor such as the Phase 68 baseline, or
  - one smaller/adjacent wave with the same runtime
- Phase 71 should not expand into an all-wave evaluation project. The goal is confident diagnosis, not broad rerun coverage.

### 5) Required empty-state decomposition
- Phase 71 must explain the empty-state population with quantified buckets instead of a single residual “limited” label.
- The decomposition should answer at least:
  - no latent valid path exists
  - latent valid path exists but is not rankable
  - latent rankable path exists but shows no meaningful movement
  - latent movement exists but threshold-reaching signal is trivial
  - latent movement / threshold signal exists but the recoverability gate suppresses surfacing
  - latent signal survives the gate but selected-surface policy still collapses to empty-state
- If some buckets collapse together because the runtime never exposes separate truth, the report must say that explicitly.

### 6) Distinguish “useful latent value” with conservative thresholds
- Phase 71 should publish both:
  - raw latent availability (`valid path`, `rankable path`, `movement > 0`)
  - a stricter “potentially useful” latent subset
- Recommended conservative interpretation:
  - movement-positive if latent expected improvement is genuinely above zero
  - non-trivial threshold signal if a documented threshold-reaching indicator clears a small explicit epsilon (for example `> 0.05`) or equivalent threshold-reaching flag logic
- Exact formulas may be refined in planning, but the cutoff must be explicit, deterministic, and reproducible.

### 7) Mandatory comparison dimensions
- Before Phase 72 starts, Phase 71 diagnostics must compare at least:
  - `recoverability_bucket`
  - `recourse_mode`
  - `selected_recommendation_source`
  - latent action diversity versus surfaced action diversity
  - empty-state rate
  - latent valid/rankable path rates
  - latent movement-positive rate
  - latent non-trivial threshold-signal rate
- Segment reporting must cover at least:
  - `near_threshold`
  - `mid_risk`
  - `structural_limited` / `hard_denied`

### 8) Concrete Phase 72 handoff requirement
- Phase 71 must end with one explicit diagnosis-led recommendation for Phase 72:
  - which bucket is the largest actionable source of coverage loss
  - which source of loss is probably safe to relax first
  - which source of loss is likely “true no-value” and should remain suppressed
- This recommendation must remain descriptive and must not implement the relaxation.

### Claude's Discretion
- Exact file names and table schemas inside the standalone diagnostic artifact, as long as the artifact remains reproducible and clearly tied to W2a plus one control anchor.
- Exact derived bucket labels, as long as they preserve the locked distinction between structural limitation and policy suppression.
- Whether pre-gate shadow truth is computed directly from existing W2a evaluation outputs or via a small additive diagnostic pass, as long as shipped selected truth remains unchanged.

</decisions>

<specifics>
## Specific Findings Already Confirmed

### W2a facts from current artifacts
- `customer_level_analysis.csv` already shows:
  - `recourse_mode=limited` for about `97%`
  - `recourse_mode=full` for about `3%`
  - `selected_recommendation_source=empty_state` for about `97%`
- At the same time, the same W2a artifact already reports:
  - `has_valid_path_flag` rate: `1.0`
  - `has_rankable_path_flag` rate: `1.0`
- Segment split from W2a:
  - `near_threshold`: `n=108`, `full_rate=0.8333`
  - `mid_risk`: `n=463`, `full_rate=0.0`, `empty_state_rate=1.0`
  - `structural_limited`: `n=2429`, `full_rate=0.0`, `empty_state_rate=1.0`
- This means Phase 71 is not trying to discover whether latent structure exists. It is trying to explain why existing latent structure collapses into limited-mode empty state.

### Latent richness already visible in W2a
- Limited-mode customers in W2a still show strong latent diversity in path artifacts:
  - `100%` have at least one latent action family
  - about `96.3%` have at least two latent action families
  - about `76.6%` have at least three latent action families
- Dominant latent action families among limited-mode customers include:
  - `adjust_requested_loan_amount`
  - `refinance`
  - `debt_consolidation`
- Limited-mode latent path types are still diverse:
  - mostly `hybrid`
  - then `customer_only`
  - then `institution_assisted`

### Why pre-gate shadow truth is required
- The shipped gate currently zeroes or blanks selected-path movement fields for limited-mode customers.
- Therefore post-gate fields such as:
  - `movement_score`
  - `threshold_reach_probability`
  - `selected_path_*`
do **not** tell us whether latent value existed before suppression.
- Phase 71 must therefore inspect pre-gate latent evidence from candidate/path artifacts or emit additive shadow diagnostics.

### Working interpretation for Phase 71
- Treat the current system as:
  - trust-clean
  - path-rich internally
  - intentionally fail-closed at the gate/surface layer
- The phase question is therefore:
  - how much of the `97%` empty-state rate is true structural no-value,
  - and how much is conservative suppression of latent but not-yet-promoted value?

</specifics>

<code_context>
## Existing Code Insights

### Reusable assets
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py): the key diagnostic seam.
  - `_attach_recoverability_signal_to_roadmap(...)` computes recoverability from:
    - valid path existence
    - rankable path existence
    - best possible PD improvement
    - readiness / offer posture
  - `_apply_recourse_gate_to_roadmap(...)` then applies shipped gating.
  - In limited mode, it deliberately rewrites selected truth to empty-state and zeroes movement-style selected fields.
- [run_v24_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py): already exports most of the Phase 71 inputs in `customer_level_analysis.csv`, including:
  - recoverability signals
  - gate outputs
  - selected recommendation source
  - path counts
  - path/action diversity
  - movement and threshold fields
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py): already computes useful aggregate diagnostics such as:
  - selected empty-state counts
  - action dominance
  - empty-state-with-action contradiction checks
- [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py): confirms empty-state packets intentionally suppress actions when selected source is empty-state.
- Existing evaluation outputs already include:
  - `customer_level_analysis.csv`
  - `candidate_plans.jsonl`
  - `path_groupings.jsonl`
  - `selected_plans.jsonl`
These are enough to attempt a first diagnostic slice without changing runtime semantics.

### Established patterns
- The repo prefers additive diagnostics over early contract rewrites.
- Trust-clean selected-surface behavior is already treated as a hard invariant.
- Existing planning phases separated:
  - recoverability truth (Phase 61-62)
  - gate routing (Phase 63)
  - movement ranking (Phase 64)
- Phase 71 should therefore explain interactions among those layers, not blur them together into a new runtime rule.

### Critical seam to preserve
- The limited-mode gate currently reuses trusted empty-state rendering rather than inventing a softer selected state.
- Phase 71 diagnostics must sit **around** that seam, not inside it.
- Any latent analysis should therefore be labeled:
  - pre-gate
  - audit-only
  - non-selected

### Best first integration points
- Start from W2a `customer_level_analysis.csv` as the spine table.
- Join latent evidence from:
  - `path_groupings.jsonl` for path/action diversity and rankable-path structure
  - `candidate_plans.jsonl` for latent movement, threshold, execution, and validity evidence
- Use `selected_plans.jsonl` only to confirm what selected truth looked like after gating.
- Publish the derived taxonomy in a standalone phase artifact rather than modifying canonical evaluation outputs first.

</code_context>

<deferred>
## Deferred Ideas

- Introducing `assisted_full` or any other intermediate runtime mode belongs to Phase 72, not Phase 71.
- Surfacing top-k actions belongs to Phase 73.
- Sequential or staged product output belongs to Phase 74.
- Mid-risk unlock behavior belongs to Phase 75.
- Any customer/operator-facing copy changes belong to later surface phases unless a diagnostic label is strictly needed for audit output.

</deferred>

---

*Phase: 71-coverage-diagnostics-failure-analysis*
*Context gathered: 2026-04-18*
