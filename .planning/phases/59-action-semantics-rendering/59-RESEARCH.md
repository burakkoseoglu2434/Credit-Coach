# Phase 59: Action Semantics Rendering - Research

**Researched:** 2026-04-04
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest safe implementation that turns the existing semantic action and path artifacts into deterministic, human-readable recommendation text, while preserving selected-plan truth, selected-path truth, and the locked trust baseline?

## Planning Basis

Phase 59 decisions were discussed in-session and are now locked in [59-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/59-action-semantics-rendering/59-CONTEXT.md). The authoritative planning inputs for this pass are:

- [PROJECT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/PROJECT.md)
- [ROADMAP.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/ROADMAP.md)
- [REQUIREMENTS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/REQUIREMENTS.md)
- [STATE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/STATE.md)
- [35-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/35-narrative-generation-v2/35-CONTEXT.md)
- [58-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/58-multi-path-recourse-generation/58-CONTEXT.md)
- [schema.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py)
- [messaging.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/messaging.py)
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py)
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py)
- [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py)
- [test_messaging.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_messaging.py)
- [test_recourse_redesign.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_recourse_redesign.py)
- [test_selected_surface_consistency.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_selected_surface_consistency.py)
- [test_operator_packet_coherence.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_operator_packet_coherence.py)
- [test_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_customer_artifact_collection.py)

## Executive Summary

Phase 59 should be planned as a **deterministic rendering hardening phase**, not as a planning, policy, or evaluation phase.

The safest implementation shape is:

`render primitives -> additive path render schema -> runtime/customer artifact integration -> selected projection alignment -> operator consumer alignment -> trust regression proof`

The repo scan shows six important truths:

1. The existing narrative system in `messaging.py` already owns deterministic wording, so Phase 59 should extend that seam instead of creating a new renderer
2. Phase 47 already locked selected recommendation projection as a trust seam, so improved wording must still flow through the same selected projection path
3. Phase 48 already locked operator packet rendering as a consumer of selected truth, so operator wording must reuse the same render outputs rather than inventing parallel copy
4. Phase 58 already added `customer_paths.json` and path identity, so path summaries can be added as additive render fields instead of new structural artifacts
5. Existing messaging and redesign tests already cover most step-level narrative behavior, so the missing proof is one focused path-and-render suite plus selected/operator regressions
6. The biggest missing capability is canonical action-aware, path-aware phrasing and weak-language suppression, not broader narrative creativity

## Concrete Repo Findings

### 1. `messaging.py` already owns deterministic recommendation wording

[messaging.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/messaging.py) already contains:

- canonical action narrative templates
- primary numeric target formatting
- `primary_recommendation` and `institution_condition` generation
- offer narrative generation
- executive summary, checkpoint, and reason rendering

Planning implication:
- Phase 59 should centralize all new action and path phrasing inside `messaging.py`.
- New render helpers should be additive consumers of existing semantic and numeric truth, not a second narrative layer hidden in CLI code.

### 2. The selected projection is already a frozen trust seam

[run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py) already uses `_build_selected_surface_projection(...)` to derive:

- `selected_recommendation_text`
- `selected_institution_condition`
- selected recommendation source
- selected action count

[test_selected_surface_consistency.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_selected_surface_consistency.py) already proves:

- selected consumer status stays separate from internal plan status
- `no_valid_winner` becomes a true empty state

Planning implication:
- Phase 59 may improve the text payload feeding selected projection, but it must not create a second selected-text source.
- The selected projection should continue to read from narrative output built by the engine-owned render helpers.

### 3. Operator wording is already consumer-side and should stay that way

[operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py) already:

- consumes selected recommendation text and institution condition from roadmap summary
- consumes narrative steps for timing and fallback action detail
- produces operator short-view and technical appendix outputs

Planning implication:
- Phase 59 should keep operator packet assembly as a consumer of selected render truth.
- If operator-facing path wording is added, it should come from additive render fields already attached upstream rather than from packet-local phrasing logic.

### 4. Path artifacts already exist and are the right home for alternative-path summaries

Phase 58 added:

- plan-level path identity
- `RecoursePathRecord`
- `customer_paths.json`
- selected-path traceability in roadmap summary

Planning implication:
- Phase 59 should add localized path-summary fields directly to `RecoursePathRecord` instead of creating a new sidecar artifact.
- The simplest first-wave contract is additive path summary text such as:
  - `customer_summary`
  - `operator_summary`
  - optional render version traceability

### 5. Existing tests already prove most narrative determinism

[test_messaging.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_messaging.py) already covers:

- deterministic roadmap narrative generation
- primary target phrasing
- offer narrative separation
- dependency-gated behavior
- grouped-step behavior
- no-credit-score-primary-recommendation safety

[test_recourse_redesign.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_recourse_redesign.py) already covers sibling narrative serialization.

Planning implication:
- Phase 59 does not need to reinvent broad narrative tests.
- It needs one focused render regression module for:
  - path summary generation
  - weak-language suppression
  - customer vs institution vs hybrid wording
  - render-version and artifact propagation

### 6. The phase boundary is narrow and should stay narrow

The discussion context and current requirements lock:

- no planner redesign
- no decision-policy redesign
- no trust relaxation
- no fuzzy or probabilistic generation
- no UI-side rewrite

Planning implication:
- Phase 59 should stay inside the engine-owned render contract.
- Broader cohort interpretation and metric reporting remain Phase 60 work.

## What Phase 59 Must Deliver

### 1. Canonical action-aware render primitives

Phase 59 must harden deterministic phrasing based on:

- `action_key`
- `action_owner`
- primary numeric target
- offer or approval dependency truth

This includes stronger before/after wording and suppression of generic filler text.

### 2. Deterministic path summaries

Phase 59 must render one stable summary per rankable path using representative-plan truth.

Those summaries should say:

- what the path is
- what movement it targets
- whether institution support or approval is required

without sounding like guaranteed approvals or synthetic alternatives.

### 3. Selected-surface and artifact alignment

Phase 59 must keep:

- `narrative.steps[*].primary_recommendation`
- `narrative.steps[*].institution_condition`
- `selected_recommendation_text`
- `selected_institution_condition`
- `customer_paths.json` path summaries

aligned through one shared render core.

### 4. Operator-safe consumption

Phase 59 must ensure operator-facing wording continues to consume engine-owned render truth rather than rebuilding it independently inside packet assembly.

## Recommended Plan Shape

The cleanest split is:

1. `59-01` - render primitive hardening plus additive path render schema
2. `59-02` - integration into customer artifacts, selected projection, and operator-facing consumers
3. `59-03` - rendering-focused regression proof for weak-language suppression, selected-surface consistency, operator packet coherence, and empty-state preservation

## Validation Architecture

Validation should prove both render quality and trust preservation:

1. Render-core correctness
- canonical actions produce deterministic recommendation text
- before/after phrasing uses real primary target truth
- weak or generic phrasing is suppressed rather than surfaced
- institution-assisted and hybrid wording stays dependency-honest

2. Artifact correctness
- `customer_paths.json` carries rendered path summaries
- roadmap narrative and flat selected projection stay aligned
- customer artifact collection exports additive render/path fields coherently

3. Trust preservation
- selected projection stays the sole selected-text owner
- operator packets remain coherent and consume the same render truth
- `no_valid_winner` stays a real empty state with no fake selected recommendation
- winner integrity remains unchanged

Recommended commands:

- Quick: `cd credit-coach && python -m pytest tests/test_recourse_rendering.py tests/test_messaging.py tests/test_customer_artifact_collection.py -q`
- Full: `cd credit-coach && python -m pytest tests/test_recourse_rendering.py tests/test_messaging.py tests/test_recourse_redesign.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py tests/test_customer_artifact_collection.py tests/test_winner_integrity_hard_stop.py -q`

## RESEARCH COMPLETE
