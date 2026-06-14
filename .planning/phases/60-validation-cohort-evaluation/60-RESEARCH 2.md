# Phase 60: Validation & Cohort Evaluation - Research

**Researched:** 2026-04-04
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest safe implementation that turns the existing Phase 54-59 runtime outputs into cohort-level movement evidence, path-diversity evidence, and trust-safe evaluation summaries without changing planner semantics, trust logic, or the action space?

## Planning Basis

Phase 60 decisions were discussed in-session and are now locked in [60-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/60-validation-cohort-evaluation/60-CONTEXT.md). The authoritative inputs for this planning pass are:

- [PROJECT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/PROJECT.md)
- [ROADMAP.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/ROADMAP.md)
- [REQUIREMENTS.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/REQUIREMENTS.md)
- [STATE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/STATE.md)
- [59-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/59-action-semantics-rendering/59-CONTEXT.md)
- [pathing.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/pathing.py)
- [run_batch_recourse_eval.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py)
- [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py)
- [decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py)
- [test_batch_candidate_diversity.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_batch_candidate_diversity.py)
- [test_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_customer_artifact_collection.py)
- [test_selected_surface_consistency.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_selected_surface_consistency.py)
- [test_operator_packet_coherence.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_operator_packet_coherence.py)
- [test_winner_integrity_hard_stop.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_winner_integrity_hard_stop.py)

## Executive Summary

Phase 60 should be planned as an **evaluation assembly and evidence-export phase**, not as a planner, generation, or policy phase.

The safest implementation shape is:

`reuse existing path metrics -> reuse existing candidate-quality summaries -> reuse existing movement-guardrail diagnosis -> assemble one canonical cohort-evidence package -> materialize required cohort artifacts -> gate the final interpretation through existing trust suites`

The code scan shows six important truths:

1. The repo already computes most Phase 60 metrics at the customer and population level, so the missing work is mainly aggregation, standardization, and evidence packaging
2. The batch evaluator already owns denied and high-risk denied candidate-quality summaries, so it should remain the source of truth for path-diversity and selected-path mix metrics
3. The calibration layer already owns movement diagnosis and `dominant_movement_bottleneck`, so Phase 60 should reuse that diagnosis rather than inventing a second movement theory
4. The customer artifact collection flow already owns the pilot-mixed and calibration-ready cohort selection logic, so Phase 60 can reuse it for the third required population instead of creating new cohort definitions
5. Trust proof is already enforced by explicit suites, so Phase 60 should report those results, not redesign trust logic
6. The missing capability is one aggregate evidence seam plus standardized summary tables and files, not new recourse behavior

## Concrete Repo Findings

### 1. The core Phase 60 path and action metrics already exist

[pathing.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/pathing.py) already exposes `summarize_path_metrics(...)`, which returns:

- `path_count`
- `rankable_path_count`
- `multi_path_flag`
- `customer_only_path_count`
- `institution_assisted_path_count`
- `hybrid_path_count`
- `action_diversity_index`
- `non_utilization_action_rate`
- `institution_action_rate`
- selected-path identity fields

Planning implication:
- Phase 60 should consume these fields as evidence.
- It should not recompute path behavior from raw actions or invent a second path metric source.

### 2. Batch evaluation already computes most denied and high-risk population summaries

[run_batch_recourse_eval.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py) already defines `_candidate_quality_metrics_for_population(...)` and `_build_candidate_quality_artifacts(...)`, which produce:

- `multi_path_rate`
- `action_diversity_index`
- `non_utilization_action_rate`
- `institution_action_rate`
- `non_empty_contender_share`
- `approved_or_conditional_contender_share`
- `mean_execution_aware_value`
- offer-ready and approval-shell shares
- selected-plan category rates across `customer_only`, `institution_assisted`, `hybrid`
- best-source rates across `internal`, `dice`, `rule`, `fallback`

Planning implication:
- Phase 60 should extend this existing candidate-quality seam into one canonical cohort evidence package.
- The denied and high-risk denied populations already exist and should remain canonical.

### 3. The calibration layer already owns movement diagnosis

[decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py) already exposes `build_movement_guardrail_evidence(...)`, which returns:

- `movement_guardrail_summary`
- `movement_promotion_blockers`
- `movement_bottleneck_breakdown`
- `movement_ceiling_breakdown`

The summary already contains:

- `dominant_movement_bottleneck`
- `movement_guardrail_summary`
- `promotion_blocker_summary`
- `recommendation_space`
- `structural_cohort`
- `trust_guardrails`

Planning implication:
- Phase 60 should treat this as the authoritative movement-potential diagnosis.
- The phase should compare new cohort evidence to this diagnosis, not replace it.

### 4. Pilot-mixed cohort selection already exists and is deterministic

[decision_calibration.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/evaluation/decision_calibration.py) already exposes `select_initial_cohort(...)` with a `pilot_mixed` policy using fixed bucket weights and deterministic fallback behavior.

[run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) already uses that machinery to produce export-first calibration and collection outputs.

Planning implication:
- Phase 60 should reuse `pilot_mixed` as the third required cohort population.
- It should not add a new cohort policy just to satisfy Phase 60.

### 5. Collection and calibration flows already write most of the evidence-family files

[run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) already writes:

- `movement_guardrail_summary.json`
- `movement_guardrail_review.md`
- calibration tables and comparison CSVs
- operator-review briefing outputs
- collection summary metadata

Planning implication:
- Phase 60 should add a Phase 60-specific evidence bundle adjacent to these outputs.
- It should follow the existing export-first pattern of JSON/CSV plus Markdown.

### 6. The trust baseline is already explicit and test-driven

The repo already has explicit regression suites for:

- winner integrity
- selected-surface consistency
- operator packet coherence
- customer artifact parity
- DICE validity enforcement

Planning implication:
- Phase 60 should add one focused test module for cohort evidence assembly and rely on the existing trust suites for the non-negotiable v2.2 baseline.
- The phase should report trust status in a table, not redefine the invariants.

## What Phase 60 Must Deliver

### 1. One canonical cohort-evidence assembly seam

Phase 60 must combine the existing metric sources into one additive, reusable evidence layer that can produce:

- Movement Potential Table
- Path Diversity Table
- Action Coverage Table
- Selected Path Distribution Table
- Trust Regression Table

### 2. Three required cohort populations with consistent outputs

Phase 60 must materialize evidence for:

- `denied`
- `high_risk_denied`
- `pilot_mixed`

using existing selection and evaluation seams rather than new cohort logic.

### 3. One machine-readable and one human-readable Phase 60 package

The phase should export:

- one canonical JSON evidence summary
- supporting table artifacts in JSON/CSV
- one Markdown interpretation that answers whether movement improved and whether trust stayed intact

### 4. Explicit separation between evidence and runtime behavior

Phase 60 must not:

- add new action types
- change planner ranking or contender logic
- change trust rules
- reinterpret winner semantics

The entire phase is about measuring the shipped runtime, not changing it.

## Recommended Plan Shape

The cleanest split is:

1. `60-01` - cohort-evidence assembly helpers, population table builders, and focused evaluation tests
2. `60-02` - batch and collection integration for required cohort runs plus additive artifact writing
3. `60-03` - trust-gated interpretation, regression reporting, and phase-close verification outputs

## Validation Architecture

Validation should prove both evidence correctness and trust preservation:

1. Evidence correctness
- cohort tables consume the existing metric sources without inventing new semantics
- denied, high-risk denied, and pilot-mixed populations all receive the required outputs
- selected-path and source distributions match existing serialized fields

2. Movement diagnosis integrity
- `dominant_movement_bottleneck` remains sourced from `build_movement_guardrail_evidence(...)`
- Phase 60 summaries state whether `structural_cohort_limited` softened or remained dominant
- movement-potential reporting stays separate from path-diversity reporting

3. Trust preservation
- winner integrity remains unchanged
- selected-surface consistency remains unchanged
- operator packet coherence remains unchanged
- DICE and contender-quality enforcement remain unchanged

Recommended commands:

- Quick: `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py tests/test_batch_candidate_diversity.py tests/test_customer_artifact_collection.py -q`
- Full: `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py tests/test_batch_candidate_diversity.py tests/test_customer_artifact_collection.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py tests/test_winner_integrity_hard_stop.py tests/test_dice_lane_validity_enforcement.py -q`

## RESEARCH COMPLETE
