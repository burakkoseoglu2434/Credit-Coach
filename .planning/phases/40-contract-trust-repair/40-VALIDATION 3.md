---
phase: 40
slug: contract-trust-repair
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-23
---

# Phase 40 - Validation Strategy

> Per-phase validation contract for raw artifact normalization, raw-to-flat parity, zero-step rejection, contract-health rollups, and business-safe consumer trust alignment.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + TypeScript static checks |
| **Config file** | `credit-coach/pyproject.toml`, `credit-coach-website/package.json` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_customer_artifact_collection.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_customer_artifact_collection.py -q && cd ../credit-coach-website && npm run check` |
| **Estimated runtime** | ~35 seconds |

---

## Sampling Rate

- **After every task commit:** Run the plan-local command listed in the task map
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_customer_artifact_collection.py -q`
- **Before `$gsd-verify-work`:** Full suite plus website static check must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 40-01-01 | 01 | 1 | TRST-01 | raw roadmap normalization and fallback rules | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py -q` | ✅ | ⬜ pending |
| 40-01-02 | 01 | 1 | TRST-01 | shared contract normalization helper | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_customer_artifact_collection.py -q` | ✅ | ⬜ pending |
| 40-02-01 | 02 | 2 | TRST-02 | flat customer metrics mirroring and parity flags | `cd credit-coach && python -m pytest tests/test_customer_artifact_collection.py -q` | ✅ | ⬜ pending |
| 40-02-02 | 02 | 2 | TRST-02 | manifest and summary contract-health rollups | `cd credit-coach && python -m pytest tests/test_customer_artifact_collection.py -q` | ✅ | ⬜ pending |
| 40-03-01 | 03 | 3 | TRST-01 | zero-step rejection and no-path contract behavior | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_customer_artifact_collection.py -q` | ✅ | ⬜ pending |
| 40-03-02 | 03 | 3 | TRST-02 | business-facing consumer trust alignment | `cd credit-coach-website && npm run check` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_recourse_redesign.py` — existing raw roadmap tests can protect summary, checkpoint, and serialized contract fields
- [x] `credit-coach/tests/test_customer_artifact_collection.py` — existing collection tests can protect raw-plus-flat output structure and row counts
- [x] `credit-coach-website/server/services/live-demo.ts` — existing live consumer path is available for contract-source alignment
- [x] `credit-coach-website/shared/demo-schema.ts` — consumer-side typing exists if producer truth becomes stricter

---

## Manual-Only Verifications

One human scan is still required after execution:

- confirm `summary` is clearly the canonical decision truth and `contract_health` reads as derived
- confirm zero-step customers appear as explicit rejections rather than silent empty plans
- confirm business-visible outputs never show internal `NEEDS_REVIEW`
- confirm collection summary can explain contract failures in one read without opening raw JSON

All core logic should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers raw roadmap, collection artifacts, and downstream consumer trust
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-23
