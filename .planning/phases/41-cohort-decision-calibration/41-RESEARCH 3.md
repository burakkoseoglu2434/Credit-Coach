# Phase 41: Cohort & Decision Calibration - Research

**Researched:** 2026-03-23
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest safe implementation that measures the Phase 40.5 decision owner like a fintech funnel across realistic cohorts, without creating a second decision system or leaking shadow-tuning results into raw customer truth?

## Planning Basis

Phase 41 decisions were already discussed in-session and have been reconstructed into `41-CONTEXT.md`. For this planning pass the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/41-cohort-decision-calibration/41-CONTEXT.md`
- `credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py`
- `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/tests/test_customer_artifact_collection.py`
- `credit-coach/tests/test_phase_experiment_suite.py`

This is sufficient because the repo already has:

- a deterministic decision owner from Phase 40.5
- summary-owned raw and flat collection outputs
- reusable segment lenses in portfolio validation
- reusable threshold and snapshot patterns in the phase experiment suite

The gap is no longer missing decision ownership. The gap is missing **cohort realism, funnel measurement, readiness cross-tabs, and shadow calibration packaging**.

## Executive Summary

Phase 41 should be planned as a **measurement-and-comparison phase**, not as a policy-rewrite phase.

The safest shape is:

`deterministic cohort selection -> funnel/readiness aggregation -> shadow calibration comparison -> calibration packaging`

The code scan shows four important truths:

1. collection runner already owns cohort sampling and collection-root artifact packaging
2. Phase 40.5 decision fields already exist in raw and flat outputs, so Phase 41 can measure them directly
3. portfolio validation already has trustworthy segment lenses worth reusing
4. phase experiment suite already has threshold/snapshot comparison patterns, so Phase 41 does not need to invent a new reporting language

The clean split for this phase is therefore:

`cohort semantics -> funnel/readiness contract -> shadow calibration review -> artifact packaging`

## Existing Assets We Can Reuse

### Collection runner already owns the right root seam

- `credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py`
  - already selects cohorts deterministically
  - already writes one run root with `raw/`, `flat/`, manifest, and summary
  - already mirrors decision payload from the shared producer-side owner

This is the right seam for:

- adding new cohort policies
- writing `calibration/` outputs
- extending manifest and summary with funnel and calibration sections

### Portfolio validation already has the right segment lenses

- `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`
  - already uses:
    - `risk_band`
    - `recoverability_segment`
    - `offer_needed_segment`
  - already thinks in business headline vs supporting breakdown terms

This is the right pattern source for:

- segment breakdown tables
- cohort supporting lenses
- honest summary framing

### Phase experiment suite already has threshold comparison language

- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - already works with:
    - threshold dictionaries
    - snapshots
    - pass/fail summaries
    - baseline deltas

This is the right pattern source for:

- `north_star_pass`
- candidate-vs-baseline comparison rows
- calibration review markdown structure

## Concrete Repo Findings

### 1. Current cohort policies are still inspection-first, not funnel-first

`run_customer_artifact_collection.py` today supports:

- `denied_first_near`
- `union_denied_near`
- `denied_only`
- `random_mixed`

That is good enough for artifact inspection, but not yet good enough for pilot-facing funnel measurement. There is no explicit distinction yet between:

- stress-test cohort
- pilot cohort
- queue replay cohort
- offer-balance cohort

### 2. Collection summary is still too simple for calibration use

Current `collection_summary.md` reports:

- decision status distribution
- risk band distribution
- mean best action count / cost / execution probability
- top action / top constraint reason
- contract health

This is useful, but it does not yet answer:

- what is the funnel split?
- where are decisions landing by readiness?
- how would a shadow policy change outcomes?
- is higher approval coming from smarter policy or looser policy?

### 3. Phase 40.5 outputs are already enough to support calibration

Collection metrics already carry:

- `decision_status`
- `decision_status_internal`
- `expected_readiness`
- `decision_confidence`
- `conditional_type`
- `rejection_type`
- `decision_policy_version`
- `realization_anchor`-like probabilities through mirrored summary fields

That means Phase 41 can stay strictly measurement-first.

### 4. Offer-balance cannot be solved honestly with pre-run heuristics only

`offer_needed_segment` is most trustworthy after realized plan outputs exist. That makes a clean `two-pass deterministic rebalance` the right implementation posture instead of inventing a fake pre-run classifier.

## What Phase 41 Must Deliver

### 1. Real cohort semantics

This phase must add clear cohort meanings:

- `pilot_mixed`
- `risk_band_balanced`
- `ops_queue_replay`
- `offer_needed_balanced`
- `denied_first_near` as explicit stress-test only

Selection semantics must be deterministic, explainable, and recorded in manifest metadata.

### 2. Funnel and readiness truth

This phase must turn the Phase 40.5 decision owner into cohort-level funnel reporting:

- external funnel shares
- internal review share
- readiness distribution
- `P(status | readiness)` cross-tab

This is the heart of the fintech funnel story.

### 3. Shadow calibration only

Threshold tuning belongs here only as a comparison layer.

Safe posture:

- shipped policy remains truth
- candidate policies are analysis-only
- candidate policies never overwrite raw or flat customer truth

### 4. Honest optimism control

Phase 41 must explicitly quantify overly optimistic decision movement through a formal `false_positive_proxy`.

Without that, approval growth is impossible to trust.

### 5. Calibration packaging in the same run root

The right artifact model is one collection run that contains:

- raw inspection
- flat review
- calibration review

This preserves one run ID and one truth owner.

## Recommended Plan Split

### Plan 41-01 — Cohort semantics plus funnel/readiness contract

Focus on:

- new cohort policy definitions
- deterministic quota and soft-fill behavior
- funnel metrics
- readiness distribution
- readiness/status cross-tab
- selection metadata

### Plan 41-02 — Shadow calibration and policy comparison

Focus on:

- candidate policy evaluation in shadow mode
- false-positive proxy
- baseline deltas
- decision shift matrix
- segment breakdown with confidence bands

### Plan 41-03 — Manifest, summary, and calibration packaging

Focus on:

- `calibration/` subtree outputs
- manifest expansion
- summary markdown expansion
- backward-compatible packaging
- regression closure
