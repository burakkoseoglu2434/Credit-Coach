---
phase: 12
slug: action-realism-feasibility-expansion
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-15
---

# Phase 12 - Validation Strategy

> Per-phase validation contract for action realism, feasibility realism, and interaction constraints.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_recourse_feasibility.py tests/test_recourse_redesign.py` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_recourse_feasibility.py tests/test_recourse_redesign.py tests/test_planner_denied_objective.py tests/test_recourse_funnel_kpis.py tests/test_recourse_generator_action_budget.py` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_recourse_feasibility.py`
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_recourse_feasibility.py tests/test_recourse_redesign.py tests/test_planner_denied_objective.py`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 12-01-01 | 01 | 1 | REC-01 | unit | `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_recourse_redesign.py` | ✅ | ⬜ pending |
| 12-01-02 | 01 | 1 | REC-01 | regression | `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_recourse_funnel_kpis.py` | ✅ | ⬜ pending |
| 12-02-01 | 02 | 2 | REC-02 | unit | `cd credit-coach && python -m pytest tests/test_recourse_feasibility.py` | ✅ | ⬜ pending |
| 12-02-02 | 02 | 2 | REC-02 | integration | `cd credit-coach && python -m pytest tests/test_recourse_feasibility.py tests/test_recourse_generator_action_budget.py tests/test_planner_denied_objective.py` | ✅ | ⬜ pending |
| 12-03-01 | 03 | 3 | REC-03 | unit | `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_planner_denied_objective.py` | ✅ | ⬜ pending |
| 12-03-02 | 03 | 3 | REC-03 | integration | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_recourse_funnel_kpis.py tests/test_planner_denied_objective.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_action_space.py` - extend coverage for typed action taxonomy and compatibility
- [x] `credit-coach/tests/test_recourse_feasibility.py` - extend financially realistic constraint coverage
- [x] `credit-coach/tests/test_recourse_redesign.py` - protect generator compatibility and phased action behavior
- [x] `credit-coach/tests/test_recourse_funnel_kpis.py` - keep trajectory metrics stable under richer action semantics
- [x] `credit-coach/tests/test_planner_denied_objective.py` - verify ranking stays sane when invalid or conflicting actions are filtered
- [x] `credit-coach/tests/test_recourse_generator_action_budget.py` - protect search-budget behavior while feasibility realism tightens

---

## Manual-Only Verifications

One human scan is still useful after execution:

- confirm the new action labels read like real-world recommendations rather than disguised raw feature edits
- confirm infeasible-plan and invalid-combination reasons are explicit and interpretable in machine-readable artifacts
- confirm institutional actions are represented as constrained recommendations rather than silently treated as unconditional feature changes
- confirm backward-compatible trajectory summaries still make sense with typed actions and richer feasibility rules

All core behavior should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers action schema, feasibility, generator, planner, and trajectory seams
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-15
