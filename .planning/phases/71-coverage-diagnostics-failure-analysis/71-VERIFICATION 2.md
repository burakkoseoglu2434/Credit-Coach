---
phase: 71-coverage-diagnostics-failure-analysis
verified: 2026-04-18T17:25:47+03:00
status: passed
score: 3/3 must-haves verified
requirements: [COV-01, COV-02, COV-03]
---

# Phase 71: Coverage Diagnostics & Failure Analysis Verification Report

**Phase Goal:** explain why customers fall into limited mode / empty-state and publish segment-level failure patterns that quantify the true coverage bottleneck (diagnostic-only; no runtime behavior change).
**Verified:** 2026-04-18T17:25:47+03:00
**Status:** passed

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A machine-readable diagnostic artifact explains recommendation-mode outcomes per customer (without changing selection/gating semantics). | ✓ VERIFIED | `credit-coach/src/credit_coach/evaluation/coverage_diagnostics.py` emits `coverage_diagnostic_customer_breakdown.csv` including `recourse_mode`, `recommendation_mode`, `selected_recommendation_source`, empty/zero-action flags, and `coverage_loss_bucket`. CLI: `credit-coach/src/credit_coach/cli/run_v27_coverage_diagnostics.py`. |
| 2 | Failure reasons are broken down across at least `near_threshold`, `mid_risk`, and `hard_denied` segments. | ✓ VERIFIED | Segment normalization in `credit-coach/src/credit_coach/evaluation/coverage_diagnostics.py` maps `structural_limited -> hard_denied`; summaries include `by_segment`. Evidence: diagnostics run outputs (W2a + control anchor) in `coverage_diagnostics/coverage_diagnostic_summary.json`. |
| 3 | Empty-state rate, actionability rate, and selected-plan availability are published overall and by segment. | ✓ VERIFIED | `coverage_diagnostics/coverage_diagnostic_summary.json` includes `overall` and `by_segment` with `empty_state_rate`, `actionability_rate`, `selected_plan_availability_rate`. |

**Score:** 3/3 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `credit-coach/src/credit_coach/evaluation/coverage_diagnostics.py` | deterministic diagnostics generator | ✓ EXISTS + SUBSTANTIVE | Derived bucket assignment + artifact writers. |
| `credit-coach/src/credit_coach/cli/run_v27_coverage_diagnostics.py` | post-hoc CLI | ✓ EXISTS + SUBSTANTIVE | Reads `customer_level_analysis.csv` from run dir; writes `coverage_diagnostics/*`. |
| `credit-coach/tests/test_coverage_diagnostics.py` | unit proof | ✓ EXISTS + SUBSTANTIVE | Locks bucket assignment and required artifact emission. |

### Evidence Runs (Local Artifacts)

Primary W2a run directory:
- `credit-coach/artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_TEST/W2a_large_n3000_seed42/coverage_diagnostics/`

Control anchor run directory:
- `credit-coach/artifacts/evaluations/v26_phase70_large_data_diagnostic_audit_TEST/S1_small_n300_seed42/coverage_diagnostics/`

Each contains:
- `coverage_diagnostic_customer_breakdown.csv`
- `coverage_diagnostic_summary.json`
- `coverage_reason_frequency.csv`
- `empty_state_decomposition.json`

## Requirements Coverage (Phase 71)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| `COV-01` | ✓ SATISFIED | Library + CLI emit per-customer breakdown and machine-readable summary artifacts. |
| `COV-02` | ✓ SATISFIED | Diagnostics report `near_threshold`, `mid_risk`, and normalized `hard_denied` segment slices. |
| `COV-03` | ✓ SATISFIED | Summary JSON publishes empty-state/actionability/selected availability overall and by segment. |

## Trust-Safety Statement (Phase Boundary)

Phase 71 is diagnostic-only:
- no changes to gating, selection, or surfaced recommendation semantics
- cohort evaluation runner emission is opt-in via `--emit_coverage_diagnostics` (default off)
- diagnostics are additive artifacts under `coverage_diagnostics/` for audit and phase handoff

## Human Verification Required

None.

## Finish

### status

`passed`

### verification result summary

Phase 71 meets its roadmap goal: it produces deterministic, additive coverage diagnostics that explain why W2a customers route to empty-state/limited outcomes, and publishes segment-level failure patterns and rates needed to drive Phase 72’s controlled gate relaxation.

### tests run

- `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_coverage_diagnostics.py -q` -> `3 passed`
- `cd credit-coach && PYTHONPATH=src python3 -m pytest tests/test_cohort_evaluation.py -q` -> `8 passed`

### blockers/gaps if any

None.
