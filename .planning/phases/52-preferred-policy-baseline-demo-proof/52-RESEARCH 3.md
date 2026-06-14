# Phase 52: Preferred Policy Baseline & Demo Proof - Research

**Researched:** 2026-04-03
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest honest implementation that can select the preferred demo/pilot baseline, package one fallback communication profile, explain why the bounded Phase `49` and Phase `50` candidates were not adopted, and hand off the next milestone without inventing a false uplift win?

## Planning Basis

Phase 52 decisions are locked in [52-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/52-preferred-policy-baseline-demo-proof/52-CONTEXT.md). This planning pass relies on:

- [PROJECT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/PROJECT.md)
- [ROADMAP.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/ROADMAP.md)
- [REQUIREMENTS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/REQUIREMENTS.md)
- [STATE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/STATE.md)
- [49-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/49-threshold-policy-evaluation-provenance/49-CONTEXT.md)
- [50-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/50-offer-readiness-outcome-rules/50-CONTEXT.md)
- [51-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/51-funnel-movement-guardrails-evidence/51-CONTEXT.md)
- [52-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/52-preferred-policy-baseline-demo-proof/52-CONTEXT.md)
- [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py)
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py)
- [run_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_baseline_refresh.py)
- [run_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_artifact_qa.py)
- [pilot/contracts.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/pilot/contracts.py)
- [test_decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_decision_calibration.py)
- [test_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_customer_artifact_collection.py)
- [test_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_pilot_baseline_refresh.py)
- [test_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_pilot_artifact_qa.py)
- [test_phase_experiment_suite.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_phase_experiment_suite.py)
- [test_recourse_funnel_kpis.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_recourse_funnel_kpis.py)

This is sufficient because Phase 52 does not need new signals, new candidate families, or new live policy logic. It needs to consume the already-locked Phase `49-51` evidence and convert that evidence into a deterministic baseline-selection and demo-proof contract.

## Executive Summary

Phase 52 should be planned as an **honest baseline-selection and packaging phase**, not as a final optimization retry.

The cleanest shape is:

`existing policy recommendation + existing outcome-rule recommendation + existing movement guardrail summary -> deterministic baseline selection -> candidate disposition table -> collection and pilot proof packaging -> regression closure`

The repo scan shows five important truths:

1. [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py) already owns the Phase `49` policy catalog and recommendation summary, the Phase `50` outcome-rule catalog and recommendation summary, and the Phase `51` movement guardrail summary and dominant bottleneck logic
2. [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) already writes every calibration artifact Phase 52 needs as inputs and already propagates policy, outcome-rule, and movement summaries into the collection manifest
3. [run_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_baseline_refresh.py) already mirrors comparison truth into refresh summaries and writes proof-facing markdown outputs, so it is the correct place for `demo_policy_proof.md` and `next_milestone_handoff.md`
4. [run_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_artifact_qa.py) already validates additive provenance and artifact existence, which makes it the right seam for enforcing the new Phase 52 proof contract
5. The strongest honest interpretation of the current evidence is that the shipped runtime baseline remains the preferred policy owner, while “preferred” and “fallback” in Phase 52 should mean **communication and packaging posture**, not hidden runtime policy drift

## Concrete Repo Findings

### 1. The analysis truth Phase 52 needs already exists

[decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py) already produces:

- the baseline policy mirror
- the Phase `49` candidate policy catalog
- the Phase `49` recommendation summary with explicit `shortlisted | blocked | no_safe_uplift`
- the Phase `50` outcome-rule catalog
- the Phase `50` recommendation summary with explicit `shortlisted | blocked | no_safe_uplift`
- the Phase `51` movement guardrail summary
- the dominant bottleneck classifier

That means Phase 52 does not need a new evaluator. It needs one deterministic selector that reads these locked outputs and converts them into a demo-ready baseline decision.

### 2. Collection packaging already carries the right provenance seam

[run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) already:

- writes the calibration subtree under each collection run
- writes the collection summary
- writes the collection manifest
- propagates policy and outcome-rule recommendation summaries
- propagates movement guardrail summary, dominant bottleneck, and promotion blocker summary

So Phase 52 should extend this seam with:

- one baseline-selection JSON
- one candidate-disposition CSV
- a few additive manifest fields

rather than creating a parallel reporting path.

### 3. Pilot refresh already has a proof-document seam

[run_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_baseline_refresh.py) already writes:

- `policy_version_comparison.csv`
- `policy_version_comparison.md`
- `pilot_refresh_summary.md`
- `artifact_qa_summary.json`
- `pilot_refresh_manifest.json`

It already mirrors recommended policy status, recommended outcome-rule status, dominant movement bottleneck, and blocker summaries. Phase 52 can therefore add:

- `demo_policy_proof.md`
- `next_milestone_handoff.md`
- preferred/fallback profile fields

without changing the refresh architecture.

### 4. Pilot manifest typing is additive-friendly

[PilotRefreshManifest](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/pilot/contracts.py#L261) already carries:

- `comparison_summary`
- `output_artifacts`
- `policy_version_evaluated`
- `artifact_qa_status`
- `comparison_is_canonical`

Phase 52 can either:

- keep the new profile-selection fields inside `comparison_summary`, or
- promote them to first-class typed fields if readability and QA contracts improve

Both fit the existing design; no new manifest family is required.

### 5. Existing tests already cover the right blast radius

The current test suite already divides naturally across the Phase 52 work:

- [test_decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_decision_calibration.py): deterministic selector, non-adoption reasons, shared-runtime-baseline contract
- [test_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_customer_artifact_collection.py): new calibration artifacts, manifest fields, summary sections
- [test_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_pilot_baseline_refresh.py): proof docs, refresh summary propagation, manifest compatibility
- [test_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_pilot_artifact_qa.py): missing-artifact and inconsistent-field failures or degradations
- [test_phase_experiment_suite.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_phase_experiment_suite.py) and [test_recourse_funnel_kpis.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_recourse_funnel_kpis.py): three-cohort rerun compatibility and unchanged funnel/trust evidence coexistence

## What Phase 52 Must Deliver

### 1. One canonical baseline-selection owner

The owner should live in [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py) and emit:

- `preferred_demo_profile`
- `fallback_demo_profile`
- selected runtime policy version
- baseline selection reason
- threshold family promotion status
- outcome-rule family promotion status
- candidate disposition rows
- current next-milestone focus label

### 2. One explicit candidate disposition table

Phase 52 should make every prior candidate readable in one place:

- threshold family rows
- outcome-rule family rows
- status
- why not adopted
- whether movement was created
- whether a guardrail blocked adoption

This is the artifact that turns prior negative results into reusable demo evidence rather than scattered history.

### 3. Preferred and fallback profiles must be packaging profiles, not runtime policy forks

The research strongly supports this contract:

- preferred profile = full evidence appendix over the shipped live baseline
- fallback profile = narrower trust-first proof over the same shipped live baseline

Why this is the right design:

- it matches the Phase `49-51` evidence
- it satisfies the roadmap’s “preferred + fallback” requirement honestly
- it avoids inventing a fake promoted policy when both candidate families ended `no_safe_uplift`

### 4. Demo proof must include claim discipline

The demo package should explicitly separate:

- what the current evidence supports
- what the current evidence does not support
- what the next milestone needs to solve

That should be rendered as first-class output, not hidden in planner notes.

### 5. The next-milestone handoff should be part of the package

Phase 52 is the closeout phase for `v2.3`, so the handoff should not be an afterthought. It should state:

- why bounded threshold and outcome-rule families were not adopted
- why the current bottleneck is structural under the current action/signal envelope
- why the next milestone should not simply retry the same bounded families

## Validation Architecture

The existing verification seams are already strong enough:

- [test_decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_decision_calibration.py) for deterministic baseline selection, preferred/fallback profile labels, and candidate disposition logic
- [test_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_customer_artifact_collection.py) for collection artifact creation, manifest propagation, and summary-section packaging
- [test_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_pilot_baseline_refresh.py) for proof-doc rendering and refresh summary compatibility
- [test_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_pilot_artifact_qa.py) for presence, consistency, and failure/degraded behavior when Phase 52 artifacts are missing
- [test_phase_experiment_suite.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_phase_experiment_suite.py) and [test_recourse_funnel_kpis.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_recourse_funnel_kpis.py) for compatibility with deterministic rerun evidence on the standard cohorts

One manual review still adds value after execution:

- confirm `demo_policy_proof.md` is quotable in a demo without implying a promoted uplift
- confirm `next_milestone_handoff.md` does not smuggle new scope into Phase 52

## Recommended Plan Shape

The cleanest split is:

1. `52-01` — implement the baseline-selection owner and candidate-disposition contract in [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py)
2. `52-02` — package the new selection truth into [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py), [run_pilot_baseline_refresh.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_baseline_refresh.py), [run_pilot_artifact_qa.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_pilot_artifact_qa.py), and typed pilot contracts as needed
3. `52-03` — extend regression protection and run the three standard cohorts so the final artifact bundle proves the same honest preferred-baseline story across deterministic reruns

Phase 52 is successful if the repo ends with one preferred baseline story, one fallback story, explicit reasons the bounded candidates were not adopted, and a clean next-step package for the next milestone, all without pretending Phase `49-51` found a safe promoted uplift.
