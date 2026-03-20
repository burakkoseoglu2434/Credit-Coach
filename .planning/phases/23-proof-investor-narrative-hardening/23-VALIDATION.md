---
phase: 23
slug: proof-investor-narrative-hardening
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-20
---

# Phase 23 - Validation Strategy

> Per-phase validation contract for Proof and Investor narrative hardening, executive-first hierarchy, and shared buyer-safe vocabulary.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | TypeScript build checks + shell content guards |
| **Config file** | `credit-coach-website/tsconfig.json`, `credit-coach-website/tsconfig.node.json` |
| **Quick run command** | `cd credit-coach-website && npm run check` |
| **Full suite command** | `cd credit-coach-website && npm run check && npm run build` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach-website && npm run check`
- **After every plan wave:** Run `cd credit-coach-website && npm run check && npm run build`
- **Before `$gsd-verify-work`:** Full suite must be green and buyer-facing copy checks must pass
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 23-01-01 | 01 | 1 | WEB-03 | shared content seam integrity | `cd credit-coach-website && npm run check` | ✅ | ⬜ pending |
| 23-01-02 | 01 | 1 | WEB-03 | vocabulary guardrail presence | `rg -n "controlled rollout|institution-ready safeguards|decision intelligence infrastructure|baseline portfolio snapshot|previous benchmark" credit-coach-website/client/src/data/site-content.ts credit-coach-website/client/src/pages/ProofPage.tsx credit-coach-website/client/src/pages/InvestorPage.tsx` | ✅ | ⬜ pending |
| 23-02-01 | 02 | 2 | WEB-03 | proof executive memo render integrity | `cd credit-coach-website && npm run check` | ✅ | ⬜ pending |
| 23-02-02 | 02 | 2 | WEB-03 | proof page buildability after narrative rewrite | `cd credit-coach-website && npm run build` | ✅ | ⬜ pending |
| 23-03-01 | 03 | 2 | WEB-03 | investor narrative arc render integrity | `cd credit-coach-website && npm run check` | ✅ | ⬜ pending |
| 23-03-02 | 03 | 2 | WEB-03 | investor page buildability after commercial-story rewrite | `cd credit-coach-website && npm run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach-website/package.json` scripts — existing `check` and `build` commands are sufficient for page and content validation
- [x] `credit-coach-website/client/src/pages/ProofPage.tsx` — existing proof rendering seam can be rewritten in place
- [x] `credit-coach-website/client/src/pages/InvestorPage.tsx` — existing investor rendering seam can be rewritten in place
- [x] `credit-coach-website/client/src/data/site-content.ts` — current shared copy seam can host the unified vocabulary layer

---

## Manual-Only Verifications

One human narrative review is still required after execution:

- confirm the Proof page opens by answering `Will this system actually work on my portfolio?`
- confirm the top Proof verdict reads as a buyer-confidence statement rather than an evidence spreadsheet
- confirm a compact trust rail appears directly under the Proof verdict and communicates `safe to pilot`
- confirm `Phase 17` does not appear in buyer-facing page copy and is translated into baseline language
- confirm default Proof copy avoids internal terms such as `governance-safe`, `proof artifact`, or `release controls`
- confirm Proof evidence remains available in lower-detail sections or technical reveals rather than disappearing
- confirm the Investor page follows:
  - market pain
  - product wedge
  - proof it works
  - monetization
- confirm the Investor page reads like a disciplined product brief rather than a hype-heavy pitch page
- confirm Investor positioning reads as `decision intelligence infrastructure`
- confirm the default commercial read stays `pilot -> platform` without explicit pricing-model detail
- confirm TR mode is fully Turkish and EN mode is fully English

All structural behavior should remain automatically verified through `check`, `build`, and content-string guards.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity preserved across both execution waves
- [x] Wave 0 covers all page and shared-content seams touched by this phase
- [x] No watch-mode flags
- [x] Feedback latency acceptable for iterative execution
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-20
