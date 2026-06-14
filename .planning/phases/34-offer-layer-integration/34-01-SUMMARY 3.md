---
phase: 34-offer-layer-integration
plan: 01
subsystem: offer-contract
tags: [offer, schema, runtime, serialization, pytest]
requires: []
provides:
  - canonical nested offer contract
  - semi-typed canonical offer terms
  - backward-compatible runtime bridge
affects: [phase-34, offers, schema, runtime, serialization]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/data/schema.py
    - credit-coach/src/credit_coach/recourse/offer_optimization.py
    - credit-coach/src/credit_coach/recourse/generator.py
    - credit-coach/src/credit_coach/cli/run_recourse.py
    - credit-coach/src/credit_coach/cli/run_batch_recourse_eval.py
    - credit-coach/tests/test_recourse_redesign.py
key-decisions:
  - "Institutional actions remain the semantic owners, while offer truth now lives in a nested canonical offer contract."
  - "Offer terms are semi-typed: stable known fields plus a small extension map."
  - "Action-level offer truth is the only authored source; flat runtime fields are compatibility mirrors."
patterns-established:
  - "Offer identity and terms now serialize from one action-level contract across recourse and batch flows."
duration: manual-execution
completed: 2026-03-22
---

# Phase 34 Plan 01 Summary

**Institutional actions now carry one canonical nested `offer_contract` instead of relying on loose flat offer metadata.**

## Accomplishments

- Added explicit `OfferTerms` and `OfferContract` models to the action schema, including stable offer identity, semi-typed canonical terms, approval state, policy metadata, and a small extension map for specialized fields.
- Hardened `PlanAction` validation so nested offer truth is canonical while legacy flat fields are still backfilled for downstream compatibility.
- Updated offer builders in recourse and batch generation paths so institution-side actions emit the nested contract directly.
- Extended runtime serialization so plan rows and timeline steps carry the nested `offer_contract` without forcing downstream consumers to reconstruct offer identity.
- Added regression coverage for nested-contract construction, flat-field backfill, and runtime serialization continuity.

## Verification

- `python -m pytest tests/test_action_space.py tests/test_recourse_redesign.py -q`

## Notes

- This plan established the contract half of the offer layer; approval, rankability, and product-safe visibility were tightened in later Phase 34 plans.

---
*Phase: 34-offer-layer-integration*
*Completed: 2026-03-22*
