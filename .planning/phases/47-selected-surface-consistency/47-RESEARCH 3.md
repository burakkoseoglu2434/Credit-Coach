# Phase 47: Selected Surface Consistency - Research

**Researched:** 2026-04-01
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest safe implementation that makes selected plan rows, external decision summaries, collection metrics, operator packets, and explanation packs describe one coherent selected winner without reopening decision ownership, winner hard-stop, or operator-packet semantics?

## Planning Basis

Phase 47 decisions were discussed in-session and are now locked in [47-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/47-selected-surface-consistency/47-CONTEXT.md). For this planning pass the authoritative inputs are:

- [PROJECT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/PROJECT.md)
- [ROADMAP.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/ROADMAP.md)
- [REQUIREMENTS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/REQUIREMENTS.md)
- [STATE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/STATE.md)
- [45-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/45-winner-integrity-hard-stop/45-CONTEXT.md)
- [46-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/46-dice-lane-validity-enforcement/46-CONTEXT.md)
- [47-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/47-selected-surface-consistency/47-CONTEXT.md)
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py)
- [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py)
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py)
- [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py)
- [decision_explanation_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/decision_explanation_pack.py)
- [test_recourse_redesign.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_recourse_redesign.py)
- [test_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_customer_artifact_collection.py)
- [test_operator_review_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_operator_review_pack.py)
- [test_decision_explanation_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_decision_explanation_pack.py)

This is sufficient because the repo already has:

- deterministic external decision ownership from Phase 40.5
- explicit `no_valid_winner` selection semantics from Phase 45
- DICE contender cleanliness from Phase 46
- derived operator packet and explanation pack consumers from Phases 43 and 44

The missing layer is no longer winner validity or DICE quality. The missing layer is **selected-surface coherence**.

## Executive Summary

Phase 47 should be planned as a **selected-truth projection and drift-guard phase**, not as an operator UX or threshold phase.

The safest shape is:

`selected overlay contract -> explicit empty-state contract -> flat/operator/explanation propagation -> drift guards -> rerun proof`

The code scan shows five important truths:

1. [ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py) already owns consumer-safe `decision_status` and `expected_readiness`, so Phase 47 should project from that owner rather than invent a second consumer truth
2. [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py) still carries both technical selected-plan status and decision-owned status in the same roadmap summary, but it does not yet define a first-class selected-surface overlay
3. [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) correctly writes `selected_best_flag`, but selected rows do not yet carry a consumer-safe selected decision projection, so external `CONDITIONAL` can still point at a raw selected technical `REJECTED` row
4. [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py) and [decision_explanation_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/decision_explanation_pack.py) both read recommendation text from narrative steps, but they do not yet consume one explicit selected recommendation projection contract
5. Phase 45 and Phase 46 already established the correct proof posture: additive raw/flat fields plus collection-level acceptance proof across the three 250-customer rerun cohorts

## Concrete Repo Findings

### 1. The external decision owner is already consumer-safe

[ownership.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/decision/ownership.py) computes:

- `decision_status`
- `decision_status_internal`
- `expected_readiness`
- `decision_reason_summary`
- `upgrade_condition`

and already clamps problematic readiness outputs for rejected or unknown-review states.

That means Phase 47 should not redesign decision semantics. It should **project selected surfaces from the decision owner explicitly**.

### 2. `run_recourse.py` is the main selected-surface assembly seam

[run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py) currently:

- writes technical selected-plan truth like `best_plan_id`, `best_status`, and `best_constraint_status`
- applies decision ownership into `summary`
- builds narrative steps from the normalized summary and plan

This is exactly where a selected-surface overlay should be introduced. The phase does not need a new owner; it needs a **canonical projection layer**.

### 3. `customer_plans.csv` is still technical-first

[run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) inserts:

- `selected_best_flag`
- `selection_outcome`
- `selection_stage`
- `plan_contract_pass`

but selected plan rows remain primarily technical plan rows. That is acceptable for raw diagnostics, but Phase 47 needs a consumer-safe overlay so flat artifacts can answer:

- what was technically selected?
- what is the selected consumer truth?

without requiring downstream guesswork.

### 4. Operator packet and explanation pack still consume recommendation text indirectly

[operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py) still falls back from `primary_recommendation` to `action_summary`.

[decision_explanation_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/decision_explanation_pack.py) builds its own recommendation projection from narrative steps and only later drift-checks against operator packet.

That means Phase 47 should not allow freeform fallback anymore. Both surfaces need one **selected recommendation projection** contract.

### 5. `no_valid_winner` is already safe enough to extend

Phase 45 already made `no_valid_winner` explicit at selection time. Phase 47 can extend that into a consumer-safe empty-state contract without reopening chooser logic:

- no best plan
- no selected row
- no selected recommendation text
- explicit empty-state output

This is a clean extension, not a redesign.

## What Phase 47 Must Deliver

### 1. A first-class selected-surface overlay

The phase should explicitly separate:

- technical selected plan truth
- consumer-safe selected decision truth

so external decision and selected consumer surface cannot drift.

### 2. One owner for selected recommendation projection

The system should emit:

- `selected_recommendation_text`
- `selected_recommendation_source`
- `selected_action_count`
- `selected_recommendation_projection_version`

and downstream surfaces should consume those fields rather than recomputing recommendation text independently.

### 3. A strict `no_valid_winner` empty-state contract

`no_valid_winner` must become a real selected-surface empty state, not a generic recommendation fallback state.

### 4. A drift-guard field set with rerun-proof metrics

Phase 47 needs first-class consistency checks for:

- `best_plan_id`
- `best_plan_source`
- `selection_outcome`
- `selection_stage`
- `decision_status`
- `expected_readiness`
- `selected_decision_status`
- `selected_recommendation_text`
- `selected_action_count`

## Validation Architecture

Phase 47 needs one new dedicated test seam plus extensions to recourse, collection, operator-packet, and explanation-pack tests:

- a new selected-surface-consistency test module
- recourse tests for overlay and empty-state projection
- collection tests for selected-row versus selected-decision parity
- operator and explanation tests for shared selected recommendation projection
- three-cohort rerun proof to confirm there are no external `CONDITIONAL -> selected technical REJECTED` consumer leaks

## Recommended Plan Shape

The cleanest split is:

1. `47-01` — selected overlay contract plus explicit `no_valid_winner` empty-state projection
2. `47-02` — raw/flat/operator/explanation propagation and shared selected recommendation projection
3. `47-03` — drift-guard regression closure and three-cohort rerun proof for selected-surface consistency

