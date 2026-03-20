---
phase: 30-action-semantics-hardening
plan: 02
subsystem: grouped-semantic-serialization
tags: [grouped-actions, serialization, business-view, technical-view, schema]
requires: [30-01]
provides:
  - deterministic phase-based grouped action identity
  - explicit `business_view` and `technical_view` schema branches
  - product-safe serialized action contract
affects: [phase-30, schema, roadmap, recourse-runtime]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/recourse/action_space.py
    - credit-coach/src/credit_coach/data/schema.py
    - credit-coach/src/credit_coach/recourse/generator.py
    - credit-coach/src/credit_coach/cli/run_recourse.py
    - credit-coach/tests/test_action_space.py
    - credit-coach/tests/test_recourse_redesign.py
key-decisions:
  - "Grouped action identity is deterministic and phase-based: action_key plus phase."
  - "Cross-class grouping is disallowed."
  - "Feature anchors stay technical; business identity stays business-only."
patterns-established:
  - "The engine now serializes action meaning and technical effect as separate first-class branches rather than leaving the split implicit."
requirements-completed: [ACT-01]
duration: manual-execution
completed: 2026-03-20
---

# Phase 30 Plan 02 Summary

**The runtime contract now speaks in grouped semantic actions first and exposes raw effect anchors only in the technical layer.**

## Accomplishments

- Re-keyed grouped action identity around deterministic `action_key + phase` semantics instead of looser month-oriented grouping.
- Added schema-owned `business_view` and `technical_view` models so semantic identity and raw effect traceability are explicitly separated in the engine contract.
- Extended `PlanAction`, generator, and recourse serialization paths to carry `action_family`, deterministic titles and descriptions, and grouped action identity end-to-end.
- Kept low-level effect anchors like `feature_name` in the technical branch while the visible action contract stays aligned to the locked five-field semantic identity.

## Verification

- `python -m pytest credit-coach/tests/test_action_space.py credit-coach/tests/test_recourse_redesign.py -q`

## Notes

- This plan is where Phase 30 stopped being just a catalog cleanup and became an engine-owned product contract.
- Grouped semantics stay traceable because technical detail still exists; it is simply no longer the default recommendation language.

---
*Phase: 30-action-semantics-hardening*
*Completed: 2026-03-20*
