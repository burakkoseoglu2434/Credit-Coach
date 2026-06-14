# Phase 30: Action Semantics Hardening - Research

**Researched:** 2026-03-20
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What must change so the recourse engine stops expressing recommendations as raw feature deltas and instead emits a deterministic, typed, grouped, and product-safe action contract?

## Planning Basis

Phase 30 now has a locked `30-CONTEXT.md`. For this planning pass the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/12-action-realism-feasibility-expansion/12-CONTEXT.md`
- `.planning/phases/18-decision-narrative-product-output-translation/18-CONTEXT.md`
- `.planning/phases/30-action-semantics-hardening/30-CONTEXT.md`
- `credit-coach/src/credit_coach/recourse/action_space.py`
- `credit-coach/src/credit_coach/data/schema.py`
- `credit-coach/src/credit_coach/cli/run_recourse.py`
- `credit-coach/src/credit_coach/coaching/messaging.py`
- `credit-coach/src/credit_coach/recourse/generator.py`
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- `credit-coach/tests/test_action_space.py`
- `credit-coach/tests/test_recourse_redesign.py`
- `credit-coach/tests/test_messaging.py`
- `credit-coach/tests/test_batch_candidate_diversity.py`

This is sufficient because Phase 30 is not inventing semantics from scratch. The repo already has:

- a typed action catalog seam in `recourse/action_space.py`
- a feature-level plan record seam in `data/schema.py`
- serialization and roadmap emission in `cli/run_recourse.py`
- a prior technical-reveal pattern in `coaching/messaging.py`
- regression coverage for typed actions and roadmap structure in `tests/test_action_space.py` and `tests/test_recourse_redesign.py`

The remaining gap is not “whether semantics exist at all,” but whether they are hard enough to serve as the canonical action contract for the new milestone.

## Executive Summary

The codebase already contains the basic ingredients for action semantics:

- `ACTION_CATALOG` already maps action keys to real-world titles and classes
- `ACTION_SPACE` already maps actionable features into typed action specs
- `derive_action_group_id()` already gives composite actions a stable shared identity
- roadmap narrative already preserves technical detail through `technical_reveal`

What is still missing is the Phase 30 contract:

1. `action_family` does not yet exist as a canonical second taxonomy layer
2. feature-to-action mapping is mostly present, but not yet enforced as a hard no-fallback contract
3. grouped semantics are still month-oriented and not yet explicitly locked to `action_key + phase`
4. `PlanAction` remains feature-centric instead of clearly splitting `business_view` from `technical_view`
5. `run_recourse.py` still serializes `feature_name`, `current_value`, and `target_value` in the same visible step rows that product consumers use

Phase 30 should therefore be planned as a focused contract hardening pass:

`catalog truth -> grouped action truth -> business-safe serialized truth`

## Existing Assets We Can Reuse

### Action catalog seam already exists

- `credit-coach/src/credit_coach/recourse/action_space.py`
  - already defines:
    - `ActionClass`
    - `ActionTemplate`
    - `ActionSpec`
    - `ACTION_CATALOG`
    - `ACTION_SPACE`
  - already carries:
    - `action_key`
    - `action_class`
    - deterministic catalog titles
    - grouped composite intent through shared templates

This is the correct seam for:

- adding canonical `action_family`
- enforcing one primary action per actionable feature
- rejecting unmapped actionable features
- locking deterministic catalog-driven titles and descriptions

### Grouped action helper already exists

- `derive_action_group_id()` in `action_space.py`
  - already provides deterministic grouping
  - currently derives group identity from `action_key` plus month

This is the right seam for:

- shifting grouped identity to the new `action_key + phase` posture
- keeping grouped actions visible as one main action
- preserving low-level effect traceability behind the grouped layer

### Schema seam already exists but is too feature-centric

- `credit-coach/src/credit_coach/data/schema.py`
  - `PlanAction` currently exposes:
    - `feature_name`
    - `current_value`
    - `target_value`
    - `delta`
    - `action_key`
    - `action_class`
    - `action_title`
    - `action_group_id`

This is the correct seam for:

- adding explicit schema-level `business_view`
- adding explicit schema-level `technical_view`
- ensuring top-level semantic identity no longer depends on `feature_name`

### Serialization seam already exists and currently leaks raw technical detail

- `credit-coach/src/credit_coach/cli/run_recourse.py`
  - already assembles `PlanAction`
  - already serializes roadmap and customer-facing artifacts
  - still makes top-level action rows readable as feature deltas

This is the correct seam for:

- default serialized identity:
  - `action_key`
  - `action_family`
  - `action_class`
  - `action_title`
  - `action_group_id`
- moving `feature_name` and raw effect anchors fully into the technical layer
- making grouped semantic actions the default visible contract

### Technical reveal precedent already exists

- `credit-coach/src/credit_coach/coaching/messaging.py`
  - already separates default narrative from `technical_reveal`
  - already preserves feature-level traceability

This is the right precedent for:

- enforcing business-vs-technical separation at schema level
- making sure product-facing outputs stay semantic by default
- keeping feature-level effect anchors available only on demand

## What Phase 30 Must Deliver

### 1. Locked taxonomy and mapping contract

Phase 30 must finalize:

- top-level action taxonomy:
  - `behavioral`
  - `structural`
  - `institutional`
- canonical second layer:
  - `action_family`
- exactly one primary action per actionable feature
- hard failure for actionable features with no canonical mapping

No fallback generic action and no raw feature recommendation in the default contract.

### 2. Deterministic grouped-action contract

Phase 30 must lock:

- same primary action + same phase -> one grouped visible action
- `action_group_id` derived from:
  - `action_key + phase`
- no cross-class grouping
- grouped supporting effects visible only in technical view

### 3. Product-safe serialization identity

The default serialized action identity must be:

- `action_key`
- `action_family`
- `action_class`
- `action_title`
- `action_group_id`

`feature_name` must stop being part of the main semantic action identity.

### 4. Explicit business vs technical separation

The contract must become explicit rather than implied:

- `business_view`
- `technical_view`

This split should be engine-owned and machine-readable so downstream consumers do not invent their own interpretation.

## Recommended Plan Split

### Plan 30-01 — Catalog and mapping hardening

Focus on:

- adding `action_family` to the canonical action catalog
- enforcing one primary action per actionable feature
- hard-failing unmapped actionable features
- keeping titles and descriptions fully catalog-driven and deterministic

### Plan 30-02 — Grouped action and serialization contract

Focus on:

- shifting grouped identity to deterministic `action_key + phase`
- introducing an explicit semantic action identity
- moving feature anchors into a technical/effect layer
- making `PlanAction` and recourse serialization business-safe by default

### Plan 30-03 — Downstream contract alignment and regression closure

Focus on:

- making roadmap and narrative consumers read semantic actions by default
- preserving sub-effects only in `technical_reveal`
- aligning batch and engine-side downstream consumers to the new grouped contract
- locking regression coverage across behavioral, structural, and institutional cases

## Main Risks

### Risk 1: Catalog hardens but runtime serialization still leaks feature-first rows

If `action_space.py` is hardened but `run_recourse.py` still emits raw feature identity at top level, product consumers will not feel the benefit of Phase 30.

Mitigation:

- treat serialization as core scope, not follow-up cleanup

### Risk 2: Grouping becomes visually cleaner but less traceable

If grouped actions collapse multiple effects without a proper technical view, later phases lose auditability.

Mitigation:

- grouped business view by default
- full effect anchors preserved in technical view

### Risk 3: Unmapped actionable features remain silently tolerated

If the engine still allows semantic fallbacks, the milestone foundation remains soft and raw feature leakage comes back later.

Mitigation:

- explicit hard-fail behavior for unmapped actionable features
- regression tests that assert no raw fallback is allowed

### Risk 4: Business and technical views drift across engine consumers

If separation is implemented only in one surface, the contract will fork.

Mitigation:

- encode separation at schema level
- make downstream engine consumers use the same contract

## Recommendation

Proceed with Phase 30 now. The repo already has the right catalog, grouping, serialization, and narrative seams. The correct move is to harden them into one deterministic action contract before Phase 31 starts generating numeric targets on top of unstable semantics.

## Validation Architecture

Phase 30 has enough existing pytest coverage to stay Nyquist-compliant without introducing a new framework:

- `tests/test_action_space.py` can protect taxonomy, action families, and grouping helpers
- `tests/test_recourse_redesign.py` can protect grouped semantic output and roadmap-level serialization
- `tests/test_messaging.py` can protect semantic-vs-technical output separation
- `tests/test_batch_candidate_diversity.py` can protect downstream artifact compatibility where grouped actions flow into batch-facing outputs

The validation strategy should therefore require:

- local action-space checks after catalog and mapping tasks
- roadmap-contract checks after schema and serialization tasks
- messaging and downstream artifact checks before phase closeout

No wave-zero framework install is needed.
