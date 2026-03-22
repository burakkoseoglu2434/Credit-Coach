---
phase: 36-product-surface-upgrade
plan: 02
subsystem: customer-surface-hierarchy
tags: [website, demo-center, action-cards, checkpoints, offers]
requires:
  - 36-01
provides:
  - action-first customer flow
  - 4w-dominant checkpoint strip
  - supporting offer and reasons placement
affects: [phase-36, demo-center, customer-surface]
tech-stack:
  modified:
    - credit-coach-website/client/src/pages/DemoCenterPage.tsx
    - credit-coach-website/client/src/components/RoadmapPhaseCard.tsx
key-decisions:
  - "The customer surface now reads as executive summary, checkpoint strip, action cards, offer panel, and reasons."
  - "Action cards are the primary unit of meaning; phase remains only a lightweight grouping cue."
  - "Offer support appears as a short companion signal in cards and a dedicated secondary panel only when present."
patterns-established:
  - "The 4-week checkpoint is visually dominant while 12-week and 24-week checkpoints remain supporting context."
duration: manual-execution
completed: 2026-03-22
---

# Phase 36 Plan 02 Summary

**The single-customer page now behaves like a product workflow instead of a phase-led demo stack.**

## Accomplishments

- Added executive narrative cards so the top of the customer section opens with decision-ready product reading instead of raw roadmap structure.
- Inserted a compact checkpoint strip directly above the action flow and made the `4w` checkpoint visually dominant.
- Reframed roadmap rendering around action cards that answer what to do, what outcome is targeted, when it matters, and how realistic it is.
- Moved offer and reasons into supporting positions after the action flow so they explain the plan without overtaking it.

## Verification

- `cd credit-coach-website && npm run check`
- `cd credit-coach-website && npm run build`

## Notes

- This plan locked the visible product hierarchy; the final business-vs-technical boundary and single analyst reveal were closed in `36-03`.

---
*Phase: 36-product-surface-upgrade*
*Completed: 2026-03-22*
