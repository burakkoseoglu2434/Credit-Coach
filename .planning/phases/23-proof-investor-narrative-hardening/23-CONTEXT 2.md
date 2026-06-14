# Phase 23: Proof & Investor Narrative Hardening - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Reframe the Proof and Investor surfaces so they read in executive business language instead of internal artifact language. This phase hardens narrative order, vocabulary, trust framing, and commercial story across the buyer-facing proof and investor pages. It does not change engine math, proof computation, roadmap logic, pricing mechanics, or add new website capabilities beyond the scoped proof and investor storytelling work.

</domain>

<decisions>
## Implementation Decisions

### Carry-Forward Decisions From Phases 18, 21, And 22
- Engine artifacts remain the source of truth.
- Website pages stay renderers of curated artifacts, not alternate interpreters.
- Default reading order must be business-first, with technical or diagnostic detail behind explicit reveal controls.
- Visible KPI context must stay explicit through business-safe labels such as curated snapshot, representative simulation, or offline benchmark.
- Locale purity is mandatory:
  - TR mode must be fully Turkish
  - EN mode must be fully English
- Phase 23 should preserve the calmer, executive-first product surface established in Phase 22 rather than reverting to a dashboard or proof-board style.

### Proof Page Headline Hierarchy
- The first-screen business question is:
  - "Bu sistem gercekten portfoyumde ise yarar mi?"
  - "Will this system actually work on my portfolio?"
- The top verdict should read as a buyer-confidence statement, not a technical evidence bundle.
- The headline answer should still use the proof verdict family:
  - `working`
  - `promising`
  - `mixed`
  - `not_proven`
- That verdict should be paired with one short sentence that feels like a business decision read, not an internal review artifact.
- Supporting evidence should come below the verdict, not compete with it on first read.
- The overall first-screen feel should be:
  - executive memo
  - fast to read
  - decision-led
  - "okudum -> anladim -> guveniyorum / guvenmiyorum"

### Baseline Comparison And Vocabulary Guardrails
- `Phase 17` must not appear in buyer-facing UI copy.
- Internal baseline references may remain in data and code, but UI language should translate them into business-safe phrasing such as:
  - `baseline portfolio snapshot`
  - `previous benchmark`
- Default copy must remove internal-seeming artifact terms such as:
  - `product-ready coverage`
  - `execution-aware value`
  - `governance-safe`
  - `release controls`
  - `proof artifact`
  when shown to the buyer in the first read.
- If these ideas remain important, they should be translated into business vocabulary rather than deleted.

### Governance And Release-Control Framing
- Governance or release discipline should not be a full narrative block near the top of the Proof page.
- Instead, it should appear as a compact trust rail directly under the main verdict.
- The trust rail should feel like:
  - 2-3 short lines or badges
  - immediately visible
  - confidence-building
  - not flow-breaking
- The buyer takeaway for this rail should be:
  - `safe to pilot`
- Default wording should collapse fairness, reliability, and telemetry into one business phrase:
  - `institution-ready safeguards`
- Detailed fairness, reliability, and telemetry language should move under expand or technical detail.
- Preferred business-facing vocabulary is:
  - `controlled rollout`
  - `institution-ready safeguards`
- Internal terms such as `governance-safe` should be removed from default UI language.

### Investor Narrative Arc
- The first takeaway on the Investor page should be:
  - clear wedge
- The first question the page should answer is:
  - what this solves differently
- Category-creation language is allowed, but only as a second-layer message rather than the lead.
- The required investor story order is:
  - market pain
  - product wedge
  - proof it works
  - monetization
- The overall tone should be:
  - disciplined product brief
  - low hype
  - clear, controlled, and specific
- The Investor page should not reuse Proof-page verdict language verbatim.
- Instead, it should translate proof into the broader company-level question:
  - Proof page = "does it work?"
  - Investor page = "why can this become a company?"

### Commercial Positioning And Specificity
- Default monetization framing should remain:
  - `pilot -> platform`
- Pricing model detail such as annual pricing or expansion pricing should not be explicit in the default read.
- Pricing mechanics may be implied in lower-detail sections, but should not dominate the headline story.
- Product positioning should be:
  - `decision intelligence infrastructure`
- The narrative should not trap the company in language that sounds too narrow such as only:
  - recovery software
  - post-decline workflow tool
- Category claim strength should be medium:
  - not in the page headline
  - allowed inside section-level copy as `new layer`, `new approach`, or equivalent
- Expansion logic should prioritize:
  - first depth inside the same institution across more teams
  - then breadth into more use cases

### Claude's Discretion
- Exact buyer-facing verdict one-liners beneath `working / promising / mixed / not_proven`
- Exact compact-trust-rail layout as long as it stays immediately under the verdict and does not become a full section
- Exact baseline-translation wording between `baseline portfolio snapshot` and `previous benchmark`
- Exact section titles and card labels for the investor story as long as the required order remains:
  - market pain
  - product wedge
  - proof it works
  - monetization
- Exact phrasing for category language as long as it stays medium-strength and off the main headline

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- [ProofPage.tsx](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/client/src/pages/ProofPage.tsx)
  - already consumes the curated `product-confidence-snapshot`
  - already contains verdict, confidence, supporting metrics, and baseline comparison seams
  - currently needs narrative reordering and vocabulary translation more than new data plumbing
- [InvestorPage.tsx](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/client/src/pages/InvestorPage.tsx)
  - already has the raw building blocks for wedge, why-now, monetization, and productization story
  - currently reads as a loose section stack rather than one disciplined narrative arc
- [site-content.ts](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/client/src/data/site-content.ts)
  - already contains shared `investorNarrative`, `proofPillars`, and `investorHighlights`
  - is the likely seam for aligning proof and investor vocabulary without hardcoding every phrase directly into page components
- [PageHero.tsx](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/client/src/components/PageHero.tsx)
  - already supports the calmer product-mode hero established in Phase 22
- [MetricTile.tsx](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/client/src/components/MetricTile.tsx)
  - already supports the reduced-density, context-labeled product metric pattern
- [DemoSectionCta.tsx](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/client/src/components/DemoSectionCta.tsx)
  - can be reused if Phase 23 wants consistent buyer conversion seams across proof and investor surfaces
- [shared/demo-schema.ts](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/shared/demo-schema.ts)
  - already contains the typed `productConfidenceSnapshotSchema`
  - supports translated proof rendering without inventing new frontend-only contracts

### Established Patterns
- Executive-first page composition now exists in Demo Center and should be mirrored where appropriate.
- Technical truth should move behind reveals, not disappear.
- Shared product-surface components should be preferred over page-local visual hacks.
- Visible metrics should carry context labels instead of implicit provenance.
- Buyer-facing copy should answer business questions first and surface evidence only after the decision frame is clear.

### Integration Points
- Primary Phase 23 implementation surfaces:
  - `credit-coach-website/client/src/pages/ProofPage.tsx`
  - `credit-coach-website/client/src/pages/InvestorPage.tsx`
- Shared vocabulary and story helpers likely live in:
  - `credit-coach-website/client/src/data/site-content.ts`
- Shared presentation seams likely remain:
  - `credit-coach-website/client/src/components/PageHero.tsx`
  - `credit-coach-website/client/src/components/MetricTile.tsx`
  - `credit-coach-website/client/src/components/SectionHeading.tsx`
  - `credit-coach-website/client/src/components/DemoSectionCta.tsx`
- Proof page data should continue to come from:
  - `credit-coach-website/server/services/demo-data.ts`
  - `credit-coach-website/shared/demo-schema.ts`
- If shared proof or investor copy also affects other pages through `site-content.ts`, planning should account for those downstream consumers and keep vocabulary consistent.

</code_context>

<specifics>
## Specific Ideas

- Proof page should feel like an executive memo that quickly answers:
  - "Bu sistem gercekten portfoyumde ise yarar mi?"
- Proof page top structure should likely read:
  - buyer-confidence verdict
  - short business explanation
  - compact trust rail showing `safe to pilot`
  - then deeper evidence and baseline comparison
- Baseline comparison should remain visible, but in translated language:
  - `baseline portfolio snapshot`
  - `previous benchmark`
- Investor page should not mirror Proof page structure directly.
- Investor page should translate proof into company-building logic:
  - market pain
  - product wedge
  - proof it works
  - monetization
- Category ambition should be real but controlled:
  - not headline-level category-creation hype
  - yes to section-level `new layer / new approach` framing
- Commercial story should imply a serious software business without spelling out pricing mechanics in headline copy.

</specifics>

<deferred>
## Deferred Ideas

- Explicit pricing-model detail such as annual contract structure or expansion pricing remains outside the default narrative and can be handled later if a dedicated commercial-packaging phase is opened.
- Any broader website-wide rewrite beyond Proof and Investor surfaces remains outside this phase.

</deferred>

---
*Phase: 23-proof-investor-narrative-hardening*
*Context gathered: 2026-03-20*
