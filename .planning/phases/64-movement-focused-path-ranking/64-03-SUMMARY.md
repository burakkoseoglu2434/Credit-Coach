---
phase: 64-movement-focused-path-ranking
plan: 03
subsystem: cohort-evidence
tags: [movement-ranking, cohort-evidence, trust-proof, pytest]
requires:
  - phase: 64-01
    provides: recoverable/full-mode movement ranking contract and runtime activation seam
  - phase: 64-02
    provides: runtime and flat-artifact movement propagation with limited-mode clearing
provides:
  - cohort-visible selected-path movement ranking evidence
  - additive movement-ranking aggregate tables for later targeted evaluation
  - downstream trust proof that movement fields stay honesty-safe
affects: [phase-64-closeout, phase-65-targeted-evaluation, explanation-honesty, operator-packet-coherence]
tech-stack:
  added: []
  patterns: [runtime-first cohort propagation, additive evidence packaging, trust-safe diagnostics]
key-files:
  created:
    - .planning/phases/64-movement-focused-path-ranking/64-03-SUMMARY.md
  modified:
    - credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py
    - credit-coach/src/credit_coach/evaluation/cohort_evidence.py
    - credit-coach/tests/test_cohort_evaluation.py
    - credit-coach/tests/test_decision_explanation_pack.py
    - credit-coach/tests/test_operator_packet_coherence.py
    - credit-coach/tests/test_winner_integrity_hard_stop.py
key-decisions:
  - "Kept cohort outputs runtime-first by reading movement fields from roadmap and metrics summaries instead of recomputing ranking logic downstream."
  - "Added a dedicated movement-ranking evidence table rather than overloading recoverability or selected-path distributions with ambiguous fields."
  - "Proved movement diagnostics remain additive only; operator and explanation narratives still ignore them for user-facing honesty."
patterns-established:
  - "Selected-path ranking diagnostics can be surfaced at cohort level through additive evidence tables without changing planner or narrative semantics."
  - "Trust regressions can be re-proved by enriching shared roadmap fixtures with additive fields and asserting existing behavior stays unchanged."
requirements-completed: [MOVE-02, MOVE-03]
duration: 2min
completed: 2026-04-08
---

# Phase 64: Movement-Focused Path Ranking Summary

**Phase 64 now closes with selected-path movement truth visible in cohort outputs and explicit proof that the extra diagnostics do not change winner integrity, operator coherence, or explanation honesty.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-04-08T22:13:50+03:00
- **Completed:** 2026-04-08T22:15:43+03:00
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Propagated `movement_score`, `threshold_reach_probability`, `threshold_reach_priority_flag`, `movement_rank_reason_codes_json`, and `selected_path_movement_strength` into cohort customer rows and selected-plan audit rows.
- Published additive movement-ranking aggregates in cohort metrics and Phase 60 evidence artifacts, including mean movement score, mean threshold-reach probability, threshold-reach-priority rate, and selected-path movement-strength distribution.
- Re-proved that explanation packs, operator review packets, and limited-mode / no-valid-winner integrity paths stay fail-closed and narrative-stable when movement diagnostics are present.

## Task Commits

Each task was committed atomically:

1. **Task 1: Persist movement-ranking truth into cohort evaluation and evidence outputs** - `d8816e9` (feat)
2. **Task 2: Re-prove the trust baseline after the ranking refinement** - `2a8296c` (test)

## Files Created/Modified

- `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py` - Added selected-path movement fields to cohort customer rows, selected-plan audit payloads, and aggregate cohort metrics.
- `credit-coach/src/credit_coach/evaluation/cohort_evidence.py` - Added additive `movement_ranking` evidence packaging plus summary/CSV export support.
- `credit-coach/tests/test_cohort_evaluation.py` - Proved customer-level and cohort-level outputs carry the new movement truth in both full and limited modes.
- `credit-coach/tests/test_decision_explanation_pack.py` - Proved explanation packs remain external-only and honest when movement diagnostics are present in roadmap summary.
- `credit-coach/tests/test_operator_packet_coherence.py` - Proved operator packets ignore additive movement diagnostics for render behavior.
- `credit-coach/tests/test_winner_integrity_hard_stop.py` - Proved empty-state and limited-mode surfaces still clear movement truth fail-closed.
- `.planning/phases/64-movement-focused-path-ranking/64-03-SUMMARY.md` - Captured Wave 3 execution outcome, verification, and commit traceability.

## Decisions Made

- Chose a dedicated movement-ranking evidence table as the smallest clear audit surface for Phase 65 follow-on analysis.
- Preserved runtime-first truth by preferring `metrics_summary` / roadmap summary fields over any cohort-side heuristic recomputation.
- Kept downstream narrative systems untouched; movement diagnostics remain technical evidence only in this phase.

## Verification

- `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py -q` -> passed (`6 passed`)
- `cd credit-coach && python -m pytest tests/test_decision_explanation_pack.py tests/test_operator_packet_coherence.py tests/test_winner_integrity_hard_stop.py -q` -> passed (`15 passed`)
- `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py tests/test_decision_explanation_pack.py tests/test_operator_packet_coherence.py tests/test_winner_integrity_hard_stop.py -q` -> passed (`21 passed`)

## Deviations from Plan

None.

## Issues Encountered

- None beyond the expected need to keep limited-mode and no-valid-winner fixtures explicitly zeroed so the new movement diagnostics could not leak onto empty-state surfaces.

## User Setup Required

None.

## Next Phase Readiness

- Phase 65 can now compare recoverable-focused cohorts using explicit selected-path movement evidence instead of only broad movement-potential heuristics.
- Phase 64 is fully complete; the next logical step is planning `65 Targeted Cohort Evaluation`.

## Self-Check

PASSED

---
*Phase: 64-movement-focused-path-ranking*
*Completed: 2026-04-08*
