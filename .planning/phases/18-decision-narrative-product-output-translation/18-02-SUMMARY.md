---
phase: 18-decision-narrative-product-output-translation
plan: 02
subsystem: controlled-technical-reveal
tags: [technical-reveal, checkpoints, offers, reasons, confidence]
requires: [18-01]
provides:
  - checkpoint narration with success/failure meaning
  - separate offer narration block
  - coarse confidence labels plus raw confidence trace
  - controlled technical reveal for analysts
affects: [phase-18, roadmap, policy-explanations]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/coaching/messaging.py
    - credit-coach/src/credit_coach/cli/run_recourse.py
    - credit-coach/tests/test_messaging.py
    - credit-coach/tests/test_policy_engine.py
    - credit-coach/tests/test_phase_experiment_suite.py
key-decisions:
  - "Technical detail stays available under `technical_reveal` rather than leaking into the default story."
  - "Offer narration remains separate from ordinary action narration."
  - "Narrative confidence is surfaced as `high | moderate | low` by default while raw score stays available technically."
patterns-established:
  - "The roadmap now supports business-first default rendering plus analyst-depth expansion from the same artifact."
requirements-completed: [PORT-02]
duration: manual-execution
completed: 2026-03-18
---

# Phase 18 Plan 02 Summary

**Phase 18 now has a controlled reveal layer, not just prettier action summaries.**

## Accomplishments
- Completed deterministic checkpoint narration so each review point now explains expected state, success condition, failure implication, and next review action.
- Added separate offer narratives and human-readable principal reason narratives without exposing raw internal codes in default UI paths.
- Wired `technical_reveal` and coarse confidence labels into the same roadmap artifact so analyst depth remains available without polluting the buyer view.

## Verification
- `python -m pytest credit-coach/tests/test_messaging.py credit-coach/tests/test_policy_engine.py credit-coach/tests/test_recourse_redesign.py credit-coach/tests/test_phase_experiment_suite.py`

## Notes
- This layer is intentionally deterministic and vocabulary-controlled so the product speaks in one voice across surfaces.
- Confidence labels are simplified for default rendering, but the raw confidence inputs remain available for technical consumers.

---
*Phase: 18-decision-narrative-product-output-translation*
*Completed: 2026-03-18*
