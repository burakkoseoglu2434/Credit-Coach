# Phase 36: Product Surface Upgrade - Research

**Researched:** 2026-03-22
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What must change so the website can render the hardened v2.0 action, numeric, feasibility, execution, offer, and narrative truth as a clearer product surface without inventing new meaning outside the engine-owned contract?

## Planning Basis

Phase 36 now has a locked `36-CONTEXT.md`. For this planning pass the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/22-business-first-demo-center-refactor/22-CONTEXT.md`
- `.planning/phases/30-action-semantics-hardening/30-CONTEXT.md`
- `.planning/phases/31-numeric-target-engine/31-CONTEXT.md`
- `.planning/phases/32-feasibility-constraint-engine/32-CONTEXT.md`
- `.planning/phases/33-action-difficulty-execution-modeling/33-CONTEXT.md`
- `.planning/phases/34-offer-layer-integration/34-CONTEXT.md`
- `.planning/phases/35-narrative-generation-v2/35-CONTEXT.md`
- `.planning/phases/36-product-surface-upgrade/36-CONTEXT.md`
- `credit-coach-website/client/src/pages/DemoCenterPage.tsx`
- `credit-coach-website/client/src/components/RoadmapPhaseCard.tsx`
- `credit-coach-website/shared/demo-schema.ts`
- `credit-coach-website/client/src/lib/demo-formatters.ts`
- `credit-coach-website/server/services/demo-data.ts`
- `credit-coach-website/server/services/live-demo.ts`
- `credit-coach-website/package.json`

This is sufficient because Phase 36 is not designing a new engine contract. The engine already owns:

- semantic actions
- numeric targets
- feasibility truth
- difficulty and follow-through truth
- offer truth
- narrative truth

The open question is whether the website renders that stack with a cleaner hierarchy and stricter UI guardrails.

## Executive Summary

The repository already contains a business-first single-customer experience, but the current Demo Center still behaves like a transitional surface between:

- older phase-first demo composition
- newer engine-owned narrative artifacts

The main gap is no longer missing data. The gap is product-surface discipline.

Today:

- `DemoCenterPage.tsx` already reads `executive_summary`, steps, checkpoints, reasons, and `technical_reveal`
- `singleCustomerDemoSchema` already carries a rich typed mirror for the roadmap artifact
- the live-demo service already returns engine-derived roadmap content

But the current rendering layer still introduces drift:

- `RoadmapPhaseCard.tsx` is phase-first rather than action-first
- it still contains local fallback narrative helpers:
  - `phaseNarrative(...)`
  - `fallbackExpectedOutcome(...)`
  - `fallbackTimingHint(...)`
- the page still makes some local assumptions about offer presence and section behavior
- technical detail and business detail are mixed at the component level instead of cleanly layered

Phase 36 therefore needs to do four things:

1. tighten the typed UI contract around the richer engine narrative
2. recompose the customer surface into an action-first product flow
3. surface offer truth as a supporting institution layer rather than a competing story
4. remove UI-side narrative invention and replace it with strict consumer behavior

## Existing Assets We Can Reuse

### The typed mirror already exists

- `credit-coach-website/shared/demo-schema.ts`
  - already defines:
    - `SingleCustomerDemo`
    - `roadmapPhaseSchema`
    - step narrative
    - checkpoint narrative
    - reason narrative
    - technical reveal
  - is the correct seam for surfacing richer action-card and page-composition inputs without ad hoc page-local types

### The primary page seam already exists

- `credit-coach-website/client/src/pages/DemoCenterPage.tsx`
  - already owns the main product walkthrough
  - already contains executive and section-level hierarchy patterns from Phase 22
  - is the correct seam for:
    - executive summary
    - checkpoint strip placement
    - action flow composition
    - offer panel placement
    - technical reveal placement

### The main drift risk is localized

- `credit-coach-website/client/src/components/RoadmapPhaseCard.tsx`
  - still makes local narrative decisions
  - still synthesizes phase copy and fallback business meaning
  - is the clearest Phase 36 target for strict `no UI-side narrative fallback`

This is good news: Phase 36 does not need a site-wide rewrite. The core cleanup is localized to the single-customer surface and its typed contract.

### Presentation-only helpers already exist

- `credit-coach-website/client/src/lib/demo-formatters.ts`
  - is appropriate for:
    - locale-safe text selection
    - label formatting
    - presentation-only transforms
  - is not appropriate for semantic inference

Phase 36 should preserve that separation.

### Runtime artifact ownership is already solved

- `credit-coach-website/server/services/live-demo.ts`
  - already loads the engine-derived roadmap artifact
- `credit-coach-website/server/services/demo-data.ts`
  - already routes the single-customer surface through the typed payload path

This means Phase 36 can stay consumer-side and should not pull new meaning into the website server.

## What Phase 36 Must Deliver

### 1. A locked action-first surface hierarchy

The single-customer surface must read in this order:

- `executive_summary`
- `action cards`
- `checkpoint strip`
- `offer panel`
- `reasons`
- `technical reveal`

This must feel action-first rather than phase-first, while still preserving lightweight phase grouping.

### 2. A canonical action-card rendering contract

Each visible action card should answer:

- what to do
- what happens
- by when
- how realistic it is

The default visible card content must stay compact:

- `action_summary`
- `expected_outcome`
- `action_timing_hint`
- feasibility label
- difficulty label
- follow-through note

Expanded business-safe detail may show:

- `why_this_matters`
- `what_happens_if_done`
- `what_happens_if_not_done`

### 3. Offer truth that supports the main story

Offer should appear:

- as a short companion signal inside relevant action cards
- as a fuller dedicated panel for offer-bearing plans

The customer path remains primary. Offer remains institution-side support.

### 4. Strict UI guardrails

The website must stop inventing narrative meaning when engine fields are absent.

Locked Phase 36 posture:

- no UI-generated fallback narrative
- no synthetic phase explanations
- no UI-side outcome invention
- only formatting, localization, ordering, and empty-state behavior remain local

If engine truth is missing, UI must fail soft rather than inventing replacement meaning.

## Recommended Plan Split

### Plan 36-01 — Typed surface contract and action-card primitive hardening

Focus on:

- extending the shared demo schema where needed for action-first rendering
- aligning live/static payload consumption with the richer typed surface contract
- removing UI-side fallback narrative generation from the main roadmap-card seam
- establishing a stricter action-card component posture

### Plan 36-02 — Recompose the single-customer page into an action-first product flow

Focus on:

- executive summary first
- checkpoint strip above actions
- action-first card list with lightweight phase grouping
- dedicated offer panel placement
- reasons after the action flow

### Plan 36-03 — Enforce the business-vs-technical UI boundary and close regressions

Focus on:

- end-of-page collapsed technical reveal
- fail-soft handling for missing engine fields
- removal of local semantic inference
- typed artifact consumption integrity across live and static data paths
- final build and surface-level regression closure

## Main Risks

### Risk 1: UI keeps quietly inventing copy

If `RoadmapPhaseCard.tsx` or page-local helpers keep fallback wording, the website will remain a second interpretation engine.

Mitigation:

- remove local fallback narrative helpers
- render only engine-owned fields or neutral empty states

### Risk 2: The surface becomes cleaner but less actionable

If the page reduces clutter without improving hierarchy, the user still will not know what to do first.

Mitigation:

- make action cards the main product object
- keep checkpoint strip near the top
- keep one primary numeric statement per step

### Risk 3: Offer becomes too prominent

If offer gets promoted to a primary story block, the surface will drift away from customer action intelligence into commercial dump behavior.

Mitigation:

- keep offer as companion signal plus dedicated support panel
- preserve customer path as the primary narrative

### Risk 4: Technical reveal bleeds into default business flow

If the technical section is visually mixed into the main flow, trust and readability will drop.

Mitigation:

- keep technical reveal end-of-page and default closed
- ensure business cards only show compact labels and primary statements

## Recommendation

Proceed with Phase 36 now. The engine contracts are already hard enough. The main remaining work is to make the website a stricter, clearer consumer of those contracts so the personalized v2.0 roadmap reads like a real product surface instead of a semi-interpreted demo renderer.
