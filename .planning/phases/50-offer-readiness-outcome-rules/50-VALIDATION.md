---
phase: 50
slug: offer-readiness-outcome-rules
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-02
---

# Phase 50 — Validation Strategy

> Per-phase validation contract for bounded offer/readiness outcome-rule evaluation, additive provenance packaging, consumer-safe rule-effect notes, and three-cohort rerun proof against the shipped `v2.2` trust baseline.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py tests/test_operator_review_pack.py tests/test_decision_explanation_pack.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py tests/test_pilot_baseline_refresh.py tests/test_pilot_artifact_qa.py tests/test_operator_review_pack.py tests/test_decision_explanation_pack.py tests/test_phase_experiment_suite.py tests/test_recourse_funnel_kpis.py -q` |
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
| 50-01-01 | 01 | 1 | OUT-01, OUT-02 | bounded offer/readiness rule catalog and candidate comparison | `cd credit-coach && python -m pytest tests/test_decision_calibration.py -q` | ✅ | ⬜ pending |
| 50-01-02 | 01 | 1 | OUT-01, OUT-02 | shortlist / blocked / `no_safe_uplift` over outcome-rule candidates | `cd credit-coach && python -m pytest tests/test_decision_calibration.py -q` | ✅ | ⬜ pending |
| 50-02-01 | 02 | 2 | OUT-01, OUT-02 | collection and pilot-facing outcome-rule provenance packaging | `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py tests/test_pilot_baseline_refresh.py tests/test_pilot_artifact_qa.py -q` | ✅ / ✅ / ✅ / ✅ | ⬜ pending |
| 50-02-02 | 02 | 2 | OUT-03 | operator/explanation additive outcome-rule note rendering without selected-truth drift | `cd credit-coach && python -m pytest tests/test_operator_review_pack.py tests/test_decision_explanation_pack.py tests/test_customer_artifact_collection.py -q` | ✅ / ✅ / ✅ | ⬜ pending |
| 50-03-01 | 03 | 3 | OUT-01, OUT-02, OUT-03 | integrated regression and provenance closure | `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py tests/test_pilot_baseline_refresh.py tests/test_pilot_artifact_qa.py tests/test_operator_review_pack.py tests/test_decision_explanation_pack.py tests/test_phase_experiment_suite.py tests/test_recourse_funnel_kpis.py -q` | ✅ / ✅ / ✅ / ✅ / ✅ / ✅ / ✅ / ✅ | ⬜ pending |
| 50-03-02 | 03 | 3 | OUT-01, OUT-02, OUT-03 | three-cohort offer/readiness outcome proof | `cd credit-coach && MPLCONFIGDIR=/tmp/mpl PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy pilot_mixed && MPLCONFIGDIR=/tmp/mpl PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy risk_band_balanced && MPLCONFIGDIR=/tmp/mpl PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy offer_needed_balanced` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_decision_calibration.py` — existing calibration tests can own outcome-rule catalog determinism, candidate comparison, and recommendation-summary assertions
- [x] `credit-coach/tests/test_customer_artifact_collection.py` — existing collection tests can protect outcome-rule artifact packaging, manifest fields, summary sections, and cohort-level provenance
- [x] `credit-coach/tests/test_pilot_baseline_refresh.py` — existing pilot refresh tests can protect additive outcome-rule provenance compatibility
- [x] `credit-coach/tests/test_pilot_artifact_qa.py` — existing QA tests can protect coexistence of live policy-version checks with analysis-only outcome-rule provenance
- [x] `credit-coach/tests/test_operator_review_pack.py` — existing operator packet tests can protect additive rule-effect notes without selected-truth drift
- [x] `credit-coach/tests/test_decision_explanation_pack.py` — existing explanation-pack tests can protect additive rule-effect note parity
- [x] `credit-coach/tests/test_phase_experiment_suite.py` — existing rerun compatibility tests can protect outcome-rule artifact wiring
- [x] `credit-coach/tests/test_recourse_funnel_kpis.py` — existing funnel KPI tests can sanity-check decision movement reporting against unchanged trust invariants

---

## Manual-Only Verifications

One human scan is still recommended after execution:

- confirm the outcome-rule catalog clearly marks all profiles as analysis-only
- confirm the comparison review states either a concrete shortlist or explicit `no_safe_uplift`, never implied movement
- confirm operator packet and explanation pack notes describe rule-caused movement additively rather than rewriting selected truth
- confirm `offer_needed_balanced` is explicitly inspected for whether offer/readiness rules produced meaningful movement

All core rule evaluation, packaging, and drift behavior should otherwise remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 is satisfied with existing test seams; no brand-new dedicated module is required
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-04-02
