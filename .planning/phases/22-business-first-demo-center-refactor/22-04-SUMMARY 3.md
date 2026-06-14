---
phase: 22-business-first-demo-center-refactor
plan: 04
subsystem: roadmap-surface
tags: [react, roadmap, localization, demo, narrative]
requires:
  - phase: 22-business-first-demo-center-refactor
    provides: executive-first demo center surface
provides:
  - phase-window roadmap language
  - business-first roadmap narrative cards
  - roadmap technical reveal with raw action diagnostics
affects: [single-customer-roadmap, localization, technical-traceability]
tech-stack:
  modified:
    - credit-coach-website/client/src/components/RoadmapPhaseCard.tsx
    - credit-coach-website/client/src/lib/demo-formatters.ts
key-decisions:
  - "Month counters were removed from the buyer-facing roadmap path in favor of first-4-weeks and week-window language."
  - "Raw action keys, cost, execution probability, and target PD stay available only inside the technical reveal."
patterns-established:
  - "Roadmap cards should communicate phase intent and expected business outcome before exposing engine detail."
requirements-completed: [WEB-02]
duration: manual-execution
completed: 2026-03-20
---

# Phase 22 Plan 04 Summary

**The single-customer roadmap now reads like a governed recovery workflow built around phase windows instead of month counters and raw diagnostics.**

## Accomplishments
- Centralized the new phase-window vocabulary in `demo-formatters.ts`.
- Rewrote roadmap cards to lead with phase summary, why-it-matters context, and business-safe step outcomes.
- Moved target PD, execution probability, cost, raw class, and action keys into one technical reveal per phase card.

## Verification
- `cd credit-coach-website && npm run check`
- `cd credit-coach-website && npm run build`

## Notes
- The buyer-facing roadmap path now uses `First 4 weeks`, `Weeks 4-12`, and `Weeks 12-24`, with fully aligned Turkish equivalents.
- Typed artifact consumption stayed unchanged; only language, hierarchy, and visibility shifted.

---
*Phase: 22-business-first-demo-center-refactor*
*Completed: 2026-03-20*
