---
phase: 31
slug: numeric-target-engine
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-21
---

# Phase 31 - Validation Strategy

> Per-phase validation contract for customer-specific numeric target generation, controlled unit semantics, deterministic primary-target serialization, and a clean non-verdict handoff to feasibility.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_action_space.py` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_recourse_redesign.py tests/test_messaging.py tests/test_recourse_feasibility.py` |
| **Estimated runtime** | ~40 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_action_space.py`
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_action_space.py`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 31-01-01 | 01 | 1 | NUM-01 | unit/metric catalog defaults | `cd credit-coach && python -m pytest tests/test_action_space.py` | ✅ | ⬜ pending |
| 31-01-02 | 01 | 1 | NUM-01 | numeric target schema contract | `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_recourse_redesign.py` | ✅ | ⬜ pending |
| 31-02-01 | 02 | 2 | NUM-01 | primary target generation | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py` | ✅ | ⬜ pending |
| 31-02-02 | 02 | 2 | NUM-01 | feasibility handoff boundary | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_recourse_feasibility.py` | ✅ | ⬜ pending |
| 31-03-01 | 03 | 3 | NUM-01 | runtime serialization | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_messaging.py` | ✅ | ⬜ pending |
| 31-03-02 | 03 | 3 | NUM-01 | business/technical target consumption | `cd credit-coach && python -m pytest tests/test_messaging.py tests/test_recourse_feasibility.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_action_space.py` — existing catalog tests can protect family-driven unit and metric defaults
- [x] `credit-coach/tests/test_recourse_redesign.py` — existing runtime tests can protect numeric target emission on generated plans and roadmap artifacts
- [x] `credit-coach/tests/test_messaging.py` — existing narrative tests can protect downstream consumption of primary numeric targets without reopening raw feature identity
- [x] `credit-coach/tests/test_recourse_feasibility.py` — existing feasibility tests can protect the boundary that clip/repair/reject logic still belongs downstream

---

## Manual-Only Verifications

One human scan is still required after execution:

- confirm the primary numeric target is expressed as absolute target plus signed delta
- confirm `metric_key` is business-friendly and deterministic rather than a raw feature name
- confirm mixed-unit actions expose one primary numeric target and keep secondary numeric effects technical-only
- confirm `due_month` remains one canonical value rather than silently turning into a range
- confirm Phase 31 emits generation handoff notes without introducing feasibility verdicts
- confirm unit selection is stable by `action_family` with only explicit feature overrides

All core logic should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers catalog defaults, runtime contract, downstream messaging, and feasibility-boundary seams
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-21
