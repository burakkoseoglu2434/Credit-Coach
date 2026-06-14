---
phase: 60-validation-cohort-evaluation
plan: 02
subsystem: artifacts
tags: [batch-eval, collection, pilot-mixed, exports]
provides:
  - batch Phase 60 cohort evidence artifacts
  - pilot-mixed collection evidence exports
  - manifest and summary wiring for Phase 60 files
affects: [batch-evaluation, customer-artifact-collection, manifests]
key-files:
  created: []
  modified:
    - credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py
    - credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py
    - credit-coach/tests/test_customer_artifact_collection.py
requirements-completed: [EVAL-01, EVAL-02]
completed: 2026-04-05
---

# Phase 60: Validation & Cohort Evaluation Summary

**Materialized one consistent Phase 60 artifact family across denied, high-risk denied, and pilot-mixed evidence paths**

## Accomplishments

- Batch evaluation now writes Phase 60 cohort evidence JSON, Markdown, and CSV tables next to the existing candidate-quality outputs.
- Customer artifact collection now carries path metrics and execution-aware value into `customer_metrics.csv`, builds a pilot-mixed Phase 60 evidence package, and exposes those files through the manifest.
- Collection summary Markdown now includes a dedicated Phase 60 evidence section plus direct links to the exported Phase 60 tables.

## Key Decisions

- Reused `pilot_mixed` as the calibration-ready population instead of creating a new cohort policy.
- Kept the Phase 60 artifact family additive and file-based so existing collection and calibration outputs remain unchanged.
- Used the same export helper for batch and collection to avoid drift between denied/high-risk and pilot-mixed reporting.

## Verification

- `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py tests/test_batch_candidate_diversity.py tests/test_customer_artifact_collection.py -q`

## Task Commits

Atomic task commits were intentionally skipped in this pass.

The shared worktree already contained active local changes in Phase 60 target files, so task-level commits would have risked bundling unrelated work into the same history slice.
