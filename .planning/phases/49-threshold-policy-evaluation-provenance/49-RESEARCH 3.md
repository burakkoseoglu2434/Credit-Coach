# Phase 49: Threshold Policy Evaluation & Provenance - Research

**Researched:** 2026-04-02
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest safe implementation that can compare a bounded set of threshold-policy profiles against the shipped `v2.2` baseline, preserve exact provenance, and surface a clear shortlist or `no_safe_uplift` result without reopening any trust layer?

## Planning Basis

Phase 49 decisions were discussed in-session and are now locked in [49-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/49-threshold-policy-evaluation-provenance/49-CONTEXT.md). For this planning pass the authoritative inputs are:

- [PROJECT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/PROJECT.md)
- [ROADMAP.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/ROADMAP.md)
- [REQUIREMENTS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/REQUIREMENTS.md)
- [STATE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/STATE.md)
- [41-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/41-cohort-decision-calibration/41-CONTEXT.md)
- [44-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/44-production-pilot-baseline/44-CONTEXT.md)
- [49-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/49-threshold-policy-evaluation-provenance/49-CONTEXT.md)
- [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py)
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py)
- [run_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_baseline_refresh.py)
- [run_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_artifact_qa.py)
- [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py)
- [test_decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_decision_calibration.py)
- [test_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_customer_artifact_collection.py)
- [test_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_pilot_baseline_refresh.py)
- [test_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_pilot_artifact_qa.py)

This is sufficient because Phase 49 does not need a new decision engine. It only needs to formalize a bounded threshold ladder, compare it against the shipped policy, and carry that comparison truth into the same evidence surfaces already established by Phases 41 and 44.

## Executive Summary

Phase 49 should be planned as an **analysis-only policy ladder and provenance phase**, not as a policy-promotion phase and not as an offer/readiness outcome phase.

The safest shape is:

`baseline mirror -> deterministic candidate ladder -> analysis-only shortlist/no_safe_uplift -> collection/pilot provenance propagation -> three-cohort proof`

The code scan shows five important truths:

1. [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py) already owns candidate-policy comparison, false-positive proxy, shift matrices, and segment breakdowns, so Phase 49 should extend that owner rather than inventing a second evaluator
2. `DEFAULT_CANDIDATE_POLICIES` in [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py) still reflects older generic candidates, so the bounded `v2.3a` ladder is the cleanest Phase 49 insertion point
3. [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) already writes the calibration subtree and carries `policy_version_evaluated` plus `candidate_policy_versions_compared`, so Phase 49 can stay additive
4. [run_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_baseline_refresh.py) and [run_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_artifact_qa.py) already expect policy-version provenance, so Phase 49 should enrich that provenance instead of redefining it
5. [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py) remains the sole live decision owner, so Phase 49 must not touch decision truth or selected consumer surfaces

## Concrete Repo Findings

### 1. The comparison seam already exists and is analysis-friendly

[decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py) already exposes:

- `prepare_metrics_for_calibration(...)`
- `_candidate_policy_row(...)`
- `build_policy_comparison(...)`
- false-positive proxy computation

That means Phase 49 does not need a new evaluation framework. It needs a better policy catalog, a deterministic recommendation summary, and explicit provenance.

### 2. Current candidate policies are too generic for v2.3

The existing `DEFAULT_CANDIDATE_POLICIES` still point to older relaxed/strict profiles. Phase 49 needs the locked small ladder from [49-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/49-threshold-policy-evaluation-provenance/49-CONTEXT.md):

- shipped baseline mirror
- `analysis_mild_relax_v2_3a`
- `analysis_relaxed_v2_3a`
- `analysis_strict_control_v2_3a`

That ladder should stay deterministic, tiny, and analysis-only.

### 3. Collection outputs already carry most of the needed artifact structure

[run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) already writes:

- `policy_comparison.csv`
- `decision_shift_matrix.csv`
- `segment_breakdown.csv`
- `calibration_review.md`

It also already threads:

- `policy_version_evaluated`
- `candidate_policy_versions_compared`

So the missing work is mostly:

- deterministic candidate catalog artifact
- explicit recommended candidate summary
- additive summary/manifest proof for shortlist vs `no_safe_uplift`

### 4. Downstream pilot surfaces are provenance consumers, not policy owners

[run_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_baseline_refresh.py) and [run_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_artifact_qa.py) already use `policy_version_evaluated` as a compatibility anchor.

Phase 49 should add analysis provenance such as:

- candidate versions compared
- recommended candidate version
- recommendation status

without weakening existing live-version checks.

### 5. The real deliverable is explicit policy evidence, not uplift at any cost

Phase 49 ends successfully even if it concludes `no_safe_uplift`.

The success condition is:

- deterministic comparison
- trust counters remain clean
- shortlist or explicit block decision is written honestly

This is important because Phase 49 is still a proof phase, not a promotion phase.

## What Phase 49 Must Deliver

### 1. One deterministic bounded policy ladder

The shipped baseline mirror and the three locked candidate profiles must be represented in one canonical catalog, replayable in artifacts and tests.

### 2. One recommendation summary over the comparison outputs

The evaluator must say one of:

- `shortlisted`
- `blocked`
- `no_safe_uplift`

with a reason that can be surfaced in artifacts.

### 3. Additive provenance in collection and pilot packaging

Phase 49 must make it obvious:

- which policy produced live truth
- which policy was evaluated as baseline
- which candidate policies were compared
- which candidate, if any, is recommended for later phases

### 4. Three-cohort proof on the standard evidence cohorts

The phase must close on:

- `pilot_mixed`
- `risk_band_balanced`
- `offer_needed_balanced`

with trust counters still clean and a clear comparison outcome.

## Validation Architecture

Phase 49 can reuse existing test seams:

- [test_decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_decision_calibration.py) for policy ladder, policy comparison, segment breakdown, shortlist logic, and `no_safe_uplift`
- [test_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_customer_artifact_collection.py) for collection packaging, manifest, summary, and calibration subtree provenance
- [test_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_pilot_baseline_refresh.py) and [test_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_pilot_artifact_qa.py) for additive pilot-facing provenance compatibility
- [test_phase_experiment_suite.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_phase_experiment_suite.py) and optionally [test_recourse_funnel_kpis.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_recourse_funnel_kpis.py) for rerun compatibility and funnel-output sanity

## Recommended Plan Shape

The cleanest split is:

1. `49-01` — baseline mirror, bounded candidate ladder, and shortlist / `no_safe_uplift` evaluator in [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py)
2. `49-02` — collection and pilot-facing provenance propagation with additive artifacts only
3. `49-03` — regression closure plus three deterministic 250-customer reruns proving trust-safe threshold evaluation
