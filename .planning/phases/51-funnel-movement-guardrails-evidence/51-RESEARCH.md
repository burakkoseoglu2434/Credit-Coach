# Phase 51: Funnel Movement Guardrails & Evidence - Research

**Researched:** 2026-04-03
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest deterministic evidence layer that can explain why `APPROVED` and `CONDITIONAL` movement is still absent after Phase `49` and Phase `50`, while preserving the shipped `v2.2` trust baseline and without introducing a new policy family?

## Planning Basis

Phase 51 decisions are locked in [51-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/51-funnel-movement-guardrails-evidence/51-CONTEXT.md). This planning pass relies on:

- [PROJECT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/PROJECT.md)
- [ROADMAP.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/ROADMAP.md)
- [REQUIREMENTS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/REQUIREMENTS.md)
- [STATE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/STATE.md)
- [49-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/49-threshold-policy-evaluation-provenance/49-CONTEXT.md)
- [50-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/50-offer-readiness-outcome-rules/50-CONTEXT.md)
- [51-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/51-funnel-movement-guardrails-evidence/51-CONTEXT.md)
- [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py)
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py)
- [run_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_baseline_refresh.py)
- [run_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_artifact_qa.py)
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py)
- [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py)
- [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py)
- [run_phase_experiment_suite.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py)
- [test_decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_decision_calibration.py)
- [test_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_customer_artifact_collection.py)
- [test_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_pilot_baseline_refresh.py)
- [test_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_pilot_artifact_qa.py)
- [test_phase_experiment_suite.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_phase_experiment_suite.py)
- [test_recourse_funnel_kpis.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_recourse_funnel_kpis.py)

This basis is sufficient because Phase 51 does not need new signals or new decision logic. It needs to read the Phase `49` threshold comparison outputs and Phase `50` outcome-rule comparison outputs, classify why they did not create promotable movement, and package that diagnosis into the existing collection and pilot proof surfaces.

## Executive Summary

Phase 51 should be implemented as a **diagnostic attribution layer**, not as a third tuning wave.

The cleanest shape is:

`existing policy comparison + existing outcome-rule comparison + existing trust counters + existing portfolio blocker mix -> deterministic movement guardrail summary -> dominant bottleneck diagnosis -> collection/pilot proof`

The repo scan shows six important truths:

1. [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py) already owns the comparison frames, shift matrices, false-positive proxy logic, and explicit `shortlisted | blocked | no_safe_uplift` recommendation outputs from Phases `49` and `50`
2. [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) already packages calibration artifacts, readiness distributions, segment breakdowns, trust counters, and collection summaries, so it is the correct seam for new guardrail evidence
3. [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py) already emits the structural ceiling metrics Phase 51 needs, especially `offer_ready_contender_share`, `provisional_offer_share`, `approval_shell_only_share`, and `non_empty_contender_share`
4. [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py) already aggregates dominant blockers and queue hotspots at collection level; Phase 51 can reuse that as an input to recommendation-space and cohort-structure diagnosis without reopening operator semantics
5. [run_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_baseline_refresh.py) and [run_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_artifact_qa.py) already mirror and validate comparison provenance, so they are the right additive path for dominant bottleneck reporting
6. The standard three-cohort rerun loop already exists and should remain the only cohort proof surface for Phase 51

## Concrete Repo Findings

### 1. Comparison owners already separate threshold and offer/readiness candidate families

[decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py) already produces:

- threshold comparison rows for the Phase `49` policy ladder
- outcome-rule comparison rows for the Phase `50` ladder
- shift matrices for both
- explicit recommendation summaries with `shortlisted`, `blocked`, and `no_safe_uplift`
- false-positive proxy and internal review metrics

That means Phase 51 can diagnose:

- “no movement happened”
- “movement happened but was blocked”
- “movement happened in one candidate family but not the other”

without building a new evaluation engine.

### 2. Structural ceiling signals already exist in current run outputs

[run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py) and [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) already expose:

- readiness distributions
- `offer_ready_contender_share`
- `provisional_offer_share`
- `approval_shell_only_share`
- `non_empty_contender_share`
- trust counters
- segment breakdowns

So Phase 51 does not need new portfolio instrumentation. It needs a deterministic way to interpret what the current evidence already says about movement ceilings.

### 3. Operator collection briefing is already a blocker-mix input

[operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py) already produces collection-level blocker summaries and hotspots.

That gives Phase 51 a clean additive input for diagnosing:

- recommendation-space bottlenecks when dominant blockers point to weak actionability or weak impact
- structural bottlenecks when the blocker mix points to customer populations that are too far from movement

This is the right posture because operator packet semantics remain untouched.

### 4. Pilot proof seams are already provenance-friendly

[run_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_baseline_refresh.py) already mirrors recommendation summaries from calibration artifacts, and [run_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_artifact_qa.py) already asserts additive provenance contracts.

Phase 51 should extend these seams only additively:

- dominant bottleneck
- movement guardrail summary
- promotion-blocker summary

### 5. Trust guardrails are already fixed promotion prerequisites

Phases `45` through `48` made the trust stack explicit and measurable:

- invalid winners cannot be selected
- DICE contenders are typed and eligible
- selected-surface drift is tracked
- operator coherence is tracked

Phase 51 should not reinterpret these as soft signals. If any trust counter regresses, the diagnosis should become `trust_regression_blocked`.

## What Phase 51 Must Deliver

### 1. One canonical movement-guardrail summary owner

The owner should live in [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py) and produce:

- trust guardrail status
- risk/promotion guardrail status
- movement evidence counters
- structural ceiling signals
- threshold-vs-outcome attribution
- dominant bottleneck diagnosis

### 2. One promotion-blocker matrix

The phase should make it easy to answer:

- which candidate families created movement
- which candidates were blocked
- why they were blocked
- whether the absence of movement is due to guardrails or zero candidate effect

### 3. One deterministic bottleneck classifier

The classifier should distinguish:

- `threshold_guardrail_blocked`
- `offer_readiness_guardrail_blocked`
- `recommendation_space_limited`
- `structural_cohort_limited`
- `mixed_no_safe_uplift`
- `trust_regression_blocked`

### 4. First-class evidence artifacts

The calibration subtree should gain:

- `movement_guardrail_summary.json`
- `movement_promotion_blockers.csv`
- `movement_bottleneck_breakdown.csv`
- `movement_ceiling_breakdown.csv`
- `movement_guardrail_review.md`

And collection artifacts should surface:

- `dominant_movement_bottleneck`
- `movement_guardrail_summary`
- `promotion_blocker_summary`

### 5. Honest three-cohort proof

Phase 51 succeeds if it can explain why movement is absent on:

- `pilot_mixed`
- `risk_band_balanced`
- `offer_needed_balanced`

even if no new uplift is found.

## Validation Architecture

The existing test seams are already strong enough:

- [test_decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_decision_calibration.py) for guardrail summary, blocker attribution, and dominant bottleneck classification
- [test_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_customer_artifact_collection.py) for artifact packaging, manifest fields, and summary sections
- [test_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_pilot_baseline_refresh.py) and [test_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_pilot_artifact_qa.py) for pilot-facing provenance and QA checks
- [test_phase_experiment_suite.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_phase_experiment_suite.py) and [test_recourse_funnel_kpis.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_recourse_funnel_kpis.py) for rerun compatibility and movement evidence sanity

## Recommended Plan Shape

The cleanest split is:

1. `51-01` — build the movement guardrail summary, promotion-blocker matrix, and deterministic bottleneck classifier in [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py)
2. `51-02` — package the new artifacts and summary sections in [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py), and mirror the dominant diagnosis into pilot-facing refresh and QA outputs
3. `51-03` — extend regressions and run the three standard 250-customer cohorts to prove whether the dominant bottleneck is guardrail-driven, recommendation-space-driven, structural, or mixed

The phase is successful if the resulting evidence is explicit, replayable, and trust-safe, even when the answer is that uplift is absent because the current action space or current cohort composition is the binding constraint.
