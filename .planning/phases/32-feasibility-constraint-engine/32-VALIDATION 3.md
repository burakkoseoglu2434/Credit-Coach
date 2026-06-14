---
phase: 32
slug: feasibility-constraint-engine
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-21
---

# Phase 32 - Validation Strategy

> Per-phase validation contract for canonical feasibility verdicts, normalized constraint families, repair-vs-reject behavior, and business-safe visibility of feasibility truth.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_recourse_feasibility.py tests/test_recourse_redesign.py` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_recourse_feasibility.py tests/test_recourse_redesign.py tests/test_planner_denied_objective.py tests/test_messaging.py tests/test_portfolio_validation.py` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_recourse_feasibility.py`
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_recourse_feasibility.py tests/test_recourse_redesign.py`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 32-01-01 | 01 | 1 | FEAS-01 | action-level verdict and family normalization | `cd credit-coach && python -m pytest tests/test_recourse_feasibility.py tests/test_recourse_redesign.py` | ✅ | ⬜ pending |
| 32-01-02 | 01 | 1 | FEAS-01 | schema/trace canonicalization | `cd credit-coach && python -m pytest tests/test_recourse_feasibility.py` | ✅ | ⬜ pending |
| 32-02-01 | 02 | 2 | FEAS-01 | repair-vs-reject semantics | `cd credit-coach && python -m pytest tests/test_recourse_feasibility.py tests/test_planner_denied_objective.py` | ✅ | ⬜ pending |
| 32-02-02 | 02 | 2 | FEAS-01 | plan-level rollup and ranking posture | `cd credit-coach && python -m pytest tests/test_planner_denied_objective.py tests/test_recourse_redesign.py` | ✅ | ⬜ pending |
| 32-03-01 | 03 | 3 | FEAS-01 | business-vs-technical visibility | `cd credit-coach && python -m pytest tests/test_messaging.py tests/test_recourse_redesign.py` | ✅ | ⬜ pending |
| 32-03-02 | 03 | 3 | FEAS-01 | portfolio/runtime consumer alignment | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_recourse_redesign.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_recourse_feasibility.py` — existing feasibility tests can protect clip, semantic-loss, and rejection behavior
- [x] `credit-coach/tests/test_recourse_redesign.py` — roadmap/runtime tests can protect serialized feasibility truth
- [x] `credit-coach/tests/test_planner_denied_objective.py` — planner tests can protect repaired/provisional ordering and ranking preference
- [x] `credit-coach/tests/test_messaging.py` — existing narrative tests can protect business-safe vs technical visibility split
- [x] `credit-coach/tests/test_portfolio_validation.py` — portfolio proof tests can protect downstream consumption of normalized feasibility truth

---

## Manual-Only Verifications

One human scan is still required after execution:

- confirm `provisional` is presented as dependency-gated rather than infeasible
- confirm `invalid` does not leak to default business/product output
- confirm `repaired` remains eligible but still ranks behind comparable `valid` plans
- confirm primary-action semantic loss kills the plan, while secondary-effect loss alone does not
- confirm raw `reason_code` remains technical-only and is rolled up into canonical `constraint_family`

All core logic should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers feasibility engine, runtime serialization, ranking posture, messaging, and portfolio consumers
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-21
