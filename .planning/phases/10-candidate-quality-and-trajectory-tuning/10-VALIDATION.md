---
phase: 10
slug: candidate-quality-and-trajectory-tuning
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-15
---

# Phase 10 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_batch_candidate_diversity.py tests/test_phase_experiment_suite.py tests/test_challenger_matrix_selection.py` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_batch_candidate_diversity.py tests/test_phase_experiment_suite.py tests/test_challenger_matrix_selection.py tests/test_production_smoke.py tests/test_release_decision.py` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_batch_candidate_diversity.py tests/test_phase_experiment_suite.py`
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_batch_candidate_diversity.py tests/test_phase_experiment_suite.py tests/test_challenger_matrix_selection.py`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | CAND-01 | unit | `cd credit-coach && python -m pytest tests/test_batch_candidate_diversity.py tests/test_phase_experiment_suite.py` | ✅ | ⬜ pending |
| 10-01-02 | 01 | 1 | CAND-01 | integration | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_challenger_matrix_selection.py` | ✅ | ⬜ pending |
| 10-02-01 | 02 | 2 | CAND-02 | unit | `cd credit-coach && python -m pytest tests/test_batch_candidate_diversity.py` | ✅ | ⬜ pending |
| 10-02-02 | 02 | 2 | CAND-02 | integration | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_challenger_matrix_selection.py` | ✅ | ⬜ pending |
| 10-03-01 | 03 | 3 | CAND-03 | contract | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_challenger_matrix_selection.py` | ✅ | ⬜ pending |
| 10-03-02 | 03 | 3 | CAND-03 | regression | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_challenger_matrix_selection.py tests/test_production_smoke.py tests/test_release_decision.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_batch_candidate_diversity.py` - extend diversity, source-provenance, and high-risk profile assertions before runner orchestration changes
- [x] `credit-coach/tests/test_phase_experiment_suite.py` - extend seeded artifact assertions for candidate-quality summaries and trajectory-tuning rollups
- [x] `credit-coach/tests/test_challenger_matrix_selection.py` - extend generator-impact, candidate-source, and promotion-diagnostic assertions
- [x] `credit-coach/tests/test_production_smoke.py` - protect Phase 9 release and acceptance behavior while derived diagnostics are added beside milestone evidence
- [x] `credit-coach/tests/test_release_decision.py` - preserve Phase 8 release-decision precedence while candidate-quality diagnostics remain non-blocking support artifacts

---

## Manual-Only Verifications

One human scan is still useful after execution:

- confirm generator and policy impact summaries remain concise and do not turn into a second acceptance contract
- confirm high-risk fast-track reporting is readable enough for milestone review without duplicating Phase 11 release-pack scope

All candidate-quality behavior itself should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers existing batch metric and seeded evidence seams
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-15
