---
phase: 66-demo-narrative-alignment
plan: 03
subsystem: website-demo
tags: [demo_center, narrative_contract, proof_rail, engine_owned_fields]
requires:
  - phase: 66-demo-narrative-alignment
    provides: "Narrative posture fields are emitted producer-side (plan 01)"
provides:
  - "Website demo consumes engine-owned posture fields (no consumer inference)"
  - "Deterministic actionable vs informational demo cases (registry-backed)"
  - "Demo Center renders the canonical one-screen story + proof rail"
affects: [credit-coach-website]
tech-stack:
  added: []
  patterns:
    - "Typed consumer: UI shows 'Unavailable in this view' instead of synthesizing meaning"
key-files:
  created:
    - credit-coach-website/demo-data/demo-cases.json
  modified:
    - credit-coach/src/credit_coach/cli/run_recourse.py
    - credit-coach-website/shared/demo-schema.ts
    - credit-coach-website/server/services/live-demo.ts
    - credit-coach-website/server/services/demo-data.ts
    - credit-coach-website/client/src/pages/DemoCenterPage.tsx
key-decisions:
  - "Proof rail shows recoverability band first + approval_gap numeric second"
  - "Demo Center exposes an explicit full vs limited toggle via two deterministic demo slugs"
  - "No ACTION_DETAILS/FEATURE_ACTIONS inference: website is a typed consumer of engine truth"
requirements-completed: [NARR-03]
duration: 70m
completed: 2026-04-10
---

# Phase 66 — Plan 03 Summary

**Aligned the website demo to the Phase 66 narrative contract: deterministic posture, band-first proof rail, and a canonical one-screen story without consumer-side inference.**

## Accomplishments
- Removed website-side action/detail inference and made the demo a typed consumer of engine-owned posture fields (`recourse_mode`, `recoverability_bucket`, `approval_gap`, `narrative_type`, `informational_subtype`, etc.).
- Added a deterministic demo case registry (`demo-cases.json`) and a second “limited” demo slug so the website can show both actionable/full and informational/limited postures.
- Updated Demo Center to a deterministic one-screen story (Decision → Mode → Why → Path/No-plan → Outcome) and added a proof rail (band primary, numeric secondary) with explicit “no plan promoted” limited-mode wording.

## Task Commits
1. **Prereq: Fix readiness stage derivation (checkpoint-based)** — `a366d80`
2. **Task 1: Schema + live demo normalization (engine-owned posture, no inference)** — `b5a20e8`
3. **Task 2–3: Deterministic cases + Demo Center story + proof rail** — `c5ff1d3`

## Verification
- `cd credit-coach-website && npm run check`
- `cd credit-coach-website && npm run build`

---
*Phase: 66-demo-narrative-alignment*
*Completed: 2026-04-10*

