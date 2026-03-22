---
phase: 36-product-surface-upgrade
plan: 01
subsystem: typed-surface-contract
tags: [website, schema, live-demo, contract, typescript]
requires: []
provides:
  - strict website typed mirror for v2.0 roadmap truth
  - aligned live and static single-customer payload routing
  - no-fallback action-card seam
affects: [phase-36, website, surface-contract, live-demo]
tech-stack:
  modified:
    - credit-coach-website/shared/demo-schema.ts
    - credit-coach-website/server/services/demo-data.ts
    - credit-coach-website/server/services/live-demo.ts
    - credit-coach-website/client/src/components/RoadmapPhaseCard.tsx
key-decisions:
  - "The website mirror now includes action-level business and technical views, primary numeric targets, offer contracts, and richer narrative cues."
  - "Static and live single-customer payloads are validated against the same typed contract."
  - "Roadmap cards no longer synthesize fallback outcomes or timing narratives."
patterns-established:
  - "UI consumers fail soft when engine fields are missing instead of inventing substitute meaning."
requirements-completed: [SURF-01]
duration: manual-execution
completed: 2026-03-22
---

# Phase 36 Plan 01 Summary

**The product surface contract now matches the richer v2.0 roadmap truth instead of relying on page-local inference.**

## Accomplishments

- Extended the shared demo schema to cover action-group identifiers, business and technical views, primary numeric targets, nested offer contracts, richer step narrative cues, executive follow-through readiness, and technical reveal payloads.
- Forced both static and live single-customer demo paths through the same typed schema validation.
- Hardened the live-demo normalizer so optional nested roadmap fields are shaped into schema-safe typed objects before they reach the UI.
- Rebuilt the roadmap phase card seam around engine-owned action summaries and neutral missing-state behavior, removing local narrative fallback helpers entirely.

## Verification

- `cd credit-coach-website && npm run check`
- `rg -n "phaseNarrative|fallbackExpectedOutcome|fallbackTimingHint" credit-coach-website/client/src/components/RoadmapPhaseCard.tsx`

## Notes

- This plan established the strict typed boundary; the action-first page hierarchy and end-of-page technical reveal were completed in later Phase 36 plans.

---
*Phase: 36-product-surface-upgrade*
*Completed: 2026-03-22*
