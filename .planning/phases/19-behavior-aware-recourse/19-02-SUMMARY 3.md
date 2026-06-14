---
phase: 19-behavior-aware-recourse
plan: 02
subsystem: execution-aware-ranking
tags: [behavior-aware, planner, ranking, denied-mode, pytest]
requires: [19-01]
provides:
  - strong execution-aware ranking leverage
  - high-risk specific demotion posture
  - harder provisional contender penalties
affects: [phase-19, planner, best-plan-selection, cohort-winners]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/coaching/planner.py
    - credit-coach/tests/test_planner_denied_objective.py
key-decisions:
  - "Execution-aware truth now dominates nominal-only upside once plans clear eligibility filters."
  - "Low follow-through risk produces strong demotion rather than a soft tie-break."
  - "High-risk ranking is stricter still and penalizes provisional or approval-pending contenders more heavily."
patterns-established:
  - "The winning plan is the one that can be defended in product, not merely the one with the strongest theoretical uplift."
requirements-completed: [PORT-03]
duration: manual-execution
completed: 2026-03-19
---

# Phase 19 Plan 02 Summary

**Winner selection now prefers realistic completion over nominal-only upside.**

## Accomplishments
- Added planner-side execution demotion and defensibility scoring that materially reorders contenders after gate and feasibility filters.
- Moved execution-aware leverage ahead of nominal-only ranking signals in denied, high-risk, and default winner selection paths.
- Added explicit penalties for provisional and approval-pending contenders so they remain visible without behaving like ordinary winners.
- Added regression tests proving that lower nominal uplift can still win when execution-aware value is stronger, and that high-risk provisional plans are demoted hard.

## Verification
- `python -m pytest credit-coach/tests/test_planner_denied_objective.py credit-coach/tests/test_batch_candidate_diversity.py -q`

## Notes
- Gate-first semantics remain intact; this pass only hardens ranking among otherwise eligible contenders.
- Trajectory policy still matters, but it no longer hides major follow-through risk.

---
*Phase: 19-behavior-aware-recourse*
*Completed: 2026-03-19*
