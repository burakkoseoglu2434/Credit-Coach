---
phase: 64-movement-focused-path-ranking
plan: 01
subsystem: planner
tags: [movement-ranking, recoverability, path-selection, pytest]
requires:
  - phase: 63-recourse-gating-by-recoverability
    provides: recoverable/full-mode activation seam and limited-mode fallback contract
provides:
  - deterministic movement-aware ranking primitives for recoverable/full-mode denied customers
  - threshold-reaching priority inside the existing planner seam
  - shared movement-mode activation that keeps selected-plan and grouped-path ranking aligned
affects: [64-02-runtime-artifacts, 64-03-cohort-evidence, selected-path-usefulness]
tech-stack:
  added: []
  patterns: [ordered deterministic ranking, recoverability-activated reranking, path-plan coherence]
key-files:
  created:
    - .planning/phases/64-movement-focused-path-ranking/64-01-SUMMARY.md
  modified:
    - credit-coach/src/credit_coach/coaching/planner.py
    - credit-coach/src/credit_coach/data/schema.py
    - credit-coach/src/credit_coach/cli/run_recourse.py
    - credit-coach/tests/test_planner_denied_objective.py
    - credit-coach/tests/test_planner_quality_source_mix.py
    - credit-coach/tests/test_recourse_paths.py
key-decisions:
  - "Kept Phase 64 additive by introducing a recoverable/full-mode ranking branch instead of replacing the existing chooser."
  - "Moved threshold-reaching priority ahead of softer denied-ranking terms while preserving status, constraint, contender, and warning guards."
  - "Resolved movement-mode activation from recoverability truth before final selection, then reran both selected-plan and path-representative ranking through the same shared flag."
patterns-established:
  - "Movement ranking should activate only after Phase 63 recoverability truth indicates recoverable/full mode."
  - "Selected plan and grouped path representative ordering should always reuse the same planner seam to avoid path-vs-plan drift."
requirements-completed: [MOVE-01, MOVE-02, MOVE-03]
duration: 1min
completed: 2026-04-07
---

# Phase 64: Movement-Focused Path Ranking Summary

**Recoverable/full-mode denied customers now rank by realistic threshold-reaching movement, and grouped path ranking stays aligned with the same chooser policy.**

## Performance

- **Duration:** 1 min
- **Started:** 2026-04-07T23:15:11+03:00
- **Completed:** 2026-04-07T23:15:25+03:00
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Added deterministic `movement_score`, `threshold_reach_probability`, `threshold_reach_priority_flag`, and `movement_rank_reason_codes` to the shared planner seam.
- Introduced a recoverable/full-mode movement sort that explicitly favors plausible threshold reach before softer execution-comfort signals, while keeping status, constraint, contender, and warning guards intact.
- Wired runtime selection so recoverability truth decides whether movement ranking should activate, then reruns both winner selection and grouped path representative ranking through the same flag.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add deterministic movement-ranking primitives to the shared planner seam** - `bc2ec5a` (feat)
2. **Task 2: Thread the movement-ranking activation through runtime and grouped path ranking** - `5f20f02` (feat)

## Files Created/Modified

- `credit-coach/src/credit_coach/coaching/planner.py` - Added recoverable/full-mode movement ranking primitives, threshold-reaching heuristics, and the ordered movement-aware sort key.
- `credit-coach/src/credit_coach/data/schema.py` - Added additive plan-level fields for movement score, threshold-reaching probability, and movement rank reason codes.
- `credit-coach/src/credit_coach/cli/run_recourse.py` - Added preselection recoverability-driven movement activation and reranked selected plans plus grouped paths through one shared seam.
- `credit-coach/tests/test_planner_denied_objective.py` - Proved threshold-capable plans gain priority when movement mode activates.
- `credit-coach/tests/test_planner_quality_source_mix.py` - Proved customer-only paths win near-ties under movement mode when movement is comparable.
- `credit-coach/tests/test_recourse_paths.py` - Proved grouped path representative ordering stays aligned with the movement-ranked winner.
- `.planning/phases/64-movement-focused-path-ranking/64-01-SUMMARY.md` - Captured execution outcome, verification, and commit traceability.

## Decisions Made

- Treated raw gate-distance as a softer denied-ranking term than threshold-reaching priority once validity and contender screening have already passed.
- Kept high-level planner structure intact; the new behavior is a branch inside `choose_best_plan(...)`, not a new chooser regime.
- Used recoverability-derived runtime activation instead of a second path-count or heuristic trigger.

## Verification

- `cd credit-coach && python -m pytest tests/test_planner_denied_objective.py tests/test_planner_quality_source_mix.py -q` -> passed (`24 passed`)
- `cd credit-coach && python -m pytest tests/test_recourse_paths.py -q` -> passed (`4 passed`)
- `cd credit-coach && python -m pytest tests/test_planner_denied_objective.py tests/test_planner_quality_source_mix.py tests/test_recourse_paths.py -q` -> passed (`28 passed`)

## Deviations from Plan

None - plan executed as written, with one additional schema touch to store the new planner fields explicitly.

## Issues Encountered

- The first movement-ranking pass still let a threshold-weak plan win because raw gate-distance sat ahead of threshold priority; this was corrected by moving threshold-reaching advantage earlier in the movement sort order while preserving hard validity guards.

## User Setup Required

None.

## Next Phase Readiness

- Runtime now knows when movement ranking should turn on for recoverable/full-mode customers.
- Wave 2 can focus on emitting selected-path movement truth into runtime summaries and flat artifacts without reopening chooser structure.

## Self-Check

PASSED

---
*Phase: 64-movement-focused-path-ranking*
*Completed: 2026-04-07*
