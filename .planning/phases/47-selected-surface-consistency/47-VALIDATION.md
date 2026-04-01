---
phase: 47
slug: selected-surface-consistency
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-01
---

# Phase 47 — Validation Strategy

> Per-phase validation contract for selected-plan overlay truth, empty-state rendering, cross-surface projection consistency, and three-cohort rerun proof.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_selected_surface_consistency.py tests/test_recourse_redesign.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_selected_surface_consistency.py tests/test_recourse_redesign.py tests/test_customer_artifact_collection.py tests/test_operator_review_pack.py tests/test_decision_explanation_pack.py tests/test_phase_experiment_suite.py -q` |
| **Estimated runtime** | ~70 seconds plus reruns |

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
| 47-01-01 | 01 | 1 | CONS-01, CONS-02 | selected overlay / empty-state unit | `cd credit-coach && python -m pytest tests/test_selected_surface_consistency.py tests/test_recourse_redesign.py -q` | ❌ W0 / ✅ | ⬜ pending |
| 47-01-02 | 01 | 1 | CONS-01 | decision-owner overlay propagation | `cd credit-coach && python -m pytest tests/test_selected_surface_consistency.py tests/test_recourse_redesign.py -q` | ❌ W0 / ✅ | ⬜ pending |
| 47-02-01 | 02 | 2 | CONS-01, CONS-03 | flat artifact and selected-row parity | `cd credit-coach && python -m pytest tests/test_customer_artifact_collection.py tests/test_selected_surface_consistency.py -q` | ✅ / ❌ W0 | ⬜ pending |
| 47-02-02 | 02 | 2 | CONS-03 | operator/explanation shared projection | `cd credit-coach && python -m pytest tests/test_operator_review_pack.py tests/test_decision_explanation_pack.py tests/test_selected_surface_consistency.py -q` | ✅ / ✅ / ❌ W0 | ⬜ pending |
| 47-03-01 | 03 | 3 | CONS-01, CONS-02, CONS-03 | integrated regression | `cd credit-coach && python -m pytest tests/test_selected_surface_consistency.py tests/test_recourse_redesign.py tests/test_customer_artifact_collection.py tests/test_operator_review_pack.py tests/test_decision_explanation_pack.py tests/test_phase_experiment_suite.py -q` | ❌ W0 / ✅ / ✅ / ✅ / ✅ / ✅ | ⬜ pending |
| 47-03-02 | 03 | 3 | CONS-01, CONS-02, CONS-03 | three-cohort rerun proof | `cd credit-coach && PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy pilot_mixed && PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy risk_band_balanced && PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy offer_needed_balanced` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `credit-coach/tests/test_selected_surface_consistency.py` — new dedicated module for selected overlay, no-valid empty-state, selected recommendation projection, and cross-surface drift guards
- [x] `credit-coach/tests/test_recourse_redesign.py` — existing roadmap/summary integration coverage can protect selected overlay propagation
- [x] `credit-coach/tests/test_customer_artifact_collection.py` — existing collection tests can protect selected-row parity and flat-metric consistency
- [x] `credit-coach/tests/test_operator_review_pack.py` — existing packet tests can protect shared selected recommendation projection
- [x] `credit-coach/tests/test_decision_explanation_pack.py` — existing explanation-pack drift checks can protect selected recommendation and readiness consistency
- [x] `credit-coach/tests/test_phase_experiment_suite.py` — existing large-sample integration coverage can protect rerun compatibility

---

## Manual-Only Verifications

One human scan is still required after execution:

- confirm `no_valid_winner` customers render explicit empty-state messaging rather than generic behavioral advice
- confirm no consumer-visible selected surface shows external `CONDITIONAL` while exposing a raw selected technical `REJECTED` status
- confirm operator packet and explanation pack show the same selected recommendation text for the same customer
- confirm collection summaries expose selected-surface consistency metrics clearly enough to read Phase 47 acceptance

All overlay, drift-guard, and rerun metrics should otherwise remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers the one new dedicated Phase 47 test seam
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-04-01

