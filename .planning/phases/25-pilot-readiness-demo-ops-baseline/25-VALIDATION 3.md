---
phase: 25
slug: pilot-readiness-demo-ops-baseline
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-20
---

# Phase 25 - Validation Strategy

> Per-phase validation contract for buyer handoff readiness, pilot ops baseline, and curated demo packaging.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | TypeScript build checks + Markdown artifact guards + shell content checks |
| **Config file** | `credit-coach-website/tsconfig.json`, `credit-coach-website/tsconfig.node.json` |
| **Quick run command** | `cd credit-coach-website && npm run check` |
| **Full suite command** | `cd credit-coach-website && npm run check && npm run build` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach-website && npm run check`
- **After every plan wave:** Run `cd credit-coach-website && npm run check && npm run build`
- **Before `$gsd-verify-work`:** Full suite must be green and the new docs must state the pilot baseline and curated demo handoff explicitly
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 25-01-01 | 01 | 1 | OPS-02 | structured demo-intake schema coverage | `rg -n "institutionType|portfolioFocus|demoTrack|timeline|dataReadiness" credit-coach-website/shared/content-schema.ts credit-coach-website/client/src/components/InquiryForm.tsx` | ✅ | ⬜ pending |
| 25-01-02 | 01 | 1 | OPS-02 | route and persistence wiring for buyer handoff | `rg -n "institutionType|portfolioFocus|demoTrack|timeline|dataReadiness|storageMode|database|memory" credit-coach-website/shared/schema.ts credit-coach-website/server/routes.ts credit-coach-website/server/storage/inbound.ts credit-coach-website/client/src/pages/ContactPage.tsx && cd credit-coach-website && npm run check && npm run build` | ✅ | ⬜ pending |
| 25-02-01 | 02 | 2 | OPS-02 | pilot readiness baseline doc completeness | `rg -n "DATABASE_URL|PORT|npm run build|npm run start|/api/health|auth|memory|database|pilot" credit-coach-website/PILOT_READINESS.md` | ✅ | ⬜ pending |
| 25-02-02 | 02 | 2 | OPS-02 | docs cross-link and scope honesty | `rg -n "PILOT_READINESS.md|pilot readiness|auth|CRM|database|memory" credit-coach-website/README.md credit-coach-website/TECH_ARCHITECTURE.md && cd credit-coach-website && npm run check && npm run build` | ✅ | ⬜ pending |
| 25-03-01 | 03 | 3 | OPS-02 | curated demo handoff mapping completeness | `rg -n "institutionType|portfolioFocus|demoTrack|timeline|dataReadiness|/demo|/proof|next step" credit-coach-website/CURATED_DEMO_HANDOFF.md` | ✅ | ⬜ pending |
| 25-03-02 | 03 | 3 | OPS-02 | artifact and trust-preservation coverage | `rg -n "single-customer-roadmap|portfolio-batch-summary|offer-optimization|outcome-ingestion|product-confidence-snapshot|Representative product preview|safe to pilot" credit-coach-website/CURATED_DEMO_HANDOFF.md && cd credit-coach-website && npm run check && npm run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach-website/client/src/pages/ContactPage.tsx` - contact entry surface already exists
- [x] `credit-coach-website/client/src/components/InquiryForm.tsx` - inbound form handling already exists
- [x] `credit-coach-website/shared/content-schema.ts` - intake schemas already exist and can be extended
- [x] `credit-coach-website/server/routes.ts` - inbound request routes already exist
- [x] `credit-coach-website/server/storage/inbound.ts` - persistence seam already exists
- [x] `credit-coach-website/server/db.ts` - environment-driven database seam already exists
- [x] `.planning/phases/25-pilot-readiness-demo-ops-baseline/25-CONTEXT.md` - phase objective already exists

---

## Manual-Only Verifications

- confirm the buyer handoff story is honest about the current auth and persistence posture
- confirm the structured intake fields are enough to tailor a serious institution-specific demo without turning into a CRM rebuild
- confirm the curated demo handoff pack maps only to shipped `/demo` and `/proof` capability, not invented product scope
- confirm the pilot-readiness baseline separates ready-now, required-before-pilot, and deferred items

All structural behavior should remain automatically verified through schema guards, docs guards, and website `check` and `build`.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity preserved across all three execution waves
- [x] Wave 0 covers the current product and ops seams used by Phase 25
- [x] No watch-mode flags
- [x] Feedback latency acceptable for iterative execution
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-20
