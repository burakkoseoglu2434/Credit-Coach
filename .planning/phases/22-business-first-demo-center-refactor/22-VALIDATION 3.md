---
phase: 22
slug: business-first-demo-center-refactor
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-20
---

# Phase 22 - Validation Strategy

> Per-phase validation contract for Demo Center hierarchy simplification, phase-window language cleanup, and Phase 21 summary traceability repair.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | TypeScript build checks + shell traceability audit |
| **Config file** | `credit-coach-website/tsconfig.json`, `credit-coach-website/tsconfig.node.json` |
| **Quick run command** | `cd credit-coach-website && npm run check` |
| **Full suite command** | `cd credit-coach-website && npm run check && npm run build` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach-website && npm run check`
- **After every plan wave:** Run `cd credit-coach-website && npm run check && npm run build`
- **Before `$gsd-verify-work`:** Full suite must be green and Phase 21 summary metadata must be present
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 22-01-01 | 01 | 1 | WEB-01 | summary frontmatter repair | `rg -n "^(---|phase:|plan:|requirements-completed:)" .planning/phases/21-portfolio-proof-product-confidence/21-0[123]-SUMMARY.md` | ✅ | ⬜ pending |
| 22-01-02 | 01 | 1 | WEB-01 | closure metadata accuracy | `rg -n "WEB-01" .planning/phases/21-portfolio-proof-product-confidence/21-0[123]-SUMMARY.md` | ✅ | ⬜ pending |
| 22-02-01 | 02 | 1 | WEB-02 | shared demo-surface component integrity | `cd credit-coach-website && npm run check` | ✅ | ⬜ pending |
| 22-02-02 | 02 | 1 | WEB-02 | product-surface buildability after visual simplification | `cd credit-coach-website && npm run build` | ✅ | ⬜ pending |
| 22-03-01 | 03 | 2 | WEB-02 | executive and section hierarchy render integrity | `cd credit-coach-website && npm run check` | ✅ | ⬜ pending |
| 22-03-02 | 03 | 2 | WEB-02 | CTA, bridge, and KPI reduction renderability | `cd credit-coach-website && npm run build` | ✅ | ⬜ pending |
| 22-04-01 | 04 | 2 | WEB-02 | phase-window roadmap language integrity | `cd credit-coach-website && npm run check` | ✅ | ⬜ pending |
| 22-04-02 | 04 | 2 | WEB-02 | roadmap card buildability after month-language removal | `cd credit-coach-website && npm run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach-website/package.json` scripts — existing `check` and `build` commands are sufficient for page and component validation
- [x] `credit-coach-website/client/src/pages/DemoCenterPage.tsx` — existing page seam can be refactored without adding a new validation harness
- [x] `credit-coach-website/client/src/components/RoadmapPhaseCard.tsx` — existing roadmap card seam can be updated in place
- [x] `.planning/phases/21-portfolio-proof-product-confidence/21-0*-SUMMARY.md` — traceability repair target already exists and can be verified with `rg`

---

## Manual-Only Verifications

One human visual review is still required after execution:

- confirm the page opens with `Representative product preview — not real customer data` and a business-first executive frame
- confirm the default customer view leads with status, expected outcome, and risk trend rather than PD, phase, or execution-probability language
- confirm customer, portfolio, offer, and learning sections each begin with:
  - a bridge sentence
  - a one-line summary
  - a `Why this matters` explanation
- confirm each major section ends with a `Request Demo` CTA block
- confirm every visible KPI or chart includes a context label such as `Curated demo snapshot`, `Representative simulation`, or `Offline benchmark`
- confirm visible KPI density is capped at 2-3 per major section
- confirm technical details are hidden behind explicit reveal controls by default
- confirm the roadmap uses `first 4 weeks`, `weeks 4-12`, and `weeks 12-24` rather than month labels
- confirm TR mode is fully Turkish and EN mode is fully English
- confirm the page looks like a restrained product UI rather than a glowing dashboard

All core behavior should remain automatically verified through `check`, `build`, and summary metadata inspection.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity preserved across both execution waves
- [x] Wave 0 covers website buildability and summary-traceability repair
- [x] No watch-mode flags
- [x] Feedback latency acceptable for iterative execution
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-20
