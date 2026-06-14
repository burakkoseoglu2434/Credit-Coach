---
phase: 33
slug: action-difficulty-execution-modeling
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-21
---

# Phase 33 - Validation Strategy

> Per-phase validation contract for explicit difficulty truth, weakest-link-aware execution aggregation, planner leverage, and business-safe visibility of execution realism.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_planner_denied_objective.py` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_planner_denied_objective.py tests/test_messaging.py tests/test_portfolio_validation.py tests/test_phase_experiment_suite.py tests/test_kpi_contract.py` |
| **Estimated runtime** | ~55 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_recourse_redesign.py`
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_planner_denied_objective.py`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 33-01-01 | 01 | 1 | EXEC-01 | difficulty schema and action-level contract | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py` | ✅ | ⬜ pending |
| 33-01-02 | 01 | 1 | EXEC-01 | alive-only difficulty emission and approval-friction separation | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_planner_denied_objective.py` | ✅ | ⬜ pending |
| 33-02-01 | 02 | 2 | EXEC-01 | grouped execution aggregation and load penalty | `cd credit-coach && python -m pytest tests/test_planner_denied_objective.py tests/test_recourse_redesign.py` | ✅ | ⬜ pending |
| 33-02-02 | 02 | 2 | EXEC-01 | planner leverage and execution-aware plan quality | `cd credit-coach && python -m pytest tests/test_planner_denied_objective.py tests/test_portfolio_validation.py` | ✅ | ⬜ pending |
| 33-03-01 | 03 | 3 | EXEC-01 | business-vs-technical execution visibility | `cd credit-coach && python -m pytest tests/test_messaging.py tests/test_recourse_redesign.py` | ✅ | ⬜ pending |
| 33-03-02 | 03 | 3 | EXEC-01 | proof, suite, and KPI consumer alignment | `cd credit-coach && python -m pytest tests/test_portfolio_validation.py tests/test_phase_experiment_suite.py tests/test_kpi_contract.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_recourse_redesign.py` — existing runtime contract tests can protect emitted action and plan execution truth
- [x] `credit-coach/tests/test_planner_denied_objective.py` — planner tests can protect execution-aware ordering and realistic plan quality pressure
- [x] `credit-coach/tests/test_messaging.py` — narrative tests can protect business-safe difficulty and follow-through wording
- [x] `credit-coach/tests/test_portfolio_validation.py` — proof tests can protect execution-aware value and downstream risk framing
- [x] `credit-coach/tests/test_phase_experiment_suite.py` — suite packaging tests can protect curated proof artifact alignment
- [x] `credit-coach/tests/test_kpi_contract.py` — KPI-level consumers can protect execution-aware metric continuity

---

## Manual-Only Verifications

One human scan is still required after execution:

- confirm default product output shows difficulty/readiness labels rather than raw execution probabilities
- confirm invalid or semantic-break actions do not carry difficulty truth
- confirm provisional actions preserve separate approval friction rather than being described as pure customer burden
- confirm grouped actions contribute one coherent follow-through truth instead of fragmented low-level items
- confirm low execution truth is described honestly but without alarmist or model-jargon wording
- confirm planner behavior still prefers realistically executable plans over nominally stronger but follow-through-weak plans

All core logic should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers runtime contract, ranking leverage, messaging, proof, suite, and KPI consumers
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-21
