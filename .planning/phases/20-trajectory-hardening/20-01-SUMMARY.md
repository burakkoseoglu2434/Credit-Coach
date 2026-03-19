---
phase: 20-trajectory-hardening
plan: 01
subsystem: checkpoint-contract-hardening
tags: [trajectory, checkpoints, schema, roadmap, pytest]
requires: []
provides:
  - locked three-phase trajectory contract
  - canonical 4w/12w/24w checkpoint schema
  - machine-readable checkpoint type and status enums
affects: [phase-20, roadmap-serialization, cli-contracts, product-surfaces]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/data/schema.py
    - credit-coach/src/credit_coach/recourse/trajectory.py
    - credit-coach/src/credit_coach/cli/run_recourse.py
    - credit-coach/tests/test_recourse_funnel_kpis.py
key-decisions:
  - "The canonical checkpoint contract is now fixed to exactly 4w / 12w / 24w."
  - "Checkpoint-local meaning is serialized directly as `checkpoint_type` and `status` instead of being inferred later."
  - "`phase_3_optimize` now closes at 13-24w and reads as 3-6 ay."
patterns-established:
  - "Roadmap truth is now machine-readable enough for product, proof, and analyst surfaces to consume the same contract."
requirements-completed: [PORT-04]
duration: manual-execution
completed: 2026-03-19
---

# Phase 20 Plan 01 Summary

**Trajectory contract drift is now closed at the schema and serialization layer.**

## Accomplishments
- Tightened the canonical phase specs so `phase_3_optimize` closes at `13-24w` / `3-6 ay` instead of behaving like an open-ended horizon.
- Hardened `TrajectoryCheckpoint` into a locked contract with:
  - fixed weeks `4 | 12 | 24`
  - fixed types `primary | confirmation | stability`
  - fixed local statuses `on_track | at_risk | missed`
- Added checkpoint contract validation so week, month, phase, type, and priority remain internally consistent.
- Canonicalized action-to-phase resolution so roadmap phases always group actions under one deterministic primary phase.
- Updated recourse roadmap serialization so customer roadmap outputs now carry checkpoint type, status, and consistency flags directly.

## Verification
- `python -m pytest credit-coach/tests/test_recourse_funnel_kpis.py credit-coach/tests/test_sequential_recourse.py -q`

## Notes
- This pass locks the raw contract only; planner pressure, narrative alignment, and replan semantics are hardened in Plans 02 and 03.
- Website or analyst consumers no longer need to reconstruct checkpoint meaning from week numbers alone.

---
*Phase: 20-trajectory-hardening*
*Completed: 2026-03-19*
