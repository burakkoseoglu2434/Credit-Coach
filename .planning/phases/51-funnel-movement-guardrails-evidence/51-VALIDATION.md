---
phase: 51
slug: funnel-movement-guardrails-evidence
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-03
---

# Phase 51 — Validation Strategy

> Per-phase validation contract for movement-guardrail evidence, promotion-blocker attribution, dominant bottleneck diagnosis, collection/pilot packaging, and three-cohort proof without reopening trust or policy semantics.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py tests/test_pilot_baseline_refresh.py tests/test_pilot_artifact_qa.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py tests/test_pilot_baseline_refresh.py tests/test_pilot_artifact_qa.py tests/test_phase_experiment_suite.py tests/test_recourse_funnel_kpis.py -q` |
| **Estimated runtime** | ~90 seconds plus reruns |

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
| 51-01-01 | 01 | 1 | FUN-01, FUN-02, FUN-03 | guardrail summary, blocker matrix, bottleneck classifier | `cd credit-coach && python -m pytest tests/test_decision_calibration.py -q` | ✅ | ⬜ pending |
| 51-01-02 | 01 | 1 | FUN-01, FUN-02, FUN-03 | threshold-vs-outcome attribution and dominant diagnosis determinism | `cd credit-coach && python -m pytest tests/test_decision_calibration.py -q` | ✅ | ⬜ pending |
| 51-02-01 | 02 | 2 | FUN-01, FUN-02, FUN-03 | collection artifact packaging and summary/manifest propagation | `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py -q` | ✅ / ✅ | ⬜ pending |
| 51-02-02 | 02 | 2 | FUN-02, FUN-03 | pilot refresh and QA exposure of dominant movement diagnosis | `cd credit-coach && python -m pytest tests/test_pilot_baseline_refresh.py tests/test_pilot_artifact_qa.py tests/test_customer_artifact_collection.py -q` | ✅ / ✅ / ✅ | ⬜ pending |
| 51-03-01 | 03 | 3 | FUN-01, FUN-02, FUN-03 | integrated regression closure for guardrail evidence | `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py tests/test_pilot_baseline_refresh.py tests/test_pilot_artifact_qa.py tests/test_phase_experiment_suite.py tests/test_recourse_funnel_kpis.py -q` | ✅ / ✅ / ✅ / ✅ / ✅ / ✅ | ⬜ pending |
| 51-03-02 | 03 | 3 | FUN-01, FUN-02, FUN-03 | three-cohort movement diagnosis proof | `cd credit-coach && MPLCONFIGDIR=/tmp/mpl PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy pilot_mixed && MPLCONFIGDIR=/tmp/mpl PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy risk_band_balanced && MPLCONFIGDIR=/tmp/mpl PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy offer_needed_balanced` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_decision_calibration.py` — existing calibration tests can own guardrail summary logic, promotion-blocker attribution, and dominant bottleneck classification
- [x] `credit-coach/tests/test_customer_artifact_collection.py` — existing collection tests can protect new movement evidence artifacts, manifest fields, and summary sections
- [x] `credit-coach/tests/test_pilot_baseline_refresh.py` — existing pilot refresh tests can protect additive dominant-bottleneck and blocker-summary reporting
- [x] `credit-coach/tests/test_pilot_artifact_qa.py` — existing QA tests can protect artifact existence and provenance checks for the new evidence package
- [x] `credit-coach/tests/test_phase_experiment_suite.py` — existing experiment-suite tests can protect rerun compatibility for the new evidence files
- [x] `credit-coach/tests/test_recourse_funnel_kpis.py` — existing funnel KPI tests can protect movement counters, shift reporting, and trust/risk coexistence

---

## Manual-Only Verifications

One human scan is still recommended after execution:

- confirm the dominant bottleneck language is short enough to quote in demo and pilot discussions
- confirm `movement_guardrail_review.md` clearly separates threshold, outcome-rule, recommendation-space, and structural explanations
- confirm any “guardrail blocked” label names the specific blocker family instead of vague “too risky” wording
- confirm `mixed_no_safe_uplift` is used only when evidence is truly split

All guardrail metrics, artifact presence, and rerun-level diagnosis should otherwise remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 is satisfied with existing test seams; no brand-new dedicated test module is required
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-04-03
