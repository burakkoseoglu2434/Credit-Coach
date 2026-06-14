---
phase: 42
slug: planner-quality-source-mix
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-23
---

# Phase 42 — Validation Strategy

> Per-phase validation contract for source provenance, empty-contender removal, planner competitiveness, and action-diversity / offer-maturity hardening.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_planner_quality_source_mix.py tests/test_planner_denied_objective.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_planner_quality_source_mix.py tests/test_planner_denied_objective.py tests/test_customer_artifact_collection.py tests/test_recourse_redesign.py tests/test_decision_calibration.py tests/test_phase_experiment_suite.py -q` |
| **Estimated runtime** | ~45 seconds |

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
| 42-01-01 | 01 | 1 | PLAN-01 | explicit `plan_source` contract and producer-side source propagation | `cd credit-coach && python -m pytest tests/test_planner_quality_source_mix.py tests/test_recourse_redesign.py -q` | ❌ W0 / ✅ | ⬜ pending |
| 42-01-02 | 01 | 1 | PLAN-01 | empty contender classification and pre-selection removal | `cd credit-coach && python -m pytest tests/test_planner_quality_source_mix.py tests/test_planner_denied_objective.py -q` | ❌ W0 / ✅ | ⬜ pending |
| 42-02-01 | 02 | 2 | PLAN-01 | internal-vs-dice competitiveness and near-tie source preference | `cd credit-coach && python -m pytest tests/test_planner_quality_source_mix.py tests/test_planner_denied_objective.py -q` | ❌ W0 / ✅ | ⬜ pending |
| 42-02-02 | 02 | 2 | PLAN-01 | collection-level source-mix reporting and recovery-lane wording | `cd credit-coach && python -m pytest tests/test_planner_quality_source_mix.py tests/test_customer_artifact_collection.py tests/test_decision_calibration.py -q` | ❌ W0 / ✅ / ✅ | ⬜ pending |
| 42-03-01 | 03 | 3 | PLAN-01 | action diversity and offer maturity guardrails | `cd credit-coach && python -m pytest tests/test_planner_quality_source_mix.py tests/test_customer_artifact_collection.py tests/test_recourse_redesign.py -q` | ❌ W0 / ✅ / ✅ | ⬜ pending |
| 42-03-02 | 03 | 3 | PLAN-01 | integrated regression and no-decision-owner drift | `cd credit-coach && python -m pytest tests/test_planner_quality_source_mix.py tests/test_planner_denied_objective.py tests/test_customer_artifact_collection.py tests/test_recourse_redesign.py tests/test_decision_calibration.py tests/test_phase_experiment_suite.py -q` | ❌ W0 / ✅ / ✅ / ✅ / ✅ / ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `credit-coach/tests/test_planner_quality_source_mix.py` — new dedicated test module for source truth, contender buckets, near-tie preference, diversity warnings, and offer-maturity penalties
- [x] `credit-coach/tests/test_planner_denied_objective.py` — existing planner tests can protect deterministic best-plan ordering and denied-objective stability
- [x] `credit-coach/tests/test_customer_artifact_collection.py` — existing collection tests can protect additive source-mix and diversity packaging
- [x] `credit-coach/tests/test_recourse_redesign.py` — existing recourse artifact tests can protect source propagation into single-customer artifacts
- [x] `credit-coach/tests/test_decision_calibration.py` — existing calibration tests can protect additive collection-root reporting
- [x] `credit-coach/tests/test_phase_experiment_suite.py` — existing suite tests can protect downstream proof packaging against schema drift

---

## Manual-Only Verifications

One human scan is still recommended after execution:

- confirm `fallback` best wins are reported as recovery-lane behavior, not as planner success
- confirm empty or semantically empty contenders still appear in diagnostics even though they can no longer win
- confirm internal-vs-`dice` competitiveness reads as the main quality axis in collection outputs
- confirm diversity warnings feel like anti-collapse guardrails rather than forced-equality goals
- confirm offer maturity penalties do not change the shipped customer-facing decision policy semantics

All core selection and reporting rules should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers the only missing test seam
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-23
