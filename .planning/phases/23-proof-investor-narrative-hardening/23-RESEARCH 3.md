# Phase 23: Proof & Investor Narrative Hardening - Research

**Researched:** 2026-03-20
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What must change so the Proof and Investor pages stop reading like stitched-together internal product artifacts and instead read like executive business surfaces for institutional buyers and investors?

## Planning Basis

Phase 23 now has a locked `23-CONTEXT.md`. For this planning pass, the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/phases/18-decision-narrative-product-output-translation/18-CONTEXT.md`
- `.planning/phases/21-portfolio-proof-product-confidence/21-CONTEXT.md`
- `.planning/phases/22-business-first-demo-center-refactor/22-CONTEXT.md`
- `.planning/phases/23-proof-investor-narrative-hardening/23-CONTEXT.md`
- `credit-coach-website/client/src/pages/ProofPage.tsx`
- `credit-coach-website/client/src/pages/InvestorPage.tsx`
- `credit-coach-website/client/src/data/site-content.ts`
- `credit-coach-website/client/src/components/PageHero.tsx`
- `credit-coach-website/client/src/components/MetricTile.tsx`
- `credit-coach-website/client/src/components/DemoSectionCta.tsx`
- `credit-coach-website/shared/demo-schema.ts`
- `credit-coach-website/server/services/demo-data.ts`

This is sufficient because the engine-side proof contract already exists. Phase 23 does not need new proof math or a new artifact schema. It needs page hierarchy, vocabulary, trust framing, and investor story order to be rewritten so the same typed truth reads clearly to buyers and investors.

## Executive Summary

The repository already has the core ingredients Phase 23 needs:

- a curated `product-confidence-snapshot` typed contract
- a functioning Proof page seam
- a functioning Investor page seam
- shared product-surface components from Phase 22
- a content registry in `site-content.ts`

The remaining gap is not missing data. It is how the pages speak.

Today the main issues are:

- `ProofPage.tsx` still leads with internal proof language such as `Phase 17`, `product-ready coverage`, `governance-safe`, and `proof artifact`
- the Proof page reads metric-first rather than decision-first
- governance and rollout language is present, but not yet shaped into the compact `safe to pilot` trust rail the user wants
- `InvestorPage.tsx` has the right building blocks, but not one disciplined story arc
- proof and investor copy are not yet aligned to one shared business-safe vocabulary

Phase 23 should therefore stay presentation-focused and split into three clear planning tracks:

1. define one bilingual proof/investor vocabulary seam
2. rewrite the Proof page into an executive memo
3. rewrite the Investor page into a disciplined product brief

## Existing Assets We Can Reuse

### The proof contract already exists

- `credit-coach-website/shared/demo-schema.ts`
  - already defines `ProductConfidenceSnapshot`
- `credit-coach-website/server/services/demo-data.ts`
  - already serves `product-confidence-snapshot`
- `credit-coach-website/client/src/pages/ProofPage.tsx`
  - already consumes the proof snapshot

This means Phase 23 should not reopen:

- proof computation
- baseline comparison logic
- verdict derivation
- artifact sync

It should instead translate and reorder the existing proof story.

### Shared product-surface components are already strong enough

- `PageHero.tsx`
  - already supports the calmer product-mode visual treatment established in Phase 22
- `MetricTile.tsx`
  - already supports context labels and lower-density product presentation
- `DemoSectionCta.tsx`
  - can be reused if either page needs a consistent conversion seam

Phase 23 can therefore stay mostly inside the page and content layers rather than opening another component-foundation phase.

### The main content seam already exists

- `credit-coach-website/client/src/data/site-content.ts`
  - already contains:
    - `proofPillars`
    - `investorNarrative`
    - `investorHighlights`

This is the right place to centralize:

- shared business-safe terminology
- buyer-safe baseline wording
- trust-rail copy
- investor story helpers

without duplicating strings across multiple pages.

### Phase 22 already established the target presentation posture

The Phase 22 Demo Center refactor already locked:

- executive-first reading hierarchy
- controlled technical detail
- explicit KPI context labels
- restrained product UI instead of glowing dashboard styling

Phase 23 should extend that same posture to Proof and Investor rather than inventing a new visual language.

## What Phase 23 Must Deliver

### 1. One shared bilingual vocabulary for proof and investor surfaces

The current copy still leaks internal terms into buyer-facing UI. Phase 23 must centralize and reuse business-safe alternatives such as:

- `baseline portfolio snapshot`
- `previous benchmark`
- `controlled rollout`
- `institution-ready safeguards`
- `decision intelligence infrastructure`

This shared seam matters because Proof and Investor should feel aligned, even though they answer different top-level questions.

### 2. A Proof page that answers the buyer question first

The locked first-screen question is:

- `Bu sistem gercekten portfoyumde ise yarar mi?`
- `Will this system actually work on my portfolio?`

That means the Proof page should lead with:

- buyer-confidence verdict
- one short decision-oriented sentence
- a compact trust rail with `safe to pilot`
- deeper evidence only after the verdict is clear

The current page already has the right data, but the order and wording are still wrong.

### 3. A compact trust rail instead of a full governance block

The user explicitly does not want governance to become a large narrative interruption.

The correct posture is:

- compact rail under the verdict
- 2-3 short lines or badges
- `safe to pilot`
- `controlled rollout`
- `institution-ready safeguards`

Detailed fairness, reliability, and telemetry language should move below the fold or behind detail reveals.

### 4. An Investor page with a disciplined narrative arc

The user locked the required order:

- market pain
- product wedge
- proof it works
- monetization

The Investor page must therefore stop feeling like a set of adjacent sections and start feeling like one argument.

The page should not simply restate Proof-page verdicts. It should translate proof into the larger company story:

- Proof page = does it work?
- Investor page = why can this become a company?

### 5. Commercial positioning that stays broad but controlled

The commercial story should remain:

- `pilot -> platform`

but avoid:

- explicit pricing mechanics in the default read
- overly narrow labels such as only `recovery software`

The target positioning is:

- `decision intelligence infrastructure`

with category claim strength kept medium and off the main headline.

## Recommended Plan Split

### Plan 23-01 — Shared proof and investor vocabulary

Focus on:

- centralizing shared bilingual business-safe copy in `site-content.ts`
- introducing translated baseline language and trust-rail phrasing
- aligning proof and investor terminology without forcing them into the same page structure

This is a wave-1 dependency because both page rewrites should consume one shared vocabulary seam.

### Plan 23-02 — Proof page executive memo refactor

Focus on:

- turning the opening of `ProofPage.tsx` into a decision-led executive memo
- moving governance/release framing into a compact trust rail
- translating baseline comparison and deeper evidence into buyer-safe language
- keeping technical detail available only in lower-detail or reveal paths

### Plan 23-03 — Investor page disciplined brief refactor

Focus on:

- restructuring `InvestorPage.tsx` into:
  - market pain
  - product wedge
  - proof it works
  - monetization
- translating proof into a company-building narrative
- locking the commercial positioning to `decision intelligence infrastructure`
- keeping pricing mechanics implied rather than explicit

## Main Risks

### Risk 1: Proof page stays too close to the internal artifact contract

If the rewrite only changes labels and not hierarchy, the page will still read like an internal proof sheet rather than an executive memo.

Mitigation:

- rewrite the opening section around the buyer question
- force verdict first and evidence second
- make the trust rail visually immediate

### Risk 2: Investor page becomes a hype page

If the investor rewrite overcompensates, it can drift into pitch-deck language that no longer feels trustworthy or product-grounded.

Mitigation:

- keep the tone as a disciplined product brief
- translate proof, do not inflate it
- keep category language section-level rather than headline-level

### Risk 3: Proof and Investor drift into different vocabularies

If copy is rewritten page-by-page without a shared seam, the site will sound inconsistent and reintroduce mixed terminology.

Mitigation:

- centralize shared wording in `site-content.ts`
- make page rewrites consume the same vocabulary base

## Validation Architecture

Phase 23 can rely on the existing website verification stack:

- `cd credit-coach-website && npm run check`
- `cd credit-coach-website && npm run build`

Because the work is page- and copy-centric, validation should add string-level structural checks alongside type and build checks. The most important automated guardrails are:

- required business-safe terms appear where expected
- banned internal language no longer appears in buyer-facing page copy
- Proof and Investor pages still build as consumers of the typed artifact contract

Manual review should confirm:

- Proof reads like an executive memo
- the trust rail is compact and visible
- Investor follows the locked market-pain-to-monetization arc
- category ambition stays medium-strength rather than headline hype

## Recommended Execution Posture

This phase should execute in two waves:

- wave 1: shared vocabulary and content seam
- wave 2: Proof and Investor page rewrites in parallel

That split keeps the language contract centralized and makes it easier to verify both pages against the same narrative rules.

---
*Phase: 23-proof-investor-narrative-hardening*
*Research completed: 2026-03-20*
