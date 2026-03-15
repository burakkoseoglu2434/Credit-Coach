# Phase 12: Action Realism & Feasibility Expansion - Research

**Researched:** 2026-03-15
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What has to change so Credit Coach can recommend more real-world behavioral, structural, and institutional actions while keeping feasibility, trajectory, and governance behavior trustworthy?

## Planning Assumption

This phase does not yet have a `12-CONTEXT.md`. For this planning pass, the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/research/v1.2-RECOMMENDATION-QUALITY-HARDENING.md`
- current recommendation code under `credit-coach/src/credit_coach/`
- current tests under `credit-coach/tests/`

That is sufficient because the user already locked the milestone contract in detail. The remaining work is not open-ended discovery; it is translating the milestone into executable brownfield changes against the existing planner, generator, feasibility, and reporting seams.

## Executive Summary

Phase 12 should be treated as a schema-and-constraints hardening phase, not a behavior-modeling phase yet. The repo already has a useful recourse engine, feature-level action space, phased action metadata, trajectory rollups, and feature-level feasibility caps. What it does not yet have is a recommendation language that maps cleanly to real-world customer and institution actions, or a constraint layer that can reject unrealistic or incompatible action combinations before ranking.

The right implementation strategy is:

- expand the action schema from pure feature edits into typed actions
- keep those typed actions backward-compatible with the current feature-grounded planner and generator
- strengthen feasibility rules around monthly change, income growth, utilization shifts, credit-limit movement, and financial capacity
- add explicit dependency and conflict modeling so invalid action bundles are filtered or downgraded before they reach the final plan-ranking path

Behavior-aware execution probability, expected utility, and partial-execution simulation belong to Phase 13. Phase 12 should prepare for them by making actions and constraints explicit and machine-readable.

## Existing Assets We Can Reuse

### `PlanAction` already carries phase and timing metadata

- `credit-coach/src/credit_coach/data/schema.py`
  - `PlanAction` already supports:
    - `phase_id`
    - `week_start`
    - `week_end`
    - `expected_pd_delta`
    - `checkpoint_metric`
- `PlanRecord` already supports multi-action plans and trajectory-compatible serialization

This means Phase 12 does not need to invent phased plans from scratch. It can extend the existing action contract instead of replacing it.

### The current action space is explicit, but feature-bound

- `credit-coach/src/credit_coach/recourse/action_space.py`
  - already defines `ActionSpec`
  - already separates actionable vs immutable fields
  - already estimates cost and default time horizon

This is the right seam for Action Taxonomy redesign. The gap is that `ActionSpec` is still fundamentally “change this feature” instead of “perform this real-world action.”

### Generator and CLI flows already consume explicit action specs

- `credit-coach/src/credit_coach/recourse/generator.py`
  - relies on `get_action_spec(...)`
  - builds `PlanAction` instances
  - already maps actions into phase ids and week windows
- `credit-coach/src/credit_coach/cli/run_recourse.py`
  - serializes phased steps for roadmap-like outputs
  - already computes trajectory metrics from time-layered actions

This means Phase 12 should modify the existing action-semantics seam instead of introducing a second planner stack.

### Feasibility controls already exist, but are still mostly feature-local

- `credit-coach/src/credit_coach/recourse/feasibility.py`
  - already supports:
    - `max_relative_change`
    - `max_abs_increase / max_abs_decrease`
    - `max_abs_increase_per_month / max_abs_decrease_per_month`
    - `min_target / max_target`
    - `freeze_if_current_below / freeze_if_current_above`
    - `round_to_int`

This is a strong base for Phase 12. The missing layer is financial realism across action semantics, not raw cap infrastructure.

### Constraint-style logic already exists elsewhere in the repo

- `credit-coach/src/credit_coach/causality/action_constraints.py`
  - already applies a causal penalty over acted features

This is not enough for Phase 12, but it proves the repo already accepts the idea that recommendation actions can be constrained by relationships instead of only local scoring.

### There is already trajectory evidence and action-count reporting

- `credit-coach/src/credit_coach/cli/run_recourse.py`
  - already writes phase-layered action counts and trajectory outputs
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - already writes action-count distributions
  - already tracks `feasibility_gate` style rejection causes
  - already exposes trajectory phase-1 action count metrics
- `credit-coach/tests/test_recourse_funnel_kpis.py`
  - already protects time-layered action behavior

This means Phase 12 can make “action diversity vs infeasible-plan rate” measurable without inventing a new reporting framework.

## Gaps Phase 12 Must Close

### 1. Action semantics are still too close to raw feature edits

Today the system knows how to change `dti`, `annual_inc`, `revol_util`, and similar fields. It does not yet distinguish:

- behavioral actions
- structural actions
- institutional actions

That makes plans technically useful but still too abstract for real-world recommendation quality hardening.

### 2. Feasibility realism is mostly local, not financial-system aware

Current feasibility rules can cap a target value, but they do not yet directly express milestone-level rules such as:

- monthly change realism
- income growth caps
- one-step utilization drop bounds
- credit-limit adjustment bounds
- financial capacity constraints

Phase 12 should add those without breaking the existing cap engine.

### 3. Invalid action combinations are not modeled explicitly

The engine still lacks a machine-readable way to say:

- these two actions conflict
- this action requires another one first
- this action needs institutional approval

Without that layer, unrealistic plans can still be generated and only indirectly penalized later.

### 4. Success criteria need measurable diagnostics

The phase goal includes improving action diversity without increasing infeasible-plan rate. That means execution should likely extend existing batch diagnostics with at least:

- action-type distribution evidence
- feasibility rejection reason breakdown
- infeasible-plan rate or invalid-combination rate

## Context-Locked Interpretation For Phase 12

### Phase 12 is not yet behavior-aware execution modeling

Execution probability, expected utility, and partial-execution modeling are explicitly Phase 13 work. Phase 12 should prepare the action contract and realism controls that those later phases will consume.

### Backward compatibility matters

Current feature-grounded plans and trajectory outputs must continue to work. Typed actions should wrap or enrich the existing feature-based machinery rather than abruptly replacing it.

### Recommendation realism must remain additive to inherited gates

`v1.1` already hardened fairness, reliability, telemetry, and release evidence. Phase 12 must not weaken those gates in the name of richer actions.

### Institutional actions can be represented before they are fully optimized

Phase 12 should add institutional action semantics and constraints, even if full offer optimization and acceptance modeling do not arrive until Phase 15.

## Recommended Architecture

### A. Extend the action contract instead of replacing it

The safest path is to enrich `ActionSpec` and `PlanAction` with typed action semantics such as:

- action class or family
- action key
- optional prerequisite tags
- optional conflict tags
- optional institution-approval flags

while preserving the existing feature-grounded effect fields and phased scheduling metadata.

### B. Keep feasibility as a reusable rule engine with richer rule families

`apply_target_feasibility(...)` should stay the central seam, but it should grow to understand financially realistic rule families rather than only local numeric caps. Typed actions may require companion context, not a second feasibility engine.

### C. Add a dedicated dependency/conflict layer

Phase 12 likely needs a small dedicated module such as a graph or rule bundle for:

- prerequisites
- conflicts
- approval-required actions

This should run before final ranking so invalid plans are rejected or reason-coded deterministically.

### D. Use existing batch and trajectory outputs for observability

Rather than inventing a new reporting path, Phase 12 should extend current recourse and batch artifacts to expose:

- action-type breakdowns
- invalid-combination reasons
- richer feasibility rejection summaries

## Artifact Contract Recommended For Phase 12

Phase 12 does not need a new acceptance bundle. It should extend existing artifacts with machine-readable recommendation-realism evidence such as:

- typed action fields in serialized plans
- action-type distribution rollups
- feasibility rejection reason breakdowns
- invalid-combination or dependency-failure summaries

Markdown remains derived; canonical truth remains machine-readable.

## Recommended Plan Breakdown

### Plan 12-01: Action taxonomy redesign

Focus on explicit action classes, schema updates, generator compatibility, and preserving phased serialization.

### Plan 12-02: Feasibility realism expansion

Focus on financially realistic constraint families and measurable infeasible-plan diagnostics.

### Plan 12-03: Action interaction constraints

Focus on prerequisites, conflicts, institutional approval flags, and deterministic invalid-combination handling.

## Risks To Avoid

- replacing the current feature-grounded planner with a second incompatible action engine
- adding typed actions without backward-compatible serialization
- treating feasibility only as soft scoring instead of blocking impossible transitions
- letting conflict resolution silently drop actions without reason-coded diagnostics
- pulling execution-probability or off-policy-learning work forward from later phases
- weakening fairness, reliability, or telemetry inheritance while enriching recommendations

## Recommendation

Proceed with Phase 12 as a brownfield contract-hardening phase:

1. redesign the action taxonomy around behavioral, structural, and institutional actions
2. extend feasibility rules so financially unrealistic transitions are blocked explicitly
3. add dependency and conflict modeling so invalid action bundles never look like high-quality plans
