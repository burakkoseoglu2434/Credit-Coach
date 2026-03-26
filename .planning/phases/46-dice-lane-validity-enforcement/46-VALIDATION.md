---
phase: 46
slug: dice-lane-validity-enforcement
status: approved
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-26
---

# Phase 46 — Validation Strategy

> Per-phase validation contract for DICE normalization parity, semantic-quality enforcement, contender eligibility, and DICE-specific rerun proof.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `credit-coach/pyproject.toml` |
| **Quick run command** | `cd credit-coach && python -m pytest tests/test_dice_lane_validity_enforcement.py tests/test_dice_baseline.py tests/test_dice_baseline_direction.py -q` |
| **Full suite command** | `cd credit-coach && python -m pytest tests/test_dice_lane_validity_enforcement.py tests/test_dice_baseline.py tests/test_dice_baseline_direction.py tests/test_recourse_redesign.py tests/test_customer_artifact_collection.py tests/test_phase_experiment_suite.py -q` |
| **Estimated runtime** | ~55 seconds plus reruns |

---

## Sampling Rate

- **After every task commit:** Run the task-local command in the plan
- **After every plan wave:** Run the quick run command
- **Before `$gsd-verify-work`:** Run the full suite command
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 46-01-01 | 01 | 1 | DICE-01 | DICE normalization unit | `cd credit-coach && python -m pytest tests/test_dice_lane_validity_enforcement.py -q` | ❌ W0 | ⬜ pending |
| 46-01-02 | 01 | 1 | DICE-01 | backend / fallback provenance and semantic quality | `cd credit-coach && python -m pytest tests/test_dice_lane_validity_enforcement.py tests/test_dice_baseline.py tests/test_dice_baseline_direction.py -q` | ❌ W0 / ✅ / ✅ | ⬜ pending |
| 46-02-01 | 02 | 2 | DICE-01, DICE-02 | contender-eligibility integration | `cd credit-coach && python -m pytest tests/test_dice_lane_validity_enforcement.py tests/test_recourse_redesign.py -q` | ❌ W0 / ✅ | ⬜ pending |
| 46-02-02 | 02 | 2 | DICE-02 | collection and artifact proof | `cd credit-coach && python -m pytest tests/test_customer_artifact_collection.py tests/test_dice_lane_validity_enforcement.py -q` | ✅ / ❌ W0 | ⬜ pending |
| 46-03-01 | 03 | 3 | DICE-01, DICE-02 | integrated regression | `cd credit-coach && python -m pytest tests/test_dice_lane_validity_enforcement.py tests/test_dice_baseline.py tests/test_dice_baseline_direction.py tests/test_recourse_redesign.py tests/test_customer_artifact_collection.py tests/test_phase_experiment_suite.py -q` | ❌ W0 / ✅ / ✅ / ✅ / ✅ / ✅ | ⬜ pending |
| 46-03-02 | 03 | 3 | DICE-02 | three-cohort rerun proof | `cd credit-coach && PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy pilot_mixed && PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy risk_band_balanced && PYTHONPATH=src python -m credit_coach.cli.run_customer_artifact_collection --n_customers 250 --sample_seed 42 --cohort_policy offer_needed_balanced` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `credit-coach/tests/test_dice_lane_validity_enforcement.py` — new dedicated module for DICE annotation completeness, semantic quality, contender eligibility, and selected-DICE cleanliness
- [x] `credit-coach/tests/test_dice_baseline.py` — existing DICE backend/fallback coverage can protect provenance and method behavior
- [x] `credit-coach/tests/test_dice_baseline_direction.py` — existing direction-focused DICE tests can protect directional assumptions at the baseline layer
- [x] `credit-coach/tests/test_recourse_redesign.py` — existing recourse integration tests can protect raw summary and contender propagation
- [x] `credit-coach/tests/test_customer_artifact_collection.py` — existing collection tests can protect DICE-specific metrics and summary rollups
- [x] `credit-coach/tests/test_phase_experiment_suite.py` — existing large-sample integration coverage can protect rerun compatibility

---

## Manual-Only Verifications

One human scan is still required after execution:

- confirm selected `dice` winners, if any, all show `dice_contender_eligible = true`
- confirm `heuristic_fallback` DICE candidates remain visible in diagnostics even when excluded from contention
- confirm `dice_all_candidates_ineligible` is distinguishable from `no_valid_winner`
- confirm collection summaries expose DICE-specific rates clearly enough to read Phase 46 acceptance

All lane contracts and rerun metrics should otherwise remain automatically verified.

---

## Validation Sign-Off

- [x] All tasks have automated verify paths
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers the one new dedicated Phase 46 test seam
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-26
