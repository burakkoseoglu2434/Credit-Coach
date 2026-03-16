---
phase: 16
slug: outcome-feedback-learning-loop
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-16
---

# Phase 16 - Validation Strategy

> Per-phase validation contract for decision logging expansion, richer outcome ingestion, and off-policy evaluation.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_outcome_feedback.py tests/test_audit_chain.py` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_outcome_feedback.py tests/test_audit_chain.py tests/test_phase_experiment_suite.py tests/test_kpi_contract.py tests/test_off_policy_evaluation.py` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_outcome_feedback.py tests/test_audit_chain.py`
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_outcome_feedback.py tests/test_audit_chain.py tests/test_phase_experiment_suite.py`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 16-01-01 | 01 | 1 | REC-10 | schema + persistence | `cd credit-coach && python -m pytest tests/test_outcome_feedback.py tests/test_audit_chain.py` | ✅ | ⬜ pending |
| 16-01-02 | 01 | 1 | REC-10 | logging completeness | `cd credit-coach && python -m pytest tests/test_outcome_feedback.py tests/test_phase_experiment_suite.py` | ✅ | ⬜ pending |
| 16-02-01 | 02 | 2 | REC-10, REC-11 | ingestion pipeline | `cd credit-coach && python -m pytest tests/test_outcome_feedback.py tests/test_phase_experiment_suite.py` | ✅ | ⬜ pending |
| 16-02-02 | 02 | 2 | REC-11 | completeness artifacts | `cd credit-coach && python -m pytest tests/test_outcome_feedback.py tests/test_kpi_contract.py` | ✅ | ⬜ pending |
| 16-03-01 | 03 | 3 | REC-11 | OPE estimators | `cd credit-coach && python -m pytest tests/test_off_policy_evaluation.py` | ✅ | ⬜ pending |
| 16-03-02 | 03 | 3 | REC-11 | review and seeded integration | `cd credit-coach && python -m pytest tests/test_outcome_feedback.py tests/test_phase_experiment_suite.py tests/test_kpi_contract.py tests/test_off_policy_evaluation.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_outcome_feedback.py` - extend delayed-outcome tests to cover richer decision context, completeness, and OPE-ready logging semantics
- [x] `credit-coach/tests/test_audit_chain.py` - protect additive decision logging against audit-chain regressions
- [x] `credit-coach/tests/test_phase_experiment_suite.py` - verify Phase 16 artifacts can be mirrored and referenced as supporting evidence
- [x] `credit-coach/tests/test_kpi_contract.py` - protect explanation-first learning-loop review integration
- [x] `credit-coach/tests/test_off_policy_evaluation.py` - add dedicated IPS / Doubly Robust regression coverage

---

## Manual-Only Verifications

One human scan is still useful after execution:

- confirm decision logging remains additive and audit-safe despite the repo lacking a migration framework
- confirm logged policy metadata is sufficient to interpret control vs treatment vs richer offer-policy arms
- confirm outcome ingestion distinguishes descriptive missingness from learning-grade complete records
- confirm IPS / DR outputs downgrade to tentative or degraded evidence when propensities or reward coverage are insufficient
- confirm learning-loop artifacts remain supporting evidence rather than silently redefining release gates

All core behavior should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers persistence, audit, outcome ingestion, seeded integration, review, and OPE seams
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-16
