---
phase: 64
slug: movement-focused-path-ranking
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-07
---

# Phase 64 - Validation Strategy

> Per-phase validation contract for recoverable/full-mode movement ranking, additive movement-field propagation, and unchanged trust semantics.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_planner_denied_objective.py tests/test_planner_quality_source_mix.py tests/test_recourse_paths.py tests/test_customer_artifact_collection.py tests/test_cohort_evaluation.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_planner_denied_objective.py tests/test_planner_quality_source_mix.py tests/test_recourse_paths.py tests/test_customer_artifact_collection.py tests/test_cohort_evaluation.py tests/test_selected_surface_consistency.py tests/test_operator_packet_coherence.py tests/test_decision_explanation_pack.py tests/test_winner_integrity_hard_stop.py -q` |
| **Estimated runtime** | ~55 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task-local command in the plan
- **After every plan wave:** Run the quick run command
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 64-01-01 | 01 | 1 | MOVE-01, MOVE-02, MOVE-03 | unit | `cd credit-coach && python -m pytest tests/test_planner_denied_objective.py tests/test_planner_quality_source_mix.py -q` | ✅ | ⬜ pending |
| 64-01-02 | 01 | 1 | MOVE-01, MOVE-02, MOVE-03 | integration | `cd credit-coach && python -m pytest tests/test_recourse_paths.py -q` | ✅ | ⬜ pending |
| 64-02-01 | 02 | 2 | MOVE-01, MOVE-02 | integration | `cd credit-coach && python -m pytest tests/test_customer_artifact_collection.py -q` | ✅ | ⬜ pending |
| 64-02-02 | 02 | 2 | MOVE-02, MOVE-03 | regression | `cd credit-coach && python -m pytest tests/test_customer_artifact_collection.py tests/test_selected_surface_consistency.py -q` | ✅ | ⬜ pending |
| 64-03-01 | 03 | 3 | MOVE-02 | integration | `cd credit-coach && python -m pytest tests/test_cohort_evaluation.py -q` | ✅ | ⬜ pending |
| 64-03-02 | 03 | 3 | MOVE-03 | regression | `cd credit-coach && python -m pytest tests/test_decision_explanation_pack.py tests/test_operator_packet_coherence.py tests/test_winner_integrity_hard_stop.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠ flaky*

---

## Wave 0 Requirements

- [x] `credit-coach/tests/test_planner_denied_objective.py` and `credit-coach/tests/test_planner_quality_source_mix.py` already exist and should be extended for recoverable/full-mode movement ordering
- [x] `credit-coach/tests/test_recourse_paths.py` already exists and should be extended to prove plan/path representative coherence under the new ranking layer

*Existing customer artifact, cohort evaluation, selected-surface, operator-packet, explanation-pack, and winner-integrity suites cover the rest of the phase surface.*

---

## Manual-Only Verifications

- All Phase 64 behaviors should be automatable through the existing planner, artifact, cohort, and trust suites; no manual-only verification is required if the planned tests are extended as scoped.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths or Wave 0 coverage
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending execution
