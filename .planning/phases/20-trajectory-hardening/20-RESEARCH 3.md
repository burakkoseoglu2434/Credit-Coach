# Phase 20: Trajectory Hardening - Research

**Researched:** 2026-03-19
**Status:** Ready for replanning
**Confidence:** HIGH

## Planning Question

What still has to change so the shipped trajectory layer becomes deterministic, checkpoint-safe, and product-defensible before Phase 21 re-runs proof across the portfolio?

## Planning Basis

Phase 20 now has a locked `20-CONTEXT.md`. For this planning pass the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/19-behavior-aware-recourse/19-CONTEXT.md`
- `.planning/phases/20-trajectory-hardening/20-CONTEXT.md`
- `credit-coach/src/credit_coach/recourse/trajectory.py`
- `credit-coach/src/credit_coach/coaching/loop.py`
- `credit-coach/src/credit_coach/coaching/planner.py`
- `credit-coach/src/credit_coach/data/schema.py`
- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`
- `credit-coach/src/credit_coach/cli/run_recourse.py`
- `credit-coach/tests/test_sequential_recourse.py`
- `credit-coach/tests/test_recourse_funnel_kpis.py`
- `credit-coach/tests/test_planner_denied_objective.py`
- `credit-coach/tests/test_batch_candidate_diversity.py`
- `credit-coach/tests/test_phase_experiment_suite.py`
- `credit-coach/tests/test_messaging.py`

This is sufficient because Phase 20 is not inventing trajectory planning from scratch. The repo already contains:

- canonical phase and checkpoint builders in `recourse/trajectory.py`
- hybrid weekly review and replan logic in `coaching/loop.py`
- trajectory-aware ranking and policy labels in `coaching/planner.py`
- schema support for phases, checkpoints, statuses, and policy labels in `data/schema.py`
- batch and suite surfaces that already consume trajectory outputs

The gap is no longer ambiguity about direction. The gap is updating the planning package so it fully inherits the locked context:

- `phase_3_optimize` must close at `24w`, not drift into an open-ended horizon
- checkpoint type and checkpoint-local status need explicit machine-readable enums
- soft monotonicity must use a bounded tolerance (`0.01`) and explicit jump threshold (`>0.03`)
- replan and policy labels must remain deterministic and only use execution truth as a conservative secondary signal

## Executive Summary

The trajectory stack already exists, but it still behaves like an inherited heuristic layer rather than a tightly governed product contract:

- `trajectory.py` already emits canonical phases and nominal checkpoints
- `loop.py` already uses canonical review weeks and emits replan or status fields
- `planner.py` already prefers early-health trajectories and assigns policy labels
- batch and suite surfaces already serialize trajectory metrics, status, and policy labels

The remaining problem is contract drift and product defensibility:

1. phase and checkpoint definitions are not yet fully locked to the re-scoped Phase 20 contract
2. monotonicity and jump handling are still more implicit than explicit
3. weak early checkpoints can still look better than they should
4. replan and status semantics need to be deterministic enough for proof and product surfaces

Phase 20 should therefore be planned as a mini hardening pass over existing seams, not as a new trajectory design.

## Existing Assets We Can Reuse

### The canonical trajectory builder already exists

- `credit-coach/src/credit_coach/recourse/trajectory.py`
  - already defines `PHASE_SPECS`
  - already attaches `phases`
  - already builds nominal trajectory checkpoints

This is the right seam for locking:

- exact phase windows
- exact checkpoint count
- required checkpoint fields
- single-phase action assignment

It also reveals the main inherited drift:

- the current phase 3 definition still spans `13-52w` and `4-12 months`
- the re-scoped roadmap now wants a tighter `12-24w` product-safe contract

### Weekly review truth already exists

- `credit-coach/src/credit_coach/coaching/loop.py`
  - already uses `review_weeks=(4, 12, 24)`
  - already emits `trajectory_status`
  - already emits `current_phase`
  - already emits `next_review_week`
  - already emits `phase_transition_reason`

This is the correct seam for deterministic replan boundaries and trajectory status logic.

### Planner already has a trajectory-aware insertion point

- `credit-coach/src/credit_coach/coaching/planner.py`
  - already derives checkpoint-aware priority scores
  - already prefers early checkpoint strength
  - already emits policy labels

Phase 20 should harden this seam so `4w` weakness, monotonicity drift, and trajectory instability materially affect plan defensibility.

### Artifact surfaces already exist

- `credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py`
- `credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py`

These already report trajectory metrics. Phase 20 can sharpen their meaning rather than inventing a second trajectory proof stack.

## What Phase 20 Must Deliver

### 1. Deterministic phase and checkpoint contract

Phase 20 must lock:

- exactly one `primary_phase` per action
- exactly three canonical phases:
  - `phase_1_stabilize`
  - `phase_2_build`
  - `phase_3_optimize`
- `phase_3_optimize` specifically means:
  - logical horizon `13-24w`
  - product language `3-6 ay`
- exactly three canonical checkpoints:
  - week `4` / `primary`
  - week `12` / `confirmation`
  - week `24` / `stability`
- checkpoint type enum is locked to:
  - `primary`
  - `confirmation`
  - `stability`
- checkpoint-local status enum is locked to:
  - `on_track`
  - `at_risk`
  - `missed`

No missing checkpoints, no extra checkpoints, and no ambiguous multi-phase assignment.

### 2. Consistency and soft monotonicity hardening

Trajectory quality should not just mean “eventually better.” It should mean:

- no unexplained PD jumps
- limited and explicit tolerance for minor drift
- clear early-health protection
- narrative and metric alignment
- explicit split between:
  - `non_monotonic_flag`
  - `checkpoint_inconsistency_flag`

The key product rule is:

- if `4w` is weak, the plan should not read as strong

The locked quantitative posture is:

- minor worsening up to `0.01` is tolerated
- worsening above `0.03` is a true trajectory jump

### 3. Deterministic replan and status semantics

Replan and status must stop feeling like soft heuristics. Phase 20 must lock:

- replan only at `4`, `12`, or `24`
- stable statuses:
  - `on_track`
  - `needs_replan`
  - `degraded`
- stable, rule-based policy labels:
  - `stabilize_first`
  - `balanced_progress`
  - `long_horizon_heavy`

### 4. Phase 19 alignment

Trajectory truth must remain aligned with hardened behavior truth from Phase 19:

- `plan_execution_probability` stays visible in trajectory evaluation
- approval-dependent realization is not hidden
- late-heavy plans with weak early health should not survive purely because nominal endpoints look attractive
- execution truth may temper policy labels only in the conservative direction
- checkpoint shape remains the primary trajectory interpretation driver

## Recommended Plan Split

### Plan 20-01 — Phase and checkpoint contract hardening

Focus on:

- locking the three-phase contract
- locking the three-checkpoint contract
- making checkpoint types and required fields machine-readable
- ensuring all roadmap outputs serialize the same deterministic trajectory shape

### Plan 20-02 — Consistency and monotonicity hardening

Focus on:

- soft monotonicity expectations
- jump and inconsistency flags
- early-health protection
- narrative-to-metric alignment for checkpoint meaning

### Plan 20-03 — Replan logic and status hardening

Focus on:

- deterministic review boundaries
- stable trajectory status semantics
- stable policy-label mapping
- keeping trajectory evaluation aligned with execution truth from Phase 19

## Main Risks

- tightening the phase contract in one seam but leaving `run_recourse.py` or batch outputs on an older checkpoint shape
- making monotonicity so rigid that legitimate late-improving plans are misclassified as broken
- preserving replan visibility but still allowing non-boundary review semantics to leak into outputs
- hardening trajectory semantics without making the result obvious in batch or suite artifacts

## Recommendation

Proceed with Phase 20 now. The repo already contains the right trajectory, loop, planner, and artifact seams. The correct move is to lock them into one deterministic product contract, then use Phase 21 to re-run proof against the hardened truth instead of trying to answer proof and hardening in the same phase.
