# Phase 13: Behavior-Aware Recourse - Context

**Gathered:** 2026-03-16
**Status:** Ready for replanning

<domain>
## Phase Boundary

Introduce execution probability modeling, expected-utility scoring, and partial-execution simulation so recommendations better reflect real-world follow-through. This phase extends the Phase 12 typed-action and constraint contract, but it does not create a second planner stack, it does not override inherited fairness, reliability, telemetry, or acceptance gates, and it does not yet redesign the planner into the fully sequential multi-phase system reserved for Phase 14.

</domain>

<decisions>
## Implementation Decisions

### Carry-Forward Decisions From Phases 8-12
- Phase 8 through Phase 11 governance remains authoritative:
  - fairness, reliability, telemetry, and release evidence contracts are inherited guardrails
  - behavior-aware scoring cannot override those gates
- Phase 10 interpretation rules remain authoritative:
  - high-risk tuning remains promotion or ordering evidence, not a gate override
  - machine-readable artifacts remain canonical source of truth
  - markdown review remains derived and explanation-first
- Phase 12 action contract remains authoritative:
  - typed actions stay `hybrid`
  - `action_key` is user-facing
  - `feature_name` remains the effect anchor
  - composite actions stay grouped under `action_group_id`
  - `provisional` approval-dependent actions remain non-winner branches

### Execution Probability Contract
- Canonical probability units are:
  - `action_execution_probability`
  - `plan_execution_probability`
- `action_execution_probability` is the action-level canonical truth
- `plan_execution_probability` is the plan-level canonical summary
- Composite actions must not be treated as fully independent rows for probability aggregation
- For actions sharing the same `action_group_id`:
  - compute a group-level execution probability first
  - then aggregate to the plan level from grouped action units
- `provisional` or approval-required actions must not behave like normal executable actions
- For those actions:
  - `action_execution_probability = null`
  - an optional companion field such as `approval_dependent_probability` may be emitted
  - they must not be used directly in ordinary winner scoring
- The initial Phase 13 estimator may be heuristic or rules-based, but it must be explicit and replaceable
- The initial estimator input family should be limited to:
  - `action_class`
  - `action_key`
  - `time_months`
  - feasibility and constraint status
  - cost, action count, and composite load
  - lightweight customer context
- Historical compliance or real outcome-learning signals are not required in Phase 13 and remain Phase 16 work

### Expected Utility Scoring
- The primary expected-utility impact term is:
  - `expected_pd_improvement = plan_execution_probability × nominal_pd_improvement`
- Phase 13 expected utility remains recommendation-quality evidence rather than a full business-utility objective
- Ranking order must be:
  - constraint, safety, and gate eligibility filters first
  - then expected-utility ranking among eligible plans
  - then normal tie-break and secondary ordering logic
- A gate-failing plan must never outrank a gate-eligible plan because its execution likelihood is higher
- High-risk ranking keeps:
  - `denied_high_risk_lift` as the primary nominal signal
  - `high_risk_profile_applied_rate` activation-floor logic unchanged
- Among otherwise gate-eligible high-risk plans, lower `plan_execution_probability` should reduce ranking quality
- Low execution probability is not a Phase 13 reject condition
- In Phase 13 it should behave as:
  - ranking penalty
  - explanation signal
  - decision-supporting, non-blocking evidence

### Partial Execution Semantics
- Canonical simulation grain is the existing weekly execution loop
- Phase 13 must not invent a disconnected monthly or alternate simulator
- Canonical execution scenario classes are:
  - `full_execution`
  - `mixed_execution`
  - `failed_execution`
- Classification should be driven by aggregate `execution_rate`
- Companion explanation fields should include:
  - `missed_action`
  - `missed_actions_streak`
- Canonical Phase 13 behavior-aware metric set is:
  - `mean_plan_execution_probability`
  - `expected_pd_improvement`
  - `partial_execution_rate`
  - `failed_execution_rate`
  - `mixed_execution_rate`
  - `expected_partial_progress_rate`

### Behavior-Aware Evidence Surface
- Phase 13 must introduce one canonical machine-readable artifact:
  - `behavior_aware_summary.json`
- Required companion breakdown artifacts are:
  - `execution_probability_breakdown.csv`
  - `partial_execution_breakdown.csv`
- The default review section name is:
  - `Behavior-Aware Summary`
- The review should highlight only:
  - `mean_plan_execution_probability`
  - `expected_pd_improvement`
  - `mixed_execution_rate`
  - `failed_execution_rate`
  - `expected_partial_progress_rate`
- The review must remain explanation-first and must not become a dashboard
- In the seeded suite and challenger contract, behavior-aware evidence is:
  - mandatory supporting evidence
  - non-blocking
  - not release-defining
  - not acceptance-defining in Phase 13
- Suite and challenger should carry this evidence through aggregate summaries and `supporting_artifacts` without redefining the primary KPI or milestone-acceptance contract

### Claude's Discretion
- Exact aggregation formula for group-level execution probability as long as grouped composite actions are not treated as fully independent rows
- Exact heuristic weighting inside the first execution-probability estimator as long as the locked input family remains explicit and testable
- Exact thresholding used to separate `mixed_execution` from `failed_execution` as long as aggregate `execution_rate` remains the primary classification basis
- Exact JSON nesting for `behavior_aware_summary.json` and companion breakdowns as long as the locked field names and section labels remain explicit

</decisions>

<specifics>
## Specific Ideas

- Execution-likelihood fields should read like recommendation-quality evidence, not opaque modeling internals
- Approval-dependent institutional actions should stay visible as machine-readable evidence without being ranked like ordinary executable actions
- Expected utility should help answer "which safe plan is more realistic to complete?" rather than "which plan may ignore the gate contract?"
- The behavior-aware review should stay readable in under a couple of minutes without forcing users into raw CSVs

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `credit-coach/src/credit_coach/data/schema.py`
  - `PlanAction` and `PlanRecord` already carry typed-action, timing, and constraint metadata, making them the natural seam for execution-likelihood fields
- `credit-coach/src/credit_coach/recourse/generator.py`
  - already builds action objects, attaches typed metadata, and records realism diagnostics, so it is the right hook for action- and plan-level execution probability
- `credit-coach/src/credit_coach/coaching/planner.py`
  - already has gate-aware ranking logic, making it the correct seam for expected-utility ordering after eligibility filters
- `credit-coach/src/credit_coach/coaching/loop.py`
  - already simulates planned versus executed actions, missed actions, execution rate, and replan behavior, so it should become the canonical partial-execution seam
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - already emits candidate-quality, trajectory, and action-realism summaries under stable batch artifacts, making it the natural owner for `behavior_aware_summary.json`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - already aggregates machine-readable seeded evidence and can promote behavior-aware evidence into supporting artifacts
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`
  - already compares seeded variant performance and can carry behavior-aware evidence into control-relative comparisons without redefining the KPI contract

### Established Patterns
- Canonical machine-readable evidence lives under `artifacts/runs/<run_id>/tables/`
- Release and acceptance semantics are already centralized and should remain separate from behavior-aware evidence
- High-risk interpretation uses a primary metric plus supporting evidence model rather than a single synthetic score
- Existing weekly coaching simulation already provides the brownfield behavior seam; Phase 13 should extend it rather than replace it

### Integration Points
- Phase 13 changes should primarily hook into:
  - `credit-coach/src/credit_coach/data/schema.py`
  - `credit-coach/src/credit_coach/recourse/generator.py`
  - `credit-coach/src/credit_coach/recourse/execution_probability.py`
  - `credit-coach/src/credit_coach/coaching/planner.py`
  - `credit-coach/src/credit_coach/coaching/loop.py`
  - `credit-coach/src/credit_coach/cli/run_recourse.py`
  - `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`
- Regression coverage should extend through:
  - `credit-coach/tests/test_recourse_redesign.py`
  - `credit-coach/tests/test_robust_recourse.py`
  - `credit-coach/tests/test_planner_denied_objective.py`
  - `credit-coach/tests/test_sequential_recourse.py`
  - `credit-coach/tests/test_recourse_funnel_kpis.py`
  - `credit-coach/tests/test_batch_candidate_diversity.py`
  - `credit-coach/tests/test_phase_experiment_suite.py`
  - `credit-coach/tests/test_challenger_matrix_selection.py`

</code_context>

<deferred>
## Deferred Ideas

- A learned execution-probability model grounded in real outcome or compliance history remains later work once Phase 16 learning loops are in place
- A hard floor that rejects very low-probability plans can be revisited after real outcome evidence exists
- Full business-utility expansion beyond `expected_pd_improvement` remains later policy-optimization and learning-loop work
- Fully multi-phase trajectory redesign remains Phase 14 rather than Phase 13

</deferred>

---
*Phase: 13-behavior-aware-recourse*
*Context gathered: 2026-03-16*
