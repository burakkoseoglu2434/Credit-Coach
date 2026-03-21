---
phase: 35-narrative-generation-v2
plan: 02
subsystem: personalization-tone
tags: [narrative, personalization, tone, reasons, pytest]
requires:
  - 35-01
provides:
  - current-state-target-timing personalization
  - calmer and more directive tone discipline
  - short default reason curation
affects: [phase-35, narrative, messaging, product-language]
tech-stack:
  modified:
    - credit-coach/src/credit_coach/coaching/messaging.py
    - credit-coach/tests/test_messaging.py
key-decisions:
  - "Personalization must come from current state, target, and timing rather than persona-style copy."
  - "Tone remains calm, confident, gently directive, and non-judgmental."
  - "Default reasons are capped to the top 2-3 while technical layers retain the fuller reason trace."
patterns-established:
  - "Narrative now feels customer-specific through value and timing truth rather than through extra prose."
duration: manual-execution
completed: 2026-03-22
---

# Phase 35 Plan 02 Summary

**Narrative wording now feels more customer-specific and guidance-oriented without becoming hype, blame, or explicit segment jargon.**

## Accomplishments

- Reworked primary numeric sentences so they reflect current state, target, and timing in a single customer-specific statement.
- Tightened timing hints to use exact due-month windows instead of generic short-horizon phrasing.
- Reframed executive summary headline and supporting line away from “raw engine output” wording and toward a controlled recovery roadmap story.
- Capped default-visible reasons to the top three while preserving the full technical reason trace under reveal surfaces.
- Added regression coverage for current-state numeric phrasing, shorter default reason sets, and tone-safe executive summary wording.

## Verification

- `python -m pytest credit-coach/tests/test_messaging.py credit-coach/tests/test_recourse_redesign.py -q`

## Notes

- This plan tightened personalization and tone on top of the structured contract from Plan 01; the final business-vs-technical split was closed in Plan 03.

---
*Phase: 35-narrative-generation-v2*
*Completed: 2026-03-22*
