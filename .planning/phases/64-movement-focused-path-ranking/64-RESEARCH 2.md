# Phase 64: Movement-Focused Path Ranking - Research

**Researched:** 2026-04-07
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest safe implementation that makes recoverable/full-mode ranking explicitly movement-focused for denied-target customers, while preserving winner integrity, selected-surface consistency, and Phase 63 gating semantics?

## Planning Basis

Phase 64 decisions were discussed in-session and are now locked in [64-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/64-movement-focused-path-ranking/64-CONTEXT.md). The authoritative inputs for this planning pass are:

- [PROJECT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/PROJECT.md)
- [ROADMAP.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/ROADMAP.md)
- [REQUIREMENTS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/REQUIREMENTS.md)
- [STATE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/STATE.md)
- [61-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/61-recoverability-signal-definition/61-CONTEXT.md)
- [62-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/62-recoverable-customer-classifier/62-CONTEXT.md)
- [63-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/63-recourse-gating-by-recoverability/63-CONTEXT.md)
- [64-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/64-movement-focused-path-ranking/64-CONTEXT.md)
- [planner.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/planner.py)
- [pathing.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/pathing.py)
- [run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py)
- [recoverability.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/recoverability.py)
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py)
- [run_v24_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py)
- [cohort_evidence.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/cohort_evidence.py)
- [test_planner_denied_objective.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_planner_denied_objective.py)
- [test_planner_quality_source_mix.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_planner_quality_source_mix.py)
- [test_recourse_paths.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_recourse_paths.py)
- [test_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_customer_artifact_collection.py)
- [test_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_cohort_evaluation.py)
- [test_selected_surface_consistency.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_selected_surface_consistency.py)
- [test_operator_packet_coherence.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_operator_packet_coherence.py)
- [test_decision_explanation_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_decision_explanation_pack.py)
- [test_winner_integrity_hard_stop.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_winner_integrity_hard_stop.py)

## Executive Summary

Phase 64 should be planned as a **recoverable-only ranking refinement**, not a planner redesign. The safest implementation shape is:

`activate a recoverable/full-mode ranking branch inside the existing deterministic planner seam -> prioritize threshold-reaching movement over cosmetic richness -> preserve simplicity and path-type realism as bounded penalties -> propagate additive movement fields into runtime, flat artifacts, and cohort evidence -> prove trust contracts remain unchanged`

The repo is already set up for this approach:

1. Phase 61 and Phase 62 already provide the threshold-gap and recoverability truth Phase 64 needs.
2. Phase 63 already defines `recoverable_flag` plus `recourse_mode=full|limited` as the canonical activation seam.
3. `choose_best_plan(...)` already centralizes deterministic rank ordering used by both selected-plan and path-representative selection.
4. downstream artifact and trust surfaces already consume runtime summary truth rather than inventing ranking semantics independently.

Planning implication:
- Phase 64 should refine ordering inside the existing planner regime.
- It should not create a new planner stage, new recourse mode, or customer-facing narrative type.
- Limited mode should remain completely unchanged.

## Concrete Repo Findings

### 1. The planner already has layered deterministic ranking seams

[planner.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/planner.py) already contains reusable sort helpers and structured tie-break behavior:

- `_denied_sort_key(...)`
- `_high_risk_sort_key(...)`
- `_execution_rank_penalty(...)`
- `_phase_aware_priority_score(...)`
- `choose_best_plan(...)`

Planning implication:
- Phase 64 should add a recoverable/full-mode movement layer inside this existing ordering model.
- It should not replace ranking with one opaque composite score.

### 2. Path representative ranking already reuses the planner seam

[pathing.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/pathing.py) uses `choose_best_plan(...)` to:

- choose one representative plan per grouped path
- rank path representatives globally

Planning implication:
- if Phase 64 activates through the shared planner entrypoint, selected plan choice and selected path choice will stay aligned automatically.
- This is the cleanest way to avoid path-level and plan-level drift.

### 3. Runtime already owns the activation context we need

[run_recourse.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_recourse.py) already passes:

- `denied_mode`
- `segment_context`
- `denied_objective_cfg`

into both `choose_best_plan(...)` and `build_recourse_path_records(...)`.

Planning implication:
- Phase 64 can activate movement-focused ranking by threading recoverability and recourse-mode truth into the existing runtime calls.
- No second planner entrypoint is needed.

### 4. Recoverability and gating truth should remain the only activation rule

[recoverability.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/recoverability.py) and the Phase 63 runtime contract already provide:

- `approval_gap`
- `threshold_reach_possible`
- `recoverable_flag`
- `recourse_mode`

Planning implication:
- Phase 64 should apply only when `denied-target && recoverable_flag && recourse_mode="full"`.
- It should not infer activation from path count, path diversity, or raw plan availability.

### 5. Runtime-derived artifacts are summary-first consumers

[run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) and [run_v24_cohort_evaluation.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py) already flatten runtime truth into:

- selected-path metrics
- customer metrics rows
- cohort customer rows
- aggregate evidence packages

Planning implication:
- Phase 64 should emit new movement fields in runtime summary first, then let collection and cohort flows propagate them additively.
- Downstream code should not recompute a second movement policy.

### 6. Trust-critical regressions already exist for the risky surfaces

The current suite already protects the contracts Phase 64 must not reopen:

- [test_recourse_paths.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_recourse_paths.py)
- [test_selected_surface_consistency.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_selected_surface_consistency.py)
- [test_operator_packet_coherence.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_operator_packet_coherence.py)
- [test_decision_explanation_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_decision_explanation_pack.py)
- [test_winner_integrity_hard_stop.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_winner_integrity_hard_stop.py)

Planning implication:
- Phase 64 can prove trust safety by extending the existing ranking and downstream honesty tests rather than inventing a parallel trust suite.

## What Phase 64 Must Deliver

### 1. One recoverable/full-mode movement ranking contract

Phase 64 should add:

- `movement_score`
- `threshold_reach_probability`
- `threshold_reach_priority_flag`
- `movement_rank_reason_codes`

These should apply only to the recoverable/full-mode denied-target ranking branch.

### 2. Threshold-reaching advantage without planner redesign

The ranking policy should:

- keep existing validity and contender screening first
- prefer candidates that plausibly close the approval gap
- use `movement_score` to balance expected movement with execution realism
- use simplicity and path type as deterministic realism controls
- preserve existing source tie-break behavior at the end

### 3. Additive runtime and artifact propagation

The selected path should expose:

- `movement_score`
- `threshold_reach_probability`
- `threshold_reach_priority_flag`
- `movement_rank_reason_codes`
- `selected_path_movement_strength`

These should flow additively through:

- runtime summary
- `metrics_summary`
- customer artifact collection
- cohort evaluation and evidence packaging

### 4. Explicit proof that trust contracts remain intact

Phase 64 must prove:

- no invalid winner is introduced
- limited mode remains unchanged and informational
- selected-surface truth remains honest
- operator and explanation surfaces do not become movement-marketing layers

## Recommended Plan Shape

The cleanest split is:

1. `64-01` - recoverable/full-mode movement ranking core plus shared planner/path activation
2. `64-02` - runtime summary and flat artifact propagation of movement fields
3. `64-03` - cohort evidence propagation plus trust-regression proof

## Validation Architecture

Validation should prove both ranking usefulness and unchanged honesty:

1. Planner contract correctness
- movement-focused ranking activates only in recoverable/full denied-target context
- threshold-reaching candidates gain deterministic ranking advantage
- simplicity and path type only override when movement is genuinely close

2. Shared selection coherence
- selected plan ranking and grouped path representative ranking stay aligned
- runtime activation uses the same movement policy for both seams

3. Artifact propagation
- runtime summary, `metrics_summary`, customer metrics, and cohort outputs expose one consistent movement contract
- downstream flows do not invent a second movement score or threshold heuristic

4. Trust regression protection
- winner integrity still fails closed when appropriate
- selected-surface consistency still holds
- operator packet coherence and explanation honesty remain intact

Recommended commands:

- Quick: `cd credit-coach && python -m pytest tests/test_planner_denied_objective.py tests/test_planner_quality_source_mix.py tests/test_recourse_paths.py tests/test_customer_artifact_collection.py tests/test_cohort_evaluation.py -q`
- Full: `cd credit-coach && python -m pytest tests/test_planner_denied_objective.py tests/test_planner_quality_source_mix.py tests/test_recourse_paths.py tests/test_customer_artifact_collection.py tests/test_cohort_evaluation.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py tests/test_decision_explanation_pack.py tests/test_winner_integrity_hard_stop.py -q`

## RESEARCH COMPLETE
