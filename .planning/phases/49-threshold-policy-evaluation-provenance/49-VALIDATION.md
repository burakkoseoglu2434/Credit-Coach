---
phase: 49
slug: threshold-policy-evaluation-provenance
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-02
---

# Phase 49 — Validation Strategy

> Per-phase validation contract for bounded threshold-policy comparison, analysis-only shortlist logic, policy provenance packaging, and three-cohort rerun proof against the shipped `v2.2` trust baseline.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py tests/test_pilot_baseline_refresh.py tests/test_pilot_artifact_qa.py tests/test_phase_experiment_suite.py tests/test_recourse_funnel_kpis.py -q` |
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
| 49-01-01 | 01 | 1 | THR-01, THR-02 | baseline mirror and bounded candidate ladder | `cd credit-coach && python -m pytest tests/test_decision_calibration.py -q` | ✅ | ⬜ pending |
| 49-01-02 | 01 | 1 | THR-01, THR-02 | shortlist / blocked / `no_safe_uplift` evaluation logic | `cd credit-coach && python -m pytest tests/test_decision_calibration.py -q` | ✅ | ⬜ pending |
| 49-02-01 | 02 | 2 | THR-01, THR-03 | collection calibration subtree provenance | `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py -q` | ✅ / ✅ | ⬜ pending |
| 49-02-02 | 02 | 2 | THR-03 | pilot refresh and QA additive provenance compatibility | `cd credit-coach && python -m pytest tests/test_customer_artifact_collection.py tests/test_pilot_baseline_refresh.py tests/test_pilot_artifact_qa.py -q` | ✅ / ✅ / ✅ | ⬜ pending |
| 49-03-01 | 03 | 3 | THR-01, THR-02, THR-03 | integrated regression and packaging closure | `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py tests/test_pilot_baseline_refresh.py tests/test_pilot_artifact_qa.py tests/test_phase_experiment_suite.py tests/test_recourse_funnel_kpis.py -q` | ✅ / ✅ / ✅ / ✅ / ✅ / ✅ | ⬜ pending |
| 49-03-02 | 03 | 3 | THR-01, THR-02, THR-03 | three-cohort threshold evaluation proof | `cd credit-coach && PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy pilot_mixed && PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy risk_band_balanced && PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy offer_needed_balanced` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_decision_calibration.py` — existing calibration tests can own candidate ladder, shortlist logic, shift matrix, segment breakdown, and false-positive proxy assertions
- [x] `credit-coach/tests/test_customer_artifact_collection.py` — existing collection tests can protect calibration subtree packaging, manifest fields, summary sections, and recommendation summary propagation
- [x] `credit-coach/tests/test_pilot_baseline_refresh.py` — existing pilot refresh tests can protect additive policy-analysis provenance compatibility
- [x] `credit-coach/tests/test_pilot_artifact_qa.py` — existing QA tests can protect coexistence of live policy version checks with analysis-only candidate provenance
- [x] `credit-coach/tests/test_phase_experiment_suite.py` — existing rerun compatibility tests can protect threshold-comparison artifact wiring
- [x] `credit-coach/tests/test_recourse_funnel_kpis.py` — existing funnel KPI tests can sanity-check yield and readiness reporting against the unchanged trust baseline

---

## Manual-Only Verifications

One human scan is still recommended after execution:

- confirm `calibration/policy_profile_catalog.json` is deterministic, readable, and clearly marks candidate profiles as analysis-only
- confirm `calibration_review.md` states either a concrete shortlist or explicit `no_safe_uplift`, never silent fallback
- confirm `collection_summary.md` remains business-safe while exposing policy comparison provenance and recommendation summary
- confirm live `decision_policy_version` still reads as the shipped baseline even when analysis candidates are compared in the same run

All core comparison, packaging, and provenance behavior should otherwise remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 is satisfied with existing test seams; no new dedicated module is required
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-04-02
