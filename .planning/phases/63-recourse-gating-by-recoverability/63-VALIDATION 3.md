---
phase: 63
slug: recourse-gating-by-recoverability
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-07
---

# Phase 63 - Validation Strategy

> Per-phase validation contract for deterministic recoverability gating, additive artifact propagation, and unchanged trust semantics under limited-mode suppression.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_recoverability_signals.py tests/test_selected_surface_consistency.py tests/test_customer_artifact_collection.py tests/test_cohort_evaluation.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_recoverability_signals.py tests/test_selected_surface_consistency.py tests/test_winner_integrity_hard_stop.py tests/test_customer_artifact_collection.py tests/test_decision_calibration.py tests/test_cohort_evaluation.py tests/test_operator_packet_coherence.py tests/test_operator_review_pack.py tests/test_decision_explanation_pack.py -q` |
| **Estimated runtime** | ~45 seconds |

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
| 63-01-01 | 01 | 1 | GATE-01, GATE-02, GATE-03 | unit | `cd credit-coach && python -m pytest tests/test_recoverability_signals.py -q` | ✅ | ⬜ pending |
| 63-01-02 | 01 | 1 | GATE-01, GATE-02, GATE-03 | regression | `cd credit-coach && python -m pytest tests/test_selected_surface_consistency.py tests/test_winner_integrity_hard_stop.py -q` | ✅ | ⬜ pending |
| 63-02-01 | 02 | 2 | GATE-02, GATE-03 | integration | `cd credit-coach && python -m pytest tests/test_customer_artifact_collection.py tests/test_decision_calibration.py -q` | ✅ | ⬜ pending |
| 63-02-02 | 02 | 2 | GATE-02, GATE-03 | regression | `cd credit-coach && python -m pytest tests/test_customer_artifact_collection.py tests/test_operator_packet_coherence.py tests/test_operator_review_pack.py -q` | ✅ | ⬜ pending |
| 63-03-01 | 03 | 3 | GATE-02, GATE-03 | integration | `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py -q` | ✅ | ⬜ pending |
| 63-03-02 | 03 | 3 | GATE-01, GATE-02, GATE-03 | regression | `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py tests/test_decision_explanation_pack.py tests/test_operator_packet_coherence.py tests/test_selected_surface_consistency.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_recoverability_signals.py` already exists and should be extended for the gate-resolution contract

*Existing selected-surface, winner-integrity, collection, cohort, operator-packet, operator-review-pack, and explanation-pack suites cover the rest of the phase surface.*

---

## Manual-Only Verifications

- All Phase 63 behaviors should be automatable through the existing trust and artifact suites; no manual-only verification is required if the planned tests are extended as scoped.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths or Wave 0 coverage
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending execution
