# Phase 13: Behavior-Aware Recourse - Research

**Researched:** 2026-03-16
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What has to change so Credit Coach can rank recommendations by expected real-world execution likelihood rather than only nominal offline impact?

## Planning Assumption

This phase does not yet have a `13-CONTEXT.md`. For this planning pass, the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/research/v1.2-RECOMMENDATION-QUALITY-HARDENING.md`
- `.planning/phases/12-action-realism-feasibility-expansion/12-CONTEXT.md`
- `.planning/phases/12-action-realism-feasibility-expansion/12-RESEARCH.md`
- `.planning/phases/12-action-realism-feasibility-expansion/12-VALIDATION.md`
- current recommendation code under `credit-coach/src/credit_coach/`
- current tests under `credit-coach/tests/`

That is sufficient because the milestone contract is already locked at the roadmap and requirements level. The remaining work is brownfield design against the existing typed-action, feasibility, planner, batch-evaluation, and sequential-coaching seams.

## Executive Summary

Phase 13 should be treated as a scoring-and-simulation hardening phase, not a new planner rewrite. Phase 12 already made actions explicit, machine-readable, and constraint-aware. The repo also already has strong gate-aware ranking, high-risk tuning, sequential weekly coaching simulation, seeded KPI contracts, and challenger evidence. What is missing is the behavior layer between "recommended" and "actually executed."

The right implementation strategy is:

- add a canonical execution-probability seam for each action and plan
- thread execution-likelihood metadata through generator and serialized plan outputs
- update planner ranking to use expected utility under the inherited gate contracts
- reuse the existing weekly coaching loop and trajectory evidence seams to simulate partial execution, failed steps, and mixed execution rather than inventing an unrelated simulator
- publish machine-readable behavior-aware artifacts that batch, suite, and challenger flows can aggregate

Phase 13 should not yet redesign the time horizon model; that is Phase 14. It should make the existing one-shot or short phased plans behavior-aware enough that later sequential trajectory planning can build on them.

## Existing Assets We Can Reuse

### Phase 12 now provides typed actions and explicit constraint states

- `credit-coach/src/credit_coach/data/schema.py`
  - `PlanAction` already carries:
    - `action_key`
    - `action_class`
    - `action_group_id`
    - `requires_institutional_approval`
    - `action_status`
    - `diagnostic_flags`
- `credit-coach/src/credit_coach/recourse/action_space.py`
  - already defines the canonical typed action catalog
- `credit-coach/src/credit_coach/recourse/action_constraints.py`
  - already emits explicit `valid | repaired | provisional | invalid` states plus trace evidence

This is the right substrate for execution likelihood. Behavior-aware probability can now depend on action class, timing, approval state, and composite structure without guessing from raw feature edits.

### Generator already builds machine-readable plan actions with phase metadata

- `credit-coach/src/credit_coach/recourse/generator.py`
  - constructs `PlanAction`
  - already computes action metadata and realism diagnostics
  - already attaches phase and week windows

This means execution probability should be attached during generation rather than bolted on later by a reporting-only step.

### Planner already has gate-aware ranking seams

- `credit-coach/src/credit_coach/coaching/planner.py`
  - already prioritizes:
    - constraint eligibility
    - CI and reliability margins
    - worst-margin safety
    - denied/high-risk objectives
    - short-term action signal

Phase 13 does not need a second optimizer. It can extend the existing priority and bonus structure to include expected utility while keeping fairness, reliability, and safety semantics intact.

### The repo already has sequential execution simulation primitives

- `credit-coach/src/credit_coach/coaching/loop.py`
  - already simulates:
    - planned vs executed actions
    - action dropout
    - execution noise
    - replan triggers
- `credit-coach/tests/test_sequential_recourse.py`
  - already protects weekly replan behavior under missed actions

This is an excellent seam for partial execution. Phase 13 should extend it instead of introducing a disconnected Monte Carlo stack with no integration to the existing coaching flow.

### Batch, suite, challenger, and KPI contracts already aggregate evidence

- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - already emits trajectory, candidate-quality, and action-realism summaries
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - already builds seeded aggregate evidence and `kpi_contract_snapshot.json`
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`
  - already compares variants under seeded metrics
- `credit-coach/src/credit_coach/ops/kpi_contract.py`
  - already centralizes machine-readable contract logic

This means Phase 13 can introduce behavior-aware evidence without inventing a parallel artifact regime.

## Gaps Phase 13 Must Close

### 1. There is no explicit execution-probability contract

Today a plan can be typed, feasible, and safe, but the system still treats all surviving actions as if they are equally likely to be executed. That leaves a key gap between recommendation quality and real-world actionability.

### 2. Planner scoring still emphasizes nominal improvement over expected utility

The planner already reasons about gate safety, cost, and short-term urgency, but it does not yet explicitly compute:

- action execution likelihood
- plan execution likelihood
- expected utility under partial or failed execution

Phase 13 should close that gap without weakening the inherited gate logic.

### 3. Partial execution is simulated in the coaching loop, but not in recommendation evidence

The weekly loop already supports action dropout and replan triggers, but these execution dynamics are not yet surfaced as canonical recommendation evidence in batch, suite, or challenger workflows.

### 4. High-risk prioritization is still nominally action-centric

Phase 10 introduced high-risk tuning evidence, but Phase 13 must ensure high-risk recommendations prefer likely, feasible actions rather than merely high nominal lift.

## Context-Locked Interpretation For Phase 13

### Phase 13 is behavior-aware, not yet fully sequential

Execution probability and partial execution should enrich the existing plan model. Multi-phase horizon redesign belongs to Phase 14.

### A heuristic seam is acceptable if the contract is explicit

The requirement is that actions and plans carry execution probability grounded in context. That can begin as a deterministic or rules-based estimator if the interface is clean, testable, and replaceable by a learned model later.

### Execution likelihood must remain subordinate to inherited gates

Expected utility can influence ranking only among gate-eligible options. It must not override fairness, reliability, telemetry, or release semantics inherited from `v1.1`.

### Partial execution evidence should stay machine-readable

Markdown summaries may explain the behavior-aware evidence, but canonical truth should remain in JSON or CSV artifacts that batch, suite, and challenger can diff and aggregate.

## Recommended Architecture

### A. Add a dedicated execution-probability module

The safest path is a small module such as:

- `credit-coach/src/credit_coach/recourse/execution_probability.py`

with stable helpers for:

- per-action execution probability
- aggregated plan execution probability
- optional behavior-aware diagnostic explanations

This avoids scattering probability logic across generator, planner, and batch code.

### B. Attach execution likelihood at generation time

`PlanAction` and `PlanRecord` should carry execution-aware fields so downstream modules can use them consistently. Generator is the best place to resolve action-level values because it already knows action type, timing, feasibility state, and plan composition.

### C. Keep expected utility inside the existing planner seam

`coaching/planner.py` should incorporate expected utility into ranking by combining:

- execution likelihood
- nominal PD improvement
- inherited gate margins
- high-risk prioritization

The planner should prefer likely actions when nominal impact is similar, rather than discarding gate-safe plans purely because their offline effect looks smaller.

### D. Reuse the weekly coaching loop for partial execution

Partial execution should be modeled by extending the existing weekly simulation seam so the system can surface:

- full execution
- mixed execution
- failed execution
- expected partial progress

This keeps Phase 13 aligned with the current replan logic and reduces the risk of simulation drift.

### E. Publish a canonical behavior-aware artifact

Phase 13 should likely introduce:

- `behavior_aware_summary.json`

and companion breakdowns such as:

- `partial_execution_breakdown.csv`
- `execution_probability_breakdown.csv`

Batch evaluation should emit them first, and suite or challenger should aggregate from those stable artifacts rather than recomputing incompatible summaries.

## Recommended Plan Breakdown

### Plan 13-01: Action execution probability model

Focus on introducing a replaceable execution-probability seam and threading action or plan likelihood into generated recommendations.

### Plan 13-02: Expected utility scoring

Focus on integrating execution likelihood into planner ranking, high-risk prioritization, and machine-readable behavior-aware summaries.

### Plan 13-03: Partial execution simulation

Focus on simulating mixed or failed action execution, then surfacing the resulting robustness evidence through batch, suite, and challenger artifacts.

## Risks To Watch

- overfitting Phase 13 to a learned model before the behavior contract is stable
- letting execution likelihood silently override inherited safety gates
- building a second sequential simulator that drifts from the existing coaching loop
- emitting behavior-aware metrics only in markdown instead of machine-readable artifacts

## Recommendation

Proceed with Phase 13 now. The codebase already has the right brownfield seams: typed actions from Phase 12, gate-aware ranking from earlier phases, and a weekly execution loop that can be extended into partial-execution evidence. This is a natural next step before Phase 14 makes trajectories more explicitly multi-phase.
