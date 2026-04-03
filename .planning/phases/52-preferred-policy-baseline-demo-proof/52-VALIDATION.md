---
phase: 52
slug: preferred-policy-baseline-demo-proof
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-03
---

# Phase 52 — Validation Strategy

> Per-phase validation contract for preferred-baseline selection, candidate non-adoption proof, collection and pilot packaging, and deterministic three-cohort evidence without inventing new policy families or new action semantics.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py tests/test_pilot_baseline_refresh.py tests/test_pilot_artifact_qa.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py tests/test_pilot_baseline_refresh.py tests/test_pilot_artifact_qa.py tests/test_phase_experiment_suite.py tests/test_recourse_funnel_kpis.py -q` |
| **Estimated runtime** | ~120 seconds plus reruns |

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
| 52-01-01 | 01 | 1 | POL-01, POL-02 | baseline selector determinism and shared-runtime-baseline contract | `cd credit-coach && python -m pytest tests/test_decision_calibration.py -q` | ✅ | ⬜ pending |
| 52-01-02 | 01 | 1 | POL-01, POL-02 | candidate disposition and non-adoption reason coverage | `cd credit-coach && python -m pytest tests/test_decision_calibration.py -q` | ✅ | ⬜ pending |
| 52-02-01 | 02 | 2 | POL-01, POL-02 | collection artifact packaging, manifest propagation, summary sections | `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py -q` | ✅ / ✅ | ⬜ pending |
| 52-02-02 | 02 | 2 | POL-01, POL-02 | pilot refresh proof docs, typed manifest compatibility, and QA checks | `cd credit-coach && python -m pytest tests/test_pilot_baseline_refresh.py tests/test_pilot_artifact_qa.py tests/test_customer_artifact_collection.py -q` | ✅ / ✅ / ✅ | ⬜ pending |
| 52-03-01 | 03 | 3 | POL-01, POL-02 | integrated regression closure for baseline-selection and proof packaging | `cd credit-coach && python -m pytest tests/test_decision_calibration.py tests/test_customer_artifact_collection.py tests/test_pilot_baseline_refresh.py tests/test_pilot_artifact_qa.py tests/test_phase_experiment_suite.py tests/test_recourse_funnel_kpis.py -q` | ✅ / ✅ / ✅ / ✅ / ✅ / ✅ | ⬜ pending |
| 52-03-02 | 03 | 3 | POL-01, POL-02 | three-cohort preferred-baseline proof | `cd credit-coach && MPLCONFIGDIR=/tmp/mpl PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy pilot_mixed && MPLCONFIGDIR=/tmp/mpl PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy risk_band_balanced && MPLCONFIGDIR=/tmp/mpl PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy offer_needed_balanced` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_decision_calibration.py` — existing calibration tests can own baseline-selection logic, preferred/fallback profile labels, and candidate disposition truth
- [x] `credit-coach/tests/test_customer_artifact_collection.py` — existing collection tests can protect new Phase 52 artifacts, manifest fields, and summary packaging
- [x] `credit-coach/tests/test_pilot_baseline_refresh.py` — existing refresh tests can protect proof-doc rendering and refresh-summary propagation
- [x] `credit-coach/tests/test_pilot_artifact_qa.py` — existing QA tests can protect artifact existence and provenance checks for the new Phase 52 proof package
- [x] `credit-coach/tests/test_phase_experiment_suite.py` — existing experiment-suite tests can protect three-cohort compatibility for Phase 52 artifact coexistence
- [x] `credit-coach/tests/test_recourse_funnel_kpis.py` — existing funnel KPI tests can protect unchanged trust, movement, and bottleneck summaries while Phase 52 selection artifacts are added

---

## Manual-Only Verifications

Two human scans are still recommended after execution:

- confirm `demo_policy_proof.md` uses bounded language and never implies that a new uplift policy has been promoted
- confirm `next_milestone_handoff.md` points to the next milestone honestly without reopening Phase 52 scope

If a real pilot input bundle is locally available, one spot-check of the generated refresh markdown is useful, but the required packaging and contract behavior should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 is satisfied with existing test seams; no brand-new dedicated test module is required
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-04-03
