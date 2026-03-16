---
phase: 14-sequential-recourse-planning
plan: 01
subsystem: recourse-schema
tags: [trajectory, phases, serialization, generator, pytest]
requires: []
provides:
  - canonical `phases[]` trajectory contract for 0-4 weeks, 1-3 months, and 3-12 months
  - shared trajectory helper seam reused by generator and CLI serialization
  - phase and checkpoint metadata attached directly to generated plans
affects: [phase-14, generator, cli, schema]
tech-stack:
  added: [credit-coach/src/credit_coach/recourse/trajectory.py]
  patterns: [canonical phases, compatibility actions, shared trajectory helpers]
key-files:
  created: [credit-coach/src/credit_coach/recourse/trajectory.py]
  modified: [credit-coach/src/credit_coach/data/schema.py, credit-coach/src/credit_coach/recourse/generator.py, credit-coach/src/credit_coach/cli/run_recourse.py, credit-coach/tests/test_recourse_redesign.py, credit-coach/tests/test_recourse_funnel_kpis.py]
key-decisions:
  - "`phases[]` is the canonical trajectory semantic layer while flat `actions[]` remains the compatibility layer."
  - "The fixed trajectory vocabulary is `phase_1_stabilize`, `phase_2_build`, and `phase_3_optimize`."
  - "Repeated interventions become new steps; one action never spans multiple primary phases."
patterns-established:
  - "Trajectory schema, generation, and serialization now reuse one shared `trajectory.py` seam."
requirements-completed: [REC-06]
duration: manual-execution
completed: 2026-03-16
---

# Phase 14 Plan 01 Summary

**Sequential planning is now a first-class contract: recommendations carry explicit multi-phase trajectories instead of only flattened action lists.**

## Accomplishments
- Added canonical `TrajectoryPhase` and `TrajectoryCheckpoint` structures to the plan schema.
- Introduced a shared `trajectory.py` seam that groups actions into fixed near-, mid-, and long-horizon phases with target and review metadata.
- Updated generator and recourse serialization paths so emitted plans expose `phases[]`, checkpoints, and initial trajectory state without dropping existing typed-action compatibility fields.

## Verification
- `python -m pytest credit-coach/tests/test_recourse_redesign.py`
- `python -m pytest credit-coach/tests/test_recourse_redesign.py credit-coach/tests/test_recourse_funnel_kpis.py`

## Notes
- `actions[]` still exists for downstream compatibility, but trajectory meaning now lives in `phases[]`.

---
*Phase: 14-sequential-recourse-planning*
*Completed: 2026-03-16*
