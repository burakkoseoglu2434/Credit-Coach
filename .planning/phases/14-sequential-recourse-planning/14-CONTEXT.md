# Phase 14: Sequential Recourse Planning - Context

**Gathered:** 2026-03-16
**Status:** Ready for replanning

<domain>
## Phase Boundary

Transition Credit Coach from behavior-aware one-shot recommendations toward canonical multi-phase trajectories with dynamic, time-aware risk simulation. This phase makes trajectory structure, checkpoint interpretation, adaptive phase transitions, and phase-aware optimization explicit. It builds on the typed-action, feasibility, execution-probability, and partial-execution contracts from Phases 12 and 13, but it does not introduce institution-side offer optimization, new end-user product surfaces, or a second planner stack.

</domain>

<decisions>
## Implementation Decisions

### Carry-Forward Decisions From Phases 8-13
- Phase 8 through Phase 11 governance remains authoritative:
  - fairness, reliability, telemetry, and release evidence contracts are inherited guardrails
  - sequential planning cannot override those gates
- Machine-readable artifacts remain the canonical source of truth
- Markdown review remains derived and explanation-first rather than dashboard-like
- Phase 12 action contract remains authoritative:
  - typed actions stay `hybrid`
  - `action_key` is user-facing
  - `feature_name` remains the effect anchor
  - composite actions stay grouped under `action_group_id`
  - approval-dependent actions remain non-winner or provisional branches
- Phase 13 behavior contract remains authoritative:
  - canonical probability units are action- and plan-level
  - weekly coaching loop remains the canonical simulation grain
  - behavior-aware evidence remains supporting and non-blocking

### Canonical Trajectory Shape
- The canonical recommendation contract keeps both:
  - flat `actions[]`
  - explicit `phases[]`
- Flat `actions[]` remain available for compatibility and low-level processing
- Canonical trajectory semantics live in `phases[]`
- The Phase 14 phase set is fixed:
  - `phase_1_stabilize` = `0-4 hafta`
  - `phase_2_build` = `1-3 ay`
  - `phase_3_optimize` = `3-12 ay`
- One action must belong to one primary phase only
- If the same intervention must recur across phases, it should be represented as a new step or action row rather than one action spanning multiple phases
- Each phase bucket must carry canonical metadata, not just a step list
- Minimum required phase metadata:
  - `phase_id`
  - `phase_title`
  - `target_window_weeks`
  - `steps`
  - `target_pd`
  - `gate_pass_target`
  - `review_week`

### Checkpoint Semantics
- The primary checkpoint for Phase 14 is:
  - `4 hafta`
- `12 hafta` is the medium-horizon confirmation checkpoint
- `24 hafta` is the long-horizon upside and stability checkpoint
- Optimization and review must prioritize checkpoint importance in this order:
  - `4w > 12w > 24w`
- Phase 14 should not require strict monotonicity across checkpoint metrics
- Mild noise is acceptable
- But meaningful regression should be penalized:
  - `12 hafta`, `4 hafta` sonucundan belirgin bicimde kotu olmamali
  - `24 hafta`, `12 hafta` sonucundan belirgin bicimde kotu olmamali
- Checkpoint regression should be treated as trajectory penalty rather than automatic invalidation

### Replan and Phase Transition Behavior
- The default trajectory model is `hybrid`
- Canonical phases remain fixed and predeclared
- Phase transitions may adapt at review checkpoints
- Missing a `phase_1` target must not automatically invalidate the entire trajectory
- Default behavior is:
  - `phase_2` and `phase_3` continue as conditional
  - checkpoint review may trigger rebase or replan
  - behavior is fail-reviewed rather than fail-open
- Replan granularity is phase-boundary based, not weekly full-trajectory regeneration
- Canonical review points are:
  - `week 4`
  - `week 12`
  - optional `week 24` closeout
- Trajectory artifacts must carry explicit transition state
- Minimum required replan or transition fields:
  - `trajectory_status = on_track | needs_replan | degraded`
  - `current_phase`
  - `next_review_week`
  - `phase_transition_reason`
  - `replanned_from_phase` when applicable

### Phase-Aware Optimization Policy
- Primary optimization preference is:
  - `short-term feasibility / early checkpoint health`
- A trajectory with attractive long-horizon upside must not outrank a materially weaker short-term path by default
- Long-horizon upside is only meaningful when early checkpoint health is acceptable
- `24 hafta` improvement may act as bonus or stability evidence, but it must not mask weak `4 hafta` behavior
- High-risk segments use a more conservative version of the same policy
- For high-risk planning:
  - short-term stabilization carries more weight
  - long-run upside remains secondary
- Optimizer outputs should carry policy labels rather than collapsing everything into one opaque score
- Allowed policy labels:
  - `stabilize_first`
  - `balanced_progress`
  - `long_horizon_heavy`
- Default ranking preference should favor:
  - `stabilize_first`
  - `balanced_progress`
- `long_horizon_heavy` may rank highly only when early checkpoints are already sufficiently healthy

### Claude's Discretion
- Exact JSON nesting for `phases[]` and the supporting flat action list as long as `phases[]` remain the canonical semantic layer
- Exact penalty shape for checkpoint regression as long as it is soft, reviewable, and does not silently become a hard invalidation rule
- Exact weight values inside the phase-aware objective as long as the locked priority order `4w > 12w > 24w` is preserved
- Exact serialization strategy for replan metadata as long as the required transition fields remain explicit and machine-readable

</decisions>

<specifics>
## Specific Ideas

- Sequential plans should read like a controlled roadmap rather than a bag of time-stamped actions
- Early checkpoint health should answer "is this trajectory actually survivable?" before the system celebrates long-horizon upside
- The system should preserve a trajectory even after a weak early phase when a sensible review-based recovery path exists
- High-risk cases should look more conservative in the first phase instead of chasing long-run upside too early
- `phases[]` should be rich enough that later outcome learning can connect checkpoint transitions and replans back to one canonical plan history

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `credit-coach/src/credit_coach/data/schema.py`
  - `PlanAction` already carries `time_months`, `phase_id`, `week_start`, and `week_end`, so it is the right seam for promoting phase buckets into canonical trajectory structure
- `credit-coach/src/credit_coach/recourse/generator.py`
  - already maps months into `phase_1_stabilize`, `phase_2_build`, and `phase_3_optimize`
  - already builds weekly trajectories when the weekly optimizer is enabled
- `credit-coach/src/credit_coach/coaching/loop.py`
  - already provides the canonical weekly execution and replan seam
- `credit-coach/src/credit_coach/cli/run_recourse.py`
  - already emits phased roadmap views and checkpoint estimates, making it the natural serialization seam for canonical `phases[]`
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - already computes `trajectory_pd_4w/12w/24w`, gate-pass rates, partial progress, and phase action counts
- `credit-coach/src/credit_coach/coaching/planner.py`
  - already applies gate-first ranking and Phase 13 behavior-aware ordering, making it the right seam for phase-aware optimization
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - already aggregates seeded trajectory and behavior-aware evidence
- `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`
  - already compares trajectory and behavior-aware metrics across variants

### Established Patterns
- Canonical machine-readable evidence lives under `artifacts/runs/<run_id>/tables/`
- The repo already uses stable checkpoint vocabulary:
  - `4w`
  - `12w`
  - `24w`
- Roadmap-style recommendation output already exists, but it is currently more descriptive than canonical
- Weekly simulation is already the accepted execution and replan grain
- Release and milestone-acceptance contracts remain separate from recommendation-quality evidence

### Integration Points
- Phase 14 changes should primarily hook into:
  - `credit-coach/src/credit_coach/data/schema.py`
  - `credit-coach/src/credit_coach/recourse/generator.py`
  - `credit-coach/src/credit_coach/coaching/loop.py`
  - `credit-coach/src/credit_coach/coaching/planner.py`
  - `credit-coach/src/credit_coach/cli/run_recourse.py`
  - `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
  - `credit-coach/src/credit_coach/cli/run_model_challenger_matrix.py`
- Regression coverage should extend through:
  - `credit-coach/tests/test_recourse_redesign.py`
  - `credit-coach/tests/test_sequential_recourse.py`
  - `credit-coach/tests/test_recourse_funnel_kpis.py`
  - `credit-coach/tests/test_planner_denied_objective.py`
  - `credit-coach/tests/test_batch_candidate_diversity.py`
  - `credit-coach/tests/test_phase_experiment_suite.py`
  - `credit-coach/tests/test_challenger_matrix_selection.py`

</code_context>

<deferred>
## Deferred Ideas

- Institution-side offer actions and offer acceptance likelihood remain Phase 15 work
- Outcome-driven trajectory adaptation and learned checkpoint transition models remain later learning-loop work
- Any hard-reject threshold based on poor long-horizon trajectory quality can be revisited after richer real-world outcome evidence exists

</deferred>

---
*Phase: 14-sequential-recourse-planning*
*Context gathered: 2026-03-16*
