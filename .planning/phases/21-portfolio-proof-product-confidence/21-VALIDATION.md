---
phase: 21
slug: portfolio-proof-product-confidence
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-19
---

# Phase 21 - Validation Strategy

> Per-phase validation contract for refreshed portfolio proof, explicit product-facing proof verdicts, baseline-aware comparison against Phase 17, and engine-owned proof-page sync.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Engine framework** | pytest 8.x |
| **Website checks** | `npm run check` + `npm run build` |
| **Engine quick run** | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_phase_experiment_suite.py` |
| **Engine full run** | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_phase_experiment_suite.py tests/test_kpi_contract.py` |
| **Website run** | `cd credit-coach-website && npm run check && npm run build` |
| **Estimated runtime** | ~75 seconds |

---

## Sampling Rate

- **After every task commit:** Run the most local engine or website verifier for that task
- **After every plan wave:** Run the designated wave verification command
- **Before `$gsd-verify-work`:** Engine full run + website run must both be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 21-01-01 | 01 | 1 | PORT-01 | proof verdict | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py` | ✅ | ⬜ pending |
| 21-01-02 | 01 | 1 | PORT-01 | batch artifact refresh | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_phase_experiment_suite.py` | ✅ | ⬜ pending |
| 21-02-01 | 02 | 2 | WEB-01 | suite confidence packaging | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_kpi_contract.py` | ✅ | ⬜ pending |
| 21-02-02 | 02 | 2 | WEB-01 | curated proof snapshot contract | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py` | ✅ | ⬜ pending |
| 21-03-01 | 03 | 3 | WEB-01 | typed proof schema | `cd credit-coach-website && npm run check` | ✅ | ⬜ pending |
| 21-03-02 | 03 | 3 | WEB-03 | proof page consumption | `cd credit-coach-website && npm run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_portfolio_validation.py` — existing proof tests can protect verdict, confidence, delta, and demo-fit proof semantics
- [x] `credit-coach/tests/test_phase_experiment_suite.py` — suite aggregation tests can protect refreshed portfolio proof and curated confidence packaging
- [x] `credit-coach/tests/test_kpi_contract.py` — release-facing contract tests can guard against accidental mixing of internal release semantics with product-facing proof verdicts
- [x] `credit-coach-website/shared/demo-schema.ts` — typed website schema can protect the curated proof snapshot contract
- [x] `credit-coach-website/client/src/pages/ProofPage.tsx` — proof page already has a single rendering seam that can be verified through typecheck and build

---

## Manual-Only Verifications

One human proof scan is still required after execution:

- confirm product-facing proof verdict stays separate from internal release decision language
- confirm the refreshed proof carries explicit delta versus the Phase 17 canonical snapshot
- confirm the headline proof story centers on:
  - product-ready coverage
  - governance-safe coverage
  - execution-aware value
- confirm `weak_4w` and delayed trajectory truth stay visible as first-class supporting evidence
- confirm demo representativeness is visible as a trust annotation rather than a headline KPI
- confirm the curated proof snapshot contains:
  - verdict
  - confidence
  - metric hierarchy
  - Phase 17 delta
  - demo-fit annotation
  - supporting trust layer
- confirm the website proof page no longer depends on stitching together multiple low-level proof artifacts to explain whether the system is working
- confirm an outcome such as `more honest but narrower` can still be expressed without being flattened into a false-positive “working” story

All core logic should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity preserved across all three waves
- [x] Wave 0 covers engine proof, suite packaging, release-semantics adjacency, and website proof consumption
- [x] No watch-mode flags
- [x] Feedback latency acceptable for iterative execution
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-19
