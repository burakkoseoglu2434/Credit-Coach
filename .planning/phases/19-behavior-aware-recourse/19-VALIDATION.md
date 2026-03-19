---
phase: 19
slug: behavior-aware-recourse
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-19
---

# Phase 19 - Validation Strategy

> Per-phase validation contract for conservative execution truth, stronger execution-aware ranking, and risk-band-centered behavior evidence.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_planner_denied_objective.py tests/test_batch_candidate_diversity.py` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_planner_denied_objective.py tests/test_batch_candidate_diversity.py tests/test_phase_experiment_suite.py tests/test_portfolio_validation.py tests/test_kpi_contract.py` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_planner_denied_objective.py`
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_planner_denied_objective.py tests/test_batch_candidate_diversity.py tests/test_phase_experiment_suite.py`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 19-01-01 | 01 | 1 | PORT-03 | unit | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py` | ✅ | ⬜ pending |
| 19-01-02 | 01 | 1 | PORT-03 | integration | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_planner_denied_objective.py` | ✅ | ⬜ pending |
| 19-02-01 | 02 | 2 | PORT-03 | planner | `cd credit-coach && python -m pytest tests/test_planner_denied_objective.py` | ✅ | ⬜ pending |
| 19-02-02 | 02 | 2 | PORT-03 | cohort integration | `cd credit-coach && python -m pytest tests/test_planner_denied_objective.py tests/test_batch_candidate_diversity.py` | ✅ | ⬜ pending |
| 19-03-01 | 03 | 3 | PORT-03 | artifact | `cd credit-coach && python -m pytest tests/test_batch_candidate_diversity.py tests/test_phase_experiment_suite.py` | ✅ | ⬜ pending |
| 19-03-02 | 03 | 3 | PORT-03 | proof/review | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_portfolio_validation.py tests/test_kpi_contract.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_recourse_redesign.py` — existing schema and execution-probability coverage can be extended for conservative posture and dual-realization fields
- [x] `credit-coach/tests/test_planner_denied_objective.py` — existing ranking tests can protect stronger execution-aware demotion behavior
- [x] `credit-coach/tests/test_batch_candidate_diversity.py` — existing artifact checks can protect nominal-vs-execution-aware reporting and risk-band emphasis
- [x] `credit-coach/tests/test_phase_experiment_suite.py` — existing seeded aggregation tests can protect behavior-aware summary drift
- [x] `credit-coach/tests/test_portfolio_validation.py` — existing cohort-proof tests can protect downstream execution-aware truth
- [x] `credit-coach/tests/test_kpi_contract.py` — existing review-layer tests can protect executive summary emphasis

---

## Manual-Only Verifications

One human scan is still required after execution:

- confirm the hardened estimator is still balanced and does not collapse all hard plans to near-zero probability
- confirm burden plus horizon interaction reads as a realism penalty, not arbitrary punishment
- confirm provisional and approval-pending plans remain visible but no longer feel like ordinary winners
- confirm high-risk or denied ranking clearly prefers plans that are defensible in the product, not merely theoretically attractive
- confirm behavior-aware review now foregrounds:
  - nominal vs execution-aware improvement
  - the “high uplift but low follow-through” risk
  - risk-band-first evidence
- confirm website-facing or buyer-facing interpretation can answer:
  - how much of this plan is realistically executable?

All core logic should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers estimator, planner, batch, suite, portfolio, and review seams
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-19
