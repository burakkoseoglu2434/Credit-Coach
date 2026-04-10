# Phase 67: Execution & Outcome Realization - Context

**Gathered:** 2026-04-10
**Status:** Ready for planning after roadmap insertion

<domain>
## Phase Boundary

This future phase adds a deterministic, additive tracking layer that measures whether selected-path recommendations were actually executed and whether they produced observed downstream movement.

This phase owns:
- execution tracking for selected-path actions after a decision is issued
- deterministic realized-outcome definitions using observed follow-up data
- additive effectiveness metrics for action execution, path realization, and outcome improvement
- a minimal storage contract linking recommendation truth to observed execution and outcome truth
- evaluation/reporting artifacts that compare predicted realization against observed realization

This phase does not own:
- changes to core decision logic, recoverability, gating, ranking, or winner selection
- new action types, new recourse modes, or threshold redesign
- causal policy claims, online learning, or automatic policy promotion
- broad customer/product narrative redesign
- live institution integrations beyond additive ingestion of observed events or CSV-based refreshes

Guardrails:
- the selected decision and selected path remain the canonical parent unit
- tracking is additive and descriptive before it is causal
- runtime-emitted recommendation truth stays canonical
- missing data must degrade to explicit `pending` or `not_observed`, never inferred completion

</domain>

<decisions>
## Implementation Decisions

### Canonical tracking unit
- The parent tracking unit should remain the logged selected decision and selected path, not the full candidate set.
- First-wave execution tracking should scope only to actions from the selected path.
- Candidate actions that were not selected should not receive observed-execution tracking in this phase.
- The canonical linkage chain should be:
  - `decision_id`
  - `customer_id`
  - `selected_plan_id`
  - `selected_path_id` when available
  - `action_key`
- Path realization should be derived from selected-path action observations rather than from planner probabilities alone.

### Minimum viable action execution model
- The minimum viable model should use append-only observed action events plus deterministic derived status.
- First-wave event types should be:
  - `attempted`
  - `completed`
  - `blocked`
  - `reversed`
- `recommended` should not be duplicated as a new event because recommendation truth already exists in canonical run artifacts.
- The derived action-level status should be one of:
  - `not_observed`
  - `attempted`
  - `completed`
  - `blocked`
  - `reversed`
- Status should be derived deterministically from the latest known event by precedence, never from heuristic guesswork.
- A path should be considered `realized` only when at least one selected action is observed `completed`.
- A path should be considered `blocked` when no selected action is completed and at least one blocking event is observed.

### Realized outcome definition
- Outcome measurement should remain multi-axis rather than collapsing immediately into one hidden score.
- The minimum realized outcome axes should be:
  - execution outcome: were selected actions attempted or completed
  - movement outcome: did follow-up approval distance improve
  - decision outcome: did the customer move from `REJECTED` to `CONDITIONAL` or `APPROVED`
  - downside outcome: did observed default or payment behavior materially worsen
- First-wave realized customer outcome labels should be:
  - `pending_observation`
  - `no_observed_progress`
  - `partial_progress`
  - `threshold_reached`
  - `approval_realized`
  - `negative_outcome`
- `partial_progress` should mean observed improvement without threshold reach.
- `threshold_reached` should mean the follow-up state indicates the approval threshold was crossed, even if institution approval is not yet explicitly realized.
- `approval_realized` should remain the strongest realized outcome and should require an observed positive decision-state change, not just modeled potential.
- Existing observed payment/default/margin/recovery fields remain additive realized evidence; they should not be replaced by a single synthetic outcome label.

### Time windows and time-to-impact
- The primary outcome window should remain `90d`, inherited from the existing outcome-feedback contract.
- First-wave supporting windows should be:
  - `30d` for early execution uptake
  - `90d` for realized movement and realized approval
- `60d` may remain available as supporting evidence but should not be the primary contract.
- The first required latency metrics should be:
  - `time_to_first_execution_days`
  - `time_to_first_completed_action_days`
  - `time_to_realized_outcome_days`
- If timestamps are missing, latency metrics must be null rather than imputed.

### Attribution posture
- First-wave attribution should be descriptive and path-level, not causal and not action-isolating.
- The selected path may receive observational credit for realized outcomes only when the outcome is evaluated after the selected recommendation was issued.
- Action-level effectiveness should be reported as association, not causal proof.
- When multiple selected actions are completed, the system should attribute realized outcome to the selected path as a whole, not declare a single winning action.
- This phase should explicitly avoid downstream claims such as:
  - “action X caused approval”
  - “path Y caused margin lift”
- Stronger attribution, off-policy reuse, or causal decomposition belong to later work.

### Minimal effectiveness metric contract
- The minimum top-line metrics should be:
  - `action_execution_rate`
  - `action_completion_rate`
  - `blocked_action_rate`
  - `path_realization_rate`
  - `realized_movement_rate`
  - `threshold_reach_realization_rate`
  - `approval_realization_rate`
  - `negative_outcome_rate`
  - `observation_coverage_rate`
  - `time_to_first_execution_days`
  - `time_to_realized_outcome_days`
- The minimum comparison cuts should be:
  - by `recourse_mode`
  - by `recoverable_flag`
  - by selected-path type (`customer_only`, `institution_assisted`, `hybrid`)
  - by selected-path movement strength
- Limited mode should remain visible as an honesty/control population, but first-wave execution metrics should expect sparse or null action realization there.
- Predicted-versus-observed comparison should be additive:
  - `plan_execution_probability` vs observed action/path execution
  - `combined_plan_realization_probability` vs observed realized outcome

### Minimal data schema
- The existing `DecisionOutcomeRecord` should remain the parent observed-outcome record.
- First-wave should extend the existing outcome seam rather than create a disconnected execution system.
- The minimum additive parent fields to log or preserve with realized-outcome data should include:
  - `selected_path_id` when available
  - `selected_path_type`
  - `selected_path_movement_strength`
  - `recourse_mode`
  - `recoverable_flag`
  - `movement_score`
  - `threshold_reach_probability`
- A new companion action-execution record should be introduced for selected-path actions only.
- The minimum action-execution event fields should be:
  - `decision_id`
  - `customer_id`
  - `selected_plan_id`
  - `selected_path_id`
  - `action_key`
  - `event_type`
  - `event_at`
  - `event_source`
  - `evidence_reference` or equivalent raw-source pointer
- `event_source` should stay explicit and narrow, for example:
  - `manual_review`
  - `batch_refresh`
  - `self_report`
  - `servicer_signal`
- The schema should remain additive and audit-safe; no existing decision or plan tables should be reinterpreted.

### Evaluation and artifact plan
- This phase should extend the existing outcome-feedback flow rather than invent a second feedback CLI.
- The primary integration seam should remain:
  - `run_outcome_feedback.py`
  - repository-backed summaries
  - additive machine-readable artifacts under `artifacts/runs/.../tables`
- The minimum new artifact family should be:
  - `action_execution_summary.csv`
  - `path_realization_summary.json`
  - `outcome_realization_summary.json`
  - `outcome_realization_report.md`
- Existing outcome-feedback and learning artifacts should remain present and compatible.
- The canonical human-readable artifact should be `outcome_realization_report.md`.
- The report should answer:
  - were actions executed
  - did selected paths realize
  - did realized movement or approval follow
  - where is evidence still pending or weak

### Claude's Discretion
- Exact naming of new event tables and artifact files, as long as they remain clearly scoped to execution and realized outcomes.
- Exact precedence logic for deriving action status from multiple events, as long as it is deterministic and documented.
- Exact thresholding for `partial_progress` vs `negative_outcome`, as long as it is runtime-first and auditable from stored observations.

</decisions>

<specifics>
## Specific Ideas

- Reuse the older Phase 16 learning-loop seam, but shift the emphasis from policy-arm comparison toward recommendation execution and observed realization.
- Keep the first wave deliberately small: selected path only, observed events only, no customer-wide behavior ledger.
- Treat `recoverable/full` customers as the primary realized-outcome population and `limited` customers as an honesty/control slice.
- Prefer explicit observation gaps over optimistic inference; `pending_observation` is better than fake success.
- Compare predicted realization probabilities against observed execution/outcome rates, but do not turn that comparison into automatic policy updates.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- [run_outcome_feedback.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_outcome_feedback.py): already ingests delayed outcome CSV rows and writes machine-readable outcome artifacts, making it the natural seam for additive execution/outcome realization extensions.
- [DecisionOutcomeRecord](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py): already carries decision identity, selected-plan linkage, planner probabilities, action completion, offer acceptance, and delayed 90-day outcomes.
- [repository.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/storage/repository.py): already owns `save_decision_outcome`, decision-log completeness, outcome-ingestion summaries, learning-dataset loading, and policy delta reporting.
- [test_outcome_feedback.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/tests/test_outcome_feedback.py): already proves the current outcome-feedback seam and can be extended with execution-event and realized-outcome coverage tests.
- [16-CONTEXT.md](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/.planning/phases/16-outcome-feedback-learning-loop/16-CONTEXT.md): already locked the brownfield outcome-feedback posture, 90-day primary window, graded observation completeness, and non-causal reporting discipline.

### Established Patterns
- Outcome and learning evidence already live in repository-backed, machine-readable artifacts rather than frontend recomputation.
- The codebase prefers additive companion evidence over replacing existing summaries.
- The 90-day window is already the canonical realized-outcome horizon.
- Audit-safe storage and explicit coverage summaries are established patterns; missing observations should be visible by dimension rather than hidden.

### Integration Points
- Extend [DecisionOutcomeRecord](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py) and related persistence models only additively for path/action realization metadata.
- Introduce selected-action execution storage alongside the existing repository outcome context instead of building a detached event service.
- Extend [run_outcome_feedback.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_outcome_feedback.py) to ingest action-execution observations and emit realization artifacts.
- Reuse the current cohort and targeted-evaluation truth when slicing realized outcomes by recoverable/full vs limited/control posture.

### Brownfield Risks
- The repository does not have a formal migration framework, so new persistence must stay small, additive, and reversible.
- Existing outcome storage is decision-centric and relatively compact; path/action realization detail must not bloat it into a duplicate plan archive.
- Action execution data may arrive sparsely or unevenly across event sources, so completeness semantics must remain explicit and conservative.

</code_context>

<deferred>
## Deferred Ideas

- Causal attribution or single-action credit assignment
- Online learning, policy auto-promotion, or adaptive routing
- Live institution-side action confirmation integrations
- Customer-wide behavioral event streams unrelated to the selected path
- New decision logic that changes recoverability, ranking, or recommendation generation based on realized outcomes

</deferred>

---
*Phase: 67-execution-outcome-realization*
*Context gathered: 2026-04-10*
