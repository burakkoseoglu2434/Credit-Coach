---
phase: 14
slug: sequential-recourse-planning
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-16
---

# Phase 14 - Validation Strategy

> Per-phase validation contract for multi-phase trajectory planning, dynamic trajectory simulation, and phase-aware optimization.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_sequential_recourse.py tests/test_recourse_funnel_kpis.py` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_planner_denied_objective.py tests/test_sequential_recourse.py tests/test_robust_recourse.py tests/test_recourse_funnel_kpis.py tests/test_batch_candidate_diversity.py tests/test_phase_experiment_suite.py tests/test_challenger_matrix_selection.py` |
| **Estimated runtime** | ~40 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_sequential_recourse.py`
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_planner_denied_objective.py tests/test_sequential_recourse.py tests/test_recourse_funnel_kpis.py`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 1 | REC-06 | schema | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_recourse_funnel_kpis.py` | ✅ | ⬜ pending |
| 14-01-02 | 01 | 1 | REC-06 | integration | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_sequential_recourse.py` | ✅ | ⬜ pending |
| 14-02-01 | 02 | 2 | REC-07 | simulation | `cd credit-coach && python -m pytest tests/test_sequential_recourse.py tests/test_recourse_funnel_kpis.py tests/test_robust_recourse.py` | ✅ | ⬜ pending |
| 14-02-02 | 02 | 2 | REC-07 | seeded integration | `cd credit-coach && python -m pytest tests/test_batch_candidate_diversity.py tests/test_phase_experiment_suite.py` | ✅ | ⬜ pending |
| 14-03-01 | 03 | 3 | REC-06, REC-07 | planner | `cd credit-coach && python -m pytest tests/test_planner_denied_objective.py tests/test_challenger_matrix_selection.py` | ✅ | ⬜ pending |
| 14-03-02 | 03 | 3 | REC-06, REC-07 | e2e aggregation | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_challenger_matrix_selection.py tests/test_recourse_funnel_kpis.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_recourse_redesign.py` - extend canonical plan and serialization coverage for multi-phase trajectory structure
- [x] `credit-coach/tests/test_sequential_recourse.py` - protect weekly-loop trajectory simulation and checkpoint behavior
- [x] `credit-coach/tests/test_recourse_funnel_kpis.py` - validate phase counts, checkpoint deltas, and trajectory rollout metrics
- [x] `credit-coach/tests/test_planner_denied_objective.py` - protect phase-aware objective ordering under inherited gates
- [x] `credit-coach/tests/test_batch_candidate_diversity.py` - keep trajectory-supporting artifacts machine-readable in batch outputs
- [x] `credit-coach/tests/test_phase_experiment_suite.py` - verify seeded trajectory aggregation remains deterministic
- [x] `credit-coach/tests/test_challenger_matrix_selection.py` - verify challenger comparisons remain stable when phase-aware objective terms are added

---

## Manual-Only Verifications

One human scan is still useful after execution:

- confirm trajectory phases read like a canonical plan structure rather than a duplicated reporting view
- confirm week 4, week 12, and week 24 checkpoints are consistent with the serialized trajectory representation
- confirm long-horizon optimization never promotes a trajectory that weakens inherited safety and governance gates
- confirm dynamic simulation extends the weekly coaching seam instead of introducing a disconnected second simulator
- confirm trajectory evidence remains machine-readable and explanation-first rather than becoming a dashboard-only layer

All core behavior should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers schema, generator, simulation, planner, batch, suite, and challenger seams
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-16
