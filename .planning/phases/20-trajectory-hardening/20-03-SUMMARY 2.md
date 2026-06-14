---
phase: 20-trajectory-hardening
plan: 03
subsystem: replan-status-policy-hardening
tags: [trajectory, replan, status, policy-labels, loop, suite, pytest]
requires: [20-01, 20-02]
provides:
  - deterministic boundary-only replan behavior
  - stable trajectory status semantics
  - execution-aware but rule-based policy label interpretation
affects: [phase-20, weekly-loop, review-surfaces, suite-proof, portfolio-artifacts]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/coaching/loop.py
    - credit-coach/src/credit_coach/coaching/planner.py
    - credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py
    - credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py
    - credit-coach/tests/test_sequential_recourse.py
    - credit-coach/tests/test_phase_experiment_suite.py
key-decisions:
  - "Formal replan remains allowed only at 4w, 12w, and 24w."
  - "`degraded` is reserved for cases where continuing the same plan no longer looks rational; 4w weakness alone stays in `needs_replan`."
  - "Execution truth can harden policy labels conservatively, but checkpoint shape remains the primary label driver."
patterns-established:
  - "Trajectory status now behaves like a deterministic review contract instead of an implicit side effect of weekly simulation."
requirements-completed: [PORT-04]
duration: manual-execution
completed: 2026-03-19
---

# Phase 20 Plan 03 Summary

**Review boundaries, trajectory status, and policy labels now behave like a stable contract rather than a loosely implied simulation outcome.**

## Accomplishments
- Hardened the weekly coaching loop so:
  - checkpoint type and checkpoint status are emitted directly
  - formal replan stays boundary-only
  - `4w` misses remain recoverable as `needs_replan` rather than being over-escalated to `degraded`
- Clarified `degraded` as the true “same plan no longer rational” state instead of a generic weak-signal bucket.
- Updated planner gate and rank semantics so checkpoint-safe trajectories can beat superficially stronger but late-heavy stories.
- Made phase-suite trajectory rollups backward-compatible while still carrying the new consistency metrics.
- Closed the loop between Phase 19 execution truth and Phase 20 policy labels without letting execution override checkpoint shape as the primary driver.

## Verification
- `python -m pytest credit-coach/tests/test_planner_denied_objective.py credit-coach/tests/test_sequential_recourse.py credit-coach/tests/test_phase_experiment_suite.py -q`

## Notes
- Proof refresh is still intentionally deferred to Phase 21.
- The product-facing claim after this plan is narrower and safer: the roadmap is now deterministic enough to trust before refreshing portfolio proof.

---
*Phase: 20-trajectory-hardening*
*Completed: 2026-03-19*
