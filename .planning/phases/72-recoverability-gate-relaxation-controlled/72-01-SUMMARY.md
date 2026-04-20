---
phase: 72-recoverability-gate-relaxation-controlled
plan: 01
subsystem: recourse-gate
tags: [recoverability, recourse, gating, assisted_full, provenance, pytest]

requires: []
provides:
  - assisted_full recourse tier with explicit provenance fields
  - Wave 1 assisted_full surfacing (single allowlisted customer-only step) with deterministic fallback to limited
  - Additive cohort export columns for assisted_full and pre-gate shadow fields
  - Unit tests for assisted_full routing, pruning, and fallback behavior
affects: [phase-72, phase-73, cohort-evaluation, surfacing, messaging]

tech-stack:
  added: []
  patterns:
    - config-driven assisted_full policy (read via recourse_gate_config)
    - pre-gate shadow fields persisted before limited rewrite

key-files:
  created:
    - credit-coach/tests/test_recourse_gate_relaxation.py
  modified:
    - credit-coach/src/credit_coach/evaluation/recoverability.py
    - credit-coach/src/credit_coach/cli/run_recourse.py
    - credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py

key-decisions:
  - "Eligibility is computed in run_recourse and expressed as assisted_full_flag; build_recourse_gate only reads flags and emits modes/reason codes."
  - "Wave 1 assisted_full surfaces exactly one allowlisted customer-only step with deterministic preference order (adjust_requested_loan_amount > limit_credit_usage > reduce_spending), otherwise falls back to limited."

patterns-established:
  - "Assisted_full provenance fields: assisted_full_flag, assisted_full_reason_codes_json, assisted_full_thresholds_json."

requirements-completed: [GATE-01, GATE-02, GATE-03, TRUST-01, TRUST-02, TRUST-03]

duration: 12m
completed: 2026-04-20
---

# Phase 72 Plan 01: Recoverability Gate Relaxation (Controlled) Summary

**Introduces an `assisted_full` intermediate recourse tier with strict Wave 1 surfacing constraints (single allowlisted customer-only action) and explicit provenance, without touching winner selection/ranking or trust counters.**

## Performance

- **Duration:** 11m 52s
- **Started:** 2026-04-20T07:21:02Z
- **Completed:** 2026-04-20T07:32:54Z
- **Tasks:** 4
- **Files modified:** 4 (plus 1 test file created)

## Accomplishments

- Added `recourse_mode=assisted_full` to the recourse gate contract (actionable posture, new gate reason code).
- Implemented Wave 1 assisted_full routing + pruning in the recourse gating seam with deterministic fallback to limited.
- Exported assisted_full provenance and pre-gate shadow fields additively in `customer_level_analysis.csv`.
- Locked behavior with unit tests for eligibility, customer-only restriction, allowlist pruning, and fallback modes.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add assisted_full schema support to the gate (no eligibility logic)** - `f0fc687` (feat)
2. **Task 2: Enforce Wave 1 assisted_full constraints + fallback in recourse gating seam** - `d0b5f1e` (feat)
3. **Task 3: Export assisted_full provenance fields additively in cohort evaluation artifacts** - `c5926e3` (feat)
4. **Task 4: Add unit tests locking assisted_full routing, allowlist pruning, and fallback behavior** - `f68ed20` (test)

## Files Created/Modified

- `credit-coach/src/credit_coach/evaluation/recoverability.py` - Allows `recourse_mode=assisted_full` when `assisted_full_flag=1`, with stable legacy reason codes.
- `credit-coach/src/credit_coach/cli/run_recourse.py` - Computes assisted_full eligibility + provenance, enforces Wave 1 customer-only allowlist surfacing, and falls back to limited deterministically.
- `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py` - Adds assisted_full and pre-gate provenance columns to `customer_level_analysis.csv` (additive only).
- `credit-coach/tests/test_recourse_gate_relaxation.py` - Unit tests for assisted_full routing, pruning, and fallback behavior.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Ensure pruned assisted_full outputs report a single surfaced step**
- **Found during:** Task 4 (unit tests)
- **Issue:** Pruning to 1 step did not update `best_action_count`, so `selected_action_count` could drift from the surfaced single-step contract.
- **Fix:** Set `best_action_count=1` and `zero_step_flag=0` when pruning to one step.
- **Files modified:** `credit-coach/src/credit_coach/cli/run_recourse.py`
- **Verification:** `PYTHONPATH=src python3 -m pytest tests/test_recourse_gate_relaxation.py -q`
- **Committed in:** `85fbf61`

## Verification

- `cd credit-coach && PYTHONPATH=src python3 -m compileall -q src`
- `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_cohort_evaluation.py -q`
- `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_recourse_gate_relaxation.py -q`

## Issues Encountered

- The working tree contained many unrelated local changes (including `.DS_Store` and `.planning/*`). Plan commits staged only the files listed in `72-01-PLAN.md`.

## Next Phase Readiness

- Phase 72-02 can calibrate and lock assisted_full thresholds by enabling `recourse_gate.assisted_full` in the recourse config and running cohort evaluations with provenance already exported.

## Self-Check: PASSED

- Summary file present on disk
- All task + deviation commits present in git history
