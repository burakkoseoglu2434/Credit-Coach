---
phase: 45
slug: winner-integrity-hard-stop
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-26
---

# Phase 45 — Validation Strategy

> Per-phase validation contract for winner hard-stop enforcement, no-valid-winner propagation, and selected-surface integrity.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_winner_integrity_hard_stop.py tests/test_customer_artifact_collection.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_winner_integrity_hard_stop.py tests/test_customer_artifact_collection.py tests/test_recourse_redesign.py tests/test_planner_quality_source_mix.py tests/test_phase_experiment_suite.py -q` |
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
| 45-01-01 | 01 | 1 | WINT-01, WINT-02 | planner unit | `cd credit-coach && python -m pytest tests/test_winner_integrity_hard_stop.py -q` | ❌ W0 | ⬜ pending |
| 45-01-02 | 01 | 1 | WINT-01, WINT-02 | single/batch chooser integration | `cd credit-coach && python -m pytest tests/test_winner_integrity_hard_stop.py tests/test_planner_quality_source_mix.py -q` | ❌ W0 / ✅ | ⬜ pending |
| 45-02-01 | 02 | 2 | WINT-03 | raw/flat parity and selected-best integrity | `cd credit-coach && python -m pytest tests/test_customer_artifact_collection.py tests/test_recourse_redesign.py -q` | ✅ / ✅ | ⬜ pending |
| 45-02-02 | 02 | 2 | WINT-03 | no-valid-winner collection summary semantics | `cd credit-coach && python -m pytest tests/test_customer_artifact_collection.py tests/test_winner_integrity_hard_stop.py -q` | ✅ / ❌ W0 | ⬜ pending |
| 45-03-01 | 03 | 3 | WINT-01, WINT-02, WINT-03 | integrated regression | `cd credit-coach && python -m pytest tests/test_winner_integrity_hard_stop.py tests/test_customer_artifact_collection.py tests/test_recourse_redesign.py tests/test_planner_quality_source_mix.py tests/test_phase_experiment_suite.py -q` | ❌ W0 / ✅ / ✅ / ✅ / ✅ | ⬜ pending |
| 45-03-02 | 03 | 3 | WINT-01, WINT-03 | large-sample rerun proof | `cd credit-coach && PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy pilot_mixed && PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy risk_band_balanced && PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy offer_needed_balanced` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `credit-coach/tests/test_winner_integrity_hard_stop.py` — new dedicated module for widened-valid selection, invalid hard-stop, and `no_valid_winner` result semantics
- [x] `credit-coach/tests/test_customer_artifact_collection.py` — existing collection tests can protect `selected_best_flag`, parity, and summary rollups
- [x] `credit-coach/tests/test_recourse_redesign.py` — existing recourse artifact tests can protect raw summary propagation
- [x] `credit-coach/tests/test_planner_quality_source_mix.py` — existing planner-quality tests can protect ordering and source-aware ranking semantics
- [x] `credit-coach/tests/test_phase_experiment_suite.py` — existing large-sample experiment tests can protect batch integration paths

---

## Manual-Only Verifications

One human scan is still required after execution:

- confirm `no_valid_winner` cases show `best_plan_id = null` and zero selected rows without being labeled as parity corruption
- confirm widened winners report `selection_stage` and `selected_from_widened_valid_pool` coherently
- confirm collection summaries expose invalid-winner counts/rates clearly enough to read Phase 45 acceptance
- confirm no invalid selected winner remains in operator-facing rerun artifacts, even though Phase 45 is not yet an operator coherence phase

All planner and artifact contracts should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers the one new dedicated Phase 45 test seam
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-26
