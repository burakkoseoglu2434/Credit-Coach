---
phase: 34
slug: offer-layer-integration
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-22
---

# Phase 34 - Validation Strategy

> Per-phase validation contract for explicit offer contracts, approval and acceptance semantics, rankable vs provisional offer behavior, and product-safe offer visibility.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_recourse_redesign.py` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_recourse_redesign.py tests/test_batch_candidate_diversity.py tests/test_messaging.py tests/test_planner_denied_objective.py tests/test_portfolio_validation.py tests/test_phase_experiment_suite.py` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_recourse_redesign.py`
- **After every plan wave:** Run the plan-local verification command listed below
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 34-01-01 | 01 | 1 | OFFR-01 | nested offer contract schema and typed terms | `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_recourse_redesign.py` | ✅ | ⬜ pending |
| 34-01-02 | 01 | 1 | OFFR-01 | runtime serialization and backward-compatible offer bridge | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_batch_candidate_diversity.py` | ✅ | ⬜ pending |
| 34-02-01 | 02 | 2 | OFFR-01 | approval vs acceptance and rankable-offer semantics | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_planner_denied_objective.py` | ✅ | ⬜ pending |
| 34-02-02 | 02 | 2 | OFFR-01 | provisional handling and plan-level derived offer summaries | `cd credit-coach && python -m pytest tests/test_batch_candidate_diversity.py tests/test_portfolio_validation.py` | ✅ | ⬜ pending |
| 34-03-01 | 03 | 3 | OFFR-01 | business-vs-technical offer visibility and narrative wording | `cd credit-coach && python -m pytest tests/test_messaging.py tests/test_recourse_redesign.py` | ✅ | ⬜ pending |
| 34-03-02 | 03 | 3 | OFFR-01 | proof and suite consumer alignment | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_portfolio_validation.py tests/test_batch_candidate_diversity.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_action_space.py` — offer-bearing institutional templates already protect source metadata
- [x] `credit-coach/tests/test_recourse_redesign.py` — runtime contract tests already protect offer serialization and execution coupling
- [x] `credit-coach/tests/test_batch_candidate_diversity.py` — offer artifact tests already protect rankable offer metrics and summaries
- [x] `credit-coach/tests/test_messaging.py` — offer narrative tests already protect business-safe wording and technical reveal exposure
- [x] `credit-coach/tests/test_planner_denied_objective.py` — planner tests can protect provisional and approval-dependent contender semantics
- [x] `credit-coach/tests/test_portfolio_validation.py` — proof tests can protect offer summary continuity and portfolio contract stability
- [x] `credit-coach/tests/test_phase_experiment_suite.py` — suite packaging tests can protect offer-proof artifact alignment

---

## Manual-Only Verifications

One human scan is still required after execution:

- confirm business-facing default output keeps customer action primary and offer as companion narrative
- confirm approval-pending and acceptance-pending are phrased differently in product-safe language
- confirm acceptance-required offers can still appear as winners when terms are complete and approval is ready
- confirm incomplete or approval-gated offers show as conditional rather than silently disappearing
- confirm fully non-executable placeholders stay out of default customer-facing output
- confirm technical reveal carries the full offer contract and policy/scoring trace without leaking it into default business text

All core logic should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers schema, runtime, planner, messaging, proof, and suite consumers
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-22
