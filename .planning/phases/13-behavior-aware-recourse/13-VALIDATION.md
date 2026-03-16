---
phase: 13
slug: behavior-aware-recourse
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-16
---

# Phase 13 - Validation Strategy

> Per-phase validation contract for execution probability, expected-utility ranking, and partial-execution simulation.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_planner_denied_objective.py tests/test_sequential_recourse.py` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_planner_denied_objective.py tests/test_sequential_recourse.py tests/test_robust_recourse.py tests/test_recourse_funnel_kpis.py tests/test_batch_candidate_diversity.py tests/test_phase_experiment_suite.py tests/test_challenger_matrix_selection.py` |
| **Estimated runtime** | ~35 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_planner_denied_objective.py`
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_planner_denied_objective.py tests/test_sequential_recourse.py tests/test_robust_recourse.py`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 13-01-01 | 01 | 1 | REC-04 | unit | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_robust_recourse.py` | ✅ | ⬜ pending |
| 13-01-02 | 01 | 1 | REC-04 | integration | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_planner_denied_objective.py tests/test_batch_candidate_diversity.py` | ✅ | ⬜ pending |
| 13-02-01 | 02 | 2 | REC-05 | unit | `cd credit-coach && python -m pytest tests/test_planner_denied_objective.py tests/test_robust_recourse.py` | ✅ | ⬜ pending |
| 13-02-02 | 02 | 2 | REC-05 | integration | `cd credit-coach && python -m pytest tests/test_batch_candidate_diversity.py tests/test_recourse_funnel_kpis.py tests/test_challenger_matrix_selection.py` | ✅ | ⬜ pending |
| 13-03-01 | 03 | 3 | REC-05 | simulation | `cd credit-coach && python -m pytest tests/test_sequential_recourse.py tests/test_robust_recourse.py tests/test_recourse_funnel_kpis.py` | ✅ | ⬜ pending |
| 13-03-02 | 03 | 3 | REC-05 | seeded integration | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_challenger_matrix_selection.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_recourse_redesign.py` - extend coverage for action- and plan-level execution probability fields
- [x] `credit-coach/tests/test_planner_denied_objective.py` - protect expected-utility ranking and high-risk prioritization under gate constraints
- [x] `credit-coach/tests/test_sequential_recourse.py` - extend weekly execution simulation coverage for mixed, failed, and recovered execution paths
- [x] `credit-coach/tests/test_robust_recourse.py` - verify execution-likelihood metadata and robust planner behavior coexist
- [x] `credit-coach/tests/test_recourse_funnel_kpis.py` - protect trajectory and partial-progress evidence when partial execution is simulated
- [x] `credit-coach/tests/test_batch_candidate_diversity.py` - verify behavior-aware summaries and breakdown artifacts stay machine-readable
- [x] `credit-coach/tests/test_phase_experiment_suite.py` - verify seeded aggregation paths can consume behavior-aware artifacts
- [x] `credit-coach/tests/test_challenger_matrix_selection.py` - verify challenger comparisons stay stable when expected-utility evidence is added

---

## Manual-Only Verifications

One human scan is still useful after execution:

- confirm execution probability fields read like interpretable recommendation evidence rather than opaque model internals
- confirm expected utility never promotes gate-ineligible plans over safe ones
- confirm partial-execution simulation reuses the existing coaching semantics instead of introducing a disconnected second behavior model
- confirm behavior-aware summaries remain concise and machine-readable enough for later seeded aggregation

All core behavior should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers generator, planner, simulation, batch, suite, and challenger seams
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-16
