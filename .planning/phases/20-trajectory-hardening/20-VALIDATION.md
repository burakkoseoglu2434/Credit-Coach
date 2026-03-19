---
phase: 20
slug: trajectory-hardening
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-19
---

# Phase 20 - Validation Strategy

> Per-phase validation contract for deterministic phase/checkpoint truth, soft-monotonic trajectory safety, and controlled replan semantics.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_sequential_recourse.py tests/test_recourse_funnel_kpis.py tests/test_batch_candidate_diversity.py` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_sequential_recourse.py tests/test_recourse_funnel_kpis.py tests/test_planner_denied_objective.py tests/test_batch_candidate_diversity.py tests/test_phase_experiment_suite.py tests/test_messaging.py` |
| **Estimated runtime** | ~40 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_sequential_recourse.py tests/test_recourse_funnel_kpis.py`
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_sequential_recourse.py tests/test_recourse_funnel_kpis.py tests/test_batch_candidate_diversity.py`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 20-01-01 | 01 | 1 | PORT-04 | unit | `cd credit-coach && python -m pytest tests/test_sequential_recourse.py` | ✅ | ⬜ pending |
| 20-01-02 | 01 | 1 | PORT-04 | integration | `cd credit-coach && python -m pytest tests/test_sequential_recourse.py tests/test_recourse_funnel_kpis.py` | ✅ | ⬜ pending |
| 20-02-01 | 02 | 2 | PORT-04 | planner/consistency | `cd credit-coach && python -m pytest tests/test_planner_denied_objective.py tests/test_recourse_funnel_kpis.py` | ✅ | ⬜ pending |
| 20-02-02 | 02 | 2 | PORT-04 | artifact/narrative | `cd credit-coach && python -m pytest tests/test_batch_candidate_diversity.py tests/test_messaging.py` | ✅ | ⬜ pending |
| 20-03-01 | 03 | 3 | PORT-04 | replan/status | `cd credit-coach && python -m pytest tests/test_sequential_recourse.py tests/test_batch_candidate_diversity.py` | ✅ | ⬜ pending |
| 20-03-02 | 03 | 3 | PORT-04 | suite/proof integration | `cd credit-coach && python -m pytest tests/test_batch_candidate_diversity.py tests/test_phase_experiment_suite.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_sequential_recourse.py` — existing weekly loop tests can protect fixed review weeks and deterministic replan/status behavior
- [x] `credit-coach/tests/test_recourse_funnel_kpis.py` — existing roadmap and checkpoint serialization tests can protect canonical phase/checkpoint structure
- [x] `credit-coach/tests/test_planner_denied_objective.py` — existing planner tests can protect early-health-sensitive trajectory prioritization
- [x] `credit-coach/tests/test_batch_candidate_diversity.py` — existing artifact tests can protect trajectory status, transition reason, and policy-label outputs
- [x] `credit-coach/tests/test_phase_experiment_suite.py` — seeded suite aggregation can protect downstream trajectory metric drift
- [x] `credit-coach/tests/test_messaging.py` — narrative surfaces can protect checkpoint meaning from drifting away from checkpoint truth

---

## Manual-Only Verifications

One human scan is still required after execution:

- confirm every roadmap output now carries exactly three canonical checkpoints at `4`, `12`, and `24`
- confirm phase 3 no longer reads like an open-ended `13-52w` bucket when the product contract says `12-24w`
- confirm weak `4w` health causes a plan to read as weak even if later checkpoints improve
- confirm replan never appears outside canonical review boundaries
- confirm `on_track`, `needs_replan`, and `degraded` are easy to explain with one sentence each
- confirm policy labels feel deterministic and stable rather than opportunistic
- confirm trajectory review still preserves Phase 19 execution truth instead of silently ignoring it

All core logic should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers trajectory builder, loop, planner, artifacts, suite, and messaging seams
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-19
