---
phase: 15-policy-optimization-layer
plan: 01
subsystem: offer-action-contract
tags: [offer, institutional-actions, schema, mixed-plans, pytest]
requires: []
provides:
  - explicit offer-bearing institutional actions inside the existing typed-action stack
  - structured offer-term schema and rankability metadata on `PlanAction` and `PlanRecord`
  - mixed-plan serialization with at most one active offer branch
affects: [phase-15, action-space, generator, cli, schema]
tech-stack:
  added: [credit-coach/src/credit_coach/recourse/offer_optimization.py]
  patterns: [offer-bearing institutional actions, mixed-plan contract, term completeness]
key-files:
  created: [credit-coach/src/credit_coach/recourse/offer_optimization.py]
  modified: [credit-coach/src/credit_coach/recourse/action_space.py, credit-coach/src/credit_coach/data/schema.py, credit-coach/src/credit_coach/recourse/generator.py, credit-coach/src/credit_coach/cli/run_recourse.py, credit-coach/tests/test_action_space.py, credit-coach/tests/test_recourse_redesign.py]
key-decisions:
  - "Offer actions stay under `action_class = institutional` and gain a separate `offer_type` plus `offer_terms` layer."
  - "Mixed winner plans may combine customer actions with at most one active rankable offer branch."
  - "Term-incomplete or approval-ambiguous institutional actions remain provisional evidence rather than ordinary winner candidates."
patterns-established:
  - "Offer-bearing action metadata now flows from action templates through generator serialization into canonical plan artifacts."
requirements-completed: [REC-08]
duration: manual-execution
completed: 2026-03-16
---

# Phase 15 Plan 01 Summary

**Institution-side offers are now real planning primitives instead of opaque placeholders.**

## Accomplishments
- Extended the institutional action catalog so offer-bearing actions carry explicit `offer_type`, `offer_terms`, approval-state, acceptance, and policy-arm metadata.
- Added the dedicated `offer_optimization.py` seam to build offer contracts, distinguish rankable versus provisional offers, and annotate mixed plans.
- Updated generator and recourse serialization so one coherent plan can contain customer actions plus one explicit active offer branch without breaking typed-action, probability, or trajectory compatibility.

## Verification
- `python -m pytest credit-coach/tests/test_action_space.py credit-coach/tests/test_recourse_redesign.py`

## Notes
- `action_key` remains user-facing while `feature_name` stays the effect anchor.
- Offer terms are explicit and machine-readable, but still lightweight and heuristic until later learning phases.

---
*Phase: 15-policy-optimization-layer*
*Completed: 2026-03-16*
