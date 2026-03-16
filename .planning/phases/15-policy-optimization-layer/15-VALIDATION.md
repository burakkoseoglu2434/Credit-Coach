---
phase: 15
slug: policy-optimization-layer
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-16
---

# Phase 15 - Validation Strategy

> Per-phase validation contract for offer-bearing actions, recovery-aware ranking, and offer-policy evidence.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_planner_denied_objective.py tests/test_batch_candidate_diversity.py` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_recourse_redesign.py tests/test_planner_denied_objective.py tests/test_recourse_funnel_kpis.py tests/test_batch_candidate_diversity.py tests/test_phase_experiment_suite.py tests/test_challenger_matrix_selection.py tests/test_outcome_feedback.py tests/test_kpi_contract.py` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_planner_denied_objective.py`
- **After every plan wave:** Run `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_recourse_redesign.py tests/test_planner_denied_objective.py tests/test_batch_candidate_diversity.py`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 15-01-01 | 01 | 1 | REC-08 | schema | `cd credit-coach && python -m pytest tests/test_action_space.py tests/test_recourse_redesign.py` | ✅ | ⬜ pending |
| 15-01-02 | 01 | 1 | REC-08 | generation | `cd credit-coach && python -m pytest tests/test_recourse_redesign.py tests/test_recourse_funnel_kpis.py` | ✅ | ⬜ pending |
| 15-02-01 | 02 | 2 | REC-08, REC-09 | planner | `cd credit-coach && python -m pytest tests/test_planner_denied_objective.py tests/test_batch_candidate_diversity.py` | ✅ | ⬜ pending |
| 15-02-02 | 02 | 2 | REC-09 | batch evidence | `cd credit-coach && python -m pytest tests/test_batch_candidate_diversity.py tests/test_recourse_funnel_kpis.py` | ✅ | ⬜ pending |
| 15-03-01 | 03 | 3 | REC-08, REC-09 | seeded integration | `cd credit-coach && python -m pytest tests/test_phase_experiment_suite.py tests/test_challenger_matrix_selection.py` | ✅ | ⬜ pending |
| 15-03-02 | 03 | 3 | REC-09 | outcome and review | `cd credit-coach && python -m pytest tests/test_outcome_feedback.py tests/test_kpi_contract.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_action_space.py` - extend institutional action coverage for explicit offer-bearing templates and rankable term semantics
- [x] `credit-coach/tests/test_recourse_redesign.py` - protect offer-bearing plan serialization, mixed-plan structure, and canonical offer fields
- [x] `credit-coach/tests/test_planner_denied_objective.py` - protect governance-first offer ranking and recovery-aware ordering
- [x] `credit-coach/tests/test_recourse_funnel_kpis.py` - verify offer-bearing trajectories and offer proxy metrics remain compatible with existing funnel and checkpoint reporting
- [x] `credit-coach/tests/test_batch_candidate_diversity.py` - verify `offer_optimization_summary.json` and companion breakdown artifacts remain machine-readable
- [x] `credit-coach/tests/test_phase_experiment_suite.py` - verify seeded suite aggregation can consume offer optimization evidence deterministically
- [x] `credit-coach/tests/test_challenger_matrix_selection.py` - verify challenger comparisons stay stable when offer-policy evidence and policy-arm profiles are added
- [x] `credit-coach/tests/test_outcome_feedback.py` - verify treatment-vs-control outcome summaries remain valid when policy arms describe offer-policy profiles
- [x] `credit-coach/tests/test_kpi_contract.py` - verify review surfaces render a concise `Offer Optimization Summary` section from canonical artifacts

---

## Manual-Only Verifications

One human scan is still useful after execution:

- confirm offer-bearing actions remain inside the institutional action family rather than opening a second planner stack
- confirm mixed winner plans contain at most one active explicit offer branch
- confirm rankable offers always carry explicit terms and explicit approval state
- confirm recovery proxy upside never promotes a plan that regresses inherited fairness, reliability, telemetry, or trajectory health
- confirm `offer_acceptance_probability` remains distinct from `plan_execution_probability` in machine-readable artifacts and review copy
- confirm policy-arm outputs explain what changed in the offer policy rather than only labeling arms as control or treatment
- confirm the `Offer Optimization Summary` section remains explanation-first and does not collapse into a dashboard dump

All core behavior should remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers action space, schema, planner, batch, suite, challenger, outcome feedback, and review seams
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-16
