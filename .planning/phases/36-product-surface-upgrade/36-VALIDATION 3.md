---
phase: 36
slug: product-surface-upgrade
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-22
---

# Phase 36 - Validation Strategy

> Per-phase validation contract for action-first product rendering, strict typed artifact consumption, and removal of UI-side narrative invention from the single-customer surface.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | TypeScript build checks + shell contract checks |
| **Config file** | `credit-coach-website/tsconfig.json`, `credit-coach-website/tsconfig.node.json` |
| **Quick run command** | `cd credit-coach-website && npm run check` |
| **Full suite command** | `cd credit-coach-website && npm run check && npm run build` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach-website && npm run check`
- **After every plan wave:** Run `cd credit-coach-website && npm run check && npm run build`
- **Before `$gsd-verify-work`:** Full suite must be green and no UI-side fallback narrative helpers should remain in the single-customer surface
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 36-01-01 | 01 | 1 | SURF-01 | typed shared schema and payload bridge integrity | `cd credit-coach-website && npm run check` | ✅ | ⬜ pending |
| 36-01-02 | 01 | 1 | SURF-01 | UI fallback narrative removal | `bash -lc 'if rg -n "phaseNarrative|fallbackExpectedOutcome|fallbackTimingHint" /Users/bkoseoglu/Documents/GitHub/Credit-Coach/credit-coach-website/client/src/components/RoadmapPhaseCard.tsx; then exit 1; fi'` | ✅ | ⬜ pending |
| 36-02-01 | 02 | 2 | SURF-01 | action-first single-customer surface composition | `cd credit-coach-website && npm run check` | ✅ | ⬜ pending |
| 36-02-02 | 02 | 2 | SURF-01 | page buildability after hierarchy rewrite | `cd credit-coach-website && npm run build` | ✅ | ⬜ pending |
| 36-03-01 | 03 | 3 | SURF-01 | strict business-vs-technical boundary and fail-soft rendering | `cd credit-coach-website && npm run check` | ✅ | ⬜ pending |
| 36-03-02 | 03 | 3 | SURF-01 | end-to-end surface regression closure | `cd credit-coach-website && npm run check && npm run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach-website/package.json` scripts — existing `check` and `build` commands are sufficient for frontend validation
- [x] `credit-coach-website/client/src/pages/DemoCenterPage.tsx` — the single-customer surface seam already exists and can be refactored in place
- [x] `credit-coach-website/client/src/components/RoadmapPhaseCard.tsx` — the main drift seam is isolated and directly verifiable
- [x] `credit-coach-website/shared/demo-schema.ts` — the typed consumer contract already exists and can be extended without inventing page-local semantics
- [x] `credit-coach-website/server/services/demo-data.ts` and `credit-coach-website/server/services/live-demo.ts` — artifact routing is already in place for live and static payload validation

---

## Manual-Only Verifications

One human visual pass is still required after execution:

- confirm the customer surface opens with:
  - executive summary
  - checkpoint strip
  - action-first cards
- confirm the page feels action-first rather than phase-first
- confirm each visible action card answers:
  - what to do
  - what happens
  - by when
  - how realistic it is
- confirm only one primary numeric statement is visible per action card
- confirm the checkpoint strip sits above the action list and `4w` is visually dominant
- confirm offer appears only on offer-bearing plans and remains clearly secondary to the customer path
- confirm reasons appear after the action flow and before technical reveal
- confirm technical reveal is end-of-page and default collapsed
- confirm missing surface fields produce neutral or hidden states rather than invented fallback copy
- confirm TR mode is fully Turkish and EN mode is fully English

All core behavior should remain automatically verified through `check`, `build`, and shell contract checks.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity preserved across all execution waves
- [x] Wave 0 covers frontend buildability, typed contract seams, and fallback-removal checks
- [x] No watch-mode flags
- [x] Feedback latency acceptable for iterative execution
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-22
