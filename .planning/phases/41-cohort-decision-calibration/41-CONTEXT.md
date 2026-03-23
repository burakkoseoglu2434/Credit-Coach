# Phase 41: Cohort & Decision Calibration - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Measure and calibrate the deterministic Phase 40.5 decision system like a real fintech funnel across realistic cohorts.

Phase 41 owns:
- cohort strategy for collection runs
- funnel measurement across external and internal decision states
- readiness distribution and status-by-readiness measurement
- shadow calibration and policy comparison
- threshold-tuning review artifacts
- calibration packaging inside collection runs

Phase 41 does **not** own:
- raw or flat contract redesign from Phase 40
- decision ownership semantics from Phase 40.5
- operator packet UX or per-customer review packet copy
- planner source-mix redesign or candidate quality recovery
- production pilot refresh workflow

Those remain in later phases:
- Phase 43 for operator review packs
- Phase 42 for planner quality and source mix
- Phase 44 for production pilot baseline

</domain>

<decisions>
## Implementation Decisions

### 1. Exact Scope Of Phase 41
- Phase 41 is a **measurement and calibration layer** over the shipped Phase 40.5 decision owner.
- Collection outputs must measure the existing decision system, not create a second one.
- Threshold tuning is allowed only at calibration and reporting level unless explicitly approved later.
- Candidate policy evaluation is analysis-only:
  - shipped policy = decision truth
  - candidate policies = shadow comparison only
  - candidate outputs must never write into raw customer artifacts or business-facing consumer surfaces

### 2. Cohort Policy Definitions
- Global selection posture:
  - `quota-first with deterministic soft-fill`
- Selection must be:
  - explainable
  - repeatable
  - cohort-purpose-aware
- `selection_policy_name` and `selection_fill_behavior` must be first-class metadata in manifest outputs.

#### `pilot_mixed`
- Canonical bucket set:
  - `approved_like`
  - `near_threshold`
  - `denied_mid_pressure`
  - `denied_high_pressure`
- Default quota mix:
  - `20 / 30 / 25 / 25`
- Purpose:
  - evaluate the real decision funnel, not only denied-heavy stress behavior
- `near_threshold` should remain slightly overweight because approve-vs-conditional calibration is most visible there.

#### `risk_band_balanced`
- Selection must target balanced representation across `risk_band`.
- It should use quota-first selection by band, then deterministic soft-fill from the nearest remaining bands if a bucket underfills.
- Purpose:
  - compare decision behavior without letting one risk band dominate the run.

#### `ops_queue_replay`
- Canonical posture:
  - `order-preserving replay`
- This policy must prefer queue realism over balancing.
- It should preserve input ordering as much as possible and use deterministic truncate or deterministic slice rather than sampling-first behavior.
- Purpose:
  - simulate how the current operator queue would actually look.

#### `offer_needed_balanced`
- Canonical posture:
  - `two-pass deterministic rebalance`
- Pass 1:
  - build a broad deterministic candidate set using the primary cohort purpose
- Pass 2:
  - rebalance to `offer_needed` vs `no_offer_needed`
- Guardrail:
  - rebalance must not destroy the original cohort purpose; it may only rebalance within allowed tolerance.

#### `denied_first_near`
- Keep as:
  - `stress-test only`
- It remains useful for gap-finding and hard-case analysis, but it is not the canonical pilot cohort.

### 3. Funnel Metric Definitions
- Canonical funnel metrics:
  - `approved_share`
  - `conditional_share`
  - `rejected_share`
  - `internal_needs_review_share`
- Business-visible funnel truth is the external three-state contract:
  - `approved_share`
  - `conditional_share`
  - `rejected_share`
- Supporting calibration/system-health truth:
  - `internal_needs_review_share`
  - `approve_plus_conditional_share`
  - optional `conditional_to_approved_potential`
- `approve_plus_conditional_share` is the direct North Star tracking metric.
- `internal_needs_review_share` is system-health/supporting truth, not a business-facing decision state.

### 4. Readiness Distribution Definitions
- Readiness must reuse the Phase 40.5 taxonomy:
  - `now`
  - `week_4`
  - `week_12`
  - `week_24`
  - `not_ready`
  - `unknown_review`
- No new readiness taxonomy may be created in Phase 41.

#### Guardrails
- `APPROVED` may only align to:
  - `now`
  - `week_4`
- `CONDITIONAL` may align to:
  - `week_4`
  - `week_12`
  - `week_24`
- `REJECTED` should align to:
  - `not_ready`
- internal `NEEDS_REVIEW` should align to:
  - `unknown_review`

#### Reporting Shape
- Both are required:
  - overall readiness distribution
  - `P(status | readiness)` cross-tab
- Business summary should use short insights, not dump the full cross-tab.
- Full cross-tab matrix must exist in artifacts.

### 5. Calibration Loop Design
- Calibration posture:
  - `shadow calibration first`
- Candidate policy evaluation is allowed only as a comparison layer over the Phase 40.5 payload.
- Candidate policy must never become raw artifact truth or business-facing output.

#### Comparison Granularity
- Headline:
  - cohort-level comparison
- Supporting:
  - segment-level breakdown

#### Supporting Lenses
- `risk_band`
- `expected_readiness`
- `conditional_type`
- `offer_needed_flag`
- `decision_confidence_band`

#### Analysis Lens Guardrail
- Segments are analysis lenses only.
- Segments must not become a second decision rule set.

### 6. Threshold-Tuning Summary Design
- Minimum comparison metrics per policy version:
  - `approved_share`
  - `conditional_share`
  - `rejected_share`
  - `internal_needs_review_share`
  - `approve_plus_conditional_share`
  - `readiness_distribution`
  - `false_positive_proxy`
  - `north_star_pass`
- Threshold-tuning review must also include:
  - `delta_vs_baseline`
  - `decision_shift_matrix`

#### False-Positive Proxy
- Formal contract:
  - `false_positive_proxy = w1 * low_realization_rate + w2 * weak_readiness_alignment_rate + w3 * internal_review_pressure_rate`
- Canonical components:
  - `low_realization_rate`
    - approved or conditional customers with `realization_anchor < 0.3`
  - `weak_readiness_alignment_rate`
    - approved-like outcomes with readiness misaligned to approval expectations
  - `internal_review_pressure_rate`
    - conditional plus internal-review pressure concentration
- Guardrail:
  - if `false_positive_proxy` rises while approve share rises, the approve increase is suspect rather than automatically positive.

### 7. Required Artifact And Schema Changes
- Calibration artifacts must live under the same collection run root.
- New subtree:
  - `calibration/`
- Existing collection roots remain:
  - `raw/`
  - `flat/`

#### Manifest Additions
- `cohort_definition`
- `cohort_purpose`
- `selection_policy_name`
- `selection_fill_behavior`
- `policy_version_evaluated`
- `candidate_policy_versions_compared`
- `funnel_summary`
- `readiness_summary`
- `calibration_summary`

#### Calibration Artifact Set
- `calibration/funnel_summary.json`
- `calibration/readiness_distribution.csv`
- `calibration/status_by_readiness.csv`
- `calibration/policy_comparison.csv`
- `calibration/decision_shift_matrix.csv`
- `calibration/segment_breakdown.csv`
- `calibration/calibration_review.md`

### 8. Validation And Ownership Guardrails
- Phase 41 artifacts must be additive and backward-compatible.
- Existing flat columns must remain.
- Existing `collection_summary.md` structure must not break; new sections are additive only.
- Calibration artifacts are read-only measurement outputs over the Phase 40.5 decision payload.
- Calibration outputs must never become the source of decision truth.

### 9. Acceptance Criteria
- Collection runs can evaluate:
  - `pilot_mixed`
  - `risk_band_balanced`
  - `ops_queue_replay`
  - `offer_needed_balanced`
  - `denied_first_near`
- `denied_first_near` is clearly marked as stress-test only.
- Cohort outputs show external funnel metrics and internal review share without leaking internal review into business-facing decision truth.
- Readiness distribution and `P(status | readiness)` cross-tab are produced for every Phase 41 calibration run.
- Shadow calibration outputs compare shipped policy vs candidate policies without changing raw or business-facing decision owner.
- Threshold-tuning review includes baseline deltas and decision shift matrix.
- New calibration outputs live under the same collection run root and remain backward-compatible.

### 10. Recommended Implementation Order
- First, extend cohort selection semantics and metadata in the collection runner.
- Second, add canonical funnel and readiness aggregation over the existing Phase 40.5 decision payload.
- Third, implement shadow calibration comparison helpers:
  - candidate policy evaluation
  - false-positive proxy
  - decision shift matrix
- Fourth, write calibration artifacts into `calibration/` under the same collection root.
- Fifth, extend manifest and summary packaging with calibration-aware sections.
- Sixth, add regression tests for:
  - cohort selection semantics
  - funnel/readiness outputs
  - shadow calibration comparison
  - backward-compatible packaging

### Claude's Discretion
- Exact candidate policy config shape for shadow comparison
- Exact weights for `false_positive_proxy` components
- Exact `decision_confidence_band` bucket edges
- Whether calibration helpers live inside `run_customer_artifact_collection.py` or move into a new evaluation helper module

</decisions>

<specifics>
## Specific Ideas

- This phase should make the system feel like a real fintech funnel, not a denied-only diagnostics tool.
- `pilot_mixed` is the main truth cohort; `denied_first_near` remains useful but must stop behaving like the default business proof lens.
- The most important non-obvious rule is:
  - candidate policy comparison may exist
  - candidate policy ownership may not
- The most valuable supporting signal is not only share movement but also whether the system is becoming falsely optimistic.
- The packaging target is one collection run that carries:
  - raw inspection
  - flat review
  - calibration and tuning review
  under one run ID.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py)
  - already owns deterministic cohort selection and collection-root artifact packaging
  - already writes manifest, summary, raw, and flat outputs
  - currently supports:
    - `denied_first_near`
    - `union_denied_near`
    - `denied_only`
    - `random_mixed`
- [portfolio_validation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/portfolio_validation.py)
  - already carries useful segment lenses:
    - `risk_band`
    - `recoverability_segment`
    - `offer_needed_segment`
  - useful as a pattern source for segment analysis, not as a second decision owner
- [run_phase_experiment_suite.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py)
  - already has snapshot/comparison/threshold-review language
  - useful for policy-comparison formatting patterns and north-star pass/fail structure

### Integration Points
- Primary implementation seam:
  - `credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py`
- Likely new helper seam:
  - `credit-coach/src/credit_coach/evaluation/decision_calibration.py`
- Primary test seams:
  - `credit-coach/tests/test_customer_artifact_collection.py`
  - new `credit-coach/tests/test_decision_calibration.py`
  - optional supporting checks in `credit-coach/tests/test_phase_experiment_suite.py`

### Constraints From Existing Code
- Phase 40.5 decision payload is already mirrored into collection outputs.
- Collection summary today only reports simple distributions and contract health.
- There is no existing calibration subtree under collection root yet.
- The current cohort runner does not yet know the difference between:
  - stress-test cohorts
  - pilot cohorts
  - queue replay cohorts

</code_context>

<deferred>
## Deferred Ideas

- Operator packet formatting and short per-customer review narratives belong to Phase 43.
- Planner source-mix competitiveness and zero-action winner recovery belong to Phase 42.
- Policy promotion, release QA, and production refresh automation belong to Phase 44.

</deferred>
