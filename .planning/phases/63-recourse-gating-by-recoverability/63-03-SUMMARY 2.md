---
phase: 63-recourse-gating-by-recoverability
plan: 03
subsystem: cohort-evidence
tags: [recoverability, gating, cohort-evaluation, explanation-pack, pytest]
requires:
  - phase: 63-recourse-gating-by-recoverability
    plan: 01
    provides: runtime full-vs-limited gate contract and limited-mode selected-surface suppression
  - phase: 63-recourse-gating-by-recoverability
    plan: 02
    provides: runtime-first gate propagation through flat artifacts and operator-facing packet seams
provides:
  - cohort customer rows with runtime-first recourse gate truth
  - additive cohort evidence for full-vs-limited and actionable-vs-informational posture
  - downstream explanation-pack proof that limited mode stays recommendation-free
affects: [phase-64-ranking-inputs, cohort-audit-artifacts, trust-surfaces]
tech-stack:
  added: []
  patterns: [runtime-first cohort reporting, additive gate evidence, informational-only limited mode]
key-files:
  created:
    - .planning/phases/63-recourse-gating-by-recoverability/63-03-SUMMARY.md
  modified:
    - credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py
    - credit-coach/src/credit_coach/evaluation/cohort_evidence.py
    - credit-coach/tests/test_cohort_evaluation.py
    - credit-coach/tests/test_decision_explanation_pack.py
key-decisions:
  - "Cohort evaluation now reads `recourse_mode`, `recommendation_mode`, and gate reasons from runtime-first roadmap and metrics artifacts instead of deriving a second routing rule."
  - "Phase 60 evidence packaging gained a separate recourse-gate table so gating posture is auditable without changing movement or trust semantics."
  - "Limited mode remains informational only; explanation-pack coverage was extended instead of redesigning downstream text."
patterns-established:
  - "Customer-level and cohort-level analytics should preserve the Phase 63 gate contract additively beside recoverability signals."
  - "Trust-sensitive downstream consumers should prove honesty through empty-state regressions rather than introducing softened recommendation language."
requirements-completed: [GATE-02, GATE-03]
duration: 1min
completed: 2026-04-07
---

# Phase 63: Recourse Gating By Recoverability Summary

**Cohort evaluation and evidence packaging now expose the full Phase 63 gate contract, and explanation-pack regressions prove limited mode stays informational and empty-state-safe all the way downstream.**

## Performance

- **Duration:** 1 min
- **Started:** 2026-04-07T22:41:59+03:00
- **Completed:** 2026-04-07T22:42:26+03:00
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added runtime-first gate fields to cohort customer rows so `recourse_mode`, `recommendation_mode`, `recourse_gate_version`, and gate reasons are preserved in analyst-auditable outputs.
- Extended cohort and Phase 60 evidence metrics with additive full-vs-limited and actionable-vs-informational distributions.
- Proved explanation-pack empty-state behavior remains honest under limited mode without leaking fake promoted guidance.

## Task Commits

Each task was committed atomically:

1. **Task 1: Persist gate truth and recommendation posture in cohort evaluation outputs** - `148c002` (feat)
2. **Task 2: Prove downstream explanation surfaces remain honest under limited mode** - `f83e92a` (test)

## Files Created/Modified

- `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py` - Added runtime-first recourse gate resolution for cohort customer rows, exposed gate metrics in aggregate reporting, and surfaced limited/informational rates in the rendered report.
- `credit-coach/src/credit_coach/evaluation/cohort_evidence.py` - Added recourse-gate distributions and rates to cohort evidence packages, markdown rendering, and CSV/JSON artifact exports.
- `credit-coach/tests/test_cohort_evaluation.py` - Added customer-row, aggregate-metric, evidence-table, and limited-mode cohort regressions for the Phase 63 gate contract.
- `credit-coach/tests/test_decision_explanation_pack.py` - Extended explanation-pack empty-state coverage with Phase 63 limited-mode gate metadata.
- `.planning/phases/63-recourse-gating-by-recoverability/63-03-SUMMARY.md` - Captured Wave 3 execution outcome, verification, and commit traceability.

## Decisions Made

- Reused runtime-emitted gate truth in cohort analysis rather than teaching cohort code to infer recoverability routing independently.
- Kept recourse-gate reporting additive as a separate evidence table so older movement and trust conclusions remain comparable.
- Treated explanation-pack honesty as a regression-proofing concern, not a narrative redesign task.

## Verification

- `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py -q` -> passed (`6 passed`)
- `cd credit-coach && python -m pytest tests/test_decision_explanation_pack.py tests/test_operator_packet_coherence.py tests/test_selected_surface_consistency.py -q` -> passed (`13 passed`)
- `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py tests/test_decision_explanation_pack.py tests/test_operator_packet_coherence.py tests/test_selected_surface_consistency.py -q` -> passed (`19 passed`)

## Deviations from Plan

None - the implementation stayed within the planned cohort/evidence/reporting and explanation-pack seams.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 63 now closes with runtime, flat-artifact, operator, cohort, and explanation-pack consumers all aligned on one honest full-vs-limited gate contract.
- Phase 64 can focus on movement-oriented ranking using a cohort-visible recoverability gate baseline instead of reopening routing honesty work.

## Self-Check

PASSED

---
*Phase: 63-recourse-gating-by-recoverability*
*Completed: 2026-04-07*
