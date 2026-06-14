# Phase 58: Multi-Path Recourse Generation - Research

**Researched:** 2026-04-04
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest safe implementation that turns the existing validated candidate pool into multiple deterministic recourse paths per customer, while preserving the current winner-selection contract and the locked trust baseline?

## Planning Basis

Phase 58 decisions were discussed in-session and are now locked in [58-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/58-multi-path-recourse-generation/58-CONTEXT.md). The authoritative inputs for this planning pass are:

- [PROJECT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/PROJECT.md)
- [ROADMAP.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/ROADMAP.md)
- [REQUIREMENTS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/REQUIREMENTS.md)
- [STATE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/STATE.md)
- [57-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/57-heuristic-institution-action-lane/57-CONTEXT.md)
- [schema.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py)
- [planner.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/planner.py)
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py)
- [run_batch_recourse_eval.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py)
- [test_batch_candidate_diversity.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_batch_candidate_diversity.py)
- [test_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_customer_artifact_collection.py)
- [test_selected_surface_consistency.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_selected_surface_consistency.py)
- [test_operator_packet_coherence.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_operator_packet_coherence.py)
- [test_winner_integrity_hard_stop.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_winner_integrity_hard_stop.py)

## Executive Summary

Phase 58 should be planned as a **deterministic organization-and-artifact layer**, not as a generation, planner, or policy phase.

The safest implementation shape is:

`additive path schema -> deterministic path typing and signature rules -> grouping over already-gated PlanRecord contenders -> representative selection using existing ranking semantics -> additive customer/batch artifacts -> trust-baseline regression proof`

The code scan shows six important truths:

1. The current trust unit is already the validated `PlanRecord`, so Phase 58 can annotate and group existing plans instead of inventing a new candidate type
2. The planner already defines the ordering semantics Phase 58 needs, so a path representative can be selected without creating a new ranking policy
3. `run_recourse.py` already owns candidate assembly, winner selection, and artifact writing, so it is the right seam for path annotation and `customer_paths.json`
4. `run_batch_recourse_eval.py` already computes cohort candidate-quality summaries, so path metrics can be added as additive evidence without absorbing the broader Phase 60 evaluation scope
5. Existing selected-surface and operator-packet contracts are summary-driven, so selected-path traceability can be added without redesigning those surfaces
6. The missing capability is one deterministic pathing module plus schema and artifact propagation, not new generation logic

## Concrete Repo Findings

### 1. `PlanRecord` is already rich enough to be the path membership unit

[schema.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py) already carries the fields that matter for path identity:

- `plan_source`
- `contender_bucket`
- `offer_maturity`
- `recommendation_validity_status`
- rule-lane and DICE-lane quality gate outputs
- action-level canonical semantics on `PlanAction`

Planning implication:
- Phase 58 should add path fields to `PlanRecord` rather than inventing a separate sidecar plan model.
- The grouping unit should remain the full validated plan because that is the current trust-preserving object used everywhere downstream.

### 2. The planner already has the ranking semantics that path representatives need

[planner.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/planner.py) already contains:

- contender quality annotation
- actionable vs shell-only filtering
- source tie-breaking
- the full `choose_best_plan(...)` ordering logic

Planning implication:
- The best plan inside a path should be selected using the existing plan-ordering semantics, not a new path-specific scoring formula.
- Phase 58 may need one small reusable helper for within-path ranking, but it should not rewrite or fork decision policy.

### 3. Candidate assembly and artifact writing already converge in one runtime seam

[run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py) already:

- builds `candidate_pool = validated + dice_records + rule_records`
- applies DICE and rule contender gates
- prunes and filters the pool
- calls `choose_best_plan(...)`
- builds `plans.json`, `candidate_pool.csv/json`, `customer_roadmap.json`, `customer_roadmap_steps.csv`, and `metrics.json`

It also uses `CustomerArtifactBundle`, which currently contains:

- `plans_df`
- `roadmap`
- `roadmap_steps_df`
- `metrics_summary`

Planning implication:
- Phase 58 should add one path artifact to this same bundle flow, most likely `customer_paths.json`.
- Path construction should happen after existing candidate gating and before artifact serialization, while winner selection remains unchanged.

### 4. The selected surface already depends on roadmap summary fields, not on a new surface contract

[run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py) uses `_build_selected_surface_projection(...)` to derive:

- `selected_recommendation_text`
- `selected_institution_condition`
- `selected_action_count`
- selected recommendation source

Planning implication:
- Phase 58 can add `selected_path_id`, `selected_path_type`, and alternative-path counts into roadmap summary additively.
- This keeps selected-surface consistency intact because the selected plan remains the primary render source.

### 5. Batch evaluation already has additive metric-summary patterns that Phase 58 can reuse

[run_batch_recourse_eval.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py) already exposes:

- `_candidate_pool_diversity_index(...)`
- `_candidate_source_entropy(...)`
- `_build_candidate_quality_artifacts(...)`
- batch summary and breakdown outputs

Planning implication:
- Phase 58 should add path-aware raw fields and summary metrics in the same pattern.
- The current `candidate_pool_diversity_index` is feature-based and should stay as-is.
- Phase 58 should add path metrics like `multi_path_rate` and `action_diversity_index` additively instead of overloading the existing candidate diversity metric.

### 6. The repo already has the right regression suites to protect trust behavior

Existing tests already guard:

- customer artifact structure
- selected-surface consistency
- operator packet coherence
- winner integrity
- candidate diversity summaries

Planning implication:
- Phase 58 should add one focused pathing test module and then extend the existing trust suites rather than trying to prove everything in one new file.
- The right execution shape is path-core tests first, then runtime artifact tests, then trust-baseline regressions.

## What Phase 58 Must Deliver

### 1. Deterministic path typing and signature construction

Phase 58 must derive:

- `customer_only`
- `institution_assisted`
- `hybrid`

from canonical action ownership and offer dependency semantics, and it must build a stable path signature that ignores volatile score fields.

### 2. Deterministic path grouping and representative selection

Phase 58 must:

- group only already-gated candidates
- collapse near-duplicates deterministically
- select one representative plan per path using existing plan-ordering semantics
- preserve the selected winner as a normal plan-level outcome

### 3. Additive path identity in customer artifacts

Phase 58 must emit:

- plan-level path fields
- a path-level artifact such as `customer_paths.json`
- additive selected-path fields in roadmap summary
- additive path columns in plans and candidate-pool outputs

### 4. Path evidence sufficient for PATH-03, without absorbing Phase 60

Phase 58 must surface the raw and summary metrics required to prove multi-path behavior exists:

- path count
- multi-path flag
- selected path type
- per-type path counts
- path-level action diversity

but it should not absorb the broader validation and cohort-evaluation scope reserved for Phase 60, especially:

- structural cohort reduction analysis
- milestone-level cohort interpretation and reporting
- expanded evaluation dashboards

## Recommended Plan Shape

The cleanest split is:

1. `58-01` - additive schema plus deterministic path typing, signature, grouping, and representative selection core
2. `58-02` - `run_recourse.py` and `run_batch_recourse_eval.py` integration, path artifacts, and additive path metrics
3. `58-03` - path-aware regression proof for winner integrity, selected-surface consistency, operator packet coherence, and duplicate-resistant batch evidence

## Validation Architecture

Validation should prove both path correctness and trust preservation:

1. Path-core correctness
- path type is deterministic from canonical action semantics
- path signatures are stable
- near-duplicates collapse correctly
- each rankable path has exactly one representative plan

2. Runtime and artifact correctness
- `selected_path_id` matches the selected winner's `path_id`
- `customer_paths.json` is written and internally coherent
- `plans.json`, `candidate_pool.csv/json`, `customer_roadmap.json`, and `metrics.json` expose additive path fields without breaking existing contracts
- batch outputs surface path metrics additively

3. Trust preservation
- winner selection logic is unchanged
- `APPROVAL_SHELL_ONLY` candidates do not become fake rankable paths
- selected-surface consistency remains intact
- operator packet coherence remains intact
- DICE and rule gating remain intact

Recommended commands:

- Quick: `cd credit-coach && python -m pytest tests/test_recourse_paths.py tests/test_customer_artifact_collection.py tests/test_batch_candidate_diversity.py -q`
- Full: `cd credit-coach && python -m pytest tests/test_recourse_paths.py tests/test_customer_artifact_collection.py tests/test_batch_candidate_diversity.py tests/test_planner_quality_source_mix.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py tests/test_winner_integrity_hard_stop.py tests/test_dice_lane_validity_enforcement.py -q`

## RESEARCH COMPLETE
