---
phase: 25-pilot-readiness-demo-ops-baseline
plan: 01
subsystem: buyer-intake
tags: [ops, contact, intake, pilot, website]
requires:
  - phase: 24-analyst-workflow-uat-validation
    provides: buyer-safe and analyst-safe demo and proof surfaces
provides:
  - structured pilot-intake contract for demo requests
  - contact-page next-step framing
  - persistence-aware buyer handoff messaging
affects: [contact-page, inquiry-form, inbound-routing, shared-schema]
tech-stack:
  modified:
    - credit-coach-website/shared/content-schema.ts
    - credit-coach-website/shared/schema.ts
    - credit-coach-website/server/storage/inbound.ts
    - credit-coach-website/client/src/components/InquiryForm.tsx
    - credit-coach-website/client/src/pages/ContactPage.tsx
key-decisions:
  - "Demo requests now capture institution, portfolio, track, timeline, and data-readiness context before a serious pilot follow-up."
  - "The UI now states the difference between database-backed persistence and memory fallback instead of hiding it."
patterns-established:
  - "Buyer handoff surfaces should collect structured curation inputs and explain the next step in business language, not behave like a generic website form."
requirements-completed: [OPS-02]
duration: manual-execution
completed: 2026-03-20
---

# Phase 25 Plan 01 Summary

**The website now captures structured pilot-intake context for demo requests and explains the buyer handoff path more honestly.**

## Accomplishments
- Extended the demo-request schema and persistence layer with `institutionType`, `portfolioFocus`, `demoTrack`, `timeline`, and `dataReadiness`.
- Rebuilt the demo tab in [InquiryForm.tsx](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/client/src/components/InquiryForm.tsx) so serious buyers can specify portfolio context, track, timing, and readiness before follow-up.
- Updated [ContactPage.tsx](/Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/client/src/pages/ContactPage.tsx) to frame the page as a controlled pilot and demo intake step with explicit next-step language.
- Added persistence-aware success messaging so memory fallback is treated as acceptable for demo capture but not as a hidden pilot-ready posture.

## Verification
- `rg -n "institutionType|portfolioFocus|demoTrack|timeline|dataReadiness" credit-coach-website/shared/content-schema.ts credit-coach-website/shared/schema.ts`
- `rg -n "institutionType|portfolioFocus|demoTrack|timeline|dataReadiness|database|memory|pilot|next step" credit-coach-website/client/src/components/InquiryForm.tsx credit-coach-website/client/src/pages/ContactPage.tsx credit-coach-website/server/storage/inbound.ts`
- `cd credit-coach-website && npm run check`
- `cd credit-coach-website && npm run build`

## Notes
- The inbound API shape for `/api/demo-request` is now deeper, so database-backed pilot environments should run the normal schema push before serious use.
- Existing general contact and investor flows were left intact.

---
*Phase: 25-pilot-readiness-demo-ops-baseline*
*Completed: 2026-03-20*
