# Phase 56: DICE Action Space Expansion - Research

**Researched:** 2026-04-04
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest safe implementation that expands the DICE lane beyond the old implicit actionable-feature seam, while preserving Phase 46 contender-quality rules and the v2.2 trust baseline?

## Planning Basis

Phase 56 decisions were discussed in-session and are now locked in [56-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/56-dice-action-space-expansion/56-CONTEXT.md). The authoritative inputs for this planning pass are:

- [PROJECT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/PROJECT.md)
- [ROADMAP.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/ROADMAP.md)
- [REQUIREMENTS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/REQUIREMENTS.md)
- [STATE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/STATE.md)
- [46-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/46-dice-lane-validity-enforcement/46-CONTEXT.md)
- [46-VERIFICATION.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/46-dice-lane-validity-enforcement/46-VERIFICATION.md)
- [55-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/55-feature-action-mapping/55-CONTEXT.md)
- [action_space.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/action_space.py)
- [dice_baseline.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/dice_baseline.py)
- [dice_quality.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/dice_quality.py)
- [generator.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/generator.py)
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py)
- [schema.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py)

## Executive Summary

Phase 56 should be planned as a **DICE-runtime contract expansion**, not as a planner or policy phase.

The safest implementation shape is:

`DICE-specific allowlist and serialization bridge -> grouped/categorical generation rules -> semantic-quality hardening -> trust-baseline regression proof`

The code scan shows six important truths:

1. DICE still uses the broad `get_actionable_features()` seam in [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py), so the current lane contract is wider and less explicit than Phase 56 needs
2. Phase 55 mapping metadata is rich enough to drive a DICE-specific runtime contract, but there is no helper yet that exposes "DICE-generatable" separately from "globally actionable"
3. Support-mapped features such as `term` still do not carry a live `action_key`, so they cannot be serialized through the current canonical builder without an additive bridge
4. The current DICE extraction path in [dice_baseline.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/dice_baseline.py) assumes float-style deltas, which is not enough for grouped-support or categorical / verification-style actions
5. Phase 46 already provides the correct annotation-completeness and contender-quality owner in [dice_quality.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/dice_quality.py); Phase 56 should extend that gate, not replace it
6. The trust-baseline proof surface already exists in tests for winner integrity, selected surface consistency, operator packet coherence, and customer artifact parity

## Concrete Repo Findings

### 1. Current DICE runtime eligibility is tied to the wrong seam

[run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py) currently does:

- `actionable = set(get_actionable_features())`
- passes `sorted(actionable)` into `generate_dice_counterfactual_actions(...)`

This happens in both DICE entry points. That means DICE runtime eligibility is still inherited from the broad internal actionability contract rather than a Phase 56-specific safe set.

Planning implication:
- Phase 56 needs a dedicated helper such as `get_dice_generatable_features()` or a richer `list_dice_generation_contract()` and must route DICE through it.

### 2. Phase 55 mapping metadata is present, but not yet runtime-usable for support-only DICE features

[action_space.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/action_space.py) now exposes:

- `mapping_status`
- `mapping_action_key`
- `non_actionable_reason`
- feature-level coverage helpers

However, support-mapped features such as `term` have:

- `mapping_action_key="refinance"`
- `action_key=None`
- `actionable=False`

The current canonical serialization path still relies on `action_key`, not `mapping_action_key`, when building action metadata and numeric-target metadata.

Planning implication:
- Phase 56 needs an additive DICE-specific serialization bridge for mapped-but-not-globally-actionable features.
- This should not widen the global internal `actionable=True` behavior.

### 3. Current template `dice_eligible` flags do not match the planned first-wave rollout

In [action_space.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/action_space.py), `dice_eligible=True` is currently only set on:

- `credit_limit_adjustment`
- `settlement_discount`
- `installment_plan`

But the Phase 56 first-wave rollout is intentionally:

- `adjust_requested_loan_amount`
- `refinance`
- `verify_income_documentation`
- `installment_plan`

Planning implication:
- Phase 56 must either update canonical action-template `dice_eligible` truth or introduce a rollout-specific runtime layer that is explicit and conservative.
- The important rule is that runtime rollout must still be owned explicitly and not be derived from a vague global heuristic.

### 4. DICE extraction currently assumes numeric float deltas

[dice_baseline.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/dice_baseline.py) currently:

- casts `current = float(base[feat])`
- casts `target = float(cf_row[feat])`
- compares them numerically
- emits only `{feature_name, current_value, target_value}` numeric action dicts

This is fine for numeric features, but it is too narrow for:

- categorical / ordered-state features such as `verification_status`
- grouped support features that should not stand alone

Planning implication:
- Phase 56 needs explicit grouped and categorical extraction rules before those features can be safely activated.

### 5. Shared canonical action build path already exists and should be reused

[run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py) already uses [build_canonical_plan_action(...)](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/generator.py) inside `_dice_plan_record(...)`.

That is a strong starting point because:

- brownfield `action_class` / `action_family` compatibility is already emitted from the canonical seam
- primary numeric targets are already built centrally
- feasibility, constraints, validity, execution, and trajectory flows are already shared

Planning implication:
- Phase 56 should extend this shared builder path rather than creating a second DICE-only action serializer.

### 6. Phase 46 quality gates are already the right owner for trust preservation

[dice_quality.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/dice_quality.py) already enforces:

- annotation completeness
- semantic quality
- contender eligibility
- warning penalties

It also already treats missing primary numeric target as a hard semantic failure.

Planning implication:
- Phase 56 should add new invalid cases here for:
  - support-only orphan candidates
  - grouped actions missing the primary target feature
  - ambiguous categorical transitions
- This preserves the Phase 46 ownership model instead of inventing a new gate.

## What Phase 56 Must Deliver

### 1. A DICE-specific runtime contract

Phase 56 must define one explicit safe-set contract for DICE generation that is separate from the global actionable seam.

### 2. A bridge for mapped-but-not-globally-actionable DICE features

Support features such as `term` need additive canonical serialization support driven by Phase 55 mapping metadata.

### 3. Grouped and categorical generation rules

Phase 56 must explicitly support:

- grouped refinance actions where `term` cannot stand alone
- categorical / verification-style actions for `verification_status`
- delinquency actions anchored by `delinq_amnt`

### 4. Trust-baseline regression proof

Expanded DICE generation must still preserve:

- winner integrity
- DICE contender quality
- selected-surface consistency
- operator packet coherence

## Recommended Plan Shape

The cleanest split is:

1. `56-01` — DICE runtime contract plus mapped-feature serialization bridge
2. `56-02` — grouped/categorical DICE generation and semantic-quality hardening
3. `56-03` — trust-baseline regression and artifact parity proof

## Validation Architecture

Validation should prove both runtime expansion and trust preservation:

1. Contract correctness
- DICE uses a dedicated runtime allowlist instead of the broad global actionable seam
- mapped support features can resolve canonical metadata without widening internal actionability

2. Generation safety
- grouped support features cannot become stand-alone contenders
- `verification_status` can serialize deterministically
- delinquency support features only rank with their primary action anchor

3. Trust preservation
- selected surfaces remain coherent
- operator packets stay consistent
- DICE winners remain eligible and clean
- `no_valid_winner` integrity remains intact when expanded DICE candidates are rejected

Recommended commands:

- Quick: `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_dice_baseline.py tests/test_dice_baseline_direction.py tests/test_dice_lane_validity_enforcement.py -q`
- Full: `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_dice_baseline.py tests/test_dice_baseline_direction.py tests/test_dice_lane_validity_enforcement.py tests/test_recourse_redesign.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py tests/test_winner_integrity_hard_stop.py tests/test_customer_artifact_collection.py -q`

## RESEARCH COMPLETE
