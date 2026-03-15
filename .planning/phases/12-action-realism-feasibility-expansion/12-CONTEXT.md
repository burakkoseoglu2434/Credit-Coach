# Phase 12: Action Realism & Feasibility Expansion - Context

**Gathered:** 2026-03-15
**Status:** Ready for replanning

<domain>
## Phase Boundary

Expand the current recourse engine so recommendations can be expressed as real-world behavioral, structural, and institutional actions while preserving the existing feature-grounded planner, phased trajectory outputs, and inherited governance gates. This phase hardens action semantics, feasibility realism, and interaction constraints; it does not yet introduce execution probability, expected utility scoring, or new end-user product surfaces.

</domain>

<decisions>
## Implementation Decisions

### Carry-Forward Decisions From Phases 8-11
- Phase 8 through Phase 11 governance remains authoritative:
  - fairness, reliability, telemetry, and release evidence contracts are inherited guardrails
  - recommendation realism cannot override those gates
- Machine-readable artifacts remain the canonical source of truth
- Markdown review remains derived and explanation-first rather than dashboard-like
- Phase 12 is still a contract-hardening phase, not a behavior-modeling or policy-optimization phase

### Canonical Action Unit
- The primary action unit for Phase 12 is `hybrid`
- Each real-world recommendation should carry a user-facing `action_key`
- Existing `feature_name` remains the effect anchor for the current generator and planner stack
- Composite actions should be represented as multiple `PlanAction` rows sharing one `action_group_id`
- Phase 12 must not introduce a second plan object or a parallel planner data model
- Institutional actions must satisfy one of two explicit states:
  - they resolve to one or more concrete feature effects
  - or they are carried as an approval-gated placeholder with explicit machine-readable status
- Institutional actions must never silently degrade into no-op recommendations

### Realism Gate Semantics
- Realism handling should be action-class aware rather than one-size-fits-all
- Default behavior by action class:
  - `behavioral` actions are `clip-first`
  - `structural` actions may be `clip` or `reject`
  - `institutional` actions may become `reason-coded provisional` or `reject`
- Clipping is only allowed when the action still preserves the same real-world intent after adjustment
- If clipping would make the action semantically meaningless, effectively no-op, or inconsistent with its prerequisite or stated intent, the action must be rejected
- Missing prerequisite or institutional approval is not a numeric feasibility problem and must not be handled by clipping
- Approval or prerequisite failures must be surfaced as explicit `provisional` or `invalid` states with reason-coded diagnostics
- Final ranking eligibility is restricted to:
  - fully valid candidates
  - clipped candidates that still preserve valid semantics
- Approval-pending and unmet-prerequisite candidates may remain as evidence, but they must not appear as ordinary top-ranked recommendations in Phase 12

### Dependency and Approval Behavior
- Conflict handling should default to `repair-if-safe`
- If an invalid action can be removed while preserving a coherent remaining plan, the plan may be repaired
- If removing the invalid action breaks the remaining plan semantics, the full plan becomes invalid
- `requires` relationships are hard prerequisites, not warnings
- If a required action is missing, the dependent action is invalid
- `institutional approval required` actions should not automatically invalidate an entire plan
- Approval-required actions should instead remain as `provisional` branches that cannot become the normal winner plan
- Repair behavior must never be silent
- Machine-readable repair evidence must record at minimum:
  - which action was dropped
  - why it was dropped
  - how the repaired plan maps back to the original action or group relationship

### Action-Realism Evidence Contract
- Phase 12 must introduce one canonical machine-readable realism artifact:
  - `action_realism_summary.json`
- The minimum canonical metric set is:
  - `action_type_behavioral_rate`
  - `action_type_structural_rate`
  - `action_type_institutional_rate`
  - `composite_action_rate`
  - `clipped_action_rate`
  - `rejected_action_rate`
  - `repair_applied_rate`
  - `approval_pending_action_rate`
  - `invalid_combination_rate`
  - `infeasible_plan_rate`
- `dominant_rejection_reason` should also be surfaced in the canonical summary so the review can stay concise
- Required companion breakdown artifacts are:
  - `action_type_breakdown.csv`
  - `feasibility_rejection_breakdown.csv`
  - `constraint_repair_breakdown.csv`
  - `approval_pending_breakdown.csv`
- The Phase 12 review surface should add a short `Action Realism Summary` section that highlights:
  - action mix
  - infeasible, rejected, and repaired rates
  - approval-pending load
  - dominant rejection reason
- The review must remain explanation-first and must not become a large dashboard

### Claude's Discretion
- Exact field nesting for hybrid action metadata as long as `action_key`, `feature_name`, and `action_group_id` remain explicit and testable
- Exact reason-code naming for clip, reject, provisional, and repair outcomes as long as they stay machine-readable and stable
- Whether repair evaluation lives mostly in generator code or in a dedicated constraint helper module, as long as the locked repair semantics and traces are preserved
- Exact Markdown wording inside the derived `Action Realism Summary` section as long as the required signals remain visible

</decisions>

<specifics>
## Specific Ideas

- User-facing actions should read like real interventions such as `reduce_spending`, `debt_consolidation`, `installment_plan`, or `grace_period` rather than pure feature edits
- The hybrid model should let plans display `action_key` while still preserving `feature_name` as the engine-facing anchor
- Composite actions should be serialized under a shared `action_group_id` instead of inventing a second plan structure
- Institutional placeholders should be explicit, for example through fields like `requires_institutional_approval` and an approval-pending state
- Review summaries should surface `dominant_rejection_reason` directly instead of forcing humans to scan raw breakdown CSVs

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `credit-coach/src/credit_coach/data/schema.py`
  - `PlanAction` and `PlanRecord` already support multi-action plans plus phase and week metadata, making them the right seam for hybrid action enrichment
- `credit-coach/src/credit_coach/recourse/action_space.py`
  - `ActionSpec`, `ACTION_SPACE`, and helper functions already centralize action definitions and are the natural home for typed action taxonomy metadata
- `credit-coach/src/credit_coach/recourse/generator.py`
  - `_build_actions(...)` already constructs `PlanAction` objects and applies feasibility before actions are emitted, making it the main hook for hybrid action construction and reason-coded filtering
- `credit-coach/src/credit_coach/recourse/feasibility.py`
  - `apply_target_feasibility(...)` already supports cap-style rules and should stay the base seam for richer realism constraints
- `credit-coach/src/credit_coach/cli/run_recourse.py`
  - already serializes phased plan outputs and is the right place to expose richer action semantics without losing roadmap-style trajectory behavior
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - already emits `feasibility_gate` style diagnostics, trajectory phase counts, and candidate-quality summaries, making it the best place to publish Phase 12 realism evidence
- `credit-coach/src/credit_coach/coaching/planner.py`
  - already ranks plans with gate-aware objectives and is the seam that must respect repaired versus invalid bundles
- `credit-coach/src/credit_coach/causality/action_constraints.py`
  - already proves the repo accepts machine-readable action constraints, even though Phase 12 needs a richer recourse-specific dependency and conflict layer

### Established Patterns
- Feature-grounded action effects remain the brownfield execution seam, so richer semantics should wrap them rather than replace them
- Canonical evidence continues to live in JSON and CSV artifacts under `artifacts/runs/<run_id>/tables/`
- Markdown review is derived from canonical artifacts instead of becoming a parallel handwritten source of truth
- Existing diagnostics already use reason-coded statuses such as `feasibility_gate`, which Phase 12 should extend rather than sidestep
- Existing phased trajectory fields such as `phase_id`, `week_start`, `week_end`, and `trajectory_phase_1_action_count` should remain stable under richer action semantics

### Integration Points
- Phase 12 changes must primarily hook into:
  - `credit-coach/src/credit_coach/data/schema.py`
  - `credit-coach/src/credit_coach/recourse/action_space.py`
  - `credit-coach/src/credit_coach/recourse/feasibility.py`
  - `credit-coach/src/credit_coach/recourse/generator.py`
  - `credit-coach/src/credit_coach/recourse/action_constraints.py`
  - `credit-coach/src/credit_coach/coaching/planner.py`
  - `credit-coach/src/credit_coach/cli/run_recourse.py`
  - `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- Regression coverage should extend through:
  - `credit-coach/tests/test_action_space.py`
  - `credit-coach/tests/test_recourse_feasibility.py`
  - `credit-coach/tests/test_recourse_redesign.py`
  - `credit-coach/tests/test_recourse_generator_action_budget.py`
  - `credit-coach/tests/test_planner_denied_objective.py`
  - `credit-coach/tests/test_recourse_funnel_kpis.py`

</code_context>

<deferred>
## Deferred Ideas

- Execution probability, expected utility scoring, and partial-execution simulation belong to Phase 13 rather than Phase 12
- Multi-phase optimization beyond the current phased metadata remains Phase 14 work
- Offer optimization and acceptance modeling remain later milestone phases rather than being pulled into Phase 12

</deferred>

---
*Phase: 12-action-realism-feasibility-expansion*
*Context gathered: 2026-03-15*
