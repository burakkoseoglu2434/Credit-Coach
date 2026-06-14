---
phase: 69-evidence-amplification
plan: 01
subsystem: evaluation
tags: [cohort, manifest, sampling, denied, phase69]
requires:
  - phase: 68-real-cohort-evidence-run
    provides: canonical denied cohort artifacts (runtime-first)
provides:
  - manifest-driven (no-sampling) cohort evaluation mode
  - deterministic Phase 69 cohort selection from Phase 68 canonical artifacts
  - Phase 69 cohort evaluation artifacts (customer-level + cohort-level)
affects: [phase-69, cohort-evaluation, evidence-pack, outcome-feedback]
tech-stack:
  added: []
  patterns: [manifest-driven evaluation, deterministic selection summary]
key-files:
  created:
    - credit-coach/src/credit_coach/cli/run_v25_phase69_evidence_amplification.py
  modified:
    - credit-coach/src/credit_coach/cli/run_v24_cohort_evaluation.py
    - credit-coach/tests/test_cohort_evaluation.py
key-decisions:
  - "Selection uses Phase 68 canonical customer_level_analysis.csv: primary `threshold_reach_possible==1`, secondary approval-gap cutoff using near/mid thresholds (relax to mid if near yields <50)."
  - "Evaluation rerun uses manifest mode (no sampling; with_replacement=false)."
patterns-established:
  - "Manifest mode: evaluate explicit `source_customer_id` set without replacement."
requirements-completed: []
duration: n/a
completed: 2026-04-11
---

# Phase 69-01 Summary

**Manifest-driven (no-sampling) cohort evaluation + deterministic Phase 69 cohort selection from Phase 68 canonical denied artifacts**

## Accomplishments
- Added `--customer_manifest_csv` support to `run_v24_cohort_evaluation.py` to evaluate an explicit `source_customer_id` set without sampling.
- Implemented `run_v25_phase69_evidence_amplification.py` to select a recoverable-heavy denied cohort from the canonical Phase 68 run and rerun evaluation in manifest mode.
- Produced a Phase 69 canonical cohort evaluation directory (all eligible customers under the locked selection rule).

## Verification
- `cd credit-coach && PYTHONPATH=src python -m pytest tests/test_cohort_evaluation.py -q`

## Canonical Phase 69 Run
- Phase 68 canonical source: `credit-coach/artifacts/evaluations/v25_real_cohort_eval_20260411_full_processed_all_denied_n367_seed42`
- Phase 69 cohort evaluation dir: `credit-coach/artifacts/evaluations/v25_phase69_recoverable_heavy_eval_20260411_full_processed_thr_reach_low_gap_all_seed42`
- Phase 69 cohort size (all eligible): `n=9` (see `selection_summary.json`)
- Trust counters (Phase 69): `selected_invalid_winner_count=0`, `selected_surface_drift_count=0`, `operator_packet_contradiction_count=0`

## Artifacts
- Selection:
  - `credit-coach/artifacts/evaluations/v25_phase69_recoverable_heavy_eval_20260411_full_processed_thr_reach_low_gap_all_seed42/selected_customer_ids.csv`
  - `credit-coach/artifacts/evaluations/v25_phase69_recoverable_heavy_eval_20260411_full_processed_thr_reach_low_gap_all_seed42/selection_summary.json`
- Evaluation:
  - `credit-coach/artifacts/evaluations/v25_phase69_recoverable_heavy_eval_20260411_full_processed_thr_reach_low_gap_all_seed42/customer_level_analysis.csv`
  - `credit-coach/artifacts/evaluations/v25_phase69_recoverable_heavy_eval_20260411_full_processed_thr_reach_low_gap_all_seed42/cohort_metrics.json`
  - `credit-coach/artifacts/evaluations/v25_phase69_recoverable_heavy_eval_20260411_full_processed_thr_reach_low_gap_all_seed42/cohort_evaluation_report.md`

## Deviations / Issues
- None (evaluation-only changes; runtime/model/planner/recourse unchanged).

