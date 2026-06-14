---
phase: 41
slug: cohort-decision-calibration
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-23
---

# Phase 41 — Validation Strategy

> Per-phase validation contract for cohort policy semantics, funnel and readiness reporting, shadow calibration, and backward-compatible calibration packaging.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py tests/test_phase_experiment_suite.py tests/test_portfolio_validation.py -q` |
| **Estimated runtime** | ~35 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py -q`
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py tests/test_phase_experiment_suite.py -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 41-01-01 | 01 | 1 | CAL-01 | cohort policy unit tests | `cd credit-coach && python -m pytest tests/test_decision_calibration.py -q` | ❌ W0 | ⬜ pending |
| 41-01-02 | 01 | 1 | CAL-01 | collection funnel and readiness integration | `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py -q` | ❌ W0 / ✅ | ⬜ pending |
| 41-02-01 | 02 | 2 | CAL-02 | shadow calibration and false-positive proxy unit tests | `cd credit-coach && python -m pytest tests/test_decision_calibration.py -q` | ❌ W0 | ⬜ pending |
| 41-02-02 | 02 | 2 | CAL-02 | policy comparison and shift-matrix integration | `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py -q` | ❌ W0 / ✅ | ⬜ pending |
| 41-03-01 | 03 | 3 | CAL-01, CAL-02 | manifest, summary, and calibration subtree packaging | `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py tests/test_phase_experiment_suite.py -q` | ❌ W0 / ✅ / ✅ | ⬜ pending |
| 41-03-02 | 03 | 3 | CAL-01, CAL-02 | integrated regression and backward-compatibility closure | `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py tests/test_phase_experiment_suite.py tests/test_portfolio_validation.py -q` | ❌ W0 / ✅ / ✅ / ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `credit-coach/tests/test_decision_calibration.py` — new dedicated test module for cohort semantics, funnel aggregates, false-positive proxy, and policy comparison
- [x] `credit-coach/tests/test_customer_artifact_collection.py` — existing collection runner tests can protect artifact wiring and manifest/summary outputs
- [x] `credit-coach/tests/test_phase_experiment_suite.py` — existing snapshot/comparison patterns can protect calibration-style comparison outputs when reused
- [x] `credit-coach/tests/test_portfolio_validation.py` — existing segment-lens and readiness-oriented portfolio proofs can guard lens reuse assumptions

---

## Manual-Only Verifications

One human scan is still recommended after execution:

- confirm `collection_summary.md` keeps its existing inspection sections and only adds Phase 41 calibration sections
- confirm candidate policy rows are clearly marked analysis-only and do not replace shipped decision truth
- confirm `denied_first_near` is visibly labeled as stress-test only while `pilot_mixed` is clearly labeled as pilot cohort
- confirm readiness cross-tab reads as `P(status | readiness)` rather than a raw dump without normalization

All core computation should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers the only missing test seam
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-23
