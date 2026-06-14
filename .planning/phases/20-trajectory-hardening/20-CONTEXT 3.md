# Phase 20: Trajectory Hardening - Context

**Gathered:** 2026-03-19
**Status:** Ready for replanning

<domain>
## Phase Boundary

Re-harden the inherited trajectory layer into a deterministic, checkpoint-governed, product-ready roadmap contract. This phase does not reopen typed actions, behavior-aware execution math, offer optimization, proof refresh, website storytelling, or portfolio validation scope from earlier phases. It clarifies how strict the trajectory contract should be, how soft monotonicity and early-health protection should behave, and how replan, status, and policy-label semantics should stay stable enough for product and proof consumers to trust.

</domain>

<decisions>
## Implementation Decisions

### Carry-Forward Decisions From Phases 14, 17, 18, And 19
- The shipped `v1.2` trajectory layer remains the inherited baseline:
  - canonical `phases[]`
  - canonical `trajectory_checkpoints[]`
  - canonical trajectory-aware ranking and review metadata
- Phase 17 remains authoritative for proof semantics:
  - trajectory claims must stay believable under full-cohort product-ready and reality-gap proof
- Phase 18 remains authoritative for translation:
  - product and analyst surfaces consume engine trajectory truth
  - trajectory meaning should not be recomputed in website-only logic
- Phase 19 remains authoritative for execution truth:
  - `plan_execution_probability` stays visible in trajectory evaluation
  - approval-dependent realization stays explicit
  - execution truth may influence trajectory interpretation, but it must not replace checkpoint truth as the primary driver
- Phase 20 remains intentionally small:
  - lock trajectory correctness first
  - refresh proof in Phase 21

### Phase And Checkpoint Contract Strictness
- The canonical phase set remains:
  - `phase_1_stabilize`
  - `phase_2_build`
  - `phase_3_optimize`
- `phase_3_optimize` must be tightened to:
  - logical horizon: `13-24w`
  - product language: `3-6 ay`
- Every action must resolve to exactly one primary phase
- Multi-phase or ambiguous phase assignment is not allowed
- The canonical checkpoint set remains fixed to:
  - week `4` / `primary`
  - week `12` / `confirmation`
  - week `24` / `stability`
- Checkpoint type enum is locked to:
  - `primary`
  - `confirmation`
  - `stability`
- Checkpoint-local status enum is locked to:
  - `on_track`
  - `at_risk`
  - `missed`
- Checkpoint-local status is intentionally distinct from plan-level `trajectory_status`
- `24w` is the product and proof closing horizon:
  - no optional long-tail checkpoint contract after it
  - no open-ended roadmap extension inside this phase

### Soft Monotonicity And Early-Health Protection
- Soft monotonicity remains the default trajectory expectation:
  - `4w >= 12w >= 24w`
- Small drift tolerance is locked to:
  - `0.01` PD
- Small drift should not be treated as a meaningful signal by itself
- `trajectory_jump_flag` should fire when checkpoint-to-checkpoint PD worsening is:
  - greater than `0.03`
- `4w` weakness should not hard-reject a plan, but it must prevent the plan from reading as strong
- A late-improving plan with weak early health may still exist, but should not surface as a strong default plan
- `non_monotonic_flag` means:
  - the numeric checkpoint path is inconsistent
- `checkpoint_inconsistency_flag` means:
  - checkpoint metrics and checkpoint-facing labels or narrative do not agree
- These two flags must remain separate

### Replan And Trajectory Status Semantics
- `needs_replan` may be assigned only at canonical review boundaries
- `needs_replan` is the correct verdict when:
  - `4w` or `12w` is weak
  - but recovery still appears plausible
- `degraded` means:
  - continuing the same plan no longer looks rational
- `degraded` should cover cases such as:
  - worsening PD direction
  - severe jump or consistency failure
  - missed checkpoint plus execution deterioration
- Boundary-external deterioration must not trigger immediate formal replan
- Outside canonical review boundaries, deterioration should surface as:
  - diagnostic
  - `at_risk`
  - review-triggering at the next allowed boundary
- `next_review_week` is locked to:
  - `4`
  - `12`
  - `24`
- After `24`, no further review week is part of this phase contract

### Policy Labels And Execution Alignment
- Policy labels must remain fully rule-based
- The same trajectory truth must always produce the same policy label
- The canonical label set remains:
  - `stabilize_first`
  - `balanced_progress`
  - `long_horizon_heavy`
- Checkpoint shape is the primary driver of policy-label assignment
- Phase 19 execution truth may adjust labels only in the more conservative direction
- Execution truth is therefore:
  - secondary to checkpoint shape
  - but allowed to harden interpretation
- `stabilize_first` means:
  - `4w` is strong
  - early confidence is established
  - the short-term profile is product-defensible
- `long_horizon_heavy` means:
  - `4w` is weak
  - improvement is concentrated in `12w/24w`
  - and this reading becomes stronger when execution burden is also high

### Claude's Discretion
- Exact field naming for checkpoint-local machine-readable fields as long as all locked semantics remain explicit:
  - checkpoint type
  - checkpoint-local status
  - predicted PD
  - PD delta
  - gate-pass estimate
- Exact formulas for:
  - early-health demotion strength
  - monotonicity penalties
  - when execution truth softens or hardens policy-label assignment
- Exact artifact nesting and summary-file naming as long as:
  - the locked enums remain canonical
  - the `4w/12w/24w` contract stays fixed
  - replan remains boundary-only

</decisions>

<specifics>
## Specific Ideas

- The user wants Phase 20 to answer:
  - “plan dogru mu?”
  rather than:
  - “plan gerçekten çalışıyor mu?”
- The user explicitly wants `24w` to be the closing horizon for both proof and product surfaces in this phase.
- The user wants weak `4w` trajectories to stay visible but never read as strong.
- The user wants checkpoint-local interpretation to be cleaner than plan-level status:
  - `on_track`
  - `at_risk`
  - `missed`
- The user explicitly prefers rule-based deterministic labels over fuzzy or learned label assignment.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- [trajectory.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/recourse/trajectory.py)
  - already owns canonical phase specs and nominal checkpoint generation
  - is the natural seam for tightening phase 3, checkpoint type fields, and consistency flags
- [loop.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/loop.py)
  - already owns review-boundary behavior and emitted trajectory states
  - is the natural seam for deterministic `needs_replan` vs `degraded`
- [planner.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/coaching/planner.py)
  - already uses checkpoint-aware priority and policy labels
  - is the natural seam for early-health protection and conservative label adjustment
- [schema.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/data/schema.py)
  - already carries phases, checkpoints, plan-level trajectory status, next-review semantics, and policy labels
  - needs the checkpoint-local contract to become more explicit
- [run_batch_recourse_eval.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py)
  - already emits trajectory artifacts and breakdowns
  - is the correct seam for surfacing consistency and replan evidence
- [run_phase_experiment_suite.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py)
  - already aggregates trajectory metrics and policy labels across seeds
  - is the correct seam for keeping the hardened contract visible in suite rollups

### Established Patterns
- Machine-readable trajectory truth remains primary; review markdown and product surfaces are derived
- Canonical review boundaries already exist at `4`, `12`, and `24`
- Plan-level and checkpoint-level semantics can differ if they remain explicit and deterministic
- Behavior-aware truth from Phase 19 should be reused rather than recomputed in a separate trajectory-only layer

### Integration Points
- Likely Phase 20 code seams:
  - `credit-coach/src/credit_coach/recourse/trajectory.py`
  - `credit-coach/src/credit_coach/coaching/loop.py`
  - `credit-coach/src/credit_coach/coaching/planner.py`
  - `credit-coach/src/credit_coach/cli/run_recourse.py`
  - `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
  - `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- Likely regression seams:
  - `credit-coach/tests/test_sequential_recourse.py`
  - `credit-coach/tests/test_recourse_funnel_kpis.py`
  - `credit-coach/tests/test_planner_denied_objective.py`
  - `credit-coach/tests/test_batch_candidate_diversity.py`
  - `credit-coach/tests/test_phase_experiment_suite.py`
  - `credit-coach/tests/test_messaging.py`

</code_context>

<deferred>
## Deferred Ideas

- Re-running the full portfolio and refreshing product-facing proof remains Phase 21 work.
- Website or investor-surface reinterpretation of trajectory outputs remains outside this phase.
- Any trajectory horizon beyond the locked `24w` closing contract is out of scope here.

</deferred>

---
*Phase: 20-trajectory-hardening*
*Context gathered: 2026-03-19*
