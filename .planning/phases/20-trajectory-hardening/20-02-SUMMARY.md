---
phase: 20-trajectory-hardening
plan: 02
subsystem: consistency-and-early-health
tags: [trajectory, monotonicity, planner, messaging, evidence, pytest]
requires: [20-01]
provides:
  - explicit monotonicity and jump diagnostics
  - early-health-sensitive planner behavior
  - checkpoint narrative alignment with trajectory truth
affects: [phase-20, ranking, messaging, batch-artifacts, suite-rollups]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/recourse/trajectory.py
    - credit-coach/src/credit_coach/coaching/planner.py
    - credit-coach/src/credit_coach/coaching/messaging.py
    - credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py
    - credit-coach/src/credit_coach/cli/run_phase_experiment_suite.py
    - credit-coach/tests/test_planner_denied_objective.py
    - credit-coach/tests/test_batch_candidate_diversity.py
    - credit-coach/tests/test_messaging.py
key-decisions:
  - "Soft monotonicity tolerates only 0.01 worsening; anything above 0.03 is treated as a real jump."
  - "Weak 4w health remains visible but can no longer read as a strong default plan."
  - "Checkpoint narrative must follow checkpoint status and flags, not optimistic late-horizon summary alone."
patterns-established:
  - "Trajectory consistency is now explicit enough to travel from engine truth into ranking, messaging, and proof artifacts."
requirements-completed: [PORT-04]
duration: manual-execution
completed: 2026-03-19
---

# Phase 20 Plan 02 Summary

**Trajectory quality now depends on believable early health, not just attractive long-horizon PD.**

## Accomplishments
- Added reusable trajectory consistency truth:
  - `weak_early_health`
  - `trajectory_jump_flag`
  - `non_monotonic_flag`
  - `checkpoint_inconsistency_flag`
- Hardened planner scoring so weak `4w` health, jumpy paths, and inconsistent checkpoint stories get explicit demotion before product surfaces can over-read them.
- Kept policy labels rule-based while allowing trajectory truth to push labels toward more conservative interpretations.
- Updated checkpoint narratives so `on_track`, `at_risk`, and `missed` checkpoints now generate different product text instead of sharing one generic story.
- Surfaced consistency evidence into batch and suite trajectory summaries, including weak-4w, jump, and non-monotonic rates.

## Verification
- `python -m pytest credit-coach/tests/test_planner_denied_objective.py credit-coach/tests/test_recourse_funnel_kpis.py credit-coach/tests/test_batch_candidate_diversity.py credit-coach/tests/test_messaging.py credit-coach/tests/test_phase_experiment_suite.py -q`

## Notes
- This remains a hardening layer over inherited trajectory math; it does not replace the planner with a new optimizer.
- Product copy is still deterministic and engine-owned; the website does not invent its own checkpoint interpretation.

---
*Phase: 20-trajectory-hardening*
*Completed: 2026-03-19*
