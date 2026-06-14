# Phase 57: Heuristic / Institution Action Lane - Research

**Researched:** 2026-04-04
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest safe implementation that adds institution and hybrid action candidates to the shared contender pool, while preserving the v2.2 trust baseline and avoiding planner redesign?

## Planning Basis

Phase 57 decisions were discussed in-session and are now locked in [57-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/57-heuristic-institution-action-lane/57-CONTEXT.md). The authoritative inputs for this planning pass are:

- [PROJECT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/PROJECT.md)
- [ROADMAP.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/ROADMAP.md)
- [REQUIREMENTS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/REQUIREMENTS.md)
- [STATE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/STATE.md)
- [56-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/56-dice-action-space-expansion/56-CONTEXT.md)
- [action_space.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/action_space.py)
- [generator.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/generator.py)
- [offer_optimization.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/offer_optimization.py)
- [recommendation_validity.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/recommendation_validity.py)
- [planner.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/planner.py)
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py)
- [schema.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py)
- [messaging.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/messaging.py)
- [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py)

## Executive Summary

Phase 57 should be planned as a **deterministic rule-source expansion layer**, not as a planner or policy phase.

The safest implementation shape is:

`first-wave institution/hybrid generation contract -> shared PlanAction/offer serialization -> heuristic-lane quality and contender gating -> trust-surface regression proof`

The code scan shows six important truths:

1. The canonical action catalog already contains the right first-wave institution and hybrid actions, including approval and offer metadata
2. The shared canonical action builder and nested `OfferContract` seam already exist, so Phase 57 can reuse serialization rather than inventing a sidecar artifact model
3. The planner already supports the right contender buckets and source types, especially `rule` and `APPROVAL_SHELL_ONLY`, so Phase 57 does not need planner logic changes to integrate new candidates
4. Offer readiness, provisionality, and maturity are already represented in the repo and should be reused as the truth source for `offer_feasibility`
5. Customer and operator surfaces already render `institution_condition` separately from `primary_recommendation`, which is exactly the trust-preserving UX Phase 57 needs
6. The missing piece is not downstream support; it is a deterministic generator plus a lane-equivalent semantic-quality gate for institution/hybrid candidates before they enter contention

## Concrete Repo Findings

### 1. The canonical first-wave institution actions already exist

[action_space.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/action_space.py) already defines:

- `credit_limit_adjustment`
- `debt_consolidation`
- `settlement_discount`
- `installment_plan`

and those templates already carry:

- `action_owner`
- `requires_institutional_approval`
- `institutional_approval_state`
- `offer_type`
- `offer_family`
- `offer_scoring_profile`
- `term_generation_rule`
- `offer_policy_arm`
- `prerequisite_tags`
- `conflict_tags`

Planning implication:
- Phase 57 should not create a parallel taxonomy. It should reuse the Phase 54/55 canonical actions and make them generatable outside the DICE lane.

### 2. The shared canonical builder is already strong enough to stay central

[generator.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/generator.py) already provides:

- `build_canonical_plan_action(...)`
- primary numeric target generation
- canonical action metadata lookup
- nested offer-contract construction
- recommendation-validity annotation
- constraint, feasibility, and trajectory handoff

Planning implication:
- Phase 57 should add a deterministic institution/hybrid candidate generator that feeds the existing canonical builder instead of inventing a new action serializer.

### 3. The planner already has the right source and bucket semantics

[planner.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/planner.py) already supports:

- `canonical_plan_source()` with `internal`, `dice`, `rule`, `fallback`
- `classify_plan_contender()`
- `APPROVAL_SHELL_ONLY`
- `offer_maturity`
- `filter_empty_contenders(...)`

Planning implication:
- the new heuristic institution lane should enter the pool as `plan_source="rule"`
- approval-dependent shells can remain visible using the already-existing `APPROVAL_SHELL_ONLY` behavior
- no planner ranking redesign is necessary

### 4. Offer readiness and provisionality are already modeled

[offer_optimization.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/offer_optimization.py) already exposes:

- `offer_contract_for_action(...)`
- `approval_state_for_action(...)`
- `is_rankable_offer_action(...)`
- `is_provisional_offer_action(...)`
- `annotate_offer_optimization(...)`

The repo already distinguishes:

- active/rankable offers
- pending/unknown/provisional offers
- non-offer actions

Planning implication:
- `offer_feasibility` in Phase 57 should align with existing offer-maturity / approval truth rather than inventing a separate fuzzy status system
- rule-generated institution actions can be either:
  - fully rankable
  - provisional but visible
  - inactive and therefore non-contender

### 5. Recommendation validity already protects institution-role honesty

[recommendation_validity.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/recommendation_validity.py) already enforces:

- directional numeric sanity
- bounded target warnings
- `customer_institution_mislabel`

Planning implication:
- Phase 57 should reuse the same validity layer and only add heuristic-lane semantics where institution truth, offer completeness, or approval shells need stronger handling

### 6. Downstream selected-surface and operator-packet support already exists

[messaging.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/messaging.py) and [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py) already support:

- separate `primary_recommendation`
- separate `institution_condition`
- offer-state messaging
- selected-surface projection of `selected_institution_condition`
- operator-packet rendering for institution conditions

Planning implication:
- Phase 57 is mostly a generation-and-contract problem
- downstream rendering should need only additive projection fixes, not a redesign

## What Phase 57 Must Deliver

### 1. A deterministic heuristic institution runtime contract

Phase 57 must define one explicit first-wave contract for:

- `credit_limit_adjustment`
- `debt_consolidation`
- `settlement_discount`
- `installment_plan`

including:

- trigger conditions
- primary-target anchors
- do-not-generate exclusions
- approval / offer semantics

### 2. Shared PlanAction and offer serialization for institution truth

Phase 57 must carry or derive:

- `offer_required_flag`
- `institution_condition`
- `offer_feasibility`

without creating a disconnected action model.

### 3. A heuristic-lane quality and contender gate

The new lane must have an equivalent to DICE semantic-quality enforcement so that institution/hybrid actions do not enter contention unless they are:

- annotation-complete
- role-correct
- offer-complete when required
- truthful about approval state
- renderable on the selected and operator surfaces

### 4. Trust-baseline regression proof

Expanded candidate generation must still preserve:

- winner integrity
- selected-surface consistency
- operator packet coherence
- DICE quality enforcement

## Recommended Plan Shape

The cleanest split is:

1. `57-01` — heuristic institution lane contract, first-wave generator, and offer/feasibility action contract
2. `57-02` — rule-source pool integration, heuristic-lane quality gate, and contender eligibility
3. `57-03` — customer/operator rendering alignment and trust-baseline regression proof

## Validation Architecture

Validation should prove both generation correctness and trust preservation:

1. Contract correctness
- first-wave institution/hybrid triggers are deterministic
- generated actions serialize through canonical `PlanAction`
- `offer_required_flag`, `institution_condition`, and `offer_feasibility` are truthful

2. Pool and gate correctness
- heuristic institution candidates enter as `rule` plans
- approval shells stay visible but do not bypass contention rules
- fully actionable institution candidates can compete without planner changes

3. Trust preservation
- selected-surface projection remains coherent
- operator packets remain coherent
- `no_valid_winner` integrity remains intact
- DICE quality enforcement remains unchanged for DICE candidates

Recommended commands:

- Quick: `cd credit-coach && python -m pytest tests/test_heuristic_institution_lane.py tests/test_planner_quality_source_mix.py tests/test_recourse_redesign.py tests/test_messaging.py -q`
- Full: `cd credit-coach && python -m pytest tests/test_heuristic_institution_lane.py tests/test_planner_quality_source_mix.py tests/test_recourse_redesign.py tests/test_messaging.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py tests/test_winner_integrity_hard_stop.py tests/test_customer_artifact_collection.py tests/test_dice_lane_validity_enforcement.py -q`

## RESEARCH COMPLETE
