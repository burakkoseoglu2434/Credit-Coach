---
phase: 44
slug: production-pilot-baseline
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-23
---

# Phase 44 — Validation Strategy

> Per-phase validation contract for pilot refresh orchestration, pilot artifact QA, institution overlay provenance, explanation-pack packaging, and bounded proof-surface guidance.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_pilot_baseline_refresh.py tests/test_pilot_artifact_qa.py tests/test_decision_explanation_pack.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_pilot_baseline_refresh.py tests/test_pilot_artifact_qa.py tests/test_decision_explanation_pack.py tests/test_pilot_integration.py tests/test_production_smoke.py tests/test_customer_artifact_collection.py tests/test_operator_review_pack.py tests/test_decision_calibration.py -q` |
| **Estimated runtime** | ~50 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task-local command in the plan
- **After every plan wave:** Run the quick run command
- **Before `$gsd-verify-work`:** Run the full suite command
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 44-01-01 | 01 | 1 | PROD-01 | refresh orchestration and manifest packaging | `cd credit-coach && python -m pytest tests/test_pilot_baseline_refresh.py -q` | ❌ W0 | ⬜ pending |
| 44-01-02 | 01 | 1 | PROD-01 | artifact QA contract and PASS/DEGRADED/FAIL classification | `cd credit-coach && python -m pytest tests/test_pilot_artifact_qa.py tests/test_pilot_baseline_refresh.py -q` | ❌ W0 / ❌ W0 | ⬜ pending |
| 44-02-01 | 02 | 2 | PROD-01, PROD-02 | institution overlay resolution and manifest provenance | `cd credit-coach && python -m pytest tests/test_pilot_baseline_refresh.py tests/test_pilot_integration.py -q` | ❌ W0 / ✅ | ⬜ pending |
| 44-02-02 | 02 | 2 | PROD-02 | explanation-pack serialization and drift guards | `cd credit-coach && python -m pytest tests/test_decision_explanation_pack.py tests/test_operator_review_pack.py -q` | ❌ W0 / ✅ | ⬜ pending |
| 44-03-01 | 03 | 3 | PROD-02 | pilot package schema, proof guidance, and non-leakage closure | `cd credit-coach && python -m pytest tests/test_decision_explanation_pack.py tests/test_pilot_integration.py tests/test_production_smoke.py -q` | ❌ W0 / ✅ / ✅ | ⬜ pending |
| 44-03-02 | 03 | 3 | PROD-01, PROD-02 | integrated regression for refresh, QA, calibration, and operator reuse | `cd credit-coach && python -m pytest tests/test_pilot_baseline_refresh.py tests/test_pilot_artifact_qa.py tests/test_decision_explanation_pack.py tests/test_pilot_integration.py tests/test_production_smoke.py tests/test_customer_artifact_collection.py tests/test_operator_review_pack.py tests/test_decision_calibration.py -q` | ❌ W0 / ❌ W0 / ❌ W0 / ✅ / ✅ / ✅ / ✅ / ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `credit-coach/tests/test_pilot_baseline_refresh.py` — new dedicated module for refresh orchestration, reference-run handling, cadence contract, and manifest outputs
- [ ] `credit-coach/tests/test_pilot_artifact_qa.py` — new dedicated module for PASS / DEGRADED / FAIL artifact QA classification and leakage guards
- [ ] `credit-coach/tests/test_decision_explanation_pack.py` — new dedicated module for explanation-pack schema, operator/explanation drift guards, and external-only decision packaging
- [x] `credit-coach/tests/test_pilot_integration.py` — existing pilot-package tests can protect package compatibility and refreshed artifact reuse
- [x] `credit-coach/tests/test_production_smoke.py` — existing smoke tests can protect portfolio-smoke behavior and release summary compatibility
- [x] `credit-coach/tests/test_customer_artifact_collection.py` — existing collection tests can protect upstream artifact truth consumed by refresh orchestration
- [x] `credit-coach/tests/test_operator_review_pack.py` — existing operator-packet tests can protect shared-truth drift between internal and institution-facing derived artifacts
- [x] `credit-coach/tests/test_decision_calibration.py` — existing calibration tests can protect policy-version comparison reuse

---

## Manual-Only Verifications

One human scan is still recommended after execution:

- confirm the refresh summary clearly separates `portfolio_smoke_status` from `artifact_qa_status`
- confirm `DEGRADED` reads like a usable but watchlisted pilot baseline rather than a silent failure
- confirm institution overlays are visible in manifest provenance and do not pretend to be live integrations
- confirm `decision_explanation_pack.json` carries only external-safe decision truth and bounded disclaimers
- confirm proof-facing docs say “controlled, governed, repeatable pilot baseline” rather than implying full autonomous production decisioning

All core orchestration, QA, and explanation-pack rules should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers the three new Phase 44 seams
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-23
