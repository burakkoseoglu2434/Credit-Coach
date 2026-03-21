# Phase 32: Feasibility & Constraint Engine - Research

**Researched:** 2026-03-21
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What must change so Phase 31's customer-specific numeric targets become explicitly feasible, safely repairable when meaning survives, and invalid when semantic or dependency truth breaks?

## Planning Basis

Phase 32 now has a locked `32-CONTEXT.md`. For this planning pass the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/31-numeric-target-engine/31-CONTEXT.md`
- `.planning/phases/32-feasibility-constraint-engine/32-CONTEXT.md`
- `credit-coach/src/credit_coach/recourse/feasibility.py`
- `credit-coach/src/credit_coach/recourse/action_constraints.py`
- `credit-coach/src/credit_coach/data/schema.py`
- `credit-coach/src/credit_coach/coaching/planner.py`
- `credit-coach/src/credit_coach/safety/validator.py`
- `credit-coach/src/credit_coach/coaching/messaging.py`
- `credit-coach/src/credit_coach/cli/run_recourse.py`
- `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`
- `credit-coach/tests/test_recourse_feasibility.py`
- `credit-coach/tests/test_recourse_redesign.py`
- `credit-coach/tests/test_planner_denied_objective.py`
- `credit-coach/tests/test_messaging.py`
- `credit-coach/tests/test_portfolio_validation.py`

This is sufficient because Phase 32 is not inventing a new feasibility layer from scratch. The repo already contains:

- target-level feasibility checks and clip diagnostics in `recourse/feasibility.py`
- prerequisite, conflict, and provisional handling in `recourse/action_constraints.py`
- action- and plan-level status fields in `data/schema.py`
- ranking penalties and preference ordering in `coaching/planner.py`
- downstream visibility seams in messaging, runtime serialization, and portfolio validation

The gap is no longer whether constraints exist. The gap is whether feasibility truth is canonical, deterministic, and product-safe now that numeric targets are explicit.

## Executive Summary

Phase 31 made numeric targets explicit. Phase 32 must now make feasibility truth explicit in the same way.

The codebase already has the important raw pieces:

- numeric clipping and semantic-loss detection
- repair-drop and provisional logic
- downstream ranking that distinguishes `valid`, `repaired`, and `provisional`
- product and proof surfaces that can already separate business and technical views

What is still missing is a single locked contract for:

1. action-level feasibility verdicts
2. plan-level rollup precedence
3. constraint-family classification
4. safe repair vs true invalidation
5. business-safe vs technical visibility

Phase 32 should therefore be planned as:

`verdict and family normalization -> repair/reject rollup hardening -> downstream visibility and artifact alignment`

## Existing Assets We Can Reuse

### Target-level feasibility engine already exists

- `credit-coach/src/credit_coach/recourse/feasibility.py`
  - already applies target-level realism checks
  - already emits detailed reason codes and clip metadata
  - already knows about semantic loss after clipping

This is the right seam for canonical action-level verdicts and reason-family normalization.

### Dependency and interaction logic already exists

- `credit-coach/src/credit_coach/recourse/action_constraints.py`
  - already handles:
    - prerequisites
    - incompatible combinations
    - repair-drop behavior
    - approval-pending/provisional branches

This is the right seam for:

- `interaction` family truth
- `dependency` family truth
- repair-if-safe semantics

### Schema already carries feasibility-adjacent truth

- `credit-coach/src/credit_coach/data/schema.py`
  - already carries:
    - `action_status`
    - `constraint_status`
    - `constraint_reason`
    - `constraint_trace`
    - `technical_reveal`

This is the right seam to lock:

- canonical verdict vocabulary
- plan-level rollup meaning
- business vs technical visibility boundaries

### Ranking and validation already consume feasibility truth

- `credit-coach/src/credit_coach/coaching/planner.py`
  - already ranks `valid`, `repaired`, `provisional`, and `invalid` differently
- `credit-coach/src/credit_coach/safety/validator.py`
  - already turns constraint truth into status/reason language
- `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`
  - already distinguishes valid vs repaired vs provisional in portfolio coverage logic

This means Phase 32 can harden contract semantics without inventing a second proof or ranking stack.

## What Phase 32 Must Deliver

### 1. Canonical feasibility verdict contract

Phase 32 must lock:

- action-level verdict set:
  - `valid`
  - `clipped`
  - `repaired`
  - `provisional`
  - `invalid`
- plan-level precedence:
  - `invalid`
  - `provisional`
  - `repaired`
  - `valid`

And it must preserve the important distinction that:

- `clipped` is an action-level realism truth
- `provisional` is dependency-gated realism, not failure

### 2. Canonical constraint-family layer

Phase 32 must introduce a stable rollup layer over legacy reason codes:

- `capacity`
- `policy`
- `dependency`
- `interaction`
- `semantic`
- `documentation`

This is essential for:

- technical trace readability
- batch and validation summaries
- later business-safe wording in Phase 35+

### 3. Repair-if-safe / reject-if-semantic-break posture

Phase 32 must explicitly encode:

- when clipping is still acceptable
- when repair is allowed
- when a plan must die because the primary action meaning is gone

The locked posture is:

- preserve meaning if possible
- reject when the action no longer means what it claimed to mean

### 4. Visibility split for feasibility truth

Phase 32 must not leak raw constraint internals into business defaults.

Business default should carry only outcome labels such as:

- directly feasible
- softened but usable
- dependency-gated / conditional

Technical layers must still carry:

- constraint family
- granular reason code
- clip or repair truth
- semantic preservation state

## Recommended Plan Split

### Plan 32-01 — Verdict and constraint-family normalization

Focus on:

- canonical action-level verdict vocabulary
- plan-level precedence rules
- constraint-family classification over existing reason codes
- schema and trace normalization

### Plan 32-02 — Repair/reject posture and ranking-safe rollups

Focus on:

- repair-if-safe semantics
- direct invalid triggers
- grouped-action primary-meaning preservation
- repaired/provisional plan rollup and ranking alignment

### Plan 32-03 — Business vs technical feasibility visibility

Focus on:

- business-safe outcome labels
- technical reveal minimum fields
- runtime, messaging, validator, and portfolio consumer alignment
- regression closure and artifact hygiene

## Main Risks

### Risk 1: Phase 32 duplicates old feasibility behavior instead of hardening it

If plan and action verdict semantics stay partially implicit, numeric targets become explicit but feasibility remains fuzzy.

Mitigation:

- lock action-level verdicts and plan-level precedence in schema and downstream consumers

### Risk 2: Repair logic preserves dead plans

If repair drops the main business action but keeps technical residue, low-quality plans may still survive.

Mitigation:

- enforce primary-action meaning preservation as the survival test

### Risk 3: Provisional branches get mislabeled as infeasible

If dependency-gated actions collapse into invalid or generic failure buckets, product and analyst trust erode.

Mitigation:

- keep `provisional` explicit and separate from feasibility failure

### Risk 4: Technical trace leaks into business defaults

If raw reason codes or clip math surface by default, the product layer becomes too engine-native.

Mitigation:

- lock the business/technical visibility split in engine-owned consumers now rather than later

## Recommendation

Proceed with Phase 32 now. The repo already has strong feasibility, constraint, and ranking seams; the correct move is to normalize them around the new numeric-target contract rather than layering new ad hoc checks on top.
