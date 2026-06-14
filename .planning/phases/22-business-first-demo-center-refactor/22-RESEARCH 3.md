# Phase 22: Business-First Demo Center Refactor - Research

**Researched:** 2026-03-20
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What has to change so the Demo Center stops reading like a dense engine-output showcase and starts reading like a trustworthy enterprise product experience for institutional buyers, while also repairing the missing Phase 21 traceability evidence for `WEB-01`?

## Planning Basis

Phase 22 now has a locked `22-CONTEXT.md`. For this planning pass, the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/v1.3-MILESTONE-AUDIT.md`
- `.planning/phases/22-business-first-demo-center-refactor/22-CONTEXT.md`
- `.planning/phases/21-portfolio-proof-product-confidence/21-01-SUMMARY.md`
- `.planning/phases/21-portfolio-proof-product-confidence/21-02-SUMMARY.md`
- `.planning/phases/21-portfolio-proof-product-confidence/21-03-SUMMARY.md`
- `credit-coach-website/client/src/pages/DemoCenterPage.tsx`
- `credit-coach-website/client/src/components/RoadmapPhaseCard.tsx`
- `credit-coach-website/client/src/components/MetricTile.tsx`
- `credit-coach-website/client/src/components/PageHero.tsx`
- `credit-coach-website/client/src/components/SectionHeading.tsx`
- `credit-coach-website/client/src/lib/demo-formatters.ts`
- `credit-coach-website/client/src/index.css`
- `credit-coach-website/server/services/demo-data.ts`
- `credit-coach-website/server/services/live-demo.ts`
- `credit-coach-website/shared/demo-schema.ts`

This is sufficient because the engine-side narrative contract already exists. Phase 22 does not need a new recommendation or narrative model. It needs to repair audit traceability for the curated snapshot chain and redesign the website rendering layer so business meaning appears first, technical depth appears on demand, and the page stops feeling like a dashboard proof dump.

## Executive Summary

The current repository already has the raw ingredients for a business-first demo, but the composition is wrong:

- Phase 18 gave the single-customer artifact an executive summary, step narratives, checkpoint narratives, and a `technical_reveal`
- the Demo Center already has separate customer, portfolio, offer, and learning sections
- context pills already exist on `MetricTile`
- the roadmap already knows about `0-4`, `4-12`, and `12-24` week windows

What still makes the page feel like “engine output” is the presentation layer:

- too many visible metrics at once
- too many low-level labels in the default view
- month-based roadmap guidance still appears in the customer flow
- section entry copy does not consistently bridge from customer story to portfolio, offer, and learning meaning
- visual treatment still leans toward glowing demo-dashboard aesthetics
- the audit-safe summary evidence for Phase 21 is still incomplete

Phase 22 should therefore stay narrow and deliberate:

1. repair `WEB-01` traceability by fixing the Phase 21 summary metadata
2. keep the existing typed demo contract as the source of truth
3. redesign the Demo Center around a three-level reading hierarchy
4. reduce visible KPIs to executive-safe density
5. move raw technical data behind explicit reveals
6. align roadmap language to `first 4 weeks`, `weeks 4-12`, and `weeks 12-24`
7. simplify the visual system enough that the page reads like a real product

## Existing Assets We Can Reuse

### Engine-owned narrative truth already exists

- `credit-coach-website/shared/demo-schema.ts`
  - the single-customer contract already includes:
    - `executive_summary`
    - step narratives
    - checkpoint narratives
    - `technical_reveal`
- `credit-coach-website/server/services/live-demo.ts`
  - already returns a typed `SingleCustomerDemo`

This means Phase 22 should not reopen engine-owned narrative generation unless a tiny schema extension is unavoidable. The website can already render a business-first story from current artifact truth.

### The Demo Center already contains the right top-level sections

- `credit-coach-website/client/src/pages/DemoCenterPage.tsx`
  - already divides the experience into:
    - single customer
    - portfolio impact
    - offer optimization
    - learning loop

The phase does not need a new information architecture from scratch. It needs a hierarchy rewrite inside the existing sections.

### Existing product components already support the basic trust cues

- `MetricTile.tsx` already supports a visible context label
- `PageHero.tsx` already supports supporting-note and badge patterns
- `details` / `summary` is already used for technical reveal in the page and roadmap card

Phase 22 can reuse these patterns, but should tighten them and make them consistent across the whole demo.

### The current week-window vocabulary already exists in one seam

- `credit-coach-website/client/src/lib/demo-formatters.ts`
  - `formatPhaseTitle(...)` already speaks in the “first 4 weeks” style
  - `formatWindowLabel(...)` already maps canonical week windows

The lingering month-based language is concentrated in `RoadmapPhaseCard.tsx`, not across the whole codebase.

### The audit gap is localized and repairable

- `.planning/v1.3-MILESTONE-AUDIT.md` says `WEB-01` is partial because the Phase 21 summary files are missing YAML frontmatter and `requirements-completed`
- the missing evidence is localized to:
  - `21-01-SUMMARY.md`
  - `21-02-SUMMARY.md`
  - `21-03-SUMMARY.md`

This is a narrow repair and should be treated as part of Phase 22 rather than a reason to reopen Phase 21 implementation.

## What Phase 22 Must Deliver

### 1. Audit-safe curated snapshot traceability

Phase 22 must repair the summary metadata for Phase 21 so the milestone audit can verify the curated demo/proof snapshot chain without hand-waving.

Locked posture:

- add valid YAML frontmatter
- add `requirements-completed`
- record only what Phase 21 truly closed
- do not retroactively claim `WEB-03`

### 2. A true three-level reading hierarchy

The Demo Center should render in three levels:

- executive view by default
- section view for customer, portfolio, offer, and learning
- technical detail collapsed under explicit reveal controls

The current page has fragments of this pattern, but not a consistent hierarchy.

### 3. Business narrative first for the single-customer flow

The customer section should lead with:

- status
- expected outcome
- risk trend

It should not lead with:

- PD deltas
- raw phase mechanics
- execution probability jargon

Those signals remain valid, but they belong in technical reveal, not in the first read.

### 4. Executive-safe KPI density

Each major section should show no more than 2-3 headline KPIs in the default view, with all others behind detail toggles or secondary surfaces.

This is especially important in:

- portfolio impact
- offer optimization
- learning

because these are currently the highest-density sections in the page.

### 5. Phase-window language instead of month language

`RoadmapPhaseCard.tsx` still contains:

- month numbers
- “month-by-month plan”
- per-step month guidance

Phase 22 must reframe this into:

- first 4 weeks
- weeks 4-12
- weeks 12-24

without losing useful sequencing meaning.

### 6. Strong trust framing and restrained visual treatment

The Demo Center needs:

- top-of-page disclaimer:
  - `Representative product preview — not real customer data`
- visible context labels on every visible KPI
- section-ending CTA blocks
- lighter glow, lighter density, more product-like composition

The page should still feel premium, but not theatrical.

## Recommended Plan Split

The roadmap’s Phase 22 scope is best executed as four plans in two waves.

### Plan 22-01 — Repair Phase 21 summary traceability

Focus on:

- adding summary frontmatter
- adding `requirements-completed`
- keeping the closure story accurate to what Phase 21 actually shipped

This closes the audit’s narrow `WEB-01` evidence gap without reopening product code.

### Plan 22-02 — Build shared Demo Center presentation primitives

Focus on:

- disclaimer and CTA block patterns
- lighter card and hero treatment
- consistent context-label and reveal affordances

This creates the reusable surface language before the main page rewrite.

### Plan 22-03 — Rebuild DemoCenterPage around executive and section hierarchy

Focus on:

- executive-first opening
- section bridges
- one-line summaries
- why-it-matters framing
- KPI reduction
- technical detail collapsed by default

This is the phase’s main business-first product rewrite.

### Plan 22-04 — Replace month guidance with phase-window roadmap language

Focus on:

- `RoadmapPhaseCard.tsx`
- week-window helper text
- business-first roadmap labels
- technical detail relegated to collapsible sections

This removes one of the strongest remaining “engine demo” signals from the page.

## Main Risks

### Risk 1: The website starts inventing business meaning again

If Phase 22 solves density by adding page-local interpretation logic that drifts from the artifact, the business-first surface will become fragile.

Mitigation:

- keep existing typed contract authoritative
- prefer composition changes over new inference logic

### Risk 2: The redesign balloons into a whole-site visual rewrite

The user asked for Demo Center refactoring, not a global brand restart.

Mitigation:

- keep shared-style changes narrow and demo-surface-oriented
- avoid broad changes to unrelated pages

### Risk 3: Technical truth is either still too visible or disappears completely

If technical details stay in the default path, the page remains too dense. If they disappear, trust drops.

Mitigation:

- use explicit reveal controls
- move, do not delete, technical detail

### Risk 4: Language consistency regresses across TR and EN

The current site relies on localized strings mixed with fallback formatters. That can easily create partial English or Turkish leakage.

Mitigation:

- keep all new buyer-facing copy in explicit TR/EN pairs
- avoid string concatenation where possible

## Validation Architecture

Phase 22 can rely on existing website validation infrastructure plus one lightweight audit check:

### Automated checks

- `cd credit-coach-website && npm run check`
  - validates TypeScript integrity across page, component, and shared-schema changes
- `cd credit-coach-website && npm run build`
  - validates final renderability and server/client integration
- `rg -n "^(---|phase:|plan:|requirements-completed:)" .planning/phases/21-portfolio-proof-product-confidence/21-0[123]-SUMMARY.md`
  - validates the Phase 21 summary metadata repair exists

### Manual review requirements

One human visual review is still required after execution:

- confirm the disclaimer is visible at the top of the page
- confirm the default read contains no PD/probability/phase jargon as headline language
- confirm each major section begins with:
  - bridge
  - summary
  - why this matters
- confirm each major section ends with a strong CTA
- confirm visible KPI count stays capped at 2-3 per section
- confirm every visible KPI carries a context label
- confirm technical details are collapsed by default
- confirm month language is gone from the roadmap flow
- confirm EN mode is fully English and TR mode is fully Turkish
- confirm the page feels like a product workflow rather than a glowing dashboard

That combination is enough for a planning pass because the phase is largely presentation and hierarchy work over an existing typed contract.
