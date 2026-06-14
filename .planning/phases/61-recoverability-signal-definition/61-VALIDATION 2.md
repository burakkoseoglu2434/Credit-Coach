---
phase: 61
slug: recoverability-signal-definition
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-05
---

# Phase 61 - Validation Strategy

> Per-phase validation contract for deterministic recoverability signal correctness, additive artifact propagation, and unchanged trust semantics.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_recoverability_signals.py tests/test_customer_artifact_collection.py tests/test_cohort_evaluation.py -q` |
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
| 61-01-01 | 01 | 1 | RECV-01, RECV-02, RECV-03 | unit | `cd credit-coach && python -m pytest tests/test_recoverability_signals.py -q` | ❌ W0 | ⬜ pending |
| 61-01-02 | 01 | 1 | RECV-02, RECV-03 | unit | `cd credit-coach && python -m pytest tests/test_recoverability_signals.py -q` | ❌ W0 | ⬜ pending |
| 61-02-01 | 02 | 2 | RECV-01, RECV-02, RECV-04 | integration | `cd credit-coach && python -m pytest tests/test_recoverability_signals.py tests/test_customer_artifact_collection.py -q` | ✅ | ⬜ pending |
| 61-02-02 | 02 | 2 | RECV-03, RECV-04 | integration | `cd credit-coach && python -m pytest tests/test_customer_artifact_collection.py tests/test_decision_calibration.py -q` | ✅ | ⬜ pending |
| 61-03-01 | 03 | 3 | RECV-04 | integration | `cd credit-coach && python -m pytest tests/test_recoverability_signals.py tests/test_cohort_evaluation.py -q` | ✅ | ⬜ pending |
| 61-03-02 | 03 | 3 | RECV-01, RECV-02, RECV-04 | regression | `cd credit-coach && python -m pytest tests/test_recoverability_signals.py tests/test_customer_artifact_collection.py tests/test_cohort_evaluation.py tests/test_decision_calibration.py tests/test_decision_ownership.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_recoverability_signals.py` - new focused signal contract coverage for gap math, buckets, score, threshold reachability, and reason-code derivation

*Existing infrastructure covers collection, calibration, and trust-surface regression tests.*

---

## Manual-Only Verifications

- confirm the customer-level evaluation CSV and JSON/Markdown summaries expose the recoverability fields without changing the existing trust outputs
- confirm hard-vs-soft structural blocker language stays descriptive and additive rather than replacing current decision reasons

All deterministic signal behavior and artifact propagation should otherwise remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths or Wave 0 coverage
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending execution

