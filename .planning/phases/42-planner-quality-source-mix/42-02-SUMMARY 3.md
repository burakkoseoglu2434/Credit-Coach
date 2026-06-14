---
phase: 42-planner-quality-source-mix
plan: 02
subsystem: competitiveness-and-source-mix-reporting
tags: [engine, calibration, collection, pytest]
requires: [42-01]
provides:
  - near-tie source-aware preference that preserves materially better candidates
  - internal-vs-dice competitiveness metrics plus recovery-lane reporting
  - additive source-mix packaging in customer and collection artifacts
affects: [phase-42, planner-quality, source-mix, calibration]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/coaching/planner.py
    - credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py
    - credit-coach/src/credit_coach/cli/run_recourse.py
    - credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py
    - credit-coach/tests/test_planner_quality_source_mix.py
    - credit-coach/tests/test_customer_artifact_collection.py
    - credit-coach/tests/test_decision_calibration.py
key-decisions:
  - "Source preference only breaks genuine cross-source near ties and never overrides materially better candidates."
  - "`internal vs dice` remains the main competitiveness axis; `rule` and `fallback` are reported as recovery lanes."
  - "Collection outputs stay additive over Phase 41 calibration packaging and do not become a second decision layer."
patterns-established:
  - "Planner competitiveness is now readable from the same collection run root as funnel, readiness, and operator artifacts."
requirements-completed: [PLAN-01]
duration: manual-execution
completed: 2026-03-23
---

# Phase 42 Plan 02 Summary

**Source mix is now honest and reviewable: collection artifacts can distinguish real planner wins from recovery-lane rescues.**

## Accomplishments

- Added disciplined source-aware tie-breaking in `planner.py` so only true cross-source near ties prefer `internal`, then `dice`, then `rule`, then `fallback`.
- Extended batch candidate-quality rollups with non-empty contender share, approved-or-conditional contender share, execution-aware value, offer-ready share, provisional-offer share, and approval-shell share.
- Added per-customer source counts, source presence flags, candidate-source entropy, pool-diversity index, and best-plan source/offer/contender metrics to single-customer metrics summaries.
- Expanded collection-root summary and manifest with `source_mix_summary`, planner source-mix sections, internal-vs-dice competitiveness wording, and explicit recovery-lane rates.

## Verification

- `cd credit-coach && python -m pytest tests/test_planner_quality_source_mix.py tests/test_customer_artifact_collection.py tests/test_decision_calibration.py -q`

## Notes

- This plan makes competitiveness visible and honest. Diversity collapse and offer-maturity hardening are completed in Plan `03`.

---
*Phase: 42-planner-quality-source-mix*
*Completed: 2026-03-23*
