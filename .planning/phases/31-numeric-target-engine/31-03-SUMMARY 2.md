---
phase: 31-numeric-target-engine
plan: 03
subsystem: runtime-and-messaging-consumer-alignment
tags: [numeric-targets, messaging, runtime, serialization, pytest]
requires: []
provides:
  - runtime serialization of primary numeric targets
  - business-readable target phrasing in engine messaging
  - grouped-step preference for primary numeric targets
affects: [phase-31, run-recourse, messaging, roadmap, runtime-artifacts]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/cli/run_recourse.py
    - credit-coach/src/credit_coach/coaching/messaging.py
    - credit-coach/tests/test_messaging.py
    - credit-coach/tests/test_recourse_redesign.py
key-decisions:
  - "Runtime consumers must read the engine-owned numeric target contract rather than infer meaning from raw feature deltas."
  - "Business-readable numeric phrasing is absolute target plus signed delta."
  - "Grouped mixed-unit actions prefer the representative step that carries the primary numeric target."
patterns-established:
  - "Downstream product language now consumes one stable primary target seam while keeping secondary numeric detail technical-only."
requirements-completed: [NUM-01]
duration: manual-execution
completed: 2026-03-21
---

# Phase 31 Plan 03 Summary

**Runtime and messaging consumers now speak the same numeric target contract the generator emits.**

## Accomplishments

- Serialized primary numeric targets directly into roadmap and runtime timeline artifacts, including metric key, unit, signed delta, due month, and generation notes.
- Updated engine messaging to prefer primary numeric targets for readable target phrasing while keeping raw feature deltas and mixed-unit secondary effects inside technical branches.
- Fixed grouped-action narrative selection so repeated composite steps use the representative step that actually carries the primary numeric target.
- Expanded regression coverage to protect roadmap serialization, timeline serialization, target-aware messaging, and grouped-step behavior.

## Verification

- `python -m pytest credit-coach/tests/test_recourse_redesign.py credit-coach/tests/test_messaging.py -q`
- `python -m pytest credit-coach/tests/test_messaging.py credit-coach/tests/test_recourse_feasibility.py -q`

## Notes

- Phase 31 remains feasibility-neutral after consumer alignment; runtime and messaging consume targets but do not introduce validity language.
- This closes `NUM-01` because the contract is now emitted, serialized, and consumed end-to-end by engine-owned layers.

---
*Phase: 31-numeric-target-engine*
*Completed: 2026-03-21*
