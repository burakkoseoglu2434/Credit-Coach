---
phase: 71-coverage-diagnostics-failure-analysis
plan: "02"
subsystem: evaluation
tags: [coverage, diagnostics, w2a, segmentation]
requires:
  - phase: 71-coverage-diagnostics-failure-analysis
    provides: "Coverage diagnostics library + CLI (coverage_diagnostics/* artifacts)"
provides:
  - "W2a + control-anchor coverage diagnostics artifacts (local run dirs)"
  - "Segment-level empty-state/actionability/winner-availability rates"
  - "Phase 72 handoff recommendation rooted in derived buckets"
affects: [phase-72, gating, reporting]
tech-stack:
  added: []
  patterns: ["Run-dir co-located diagnostics under artifacts/evaluations/<run>/coverage_diagnostics/"]
key-files:
  created:
    - .planning/phases/71-coverage-diagnostics-failure-analysis/71-02-SUMMARY.md
  modified: []
key-decisions:
  - "Use W2a_large_n3000_seed42 as the primary diagnosis cohort and S1_small_n300_seed42 as the control anchor for taxonomy stability."
  - "Treat latent_value_but_gate_suppressed as the highest-leverage Phase 72 relaxation target bucket for mid-risk."
patterns-established:
  - "Phase 71 diagnostics are descriptive: derived buckets explain outcomes without altering shipped gate codes."
requirements-completed: [COV-02, COV-03]
duration: 25min
completed: 2026-04-18
---

# Phase 71: Coverage Diagnostics & Failure Analysis — Plan 02 Summary

**W2a diagnostics quantify that empty-state is dominated by `rankable_but_no_movement`, with a smaller but actionable `latent_value_but_gate_suppressed` slice concentrated in `mid_risk` (Phase 72 target).**

## Performance

- **Duration:** 25 min
- **Tasks:** 3
- **Files modified:** 1 (docs)

## Run Directories

- **Primary (W2a):** `credit-coach/artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_TEST/W2a_large_n3000_seed42`
- **Control anchor:** `credit-coach/artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_TEST/S1_small_n300_seed42`

Diagnostics output location (both dirs):
- `coverage_diagnostics/coverage_diagnostic_summary.json`
- `coverage_diagnostics/coverage_diagnostic_customer_breakdown.csv`
- `coverage_diagnostics/coverage_reason_frequency.csv`
- `coverage_diagnostics/empty_state_decomposition.json`

## Key Findings (W2a)

Overall:
- `n=3000`
- `empty_state_rate=0.97`, `actionability_rate=0.03`, `selected_plan_availability_rate=0.03`

Segment-level (recoverability_bucket normalized; `structural_limited` → `hard_denied`):
- **near_threshold (`n=108`)**: `empty_state_rate=0.1667`, `actionability_rate=0.8333`
  - buckets: `selected_plan_present=90`, `rankable_but_no_movement=10`, `latent_value_but_gate_suppressed=8`
- **mid_risk (`n=463`)**: `empty_state_rate=1.0`, `actionability_rate=0.0`
  - buckets: `rankable_but_no_movement=337`, `latent_value_but_gate_suppressed=126`
- **hard_denied (`n=2429`)**: `empty_state_rate=1.0`, `actionability_rate=0.0`
  - buckets: `rankable_but_no_movement=2233`, `latent_value_but_gate_suppressed=191`, `movement_but_no_threshold_signal=5`

Empty-state decomposition (W2a; `n=2910` empty-state customers):
- `rankable_but_no_movement=2580`
- `latent_value_but_gate_suppressed=325`
- `movement_but_no_threshold_signal=5`

## Taxonomy Stability (Control Anchor)

Control-anchor (`S1_small_n300_seed42`) shows the same dominant shape:
- near-threshold mostly `selected_plan_present`
- mid-risk and hard-denied dominated by `rankable_but_no_movement` with a meaningful `latent_value_but_gate_suppressed` minority

## Phase 72 Recommendation

**Target bucket:** `latent_value_but_gate_suppressed` within `mid_risk`.

**Why this bucket first:** it is the clearest “potentially useful latent value exists” slice that is currently routed to limited/empty-state; in W2a it accounts for `126/463` mid-risk customers.

**Conservative precondition (from Phase 71 thresholds):**
- treat a customer as eligible for Phase 72 intermediate surfacing only if the diagnostic indicates threshold-signal presence via:
  - `threshold_reach_possible == true` OR
  - `max_gap_closure_rate > 0.05` OR
  - `path_reaches_threshold_flag == true`

**Hard invariants Phase 72 must preserve:**
- `selected_invalid_winner_count = 0`
- `selected_surface_drift_count = 0`
- `operator_packet_contradiction_count = 0`

## Deviations from Plan

None — executed as written.

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness

- Phase 72 can consume `coverage_diagnostics/coverage_diagnostic_customer_breakdown.csv` to implement a controlled, diagnosis-led relaxation tier while keeping all trust counters clean.

---
*Phase: 71-coverage-diagnostics-failure-analysis*
*Completed: 2026-04-18*

