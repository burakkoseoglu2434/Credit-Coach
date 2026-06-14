# Phase 50: Offer & Readiness Outcome Rules - Research

**Researched:** 2026-04-02
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest safe implementation that can turn existing offer/readiness signals into bounded, analysis-only outcome rules, measure whether they create real funnel movement, and surface that movement without reopening any shipped trust layer?

## Planning Basis

Phase 50 decisions were discussed in-session and are now locked in [50-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/50-offer-readiness-outcome-rules/50-CONTEXT.md). For this planning pass the authoritative inputs are:

- [PROJECT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/PROJECT.md)
- [ROADMAP.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/ROADMAP.md)
- [REQUIREMENTS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/REQUIREMENTS.md)
- [STATE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/STATE.md)
- [47-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/47-selected-surface-consistency/47-CONTEXT.md)
- [48-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/48-operator-packet-coherence/48-CONTEXT.md)
- [49-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/49-threshold-policy-evaluation-provenance/49-CONTEXT.md)
- [50-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/50-offer-readiness-outcome-rules/50-CONTEXT.md)
- [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py)
- [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py)
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py)
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py)
- [run_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_baseline_refresh.py)
- [run_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_artifact_qa.py)
- [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py)
- [decision_explanation_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/decision_explanation_pack.py)
- [test_decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_decision_calibration.py)
- [test_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_customer_artifact_collection.py)
- [test_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_pilot_baseline_refresh.py)
- [test_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_pilot_artifact_qa.py)
- [test_operator_review_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_operator_review_pack.py)
- [test_decision_explanation_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_decision_explanation_pack.py)

This is sufficient because Phase 50 does not need a new decision engine. It needs to reuse already-emitted offer/readiness fields, build a bounded analysis-only rule ladder, and package the resulting outcome movement evidence into the same trustworthy artifact surfaces already established by Phases 47-49.

## Executive Summary

Phase 50 should be planned as an **analysis-only outcome-rule phase**, not as another threshold phase and not as an action-space phase.

The safest shape is:

`existing offer/readiness fields -> deterministic outcome-rule catalog -> analysis-only rule comparison -> additive consumer-safe rule-effect notes -> three-cohort proof`

The code scan shows five important truths:

1. [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py) already uses `expected_readiness`, `approval_ready_4w`, and `offer_maturity`, but only as approve/conditional blocking logic rather than explicit outcome-rule profiles
2. [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py) already publishes the additional signals Phase 50 needs, especially `approval_ready_12w`, `approval_ready_24w`, `rankable_offer_count`, `approval_pending_action_count`, `approval_dependent_plan_probability`, `offer_acceptance_probability`, and `combined_plan_realization_probability`
3. [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py) already owns analysis-only comparison, shift matrices, segment breakdowns, and recommendation summaries, so it is the correct owner for Phase 50’s bounded outcome-rule comparison
4. [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) already writes calibration artifacts and builds operator packets, making it the natural seam for additive rule-effect provenance and consumer-safe note propagation
5. [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py) and [decision_explanation_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/decision_explanation_pack.py) already consume additive selected-truth fields with drift guards, so Phase 50 should add rule-effect notes as append-only consumer context, not as alternate decision owners

## Concrete Repo Findings

### 1. Offer and readiness are present in the decision owner, but only as gating logic

[ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py) already computes:

- `offer_maturity`
- `expected_readiness`
- `approval_ready_4w`
- `combined_plan_realization_probability` through `realization_anchor`

But their current role is:

- block `APPROVED` when `offer_maturity in {inactive, provisional}`
- classify `CONDITIONAL` as `OFFER_GATED` or `TIME_GATED`
- downgrade `expected_readiness` to `not_ready` / `unknown_review`

So the positive information is present, but it is not yet organized into explicit bounded uplift rules.

### 2. The richer positive signals already exist in roadmap summary output

[run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py) already writes:

- `approval_ready_12w`
- `approval_ready_24w`
- `rankable_offer_count`
- `approval_pending_action_count`
- `approval_dependent_plan_probability`
- `offer_acceptance_probability`
- `combined_plan_realization_probability`
- `offer_maturity`

That means Phase 50 does not need new feature engineering. It needs a disciplined way to interpret these existing fields in analysis-only outcome profiles.

### 3. Phase 49 created the right comparison owner to extend

[decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py) already provides:

- deterministic candidate profile catalogs
- explicit recommendation summaries
- decision shift matrices
- segment breakdowns
- false-positive proxy reporting

So Phase 50 should extend this owner with an outcome-rule catalog and comparison frame rather than introducing a second evaluation stack.

### 4. Collection packaging is already the right place for additive evidence

[run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) already:

- writes calibration outputs
- builds per-customer operator packets
- produces collection summary and manifest evidence

This makes it the correct seam for:

- outcome-rule catalog artifacts
- outcome-rule comparison and recommendation-summary artifacts
- additive operator/explanation note fields describing analysis-only movement

### 5. Selected-truth consumers can already accept additive context safely

[operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py) and [decision_explanation_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/decision_explanation_pack.py) already follow the Phase 47/48 rule:

- selected truth stays owned elsewhere
- consumer surfaces accept additive notes but may not invent contradictory decision truth

That makes them suitable for Phase 50 rule-effect messaging such as:

- “Under the analysis offer-support rule, this case would move from REJECTED to CONDITIONAL.”

without rewriting `decision_status` or selected recommendation ownership.

## What Phase 50 Must Deliver

### 1. One deterministic outcome-rule catalog

The initial rule ladder should stay tiny and explicit:

- `analysis_offer_support_v2_3b`
- `analysis_readiness_support_v2_3b`
- `analysis_offer_readiness_combo_v2_3b`

It must remain analysis-only and must not reopen threshold-only tuning.

### 2. One explicit outcome-rule comparison owner

The evaluator should produce, per candidate profile:

- baseline decision
- candidate decision
- whether a rule applied
- what source applied it
- what transition occurred
- why it occurred

and then conclude with:

- `shortlisted`
- `blocked`
- or `no_safe_uplift`

### 3. Additive provenance in collection and pilot-facing evidence

Phase 50 must make it obvious:

- which outcome-rule catalog version was evaluated
- which rule profiles were compared
- which rule profile, if any, is recommended
- what rule transition happened for a customer or cohort

### 4. Additive consumer-safe outcome notes

Operator packet and explanation pack should be able to state when an analysis-only rule would change the outcome, but only as additive context. They must not overwrite the live selected truth.

### 5. Three-cohort proof on the standard evidence cohorts

The phase must still close on:

- `pilot_mixed`
- `risk_band_balanced`
- `offer_needed_balanced`

with trust counters clean and with either:

- at least one shortlisted rule profile
- or explicit `no_safe_uplift`

## Validation Architecture

Phase 50 can reuse and extend existing seams:

- [test_decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_decision_calibration.py) for rule catalog determinism, rule application logic, comparison rows, and shortlist / `no_safe_uplift`
- [test_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_customer_artifact_collection.py) for collection artifacts, manifest fields, summary sections, and additive outcome-rule provenance
- [test_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_pilot_baseline_refresh.py) and [test_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_pilot_artifact_qa.py) for additive pilot-facing provenance compatibility
- [test_operator_review_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_operator_review_pack.py) and [test_decision_explanation_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_decision_explanation_pack.py) for additive rule-effect notes without selected-truth drift
- [test_phase_experiment_suite.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_phase_experiment_suite.py) and [test_recourse_funnel_kpis.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_recourse_funnel_kpis.py) for rerun compatibility and cohort-level funnel sanity

## Recommended Plan Shape

The cleanest split is:

1. `50-01` — bounded offer/readiness outcome-rule catalog, comparison owner, and explicit shortlist / `no_safe_uplift` logic in [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py)
2. `50-02` — collection, pilot, and consumer-safe rule-effect provenance propagation across artifacts, operator packet, and explanation pack
3. `50-03` — regression closure plus three deterministic 250-customer reruns proving whether offer/readiness can create safe movement where thresholds alone could not

The phase should be considered successful even if it concludes `no_safe_uplift`, as long as that conclusion is explicit, evidence-backed, and trust-safe.
