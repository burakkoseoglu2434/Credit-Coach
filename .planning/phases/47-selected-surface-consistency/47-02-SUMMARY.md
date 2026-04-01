---
phase: 47-selected-surface-consistency
plan: 02
subsystem: flat-and-consumer-propagation
tags: [selected-surface, collection, operator-packet, explanation-pack, drift-guard]
requires: [47-01]
provides:
  - flat propagation of selected overlay fields
  - shared selected recommendation projection across operator and explanation surfaces
  - parity checks between selected row truth and consumer-safe overlay truth
affects: [phase-47, collection, operator-review, explanation-pack, schema]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py
    - credit-coach/src/credit_coach/ops/operator_review.py
    - credit-coach/src/credit_coach/ops/decision_explanation_pack.py
    - credit-coach/src/credit_coach/data/schema.py
    - credit-coach/src/credit_coach/pilot/contracts.py
    - credit-coach/tests/test_customer_artifact_collection.py
    - credit-coach/tests/test_operator_review_pack.py
    - credit-coach/tests/test_decision_explanation_pack.py
key-decisions:
  - "Selected recommendation text has one owner: selected valid plan projection written into summary."
  - "Fallback is explicit empty-state only; operator and explanation surfaces may not invent alternative recommendation text."
  - "Technical selected rows and consumer-safe selected overlays are different views of one selected truth chain."
patterns-established:
  - "Operator packet and explanation pack now consume shared selected recommendation projection metadata instead of recomputing text independently."
requirements-completed: [CONS-01, CONS-03]
duration: manual-execution
completed: 2026-04-01
---

# Phase 47 Plan 02 Summary

**Phase 47 now propagates one selected recommendation projection into flat metrics, plans, operator packets, and explanation packs.**

## Accomplishments

- Extended [run_customer_artifact_collection.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/cli/run_customer_artifact_collection.py) to emit selected overlay fields in flat metrics and plan rows:
  - `selected_decision_status`
  - `selected_plan_status_internal`
  - `selected_recommendation_text`
  - `selected_recommendation_source`
  - `selected_action_count`
  - `selected_recommendation_projection_version`
- Tightened collection parity checks so:
  - `no_valid_winner` requires zero selected rows and explicit empty-state projection
  - selected row technical status must match `selected_plan_status_internal`
- Updated [operator_review.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/operator_review.py) to read selected recommendation projection from summary, render explicit empty-state output, and carry projection trace fields in the technical appendix.
- Updated [decision_explanation_pack.py](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach/src/credit_coach/ops/decision_explanation_pack.py) to consume selected projection fields directly instead of recomputing recommendation text from narrative steps.
- Added additive schema fields needed for selected-surface traceability and drift guarding.

## Verification

- `python -m pytest credit-coach/tests/test_selected_surface_consistency.py credit-coach/tests/test_customer_artifact_collection.py credit-coach/tests/test_operator_review_pack.py credit-coach/tests/test_decision_explanation_pack.py -q`

## Notes

- Empty-state rendering is explicit, but `selected_recommendation_text` remains `null` in raw summary for `no_valid_winner`.

---
*Phase: 47-selected-surface-consistency*
*Completed: 2026-04-01*
