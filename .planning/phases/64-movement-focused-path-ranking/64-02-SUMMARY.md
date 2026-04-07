---
phase: 64-movement-focused-path-ranking
plan: 02
subsystem: artifacts
tags: [movement-ranking, runtime-summary, collection, selected-surface, pytest]
requires:
  - phase: 64-01
    provides: recoverable/full-mode movement ranking contract and runtime activation seam
provides:
  - runtime summary emission of selected-path movement truth
  - flat customer artifact propagation for movement fields
  - explicit limited-mode clearing of movement residue on the selected surface
affects: [64-03-cohort-evidence, customer-metrics, selected-surface-honesty]
tech-stack:
  added: []
  patterns: [runtime-first artifact propagation, additive movement diagnostics, limited-mode field clearing]
key-files:
  created:
    - .planning/phases/64-movement-focused-path-ranking/64-02-SUMMARY.md
  modified:
    - credit-coach/src/credit_coach/cli/run_recourse.py
    - credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py
    - credit-coach/tests/test_customer_artifact_collection.py
    - credit-coach/tests/test_selected_surface_consistency.py
key-decisions:
  - "Kept runtime summary as the only source of movement truth for flat artifacts."
  - "Propagated movement fields additively instead of changing any customer- or operator-facing narrative wording."
  - "Cleared selected-path movement residue in limited mode so suppressed cases still look exactly like empty-state selected surfaces."
patterns-established:
  - "New ranking diagnostics should be emitted into roadmap summary first, then mirrored into metrics and collection artifacts without recomputation."
  - "Limited-mode empty-state reuse must clear movement-strength fields along with selected path ids, summaries, and render payloads."
requirements-completed: [MOVE-01, MOVE-02, MOVE-03]
duration: 1min
completed: 2026-04-07
---

# Phase 64: Movement-Focused Path Ranking Summary

**Selected-path movement truth now flows through runtime and flat customer artifacts, and limited mode clears those fields back to empty-state-safe values when selection is suppressed.**

## Performance

- **Duration:** 1 min
- **Started:** 2026-04-07T23:25:21+03:00
- **Completed:** 2026-04-07T23:26:00+03:00
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Emitted `movement_score`, `threshold_reach_probability`, `threshold_reach_priority_flag`, `movement_rank_reason_codes`, and `selected_path_movement_strength` into roadmap summary and synced metrics.
- Propagated those fields through customer artifact collection and collection parity so flat rows preserve runtime truth without recomputing ranking.
- Proved limited mode clears the new movement fields back to zero/empty values when the selected surface reuses the trusted empty-state contract.

## Task Commits

Each task was committed atomically:

1. **Task 1: Emit selected-path movement fields into runtime summary and customer metrics** - `a2a1b90` (feat)
2. **Task 2: Prove additive movement fields do not disturb honesty contracts** - `9b7d265` (feat)

## Files Created/Modified

- `credit-coach/src/credit_coach/cli/run_recourse.py` - Added selected-path movement fields to roadmap and metrics summaries and cleared them in limited mode.
- `credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py` - Propagated movement fields into flat customer metrics and collection parity validation.
- `credit-coach/tests/test_customer_artifact_collection.py` - Proved movement-field propagation, parity preservation, and limited-mode zeroed movement rows.
- `credit-coach/tests/test_selected_surface_consistency.py` - Proved limited-mode empty-state projection clears stale movement-strength signals.
- `.planning/phases/64-movement-focused-path-ranking/64-02-SUMMARY.md` - Captured execution outcome, verification, and commit traceability.

## Decisions Made

- Treated movement fields as selected-path diagnostics, not customer-facing explanation text.
- Preserved limited mode by clearing movement fields instead of leaving planner-side scores attached to an empty-state selected surface.
- Kept movement reason-code propagation JSON-first for collection parity and later cohort evidence reuse.

## Verification

- `cd credit-coach && python -m pytest tests/test_customer_artifact_collection.py -q` -> passed (`12 passed`)
- `cd credit-coach && python -m pytest tests/test_selected_surface_consistency.py -q` -> passed (`3 passed`)
- `cd credit-coach && python -m pytest tests/test_customer_artifact_collection.py tests/test_selected_surface_consistency.py -q` -> passed (`15 passed`)

## Deviations from Plan

None.

## Issues Encountered

- Legacy no-valid-winner parity fixtures initially failed because they did not carry the new zeroed movement fields; the fixtures were updated so parity remains explicit instead of silently tolerant.

## User Setup Required

None.

## Next Phase Readiness

- Cohort evaluation can now consume selected-path movement truth directly from runtime-first artifact seams.
- Wave 3 can focus on cohort evidence and downstream trust proof without reopening runtime or collection propagation.

## Self-Check

PASSED

---
*Phase: 64-movement-focused-path-ranking*
*Completed: 2026-04-07*
