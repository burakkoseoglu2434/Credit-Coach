# Phase 22: Business-First Demo Center Refactor - Context

**Created:** 2026-03-20
**Status:** Pending planning
**Source:** v1.3 milestone audit gap closure
**Closes:** WEB-01, WEB-02

## Intent

Repair the partial `WEB-01` traceability chain and refactor the demo experience into a business-first product surface for institutional buyers.

## Known Inputs

- Audit gap: Phase 21 summary files are missing YAML frontmatter and `requirements-completed`, so the curated snapshot chain does not fully satisfy the 3-source audit for `WEB-01`.
- Audit gap: `WEB-02` is still open across the single-customer, portfolio, offer, and learning views.
- Primary implementation surface: `credit-coach-website/client/src/pages/DemoCenterPage.tsx`
- Supporting schema and formatting seams:
  - `credit-coach-website/shared/demo-schema.ts`
  - `credit-coach-website/client/src/components/RoadmapPhaseCard.tsx`
  - `credit-coach-website/client/src/lib/demo-formatters.ts`

## Required Outcome

- Introduce a three-level reading hierarchy:
  - Executive View by default
  - Section View for customer, portfolio, offer, and learning
  - Deep technical detail collapsed under a technical reveal
- Replace technical-first customer language with business narrative:
  - status
  - expected outcome
  - risk trend
- Replace monthly framing with:
  - first 4 weeks
  - weeks 4-12
  - weeks 12-24
- Reduce KPI overload to 2-3 headline metrics per section and move the rest behind reveal controls
- Add context labels, section bridges, disclaimer, and strong demo CTA blocks
- Enforce full-language consistency per locale and simplify the visual treatment into a trustworthy product UI
