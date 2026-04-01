---
phase: 48
slug: operator-packet-coherence
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-01
---

# Phase 48 — Validation Strategy

> Per-phase validation contract for status-aware operator packet rendering, fallback suppression, readiness interpretation, packet coherence diagnostics, and three-cohort rerun proof.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_operator_packet_coherence.py tests/test_operator_review_pack.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_operator_packet_coherence.py tests/test_operator_review_pack.py tests/test_customer_artifact_collection.py tests/test_phase_experiment_suite.py -q` |
| **Estimated runtime** | ~75 seconds plus reruns |

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
| 48-01-01 | 01 | 1 | OPER-01, OPER-02 | status-aware blocker/action contract | `cd credit-coach && python -m pytest tests/test_operator_packet_coherence.py tests/test_operator_review_pack.py -q` | ❌ W0 / ✅ | ⬜ pending |
| 48-01-02 | 01 | 1 | OPER-01, OPER-02 | readiness and upgrade-path suppression | `cd credit-coach && python -m pytest tests/test_operator_packet_coherence.py tests/test_operator_review_pack.py -q` | ❌ W0 / ✅ | ⬜ pending |
| 48-02-01 | 02 | 2 | OPER-01, OPER-02, OPER-03 | packet coherence diagnostics and schema propagation | `cd credit-coach && python -m pytest tests/test_operator_packet_coherence.py tests/test_operator_review_pack.py tests/test_customer_artifact_collection.py -q` | ❌ W0 / ✅ / ✅ | ⬜ pending |
| 48-02-02 | 02 | 2 | OPER-03 | flat metrics and collection summary coherence counters | `cd credit-coach && python -m pytest tests/test_customer_artifact_collection.py tests/test_operator_packet_coherence.py -q` | ✅ / ❌ W0 | ⬜ pending |
| 48-03-01 | 03 | 3 | OPER-01, OPER-02, OPER-03 | integrated regression | `cd credit-coach && python -m pytest tests/test_operator_packet_coherence.py tests/test_operator_review_pack.py tests/test_customer_artifact_collection.py tests/test_phase_experiment_suite.py -q` | ❌ W0 / ✅ / ✅ / ✅ | ⬜ pending |
| 48-03-02 | 03 | 3 | OPER-01, OPER-02, OPER-03 | three-cohort rerun proof | `cd credit-coach && PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy pilot_mixed && PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy risk_band_balanced && PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy offer_needed_balanced` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `credit-coach/tests/test_operator_packet_coherence.py` — new dedicated module for approved/conditional/rejected/empty-state packet coherence, fallback suppression, readiness render modes, and action/blocker compatibility
- [x] `credit-coach/tests/test_operator_review_pack.py` — existing packet tests can protect packet assembly and markdown rendering
- [x] `credit-coach/tests/test_customer_artifact_collection.py` — existing collection tests can protect operator metric propagation and summary counters
- [x] `credit-coach/tests/test_phase_experiment_suite.py` — existing rerun compatibility suite can protect three-cohort packet coherence proof

---

## Manual-Only Verifications

One human scan is still required after execution:

- confirm approved packets show no blockers and no next actions in short view
- confirm empty-state packets show explicit empty-state wording instead of generic advice
- confirm rejected packets do not use readiness wording that sounds like near-term approval
- confirm warning badges and appendix diagnostics remain visible even when short-view blockers or actions are suppressed

All core coherence invariants should otherwise remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers the one new dedicated Phase 48 test seam
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-04-01
