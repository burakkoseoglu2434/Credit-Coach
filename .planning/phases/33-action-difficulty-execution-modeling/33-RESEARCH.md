# Phase 33: Action Difficulty & Execution Modeling - Research

**Researched:** 2026-03-21
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What must change so feasible numeric actions carry explicit difficulty truth, execution aggregation stays weakest-link aware, and business/product surfaces can express follow-through honestly without reopening target generation or feasibility semantics?

## Planning Basis

Phase 33 now has a locked `33-CONTEXT.md`. For this planning pass the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/31-numeric-target-engine/31-CONTEXT.md`
- `.planning/phases/32-feasibility-constraint-engine/32-CONTEXT.md`
- `.planning/phases/33-action-difficulty-execution-modeling/33-CONTEXT.md`
- `credit-coach/src/credit_coach/recourse/execution_probability.py`
- `credit-coach/src/credit_coach/data/schema.py`
- `credit-coach/src/credit_coach/coaching/planner.py`
- `credit-coach/src/credit_coach/coaching/messaging.py`
- `credit-coach/src/credit_coach/cli/run_recourse.py`
- `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`
- `credit-coach/tests/test_recourse_redesign.py`
- `credit-coach/tests/test_planner_denied_objective.py`
- `credit-coach/tests/test_messaging.py`
- `credit-coach/tests/test_portfolio_validation.py`
- `credit-coach/tests/test_phase_experiment_suite.py`
- `credit-coach/tests/test_kpi_contract.py`

This is sufficient because Phase 33 is not introducing a brand-new behavior layer. The repo already contains:

- action- and plan-level execution probabilities
- approval-dependent execution truth
- grouped-action aggregation
- execution-aware ranking
- product messaging that already consumes execution truth
- proof artifacts that already report execution-aware value

The gap is no longer whether execution realism exists. The gap is whether it is expressed through a canonical `difficulty` contract, cleanly separated from feasibility truth, and consistently rendered across ranking, runtime, and product/proof consumers.

## Executive Summary

Phase 31 made targets explicit. Phase 32 made feasibility explicit. Phase 33 must now make execution difficulty explicit.

The existing engine already behaves as if difficulty exists:

- `execution_probability.py` scores burden, horizon, class, ambiguity, and load
- grouped actions already aggregate through a hybrid min/mean posture
- planner ordering already prefers execution-defensible plans
- proof already warns about `high uplift but low follow-through`

What is still missing is one locked contract for:

1. action-level difficulty truth
2. group-first plan execution aggregation
3. the line between feasibility and difficulty
4. business-safe execution wording vs technical execution trace

Phase 33 should therefore be planned as:

`difficulty contract + schema hardening -> aggregation and ranking alignment -> business/technical visibility and proof alignment`

## Existing Assets We Can Reuse

### Execution estimator already exists

- `credit-coach/src/credit_coach/recourse/execution_probability.py`
  - already models:
    - action-class anchors
    - burden and horizon pressure
    - customer context adjustments
    - semantic ambiguity penalties
    - grouped-action aggregation
    - plan-level load penalty
  - is the main seam for adding:
    - `difficulty_score`
    - `difficulty_label`
    - explicit difficulty drivers
    - approval-friction separation

### Schema already carries execution truth

- `credit-coach/src/credit_coach/data/schema.py`
  - already carries:
    - `action_execution_probability`
    - `approval_dependent_probability`
    - `action_group_execution_probability`
    - `plan_execution_probability`
    - `approval_dependent_plan_probability`
  - is the right place to make difficulty canonical instead of implicit

### Planner already uses execution-aware ordering

- `credit-coach/src/credit_coach/coaching/planner.py`
  - already penalizes:
    - low execution probability
    - nominal vs expected improvement gaps
    - weak early health
    - provisional and repaired plans
  - is the natural downstream seam for harder plan-quality interpretation once difficulty truth is explicit

### Messaging and runtime already surface execution truth

- `credit-coach/src/credit_coach/coaching/messaging.py`
  - already carries plan execution inputs into technical reveal
- `credit-coach/src/credit_coach/cli/run_recourse.py`
  - already serializes action and plan execution probabilities

This means Phase 33 can upgrade execution truth without pushing translation responsibility into the website or analyst UI.

### Portfolio proof already depends on execution-aware value

- `credit-coach/src/credit_coach/evaluation/portfolio_validation.py`
  - already reports:
    - execution-weighted expected improvement
    - execution mismatch
    - mixed and failed execution exposure
    - high uplift / low follow-through risk
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - already packages proof artifacts and should remain aligned

This makes portfolio validation a downstream consumer, not a place to invent new Phase 33 semantics.

## What Phase 33 Must Deliver

### 1. Canonical difficulty contract

Phase 33 must lock:

- `difficulty_score`
- `difficulty_label`
- stable difficulty drivers:
  - `burden`
  - `horizon`
  - `action_class`
  - `coordination_load`
  - `approval_friction`

And it must preserve the rule that:

- difficulty describes follow-through burden for a feasible action
- invalid or semantic-break actions receive no difficulty truth

### 2. Explicit group-first execution aggregation

Phase 33 must preserve and harden:

- `action_group_id` first
- then plan-level aggregation
- explicit load penalty
- separate approval-dependent plan truth

The important outcome is not just a score, but a clear engine contract for why multi-action or approval-heavy plans degrade.

### 3. Feasibility vs difficulty separation

Phase 33 must keep these distinct:

- feasibility: can the target stand?
- difficulty: how hard is it to carry through?

This is especially important for:

- repaired actions
- provisional actions
- approval-dependent institution steps

Without this line, the product will keep mixing “conditional” with “hard” and “softened” with “easy”.

### 4. Business-safe execution wording

Phase 33 must not expose raw probabilities by default.

Default product/business output should favor:

- difficulty labels
- follow-through readiness labels
- short risk wording

Technical layers must still carry:

- raw execution probabilities
- grouped execution probabilities
- plan execution truth
- approval friction
- difficulty drivers

## Recommended Plan Split

### Plan 33-01 — Difficulty contract and action-level truth

Focus on:

- explicit `difficulty_score` and `difficulty_label`
- driver-level trace at the action level
- schema and runtime contract hardening
- alive-only difficulty emission

### Plan 33-02 — Group/plan aggregation and ranking leverage

Focus on:

- grouped-action execution truth
- plan-level weakest-link aware aggregation
- load penalty hardening
- planner alignment to the explicit difficulty contract

### Plan 33-03 — Business visibility and proof alignment

Focus on:

- business-safe difficulty/readiness phrasing
- technical reveal execution trace
- runtime serialization completeness
- portfolio/suite/proof consumer alignment

## Main Risks

### Risk 1: Difficulty becomes a duplicate label over existing probability

If Phase 33 only adds a label and not a contract, downstream consumers will keep reverse-engineering the old estimator.

Mitigation:

- lock score, label, and driver semantics in schema and runtime output

### Risk 2: Feasibility and difficulty collapse into one truth again

If repaired or provisional cases are treated as difficulty-only or feasibility-only, the product will misstate why a plan is risky.

Mitigation:

- preserve explicit feasibility precedence from Phase 32 and add difficulty only after survival

### Risk 3: Group aggregation loses business meaning

If grouped actions are flattened into independent low-level items, plan execution truth will understate weakest-link risk and overstate follow-through realism.

Mitigation:

- keep group-first aggregation and explicit load penalty

### Risk 4: Product defaults become too technical

If raw execution probabilities leak into business output, the product will read like engine diagnostics instead of decision intelligence.

Mitigation:

- make labels/default notes canonical in-engine, keep raw probabilities technical-only

## Recommendation

Proceed with Phase 33 now. The codebase already has execution-aware realism; the right move is to turn it into a canonical difficulty contract and align ranking, runtime, and proof around that single truth.
