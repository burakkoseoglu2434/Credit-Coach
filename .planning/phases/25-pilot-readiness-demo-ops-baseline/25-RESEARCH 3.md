# Phase 25: Pilot Readiness & Demo Ops Baseline - Research

**Researched:** 2026-03-20
**Status:** Ready for planning
**Confidence:** HIGH

## Planning Question

What is the minimum serious-buyer handoff baseline that turns the current website from a strong demo surface into a controlled pilot entry point without pretending that full auth, CRM, or production operations already exist?

## Planning Basis

Phase 25 now has a scoped `25-CONTEXT.md`. For this research pass, the authoritative inputs are:

- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/v1.3-MILESTONE-AUDIT.md`
- `.planning/phases/24-analyst-workflow-uat-validation/24-VERIFICATION.md`
- `.planning/phases/25-pilot-readiness-demo-ops-baseline/25-CONTEXT.md`
- `credit-coach-website/client/src/pages/ContactPage.tsx`
- `credit-coach-website/client/src/components/InquiryForm.tsx`
- `credit-coach-website/shared/content-schema.ts`
- `credit-coach-website/shared/schema.ts`
- `credit-coach-website/server/routes.ts`
- `credit-coach-website/server/storage/inbound.ts`
- `credit-coach-website/server/db.ts`
- `credit-coach-website/README.md`
- `credit-coach-website/TECH_ARCHITECTURE.md`
- `credit-coach-website/package.json`

This is sufficient because the missing Phase 25 work is not deeper model capability. The gap is buyer handoff readiness: what the site captures, what the ops baseline promises, and how a team turns one inbound request into a trustworthy institution-specific demo path.

## Executive Summary

Phase 25 should be a mixed product-and-ops phase.

The website already has:

- a working `/contact` route
- separate `contact`, `demo`, and `investor` intake paths
- backend persistence routes with database or memory fallback
- build, start, and health-check seams

But it does not yet have a serious pilot baseline.

The gaps are now operational and packaging-oriented:

- demo requests collect too little institution context for real pilot follow-up
- the UI says requests are routed, but it does not define the pilot handoff contract clearly enough
- the current website has no explicit pilot-readiness baseline for deployment, storage, auth posture, or operator ownership
- there is no curated demo handoff pack that maps one institution's needs to the shipped `/demo` and `/proof` surfaces

Phase 25 should therefore split into three linked outputs:

1. structured buyer and demo intake
2. explicit pilot readiness baseline documentation
3. curated demo handoff packaging

## Current State of Lead Capture

### What exists

`ContactPage.tsx` and `InquiryForm.tsx` already support three inquiry kinds:

- general contact
- demo request
- investor intro

The form posts to:

- `POST /api/contact`
- `POST /api/demo-request`
- `POST /api/investor-request`

This is a valid base for Phase 25.

### What is missing

The current demo path still captures only:

- name
- company
- role
- email
- message
- use case
- team size

That is enough for a lightweight website contact form, but not enough for serious institution-specific curation. The form does not yet capture the intake details an operator needs to tailor a credible pilot conversation, such as:

- institution type
- portfolio focus
- preferred demo track
- timing or pilot horizon
- data-readiness posture

Research conclusion:

- Phase 25 should deepen the demo request contract before it tries to claim pilot readiness

## Current State of Ops Baseline

### What exists

The website has:

- `npm run build`
- `npm run start`
- `GET /api/health`
- optional `DATABASE_URL` support through `server/db.ts`

This means the repo already has the raw technical seams needed for a minimum runtime baseline.

### What is missing

The current product still leaves key handoff questions implicit:

- database-backed persistence is optional, but there is no pilot-facing rule for when memory fallback is unacceptable
- `storageMode` is returned by the API, but the product does not turn that into a clear operator baseline
- `TECH_ARCHITECTURE.md` explicitly says `auth` is not in V1, but there is no Phase 25-level statement of what access posture is acceptable for a controlled pilot handoff
- there is no single pilot-readiness document that distinguishes:
  - ready now
  - required before pilot
  - deferred beyond this milestone

Research conclusion:

- Phase 25 should document the minimum runtime and operator baseline rather than over-scoping into a full auth or CRM implementation

## Current State of Curated Demo Packaging

### What exists

The site now has strong buyer-safe and analyst-safe surfaces:

- `/demo` for customer, portfolio, offer, and learning views
- `/proof` for safe-to-pilot and watchlist framing

Phase 24 proved these surfaces are good enough for representative analyst tasks.

### What is missing

There is still no operational handoff artifact that answers:

- which demo track should be shown first for a lender buyer
- which routes and artifacts should support that track
- which disclaimers and trust cues must remain visible
- how intake context maps into a repeatable institution-specific walkthrough

Without this, an inbound demo request still depends too much on ad hoc operator judgment.

Research conclusion:

- Phase 25 should create one curated demo handoff pack that maps intake context to the existing `/demo` and `/proof` surfaces without inventing new product capability

## Phase Boundary Recommendation

Phase 25 should **not** attempt:

- full authentication
- multi-user permissions
- CRM integration
- a production admin panel
- a new institution-facing app

Phase 25 **should** establish the minimum credible boundary for a serious buyer handoff:

- enough structured intake to route a pilot conversation intelligently
- enough ops documentation to say what is ready versus deferred
- enough demo packaging to tailor the current product story to one institution safely

## Recommended Plan Split

### Plan 25-01 - Harden structured buyer intake

Focus on:

- extending the demo request contract
- persisting structured pilot-intake fields
- improving the contact surface so buyers understand what happens next

This is the minimum lead-capture baseline.

### Plan 25-02 - Publish the pilot readiness baseline

Focus on:

- creating a single pilot-readiness document
- clarifying deployment, storage, auth posture, and operator ownership
- linking the website docs to that baseline

This keeps the product honest about what "pilot-ready" means in practice.

### Plan 25-03 - Package the curated demo handoff flow

Focus on:

- creating a repeatable institution-specific demo handoff pack
- mapping intake fields to the current `/demo` and `/proof` surfaces
- preserving trust and provenance in every curated flow

This turns a request into an operator-ready demo path.

## Main Risks

### Risk 1: Phase 25 drifts into full platform hardening

If the phase tries to solve auth, admin tooling, and CRM all at once, it will blow past the intended `OPS-02` boundary.

Mitigation:

- define the minimum pilot baseline explicitly
- document what remains deferred

### Risk 2: Intake gets deeper, but the follow-up path stays ambiguous

If the form captures more fields without producing a clearer operator handoff, the work will still not close the audit gap.

Mitigation:

- pair structured intake with a curated demo handoff pack

### Risk 3: Ops docs overclaim production readiness

If the repo describes the website as pilot-ready without clarifying the current auth and persistence posture, trust will fall rather than improve.

Mitigation:

- separate "ready now" from "required before pilot" and "deferred"

## Validation Architecture

Phase 25 is best validated through a hybrid contract:

- TypeScript and build checks for any website code or schema changes
- docs integrity checks for pilot-readiness and curated demo handoff artifacts
- route and schema guardrails that confirm the intake contract, runtime baseline, and handoff pack stay aligned

This phase does not need a full end-to-end deployment environment to be Nyquist-compliant. It needs one trustworthy intake contract, one explicit ops baseline, and one repeatable curated demo handoff artifact.
