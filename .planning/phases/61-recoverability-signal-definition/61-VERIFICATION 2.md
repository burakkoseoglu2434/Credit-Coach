---
phase: 61-recoverability-signal-definition
verified: 2026-04-11T12:12:04+03:00
status: passed
score: 4/4 must-haves verified
requirements: [RECV-01, RECV-02, RECV-03, RECV-04]
---

# Phase 61: Recoverability Signal Definition Verification Report

**Phase Goal:** derive deterministic recoverability fields from current score distance and shipped structural signals.
**Verified:** 2026-04-11T12:12:04+03:00
**Status:** passed

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | The system computes deterministic `approval_gap` and `normalized_gap` from shipped `base_pd` and `tau` (no retraining). | ✓ VERIFIED | `credit-coach/src/credit_coach/evaluation/recoverability.py:78` (`compute_approval_gap`), `credit-coach/src/credit_coach/evaluation/recoverability.py:82` (`compute_normalized_gap`), `credit-coach/tests/test_recoverability_signals.py:36` |
| 2 | The system deterministically assigns `risk_band` and `recoverability_bucket` (`near_threshold`, `mid_risk`, `structural_limited`) and emits a gap-only `recoverability_score`. | ✓ VERIFIED | `credit-coach/src/credit_coach/evaluation/recoverability.py:87`, `credit-coach/src/credit_coach/evaluation/recoverability.py:98`, `credit-coach/src/credit_coach/evaluation/recoverability.py:107`, `credit-coach/tests/test_recoverability_signals.py:36` |
| 3 | The system emits deterministic threshold reachability and structural-limit diagnostics without changing downstream decision semantics. | ✓ VERIFIED | `credit-coach/src/credit_coach/evaluation/recoverability.py:124` (`threshold_reach_possible`), `credit-coach/src/credit_coach/evaluation/recoverability.py:218` (`build_recoverability_signal`), `credit-coach/tests/test_recoverability_signals.py:66` |
| 4 | Recoverability signal fields are propagated additively into runtime summaries, customer artifact collection, cohort evaluation artifacts, and cohort evidence packaging. | ✓ VERIFIED | runtime: `credit-coach/src/credit_coach/cli/run_recourse.py:434`; calibration work frame: `credit-coach/src/credit_coach/evaluation/decision_calibration.py:381`; collection: `credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py:620`; cohort eval signal resolution: `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py:166`; evidence packaging: `credit-coach/src/credit_coach/evaluation/cohort_evidence.py:191` |

**Score:** 4/4 truths verified

### Implementation Scope Summary (What Phase 61 Ships)

Source-of-truth phase artifacts:
- `.planning/phases/61-recoverability-signal-definition/61-01-SUMMARY.md`
- `.planning/phases/61-recoverability-signal-definition/61-02-SUMMARY.md`
- `.planning/phases/61-recoverability-signal-definition/61-03-SUMMARY.md`
- `.planning/phases/61-recoverability-signal-definition/61-VALIDATION.md`

Implemented behavior:
- canonical recoverability signal helper (gap math, bucket/band, score, reachability)
- additive structural diagnostic fields + reason-code lists for auditability
- additive propagation into runtime summaries, calibration work frames, customer collection rows, cohort evaluation outputs, and cohort evidence exports

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `credit-coach/src/credit_coach/evaluation/recoverability.py` | canonical recoverability signal helper | ✓ EXISTS + SUBSTANTIVE | Defines deterministic gap/bucket/score + reachability + diagnostic reason-codes via `build_recoverability_signal(...)`. |
| `credit-coach/src/credit_coach/evaluation/__init__.py` | public exports | ✓ EXISTS + SUBSTANTIVE | Exports recoverability helpers into the evaluation package surface. |
| `credit-coach/src/credit_coach/cli/run_recourse.py` | runtime emission | ✓ EXISTS + SUBSTANTIVE | Attaches recoverability signal fields to the roadmap summary additively. |
| `credit-coach/src/credit_coach/evaluation/decision_calibration.py` | calibration-safe additive fields | ✓ EXISTS + SUBSTANTIVE | Adds approval gap + bucket + score to work frames deterministically. |
| `credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py` | collection propagation | ✓ EXISTS + SUBSTANTIVE | Preserves signal fields into customer metrics rows. |
| `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py` | cohort visibility | ✓ EXISTS + SUBSTANTIVE | Resolves signal from runtime-first outputs and includes it in cohort artifacts. |
| `credit-coach/src/credit_coach/evaluation/cohort_evidence.py` | evidence packaging | ✓ EXISTS + SUBSTANTIVE | Rolls up recoverability distributions and rates in evidence packages. |
| `credit-coach/tests/test_recoverability_signals.py` | unit + integration proof | ✓ EXISTS + SUBSTANTIVE | Locks gap math, buckets, reachability, and reason-code derivation. |

**Artifacts:** 8/8 verified

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `build_recoverability_signal(...)` | runtime roadmap summary | `_attach_recoverability_signal_to_roadmap(...)` | ✓ WIRED | `credit-coach/src/credit_coach/cli/run_recourse.py:434` attaches signal fields additively. |
| runtime roadmap summary | calibration work frame | `build_selection_work_frame(...)` | ✓ WIRED | `credit-coach/src/credit_coach/evaluation/decision_calibration.py:381` emits `approval_gap`, `recoverability_bucket`, `recoverability_score` additively. |
| runtime/metrics summary | collection metrics rows | customer artifact collection row builder | ✓ WIRED | `credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py:620` copies recoverability fields into flat rows. |
| runtime-first truth | cohort evaluation artifacts | `_resolve_recoverability_signal(...)` | ✓ WIRED | `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py:166` resolves and emits recoverability fields deterministically. |
| customer rows | cohort evidence packaging | evidence rollups | ✓ WIRED | `credit-coach/src/credit_coach/evaluation/cohort_evidence.py:191` emits `threshold_reach_possible_rate` and `recoverable_customer_rate` and distributions. |

**Wiring:** 5/5 connections verified

## Requirements Coverage (Phase 61)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| `RECV-01`: compute `approval_gap` as deterministic distance from current score to threshold | ✓ SATISFIED | `credit-coach/src/credit_coach/evaluation/recoverability.py:78` + assertions in `credit-coach/tests/test_recoverability_signals.py:36` |
| `RECV-02`: compute `normalized_gap` and `recoverability_score` using shipped scores/signals only (no retraining) | ✓ SATISFIED | `credit-coach/src/credit_coach/evaluation/recoverability.py:82`, `credit-coach/src/credit_coach/evaluation/recoverability.py:107`, `credit-coach/tests/test_recoverability_signals.py:36` |
| `RECV-03`: assign `risk_band` and `recoverability_bucket` deterministically | ✓ SATISFIED | `credit-coach/src/credit_coach/evaluation/recoverability.py:87`, `credit-coach/src/credit_coach/evaluation/recoverability.py:98`, `credit-coach/tests/test_recoverability_signals.py:36` |
| `RECV-04`: emit recoverability signal fields into evaluation artifacts for cohort audit | ✓ SATISFIED | runtime attach: `credit-coach/src/credit_coach/cli/run_recourse.py:434`; collection propagation: `credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py:620`; cohort evaluation: `credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py:166`; evidence rollups: `credit-coach/src/credit_coach/evaluation/cohort_evidence.py:191` |

**Coverage:** 4/4 requirements satisfied

## Trust-Safety Statement (Phase Boundary)

Phase 61 is **signal + propagation only**. It does not change decision logic or introduce new promises:
- **No planner changes:** no selection/chooser logic changes are required for Phase 61 acceptance (signal is computed and exported additively).
- **No threshold policy changes:** `tau` remains an input; Phase 61 only computes distance-to-threshold fields (`approval_gap`, `normalized_gap`) and derived diagnostics.
- **No recourse gating introduced (as behavior):** Phase 61 does not apply full-vs-limited routing or suppress/promote selected surfaces; routing behavior is handled in later phases (Phase 63).

## Anti-Patterns Found

None observed in the Phase 61 scope.

## Human Verification Required

None. Phase 61’s acceptance criteria are deterministic field correctness and additive artifact propagation, which are covered by the phase’s unit/integration/regression test commands captured below.

## Gaps Summary

**No gaps found.** Phase 61’s definition of done is met by the shipped implementation and the recorded test evidence.

## Verification Metadata

**Verification approach:** goal-backward against Phase 61 roadmap goal and `RECV-01` through `RECV-04`
**Automated checks:** phase-local pytest commands (recorded below)
**Human checks required:** 0
**Verification timestamp:** 2026-04-11T12:12:04+03:00

## Finish

### 1. status

`passed`

### 2. verification result summary

Phase 61 meets its roadmap goal. The repo contains a deterministic recoverability signal layer (gap math, bucket/band, score, reachability, and structural diagnostics) and it is propagated additively into runtime, calibration work frames, customer artifact collection, cohort evaluation artifacts, and cohort evidence packaging, without requiring planner, threshold-policy, or routing changes for acceptance.

### 3. tests run (as recorded in Phase 61 execution summaries)

- `cd credit-coach && python -m pytest tests/test_recoverability_signals.py -q` -> `7 passed` (from `.planning/phases/61-recoverability-signal-definition/61-01-SUMMARY.md`)
- `cd credit-coach && python -m pytest tests/test_recoverability_signals.py tests/test_decision_calibration.py tests/test_customer_artifact_collection.py -q` -> `32 passed` (from `.planning/phases/61-recoverability-signal-definition/61-02-SUMMARY.md`)
- `cd credit-coach && python -m pytest tests/test_recoverability_signals.py tests/test_customer_artifact_collection.py tests/test_cohort_evaluation.py tests/test_decision_calibration.py tests/test_decision_ownership.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py -q` -> `50 passed` (from `.planning/phases/61-recoverability-signal-definition/61-03-SUMMARY.md`)

### 4. blockers/gaps if any

None.

