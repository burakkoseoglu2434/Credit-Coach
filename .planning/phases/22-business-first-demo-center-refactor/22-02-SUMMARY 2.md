---
phase: 22-business-first-demo-center-refactor
plan: 02
subsystem: demo-ui-primitives
tags: [react, ui, hero, metrics, cta]
requires: []
provides:
  - calmer demo surface primitives
  - reusable request-demo CTA block
  - context-labeled product metric treatment
affects: [demo-center, buyer-surfaces, localization]
tech-stack:
  modified:
    - credit-coach-website/client/src/components/MetricTile.tsx
    - credit-coach-website/client/src/components/PageHero.tsx
    - credit-coach-website/client/src/components/DemoSectionCta.tsx
    - credit-coach-website/client/src/index.css
key-decisions:
  - "Trust framing moved into shared primitives instead of being hardcoded inside one page."
  - "Context labels became a reusable metric-card affordance so section-level KPI restraint stays consistent."
patterns-established:
  - "Buyer-facing demo surfaces should reuse PageHero product mode, context-labeled MetricTile cards, and a repeated section CTA."
requirements-completed: [WEB-02]
duration: manual-execution
completed: 2026-03-20
---

# Phase 22 Plan 02 Summary

**The shared Demo Center surface now has calmer hero framing, explicit KPI context labels, and reusable request-demo conversion seams.**

## Accomplishments
- Extended `PageHero` with a restrained product mode and top-of-page disclaimer support.
- Added product-style `MetricTile` treatment with visible context labels for curated, representative, and benchmarked views.
- Introduced a reusable `DemoSectionCta` and supporting surface tokens so repeated CTA blocks feel like product UI instead of landing-page chrome.

## Verification
- `cd credit-coach-website && npm run check`
- `cd credit-coach-website && npm run build`

## Notes
- The CTA primitive was localized end-to-end so the Phase 22 surface remains fully Turkish in `TR` and fully English in `EN`.
- Shared styling was intentionally scoped to the demo surface rather than broadening into a whole-site redesign.

---
*Phase: 22-business-first-demo-center-refactor*
*Completed: 2026-03-20*
