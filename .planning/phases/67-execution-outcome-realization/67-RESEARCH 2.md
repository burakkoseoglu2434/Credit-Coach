# Phase 67: Execution & Outcome Realization - Research

**Researched:** 2026-04-10
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the smallest deterministic extension of the existing outcome-feedback seam that can measure whether selected-path recommendations were actually executed and whether they produced observed downstream movement, without changing decision logic or overstating causal effect?

## Planning Basis

Phase 67 decisions were discussed in-session and are now locked in [67-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/67-execution-outcome-realization/67-CONTEXT.md). Because Phase 67 has not yet been inserted into the roadmap, this planning pass uses provisional requirement anchors:

- `REAL-01` - selected-path execution tracking and minimal schema
- `REAL-02` - realized outcome metrics and additive artifact publication
- `REAL-03` - predicted-vs-observed and control-sliced realization evaluation without causal overclaim

The authoritative inputs for this planning pass are:

- [PROJECT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/PROJECT.md)
- [STATE.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/STATE.md)
- [16-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/16-outcome-feedback-learning-loop/16-CONTEXT.md)
- [65-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/65-targeted-cohort-evaluation/65-CONTEXT.md)
- [67-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/67-execution-outcome-realization/67-CONTEXT.md)
- [run_outcome_feedback.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_outcome_feedback.py)
- [schema.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py)
- [repository.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/storage/repository.py)
- [test_outcome_feedback.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_outcome_feedback.py)

## Executive Summary

Phase 67 should be planned as an **additive extension of the current decision-outcome and outcome-feedback seam**, not as a new tracking subsystem and not as a new decision layer. The safest shape is:

`preserve more selected-path truth with delayed outcomes -> ingest append-only selected-action execution events -> derive deterministic action/path/outcome realization summaries -> publish predicted-vs-observed and recoverable-vs-limited evaluation artifacts -> end with a disciplined non-causal report`

The repo is already well-positioned for this:

1. [DecisionOutcomeRecord](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py) already carries selected-plan identity, planner probabilities, and coarse execution/outcome fields.
2. [repository.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/storage/repository.py) already persists compact decision-outcome context and computes graded outcome-ingestion summaries.
3. [run_outcome_feedback.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_outcome_feedback.py) already owns the CSV-ingest and artifact-output path for delayed observations.
4. [test_outcome_feedback.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_outcome_feedback.py) already provides a focused regression surface for this seam.

Planning implication:
- Phase 67 should stay centered on the existing outcome-feedback CLI and repository.
- It should not reopen recourse generation, ranking, or gating logic.
- The main new value is deterministic observation and reporting of realized execution and realized movement, not a learning-policy rewrite.

## Concrete Repo Findings

### 1. The current outcome record is compact but already recommendation-aware

[DecisionOutcomeRecord](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py) already includes:

- `decision_id`
- `customer_id`
- `selected_plan_id`
- `selected_plan_status`
- `selection_propensity`
- `plan_execution_probability`
- `offer_acceptance_probability`
- `combined_plan_realization_probability`
- `action_completed`
- `offer_accepted`
- `observed_default_*`
- `observed_margin_90d`
- `observed_recovery_amount_90d`

What it does not yet preserve explicitly is the v2.5 selected-path and targeting truth needed for realized-outcome evaluation, such as:

- `selected_path_id`
- `selected_path_type`
- `selected_path_movement_strength`
- `recourse_mode`
- `recoverable_flag`
- `movement_score`
- `threshold_reach_probability`

Planning implication:
- Wave 1 should extend this parent observed-outcome contract additively.
- The result should remain compact and decision-centric, not a duplicate plan archive.

### 2. The repository already has the right persistence posture

[save_decision_outcome(...)](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/storage/repository.py) already upserts:

- base delayed outcomes
- compact companion decision context
- audit events

The same module already owns:

- `summarize_decision_logging`
- `summarize_outcome_ingestion`
- `summarize_decision_outcomes`
- `load_decision_learning_dataset`
- `compute_policy_outcome_deltas`

Planning implication:
- Phase 67 should add action-execution and path-realization storage beside this existing seam.
- It should not create a separate detached execution database or artifact family.

### 3. CSV-based delayed ingestion already exists and can be extended safely

[run_outcome_feedback.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_outcome_feedback.py) already:

- ingests `--outcomes_csv`
- parses optional booleans, ints, floats, and reason-code payloads
- writes machine-readable artifacts under `artifacts/runs/.../tables`

Planning implication:
- The smallest viable execution-tracking step is to add a second optional ingestion path for selected-action execution events.
- This keeps first-wave data collection deterministic, batchable, and brownfield-compatible.

### 4. The current summary layer is outcome-centric, not execution-realization-centric

Current outputs answer:

- what policy arms were observed
- what delayed default/margin differences appeared
- how complete the logged outcome coverage is

They do not yet answer:

- whether selected actions were attempted or completed
- whether selected paths were realized
- whether customers showed observed threshold progress after execution
- how predicted execution or realization compares with observed realization

Planning implication:
- Wave 2 should introduce deterministic realization summaries before any higher-level report framing.

### 5. Phase 16 already locked the discipline we need

[16-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/16-outcome-feedback-learning-loop/16-CONTEXT.md) already established:

- 90-day primary window
- graded completeness instead of binary data readiness
- non-causal, metric-by-metric reporting
- machine-readable truth before markdown summary

Planning implication:
- Phase 67 should inherit those rules rather than invent a new “realized impact” semantics layer.
- The new work is about recommendation execution and realized-path evaluation, not a new policy-evaluation philosophy.

### 6. The v2.5 truth needed for slicing already exists upstream

Phases 61-65 already emit and evaluate:

- `recoverable_flag`
- `recourse_mode`
- `selected_path_type`
- `selected_path_movement_strength`
- `movement_score`
- `threshold_reach_probability`
- `combined_plan_realization_probability`

Planning implication:
- Phase 67 can slice realized outcomes by recoverable/full vs limited/control and by movement-strength/path-type without re-deriving those labels downstream.
- That comparison should remain descriptive, not causal.

## What Phase 67 Must Deliver

### 1. A selected-path execution tracking contract

Phase 67 should introduce:

- preserved selected-path and targeting truth on the parent outcome record
- append-only selected-action execution events
- deterministic derived action status and path realization status

### 2. Deterministic realized-outcome summaries

The phase should publish:

- action execution and completion rates
- blocked and reversed posture
- path realization rates
- realized movement / threshold-reach / approval-realization rates
- observation coverage and latency metrics

### 3. Predicted-vs-observed comparison

The phase should compare:

- `plan_execution_probability` vs observed action/path execution
- `combined_plan_realization_probability` vs observed realized outcome

This should remain descriptive calibration-style evidence, not policy-learning evidence.

### 4. A controlled report

The final report should answer:

- Were actions executed?
- Did selected paths realize?
- Did observed threshold progress or approval follow?
- Where is evidence still pending or sparse?

It must not say:

- that an action caused an outcome
- that realized success proves production policy uplift

## Recommended Plan Shape

The cleanest split is:

1. `67-01` - extend the decision-outcome seam with selected-path realization context and selected-action execution event ingestion
2. `67-02` - derive deterministic action/path/outcome realization summaries and publish new machine-readable and markdown artifacts
3. `67-03` - add recoverable-vs-limited, path-type, and movement-strength evaluation plus predicted-vs-observed and non-causal conclusion framing

## Validation Architecture

Validation should prove schema correctness, persistence integrity, deterministic summary behavior, and reporting discipline:

1. Storage and ingestion
- parent outcome records preserve the new selected-path and targeting fields
- selected-action execution events can be ingested and summarized deterministically

2. Realization summaries
- action status, path realization, realized movement, and latency summaries are derived deterministically from stored observations
- missing data degrades to explicit pending/null states, not inferred success

3. Reporting discipline
- predicted-vs-observed outputs are descriptive
- recoverable/full vs limited/control slices are visible
- no causal or uplift language leaks into final outputs

Recommended commands:

- Quick: `cd credit-coach && python -m pytest tests/test_outcome_feedback.py -q`
- Full: `cd credit-coach && python -m pytest tests/test_outcome_feedback.py -q`

## RESEARCH COMPLETE
