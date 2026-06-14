# Phase 46: Dice Lane Validity Enforcement - Research

**Researched:** 2026-03-26
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest safe implementation that makes the `dice` lane obey the same typed-action and contender-quality contract as internal plans, without reopening winner hard-stop, decision ownership, or approval thresholds?

## Planning Basis

Phase 46 decisions were discussed in-session and are now locked in [46-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/46-dice-lane-validity-enforcement/46-CONTEXT.md). For this planning pass the authoritative inputs are:

- [PROJECT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/PROJECT.md)
- [ROADMAP.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/ROADMAP.md)
- [REQUIREMENTS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/REQUIREMENTS.md)
- [STATE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/STATE.md)
- [45-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/45-winner-integrity-hard-stop/45-CONTEXT.md)
- [46-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/46-dice-lane-validity-enforcement/46-CONTEXT.md)
- [generator.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/generator.py)
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py)
- [dice_baseline.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/dice_baseline.py)
- [recommendation_validity.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/recommendation_validity.py)
- [planner.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/planner.py)
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py)
- [schema.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py)

This is sufficient because the repo already has:

- deterministic decision ownership from Phase 40.5
- additive calibration and collection rollups from Phase 41
- planner-quality and source-mix semantics from Phase 42
- canonical recommendation validity taxonomy from Phase 42.5
- winner hard-stop and explicit `no_valid_winner` semantics from Phase 45

The missing layer is no longer winner prevention. The missing layer is **DICE lane parity, semantic contender quality, and lane-specific eligibility proof**.

## Executive Summary

Phase 46 should be planned as a **lane-quality enforcement phase**, not as a planner or threshold phase.

The safest shape is:

`shared action normalization parity -> DICE quality annotation -> contender-eligibility split -> DICE-specific artifact proof -> rerun evidence`

The code scan shows five important truths:

1. [generator.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/generator.py) already owns the canonical internal action build path, but [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py) still builds DICE actions through a separate ad-hoc constructor
2. [recommendation_validity.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/recommendation_validity.py) is working and should remain untouched; Phase 46 needs a separate DICE-quality truth, not a new validity taxonomy
3. [dice_baseline.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/dice_baseline.py) already exposes enough provenance to distinguish native DICE from heuristic fallback, but that provenance is not yet first-class planner or collection truth
4. Phase 45 guarantees invalid winners cannot survive selection, but it does not yet distinguish visible DICE diagnostics from planner-eligible DICE contenders
5. [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) already has the right pattern for source-mix and validity aggregates, so Phase 46 can extend that surface with DICE-specific eligibility and fallback proof

## Concrete Repo Findings

### 1. DICE currently diverges from the canonical action contract

Internal plans in [generator.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/generator.py) go through:

- typed action construction
- `primary_numeric_target`
- feasibility
- constraints
- validity
- execution probability
- trajectory
- offer annotation

DICE plans in [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py) still construct `PlanAction` records manually in `_dice_plan_record(...)`. They do gain feasibility, constraints, validity, execution, trajectory, and offer annotation later, but the typed action contract is not clearly owned by the same builder.

That means Phase 46 must converge DICE action normalization onto a shared owner rather than leaving a lane-local typed contract.

### 2. Validity and semantic contender-worthiness are not the same

Phase 42.5 already answers:

- is the numeric recommendation directionally safe?
- is it a no-op?
- is it economically implausible?

Phase 46 must answer a different question:

- is this DICE recommendation complete, readable, renderable, and contender-worthy enough to compete with internal plans?

This is why a separate DICE semantic-quality layer is required.

### 3. Heuristic fallback already exists and should be modeled as provenance

[dice_baseline.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/dice_baseline.py) already returns:

- requested method
- used method
- fallback reason
- attempted methods

That means Phase 46 does not need to invent DICE provenance. It needs to lock the vocabulary and propagate it into artifact truth:

- `native`
- `heuristic_fallback`
- `skipped`

### 4. Candidate visibility and planner eligibility are currently the same thing

Today, DICE records are added into the candidate pool and only later constrained by general validity and empty-contender logic. There is no explicit split between:

- DICE candidates that remain visible for diagnostics
- DICE candidates that are truly eligible to enter planner contention

Phase 46 must make that split first-class.

### 5. Phase 45 provides the exact proof pattern to reuse

Phase 45 already established:

- additive raw/flat integrity diagnostics
- collection summary aggregates
- three-cohort rerun proof across:
  - `pilot_mixed`
  - `risk_band_balanced`
  - `offer_needed_balanced`

Phase 46 should reuse that proof posture, but with DICE-specific metrics:

- eligible rate
- invalid rate
- warning rate
- fallback rate
- all-ineligible rate
- selected-DICE-valid rate

## What Phase 46 Must Deliver

### 1. Shared DICE action normalization parity

The DICE lane must stop constructing a semi-independent typed action contract. It should converge onto the same minimum action contract internal plans already rely on.

### 2. A separate DICE quality annotator

This annotator must classify DICE candidates by:

- annotation completeness
- semantic contender-worthiness
- contender eligibility
- DICE-specific warning penalty

without changing the existing recommendation validity taxonomy.

### 3. A visible-versus-eligible lane split

All DICE candidates should remain visible in diagnostics, but only DICE candidates that satisfy the full gate should enter planner contention.

### 4. DICE-specific artifact proof

The raw, flat, and collection layers must expose enough first-class DICE truth that reruns can answer:

- did DICE generate anything?
- were those candidates complete?
- were they contender-eligible?
- did selected DICE winners stay clean?

## Validation Architecture

Phase 46 needs one new dedicated test seam plus regression coverage across existing DICE, recourse, and collection suites:

- new dedicated DICE-lane-enforcement module
- DICE baseline and direction tests for backend/fallback provenance
- recourse and collection integration tests for candidate visibility versus contender eligibility
- three-cohort rerun proof to confirm that any selected DICE winner remains fully eligible and semantically valid

## Recommended Plan Shape

The cleanest split is:

1. `46-01` — shared DICE normalization parity plus DICE semantic-quality annotation
2. `46-02` — DICE contender eligibility split and raw/flat/collection propagation
3. `46-03` — regression closure and rerun proof for DICE lane cleanliness

