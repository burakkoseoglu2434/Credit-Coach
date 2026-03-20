---
phase: 24
slug: analyst-workflow-uat-validation
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-20
---

# Phase 24 - Validation Strategy

> Per-phase validation contract for milestone-local analyst workflow and UAT evidence.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Markdown artifacts + TypeScript build checks + shell content guards |
| **Config file** | `credit-coach-website/tsconfig.json`, `credit-coach-website/tsconfig.node.json` |
| **Quick run command** | `cd credit-coach-website && npm run check` |
| **Full suite command** | `cd credit-coach-website && npm run check && npm run build` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach-website && npm run check`
- **After every plan wave:** Run `cd credit-coach-website && npm run check && npm run build`
- **Before `$gsd-verify-work`:** Full suite must be green and UAT artifacts must show an explicit OPS-01 outcome
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 24-01-01 | 01 | 1 | OPS-01 | analyst task matrix completeness | `rg -n "Single-customer review|Portfolio interpretation|Offer assessment|Learning-readiness interpretation|Proof-confidence review" .planning/phases/24-analyst-workflow-uat-validation/24-UAT.md` | ✅ | ⬜ pending |
| 24-01-02 | 01 | 1 | OPS-01 | scoring and closure-gate presence | `rg -n "understandable|useful|trustworthy|pass|caution|fail|OPS-01" .planning/phases/24-analyst-workflow-uat-validation/24-UAT.md` | ✅ | ⬜ pending |
| 24-02-01 | 02 | 2 | OPS-01 | walkthrough packet route and section mapping | `rg -n "/demo|/proof|Demo Center|Proof page|customer|portfolio|offer|learning" .planning/phases/24-analyst-workflow-uat-validation/24-UAT-RUNBOOK.md` | ✅ | ⬜ pending |
| 24-02-02 | 02 | 2 | OPS-01 | artifact and render-reference integrity | `rg -n "single-customer-roadmap|portfolio-batch-summary|offer-optimization|outcome-ingestion|product-confidence-snapshot|Show technical details" .planning/phases/24-analyst-workflow-uat-validation/24-UAT-RUNBOOK.md && cd credit-coach-website && npm run check && npm run build` | ✅ | ⬜ pending |
| 24-03-01 | 03 | 3 | OPS-01 | results packet completeness | `rg -n "Task ID|Understanding|Usefulness|Trust|Overall|Blocker|Technical detail required" .planning/phases/24-analyst-workflow-uat-validation/24-UAT-RESULTS.md` | ✅ | ⬜ pending |
| 24-03-02 | 03 | 3 | OPS-01 | explicit closure recommendation | `rg -n "OPS-01|pass|caution|fail|blocked|next step" .planning/phases/24-analyst-workflow-uat-validation/24-UAT-RESULTS.md` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach-website/client/src/pages/DemoCenterPage.tsx` - core analyst workflow surface already exists
- [x] `credit-coach-website/client/src/pages/ProofPage.tsx` - trust and benchmark companion surface already exists
- [x] `credit-coach-website/package.json` - existing `check` and `build` commands are sufficient for current-surface validation
- [x] `.planning/phases/24-analyst-workflow-uat-validation/24-CONTEXT.md` - phase objective and requirement target already exist

---

## Manual-Only Verifications

- confirm an analyst can complete the single-customer, portfolio, offer, learning, and proof-confidence tasks using the current shipped surfaces
- confirm the default read is sufficient for the main answer in most tasks, with technical detail used as support rather than as the only readable layer
- confirm every recorded caution or failure is tied to a concrete route, section, or evidence gap
- confirm the results packet explicitly states whether `OPS-01` should close or remain open
- confirm locale notes are captured if the walkthrough is run in `TR`, `EN`, or both

All structural behavior should remain automatically verified through docs guards plus website `check` and `build`.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity preserved across all three execution waves
- [x] Wave 0 covers the current product surfaces used by the analyst workflow
- [x] No watch-mode flags
- [x] Feedback latency acceptable for iterative execution
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-20
