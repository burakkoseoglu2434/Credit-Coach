# Phase 42 — Planner Quality & Source Mix Context

**Last updated:** 2026-03-23
**Status:** Discussed and locked
**Milestone:** `v2.1 Decision Ownership & Pilot-Ready Trust`
**Requirements:** `PLAN-01`

## Phase Boundary

Phase 42 does **not** redesign:

- Phase 40 contract normalization or parity-safe artifact ownership
- Phase 40.5 deterministic customer-level decision policy
- Phase 41 calibration math, cohort semantics, or reporting structure
- Phase 43 operator packet or briefing UX
- Phase 44 production pilot workflow

Phase 42 **does** own:

- best-plan source mix truth and reporting
- zero-action and semantically empty contender removal
- internal vs `dice` competitiveness measurement
- honest positioning of `rule` and `fallback` as recovery lanes
- action diversity guardrails for candidate pools and best-plan winners
- offer maturity hardening inside planner-quality evaluation

Guardrails:

- operator and business-facing outputs must keep consuming existing decision truth
- Phase 42 may improve candidate quality and best-plan selection honesty, but it must not create a second decision system
- any source preference may only break near-ties; it may not overturn a materially better contender from another lane

## Exact Goal

Improve the quality and credibility of the underlying plan candidates so the decision system is not overly dependent on weak, empty, or single-source best plans.

## Area 1 — Best-Plan Source Mix Contract

### Locked Decisions

1. Canonical source catalog:
   - `internal`
   - `dice`
   - `rule`
   - `fallback`
2. Canonical source truth must live on an explicit `plan_source` field on `PlanRecord`
3. `plan_id` parsing may remain only as a backward-compatible fallback
4. Source mix reporting is first-class at two levels:
   - customer-level:
     - `best_plan_source`
     - `candidate_source_counts`
     - `candidate_source_presence_flags`
   - collection-level:
     - `best_source_*_rate`
     - `candidate_source_entropy`
     - `candidate_pool_diversity_index`
     - `source_mix_by_risk_band`
5. Secondary supporting lens may include:
   - `source_mix_by_expected_readiness`
6. Honesty rule:
   - `fallback` must never be reported as normal planner success
   - `rule` and `fallback` must appear as recovery lanes / last-resort lanes
   - main planner competitiveness axis is `internal vs dice`

### Guardrails

- source mix is provenance truth, not marketing copy
- batch, single-customer, collection, and calibration artifacts must all use the same source vocabulary

## Area 2 — Zero-Action / Empty Contender Removal

### Locked Decisions

1. Canonical empty contender definition includes:
   - `action_count == 0`
   - business-semantic no-op plans that produce no customer or operator movement
   - invalid or pure shell plans with no real path
2. Empty contender diagnostics should distinguish at least:
   - `ZERO_ACTION`
   - `SEMANTIC_EMPTY`
3. Empty contender removal happens:
   - after candidate generation
   - after candidate diagnostics
   - before best-plan selection
4. Empty contenders remain visible in diagnostics and source-mix accounting
5. Global hard rule:
   - empty contenders can never become best plans
6. Recommended diagnostics fields:
   - `empty_candidate_removed`
   - `empty_candidate_reason`
7. `approval-pending only` plans are **not** treated as fully empty
8. Canonical contender buckets:
   - `ACTIONABLE`
   - `APPROVAL_SHELL_ONLY`
   - `EMPTY`
9. Selection posture by bucket:
   - `ACTIONABLE` competes normally
   - `APPROVAL_SHELL_ONLY` may compete with penalty
   - `EMPTY` is removed before selection

### Guardrails

- Phase 40.5 zero-step rejection remains true at the final decision layer
- Phase 42 pushes the same honesty earlier into contender filtering so empty winners disappear before they can shape decision truth

## Area 3 — Internal vs Dice vs Rule vs Fallback Evaluation

### Locked Decisions

1. Core comparison axis:
   - `internal vs dice`
2. Supporting and recovery lanes:
   - `rule`
   - `fallback`
3. Required lane-quality metrics:
   - `best_win_share`
   - `gate_pass_share`
   - `non_empty_contender_share`
   - `approved_or_conditional_contender_share`
   - `mean_execution_aware_value`
4. Optional supporting metric:
   - `offer_ready_contender_share`
5. Source-aware tie-break is allowed only as a light near-tie preference
6. Preferred order in near-tie situations:
   - `ACTIONABLE internal`
   - `ACTIONABLE dice`
   - `rule`
   - `fallback`
7. Hard guardrail:
   - source preference may break ties
   - source preference may not overturn a materially better contender from another lane
8. Collection summary wording must separate:
   - planner competitiveness:
     - `internal vs dice competitiveness`
     - `internal best-win share`
     - `dice best-win share`
   - recovery lanes:
     - `rule rescue rate`
     - `fallback rescue rate`

### Guardrails

- `rule` and `fallback` can be valuable for system resilience
- they must not inflate the perceived competitiveness of the main planner

## Area 4 — Action Diversity And Offer Maturity Hardening

### Locked Decisions

1. Diversity is measured separately for:
   - `candidate-pool action diversity`
   - `best-plan action diversity`
2. Minimum diversity lenses:
   - `action_class mix`
   - `action_family spread`
3. Diversity target is:
   - `anti-collapse guardrail`
   - not a hard quota system
4. Warning semantics:
   - single `action_class` dominance in winners = warning
   - single `action_family` dominance in winners = warning
   - sustained collapse to one winning type = red flag
5. Canonical offer maturity taxonomy:
   - `none`
   - `inactive`
   - `provisional`
   - `active_rankable`
6. Planner-quality offer treatment:
   - `active_rankable` = full contender value
   - `provisional` = discounted contender value
   - `inactive` = heavier discount
   - `approval_shell_only` = separate penalty tag
7. Required lane-level offer maturity metrics:
   - `offer_ready_contender_share`
   - `provisional_offer_share`
   - `approval_shell_only_share`

### Guardrails

- the goal is not forced balance across action types
- the goal is to expose and reduce planner collapse while keeping institution-ready maturity visible

## Likely Code Seams

- `credit-coach/src/credit_coach/coaching/planner.py`
- `credit-coach/src/credit_coach/cli/run_recourse.py`
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- `credit-coach/src/credit_coach/decision/ownership.py`
- `credit-coach/src/credit_coach/evaluation/decision_calibration.py`
- `credit-coach/src/credit_coach/data/schema.py`
- `credit-coach/tests/test_planner_denied_objective.py`
- `credit-coach/tests/test_recourse_redesign.py`
- `credit-coach/tests/test_customer_artifact_collection.py`

## Phase-Local Success Definition

Phase 42 is successful when:

- empty and semantically empty contenders cannot win best-plan selection
- source truth is explicit and consistent across single-customer, batch, and collection artifacts
- internal planner competitiveness can be measured honestly against `dice`
- `rule` and `fallback` are reported as recovery lanes instead of normal planner success
- action diversity and offer maturity can be reviewed as planner-quality signals without changing Phase 40.5 decision ownership
