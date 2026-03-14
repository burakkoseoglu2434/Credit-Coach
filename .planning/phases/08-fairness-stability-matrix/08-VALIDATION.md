---
phase: 08
slug: fairness-stability-matrix
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-14
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_batch_candidate_diversity.py tests/test_production_smoke.py tests/test_challenger_matrix_selection.py` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_batch_candidate_diversity.py tests/test_production_smoke.py tests/test_challenger_matrix_selection.py tests/test_recourse_fairness_metrics.py tests/test_release_decision.py` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_batch_candidate_diversity.py tests/test_production_smoke.py tests/test_challenger_matrix_selection.py`
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_batch_candidate_diversity.py tests/test_production_smoke.py tests/test_challenger_matrix_selection.py tests/test_recourse_fairness_metrics.py tests/test_release_decision.py`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | FAIR-01 | unit | `cd credit-coach && python -m pytest tests/test_release_decision.py tests/test_phase_experiment_suite.py` | ✅ | ✅ green |
| 08-01-02 | 01 | 1 | FAIR-01 | integration | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py` | ✅ | ✅ green |
| 08-02-01 | 02 | 2 | FAIR-02 | unit | `cd credit-coach && python -m pytest tests/test_batch_candidate_diversity.py tests/test_recourse_fairness_metrics.py` | ✅ | ✅ green |
| 08-02-02 | 02 | 2 | FAIR-02 | integration | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_batch_candidate_diversity.py` | ✅ | ✅ green |
| 08-03-01 | 03 | 3 | FAIR-03 | integration | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_challenger_matrix_selection.py` | ✅ | ✅ green |
| 08-03-02 | 03 | 3 | FAIR-03 | contract | `cd credit-coach && python -m pytest tests/test_production_smoke.py tests/test_release_decision.py` | ✅ | ✅ green |
| 08-03-03 | 03 | 3 | FAIR-03 | regression | `cd credit-coach && python -m pytest tests/test_batch_candidate_diversity.py tests/test_challenger_matrix_selection.py tests/test_production_smoke.py` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_release_decision.py` — shared `GO | LIMITED_GO | NO_GO` helper contract tests
- [x] `credit-coach/tests/test_phase_experiment_suite.py` — extend seed summary assertions for fairness seed pass counts and worst-gap fields
- [x] `credit-coach/tests/test_production_smoke.py` — extend smoke metadata assertions for `release_decision`, `smoke_pass`, and `pilot_eligible`

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-14
