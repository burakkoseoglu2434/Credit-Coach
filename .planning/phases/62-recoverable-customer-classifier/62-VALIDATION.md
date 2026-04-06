---
phase: 62
slug: recoverable-customer-classifier
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-06
---

# Phase 62 - Validation Strategy

> Per-phase validation contract for conservative recoverable classification correctness, additive artifact propagation, and unchanged trust semantics.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_recoverability_signals.py tests/test_customer_artifact_collection.py tests/test_cohort_evaluation.py tests/test_decision_calibration.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_recoverability_signals.py tests/test_customer_artifact_collection.py tests/test_cohort_evaluation.py tests/test_decision_calibration.py tests/test_decision_ownership.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py -q` |
| **Estimated runtime** | ~35 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task-local command in the plan
- **After every plan wave:** Run the quick run command
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 62-01-01 | 01 | 1 | CLSF-01, CLSF-02, CLSF-03 | unit | `cd credit-coach && python -m pytest tests/test_recoverability_signals.py -q` | ✅ | ⬜ pending |
| 62-01-02 | 01 | 1 | CLSF-01, CLSF-02 | unit | `cd credit-coach && python -m pytest tests/test_recoverability_signals.py -q` | ✅ | ⬜ pending |
| 62-02-01 | 02 | 2 | CLSF-01, CLSF-02, CLSF-03 | integration | `cd credit-coach && python -m pytest tests/test_recoverability_signals.py tests/test_customer_artifact_collection.py tests/test_decision_calibration.py -q` | ✅ | ⬜ pending |
| 62-02-02 | 02 | 2 | CLSF-02, CLSF-03 | regression | `cd credit-coach && python -m pytest tests/test_customer_artifact_collection.py tests/test_decision_ownership.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py -q` | ✅ | ⬜ pending |
| 62-03-01 | 03 | 3 | CLSF-02, CLSF-03 | integration | `cd credit-coach && python -m pytest tests/test_recoverability_signals.py tests/test_cohort_evaluation.py -q` | ✅ | ⬜ pending |
| 62-03-02 | 03 | 3 | CLSF-01, CLSF-02, CLSF-03 | regression | `cd credit-coach && python -m pytest tests/test_recoverability_signals.py tests/test_customer_artifact_collection.py tests/test_cohort_evaluation.py tests/test_decision_calibration.py tests/test_decision_ownership.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_recoverability_signals.py` already exists and should be extended for the new classifier contract

*Existing collection, cohort-evaluation, calibration, and trust suites cover the remaining propagation and regression surface.*

---

## Manual-Only Verifications

- confirm classifier truth is visible in runtime and cohort artifacts without changing selected recommendation wording
- confirm soft-blocked customers are marked not recoverable without being mislabeled as structural-limited by summary copy

All deterministic classifier behavior and trust regression protection should otherwise remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths or Wave 0 coverage
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending execution
