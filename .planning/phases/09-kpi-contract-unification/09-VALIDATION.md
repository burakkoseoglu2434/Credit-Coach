---
phase: 09
slug: kpi-contract-unification
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-14
---

# Phase 9 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_production_smoke.py tests/test_challenger_matrix_selection.py` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_production_smoke.py tests/test_challenger_matrix_selection.py tests/test_release_decision.py` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_production_smoke.py tests/test_challenger_matrix_selection.py`
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_production_smoke.py tests/test_challenger_matrix_selection.py tests/test_release_decision.py`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | KPI-01 | unit | `cd credit-coach && python -m pytest tests/test_production_smoke.py tests/test_phase_experiment_suite.py` | ✅ | ⬜ pending |
| 09-01-02 | 01 | 1 | KPI-01 | integration | `cd credit-coach && python -m pytest tests/test_challenger_matrix_selection.py tests/test_production_smoke.py` | ✅ | ⬜ pending |
| 09-02-01 | 02 | 2 | KPI-02 | integration | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_challenger_matrix_selection.py` | ✅ | ⬜ pending |
| 09-02-02 | 02 | 2 | KPI-02 | regression | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_production_smoke.py` | ✅ | ⬜ pending |
| 09-03-01 | 03 | 3 | KPI-03 | contract | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_production_smoke.py tests/test_challenger_matrix_selection.py` | ✅ | ⬜ pending |
| 09-03-02 | 03 | 3 | KPI-03 | regression | `cd credit-coach && python -m pytest tests/test_release_decision.py tests/test_phase_experiment_suite.py tests/test_production_smoke.py tests/test_challenger_matrix_selection.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_phase_experiment_suite.py` - extend aligned KPI snapshot, frozen-model provenance, and milestone acceptance assertions
- [x] `credit-coach/tests/test_production_smoke.py` - extend shared-contract alignment and seeded-evidence preference assertions
- [x] `credit-coach/tests/test_challenger_matrix_selection.py` - extend repeated-seed promotion and frozen-snapshot assertions
- [x] `credit-coach/tests/test_release_decision.py` - preserve Phase 8 release semantics coverage while KPI helpers are centralized underneath

---

## Manual-Only Verifications

One human scan is still useful after execution:

- confirm acceptance summaries remain lightweight and do not duplicate Phase 11 release-package scope

All KPI contract behavior itself should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers shared runner seams
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-14
